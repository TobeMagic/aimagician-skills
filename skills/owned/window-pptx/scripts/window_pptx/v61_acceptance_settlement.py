"""Security primitives for the v6.1 external acceptance harness.

The author process is intentionally not trusted to attest its own cleanup or
filesystem quiescence.  The parent controller uses this module to isolate the
author in a fresh POSIX session, remove any descendants that remain in that
process group, and take separated byte inventories of the clean project.  The
independent validator uses the same constants and pure verification helpers,
but never accepts a controller assertion without cross-binding it to the
post-run manifest and the live project tree.
"""

from __future__ import annotations

import hashlib
import json
import os
import signal
import stat
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Sequence


SETTLEMENT_DIGEST_ALGORITHM = "canonical-file-records-sha256-v1"
SETTLEMENT_MIN_SAMPLES = 3
SETTLEMENT_MIN_WINDOW_MS = 200
SETTLEMENT_SAMPLE_INTERVAL_SECONDS = 0.10
PROCESS_GROUP_TERM_GRACE_SECONDS = 0.75
PROCESS_GROUP_KILL_GRACE_SECONDS = 0.75

HARNESS_FILE_NAMES = {
    "events_jsonl": "codex-events.jsonl",
    "stderr": "codex-stderr.log",
    "post_run_manifest": "post-run-manifest.v1.json",
    "run_fingerprint": "physical-assembly-run-fingerprint.v1.json",
}


class AcceptanceSettlementError(RuntimeError):
    """Fail-closed security or settlement error with a stable code."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        message = code if not detail else f"{code}: {detail}"
        super().__init__(message)


def _canonical_records_digest(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    normalised = sorted(
        (
            {
                "path": str(record["path"]),
                "sha256": str(record["sha256"]),
                "size": int(record["size"]),
            }
            for record in records
        ),
        key=lambda item: (item["path"].casefold(), item["path"]),
    )
    payload = json.dumps(
        normalised,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return {
        "digest_algorithm": SETTLEMENT_DIGEST_ALGORITHM,
        "inventory_sha256": hashlib.sha256(payload).hexdigest(),
        "entry_count": len(normalised),
        "total_size": sum(item["size"] for item in normalised),
    }


def absolute_without_resolution(path: Path | str) -> Path:
    """Return an absolute lexical path without erasing symlink evidence."""

    expanded = Path(path).expanduser()
    if ".." in expanded.parts:
        raise AcceptanceSettlementError("PATH_TRAVERSAL_FORBIDDEN", str(path))
    return Path(os.path.abspath(os.fspath(expanded)))


def reject_symlink_components(
    path: Path | str,
    *,
    allow_missing_tail: bool = False,
) -> Path:
    """Reject a symlink at the leaf or in any existing parent component.

    ``Path.resolve`` is deliberately not used until every existing lexical
    component has been inspected.  Otherwise a symlinked harness parent would
    be silently normalized into an apparently safe real path.
    """

    absolute = absolute_without_resolution(path)
    parts = absolute.parts
    if not parts:
        raise AcceptanceSettlementError("PATH_INVALID", str(path))
    cursor = Path(parts[0])
    missing = False
    for part in parts[1:]:
        cursor = cursor / part
        if missing:
            continue
        try:
            mode = cursor.lstat().st_mode
        except FileNotFoundError:
            if not allow_missing_tail:
                raise AcceptanceSettlementError("PATH_COMPONENT_MISSING", str(cursor))
            missing = True
            continue
        except OSError as exc:
            raise AcceptanceSettlementError(
                "PATH_COMPONENT_INSPECTION_FAILED", f"{cursor}: {exc}"
            ) from exc
        if stat.S_ISLNK(mode):
            raise AcceptanceSettlementError("PARENT_SYMLINK_FORBIDDEN", str(cursor))
    return absolute


def paths_overlap(left: Path, right: Path) -> bool:
    """Return true when either real path contains the other."""

    return left == right or left.is_relative_to(right) or right.is_relative_to(left)


def validate_harness_topology(
    *,
    artifact_paths: Mapping[str, Path | str],
    authority_paths: Mapping[str, Path | str],
) -> Path:
    """Prove that all four harness artifacts share one isolated real directory.

    The directory is exact: it may contain only the four governed regular
    files.  Every lexical parent is checked before resolution, and the real
    directory must be disjoint from each supplied project, Skill, private, or
    runtime authority path.
    """

    if set(artifact_paths) != set(HARNESS_FILE_NAMES):
        raise AcceptanceSettlementError(
            "HARNESS_ARTIFACT_SET_INVALID",
            f"expected={sorted(HARNESS_FILE_NAMES)} got={sorted(artifact_paths)}",
        )
    parents: set[Path] = set()
    identities: set[tuple[int, int]] = set()
    for role, expected_name in HARNESS_FILE_NAMES.items():
        lexical = reject_symlink_components(artifact_paths[role])
        if lexical.name != expected_name:
            raise AcceptanceSettlementError(
                "HARNESS_ARTIFACT_NAME_INVALID",
                f"{role}: expected {expected_name}, got {lexical.name}",
            )
        try:
            mode = lexical.lstat().st_mode
        except OSError as exc:
            raise AcceptanceSettlementError(
                "HARNESS_ARTIFACT_MISSING", f"{role}: {exc}"
            ) from exc
        if not stat.S_ISREG(mode):
            raise AcceptanceSettlementError(
                "HARNESS_ARTIFACT_NOT_REGULAR", f"{role}: {lexical}"
            )
        resolved = lexical.resolve(strict=True)
        parents.add(resolved.parent)
        info = resolved.stat()
        identity = (int(info.st_dev), int(info.st_ino))
        if identity in identities:
            raise AcceptanceSettlementError(
                "HARNESS_ARTIFACT_IDENTITY_DUPLICATE", str(resolved)
            )
        identities.add(identity)
    if len(parents) != 1:
        raise AcceptanceSettlementError(
            "HARNESS_DIRECTORY_MISMATCH",
            ",".join(sorted(str(parent) for parent in parents)),
        )
    harness = next(iter(parents))
    reject_symlink_components(harness)
    actual_names: set[str] = set()
    try:
        children = list(harness.iterdir())
    except OSError as exc:
        raise AcceptanceSettlementError("HARNESS_DIRECTORY_UNREADABLE", str(exc)) from exc
    for child in children:
        reject_symlink_components(child)
        try:
            mode = child.lstat().st_mode
        except OSError as exc:
            raise AcceptanceSettlementError(
                "HARNESS_ENTRY_INSPECTION_FAILED", f"{child}: {exc}"
            ) from exc
        if not stat.S_ISREG(mode):
            raise AcceptanceSettlementError("HARNESS_ENTRY_NOT_REGULAR", str(child))
        actual_names.add(child.name)
    expected_names = set(HARNESS_FILE_NAMES.values())
    if actual_names != expected_names:
        raise AcceptanceSettlementError(
            "HARNESS_DIRECTORY_CONTENT_MISMATCH",
            f"expected={sorted(expected_names)} got={sorted(actual_names)}",
        )

    for name, raw_authority in authority_paths.items():
        lexical = reject_symlink_components(raw_authority)
        real = lexical.resolve(strict=True)
        # Directory authorities govern their complete trees.  A manifest or
        # executable authority governs its exact file; a sibling harness in a
        # disposable parent remains disjoint.
        authority_root = real
        if paths_overlap(harness, authority_root):
            raise AcceptanceSettlementError(
                "HARNESS_AUTHORITY_OVERLAP",
                f"harness={harness} authority={name}:{authority_root}",
            )
    return harness


def validate_distinct_file_paths(
    *,
    root: Path,
    relative_paths: Sequence[str],
) -> None:
    """Reject duplicate path spellings and duplicate underlying file identities."""

    if len(relative_paths) != len(set(relative_paths)):
        raise AcceptanceSettlementError("EVIDENCE_PATH_DUPLICATE")
    if len(relative_paths) != len({value.casefold() for value in relative_paths}):
        raise AcceptanceSettlementError("EVIDENCE_PATH_CASE_COLLISION")
    identities: set[tuple[int, int]] = set()
    resolved: set[Path] = set()
    for relative in relative_paths:
        candidate = root / relative
        reject_symlink_components(candidate)
        real = candidate.resolve(strict=True)
        info = real.stat()
        identity = (int(info.st_dev), int(info.st_ino))
        if identity in identities or real in resolved:
            raise AcceptanceSettlementError(
                "EVIDENCE_FILE_IDENTITY_DUPLICATE", relative
            )
        identities.add(identity)
        resolved.add(real)


def _process_group_exists(process_group_id: int) -> bool:
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _wait_for_group_absence(process_group_id: int, timeout: float) -> tuple[bool, int]:
    deadline = time.monotonic() + timeout
    probes = 0
    while True:
        probes += 1
        if not _process_group_exists(process_group_id):
            return True, probes
        if time.monotonic() >= deadline:
            return False, probes
        time.sleep(0.025)


@dataclass(frozen=True)
class IsolatedProcessResult:
    returncode: int
    process_group_evidence: dict[str, Any]


def run_in_isolated_process_group(
    argv: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str],
    stdin_payload: bytes,
    stdout_stream: Any,
    stderr_stream: Any,
) -> IsolatedProcessResult:
    """Run one author command in a new session and remove group residue."""

    if os.name != "posix" or not hasattr(os, "killpg"):
        raise AcceptanceSettlementError(
            "PROCESS_GROUP_ISOLATION_UNSUPPORTED", os.name
        )
    process = subprocess.Popen(
        list(argv),
        cwd=cwd,
        env=dict(environment),
        stdin=subprocess.PIPE,
        stdout=stdout_stream,
        stderr=stderr_stream,
        start_new_session=True,
    )
    leader_pid = process.pid
    process_group_id = leader_pid
    if process_group_id == os.getpgrp():
        process.kill()
        process.wait()
        raise AcceptanceSettlementError("PROCESS_GROUP_ISOLATION_FAILED")
    process.communicate(input=stdin_payload)

    signals_sent: list[str] = []
    cleanup_attempted = False
    absent, probes = _wait_for_group_absence(process_group_id, 0.05)
    if not absent:
        cleanup_attempted = True
        try:
            os.killpg(process_group_id, signal.SIGTERM)
            signals_sent.append("SIGTERM")
        except ProcessLookupError:
            pass
        absent, extra = _wait_for_group_absence(
            process_group_id, PROCESS_GROUP_TERM_GRACE_SECONDS
        )
        probes += extra
    if not absent:
        try:
            os.killpg(process_group_id, signal.SIGKILL)
            signals_sent.append("SIGKILL")
        except ProcessLookupError:
            pass
        absent, extra = _wait_for_group_absence(
            process_group_id, PROCESS_GROUP_KILL_GRACE_SECONDS
        )
        probes += extra
    if not absent:
        raise AcceptanceSettlementError(
            "PROCESS_GROUP_RESIDUE", str(process_group_id)
        )
    return IsolatedProcessResult(
        returncode=int(process.returncode),
        process_group_evidence={
            "isolation": "new-posix-session",
            "leader_pid": leader_pid,
            "process_group_id": process_group_id,
            "cleanup_attempted": cleanup_attempted,
            "signals_sent": signals_sent,
            "absence_probe_count": probes,
            "residue_status": "absent",
        },
    )


def capture_settled_inventory(
    inventory: Callable[[], list[dict[str, Any]]],
    *,
    minimum_samples: int = SETTLEMENT_MIN_SAMPLES,
    minimum_window_ms: int = SETTLEMENT_MIN_WINDOW_MS,
    sample_interval_seconds: float = SETTLEMENT_SAMPLE_INTERVAL_SECONDS,
    maximum_samples: int = 8,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Capture separated, identical byte inventories or fail closed."""

    if (
        minimum_samples < 2
        or minimum_window_ms < 1
        or sample_interval_seconds <= 0
        or maximum_samples < minimum_samples
    ):
        raise AcceptanceSettlementError("SETTLEMENT_POLICY_INVALID")
    started = time.monotonic_ns()
    samples: list[dict[str, Any]] = []
    stable_suffix = 0
    final_entries: list[dict[str, Any]] = []
    for ordinal in range(1, maximum_samples + 1):
        entries = inventory()
        digest = _canonical_records_digest(entries)
        offset_ms = (time.monotonic_ns() - started) // 1_000_000
        sample = {
            "ordinal": ordinal,
            "offset_ms": int(offset_ms),
            **digest,
        }
        samples.append(sample)
        if len(samples) == 1 or all(
            sample[key] == samples[-2][key]
            for key in ("inventory_sha256", "entry_count", "total_size")
        ):
            stable_suffix += 1
        else:
            stable_suffix = 1
        final_entries = entries
        window_ms = samples[-1]["offset_ms"] - samples[-stable_suffix]["offset_ms"]
        if stable_suffix >= minimum_samples and window_ms >= minimum_window_ms:
            stable_samples = [
                {**sample, "ordinal": stable_ordinal}
                for stable_ordinal, sample in enumerate(
                    samples[-stable_suffix:],
                    start=1,
                )
            ]
            return final_entries, {
                "policy": "separated-stable-inventory-v1",
                "stable": True,
                "minimum_sample_count": minimum_samples,
                "minimum_window_ms": minimum_window_ms,
                "sample_interval_ms": int(round(sample_interval_seconds * 1000)),
                "sample_count": len(stable_samples),
                "window_ms": int(window_ms),
                "samples": stable_samples,
            }
        time.sleep(sample_interval_seconds)
    raise AcceptanceSettlementError(
        "POST_RUN_INVENTORY_UNSETTLED",
        f"samples={len(samples)} stable_suffix={stable_suffix}",
    )


def verify_settlement_evidence(
    raw: Any,
    *,
    post_inventory: Sequence[Mapping[str, Any]],
    probe_process_group: bool = True,
) -> None:
    """Independently cross-bind settlement claims to the post-run inventory."""

    if not isinstance(raw, Mapping):
        raise AcceptanceSettlementError("SETTLEMENT_EVIDENCE_INVALID", "object required")
    group = raw.get("process_group")
    inventory = raw.get("inventory")
    if not isinstance(group, Mapping) or not isinstance(inventory, Mapping):
        raise AcceptanceSettlementError(
            "SETTLEMENT_EVIDENCE_INVALID", "process_group and inventory required"
        )
    if group.get("isolation") != "new-posix-session":
        raise AcceptanceSettlementError("PROCESS_GROUP_ISOLATION_EVIDENCE_INVALID")
    leader = group.get("leader_pid")
    process_group_id = group.get("process_group_id")
    if (
        type(leader) is not int
        or leader < 1
        or type(process_group_id) is not int
        or process_group_id != leader
    ):
        raise AcceptanceSettlementError("PROCESS_GROUP_IDENTITY_INVALID")
    if group.get("residue_status") != "absent":
        raise AcceptanceSettlementError("PROCESS_GROUP_RESIDUE_NOT_CLEARED")
    if type(group.get("absence_probe_count")) is not int or group["absence_probe_count"] < 1:
        raise AcceptanceSettlementError("PROCESS_GROUP_PROBE_EVIDENCE_INVALID")
    cleanup_attempted = group.get("cleanup_attempted")
    signals_sent = group.get("signals_sent")
    if not isinstance(cleanup_attempted, bool) or not isinstance(signals_sent, list):
        raise AcceptanceSettlementError("PROCESS_GROUP_CLEANUP_EVIDENCE_INVALID")
    if any(signal_name not in {"SIGTERM", "SIGKILL"} for signal_name in signals_sent):
        raise AcceptanceSettlementError("PROCESS_GROUP_SIGNAL_EVIDENCE_INVALID")
    if not cleanup_attempted and signals_sent:
        raise AcceptanceSettlementError("PROCESS_GROUP_SIGNAL_EVIDENCE_INVALID")
    if probe_process_group and _process_group_exists(process_group_id):
        raise AcceptanceSettlementError(
            "PROCESS_GROUP_STILL_PRESENT", str(process_group_id)
        )

    if inventory.get("policy") != "separated-stable-inventory-v1":
        raise AcceptanceSettlementError("SETTLEMENT_POLICY_INVALID")
    if inventory.get("stable") is not True:
        raise AcceptanceSettlementError("SETTLEMENT_NOT_STABLE")
    minimum_samples = inventory.get("minimum_sample_count")
    minimum_window = inventory.get("minimum_window_ms")
    sample_count = inventory.get("sample_count")
    window_ms = inventory.get("window_ms")
    samples = inventory.get("samples")
    if type(minimum_samples) is not int or minimum_samples < SETTLEMENT_MIN_SAMPLES:
        raise AcceptanceSettlementError("SETTLEMENT_SAMPLE_POLICY_TOO_WEAK")
    if type(minimum_window) is not int or minimum_window < SETTLEMENT_MIN_WINDOW_MS:
        raise AcceptanceSettlementError("SETTLEMENT_WINDOW_POLICY_TOO_WEAK")
    if not isinstance(samples, list) or len(samples) < minimum_samples:
        raise AcceptanceSettlementError("SETTLEMENT_SAMPLE_COUNT_INSUFFICIENT")
    if sample_count != len(samples):
        raise AcceptanceSettlementError("SETTLEMENT_SAMPLE_COUNT_MISMATCH")
    expected = _canonical_records_digest(post_inventory)
    prior_offset: int | None = None
    for index, sample in enumerate(samples):
        if not isinstance(sample, Mapping):
            raise AcceptanceSettlementError(
                "SETTLEMENT_SAMPLE_INVALID", str(index)
            )
        if sample.get("ordinal") != index + 1:
            raise AcceptanceSettlementError("SETTLEMENT_SAMPLE_ORDINAL_INVALID")
        offset = sample.get("offset_ms")
        if type(offset) is not int or offset < 0:
            raise AcceptanceSettlementError("SETTLEMENT_SAMPLE_OFFSET_INVALID")
        if prior_offset is not None and offset <= prior_offset:
            raise AcceptanceSettlementError("SETTLEMENT_SAMPLE_OFFSET_NOT_INCREASING")
        prior_offset = offset
        for key, value in expected.items():
            if sample.get(key) != value:
                raise AcceptanceSettlementError(
                    "SETTLEMENT_INVENTORY_MISMATCH", f"sample={index + 1} field={key}"
                )
    observed_window = samples[-1]["offset_ms"] - samples[0]["offset_ms"]
    if window_ms != observed_window or observed_window < minimum_window:
        raise AcceptanceSettlementError("SETTLEMENT_WINDOW_INSUFFICIENT")
