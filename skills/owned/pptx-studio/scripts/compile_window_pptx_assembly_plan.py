#!/usr/bin/env python3
"""Compile a small AssemblyIntent into a complete physical AssemblyPlan."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Sequence

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from window_pptx.assembly_autobinder import (
    AutoBindingError,
    atomic_write_json,
    compile_assembly_intent,
    load_assembly_intent,
    load_binding_profile,
)
from window_pptx.page_template_library import load_library_index, resolve_private_root
from window_pptx.physical_assembly import resolve_project_file
from window_pptx.weak_model import load_fact_store


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AutoBindingError(f"{label}_INVALID: {exc}") from exc
    if not isinstance(payload, dict):
        raise AutoBindingError(f"{label}_INVALID: root must be an object")
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--private-root")
    parser.add_argument("--library", required=True)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--intent", required=True)
    parser.add_argument("--query-bundle", required=True)
    parser.add_argument("--fact-store", required=True)
    parser.add_argument("--asset-manifest", required=True)
    parser.add_argument("--connective-copy", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--report", required=True)
    return parser


def _private_library(args: argparse.Namespace) -> Path:
    root = resolve_private_root(explicit=args.private_root)
    requested = Path(args.library).expanduser()
    library = requested if requested.is_absolute() else root / requested
    library = library.resolve(strict=True)
    if not library.is_relative_to(root):
        raise AutoBindingError("AUTO_BIND_LIBRARY_PATH_ESCAPE")
    return library


def run(argv: Sequence[str] | None = None) -> dict[str, Any]:
    args = _parser().parse_args(argv)
    project = Path(args.project_root).expanduser().resolve(strict=True)
    profile_path = Path(args.profile).expanduser().resolve(strict=True)
    intent_path = resolve_project_file(args.intent, project, label="ASSEMBLY_INTENT")
    query_path = resolve_project_file(args.query_bundle, project, label="QUERY_BUNDLE")
    fact_path = resolve_project_file(args.fact_store, project, label="FACT_STORE")
    asset_path = resolve_project_file(args.asset_manifest, project, label="ASSET_MANIFEST")
    connective_path = resolve_project_file(
        args.connective_copy,
        project,
        label="CONNECTIVE_COPY",
    )
    library_path = _private_library(args)
    profile, profile_sha = load_binding_profile(profile_path)
    intent, intent_sha = load_assembly_intent(intent_path)
    query = _load_json(query_path, "AUTO_BIND_QUERY")
    connective = _load_json(connective_path, "AUTO_BIND_CONNECTIVE")
    library = load_library_index(library_path)
    fact_store = load_fact_store(fact_path)
    plan, report = compile_assembly_intent(
        intent,
        profile=profile,
        profile_sha256=profile_sha,
        library_index=library,
        library_index_sha256=_sha256_file(library_path),
        query_bundle=query,
        query_bundle_sha256=_sha256_file(query_path),
        query_bundle_path=args.query_bundle,
        fact_store=fact_store,
        connective_copy=connective,
        authority_paths={
            "fact_store": args.fact_store,
            "asset_manifest": args.asset_manifest,
            "connective_copy": args.connective_copy,
        },
        authority_sha256={
            "fact_store": _sha256_file(fact_path),
            "asset_manifest": _sha256_file(asset_path),
            "connective_copy": _sha256_file(connective_path),
        },
        intent_sha256=intent_sha,
    )
    plan_sha = atomic_write_json(project / args.output, plan)
    report_sha = atomic_write_json(project / args.report, report)
    return {
        "status": "pass",
        "profile_id": profile["profile_id"],
        "slide_count": plan["target_slide_count"],
        "ordinary_slot_count": report["ordinary_slot_count"],
        "assembly_plan": args.output,
        "assembly_plan_sha256": plan_sha,
        "auto_binding_report": args.report,
        "auto_binding_report_sha256": report_sha,
    }


def main(argv: Sequence[str] | None = None) -> int:
    try:
        result = run(argv)
    except (AutoBindingError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
