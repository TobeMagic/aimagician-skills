"""Private-library runtime resolution without client-folder discovery."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

from .catalog import certification_evidence_sha256


class RuntimeError(ValueError):
    """Raised when the installed Skill cannot provide its governed library."""


_CATALOG_RELATIVE = Path("intelligence/pptx-studio/catalogs/gaojie-active.v7.json")
_OBSERVATIONS_RELATIVE = Path("intelligence/pptx-studio/vision/gaojie-active-observations.v1.json")
_CERTIFICATION_RELATIVE = Path("intelligence/gaojie/certified-core.json")
_SOURCE_RELATIVE = Path("sources/gaojie")
_CERTIFICATION_DENY_BLOCKER = "visual-certification-denied"


def _skill_private_root() -> Path:
    return Path(__file__).resolve().parents[2] / ".private"


def _configured_skill_private_root() -> Path | None:
    """Return the local development Skill library, if an operator declared it.

    A managed Codex installation intentionally excludes the commercial
    ``.private`` tree.  The installed instructions can therefore point at the
    user's local Skill checkout without copying any private bytes into either
    the installation or a client folder.  This is a declared location, never
    a filesystem search.
    """

    configured = os.environ.get("PPTX_STUDIO_SKILL_ROOT")
    if not configured:
        return None
    return Path(configured).expanduser().resolve(strict=False) / ".private"


def resolve_private_library_root(*, explicit: Path | str | None = None) -> Path:
    """Resolve a governed private library without client-folder discovery.

    Precedence is explicit root, explicit private-root environment variable,
    explicitly declared local Skill root, then a co-installed ``.private``.
    """

    candidates: list[Path | str | None] = [
        explicit,
        os.environ.get("PPTX_STUDIO_PRIVATE_ROOT"),
        _configured_skill_private_root(),
        _skill_private_root(),
    ]
    for requested in candidates:
        if requested is None:
            continue
        root = Path(requested).expanduser().resolve(strict=False)
        if (
            root.is_dir()
            and (root / _CATALOG_RELATIVE).is_file()
            and (root / _OBSERVATIONS_RELATIVE).is_file()
            and (root / _CERTIFICATION_RELATIVE).is_file()
            and (root / _SOURCE_RELATIVE).is_dir()
        ):
            return root
    raise RuntimeError("PPTX_STUDIO_PRIVATE_LIBRARY_UNAVAILABLE")


def runtime_paths(*, explicit: Path | str | None = None) -> dict[str, Path]:
    root = resolve_private_library_root(explicit=explicit)
    return {
        "private_root": root,
        "catalog": root / _CATALOG_RELATIVE,
        "observations": root / _OBSERVATIONS_RELATIVE,
        "certification": root / _CERTIFICATION_RELATIVE,
        "source_root": root / _SOURCE_RELATIVE,
    }


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def runtime_health(*, explicit: Path | str | None = None) -> dict[str, Any]:
    """Return safe health evidence; deliberately excludes private locators."""

    paths = runtime_paths(explicit=explicit)
    try:
        catalog = json.loads(paths["catalog"].read_text(encoding="utf-8"))
        observations = json.loads(paths["observations"].read_text(encoding="utf-8"))
        certification = json.loads(paths["certification"].read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("PPTX_STUDIO_PRIVATE_LIBRARY_INVALID") from exc
    pages = catalog.get("pages") if isinstance(catalog, Mapping) else None
    records = observations.get("observations") if isinstance(observations, Mapping) else None
    overlay = catalog.get("certification_overlay") if isinstance(catalog, Mapping) else None
    denied_pages = certification.get("denied_pages") if isinstance(certification, Mapping) else None
    effective_denials = (
        [
            item for item in denied_pages
            if isinstance(item, Mapping) and item.get("visual_disposition") == "deny"
        ]
        if isinstance(denied_pages, list)
        else []
    )
    if (
        not isinstance(pages, list)
        or not isinstance(records, list)
        or observations.get("status") != "COMPLETE"
        or not isinstance(overlay, Mapping)
        or overlay.get("schema_version") != "pptx-studio-certification-overlay.v1"
        or overlay.get("status") != "PASS"
        or not isinstance(denied_pages, list)
        or certification.get("schema_version") != "gaojie-certified-core.v2"
        or overlay.get("source_sha256") != certification_evidence_sha256(certification)
        or certification.get("denied_page_count") != len(denied_pages)
        or overlay.get("source_entry_count") != len(denied_pages)
        or overlay.get("denied_page_count") != len(effective_denials)
        or type(overlay.get("applied_denied_page_count")) is not int
        or type(overlay.get("out_of_scope_denied_page_count")) is not int
        or overlay["applied_denied_page_count"] + overlay["out_of_scope_denied_page_count"] != len(effective_denials)
    ):
        raise RuntimeError("PPTX_STUDIO_PRIVATE_LIBRARY_INVALID")
    applied_denied = [
        page for page in pages
        if isinstance(page, Mapping)
        and isinstance(page.get("certification"), Mapping)
        and page["certification"].get("visual_disposition") == "deny"
    ]
    if (
        len(applied_denied) != overlay["applied_denied_page_count"]
        or any(
            not isinstance(page.get("materialization"), Mapping)
            or page["materialization"].get("status") != "blocked"
            or _CERTIFICATION_DENY_BLOCKER not in page["materialization"].get("blocker_codes", [])
            for page in applied_denied
        )
    ):
        raise RuntimeError("PPTX_STUDIO_PRIVATE_LIBRARY_INVALID")
    return {
        "schema_version": "pptx-studio-runtime-health.v1",
        "status": "PASS",
        "catalog_sha256": _digest(paths["catalog"]),
        "observations_sha256": _digest(paths["observations"]),
        "certification_sha256": certification_evidence_sha256(certification),
        "catalog_page_count": len(pages),
        "observation_count": len(records),
        "catalog_denied_page_count": len(applied_denied),
        "source_package_count": sum(1 for _ in paths["source_root"].rglob("*.pptx")),
        "required_artifacts": {
            "catalog": True,
            "observations": True,
            "certification": True,
            "source_root": True,
        },
    }
