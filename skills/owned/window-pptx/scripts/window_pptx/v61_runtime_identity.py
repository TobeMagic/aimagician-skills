"""Externally frozen runtime identity for the v6.1 Codex acceptance run.

The production controller is intentionally not allowed to discover Codex from
``PATH`` and then attest whatever it found.  A separate preparation step writes
an identity manifest that binds the installed controller, the interpreter
already executing it, and the native Codex executable.  The controller accepts
that manifest only together with an independently supplied SHA-256 and verifies
all component bytes both before and after the authoring child.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping


SCHEMA_VERSION = "1.0"
RUNTIME_SCHEMA_NAME = "codex-runtime-identity-manifest.v1.schema.json"
CONTROLLER_RELATIVE = Path("scripts/run_window_pptx_v61_codex_acceptance.py")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MACHO_MAGICS = {
    b"\xfe\xed\xfa\xce",
    b"\xce\xfa\xed\xfe",
    b"\xfe\xed\xfa\xcf",
    b"\xcf\xfa\xed\xfe",
    b"\xca\xfe\xba\xbe",
    b"\xbe\xba\xfe\xca",
}


class RuntimeIdentityError(RuntimeError):
    """A runtime authority is missing, mutable, or inconsistent."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json_bytes(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def file_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "sha256": sha256_file(path),
        "size": path.stat().st_size,
    }


def _absolute_regular_file(path: Path | str, label: str) -> Path:
    requested = Path(path).expanduser()
    if not requested.is_absolute():
        raise RuntimeIdentityError(f"{label}_ABSOLUTE_PATH_REQUIRED")
    try:
        mode = requested.lstat().st_mode
    except OSError as exc:
        raise RuntimeIdentityError(f"{label}_MISSING: {requested}") from exc
    if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
        raise RuntimeIdentityError(f"{label}_REGULAR_FILE_REQUIRED: {requested}")
    resolved = requested.resolve(strict=True)
    if resolved != requested:
        raise RuntimeIdentityError(f"{label}_CANONICAL_PATH_REQUIRED: {requested}")
    return resolved


def _probe_version(path: Path, label: str) -> str:
    try:
        completed = subprocess.run(
            [str(path), "--version"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeIdentityError(f"{label}_VERSION_PROBE_FAILED: {exc}") from exc
    output = (completed.stdout + completed.stderr).decode(
        "utf-8", errors="replace"
    ).strip()
    if completed.returncode != 0 or not output or "\n" in output:
        raise RuntimeIdentityError(f"{label}_VERSION_PROBE_INVALID")
    return output


def native_binary_format(path: Path) -> str | None:
    with path.open("rb") as stream:
        magic = stream.read(4)
    if magic == b"\x7fELF":
        return "elf"
    if magic[:2] == b"MZ":
        return "pe"
    if magic in _MACHO_MAGICS:
        return "mach-o"
    return None


def _versioned_record(path: Path, label: str) -> dict[str, Any]:
    return {**file_record(path), "version": _probe_version(path, label)}


def build_runtime_identity_payload(
    *,
    installed_skill_root: Path | str,
    expected_installed_skill_sha256: str,
    controller_interpreter: Path | str,
    codex_native_executable: Path | str,
    allow_test_non_native: bool = False,
) -> dict[str, Any]:
    """Build, but do not freeze, a runtime identity payload.

    All executable inputs must be canonical absolute paths.  In production the
    Codex executable must be a native ELF/PE/Mach-O file; a script is accepted
    only by the programmatic test bypass, which is not exposed by either CLI.
    """

    installed = Path(installed_skill_root).expanduser()
    if not installed.is_absolute() or installed.is_symlink() or not installed.is_dir():
        raise RuntimeIdentityError("INSTALLED_SKILL_ROOT_CANONICAL_DIRECTORY_REQUIRED")
    installed = installed.resolve()
    if not SHA256_RE.fullmatch(expected_installed_skill_sha256):
        raise RuntimeIdentityError("EXPECTED_INSTALLED_SKILL_SHA256_INVALID")
    controller = _absolute_regular_file(
        installed / CONTROLLER_RELATIVE,
        "CONTROLLER_ENTRY",
    )
    interpreter = _absolute_regular_file(
        Path(controller_interpreter).expanduser().resolve(),
        "CONTROLLER_INTERPRETER",
    )
    native = _absolute_regular_file(codex_native_executable, "CODEX_NATIVE_EXECUTABLE")
    binary_format = native_binary_format(native)
    if binary_format is None:
        if not allow_test_non_native:
            raise RuntimeIdentityError("CODEX_NATIVE_EXECUTABLE_FORMAT_INVALID")
        binary_format = "test-script"
    return {
        "schema_version": SCHEMA_VERSION,
        "manifest_id": "phase49-gpt56-terra-runtime-identity",
        "launch_mode": "native-codex-direct",
        "installed_skill": {
            "path": str(installed),
            "expected_sha256": expected_installed_skill_sha256,
        },
        "controller": {
            "entry": file_record(controller),
            "interpreter": _versioned_record(
                interpreter,
                "CONTROLLER_INTERPRETER",
            ),
        },
        "codex": {
            "native_executable": {
                **_versioned_record(native, "CODEX_NATIVE_EXECUTABLE"),
                "binary_format": binary_format,
            }
        },
    }


def write_runtime_identity_manifest(
    path: Path | str,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Atomically write canonical bytes and return their external freeze receipt."""

    target = Path(path).expanduser()
    if not target.is_absolute():
        raise RuntimeIdentityError("RUNTIME_IDENTITY_MANIFEST_ABSOLUTE_PATH_REQUIRED")
    if target.exists() or target.is_symlink():
        raise RuntimeIdentityError("RUNTIME_IDENTITY_MANIFEST_ALREADY_EXISTS")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        temporary.write_bytes(canonical_json_bytes(payload))
        temporary.replace(target)
    finally:
        if temporary.exists():
            temporary.unlink()
    return file_record(target.resolve())


def read_runtime_identity_manifest(
    path: Path | str,
    expected_sha256: str,
) -> tuple[Path, bytes, dict[str, Any]]:
    manifest = _absolute_regular_file(path, "RUNTIME_IDENTITY_MANIFEST")
    if not SHA256_RE.fullmatch(expected_sha256):
        raise RuntimeIdentityError("EXPECTED_RUNTIME_IDENTITY_MANIFEST_SHA256_INVALID")
    raw = manifest.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != expected_sha256:
        raise RuntimeIdentityError("RUNTIME_IDENTITY_MANIFEST_SHA256_MISMATCH")
    try:
        payload = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeIdentityError(f"RUNTIME_IDENTITY_MANIFEST_INVALID: {exc}") from exc
    if not isinstance(payload, dict):
        raise RuntimeIdentityError("RUNTIME_IDENTITY_MANIFEST_OBJECT_REQUIRED")
    return manifest, raw, payload


def verify_component_record(
    record: Mapping[str, Any],
    *,
    label: str,
    probe_version: bool,
    require_native: bool = False,
) -> Path:
    path_value = record.get("path")
    if not isinstance(path_value, str):
        raise RuntimeIdentityError(f"{label}_PATH_INVALID")
    path = _absolute_regular_file(path_value, label)
    if record.get("size") != path.stat().st_size:
        raise RuntimeIdentityError(f"{label}_SIZE_MISMATCH")
    if record.get("sha256") != sha256_file(path):
        raise RuntimeIdentityError(f"{label}_SHA256_MISMATCH")
    if probe_version and record.get("version") != _probe_version(path, label):
        raise RuntimeIdentityError(f"{label}_VERSION_MISMATCH")
    observed_format = native_binary_format(path)
    if require_native and observed_format is None:
        raise RuntimeIdentityError(f"{label}_FORMAT_INVALID")
    if "binary_format" in record:
        expected_format = record.get("binary_format")
        actual_format = observed_format or "test-script"
        if expected_format != actual_format:
            raise RuntimeIdentityError(f"{label}_FORMAT_MISMATCH")
    return path


def verify_runtime_identity_payload(
    payload: Mapping[str, Any],
    *,
    installed_skill_root: Path,
    expected_installed_skill_sha256: str,
    actual_controller_entry: Path,
    production: bool,
    enforce_current_process: bool = True,
) -> dict[str, Any]:
    """Recompute every runtime component and enforce cross-authority identity."""

    installed = installed_skill_root.resolve()
    declared_installed = payload.get("installed_skill")
    controller = payload.get("controller")
    codex = payload.get("codex")
    if not all(isinstance(item, Mapping) for item in (declared_installed, controller, codex)):
        raise RuntimeIdentityError("RUNTIME_IDENTITY_MANIFEST_STRUCTURE_INVALID")
    if declared_installed.get("path") != str(installed):
        raise RuntimeIdentityError("RUNTIME_INSTALLED_SKILL_PATH_MISMATCH")
    if declared_installed.get("expected_sha256") != expected_installed_skill_sha256:
        raise RuntimeIdentityError("RUNTIME_INSTALLED_SKILL_SHA256_MISMATCH")
    entry_record = controller.get("entry")
    interpreter_record = controller.get("interpreter")
    native_record = codex.get("native_executable")
    if not all(isinstance(item, Mapping) for item in (entry_record, interpreter_record, native_record)):
        raise RuntimeIdentityError("RUNTIME_IDENTITY_COMPONENT_INVALID")
    entry_path = verify_component_record(
        entry_record,
        label="CONTROLLER_ENTRY",
        probe_version=False,
    )
    expected_entry = (installed / CONTROLLER_RELATIVE).resolve(strict=True)
    if entry_path != expected_entry:
        raise RuntimeIdentityError("CONTROLLER_ENTRY_INSTALLED_PATH_MISMATCH")
    if (
        production
        and enforce_current_process
        and actual_controller_entry.resolve(strict=True) != expected_entry
    ):
        raise RuntimeIdentityError("CONTROLLER_NOT_RUNNING_FROM_INSTALLED_SKILL")
    interpreter_path = verify_component_record(
        interpreter_record,
        label="CONTROLLER_INTERPRETER",
        probe_version=True,
        require_native=production,
    )
    if (
        production
        and enforce_current_process
        and interpreter_path != Path(sys.executable).resolve(strict=True)
    ):
        raise RuntimeIdentityError("CONTROLLER_INTERPRETER_PROCESS_MISMATCH")
    native_path = verify_component_record(
        native_record,
        label="CODEX_NATIVE_EXECUTABLE",
        probe_version=True,
        require_native=production,
    )
    return {
        "controller_entry": entry_path,
        "controller_interpreter": interpreter_path,
        "codex_native_executable": native_path,
        "codex_version": native_record.get("version"),
        "codex_binary_format": native_record.get("binary_format"),
    }
