#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import time
from typing import Dict, Iterable, List

import requests

from common import ensure_dirs, load_registry, parse_common_args


API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
API_KEY_ENV = "SEMANTIC_SCHOLAR_API_KEY"


def fetch_one(query: Dict[str, str], limit: int, api_key: str) -> Iterable[Dict]:
    response = requests.get(
        API_URL,
        params={
            "query": query["crossref"],
            "limit": str(limit),
            "fields": "title,year,venue,url,authors,citationCount,abstract,externalIds",
        },
        headers={"x-api-key": api_key, "User-Agent": "vlfm deep research bot"},
        timeout=60,
    )
    response.raise_for_status()
    for item in response.json().get("data", []):
        doi = (item.get("externalIds") or {}).get("DOI", "")
        authors = [author.get("name") for author in item.get("authors", []) if author.get("name")]
        yield {
            "retrieval_source": "semantic_scholar",
            "query_id": query["id"],
            "theme": query["theme"],
            "question": query["question"],
            "source_id": item.get("paperId"),
            "title": item.get("title"),
            "year": item.get("year"),
            "doi": doi,
            "url": item.get("url", ""),
            "authors": authors,
            "venue": item.get("venue", ""),
            "cited_by_count": item.get("citationCount"),
            "open_access": "",
            "concepts": [],
            "keywords": [],
            "abstract": item.get("abstract", "") or "",
        }
    time.sleep(0.25)


def main() -> None:
    args = parse_common_args(
        "Fetch Semantic Scholar literature records using a registry-driven query file. "
        f"Requires ${API_KEY_ENV}."
    )
    raw_dir, processed_dir = ensure_dirs(args.output_root)
    out_path = raw_dir / "semantic_scholar_works.jsonl"
    status_path = processed_dir / "semantic_scholar_status.json"
    registry = load_registry(args.registry)
    api_key = os.environ.get(API_KEY_ENV, "").strip()

    if not api_key:
        status_path.write_text(
            json.dumps(
                {
                    "enabled": False,
                    "reason": f"missing_env_{API_KEY_ENV}",
                    "out": str(out_path),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        out_path.write_text("", encoding="utf-8")
        print(
            json.dumps(
                {
                    "rows": 0,
                    "skipped": True,
                    "reason": f"missing_env_{API_KEY_ENV}",
                    "out": str(out_path),
                },
                ensure_ascii=False,
            )
        )
        return

    rows: List[Dict] = []
    error: Dict | None = None
    try:
        with out_path.open("w", encoding="utf-8") as f:
            for query in registry["queries"]:
                for row in fetch_one(query, registry["meta"]["crossref_rows"], api_key):
                    rows.append(row)
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
    except requests.HTTPError as exc:
        error = {"type": "http_error", "status": exc.response.status_code, "message": str(exc)}
    except Exception as exc:  # noqa: BLE001
        error = {"type": "runtime_error", "message": str(exc)}

    status_payload = {
        "enabled": True,
        "rows": len(rows),
        "error": error,
        "registry": str(args.registry),
        "out": str(out_path),
    }
    status_path.write_text(json.dumps(status_payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(status_payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
