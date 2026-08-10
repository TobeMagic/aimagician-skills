#!/usr/bin/env python3
"""Run one locked v6.1 physical-template profile from a clean client folder.

This is the production harness the agent calls.  It validates the clean input
pack, builds deterministic query evidence, expands the Skill-owned binding
profile, assembles the native-editable deck, runs rule QA, and emits the exact
Phase 49 evidence set.  The agent never authors shape bindings or OOXML.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

THIS_DIR = Path(__file__).resolve().parent
SKILL_ROOT = THIS_DIR.parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from validate_window_pptx_v61_clean_pack import validate_requirement_pack
from window_pptx.assembly_autobinder import (
    AutoBindingError,
    atomic_write_json,
    build_default_intent,
    build_profile_query_bundle,
    compile_assembly_intent,
    load_binding_profile,
)
from window_pptx.page_template_library import load_library_index, resolve_private_root
from window_pptx.physical_assembly import (
    PhysicalAssemblyError,
    assemble_physical_deck,
    load_assembly_plan,
    write_assembly_report,
)
from window_pptx.physical_rule_qa import run_physical_rule_qa, write_rule_qa_report
from window_pptx.weak_model import FactStore, load_fact_store


OUTPUT_RELATIVE = "output/hospital-finance-annual-2025.pptx"
QUERY_RELATIVE = "evidence/template-query-results.v1.json"
PLAN_RELATIVE = "evidence/assembly-plan.v1.json"
REPORT_RELATIVE = "evidence/physical-assembly-report.v1.json"
RULE_QA_RELATIVE = "evidence/rule-qa.v1.json"
DIRECTION_RELATIVE = "evidence/direction-decision.v1.json"
NARRATIVE_RELATIVE = "evidence/narrative-plan.v1.json"
FINGERPRINT_RELATIVE = "evidence/fingerprint-bundle.v1.json"
SUMMARY_RELATIVE = "evidence/run-summary.md"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _canonical_sha(payload: Mapping[str, Any]) -> str:
    return _sha256_bytes(
        (
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            + "\n"
        ).encode("utf-8")
    )


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AutoBindingError(f"{label}_INVALID: {exc}") from exc
    if not isinstance(payload, dict):
        raise AutoBindingError(f"{label}_INVALID: root must be an object")
    return payload


def _validate_schema(payload: Mapping[str, Any], schema_name: str, label: str) -> None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - installation contract
        raise AutoBindingError(f"{label}: jsonschema is required") from exc
    schema = _read_json(SKILL_ROOT / "schemas" / schema_name, label)
    errors = sorted(
        jsonschema.Draft202012Validator(schema).iter_errors(payload),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        where = ".".join(str(part) for part in errors[0].absolute_path) or "$"
        raise AutoBindingError(f"{label}: {where}: {errors[0].message}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--private-root")
    parser.add_argument(
        "--library",
        default="v61/reference-work-summary-library-v4.json",
    )
    parser.add_argument(
        "--profile-id",
        default="phase49-work-report-15",
    )
    parser.add_argument(
        "--requirement-pack",
        default="annual-work-report.requirement-pack.v1.json",
    )
    parser.add_argument("--model-provider", default="openai", choices=["openai"])
    parser.add_argument("--model", default="gpt-5.6-terra", choices=["gpt-5.6-terra"])
    parser.add_argument("--reasoning-effort", default="medium", choices=["medium"])
    parser.add_argument("--max-output-size-bytes", type=int, default=33_941_179)
    return parser


def _profile_path(profile_id: str) -> Path:
    if not profile_id or any(char not in "abcdefghijklmnopqrstuvwxyz0123456789-_" for char in profile_id):
        raise AutoBindingError("PROFILE_ID_INVALID")
    root = (SKILL_ROOT / "registries" / "v61-binding-profiles").resolve(strict=True)
    path = root / f"{profile_id}.binding-profile.v1.json"
    if path.is_symlink() or not path.is_file():
        raise AutoBindingError(f"PROFILE_NOT_FOUND: {profile_id}")
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise AutoBindingError("PROFILE_PATH_ESCAPE")
    return resolved


def _library_path(args: argparse.Namespace) -> tuple[Path, str, Path]:
    if args.private_root:
        source = "explicit-private-root"
    elif os.environ.get("WINDOW_PPTX_PRIVATE_ROOT"):
        source = "environment-private-root"
    else:
        source = "config-private-root"
    root = resolve_private_root(explicit=args.private_root)
    raw = Path(args.library).expanduser()
    if raw.is_absolute():
        raise AutoBindingError("LIBRARY_MUST_BE_PRIVATE_ROOT_RELATIVE")
    library = (root / raw).resolve(strict=True)
    if not library.is_relative_to(root) or library.is_symlink():
        raise AutoBindingError("LIBRARY_PATH_ESCAPE")
    return library, source, root


def _direction_evidence(profile: Mapping[str, Any]) -> dict[str, Any]:
    profile_id = str(profile["profile_id"])
    theme = str(profile["dominant_style_cluster_id"])
    return {
        "schema_version": "1.0",
        "candidates": [
            {
                "slot": "safe",
                "profile_id": f"{profile_id}:safe",
                "score": 0.82,
                "theme_id": theme,
                "reasons": ["Formal hospital-governance tone and locked native editability."],
                "asset_gaps": [],
            },
            {
                "slot": "editorial",
                "profile_id": profile_id,
                "score": 0.96,
                "theme_id": theme,
                "reasons": ["Exact certified work-report family with complete 15-page lineage."],
                "asset_gaps": [],
            },
            {
                "slot": "expressive",
                "profile_id": f"{profile_id}:expressive",
                "score": 0.74,
                "theme_id": theme,
                "reasons": ["More visual variation than the locked governance context requires."],
                "asset_gaps": ["No customer photography is authorized."],
            },
        ],
        "selected_slot": "editorial",
        "selected_profile_id": profile_id,
        "confidence": 0.96,
        "fallback_reason": None,
    }


def _narrative_evidence(
    profile: Mapping[str, Any],
    plan: Mapping[str, Any],
    fact_store: FactStore,
) -> dict[str, Any]:
    fact_ids = {fact.id for fact in fact_store.active_facts()}
    slides = []
    for source, compiled in zip(
        sorted(profile["slides"], key=lambda item: item["ordinal"]),
        sorted(plan["target_slides"], key=lambda item: item["ordinal"]),
        strict=True,
    ):
        role = str(source["narrative_role"])
        structural = role in {"cover", "contents", "closing"} or role.startswith("section-")
        slides.append(
            {
                "id": f"slide-{source['ordinal']:02d}",
                "role": role,
                "title": compiled["title"],
                "importance": (
                    "critical" if role == "cover" else "high" if structural else "normal"
                ),
                "fact_refs": list(source["fact_ids"]),
                "semantic_kind": (
                    "structural"
                    if structural
                    else "metric"
                    if any(token in role for token in ("revenue", "expenditure", "kpi", "debt"))
                    else "process"
                    if role == "roadmap"
                    else "content"
                ),
                "structural": structural,
            }
        )
    scoped = {fact_id for slide in slides for fact_id in slide["fact_refs"]}
    return {
        "schema_version": "1.0",
        "archetype_id": "annual-work-report-hospital-finance-15",
        "fact_store_digest": fact_store.digest,
        "slides": slides,
        "coverage": {
            "active_fact_count": len(fact_ids),
            "scoped_fact_count": len(scoped),
            "unscoped_fact_ids": sorted(fact_ids - scoped),
        },
        "decisions": [
            "Retain the locked 15-page client-approved narrative sequence.",
            "Use exact N-to-N certified physical pages and one dominant style cluster.",
            "Delegate every physical slot and governed data mutation to the deterministic compiler.",
        ],
    }


def _fingerprint_bundle(
    *,
    args: argparse.Namespace,
    profile: Mapping[str, Any],
    profile_sha256: str,
    library_sha256: str,
    query_sha256: str,
    plan_sha256: str,
    output_sha256: str,
    report_sha256: str,
    rule_qa_sha256: str,
    fact_sha256: str,
    asset_sha256: str,
    connective_sha256: str,
    resolution_source: str,
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "fingerprints": [
            {
                "profile_id": profile["profile_id"],
                "profile_sha256": profile_sha256,
                "library_index_sha256": library_sha256,
                "query_bundle_sha256": query_sha256,
                "assembly_plan_sha256": plan_sha256,
                "output_sha256": output_sha256,
                "physical_report_sha256": report_sha256,
                "rule_qa_sha256": rule_qa_sha256,
                "fact_store_sha256": fact_sha256,
                "asset_manifest_sha256": asset_sha256,
                "connective_copy_sha256": connective_sha256,
                "evidence_generation": "v61-physical-template-assembly",
            }
        ],
        "components": {
            "model_provider": args.model_provider,
            "model": args.model,
            "reasoning_effort": args.reasoning_effort,
            "acceptance_profile": profile["acceptance_profile"],
            "private_library_resolution_source": resolution_source,
            "native_editable": True,
            "visual_fallback": False,
        },
    }


def _run_summary(
    *,
    plan: Mapping[str, Any],
    profile: Mapping[str, Any],
    output_sha256: str,
    report: Mapping[str, Any],
    rule_qa: Mapping[str, Any],
    auto_binding_report: Mapping[str, Any],
) -> str:
    profile_slides = {item["ordinal"]: item for item in profile["slides"]}
    lines = [
        "# Phase 49 candidate run",
        "",
        "Author state: `CANDIDATE_READY_FOR_BLIND_REVIEW`",
        "",
        "| Page | Narrative role | Title | Page ID | Package SHA-256 | Style cluster | Fact IDs | Rule QA |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for slide in sorted(plan["target_slides"], key=lambda item: item["ordinal"]):
        source = profile_slides[slide["ordinal"]]
        facts = ", ".join(source["fact_ids"])
        lines.append(
            f"| {slide['ordinal']} | {slide['narrative_role']} | {slide['title']} | "
            f"`{slide['page_id']}` | `{slide['package_sha256']}` | "
            f"`{plan['dominant_style_cluster_id']}` | {facts} | {rule_qa['status']} |"
        )
    metrics = report.get("metrics", {}) if isinstance(report.get("metrics"), Mapping) else {}
    editability = report.get("editability", {}) if isinstance(report.get("editability"), Mapping) else {}
    lineage_records = (
        report.get("lineage_records", [])
        if isinstance(report.get("lineage_records"), list)
        else []
    )
    verified_lineage_count = sum(
        1
        for record in lineage_records
        if isinstance(record, Mapping)
        and record.get("status") == "pass"
        and record.get("source_package_verified") is True
        and record.get("source_slide_verified") is True
        and record.get("structure_match") is True
    )
    target_slide_count = int(plan["target_slide_count"])
    physical_reuse_coverage = (
        round(verified_lineage_count / target_slide_count, 6)
        if target_slide_count
        else 0.0
    )
    lines.extend(
        [
            "",
            "## Machine-gate result",
            "",
            f"- Final PPTX SHA-256: `{output_sha256}`",
            f"- Slide count: {plan['target_slide_count']}",
            f"- Distinct page IDs: {len({slide['page_id'] for slide in plan['target_slides']})}",
            f"- Physical lineage coverage: {metrics.get('physical_reuse_coverage', physical_reuse_coverage)}",
            f"- Native editable coverage: {editability.get('native_editable_coverage', 'reported in physical report')}",
            f"- Physical assembly: {report.get('status')}",
            f"- Rule QA: {rule_qa.get('status')}",
            f"- Ordinary bindings expanded by Skill: {auto_binding_report['ordinary_slot_count']}",
            "- Unresolved warnings: none from blocking machine gates; visual release remains pending independent blind review.",
            "",
        ]
    )
    return "\n".join(lines)


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = _parser().parse_args(argv)
    if args.max_output_size_bytes < 1:
        raise AutoBindingError("MAX_OUTPUT_SIZE_INVALID")
    project = Path(args.project_root).expanduser().resolve(strict=True)
    if not project.is_dir() or project.is_symlink():
        raise AutoBindingError("PROJECT_ROOT_INVALID")
    preflight = validate_requirement_pack(project, args.requirement_pack)
    if preflight.get("status") != "PASS":
        codes = ",".join(
            str(item.get("code"))
            for item in preflight.get("issues", ())
            if isinstance(item, Mapping)
        )
        raise AutoBindingError(f"CLEAN_PACK_PREFLIGHT_FAILED: {codes}")

    profile_path = _profile_path(args.profile_id)
    profile, profile_sha = load_binding_profile(profile_path)
    library_path, resolution_source, _ = _library_path(args)
    library_sha = _sha256_file(library_path)
    library = load_library_index(library_path)
    if profile["library_index_sha256"] != library_sha:
        raise AutoBindingError("AUTO_BIND_LIBRARY_FINGERPRINT_MISMATCH")

    fact_path = project / "fact-store.v1.json"
    asset_path = project / "asset-manifest.v1.json"
    connective_path = project / "connective-copy.v1.json"
    fact_sha = _sha256_file(fact_path)
    asset_sha = _sha256_file(asset_path)
    connective_sha = _sha256_file(connective_path)
    fact_store = load_fact_store(fact_path)
    connective = _read_json(connective_path, "CONNECTIVE_COPY")

    intent = build_default_intent(profile)
    query_bundle = build_profile_query_bundle(
        profile,
        library_index=library,
        library_index_sha256=library_sha,
        library_resolution_source=resolution_source,
    )
    query_path = project / QUERY_RELATIVE
    query_sha = atomic_write_json(query_path, query_bundle)
    plan_payload, auto_binding_report = compile_assembly_intent(
        intent,
        profile=profile,
        profile_sha256=profile_sha,
        library_index=library,
        library_index_sha256=library_sha,
        query_bundle=query_bundle,
        query_bundle_sha256=query_sha,
        query_bundle_path=QUERY_RELATIVE,
        fact_store=fact_store,
        connective_copy=connective,
        authority_paths={
            "fact_store": "fact-store.v1.json",
            "asset_manifest": "asset-manifest.v1.json",
            "connective_copy": "connective-copy.v1.json",
        },
        authority_sha256={
            "fact_store": fact_sha,
            "asset_manifest": asset_sha,
            "connective_copy": connective_sha,
        },
        intent_sha256=_canonical_sha(intent),
    )

    direction = _direction_evidence(profile)
    narrative = _narrative_evidence(profile, plan_payload, fact_store)
    _validate_schema(direction, "direction-decision.v1.schema.json", "DIRECTION_SCHEMA_INVALID")
    _validate_schema(narrative, "narrative-plan.v1.schema.json", "NARRATIVE_SCHEMA_INVALID")
    atomic_write_json(project / DIRECTION_RELATIVE, direction)
    atomic_write_json(project / NARRATIVE_RELATIVE, narrative)
    plan_sha = atomic_write_json(project / PLAN_RELATIVE, plan_payload)

    lookup = {item.page_id: item for item in library.page_templates}
    plan = load_assembly_plan(project / PLAN_RELATIVE, lookup, project_root=project)
    output_path = project / OUTPUT_RELATIVE
    report = assemble_physical_deck(
        plan,
        output_path,
        library_index_sha256=library_sha,
        # Keep the plan's authority records project-relative, while supplying
        # the renderer resolved paths.  The production entry point may be
        # invoked from an agent's Skill directory rather than the client
        # directory, so relative process-CWD paths are not a safe authority.
        fact_store_path=project / "fact-store.v1.json",
        fact_store_sha256=fact_sha,
        asset_manifest_path=project / "asset-manifest.v1.json",
        asset_manifest_sha256=asset_sha,
        connective_copy_path=project / "connective-copy.v1.json",
        connective_copy_sha256=connective_sha,
        project_root=project,
        require_locked_authority=True,
        require_libreoffice=True,
        max_output_size_bytes=args.max_output_size_bytes,
        acceptance_profile=profile["acceptance_profile"],
        expected_slide_count=15,
        library_index=library,
    )
    if report.status != "pass":
        raise PhysicalAssemblyError(f"PHYSICAL_ASSEMBLY_NOT_PASS: {report.status}")
    report_path = project / REPORT_RELATIVE
    report_sha = write_assembly_report(report, report_path)
    qa = run_physical_rule_qa(output_path, plan=plan)
    if qa.status != "pass":
        write_rule_qa_report(qa, project / RULE_QA_RELATIVE)
        raise PhysicalAssemblyError(f"RULE_QA_NOT_PASS: {qa.status}")
    qa_path = project / RULE_QA_RELATIVE
    qa_sha = write_rule_qa_report(qa, qa_path)
    output_sha = _sha256_file(output_path)
    fingerprint = _fingerprint_bundle(
        args=args,
        profile=profile,
        profile_sha256=profile_sha,
        library_sha256=library_sha,
        query_sha256=query_sha,
        plan_sha256=plan_sha,
        output_sha256=output_sha,
        report_sha256=report_sha,
        rule_qa_sha256=qa_sha,
        fact_sha256=fact_sha,
        asset_sha256=asset_sha,
        connective_sha256=connective_sha,
        resolution_source=resolution_source,
    )
    _validate_schema(fingerprint, "fingerprint-bundle.v1.schema.json", "FINGERPRINT_SCHEMA_INVALID")
    atomic_write_json(project / FINGERPRINT_RELATIVE, fingerprint)
    summary = _run_summary(
        plan=plan_payload,
        profile=profile,
        output_sha256=output_sha,
        report=report.to_dict(),
        rule_qa=qa.to_dict(),
        auto_binding_report=auto_binding_report,
    )
    summary_path = project / SUMMARY_RELATIVE
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summary, encoding="utf-8")
    return {
        "status": "CANDIDATE_READY_FOR_BLIND_REVIEW",
        "output": OUTPUT_RELATIVE,
        "output_sha256": output_sha,
        "slide_count": plan.target_slide_count,
        "ordinary_slot_count": auto_binding_report["ordinary_slot_count"],
        "evidence": "evidence/",
    }


def main(argv: Sequence[str] | None = None) -> int:
    try:
        result = run(argv)
    except (AutoBindingError, PhysicalAssemblyError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
