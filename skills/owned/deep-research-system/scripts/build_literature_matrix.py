#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

from common import ensure_dirs, first_author, normalize_title, parse_common_args


def iter_rows(paths: Iterable[Path]) -> Iterable[Dict]:
    for path in paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)


def dedupe_key(row: Dict) -> str:
    if row.get("doi"):
        return f"doi::{row['doi'].lower()}"
    if row.get("source_id") and "arxiv.org" in str(row["source_id"]):
        return f"arxiv::{row['source_id'].rstrip('/')}"
    return f"title::{normalize_title(row.get('title', ''))}"


def merge_rows(rows: Iterable[Dict]) -> List[Dict]:
    grouped: Dict[str, List[Dict]] = defaultdict(list)
    for row in rows:
        key = dedupe_key(row)
        if key.strip():
            grouped[key].append(row)

    merged: List[Dict] = []
    for key, items in grouped.items():
        items = sorted(
            items,
            key=lambda x: (
                0 if x["retrieval_source"] == "openalex" else 1 if x["retrieval_source"] == "crossref" else 2,
                -(x.get("cited_by_count") or 0),
            ),
        )
        head = items[0]
        themes = sorted({item["theme"] for item in items if item.get("theme")})
        query_ids = sorted({item["query_id"] for item in items if item.get("query_id")})
        sources = sorted({item["retrieval_source"] for item in items if item.get("retrieval_source")})
        merged.append(
            {
                "canonical_id": key,
                "title": head.get("title", ""),
                "year": head.get("year"),
                "doi": head.get("doi", ""),
                "url": head.get("url", ""),
                "first_author": first_author(head.get("authors") or []),
                "authors": head.get("authors") or [],
                "venue": head.get("venue", ""),
                "cited_by_count": head.get("cited_by_count"),
                "themes": themes,
                "query_ids": query_ids,
                "source_count": len(sources),
                "sources": sources,
                "abstract": head.get("abstract", ""),
                "keywords": head.get("keywords") or [],
            }
        )
    merged.sort(key=lambda x: ((x.get("year") or 0), (x.get("cited_by_count") or 0)), reverse=True)
    return merged


def main() -> None:
    args = parse_common_args("Build a deduplicated literature matrix from raw retrieval outputs.")
    raw_dir, processed_dir = ensure_dirs(args.output_root)
    raw_files = [
        raw_dir / "openalex_works.jsonl",
        raw_dir / "arxiv_works.jsonl",
        raw_dir / "crossref_works.jsonl",
        raw_dir / "cvf_openaccess_works.jsonl",
        raw_dir / "semantic_scholar_works.jsonl",
    ]
    rows = merge_rows(iter_rows(raw_files))

    jsonl_path = processed_dir / "literature_matrix.jsonl"
    csv_path = processed_dir / "literature_matrix.csv"
    theme_summary_path = processed_dir / "theme_summary.json"
    source_summary_path = processed_dir / "source_summary.json"

    with jsonl_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    fieldnames = [
        "canonical_id",
        "title",
        "year",
        "doi",
        "url",
        "first_author",
        "venue",
        "cited_by_count",
        "themes",
        "query_ids",
        "source_count",
        "sources",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "canonical_id": row["canonical_id"],
                    "title": row["title"],
                    "year": row["year"],
                    "doi": row["doi"],
                    "url": row["url"],
                    "first_author": row["first_author"],
                    "venue": row["venue"],
                    "cited_by_count": row["cited_by_count"],
                    "themes": "; ".join(row["themes"]),
                    "query_ids": "; ".join(row["query_ids"]),
                    "source_count": row["source_count"],
                    "sources": "; ".join(row["sources"]),
                }
            )

    theme_counter = Counter()
    source_counter = Counter()
    for row in rows:
        theme_counter.update(row["themes"])
        source_counter.update(row["sources"])

    theme_summary_path.write_text(
        json.dumps(dict(theme_counter.most_common()), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    source_summary_path.write_text(
        json.dumps(dict(source_counter.most_common()), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "rows": len(rows),
                "registry": str(args.registry),
                "out_dir": str(processed_dir),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
