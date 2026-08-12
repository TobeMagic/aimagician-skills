#!/usr/bin/env python3
"""Dry-run-first curation and deterministic catalog tooling for PPTX Studio."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

from pptx_studio.catalog import compile_catalog, serialize_catalog
from pptx_studio.curation import apply_curation, plan_curation, recover_curation, verify_curation
from pptx_studio.rendering import complete_render_index
from pptx_studio.query import query_catalog
from pptx_studio.composition import compile_composition
from pptx_studio.adaptation import compile_adaptation
from pptx_studio.visual_batches import ingest_batch_report, plan_visual_batches, prompt_for_batch, run_agnes_batch, run_agnes_range


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("JSON_INPUT_INVALID") from exc
    if not isinstance(payload, dict):
        raise ValueError("JSON_OBJECT_REQUIRED")
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        Path(temporary).unlink(missing_ok=True)
        raise


def render_index_from_asset_index(path: Path) -> dict[str, dict[str, Any]]:
    """Translate existing private portable-render evidence into compact page keys."""

    payload = _read_json(path)
    result: dict[str, dict[str, Any]] = {}
    for package in payload.get("packages", []):
        if not isinstance(package, dict) or package.get("status") != "ACCEPTED" or package.get("render_status") != "PASS":
            continue
        digest = package.get("package_sha256")
        if not isinstance(digest, str):
            continue
        for page in package.get("rendered_pages", []):
            if not isinstance(page, dict) or type(page.get("slide_number")) is not int:
                continue
            image_sha = page.get("visual_sha256")
            width, height = page.get("width"), page.get("height")
            if not isinstance(image_sha, str) or type(width) is not int or type(height) is not int:
                continue
            result[f"{digest}:{page['slide_number']:03d}"] = {
                "image_sha256": image_sha,
                "width": width,
                "height": height,
                "visual_quality": page.get("quality", 0.0),
            }
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("plan", "apply", "verify", "recover", "render", "compile", "query", "compose", "adapt", "vision-plan", "vision-prompt", "vision-ingest", "vision-run", "vision-run-range"))
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--archive-root", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="perform a hash-guarded recovery only")
    parser.add_argument("--asset-index", type=Path)
    parser.add_argument("--render-index", type=Path)
    parser.add_argument("--evidence-root", type=Path)
    parser.add_argument("--catalog-output", type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--query-input", type=Path)
    parser.add_argument("--query-output", type=Path)
    parser.add_argument("--composition-input", type=Path)
    parser.add_argument("--composition-output", type=Path)
    parser.add_argument("--composition-plan", type=Path)
    parser.add_argument("--adaptation-input", type=Path)
    parser.add_argument("--adaptation-output", type=Path)
    parser.add_argument("--private-root", type=Path)
    parser.add_argument("--completion-evidence-root", type=Path)
    parser.add_argument("--observation-index", type=Path)
    parser.add_argument("--batch-plan", type=Path)
    parser.add_argument("--batch-index", type=int)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--batch-start", type=int)
    parser.add_argument("--batch-end", type=int)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--prompt-output", type=Path)
    parser.add_argument("--agnes-report", type=Path)
    parser.add_argument("--vision-script", type=Path)
    parser.add_argument("--allow-external-upload", action="store_true")
    return parser


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = _parser().parse_args(argv)
    if args.command == "plan":
        result = plan_curation(args.source_root, archive_root=args.archive_root)
        _write_json(args.manifest, result)
        return {"status": result["status"], "manifest": str(args.manifest), "summary": {"active_categories": len(result["active_categories"]), "inactive_categories": result["inactive_categories"], "inactive_packages": len(result["inactive_packages"]), "active_tree_sha256": result["active_tree_sha256"], "inactive_tree_sha256": result["inactive_tree_sha256"]}}
    manifest = _read_json(args.manifest)
    if args.command == "apply":
        result = apply_curation(manifest, args.source_root, archive_root=args.archive_root)
        _write_json(args.manifest, result)
        return {"status": result["status"], "manifest": str(args.manifest), "summary": verify_curation(result, args.source_root, archive_root=args.archive_root)}
    if args.command == "verify":
        return verify_curation(manifest, args.source_root, archive_root=args.archive_root)
    if args.command == "recover":
        result = recover_curation(manifest, args.source_root, archive_root=args.archive_root, apply=args.apply)
        return result
    if args.command == "render":
        if args.asset_index is None or args.render_index is None or args.evidence_root is None:
            raise ValueError("RENDER_ARGUMENT_REQUIRED")
        if manifest.get("status") != "APPLIED":
            raise ValueError("CURATION_NOT_APPLIED")
        verify_curation(manifest, args.source_root, archive_root=args.archive_root)
        completed = complete_render_index(
            args.source_root,
            existing_index=render_index_from_asset_index(args.asset_index),
            evidence_root=args.evidence_root,
        )
        _write_json(args.render_index, completed)
        return {"status": "PASS", "render_index": str(args.render_index), "summary": {"rendered_package_count": completed["rendered_package_count"], "page_count": completed["page_count"]}}
    if args.command == "query":
        if args.catalog is None or args.observation_index is None or args.query_input is None or args.query_output is None:
            raise ValueError("QUERY_ARGUMENT_REQUIRED")
        observation_payload = _read_json(args.observation_index)
        entries = observation_payload.get("observations")
        if observation_payload.get("status") != "COMPLETE" or not isinstance(entries, list):
            raise ValueError("OBSERVATION_INDEX_INCOMPLETE")
        by_page_id = {
            item.get("page_id"): item for item in entries
            if isinstance(item, dict) and isinstance(item.get("page_id"), str)
        }
        result = query_catalog(
            _read_json(args.catalog),
            observations=by_page_id,
            request=_read_json(args.query_input),
        )
        _write_json(args.query_output, result)
        return {"status": result["status"], "query_output": str(args.query_output), "summary": {"candidate_count": len(result["candidates"])}}
    if args.command == "compose":
        if args.catalog is None or args.observation_index is None or args.composition_input is None or args.composition_output is None:
            raise ValueError("COMPOSITION_ARGUMENT_REQUIRED")
        observation_payload = _read_json(args.observation_index)
        entries = observation_payload.get("observations")
        if observation_payload.get("status") != "COMPLETE" or not isinstance(entries, list):
            raise ValueError("OBSERVATION_INDEX_INCOMPLETE")
        observations = {item.get("page_id"): item for item in entries if isinstance(item, dict) and isinstance(item.get("page_id"), str)}
        result = compile_composition(_read_json(args.catalog), observations=observations, request=_read_json(args.composition_input))
        _write_json(args.composition_output, result)
        return {"status": result["status"], "composition_output": str(args.composition_output), "summary": {"strategy": result["strategy"], "slide_count": len(result["slides"])}}
    if args.command == "adapt":
        if args.catalog is None or args.composition_plan is None or args.adaptation_input is None or args.adaptation_output is None:
            raise ValueError("ADAPTATION_ARGUMENT_REQUIRED")
        result = compile_adaptation(_read_json(args.composition_plan), catalog=_read_json(args.catalog), request=_read_json(args.adaptation_input))
        _write_json(args.adaptation_output, result)
        return {"status": result["status"], "adaptation_output": str(args.adaptation_output), "summary": {"operation_count": len(result["operations"])}}
    if args.command == "vision-plan":
        if any(value is None for value in (args.catalog, args.asset_index, args.render_index, args.private_root, args.completion_evidence_root, args.batch_plan)):
            raise ValueError("VISION_PLAN_ARGUMENT_REQUIRED")
        existing = _read_json(args.observation_index) if args.observation_index and args.observation_index.exists() else None
        plan = plan_visual_batches(
            _read_json(args.catalog),
            asset_index=_read_json(args.asset_index),
            completion_render_index=_read_json(args.render_index),
            private_root=args.private_root,
            completion_evidence_root=args.completion_evidence_root,
            existing_observations=existing,
            batch_size=args.batch_size,
        )
        _write_json(args.batch_plan, plan)
        return {"status": "PASS", "batch_plan": str(args.batch_plan), "summary": {"pending_page_count": plan["pending_page_count"], "batch_count": len(plan["batches"]), "public_batch_digest": plan["public_batch_digest"]}}
    if args.command == "vision-prompt":
        if args.batch_plan is None or args.batch_index is None or args.prompt_output is None:
            raise ValueError("VISION_PROMPT_ARGUMENT_REQUIRED")
        prompt = prompt_for_batch(_read_json(args.batch_plan), batch_index=args.batch_index)
        args.prompt_output.parent.mkdir(parents=True, exist_ok=True)
        args.prompt_output.write_text(prompt, encoding="utf-8")
        return {"status": "PASS", "prompt": str(args.prompt_output), "batch_index": args.batch_index}
    if args.command == "vision-ingest":
        if args.batch_plan is None or args.batch_index is None or args.agnes_report is None or args.observation_index is None:
            raise ValueError("VISION_INGEST_ARGUMENT_REQUIRED")
        existing = _read_json(args.observation_index) if args.observation_index.exists() else None
        observations = ingest_batch_report(
            _read_json(args.batch_plan),
            batch_index=args.batch_index,
            report=_read_json(args.agnes_report),
            existing_observations=existing,
        )
        _write_json(args.observation_index, observations)
        return {"status": "PASS", "summary": {"observation_count": observations["observation_count"], "state": observations["status"]}}
    if args.command == "vision-run":
        if not args.allow_external_upload:
            raise ValueError("EXTERNAL_UPLOAD_NOT_AUTHORIZED")
        if any(value is None for value in (args.batch_plan, args.batch_index, args.private_root, args.vision_script, args.observation_index)):
            raise ValueError("VISION_RUN_ARGUMENT_REQUIRED")
        existing = _read_json(args.observation_index) if args.observation_index.exists() else None
        observations = run_agnes_batch(
            _read_json(args.batch_plan),
            batch_index=args.batch_index,
            private_root=args.private_root,
            vision_script=args.vision_script,
            existing_observations=existing,
        )
        _write_json(args.observation_index, observations)
        return {"status": "PASS", "summary": {"batch_index": args.batch_index, "observation_count": observations["observation_count"], "state": observations["status"]}}
    if args.command == "vision-run-range":
        if not args.allow_external_upload:
            raise ValueError("EXTERNAL_UPLOAD_NOT_AUTHORIZED")
        if any(value is None for value in (args.batch_plan, args.batch_start, args.batch_end, args.private_root, args.vision_script, args.observation_index)):
            raise ValueError("VISION_RANGE_ARGUMENT_REQUIRED")
        if args.batch_start > args.batch_end:
            raise ValueError("VISION_RANGE_INVALID")
        existing = _read_json(args.observation_index) if args.observation_index.exists() else None
        observations, failed_batches = run_agnes_range(
            _read_json(args.batch_plan),
            batch_indices=list(range(args.batch_start, args.batch_end + 1)),
            private_root=args.private_root,
            vision_script=args.vision_script,
            existing_observations=existing,
            workers=args.workers,
        )
        _write_json(args.observation_index, observations)
        return {"status": "PASS" if not failed_batches else "PARTIAL", "summary": {"batch_start": args.batch_start, "batch_end": args.batch_end, "observation_count": observations["observation_count"], "state": observations["status"], "failed_batches": failed_batches}}
    if args.asset_index is None or args.catalog_output is None:
        raise ValueError("COMPILE_ARGUMENT_REQUIRED")
    if manifest.get("status") != "APPLIED":
        raise ValueError("CURATION_NOT_APPLIED")
    verify_curation(manifest, args.source_root, archive_root=args.archive_root)
    render_index = render_index_from_asset_index(args.asset_index)
    if args.render_index is not None:
        render_index.update(_read_json(args.render_index).get("pages", {}))
    catalog = compile_catalog(args.source_root, render_index=render_index)
    _write_json(args.catalog_output, catalog)
    return {"status": "PASS", "catalog": str(args.catalog_output), "summary": {"deck_count": catalog["deck_count"], "page_count": catalog["page_count"], "region_count": catalog["region_count"], "catalog_sha256": __import__("hashlib").sha256(serialize_catalog(catalog).encode("utf-8")).hexdigest()}}


def main(argv: Sequence[str] | None = None) -> int:
    try:
        print(json.dumps(run(argv), ensure_ascii=False, sort_keys=True, indent=2))
        return 0
    except ValueError as exc:
        print(json.dumps({"status": "FAIL", "code": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
