#!/usr/bin/env python3
"""Materialize the canonical Window-PPTX v6 brief corpus as locked JSON."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path
from typing import Any, Sequence

from window_pptx.project_brief_corpus import load_project_brief_corpus


def _write_atomic(path: Path, payload: dict[str, Any]) -> None:
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


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export all canonical locked ProjectBriefPack corpus files."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--replace",
        action="store_true",
        help="replace existing scenario JSON files in the output directory",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    corpus = load_project_brief_corpus()
    targets = {
        scenario_id: output_dir / f"{scenario_id}.project-brief-pack.v1.json"
        for scenario_id in corpus
    }
    existing = sorted(path for path in targets.values() if path.exists())
    if existing and not args.replace:
        print(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "status": "REFUSED",
                    "code": "OUTPUT_EXISTS",
                    "existing_count": len(existing),
                },
                indent=2,
            )
        )
        return 2
    for scenario_id, path in targets.items():
        _write_atomic(path, corpus[scenario_id])
    print(
        json.dumps(
            {
                "schema_version": "1.0",
                "status": "PASS",
                "count": len(targets),
                "output_dir": str(output_dir),
                "files": [path.name for path in targets.values()],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
