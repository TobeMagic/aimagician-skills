#!/usr/bin/env python3
"""Render a v6.1 physical assembly plan into an editable PPTX.

This is the narrow, portable entrypoint used by the Agent after it has
completed the discussion gate and selected certified page IDs.  It never
searches the client folder for commercial templates: the library index is
compiled from the private root and the assembly plan carries the exact page
lineage and library fingerprint.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from window_pptx.page_template_library import (  # noqa: E402
    PageTemplateError,
    load_library_index,
    resolve_private_root,
)
from window_pptx.physical_assembly import (  # noqa: E402
    DEFAULT_MAX_OUTPUT_SIZE_BYTES,
    PhysicalAssemblyError,
    assemble_physical_deck,
    load_assembly_plan,
    resolve_project_file,
    write_assembly_report,
)
from window_pptx.physical_rule_qa import (  # noqa: E402
    run_physical_rule_qa,
    write_rule_qa_report,
)
from validate_window_pptx_v61_physical_report import (  # noqa: E402
    validate_physical_report,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--assembly-plan", required=True)
    parser.add_argument("--fact-store", required=True)
    parser.add_argument("--fact-store-sha256", required=True)
    parser.add_argument("--asset-manifest", required=True)
    parser.add_argument("--asset-manifest-sha256", required=True)
    parser.add_argument("--connective-copy", required=True)
    parser.add_argument("--connective-copy-sha256", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--max-output-size-bytes",
        type=int,
        default=DEFAULT_MAX_OUTPUT_SIZE_BYTES,
    )
    parser.add_argument("--library", type=Path)
    parser.add_argument("--private-root", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--rule-qa-report", type=Path)
    parser.add_argument(
        "--acceptance-profile",
        choices=["standard", "phase49-work-report-15"],
        default="standard",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        project_root = args.project_root.expanduser()
        if project_root.is_symlink():
            raise PhysicalAssemblyError(
                f"PROJECT_ROOT_SYMLINK_REJECTED: {project_root}"
            )
        project_root = project_root.resolve(strict=True)
        assembly_plan_path = resolve_project_file(
            args.assembly_plan,
            project_root,
            label="ASSEMBLY_PLAN",
        )
        fact_store_path = resolve_project_file(
            args.fact_store,
            project_root,
            label="FACT_STORE",
        )
        asset_manifest_path = resolve_project_file(
            args.asset_manifest,
            project_root,
            label="ASSET_MANIFEST",
        )
        connective_copy_path = resolve_project_file(
            args.connective_copy,
            project_root,
            label="CONNECTIVE_COPY",
        )
        output_path = resolve_project_file(
            args.output,
            project_root,
            label="OUTPUT",
            require_file=False,
        )
        if output_path.exists():
            raise PhysicalAssemblyError(f"OUTPUT_ALREADY_EXISTS: {args.output}")
        private_root = resolve_private_root(explicit=args.private_root)
        if args.library:
            raw_library = args.library.expanduser()
            library_path = (
                raw_library.resolve(strict=False)
                if raw_library.is_absolute()
                else (private_root / raw_library).resolve(strict=False)
            )
        else:
            library_path = private_root / "v61" / (
                "reference-work-summary-library-v4.json"
                if args.acceptance_profile == "phase49-work-report-15"
                else "library-v4.json"
            )
        try:
            library_path.relative_to(project_root)
        except ValueError:
            pass
        else:
            raise PhysicalAssemblyError(
                "LIBRARY_MUST_REMAIN_OUTSIDE_PROJECT_ROOT"
            )
        if not library_path.is_file():
            raise PhysicalAssemblyError(f"library index missing: {library_path}")
        index = load_library_index(library_path)
        if (
            args.acceptance_profile == "phase49-work-report-15"
            and (
                index.library_id != "window-pptx-reference-work-summary-v1"
                or index.page_template_count != 15
                or index.dominant_style_cluster_id != "reference-work-summary"
            )
        ):
            raise PhysicalAssemblyError(
                "PHASE49_REFERENCE_LIBRARY_PROFILE_MISMATCH"
            )
        lookup = {template.page_id: template for template in index.page_templates}
        plan = load_assembly_plan(
            assembly_plan_path,
            lookup,
            project_root=project_root,
        )
        report = assemble_physical_deck(
            plan,
            output_path,
            library_index_sha256=hashlib.sha256(library_path.read_bytes()).hexdigest(),
            fact_store_path=fact_store_path,
            fact_store_sha256=args.fact_store_sha256,
            asset_manifest_path=asset_manifest_path,
            asset_manifest_sha256=args.asset_manifest_sha256,
            connective_copy_path=connective_copy_path,
            connective_copy_sha256=args.connective_copy_sha256,
            project_root=project_root,
            require_locked_authority=True,
            require_libreoffice=True,
            max_output_size_bytes=args.max_output_size_bytes,
            acceptance_profile=args.acceptance_profile,
            expected_slide_count=(
                15 if args.acceptance_profile == "phase49-work-report-15" else None
            ),
            library_index=index,
        )
        report_path = (
            resolve_project_file(
                args.report,
                project_root,
                label="REPORT",
                require_file=False,
            )
            if args.report
            else output_path.with_name(f"{output_path.stem}.physical-assembly-report.json")
        )
        report_digest = write_assembly_report(report, report_path)
        report_validation = validate_physical_report(report_path, project_root)
        if (
            report.status != "pass"
            or report_validation.get("status") != "pass"
            or not output_path.is_file()
        ):
            output_path.unlink(missing_ok=True)
            payload = report.to_dict()
            payload["report_digest"] = report_digest
            payload["independent_report_validation"] = report_validation
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 1
        qa_path = (
            resolve_project_file(
                args.rule_qa_report,
                project_root,
                label="RULE_QA_REPORT",
                require_file=False,
            )
            if args.rule_qa_report
            else output_path.with_name(f"{output_path.stem}.rule-qa.json")
        )
        qa = run_physical_rule_qa(output_path, plan=plan)
        qa_digest = write_rule_qa_report(qa, qa_path)
        if qa.status != "pass":
            output_path.unlink(missing_ok=True)
        payload = report.to_dict()
        payload["report_digest"] = report_digest
        payload["independent_report_validation"] = report_validation
        payload["rule_qa"] = qa.to_dict()
        payload["rule_qa_digest"] = qa_digest
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if report.status == "pass" and qa.status == "pass" else 1
    except (PageTemplateError, PhysicalAssemblyError, OSError, ValueError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
