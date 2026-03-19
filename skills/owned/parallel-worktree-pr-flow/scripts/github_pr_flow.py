#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any
from urllib import error, parse, request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create or merge GitHub pull requests for a local git repo without storing PATs in the repo."
    )
    parser.add_argument("--repo-root", default=".", help="Path to the target git repo root.")
    parser.add_argument("--head", default="", help="Head branch. Defaults to the current branch.")
    parser.add_argument("--base", required=True, help="Base branch for the pull request.")
    parser.add_argument("--title", default="", help="Pull request title. Defaults to the head branch name.")
    parser.add_argument("--body", default="", help="Pull request body.")
    parser.add_argument("--body-file", default="", help="Optional file containing the pull request body.")
    parser.add_argument("--draft", action="store_true", help="Create the pull request as a draft.")
    parser.add_argument("--merge", action="store_true", help="Merge the pull request after creating or locating it.")
    parser.add_argument(
        "--merge-method",
        default="squash",
        choices=["merge", "squash", "rebase"],
        help="Merge method when --merge is used.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Resolve repo and payload without calling GitHub.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text output.")
    return parser.parse_args()


def git(repo_root: Path, command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *command],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )


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


def read_body(args: argparse.Namespace) -> str:
    if args.body_file:
        return Path(args.body_file).read_text(encoding="utf-8")
    return args.body


def current_branch(repo_root: Path) -> str:
    result = git(repo_root, ["rev-parse", "--abbrev-ref", "HEAD"])
    if result.returncode != 0:
        raise SystemExit((result.stderr or result.stdout or "").strip() or "Could not determine current branch")
    return (result.stdout or "").strip()


def origin_repo(repo_root: Path) -> tuple[str, str]:
    result = git(repo_root, ["remote", "get-url", "origin"])
    if result.returncode != 0:
        raise SystemExit((result.stderr or result.stdout or "").strip() or "Could not read origin remote")
    url = (result.stdout or "").strip()

    if url.startswith("git@github.com:"):
        slug = url.split(":", 1)[1]
    elif url.startswith("https://github.com/") or url.startswith("http://github.com/"):
        slug = parse.urlparse(url).path.lstrip("/")
    else:
        raise SystemExit(f"Unsupported origin remote for GitHub PR flow: {url}")

    if slug.endswith(".git"):
        slug = slug[:-4]
    parts = slug.split("/", 1)
    if len(parts) != 2:
        raise SystemExit(f"Could not parse owner/repo from origin remote: {url}")
    return parts[0], parts[1]


def github_token() -> str:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token.strip()
    raise SystemExit(
        "Missing GitHub token. Export GITHUB_TOKEN or GH_TOKEN with a PAT that has pull request and contents access. "
        "Do not store the PAT in the repository."
    )


def github_request(token: str, method: str, url: str, payload: dict[str, Any] | None = None) -> dict[str, Any] | list[Any]:
    data = None
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "parallel-worktree-pr-flow",
    }
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = request.Request(url, data=data, headers=headers, method=method)
    try:
        with request.urlopen(req) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body) if body else {}
    except error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        detail = body
        try:
            detail = json.dumps(json.loads(body), ensure_ascii=False, indent=2)
        except Exception:
            pass
        raise SystemExit(f"GitHub API request failed ({exc.code}): {detail}") from exc


def find_existing_pr(token: str, owner: str, repo: str, head: str, base: str) -> dict[str, Any] | None:
    query = parse.urlencode({"state": "open", "head": f"{owner}:{head}", "base": base})
    payload = github_request(token, "GET", f"https://api.github.com/repos/{owner}/{repo}/pulls?{query}")
    if isinstance(payload, list) and payload:
        return payload[0]
    return None


def create_pr(
    token: str,
    owner: str,
    repo: str,
    head: str,
    base: str,
    title: str,
    body: str,
    draft: bool,
) -> dict[str, Any]:
    existing = find_existing_pr(token, owner, repo, head, base)
    if existing:
        existing["_action"] = "existing"
        return existing
    created = github_request(
        token,
        "POST",
        f"https://api.github.com/repos/{owner}/{repo}/pulls",
        {"title": title, "head": head, "base": base, "body": body, "draft": draft},
    )
    if not isinstance(created, dict):
        raise SystemExit("Unexpected GitHub response while creating pull request")
    created["_action"] = "created"
    return created


def merge_pr(token: str, owner: str, repo: str, number: int, merge_method: str, commit_title: str) -> dict[str, Any]:
    merged = github_request(
        token,
        "PUT",
        f"https://api.github.com/repos/{owner}/{repo}/pulls/{number}/merge",
        {"merge_method": merge_method, "commit_title": commit_title},
    )
    if not isinstance(merged, dict):
        raise SystemExit("Unexpected GitHub response while merging pull request")
    merged["_action"] = "merged"
    return merged


def print_result(as_json: bool, payload: dict[str, Any]) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    for key, value in payload.items():
        print(f"{key}: {value}")


def main() -> None:
    args = parse_args()
    repo_root = find_repo_root(Path(args.repo_root))
    head = args.head or current_branch(repo_root)
    title = args.title or head
    body = read_body(args)
    owner, repo = origin_repo(repo_root)

    payload: dict[str, Any] = {
        "repo_root": str(repo_root),
        "owner": owner,
        "repo": repo,
        "head": head,
        "base": args.base,
        "title": title,
        "draft": args.draft,
        "merge_requested": args.merge,
        "merge_method": args.merge_method,
    }

    if args.dry_run:
        payload["status"] = "dry_run"
        payload["body_preview"] = body[:500]
        print_result(args.json, payload)
        return

    token = github_token()
    pr = create_pr(token, owner, repo, head, args.base, title, body, args.draft)
    payload["status"] = "pr_ready"
    payload["pr_action"] = pr.get("_action", "")
    payload["number"] = pr.get("number")
    payload["html_url"] = pr.get("html_url", "")
    payload["state"] = pr.get("state", "")
    payload["draft_state"] = pr.get("draft", False)

    if args.merge:
        if not pr.get("number"):
            raise SystemExit("Could not determine pull request number for merge step")
        merged = merge_pr(token, owner, repo, int(pr["number"]), args.merge_method, title)
        payload["status"] = "merged"
        payload["merge_result"] = merged

    print_result(args.json, payload)


if __name__ == "__main__":
    main()
