#!/usr/bin/env python3
"""Archive old wiki/log.md entries into wiki/log_archive/YYYY.md files."""

from __future__ import annotations

import argparse
import os
import re
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path


WIKI_DIR_NAME = "LLM-know-how-wiki"
ENTRY_START_RE = re.compile(r"^- (?:(\d{4})-\d{2}-\d{2}(?:T[^\s]+)?|date:\s*(\d{4})-\d{2}-\d{2})\b")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def find_wiki_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate_parent in [current, *current.parents]:
        candidate = candidate_parent / WIKI_DIR_NAME
        if candidate.is_dir():
            return candidate
    return None


def resolve_wiki_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()

    env_root = os.environ.get("LLM_WIKI_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    found = find_wiki_root(Path.cwd())
    if found:
        return found

    raise SystemExit("No project-local LLM-know-how-wiki found. Pass the wiki root path explicitly.")


def split_frontmatter(text: str) -> tuple[str, str]:
    if not text.startswith("---\n"):
        return "", text
    end = text.find("\n---\n", 4)
    if end == -1:
        return "", text
    return text[: end + len("\n---\n")], text[end + len("\n---\n") :]


def update_frontmatter_date(frontmatter: str, today: str) -> str:
    if not frontmatter:
        return frontmatter
    if re.search(r"(?m)^updated:\s*", frontmatter):
        return re.sub(r"(?m)^updated:.*$", f"updated: {today}", frontmatter)
    return frontmatter


def split_log_body(body: str) -> tuple[list[str], list[list[str]]]:
    lines = body.splitlines()
    starts = [idx for idx, line in enumerate(lines) if ENTRY_START_RE.match(line)]
    if not starts:
        return lines, []

    header = lines[: starts[0]]
    blocks: list[list[str]] = []
    for pos, start in enumerate(starts):
        end = starts[pos + 1] if pos + 1 < len(starts) else len(lines)
        blocks.append(lines[start:end])
    return header, blocks


def entry_year(block: list[str]) -> str:
    if not block:
        return "unknown"
    match = ENTRY_START_RE.match(block[0])
    if not match:
        return "unknown"
    return match.group(1) or match.group(2) or "unknown"


def choose_recent_blocks(blocks: list[list[str]], keep_lines: int) -> tuple[list[list[str]], list[list[str]]]:
    if len(blocks) <= 1:
        return [], blocks

    recent_reversed: list[list[str]] = []
    line_count = 0
    for block in reversed(blocks):
        recent_reversed.append(block)
        line_count += len(block)
        if line_count >= keep_lines:
            break

    keep_count = max(1, len(recent_reversed))
    archive_count = max(0, len(blocks) - keep_count)
    return blocks[:archive_count], blocks[archive_count:]


def normalize_header(header: list[str], archive_years: list[str]) -> list[str]:
    text = "\n".join(header).strip()
    text = text.replace(
        "Append-only action history.",
        "Recent action history. Older entries are archived under `wiki/log_archive/`.",
    )

    lines = text.splitlines() if text else ["# Wiki Log"]
    cleaned: list[str] = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        if line.startswith("## Archive"):
            idx += 1
            while idx < len(lines) and not lines[idx].startswith("## "):
                idx += 1
            continue
        if line.startswith("## Recent Entries"):
            idx += 1
            continue
        cleaned.append(line)
        idx += 1

    while cleaned and not cleaned[-1].strip():
        cleaned.pop()

    cleaned.extend(["", "## Archive", ""])
    if archive_years:
        cleaned.extend(f"- [[log_archive/{year}.md]]" for year in archive_years)
    else:
        cleaned.append("- No archived log files yet.")
    cleaned.extend(["", "## Recent Entries", ""])
    return cleaned


def archive_header(year: str, today: str) -> str:
    return "\n".join(
        [
            "---",
            f"title: Wiki Log Archive {year}",
            "type: log",
            "status: archive",
            f"created: {today}",
            f"updated: {today}",
            "tags: [log, archive]",
            "sources:",
            "  - ../log.md",
            "confidence: high",
            "---",
            "",
            f"# Wiki Log Archive {year}",
            "",
            "Older activity entries moved out of `wiki/log.md` to keep recent context lightweight.",
            "",
        ]
    )


def block_text(block: list[str]) -> str:
    return "\n".join(block).rstrip() + "\n"


def archive_blocks(root: Path, blocks: list[list[str]], dry_run: bool) -> list[Path]:
    today = date.today().isoformat()
    archive_dir = root / "wiki" / "log_archive"
    grouped: defaultdict[str, list[list[str]]] = defaultdict(list)
    for block in blocks:
        grouped[entry_year(block)].append(block)

    touched: list[Path] = []
    for year, year_blocks in sorted(grouped.items()):
        path = archive_dir / f"{year}.md"
        rel = path.relative_to(root).as_posix()
        touched.append(path)
        if dry_run:
            print(f"would_update={rel} entries={len(year_blocks)}")
            continue

        archive_dir.mkdir(parents=True, exist_ok=True)
        existing = path.read_text(encoding="utf-8") if path.exists() else archive_header(year, today)
        frontmatter, rest = split_frontmatter(existing)
        frontmatter = update_frontmatter_date(frontmatter, today)
        existing = frontmatter + rest

        additions: list[str] = []
        for block in year_blocks:
            text = block_text(block)
            if text.strip() not in existing:
                additions.append(text)

        if additions:
            path.write_text(existing.rstrip() + "\n\n" + "\n".join(additions) + "\n", encoding="utf-8")
        elif frontmatter:
            path.write_text(existing, encoding="utf-8")

    return touched


def build_archive_entry(archive_paths: list[Path], archived_count: int, kept_count: int, root: Path) -> list[str]:
    updated = ["wiki/log.md", *[path.relative_to(root).as_posix() for path in archive_paths]]
    return [
        f"- {utc_now()} LOG_ARCHIVE",
        "  - sources:",
        "    - wiki/log.md",
        "  - updated:",
        *[f"    - {item}" for item in updated],
        f"  - notes: Archived {archived_count} older log entries and kept {kept_count} recent entries in wiki/log.md.",
    ]


def write_log(root: Path, frontmatter: str, header: list[str], kept: list[list[str]], archive_paths: list[Path], archived_count: int) -> None:
    today = date.today().isoformat()
    frontmatter = update_frontmatter_date(frontmatter, today)
    archive_years = sorted({path.stem for path in archive_paths})
    rebuilt: list[str] = normalize_header(header, archive_years)
    for block in kept:
        rebuilt.extend(block)
        if rebuilt and rebuilt[-1].strip():
            rebuilt.append("")
    rebuilt.extend(build_archive_entry(archive_paths, archived_count, len(kept), root))
    rebuilt.append("")
    text = (frontmatter + "\n".join(rebuilt)).rstrip() + "\n"
    (root / "wiki" / "log.md").write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Wiki root path")
    parser.add_argument("--keep-lines", type=int, default=200, help="Approximate number of recent log lines to keep")
    parser.add_argument("--dry-run", action="store_true", help="Print archive plan without writing files")
    args = parser.parse_args()

    if args.keep_lines < 20:
        raise SystemExit("--keep-lines must be at least 20")

    root = resolve_wiki_root(args.path)
    log = root / "wiki" / "log.md"
    if not log.exists():
        raise SystemExit(f"Missing wiki log: {log}")

    text = log.read_text(encoding="utf-8")
    frontmatter, body = split_frontmatter(text)
    header, blocks = split_log_body(body)
    archive, keep = choose_recent_blocks(blocks, args.keep_lines)

    print(f"wiki_root={root}")
    print(f"log={log}")
    print(f"entries_total={len(blocks)}")
    print(f"entries_to_archive={len(archive)}")
    print(f"entries_to_keep={len(keep)}")
    print(f"keep_lines={args.keep_lines}")

    if not archive:
        print("archive_needed=false")
        return 0

    archive_paths = archive_blocks(root, archive, args.dry_run)
    if args.dry_run:
        print("archive_needed=true")
        return 0

    write_log(root, frontmatter, header, keep, archive_paths, len(archive))
    print("archive_needed=true")
    print("updated=wiki/log.md")
    for path in archive_paths:
        print(f"updated={path.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
