#!/usr/bin/env python3
"""Run three isolated Phase 49 reference/candidate visual blind reviews."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from window_pptx.v61_blind_reviews import (  # noqa: E402
    BlindReviewError,
    dry_run_plan,
    load_packet,
    prepare_output_root,
    run_review_matrix,
    sha256_bytes,
    write_json,
    write_not_run_report,
)


DEFAULT_PACKET_SCHEMA = (
    SKILL_ROOT / "schemas" / "phase49-blind-review-packet.v1.schema.json"
)
DEFAULT_RUBRIC = SKILL_ROOT / "references" / "v61-blind-review-rubric.md"
DEFAULT_ANALYZER = Path(
    "/home/aimagician/.codex/skills/vision-analysis/scripts/analyze.mjs"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument(
        "--allow-external-upload",
        action="store_true",
        help="Explicitly authorize all eight packet pair images for Agnes upload.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and hash the packet, then emit a six-vision/three-synthesis plan.",
    )
    parser.add_argument("--node-bin", default="node", help=argparse.SUPPRESS)
    parser.add_argument("--analyzer", type=Path, default=DEFAULT_ANALYZER, help=argparse.SUPPRESS)
    parser.add_argument("--codex-bin", default="codex", help=argparse.SUPPRESS)
    parser.add_argument("--vision-timeout-seconds", type=int, default=300)
    parser.add_argument("--synthesis-timeout-seconds", type=int, default=600)
    return parser


def _print(value: object) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    packet_root = args.packet_root.expanduser().resolve()
    requested_output = args.output_dir.expanduser().resolve()
    if requested_output.is_relative_to(packet_root) or packet_root.is_relative_to(
        requested_output
    ):
        error = BlindReviewError(
            "ROOTS_NOT_DISJOINT", "packet and reviewer output roots must be disjoint"
        )
        _print({"status": "NOT_RUN", "failure_reason": error.failure_reason})
        return 2
    try:
        output_root = prepare_output_root(requested_output)
    except BlindReviewError as error:
        _print({"status": "NOT_RUN", "failure_reason": error.failure_reason})
        return 2

    packet_sha256: str | None = None
    rubric_sha256: str | None = None
    try:
        packet = load_packet(packet_root, schema_path=DEFAULT_PACKET_SCHEMA)
        packet_sha256 = packet.packet_sha256
        if DEFAULT_RUBRIC.is_symlink() or not DEFAULT_RUBRIC.is_file():
            raise BlindReviewError("RUBRIC_MISSING", "fixed blind-review rubric is missing")
        rubric_sha256 = sha256_bytes(DEFAULT_RUBRIC.read_bytes())

        if args.dry_run:
            plan = dry_run_plan(
                packet=packet,
                rubric_sha256=rubric_sha256,
                output_dir=output_root,
            )
            write_json(output_root / "dry-run-plan.json", plan)
            _print(plan)
            return 0
        if not args.allow_external_upload:
            raise BlindReviewError(
                "UPLOAD_AUTHORIZATION_REQUIRED",
                "production review requires --allow-external-upload",
            )
        report = run_review_matrix(
            packet=packet,
            output_dir=output_root,
            rubric_path=DEFAULT_RUBRIC,
            node_executable=args.node_bin,
            analyzer_path=args.analyzer,
            codex_executable=args.codex_bin,
            vision_timeout_seconds=args.vision_timeout_seconds,
            synthesis_timeout_seconds=args.synthesis_timeout_seconds,
        )
        _print(report)
        return 0 if report["status"] == "PASS" else 1
    except BlindReviewError as error:
        report = write_not_run_report(
            output_root,
            error=error,
            packet_sha256=packet_sha256,
            rubric_sha256=rubric_sha256,
        )
        _print(report)
        return 2
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        bounded = BlindReviewError(
            "CONTROLLER_IO_FAILED", "blind-review controller could not read or write evidence"
        )
        report = write_not_run_report(
            output_root,
            error=bounded,
            packet_sha256=packet_sha256,
            rubric_sha256=rubric_sha256,
        )
        _print(report)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
