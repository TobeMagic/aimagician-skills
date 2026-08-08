#!/usr/bin/env python3
"""Aggregate the frozen Window-PPTX v6.1 blind-review evidence matrix."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

from window_pptx.v61_blind_acceptance import (
    aggregate_v61_blind_acceptance,
    load_hashed_document,
)


def _sha256_arg(value: str) -> str:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise argparse.ArgumentTypeError("must be a 64-character lowercase SHA-256")
    return value


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Recompute PASS/FAIL/NOT_RUN from six Agnes segments and three "
            "fresh-context reviewer syntheses."
        )
    )
    parser.add_argument(
        "--segment",
        action="append",
        default=[],
        type=Path,
        help="v61-visual-segment.v1 JSON; provide exactly six",
    )
    parser.add_argument(
        "--review",
        action="append",
        default=[],
        type=Path,
        help="v61-blind-review.v1 JSON; provide exactly three",
    )
    parser.add_argument("--packet-sha256", required=True, type=_sha256_arg)
    parser.add_argument("--rubric-sha256", required=True, type=_sha256_arg)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def _load_available(paths: list[Path], kind: str):
    documents = []
    for path in paths:
        try:
            documents.append(load_hashed_document(path))
        except ValueError as exc:
            print(f"{kind} input unavailable: {exc}", file=sys.stderr)
    return documents


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        + "\n"
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    aggregate = aggregate_v61_blind_acceptance(
        _load_available(args.segment, "segment"),
        _load_available(args.review, "review"),
        expected_packet_sha256=args.packet_sha256,
        expected_rubric_sha256=args.rubric_sha256,
    )
    _atomic_json(args.output, aggregate)
    print(json.dumps(aggregate, ensure_ascii=False, indent=2, sort_keys=True))
    return {"PASS": 0, "FAIL": 1, "NOT_RUN": 2}[aggregate["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
