from __future__ import annotations

import importlib.util
import json
import sys
import zipfile
from pathlib import Path

from PIL import Image


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT
    / "skills"
    / "owned"
    / "pptx-studio"
    / "scripts"
    / "build_window_pptx_ai_blind_packet.py"
)
spec = importlib.util.spec_from_file_location("ai_blind_packet_builder", SCRIPT)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_packet_builder_stages_anonymous_verified_delivery(tmp_path: Path) -> None:
    source = tmp_path / "source"
    preview_dir = source / "proof"
    preview_dir.mkdir(parents=True)
    pptx = source / "delivery.pptx"
    with zipfile.ZipFile(pptx, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                '<Default Extension="xml" ContentType="application/xml"/>'
                "</Types>"
            ),
        )
        archive.writestr(
            "_rels/.rels",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'
            ),
        )
        archive.writestr(
            "ppt/presentation.xml",
            (
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>'
            ),
        )
    Image.new("RGB", (64, 36), "#102A36").save(
        preview_dir / "slide-001.png"
    )
    manifest = tmp_path / "candidates.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "benchmark_id": "test-benchmark",
                "candidates": [
                    {
                        "candidate_id": "visible-only-in-private-map",
                        "scenario_id": "business-report",
                        "pptx_path": str(pptx),
                        "preview_dir": str(preview_dir),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    packet = module.build_packet(manifest, tmp_path / "packet")

    assert packet.delivery_evidence_ready
    assert packet.entries[0].blind_id.startswith("B-001-")
    public = (tmp_path / "packet" / "packet.json").read_text(encoding="utf-8")
    private = (
        tmp_path / "packet" / "private-candidate-map.json"
    ).read_text(encoding="utf-8")
    assert "visible-only-in-private-map" not in public
    assert "visible-only-in-private-map" in private


def test_calibration_reference_is_a_bounded_real_png(tmp_path: Path) -> None:
    source = tmp_path / "reference.jpg"
    Image.new("RGB", (2400, 1200), "#123456").save(source, quality=95)
    destination = tmp_path / "calibration-reference.png"

    module._stage_calibration_reference(source, destination)

    assert destination.stat().st_size < 8 * 1024 * 1024
    with Image.open(destination) as image:
        assert image.format == "PNG"
        assert image.width <= 1920
        assert image.height <= 1920
