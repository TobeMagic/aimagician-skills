#!/usr/bin/env python3
"""Collect static repository evidence for interview playbook generation."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path


SKIP_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "target",
    ".next",
    ".nuxt",
}

MANIFEST_NAMES = {
    "README.md",
    "README.MD",
    "pyproject.toml",
    "requirements.txt",
    "requirements-test.txt",
    "package.json",
    "pom.xml",
    "build.gradle",
    "settings.gradle",
    "go.mod",
    "Cargo.toml",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
}

KEYWORD_PATTERNS = {
    "java": r"\b(Java|Spring|Spring Boot|JVM|MyBatis|Hibernate)\b",
    "python": r"\b(FastAPI|Pydantic|Celery|SQLAlchemy|asyncio|Django|Flask)\b",
    "agent_ai": r"\b(Agent|RAG|MCP|Skill|tool call|function call|embedding|vector|LLM|OpenAI|LangChain|LangGraph)\b",
    "data_cache_mq": r"\b(MySQL|PostgreSQL|Redis|Kafka|RocketMQ|RabbitMQ|Elasticsearch|MongoDB)\b",
    "graph_vector": r"\b(Neo4j|GraphQL|Weaviate|Milvus|Pinecone|Chroma|pgvector)\b",
    "infra": r"\b(Kubernetes|k8s|Cloud Run|Docker|Helm|Terraform|OpenTelemetry|Prometheus|Grafana)\b",
    "security": r"\b(auth|authorization|permission|tenant|secret|token|JWT|OAuth|rate limit|sandbox)\b",
}

ROUTE_PATTERNS = [
    re.compile(r"@(router|app)\.(get|post|put|delete|patch)\(", re.IGNORECASE),
    re.compile(r"\bAPIRouter\b"),
    re.compile(r"@(RestController|Controller|RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping)\b"),
    re.compile(r"\b(FastMCP|mcp\.tool|server\.tool)\b", re.IGNORECASE),
    re.compile(r"\b(GraphQL|strawberry|graphene)\b", re.IGNORECASE),
]


@dataclass
class Match:
    path: str
    line: int
    text: str


def run_git(repo: Path, args: list[str]) -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=10,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except Exception:
        return "unknown"
    return proc.stdout.strip() if proc.returncode == 0 and proc.stdout.strip() else "unknown"


def iter_files(repo: Path, max_files: int) -> list[Path]:
    files: list[Path] = []
    for root, dirs, filenames in os.walk(repo):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        for filename in filenames:
            path = Path(root) / filename
            if path.is_file():
                files.append(path)
                if len(files) >= max_files:
                    return sorted(files)
    return sorted(files)


def rel(repo: Path, path: Path) -> str:
    try:
        return path.relative_to(repo).as_posix()
    except ValueError:
        return path.as_posix()


def read_text(path: Path, max_bytes: int = 120_000) -> str:
    try:
        data = path.read_bytes()[:max_bytes]
        return data.decode("utf-8", "replace")
    except Exception:
        return ""


def collect_manifests(repo: Path, files: list[Path]) -> list[str]:
    manifests = []
    for path in files:
        if path.name in MANIFEST_NAMES or path.parent.name in {"deploy", "deploy_k8s", "k8s", ".github"}:
            manifests.append(rel(repo, path))
    return sorted(manifests)[:80]


def collect_dirs(repo: Path) -> list[str]:
    interesting = []
    names = {
        "controllers",
        "controller",
        "routers",
        "routes",
        "services",
        "service",
        "modules",
        "providers",
        "repositories",
        "repository",
        "models",
        "schema",
        "schemas",
        "config",
        "deploy",
        "deploy_k8s",
        "k8s",
        "servers",
        "workers",
        "tasks",
        "celery_tasks",
    }
    for root, dirs, _ in os.walk(repo):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRS]
        current = Path(root)
        if current.name in names:
            interesting.append(rel(repo, current))
    return sorted(set(interesting))[:120]


def collect_keyword_hits(repo: Path, files: list[Path], max_hits_per_topic: int) -> dict[str, list[Match]]:
    compiled = {key: re.compile(pattern, re.IGNORECASE) for key, pattern in KEYWORD_PATTERNS.items()}
    hits: dict[str, list[Match]] = {key: [] for key in compiled}
    text_exts = {".py", ".java", ".kt", ".ts", ".tsx", ".js", ".go", ".md", ".yaml", ".yml", ".toml", ".xml", ".gradle", ".json"}

    for path in files:
        if path.suffix not in text_exts and path.name not in MANIFEST_NAMES:
            continue
        text = read_text(path)
        if not text:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            compact = line.strip()
            if not compact or len(compact) > 240:
                continue
            for key, pattern in compiled.items():
                if len(hits[key]) >= max_hits_per_topic:
                    continue
                if pattern.search(compact):
                    hits[key].append(Match(rel(repo, path), line_no, compact))
    return hits


def collect_route_hits(repo: Path, files: list[Path], max_hits: int) -> list[Match]:
    hits: list[Match] = []
    for path in files:
        if path.suffix not in {".py", ".java", ".kt", ".ts", ".tsx", ".js", ".md"}:
            continue
        text = read_text(path)
        for line_no, line in enumerate(text.splitlines(), start=1):
            compact = line.strip()
            if not compact or len(compact) > 240:
                continue
            if any(pattern.search(compact) for pattern in ROUTE_PATTERNS):
                hits.append(Match(rel(repo, path), line_no, compact))
                if len(hits) >= max_hits:
                    return hits
    return hits


def collect_wiki_hints(wiki_root: Path | None, repo_name: str) -> list[str]:
    if not wiki_root:
        return []
    wiki = wiki_root / "wiki"
    if not wiki.is_dir():
        return []
    hints: list[str] = []
    for path in wiki.rglob("*.md"):
        if path.name == "log.md" or "log_archive" in path.parts:
            continue
        text = read_text(path, 80_000)
        if repo_name.lower() in text.lower() or repo_name.replace("-", "_").lower() in text.lower():
            hints.append(path.relative_to(wiki_root).as_posix())
    return sorted(set(hints))[:80]


def build_payload(args: argparse.Namespace) -> dict[str, object]:
    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        raise SystemExit(f"Repo path does not exist: {repo}")

    files = iter_files(repo, args.max_files)
    wiki_root = Path(args.wiki_root).expanduser().resolve() if args.wiki_root else None
    repo_name = args.service_name or repo.name
    keyword_hits = collect_keyword_hits(repo, files, args.max_hits_per_topic)

    return {
        "repo": repo.as_posix(),
        "repo_name": repo_name,
        "git": {
            "branch": run_git(repo, ["branch", "--show-current"]),
            "head": run_git(repo, ["rev-parse", "--short", "HEAD"]),
            "remote": run_git(repo, ["remote", "get-url", "origin"]),
            "dirty_count": len([line for line in run_git(repo, ["status", "--porcelain"]).splitlines() if line.strip()]),
        },
        "counts": {
            "files_scanned": len(files),
        },
        "manifests_and_docs": collect_manifests(repo, files),
        "interesting_dirs": collect_dirs(repo),
        "route_and_surface_evidence": [asdict(item) for item in collect_route_hits(repo, files, args.max_route_hits)],
        "keyword_evidence": {key: [asdict(item) for item in value] for key, value in keyword_hits.items() if value},
        "wiki_hints": collect_wiki_hints(wiki_root, repo_name),
    }


def render_markdown(payload: dict[str, object]) -> str:
    lines: list[str] = []
    lines.append(f"# Interview Evidence Inventory: {payload['repo_name']}")
    lines.append("")
    lines.append("## Repo")
    lines.append("")
    lines.append(f"- path: `{payload['repo']}`")
    git = payload["git"]
    assert isinstance(git, dict)
    for key in ["branch", "head", "remote", "dirty_count"]:
        lines.append(f"- {key}: `{git.get(key)}`")
    lines.append("")

    lines.append("## Wiki hints")
    lines.append("")
    wiki_hints = payload.get("wiki_hints") or []
    if wiki_hints:
        lines.extend(f"- `{item}`" for item in wiki_hints)
    else:
        lines.append("- No matching wiki pages found.")
    lines.append("")

    lines.append("## Manifests and docs")
    lines.append("")
    manifests = payload.get("manifests_and_docs") or []
    lines.extend(f"- `{item}`" for item in manifests) if manifests else lines.append("- None found.")
    lines.append("")

    lines.append("## Interesting directories")
    lines.append("")
    dirs = payload.get("interesting_dirs") or []
    lines.extend(f"- `{item}`" for item in dirs) if dirs else lines.append("- None found.")
    lines.append("")

    lines.append("## Route and API surface evidence")
    lines.append("")
    route_hits = payload.get("route_and_surface_evidence") or []
    if route_hits:
        for item in route_hits:
            lines.append(f"- `{item['path']}:{item['line']}` {item['text']}")
    else:
        lines.append("- None found.")
    lines.append("")

    lines.append("## Keyword evidence")
    lines.append("")
    keyword_evidence = payload.get("keyword_evidence") or {}
    if isinstance(keyword_evidence, dict) and keyword_evidence:
        for topic, matches in keyword_evidence.items():
            lines.append(f"### {topic}")
            lines.append("")
            for item in matches:
                lines.append(f"- `{item['path']}:{item['line']}` {item['text']}")
            lines.append("")
    else:
        lines.append("- None found.")

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", help="Target repository path")
    parser.add_argument("--wiki-root", help="Optional LLM-know-how-wiki root")
    parser.add_argument("--service-name", help="Service/repo name to search in wiki")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output", help="Optional output file path; stdout when omitted")
    parser.add_argument("--max-files", type=int, default=2500)
    parser.add_argument("--max-route-hits", type=int, default=80)
    parser.add_argument("--max-hits-per-topic", type=int, default=30)
    args = parser.parse_args()

    payload = build_payload(args)
    if args.format == "json":
        output = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    else:
        output = render_markdown(payload)

    if args.output:
        Path(args.output).expanduser().write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
