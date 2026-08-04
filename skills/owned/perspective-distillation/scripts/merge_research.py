#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path

STREAMS = {
    "01-writings": "authored-work",
    "02-conversations": "conversations",
    "03-expression-dna": "expression",
    "04-external-views": "external-views",
    "05-decisions": "decisions",
    "06-timeline": "timeline",
}


def inspect_file(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    urls = set(re.findall(r"https?://[^\s)>\]]+", content))
    primary = len(re.findall(r"\bprimary\b|一手|原文|原始", content, re.I))
    secondary = len(re.findall(r"\bsecondary\b|二手|转述|评论", content, re.I))
    contradictions = len(re.findall(r"contradiction|conflict|however|矛盾|相反|争议", content, re.I))
    headings = re.findall(r"^##+\s+(.+)$", content, re.M)[:3]
    return {
        "present": True,
        "unique_urls": len(urls),
        "primary_markers": primary,
        "secondary_markers": secondary,
        "contradiction_markers": contradictions,
        "headings": headings,
    }


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: merge_research.py <perspective-skill-root>", file=sys.stderr)
        raise SystemExit(2)
    root = Path(sys.argv[1]).resolve()
    research = root / "references" / "research"
    report = {"root": str(root), "streams": {}, "missing": []}
    for stem, label in STREAMS.items():
        path = research / f"{stem}.md"
        if path.is_file():
            report["streams"][label] = inspect_file(path)
        else:
            report["streams"][label] = {"present": False}
            report["missing"].append(label)
    report["status"] = "pass" if not report["missing"] else "incomplete"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
