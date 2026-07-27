#!/usr/bin/env python3
"""Execute frozen Window-PPTX weak-model trials and preserve raw evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from dataclasses import replace
from pathlib import Path
from typing import Any

from window_pptx.benchmark import (
    ArtifactDigest,
    ProviderResponse,
    TrialScorecard,
    aggregate_scorecards,
    build_trial_manifest,
    build_trial_prompt,
    canonical_sha256,
    digest_artifact,
    evaluate_trial_evidence,
    fail_portable_trial_scorecard,
    finalize_portable_trial_scorecard,
    load_benchmark_spec,
    run_opencode_response,
    validate_benchmark_fingerprint_source,
    verify_trial_artifacts,
)
from window_pptx.brand import discover_installed_fonts
from window_pptx.evidence import select_portable_slide_pngs, write_contact_sheet
from window_pptx.fingerprints import (
    collect_font_inventory_manifest,
    collect_portable_runtime_manifest,
    validate_fingerprint_bundle,
    validate_fingerprint_components,
)
from window_pptx.libreoffice import LibreOfficeVerificationError, LibreOfficeVerifier
from window_pptx.models import OutputPolicy
from window_pptx.portable_renderer import PortableRenderError, PptxGenJSRenderer
from window_pptx.portable_runner import execute_portable_render_plan
from window_pptx.quality_v2 import QualityV2GateError


SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent
REPO_ROOT = SCRIPT_PATH.parents[4]
DEFAULT_BENCHMARK_ROOT = SKILL_ROOT / "benchmarks" / "v5"
FORMAL_TIMEOUT_SECONDS = 90
FORMAL_TRIAL_COUNT = 180
FORMAL_RUN_CONTRACT_FILENAME = "run-contract.json"


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _atomic_json(path: Path, value: Any) -> None:
    _atomic_text(
        path,
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
    )


def _scorecard_from_dict(value: Any) -> TrialScorecard:
    if not isinstance(value, dict):
        raise ValueError("scorecard must be an object")
    artifacts = tuple(
        ArtifactDigest(
            relative_path=str(item["relative_path"]),
            sha256=str(item["sha256"]),
            size_bytes=int(item["size_bytes"]),
        )
        for item in value.get("artifact_digests", [])
    )
    return TrialScorecard(
        schema_version=str(value["schema_version"]),
        trial_id=str(value["trial_id"]),
        scenario_id=str(value["scenario_id"]),
        arm_id=str(value["arm_id"]),
        model_id=str(value["model_id"]),
        repeat_index=int(value["repeat_index"]),
        status=str(value["status"]),
        failure_code=value.get("failure_code"),
        failure_detail=value.get("failure_detail"),
        raw_response_sha256=value.get("raw_response_sha256"),
        deck_plan_sha256=value.get("deck_plan_sha256"),
        compiled_sha256=value.get("compiled_sha256"),
        render_plan_sha256=value.get("render_plan_sha256"),
        quality_report_sha256=value.get("quality_report_sha256"),
        metrics={
            str(key): float(metric)
            for key, metric in value.get("metrics", {}).items()
        },
        violations=tuple(str(item) for item in value.get("violations", [])),
        composite=(
            None if value.get("composite") is None else float(value["composite"])
        ),
        artifact_digests=artifacts,
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _inventory_rows(root: Path, *, excluded: set[Path]) -> list[dict[str, Any]]:
    resolved_excluded = {path.resolve() for path in excluded}
    rows: list[dict[str, Any]] = []
    for path in sorted(
        (item for item in root.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(root).as_posix().casefold(),
    ):
        if path.resolve() in resolved_excluded:
            continue
        rows.append(
            {
                "relative_path": path.relative_to(root).as_posix(),
                "sha256": _sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    return rows


def _write_inventory(root: Path, target: Path) -> Path:
    _atomic_json(
        target,
        {
            "schema_version": "1.0",
            "files": _inventory_rows(root, excluded={target}),
        },
    )
    return target


def _portable_failure_code(exc: Exception) -> str:
    if isinstance(exc, QualityV2GateError):
        return "PORTABLE_QUALITY_GATE_FAILED"
    if isinstance(exc, PortableRenderError):
        return "PORTABLE_RENDER_FAILED"
    if isinstance(exc, LibreOfficeVerificationError):
        return "PORTABLE_PROOF_FAILED"
    return "PORTABLE_DELIVERY_FAILED"


def _require_exact_json(path: Path, expected: Any, *, label: str) -> None:
    if not path.is_file():
        raise ValueError(f"{label} is missing")
    try:
        existing = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is unreadable: {exc}") from exc
    if existing != expected:
        raise ValueError(f"{label} does not match the exact formal run contract")


def _validate_formal_arguments(args: argparse.Namespace) -> None:
    if args.run_kind != "formal":
        return
    if args.benchmark_root.resolve() != DEFAULT_BENCHMARK_ROOT.resolve():
        raise ValueError("formal benchmark requires the default --benchmark-root")
    if args.timeout_seconds != FORMAL_TIMEOUT_SECONDS:
        raise ValueError(
            f"formal benchmark requires --timeout-seconds={FORMAL_TIMEOUT_SECONDS}"
        )
    if args.manifest_only:
        raise ValueError("formal benchmark forbids --manifest-only")
    if args.response_file is not None:
        raise ValueError("formal benchmark forbids --response-file replay")
    if (
        args.scenario
        or args.arm
        or args.model
        or args.repeat
        or args.max_trials is not None
        or args.fingerprint_json is None
    ):
        raise ValueError(
            "formal benchmark requires the unfiltered 180-trial protocol and "
            "--fingerprint-json"
        )


def _build_formal_run_contract(
    spec: Any,
    manifest: Any,
    fingerprint_bundle: dict[str, Any],
    *,
    benchmark_root: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "run_kind": "formal",
        "benchmark_id": spec.protocol.benchmark_id,
        "benchmark_root": benchmark_root.resolve().as_posix(),
        "manifest_sha256": canonical_sha256(manifest.to_dict()),
        "fingerprint_bundle_sha256": canonical_sha256(fingerprint_bundle),
        "timeout_seconds": timeout_seconds,
        "trial_count": len(manifest.trials),
        "trial_selection": "all",
        "response_source": "live-provider",
        "manifest_only": False,
        "resume_policy": "exact-contract",
    }


def _require_formal_trial_contract(
    trial_dir: Path,
    *,
    trial_id: str,
    run_contract_sha256: str,
) -> None:
    metadata_path = trial_dir / "provider-metadata.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"formal resume metadata is unreadable: {trial_id}: {exc}"
        ) from exc
    if (
        not isinstance(metadata, dict)
        or metadata.get("run_contract_sha256") != run_contract_sha256
    ):
        raise ValueError(
            f"resume evidence is not bound to the formal run contract: {trial_id}"
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run frozen ordinary-model Window-PPTX benchmark trials."
    )
    parser.add_argument(
        "--benchmark-root", type=Path, default=DEFAULT_BENCHMARK_ROOT
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--repo-dir", type=Path, default=REPO_ROOT)
    parser.add_argument("--scenario", action="append", default=[])
    parser.add_argument("--arm", action="append", default=[])
    parser.add_argument("--model", action="append", default=[])
    parser.add_argument("--repeat", type=int, action="append", default=[])
    parser.add_argument("--max-trials", type=int)
    parser.add_argument(
        "--timeout-seconds", type=int, default=FORMAL_TIMEOUT_SECONDS
    )
    parser.add_argument(
        "--response-file",
        type=Path,
        help="Diagnostic-only exact response replay; requires exactly one selected trial.",
    )
    parser.add_argument(
        "--run-kind",
        choices=("diagnostic", "formal"),
        default="diagnostic",
        help="Formal mode requires the frozen unfiltered 180-trial run and a clean fingerprint.",
    )
    parser.add_argument(
        "--fingerprint-json",
        type=Path,
        help=(
            "Strict fingerprint-bundle.v1 JSON captured before the run. "
            "Without it, a complete run remains fingerprint-missing."
        ),
    )
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--manifest-only", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.max_trials is not None and args.max_trials < 1:
        raise ValueError("--max-trials must be positive")
    _validate_formal_arguments(args)
    spec = load_benchmark_spec(args.benchmark_root)
    manifest = build_trial_manifest(spec)
    fingerprints: tuple[dict[str, Any], ...] | None = None
    fingerprint_bundle: dict[str, Any] | None = None
    fingerprint_components: dict[str, Any] | None = None
    if args.fingerprint_json is not None:
        fingerprint_value = json.loads(
            args.fingerprint_json.read_text(encoding="utf-8")
        )
        if (
            not isinstance(fingerprint_value, dict)
            or set(fingerprint_value)
            != {"schema_version", "fingerprints", "components"}
            or fingerprint_value.get("schema_version") != "1.0"
            or not isinstance(fingerprint_value.get("fingerprints"), list)
            or not fingerprint_value["fingerprints"]
            or any(
                not isinstance(item, dict)
                for item in fingerprint_value["fingerprints"]
            )
            or not isinstance(fingerprint_value.get("components"), dict)
        ):
            raise ValueError(
                "--fingerprint-json must match fingerprint-bundle.v1"
            )
        fingerprint_bundle = fingerprint_value
        fingerprint_components = dict(fingerprint_value["components"])
        fingerprints = tuple(dict(item) for item in fingerprint_value["fingerprints"])
        fingerprint = validate_fingerprint_bundle(fingerprints)
        validate_fingerprint_components(fingerprint, fingerprint_components)
    output_dir = args.output_dir.resolve()
    if output_dir.exists() and any(output_dir.iterdir()) and not args.resume:
        raise ValueError("benchmark output directory is non-empty; use a new path or --resume")
    if (
        args.resume
        and args.run_kind == "diagnostic"
        and (output_dir / FORMAL_RUN_CONTRACT_FILENAME).exists()
    ):
        raise ValueError("diagnostic resume cannot target a formal benchmark run")
    manifest_document = manifest.to_dict()
    formal_run_contract: dict[str, Any] | None = None
    if args.run_kind == "formal":
        if fingerprint_bundle is None:
            raise RuntimeError("formal fingerprint bundle was not retained")
        formal_run_contract = _build_formal_run_contract(
            spec,
            manifest,
            fingerprint_bundle,
            benchmark_root=args.benchmark_root,
            timeout_seconds=args.timeout_seconds,
        )
        if args.resume:
            _require_exact_json(
                output_dir / FORMAL_RUN_CONTRACT_FILENAME,
                formal_run_contract,
                label="formal run contract",
            )
            _require_exact_json(
                output_dir / "manifest.json",
                manifest_document,
                label="formal resume manifest",
            )
            _require_exact_json(
                output_dir / "fingerprint-bundle.json",
                fingerprint_bundle,
                label="formal resume fingerprint bundle",
            )
    if fingerprints is not None and not args.manifest_only:
        validate_benchmark_fingerprint_source(
            spec,
            manifest,
            fingerprints,
            artifact_root=output_dir,
            component_manifests=fingerprint_components,
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    if args.resume and args.run_kind != "formal" and manifest_path.is_file():
        try:
            existing_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"resume manifest is unreadable: {exc}") from exc
        if existing_manifest != manifest.to_dict():
            raise ValueError("resume manifest does not match the frozen protocol")
    if not (args.run_kind == "formal" and args.resume):
        _atomic_json(manifest_path, manifest_document)
    fingerprint_digest: ArtifactDigest | None = None
    fingerprint_artifact: dict[str, Any] | None = None
    if fingerprints is not None:
        fingerprint_path = output_dir / "fingerprint-bundle.json"
        if fingerprint_bundle is None:
            raise RuntimeError("fingerprint bundle was not retained")
        if (
            args.resume
            and args.run_kind != "formal"
            and fingerprint_path.is_file()
        ):
            try:
                existing_fingerprint = json.loads(
                    fingerprint_path.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError) as exc:
                raise ValueError(f"resume fingerprint is unreadable: {exc}") from exc
            if existing_fingerprint != fingerprint_bundle:
                raise ValueError("resume fingerprint bundle changed")
        if not (args.run_kind == "formal" and args.resume):
            _atomic_json(fingerprint_path, fingerprint_bundle)
        fingerprint_digest = digest_artifact(fingerprint_path, root=output_dir)
        fingerprint_artifact = fingerprint_digest.to_dict()
    run_contract_digest: ArtifactDigest | None = None
    run_contract_artifact: dict[str, Any] | None = None
    if formal_run_contract is not None:
        run_contract_path = output_dir / FORMAL_RUN_CONTRACT_FILENAME
        if not args.resume:
            _atomic_json(run_contract_path, formal_run_contract)
        run_contract_digest = digest_artifact(run_contract_path, root=output_dir)
        run_contract_artifact = run_contract_digest.to_dict()
    if args.manifest_only:
        _atomic_json(
            output_dir / "run-summary.json",
            {
                "benchmark_id": spec.protocol.benchmark_id,
                "mode": "manifest-only",
                "run_kind": args.run_kind,
                "formal_benchmark_eligible": False,
                "planned_trials": len(manifest.trials),
                "manifest_artifact": digest_artifact(
                    manifest_path, root=output_dir
                ).to_dict(),
                "fingerprint_artifact": fingerprint_artifact,
            },
        )
        _write_inventory(output_dir, output_dir / "sha256-inventory.json")
        return 0

    trials = [
        trial
        for trial in manifest.trials
        if (not args.scenario or trial.scenario_id in args.scenario)
        and (not args.arm or trial.arm_id in args.arm)
        and (not args.model or trial.model_id in args.model)
        and (not args.repeat or trial.repeat_index in args.repeat)
    ]
    if args.max_trials is not None:
        trials = trials[: args.max_trials]
    if args.response_file is not None and (
        args.run_kind != "diagnostic" or len(trials) != 1
    ):
        raise ValueError(
            "--response-file is diagnostic-only and requires exactly one selected trial"
        )
    replay_response = (
        args.response_file.read_text(encoding="utf-8")
        if args.response_file is not None
        else None
    )

    formal_eligible = (
        args.run_kind == "formal"
        and len(trials) == len(manifest.trials) == FORMAL_TRIAL_COUNT
        and fingerprints is not None
        and run_contract_digest is not None
    )
    if args.run_kind == "formal" and not formal_eligible:
        raise ValueError("formal benchmark eligibility contract was not satisfied")

    if fingerprint_components is not None:
        runtime = fingerprint_components.get("portable_runtime")
        font_component = fingerprint_components.get("font_inventory")
        if not isinstance(runtime, dict) or not isinstance(font_component, dict):
            raise ValueError("benchmark execution requires a portable fingerprint profile")
        fonts = {str(item) for item in font_component["fonts"]}
    else:
        runtime = collect_portable_runtime_manifest(skill_root=SKILL_ROOT)
        font_component = collect_font_inventory_manifest(discover_installed_fonts())
        fonts = set(font_component["fonts"])
        _atomic_json(
            output_dir / "diagnostic-runtime.json",
            {
                "schema_version": "1.0",
                "run_kind": "diagnostic",
                "formal_benchmark_eligible": False,
                "portable_runtime": runtime,
                "font_inventory": font_component,
            },
        )
    renderer = PptxGenJSRenderer(
        skill_root=SKILL_ROOT,
        node_binary=runtime["node"]["executable"],
    )
    rasterizer_arguments = (
        {
            "pdfinfo": runtime["poppler"]["pdfinfo_executable"],
            "pdftoppm": runtime["poppler"]["pdftoppm_executable"],
        }
        if "poppler" in runtime
        else {
            "ghostscript": runtime["ghostscript"]["executable"],
        }
    )
    verifier = LibreOfficeVerifier(
        soffice=runtime["libreoffice"]["executable"],
        **rasterizer_arguments,
    )

    scorecards: list[TrialScorecard] = []
    for trial in trials:
        trial_dir = output_dir / "trials" / trial.trial_id
        score_path = trial_dir / "scorecard.json"
        if args.resume and score_path.is_file():
            resumed = _scorecard_from_dict(
                json.loads(score_path.read_text(encoding="utf-8"))
            )
            if not verify_trial_artifacts(trial, resumed, artifact_root=output_dir):
                raise ValueError(
                    f"resume evidence is incomplete or tampered: {trial.trial_id}"
                )
            if run_contract_digest is not None:
                _require_formal_trial_contract(
                    trial_dir,
                    trial_id=trial.trial_id,
                    run_contract_sha256=run_contract_digest.sha256,
                )
            scorecards.append(resumed)
            continue

        prompt = build_trial_prompt(spec, trial)
        prompt_path = trial_dir / "prompt.txt"
        _atomic_text(prompt_path, prompt)
        if replay_response is not None:
            provider = ProviderResponse(
                status="replayed",
                response=replay_response,
                response_sha256=canonical_sha256(replay_response),
                exit_code=0,
                stdout_sha256=canonical_sha256(""),
                stderr_sha256=canonical_sha256(""),
                stdout="",
                stderr="",
            )
        else:
            with tempfile.TemporaryDirectory(prefix="window-pptx-provider-") as provider_dir:
                provider = run_opencode_response(
                    model_id=trial.model_id,
                    prompt=prompt,
                    directory=Path(provider_dir),
                    timeout_seconds=args.timeout_seconds,
                )
        events_path = trial_dir / "provider-events.jsonl"
        stderr_path = trial_dir / "provider-stderr.txt"
        metadata_path = trial_dir / "provider-metadata.json"
        _atomic_text(events_path, provider.stdout)
        _atomic_text(stderr_path, provider.stderr)
        provider_metadata = {
            "trial_identity": {
                "trial_id": trial.trial_id,
                "scenario_id": trial.scenario_id,
                "arm_id": trial.arm_id,
                "model_id": trial.model_id,
                "repeat_index": trial.repeat_index,
            },
            "provider": provider.to_dict(),
        }
        if run_contract_digest is not None:
            provider_metadata["run_contract_sha256"] = run_contract_digest.sha256
        _atomic_json(metadata_path, provider_metadata)
        response_path: Path | None = None
        if provider.response is not None:
            response_path = trial_dir / "response.txt"
            _atomic_text(response_path, provider.response)

        evaluation = evaluate_trial_evidence(
            spec,
            trial,
            provider.response,
            installed_fonts=fonts,
        )
        score = evaluation.scorecard
        artifact_paths = [prompt_path, events_path, stderr_path, metadata_path]
        if response_path is not None:
            artifact_paths.append(response_path)
        for document_name, document in evaluation.documents:
            document_path = trial_dir / document_name
            _atomic_json(document_path, document)
            artifact_paths.append(document_path)
        if trial.arm_id == "full-v5" and score.status == "evaluated":
            if evaluation.compiled_deck is None or evaluation.render_plan is None:
                raise RuntimeError("full-v5 evaluation lost portable render inputs")
            try:
                portable = execute_portable_render_plan(
                    evaluation.compiled_deck,
                    evaluation.render_plan,
                    output_policy=OutputPolicy(
                        source_path=None,
                        output_path=trial_dir / "delivery.pptx",
                    ),
                    audit_dir=trial_dir,
                    requested_backend="pptxgenjs",
                    verification_level="portable",
                    renderer=renderer,
                    verifier=verifier,
                    export_pdf=True,
                    quality_v2_findings=evaluation.quality_v2_findings,
                )
                if portable.render_report is None or portable.verification is None:
                    raise RuntimeError("portable delivery returned incomplete evidence")
                _atomic_json(
                    trial_dir / "backend-render-report.json",
                    portable.render_report.to_dict(),
                )
                _atomic_json(
                    trial_dir / "libreoffice-report.json",
                    portable.verification.libreoffice.to_dict(),
                )
                _atomic_json(trial_dir / "portable-result.json", portable.to_dict())
                proof_dir = trial_dir / "portable-proof"
                page_pngs = select_portable_slide_pngs(
                    proof_dir.iterdir(),
                    proof_dir=proof_dir,
                    expected_count=len(evaluation.render_plan.slides),
                )
                write_contact_sheet(page_pngs, trial_dir / "contact-sheet.png")
                score = finalize_portable_trial_scorecard(spec, evaluation, portable)
            except Exception as exc:
                quality_document = (
                    exc.quality_report_v2.to_dict()
                    if isinstance(exc, QualityV2GateError)
                    else None
                )
                if quality_document is not None:
                    _atomic_json(trial_dir / "quality-report.v2.json", quality_document)
                _atomic_json(
                    trial_dir / "portable-failure.json",
                    {
                        "schema_version": "1.0",
                        "failure_code": _portable_failure_code(exc),
                        "exception_type": type(exc).__name__,
                        "detail": str(exc)[:2000],
                    },
                )
                score = fail_portable_trial_scorecard(
                    spec,
                    score,
                    failure_code=_portable_failure_code(exc),
                    failure_detail=str(exc)[:2000],
                    quality_report=quality_document,
                )
        artifact_paths = sorted(
            (
                path
                for path in trial_dir.rglob("*")
                if path.is_file()
                and path.name not in {"scorecard.json", "sha256-inventory.json"}
            ),
            key=lambda path: path.relative_to(trial_dir).as_posix().casefold(),
        )
        score = replace(
            score,
            artifact_digests=tuple(
                digest_artifact(path, root=output_dir) for path in artifact_paths
            ),
        )
        _atomic_json(score_path, score.to_dict())
        _write_inventory(trial_dir, trial_dir / "sha256-inventory.json")
        if not verify_trial_artifacts(trial, score, artifact_root=output_dir):
            raise RuntimeError(f"trial evidence verification failed: {trial.trial_id}")
        if run_contract_digest is not None:
            _require_formal_trial_contract(
                trial_dir,
                trial_id=trial.trial_id,
                run_contract_sha256=run_contract_digest.sha256,
            )
        scorecards.append(score)

    aggregate = aggregate_scorecards(
        spec,
        manifest,
        tuple(scorecards),
        fingerprints=fingerprints,
        artifact_root=output_dir,
        fingerprint_artifact=fingerprint_digest,
    )
    run_summary = {
        "benchmark_id": spec.protocol.benchmark_id,
        "run_kind": args.run_kind,
        "formal_benchmark_eligible": formal_eligible,
        "selected_trials": len(trials),
        "evaluated_trials": sum(
            score.status == "evaluated" for score in scorecards
        ),
        "invalid_trials": sum(score.status == "invalid" for score in scorecards),
        "failed_trials": sum(score.status == "failed" for score in scorecards),
        "unavailable_trials": sum(
            score.status == "unavailable" for score in scorecards
        ),
        "aggregate": aggregate.to_dict(),
        "manifest_artifact": digest_artifact(
            manifest_path, root=output_dir
        ).to_dict(),
        "fingerprint_artifact": fingerprint_artifact,
    }
    if run_contract_artifact is not None:
        run_summary["run_contract_artifact"] = run_contract_artifact
    _atomic_json(output_dir / "run-summary.json", run_summary)
    _write_inventory(output_dir, output_dir / "sha256-inventory.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
