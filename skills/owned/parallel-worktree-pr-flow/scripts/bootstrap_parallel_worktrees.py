#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="List, validate, or create parallel git worktrees from a registry JSON."
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
        "--group",
        default="",
        help="Only include streams from one group, for example distribution.",
    )
    parser.add_argument(
        "--stream-id",
        action="append",
        default=[],
        help="Select one or more exact stream ids.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Limit the number of selected streams.",
    )
    parser.add_argument(
        "--base-branch",
        default="",
        help="Override the registry base branch.",
    )
    parser.add_argument(
        "--status",
        action="append",
        default=[],
        help="Only include streams whose status matches one of these values. Repeatable.",
    )
    parser.add_argument(
        "--exclude-status",
        action="append",
        default=[],
        help="Exclude streams whose status matches one of these values. Repeatable.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List matching streams and exit.",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate registry uniqueness and low-coupling ownership rules, then exit.",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually run git worktree add commands. Without this flag the script only prints the plan.",
    )
    return parser.parse_args()


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


def normalize_streams(registry: dict[str, Any]) -> list[dict[str, Any]]:
    raw = registry.get("streams", [])
    return [item for item in raw if isinstance(item, dict) and str(item.get("id", "")).strip()]


def select_streams(registry: dict[str, Any], args: argparse.Namespace) -> list[dict[str, Any]]:
    streams = normalize_streams(registry)
    include_statuses = {item.strip() for item in args.status if item and item.strip()}
    exclude_statuses = {item.strip() for item in args.exclude_status if item and item.strip()}

    if args.execute and not include_statuses:
        defaults = registry.get("default_bootstrap_statuses", [])
        include_statuses = {str(item).strip() for item in defaults if str(item).strip()}

    if args.group:
        streams = [item for item in streams if item.get("group") == args.group]
    if args.stream_id:
        wanted = set(args.stream_id)
        streams = [item for item in streams if item.get("id") in wanted]
    if include_statuses:
        streams = [item for item in streams if str(item.get("status", "")).strip() in include_statuses]
    if exclude_statuses:
        streams = [item for item in streams if str(item.get("status", "")).strip() not in exclude_statuses]
    if args.limit > 0:
        streams = streams[: args.limit]
    return streams


def path_matches_any(candidate: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(candidate, pattern) for pattern in patterns)


def resolve_candidate_path(repo_root: Path, registry_path: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    registry_relative = (registry_path.parent / candidate).resolve()
    if registry_relative.exists():
        return registry_relative
    return (repo_root / candidate).resolve()


def validate_registry(registry: dict[str, Any], registry_path: Path, repo_root: Path) -> list[str]:
    issues: list[str] = []
    streams = normalize_streams(registry)
    shared_surfaces = [str(item) for item in registry.get("shared_surfaces", []) if str(item).strip()]
    seen_ids: dict[str, str] = {}
    seen_branches: dict[str, str] = {}
    seen_worktrees: dict[str, str] = {}
    seen_manifests: dict[str, str] = {}
    write_scope_owners: dict[str, str] = {}

    manifest_template = registry.get("provider_manifest_template", "")
    if manifest_template:
        manifest_template_path = resolve_candidate_path(repo_root, registry_path, str(manifest_template))
        if not manifest_template_path.exists():
            issues.append(f"missing provider manifest template: {manifest_template_path}")

    for item in streams:
        stream_id = str(item.get("id", "")).strip()
        branch = str(item.get("branch", "")).strip()
        worktree = str(item.get("worktree", "")).strip()
        manifest = str(item.get("manifest_path", "")).strip()
        group = str(item.get("group", "")).strip()
        status = str(item.get("status", "")).strip()
        write_scope = [str(path).strip() for path in item.get("write_scope", []) if str(path).strip()]

        if not group:
            issues.append(f"{stream_id}: missing group")
        if not status:
            issues.append(f"{stream_id}: missing status")
        if not branch:
            issues.append(f"{stream_id}: missing branch")
        if not worktree:
            issues.append(f"{stream_id}: missing worktree")
        if not manifest:
            issues.append(f"{stream_id}: missing manifest_path")
        if not write_scope:
            issues.append(f"{stream_id}: empty write_scope")

        if stream_id in seen_ids:
            issues.append(f"duplicate stream id: {stream_id}")
        seen_ids[stream_id] = stream_id

        if branch:
            owner = seen_branches.get(branch)
            if owner and owner != stream_id:
                issues.append(f"duplicate branch {branch}: {owner}, {stream_id}")
            seen_branches[branch] = stream_id

        if worktree:
            owner = seen_worktrees.get(worktree)
            if owner and owner != stream_id:
                issues.append(f"duplicate worktree {worktree}: {owner}, {stream_id}")
            seen_worktrees[worktree] = stream_id

        if manifest:
            owner = seen_manifests.get(manifest)
            if owner and owner != stream_id:
                issues.append(f"duplicate manifest_path {manifest}: {owner}, {stream_id}")
            seen_manifests[manifest] = stream_id

        for path in write_scope:
            if path_matches_any(path, shared_surfaces):
                issues.append(f"{stream_id}: write_scope overlaps shared surface: {path}")
            owner = write_scope_owners.get(path)
            if owner and owner != stream_id:
                issues.append(f"write_scope collision on {path}: {owner}, {stream_id}")
            write_scope_owners[path] = stream_id

    return issues


def git(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *command],
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
    )


def branch_exists(repo_root: Path, branch: str) -> bool:
    result = git(["branch", "--list", branch], repo_root)
    return bool((result.stdout or "").strip())


def worktree_exists(repo_root: Path, target: Path) -> bool:
    result = git(["worktree", "list", "--porcelain"], repo_root)
    if result.returncode != 0:
        return False
    wanted = str(target.resolve())
    for line in (result.stdout or "").splitlines():
        if line.startswith("worktree ") and line.split(" ", 1)[1].strip() == wanted:
            return True
    return False


def print_streams(streams: list[dict[str, Any]], base_branch: str) -> None:
    if not streams:
        print("No matching streams.")
        return
    print(f"Base branch: {base_branch}")
    print("")
    for item in streams:
        print(f"- {item.get('id', '')}")
        print(f"  label: {item.get('label', '')}")
        print(f"  group: {item.get('group', '')}")
        print(f"  branch: {item.get('branch', '')}")
        print(f"  worktree: {item.get('worktree', '')}")
        print(f"  status: {item.get('status', '')}")
        print(f"  priority: {item.get('priority', '')}")


def create_worktrees(repo_root: Path, streams: list[dict[str, Any]], base_branch: str) -> int:
    exit_code = 0
    for item in streams:
        branch = str(item.get("branch", "")).strip()
        worktree_raw = str(item.get("worktree", "")).strip()
        target = (repo_root / worktree_raw).resolve() if not Path(worktree_raw).is_absolute() else Path(worktree_raw)
        if not branch or not worktree_raw:
            print(f"[skip] {item.get('id', '')}: missing branch/worktree definition")
            exit_code = 1
            continue
        if target.exists() or worktree_exists(repo_root, target):
            print(f"[skip] {item.get('id', '')}: worktree already exists at {target}")
            continue
        if branch_exists(repo_root, branch):
            print(f"[skip] {item.get('id', '')}: branch already exists: {branch}")
            exit_code = 1
            continue
        command = ["worktree", "add", str(target), "-b", branch, base_branch]
        result = git(command, repo_root)
        if result.returncode == 0:
            print(f"[ok] {item.get('id', '')}: created {target} on {branch}")
        else:
            print(f"[error] {item.get('id', '')}: {' '.join(command)}")
            stderr = (result.stderr or result.stdout or "").strip()
            if stderr:
                print(stderr)
            exit_code = 1
    return exit_code


def main() -> None:
    args = parse_args()
    registry_path = Path(args.registry_file).resolve()
    registry = load_registry(registry_path)
    repo_root = Path(args.repo_root).resolve() if args.repo_root else find_repo_root(registry_path.parent)
    base_branch = args.base_branch or str(registry.get("base_branch", "master"))

    if args.validate:
        issues = validate_registry(registry, registry_path, repo_root)
        if issues:
            print("Registry validation failed:")
            for issue in issues:
                print(f"- {issue}")
            raise SystemExit(1)
        print("Registry validation passed.")
        return

    streams = select_streams(registry, args)
    print_streams(streams, base_branch)

    if args.execute:
        raise SystemExit(create_worktrees(repo_root, streams, base_branch))


if __name__ == "__main__":
    main()
