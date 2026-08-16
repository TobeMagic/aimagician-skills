#!/usr/bin/env python3
"""Run deterministic rule QA for a v6.1 physical assembly output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from window_pptx.page_template_library import load_library_index
from window_pptx.physical_assembly import load_assembly_plan
from window_pptx.physical_rule_qa import run_physical_rule_qa, write_rule_qa_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pptx", required=True, type=Path)
    parser.add_argument("--assembly-plan", required=True, type=Path)
    parser.add_argument("--library", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    index = load_library_index(args.library)
    plan = load_assembly_plan(args.assembly_plan, {item.page_id: item for item in index.page_templates})
    report = run_physical_rule_qa(args.pptx, plan=plan)
    payload = report.to_dict()
    if args.report:
        payload["report_digest"] = write_rule_qa_report(report, args.report)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if report.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
