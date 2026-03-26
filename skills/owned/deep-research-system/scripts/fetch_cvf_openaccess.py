#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import time
from typing import Dict, Iterable, List, Set

import requests

from common import ensure_dirs, load_registry, parse_common_args


CONFERENCE_URLS = [
    "https://openaccess.thecvf.com/CVPR2025?day=all",
    "https://openaccess.thecvf.com/ICCV2025?day=all",
    "https://openaccess.thecvf.com/CVPR2024?day=all",
    "https://openaccess.thecvf.com/ICCV2023?day=all",
]

STOPWORDS = {
    "and",
    "for",
    "with",
    "from",
    "into",
    "using",
    "object",
    "robot",
    "robots",
    "navigation",
    "vision",
    "language",
    "model",
    "models",
    "indoor",
    "semantic",
    "embodied",
    "benchmark",
}


def keyword_pool(query: Dict[str, str]) -> Set[str]:
    text = " ".join([query.get("openalex", ""), query.get("crossref", ""), query.get("theme", "")]).lower()
    tokens = re.findall(r"[a-z0-9][a-z0-9\\-]+", text)
    return {token for token in tokens if len(token) >= 4 and token not in STOPWORDS}


def title_matches(title: str, keywords: Set[str]) -> bool:
    low = title.lower()
    return any(keyword in low for keyword in keywords)


def parse_entries(page_url: str, html_text: str, queries: List[Dict[str, str]]) -> Iterable[Dict]:
    blocks = re.findall(
        r'<dt class="ptitle">.*?<a href="(?P<href>[^"]+)">(?P<title>.*?)</a></dt>',
        html_text,
        re.S,
    )
    conference = page_url.split("/")[-1].split("?")[0]
    query_keywords = {query["id"]: keyword_pool(query) for query in queries}
    seen: Set[tuple[str, str]] = set()
    for href, raw_title in blocks:
        title = html.unescape(re.sub(r"<.*?>", "", raw_title)).strip()
        if not title:
            continue
        matched_queries = [query for query in queries if title_matches(title, query_keywords[query["id"]])]
        if not matched_queries:
            continue
        for query in matched_queries:
            key = (query["id"], title)
            if key in seen:
                continue
            seen.add(key)
            yield {
                "retrieval_source": "cvf_openaccess",
                "query_id": query["id"],
                "theme": query["theme"],
                "question": query["question"],
                "source_id": href,
                "title": title,
                "year": int(re.search(r"(20\\d{2})", conference).group(1)) if re.search(r"(20\\d{2})", conference) else None,
                "doi": "",
                "url": f"https://openaccess.thecvf.com{href}",
                "authors": [],
                "venue": conference,
                "cited_by_count": None,
                "open_access": "openaccess",
                "concepts": [],
                "keywords": [],
                "abstract": "",
            }


def main() -> None:
    args = parse_common_args("Fetch keyword-filtered papers from CVF Open Access conference index pages.")
    raw_dir, processed_dir = ensure_dirs(args.output_root)
    out_path = raw_dir / "cvf_openaccess_works.jsonl"
    status_path = processed_dir / "cvf_openaccess_status.json"
    registry = load_registry(args.registry)

    rows: List[Dict] = []
    errors: List[Dict] = []
    with out_path.open("w", encoding="utf-8") as f:
        for url in CONFERENCE_URLS:
            try:
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
                response.raise_for_status()
                for row in parse_entries(url, response.text, registry["queries"]):
                    rows.append(row)
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
            except Exception as exc:  # noqa: BLE001
                errors.append({"url": url, "message": str(exc)})
            time.sleep(0.25)

    payload = {
        "rows": len(rows),
        "errors": errors,
        "registry": str(args.registry),
        "out": str(out_path),
    }
    status_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    main()
