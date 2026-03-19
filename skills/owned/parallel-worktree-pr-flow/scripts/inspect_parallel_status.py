#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect branch/worktree/manifest state for a parallel workstream registry."
    )
    parser.add_argument(
        "--registry-file",
        required=True,
        help="Path to the parallel workstream registry JSON.",
    )
    parser.add_argument(
        "--repo-root",
        default="",
        help="Optional git repo root. Use this when the registry file lives outside the target repo.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of a text summary.",
    )
    return parser.parse_args()


def git(repo_root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *command],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )


def load_registry(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists():
            return candidate
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=str(start.resolve()),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0 and (result.stdout or "").strip():
        return Path((result.stdout or "").strip()).resolve()
    raise SystemExit(f"Could not determine git repo root from: {start}")


def branch_exists(repo_root: Path, branch: str) -> bool:
    result = git(repo_root, ["show-ref", "--verify", "--quiet", f"refs/heads/{branch}"])
    return result.returncode == 0


def remote_branch_exists(repo_root: Path, branch: str) -> bool:
    result = git(repo_root, ["show-ref", "--verify", "--quiet", f"refs/remotes/origin/{branch}"])
    return result.returncode == 0


def worktree_lookup(repo_root: Path) -> dict[str, dict[str, str]]:
    result = git(repo_root, ["worktree", "list", "--porcelain"])
    mapping: dict[str, dict[str, str]] = {}
    if result.returncode != 0:
        return mapping

    current: dict[str, str] = {}
    for line in (result.stdout or "").splitlines():
        if not line:
            if current.get("path"):
                mapping[current["path"]] = current
            current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value.strip()
    if current.get("path"):
        mapping[current["path"]] = current
    return mapping


def worktree_status(worktree_path: Path) -> str:
    if not worktree_path.exists():
        return "missing"
    tracked_result = subprocess.run(
        ["git", "diff", "--quiet", "--ignore-submodules", "HEAD", "--"],
        cwd=str(worktree_path),
        check=False,
        capture_output=True,
        text=True,
    )
    if tracked_result.returncode not in (0, 1):
        return "unknown"
    staged_result = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--ignore-submodules", "--"],
        cwd=str(worktree_path),
        check=False,
        capture_output=True,
        text=True,
    )
    if staged_result.returncode not in (0, 1):
        return "unknown"
    return "dirty" if tracked_result.returncode == 1 or staged_result.returncode == 1 else "clean"


def ahead_behind(repo_root: Path, local_ref: str, remote_ref: str) -> tuple[int | None, int | None]:
    result = git(repo_root, ["rev-list", "--left-right", "--count", f"{local_ref}...{remote_ref}"])
    if result.returncode != 0:
        return None, None
    parts = (result.stdout or "").strip().split()
    if len(parts) != 2:
        return None, None
    return int(parts[0]), int(parts[1])


def resolve_worktree(repo_root: Path, worktree_raw: str) -> Path:
    raw_path = Path(worktree_raw)
    return raw_path if raw_path.is_absolute() else (repo_root / raw_path).resolve()


def collect_status(registry_path: Path, repo_root_override: str = "") -> dict[str, Any]:
    registry = load_registry(registry_path)
    repo_root = Path(repo_root_override).resolve() if repo_root_override else find_repo_root(registry_path.parent)
    worktrees = worktree_lookup(repo_root)
    streams = registry.get("streams", [])
    results: list[dict[str, Any]] = []

    for item in streams:
        stream_id = str(item.get("id", "")).strip()
        if not stream_id:
            continue
        branch = str(item.get("branch", "")).strip()
        worktree_path = resolve_worktree(repo_root, str(item.get("worktree", "")).strip())
        manifest_path = (repo_root / str(item.get("manifest_path", "")).strip()).resolve()

        local_exists = branch_exists(repo_root, branch) if branch else False
        remote_exists = remote_branch_exists(repo_root, branch) if branch else False
        ahead, behind = (None, None)
        if local_exists and remote_exists:
            ahead, behind = ahead_behind(repo_root, branch, f"origin/{branch}")

        results.append(
            {
                "id": stream_id,
                "group": item.get("group", ""),
                "status": item.get("status", ""),
                "branch": branch,
                "local_branch_exists": local_exists,
                "remote_branch_exists": remote_exists,
                "ahead_of_remote": ahead,
                "behind_remote": behind,
                "worktree_path": str(worktree_path),
                "worktree_registered": str(worktree_path) in worktrees,
                "worktree_status": worktree_status(worktree_path),
                "manifest_path": str(manifest_path),
                "manifest_exists": manifest_path.exists(),
            }
        )

    return {"repo_root": str(repo_root), "stream_count": len(results), "streams": results}


def print_text_report(payload: dict[str, Any]) -> None:
    print(f"repo_root: {payload['repo_root']}")
    print(f"stream_count: {payload['stream_count']}")
    print("")
    for item in payload["streams"]:
        summary = [
            f"id={item['id']}",
            f"branch_local={'yes' if item['local_branch_exists'] else 'no'}",
            f"branch_remote={'yes' if item['remote_branch_exists'] else 'no'}",
            f"worktree={item['worktree_status']}",
            f"manifest={'yes' if item['manifest_exists'] else 'no'}",
        ]
        if item["ahead_of_remote"] is not None and item["behind_remote"] is not None:
            summary.append(f"ahead={item['ahead_of_remote']}")
            summary.append(f"behind={item['behind_remote']}")
        print("- " + " | ".join(summary))


def main() -> None:
    args = parse_args()
    payload = collect_status(Path(args.registry_file).resolve(), args.repo_root)
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_text_report(payload)


if __name__ == "__main__":
    main()
