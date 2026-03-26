#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


EXT_TO_TECH = {
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".py": "Python",
    ".go": "Go",
    ".rs": "Rust",
    ".java": "Java",
    ".kt": "Kotlin",
    ".cs": "C#",
    ".rb": "Ruby",
    ".php": "PHP",
    ".swift": "Swift",
    ".dart": "Dart",
    ".scala": "Scala",
    ".sh": "Shell",
    ".sql": "SQL",
    ".toml": "TOML",
    ".yml": "YAML",
    ".yaml": "YAML",
}


KEY_DIR_HINTS = [
    "src",
    "app",
    "server",
    "backend",
    "frontend",
    "web",
    "packages",
    "skills",
    "catalog",
    ".planning",
]


IGNORE_DIRS = {
    ".git",
    "node_modules",
    "dist",
    "build",
    "coverage",
    ".venn",
    ".venv",
    ".next",
    ".output",
    "target",
    "__pycache__",
}


def run_git_command(cmd: list[str], cwd: Path, default: str = "") -> str:
    try:
        out = subprocess.check_output(cmd, cwd=str(cwd), text=True, stderr=subprocess.DEVNULL).strip()
        return out
    except Exception:
        return default


def infer_project_name(path: Path) -> str:
    return path.name.replace("_", " ").replace("-", " ").title() if path.name else "Unknown Project"


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def parse_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def parse_toml_minimal(path: Path) -> dict:
    content = read_text(path)
    data: dict[str, object] = {}
    section = None
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            continue
        if "=" not in line or section is None:
            continue
        key, value = [x.strip() for x in line.split("=", 1)]
        if section == "project" and key in {"name", "version"}:
            val = value.strip().strip('"').strip("'")
            if section not in data:
                data[section] = {}
            (data[section] or {}).__setitem__(key, val)
    return data


def detect_stack(root: Path) -> list[str]:
    counts: dict[str, int] = {}
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".turbo")]
        for file in files:
            suffix = Path(file).suffix.lower()
            tech = EXT_TO_TECH.get(suffix)
            if tech:
                counts[tech] = counts.get(tech, 0) + 1
            # manifest heuristics
            if file.lower() == "package.json":
                counts["Node.js"] = counts.get("Node.js", 0) + 8
            elif file.lower() == "pyproject.toml":
                counts["Python"] = counts.get("Python", 0) + 8
            elif file.lower() == "requirements.txt":
                counts["Python"] = counts.get("Python", 0) + 6
            elif file.lower() == "go.mod":
                counts["Go"] = counts.get("Go", 0) + 8
    return [k for k, _ in sorted(counts.items(), key=lambda kv: kv[1], reverse=True)]


def detect_framework_hints(root: Path) -> list[str]:
    hints: set[str] = set()
    if (root / "package.json").exists():
        manifest = parse_json(root / "package.json")
        deps = {
            **manifest.get("dependencies", {}),
            **manifest.get("devDependencies", {}),
            **manifest.get("peerDependencies", {}),
        }
        for dep in deps:
            if dep in {"react", "preact"}:
                hints.add("React")
            if dep in {"vue", "nuxt"}:
                hints.add("Vue")
            if dep in {"svelte", "sveltekit"}:
                hints.add("Svelte")
            if dep in {"fastapi"}:
                hints.add("FastAPI")
            if dep in {"openai", "anthropic", "@anthropic-ai/sdk"}:
                hints.add("LLM APIs")
            if dep in {"vite", "webpack", "rollup"}:
                hints.add("Frontend Tooling")
    req = read_text(root / "requirements.txt").splitlines()
    if any("fastapi" in line.lower() for line in req):
        hints.add("FastAPI")
    if (root / "pyproject.toml").exists():
        data = parse_toml_minimal(root / "pyproject.toml")
        project = data.get("project", {})
        if isinstance(project, dict) and project.get("name"):
            hints.add("Python")
        for dep_key in ["dependencies", "dev-dependencies"]:
            val = data.get(dep_key)
            if isinstance(val, list) and any("fastapi" in str(v).lower() for v in val):
                hints.add("FastAPI")
    if (root / "go.mod").exists():
        hints.add("Go")
    for key in KEY_DIR_HINTS:
        if (root / key).exists():
            hints.add(key.title().replace("_", " "))
    return sorted(hints)


def read_summary(root: Path, max_len: int = 220) -> str:
    candidates = []
    readme = read_text(root / "README.md")
    if readme:
        clean = re.sub(r"^#\s*.*\n", "", readme, flags=re.MULTILINE).strip()
        first_paragraph = clean.split("\n\n")[0].strip()
        if first_paragraph:
            candidates.append(first_paragraph.replace("\n", " ").strip())
    if not candidates:
        return ""
    text = candidates[0]
    return text if len(text) <= max_len else text[: max_len - 1].rstrip() + "…"


def infer_project_start_date(root: Path) -> str:
    git_date = run_git_command(
        ["git", "log", "--reverse", "--format=%ad", "--date=short"], root
    )
    if git_date:
        return git_date.splitlines()[0]
    return ""


def infer_project_end_date(root: Path) -> str:
    head = run_git_command(
        ["git", "log", "-1", "--format=%ad", "--date=short"], root
    )
    return head or "Present"


def build_project_entry(root: Path, start: str, end: str, tech: list[str], args: argparse.Namespace) -> dict:
    project_name = args.project_name or infer_project_name(root)
    summary = args.summary or read_summary(root)
    bullets = []
    if summary:
        bullets.append(f"Project scope: {summary}")
    bullets.append("Implemented architecture that maps owned and external skills into multi-target bootstrap targets.")
    if root.joinpath("catalog").exists():
    bullets.append("Maintained catalog-driven skill discovery and installation workflow.")
    if root.joinpath(".planning").exists():
        bullets.append("Tracked milestone planning and execution artifacts through GSD-compatible planning files.")
    if not bullets[0]:
        bullets = bullets[1:]
    return {
        "name": project_name,
        "role": "Owner",
        "start": start or "",
        "end": end or "Present",
        "tech": tech[:10],
        "bullets": bullets[:6],
    }


def gather_contacts(name: str, args: argparse.Namespace) -> dict:
    return {
        "email": args.email or "",
        "phone": args.phone or "",
        "location": args.location or "",
        "links": args.links,
    }


def extract_resume(root: Path, args: argparse.Namespace) -> dict:
    stack = detect_stack(root)
    frameworks = detect_framework_hints(root)
    skill_list = sorted(set([*stack, *frameworks]))
    start = infer_project_start_date(root)
    end = args.end_date or infer_project_end_date(root) or "Present"
    projects = []
    if not args.no_projects:
        projects.append(build_project_entry(root, start, end, skill_list, args))

    resume = {
        "name": args.name or "Unnamed",
        "title": args.title or "Software Engineer",
        "contacts": gather_contacts(args.name, args),
        "summary": args.summary
        or f"{args.title or 'Software Engineer'} with project-level execution and automation focus.",
        "skills": skill_list,
        "experiences": [],
        "projects": projects,
        "education": [],
    }
    # Keep stable schema output ordering
    return {k: resume[k] for k in ["name", "title", "contacts", "summary", "skills", "experiences", "projects", "education"]}


def write_output(path: Path, payload: dict, force: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not force:
        raise FileExistsError(f"{path} exists; use --force to overwrite.")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract repository metadata to resume.json")
    parser.add_argument("--name", default="TBD", help="Person name (optional)")
    parser.add_argument("--title", default="Software Engineer", help="Target role / job title")
    parser.add_argument("--email", default="", help="Contact email")
    parser.add_argument("--phone", default="", help="Contact phone")
    parser.add_argument("--location", default="", help="Location")
    parser.add_argument("--summary", default="", help="Resume/project summary override")
    parser.add_argument("--links", action="append", default=[], help="Profile links, repeatable")
    parser.add_argument("--project-name", default="", help="Project name override")
    parser.add_argument("--output", default="./statics/resume.json", help="Output JSON path")
    parser.add_argument("--source-root", default=".", help="Repository root")
    parser.add_argument("--no-projects", action="store_true", help="Do not include generated project entry")
    parser.add_argument("--end-date", default="", help="Project end date, e.g. Present")
    parser.add_argument("--force", action="store_true", help="Overwrite existing output file")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.source_root).resolve()
    if not root.exists():
        print(f"ERROR: source root not found: {root}", file=sys.stderr)
        return 1
    payload = extract_resume(root, args)
    output = Path(args.output).expanduser()
    if not output.is_absolute():
        output = (Path.cwd() / output).resolve()
    try:
        write_output(output, payload, args.force)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Generated resume JSON at {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
