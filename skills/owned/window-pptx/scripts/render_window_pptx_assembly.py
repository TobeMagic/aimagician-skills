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
    PhysicalAssemblyError,
    assemble_physical_deck,
    load_assembly_plan,
    write_assembly_report,
)
from window_pptx.physical_rule_qa import (  # noqa: E402
    run_physical_rule_qa,
    write_rule_qa_report,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assembly-plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--library", type=Path)
    parser.add_argument("--private-root", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--rule-qa-report", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        private_root = resolve_private_root(explicit=args.private_root)
        library_path = (
            args.library.expanduser().resolve(strict=False)
            if args.library
            else private_root / "v61" / "library-v4.json"
        )
        if not library_path.is_file():
            raise PhysicalAssemblyError(f"library index missing: {library_path}")
        index = load_library_index(library_path)
        lookup = {template.page_id: template for template in index.page_templates}
        plan = load_assembly_plan(args.assembly_plan, lookup)
        report = assemble_physical_deck(
            plan,
            args.output,
            library_index_sha256=hashlib.sha256(library_path.read_bytes()).hexdigest(),
        )
        report_path = (
            args.report
            if args.report
            else args.output.with_name(f"{args.output.stem}.physical-assembly-report.json")
        )
        report_digest = write_assembly_report(report, report_path)
        qa_path = (
            args.rule_qa_report
            if args.rule_qa_report
            else args.output.with_name(f"{args.output.stem}.rule-qa.json")
        )
        qa = run_physical_rule_qa(args.output, plan=plan)
        qa_digest = write_rule_qa_report(qa, qa_path)
        payload = report.to_dict()
        payload["report_digest"] = report_digest
        payload["rule_qa"] = qa.to_dict()
        payload["rule_qa_digest"] = qa_digest
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0 if report.status == "pass" and qa.status == "pass" else 1
    except (PageTemplateError, PhysicalAssemblyError, OSError, ValueError) as exc:
        print(json.dumps({"status": "fail", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
