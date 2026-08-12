#!/usr/bin/env python3
"""Build the fail-closed Phase 49 reference/candidate blind-review packet.

The packet is intentionally visual-only for reviewers, but cryptographically
binds the two source decks, the physical-assembly report, the deterministic
rule-QA report, every rendered page, every comparison image, and the renderer
toolchain.  Reference and candidate decks are always rendered independently by
the same LibreOffice and pdftoppm executables at the same DPI.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Mapping, Sequence

from PIL import Image, ImageDraw, ImageFont, __version__ as PILLOW_VERSION


SCHEMA_VERSION = "1.0"
PACKET_KIND = "phase49-reference-candidate-blind-review"
PHASE49_EXPECTED_SLIDE_COUNT = 15
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RASTER_PAGE_RE = re.compile(r"^page-([0-9]+)\.png$")
PRESENTATION_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
PAIR_CELL_WIDTH = 960
PAIR_CELL_HEIGHT = 540
PAIR_MARGIN = 24
PAIR_GUTTER = 24
PAIR_HEADER_HEIGHT = 62
PAIR_LABEL_HEIGHT = 46
PAIR_ROW_GAP = 24
COMMAND_TIMEOUT_SECONDS = 180


class BlindPacketError(ValueError):
    """Raised when a packet cannot be proven complete and internally bound."""


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _require_sha256(value: str, label: str) -> str:
    normalized = value.strip().lower()
    if not SHA256_RE.fullmatch(normalized):
        raise BlindPacketError(f"{label} must be a lowercase SHA-256 digest")
    return normalized


def _require_regular_file(path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve(strict=False)
    if not resolved.is_file():
        raise BlindPacketError(f"{label} is missing or not a regular file: {resolved}")
    return resolved


def _json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BlindPacketError(f"{label} is not valid UTF-8 JSON: {exc}") from exc
    if not isinstance(value, dict):
        raise BlindPacketError(f"{label} must contain a JSON object")
    return value


def _pptx_slide_count(path: Path) -> int:
    """Count authored slides from presentation.xml, not orphan slide parts."""

    try:
        with zipfile.ZipFile(path, "r") as archive:
            root = ET.fromstring(archive.read("ppt/presentation.xml"))
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as exc:
        raise BlindPacketError(f"PPTX cannot be inspected: {path}: {exc}") from exc
    slide_lists = root.findall(f"{{{PRESENTATION_NS}}}sldIdLst")
    if len(slide_lists) != 1:
        raise BlindPacketError(f"PPTX has no unique slide list: {path}")
    slide_ids = slide_lists[0].findall(f"{{{PRESENTATION_NS}}}sldId")
    relationship_ids = [
        item.attrib.get(
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id",
            "",
        )
        for item in slide_ids
    ]
    if any(not value for value in relationship_ids):
        raise BlindPacketError(f"PPTX slide list has a missing relationship id: {path}")
    if len(set(relationship_ids)) != len(relationship_ids):
        raise BlindPacketError(f"PPTX slide list has duplicate relationship ids: {path}")
    return len(slide_ids)


def _require_pass_status(value: Mapping[str, Any], location: str) -> None:
    if value.get("status") != "pass":
        raise BlindPacketError(f"{location}.status must be 'pass'")


def _validate_physical_report(
    report: Mapping[str, Any],
    *,
    candidate_sha256: str,
    expected_slide_count: int,
) -> None:
    """Recheck the release-critical Phase 49 report invariants."""

    if report.get("schema_version") != "1.0":
        raise BlindPacketError("physical report schema_version must equal '1.0'")
    _require_pass_status(report, "physical report")
    if report.get("acceptance_profile") != "phase49-work-report-15":
        raise BlindPacketError("physical report acceptance_profile is not Phase 49")
    if report.get("output_sha256") != candidate_sha256:
        raise BlindPacketError("physical report is not bound to the candidate SHA-256")
    for field in ("expected_slide_count", "target_slide_count"):
        if report.get(field) != expected_slide_count:
            raise BlindPacketError(
                f"physical report {field} must equal {expected_slide_count}"
            )
    if report.get("distinct_page_id_count") != expected_slide_count:
        raise BlindPacketError("physical report does not prove 15 distinct physical pages")
    if report.get("duplicate_page_records") != []:
        raise BlindPacketError("physical report contains duplicate physical pages")

    lineage = report.get("lineage_records")
    if not isinstance(lineage, list) or len(lineage) != expected_slide_count:
        raise BlindPacketError("physical report lineage does not cover every slide")
    ordinals: list[int] = []
    page_ids: list[str] = []
    for index, record in enumerate(lineage, start=1):
        if not isinstance(record, dict):
            raise BlindPacketError(f"physical report lineage[{index}] is not an object")
        ordinal = record.get("ordinal")
        page_id = record.get("page_id")
        if not isinstance(ordinal, int):
            raise BlindPacketError(f"physical report lineage[{index}].ordinal is invalid")
        if not isinstance(page_id, str) or not page_id:
            raise BlindPacketError(f"physical report lineage[{index}].page_id is invalid")
        ordinals.append(ordinal)
        page_ids.append(page_id)
        for flag in (
            "source_package_verified",
            "source_slide_verified",
            "structure_match",
        ):
            if record.get(flag) is not True:
                raise BlindPacketError(
                    f"physical report lineage[{index}].{flag} must be true"
                )
        _require_pass_status(record, f"physical report lineage[{index}]")
    expected_ordinals = list(range(1, expected_slide_count + 1))
    if ordinals != expected_ordinals:
        raise BlindPacketError("physical report lineage ordinals are duplicated or missing")
    if len(set(page_ids)) != expected_slide_count:
        raise BlindPacketError("physical report lineage page_ids are duplicated")

    for field in (
        "opc_integrity",
        "editability",
        "style_cluster_adherence",
        "authority",
        "selection_authority",
        "source_residue",
        "libreoffice",
        "size_check",
    ):
        value = report.get(field)
        if not isinstance(value, dict):
            raise BlindPacketError(f"physical report {field} must be an object")
        _require_pass_status(value, f"physical report {field}")
    libreoffice = report["libreoffice"]
    if libreoffice.get("open_result") != "pass" or libreoffice.get("render_result") != "pass":
        raise BlindPacketError("physical report LibreOffice open/render did not pass")
    editability = report["editability"]
    if editability.get("native_editable") is not True:
        raise BlindPacketError("physical report does not prove native editability")
    if editability.get("native_editable_coverage") != 1:
        raise BlindPacketError("physical report native editable coverage must equal 1")


def _validate_rule_qa(
    report: Mapping[str, Any],
    *,
    candidate_sha256: str,
    candidate_size_bytes: int,
    expected_slide_count: int,
) -> None:
    if report.get("schema_version") != "1.1":
        raise BlindPacketError("rule-QA schema_version must equal '1.1'")
    _require_pass_status(report, "rule-QA report")
    if report.get("output_sha256") != candidate_sha256:
        raise BlindPacketError("rule-QA report is not bound to the candidate SHA-256")
    if report.get("output_size_bytes") != candidate_size_bytes:
        raise BlindPacketError("rule-QA report is not bound to the candidate size")
    if report.get("output_identity_status") != "verified-stable":
        raise BlindPacketError("rule-QA report does not prove stable output identity")
    if report.get("slide_count") != expected_slide_count:
        raise BlindPacketError("rule-QA slide_count does not match acceptance")
    if report.get("blocking_findings") != []:
        raise BlindPacketError("rule-QA report contains blocking findings")


def _run_command(command: Sequence[str], *, label: str) -> subprocess.CompletedProcess[str]:
    try:
        completed = subprocess.run(
            list(command),
            check=False,
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise BlindPacketError(f"{label} could not run: {exc}") from exc
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()[-1000:]
        raise BlindPacketError(
            f"{label} failed with exit code {completed.returncode}: {detail}"
        )
    return completed


def _tool_record(
    explicit: Path | None,
    *names: str,
    version_args: Sequence[str],
) -> dict[str, Any]:
    selected: str | None
    if explicit is not None:
        resolved = explicit.expanduser().resolve(strict=False)
        selected = str(resolved) if resolved.is_file() else None
    else:
        selected = next((shutil.which(name) for name in names if shutil.which(name)), None)
    if selected is None:
        raise BlindPacketError(f"required tool is unavailable: {'/'.join(names)}")
    executable = Path(selected).resolve(strict=True)
    completed = _run_command(
        [str(executable), *version_args],
        label=f"{'/'.join(names)} version probe",
    )
    version = next(
        (
            line.strip()
            for line in (completed.stdout + "\n" + completed.stderr).splitlines()
            if line.strip()
        ),
        "",
    )
    if not version:
        raise BlindPacketError(f"required tool returned no version: {executable}")
    return {
        "executable": str(executable),
        "version": version,
        "sha256": _sha256(executable),
        "size_bytes": executable.stat().st_size,
    }


def _png_record(path: Path, relative_to: Path, ordinal: int) -> dict[str, Any]:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
    except (OSError, SyntaxError) as exc:
        raise BlindPacketError(f"rendered page is not a valid PNG: {path}: {exc}") from exc
    if width < 1 or height < 1:
        raise BlindPacketError(f"rendered page has invalid dimensions: {path}")
    return {
        "ordinal": ordinal,
        "path": path.relative_to(relative_to).as_posix(),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
        "width_px": width,
        "height_px": height,
    }


def _collect_raster_pages(raw_dir: Path, expected_slide_count: int) -> dict[int, Path]:
    pages: dict[int, Path] = {}
    for path in sorted(raw_dir.iterdir(), key=lambda item: item.name):
        if not path.is_file():
            raise BlindPacketError(f"unexpected raster output: {path.name}")
        match = RASTER_PAGE_RE.fullmatch(path.name)
        if match is None:
            raise BlindPacketError(f"unexpected raster output: {path.name}")
        ordinal = int(match.group(1))
        if ordinal in pages:
            raise BlindPacketError(f"duplicate rendered page ordinal: {ordinal}")
        pages[ordinal] = path
    expected = set(range(1, expected_slide_count + 1))
    observed = set(pages)
    if observed != expected:
        missing = sorted(expected - observed)
        extra = sorted(observed - expected)
        raise BlindPacketError(
            f"rendered page coverage mismatch; missing={missing}, extra={extra}"
        )
    return pages


def _render_deck(
    source: Path,
    *,
    label: str,
    expected_sha256: str,
    expected_slide_count: int,
    dpi: int,
    libreoffice: Path,
    pdftoppm: Path,
    packet_root: Path,
    work_root: Path,
) -> dict[str, Any]:
    render_work = work_root / label
    render_work.mkdir(parents=True)
    local_pptx = render_work / f"{label}.pptx"
    shutil.copyfile(source, local_pptx)
    if _sha256(local_pptx) != expected_sha256:
        raise BlindPacketError(f"{label} deck changed while it was staged")

    pdf_dir = render_work / "pdf"
    raster_dir = render_work / "raster"
    profile_dir = render_work / "libreoffice-profile"
    pdf_dir.mkdir()
    raster_dir.mkdir()
    profile_dir.mkdir()
    _run_command(
        [
            str(libreoffice),
            "--headless",
            "--nologo",
            "--nodefault",
            "--nolockcheck",
            "--norestore",
            f"-env:UserInstallation={profile_dir.resolve().as_uri()}",
            "--convert-to",
            "pdf",
            "--outdir",
            str(pdf_dir),
            str(local_pptx),
        ],
        label=f"LibreOffice {label} render",
    )
    pdfs = tuple(pdf_dir.glob("*.pdf"))
    expected_pdf = pdf_dir / f"{label}.pdf"
    if pdfs != (expected_pdf,):
        raise BlindPacketError(
            f"LibreOffice {label} render produced an unexpected PDF set"
        )
    _run_command(
        [
            str(pdftoppm),
            "-png",
            "-r",
            str(dpi),
            str(expected_pdf),
            str(raster_dir / "page"),
        ],
        label=f"pdftoppm {label} rasterization",
    )
    raw_pages = _collect_raster_pages(raster_dir, expected_slide_count)

    target_root = packet_root / "renders" / label
    page_root = target_root / "pages"
    page_root.mkdir(parents=True)
    target_pdf = target_root / f"{label}.pdf"
    shutil.copyfile(expected_pdf, target_pdf)
    page_records: list[dict[str, Any]] = []
    for ordinal in range(1, expected_slide_count + 1):
        target = page_root / f"slide-{ordinal:03d}.png"
        shutil.copyfile(raw_pages[ordinal], target)
        page_records.append(_png_record(target, packet_root, ordinal))
    if _sha256(source) != expected_sha256:
        raise BlindPacketError(f"{label} deck changed during rendering")
    return {
        "pdf": {
            "path": target_pdf.relative_to(packet_root).as_posix(),
            "sha256": _sha256(target_pdf),
            "size_bytes": target_pdf.stat().st_size,
        },
        "page_count": len(page_records),
        "pages": page_records,
    }


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(name, size=size)
    except OSError:
        try:
            return ImageFont.load_default(size=size)
        except TypeError:  # pragma: no cover - older Pillow compatibility
            return ImageFont.load_default()


def _fit_page(image: Image.Image) -> Image.Image:
    fitted = image.convert("RGB")
    fitted.thumbnail((PAIR_CELL_WIDTH, PAIR_CELL_HEIGHT), Image.Resampling.LANCZOS)
    return fitted


def _write_pair_image(
    *,
    packet_root: Path,
    pair_index: int,
    slide_ordinals: Sequence[int],
    reference_pages: Mapping[int, Path],
    candidate_pages: Mapping[int, Path],
) -> dict[str, Any]:
    row_height = PAIR_LABEL_HEIGHT + PAIR_CELL_HEIGHT
    width = PAIR_MARGIN * 2 + PAIR_CELL_WIDTH * 2 + PAIR_GUTTER
    height = (
        PAIR_MARGIN * 2
        + PAIR_HEADER_HEIGHT
        + len(slide_ordinals) * row_height
        + max(0, len(slide_ordinals) - 1) * PAIR_ROW_GAP
    )
    canvas = Image.new("RGB", (width, height), "#F2F4F7")
    draw = ImageDraw.Draw(canvas)
    header_font = _font(30, bold=True)
    label_font = _font(25, bold=True)
    range_label = (
        f"SLIDE {slide_ordinals[0]:02d}"
        if len(slide_ordinals) == 1
        else f"SLIDES {slide_ordinals[0]:02d}-{slide_ordinals[-1]:02d}"
    )
    draw.text(
        (PAIR_MARGIN, PAIR_MARGIN + 4),
        f"PHASE 49 BLIND COMPARISON  /  {range_label}",
        fill="#111827",
        font=header_font,
    )
    labels: list[dict[str, Any]] = []
    for row, ordinal in enumerate(slide_ordinals):
        top = PAIR_MARGIN + PAIR_HEADER_HEIGHT + row * (row_height + PAIR_ROW_GAP)
        for column, (kind, border, source) in enumerate(
            (
                ("REFERENCE", "#2457A6", reference_pages[ordinal]),
                ("CANDIDATE", "#0E7C66", candidate_pages[ordinal]),
            )
        ):
            left = PAIR_MARGIN + column * (PAIR_CELL_WIDTH + PAIR_GUTTER)
            label = f"{kind}  /  SLIDE {ordinal:02d}"
            draw.rounded_rectangle(
                (
                    left,
                    top,
                    left + PAIR_CELL_WIDTH,
                    top + PAIR_LABEL_HEIGHT + PAIR_CELL_HEIGHT,
                ),
                radius=8,
                fill="#FFFFFF",
                outline=border,
                width=4,
            )
            draw.rectangle(
                (left, top, left + PAIR_CELL_WIDTH, top + PAIR_LABEL_HEIGHT),
                fill=border,
            )
            draw.text(
                (left + 16, top + 8),
                label,
                fill="#FFFFFF",
                font=label_font,
            )
            with Image.open(source) as opened:
                page = _fit_page(opened)
            image_left = left + (PAIR_CELL_WIDTH - page.width) // 2
            image_top = top + PAIR_LABEL_HEIGHT + (PAIR_CELL_HEIGHT - page.height) // 2
            canvas.paste(page, (image_left, image_top))
            labels.append(
                {"kind": kind.lower(), "ordinal": ordinal, "label": label}
            )

    pair_root = packet_root / "pairs"
    pair_root.mkdir(exist_ok=True)
    suffix = (
        f"slide-{slide_ordinals[0]:02d}"
        if len(slide_ordinals) == 1
        else f"slides-{slide_ordinals[0]:02d}-{slide_ordinals[-1]:02d}"
    )
    target = pair_root / f"pair-{pair_index:02d}-{suffix}.png"
    canvas.save(target, format="PNG", compress_level=6)
    with Image.open(target) as verified:
        verified.verify()
    return {
        "pair_index": pair_index,
        "slide_ordinals": list(slide_ordinals),
        "path": target.relative_to(packet_root).as_posix(),
        "sha256": _sha256(target),
        "size_bytes": target.stat().st_size,
        "width_px": width,
        "height_px": height,
        "labels": labels,
    }


def _page_path_map(packet_root: Path, render: Mapping[str, Any]) -> dict[int, Path]:
    pages = render.get("pages")
    if not isinstance(pages, list):
        raise BlindPacketError("render record has no page list")
    result: dict[int, Path] = {}
    for record in pages:
        if not isinstance(record, dict):
            raise BlindPacketError("render page record is invalid")
        ordinal = record.get("ordinal")
        relative = record.get("path")
        if not isinstance(ordinal, int) or not isinstance(relative, str):
            raise BlindPacketError("render page record identity is invalid")
        if ordinal in result:
            raise BlindPacketError(f"duplicate render page record: {ordinal}")
        result[ordinal] = packet_root / relative
    return result


def _verify_success_coverage(
    *,
    expected_slide_count: int,
    reference: Mapping[str, Any],
    candidate: Mapping[str, Any],
    pairs: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    expected = list(range(1, expected_slide_count + 1))
    reference_ordinals = [item["ordinal"] for item in reference["pages"]]
    candidate_ordinals = [item["ordinal"] for item in candidate["pages"]]
    pair_ordinals = [
        ordinal for pair in pairs for ordinal in pair["slide_ordinals"]
    ]
    for label, observed in (
        ("reference", reference_ordinals),
        ("candidate", candidate_ordinals),
        ("pairs", pair_ordinals),
    ):
        if observed != expected:
            raise BlindPacketError(
                f"{label} coverage is duplicated, missing, or out of order"
            )
    if len(pairs) != 8:
        raise BlindPacketError("Phase 49 packet must contain exactly 8 pair images")
    return {
        "expected_slide_ordinals": expected,
        "reference_slide_ordinals": reference_ordinals,
        "candidate_slide_ordinals": candidate_ordinals,
        "pair_slide_ordinals": pair_ordinals,
        "missing_slide_ordinals": [],
        "duplicate_slide_ordinals": [],
        "status": "pass",
    }


def _input_record(
    path: Path,
    *,
    kind: str,
    expected_sha256: str | None = None,
    slide_count: int | None = None,
) -> dict[str, Any]:
    observed = _sha256(path)
    record: dict[str, Any] = {
        "kind": kind,
        "file_name": path.name,
        "observed_sha256": observed,
        "size_bytes": path.stat().st_size,
    }
    if expected_sha256 is not None:
        record["expected_sha256"] = expected_sha256
        record["hash_match"] = observed == expected_sha256
    if slide_count is not None:
        record["slide_count"] = slide_count
    return record


def build_phase49_blind_review_packet(
    *,
    reference_pptx: Path,
    candidate_pptx: Path,
    reference_sha256: str,
    candidate_sha256: str,
    physical_report: Path,
    rule_qa_report: Path,
    expected_slide_count: int,
    dpi: int,
    output_dir: Path,
    libreoffice_binary: Path | None = None,
    pdftoppm_binary: Path | None = None,
) -> dict[str, Any]:
    """Build one atomic, complete Phase 49 visual comparison packet."""

    if expected_slide_count != PHASE49_EXPECTED_SLIDE_COUNT:
        raise BlindPacketError("Phase 49 expected_slide_count must equal 15")
    if not 72 <= dpi <= 300:
        raise BlindPacketError("dpi must be between 72 and 300")
    reference = _require_regular_file(reference_pptx, "reference PPTX")
    candidate = _require_regular_file(candidate_pptx, "candidate PPTX")
    physical = _require_regular_file(physical_report, "physical report")
    rule_qa = _require_regular_file(rule_qa_report, "rule-QA report")
    reference_expected = _require_sha256(reference_sha256, "reference_sha256")
    candidate_expected = _require_sha256(candidate_sha256, "candidate_sha256")
    output = output_dir.expanduser().resolve(strict=False)
    if output.exists():
        raise BlindPacketError(f"output_dir must not already exist: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    reference_count = _pptx_slide_count(reference)
    candidate_count = _pptx_slide_count(candidate)
    if reference_count != expected_slide_count:
        raise BlindPacketError(
            f"reference PPTX has {reference_count} slides, expected {expected_slide_count}"
        )
    if candidate_count != expected_slide_count:
        raise BlindPacketError(
            f"candidate PPTX has {candidate_count} slides, expected {expected_slide_count}"
        )
    reference_input = _input_record(
        reference,
        kind="reference-pptx",
        expected_sha256=reference_expected,
        slide_count=reference_count,
    )
    candidate_input = _input_record(
        candidate,
        kind="candidate-pptx",
        expected_sha256=candidate_expected,
        slide_count=candidate_count,
    )
    if not reference_input["hash_match"]:
        raise BlindPacketError("reference PPTX SHA-256 does not match expected value")
    if not candidate_input["hash_match"]:
        raise BlindPacketError("candidate PPTX SHA-256 does not match expected value")

    physical_payload = _json_object(physical, "physical report")
    rule_qa_payload = _json_object(rule_qa, "rule-QA report")
    _validate_physical_report(
        physical_payload,
        candidate_sha256=candidate_expected,
        expected_slide_count=expected_slide_count,
    )
    _validate_rule_qa(
        rule_qa_payload,
        candidate_sha256=candidate_expected,
        candidate_size_bytes=candidate.stat().st_size,
        expected_slide_count=expected_slide_count,
    )
    physical_input = _input_record(physical, kind="physical-assembly-report")
    rule_qa_input = _input_record(rule_qa, kind="rule-qa-report")

    libreoffice_record = _tool_record(
        libreoffice_binary,
        "libreoffice",
        "soffice",
        version_args=("--version",),
    )
    pdftoppm_record = _tool_record(
        pdftoppm_binary,
        "pdftoppm",
        version_args=("-v",),
    )
    toolchain = {
        "libreoffice": libreoffice_record,
        "pdftoppm": pdftoppm_record,
        "pillow": {"version": PILLOW_VERSION},
    }

    with tempfile.TemporaryDirectory(
        prefix=f".{output.name}.staging-",
        dir=output.parent,
    ) as temporary:
        packet_root = Path(temporary) / "packet"
        packet_root.mkdir()
        work_root = Path(temporary) / "work"
        work_root.mkdir()
        inputs_root = packet_root / "inputs"
        inputs_root.mkdir()
        staged_physical = inputs_root / "physical-assembly-report.v1.json"
        staged_rule_qa = inputs_root / "rule-qa.v1.json"
        shutil.copyfile(physical, staged_physical)
        shutil.copyfile(rule_qa, staged_rule_qa)
        if _sha256(staged_physical) != physical_input["observed_sha256"]:
            raise BlindPacketError("physical report changed while it was staged")
        if _sha256(staged_rule_qa) != rule_qa_input["observed_sha256"]:
            raise BlindPacketError("rule-QA report changed while it was staged")
        physical_input["packet_path"] = staged_physical.relative_to(packet_root).as_posix()
        rule_qa_input["packet_path"] = staged_rule_qa.relative_to(packet_root).as_posix()

        reference_render = _render_deck(
            reference,
            label="reference",
            expected_sha256=reference_expected,
            expected_slide_count=expected_slide_count,
            dpi=dpi,
            libreoffice=Path(libreoffice_record["executable"]),
            pdftoppm=Path(pdftoppm_record["executable"]),
            packet_root=packet_root,
            work_root=work_root,
        )
        candidate_render = _render_deck(
            candidate,
            label="candidate",
            expected_sha256=candidate_expected,
            expected_slide_count=expected_slide_count,
            dpi=dpi,
            libreoffice=Path(libreoffice_record["executable"]),
            pdftoppm=Path(pdftoppm_record["executable"]),
            packet_root=packet_root,
            work_root=work_root,
        )
        reference_pages = _page_path_map(packet_root, reference_render)
        candidate_pages = _page_path_map(packet_root, candidate_render)
        pairs: list[dict[str, Any]] = []
        for pair_index, first_ordinal in enumerate(range(1, 16, 2), start=1):
            ordinals = tuple(
                range(first_ordinal, min(first_ordinal + 2, expected_slide_count + 1))
            )
            pairs.append(
                _write_pair_image(
                    packet_root=packet_root,
                    pair_index=pair_index,
                    slide_ordinals=ordinals,
                    reference_pages=reference_pages,
                    candidate_pages=candidate_pages,
                )
            )
        coverage = _verify_success_coverage(
            expected_slide_count=expected_slide_count,
            reference=reference_render,
            candidate=candidate_render,
            pairs=pairs,
        )

        if _sha256(reference) != reference_expected:
            raise BlindPacketError("reference PPTX changed during packet creation")
        if _sha256(candidate) != candidate_expected:
            raise BlindPacketError("candidate PPTX changed during packet creation")
        if _sha256(physical) != physical_input["observed_sha256"]:
            raise BlindPacketError("physical report changed during packet creation")
        if _sha256(rule_qa) != rule_qa_input["observed_sha256"]:
            raise BlindPacketError("rule-QA report changed during packet creation")

        identity_basis = {
            "reference_sha256": reference_expected,
            "candidate_sha256": candidate_expected,
            "physical_report_sha256": physical_input["observed_sha256"],
            "rule_qa_sha256": rule_qa_input["observed_sha256"],
            "dpi": dpi,
        }
        packet_id = f"phase49-blind-{_canonical_sha256(identity_basis)[:16]}"
        payload: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "packet_kind": PACKET_KIND,
            "packet_id": packet_id,
            "packet_sha256": "0" * 64,
            "status": "pass",
            "expected_slide_count": expected_slide_count,
            "dpi": dpi,
            "inputs": {
                "reference_pptx": reference_input,
                "candidate_pptx": candidate_input,
                "physical_report": physical_input,
                "rule_qa_report": rule_qa_input,
            },
            "toolchain": toolchain,
            "renders": {
                "reference": reference_render,
                "candidate": candidate_render,
            },
            "pairs": pairs,
            "coverage": coverage,
        }
        basis = dict(payload)
        basis.pop("packet_sha256")
        payload["packet_sha256"] = _canonical_sha256(basis)
        packet_path = packet_root / "packet.json"
        packet_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(packet_root, output)
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-pptx", type=Path, required=True)
    parser.add_argument("--candidate-pptx", type=Path, required=True)
    parser.add_argument("--reference-sha256", required=True)
    parser.add_argument("--candidate-sha256", required=True)
    parser.add_argument("--physical-report", type=Path, required=True)
    parser.add_argument("--rule-qa-report", type=Path, required=True)
    parser.add_argument("--expected-slide-count", type=int, required=True)
    parser.add_argument("--dpi", type=int, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--libreoffice", type=Path)
    parser.add_argument("--pdftoppm", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = build_phase49_blind_review_packet(
            reference_pptx=args.reference_pptx,
            candidate_pptx=args.candidate_pptx,
            reference_sha256=args.reference_sha256,
            candidate_sha256=args.candidate_sha256,
            physical_report=args.physical_report,
            rule_qa_report=args.rule_qa_report,
            expected_slide_count=args.expected_slide_count,
            dpi=args.dpi,
            output_dir=args.output_dir,
            libreoffice_binary=args.libreoffice,
            pdftoppm_binary=args.pdftoppm,
        )
    except BlindPacketError as exc:
        print(
            json.dumps(
                {"status": "fail", "error": str(exc)},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
