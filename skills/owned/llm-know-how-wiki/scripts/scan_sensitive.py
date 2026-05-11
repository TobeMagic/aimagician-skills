#!/usr/bin/env python3
"""Scan an LLM-know-how-wiki for obvious secret-looking strings."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


WIKI_DIR_NAME = "LLM-know-how-wiki"
TEXT_SUFFIXES = {
    ".md",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".env",
    ".ini",
    ".cfg",
    ".csv",
    ".tsv",
    ".toml",
}

PATTERNS = [
    ("password_cn", re.compile(r"密码[:：]\s*(?!(?:REDACTED|<|\*{3,}|x{3,}))[^\s,，;；]+", re.I)),
    ("password_en", re.compile(r"\bpassword\s*[:=]\s*(?!(?:REDACTED|<|\*{3,}|x{3,}))[^\s,;]+", re.I)),
    ("token_assignment", re.compile(r"\b(api[_-]?key|access[_-]?token|auth[_-]?token|secret[_-]?key)\s*[:=]\s*(?!(?:REDACTED|<|\*{3,}|x{3,}))[A-Za-z0-9_./+=:@-]{12,}", re.I)),
    ("bearer_token", re.compile(r"\bBearer\s+[A-Za-z0-9_./+=-]{20,}", re.I)),
    ("openai_style_key", re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}")),
    ("aws_access_key", re.compile(r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("cookie_assignment", re.compile(r"\bcookie\s*[:=]\s*(?!(?:REDACTED|<|\*{3,}|x{3,}))[^\s;]{20,}", re.I)),
    ("feishu_authcode_url", re.compile(r"authcode/\?code=(?!REDACTED)[A-Za-z0-9_-]+", re.I)),
]


def find_wiki_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate_parent in [current, *current.parents]:
        candidate = candidate_parent / WIKI_DIR_NAME
        if candidate.is_dir():
            return candidate
    return None


def resolve_root(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    found = find_wiki_root(Path.cwd())
    if found:
        return found
    raise SystemExit("No LLM-know-how-wiki found. Pass the wiki root path explicitly.")


def should_scan(path: Path) -> bool:
    if path.name.startswith("."):
        return False
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True
    if path.suffix == "":
        return True
    return False


def scan(root: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or not should_scan(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            for name, pattern in PATTERNS:
                if pattern.search(line):
                    findings.append(
                        {
                            "path": str(path.relative_to(root)),
                            "line": line_no,
                            "pattern": name,
                            "preview": line.strip()[:220],
                        }
                    )
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Wiki root path")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    root = resolve_root(args.path)
    findings = scan(root)

    if args.json:
        print(json.dumps({"wiki_root": str(root), "findings": findings}, ensure_ascii=False, indent=2))
    else:
        print(f"wiki_root={root}")
        print(f"findings={len(findings)}")
        for item in findings:
            print(f"{item['path']}:{item['line']} {item['pattern']} {item['preview']}")

    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
