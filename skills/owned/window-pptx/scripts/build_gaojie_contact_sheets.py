#!/usr/bin/env python3
"""Build private labeled Gaojie contact sheets from completed selections."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from window_pptx.gaojie_contact_sheets import build_gaojie_contact_sheets


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--columns", type=int, default=3)
    args = parser.parse_args()
    report = build_gaojie_contact_sheets(
        args.private_root,
        columns=args.columns,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
