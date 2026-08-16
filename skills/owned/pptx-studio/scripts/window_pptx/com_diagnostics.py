"""Read-only PowerPoint COM registration diagnostics and safe certification."""

from __future__ import annotations

import csv
import io
import json
import os
import platform
import re
import shutil
import struct
import subprocess
import tempfile
import time
import ctypes
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .transaction import sha256_file, validate_ooxml_package


POWERPOINT_APPLICATION_CLSID = "{91493441-5A91-11CF-8700-00AA0060263B}"
POWERPOINT_APPLICATION_IID = "{91493442-5A91-11CF-8700-00AA0060263B}"
POWERPOINT_TYPELIB = "{91493440-5A91-11CF-8700-00AA0060263B}"
KNOWN_WPS_POWERPOINT_TYPELIB = "{44720440-94BF-4940-926D-4F38FECF2A48}"


class PowerPointCertificationError(RuntimeError):
    """PowerPoint could not certify a candidate without risking user state."""


@dataclass(frozen=True)
class InterfaceTypeLibRegistration:
    interface_iid: str
    typelib_guid: str | None
    version: str | None
    typelib_path: Path | None
    registry_view: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "interface_iid": self.interface_iid,
            "typelib_guid": self.typelib_guid,
            "version": self.version,
            "typelib_path": str(self.typelib_path) if self.typelib_path else None,
            "typelib_exists": self.typelib_path.is_file() if self.typelib_path else False,
            "registry_view": self.registry_view,
        }


@dataclass(frozen=True)
class DiagnosticFinding:
    code: str
    severity: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
        }


@dataclass(frozen=True)
class PowerPointDoctorResult:
    platform_supported: bool
    registration: InterfaceTypeLibRegistration | None
    findings: tuple[DiagnosticFinding, ...]
    evidence: Mapping[str, Any] = field(default_factory=dict)
    automatic_registry_changes: bool = False

    @property
    def healthy(self) -> bool:
        return self.platform_supported and not any(
            finding.severity == "error" for finding in self.findings
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "platform_supported": self.platform_supported,
            "healthy": self.healthy,
            "registration": self.registration.to_dict() if self.registration else None,
            "findings": [finding.to_dict() for finding in self.findings],
            "evidence": dict(self.evidence),
            "automatic_registry_changes": self.automatic_registry_changes,
            "repair_policy": (
                "Back up the reported key and use Microsoft Office Quick/Online Repair; "
                "this doctor never edits the registry."
            ),
        }


@dataclass(frozen=True)
class PowerPointCertificationResult:
    powerpoint_version: str
    pdf_path: Path
    png_paths: tuple[Path, ...]
    candidate_hash_before: str
    candidate_hash_after: str
    owned_pid: int

    def to_dict(self) -> dict[str, object]:
        return {
            "powerpoint_version": self.powerpoint_version,
            "pdf_path": str(self.pdf_path),
            "png_paths": [str(path) for path in self.png_paths],
            "candidate_hash_before": self.candidate_hash_before,
            "candidate_hash_after": self.candidate_hash_after,
            "owned_pid": self.owned_pid,
        }


def classify_interface_registration(
    registration: InterfaceTypeLibRegistration,
) -> tuple[DiagnosticFinding, ...]:
    findings: list[DiagnosticFinding] = []
    guid = (registration.typelib_guid or "").upper()
    path_text = str(registration.typelib_path or "").casefold()
    if not guid:
        findings.append(
            DiagnosticFinding(
                "POWERPOINT_INTERFACE_TYPELIB_MISSING",
                "error",
                f"{registration.interface_iid} has no registered TypeLib",
            )
        )
    elif guid != POWERPOINT_TYPELIB.upper():
        findings.append(
            DiagnosticFinding(
                "POWERPOINT_INTERFACE_TYPELIB_MISMATCH",
                "error",
                f"_Application points to {registration.typelib_guid}, not {POWERPOINT_TYPELIB}",
            )
        )
    if guid == KNOWN_WPS_POWERPOINT_TYPELIB.upper() or "wps office" in path_text or "wppapi" in path_text:
        findings.append(
            DiagnosticFinding(
                "STALE_WPS_TYPELIB_REGISTRATION",
                "error",
                "PowerPoint _Application is registered against a WPS presentation TypeLib",
            )
        )
    if registration.typelib_path is None:
        findings.append(
            DiagnosticFinding(
                "TYPELIB_PATH_MISSING",
                "error",
                "the registered TypeLib has no win32/win64 library path",
            )
        )
    elif not registration.typelib_path.is_file():
        findings.append(
            DiagnosticFinding(
                "TYPELIB_FILE_MISSING",
                "error",
                f"registered TypeLib file does not exist: {registration.typelib_path}",
            )
        )
    if (
        (guid == KNOWN_WPS_POWERPOINT_TYPELIB.upper() or "wppapi" in path_text)
        and registration.typelib_path is not None
        and not registration.typelib_path.is_file()
    ):
        findings.append(
            DiagnosticFinding(
                "TYPE_E_CANTLOADLIBRARY_ROOT_CAUSE",
                "error",
                "early-bound _Application metadata resolves to a missing WPS "
                "wppapi.dll; pywin32 therefore raises TYPE_E_CANTLOADLIBRARY "
                "(0x80029C4A) even when Microsoft PowerPoint and MSPPT.OLB work",
            )
        )
    if not findings:
        findings.append(
            DiagnosticFinding(
                "POWERPOINT_INTERFACE_TYPELIB_HEALTHY",
                "info",
                "PowerPoint _Application points to the Microsoft PowerPoint TypeLib",
            )
        )
    return tuple(findings)


def _read_default(winreg: Any, hive: Any, path: str, access: int) -> str | None:
    try:
        with winreg.OpenKey(hive, path, 0, access) as key:
            value, _kind = winreg.QueryValueEx(key, None)
    except OSError:
        return None
    return str(value).strip() if value is not None else None


def _windows_interface_registration() -> InterfaceTypeLibRegistration:
    import winreg  # type: ignore[import-not-found]

    base_access = winreg.KEY_READ
    views = (
        ("64-bit", getattr(winreg, "KEY_WOW64_64KEY", 0)),
        ("32-bit", getattr(winreg, "KEY_WOW64_32KEY", 0)),
    )
    roots = (
        (winreg.HKEY_CURRENT_USER, r"Software\Classes"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Classes"),
    )
    for view_name, view_flag in views:
        for hive, root in roots:
            interface_root = rf"{root}\Interface\{POWERPOINT_APPLICATION_IID}"
            guid = _read_default(
                winreg,
                hive,
                interface_root + r"\TypeLib",
                base_access | view_flag,
            )
            if not guid:
                continue
            version = _read_default(
                winreg,
                hive,
                interface_root + r"\TypeLib\Version",
                base_access | view_flag,
            ) or _read_default(
                winreg,
                hive,
                interface_root + r"\Version",
                base_access | view_flag,
            )
            library_path: Path | None = None
            if version:
                for platform_key in ("win64", "win32"):
                    value = _read_default(
                        winreg,
                        hive,
                        rf"{root}\TypeLib\{guid}\{version}\0\{platform_key}",
                        base_access | view_flag,
                    )
                    if value:
                        library_path = Path(os.path.expandvars(value))
                        break
            return InterfaceTypeLibRegistration(
                POWERPOINT_APPLICATION_IID,
                guid,
                version,
                library_path,
                view_name,
            )
    return InterfaceTypeLibRegistration(
        POWERPOINT_APPLICATION_IID, None, None, None, None
    )


def _registry_command_path(value: str | None) -> Path | None:
    if not value:
        return None
    expanded = os.path.expandvars(value).strip()
    match = re.match(r'^"([^"]+)"|^(.+?\.exe)\b', expanded, re.I)
    if match is None:
        return Path(expanded)
    return Path(match.group(1) or match.group(2))


def _pe_bitness(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    try:
        with path.open("rb") as stream:
            header = stream.read(64)
            if len(header) < 64 or header[:2] != b"MZ":
                return None
            stream.seek(struct.unpack_from("<I", header, 0x3C)[0] + 4)
            machine = struct.unpack("<H", stream.read(2))[0]
    except (OSError, struct.error):
        return None
    return {
        0x014C: "32-bit",
        0x8664: "64-bit",
        0xAA64: "arm64",
    }.get(machine, f"machine-0x{machine:04X}")


def _windows_registered_typelib(guid: str) -> dict[str, object]:
    import winreg  # type: ignore[import-not-found]

    views = (
        ("64-bit", getattr(winreg, "KEY_WOW64_64KEY", 0)),
        ("32-bit", getattr(winreg, "KEY_WOW64_32KEY", 0)),
    )
    roots = (
        (winreg.HKEY_CURRENT_USER, r"Software\Classes", "HKCU"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Classes", "HKLM"),
    )
    candidates: list[tuple[tuple[int, ...], dict[str, object]]] = []
    for view_name, view_flag in views:
        for hive, root, hive_name in roots:
            base = rf"{root}\TypeLib\{guid}"
            try:
                with winreg.OpenKey(hive, base, 0, winreg.KEY_READ | view_flag) as key:
                    versions: list[str] = []
                    index = 0
                    while True:
                        try:
                            versions.append(winreg.EnumKey(key, index))
                        except OSError:
                            break
                        index += 1
            except OSError:
                continue
            for version in versions:
                library_path: Path | None = None
                for lcid in ("0", "409"):
                    for platform_key in ("win64", "win32"):
                        value = _read_default(
                            winreg,
                            hive,
                            rf"{base}\{version}\{lcid}\{platform_key}",
                            winreg.KEY_READ | view_flag,
                        )
                        if value:
                            library_path = Path(os.path.expandvars(value))
                            break
                    if library_path is not None:
                        break
                numeric = tuple(
                    int(item, 16 if re.search(r"[a-fA-F]", item) else 10)
                    for item in version.split(".")
                    if item
                )
                candidates.append(
                    (
                        numeric,
                        {
                            "guid": guid,
                            "version": version,
                            "path": str(library_path) if library_path else None,
                            "path_exists": bool(library_path and library_path.is_file()),
                            "registry_view": view_name,
                            "hive": hive_name,
                        },
                    )
                )
    if not candidates:
        return {
            "guid": guid,
            "version": None,
            "path": None,
            "path_exists": False,
            "load_type_lib": "not-run",
        }
    result = dict(max(candidates, key=lambda item: item[0])[1])
    library_value = result.get("path")
    load_status = "not-run"
    if isinstance(library_value, str) and Path(library_value).is_file():
        try:
            import pythoncom  # type: ignore[import-not-found]

            pythoncom.LoadTypeLib(library_value)
        except Exception as exc:
            load_status = f"failed: {type(exc).__name__}: {exc}"
        else:
            load_status = "passed"
    result["load_type_lib"] = load_status
    return result


def _windows_powerpoint_evidence(
    registration: InterfaceTypeLibRegistration,
) -> dict[str, object]:
    import winreg  # type: ignore[import-not-found]

    local_server: Path | None = None
    for view_flag in (
        getattr(winreg, "KEY_WOW64_64KEY", 0),
        getattr(winreg, "KEY_WOW64_32KEY", 0),
    ):
        for hive, root in (
            (winreg.HKEY_CURRENT_USER, r"Software\Classes"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Classes"),
        ):
            value = _read_default(
                winreg,
                hive,
                rf"{root}\CLSID\{POWERPOINT_APPLICATION_CLSID}\LocalServer32",
                winreg.KEY_READ | view_flag,
            )
            local_server = _registry_command_path(value)
            if local_server is not None:
                break
        if local_server is not None:
            break
    interface_guid = (registration.typelib_guid or "").upper()
    early_binding = (
        "blocked-by-interface-typelib"
        if interface_guid != POWERPOINT_TYPELIB.upper()
        or registration.typelib_path is None
        or not registration.typelib_path.is_file()
        else "registration-compatible"
    )
    return {
        "python_bitness": f"{struct.calcsize('P') * 8}-bit",
        "powerpoint_local_server": str(local_server) if local_server else None,
        "powerpoint_local_server_exists": bool(local_server and local_server.is_file()),
        "powerpoint_bitness": _pe_bitness(local_server),
        "microsoft_powerpoint_typelib": _windows_registered_typelib(
            POWERPOINT_TYPELIB
        ),
        "early_binding": {
            "status": early_binding,
            "interface_iid": POWERPOINT_APPLICATION_IID,
        },
        "late_binding": {
            "status": "available-through-safe-certifier",
            "probe": "not-run-by-read-only-doctor",
            "reason": (
                "late-bound IDispatch does not require generated _Application "
                "type metadata; use --certify-pptx for an ownership-proven probe"
            ),
        },
        "process_ownership_policy": (
            "certification fails closed if any POWERPNT.EXE already exists and "
            "never terminates an unowned process"
        ),
    }


def doctor_powerpoint() -> PowerPointDoctorResult:
    if platform.system().casefold() != "windows":
        finding = DiagnosticFinding(
            "POWERPOINT_DOCTOR_REQUIRES_WINDOWS",
            "warning",
            "registry diagnosis must run from native Windows Python",
        )
        return PowerPointDoctorResult(False, None, (finding,))
    registration = _windows_interface_registration()
    return PowerPointDoctorResult(
        True,
        registration,
        classify_interface_registration(registration),
        _windows_powerpoint_evidence(registration),
    )


def _powerpoint_pids() -> set[int]:
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq POWERPNT.EXE", "/FO", "CSV", "/NH"],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        raise PowerPointCertificationError("could not inventory POWERPNT.EXE processes")
    pids: set[int] = set()
    for row in csv.reader(io.StringIO(result.stdout)):
        if len(row) >= 2 and row[0].casefold() == "powerpnt.exe":
            try:
                pids.add(int(row[1].replace(",", "")))
            except ValueError:
                continue
    return pids


def _pid_for_powerpoint_window(hwnd: int) -> int:
    if not isinstance(hwnd, int) or hwnd <= 0:
        raise PowerPointCertificationError(
            "PowerPoint did not expose a valid application window handle"
        )
    process_id = ctypes.c_ulong(0)
    thread_id = ctypes.windll.user32.GetWindowThreadProcessId(  # type: ignore[attr-defined]
        hwnd,
        ctypes.byref(process_id),
    )
    if not thread_id or not process_id.value:
        raise PowerPointCertificationError(
            "could not bind the PowerPoint COM object to a process id"
        )
    return int(process_id.value)


def validate_portable_certification_input(
    candidate: Path,
    verification_report: Path,
) -> dict[str, Any]:
    """Bind standalone PowerPoint certification to a passed portable candidate."""

    try:
        payload = json.loads(verification_report.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PowerPointCertificationError(
            f"portable verification report is unreadable: {exc}"
        ) from exc
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version",
        "candidate_path",
        "candidate_sha256",
        "backend",
        "verification",
        "artifact_sha256",
        "artifact_files",
    }:
        raise PowerPointCertificationError(
            "portable verification report has an invalid contract"
        )
    backend = payload.get("backend")
    verification = payload.get("verification")
    quality = verification.get("quality") if isinstance(verification, dict) else None
    libreoffice = (
        verification.get("libreoffice") if isinstance(verification, dict) else None
    )
    if (
        payload.get("schema_version") != "1.0"
        or not isinstance(backend, dict)
        or backend.get("backend_id") != "pptxgenjs"
        or not isinstance(verification, dict)
        or verification.get("level") not in {"portable", "powerpoint"}
        or not isinstance(quality, dict)
        or quality.get("passed") is not True
        or quality.get("hard_gate_failures") != []
        or not isinstance(libreoffice, dict)
        or libreoffice.get("candidate_hash_before")
        != libreoffice.get("candidate_hash_after")
    ):
        raise PowerPointCertificationError(
            "portable verification report does not prove a passed portable candidate"
        )
    expected_hash = payload.get("candidate_sha256")
    if not isinstance(expected_hash, str) or expected_hash != sha256_file(candidate):
        raise PowerPointCertificationError(
            "portable verification report does not match the certification candidate"
        )
    if libreoffice.get("candidate_hash_after") != expected_hash:
        raise PowerPointCertificationError(
            "portable verification report contains inconsistent candidate hashes"
        )
    artifact_hashes = payload.get("artifact_sha256")
    artifact_files = payload.get("artifact_files")
    if not isinstance(artifact_hashes, dict) or not isinstance(artifact_files, dict):
        raise PowerPointCertificationError(
            "portable verification report has no hash-bound proof inventory"
        )
    required_artifacts = {"ooxml_report", "quality_report_v2", "portable_pdf"}
    png_keys = sorted(
        key
        for key in artifact_files
        if isinstance(key, str) and re.fullmatch(r"portable_png_\d{3}", key)
    )
    if (
        not required_artifacts.issubset(artifact_files)
        or not png_keys
        or not set(artifact_files).issubset(artifact_hashes)
        or artifact_hashes.get("output_pptx") != expected_hash
    ):
        raise PowerPointCertificationError(
            "portable verification proof inventory is incomplete"
        )
    report_root = verification_report.resolve().parent
    resolved_artifacts: dict[str, Path] = {}
    for key, relative_value in artifact_files.items():
        digest = artifact_hashes.get(key)
        if (
            not isinstance(key, str)
            or not isinstance(relative_value, str)
            or not re.fullmatch(r"[0-9a-f]{64}", str(digest))
        ):
            raise PowerPointCertificationError(
                "portable verification proof inventory contains invalid fields"
            )
        relative = Path(relative_value)
        if relative.is_absolute() or ".." in relative.parts:
            raise PowerPointCertificationError(
                "portable verification proof inventory contains an unsafe path"
            )
        proof_path = (report_root / relative).resolve()
        try:
            proof_path.relative_to(report_root)
        except ValueError as exc:
            raise PowerPointCertificationError(
                "portable verification proof escaped the report directory"
            ) from exc
        if not proof_path.is_file() or sha256_file(proof_path) != digest:
            raise PowerPointCertificationError(
                f"portable verification proof hash mismatch: {key}"
            )
        resolved_artifacts[key] = proof_path
    if not resolved_artifacts["portable_pdf"].read_bytes().startswith(b"%PDF-"):
        raise PowerPointCertificationError("portable verification PDF is unreadable")
    if any(
        not resolved_artifacts[key].read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
        for key in png_keys
    ):
        raise PowerPointCertificationError("portable verification PNG is unreadable")
    try:
        ooxml_payload = json.loads(
            resolved_artifacts["ooxml_report"].read_text(encoding="utf-8")
        )
        quality_payload = json.loads(
            resolved_artifacts["quality_report_v2"].read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise PowerPointCertificationError(
            f"portable verification proof report is unreadable: {exc}"
        ) from exc
    if ooxml_payload != verification.get("ooxml") or quality_payload != quality:
        raise PowerPointCertificationError(
            "portable verification proof reports do not match the manifest"
        )
    if len(png_keys) != libreoffice.get("page_count"):
        raise PowerPointCertificationError(
            "portable verification PNG count does not match LibreOffice evidence"
        )
    try:
        validate_ooxml_package(candidate)
    except Exception as exc:
        raise PowerPointCertificationError(
            f"certification candidate is not a readable OOXML package: {exc}"
        ) from exc
    return payload


def certify_powerpoint(candidate: Path, *, artifact_dir: Path) -> PowerPointCertificationResult:
    """Open and export a portable candidate without touching pre-existing PowerPoint."""

    if platform.system().casefold() != "windows":
        raise PowerPointCertificationError("PowerPoint certification requires Windows")
    if not candidate.is_file() or candidate.suffix.casefold() != ".pptx":
        raise PowerPointCertificationError("certification candidate must be a readable .pptx")
    before_pids = _powerpoint_pids()
    if before_pids:
        raise PowerPointCertificationError(
            "certification fails closed while a user PowerPoint process already exists"
        )
    before_hash = sha256_file(candidate)
    try:
        import pythoncom  # type: ignore[import-not-found]
        from win32com.client import dynamic  # type: ignore[import-not-found]
    except ImportError as exc:
        raise PowerPointCertificationError("pywin32 is required for certification") from exc

    app = None
    presentation = None
    old_security = None
    failure: Exception | None = None
    owned_pid: int | None = None
    version: str | None = None
    pdf_path: Path | None = None
    png_paths: list[Path] = []
    with tempfile.TemporaryDirectory(prefix="pptx-studio-cert-") as temp_value:
        certification_copy = Path(temp_value) / "candidate-copy.pptx"
        shutil.copyfile(candidate, certification_copy)
        if sha256_file(certification_copy) != before_hash:
            raise PowerPointCertificationError(
                "could not create an exact certification copy"
            )
        try:
            raw = pythoncom.CoCreateInstance(
                POWERPOINT_APPLICATION_CLSID,
                None,
                pythoncom.CLSCTX_LOCAL_SERVER,
                pythoncom.IID_IDispatch,
            )
            app = dynamic.Dispatch(raw)
            new_pids = _powerpoint_pids() - before_pids
            hwnd_pid = _pid_for_powerpoint_window(int(getattr(app, "HWND", 0)))
            if new_pids != {hwnd_pid}:
                raise PowerPointCertificationError(
                    "could not bind the COM window to one uniquely created "
                    f"PowerPoint process: hwnd_pid={hwnd_pid}, new={sorted(new_pids)}"
                )
            owned_pid = hwnd_pid
            old_security = getattr(app, "AutomationSecurity", None)
            app.AutomationSecurity = 3
            presentation = app.Presentations.Open(
                str(certification_copy), -1, 0, 0
            )
            if _powerpoint_pids() - before_pids != {owned_pid}:
                raise PowerPointCertificationError(
                    "PowerPoint process inventory changed during certification"
                )
            artifact_dir.mkdir(parents=True, exist_ok=True)
            pdf_path = artifact_dir / "powerpoint-certification.pdf"
            pdf_path.unlink(missing_ok=True)
            for stale in artifact_dir.glob("slide-*.png"):
                stale.unlink()
            presentation.ExportAsFixedFormat(str(pdf_path), 2, 2)
            if not pdf_path.read_bytes().startswith(b"%PDF-"):
                raise PowerPointCertificationError("PowerPoint PDF export is unreadable")
            for index in range(1, int(presentation.Slides.Count) + 1):
                png = artifact_dir / f"slide-{index:03d}.png"
                presentation.Slides.Item(index).Export(str(png), "PNG")
                if not png.read_bytes().startswith(b"\x89PNG"):
                    raise PowerPointCertificationError(
                        f"PowerPoint PNG is unreadable: {png}"
                    )
                png_paths.append(png)
            version = str(getattr(app, "Version", "unknown"))
        except Exception as exc:
            failure = exc
        finally:
            if presentation is not None:
                try:
                    presentation.Close()
                except Exception:
                    pass
            if app is not None and old_security is not None:
                try:
                    app.AutomationSecurity = old_security
                except Exception:
                    pass
            if app is not None and owned_pid is not None:
                try:
                    app.Quit()
                except Exception:
                    pass
    after_hash = sha256_file(candidate)
    if after_hash != before_hash:
        raise PowerPointCertificationError("PowerPoint certification mutated the candidate")
    residual: set[int] = set()
    for _attempt in range(50):
        residual = _powerpoint_pids() - before_pids
        if not residual:
            break
        time.sleep(0.2)
    if residual:
        raise PowerPointCertificationError(
            f"PowerPoint certification left owned process residue: {sorted(residual)}"
        )
    if failure is not None:
        if isinstance(failure, PowerPointCertificationError):
            raise failure
        raise PowerPointCertificationError(
            f"PowerPoint certification failed: {type(failure).__name__}: {failure}"
        ) from failure
    if owned_pid is None or version is None or pdf_path is None or not png_paths:
        raise PowerPointCertificationError(
            "PowerPoint certification returned incomplete evidence"
        )
    return PowerPointCertificationResult(
        version,
        pdf_path,
        tuple(png_paths),
        before_hash,
        after_hash,
        owned_pid,
    )


__all__ = [
    "DiagnosticFinding",
    "InterfaceTypeLibRegistration",
    "PowerPointCertificationError",
    "PowerPointCertificationResult",
    "PowerPointDoctorResult",
    "certify_powerpoint",
    "classify_interface_registration",
    "doctor_powerpoint",
    "validate_portable_certification_input",
]
