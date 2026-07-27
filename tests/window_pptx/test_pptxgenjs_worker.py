from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_ROOT = REPO_ROOT / "skills" / "owned" / "window-pptx"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from window_pptx.layouts import SlideSize  # noqa: E402
from window_pptx.portable_renderer import (  # noqa: E402
    PortableRenderError,
    PptxGenJSRenderer,
)
from window_pptx.render_plan import build_render_plan  # noqa: E402


def _plan(*, motion: str = "off"):
    return build_render_plan(
        {
            "schema_version": "1.0",
            "project": {
                "title": "Worker protocol",
                "scenario": "business-report",
                "audience": "executive",
                "language": "zh-CN",
            },
            "preferences": {"density": "balanced", "motion": motion},
            "slides": [
                {
                    "id": "summary",
                    "role": "summary",
                    "title": "摘要",
                    "blocks": [
                        {
                            "id": "summary-copy",
                            "kind": "statement",
                            "text": "便携式后端必须拒绝未治理字段。",
                        }
                    ],
                }
            ],
        },
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )


def _rich_plan():
    return build_render_plan(
        {
            "schema_version": "1.0",
            "project": {
                "title": "Metric hierarchy",
                "scenario": "business-report",
                "audience": "executive",
                "language": "en-US",
            },
            "preferences": {"density": "balanced", "motion": "off"},
            "slides": [
                {
                    "id": "metric",
                    "role": "performance",
                    "title": "Revenue reached 48.2 million dollars.",
                    "blocks": [
                        {
                            "id": "metric-value",
                            "kind": "metrics",
                            "items": [
                                {
                                    "label": "Revenue",
                                    "value": 48.2,
                                    "unit": "million dollars",
                                }
                            ],
                        }
                    ],
                }
            ],
        },
        slide_size=SlideSize(13.333, 7.5),
        installed_fonts={"Arial"},
    )


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_worker_rejects_unknown_request_data_without_writing(tmp_path: Path) -> None:
    output = tmp_path / "must-not-exist.pptx"
    request = {
        "protocol_version": "1.0",
        "output_path": str(output),
        "render_plan": _plan().to_dict(),
        "unexpected": "not governed",
    }
    worker = SKILL_ROOT / "scripts" / "node" / "window_pptx_worker.mjs"

    completed = subprocess.run(
        [shutil.which("node"), str(worker)],
        input=json.dumps(request, ensure_ascii=False),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        shell=False,
    )

    assert completed.returncode != 0
    assert "unknown fields" in completed.stderr
    assert not output.exists()


@pytest.mark.skipif(shutil.which("node") is None, reason="Node.js is required")
def test_worker_rejects_forged_rich_text_without_writing(tmp_path: Path) -> None:
    output = tmp_path / "must-not-exist.pptx"
    render_plan = _rich_plan().to_dict()
    rich_object = next(
        item
        for slide in render_plan["slides"]
        for item in slide["objects"]
        if "text_runs" in item
    )
    rich_object["text_runs"][0]["bold"] = "false"
    request = {
        "protocol_version": "1.0",
        "output_path": str(output),
        "render_plan": render_plan,
    }
    worker = SKILL_ROOT / "scripts" / "node" / "window_pptx_worker.mjs"

    completed = subprocess.run(
        [shutil.which("node"), str(worker)],
        input=json.dumps(request),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        shell=False,
    )

    assert completed.returncode != 0
    assert "style flags must be boolean" in completed.stderr
    assert not output.exists()


def test_python_adapter_rejects_non_pptx_and_motion_before_render(
    tmp_path: Path,
) -> None:
    renderer = PptxGenJSRenderer(skill_root=SKILL_ROOT)

    with pytest.raises(PortableRenderError, match="must end in .pptx"):
        renderer.render(_plan(), tmp_path / "deck.pdf")
    with pytest.raises(PortableRenderError, match="does not support shape motion"):
        renderer.render(_plan(motion="subtle-fade"), tmp_path / "deck.pptx")

    assert not tuple(tmp_path.iterdir())


def test_python_adapter_rejects_worker_version_drift(tmp_path: Path) -> None:
    output = (tmp_path / "deck.pptx").resolve()
    payload = {
        "protocol_version": "1.0",
        "ok": True,
        "backend_id": "pptxgenjs",
        "backend_version": "4.0.2",
        "output_path": str(output),
        "slide_count": 1,
        "planned_object_count": 1,
        "native_editable_count": 1,
        "diagram_child_count": 0,
        "object_names": ["shape"],
        "group_names": [],
        "warnings": [],
    }

    with pytest.raises(PortableRenderError, match="version drifted"):
        PptxGenJSRenderer._parse_result(payload, output)
