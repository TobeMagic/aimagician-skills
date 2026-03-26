#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from typing import Dict, Iterable, List

import requests

from common import ensure_dirs, load_registry, parse_common_args


CROSSREF_API = "https://api.crossref.org/works"
USER_AGENT = "vlfm deep research bot (mailto:research@example.com)"


def fetch_one(query: Dict[str, str], meta: Dict[str, int]) -> Iterable[Dict]:
    response = requests.get(
        CROSSREF_API,
        params={
            "query.bibliographic": query["crossref"],
            "rows": str(meta["crossref_rows"]),
            "sort": "relevance",
            "filter": (
                f"from-pub-date:{meta['from_year']}-01-01,"
                f"until-pub-date:{meta['to_year']}-12-31"
            ),
        },
        headers={"User-Agent": USER_AGENT},
        timeout=60,
    )
    response.raise_for_status()
    for item in response.json().get("message", {}).get("items", []):
        issued = item.get("issued", {}).get("date-parts", [[None]])
        year = issued[0][0]
        authors = []
        for author in item.get("author", []):
            parts = [author.get("given", ""), author.get("family", "")]
            name = " ".join(p for p in parts if p).strip()
            if name:
                authors.append(name)
        yield {
            "retrieval_source": "crossref",
            "query_id": query["id"],
            "theme": query["theme"],
            "question": query["question"],
            "source_id": item.get("DOI"),
            "title": (item.get("title") or [""])[0],
            "year": year,
            "doi": item.get("DOI"),
            "url": item.get("URL"),
            "authors": authors,
            "venue": (item.get("container-title") or [""])[0],
            "cited_by_count": item.get("is-referenced-by-count"),
            "open_access": "",
            "concepts": [],
            "keywords": item.get("subject", [])[:8],
            "abstract": item.get("abstract", "") or ""
        }
    time.sleep(0.25)


def main() -> None:
    args = parse_common_args("Fetch Crossref literature records using a registry-driven query file.")
    raw_dir, _ = ensure_dirs(args.output_root)
    out_path = raw_dir / "crossref_works.jsonl"
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
