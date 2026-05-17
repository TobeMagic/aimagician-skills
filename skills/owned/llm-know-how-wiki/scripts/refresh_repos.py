#!/usr/bin/env python3
"""Fetch all git repositories under a workspace and optionally write a raw snapshot."""

from __future__ import annotations

import argparse
import os
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


WIKI_DIR_NAME = "LLM-know-how-wiki"
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".next",
    ".nuxt",
    "dist",
    "build",
    "target",
    ".idea",
    ".vscode",
}


@dataclass
class RepoResult:
    path: Path
    rel_path: str
    branch: str
    head: str
    dirty_count: int
    upstream: str
    ahead: str
    behind: str
    remotes: list[str]
    action: str
    exit_code: int | None
    duration_s: float
    stdout: str
    stderr: str


def run_git(repo: Path, args: list[str], timeout: int = 30) -> tuple[int, str, str]:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
    )
    return proc.returncode, proc.stdout.strip(), proc.stderr.strip()


def git_text(repo: Path, args: list[str], default: str = "unknown") -> str:
    try:
        code, out, _ = run_git(repo, args)
    except Exception:
        return default
    if code != 0 or not out:
        return default
    return out


def find_wiki_root(start: Path) -> Path | None:
    current = start.resolve()
    for candidate_parent in [current, *current.parents]:
        candidate = candidate_parent / WIKI_DIR_NAME
        if candidate.is_dir():
            return candidate
    return None


def resolve_workspace(value: str | None) -> Path:
    if value:
        return Path(value).expanduser().resolve()
    found_wiki = find_wiki_root(Path.cwd())
    if found_wiki:
        return found_wiki.parent.resolve()
    return Path.cwd().resolve()


def resolve_wiki_root(value: str | None, workspace: Path) -> Path | None:
    if value:
        root = Path(value).expanduser().resolve()
        return root if root.is_dir() else None
    candidate = workspace / WIKI_DIR_NAME
    if candidate.is_dir():
        return candidate.resolve()
    return find_wiki_root(Path.cwd())


def is_git_repo(path: Path) -> bool:
    return (path / ".git").exists()


def discover_repos(workspace: Path, max_depth: int) -> list[Path]:
    repos: list[Path] = []
    workspace = workspace.resolve()
    for dirpath, dirnames, _ in os.walk(workspace):
        current = Path(dirpath)
        rel_parts = current.relative_to(workspace).parts
        if len(rel_parts) > max_depth:
            dirnames[:] = []
            continue

        dirnames[:] = [name for name in dirnames if name not in SKIP_DIRS]

        if is_git_repo(current):
            repos.append(current)
            dirnames[:] = []

    return sorted(repos)


def repo_status(repo: Path, workspace: Path) -> dict[str, object]:
    branch = git_text(repo, ["branch", "--show-current"], default="detached-or-unknown")
    head = git_text(repo, ["rev-parse", "--short", "HEAD"], default="unknown")
    status = git_text(repo, ["status", "--porcelain"], default="")
    dirty_count = len([line for line in status.splitlines() if line.strip()])
    upstream = git_text(repo, ["rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], default="")
    ahead = "unknown"
    behind = "unknown"
    if upstream:
        code, out, _ = run_git(repo, ["rev-list", "--left-right", "--count", "HEAD...@{u}"])
        if code == 0 and out:
            parts = out.split()
            if len(parts) == 2:
                ahead, behind = parts
    remote_lines = git_text(repo, ["remote", "-v"], default="").splitlines()
    remotes = sorted(set(remote_lines))
    return {
        "branch": branch,
        "head": head,
        "dirty_count": dirty_count,
        "upstream": upstream or "none",
        "ahead": ahead,
        "behind": behind,
        "remotes": remotes,
    }


def fetch_repo(repo: Path, workspace: Path, timeout: int, dry_run: bool) -> RepoResult:
    before = repo_status(repo, workspace)
    rel_path = repo.relative_to(workspace).as_posix()
    remotes = before["remotes"]

    if not remotes:
        return RepoResult(
            path=repo,
            rel_path=rel_path,
            branch=str(before["branch"]),
            head=str(before["head"]),
            dirty_count=int(before["dirty_count"]),
            upstream=str(before["upstream"]),
            ahead=str(before["ahead"]),
            behind=str(before["behind"]),
            remotes=[],
            action="skipped_no_remote",
            exit_code=None,
            duration_s=0.0,
            stdout="",
            stderr="",
        )

    if dry_run:
        return RepoResult(
            path=repo,
            rel_path=rel_path,
            branch=str(before["branch"]),
            head=str(before["head"]),
            dirty_count=int(before["dirty_count"]),
            upstream=str(before["upstream"]),
            ahead=str(before["ahead"]),
            behind=str(before["behind"]),
            remotes=list(remotes),
            action="dry_run",
            exit_code=None,
            duration_s=0.0,
            stdout="",
            stderr="",
        )

    started = time.monotonic()
    try:
        code, stdout, stderr = run_git(repo, ["fetch", "--all", "--prune", "--tags"], timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        duration = time.monotonic() - started
        return RepoResult(
            path=repo,
            rel_path=rel_path,
            branch=str(before["branch"]),
            head=str(before["head"]),
            dirty_count=int(before["dirty_count"]),
            upstream=str(before["upstream"]),
            ahead=str(before["ahead"]),
            behind=str(before["behind"]),
            remotes=list(remotes),
            action="timeout",
            exit_code=None,
            duration_s=duration,
            stdout=exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else str(exc.stdout or ""),
            stderr=exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else str(exc.stderr or ""),
        )
    duration = time.monotonic() - started
    after = repo_status(repo, workspace)
    return RepoResult(
        path=repo,
        rel_path=rel_path,
        branch=str(after["branch"]),
        head=str(after["head"]),
        dirty_count=int(after["dirty_count"]),
        upstream=str(after["upstream"]),
        ahead=str(after["ahead"]),
        behind=str(after["behind"]),
        remotes=list(remotes),
        action="fetched" if code == 0 else "failed",
        exit_code=code,
        duration_s=duration,
        stdout=stdout,
        stderr=stderr,
    )


def render_report(workspace: Path, results: list[RepoResult], dry_run: bool) -> str:
    now = datetime.now().isoformat(timespec="seconds")
    counts: dict[str, int] = {}
    for result in results:
        counts[result.action] = counts.get(result.action, 0) + 1
    lines = [
        f"# Git Fetch Snapshot - {now}",
        "",
        f"Workspace: `{workspace}`",
        f"Mode: `{'dry_run' if dry_run else 'fetch'}`",
        "",
        "## Summary",
        "",
        f"- Repositories discovered: {len(results)}",
    ]
    for action in sorted(counts):
        lines.append(f"- {action}: {counts[action]}")

    lines.extend(
        [
            "",
            "## Repository status",
            "",
            "| Repo | Action | Branch | HEAD | Upstream | Ahead | Behind | Dirty files | Remotes | Duration |",
            "| --- | --- | --- | --- | --- | ---: | ---: | ---: | --- | ---: |",
        ]
    )
    for result in results:
        remotes = "<br>".join(remote.replace("|", "\\|") for remote in result.remotes) or "none"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{result.rel_path}`",
                    f"`{result.action}`",
                    f"`{result.branch}`",
                    f"`{result.head}`",
                    f"`{result.upstream}`",
                    result.ahead,
                    result.behind,
                    str(result.dirty_count),
                    remotes,
                    f"{result.duration_s:.1f}s",
                ]
            )
            + " |"
        )

    failed = [item for item in results if item.action in {"failed", "timeout"}]
    if failed:
        lines.extend(["", "## Failures", ""])
        for item in failed:
            lines.append(f"### `{item.rel_path}`")
            lines.append("")
            lines.append(f"- action: `{item.action}`")
            if item.exit_code is not None:
                lines.append(f"- exit_code: `{item.exit_code}`")
            if item.stderr:
                lines.append("")
                lines.append("```text")
                lines.append(item.stderr[-4000:])
                lines.append("```")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This snapshot uses `git fetch --all --prune --tags` only.",
            "- It does not pull, merge, rebase, checkout, or change the working tree.",
            "- Dirty file counts are from `git status --porcelain` after fetch.",
            "",
        ]
    )
    return "\n".join(lines)


def write_raw_snapshot(wiki_root: Path, report: str) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%dT%H%M%S")
    target = wiki_root / "raw" / "repo_snapshots" / f"{timestamp}-git-fetch.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report, encoding="utf-8")
    return target


def append_log(wiki_root: Path, snapshot: Path, results: list[RepoResult], dry_run: bool) -> None:
    log = wiki_root / "wiki" / "log.md"
    if not log.exists():
        return
    today = datetime.now().date().isoformat()
    rel_snapshot = snapshot.relative_to(wiki_root).as_posix()
    failed = sum(1 for item in results if item.action in {"failed", "timeout"})
    fetched = sum(1 for item in results if item.action == "fetched")
    skipped = sum(1 for item in results if item.action == "skipped_no_remote")
    mode = "dry-run" if dry_run else "fetch"
    entry = (
        f"\n- {today} REFRESH_REPOS\n"
        "  - sources:\n"
        "    - workspace git repositories\n"
        "  - updated:\n"
        f"    - {rel_snapshot}\n"
        "    - wiki/log.md\n"
        f"  - notes: Git {mode} snapshot recorded {len(results)} repos; fetched={fetched}, skipped_no_remote={skipped}, failed={failed}.\n"
    )
    with log.open("a", encoding="utf-8") as handle:
        handle.write(entry)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", help="Workspace root to scan. Defaults to parent of project-local wiki, or cwd.")
    parser.add_argument("--wiki-root", help="Wiki root for writing raw snapshot/log.")
    parser.add_argument("--max-depth", type=int, default=4, help="Maximum directory depth to scan.")
    parser.add_argument("--timeout", type=int, default=180, help="Fetch timeout per repository in seconds.")
    parser.add_argument("--dry-run", action="store_true", help="Discover repos and report status without fetching.")
    parser.add_argument("--no-write-raw", action="store_true", help="Do not write raw/repo_snapshots report.")
    parser.add_argument("--no-log", action="store_true", help="Do not append wiki/log.md.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    wiki_root = resolve_wiki_root(args.wiki_root, workspace)
    repos = discover_repos(workspace, max_depth=args.max_depth)
    results = [fetch_repo(repo, workspace, args.timeout, args.dry_run) for repo in repos]
    report = render_report(workspace, results, args.dry_run)

    print(f"workspace={workspace}")
    print(f"wiki_root={wiki_root or 'none'}")
    print(f"repos={len(results)}")
    for action in sorted({item.action for item in results}):
        print(f"{action}={sum(1 for item in results if item.action == action)}")

    snapshot: Path | None = None
    if wiki_root and not args.no_write_raw:
        snapshot = write_raw_snapshot(wiki_root, report)
        print(f"snapshot={snapshot}")
        if not args.no_log:
            append_log(wiki_root, snapshot, results, args.dry_run)
            print(f"log_appended={wiki_root / 'wiki' / 'log.md'}")
    elif args.no_write_raw:
        print("snapshot=disabled")
    else:
        print("snapshot=skipped_no_wiki_root")

    failures = [item for item in results if item.action in {"failed", "timeout"}]
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())

