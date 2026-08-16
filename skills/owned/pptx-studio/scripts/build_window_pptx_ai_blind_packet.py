#!/usr/bin/env python3
"""Stage an anonymous, hash-bound AI blind-review packet from deliveries."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from window_pptx.ai_blind_review import AI_BLIND_RUBRIC  # noqa: E402
from window_pptx.benchmark import (  # noqa: E402
    BENCHMARK_SCHEMA_VERSION,
    BlindReviewArtifact,
    BlindReviewEntry,
    BlindReviewPacket,
    canonical_sha256,
    load_blind_review_packet,
)
from window_pptx.evidence import write_contact_sheet  # noqa: E402


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _candidate(value: Any, index: int) -> dict[str, str]:
    if not isinstance(value, dict) or set(value) != {
        "candidate_id",
        "scenario_id",
        "pptx_path",
        "preview_dir",
    }:
        raise ValueError(f"candidates[{index}] keys mismatch")
    result: dict[str, str] = {}
    for key, item in value.items():
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"candidates[{index}].{key} must be non-empty")
        result[key] = item
    return result


def _stage_calibration_reference(source: Path, destination: Path) -> None:
    """Materialize a real, bounded PNG from an image or reference PPTX."""

    suffix = source.suffix.casefold()
    if suffix == ".pptx":
        soffice = shutil.which("libreoffice") or shutil.which("soffice")
        pdftoppm = shutil.which("pdftoppm")
        if soffice is None or pdftoppm is None:
            raise ValueError(
                "PPTX calibration requires LibreOffice and pdftoppm"
            )
        with tempfile.TemporaryDirectory(prefix="pptx-studio-calibration-") as raw:
            work = Path(raw)
            converted = subprocess.run(
                [
                    soffice,
                    "--headless",
                    "--convert-to",
                    "pdf",
                    "--outdir",
                    str(work),
                    str(source),
                ],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
            pdf = work / f"{source.stem}.pdf"
            if converted.returncode != 0 or not pdf.is_file():
                raise ValueError("calibration PPTX could not be rendered")
            rasterized = subprocess.run(
                [pdftoppm, "-png", "-r", "96", str(pdf), str(work / "slide")],
                check=False,
                capture_output=True,
                text=True,
                timeout=120,
            )
            pages = tuple(sorted(work.glob("slide-*.png")))
            if rasterized.returncode != 0 or not pages:
                raise ValueError("calibration PPTX pages could not be rasterized")
            proof = work / "portable-proof"
            proof.mkdir()
            staged_pages = []
            for index, page in enumerate(pages, start=1):
                staged = proof / f"slide-{index:03d}.png"
                shutil.copy2(page, staged)
                staged_pages.append(staged)
            write_contact_sheet(tuple(staged_pages), destination)
    elif suffix in {".png", ".jpg", ".jpeg"}:
        with Image.open(source) as opened:
            image = opened.convert("RGB")
            image.thumbnail((1920, 1920), Image.Resampling.LANCZOS)
            image.save(destination, format="PNG", optimize=True)
    else:
        raise ValueError("calibration reference must be PNG, JPEG, or PPTX")

    with Image.open(destination) as verified:
        verified.verify()
    if destination.stat().st_size > 8 * 1024 * 1024:
        raise ValueError("calibration reference exceeds the 8 MiB review limit")


def build_packet(
    manifest_path: Path,
    output_dir: Path,
    *,
    calibration_reference: Path | None = None,
) -> BlindReviewPacket:
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) != {
        "schema_version",
        "benchmark_id",
        "candidates",
    }:
        raise ValueError("candidate manifest keys mismatch")
    if raw["schema_version"] != BENCHMARK_SCHEMA_VERSION:
        raise ValueError("candidate manifest schema_version must equal 1.0")
    benchmark_id = raw["benchmark_id"]
    if not isinstance(benchmark_id, str) or not benchmark_id.strip():
        raise ValueError("candidate manifest benchmark_id must be non-empty")
    values = raw["candidates"]
    if not isinstance(values, list) or not values:
        raise ValueError("candidate manifest candidates must be non-empty")
    candidates = [_candidate(value, index) for index, value in enumerate(values)]
    if len({item["candidate_id"] for item in candidates}) != len(candidates):
        raise ValueError("candidate_id values must be unique")

    output_dir.mkdir(parents=True, exist_ok=True)
    entries: list[BlindReviewEntry] = []
    private_map: dict[str, str] = {}
    ordered = sorted(
        candidates,
        key=lambda item: canonical_sha256(
            {
                "candidate_id": item["candidate_id"],
                "scenario_id": item["scenario_id"],
            }
        ),
    )
    for index, candidate in enumerate(ordered, start=1):
        pptx = Path(candidate["pptx_path"]).resolve()
        preview_dir = Path(candidate["preview_dir"]).resolve()
        previews = sorted(preview_dir.glob("slide-*.png"))
        if not pptx.is_file() or not previews:
            raise ValueError(
                f"candidate {candidate['candidate_id']} lacks PPTX or previews"
            )
        source_basis = {
            "candidate_sha256": _sha256(pptx),
            "preview_sha256s": [_sha256(path) for path in previews],
            "scenario_id": candidate["scenario_id"],
        }
        evidence_sha256 = canonical_sha256(source_basis)
        blind_id = f"B-{index:03d}-{evidence_sha256[:8]}"
        target_dir = output_dir / blind_id
        target_dir.mkdir(parents=True, exist_ok=True)
        staged_pptx = target_dir / "delivery.pptx"
        shutil.copy2(pptx, staged_pptx)
        artifacts = [
            BlindReviewArtifact(
                kind="editable-pptx",
                review_path=f"{blind_id}/delivery.pptx",
                sha256=_sha256(staged_pptx),
                size_bytes=staged_pptx.stat().st_size,
            )
        ]
        for preview_index, source in enumerate(previews, start=1):
            target = target_dir / f"slide-{preview_index:03d}.png"
            shutil.copy2(source, target)
            artifacts.append(
                BlindReviewArtifact(
                    kind="slide-preview",
                    review_path=f"{blind_id}/{target.name}",
                    sha256=_sha256(target),
                    size_bytes=target.stat().st_size,
                )
            )
        entries.append(
            BlindReviewEntry(
                blind_id=blind_id,
                scenario_id=candidate["scenario_id"],
                evidence_sha256=evidence_sha256,
                rubric=AI_BLIND_RUBRIC,
                artifacts=tuple(artifacts),
            )
        )
        private_map[blind_id] = candidate["candidate_id"]

    basis = {
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "benchmark_id": benchmark_id,
        "delivery_evidence_ready": True,
        "entries": [entry.to_dict() for entry in entries],
    }
    packet = BlindReviewPacket(
        schema_version=BENCHMARK_SCHEMA_VERSION,
        benchmark_id=benchmark_id,
        packet_sha256=canonical_sha256(basis),
        delivery_evidence_ready=True,
        entries=tuple(entries),
    )
    _atomic_json(output_dir / "packet.json", packet.to_dict())
    _atomic_json(
        output_dir / "private-candidate-map.json",
        {
            "schema_version": BENCHMARK_SCHEMA_VERSION,
            "packet_sha256": packet.packet_sha256,
            "mapping": private_map,
        },
    )
    if calibration_reference is not None:
        reference = calibration_reference.resolve()
        if not reference.is_file():
            raise ValueError("calibration reference is missing")
        _stage_calibration_reference(
            reference,
            output_dir / "calibration-reference.png",
        )
    load_blind_review_packet(packet.to_dict(), review_root=output_dir)
    return packet


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--calibration-reference", type=Path)
    args = parser.parse_args(argv)
    packet = build_packet(
        args.candidate_manifest.resolve(),
        args.output_dir.resolve(),
        calibration_reference=args.calibration_reference,
    )
    print(json.dumps(packet.to_dict(), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
