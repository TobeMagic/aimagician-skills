#!/usr/bin/env python3
"""Lint an LLM-know-how-wiki for structure, links, index coverage, and freshness."""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path


WIKI_DIR_NAME = "LLM-know-how-wiki"
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
ALLOWED_TYPES = {
    "service",
    "architecture",
    "api",
    "project",
    "reference",
    "runbook",
    "decision",
    "digest",
    "interview",
    "index",
    "log",
}
REQUIRED_KEYS = {"title", "type", "status", "created", "updated", "tags", "sources", "confidence"}


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


def parse_frontmatter(text: str) -> tuple[dict[str, str], int]:
    if not text.startswith("---\n"):
        return {}, 0
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, 0
    block = text[4:end].splitlines()
    data: dict[str, str] = {}
    current_key: str | None = None
    for line in block:
        if not line.strip() or line.startswith("  - "):
            continue
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            current_key = key.strip()
            data[current_key] = value.strip()
        elif current_key and line.startswith(" "):
            data[current_key] += "\n" + line
    return data, end + len("\n---\n")


def extract_tags(raw: str) -> set[str]:
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        body = raw[1:-1].strip()
        if not body:
            return set()
        return {part.strip().strip('"').strip("'") for part in body.split(",") if part.strip()}
    return set()


def load_schema_tags(root: Path) -> set[str]:
    schema = root / "SCHEMA.md"
    if not schema.exists():
        return set()
    text = schema.read_text(encoding="utf-8")
    marker = "## Controlled Tags"
    if marker not in text:
        return set()
    section = text.split(marker, 1)[1]
    next_header = section.find("\n## ")
    if next_header != -1:
        section = section[:next_header]
    tags = set()
    for line in section.splitlines():
        line = line.strip()
        if line.startswith("- "):
            tags.add(line[2:].strip(" `"))
    return tags


def days_old(value: str) -> int | None:
    try:
        parsed = datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None
    return (date.today() - parsed).days


def lint(root: Path, stale_days: int, large_lines: int) -> tuple[list[str], dict[str, int]]:
    wiki = root / "wiki"
    if not wiki.is_dir():
        raise SystemExit(f"Missing wiki directory: {wiki}")

    pages = sorted(wiki.rglob("*.md"))
    index_text = (wiki / "index.md").read_text(encoding="utf-8") if (wiki / "index.md").exists() else ""
    schema_tags = load_schema_tags(root)
    findings: list[str] = []
    inbound: Counter[str] = Counter()
    outbound: defaultdict[str, list[str]] = defaultdict(list)

    for page in pages:
        rel = page.relative_to(wiki).as_posix()
        text = page.read_text(encoding="utf-8")
        fm, _ = parse_frontmatter(text)

        if not fm:
            findings.append(f"ERROR missing_frontmatter {rel}")
        else:
            missing = sorted(REQUIRED_KEYS - set(fm))
            if missing:
                findings.append(f"ERROR missing_frontmatter_keys {rel}: {', '.join(missing)}")
            page_type = fm.get("type", "").strip()
            if page_type and page_type not in ALLOWED_TYPES:
                findings.append(f"ERROR unknown_type {rel}: {page_type}")
            tags = extract_tags(fm.get("tags", ""))
            if schema_tags:
                unknown_tags = sorted(tag for tag in tags if tag not in schema_tags)
                if unknown_tags:
                    findings.append(f"WARN unknown_tags {rel}: {', '.join(unknown_tags)}")
            age = days_old(fm.get("updated", ""))
            if age is None and "updated" in fm:
                findings.append(f"WARN invalid_updated_date {rel}: {fm.get('updated')}")
            elif age is not None and age > stale_days:
                findings.append(f"WARN stale_page {rel}: updated {age} days ago")

        if rel not in {"index.md", "log.md"} and not rel.startswith("log_archive/") and f"[[{rel}]]" not in index_text:
            findings.append(f"ERROR missing_index_entry {rel}")

        line_count = text.count("\n") + 1
        if line_count > large_lines and not rel.startswith("log_archive/"):
            if rel == "log.md":
                findings.append(
                    f"WARN large_page {rel}: {line_count} lines; "
                    "run scripts/archive_log.py <wiki-root> --dry-run"
                )
            else:
                findings.append(f"WARN large_page {rel}: {line_count} lines")

        for raw in WIKILINK_RE.findall(text):
            target = raw.split("|", 1)[0].split("#", 1)[0].strip()
            if not target:
                continue
            resolved = (page.parent / target).resolve()
            outbound[rel].append(target)
            if not resolved.exists():
                findings.append(f"ERROR broken_wikilink {rel}: [[{raw}]]")
            else:
                try:
                    inbound[resolved.relative_to(wiki.resolve()).as_posix()] += 1
                except ValueError:
                    pass

    for page in pages:
        rel = page.relative_to(wiki).as_posix()
        if rel in {"index.md", "log.md", "overview.md"} or rel.startswith("log_archive/"):
            continue
        if inbound[rel] == 0:
            findings.append(f"WARN orphan_page {rel}")

    stats = {
        "pages": len(pages),
        "errors": sum(1 for item in findings if item.startswith("ERROR ")),
        "warnings": sum(1 for item in findings if item.startswith("WARN ")),
    }
    return findings, stats


def write_report(root: Path, findings: list[str], stats: dict[str, int]) -> Path:
    today = date.today().isoformat()
    report = root / "wiki" / "digest" / f"lint-{today}.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    status = "active"
    body = [
        "---",
        f"title: Lint Report {today}",
        "type: digest",
        f"status: {status}",
        f"created: {today}",
        f"updated: {today}",
        "tags: [digest, runbook]",
        "sources:",
        "  - ../index.md",
        "confidence: high",
        "---",
        "",
        f"# Lint Report - {today}",
        "",
        "## Summary",
        "",
        f"- Pages: {stats['pages']}",
        f"- Errors: {stats['errors']}",
        f"- Warnings: {stats['warnings']}",
        "",
        "## Findings",
        "",
    ]
    if findings:
        body.extend(f"- `{item}`" for item in findings)
    else:
        body.append("- No lint findings.")
    body.append("")
    report.write_text("\n".join(body), encoding="utf-8")
    return report


def append_log(root: Path, report: Path, findings: list[str]) -> None:
    log = root / "wiki" / "log.md"
    if not log.exists():
        return
    today = date.today().isoformat()
    rel_report = report.relative_to(root).as_posix()
    entry = (
        f"\n- {today} LINT\n"
        "  - sources:\n"
        "    - wiki/index.md\n"
        "    - wiki/**/*.md\n"
        "  - updated:\n"
        f"    - {rel_report}\n"
        "    - wiki/log.md\n"
        f"  - notes: Lint found {len(findings)} issue(s).\n"
    )
    with log.open("a", encoding="utf-8") as handle:
        handle.write(entry)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Wiki root path")
    parser.add_argument("--stale-days", type=int, default=180)
    parser.add_argument("--large-lines", type=int, default=350)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    root = resolve_root(args.path)
    findings, stats = lint(root, args.stale_days, args.large_lines)
    print(f"wiki_root={root}")
    print(f"pages={stats['pages']}")
    print(f"errors={stats['errors']}")
    print(f"warnings={stats['warnings']}")
    for item in findings:
        print(item)

    if args.write_report:
        report = write_report(root, findings, stats)
        append_log(root, report, findings)
        print(f"report={report}")

    return 1 if stats["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
