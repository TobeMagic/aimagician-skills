from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "skills" / "owned" / "pptx-studio" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

from pptx_studio.regions import extract_regions  # noqa: E402


def test_extract_regions_is_stable_and_excludes_image_only() -> None:
    page = {
        "page_id": "page_aaaaaaaaaaaaaaaaaaaaaaaa_001",
        "editability": "native_editable",
        "component_eligible": True,
        "shapes": [
            {"shape_id": "2", "kind": "text", "text": "Title", "bbox": {"x": 8, "y": 8, "w": 50, "h": 12}, "max_chars": 24},
            {"shape_id": "3", "kind": "text", "text": "Body", "bbox": {"x": 8, "y": 28, "w": 52, "h": 35}, "max_chars": 120},
        ],
    }
    first = extract_regions(page)
    second = extract_regions(page)

    assert first == second
    assert [item["region_kind"] for item in first] == ["title", "content-block"]
    assert first[0]["editable_shape_ids"] == ["2"]
    assert first[1]["capacity"]["max_text_chars"] == 120

    assert extract_regions({**page, "editability": "image_only", "component_eligible": False}) == []
