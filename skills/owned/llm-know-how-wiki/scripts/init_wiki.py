#!/usr/bin/env python3
"""Initialize or locate a project-local LLM-know-how-wiki."""

from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path


WIKI_DIR_NAME = "LLM-know-how-wiki"


def find_wiki_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate_parent in [current, *current.parents]:
        candidate = candidate_parent / WIKI_DIR_NAME
        if candidate.is_dir():
            return candidate
    return None


def resolve_wiki_root(explicit: str | None, create: bool) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()

    env_root = os.environ.get("LLM_WIKI_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    found = find_wiki_root(Path.cwd())
    if found:
        return found

    if create:
        return (Path.cwd() / WIKI_DIR_NAME).resolve()

    raise SystemExit(
        "No project-local LLM-know-how-wiki found. "
        "Run again without --no-create to initialize ./LLM-know-how-wiki."
    )


def render_template(name: str, replacements: dict[str, str]) -> str:
    templates_dir = Path(__file__).resolve().parents[1] / "templates"
    text = (templates_dir / name).read_text(encoding="utf-8")
    for key, value in replacements.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def write_if_missing(path: Path, content: str) -> str:
    if path.exists():
        return "reused"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return "created"


def init_wiki(root: Path, domain: str) -> dict[str, list[str]]:
    today = date.today().isoformat()
    replacements = {"DATE": today, "DOMAIN": domain}
    created: list[str] = []
    reused: list[str] = []

    dirs = [
        "raw",
        "raw/repo_snapshots",
        "raw/external_reference_repos",
        "raw/gcloud_inventory",
        "raw/workflow_activity",
        "raw/imports",
        "external_reference_repos",
        "external_reference_repos/open_source",
        "wiki",
        "wiki/service",
        "wiki/architecture",
        "wiki/api",
        "wiki/project",
        "wiki/reference",
        "wiki/runbook",
        "wiki/decision",
        "wiki/digest",
    ]
    for rel in dirs:
        path = root / rel
        if path.exists():
            reused.append(rel + "/")
        else:
            path.mkdir(parents=True, exist_ok=True)
            created.append(rel + "/")

    files = {
        "README.md": "README.md.tpl",
        "SCHEMA.md": "SCHEMA.md.tpl",
        "external_reference_repos/README.md": "external_reference_repos_README.md.tpl",
        "wiki/index.md": "wiki_index.md.tpl",
        "wiki/log.md": "wiki_log.md.tpl",
        "wiki/overview.md": "wiki_overview.md.tpl",
    }
    for rel, template in files.items():
        status = write_if_missing(root / rel, render_template(template, replacements))
        (created if status == "created" else reused).append(rel)

    return {"created": created, "reused": reused}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Explicit wiki root path")
    parser.add_argument("--domain", default="project engineering knowledge", help="Short wiki domain description")
    parser.add_argument("--no-create", action="store_true", help="Only locate an existing wiki")
    parser.add_argument("--print-root", action="store_true", help="Print only the resolved wiki root")
    args = parser.parse_args()

    root = resolve_wiki_root(args.path, create=not args.no_create)
    if args.print_root:
        print(root)
        return 0

    if args.no_create:
        print(f"wiki_root={root}")
        print("mode=reuse")
        return 0

    result = init_wiki(root, args.domain)
    print(f"wiki_root={root}")
    print("created:")
    for item in result["created"]:
        print(f"  - {item}")
    print("reused:")
    for item in result["reused"]:
        print(f"  - {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
