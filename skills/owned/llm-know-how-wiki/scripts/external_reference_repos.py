#!/usr/bin/env python3
"""Manage external open-source reference repositories for an LLM-know-how-wiki."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


WIKI_DIR_NAME = "LLM-know-how-wiki"
REF_ROOT = Path("external_reference_repos")
OPEN_SOURCE_DIR = REF_ROOT / "open_source"
MANIFEST_PATH = REF_ROOT / "manifest.json"
RAW_SNAPSHOT_DIR = Path("raw") / "external_reference_repos"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")


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


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"
    return subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def sanitize_token(text: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", text.strip().lower())
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "repo"


def sanitize_url(url: str) -> str:
    if re.match(r"^[A-Za-z0-9_.-]+@[^:]+:.+", url):
        return url

    parts = urlsplit(url)
    if not parts.netloc:
        return url

    host = parts.hostname or parts.netloc.split("@")[-1]
    netloc = host
    if parts.port:
        netloc = f"{netloc}:{parts.port}"
    return urlunsplit((parts.scheme, netloc, parts.path, "", ""))


def infer_name(url: str) -> str:
    ssh_match = re.match(r"^(?P<user>[A-Za-z0-9_.-]+)@(?P<host>[^:]+):(?P<path>.+)$", url)
    if ssh_match:
        host = ssh_match.group("host")
        path = ssh_match.group("path")
    else:
        parts = urlsplit(url)
        host = parts.hostname or "local"
        path = parts.path

    bits = [bit for bit in path.strip("/").split("/") if bit]
    if not bits:
        return sanitize_token(host)

    repo = re.sub(r"\.git$", "", bits[-1])
    owner = bits[-2] if len(bits) >= 2 else "unknown"
    host_token = "github" if host.lower() == "github.com" else sanitize_token(host)
    return "__".join(sanitize_token(part) for part in [host_token, owner, repo])


def load_manifest(root: Path) -> dict:
    path = root / MANIFEST_PATH
    if not path.exists():
        return {"schema_version": 1, "items": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save_manifest(root: Path, manifest: dict) -> None:
    path = root / MANIFEST_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest["updated_at"] = utc_now()
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def ensure_reference_root(root: Path) -> None:
    (root / OPEN_SOURCE_DIR).mkdir(parents=True, exist_ok=True)
    (root / RAW_SNAPSHOT_DIR).mkdir(parents=True, exist_ok=True)
    readme = root / REF_ROOT / "README.md"
    if not readme.exists():
        readme.write_text(
            "# External Reference Repositories\n\n"
            "This directory stores third-party repositories used only for architecture and implementation reference.\n\n"
            "- These repositories are not company services.\n"
            "- Do not treat them as deployable workspace projects.\n"
            "- Keep source URL, license, ref, and update metadata in `manifest.json`.\n"
            "- Curated analysis belongs under `wiki/reference/`; raw snapshots belong under `raw/external_reference_repos/`.\n",
            encoding="utf-8",
        )


def git_output(repo: Path, args: list[str]) -> str:
    result = run(["git", *args], cwd=repo, check=False)
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip() or "unknown"


def repo_metadata(repo: Path) -> dict[str, str]:
    branch = git_output(repo, ["branch", "--show-current"])
    head = git_output(repo, ["rev-parse", "HEAD"])
    remote = git_output(repo, ["remote", "get-url", "origin"])
    license_files = []
    for candidate in ["LICENSE", "LICENSE.md", "COPYING", "NOTICE"]:
        if (repo / candidate).exists():
            license_files.append(candidate)
    return {
        "branch": branch,
        "head": head,
        "remote": sanitize_url(remote),
        "license_files": ", ".join(license_files) if license_files else "unknown",
    }


def upsert_item(manifest: dict, item: dict) -> None:
    items = manifest.setdefault("items", [])
    for index, existing in enumerate(items):
        if existing.get("name") == item["name"]:
            merged = {**existing, **item, "added_at": existing.get("added_at") or item.get("added_at")}
            items[index] = merged
            return
    items.append(item)


def append_log(root: Path, operation: str, sources: list[str], updated: list[str], notes: str) -> None:
    log = root / "wiki" / "log.md"
    if not log.exists():
        return
    block = [
        "",
        f"- {utc_now()} {operation}",
        "  - sources:",
        *[f"    - {source}" for source in sources],
        "  - updated:",
        *[f"    - {path}" for path in updated],
        f"  - notes: {notes}",
    ]
    with log.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(block) + "\n")


def add_repo(args: argparse.Namespace) -> int:
    root = resolve_wiki_root(args.wiki_root)
    ensure_reference_root(root)
    manifest = load_manifest(root)

    safe_url = sanitize_url(args.url)
    name = sanitize_token(args.name) if args.name else infer_name(args.url)
    target = root / OPEN_SOURCE_DIR / name

    if target.exists():
        if not (target / ".git").is_dir():
            raise SystemExit(f"Target exists but is not a git repo: {target}")
        status = "existing"
        run(["git", "fetch", "--all", "--prune", "--tags"], cwd=target)
    else:
        run(["git", "clone", "--filter=blob:none", args.url, str(target)])
        status = "cloned"

    if args.ref:
        run(["git", "checkout", "--quiet", args.ref], cwd=target)

    meta = repo_metadata(target)
    rel_path = target.relative_to(root).as_posix()
    now = utc_now()
    upsert_item(
        manifest,
        {
            "name": name,
            "kind": "open_source",
            "url": safe_url,
            "path": rel_path,
            "ref": args.ref or "",
            "branch": meta["branch"],
            "head": meta["head"],
            "license_files": meta["license_files"],
            "added_at": now,
            "updated_at": now,
            "notes": args.notes or "",
        },
    )
    save_manifest(root, manifest)
    append_log(
        root,
        "REFERENCE_REPO",
        [safe_url],
        [rel_path, MANIFEST_PATH.as_posix()],
        f"{status} external open-source reference repo `{name}`.",
    )
    print(f"{status}: {name} -> {target}")
    print(f"head={meta['head']}")
    return 0


def update_repos(args: argparse.Namespace) -> int:
    root = resolve_wiki_root(args.wiki_root)
    ensure_reference_root(root)
    manifest = load_manifest(root)
    selected = set(args.names or [])
    updated: list[str] = []

    for item in manifest.get("items", []):
        if selected and item.get("name") not in selected:
            continue
        repo = root / item["path"]
        if not (repo / ".git").is_dir():
            print(f"missing: {item.get('name')} -> {repo}")
            continue
        run(["git", "fetch", "--all", "--prune", "--tags"], cwd=repo)
        meta = repo_metadata(repo)
        item.update(
            {
                "branch": meta["branch"],
                "head": meta["head"],
                "license_files": meta["license_files"],
                "updated_at": utc_now(),
            }
        )
        updated.append(item["path"])
        print(f"updated: {item['name']} head={meta['head']}")

    save_manifest(root, manifest)
    if updated:
        append_log(
            root,
            "REFERENCE_REPO_REFRESH",
            ["external_reference_repos/manifest.json"],
            [*updated, MANIFEST_PATH.as_posix()],
            f"Fetched {len(updated)} external reference repositories.",
        )
    return 0


def list_repos(args: argparse.Namespace) -> int:
    root = resolve_wiki_root(args.wiki_root)
    manifest = load_manifest(root)
    for item in manifest.get("items", []):
        print(f"{item.get('name')}\t{item.get('head')}\t{item.get('url')}\t{item.get('path')}")
    return 0


def architecture_files(repo: Path) -> list[str]:
    candidates = [
        "README.md",
        "README",
        "AGENTS.md",
        "CLAUDE.md",
        "CODEX.md",
        "GEMINI.md",
        "package.json",
        "pnpm-workspace.yaml",
        "bun.lock",
        "Cargo.toml",
        "go.mod",
        "pyproject.toml",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        "Makefile",
    ]
    found = [path for path in candidates if (repo / path).exists()]
    for directory in ["docs", "documentation", "examples", "packages", "apps", "src", "crates", "cmd"]:
        if (repo / directory).exists():
            found.append(directory + "/")
    return found


def git_files(repo: Path, limit: int) -> list[str]:
    result = run(["git", "ls-files"], cwd=repo, check=False)
    if result.returncode != 0:
        return []
    files = [line for line in result.stdout.splitlines() if line.strip()]
    return files[:limit]


def snapshot_repo(args: argparse.Namespace) -> int:
    root = resolve_wiki_root(args.wiki_root)
    ensure_reference_root(root)
    manifest = load_manifest(root)
    items = {item["name"]: item for item in manifest.get("items", [])}
    if args.name not in items:
        raise SystemExit(f"Unknown reference repo: {args.name}")

    item = items[args.name]
    repo = root / item["path"]
    meta = repo_metadata(repo)
    files = git_files(repo, args.file_limit)
    important = architecture_files(repo)
    raw_rel = RAW_SNAPSHOT_DIR / f"{timestamp()}-{args.name}-snapshot.md"
    raw_path = root / raw_rel
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    body = [
        f"# External Reference Repo Snapshot: {args.name}",
        "",
        "## Metadata",
        f"- name: `{args.name}`",
        f"- source_url: `{item.get('url', 'unknown')}`",
        f"- local_path: `{item.get('path', 'unknown')}`",
        f"- branch: `{meta['branch']}`",
        f"- head: `{meta['head']}`",
        f"- license_files: `{meta['license_files']}`",
        f"- captured_at: `{utc_now()}`",
        "",
        "## Important architecture files",
        *[f"- `{path}`" for path in important],
        "",
        "## File inventory sample",
        *[f"- `{path}`" for path in files],
        "",
        "## Notes",
        "- This is an external open-source reference repository, not a company service.",
        "- Use this snapshot as raw evidence for later architecture comparison pages under `wiki/reference/`.",
    ]
    raw_path.write_text("\n".join(body) + "\n", encoding="utf-8")
    append_log(
        root,
        "REFERENCE_REPO_SNAPSHOT",
        [item.get("path", args.name)],
        [raw_rel.as_posix(), "wiki/log.md"],
        f"Captured shallow file inventory for external reference repo `{args.name}`.",
    )
    print(raw_path)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wiki-root", help="Explicit LLM-know-how-wiki root")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="Clone or refresh one external reference repo")
    add.add_argument("url", help="Git URL")
    add.add_argument("--name", help="Manifest/local directory name")
    add.add_argument("--ref", help="Optional branch, tag, or commit to checkout")
    add.add_argument("--notes", help="Optional manifest notes")
    add.set_defaults(func=add_repo)

    update = sub.add_parser("update", help="Fetch existing reference repos")
    update.add_argument("names", nargs="*", help="Optional repo names to update")
    update.set_defaults(func=update_repos)

    list_cmd = sub.add_parser("list", help="List manifest entries")
    list_cmd.set_defaults(func=list_repos)

    snap = sub.add_parser("snapshot", help="Write a shallow raw snapshot for a reference repo")
    snap.add_argument("name", help="Reference repo name from the manifest")
    snap.add_argument("--file-limit", type=int, default=240, help="Maximum git-tracked files to list")
    snap.set_defaults(func=snapshot_repo)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
