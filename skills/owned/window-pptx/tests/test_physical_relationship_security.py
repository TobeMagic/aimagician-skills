"""Security regressions for strict OPC relationship parsing and rewriting."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest


SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from window_pptx.physical_assembly import (
    PhysicalAssemblyError,
    _inspect_all_relationships,
    _parse_relationships,
    _rewrite_relationship_targets,
)


REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def test_strict_parser_accepts_default_namespace_and_single_quoted_attributes() -> None:
    relationships = (
        f"<Relationships xmlns='{REL_NS}'>"
        f"<Relationship Id='rId1' Type='{OFFICE_REL}/image' "
        "Target='../media/image1.png'/>"
        "</Relationships>"
    ).encode()

    assert _parse_relationships(relationships) == [
        {
            "Id": "rId1",
            "Type": f"{OFFICE_REL}/image",
            "Target": "../media/image1.png",
            "TargetMode": "",
        }
    ]


def test_strict_parser_accepts_prefixed_relationship_namespace() -> None:
    relationships = (
        f"<pkg:Relationships xmlns:pkg='{REL_NS}'>"
        f"<pkg:Relationship Id='rId9' Type='{OFFICE_REL}/chart' "
        "Target='../charts/chart1.xml'></pkg:Relationship>"
        "</pkg:Relationships>"
    ).encode()

    parsed = _parse_relationships(relationships)

    assert parsed[0]["Id"] == "rId9"
    assert parsed[0]["Target"] == "../charts/chart1.xml"


@pytest.mark.parametrize(
    "relationships",
    (
        b"<Relationships>",
        (
            f"<Relationships xmlns='{REL_NS}'>"
            f"<Relationship Id='rId1' Type='{OFFICE_REL}/image' "
            "Target='../media/image1.png'/><broken>"
            "</Relationships>"
        ).encode(),
        (
            f"<Relationships xmlns='{REL_NS}'>"
            f"<Relationship Id='rId1' Type='{OFFICE_REL}/image'/>"
            "</Relationships>"
        ).encode(),
        (
            f"<Relationships xmlns='{REL_NS}'>"
            f"<Relationship Id='rId1' Type='{OFFICE_REL}/image' "
            "Target='../media/image1.png' TargetMode='external'/>"
            "</Relationships>"
        ).encode(),
    ),
)
def test_strict_parser_rejects_malformed_or_invalid_documents(
    relationships: bytes,
) -> None:
    with pytest.raises(PhysicalAssemblyError, match="relationship XML"):
        _parse_relationships(relationships)


def test_rewrite_preserves_safe_https_and_applies_asset_override_deterministically() -> None:
    relationships = (
        f"<r:Relationships xmlns:r='{REL_NS}'>"
        f"<r:Relationship Id='rId2' Type='{OFFICE_REL}/image' "
        "Target='../media/source.png'/>"
        f"<r:Relationship Id='rId1' Type='{OFFICE_REL}/hyperlink' "
        "Target='https://example.com/evidence?a=1&amp;b=2' TargetMode='External'/>"
        "</r:Relationships>"
    ).encode()
    kwargs = {
        "rels_xml": relationships,
        "rels_path": "ppt/slides/_rels/slide1.xml.rels",
        "target_map": {},
        "output_rels_path": "ppt/slides/_rels/slide5.xml.rels",
        "relationship_overrides": {"rId2": "ppt/media/authority.png"},
    }

    first = _rewrite_relationship_targets(**kwargs)
    second = _rewrite_relationship_targets(**kwargs)
    parsed = {entry["Id"]: entry for entry in _parse_relationships(first)}

    assert first == second
    assert parsed["rId1"]["Target"] == "https://example.com/evidence?a=1&b=2"
    assert parsed["rId1"]["TargetMode"] == "External"
    assert parsed["rId2"]["Target"] == "../media/authority.png"


@pytest.mark.parametrize(
    "target",
    (
        "file:///tmp/secret.txt",
        "javascript:alert(1)",
        "http://example.com/insecure",
    ),
)
def test_rewrite_rejects_unsafe_external_targets(target: str) -> None:
    relationships = (
        f"<Relationships xmlns='{REL_NS}'>"
        f"<Relationship Id='rId1' Type='{OFFICE_REL}/hyperlink' "
        f"Target='{target}' TargetMode='External'/>"
        "</Relationships>"
    ).encode()

    with pytest.raises(PhysicalAssemblyError, match="unsafe external"):
        _rewrite_relationship_targets(
            relationships,
            "ppt/slides/_rels/slide1.xml.rels",
            {},
        )


def test_rewrite_rejects_https_without_external_target_mode() -> None:
    relationships = (
        f"<Relationships xmlns='{REL_NS}'>"
        f"<Relationship Id='rId1' Type='{OFFICE_REL}/hyperlink' "
        "Target='https://example.com/evidence'/>"
        "</Relationships>"
    ).encode()

    with pytest.raises(PhysicalAssemblyError, match="unsafe relationship target mode"):
        _rewrite_relationship_targets(
            relationships,
            "ppt/slides/_rels/slide1.xml.rels",
            {},
        )


@pytest.mark.parametrize("forbidden_type", ("oleObject", "vbaProject", "script", "macroLink"))
def test_rewrite_rejects_ole_macro_and_script_relationship_types(
    forbidden_type: str,
) -> None:
    relationships = (
        f"<Relationships xmlns='{REL_NS}'>"
        f"<Relationship Id='rId1' Type='{OFFICE_REL}/{forbidden_type}' "
        "Target='../customXml/item1.xml'/>"
        "</Relationships>"
    ).encode()

    with pytest.raises(PhysicalAssemblyError, match="forbidden relationship type"):
        _rewrite_relationship_targets(
            relationships,
            "ppt/slides/_rels/slide1.xml.rels",
            {"ppt/customXml/item1.xml": "ppt/v61/customXml/item1.xml"},
        )


def test_rewrite_rejects_script_target_even_over_https() -> None:
    relationships = (
        f"<Relationships xmlns='{REL_NS}'>"
        f"<Relationship Id='rId1' Type='{OFFICE_REL}/hyperlink' "
        "Target='https://example.com/run.js' TargetMode='External'/>"
        "</Relationships>"
    ).encode()

    with pytest.raises(PhysicalAssemblyError, match="forbidden relationship target"):
        _rewrite_relationship_targets(
            relationships,
            "ppt/slides/_rels/slide1.xml.rels",
            {},
        )


def test_output_audit_fails_closed_on_malformed_relationship_part(tmp_path: Path) -> None:
    output = tmp_path / "malformed.pptx"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("ppt/slides/slide1.xml", b"<p:sld xmlns:p='p'/>")
        archive.writestr(
            "ppt/slides/_rels/slide1.xml.rels",
            (
                f"<Relationships xmlns='{REL_NS}'>"
                f"<Relationship Id='rId1' Type='{OFFICE_REL}/image' "
                "Target='../media/image1.png'>"
                "</Relationships>"
            ).encode(),
        )

    audit = _inspect_all_relationships(output)

    assert audit.status == "fail"
    assert audit.unresolved_internal_relationships[0]["reason"] == (
        "relationship-package-read-failed"
    )
