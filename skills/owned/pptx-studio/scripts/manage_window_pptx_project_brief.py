#!/usr/bin/env python3
"""Validate, discuss, and lock Window-PPTX ProjectBriefPack v1 files."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Sequence

from window_pptx.project_brief import (
    BriefLockError,
    BriefValidationError,
    lock_project_brief_pack,
    prepare_formal_brief,
    validate_project_brief_pack,
)


def _read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BriefValidationError("BRIEF_INPUT_UNREADABLE") from exc
    if not isinstance(payload, dict):
        raise BriefValidationError("BRIEF_OBJECT_REQUIRED")
    return payload


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def _question_payload(validated: Any) -> list[dict[str, str]]:
    return [
        {"code": item.code, "path": item.path, "prompt": item.prompt}
        for item in validated.questions
    ]


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Manage discussion-locked Window-PPTX project briefs."
    )
    parser.add_argument(
        "command",
        choices=("validate", "lock", "formal-check"),
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.command == "lock" and args.output is None:
        parser.error("lock requires --output")
    if args.command != "lock" and args.output is not None:
        parser.error("--output is only valid with lock")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        payload = _read_json(args.input)
        if args.command == "lock":
            locked = lock_project_brief_pack(payload)
            assert args.output is not None
            _write_json_atomic(args.output, locked)
            _emit(
                {
                    "schema_version": "1.0",
                    "status": "LOCKED",
                    "brief_id": locked["brief_id"],
                    "lock_sha256": locked["lock_sha256"],
                    "output": str(args.output),
                }
            )
            return 0
        if args.command == "formal-check":
            validated = prepare_formal_brief(payload)
            _emit(
                {
                    "schema_version": "1.0",
                    "status": "PASS",
                    "brief_id": validated.brief_id,
                    "formal_ready": True,
                    "lock_sha256": validated.lock_sha256,
                }
            )
            return 0

        validated = validate_project_brief_pack(payload)
        status = "VALID" if not validated.questions else "NEEDS_DISCUSSION"
        _emit(
            {
                "schema_version": "1.0",
                "status": status,
                "brief_id": validated.brief_id,
                "state": validated.state.value,
                "formal_ready": validated.formal_ready,
                "lock_sha256": validated.lock_sha256,
                "questions": _question_payload(validated),
            }
        )
        return 0 if not validated.questions else 1
    except BriefLockError as exc:
        _emit(
            {
                "schema_version": "1.0",
                "status": "LOCK_ERROR",
                "code": str(exc).split(":", 1)[0],
            }
        )
        return 2
    except BriefValidationError as exc:
        _emit(
            {
                "schema_version": "1.0",
                "status": "INVALID",
                "code": str(exc).split(":", 1)[0],
            }
        )
        return 2
    except OSError:
        _emit(
            {
                "schema_version": "1.0",
                "status": "IO_ERROR",
                "code": "BRIEF_OUTPUT_UNWRITABLE",
            }
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
