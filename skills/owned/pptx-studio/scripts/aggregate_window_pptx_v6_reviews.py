#!/usr/bin/env python3
"""Aggregate three fresh-context v6 visual-review reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from window_pptx.v6_blind_acceptance import aggregate_v6_blind_reviews


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", action="append", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reports = [json.loads(path.read_text(encoding="utf-8")) for path in args.review]
    aggregate = aggregate_v6_blind_reviews(reports)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(aggregate, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(aggregate, ensure_ascii=False, indent=2))
    return 0 if aggregate["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
