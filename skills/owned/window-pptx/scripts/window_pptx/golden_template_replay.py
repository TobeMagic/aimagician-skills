"""One-command, hash-bound golden replay for a trusted TemplatePack."""

from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from .layouts import SlideSize
from .libreoffice import LibreOfficeVerificationResult, LibreOfficeVerifier
from .reference_quality import assess_reference_grade_quality
from .template_geometry import VisualMask
from .template_pack import (
    TemplatePackError,
    adapt_template_pack,
    load_template_bindings,
    load_template_pack,
    sha256_file,
)
from .visual_similarity import VisualSimilarityReport, compare_masked_previews


PML = "http://schemas.openxmlformats.org/presentationml/2006/main"
EMU_PER_INCH = 914_400


class GoldenReplayError(RuntimeError):
    """A golden replay gate did not pass."""


def _canonical_json_hash(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _slide_size(template_path: Path) -> SlideSize:
    with zipfile.ZipFile(template_path) as archive:
        root = ET.fromstring(archive.read("ppt/presentation.xml"))
    node = root.find(f"{{{PML}}}sldSz")
    try:
        width = int(node.get("cx")) / EMU_PER_INCH if node is not None else 0
        height = int(node.get("cy")) / EMU_PER_INCH if node is not None else 0
    except (TypeError, ValueError) as exc:
        raise GoldenReplayError("source slide size is invalid") from exc
    if width <= 0 or height <= 0:
        raise GoldenReplayError("source slide size is invalid")
    return SlideSize(width=width, height=height)


def _renderer_fingerprint(
    result: LibreOfficeVerificationResult,
    *,
    dpi: int,
) -> str:
    return (
        f"libreoffice={result.engine_version}|"
        f"rasterizer={result.poppler_version}|dpi={dpi}"
    )


@dataclass(frozen=True)
class GoldenReplayResult:
    output_dir: Path
    candidate_path: Path
    manifest_path: Path
    candidate_sha256: str
    manifest: dict[str, Any]
    similarity: VisualSimilarityReport


def run_golden_template_replay(
    template_pack: str | Path,
    bindings_path: str | Path,
    output_dir: str | Path,
    *,
    verifier: LibreOfficeVerifier | None = None,
) -> GoldenReplayResult:
    """Adapt, render, inspect, compare, and record one portable golden replay."""

    pack = load_template_pack(template_pack)
    if not pack.visual_masks:
        raise GoldenReplayError("TemplatePack has no trusted visual_masks")
    binding_pack_id, bindings = load_template_bindings(bindings_path)
    if binding_pack_id != pack.id:
        raise TemplatePackError(
            f"binding pack {binding_pack_id!r} does not match {pack.id!r}"
        )
    root = Path(output_dir).resolve()
    root.mkdir(parents=True, exist_ok=True)
    candidate_path = root / "candidate.pptx"
    adaptation = adapt_template_pack(pack, bindings, candidate_path)
    renderer = verifier or LibreOfficeVerifier()
    slide_size = _slide_size(pack.template_path)
    source_proof = renderer.verify(
        pack.template_path,
        artifact_dir=root / "proof" / "source",
        expected_slide_count=pack.slide_count,
        slide_size=slide_size,
    )
    candidate_proof = renderer.verify(
        candidate_path,
        artifact_dir=root / "proof" / "candidate",
        expected_slide_count=pack.slide_count,
        slide_size=slide_size,
    )
    source_fingerprint = _renderer_fingerprint(source_proof, dpi=renderer.dpi)
    candidate_fingerprint = _renderer_fingerprint(candidate_proof, dpi=renderer.dpi)
    masks = tuple(
        VisualMask(
            slide=mask.slide,
            target_kind=mask.target_kind,
            target_id=mask.target_id,
            x=mask.x,
            y=mask.y,
            width=mask.width,
            height=mask.height,
            padding=mask.padding,
        )
        for mask in pack.visual_masks
    )
    similarity = compare_masked_previews(
        source_proof.png_paths,
        candidate_proof.png_paths,
        masks,
        source_renderer_fingerprint=source_fingerprint,
        candidate_renderer_fingerprint=candidate_fingerprint,
    )
    similarity.write_json(root / "visual-similarity-report.json")
    if not similarity.passed:
        raise GoldenReplayError("masked non-slot rendered similarity gate failed")
    reference_quality = assess_reference_grade_quality(
        candidate_path,
        png_paths=candidate_proof.png_paths,
        expected_slide_count=pack.slide_count,
    )
    if not reference_quality.passed:
        raise GoldenReplayError("reference-grade structural/preview quality gate failed")
    candidate_sha256 = sha256_file(candidate_path)
    if (
        candidate_sha256 != adaptation.output_sha256
        or candidate_sha256 != candidate_proof.candidate_hash_before
        or candidate_sha256 != candidate_proof.candidate_hash_after
    ):
        raise GoldenReplayError("candidate hash is unstable across replay gates")
    manifest: dict[str, Any] = {
        "schema_version": "1.0",
        "template_pack_id": pack.id,
        "source_sha256": pack.template_sha256,
        "bindings_sha256": _canonical_json_hash(
            {
                "schema_version": "1.0",
                "template_pack_id": binding_pack_id,
                "bindings": bindings,
            }
        ),
        "candidate_sha256": candidate_sha256,
        "slide_count": pack.slide_count,
        "changed_parts": list(adaptation.changed_parts),
        "changed_slot_count": len(adaptation.slot_changes),
        "source_integrity_preserved": adaptation.source_integrity_preserved,
        "renderer_fingerprint": candidate_fingerprint,
        "reference_quality": {
            "passed": reference_quality.passed,
            "average_objects_per_slide": (
                reference_quality.complexity.average_objects_per_slide
            ),
            "layout_signature_count": (
                reference_quality.complexity.layout_signature_count
            ),
            "chart_count": reference_quality.complexity.chart_count,
            "media_count": reference_quality.complexity.media_count,
        },
        "visual_similarity": similarity.to_dict(),
        "artifacts": {
            "candidate": "candidate.pptx",
            "similarity_report": "visual-similarity-report.json",
            "source_proof_dir": "proof/source",
            "candidate_proof_dir": "proof/candidate",
        },
        "passed": True,
    }
    manifest_path = root / "golden-replay-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return GoldenReplayResult(
        output_dir=root,
        candidate_path=candidate_path,
        manifest_path=manifest_path,
        candidate_sha256=candidate_sha256,
        manifest=manifest,
        similarity=similarity,
    )
