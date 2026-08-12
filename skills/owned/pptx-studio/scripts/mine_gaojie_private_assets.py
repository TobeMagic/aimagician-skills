#!/usr/bin/env python3
"""Quarantine, inspect, and optionally render acquired private PPTX assets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from window_pptx.private_asset_intelligence import mine_gaojie_private_assets


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--maximum-items", type=int)
    parser.add_argument("--render-workers", type=int, default=4)
    args = parser.parse_args()
    report = mine_gaojie_private_assets(
        args.private_root,
        render=args.render,
        maximum_items=args.maximum_items,
        render_workers=args.render_workers,
    )
    print(json.dumps({
        "schema_version": report["schema_version"],
        "status": report["status"],
        "package_count": report["package_count"],
        "accepted_count": report["accepted_count"],
        "rendered_slide_count": report["rendered_slide_count"],
    }, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
