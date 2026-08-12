#!/usr/bin/env python3
"""Run and independently fingerprint the locked Phase 49 Codex acceptance.

This is a parent-side controller, not an authoring surface.  It launches the
locked Codex command, keeps process evidence outside the clean client folder,
captures a stable post-run inventory only after the child exits, constructs
the external run fingerprint, and immediately invokes the independent clean
run validator.  Only a validator PASS with a successful child returns zero.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence


# The installed Skill tree is a frozen authority.  Set this before importing
# any Skill-local module so controller startup cannot create __pycache__ drift.
sys.dont_write_bytecode = True
THIS_DIR = Path(__file__).resolve().parent
SKILL_ROOT = THIS_DIR.parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from validate_window_pptx_v61_clean_pack import (  # noqa: E402
    EVIDENCE_OUTPUT_PATHS,
    OUTPUT_PPTX_PATH,
    PHASE49_LIBRARY_RELATIVE,
    PHYSICAL_REPORT_PATH,
    RULE_QA_PATH,
    _phase49_private_library_identity,
    bundle_fingerprint,
    tree_fingerprint,
    validate_requirement_pack,
    validate_run_fingerprint,
)
from window_pptx.v61_acceptance_settlement import (  # noqa: E402
    AcceptanceSettlementError,
    capture_settled_inventory,
    reject_symlink_components,
    run_in_isolated_process_group,
)
from window_pptx.v61_runtime_identity import (  # noqa: E402
    CONTROLLER_RELATIVE,
    RUNTIME_SCHEMA_NAME,
    RuntimeIdentityError,
    build_runtime_identity_payload,
    read_runtime_identity_manifest,
    verify_runtime_identity_payload,
    write_runtime_identity_manifest,
)


SCHEMA_VERSION = "1.0"
DEFAULT_REQUIREMENT_PACK = "annual-work-report.requirement-pack.v1.json"
DEFAULT_PROMPT = "PRODUCTION_PROMPT.md"
DEFAULT_RUN_ID = "hospital-finance-annual-2025-v61-run-1"
DEFAULT_PROFILE = "phase49-work-report-15"
RUN_FINGERPRINT_NAME = "physical-assembly-run-fingerprint.v1.json"
POST_MANIFEST_NAME = "post-run-manifest.v1.json"
EVENTS_NAME = "codex-events.jsonl"
STDERR_NAME = "codex-stderr.log"
TEST_RUNTIME_MANIFEST_NAME = "test-only-runtime-identity-manifest.v1.json"
RUN_ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class AcceptanceControllerError(RuntimeError):
    """Fail-closed controller configuration or preflight error."""


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _record(root: Path, relative: str) -> dict[str, Any]:
    path = root / PurePosixPath(relative)
    return {
        "path": relative,
        "sha256": _sha256_file(path),
        "size": path.stat().st_size,
    }


def _bytes_record(relative: str, payload: bytes) -> dict[str, Any]:
    return {
        "path": relative,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "size": len(payload),
    }


def _record_or_missing(root: Path, relative: str) -> dict[str, Any]:
    path = root / PurePosixPath(relative)
    try:
        mode = path.lstat().st_mode
    except OSError:
        return {"path": relative, "sha256": "0" * 64, "size": 0}
    if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
        return {"path": relative, "sha256": "0" * 64, "size": 0}
    return _record(root, relative)


def _external_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "sha256": _sha256_file(path),
        "size": path.stat().st_size,
    }


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    text = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ) + "\n"
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def _read_json(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AcceptanceControllerError(f"{label}_INVALID: {exc}") from exc
    if not isinstance(payload, dict):
        raise AcceptanceControllerError(f"{label}_INVALID: object required")
    return payload


def _real_directory(path: Path, label: str) -> Path:
    requested = path.expanduser()
    if requested.is_symlink() or not requested.is_dir():
        raise AcceptanceControllerError(f"{label}_INVALID: {requested}")
    return requested.resolve()


def _validate_harness_request(requested: Path) -> tuple[Path, Path]:
    raw = requested.expanduser()
    try:
        raw = reject_symlink_components(raw, allow_missing_tail=True)
    except AcceptanceSettlementError as exc:
        raise AcceptanceControllerError(str(exc)) from exc
    prospective = raw.resolve(strict=False)
    if raw.exists():
        if not raw.is_dir():
            raise AcceptanceControllerError("HARNESS_DIR_NOT_DIRECTORY")
        if any(raw.iterdir()):
            raise AcceptanceControllerError("HARNESS_DIR_NOT_EMPTY")
    return raw, prospective


def _materialize_harness_dir(raw: Path, prospective: Path) -> Path:
    if not raw.exists():
        raw.mkdir(parents=True, exist_ok=False)
    harness = raw.resolve()
    try:
        reject_symlink_components(raw)
    except AcceptanceSettlementError as exc:
        raise AcceptanceControllerError(str(exc)) from exc
    if harness != prospective or raw.is_symlink():
        raise AcceptanceControllerError("HARNESS_DIR_CHANGED_DURING_PREFLIGHT")
    return harness


def _require_pairwise_disjoint(named_paths: Mapping[str, Path]) -> None:
    items = list(named_paths.items())
    for index, (left_name, left) in enumerate(items):
        for right_name, right in items[index + 1 :]:
            if (
                left == right
                or left.is_relative_to(right)
                or right.is_relative_to(left)
            ):
                raise AcceptanceControllerError(
                    f"AUTHORITY_PATHS_OVERLAP: {left_name}:{left} {right_name}:{right}"
                )


def _codex_home_for_installed_skill(installed: Path) -> Path:
    if installed.name != "window-pptx" or installed.parent.name != "skills":
        raise AcceptanceControllerError(
            "INSTALLED_SKILL_MUST_BE_CODEX_HOME_SKILLS_WINDOW_PPTX"
        )
    codex_home = installed.parent.parent
    if codex_home.is_symlink() or not codex_home.is_dir():
        raise AcceptanceControllerError("CODEX_HOME_INVALID")
    return codex_home.resolve()


def _require_installed_controller_origin(installed: Path, *, test_bypass: bool) -> None:
    """Production must execute this controller from the attested Skill tree."""

    if test_bypass:
        return
    expected_root = installed.resolve()
    expected_entry = (expected_root / CONTROLLER_RELATIVE).resolve(strict=True)
    if SKILL_ROOT.resolve() != expected_root or Path(__file__).resolve() != expected_entry:
        raise AcceptanceControllerError("CONTROLLER_NOT_RUNNING_FROM_INSTALLED_SKILL")


def _resolve_test_codex_identity(codex_bin: str) -> dict[str, Any]:
    """Resolve a pytest double; production never calls this PATH-aware helper."""

    candidate = (
        shutil.which(codex_bin)
        if os.sep not in codex_bin and (os.altsep is None or os.altsep not in codex_bin)
        else codex_bin
    )
    if not candidate:
        raise AcceptanceControllerError("CODEX_EXECUTABLE_NOT_FOUND")
    requested = Path(candidate).expanduser()
    if not requested.exists() or not requested.is_file():
        raise AcceptanceControllerError("CODEX_EXECUTABLE_INVALID")
    resolved = requested.resolve(strict=True)
    try:
        completed = subprocess.run(
            [str(resolved), "--version"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise AcceptanceControllerError(
            f"CODEX_VERSION_PROBE_FAILED: {exc}"
        ) from exc
    version = completed.stdout.decode("utf-8", errors="replace").strip()
    if completed.returncode != 0 or not version or "\n" in version:
        raise AcceptanceControllerError("CODEX_VERSION_PROBE_INVALID")
    return {
        "requested_path": str(requested.absolute()),
        "resolved_path": str(resolved),
        "sha256": _sha256_file(resolved),
        "size": resolved.stat().st_size,
        "version": version,
    }


def _load_runtime_identity(
    *,
    manifest_path: Path | str,
    expected_manifest_sha256: str,
    installed_skill_root: Path,
    expected_installed_skill_sha256: str,
    production: bool,
) -> dict[str, Any]:
    try:
        manifest, raw, payload = read_runtime_identity_manifest(
            manifest_path,
            expected_manifest_sha256,
        )
        _validate_schema(payload, RUNTIME_SCHEMA_NAME)
        components = verify_runtime_identity_payload(
            payload,
            installed_skill_root=installed_skill_root,
            expected_installed_skill_sha256=expected_installed_skill_sha256,
            actual_controller_entry=Path(__file__).resolve(),
            production=production,
        )
    except RuntimeIdentityError as exc:
        raise AcceptanceControllerError(str(exc)) from exc
    return {
        "path": manifest,
        "bytes": raw,
        "payload": payload,
        "record": {
            "path": str(manifest),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "size": len(raw),
        },
        "components": components,
    }


def _materialize_test_runtime_identity(
    *,
    harness_prospective: Path,
    installed_skill_root: Path,
    expected_installed_skill_sha256: str,
    test_codex_identity: Mapping[str, Any],
) -> tuple[Path, str]:
    """Create the programmatic-only test authority; no CLI reaches this path."""

    manifest = harness_prospective.with_name(
        f".{harness_prospective.name}.{TEST_RUNTIME_MANIFEST_NAME}"
    )
    try:
        payload = build_runtime_identity_payload(
            installed_skill_root=installed_skill_root,
            expected_installed_skill_sha256=expected_installed_skill_sha256,
            controller_interpreter=Path(sys.executable).resolve(),
            codex_native_executable=Path(str(test_codex_identity["resolved_path"])),
            allow_test_non_native=True,
        )
        _validate_schema(payload, RUNTIME_SCHEMA_NAME)
        record = write_runtime_identity_manifest(manifest, payload)
    except RuntimeIdentityError as exc:
        raise AcceptanceControllerError(str(exc)) from exc
    return Path(record["path"]), str(record["sha256"])


def _logical_argv(project: Path) -> list[str]:
    return [
        "codex",
        "exec",
        "--dangerously-bypass-approvals-and-sandbox",
        "--skip-git-repo-check",
        "-c",
        'model_provider="openai"',
        "-c",
        'model_reasoning_effort="medium"',
        "--cd",
        str(project),
        "-m",
        "gpt-5.6-terra",
        "--json",
        "-",
    ]


def _validate_schema(payload: Mapping[str, Any], schema_name: str) -> None:
    try:
        import jsonschema
    except ImportError as exc:  # pragma: no cover - installation contract
        raise AcceptanceControllerError("JSONSCHEMA_UNAVAILABLE") from exc
    schema = _read_json(SKILL_ROOT / "schemas" / schema_name, "SCHEMA")
    errors = sorted(
        jsonschema.Draft202012Validator(schema).iter_errors(payload),
        key=lambda item: tuple(str(part) for part in item.absolute_path),
    )
    if errors:
        where = ".".join(str(part) for part in errors[0].absolute_path) or "$"
        raise AcceptanceControllerError(
            f"SCHEMA_INVALID: {schema_name}: {where}: {errors[0].message}"
        )


def _resolve_private_identity(
    private_root: Path,
    installed_skill: Path,
    library_relative: str,
) -> tuple[Path, dict[str, str]]:
    root = _real_directory(private_root, "PRIVATE_ROOT")
    pure = PurePosixPath(library_relative)
    if pure.is_absolute() or ".." in pure.parts or "\\" in library_relative:
        raise AcceptanceControllerError("PRIVATE_LIBRARY_PATH_INVALID")
    library = root / pure
    if library.is_symlink() or not library.is_file():
        raise AcceptanceControllerError("PRIVATE_LIBRARY_INDEX_MISSING")
    library = library.resolve()
    if not library.is_relative_to(root):
        raise AcceptanceControllerError("PRIVATE_LIBRARY_INDEX_ESCAPE")
    try:
        identity = _phase49_private_library_identity(
            library,
            allowed_source_roots=(root, installed_skill),
        )
    except (OSError, ValueError) as exc:
        raise AcceptanceControllerError(f"PRIVATE_LIBRARY_INDEX_INVALID: {exc}") from exc
    private_root_sha = identity["private_root_sha256"]
    if not isinstance(private_root_sha, str):
        raise AcceptanceControllerError("PRIVATE_ROOT_SHA256_MISSING")
    library_sha = _sha256_file(library)

    profile_path = (
        installed_skill
        / "registries"
        / "v61-binding-profiles"
        / f"{DEFAULT_PROFILE}.binding-profile.v1.json"
    )
    if profile_path.is_symlink() or not profile_path.is_file():
        raise AcceptanceControllerError("INSTALLED_PROFILE_MISSING")
    profile = _read_json(profile_path, "INSTALLED_PROFILE")
    if profile.get("library_index_sha256") != library_sha:
        raise AcceptanceControllerError("PRIVATE_LIBRARY_PROFILE_SHA256_MISMATCH")
    return root, {
        "resolution_source": "environment-private-root",
        "private_root_sha256": private_root_sha,
        "library_index_sha256": library_sha,
    }


def _inventory(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        directory_path = Path(directory)
        for name in tuple(directory_names):
            if (directory_path / name).is_symlink():
                directory_names.remove(name)
        for name in file_names:
            path = directory_path / name
            try:
                mode = path.lstat().st_mode
            except OSError:
                continue
            if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
                continue
            relative = path.relative_to(root).as_posix()
            records.append(
                {
                    "path": relative,
                    "sha256": _sha256_file(path),
                    "size": path.stat().st_size,
                }
            )
    return sorted(records, key=lambda item: (item["path"].casefold(), item["path"]))


def _post_manifest(
    project: Path,
    run_id: str,
    entries: list[dict[str, Any]],
) -> dict[str, Any]:
    fingerprint = bundle_fingerprint(entries)
    return {
        "schema_version": SCHEMA_VERSION,
        "manifest_id": f"{run_id}-post-run",
        "project_root": str(project),
        "recursive": True,
        "digest_algorithm": fingerprint["digest_algorithm"],
        "inventory_sha256": fingerprint["sha256"],
        "entry_count": fingerprint["file_count"],
        "total_size": fingerprint["total_size"],
        "entries": entries,
    }


def _validate_pre_execution_snapshot(
    *,
    preflight: Mapping[str, Any],
    pre_manifest_bytes: bytes,
    pre_manifest_record: Mapping[str, Any],
    prompt_record: Mapping[str, Any],
) -> None:
    if preflight.get("pre_run_manifest") != pre_manifest_record:
        raise AcceptanceControllerError("PRE_RUN_MANIFEST_CHANGED_AFTER_PREFLIGHT")
    try:
        manifest = json.loads(pre_manifest_bytes)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise AcceptanceControllerError(f"PRE_RUN_MANIFEST_INVALID: {exc}") from exc
    if not isinstance(manifest, Mapping):
        raise AcceptanceControllerError("PRE_RUN_MANIFEST_INVALID: object required")
    entries = manifest.get("entries")
    prompt_entries = (
        [
            item
            for item in entries
            if isinstance(item, Mapping) and item.get("path") == prompt_record["path"]
        ]
        if isinstance(entries, list)
        else []
    )
    if len(prompt_entries) != 1:
        raise AcceptanceControllerError("PROMPT_NOT_PREDECLARED")
    declared = prompt_entries[0]
    observed = {
        "path": declared.get("path"),
        "sha256": declared.get("sha256"),
        "size": declared.get("size"),
    }
    if observed != prompt_record:
        raise AcceptanceControllerError("PROMPT_CHANGED_AFTER_PREFLIGHT")


def _validate_jsonl(path: Path) -> list[str]:
    issues: list[str] = []
    count = 0
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        return [f"CODEX_EVENTS_UNREADABLE: {exc}"]
    for ordinal, line in enumerate(lines, 1):
        if not line.strip():
            continue
        count += 1
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            issues.append(f"CODEX_EVENT_JSON_INVALID[{ordinal}]: {exc.msg}")
            continue
        if not isinstance(value, Mapping):
            issues.append(f"CODEX_EVENT_NOT_OBJECT[{ordinal}]")
    if count == 0:
        issues.append("CODEX_EVENTS_EMPTY")
    return issues


def _exit_record(returncode: int) -> dict[str, Any]:
    if returncode == 0:
        return {"code": 0, "status": "success"}
    if returncode < 0:
        return {"code": min(255, 128 + abs(returncode)), "status": "terminated"}
    return {"code": min(255, returncode), "status": "failed"}


def run_acceptance(
    *,
    project_root: Path | str,
    installed_skill_root: Path | str,
    private_root: Path | str,
    harness_dir: Path | str,
    requirement_pack: str = DEFAULT_REQUIREMENT_PACK,
    prompt: str = DEFAULT_PROMPT,
    library: str = PHASE49_LIBRARY_RELATIVE,
    run_id: str = DEFAULT_RUN_ID,
    expected_installed_skill_sha256: str | None = None,
    runtime_identity_manifest: Path | str | None = None,
    expected_runtime_identity_manifest_sha256: str | None = None,
    codex_bin: str = "codex",
    allow_test_codex: bool = False,
) -> dict[str, Any]:
    if not RUN_ID_RE.fullmatch(run_id) or len(run_id) > 151:
        raise AcceptanceControllerError("RUN_ID_INVALID")
    if allow_test_codex and (
        "pytest" not in sys.modules or not os.environ.get("PYTEST_CURRENT_TEST")
    ):
        raise AcceptanceControllerError("TEST_CODEX_BYPASS_FORBIDDEN_OUTSIDE_PYTEST")
    if codex_bin != "codex" and not allow_test_codex:
        raise AcceptanceControllerError("CODEX_BINARY_OVERRIDE_FORBIDDEN")
    project = _real_directory(Path(project_root), "PROJECT_ROOT")
    installed = _real_directory(Path(installed_skill_root), "INSTALLED_SKILL_ROOT")
    _require_installed_controller_origin(installed, test_bypass=allow_test_codex)
    codex_home = _codex_home_for_installed_skill(installed)
    harness_raw, harness_prospective = _validate_harness_request(Path(harness_dir))
    prompt_parts = PurePosixPath(prompt).parts
    if (
        prompt != DEFAULT_PROMPT
        or PurePosixPath(prompt).is_absolute()
        or ".." in prompt_parts
        or "\\" in prompt
    ):
        raise AcceptanceControllerError("PROMPT_PATH_INVALID")
    prompt_path = project / prompt
    if prompt_path.is_symlink() or not prompt_path.is_file():
        raise AcceptanceControllerError("PROMPT_MISSING")

    preflight = validate_requirement_pack(project, requirement_pack)
    if preflight.get("status") != "PASS":
        raise AcceptanceControllerError(
            "CLEAN_PACK_PREFLIGHT_FAILED: "
            + ",".join(
                str(item.get("code"))
                for item in preflight.get("issues", [])
                if isinstance(item, Mapping)
            )
        )
    installed_fingerprint = tree_fingerprint(installed)
    if expected_installed_skill_sha256 is None:
        if not allow_test_codex:
            raise AcceptanceControllerError(
                "EXPECTED_INSTALLED_SKILL_SHA256_REQUIRED"
            )
        expected_installed_skill_sha256 = str(installed_fingerprint["sha256"])
    if not SHA256_RE.fullmatch(expected_installed_skill_sha256):
        raise AcceptanceControllerError("EXPECTED_INSTALLED_SKILL_SHA256_INVALID")
    if installed_fingerprint.get("sha256") != expected_installed_skill_sha256:
        raise AcceptanceControllerError("INSTALLED_SKILL_EXPECTED_DIGEST_MISMATCH")
    test_codex_identity: dict[str, Any] | None = None
    if runtime_identity_manifest is None or expected_runtime_identity_manifest_sha256 is None:
        if not allow_test_codex:
            raise AcceptanceControllerError(
                "RUNTIME_IDENTITY_MANIFEST_AND_EXPECTED_SHA256_REQUIRED"
            )
        test_codex_identity = _resolve_test_codex_identity(codex_bin)
        runtime_identity_manifest, expected_runtime_identity_manifest_sha256 = (
            _materialize_test_runtime_identity(
                harness_prospective=harness_prospective,
                installed_skill_root=installed,
                expected_installed_skill_sha256=expected_installed_skill_sha256,
                test_codex_identity=test_codex_identity,
            )
        )
    runtime_before = _load_runtime_identity(
        manifest_path=runtime_identity_manifest,
        expected_manifest_sha256=expected_runtime_identity_manifest_sha256,
        installed_skill_root=installed,
        expected_installed_skill_sha256=expected_installed_skill_sha256,
        production=not allow_test_codex,
    )
    native_record = runtime_before["payload"]["codex"]["native_executable"]
    codex_identity = {
        "requested_path": native_record["path"],
        "resolved_path": native_record["path"],
        "sha256": native_record["sha256"],
        "size": native_record["size"],
        "version": native_record["version"],
    }
    resolved_private_root, private_identity = _resolve_private_identity(
        Path(private_root),
        installed,
        library,
    )
    _require_pairwise_disjoint(
        {
            "project": project,
            "installed_skill": installed,
            "private_root": resolved_private_root,
            "runtime_identity_manifest": runtime_before["path"],
            "harness": harness_prospective,
        }
    )
    harness = _materialize_harness_dir(harness_raw, harness_prospective)

    prompt_bytes = prompt_path.read_bytes()
    prompt_record_before = _bytes_record(prompt, prompt_bytes)
    pre_manifest_bytes = (project / "PRE-RUN-MANIFEST.json").read_bytes()
    pre_manifest_record_before = _bytes_record(
        "PRE-RUN-MANIFEST.json",
        pre_manifest_bytes,
    )
    _validate_pre_execution_snapshot(
        preflight=preflight,
        pre_manifest_bytes=pre_manifest_bytes,
        pre_manifest_record=pre_manifest_record_before,
        prompt_record=prompt_record_before,
    )

    logical_argv = _logical_argv(project)
    actual_argv = [codex_identity["resolved_path"], *logical_argv[1:]]
    events_path = harness / EVENTS_NAME
    stderr_path = harness / STDERR_NAME
    environment = dict(os.environ)
    environment["CODEX_HOME"] = str(codex_home)
    environment["WINDOW_PPTX_PRIVATE_ROOT"] = str(resolved_private_root)
    # The installed Skill tree is an acceptance authority.  Prevent a first
    # Python invocation from creating __pycache__ files inside that tree.
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        with events_path.open("wb") as stdout_stream, stderr_path.open("wb") as stderr_stream:
            isolated_result = run_in_isolated_process_group(
                actual_argv,
                cwd=project,
                environment=environment,
                stdin_payload=prompt_bytes,
                stdout_stream=stdout_stream,
                stderr_stream=stderr_stream,
            )
    except (AcceptanceSettlementError, OSError) as exc:
        raise AcceptanceControllerError(f"CODEX_LAUNCH_FAILED: {exc}") from exc

    controller_issues = _validate_jsonl(events_path)
    exit_record = _exit_record(isolated_result.returncode)
    if exit_record["status"] != "success":
        controller_issues.append(f"CODEX_CHILD_{exit_record['status'].upper()}")
    if _record_or_missing(project, prompt) != prompt_record_before:
        controller_issues.append("PROMPT_CHANGED_DURING_RUN")
    if (
        _record_or_missing(project, "PRE-RUN-MANIFEST.json")
        != pre_manifest_record_before
    ):
        controller_issues.append("PRE_RUN_MANIFEST_CHANGED_DURING_RUN")
    try:
        entries, inventory_settlement = capture_settled_inventory(
            lambda: _inventory(project)
        )
    except AcceptanceSettlementError as exc:
        raise AcceptanceControllerError(str(exc)) from exc
    post_payload = _post_manifest(project, run_id, entries)
    _validate_schema(post_payload, "physical-assembly-post-run-manifest.v1.schema.json")
    post_path = harness / POST_MANIFEST_NAME
    _write_json(post_path, post_payload)

    try:
        installed_after = tree_fingerprint(installed)
    except (OSError, ValueError) as exc:
        controller_issues.append(f"INSTALLED_SKILL_POSTCHECK_FAILED: {exc}")
    else:
        if installed_after != installed_fingerprint:
            controller_issues.append("INSTALLED_SKILL_CHANGED_DURING_RUN")
    try:
        runtime_after = _load_runtime_identity(
            manifest_path=runtime_before["path"],
            expected_manifest_sha256=expected_runtime_identity_manifest_sha256,
            installed_skill_root=installed,
            expected_installed_skill_sha256=expected_installed_skill_sha256,
            production=not allow_test_codex,
        )
    except (AcceptanceControllerError, OSError, ValueError) as exc:
        controller_issues.append(f"RUNTIME_IDENTITY_POSTCHECK_FAILED: {exc}")
    else:
        if runtime_after != runtime_before:
            controller_issues.append("RUNTIME_IDENTITY_CHANGED_DURING_RUN")
    try:
        _, private_after = _resolve_private_identity(
            resolved_private_root,
            installed,
            library,
        )
    except (AcceptanceControllerError, OSError, ValueError) as exc:
        controller_issues.append(f"PRIVATE_LIBRARY_POSTCHECK_FAILED: {exc}")
    else:
        if private_after != private_identity:
            controller_issues.append("PRIVATE_LIBRARY_CHANGED_DURING_RUN")

    artifacts = {
        "output_pptx": _record_or_missing(project, OUTPUT_PPTX_PATH),
        "physical_assembly_report": _record_or_missing(project, PHYSICAL_REPORT_PATH),
        "rule_qa_report": _record_or_missing(project, RULE_QA_PATH),
        "evidence_outputs": [
            _record_or_missing(project, relative) for relative in EVIDENCE_OUTPUT_PATHS
        ],
    }
    fingerprint = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "command": {
            "argv": logical_argv,
            "cwd": str(project),
            "stdin": prompt_record_before,
            "executable": codex_identity,
            "model_provider": "openai",
            "model": "gpt-5.6-terra",
            "reasoning_effort": "medium",
        },
        "installed_skill": {
            "path": str(installed),
            "expected_sha256": expected_installed_skill_sha256,
            **installed_fingerprint,
        },
        "runtime_identity": {
            "manifest": runtime_before["record"],
            "expected_sha256": expected_runtime_identity_manifest_sha256,
            "launch_mode": "native-codex-direct",
        },
        "requirements": preflight["requirements"],
        "assets": preflight["assets"],
        "private_library": private_identity,
        "process_evidence": {
            "events_jsonl": _external_record(events_path),
            "stderr": _external_record(stderr_path),
            "settlement": {
                "process_group": isolated_result.process_group_evidence,
                "inventory": inventory_settlement,
            },
        },
        "manifests": {
            "pre_run": pre_manifest_record_before,
            "post_run": _external_record(post_path),
        },
        "artifacts": artifacts,
        "exit": exit_record,
    }
    _validate_schema(fingerprint, "physical-assembly-run-fingerprint.v1.schema.json")
    fingerprint_path = harness / RUN_FINGERPRINT_NAME
    _write_json(fingerprint_path, fingerprint)
    validation = validate_run_fingerprint(
        project,
        requirement_pack,
        fingerprint_path,
        private_root=resolved_private_root,
    )
    status = (
        "PASS"
        if validation.get("status") == "PASS"
        and exit_record["status"] == "success"
        and not controller_issues
        else "FAIL"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "controller_id": "window-pptx-v61-codex-acceptance-controller",
        "status": status,
        "run_id": run_id,
        "child_exit": exit_record,
        "controller_issues": controller_issues,
        "validation": validation,
        "harness": {
            "directory": str(harness),
            "events": _external_record(events_path),
            "stderr": _external_record(stderr_path),
            "post_run_manifest": _external_record(post_path),
            "run_fingerprint": _external_record(fingerprint_path),
        },
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", required=True, type=Path)
    parser.add_argument("--installed-skill-root", required=True, type=Path)
    parser.add_argument("--private-root", required=True, type=Path)
    parser.add_argument("--harness-dir", required=True, type=Path)
    parser.add_argument("--requirement-pack", default=DEFAULT_REQUIREMENT_PACK)
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--library", default=PHASE49_LIBRARY_RELATIVE)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--expected-installed-skill-sha256", required=True)
    parser.add_argument("--runtime-identity-manifest", required=True, type=Path)
    parser.add_argument(
        "--expected-runtime-identity-manifest-sha256",
        required=True,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        result = run_acceptance(
            project_root=args.project_root,
            installed_skill_root=args.installed_skill_root,
            private_root=args.private_root,
            harness_dir=args.harness_dir,
            requirement_pack=args.requirement_pack,
            prompt=args.prompt,
            library=args.library,
            run_id=args.run_id,
            expected_installed_skill_sha256=args.expected_installed_skill_sha256,
            runtime_identity_manifest=args.runtime_identity_manifest,
            expected_runtime_identity_manifest_sha256=(
                args.expected_runtime_identity_manifest_sha256
            ),
        )
    except (AcceptanceControllerError, OSError, ValueError) as exc:
        result = {
            "schema_version": SCHEMA_VERSION,
            "controller_id": "window-pptx-v61-codex-acceptance-controller",
            "status": "NOT_RUN",
            "issues": [str(exc)],
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    if result["status"] == "PASS":
        return 0
    return 2 if result["status"] == "NOT_RUN" else 1


if __name__ == "__main__":
    raise SystemExit(main())
