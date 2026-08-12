#!/usr/bin/env python3
"""Certify the bounded private Gaojie slide core."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from window_pptx.private_asset_intelligence import certify_gaojie_core


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--maximum-pages", type=int, default=500)
    parser.add_argument("--multi-page-limit", type=int, default=155)
    parser.add_argument("--minimum-render-quality", type=float, default=0.75)
    parser.add_argument("--disposition", type=Path)
    parser.add_argument("--supplement-report", type=Path)
    parser.add_argument("--supplement-disposition", type=Path)
    parser.add_argument("--final-visual-overrides", type=Path)
    parser.add_argument("--near-duplicate-distance", type=float, default=0.03)
    args = parser.parse_args()
    report = certify_gaojie_core(
        args.private_root,
        maximum_pages=args.maximum_pages,
        multi_page_limit=args.multi_page_limit,
        minimum_render_quality=args.minimum_render_quality,
        disposition_path=args.disposition,
        supplement_report_path=args.supplement_report,
        supplement_disposition_path=args.supplement_disposition,
        final_visual_overrides_path=args.final_visual_overrides,
        near_duplicate_distance=args.near_duplicate_distance,
    )
    print(json.dumps({
        "schema_version": report["schema_version"],
        "status": report["status"],
        "rendered_slide_count": report["rendered_slide_count"],
        "single_page_core_count": report["single_page_core_count"],
        "multi_page_candidate_count": report["multi_page_candidate_count"],
        "multi_page_selected_count": report["multi_page_selected_count"],
        "certified_page_count": report["certified_page_count"],
        "reviewed_candidate_count": report["reviewed_candidate_count"],
        "target_shortfall": report["target_shortfall"],
        "layout_page_count": report["layout_page_count"],
        "support_page_count": report["support_page_count"],
        "denied_page_count": report["denied_page_count"],
        "supplement_page_count": report["supplement_page_count"],
    }, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
