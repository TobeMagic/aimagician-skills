#!/usr/bin/env python3

import json
import re
import sys
from pathlib import Path


def section(content: str, names: str) -> str:
    match = re.search(rf"^##\s+.*(?:{names}).*$([\s\S]*?)(?=^##\s|\Z)", content, re.I | re.M)
    return match.group(1) if match else ""


def result(name: str, passed: bool, detail: str) -> dict:
    return {"name": name, "status": "pass" if passed else "fail", "detail": detail}


def audit(path: Path) -> dict:
    content = path.read_text(encoding="utf-8")
    model_block = section(content, r"mental models?|心智模型")
    model_count = len(re.findall(r"^###\s+", model_block, re.M))
    boundary_block = section(content, r"honest boundar|诚实边界|limitations?")
    boundary_count = len(re.findall(r"^[-*]\s+", boundary_block, re.M))
    style_block = section(content, r"expression|voice|表达")
    style_markers = len(re.findall(r"sentence|vocabulary|certainty|humou?r|rhythm|句式|词汇|语气|幽默|节奏", style_block, re.I))
    tension_count = len(re.findall(r"tension|contradiction|paradox|张力|矛盾", content, re.I))
    evidence_markers = len(re.findall(r"evidence|source|primary|secondary|来源|一手|二手", content, re.I))
    forbidden = re.findall(r"npx skills add|github\.com/[^\s)]+|twitter|wechat|公众号|创建者", content, re.I)

    checks = [
        result("mental-model-count", 3 <= model_count <= 7, f"{model_count} models"),
        result("honest-boundaries", boundary_count >= 3, f"{boundary_count} list items"),
        result("expression-constraints", style_markers >= 3, f"{style_markers} markers"),
        result("tensions", tension_count >= 2, f"{tension_count} markers"),
        result("evidence-contract", evidence_markers >= 4, f"{evidence_markers} markers"),
        result("runtime-neutrality", len(forbidden) == 0, f"{len(forbidden)} forbidden matches"),
    ]
    return {
        "skill": str(path.resolve()),
        "status": "pass" if all(item["status"] == "pass" for item in checks) else "fail",
        "checks": checks,
    }


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: quality_check.py <SKILL.md>", file=sys.stderr)
        raise SystemExit(2)
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f"SKILL.md not found: {path}", file=sys.stderr)
        raise SystemExit(2)
    report = audit(path)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    raise SystemExit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
