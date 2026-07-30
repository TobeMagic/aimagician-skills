#!/usr/bin/env python3
"""Collect the private Gaojie rendered-page quality band for visual review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from window_pptx.private_asset_intelligence import (
    collect_gaojie_quality_band_candidates,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--minimum-quality", type=float, default=0.65)
    parser.add_argument("--maximum-quality", type=float, default=0.75)
    args = parser.parse_args()
    report = collect_gaojie_quality_band_candidates(
        args.private_root,
        minimum_quality=args.minimum_quality,
        maximum_quality=args.maximum_quality,
    )
    print(json.dumps({
        "schema_version": report["schema_version"],
        "status": report["status"],
        "minimum_quality_inclusive": report["minimum_quality_inclusive"],
        "maximum_quality_exclusive": report["maximum_quality_exclusive"],
        "candidate_page_count": report["candidate_page_count"],
    }, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
