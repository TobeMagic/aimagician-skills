#!/usr/bin/env python3
from __future__ import annotations

import json
import time
import xml.etree.ElementTree as ET
from typing import Dict, List
from urllib.parse import quote_plus

import requests

from common import ensure_dirs, load_registry, parse_common_args


ARXIV_API = "http://export.arxiv.org/api/query"


def text_of(node: ET.Element | None) -> str:
    return (node.text or "").strip() if node is not None else ""


def fetch_one(query: Dict[str, str], max_results: int) -> List[Dict]:
    response = requests.get(
        f"{ARXIV_API}?search_query={quote_plus(query['arxiv'])}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending",
        timeout=60,
        headers={"User-Agent": "vlfm deep research bot"},
    )
    response.raise_for_status()
    root = ET.fromstring(response.text)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    rows: List[Dict] = []
    for entry in root.findall("atom:entry", ns):
        authors = [text_of(author.find("atom:name", ns)) for author in entry.findall("atom:author", ns)]
        published = text_of(entry.find("atom:published", ns))
        rows.append(
            {
                "retrieval_source": "arxiv",
                "query_id": query["id"],
                "theme": query["theme"],
                "question": query["question"],
                "source_id": text_of(entry.find("atom:id", ns)),
                "title": text_of(entry.find("atom:title", ns)),
                "year": int(published[:4]) if published[:4].isdigit() else None,
                "doi": "",
                "url": text_of(entry.find("atom:id", ns)),
                "authors": [a for a in authors if a],
                "venue": "arXiv",
                "cited_by_count": None,
                "open_access": "preprint",
                "concepts": [],
                "keywords": [],
                "abstract": text_of(entry.find("atom:summary", ns)),
            }
        )
    time.sleep(0.5)
    return rows


def main() -> None:
    args = parse_common_args("Fetch arXiv literature records using a registry-driven query file.")
    raw_dir, _ = ensure_dirs(args.output_root)
    out_path = raw_dir / "arxiv_works.jsonl"
    registry = load_registry(args.registry)
    rows: List[Dict] = []
    with out_path.open("w", encoding="utf-8") as f:
        for query in registry["queries"]:
            for row in fetch_one(query, registry["meta"]["arxiv_max_results"]):
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
