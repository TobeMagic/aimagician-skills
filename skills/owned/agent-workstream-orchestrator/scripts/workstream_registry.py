#!/usr/bin/env python3
"""Preview or update a repository-local agent workstream registry."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_STATES = {
    "planned",
    "ready",
    "running",
    "waiting",
    "blocked",
    "failed",
    "handoff",
    "integrated",
    "closed",
}
VALID_MODES = {"read-only", "bounded-write", "worktree", "integration"}


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    subcommands = command.add_subparsers(dest="action", required=True)

    for name in ("init", "list", "validate"):
        item = subcommands.add_parser(name)
        add_common(item)
        if name == "init":
            item.add_argument("--write", action="store_true")

    add = subcommands.add_parser("add")
    add_common(add)
    add.add_argument("--id", required=True)
    add.add_argument("--objective", required=True)
    add.add_argument("--provider", required=True)
    add.add_argument("--model", default="selected-by-controller")
    add.add_argument("--mode", choices=sorted(VALID_MODES), required=True)
    add.add_argument("--write-scope", action="append", default=[])
    add.add_argument("--write", action="store_true")

    update = subcommands.add_parser("update")
    add_common(update)
    update.add_argument("--id", required=True)
    update.add_argument("--status", choices=sorted(VALID_STATES), required=True)
    update.add_argument("--session")
    update.add_argument("--evidence", action="append", default=[])
    update.add_argument("--write", action="store_true")
    return command


def add_common(command: argparse.ArgumentParser) -> None:
    command.add_argument("--root", type=Path, default=Path.cwd())
    command.add_argument("--registry", type=Path)


def registry_path(args: argparse.Namespace) -> Path:
    root = args.root.resolve()
    if args.registry:
        path = args.registry
        return path if path.is_absolute() else root / path
    parent = root / (".planning" if (root / ".planning").is_dir() else ".agent")
    return parent / "workstreams" / "registry.json"


def empty_registry() -> dict[str, Any]:
    return {
        "version": 1,
        "parent_objective": "",
        "base_commit": None,
        "shared_surfaces": [],
        "workstreams": [],
    }


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ValueError(f"registry not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("registry root must be an object")
    return data


def validate(data: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if data.get("version") != 1:
        issues.append("version must be 1")
    streams = data.get("workstreams")
    if not isinstance(streams, list):
        return issues + ["workstreams must be an array"]

    seen: set[str] = set()
    write_owners: dict[str, str] = {}
    for index, stream in enumerate(streams):
        label = f"workstreams[{index}]"
        if not isinstance(stream, dict):
            issues.append(f"{label} must be an object")
            continue
        stream_id = stream.get("id")
        if not isinstance(stream_id, str) or not stream_id.strip():
            issues.append(f"{label}.id is required")
        elif stream_id in seen:
            issues.append(f"duplicate workstream id: {stream_id}")
        else:
            seen.add(stream_id)
        if stream.get("status") not in VALID_STATES:
            issues.append(f"{label}.status is invalid")
        if stream.get("mode") not in VALID_MODES:
            issues.append(f"{label}.mode is invalid")
        if not stream.get("objective"):
            issues.append(f"{label}.objective is required")
        if not stream.get("provider"):
            issues.append(f"{label}.provider is required")
        for scope in stream.get("write_scope", []):
            owner = write_owners.get(scope)
            if owner and owner != stream_id:
                issues.append(f"write scope {scope!r} is owned by both {owner} and {stream_id}")
            elif isinstance(stream_id, str):
                write_owners[scope] = stream_id
    return issues


def write_or_preview(path: Path, data: dict[str, Any], write: bool) -> None:
    payload = json.dumps(data, ensure_ascii=True, indent=2) + "\n"
    if not write:
        print(f"PREVIEW {path}")
        print(payload, end="")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    print(f"WROTE {path}")


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def main() -> int:
    args = parser().parse_args()
    path = registry_path(args)
    try:
        if args.action == "init":
            if path.exists():
                raise ValueError(f"refusing to overwrite existing registry: {path}")
            write_or_preview(path, empty_registry(), args.write)
            return 0

        data = load(path)
        if args.action == "validate":
            issues = validate(data)
            if issues:
                for issue in issues:
                    print(f"ERROR {issue}", file=sys.stderr)
                return 1
            print(f"VALID {path} ({len(data['workstreams'])} workstreams)")
            return 0

        if args.action == "list":
            for stream in data.get("workstreams", []):
                print(
                    "\t".join(
                        str(stream.get(key) or "-")
                        for key in ("id", "status", "mode", "provider", "model", "session_id")
                    )
                )
            return 0

        streams = data.setdefault("workstreams", [])
        target = next((item for item in streams if item.get("id") == args.id), None)
        if args.action == "add":
            if target:
                raise ValueError(f"workstream already exists: {args.id}")
            streams.append(
                {
                    "id": args.id,
                    "objective": args.objective,
                    "status": "planned",
                    "mode": args.mode,
                    "provider": args.provider,
                    "model": args.model,
                    "session_id": None,
                    "last_activity_at": None,
                    "source_context": [],
                    "required_skills": [],
                    "dependencies": [],
                    "read_scope": [],
                    "write_scope": args.write_scope,
                    "forbidden_scope": [],
                    "branch": None,
                    "worktree": None,
                    "expected_output": "",
                    "validation": [],
                    "evidence": [],
                    "handoff": None,
                    "blockers": [],
                }
            )
        elif args.action == "update":
            if not target:
                raise ValueError(f"workstream not found: {args.id}")
            target["status"] = args.status
            target["last_activity_at"] = now()
            if args.session:
                target["session_id"] = args.session
            if args.evidence:
                target.setdefault("evidence", []).extend(args.evidence)

        issues = validate(data)
        if issues:
            raise ValueError("; ".join(issues))
        write_or_preview(path, data, args.write)
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
