"""Canonical hashes and typed runtime evidence for governed PPTX delivery.

The original v1 fingerprint remains a supported legacy PowerPoint profile.  A
portable profile is additive: it replaces the mandatory PowerPoint component
with a pinned Node/PptxGenJS/LibreOffice and Poppler-or-Ghostscript runtime
component.  PowerPoint
is present in a portable fingerprint only when a successful certification
artifact is hash-bound to the component.
"""

from __future__ import annotations

import hashlib
import json
import locale
import platform
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


SHA256 = re.compile(r"[0-9a-f]{64}")
PINNED_PPTXGENJS_VERSION = "4.0.1"

# Kept byte-for-byte compatible as a public constant for the existing
# calibration and benchmark readers.
FINGERPRINT_FIELDS = (
    "git_commit",
    "dirty_state",
    "engine_sha256",
    "registry_bundle_sha256",
    "schemas_sha256",
    "skill_sha256",
    "corpus_sha256",
    "protocol_sha256",
    "prompt_sha256",
    "thresholds_sha256",
    "dependencies_sha256",
    "model_provider_sha256",
    "environment_sha256",
    "font_inventory_sha256",
    "powerpoint_build_sha256",
    "asset_manifest_sha256",
    "evidence_generation",
)
PORTABLE_RUNTIME_HASH_FIELD = "portable_runtime_sha256"
PORTABLE_FINGERPRINT_FIELDS = tuple(
    field for field in FINGERPRINT_FIELDS if field != "powerpoint_build_sha256"
) + (PORTABLE_RUNTIME_HASH_FIELD,)

# Legacy mapping retained for readers which import this constant directly.
FINGERPRINT_COMPONENT_FIELDS = {
    "dependencies": "dependencies_sha256",
    "model_provider": "model_provider_sha256",
    "environment": "environment_sha256",
    "font_inventory": "font_inventory_sha256",
    "powerpoint_build": "powerpoint_build_sha256",
    "asset_manifest": "asset_manifest_sha256",
}
PORTABLE_FINGERPRINT_COMPONENT_FIELDS = {
    "dependencies": "dependencies_sha256",
    "model_provider": "model_provider_sha256",
    "environment": "environment_sha256",
    "font_inventory": "font_inventory_sha256",
    "portable_runtime": PORTABLE_RUNTIME_HASH_FIELD,
    "asset_manifest": "asset_manifest_sha256",
}


def canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def canonical_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def governed_engine_source_paths(skill_root: Path | str) -> tuple[Path, ...]:
    """Return the canonical source files that define the governed engine.

    The Python orchestration and the owned Node worker are one renderer.  Keep
    their source fingerprint in one place so calibration and benchmark runs
    cannot silently hash different implementations.  Installed dependencies
    are deliberately excluded; the pinned package manifests and portable
    runtime component bind those separately.
    """

    root = Path(skill_root).resolve()
    scripts_root = root / "scripts"
    node_root = scripts_root / "node"
    package_files = (
        node_root / "package.json",
        node_root / "package-lock.json",
    )
    missing = [path for path in package_files if not path.is_file()]
    if missing:
        raise ValueError(
            "governed engine package manifest is missing: "
            + ", ".join(path.as_posix() for path in missing)
        )

    python_sources = (
        path
        for path in scripts_root.rglob("*.py")
        if path.is_file()
        and "node_modules" not in path.relative_to(scripts_root).parts
    )
    node_sources = tuple(path for path in node_root.glob("*.mjs") if path.is_file())
    if not node_sources:
        raise ValueError("governed engine Node worker source is missing")

    sources = {*python_sources, *node_sources, *package_files}
    return tuple(
        sorted(
            sources,
            key=lambda path: (
                path.relative_to(root).as_posix().casefold(),
                path.relative_to(root).as_posix(),
            ),
        )
    )


def _fingerprint_profile(fields: set[str]) -> tuple[str, bool]:
    legacy = set(FINGERPRINT_FIELDS)
    portable = set(PORTABLE_FINGERPRINT_FIELDS)
    portable_certified = portable | {"powerpoint_build_sha256"}
    if fields == legacy:
        return "legacy-powerpoint", True
    if fields == portable:
        return "portable", False
    if fields == portable_certified:
        return "portable", True
    allowed = legacy | {PORTABLE_RUNTIME_HASH_FIELD}
    unknown = sorted(fields - allowed)
    missing_legacy = sorted(legacy - fields)
    missing_portable = sorted(portable - fields)
    raise ValueError(
        "fingerprint fields mismatch; "
        f"missing_legacy={missing_legacy}; missing_portable={missing_portable}; "
        f"unknown={unknown}"
    )


def validate_fingerprint(value: Mapping[str, Any]) -> dict[str, Any]:
    _fingerprint_profile(set(value))
    result = dict(value)
    if not isinstance(result["git_commit"], str) or not re.fullmatch(
        r"[0-9a-f]{40}", result["git_commit"]
    ):
        raise ValueError("fingerprint git_commit is invalid")
    if not isinstance(result["dirty_state"], bool):
        raise ValueError("fingerprint dirty_state must be boolean")
    for field, field_value in result.items():
        if field.endswith("_sha256") and (
            not isinstance(field_value, str) or not SHA256.fullmatch(field_value)
        ):
            raise ValueError(f"fingerprint {field} is invalid")
    if result["evidence_generation"] not in {"pre-huashu", "post-huashu"}:
        raise ValueError("fingerprint evidence_generation is invalid")
    return result


def validate_fingerprint_bundle(values: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    fingerprints = [validate_fingerprint(value) for value in values]
    if not fingerprints:
        raise ValueError("fingerprint bundle is empty")
    if any(item["dirty_state"] for item in fingerprints):
        raise ValueError("dirty formal benchmark fingerprint is forbidden")
    if any(item["evidence_generation"] != "post-huashu" for item in fingerprints):
        raise ValueError("pre-huashu evidence is noncanonical")
    first = fingerprints[0]
    if any(item != first for item in fingerprints[1:]):
        raise ValueError("mixed fingerprint bundle is forbidden")
    return first


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_portable_runtime_manifest(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the strict, executable-backed portable renderer fingerprint."""

    base_required = {
        "schema_version",
        "node",
        "npm",
        "pptxgenjs",
        "libreoffice",
    }
    if not isinstance(value, Mapping):
        raise ValueError("portable_runtime component must be an object")
    rasterizers = set(value) & {"poppler", "ghostscript"}
    if (
        set(value) - {"poppler", "ghostscript"} != base_required
        or len(rasterizers) != 1
    ):
        raise ValueError("portable_runtime component fields are incomplete")
    result = dict(value)
    if result["schema_version"] != "1.0":
        raise ValueError("portable_runtime schema_version must be 1.0")
    for component in ("node", "npm", "libreoffice"):
        document = result[component]
        if not isinstance(document, Mapping) or set(document) != {
            "version",
            "executable",
        }:
            raise ValueError(
                f"portable_runtime {component} requires version and executable"
            )
        if not all(_non_empty_string(document.get(field)) for field in document):
            raise ValueError(f"portable_runtime {component} contains empty evidence")
        result[component] = dict(document)
    pptxgenjs = result["pptxgenjs"]
    if not isinstance(pptxgenjs, Mapping) or set(pptxgenjs) != {
        "version",
        "package_json_sha256",
        "package_lock_sha256",
    }:
        raise ValueError("portable_runtime pptxgenjs fields are incomplete")
    if pptxgenjs.get("version") != PINNED_PPTXGENJS_VERSION:
        raise ValueError(
            f"portable_runtime requires PptxGenJS {PINNED_PPTXGENJS_VERSION}"
        )
    for field in ("package_json_sha256", "package_lock_sha256"):
        if not isinstance(pptxgenjs.get(field), str) or not SHA256.fullmatch(
            str(pptxgenjs[field])
        ):
            raise ValueError(f"portable_runtime pptxgenjs {field} is invalid")
    result["pptxgenjs"] = dict(pptxgenjs)
    if "poppler" in result:
        poppler = result["poppler"]
        if not isinstance(poppler, Mapping) or set(poppler) != {
            "pdfinfo_version",
            "pdfinfo_executable",
            "pdftoppm_version",
            "pdftoppm_executable",
        }:
            raise ValueError("portable_runtime poppler fields are incomplete")
        if not all(_non_empty_string(poppler.get(field)) for field in poppler):
            raise ValueError("portable_runtime poppler contains empty evidence")
        result["poppler"] = dict(poppler)
    else:
        ghostscript = result["ghostscript"]
        if not isinstance(ghostscript, Mapping) or set(ghostscript) != {
            "version",
            "executable",
        }:
            raise ValueError(
                "portable_runtime ghostscript requires version and executable"
            )
        if not all(
            _non_empty_string(ghostscript.get(field)) for field in ghostscript
        ):
            raise ValueError("portable_runtime ghostscript contains empty evidence")
        result["ghostscript"] = dict(ghostscript)
    return result


def validate_fingerprint_components(
    fingerprint: Mapping[str, Any],
    components: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    """Bind every opaque environment hash to a typed, human-readable manifest."""

    fingerprint_result = validate_fingerprint(fingerprint)
    profile, powerpoint_claimed = _fingerprint_profile(set(fingerprint_result))
    component_fields = (
        dict(PORTABLE_FINGERPRINT_COMPONENT_FIELDS)
        if profile == "portable"
        else dict(FINGERPRINT_COMPONENT_FIELDS)
    )
    if profile == "portable" and powerpoint_claimed:
        component_fields["powerpoint_build"] = "powerpoint_build_sha256"
    if not isinstance(components, Mapping) or set(components) != set(component_fields):
        raise ValueError("fingerprint component manifests are incomplete")
    result: dict[str, dict[str, Any]] = {}
    for name, hash_field in component_fields.items():
        value = components[name]
        if not isinstance(value, Mapping) or not value:
            raise ValueError(f"fingerprint component {name} must be a non-empty object")
        document = dict(value)
        if canonical_sha256(document) != fingerprint_result[hash_field]:
            raise ValueError(f"fingerprint component hash mismatch: {name}")
        result[name] = document

    dependencies = result["dependencies"]
    if profile == "portable" and set(dependencies) != {"python", "packages"}:
        raise ValueError("portable dependencies component fields are invalid")
    if not (
        _non_empty_string(dependencies.get("python"))
        and isinstance(dependencies.get("packages"), (dict, list))
    ):
        raise ValueError("dependencies component requires python and packages")
    provider = result["model_provider"]
    if profile == "portable" and set(provider) != {"opencode_version", "models"}:
        raise ValueError("portable model_provider component fields are invalid")
    provider_models = provider.get("models")
    if not (
        _non_empty_string(provider.get("opencode_version"))
        and isinstance(provider_models, list)
        and provider_models
        and all(_non_empty_string(item) for item in provider_models)
    ):
        raise ValueError("model_provider component requires opencode_version and models")
    if profile == "portable" and len(provider_models) != len(set(provider_models)):
        raise ValueError("portable model_provider models must be unique")
    environment = result["environment"]
    if profile == "portable" and set(environment) != {
        "system",
        "release",
        "machine",
        "locale",
    }:
        raise ValueError("portable environment component fields are invalid")
    if not all(
        _non_empty_string(environment.get(field))
        for field in ("system", "release", "locale")
    ):
        raise ValueError("environment component requires system, release, and locale")
    if profile == "portable" and not _non_empty_string(environment.get("machine")):
        raise ValueError("portable environment component requires machine")
    if profile == "portable" and set(result["font_inventory"]) != {"fonts"}:
        raise ValueError("portable font_inventory component fields are invalid")
    fonts = result["font_inventory"].get("fonts")
    if not isinstance(fonts, list) or not fonts or not all(
        _non_empty_string(item) for item in fonts
    ):
        raise ValueError("font_inventory component requires installed font names")
    if profile == "portable" and fonts != sorted(set(fonts), key=str.casefold):
        raise ValueError("portable font_inventory must be sorted and unique")
    if profile == "portable":
        result["portable_runtime"] = validate_portable_runtime_manifest(
            result["portable_runtime"]
        )
    if powerpoint_claimed:
        powerpoint = result["powerpoint_build"]
        if not _non_empty_string(powerpoint.get("version")):
            raise ValueError("powerpoint_build component requires a version")
        if profile == "portable" and not (
            set(powerpoint)
            == {
                "version",
                "status",
                "certification_evidence_sha256",
                "candidate_sha256",
                "pdf_sha256",
                "png_sha256",
                "process_ownership",
            }
            and powerpoint.get("status") == "passed"
            and isinstance(powerpoint.get("certification_evidence_sha256"), str)
            and SHA256.fullmatch(powerpoint["certification_evidence_sha256"])
            and isinstance(powerpoint.get("candidate_sha256"), str)
            and SHA256.fullmatch(powerpoint["candidate_sha256"])
            and isinstance(powerpoint.get("pdf_sha256"), str)
            and SHA256.fullmatch(powerpoint["pdf_sha256"])
            and isinstance(powerpoint.get("png_sha256"), list)
            and bool(powerpoint["png_sha256"])
            and all(
                isinstance(value, str) and SHA256.fullmatch(value)
                for value in powerpoint["png_sha256"]
            )
            and powerpoint.get("process_ownership") == "hwnd-pid-bound"
        ):
            raise ValueError(
                "portable powerpoint_build requires passed certification evidence"
            )
    if profile == "portable" and set(result["asset_manifest"]) != {"bindings"}:
        raise ValueError("portable asset_manifest component fields are invalid")
    if not isinstance(result["asset_manifest"].get("bindings"), Mapping):
        raise ValueError("asset_manifest component requires bindings")

    def scalar_strings(value: Any) -> Iterable[str]:
        if isinstance(value, str):
            yield value
        elif isinstance(value, Mapping):
            for child in value.values():
                yield from scalar_strings(child)
        elif isinstance(value, list):
            for child in value:
                yield from scalar_strings(child)

    forbidden = {"not_run", "not-run", "unavailable", "unknown", "placeholder", "fixture"}
    if any(
        token.strip().casefold() in forbidden
        for document in result.values()
        for token in scalar_strings(document)
    ):
        raise ValueError("fingerprint component contains unavailable or placeholder evidence")
    return result


def _resolve_executable(value: str | Path | None, *names: str) -> str:
    if value is not None:
        candidate = shutil.which(str(value))
        if candidate is None and Path(value).is_file():
            candidate = str(Path(value).resolve())
        if candidate:
            return candidate
    for name in names:
        candidate = shutil.which(name)
        if candidate:
            return candidate
    raise ValueError("portable fingerprint executable is missing: " + "/".join(names))


def _command_version(executable: str, *arguments: str) -> str:
    try:
        completed = subprocess.run(
            [executable, *arguments],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError(f"portable fingerprint command failed: {executable}: {exc}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip().replace("\n", " ")[:400]
        raise ValueError(
            f"portable fingerprint command failed: {executable} "
            f"exited {completed.returncode}: {detail}"
        )
    lines = [
        line.strip()
        for line in (completed.stdout + "\n" + completed.stderr).splitlines()
        if line.strip()
    ]
    if not lines:
        raise ValueError(f"portable fingerprint command returned no version: {executable}")
    return lines[0]


def collect_portable_runtime_manifest(
    *,
    skill_root: Path | None = None,
    node_binary: str | Path | None = None,
    npm_binary: str | Path | None = None,
    libreoffice_binary: str | Path | None = None,
    pdfinfo_binary: str | Path | None = None,
    pdftoppm_binary: str | Path | None = None,
    ghostscript_binary: str | Path | None = None,
) -> dict[str, Any]:
    """Collect actual portable executable and pinned package versions.

    Collection fails closed if the installed PptxGenJS version differs from the
    exact package pin or if any proof executable cannot report its version.
    """

    root = (
        Path(skill_root).resolve()
        if skill_root is not None
        else Path(__file__).resolve().parents[2]
    )
    node_dir = root / "scripts" / "node"
    package_json = node_dir / "package.json"
    package_lock = node_dir / "package-lock.json"
    installed_package = node_dir / "node_modules" / "pptxgenjs" / "package.json"
    for path in (package_json, package_lock, installed_package):
        if not path.is_file():
            raise ValueError(f"portable fingerprint dependency manifest is missing: {path}")
    try:
        declared = json.loads(package_json.read_text(encoding="utf-8"))
        installed = json.loads(installed_package.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"portable fingerprint package metadata is unreadable: {exc}") from exc
    declared_dependencies = (
        declared.get("dependencies", {}) if isinstance(declared, Mapping) else {}
    )
    declared_version = (
        declared_dependencies.get("pptxgenjs")
        if isinstance(declared_dependencies, Mapping)
        else None
    )
    installed_version = installed.get("version") if isinstance(installed, Mapping) else None
    if declared_version != PINNED_PPTXGENJS_VERSION or installed_version != declared_version:
        raise ValueError(
            "portable runtime must declare and install exact PptxGenJS "
            f"{PINNED_PPTXGENJS_VERSION}; declared={declared_version!r}; "
            f"installed={installed_version!r}"
        )

    node = _resolve_executable(node_binary, "node")
    npm = _resolve_executable(npm_binary, "npm")
    libreoffice = _resolve_executable(libreoffice_binary, "libreoffice", "soffice")
    pdfinfo = (
        _resolve_executable(pdfinfo_binary, "pdfinfo")
        if pdfinfo_binary is not None or shutil.which("pdfinfo")
        else None
    )
    pdftoppm = (
        _resolve_executable(pdftoppm_binary, "pdftoppm")
        if pdftoppm_binary is not None or shutil.which("pdftoppm")
        else None
    )
    manifest = {
        "schema_version": "1.0",
        "node": {
            "version": _command_version(node, "--version"),
            "executable": str(Path(node).absolute()),
        },
        "npm": {
            "version": _command_version(npm, "--version"),
            "executable": str(Path(npm).absolute()),
        },
        "pptxgenjs": {
            "version": installed_version,
            "package_json_sha256": _sha256_file(package_json),
            "package_lock_sha256": _sha256_file(package_lock),
        },
        "libreoffice": {
            "version": _command_version(libreoffice, "--version"),
            "executable": str(Path(libreoffice).absolute()),
        },
    }
    if pdfinfo is not None and pdftoppm is not None:
        manifest["poppler"] = {
            "pdfinfo_version": _command_version(pdfinfo, "-v"),
            "pdfinfo_executable": str(Path(pdfinfo).absolute()),
            "pdftoppm_version": _command_version(pdftoppm, "-v"),
            "pdftoppm_executable": str(Path(pdftoppm).absolute()),
        }
    else:
        ghostscript = _resolve_executable(ghostscript_binary, "gs", "gswin64c")
        manifest["ghostscript"] = {
            "version": _command_version(ghostscript, "--version"),
            "executable": str(Path(ghostscript).absolute()),
        }
    return validate_portable_runtime_manifest(manifest)


def collect_environment_manifest() -> dict[str, str]:
    """Collect the OS and active process locale without invoking a renderer."""

    active_locale = locale.setlocale(locale.LC_ALL, None)
    if not active_locale:
        raise ValueError("active locale could not be determined")
    return {
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "locale": active_locale,
    }


def collect_font_inventory_manifest(
    fonts: Iterable[str] | None = None,
) -> dict[str, list[str]]:
    """Collect a stable, de-duplicated font-family inventory."""

    if fonts is None:
        from .brand import discover_installed_fonts

        fonts = discover_installed_fonts()
    normalized = sorted(
        {font.strip() for font in fonts if isinstance(font, str) and font.strip()},
        key=str.casefold,
    )
    if not normalized:
        raise ValueError("font inventory is empty")
    return {"fonts": normalized}


def collect_portable_fingerprint_components(
    *,
    model_provider: Mapping[str, Any],
    asset_manifest: Mapping[str, Any],
    python_packages: Mapping[str, Any] | Sequence[Any],
    skill_root: Path | None = None,
    fonts: Iterable[str] | None = None,
    powerpoint_certification: Mapping[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    """Collect all environment components for a portable release fingerprint."""

    result: dict[str, dict[str, Any]] = {
        "dependencies": {
            "python": platform.python_version(),
            "packages": (
                dict(python_packages)
                if isinstance(python_packages, Mapping)
                else list(python_packages)
            ),
        },
        "model_provider": dict(model_provider),
        "environment": collect_environment_manifest(),
        "font_inventory": collect_font_inventory_manifest(fonts),
        "portable_runtime": collect_portable_runtime_manifest(skill_root=skill_root),
        "asset_manifest": dict(asset_manifest),
    }
    if powerpoint_certification is not None:
        evidence = dict(powerpoint_certification)
        expected_fields = {
            "powerpoint_version",
            "pdf_path",
            "png_paths",
            "candidate_hash_before",
            "candidate_hash_after",
            "owned_pid",
        }
        if set(evidence) != expected_fields:
            raise ValueError("PowerPoint certification evidence fields are incomplete")
        version = evidence.get("powerpoint_version")
        if not _non_empty_string(version):
            raise ValueError("PowerPoint certification evidence requires powerpoint_version")
        before_hash = evidence.get("candidate_hash_before")
        after_hash = evidence.get("candidate_hash_after")
        if (
            not isinstance(before_hash, str)
            or not SHA256.fullmatch(before_hash)
            or before_hash != after_hash
        ):
            raise ValueError(
                "PowerPoint certification evidence requires equal candidate hashes"
            )
        owned_pid = evidence.get("owned_pid")
        if isinstance(owned_pid, bool) or not isinstance(owned_pid, int) or owned_pid < 1:
            raise ValueError("PowerPoint certification evidence requires an owned pid")
        pdf_path = Path(str(evidence.get("pdf_path", "")))
        png_values = evidence.get("png_paths")
        if (
            not pdf_path.is_file()
            or not pdf_path.read_bytes().startswith(b"%PDF-")
            or not isinstance(png_values, list)
            or not png_values
        ):
            raise ValueError("PowerPoint certification proof files are incomplete")
        png_paths = tuple(Path(str(value)) for value in png_values)
        if any(
            not path.is_file()
            or not path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
            for path in png_paths
        ):
            raise ValueError("PowerPoint certification PNG proof is invalid")
        result["powerpoint_build"] = {
            "version": version,
            "status": "passed",
            "certification_evidence_sha256": canonical_sha256(evidence),
            "candidate_sha256": before_hash,
            "pdf_sha256": _sha256_file(pdf_path),
            "png_sha256": [_sha256_file(path) for path in png_paths],
            "process_ownership": "hwnd-pid-bound",
        }
    return result


__all__ = [
    "FINGERPRINT_COMPONENT_FIELDS",
    "FINGERPRINT_FIELDS",
    "PINNED_PPTXGENJS_VERSION",
    "PORTABLE_FINGERPRINT_COMPONENT_FIELDS",
    "PORTABLE_FINGERPRINT_FIELDS",
    "PORTABLE_RUNTIME_HASH_FIELD",
    "canonical_json",
    "canonical_sha256",
    "collect_environment_manifest",
    "collect_font_inventory_manifest",
    "collect_portable_fingerprint_components",
    "collect_portable_runtime_manifest",
    "governed_engine_source_paths",
    "validate_fingerprint",
    "validate_fingerprint_bundle",
    "validate_fingerprint_components",
    "validate_portable_runtime_manifest",
]
