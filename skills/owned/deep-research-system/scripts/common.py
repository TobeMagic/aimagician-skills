#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "queries" / "query_registry.json"


def parse_common_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--registry",
        type=Path,
        default=DEFAULT_REGISTRY,
        help="Path to a query registry JSON.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=ROOT,
        help="Output root containing raw/ and processed/ directories.",
    )
    return parser.parse_args()


def ensure_dirs(output_root: Path) -> tuple[Path, Path]:
    raw_dir = output_root / "raw"
    processed_dir = output_root / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir, processed_dir


def load_registry(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_title(title: str) -> str:
    title = title or ""
    title = title.casefold()
    title = re.sub(r"[^a-z0-9]+", " ", title)
    return re.sub(r"\s+", " ", title).strip()


def first_author(authors: list[str]) -> str:
    return authors[0] if authors else ""
