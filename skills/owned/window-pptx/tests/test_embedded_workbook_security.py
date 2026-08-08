"""Security regressions for governed chart workbooks embedded in PPTX output."""

from __future__ import annotations

import hashlib
import io
import posixpath
import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable

import pytest

SKILL_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_ROOT / "scripts"))

from window_pptx.page_template_library import PageTemplate
from window_pptx.physical_assembly import (
    AssemblyTargetSlide,
    PhysicalAssemblyError,
    TextBindingSpec,
    _SourceGraph,
    _mutate_governed_workbook,
    _prepare_governed_content_replacements,
)
from window_pptx.weak_model import Fact, FactSource, FactStore, TrustedProject


PACKAGE_REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE_REL_NS = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
)
SPREADSHEET_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
CONTENT_TYPES_NS = "http://schemas.openxmlformats.org/package/2006/content-types"

SENSITIVE_TEXT = "Sensitive customer label"
REPLACEMENT_TEXT = "Approved replacement"


def _relationships(
    entries: Iterable[tuple[str, str, str, str]],
) -> bytes:
    body = "".join(
        (
            f'<Relationship Id="{relation_id}" Type="{relation_type}" '
            f'Target="{target}"'
            + (f' TargetMode="{target_mode}"' if target_mode else "")
            + "/>"
        )
        for relation_id, relation_type, target, target_mode in entries
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<Relationships xmlns="{PACKAGE_REL_NS}">{body}</Relationships>'
    ).encode("utf-8")


def _content_types(overrides: Iterable[tuple[str, str]]) -> bytes:
    body = "".join(
        f'<Override PartName="/{part_name}" ContentType="{content_type}"/>'
        for part_name, content_type in overrides
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<Types xmlns="{CONTENT_TYPES_NS}">'
        '<Default Extension="rels" '
        'ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        f"{body}</Types>"
    ).encode("utf-8")


def _zip_bytes(parts: dict[str, bytes]) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(parts):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, parts[name])
    return output.getvalue()


def _rewrite_workbook_parts(
    source: bytes,
    *,
    updates: dict[str, bytes] | None = None,
    remove: tuple[str, ...] = (),
) -> bytes:
    with zipfile.ZipFile(io.BytesIO(source), "r") as archive:
        parts = {name: archive.read(name) for name in archive.namelist()}
    parts.update(updates or {})
    for name in remove:
        parts.pop(name, None)
    return _zip_bytes(parts)


def _workbook_bytes(*, threat: str | None = None) -> bytes:
    """Build a deterministic XLSX with one governed and three retained cells."""

    workbook_relationships = [
        ("rId1", f"{OFFICE_REL_NS}/worksheet", "worksheets/sheet1.xml", ""),
        ("rId2", f"{OFFICE_REL_NS}/sharedStrings", "sharedStrings.xml", ""),
    ]
    worksheet_relationships: list[tuple[str, str, str, str]] = []
    overrides = [
        (
            "xl/workbook.xml",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml",
        ),
        (
            "xl/worksheets/sheet1.xml",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
        ),
        (
            "xl/sharedStrings.xml",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml",
        ),
    ]
    extra_parts: dict[str, bytes] = {}
    formula_cell = ""

    if threat == "formula":
        formula_cell = '<c r="B1"><f>SUM(1,1)</f><v>2</v></c>'
    elif threat == "external-links":
        workbook_relationships.append(
            (
                "rId3",
                f"{OFFICE_REL_NS}/externalLink",
                "externalLinks/externalLink1.xml",
                "",
            )
        )
        extra_parts["xl/externalLinks/externalLink1.xml"] = (
            f'<externalLink xmlns="{SPREADSHEET_NS}"/>'
        ).encode("utf-8")
        extra_parts["xl/externalLinks/_rels/externalLink1.xml.rels"] = _relationships(
            [
                (
                    "rId1",
                    f"{OFFICE_REL_NS}/externalLinkPath",
                    "file:///private/source.xlsx",
                    "External",
                )
            ]
        )
        overrides.append(
            (
                "xl/externalLinks/externalLink1.xml",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.externalLink+xml",
            )
        )
    elif threat == "connections":
        workbook_relationships.append(
            ("rId3", f"{OFFICE_REL_NS}/connections", "connections.xml", "")
        )
        extra_parts["xl/connections.xml"] = (
            f'<connections xmlns="{SPREADSHEET_NS}" count="0"/>'
        ).encode("utf-8")
        overrides.append(
            (
                "xl/connections.xml",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.connections+xml",
            )
        )
    elif threat == "ole":
        worksheet_relationships.append(
            (
                "rId1",
                f"{OFFICE_REL_NS}/oleObject",
                "../embeddings/oleObject1.bin",
                "",
            )
        )
        extra_parts["xl/embeddings/oleObject1.bin"] = b"OLE-object-payload"
        overrides.append(
            (
                "xl/embeddings/oleObject1.bin",
                "application/vnd.openxmlformats-officedocument.oleObject",
            )
        )
    elif threat == "activex":
        worksheet_relationships.append(
            (
                "rId1",
                f"{OFFICE_REL_NS}/control",
                "../activeX/activeX1.bin",
                "",
            )
        )
        extra_parts["xl/activeX/activeX1.bin"] = b"ActiveX-control-payload"
        overrides.append(
            ("xl/activeX/activeX1.bin", "application/vnd.ms-office.activeX")
        )
    elif threat == "macro":
        workbook_relationships.append(
            ("rId3", f"{OFFICE_REL_NS}/vbaProject", "vbaProject.bin", "")
        )
        extra_parts["xl/vbaProject.bin"] = b"VBA-project-payload"
        overrides.append(("xl/vbaProject.bin", "application/vnd.ms-office.vbaProject"))
    elif threat == "unsafe-external-relationship":
        worksheet_relationships.append(
            (
                "rId1",
                f"{OFFICE_REL_NS}/hyperlink",
                "file:///private/customer-data.xlsx",
                "External",
            )
        )
    elif threat == "missing-internal-relationship":
        worksheet_relationships.append(
            ("rId1", f"{OFFICE_REL_NS}/image", "../media/missing.png", "")
        )
    elif threat is not None:
        raise AssertionError(f"unknown threat fixture: {threat}")

    parts = {
        "[Content_Types].xml": _content_types(overrides),
        "_rels/.rels": _relationships(
            [
                (
                    "rId1",
                    f"{OFFICE_REL_NS}/officeDocument",
                    "xl/workbook.xml",
                    "",
                )
            ]
        ),
        "xl/workbook.xml": (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<workbook xmlns="{SPREADSHEET_NS}" xmlns:r="{OFFICE_REL_NS}">'
            '<sheets><sheet name="Data" sheetId="1" r:id="rId1"/></sheets>'
            "</workbook>"
        ).encode("utf-8"),
        "xl/_rels/workbook.xml.rels": _relationships(workbook_relationships),
        "xl/worksheets/sheet1.xml": (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<worksheet xmlns="{SPREADSHEET_NS}"><sheetData>'
            f'<row r="1"><c r="A1" t="s"><v>0</v></c>{formula_cell}</row>'
            '<row r="2"><c r="A2" t="s"><v>1</v></c></row>'
            '<row r="3"><c r="A3" t="s"><v>1</v></c></row>'
            '<row r="4"><c r="A4" t="s"><v>2</v></c></row>'
            "</sheetData></worksheet>"
        ).encode("utf-8"),
        "xl/sharedStrings.xml": (
            '<?xml version="1.0" encoding="UTF-8"?>'
            f'<sst xmlns="{SPREADSHEET_NS}" count="4" uniqueCount="3">'
            f"<si><t>{SENSITIVE_TEXT}</t></si>"
            "<si><t>Retained label</t></si>"
            "<si><t>Other label</t></si>"
            "</sst>"
        ).encode("utf-8"),
        **extra_parts,
    }
    if worksheet_relationships:
        parts["xl/worksheets/_rels/sheet1.xml.rels"] = _relationships(
            worksheet_relationships
        )
    return _zip_bytes(parts)


def _governed_record(*, source_part: str = "ppt/embeddings/book.xlsx") -> dict[str, str]:
    return {
        "slot_id": "workbook-cell-a1",
        "kind": "workbook-cell",
        "source_part": source_part,
        "locator": "chartFrame[id=7]/xl/worksheets/sheet1.xml!A1",
        "source_text": SENSITIVE_TEXT,
        "source_text_sha256": hashlib.sha256(SENSITIVE_TEXT.encode("utf-8")).hexdigest(),
        "semantic_role": "workbook-unreferenced",
        "value_type": "string",
    }


def _mutate(workbook_bytes: bytes) -> bytes:
    return _mutate_governed_workbook(
        workbook_bytes,
        [(_governed_record(), REPLACEMENT_TEXT)],
    )


def _shared_strings(archive: zipfile.ZipFile) -> tuple[ET.Element, list[str]]:
    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    values = [
        "".join(
            node.text or ""
            for node in item.iter()
            if node.tag.rsplit("}", 1)[-1] == "t"
        )
        for item in root.iter()
        if item.tag.rsplit("}", 1)[-1] == "si"
    ]
    return root, values


def _worksheet_cells(
    archive: zipfile.ZipFile,
    shared_strings: list[str],
) -> tuple[dict[str, str], dict[str, int]]:
    root = ET.fromstring(archive.read("xl/worksheets/sheet1.xml"))
    values: dict[str, str] = {}
    shared_indices: dict[str, int] = {}
    for cell in (node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "c"):
        reference = cell.attrib["r"]
        if cell.attrib.get("t") == "inlineStr":
            values[reference] = "".join(
                node.text or ""
                for node in cell.iter()
                if node.tag.rsplit("}", 1)[-1] == "t"
            )
            continue
        value_node = next(
            (
                node
                for node in list(cell)
                if node.tag.rsplit("}", 1)[-1] == "v"
            ),
            None,
        )
        raw = (value_node.text or "") if value_node is not None else ""
        if cell.attrib.get("t") == "s":
            index = int(raw)
            assert 0 <= index < len(shared_strings), (
                f"{reference} has invalid shared-string index {index}"
            )
            shared_indices[reference] = index
            values[reference] = shared_strings[index]
        else:
            values[reference] = raw
    return values, shared_indices


def _owner_part_from_rels_path(rels_path: str) -> str | None:
    if rels_path == "_rels/.rels":
        return None
    parts = rels_path.split("/")
    assert len(parts) >= 2 and parts[-2] == "_rels" and parts[-1].endswith(
        ".rels"
    )
    return "/".join(parts[:-2] + [parts[-1][:-5]])


def _resolve_relationship_target(rels_path: str, target: str) -> str | None:
    if not target:
        return None
    owner = _owner_part_from_rels_path(rels_path)
    base = posixpath.dirname(owner) if owner else ""
    if target.startswith("/"):
        return target.lstrip("/")
    resolved = posixpath.normpath(posixpath.join(base, target)).lstrip("/")
    if resolved == ".." or resolved.startswith("../"):
        return None
    return resolved


def _assert_secure_nested_workbook(workbook_bytes: bytes) -> None:
    """Accept either sanitization or rejection, but never a tainted output."""

    with zipfile.ZipFile(io.BytesIO(workbook_bytes), "r") as archive:
        names = {name.replace("\\", "/") for name in archive.namelist()}
        lowered_names = {name.lower() for name in names}
        assert not any("/externallinks/" in name for name in lowered_names)
        assert not any(name.endswith("/connections.xml") for name in lowered_names)
        assert not any("/embeddings/" in name for name in lowered_names)
        assert not any("/activex/" in name for name in lowered_names)
        assert not any("vbaproject" in name for name in lowered_names)

        for name in sorted(names):
            if not name.endswith(".xml"):
                continue
            root = ET.fromstring(archive.read(name))
            assert not any(
                node.tag.rsplit("}", 1)[-1] == "f" for node in root.iter()
            ), f"formula survived in {name}"

        forbidden_type_fragments = (
            "externallink",
            "connections",
            "oleobject",
            "activex",
            "control",
            "vbaproject",
        )
        for rels_path in sorted(name for name in names if name.endswith(".rels")):
            root = ET.fromstring(archive.read(rels_path))
            for relation in root.iter():
                if relation.tag.rsplit("}", 1)[-1] != "Relationship":
                    continue
                relation_type = relation.attrib.get("Type", "").lower()
                assert not any(
                    fragment in relation_type for fragment in forbidden_type_fragments
                ), f"forbidden relationship survived in {rels_path}: {relation_type}"
                target = relation.attrib.get("Target", "")
                if relation.attrib.get("TargetMode", "").lower() == "external":
                    assert target.lower().startswith("https://"), (
                        f"unsafe external relationship survived in {rels_path}: {target}"
                    )
                    continue
                resolved = _resolve_relationship_target(rels_path, target)
                assert resolved in names, (
                    f"unresolved internal relationship survived in {rels_path}: {target}"
                )


def _mutate_or_assert_security_rejection(
    workbook_bytes: bytes,
    *,
    expected_error_tokens: tuple[str, ...],
) -> None:
    try:
        output = _mutate(workbook_bytes)
    except PhysicalAssemblyError as exc:
        message = str(exc).upper()
        assert any(token in message for token in expected_error_tokens), message
        return
    _assert_secure_nested_workbook(output)


def test_governed_shared_string_mutation_removes_unreferenced_sensitive_bytes() -> None:
    output = _mutate(_workbook_bytes())

    with zipfile.ZipFile(io.BytesIO(output), "r") as archive:
        part_bytes = {name: archive.read(name) for name in archive.namelist()}
        _, shared_strings = _shared_strings(archive)
        values, _ = _worksheet_cells(archive, shared_strings)

    assert values["A1"] == REPLACEMENT_TEXT
    assert all(
        SENSITIVE_TEXT.encode("utf-8") not in payload
        for payload in part_bytes.values()
    ), "the old governed string remains recoverable in a raw XLSX part"


def test_zero_replacement_workbook_is_still_sanitized_deterministically() -> None:
    source = _workbook_bytes()

    first = _mutate_governed_workbook(source, ())
    second = _mutate_governed_workbook(source, ())

    assert first == second
    assert first != source
    _assert_secure_nested_workbook(first)
    with zipfile.ZipFile(io.BytesIO(first), "r") as archive:
        _, shared_strings = _shared_strings(archive)
        values, _ = _worksheet_cells(archive, shared_strings)
    assert values == {
        "A1": SENSITIVE_TEXT,
        "A2": "Retained label",
        "A3": "Retained label",
        "A4": "Other label",
    }


def _zero_slot_template() -> PageTemplate:
    return PageTemplate(
        schema_version="1.0",
        page_id="zero-slot-workbook-page",
        package_sha256="a" * 64,
        slide_number=1,
        source_path="private/template.pptx",
        source_sha256="a" * 64,
        source_slide_sha256="b" * 64,
        page_role="content",
        category_names=("security-test",),
        style_cluster_id="security-test-style",
        deck_family_id="security-test-deck",
        theme_palette=("#000000",),
        capacity={"text_chars": 0, "items": 0, "images": 0},
        editability="native",
        certification="certified",
        visual_quality=1.0,
        structure={},
        slot_graph={},
        requires_customer_asset=False,
        media_retention_policy="no-page-media",
        governed_content_inventory={
            "complete": True,
            "content_slot_count": 0,
            "slots": [],
            "closure_metadata": {"workbook_part_count": 1},
        },
    )


def test_zero_slot_reachable_xlsx_is_sanitized_without_fact_authority() -> None:
    source_part = "ppt/embeddings/passive-book.xlsx"
    source = _workbook_bytes()
    graph = _SourceGraph(
        root_slide_name="ppt/slides/slide1.xml",
        slide_xml=b"<p:sld xmlns:p='p'/>",
        slide_sha="c" * 64,
        extra_parts={source_part: source},
    )
    slide = AssemblyTargetSlide(
        ordinal=1,
        page_template=_zero_slot_template(),
        bindings={},
        narrative_role="content",
        title="Security test",
        headline="Security test",
    )

    mutated, evidence = _prepare_governed_content_replacements(
        slide,
        graph,
        None,
        {},
    )

    assert evidence == []
    assert set(mutated) == {source_part}
    assert mutated[source_part] != source
    _assert_secure_nested_workbook(mutated[source_part])


def test_zero_slot_reachable_xlsm_is_rejected_fail_closed() -> None:
    source_part = "ppt/embeddings/passive-book.xlsm"
    graph = _SourceGraph(
        root_slide_name="ppt/slides/slide1.xml",
        slide_xml=b"<p:sld xmlns:p='p'/>",
        slide_sha="c" * 64,
        extra_parts={source_part: _workbook_bytes()},
    )
    slide = AssemblyTargetSlide(
        ordinal=1,
        page_template=_zero_slot_template(),
        bindings={},
        narrative_role="content",
        title="Security test",
        headline="Security test",
    )

    with pytest.raises(PhysicalAssemblyError, match=r"(?i)xlsm|macro|workbook"):
        _prepare_governed_content_replacements(slide, graph, None, {})


@pytest.mark.parametrize(
    "corrupt",
    (
        "root-to-worksheet",
        "duplicate-office-document",
        "workbook-root-namespace",
        "worksheet-root-namespace",
        "workbook-content-type",
        "sheet-relationship-missing",
        "worksheet-relationship-unbound",
    ),
)
def test_malformed_workbook_structure_fails_closed(corrupt: str) -> None:
    source = _workbook_bytes()
    updates: dict[str, bytes] = {}
    if corrupt == "root-to-worksheet":
        updates["_rels/.rels"] = _relationships(
            [
                (
                    "rId1",
                    f"{OFFICE_REL_NS}/officeDocument",
                    "xl/worksheets/sheet1.xml",
                    "",
                )
            ]
        )
    elif corrupt == "duplicate-office-document":
        updates["_rels/.rels"] = _relationships(
            [
                ("rId1", f"{OFFICE_REL_NS}/officeDocument", "xl/workbook.xml", ""),
                ("rId2", f"{OFFICE_REL_NS}/officeDocument", "xl/workbook.xml", ""),
            ]
        )
    elif corrupt == "workbook-root-namespace":
        updates["xl/workbook.xml"] = b'<workbook xmlns="urn:not-spreadsheetml"/>'
    elif corrupt == "worksheet-root-namespace":
        updates["xl/worksheets/sheet1.xml"] = (
            b'<worksheet xmlns="urn:not-spreadsheetml"><sheetData/></worksheet>'
        )
    elif corrupt == "workbook-content-type":
        updates["[Content_Types].xml"] = _content_types(
            [
                ("xl/workbook.xml", "application/xml"),
                (
                    "xl/worksheets/sheet1.xml",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml",
                ),
                (
                    "xl/sharedStrings.xml",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml",
                ),
            ]
        )
    elif corrupt == "sheet-relationship-missing":
        updates["xl/workbook.xml"] = (
            f'<workbook xmlns="{SPREADSHEET_NS}" xmlns:r="{OFFICE_REL_NS}">'
            '<sheets><sheet name="Data" sheetId="1" r:id="rId404"/></sheets>'
            "</workbook>"
        ).encode()
    elif corrupt == "worksheet-relationship-unbound":
        updates["xl/_rels/workbook.xml.rels"] = _relationships(
            [
                ("rId1", f"{OFFICE_REL_NS}/worksheet", "worksheets/sheet1.xml", ""),
                ("rId2", f"{OFFICE_REL_NS}/worksheet", "worksheets/sheet1.xml", ""),
                ("rId3", f"{OFFICE_REL_NS}/sharedStrings", "sharedStrings.xml", ""),
            ]
        )
    else:  # pragma: no cover - guards fixture maintenance
        raise AssertionError(corrupt)

    with pytest.raises(PhysicalAssemblyError, match="GOVERNED_WORKBOOK_SECURITY"):
        _mutate_governed_workbook(
            _rewrite_workbook_parts(source, updates=updates),
            (),
        )


@pytest.mark.parametrize(
    ("threat", "expected_error_tokens"),
    [
        ("formula", ("FORMULA",)),
        ("external-links", ("EXTERNAL", "LINK")),
        ("connections", ("CONNECTION",)),
        ("ole", ("OLE",)),
        ("activex", ("ACTIVEX", "CONTROL")),
        ("macro", ("MACRO", "VBA")),
        ("unsafe-external-relationship", ("UNSAFE", "EXTERNAL")),
        ("missing-internal-relationship", ("MISSING", "UNRESOLVED")),
    ],
    ids=[
        "formula",
        "external-links",
        "connections",
        "ole",
        "activex",
        "macro",
        "unsafe-external-relationship",
        "missing-internal-relationship",
    ],
)
def test_governed_workbook_never_emits_active_or_unresolved_nested_content(
    threat: str,
    expected_error_tokens: tuple[str, ...],
) -> None:
    _mutate_or_assert_security_rejection(
        _workbook_bytes(threat=threat),
        expected_error_tokens=expected_error_tokens,
    )


def test_governed_xlsm_part_is_rejected_fail_closed() -> None:
    source_part = "ppt/embeddings/governed-book.xlsm"
    record = _governed_record(source_part=source_part)
    template = PageTemplate(
        schema_version="1.0",
        page_id="xlsm-security-page",
        package_sha256="a" * 64,
        slide_number=1,
        source_path="private/template.pptx",
        source_sha256="a" * 64,
        source_slide_sha256="b" * 64,
        page_role="content",
        category_names=("security-test",),
        style_cluster_id="security-test-style",
        deck_family_id="security-test-deck",
        theme_palette=("#000000",),
        capacity={"text_chars": 0, "items": 0, "images": 0},
        editability="native",
        certification="certified",
        visual_quality=1.0,
        structure={},
        slot_graph={},
        requires_customer_asset=False,
        media_retention_policy="no-page-media",
        governed_content_inventory={
            "complete": True,
            "content_slot_count": 1,
            "slots": [record],
        },
    )
    slide = AssemblyTargetSlide(
        ordinal=1,
        page_template=template,
        bindings={},
        narrative_role="content",
        title="Security test",
        headline="Security test",
        governed_content_binding_specs={
            record["slot_id"]: TextBindingSpec(
                REPLACEMENT_TEXT,
                ("replacement-fact",),
                "auto",
            )
        },
    )
    graph = _SourceGraph(
        root_slide_name="ppt/slides/slide1.xml",
        slide_xml=b"<p:sld xmlns:p='p'/>",
        slide_sha="c" * 64,
        extra_parts={source_part: _workbook_bytes()},
    )
    fact_store = FactStore(
        schema_version="1.0",
        project=TrustedProject(
            title="Security test",
            objective=None,
            audience=None,
            language="en-US",
        ),
        sources=(FactSource("client-request", "request", "REQUEST.md"),),
        facts=(
            Fact(
                id="replacement-fact",
                kind="claim",
                text=REPLACEMENT_TEXT,
                language="en-US",
                source_id="client-request",
                locator="REQUEST.md#replacement",
                required=False,
            ),
        ),
        digest="d" * 64,
    )

    with pytest.raises(PhysicalAssemblyError, match=r"(?i)xlsm|macro|workbook"):
        _prepare_governed_content_replacements(slide, graph, fact_store, {})


def test_shared_string_compaction_remaps_repeated_indices_deterministically() -> None:
    source = _workbook_bytes()
    first = _mutate(source)
    second = _mutate(source)

    assert first == second
    with zipfile.ZipFile(io.BytesIO(first), "r") as archive:
        shared_root, shared_strings = _shared_strings(archive)
        values, indices = _worksheet_cells(archive, shared_strings)

    assert shared_strings == ["Retained label", "Other label"]
    assert shared_root.attrib.get("count") == "3"
    assert shared_root.attrib.get("uniqueCount") == "2"
    assert values == {
        "A1": REPLACEMENT_TEXT,
        "A2": "Retained label",
        "A3": "Retained label",
        "A4": "Other label",
    }
    assert indices == {"A2": 0, "A3": 0, "A4": 1}
