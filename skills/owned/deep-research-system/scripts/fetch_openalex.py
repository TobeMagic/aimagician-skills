#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from typing import Dict, Iterable, List

import requests

from common import ensure_dirs, load_registry, parse_common_args


OPENALEX_BASE = "https://api.openalex.org"
USER_AGENT = "vlfm deep research bot (mailto:research@example.com)"


def reconstruct_abstract(index: Dict[str, List[int]] | None) -> str:
    if not index:
        return ""
    position_to_word: Dict[int, str] = {}
    for word, positions in index.items():
        for pos in positions:
            position_to_word[pos] = word
    return " ".join(position_to_word[pos] for pos in sorted(position_to_word))


def fetch_one(query: Dict[str, str], meta: Dict[str, int]) -> Iterable[Dict]:
    for page in range(1, meta["openalex_pages"] + 1):
        response = requests.get(
            f"{OPENALEX_BASE}/works",
            params={
                "search": query["openalex"],
                "filter": (
                    f"from_publication_date:{meta['from_year']}-01-01,"
                    f"to_publication_date:{meta['to_year']}-12-31"
                ),
                "sort": "cited_by_count:desc",
                "per-page": str(meta["openalex_per_query"]),
                "page": str(page),
                "select": ",".join(
                    [
                        "id",
                        "doi",
                        "title",
                        "publication_year",
                        "cited_by_count",
                        "authorships",
                        "primary_location",
                        "open_access",
                        "concepts",
                        "keywords",
                        "abstract_inverted_index",
                    ]
                ),
            },
            headers={"User-Agent": USER_AGENT},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.json()
        for item in payload.get("results", []):
            primary = item.get("primary_location") or {}
            source = primary.get("source") or {}
            yield {
                "retrieval_source": "openalex",
                "query_id": query["id"],
                "theme": query["theme"],
                "question": query["question"],
                "source_id": item.get("id"),
                "title": item.get("title"),
                "year": item.get("publication_year"),
                "doi": item.get("doi"),
                "url": primary.get("landing_page_url") or item.get("id"),
                "authors": [
                    auth.get("author", {}).get("display_name")
                    for auth in item.get("authorships", [])
                    if auth.get("author", {}).get("display_name")
                ],
                "venue": source.get("display_name"),
                "cited_by_count": item.get("cited_by_count"),
                "open_access": (item.get("open_access") or {}).get("oa_status"),
                "concepts": [c.get("display_name") for c in item.get("concepts", []) if c.get("display_name")][:8],
                "keywords": [k.get("display_name") for k in item.get("keywords", []) if k.get("display_name")][:8],
                "abstract": reconstruct_abstract(item.get("abstract_inverted_index")),
            }
        time.sleep(0.25)


def main() -> None:
    args = parse_common_args("Fetch OpenAlex literature records using a registry-driven query file.")
    raw_dir, _ = ensure_dirs(args.output_root)
    out_path = raw_dir / "openalex_works.jsonl"
    registry = load_registry(args.registry)
    rows: List[Dict] = []
    with out_path.open("w", encoding="utf-8") as f:
        for query in registry["queries"]:
            for row in fetch_one(query, registry["meta"]):
                rows.append(row)
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(
        json.dumps(
            {"rows": len(rows), "registry": str(args.registry), "out": str(out_path)},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
