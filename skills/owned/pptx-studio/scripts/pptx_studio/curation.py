"""Recoverable curation of the user-approved local Gaojie source subset.

This module deliberately accepts an explicit source root and archive root. It
never searches a client requirement directory, does not contact a service, and
does not delete source assets. Archive and recovery are ``os.replace`` moves
on one filesystem, guarded by source and destination hashes.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Mapping, Sequence


ACTIVE_GAOJIE_CATEGORIES: tuple[str, ...] = (
    "003-封面模板", "036-目录模板", "037-章节模板", "038-标题模板",
    "039-结尾模板", "041-二段内容", "042-三段内容", "043-四段内容",
    "044-五段内容", "045-六段内容", "046-多段内容", "047-人物介绍",
    "048-荣誉奖项", "049-时间轴图", "050-架构流程", "051-商业模型",
    "052-样机展示", "053-金句模板", "054-合作伙伴", "057-优秀作品",
    "059-一段内容", "082-地图排版",
)
INACTIVE_GAOJIE_CATEGORIES: tuple[str, ...] = (
    "055-图文排版", "056-表格图表", "058-实用素材", "062-风格配色",
    "104-数据基座", "105-文本组件", "106-装饰形状",
)
SCHEMA_VERSION = "1.0"


class CurationError(ValueError):
    """Raised before an unsafe source/archive mutation can happen."""


def _resolve_directory(value: Path | str, *, label: str) -> Path:
    path = Path(value).expanduser().resolve(strict=False)
    if path.is_symlink() or not path.is_dir():
        raise CurationError(f"{label}_INVALID")
    return path


def _relative(root: Path, target: Path) -> str:
    try:
        relative = target.resolve(strict=False).relative_to(root)
    except ValueError as exc:
        raise CurationError("PATH_ESCAPE") from exc
    if not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise CurationError("PATH_ESCAPE")
    return relative.as_posix()


def _safe_relative(value: str) -> PurePosixPath:
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or not candidate.parts or any(part in {"", ".", ".."} for part in candidate.parts):
        raise CurationError("LOCATOR_INVALID")
    return candidate


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise CurationError("PACKAGE_UNREADABLE") from exc
    return digest.hexdigest()


def _iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise CurationError("SYMLINK_FORBIDDEN")
        if path.is_file():
            yield path


def _tree_sha256(root: Path) -> str:
    digest = hashlib.sha256()
    for path in _iter_files(root):
        relative = _relative(root, path)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_file_sha256(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _category_directories(root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for child in sorted(root.iterdir(), key=lambda item: item.name):
        if child.is_symlink():
            raise CurationError("SYMLINK_FORBIDDEN")
        if child.is_dir():
            result[child.name] = child
        elif child.is_file():
            raise CurationError("SOURCE_ROOT_FILE_FORBIDDEN")
    return result


def _validate_categories(
    found: Mapping[str, Path], active_categories: Sequence[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    active = tuple(active_categories)
    if not active or len(set(active)) != len(active):
        raise CurationError("ACTIVE_CATEGORY_LIST_INVALID")
    missing = sorted(set(active) - set(found))
    if missing:
        raise CurationError("ACTIVE_CATEGORY_MISSING")
    inactive = tuple(sorted(set(found) - set(active)))
    if active == ACTIVE_GAOJIE_CATEGORIES and inactive != INACTIVE_GAOJIE_CATEGORIES:
        raise CurationError("UNKNOWN_CATEGORY")
    return active, inactive


def _package_records(source_root: Path, inactive: Sequence[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for category in inactive:
        directory = source_root / category
        for package in _iter_files(directory):
            if package.suffix.casefold() != ".pptx":
                continue
            locator = _relative(source_root, package)
            source_sha256 = _file_sha256(package)
            records.append({
                "opaque_id": f"pkg_{source_sha256[:24]}",
                "original_locator": locator,
                "archive_locator": locator,
                "source_sha256": source_sha256,
                "post_move_sha256": None,
                "recovery": {
                    "operation": "restore_package_tree",
                    "from_archive_locator": locator,
                    "to_source_locator": locator,
                },
            })
    return sorted(records, key=lambda item: (item["opaque_id"], item["original_locator"]))


def _combined_tree_sha256(root: Path, names: Sequence[str]) -> str:
    digest = hashlib.sha256()
    for name in names:
        directory = root / name
        if not directory.is_dir() or directory.is_symlink():
            raise CurationError("CATEGORY_INVALID")
        digest.update(name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(_tree_sha256(directory).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def _manifest_base(
    source_root: Path,
    archive_root: Path,
    *,
    active_categories: Sequence[str],
) -> dict[str, Any]:
    found = _category_directories(source_root)
    active, inactive = _validate_categories(found, active_categories)
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PLANNED",
        "source_kind": "gaojie",
        "active_categories": list(active),
        "inactive_categories": list(inactive),
        "source_tree_sha256": _combined_tree_sha256(source_root, tuple(found)),
        "active_tree_sha256": _combined_tree_sha256(source_root, active),
        "inactive_tree_sha256": _combined_tree_sha256(source_root, inactive),
        "archive_tree_sha256": None,
        "inactive_packages": _package_records(source_root, inactive),
        "archive_root_locator": _relative(archive_root.parent, archive_root),
    }


def plan_curation(
    source_root: Path | str,
    *,
    archive_root: Path | str,
    active_categories: Sequence[str] = ACTIVE_GAOJIE_CATEGORIES,
) -> dict[str, Any]:
    """Return an immutable-source dry-run archive plan without moving files."""

    source = _resolve_directory(source_root, label="SOURCE_ROOT")
    archive = Path(archive_root).expanduser().resolve(strict=False)
    if archive == source or source in archive.parents:
        raise CurationError("ARCHIVE_ROOT_INVALID")
    if archive.exists() and (archive.is_symlink() or not archive.is_dir()):
        raise CurationError("ARCHIVE_ROOT_INVALID")
    return _manifest_base(source, archive, active_categories=active_categories)


def _validate_plan_shape(plan: Mapping[str, Any]) -> None:
    if plan.get("schema_version") != SCHEMA_VERSION or plan.get("status") not in {"PLANNED", "APPLIED"}:
        raise CurationError("MANIFEST_INVALID")
    active = plan.get("active_categories")
    inactive = plan.get("inactive_categories")
    packages = plan.get("inactive_packages")
    if not isinstance(active, list) or not isinstance(inactive, list) or not isinstance(packages, list):
        raise CurationError("MANIFEST_INVALID")
    if set(active) & set(inactive) or len(active) != len(set(active)) or len(inactive) != len(set(inactive)):
        raise CurationError("MANIFEST_INVALID")
    for record in packages:
        if not isinstance(record, Mapping):
            raise CurationError("MANIFEST_INVALID")
        required = {"opaque_id", "original_locator", "archive_locator", "source_sha256", "post_move_sha256", "recovery"}
        if required - set(record):
            raise CurationError("MANIFEST_INVALID")
        _safe_relative(str(record["original_locator"]))
        _safe_relative(str(record["archive_locator"]))
        if not isinstance(record["recovery"], Mapping):
            raise CurationError("MANIFEST_INVALID")


def _assert_source_matches_plan(plan: Mapping[str, Any], source: Path) -> None:
    found = _category_directories(source)
    active = tuple(str(item) for item in plan["active_categories"])
    inactive = tuple(str(item) for item in plan["inactive_categories"])
    if tuple(sorted(found)) != tuple(sorted((*active, *inactive))):
        raise CurationError("SOURCE_PARTITION_CHANGED")
    if _combined_tree_sha256(source, tuple(found)) != plan.get("source_tree_sha256"):
        for record in plan["inactive_packages"]:
            path = source / _safe_relative(str(record["original_locator"]))
            if not path.is_file() or _file_sha256(path) != record["source_sha256"]:
                raise CurationError("SOURCE_HASH_MISMATCH")
        raise CurationError("SOURCE_TREE_MISMATCH")


def apply_curation(
    plan: Mapping[str, Any],
    source_root: Path | str,
    *,
    archive_root: Path | str,
) -> dict[str, Any]:
    """Move exactly planned inactive category trees after revalidating hashes."""

    _validate_plan_shape(plan)
    if plan.get("status") != "PLANNED":
        raise CurationError("MANIFEST_NOT_PLANNED")
    source = _resolve_directory(source_root, label="SOURCE_ROOT")
    archive = Path(archive_root).expanduser().resolve(strict=False)
    if archive.exists() and (archive.is_symlink() or not archive.is_dir()):
        raise CurationError("ARCHIVE_ROOT_INVALID")
    if source in archive.parents or archive == source:
        raise CurationError("ARCHIVE_ROOT_INVALID")
    _assert_source_matches_plan(plan, source)
    inactive = tuple(str(item) for item in plan["inactive_categories"])
    if any((archive / name).exists() for name in inactive):
        raise CurationError("ARCHIVE_DESTINATION_EXISTS")
    archive.mkdir(parents=True, exist_ok=True)
    moved: list[str] = []
    try:
        for name in inactive:
            os.replace(source / name, archive / name)
            moved.append(name)
        post_records: list[dict[str, Any]] = []
        for record in plan["inactive_packages"]:
            copied = dict(record)
            archived = archive / _safe_relative(str(copied["archive_locator"]))
            post_sha = _file_sha256(archived) if archived.is_file() else None
            if post_sha != copied["source_sha256"]:
                raise CurationError("ARCHIVE_HASH_MISMATCH")
            copied["post_move_sha256"] = post_sha
            post_records.append(copied)
    except BaseException:
        for name in reversed(moved):
            target = archive / name
            if target.exists() and not (source / name).exists():
                os.replace(target, source / name)
        raise
    applied = dict(plan)
    applied["status"] = "APPLIED"
    applied["inactive_packages"] = post_records
    applied["archive_tree_sha256"] = _combined_tree_sha256(archive, inactive)
    return applied


def verify_curation(
    manifest: Mapping[str, Any],
    source_root: Path | str,
    *,
    archive_root: Path | str,
) -> dict[str, Any]:
    """Verify an applied archive without moving a byte."""

    _validate_plan_shape(manifest)
    if manifest.get("status") != "APPLIED":
        raise CurationError("MANIFEST_NOT_APPLIED")
    source = _resolve_directory(source_root, label="SOURCE_ROOT")
    archive = _resolve_directory(archive_root, label="ARCHIVE_ROOT")
    active = tuple(str(item) for item in manifest["active_categories"])
    inactive = tuple(str(item) for item in manifest["inactive_categories"])
    found = _category_directories(source)
    if tuple(sorted(found)) != tuple(sorted(active)):
        raise CurationError("ACTIVE_PARTITION_INVALID")
    if _combined_tree_sha256(source, active) != manifest.get("active_tree_sha256"):
        raise CurationError("ACTIVE_TREE_MISMATCH")
    if _combined_tree_sha256(archive, inactive) != manifest.get("archive_tree_sha256"):
        raise CurationError("ARCHIVE_TREE_MISMATCH")
    for record in manifest["inactive_packages"]:
        archived = archive / _safe_relative(str(record["archive_locator"]))
        if not archived.is_file() or _file_sha256(archived) != record["source_sha256"]:
            raise CurationError("ARCHIVE_HASH_MISMATCH")
        if record.get("post_move_sha256") != record["source_sha256"]:
            raise CurationError("POST_MOVE_HASH_INVALID")
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "PASS",
        "active_tree_sha256": manifest["active_tree_sha256"],
        "archive_tree_sha256": manifest["archive_tree_sha256"],
        "package_count": len(manifest["inactive_packages"]),
    }


def recover_curation(
    manifest: Mapping[str, Any],
    source_root: Path | str,
    *,
    archive_root: Path | str,
    apply: bool = False,
) -> dict[str, Any]:
    """Plan or perform a hash-guarded reversal of an applied curation."""

    verify_curation(manifest, source_root, archive_root=archive_root)
    source = _resolve_directory(source_root, label="SOURCE_ROOT")
    archive = _resolve_directory(archive_root, label="ARCHIVE_ROOT")
    inactive = tuple(str(item) for item in manifest["inactive_categories"])
    result = {
        "schema_version": SCHEMA_VERSION,
        "status": "RECOVERY_PLANNED",
        "categories": list(inactive),
        "package_count": len(manifest["inactive_packages"]),
    }
    if not apply:
        return result
    moved: list[str] = []
    try:
        for name in inactive:
            if (source / name).exists():
                raise CurationError("RECOVERY_DESTINATION_EXISTS")
            os.replace(archive / name, source / name)
            moved.append(name)
        for record in manifest["inactive_packages"]:
            restored = source / _safe_relative(str(record["original_locator"]))
            if not restored.is_file() or _file_sha256(restored) != record["source_sha256"]:
                raise CurationError("RECOVERY_HASH_MISMATCH")
    except BaseException:
        for name in reversed(moved):
            target = source / name
            if target.exists() and not (archive / name).exists():
                os.replace(target, archive / name)
        raise
    result["status"] = "RECOVERED"
    return result
