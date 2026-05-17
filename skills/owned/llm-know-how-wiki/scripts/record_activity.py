#!/usr/bin/env python3
"""Record workflow activity into a project-local LLM-know-how-wiki."""

from __future__ import annotations

import argparse
import os
import re
from datetime import datetime, timezone
from pathlib import Path


WIKI_DIR_NAME = "LLM-know-how-wiki"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-").lower()
    return slug[:80] or "activity"


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

    raise SystemExit("No project-local LLM-know-how-wiki found. Pass --wiki-root explicitly.")


def read_details(args: argparse.Namespace) -> str:
    parts: list[str] = []
    if args.details:
        parts.append(args.details.strip())
    if args.details_file:
        parts.append(Path(args.details_file).read_text(encoding="utf-8").strip())
    return "\n\n".join(part for part in parts if part)


def write_raw_activity(root: Path, args: argparse.Namespace, details: str) -> Path:
    raw_dir = root / "raw" / "workflow_activity"
    raw_dir.mkdir(parents=True, exist_ok=True)
    name_seed = args.issue or args.pr or args.branch or args.operation
    rel = Path("raw") / "workflow_activity" / f"{timestamp()}-{slugify(name_seed)}.md"
    path = root / rel

    body = [
        f"# Workflow Activity: {args.operation}",
        "",
        "## Metadata",
        f"- recorded_at: `{utc_now()}`",
        f"- operation: `{args.operation}`",
        f"- issue: `{args.issue or 'unknown'}`",
        f"- pr: `{args.pr or 'unknown'}`",
        f"- repo: `{args.repo or 'unknown'}`",
        f"- branch: `{args.branch or 'unknown'}`",
        "",
        "## Summary",
        "",
        args.summary.strip() if args.summary else "No summary provided.",
        "",
        "## Details",
        "",
        details if details else "No details provided.",
        "",
        "## Sources",
    ]
    sources = args.source or []
    body.extend(f"- `{source}`" for source in sources) if sources else body.append("- unknown")
    body.append("")
    path.write_text("\n".join(body), encoding="utf-8")
    return rel


def append_log(root: Path, args: argparse.Namespace, raw_rel: Path) -> None:
    log = root / "wiki" / "log.md"
    if not log.exists():
        raise SystemExit(f"Missing wiki log: {log}")

    sources = args.source or []
    if args.issue:
        sources.append(args.issue)
    if args.pr:
        sources.append(args.pr)
    if not sources:
        sources = ["workflow activity"]

    updated = [raw_rel.as_posix(), "wiki/log.md"]
    updated.extend(args.updated or [])

    block = [
        "",
        f"- {utc_now()} {args.operation}",
        "  - sources:",
        *[f"    - {source}" for source in sources],
        "  - updated:",
        *[f"    - {path}" for path in updated],
        f"  - notes: {args.summary.strip() if args.summary else 'Recorded workflow activity.'}",
    ]
    with log.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(block) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wiki-root", help="Explicit LLM-know-how-wiki root")
    parser.add_argument("--operation", default="WORKFLOW_ACTIVITY", help="Log operation label")
    parser.add_argument("--issue", help="Linear issue identifier or URL")
    parser.add_argument("--pr", help="GitHub PR URL or number")
    parser.add_argument("--repo", help="Repository path or owner/name")
    parser.add_argument("--branch", help="Git branch name")
    parser.add_argument("--summary", required=True, help="One-line activity summary")
    parser.add_argument("--details", help="Markdown details to store in raw activity")
    parser.add_argument("--details-file", help="Read Markdown details from a file")
    parser.add_argument("--source", action="append", help="Source path or URL; repeatable")
    parser.add_argument("--updated", action="append", help="Additional updated path; repeatable")
    args = parser.parse_args()

    root = resolve_wiki_root(args.wiki_root)
    details = read_details(args)
    raw_rel = write_raw_activity(root, args, details)
    append_log(root, args, raw_rel)
    print((root / raw_rel).as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
