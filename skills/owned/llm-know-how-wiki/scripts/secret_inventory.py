#!/usr/bin/env python3
"""Scan workspace repositories for secrets and copy findings into a local wiki vault."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import date, datetime
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

TARGETED_CACHE_DIRS = {".cache", ".config", ".npm", ".pip", ".docker", ".aws", ".gcloud"}

TEXT_SUFFIXES = {
    ".env",
    ".ini",
    ".cfg",
    ".conf",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".txt",
    ".md",
    ".sh",
    ".bash",
    ".zsh",
    ".ps1",
    ".properties",
    ".tf",
    ".tfvars",
    ".pem",
    ".key",
}

HIGH_RISK_NAMES = {
    ".env",
    ".env.local",
    ".env.development",
    ".env.production",
    ".npmrc",
    ".pypirc",
    ".netrc",
    "credentials",
    "config",
    "terraform.tfstate",
    "terraform.tfvars",
    "service-account.json",
}

SECRET_KEY_RE = re.compile(
    r"(?:TOKEN|SECRET|PASSWORD|PASS|API[_-]?KEY|ACCESS[_-]?KEY|PRIVATE[_-]?KEY|CLIENT[_-]?SECRET|AUTH)",
    re.I,
)


@dataclass(frozen=True)
class SecretPattern:
    name: str
    regex: re.Pattern[str]
    key_group: str | None = None
    value_group: str = "value"


PATTERNS = [
    SecretPattern(
        "env_secret_assignment",
        re.compile(
            r"(?P<key>[A-Za-z_][A-Za-z0-9_]*(?:TOKEN|SECRET|PASSWORD|PASS|API_KEY|ACCESS_KEY|PRIVATE_KEY|CLIENT_SECRET|AUTH)[A-Za-z0-9_]*)"
            r"\s*=\s*[\"']?(?P<value>(?!(?:REDACTED|<|\*{3,}|x{3,}))[^\s\"'#;]{8,})[\"']?",
            re.I,
        ),
        key_group="key",
    ),
    SecretPattern(
        "generic_secret_assignment",
        re.compile(
            r"\b(?P<key>api[_-]?key|access[_-]?token|auth[_-]?token|secret[_-]?key|client[_-]?secret|app[_ -]?secret|password)"
            r"\s*[:=]\s*[\"']?(?P<value>(?!(?:REDACTED|<|\*{3,}|x{3,}))[A-Za-z0-9_./+=:@-]{12,})[\"']?",
            re.I,
        ),
        key_group="key",
    ),
    SecretPattern(
        "bearer_token",
        re.compile(r"\bBearer\s+(?P<value>[A-Za-z0-9_./+=-]{20,})", re.I),
    ),
    SecretPattern(
        "openai_style_key",
        re.compile(r"(?<![A-Za-z0-9])(?P<value>sk-[A-Za-z0-9_-]{20,})"),
    ),
    SecretPattern(
        "aws_access_key",
        re.compile(r"(?<![A-Z0-9])(?P<value>AKIA[0-9A-Z]{16})"),
    ),
    SecretPattern(
        "url_basic_auth",
        re.compile(r"://(?P<value>[^/\s:@]+:[^/\s:@]{8,})@", re.I),
    ),
    SecretPattern(
        "feishu_authcode_url",
        re.compile(r"authcode/\?code=(?P<value>(?!REDACTED)[A-Za-z0-9_-]{8,})", re.I),
    ),
]


@dataclass
class Finding:
    repo: str
    path: str
    line: int
    pattern: str
    env_key: str
    fingerprint: str
    value: str


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


def git_text(repo: Path, args: list[str], default: str = "unknown") -> str:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
        )
    except Exception:
        return default
    if proc.returncode != 0 or not proc.stdout.strip():
        return default
    return proc.stdout.strip()


def discover_repos(workspace: Path, max_depth: int) -> list[Path]:
    repos: list[Path] = []
    workspace = workspace.resolve()
    for dirpath, dirnames, _ in os.walk(workspace):
        current = Path(dirpath)
        rel_parts = current.relative_to(workspace).parts
        if len(rel_parts) > max_depth:
            dirnames[:] = []
            continue

        dirnames[:] = [
            name
            for name in sorted(dirnames)
            if name not in SKIP_DIRS and not (name.startswith(".") and name not in TARGETED_CACHE_DIRS)
        ]

        if is_git_repo(current):
            repos.append(current)
            dirnames[:] = []

    if not repos:
        repos.append(workspace)
    return sorted(repos)


def is_controlled_vault(path: Path, wiki_root: Path | None) -> bool:
    if not wiki_root:
        return False
    try:
        rel = path.resolve().relative_to(wiki_root.resolve())
    except ValueError:
        return False
    return rel.parts[:1] == ("secrets",) and (
        rel.name.endswith(".local.env") or (rel.name.startswith("vault") and rel.suffix == ".env")
    )


def should_scan_file(path: Path, repo: Path, wiki_root: Path | None) -> bool:
    if is_controlled_vault(path, wiki_root):
        return False
    rel_parts = path.relative_to(repo).parts
    if any(part in SKIP_DIRS for part in rel_parts):
        return False
    name = path.name
    suffix = path.suffix.lower()
    in_targeted_cache = any(part in TARGETED_CACHE_DIRS for part in rel_parts)
    if in_targeted_cache:
        return name in HIGH_RISK_NAMES or suffix in {".env", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg"}
    return name in HIGH_RISK_NAMES or suffix in TEXT_SUFFIXES or SECRET_KEY_RE.search(name) is not None


def secret_fingerprint(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def normalize_env_key(raw_key: str | None, pattern: str, fingerprint: str) -> str:
    if raw_key:
        key = re.sub(r"[^A-Za-z0-9_]+", "_", raw_key.upper()).strip("_")
    else:
        key = "SECRET_" + re.sub(r"[^A-Z0-9_]+", "_", pattern.upper()).strip("_")
    if not key or key[0].isdigit():
        key = "SECRET_" + key
    return f"{key}_{fingerprint.split(':', 1)[1][:8]}"


def quote_env_value(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def redacted_preview(value: str) -> str:
    if len(value) <= 8:
        return "<redacted>"
    return f"{value[:3]}...{value[-3:]}"


def scan_repo(repo: Path, workspace: Path, wiki_root: Path | None) -> list[Finding]:
    findings: list[Finding] = []
    repo_rel = repo.relative_to(workspace).as_posix() if repo != workspace else "."
    for current, dirnames, filenames in os.walk(repo):
        current_path = Path(current)
        rel_parts = current_path.relative_to(repo).parts
        dirnames[:] = [
            dirname
            for dirname in sorted(dirnames)
            if dirname not in SKIP_DIRS and not (dirname.startswith(".") and dirname not in TARGETED_CACHE_DIRS)
        ]
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        for filename in sorted(filenames):
            path = current_path / filename
            if not should_scan_file(path, repo, wiki_root):
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            except OSError:
                continue
            for line_no, line in enumerate(text.splitlines(), start=1):
                for pattern in PATTERNS:
                    for match in pattern.regex.finditer(line):
                        value = match.group(pattern.value_group).strip()
                        if not value or value.upper() in {"TRUE", "FALSE", "NULL", "NONE"}:
                            continue
                        fingerprint = secret_fingerprint(value)
                        raw_key = match.group(pattern.key_group) if pattern.key_group else None
                        findings.append(
                            Finding(
                                repo=repo_rel,
                                path=path.relative_to(repo).as_posix(),
                                line=line_no,
                                pattern=pattern.name,
                                env_key=normalize_env_key(raw_key, pattern.name, fingerprint),
                                fingerprint=fingerprint,
                                value=value,
                            )
                        )
    return findings


def load_existing_fingerprints(registry: Path) -> set[str]:
    if not registry.exists():
        return set()
    text = registry.read_text(encoding="utf-8")
    return set(re.findall(r"fingerprint:\s*(sha256:[a-f0-9]{16,64})", text))


def load_existing_env_keys(vault: Path) -> set[str]:
    if not vault.exists():
        return set()
    keys: set[str] = set()
    for line in vault.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            keys.add(line.split("=", 1)[0].strip())
    return keys


def unique_findings(findings: list[Finding]) -> list[Finding]:
    seen: set[str] = set()
    unique: list[Finding] = []
    for finding in findings:
        if finding.fingerprint in seen:
            continue
        seen.add(finding.fingerprint)
        unique.append(finding)
    return unique


def write_vault_and_registry(wiki_root: Path, findings: list[Finding], dry_run: bool) -> dict[str, int]:
    secrets_dir = wiki_root / "secrets"
    vault = secrets_dir / "vault.local.env"
    registry = secrets_dir / "registry.yaml"
    if dry_run:
        return {"vault_added": 0, "registry_added": 0}

    secrets_dir.mkdir(parents=True, exist_ok=True)
    gitignore = secrets_dir / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text("*.local.env\nvault*.env\ncache/\n", encoding="utf-8")
    if not registry.exists():
        registry.write_text("# LLM wiki secret registry. Metadata only; do not store secret values here.\nsecrets: []\n", encoding="utf-8")

    existing_fingerprints = load_existing_fingerprints(registry)
    existing_env_keys = load_existing_env_keys(vault)
    vault_lines: list[str] = []
    registry_lines: list[str] = []
    today = date.today().isoformat()

    for finding in unique_findings(findings):
        if finding.fingerprint in existing_fingerprints:
            continue
        env_key = finding.env_key
        suffix = 2
        while env_key in existing_env_keys:
            env_key = f"{finding.env_key}_{suffix}"
            suffix += 1
        existing_env_keys.add(env_key)

        vault_lines.append(f"{env_key}={quote_env_value(finding.value)}")
        registry_lines.extend(
            [
                f"  - id: {env_key.lower()}",
                f"    env_key: {env_key}",
                f"    kind: {finding.pattern}",
                f"    fingerprint: {finding.fingerprint}",
                "    vault_file: secrets/vault.local.env",
                "    source_refs:",
                f"      - repo: {finding.repo}",
                f"        path: {finding.path}",
                f"        line: {finding.line}",
                f"        pattern: {finding.pattern}",
                "    status: active",
                f"    updated: {today}",
            ]
        )
        existing_fingerprints.add(finding.fingerprint)

    if vault_lines:
        with vault.open("a", encoding="utf-8") as handle:
            if vault.exists() and vault.stat().st_size > 0:
                handle.write("\n")
            handle.write("\n".join(vault_lines) + "\n")

    if registry_lines:
        text = registry.read_text(encoding="utf-8")
        if text.strip() == "# LLM wiki secret registry. Metadata only; do not store secret values here.\nsecrets: []":
            text = "# LLM wiki secret registry. Metadata only; do not store secret values here.\nsecrets:\n"
        elif text.rstrip().endswith("secrets: []"):
            text = text.rstrip()[:-2] + "\n"
        with registry.open("w", encoding="utf-8") as handle:
            handle.write(text.rstrip() + "\n")
            handle.write("\n".join(registry_lines) + "\n")

    return {"vault_added": len(vault_lines), "registry_added": len(registry_lines) // 12}


def render_report(workspace: Path, repos: list[Path], findings: list[Finding], wrote_vault: bool) -> str:
    now = datetime.now().isoformat(timespec="seconds")
    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.pattern] = counts.get(finding.pattern, 0) + 1
    lines = [
        f"# Secret Inventory Snapshot - {now}",
        "",
        f"Workspace: `{workspace}`",
        f"Vault write: `{'enabled' if wrote_vault else 'disabled'}`",
        "",
        "## Summary",
        "",
        f"- Repositories scanned: {len(repos)}",
        f"- Findings: {len(findings)}",
        f"- Unique fingerprints: {len({finding.fingerprint for finding in findings})}",
    ]
    for name in sorted(counts):
        lines.append(f"- {name}: {counts[name]}")

    lines.extend(
        [
            "",
            "## Findings",
            "",
            "| Repo | Path | Line | Pattern | Env key | Fingerprint | Preview |",
            "| --- | --- | ---: | --- | --- | --- | --- |",
        ]
    )
    for finding in findings:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{finding.repo}`",
                    f"`{finding.path}`",
                    str(finding.line),
                    f"`{finding.pattern}`",
                    f"`{finding.env_key}`",
                    f"`{finding.fingerprint}`",
                    f"`{redacted_preview(finding.value)}`",
                ]
            )
            + " |"
        )

    if not findings:
        lines.append("| none | none | 0 | none | none | none | none |")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- This report intentionally omits raw secret values.",
            "- Source files are not modified by this script.",
            "- If vault write is enabled, unique values are copied to `secrets/vault.local.env` and metadata is appended to `secrets/registry.yaml`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_raw_snapshot(wiki_root: Path, report: str) -> Path:
    timestamp = datetime.now().strftime("%Y-%m-%dT%H%M%S")
    target = wiki_root / "raw" / "secret_inventory" / f"{timestamp}-secret-scan.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report, encoding="utf-8")
    return target


def append_log(wiki_root: Path, snapshot: Path, findings: list[Finding], wrote_vault: bool) -> None:
    log = wiki_root / "wiki" / "log.md"
    if not log.exists():
        return
    today = date.today().isoformat()
    rel_snapshot = snapshot.relative_to(wiki_root).as_posix()
    entry = (
        f"\n- {today} SECRET_INVENTORY\n"
        "  - sources:\n"
        "    - workspace git repositories\n"
        "  - updated:\n"
        f"    - {rel_snapshot}\n"
        "    - wiki/log.md\n"
        f"  - notes: Secret scan found {len(findings)} finding(s); vault_write={'enabled' if wrote_vault else 'disabled'}.\n"
    )
    with log.open("a", encoding="utf-8") as handle:
        handle.write(entry)


def sanitized_findings(findings: list[Finding]) -> list[dict[str, object]]:
    return [
        {
            "repo": finding.repo,
            "path": finding.path,
            "line": finding.line,
            "pattern": finding.pattern,
            "env_key": finding.env_key,
            "fingerprint": finding.fingerprint,
            "preview": redacted_preview(finding.value),
        }
        for finding in findings
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", help="Workspace root to scan. Defaults to parent of project-local wiki, or cwd.")
    parser.add_argument("--wiki-root", help="Wiki root for writing vault, registry, raw snapshot, and log.")
    parser.add_argument("--max-depth", type=int, default=4, help="Maximum directory depth for repo discovery.")
    parser.add_argument("--dry-run", action="store_true", help="Scan and report without writing vault, raw snapshot, or log.")
    parser.add_argument("--no-write-vault", action="store_true", help="Do not copy discovered values to secrets/vault.local.env.")
    parser.add_argument("--no-write-raw", action="store_true", help="Do not write raw/secret_inventory report.")
    parser.add_argument("--no-log", action="store_true", help="Do not append wiki/log.md.")
    parser.add_argument("--json", action="store_true", help="Emit sanitized JSON summary.")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when any finding is discovered.")
    args = parser.parse_args()

    workspace = resolve_workspace(args.workspace)
    wiki_root = resolve_wiki_root(args.wiki_root, workspace)
    repos = discover_repos(workspace, max_depth=args.max_depth)
    findings: list[Finding] = []
    for repo in repos:
        findings.extend(scan_repo(repo, workspace, wiki_root))

    wrote_vault = bool(wiki_root and findings and not args.dry_run and not args.no_write_vault)
    vault_result = {"vault_added": 0, "registry_added": 0}
    if wrote_vault and wiki_root:
        vault_result = write_vault_and_registry(wiki_root, findings, dry_run=False)

    report = render_report(workspace, repos, findings, wrote_vault)
    snapshot: Path | None = None
    if wiki_root and not args.dry_run and not args.no_write_raw:
        snapshot = write_raw_snapshot(wiki_root, report)
        if not args.no_log:
            append_log(wiki_root, snapshot, findings, wrote_vault)

    if args.json:
        print(
            json.dumps(
                {
                    "workspace": str(workspace),
                    "wiki_root": str(wiki_root) if wiki_root else None,
                    "repositories": len(repos),
                    "findings": len(findings),
                    "unique_fingerprints": len({finding.fingerprint for finding in findings}),
                    "vault_write": wrote_vault,
                    "vault_added": vault_result["vault_added"],
                    "registry_added": vault_result["registry_added"],
                    "snapshot": str(snapshot) if snapshot else None,
                    "items": sanitized_findings(findings),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(f"workspace={workspace}")
        print(f"wiki_root={wiki_root or 'none'}")
        print(f"repos={len(repos)}")
        print(f"findings={len(findings)}")
        print(f"unique_fingerprints={len({finding.fingerprint for finding in findings})}")
        print(f"vault_write={'enabled' if wrote_vault else 'disabled'}")
        print(f"vault_added={vault_result['vault_added']}")
        print(f"registry_added={vault_result['registry_added']}")
        print(f"snapshot={snapshot or 'disabled'}")

    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
