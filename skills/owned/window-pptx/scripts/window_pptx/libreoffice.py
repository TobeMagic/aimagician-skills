"""Isolated LibreOffice/Poppler proof rendering for portable PPTX delivery."""

from __future__ import annotations

import os
import re
import shutil
import signal
import struct
import subprocess
import tempfile
import time
import ctypes
from dataclasses import dataclass
from pathlib import Path

from .layouts import SlideSize
from .transaction import sha256_file


class LibreOfficeVerificationError(RuntimeError):
    """The independent render proof could not be completed safely."""


@dataclass(frozen=True)
class LibreOfficeVerificationResult:
    engine_version: str
    poppler_version: str
    page_count: int
    page_width_pt: float
    page_height_pt: float
    pdf_path: Path
    png_paths: tuple[Path, ...]
    candidate_hash_before: str
    candidate_hash_after: str

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "engine": "libreoffice",
            "engine_version": self.engine_version,
            "poppler_version": self.poppler_version,
            "page_count": self.page_count,
            "page_width_pt": self.page_width_pt,
            "page_height_pt": self.page_height_pt,
            "pdf_path": str(self.pdf_path),
            "png_paths": [str(path) for path in self.png_paths],
            "candidate_hash_before": self.candidate_hash_before,
            "candidate_hash_after": self.candidate_hash_after,
        }


def _required_command(*names: str) -> str:
    for name in names:
        resolved = shutil.which(name)
        if resolved:
            return resolved
    raise LibreOfficeVerificationError(
        "PORTABLE_DEPENDENCY_MISSING: expected executable " + "/".join(names)
    )


def _run_owned_process(
    command: list[str],
    *,
    timeout_seconds: int,
    cwd: Path,
) -> subprocess.CompletedProcess[str]:
    creationflags = 0
    start_new_session = os.name != "nt"
    if os.name == "nt":
        creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
    try:
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=start_new_session,
            creationflags=creationflags,
        )
    except OSError as exc:
        raise LibreOfficeVerificationError(
            f"PROOF_PROCESS_START_FAILED: {command[0]}: {exc}"
        ) from exc
    job_handle: int | None = None
    if os.name == "nt":
        try:
            job_handle = _assign_windows_kill_job(process)
        except Exception:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
            process.communicate()
            raise
    try:
        try:
            stdout, stderr = process.communicate(timeout=timeout_seconds)
        except subprocess.TimeoutExpired as exc:
            _terminate_owned_process(process, job_handle=job_handle)
            if os.name == "nt":
                job_handle = None
            raise LibreOfficeVerificationError(
                f"PROOF_PROCESS_TIMEOUT: {command[0]} exceeded {timeout_seconds}s"
            ) from exc
        if os.name != "nt":
            _terminate_posix_residue(process.pid)
    finally:
        if job_handle is not None:
            _close_windows_job(job_handle)
    result = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().replace("\n", " ")[:800]
        raise LibreOfficeVerificationError(
            f"PROOF_PROCESS_FAILED: {command[0]} exited {result.returncode}: {detail}"
        )
    return result


def _posix_group_exists(pid: int) -> bool:
    try:
        os.killpg(pid, 0)
    except OSError:
        return False
    return True


def _terminate_posix_residue(pid: int) -> None:
    if not _posix_group_exists(pid):
        return
    try:
        os.killpg(pid, signal.SIGTERM)
    except OSError:
        pass
    for _attempt in range(40):
        if not _posix_group_exists(pid):
            return
        time.sleep(0.05)
    try:
        os.killpg(pid, signal.SIGKILL)
    except OSError:
        pass
    for _attempt in range(40):
        if not _posix_group_exists(pid):
            return
        time.sleep(0.05)
    raise LibreOfficeVerificationError(
        f"PROOF_PROCESS_RESIDUE: owned process group {pid} did not exit"
    )


def _terminate_owned_process(
    process: subprocess.Popen[str],
    *,
    job_handle: int | None,
) -> None:
    if os.name == "nt":
        if job_handle is not None:
            _close_windows_job(job_handle)
        else:
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                check=False,
                capture_output=True,
                text=True,
                timeout=15,
            )
        try:
            process.communicate(timeout=10)
        except subprocess.TimeoutExpired as exc:
            raise LibreOfficeVerificationError(
                f"PROOF_PROCESS_RESIDUE: owned Windows process {process.pid} did not exit"
            ) from exc
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except OSError:
        pass
    try:
        process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            pass
        process.communicate()
    _terminate_posix_residue(process.pid)


def _assign_windows_kill_job(process: subprocess.Popen[str]) -> int:
    """Bind a child tree to a kill-on-close Job Object on Windows."""

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_ulonglong),
            ("WriteOperationCount", ctypes.c_ulonglong),
            ("OtherOperationCount", ctypes.c_ulonglong),
            ("ReadTransferCount", ctypes.c_ulonglong),
            ("WriteTransferCount", ctypes.c_ulonglong),
            ("OtherTransferCount", ctypes.c_ulonglong),
        ]

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_longlong),
            ("PerJobUserTimeLimit", ctypes.c_longlong),
            ("LimitFlags", ctypes.c_uint32),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", ctypes.c_uint32),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", ctypes.c_uint32),
            ("SchedulingClass", ctypes.c_uint32),
        ]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    kernel32.CreateJobObjectW.restype = ctypes.c_void_p
    kernel32.SetInformationJobObject.argtypes = [
        ctypes.c_void_p,
        ctypes.c_int,
        ctypes.c_void_p,
        ctypes.c_uint32,
    ]
    kernel32.SetInformationJobObject.restype = ctypes.c_int
    kernel32.AssignProcessToJobObject.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
    kernel32.AssignProcessToJobObject.restype = ctypes.c_int
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int

    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        raise LibreOfficeVerificationError(
            f"PROOF_JOB_CREATE_FAILED: winerror={ctypes.get_last_error()}"
        )
    information = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    information.BasicLimitInformation.LimitFlags = 0x00002000
    if not kernel32.SetInformationJobObject(
        job,
        9,
        ctypes.byref(information),
        ctypes.sizeof(information),
    ) or not kernel32.AssignProcessToJobObject(  # type: ignore[attr-defined]
        job,
        ctypes.c_void_p(int(process._handle)),
    ):
        error = ctypes.get_last_error()
        kernel32.CloseHandle(job)
        raise LibreOfficeVerificationError(
            f"PROOF_JOB_ASSIGN_FAILED: winerror={error}"
        )
    return int(job)


def _close_windows_job(job_handle: int) -> None:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel32.CloseHandle.restype = ctypes.c_int
    kernel32.CloseHandle(ctypes.c_void_p(job_handle))


def _first_version_line(command: str) -> str:
    result = subprocess.run(
        [command, "--version"],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        return "unknown"
    return (result.stdout or result.stderr).strip().splitlines()[0]


def _pdf_info(pdfinfo: str, pdf_path: Path, *, timeout_seconds: int) -> tuple[int, float, float, str]:
    result = _run_owned_process(
        [pdfinfo, str(pdf_path)],
        timeout_seconds=timeout_seconds,
        cwd=pdf_path.parent,
    )
    pages_match = re.search(r"^Pages:\s+(\d+)\s*$", result.stdout, re.MULTILINE)
    size_match = re.search(
        r"^Page size:\s+([0-9.]+)\s+x\s+([0-9.]+)\s+pts",
        result.stdout,
        re.MULTILINE,
    )
    if pages_match is None or size_match is None:
        raise LibreOfficeVerificationError(
            "PDFINFO_UNPARSABLE: missing Pages or Page size"
        )
    version = subprocess.run(
        [pdfinfo, "-v"],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    version_line = (version.stderr or version.stdout).strip().splitlines()[0]
    return (
        int(pages_match.group(1)),
        float(size_match.group(1)),
        float(size_match.group(2)),
        version_line,
    )


def inspect_pdf_geometry(
    pdf_path: Path,
    *,
    expected_slide_count: int,
    slide_size: SlideSize,
    pdfinfo: str | None = None,
    timeout_seconds: int = 30,
) -> tuple[int, float, float, str]:
    """Validate a proof PDF's signature, page count, and governed page size."""

    if (
        not pdf_path.is_file()
        or not pdf_path.read_bytes().startswith(b"%PDF-")
    ):
        raise LibreOfficeVerificationError(
            f"PDF_UNREADABLE: {pdf_path}"
        )
    result = _pdf_info(
        pdfinfo or _required_command("pdfinfo"),
        pdf_path,
        timeout_seconds=timeout_seconds,
    )
    page_count, width_pt, height_pt, _version = result
    if page_count != expected_slide_count:
        raise LibreOfficeVerificationError(
            f"PDF_PAGE_COUNT_MISMATCH: expected {expected_slide_count}, "
            f"observed {page_count}"
        )
    expected_width = slide_size.width * 72
    expected_height = slide_size.height * 72
    if abs(width_pt - expected_width) > 1.5 or abs(height_pt - expected_height) > 1.5:
        raise LibreOfficeVerificationError(
            "PDF_PAGE_SIZE_MISMATCH: "
            f"expected {expected_width:.2f}x{expected_height:.2f}pt, "
            f"observed {width_pt:.2f}x{height_pt:.2f}pt"
        )
    return result


class LibreOfficeVerifier:
    """Render a copy through LibreOffice and an independent PDF rasterizer."""

    def __init__(
        self,
        *,
        soffice: str | None = None,
        pdfinfo: str | None = None,
        pdftoppm: str | None = None,
        ghostscript: str | None = None,
        timeout_seconds: int = 120,
        dpi: int = 144,
    ) -> None:
        self.soffice = soffice
        self.pdfinfo = pdfinfo
        self.pdftoppm = pdftoppm
        self.ghostscript = ghostscript
        if not isinstance(timeout_seconds, int) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be a positive integer")
        if not isinstance(dpi, int) or dpi <= 0:
            raise ValueError("dpi must be a positive integer")
        self.timeout_seconds = timeout_seconds
        self.dpi = dpi

    def verify(
        self,
        candidate: Path,
        *,
        artifact_dir: Path,
        expected_slide_count: int,
        slide_size: SlideSize,
    ) -> LibreOfficeVerificationResult:
        if candidate.suffix.casefold() != ".pptx" or not candidate.is_file():
            raise LibreOfficeVerificationError(
                f"PORTABLE_CANDIDATE_INVALID: {candidate}"
            )
        soffice = self.soffice or _required_command("soffice", "libreoffice")
        pdfinfo = self.pdfinfo or shutil.which("pdfinfo")
        pdftoppm = self.pdftoppm or shutil.which("pdftoppm")
        use_poppler = pdfinfo is not None and pdftoppm is not None
        ghostscript = None
        if not use_poppler:
            ghostscript = self.ghostscript or _required_command("gs", "gswin64c", "gswin32c")
        before = sha256_file(candidate)
        artifact_dir.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix="window-pptx-lo-") as value:
            work = Path(value)
            profile = work / "profile"
            source_dir = work / "source"
            export_dir = work / "export"
            source_dir.mkdir()
            export_dir.mkdir()
            source_copy = source_dir / "candidate.pptx"
            shutil.copyfile(candidate, source_copy)
            command = [
                soffice,
                f"-env:UserInstallation={profile.as_uri()}",
                "--headless",
                "--nologo",
                "--nodefault",
                "--nolockcheck",
                "--norestore",
                "--nofirststartwizard",
                "--convert-to",
                "pdf:impress_pdf_Export",
                "--outdir",
                str(export_dir),
                str(source_copy),
            ]
            _run_owned_process(
                command,
                timeout_seconds=self.timeout_seconds,
                cwd=work,
            )
            generated_pdf = export_dir / "candidate.pdf"
            if not generated_pdf.is_file() or not generated_pdf.read_bytes().startswith(b"%PDF-"):
                raise LibreOfficeVerificationError(
                    "LIBREOFFICE_PDF_MISSING: conversion produced no readable PDF"
                )
            if use_poppler:
                page_count, width_pt, height_pt, rasterizer_version = inspect_pdf_geometry(
                    generated_pdf,
                    expected_slide_count=expected_slide_count,
                    slide_size=slide_size,
                    pdfinfo=pdfinfo,
                    timeout_seconds=self.timeout_seconds,
                )
            else:
                page_count = expected_slide_count
                width_pt = slide_size.width * 72
                height_pt = slide_size.height * 72
                rasterizer_version = "Ghostscript " + _first_version_line(ghostscript)

            png_prefix = export_dir / "slide"
            if use_poppler:
                _run_owned_process(
                    [
                        pdftoppm,
                        "-png",
                        "-r",
                        str(self.dpi),
                        str(generated_pdf),
                        str(png_prefix),
                    ],
                    timeout_seconds=self.timeout_seconds,
                    cwd=work,
                )
            else:
                _run_owned_process(
                    [
                        ghostscript,
                        "-dSAFER",
                        "-dBATCH",
                        "-dNOPAUSE",
                        "-dQUIET",
                        "-sDEVICE=png16m",
                        f"-r{self.dpi}",
                        f"-sOutputFile={export_dir / 'slide-%03d.png'}",
                        str(generated_pdf),
                    ],
                    timeout_seconds=self.timeout_seconds,
                    cwd=work,
                )
            generated_pngs = tuple(
                sorted(
                    export_dir.glob("slide-*.png"),
                    key=lambda path: int(path.stem.rsplit("-", 1)[1]),
                )
            )
            if len(generated_pngs) != expected_slide_count:
                raise LibreOfficeVerificationError(
                    f"PNG_PAGE_COUNT_MISMATCH: expected {expected_slide_count}, "
                    f"observed {len(generated_pngs)}"
                )
            page_count = len(generated_pngs)
            for png in generated_pngs:
                payload = png.read_bytes()
                if not payload.startswith(b"\x89PNG\r\n\x1a\n") or len(payload) < 24:
                    raise LibreOfficeVerificationError(
                        f"PNG_UNREADABLE: {png.name}"
                    )
                width_px, height_px = struct.unpack(">II", payload[16:24])
                expected_width_px = round(slide_size.width * self.dpi)
                expected_height_px = round(slide_size.height * self.dpi)
                if (
                    abs(width_px - expected_width_px) > 3
                    or abs(height_px - expected_height_px) > 3
                ):
                    raise LibreOfficeVerificationError(
                        "PNG_PAGE_SIZE_MISMATCH: "
                        f"expected {expected_width_px}x{expected_height_px}px, "
                        f"observed {width_px}x{height_px}px"
                    )

            pdf_target = artifact_dir / "portable-proof.pdf"
            pdf_target.unlink(missing_ok=True)
            for stale in artifact_dir.glob("slide-*.png"):
                stale.unlink()
            shutil.copyfile(generated_pdf, pdf_target)
            png_targets: list[Path] = []
            for index, png in enumerate(generated_pngs, start=1):
                target = artifact_dir / f"slide-{index:03d}.png"
                shutil.copyfile(png, target)
                png_targets.append(target)

        after = sha256_file(candidate)
        if after != before:
            raise LibreOfficeVerificationError(
                "CANDIDATE_MUTATED_BY_PROOF_RENDERER: PPTX hash changed"
            )
        return LibreOfficeVerificationResult(
            engine_version=_first_version_line(soffice),
            poppler_version=rasterizer_version,
            page_count=page_count,
            page_width_pt=width_pt,
            page_height_pt=height_pt,
            pdf_path=pdf_target,
            png_paths=tuple(png_targets),
            candidate_hash_before=before,
            candidate_hash_after=after,
        )


__all__ = [
    "LibreOfficeVerificationError",
    "LibreOfficeVerificationResult",
    "LibreOfficeVerifier",
    "inspect_pdf_geometry",
]
