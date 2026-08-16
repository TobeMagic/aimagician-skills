"""Physical feasibility probing for client-populated certified cover pages.

A catalog capacity estimate cannot prove that independently authored title,
department and date surfaces remain visually separate after replacement.  This
module deliberately executes the same bounded physical import and release QA
used by a delivery, but only for one candidate cover and in a disposable
workspace.  It returns public IDs and compact QA evidence, never a source
path, source byte, preview or client copy.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .adaptation import compile_adaptation
from .brief_binding import compile_outline_bindings
from .composition import compile_composition
from .physical_adapter import assemble_from_plans, preflight_native_slots
from .query import (
    _SUITABILITY_PROFILES,
    _suitability_safe,
    materialization_eligible,
    role_matches_page,
    style_signature_from_observation,
)


class CoverProbeError(ValueError):
    """Raised when a requested cover probe exceeds its governed boundary."""


_REQUEST_VERSION = "pptx-studio-cover-probe.v1"
_REQUEST_FIELDS = frozenset({"schema_version", "candidate_id", "suitability", "facts"})
_FACT_FIELDS = frozenset({"fact_id", "value", "semantic_role"})
_PAGE_PROBE_REQUEST_VERSION = "pptx-studio-page-probe.v1"
_PAGE_PROBE_REQUEST_FIELDS = frozenset({"schema_version", "candidate_id", "role", "suitability", "minimum_capacity", "facts"})
_STRUCTURAL_ROLES = frozenset({"cover", "contents", "section", "closing"})


def _physical_check_status(report: Any, attribute: str) -> str:
    """Return a compact physical-gate status without masking probe failure.

    Production assembly always returns the named nested evidence object.  The
    probe is also used by narrow unit tests and future compatibility adapters,
    where a report may legitimately only expose its aggregate status.  A
    missing diagnostic must remain visible as unavailable rather than turning
    a genuine QA failure into an AttributeError.
    """

    check = getattr(report, attribute, None)
    status = getattr(check, "status", None)
    return status if isinstance(status, str) else "not_available"


def _physical_summary(report: Any) -> dict[str, Any]:
    """Expose aggregate assembly gates without leaking a private source path."""

    lineage = getattr(report, "lineage_records", ())
    if not isinstance(lineage, (list, tuple)):
        lineage = ()
    return {
        "acceptance_profile": getattr(report, "acceptance_profile", "not_available"),
        "target_slide_count": getattr(report, "target_slide_count", "not_available"),
        "lineage_record_count": len(lineage),
        "lineage_statuses": [
            status if isinstance(status := getattr(record, "status", None), str) else "not_available"
            for record in lineage
        ],
        "lineage_gates": [
            {
                "source_package_verified": bool(getattr(record, "source_package_verified", False)),
                "source_slide_verified": bool(getattr(record, "source_slide_verified", False)),
                "structure_match": bool(getattr(record, "structure_match", False)),
                "has_imported_part_map": bool(getattr(record, "imported_part_map_sha256", "")),
                "imported_part_count": (
                    getattr(record, "imported_part_count")
                    if isinstance(getattr(record, "imported_part_count", None), int)
                    else "not_available"
                ),
            }
            for record in lineage
        ],
        "duplicate_page_record_count": len(
            getattr(report, "duplicate_page_records", ())
            if isinstance(getattr(report, "duplicate_page_records", ()), (list, tuple))
            else ()
        ),
    }


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _validate_request(request: Mapping[str, Any]) -> tuple[str, str, list[dict[str, str]]]:
    if set(request) != _REQUEST_FIELDS or request.get("schema_version") != _REQUEST_VERSION:
        raise CoverProbeError("COVER_PROBE_REQUEST_INVALID")
    candidate_id = request.get("candidate_id")
    suitability = request.get("suitability")
    raw_facts = request.get("facts")
    if not isinstance(candidate_id, str) or not candidate_id:
        raise CoverProbeError("COVER_PROBE_CANDIDATE_INVALID")
    if suitability not in _SUITABILITY_PROFILES:
        raise CoverProbeError("COVER_PROBE_SUITABILITY_INVALID")
    if not isinstance(raw_facts, list) or not raw_facts:
        raise CoverProbeError("COVER_PROBE_FACTS_INVALID")
    facts: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw_facts:
        if (
            not isinstance(item, Mapping)
            or set(item) != _FACT_FIELDS
            or not isinstance(item.get("fact_id"), str)
            or not item["fact_id"]
            or item["fact_id"] in seen
            or not isinstance(item.get("value"), str)
            or not item["value"]
            or not isinstance(item.get("semantic_role"), str)
            or not item["semantic_role"]
        ):
            raise CoverProbeError("COVER_PROBE_FACT_INVALID")
        seen.add(item["fact_id"])
        facts.append({
            "fact_id": item["fact_id"],
            "value": item["value"],
            "semantic_role": item["semantic_role"],
        })
    return candidate_id, str(suitability), facts


def _candidate(
    catalog: Mapping[str, Any], observations: Mapping[str, Mapping[str, Any]],
    *, candidate_id: str, suitability: str,
) -> tuple[Mapping[str, Any], Mapping[str, Any], list[str]]:
    pages = {
        str(page.get("page_id")): page
        for page in catalog.get("pages", [])
        if isinstance(page, Mapping) and isinstance(page.get("page_id"), str)
    }
    page = pages.get(candidate_id)
    observation_entry = observations.get(candidate_id)
    if page is None or not isinstance(observation_entry, Mapping):
        raise CoverProbeError("COVER_PROBE_CANDIDATE_UNKNOWN")
    detail = observation_entry.get("observation")
    render = page.get("render")
    if (
        not isinstance(detail, Mapping)
        or not isinstance(render, Mapping)
        or observation_entry.get("image_sha256") != render.get("image_sha256")
        or not materialization_eligible(page)
        or not role_matches_page(page, detail, "cover")
        or not _suitability_safe(detail, profile=suitability)
    ):
        raise CoverProbeError("COVER_PROBE_CANDIDATE_INELIGIBLE")
    region_ids = [
        str(region.get("region_id"))
        for region in catalog.get("regions", [])
        if isinstance(region, Mapping)
        and region.get("page_id") == candidate_id
        and isinstance(region.get("region_id"), str)
    ]
    if not region_ids:
        raise CoverProbeError("COVER_PROBE_REGIONS_MISSING")
    return page, detail, region_ids


def probe_cover_candidate(
    catalog: Mapping[str, Any], *, observations: Mapping[str, Mapping[str, Any]],
    request: Mapping[str, Any], private_source_root: Path | str,
    workspace: Path | str,
) -> dict[str, Any]:
    """Physically assemble and QA one client-populated cover candidate.

    The output is intentionally an eligibility report, not a delivery plan.
    A PASS can be copied to the subsequent style-cluster request only through
    its ``locked_anchor_page_id``.  The temporary PPTX is removed after QA so
    no trial cover is mistaken for the final client delivery.
    """

    candidate_id, suitability, facts = _validate_request(request)
    page, detail, region_ids = _candidate(
        catalog, observations, candidate_id=candidate_id, suitability=suitability,
    )
    temp_root = Path(workspace).expanduser().resolve(strict=False)
    temp_root.mkdir(parents=True, exist_ok=True)
    probe_dir = Path(tempfile.mkdtemp(prefix="cover-probe-", dir=temp_root))
    probe_output = probe_dir / "cover-probe.pptx"
    try:
        title_capacity = max(len("".join(item["value"].split())) for item in facts)
        composition_request = {
            "schema_version": "1.0",
            "strategy": "page_assembly",
            "art_direction": {
                "anchor_page_id": candidate_id,
                "allowed_style_signatures": [style_signature_from_observation(detail)],
                "suitability": suitability,
            },
            "slides": [{
                "slide_id": "cover-probe",
                "role": "cover",
                "candidate_ids": [candidate_id],
                "selected_candidate_id": candidate_id,
                "minimum_capacity": title_capacity,
            }],
        }
        composition_plan = compile_composition(
            catalog, observations=observations, request=composition_request,
        )
        preflight = preflight_native_slots(
            composition_plan, catalog=catalog, private_source_root=private_source_root,
        )
        outline = {
            "schema_version": "1.0",
            "slides": [{
                "slide_id": "cover-probe",
                "facts": [
                    {"value": item["value"], "semantic_role": item["semantic_role"]}
                    for item in facts
                ],
            }],
        }
        adaptation_request = compile_outline_bindings(outline, preflight=preflight)
        adaptation_plan = compile_adaptation(
            composition_plan, catalog=catalog, request=adaptation_request,
            preflight=preflight,
        )
        physical_report, lineage = assemble_from_plans(
            composition_plan, adaptation_plan, adaptation_request,
            catalog=catalog, private_source_root=private_source_root,
            workspace=probe_dir / "assembly", output_path=probe_output,
        )
        qa = lineage.get("qa") if isinstance(lineage, Mapping) else None
        qa_status = qa.get("status") if isinstance(qa, Mapping) else "not_run"
        blockers = qa.get("blockers", []) if isinstance(qa, Mapping) else []
        if physical_report.status == "pass" and qa_status == "pass":
            return {
                "schema_version": _REQUEST_VERSION,
                "status": "PASS",
                "candidate_id": candidate_id,
                "locked_anchor_page_id": candidate_id,
                "probe_sha256": _canonical_sha256(request),
                "evidence": {
                    "physical_status": "pass",
                    "qa_status": "pass",
                    "output_sha256": lineage.get("output_sha256"),
                    "binding_count": len(adaptation_plan.get("operations", [])),
                },
            }
        return {
            "schema_version": _REQUEST_VERSION,
            "status": "NO_MATCH",
            "candidate_id": candidate_id,
            "code": "COVER_PROBE_PHYSICAL_QA_FAILED",
            "evidence": {
                "physical_status": physical_report.status,
                "qa_status": qa_status,
                "blocker_rules": [
                    str(item.get("rule")) for item in blockers
                    if isinstance(item, Mapping) and isinstance(item.get("rule"), str)
                ],
            },
        }
    except (CoverProbeError, ValueError) as exc:
        return {
            "schema_version": _REQUEST_VERSION,
            "status": "NO_MATCH",
            "candidate_id": candidate_id,
            "code": str(exc),
        }
    finally:
        # The validated anchor identity and SHA are sufficient evidence for a
        # later plan. The ephemeral candidate must not be treated as delivery.
        shutil.rmtree(probe_dir, ignore_errors=True)


def probe_page_candidate(
    catalog: Mapping[str, Any], *, observations: Mapping[str, Mapping[str, Any]],
    request: Mapping[str, Any], private_source_root: Path | str,
    workspace: Path | str,
) -> dict[str, Any]:
    """Physically bind and QA a certified non-structural page in isolation.

    This produces only disposable feasibility evidence.  It deliberately uses
    the v1 one-page composition route so it cannot pretend to be a complete
    narrative-bound delivery, while still exercising the identical native
    preflight, binding, adaptation, import and QA transaction.
    """

    if set(request) != _PAGE_PROBE_REQUEST_FIELDS or request.get("schema_version") != _PAGE_PROBE_REQUEST_VERSION:
        raise CoverProbeError("PAGE_PROBE_REQUEST_INVALID")
    candidate_id, role, suitability, minimum_capacity, raw_facts = (
        request.get("candidate_id"), request.get("role"), request.get("suitability"),
        request.get("minimum_capacity"), request.get("facts"),
    )
    if not isinstance(candidate_id, str) or not candidate_id:
        raise CoverProbeError("PAGE_PROBE_CANDIDATE_INVALID")
    if not isinstance(role, str) or not role or role in _STRUCTURAL_ROLES:
        raise CoverProbeError("PAGE_PROBE_ROLE_INVALID")
    if suitability not in _SUITABILITY_PROFILES:
        raise CoverProbeError("PAGE_PROBE_SUITABILITY_INVALID")
    if type(minimum_capacity) is not int or minimum_capacity < 1:
        raise CoverProbeError("PAGE_PROBE_CAPACITY_INVALID")
    if not isinstance(raw_facts, list) or not raw_facts:
        raise CoverProbeError("PAGE_PROBE_FACTS_INVALID")
    facts: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in raw_facts:
        if (
            not isinstance(item, Mapping)
            or set(item) != _FACT_FIELDS
            or not isinstance(item.get("fact_id"), str)
            or not item["fact_id"]
            or item["fact_id"] in seen
            or not isinstance(item.get("value"), str)
            or not item["value"]
            or not isinstance(item.get("semantic_role"), str)
            or not item["semantic_role"]
        ):
            raise CoverProbeError("PAGE_PROBE_FACT_INVALID")
        seen.add(item["fact_id"])
        facts.append({"fact_id": item["fact_id"], "value": item["value"], "semantic_role": item["semantic_role"]})

    pages = {
        str(page.get("page_id")): page
        for page in catalog.get("pages", [])
        if isinstance(page, Mapping) and isinstance(page.get("page_id"), str)
    }
    page = pages.get(candidate_id)
    observation_entry = observations.get(candidate_id)
    detail = observation_entry.get("observation") if isinstance(observation_entry, Mapping) else None
    render = page.get("render") if isinstance(page, Mapping) else None
    if (
        not isinstance(page, Mapping)
        or not isinstance(observation_entry, Mapping)
        or not isinstance(detail, Mapping)
        or not isinstance(render, Mapping)
        or observation_entry.get("image_sha256") != render.get("image_sha256")
        or not materialization_eligible(page)
        or not role_matches_page(page, detail, role)
        or not _suitability_safe(detail, profile=suitability)
    ):
        raise CoverProbeError("PAGE_PROBE_CANDIDATE_INELIGIBLE")

    temp_root = Path(workspace).expanduser().resolve(strict=False)
    temp_root.mkdir(parents=True, exist_ok=True)
    probe_dir = Path(tempfile.mkdtemp(prefix="page-probe-", dir=temp_root))
    try:
        composition_request = {
            "schema_version": "1.0",
            "strategy": "page_assembly",
            "art_direction": {
                "anchor_page_id": candidate_id,
                "allowed_style_signatures": [style_signature_from_observation(detail)],
                "suitability": suitability,
            },
            "slides": [{
                "slide_id": "page-probe", "role": role,
                "candidate_ids": [candidate_id], "selected_candidate_id": candidate_id,
                # Surface count and semantic capacity are different. A four-step
                # timeline has one title plus four meaningful milestones, while
                # binding consumes nine native title/label/body surfaces.
                "minimum_capacity": minimum_capacity,
            }],
        }
        composition_plan = compile_composition(catalog, observations=observations, request=composition_request)
        preflight = preflight_native_slots(
            composition_plan, catalog=catalog, private_source_root=private_source_root,
        )
        outline = {
            "schema_version": "1.0",
            "slides": [{"slide_id": "page-probe", "facts": [
                {"value": item["value"], "semantic_role": item["semantic_role"]} for item in facts
            ]}],
        }
        adaptation_request = compile_outline_bindings(outline, preflight=preflight)
        adaptation_plan = compile_adaptation(
            composition_plan, catalog=catalog, request=adaptation_request, preflight=preflight,
        )
        physical_report, lineage = assemble_from_plans(
            composition_plan, adaptation_plan, adaptation_request, catalog=catalog,
            private_source_root=private_source_root, workspace=probe_dir / "assembly",
            output_path=probe_dir / "page-probe.pptx",
        )
        qa = lineage.get("qa") if isinstance(lineage, Mapping) else None
        qa_status = qa.get("status") if isinstance(qa, Mapping) else "not_run"
        blockers = qa.get("blockers", []) if isinstance(qa, Mapping) else []
        if physical_report.status == "pass" and qa_status == "pass":
            return {
                "schema_version": _PAGE_PROBE_REQUEST_VERSION, "status": "PASS",
                "candidate_id": candidate_id, "role": role, "probe_sha256": _canonical_sha256(request),
                "evidence": {
                    "physical_status": "pass", "qa_status": "pass",
                    "output_sha256": lineage.get("output_sha256"),
                    "binding_count": len(adaptation_plan.get("operations", [])),
                },
            }
        return {
            "schema_version": _PAGE_PROBE_REQUEST_VERSION, "status": "NO_MATCH",
            "candidate_id": candidate_id, "role": role, "code": "PAGE_PROBE_PHYSICAL_QA_FAILED",
            "evidence": {
                "physical_status": physical_report.status, "qa_status": qa_status,
                "blocker_rules": [
                    str(item.get("rule")) for item in blockers
                    if isinstance(item, Mapping) and isinstance(item.get("rule"), str)
                ],
                "physical_checks": {
                    "opc_integrity": _physical_check_status(physical_report, "opc_integrity"),
                    "editability": _physical_check_status(physical_report, "editability"),
                    "style_cluster": _physical_check_status(physical_report, "style_cluster_adherence"),
                    "authority": _physical_check_status(physical_report, "authority"),
                    "selection_authority": _physical_check_status(physical_report, "selection_authority"),
                    "source_residue": _physical_check_status(physical_report, "source_residue"),
                    "libreoffice": _physical_check_status(physical_report, "libreoffice"),
                    "size": _physical_check_status(physical_report, "size_check"),
                },
                "physical_summary": _physical_summary(physical_report),
            },
        }
    except (CoverProbeError, ValueError) as exc:
        return {
            "schema_version": _PAGE_PROBE_REQUEST_VERSION, "status": "NO_MATCH",
            "candidate_id": candidate_id, "role": role, "code": str(exc),
        }
    finally:
        shutil.rmtree(probe_dir, ignore_errors=True)


__all__ = ["CoverProbeError", "probe_cover_candidate", "probe_page_candidate"]
