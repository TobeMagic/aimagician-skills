#!/usr/bin/env python3
"""Fail closed when private assets, secrets, or binaries enter the git index."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Sequence


PRIVATE_PART = ".private"
SECRET_PARTS = frozenset({"secret", "secrets", "credentials"})
SECRET_FILENAMES = frozenset(
    {
        "gaojie.cookies",
        "cookies.txt",
        "cookie.txt",
        "credentials.json",
        "credentials.yaml",
        "credentials.yml",
    }
)
BINARY_SUFFIXES = frozenset(
    {
        ".7z",
        ".bin",
        ".dll",
        ".docm",
        ".exe",
        ".ole",
        ".potm",
        ".potx",
        ".ppsx",
        ".pptm",
        ".pptx",
        ".rar",
        ".xlsm",
        ".zip",
    }
)
SECRET_PATTERNS = (
    re.compile(
        rb"""(?ix)
        ["']?
        (?:PHPSESSID|JSESSIONID|session(?:_?id)?|cookie|password|token|authorization)
        ["']?
        \s*[:=]\s*
        ["']?
        [A-Za-z0-9._%+/=-]{12,}
        """
    ),
    re.compile(rb"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
    re.compile(rb"\bghp_[A-Za-z0-9]{20,}\b"),
    re.compile(rb"\bsk-[A-Za-z0-9_-]{20,}\b"),
)


@dataclass(frozen=True)
class GuardFinding:
    code: str
    path: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "path": self.path,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class GuardReport:
    status: str
    checked_paths: tuple[str, ...]
    findings: tuple[GuardFinding, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "status": self.status,
            "checked_paths": list(self.checked_paths),
            "findings": [finding.to_dict() for finding in self.findings],
        }


def _normalized(path: Path | PurePosixPath | str) -> PurePosixPath:
    value = str(path).replace("\\", "/").lstrip("./")
    return PurePosixPath(value)


def private_path_reason(path: Path | PurePosixPath | str) -> str | None:
    normalized = _normalized(path)
    lowered_parts = tuple(part.casefold() for part in normalized.parts)
    if PRIVATE_PART in lowered_parts:
        return "PRIVATE_PATH"
    if any(part in SECRET_PARTS for part in lowered_parts):
        return "SECRET_PATH"
    if normalized.name.casefold() in SECRET_FILENAMES:
        return "SECRET_PATH"
    return None


def inspect_payload(
    path: Path | PurePosixPath | str,
    payload: bytes,
    *,
    is_new: bool,
) -> tuple[GuardFinding, ...]:
    del is_new  # Binary changes require explicit future approval, new or old.
    normalized = _normalized(path)
    findings: list[GuardFinding] = []
    if normalized.suffix.casefold() in BINARY_SUFFIXES or b"\x00" in payload[:8192]:
        findings.append(
            GuardFinding(
                code="UNAPPROVED_BINARY",
                path=normalized.as_posix(),
                detail="staged binary content requires an explicit tracked approval",
            )
        )
    if any(pattern.search(payload) for pattern in SECRET_PATTERNS):
        findings.append(
            GuardFinding(
                code="SECRET_LITERAL",
                path=normalized.as_posix(),
                detail="staged content matches a secret-literal signature",
            )
        )
    return tuple(findings)


def _git(
    root: Path,
    args: Sequence[str],
    *,
    text: bool,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=text,
    )


def _staged_paths(root: Path) -> tuple[str, ...]:
    completed = _git(
        root,
        ["diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z"],
        text=False,
    )
    if completed.returncode != 0:
        raise RuntimeError("git could not enumerate the staged paths")
    assert isinstance(completed.stdout, bytes)
    return tuple(
        sorted(
            item.decode("utf-8", errors="surrogateescape")
            for item in completed.stdout.split(b"\0")
            if item
        )
    )


def _staged_payload(root: Path, path: str) -> bytes:
    completed = _git(root, ["show", f":{path}"], text=False)
    if completed.returncode != 0:
        raise RuntimeError(f"git could not read staged path metadata: {path}")
    assert isinstance(completed.stdout, bytes)
    return completed.stdout


def _is_new_path(root: Path, path: str) -> bool:
    completed = _git(root, ["cat-file", "-e", f"HEAD:{path}"], text=False)
    return completed.returncode != 0


def inspect_staged_repository(repo_root: Path | str) -> GuardReport:
    root = Path(repo_root).resolve()
    paths = _staged_paths(root)
    findings: list[GuardFinding] = []
    for path in paths:
        reason = private_path_reason(path)
        if reason is not None:
            findings.append(
                GuardFinding(
                    code=reason,
                    path=_normalized(path).as_posix(),
                    detail="private or credential-bearing paths cannot be staged",
                )
            )
        findings.extend(
            inspect_payload(
                path,
                _staged_payload(root, path),
                is_new=_is_new_path(root, path),
            )
        )
    ordered = tuple(
        sorted(findings, key=lambda item: (item.path, item.code, item.detail))
    )
    return GuardReport(
        status="PASS" if not ordered else "FAIL",
        checked_paths=paths,
        findings=ordered,
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reject private Window-PPTX assets and secrets in git staging."
    )
    parser.add_argument(
        "--staged",
        action="store_true",
        help="inspect the staged git index",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path.cwd(),
        help="git repository root (default: current directory)",
    )
    args = parser.parse_args(argv)
    if not args.staged:
        parser.error("--staged is required")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = inspect_staged_repository(args.repo_root)
    except (OSError, RuntimeError):
        report = {
            "schema_version": "1.0",
            "status": "ERROR",
            "checked_paths": [],
            "findings": [
                {
                    "code": "GUARD_ERROR",
                    "path": ".",
                    "detail": "staged-index inspection failed closed",
                }
            ],
        }
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 2
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    return 0 if report.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
