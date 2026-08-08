"""Attack regressions for independent physical-report security contracts."""

from __future__ import annotations

import copy
import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path
from typing import Any

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from window_pptx.independent_validation_security import (  # noqa: E402
    audit_output_media_authority,
    audit_output_text_coverage,
    audit_zip_entries,
    validate_external_relationship,
    validate_fact_evidence_value,
    validate_fragment_group_fact_authority,
    validate_query_bundle_and_coverage,
)


SHA = "a" * 64
PAGE_ID = f"{SHA}:001"
TEXT_SLOT = "shape_2"
PEER_ID = "peer_" + "b" * 24
CHART_SLOT = "chart_value_" + "c" * 24
WORKBOOK_SLOT = "workbook_cell_" + "d" * 24
TABLE_SLOT = "table_cell_" + "1" * 24


def _hashed(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _governed_slot(
    *,
    slot_id: str,
    kind: str,
    source_part: str,
    locator: str,
    value: str,
) -> dict[str, Any]:
    return {
        "slot_id": slot_id,
        "kind": kind,
        "source_part": source_part,
        "locator": locator,
        "source_text": value,
        "source_text_sha256": _hashed(value.encode()),
        "peer_group_id": PEER_ID,
        "semantic_role": "value",
        "series_index": 0,
        "point_index": 0,
        "worksheet_ordinal": 0 if kind == "workbook-cell" else None,
        "cell_ref": "A1" if kind == "workbook-cell" else None,
        "value_type": "number",
    }


def _page_template(
    *,
    governed: bool = False,
    media: tuple[tuple[str, bytes], ...] = (),
    media_policy: str = "no-page-media",
) -> dict[str, Any]:
    source_text = "Title"
    text_slot = {
        "slot_id": TEXT_SLOT,
        "shape_id": 2,
        "kind": "text",
        "semantic_role": "title",
        "region": "top-left",
        "reading_order": 1,
        "bbox": {"x": 10, "y": 10, "w": 500, "h": 100},
        "max_chars": 40,
        "source_char_count": len(source_text),
        "source_line_count": 1,
        "source_run_count": 1,
        "source_text_sha256": _hashed(source_text.encode()),
        "source_text": source_text,
        "group_id": None,
        "group_order": None,
        "font_size_pt": 28,
        "allowed_binding_modes": ["fact"],
    }
    governed_slots: list[dict[str, Any]] = []
    if governed:
        governed_slots = [
            _governed_slot(
                slot_id=CHART_SLOT,
                kind="chart-value",
                source_part="ppt/charts/chart1.xml",
                locator=(
                    "chartFrame[id=3]/chartSpace[1]/chart[1]/plotArea[1]/"
                    "barChart[1]/ser[1]/val[1]/numRef[1]/numCache[1]/pt[1]/v[1]"
                ),
                value="42",
            ),
            _governed_slot(
                slot_id=WORKBOOK_SLOT,
                kind="workbook-cell",
                source_part="ppt/embeddings/book.xlsx",
                locator="chartFrame[id=3]/xl/worksheets/sheet1.xml!A1",
                value="42",
            ),
        ]
    media_parts = [
        {
            "source_part": source_part,
            "sha256": _hashed(payload),
            "size_bytes": len(payload),
        }
        for source_part, payload in media
    ]
    image_count = len(media)
    return {
        "schema_version": "1.0",
        "page_id": PAGE_ID,
        "package_sha256": SHA,
        "slide_number": 1,
        "source_path": "/private/certified/source.pptx",
        "source_sha256": SHA,
        "source_slide_sha256": "e" * 64,
        "page_role": "body",
        "category_names": ["test"],
        "style_cluster_id": "test-style",
        "deck_family_id": "test-family",
        "theme_palette": ["#101010", "#FFFFFF", "#00AAFF"],
        "capacity": {"max_text_chars": 40, "max_text_runs": 1},
        "editability": "native_editable",
        "certification": "certified",
        "visual_quality": 1,
        "structure": {
            "slide_count": 1,
            "shape_count": 2,
            "layout_count": 1,
            "master_count": 1,
            "theme_count": 1,
            "media_count": image_count,
            "chart_count": 1 if governed else 0,
            "table_count": 0,
            "page_shape_count": 2,
            "slide_relationship_count": image_count,
            "linked_style_part_count": 0,
            "page_image_count": image_count,
            "page_media_count": image_count,
            "page_chart_count": 1 if governed else 0,
            "page_table_count": 0,
            "page_native_object_count": 2,
            "fonts": ["Arial"],
        },
        "slot_graph": {
            "text_slot_ids": [TEXT_SLOT],
            "text_slot_count": 1,
            "reading_order": [TEXT_SLOT],
            "fragment_groups": [],
            "slots": [text_slot],
        },
        "governed_content_inventory": {
            "schema_version": "governed-content-inventory.v1",
            "peer_mapping_method": "chart-formula-range-v1",
            "policy": "locked-authority-required" if governed else "no-embedded-content",
            "complete": True,
            "content_slot_count": len(governed_slots),
            "customer_data_slot_count": len(governed_slots),
            "slots": governed_slots,
            "closure_metadata": {
                "table_count": 0,
                "chart_part_count": 1 if governed else 0,
                "workbook_part_count": 1 if governed else 0,
                "notes_part_count": 0,
                "comment_part_count": 0,
                "diagram_part_count": 0,
                "layout_master_field_count": 0,
                "layout_master_fields": [],
                "tag_part_count": 0,
                "tag_parts": [],
                "media_count": len(media_parts),
                "media_parts": media_parts,
            },
            "scan_errors": [],
        },
        "requires_customer_asset": media_policy == "customer-replacement-required",
        "media_retention_policy": media_policy,
        "pool": "certified-core",
        "decision": "direct-use",
        "direct_use": True,
        "eligibility_known": True,
        "style_features": {
            "tone": "light",
            "average_luminance": 220,
            "average_chroma": 40,
            "accent_family": "blue",
            "visual_mode": "editorial",
            "density": "balanced",
            "density_score": 50,
        },
    }


def _candidate(template: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "page_id": PAGE_ID,
        "eligibility": True,
        "reasons": [],
        "fallback_reason": None,
        "asset_fit": 1,
        "capacity_fit": True,
        "residue_risk": 0,
        "style_compatibility": "exact",
        "scores": {
            "role": 1,
            "capacity": 1,
            "semantic": 1,
            "style": 1,
            "editability": 1,
            "total": 1,
        },
        "weights": {
            "role": 0.3,
            "capacity": 0.25,
            "semantic": 0.2,
            "style": 0.15,
            "editability": 0.1,
        },
        "page_template": template,
    }


def _bundle(template: dict[str, Any]) -> dict[str, Any]:
    candidate = _candidate(template)
    return {
        "schema_version": "page-template-query-bundle.v1",
        "request_sha256": "f" * 64,
        "library_index_sha256": "9" * 64,
        "library_resolution_source": "explicit-private-root",
        "query_count": 1,
        "queries": [
            {
                "target_ordinal": 1,
                "query_id": "query-001",
                "result": {
                    "schema_version": "page-template-query-result.v1",
                    "library_index_sha256": "9" * 64,
                    "library_resolution_source": "explicit-private-root",
                    "role": "body",
                    "capacity_budget": 40,
                    "semantic_categories": ["test"],
                    "style_cluster": "test-style",
                    "asset_requirements": [],
                    "customer_assets_available": True,
                    "limit": 3,
                    "allow_fallback": False,
                    "direct_use_only": True,
                    "include_ineligible": False,
                    "weights": candidate["weights"],
                    "count": 1,
                    "eligible_count": 1,
                    "candidates": [candidate],
                },
            }
        ],
    }


def _lineage() -> list[dict[str, Any]]:
    return [{"ordinal": 1, "page_id": PAGE_ID}]


def _text_evidence() -> dict[str, Any]:
    return {
        "ordinal": 1,
        "page_id": PAGE_ID,
        "slot_id": TEXT_SLOT,
        "shape_id": 2,
        "binding_kind": "text",
    }


def _fragment_page_template() -> dict[str, Any]:
    template = _page_template()
    slot_ids = ("shape_2", "shape_3", "shape_4")
    source_texts = ("X", "Y", "Z")
    slots = []
    for index, (slot_id, source_text) in enumerate(
        zip(slot_ids, source_texts),
        1,
    ):
        slots.append(
            {
                "slot_id": slot_id,
                "shape_id": index + 1,
                "kind": "title_fragment",
                "semantic_role": "title_fragment",
                "region": "top-left",
                "reading_order": index,
                "bbox": {"x": index * 100, "y": 10, "w": 80, "h": 100},
                "max_chars": 1,
                "source_char_count": 1,
                "source_line_count": 1,
                "source_run_count": 1,
                "source_text_sha256": _hashed(source_text.encode()),
                "source_text": source_text,
                "group_id": "fragment_01",
                "group_order": index,
                "font_size_pt": 28,
                "allowed_binding_modes": ["character", "clear"],
            }
        )
    template["slot_graph"] = {
        "text_slot_ids": list(slot_ids),
        "text_slot_count": len(slot_ids),
        "reading_order": list(slot_ids),
        # Deliberately not group-order order: the slot contracts are the
        # independent ordering authority.
        "fragment_groups": [
            {
                "group_id": "fragment_01",
                "slot_ids": [slot_ids[2], slot_ids[0], slot_ids[1]],
            }
        ],
        "slots": slots,
    }
    template["capacity"] = {"max_text_chars": 3, "max_text_runs": 3}
    return template


def _fragment_evidence(
    slot_id: str,
    shape_id: int,
    text: str,
    *,
    fact_ref: str | None = "fact-title",
) -> dict[str, Any]:
    is_empty = text == ""
    return {
        "ordinal": 1,
        "page_id": PAGE_ID,
        "slot_id": slot_id,
        "shape_id": shape_id,
        "binding_kind": "text",
        "mode": "connective" if is_empty else "character",
        "replacement_sha256": _hashed(text.encode()),
        "fact_refs": [] if is_empty or fact_ref is None else [fact_ref],
        "asset_refs": [],
        "connective_ref": "connective-clear" if is_empty else "",
    }


def _embedded_evidence(slot_id: str) -> dict[str, Any]:
    return {
        "ordinal": 1,
        "page_id": PAGE_ID,
        "slot_id": slot_id,
        "shape_id": 3,
        "binding_kind": "embedded",
    }


def _mutation(slot: dict[str, Any]) -> dict[str, Any]:
    return {
        "ordinal": 1,
        "page_id": PAGE_ID,
        "slot_id": slot["slot_id"],
        "kind": slot["kind"],
        "source_part": slot["source_part"],
        "shape_id": int(slot["locator"].split("[id=", 1)[1].split("]", 1)[0]),
        "locator": slot["locator"],
        "peer_group_id": slot["peer_group_id"] or "",
    }


def _codes(result: Any) -> set[str]:
    return {finding.code for finding in result.findings}


def _table_page_template() -> dict[str, Any]:
    template = _page_template()
    slot = {
        "slot_id": TABLE_SLOT,
        "kind": "table-cell",
        "source_part": "ppt/slides/slide1.xml",
        "locator": "graphicFrame[id=3]/table[1]/row[1]/cell[1]",
        "source_text": "Approved",
        "source_text_sha256": _hashed(b"Approved"),
        "peer_group_id": None,
        "semantic_role": "table-cell",
        "series_index": None,
        "point_index": None,
        "worksheet_ordinal": None,
        "cell_ref": None,
        "value_type": "text",
    }
    inventory = template["governed_content_inventory"]
    inventory.update(
        {
            "policy": "locked-authority-required",
            "content_slot_count": 1,
            "customer_data_slot_count": 1,
            "slots": [slot],
        }
    )
    inventory["closure_metadata"]["table_count"] = 1
    template["structure"]["table_count"] = 1
    template["structure"]["page_table_count"] = 1
    return template


def test_query_bundle_derives_exact_text_and_governed_coverage() -> None:
    template = _page_template(governed=True)
    slots = template["governed_content_inventory"]["slots"]
    result = validate_query_bundle_and_coverage(
        _bundle(template),
        lineage_records=_lineage(),
        binding_evidence=[
            _text_evidence(),
            *[_embedded_evidence(slot["slot_id"]) for slot in slots],
        ],
        governed_mutations=[_mutation(slot) for slot in slots],
        expected_library_index_sha256="9" * 64,
    )

    assert result.status == "pass", result.to_dict()
    assert result.authority is not None
    assert result.authority.required_text_keys == {(1, PAGE_ID, TEXT_SLOT)}
    assert result.authority.required_governed_keys == {
        (1, PAGE_ID, CHART_SLOT),
        (1, PAGE_ID, WORKBOOK_SLOT),
    }
    assert dict(result.authority.selected_pages[0].structure_counts) == {
        "page_shape_count": 2,
        "page_native_object_count": 2,
        "page_image_count": 0,
        "page_chart_count": 1,
        "page_table_count": 0,
    }


def test_locked_query_fragment_group_authorizes_complete_single_fact_rendering() -> None:
    template = _fragment_page_template()
    evidence = [
        _fragment_evidence("shape_2", 2, "A"),
        _fragment_evidence("shape_3", 3, "B"),
        _fragment_evidence("shape_4", 4, ""),
    ]
    coverage = validate_query_bundle_and_coverage(
        _bundle(template),
        lineage_records=_lineage(),
        binding_evidence=evidence,
        governed_mutations=[],
    )

    assert coverage.status == "pass", coverage.to_dict()
    assert coverage.authority is not None
    assert coverage.authority.fragment_group_contracts == {
        (1, PAGE_ID, "fragment_01"): ("shape_2", "shape_3", "shape_4")
    }
    result = validate_fragment_group_fact_authority(
        coverage.authority,
        binding_evidence=evidence,
        actual_text_by_key={
            (1, PAGE_ID, "shape_2"): "A",
            (1, PAGE_ID, "shape_3"): "B",
            (1, PAGE_ID, "shape_4"): "",
        },
        facts_by_id={
            "fact-title": {
                "id": "fact-title",
                "text": "AB",
                "allowed_renderings": ["A B"],
                "status": "active",
            }
        },
        connectives_by_id={"connective-clear": ""},
    )

    assert result.status == "pass"
    assert result.authorized_character_keys == {
        (1, PAGE_ID, "shape_2"),
        (1, PAGE_ID, "shape_3"),
    }


def test_query_fragment_group_membership_must_match_slot_contracts() -> None:
    template = _fragment_page_template()
    template["slot_graph"]["slots"][1]["group_id"] = None
    evidence = [
        _fragment_evidence("shape_2", 2, "A"),
        _fragment_evidence("shape_3", 3, "B"),
        _fragment_evidence("shape_4", 4, ""),
    ]

    coverage = validate_query_bundle_and_coverage(
        _bundle(template),
        lineage_records=_lineage(),
        binding_evidence=evidence,
        governed_mutations=[],
    )

    assert coverage.status == "fail"
    assert "QUERY_FRAGMENT_GROUP_MEMBERSHIP_INVALID" in _codes(coverage)


def test_fragment_group_rejects_mixed_refs_and_unlocked_clear() -> None:
    template = _fragment_page_template()
    evidence = [
        _fragment_evidence("shape_2", 2, "A"),
        _fragment_evidence("shape_3", 3, "B", fact_ref="other-fact"),
        _fragment_evidence("shape_4", 4, ""),
    ]
    evidence[2]["connective_ref"] = "invented-clear"
    coverage = validate_query_bundle_and_coverage(
        _bundle(template),
        lineage_records=_lineage(),
        binding_evidence=evidence,
        governed_mutations=[],
    )
    assert coverage.authority is not None

    result = validate_fragment_group_fact_authority(
        coverage.authority,
        binding_evidence=evidence,
        actual_text_by_key={
            (1, PAGE_ID, "shape_2"): "A",
            (1, PAGE_ID, "shape_3"): "B",
            (1, PAGE_ID, "shape_4"): "",
        },
        facts_by_id={
            "fact-title": {"text": "AB", "status": "active"},
            "other-fact": {"text": "AB", "status": "active"},
        },
        connectives_by_id={"connective-clear": ""},
    )

    assert {
        "FRAGMENT_GROUP_FACT_REF_DRIFT",
        "FRAGMENT_GROUP_CLEAR_INVALID",
    } <= {finding.code for finding in result.findings}
    assert not result.authorized_character_keys


def test_character_mode_outside_locked_fragment_group_is_rejected() -> None:
    evidence = {
        **_text_evidence(),
        "mode": "character",
        "replacement_sha256": _hashed(b"T"),
        "fact_refs": ["fact-title"],
        "asset_refs": [],
        "connective_ref": "",
    }
    coverage = validate_query_bundle_and_coverage(
        _bundle(_page_template()),
        lineage_records=_lineage(),
        binding_evidence=[evidence],
        governed_mutations=[],
    )
    assert coverage.authority is not None

    result = validate_fragment_group_fact_authority(
        coverage.authority,
        binding_evidence=[evidence],
        actual_text_by_key={(1, PAGE_ID, TEXT_SLOT): "T"},
        facts_by_id={"fact-title": {"text": "Title", "status": "active"}},
        connectives_by_id={"connective-clear": ""},
    )

    assert {finding.code for finding in result.findings} == {
        "FACT_CHARACTER_OUTSIDE_FRAGMENT_GROUP"
    }


def test_query_coverage_binds_text_and_governed_shape_identity() -> None:
    template = _page_template(governed=True)
    slots = template["governed_content_inventory"]["slots"]
    text = _text_evidence()
    text["shape_id"] = 99
    embedded = [_embedded_evidence(slot["slot_id"]) for slot in slots]
    embedded[0]["shape_id"] = 88
    mutation = [_mutation(slot) for slot in slots]
    mutation[1]["shape_id"] = 77

    result = validate_query_bundle_and_coverage(
        _bundle(template),
        lineage_records=_lineage(),
        binding_evidence=[text, *embedded],
        governed_mutations=mutation,
    )

    assert result.status == "fail"
    assert {
        "QUERY_TEXT_SHAPE_ID_MISMATCH",
        "QUERY_GOVERNED_SHAPE_ID_MISMATCH",
    } <= _codes(result)


def test_query_coverage_rejects_missing_text_and_duplicate_mutation_keys() -> None:
    template = _page_template(governed=True)
    slots = template["governed_content_inventory"]["slots"]
    duplicate = _mutation(slots[0])
    result = validate_query_bundle_and_coverage(
        _bundle(template),
        lineage_records=_lineage(),
        binding_evidence=[
            *[_embedded_evidence(slot["slot_id"]) for slot in slots],
        ],
        governed_mutations=[duplicate, copy.deepcopy(duplicate)],
    )

    assert result.status == "fail"
    assert {
        "QUERY_TEXT_COVERAGE_MISMATCH",
        "COVERAGE_KEY_DUPLICATE",
        "QUERY_GOVERNED_MUTATION_COVERAGE_MISMATCH",
    } <= _codes(result)


def test_query_authority_rejects_cleared_peer_identity_and_kind_relabel() -> None:
    template = _page_template(governed=True)
    slots = template["governed_content_inventory"]["slots"]
    mutations = [_mutation(slot) for slot in slots]
    mutations[0]["kind"] = "chart-text"
    mutations[0]["peer_group_id"] = ""
    mutations[1]["source_part"] = "ppt/embeddings/decoy.xlsx"
    result = validate_query_bundle_and_coverage(
        _bundle(template),
        lineage_records=_lineage(),
        binding_evidence=[
            _text_evidence(),
            *[_embedded_evidence(slot["slot_id"]) for slot in slots],
        ],
        governed_mutations=mutations,
    )

    assert result.status == "fail"
    assert "QUERY_GOVERNED_MUTATION_CONTRACT_MISMATCH" in _codes(result)


def test_query_bundle_schema_and_semantic_count_drift_are_rejected() -> None:
    bundle = _bundle(_page_template())
    bundle["query_count"] = 2
    result = validate_query_bundle_and_coverage(
        bundle,
        lineage_records=_lineage(),
        binding_evidence=[_text_evidence()],
        governed_mutations=[],
    )

    assert result.status == "fail"
    assert "QUERY_BUNDLE_COUNT_MISMATCH" in _codes(result)


def test_customer_replacement_policy_requires_asset_binding_count() -> None:
    template = _page_template(
        media=(("ppt/media/source.png", b"source"),),
        media_policy="customer-replacement-required",
    )
    result = validate_query_bundle_and_coverage(
        _bundle(template),
        lineage_records=_lineage(),
        binding_evidence=[_text_evidence()],
        governed_mutations=[],
    )

    assert result.status == "fail"
    assert "QUERY_ASSET_BINDING_COUNT_MISMATCH" in _codes(result)


def _fact() -> dict[str, Any]:
    return {
        "id": "fact-1",
        "text": "Revenue 42",
        "allowed_renderings": ["Revenue\n42", "42%"],
        "value": 42,
        "unit": "%",
        "status": "active",
    }


@pytest.mark.parametrize(
    "mode",
    ["character", "source-slice", "exact-numeric", "source", "clear"],
)
def test_fact_mode_vocabulary_is_closed(mode: str) -> None:
    findings = validate_fact_evidence_value(
        "4",
        evidence_mode=mode,
        fact_refs=["fact-1"],
        facts_by_id={"fact-1": _fact()},
    )

    assert {finding.code for finding in findings} == {"FACT_EVIDENCE_MODE_FORBIDDEN"}


def test_exact_mode_never_extracts_numeric_substrings() -> None:
    fact = _fact()
    fact.pop("value")
    fact["allowed_renderings"] = []
    findings = validate_fact_evidence_value(
        "42",
        evidence_mode="exact",
        fact_refs=["fact-1"],
        facts_by_id={"fact-1": fact},
    )

    assert {finding.code for finding in findings} == {"FACT_EXACT_RENDERING_MISMATCH"}


def test_normalized_and_numeric_modes_use_complete_registered_values() -> None:
    facts = {"fact-1": _fact()}

    assert not validate_fact_evidence_value(
        "Revenue42",
        evidence_mode="whitespace",
        fact_refs=["fact-1"],
        facts_by_id=facts,
    )
    assert not validate_fact_evidence_value(
        "42%",
        evidence_mode="source-numeric-rendering",
        fact_refs=["fact-1"],
        facts_by_id=facts,
    )
    assert validate_fact_evidence_value(
        "4",
        evidence_mode="source-numeric-rendering",
        fact_refs=["fact-1"],
        facts_by_id=facts,
    )


def test_join_mode_requires_multiple_complete_registered_renderings() -> None:
    facts = {
        "fact-a": {
            "text": "North",
            "allowed_renderings": ["NORTH"],
            "status": "active",
        },
        "fact-b": {
            "text": "42",
            "allowed_renderings": ["42 units"],
            "status": "active",
        },
    }

    assert validate_fact_evidence_value(
        "North · 42 units",
        evidence_mode="join",
        fact_refs=["fact-a", "fact-b"],
        facts_by_id=facts,
    ) == ()
    assert validate_fact_evidence_value(
        "NORTH42",
        evidence_mode="explicit-join",
        fact_refs=["fact-a", "fact-b"],
        facts_by_id=facts,
    ) == ()
    unsafe_separator = validate_fact_evidence_value(
        "North | 42",
        evidence_mode="join",
        fact_refs=["fact-a", "fact-b"],
        facts_by_id=facts,
    )
    partial = validate_fact_evidence_value(
        "North",
        evidence_mode="join",
        fact_refs=["fact-a", "fact-b"],
        facts_by_id=facts,
    )
    single = validate_fact_evidence_value(
        "North",
        evidence_mode="join",
        fact_refs=["fact-a"],
        facts_by_id=facts,
    )

    assert {finding.code for finding in unsafe_separator} == {
        "FACT_JOIN_RENDERING_MISMATCH"
    }
    assert {finding.code for finding in partial} == {
        "FACT_JOIN_RENDERING_MISMATCH"
    }
    assert {finding.code for finding in single} == {
        "FACT_JOIN_RENDERING_MISMATCH"
    }


def test_slice_requires_exact_external_bounds_contract() -> None:
    facts = {"fact-1": _fact()}
    missing = validate_fact_evidence_value(
        "Revenue",
        evidence_mode="slice",
        fact_refs=["fact-1"],
        facts_by_id=facts,
    )
    accepted = validate_fact_evidence_value(
        "Revenue",
        evidence_mode="slice",
        fact_refs=["fact-1"],
        facts_by_id=facts,
        render_contract={
            "fact_ref": "fact-1",
            "field": "text",
            "slice_start": 0,
            "slice_end": 7,
        },
    )
    wrong = validate_fact_evidence_value(
        "42",
        evidence_mode="slice",
        fact_refs=["fact-1"],
        facts_by_id=facts,
        render_contract={
            "fact_ref": "fact-1",
            "field": "text",
            "slice_start": 0,
            "slice_end": 7,
        },
    )

    assert {finding.code for finding in missing} == {"FACT_SLICE_CONTRACT_INVALID"}
    assert accepted == ()
    assert {finding.code for finding in wrong} == {"FACT_SLICE_RENDERING_MISMATCH"}


def _zip_bytes(entries: list[tuple[str, bytes]]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        for name, payload in entries:
            archive.writestr(name, payload)
    return output.getvalue()


def _text_shape(shape_id: int, text: str) -> str:
    return (
        "<p:sp><p:nvSpPr>"
        f'<p:cNvPr id="{shape_id}" name="Text {shape_id}"/>'
        "<p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr/>"
        f"<p:txBody><a:p><a:r><a:t>{text}</a:t></a:r></a:p></p:txBody></p:sp>"
    )


def _text_slide(*shapes: str) -> bytes:
    return (
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        f"<p:cSld><p:spTree>{''.join(shapes)}</p:spTree></p:cSld></p:sld>"
    ).encode()


def _table_slide(shape_id: int, text: str) -> bytes:
    return (
        '<p:sld xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
        'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        "<p:cSld><p:spTree><p:graphicFrame><p:nvGraphicFramePr>"
        f'<p:cNvPr id="{shape_id}" name="Table {shape_id}"/>'
        "<p:cNvGraphicFramePr/><p:nvPr/></p:nvGraphicFramePr>"
        "<a:graphic><a:graphicData><a:tbl><a:tr><a:tc><a:txBody>"
        f"<a:p><a:r><a:t>{text}</a:t></a:r></a:p>"
        "</a:txBody></a:tc></a:tr></a:tbl></a:graphicData></a:graphic>"
        "</p:graphicFrame></p:spTree></p:cSld></p:sld>"
    ).encode()


def test_output_text_audit_rejects_extra_grouped_leaf_text_shape() -> None:
    result = validate_query_bundle_and_coverage(
        _bundle(_page_template()),
        lineage_records=_lineage(),
        binding_evidence=[_text_evidence()],
        governed_mutations=[],
    )
    assert result.status == "pass"
    assert result.authority is not None
    allowed = _zip_bytes(
        [("ppt/slides/slide1.xml", _text_slide(_text_shape(2, "Approved")))]
    )
    assert audit_output_text_coverage(allowed, authority=result.authority) == ()

    grouped = (
        "<p:grpSp><p:nvGrpSpPr><p:cNvPr id=\"8\" name=\"Group\"/>"
        "<p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>"
        + _text_shape(2, "Approved")
        + _text_shape(99, "Injected")
        + "</p:grpSp>"
    )
    attacked = _zip_bytes(
        [("ppt/slides/slide1.xml", _text_slide(grouped))]
    )
    findings = audit_output_text_coverage(attacked, authority=result.authority)

    assert "OUTPUT_TEXT_SHAPE_UNAUTHORIZED" in {
        finding.code for finding in findings
    }


def test_output_table_text_requires_governed_frame_identity() -> None:
    template = _table_page_template()
    slot = template["governed_content_inventory"]["slots"][0]
    result = validate_query_bundle_and_coverage(
        _bundle(template),
        lineage_records=_lineage(),
        binding_evidence=[_text_evidence(), _embedded_evidence(TABLE_SLOT)],
        governed_mutations=[_mutation(slot)],
    )
    assert result.status == "pass", result.to_dict()
    assert result.authority is not None

    allowed = _zip_bytes(
        [("ppt/slides/slide1.xml", _table_slide(3, "Approved"))]
    )
    assert audit_output_text_coverage(allowed, authority=result.authority) == ()
    attacked = _zip_bytes(
        [("ppt/slides/slide1.xml", _table_slide(4, "Injected"))]
    )
    findings = audit_output_text_coverage(attacked, authority=result.authority)

    assert {finding.code for finding in findings} == {
        "OUTPUT_TABLE_TEXT_SHAPE_UNAUTHORIZED"
    }


def test_zip_entry_audit_accepts_only_unique_canonical_file_parts() -> None:
    with zipfile.ZipFile(io.BytesIO(_zip_bytes([("ppt/slides/slide1.xml", b"x")]))) as archive:
        audit = audit_zip_entries(archive)

    assert audit.status == "pass"
    assert audit.canonical_names == ("ppt/slides/slide1.xml",)


@pytest.mark.parametrize(
    ("entries", "code"),
    [
        (
            [("ppt/slides/slide1.xml", b"first"), ("ppt/slides/slide1.xml", b"last")],
            "ZIP_ENTRY_DUPLICATE",
        ),
        ([("/ppt/slides/slide1.xml", b"hidden")], "ZIP_ENTRY_NAME_NONCANONICAL"),
        ([("ppt/customXml/secret.xml/", b"secret")], "ZIP_DIRECTORY_ENTRY_FORBIDDEN"),
        ([("ppt/../secret.xml", b"secret")], "ZIP_ENTRY_NAME_NONCANONICAL"),
        ([("ppt\\slides\\slide1.xml", b"x")], "ZIP_ENTRY_NAME_NONCANONICAL"),
    ],
)
def test_zip_entry_audit_rejects_alias_and_hidden_payload_attacks(
    entries: list[tuple[str, bytes]],
    code: str,
) -> None:
    with zipfile.ZipFile(io.BytesIO(_zip_bytes(entries))) as archive:
        audit = audit_zip_entries(archive)

    assert audit.status == "fail"
    assert code in {finding.code for finding in audit.findings}


def test_external_relationship_allowlist_accepts_only_https_hyperlinks() -> None:
    hyperlink_type = (
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink"
    )
    assert validate_external_relationship(
        {
            "Type": hyperlink_type,
            "Target": "https://example.com/path",
            "TargetMode": "External",
        }
    ) == ()
    image_findings = validate_external_relationship(
        {
            "Type": hyperlink_type.replace("hyperlink", "image"),
            "Target": "https://attacker.example/tracker.png",
            "TargetMode": "External",
        }
    )
    unsafe_findings = validate_external_relationship(
        {
            "Type": hyperlink_type,
            "Target": "https://user:secret@example.com/path",
            "TargetMode": "External",
        }
    )

    assert {finding.code for finding in image_findings} == {
        "EXTERNAL_RELATIONSHIP_TYPE_FORBIDDEN"
    }
    assert {finding.code for finding in unsafe_findings} == {
        "EXTERNAL_RELATIONSHIP_TARGET_INVALID"
    }


def test_output_media_must_match_selected_template_or_used_locked_asset() -> None:
    certified = b"certified-image"
    template = _page_template(
        media=(("ppt/media/certified.png", certified),),
        media_policy="certified-decorative-retain",
    )
    result = validate_query_bundle_and_coverage(
        _bundle(template),
        lineage_records=_lineage(),
        binding_evidence=[_text_evidence()],
        governed_mutations=[],
    )
    assert result.status == "pass", result.to_dict()
    assert result.authority is not None

    approved_asset = b"approved-client-image"
    binding = {
        "ordinal": 1,
        "page_id": PAGE_ID,
        "slot_id": "shape_9",
        "binding_kind": "asset",
        "asset_refs": ["client-image"],
        "replacement_sha256": _hashed(approved_asset),
    }
    allowed_package = _zip_bytes(
        [
            ("ppt/media/certified.png", certified),
            ("ppt/media/client.png", approved_asset),
        ]
    )
    assert audit_output_media_authority(
        allowed_package,
        authority=result.authority,
        asset_sha256_by_ref={"client-image": _hashed(approved_asset)},
        binding_evidence=[binding],
    ) == ()

    injected = _zip_bytes(
        [
            ("ppt/media/certified.png", certified),
            ("ppt/media/undeclared.png", b"undeclared"),
        ]
    )
    findings = audit_output_media_authority(
        injected,
        authority=result.authority,
        asset_sha256_by_ref={},
        binding_evidence=[],
    )
    assert {finding.code for finding in findings} == {
        "OUTPUT_MEDIA_SHA256_UNAUTHORIZED"
    }
