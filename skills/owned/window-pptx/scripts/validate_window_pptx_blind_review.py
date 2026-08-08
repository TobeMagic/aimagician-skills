#!/usr/bin/env python3
"""Validate a completed human Window-PPTX blind review and emit its release gate."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from window_pptx.benchmark import (
    BENCHMARK_SCHEMA_VERSION,
    evaluate_blind_review_gate,
    load_blind_review_packet,
    load_blind_review_score_sheet,
)


def _atomic_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            json.dump(
                value,
                handle,
                ensure_ascii=False,
                sort_keys=True,
                indent=2,
                allow_nan=False,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _file_sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _reason_code(detail: str) -> str:
    lowered = detail.casefold()
    if "artifact" in lowered or "pptx and png" in lowered:
        return "ARTIFACT_VERIFICATION_FAILED"
    if "score" in lowered or "reviewer_id" in lowered or "entries mismatch" in lowered:
        return "INCOMPLETE_OR_INVALID_SCORE_SHEET"
    if "packet" in lowered:
        return "PACKET_INVALID"
    return "INPUT_INVALID"


def _reported_threshold(value: float) -> float | str:
    return value if math.isfinite(value) else repr(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Verify the frozen blind packet and completed human scores, then "
            "apply the locked v5.1 release floor."
        )
    )
    parser.add_argument("--packet", type=Path, required=True)
    parser.add_argument("--score-sheet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--overall-threshold", type=float, default=4.2)
    parser.add_argument("--dimension-threshold", type=float, default=4.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        packet_value = _read_json(args.packet)
        packet = load_blind_review_packet(
            packet_value,
            review_root=args.packet.resolve().parent,
        )
        score_value = _read_json(args.score_sheet)
        sheet = load_blind_review_score_sheet(packet, score_value)
        report = evaluate_blind_review_gate(
            packet,
            sheet,
            overall_threshold=args.overall_threshold,
            dimension_threshold=args.dimension_threshold,
        )
        document = report.to_dict()
        document["gate_id"] = "P35-BLIND-01-SCORE-FLOOR"
        document["score_source"] = "submitted-score-sheet"
        document["human_provenance_status"] = "EXTERNAL_CONFIRMATION_REQUIRED"
        document["milestone_gate_status"] = "NOT_RUN"
        document["score_sheet_file_sha256"] = _file_sha256(args.score_sheet)
        _atomic_json(args.output, document)
        print(
            f"P35-BLIND-01-SCORE-FLOOR {report.status}: "
            f"overall={report.overall_mean:.3f}; human provenance must be "
            f"confirmed externally; report={args.output}"
        )
        return 0 if report.status == "PASS" else 1
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        detail = str(exc) or exc.__class__.__name__
        document = {
            "schema_version": BENCHMARK_SCHEMA_VERSION,
            "gate_id": "P35-BLIND-01-SCORE-FLOOR",
            "status": "NOT_RUN",
            "score_source": "submitted-score-sheet",
            "human_provenance_status": "EXTERNAL_CONFIRMATION_REQUIRED",
            "milestone_gate_status": "NOT_RUN",
            "reason_code": _reason_code(detail),
            "detail": detail,
            "score_sheet_file_sha256": _file_sha256(args.score_sheet),
            "thresholds": {
                "overall_mean": _reported_threshold(args.overall_threshold),
                "dimension_mean": _reported_threshold(args.dimension_threshold),
            },
        }
        _atomic_json(args.output, document)
        print(
            f"P35-BLIND-01-SCORE-FLOOR NOT_RUN: {detail}; "
            f"report={args.output}",
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
