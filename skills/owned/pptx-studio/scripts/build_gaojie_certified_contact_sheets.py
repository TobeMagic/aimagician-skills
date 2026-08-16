#!/usr/bin/env python3
"""Build full-coverage private contact sheets for the certified Gaojie core."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from window_pptx.gaojie_contact_sheets import (
    build_certified_core_contact_sheets,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--columns", type=int, default=4)
    parser.add_argument(
        "--input",
        choices=("certified-core", "supplement-candidates"),
        default="certified-core",
    )
    parser.add_argument(
        "--pool-scope",
        choices=("all", "direct-use", "reference-only"),
        default="all",
    )
    args = parser.parse_args()
    report_path = (
        args.private_root
        / "intelligence"
        / "gaojie"
        / f"{args.input}.json"
    )
    try:
        core = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit("certified core is missing or unreadable") from exc
    pages = core.get("pages")
    if not isinstance(pages, list):
        raise SystemExit("certified core pages are missing")
    if args.pool_scope == "direct-use":
        pages = [
            page
            for page in pages
            if not str(page.get("pool", "")).startswith("reference-only/")
        ]
    elif args.pool_scope == "reference-only":
        pages = [
            page
            for page in pages
            if str(page.get("pool", "")).startswith("reference-only/")
        ]
    output_label = (
        f"{args.input}-full"
        if args.pool_scope == "all"
        else f"{args.input}-{args.pool_scope}"
    )
    report = build_certified_core_contact_sheets(
        args.private_root,
        pages=pages,
        batch_size=args.batch_size,
        columns=args.columns,
        output_label=output_label,
    )
    print(json.dumps({
        "schema_version": report["schema_version"],
        "status": report["status"],
        "source_page_count": report["source_page_count"],
        "covered_page_count": report["covered_page_count"],
        "sheet_count": report["sheet_count"],
    }, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
