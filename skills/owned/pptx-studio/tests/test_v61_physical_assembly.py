"""Focused smoke tests for the v6.1 physical-template route.

The commercial template bytes are intentionally not fixtures.  When the local
private library is present these tests exercise its compiled metadata; in a
clean checkout they still verify the public CLI contract without requiring
private assets.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = SKILL_ROOT / ".private"
LIBRARY_PATH = PRIVATE_ROOT / "v61" / "library-v4.json"
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from window_pptx.cli import collect_requested_actions, parse_args  # noqa: E402
from window_pptx.page_template_library import (  # noqa: E402
    load_library_index,
    query_page_templates,
)
from window_pptx.physical_assembly import _default_pres_xml, _pres_xml_rels  # noqa: E402
from window_pptx.physical_rule_qa import run_physical_rule_qa  # noqa: E402

REFERENCE_PLAN = Path("/home/aimagician/tmp/pptx-studio-work-report-clean-v3/.pptx-studio/audits/reference-assembly-plan.json")
REFERENCE_OUTPUT = Path("/home/aimagician/tmp/pptx-studio-work-report-clean-v3/output/reference-final-approved.pptx")
REFERENCE_LIBRARY = SKILL_ROOT / ".private" / "v61" / "reference-library-v1.json"


def test_assembly_route_is_explicit_and_dry_run_safe() -> None:
    args = parse_args(
        [
            "--project-dir",
            "/tmp/client",
            "--render-assembly-plan",
            "--assembly-plan",
            "audits/assembly-plan.json",
            "--output",
            "output/final.pptx",
            "--dry-run",
        ]
    )
    assert args.render_assembly_plan is True
    assert collect_requested_actions(args) == ["render_assembly_plan"]


def test_presentation_package_declares_size_and_master_relationships() -> None:
    presentation = _default_pres_xml(
        ["slides/slide1.xml"],
        ["slideMasters/slideMaster1.xml"],
    ).decode("utf-8")
    relationships = _pres_xml_rels(
        ["slides/slide1.xml"],
        ["slideMasters/slideMaster1.xml"],
    ).decode("utf-8")
    assert 'cx="12192000" cy="6858000"' in presentation
    assert 'r:id="rId1"' in presentation
    assert 'Target="slideMasters/slideMaster1.xml"' in relationships


@pytest.mark.skipif(not LIBRARY_PATH.is_file(), reason="private template library is not installed")
def test_compiled_library_has_unique_certified_pages_and_query_is_deterministic() -> None:
    index = load_library_index(LIBRARY_PATH)
    assert index.page_template_count == len(index.page_templates)
    assert len({template.page_id for template in index.page_templates}) == index.page_template_count
    assert all(template.certification in {"certified", "certified-private"} for template in index.page_templates)

    first = query_page_templates(index, role="cover", style_cluster=index.dominant_style_cluster_id, limit=5)
    second = query_page_templates(index, role="cover", style_cluster=index.dominant_style_cluster_id, limit=5)
    assert [item.page_id for item in first] == [item.page_id for item in second]
    assert first


@pytest.mark.skipif(not LIBRARY_PATH.is_file(), reason="private template library is not installed")
def test_query_keeps_reference_only_exact_roles_out_of_direct_use() -> None:
    index = load_library_index(LIBRARY_PATH)
    reference_data = next(
        template
        for template in index.page_templates
        if template.page_role == "data"
    )
    assert reference_data.direct_use is False
    assert query_page_templates(
        index,
        role="data",
        style_cluster=reference_data.style_cluster_id,
        limit=10,
    ) == ()
    review_only = query_page_templates(
        index,
        role="data",
        style_cluster=reference_data.style_cluster_id,
        limit=10,
        direct_use_only=False,
    )
    assert review_only
    assert all(item.page_role == "data" for item in review_only)


@pytest.mark.skipif(not LIBRARY_PATH.is_file(), reason="private template library is not installed")
def test_library_slot_graph_uses_actual_shape_ids() -> None:
    index = load_library_index(LIBRARY_PATH)
    for template in index.page_templates[:25]:
        slot_ids = template.slot_graph.get("text_slot_ids", [])
        assert template.slot_graph.get("text_slot_count") == len(slot_ids)
        assert all(slot.startswith("shape_") for slot in slot_ids)


@pytest.mark.skipif(
    not (REFERENCE_PLAN.is_file() and REFERENCE_OUTPUT.is_file() and REFERENCE_LIBRARY.is_file()),
    reason="local reference acceptance artifacts are not installed",
)
def test_reference_acceptance_passes_deterministic_rule_qa() -> None:
    index = load_library_index(REFERENCE_LIBRARY)
    from window_pptx.physical_assembly import load_assembly_plan

    plan = load_assembly_plan(REFERENCE_PLAN, {item.page_id: item for item in index.page_templates})
    report = run_physical_rule_qa(REFERENCE_OUTPUT, plan=plan)
    assert report.status == "pass"
    assert not report.blocking_findings
