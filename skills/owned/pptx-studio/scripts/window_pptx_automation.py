#!/usr/bin/env python3
"""Conservative Windows PowerPoint COM helper for the window-pptx skill."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import shutil
import sys
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from window_pptx.cli import (
    build_dry_run_result,
    emit_result,
    parse_args as parse_cli_args,
)
from window_pptx.backends import BackendSelection, negotiate_backend
from window_pptx.agnes_direct import AgnesDirectClient
from window_pptx.com_diagnostics import (
    certify_powerpoint,
    doctor_powerpoint,
    validate_portable_certification_input,
)
from window_pptx.com_session import dispatch_powerpoint, macro_security
from window_pptx.deck_plan import compile_deck_plan, load_deck_plan
from window_pptx.brand import discover_installed_fonts, load_brand_spec
from window_pptx.errors import ComSessionError, OutputPolicyError, WindowPptxError
from window_pptx.generation import BriefGeneration, prepare_brief_generation
from window_pptx.design_quality import inspect_design_quality
from window_pptx.layouts import SlideSize
from window_pptx.models import CandidateResult, OutputPolicy, PowerPointHandle
from window_pptx.output_policy import calculate_export_size, validate_output_policy
from window_pptx.quality import (
    QualityGateError,
    QualityReport,
    RepairLog,
    write_quality_artifacts,
)
from window_pptx.quality_v2 import (
    QualityV2GateError,
    StageRepairPass,
    generation_quality_findings,
)
from window_pptx.quality_v3 import inspect_generation_quality_v3
from window_pptx.reference_quality import (
    assess_reference_grade_quality,
    write_reference_quality_report,
)
from window_pptx.render_plan import compile_render_plan, load_asset_bindings
from window_pptx.html_proof import write_html_proof
from window_pptx.libreoffice import LibreOfficeVerifier
from window_pptx.portable_runner import execute_portable_render_plan
from window_pptx.runner import execute_render_plan
from window_pptx.template_pack import (
    TemplatePack,
    adapt_template_pack,
    load_template_bindings,
    load_template_pack,
    write_adaptation_report,
)
from window_pptx.template_intelligence import (
    SlideBlueprint,
    TemplateSelectionPlan,
    load_registry_v3,
    selection_plan_from_payload,
    slide_blueprints_from_payload,
)
from window_pptx.page_template_library import (
    PageTemplateError,
    load_library_index,
    resolve_private_root,
)
from window_pptx.physical_assembly import (
    DEFAULT_MAX_OUTPUT_SIZE_BYTES,
    PhysicalAssemblyError,
    assemble_physical_deck,
    load_assembly_plan,
    resolve_project_file,
    write_assembly_report,
)
from window_pptx.physical_rule_qa import run_physical_rule_qa, write_rule_qa_report
from validate_window_pptx_v61_physical_report import validate_physical_report
from window_pptx.selection_materialization import (
    materialize_physical_selection,
)
from window_pptx.transaction import save_candidate
from window_pptx.weak_model import load_fact_store, normalize_brief_plan


MISSING = "<unavailable>"
MSO_FALSE = 0
MSO_TRUE = -1
PP_LAYOUT_BLANK = 12
MSO_TEXT_ORIENTATION_HORIZONTAL = 1
REQUEST_TEMPLATE = """# PowerPoint Request

## Goal

Describe the final deck, audience, and success outcome.

## Inputs

- Project folder:
- Template/source deck:
- Assets:
- Downloaded stock assets:
- Data:
- Notes/references:

## Output

- Output PPTX:
- Export PDF: yes/no
- Overwrite source deck: no

## Edit Requirements

1.
2.
3.

## Module Plan

List deck modules here and keep implementation detail in `MODULES.md`.

- cover:
- directory:
- section:
- body:
- comparison:
- timeline:
- awards:
- team:
- ending:

## Visual Constraints

- Aspect ratio:
- Brand colors:
- Fonts:
- Style direction:
- Master watermark:
- Layout density:
- Must preserve:
- Must avoid:

## Asset Search

- Use Pixabay: yes/no
- Search keywords:
- Image type: all/photo/illustration/vector
- Orientation: all/horizontal/vertical
- Use Iconify: yes/no
- Icon keywords:
- Icon set prefix: mdi/bi/lucide/etc.
- Icon color/size:
- Required source attribution in notes/logs: yes

## Preferred Plugins

- native PowerPoint COM only

## Macro Policy

- macros disabled

## Add-in Policy

- discovery only

## Acceptance Check

- Expected slide count:
- Required slide titles:
- Required assets/charts:
- Speaker notes required: yes/no
- PDF export required: yes/no
- Visual review required: yes/no
"""

MODULES_TEMPLATE = """# Module Plan

Use this file to manage deck-level modules before writing project-specific automation code.

## Module Vocabulary

- cover
- directory
- section
- body
- comparison
- timeline
- process
- data-chart
- awards
- team
- closing

## Module Table

| Module ID | Type | Target Slides | Purpose | Inputs | Visual Strategy | Script Function | QA Notes |
|---|---|---|---|---|---|---|---|
| M01 | cover | 1 |  |  |  | build_cover |  |
| M02 | body | 2-3 |  |  |  | build_body |  |

## Design System

- Theme:
- Primary color:
- Accent color:
- Title font:
- Body font:
- Master watermark:
- Reusable components:

## Asset Manifest

Keep downloaded or generated assets traceable:

| Asset | Source | License/Page URL | Used In | Notes |
|---|---|---|---|---|
|  |  |  |  |  |
"""

SLIDE_MAP_TEMPLATE = """# Slide Map

Use this file to classify the source deck before heavy edits.

## Role Vocabulary

- instruction
- material
- reference-result
- output
- cover
- directory
- section
- body
- ending

## Mapping

| Slide | Current Role | Target Role | Action | Assets Needed | Notes |
|---|---|---|---|---|---|
| 1 |  |  |  |  |  |
| 2 |  |  |  |  |  |

## Output Plan

- Slides to keep:
- Slides to rebuild:
- Slides to append:
- Reference-only slides:
"""

PROJECT_RUNNER_TEMPLATE = '''#!/usr/bin/env python3
"""Project-specific entrypoint for window-pptx automation.

Run this file from Windows Python when real PowerPoint COM work is needed.
Keep project-specific layout code here and reusable helpers in the installed
window-pptx skill script or copied project helpers.
"""

from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[2]


def main() -> None:
    print(f"Project runner placeholder: {PROJECT_DIR}")
    print("Replace this with project-specific PowerPoint COM build steps.")


if __name__ == "__main__":
    main()
'''


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return parse_cli_args(argv)


def die(message: str, code: int = 1) -> None:
    print(f"window-pptx: {message}", file=sys.stderr)
    raise SystemExit(code)


def require_windows() -> None:
    if platform.system().lower() != "windows":
        die(
            "PowerPoint COM automation requires native Windows. "
            "Run this script from PowerShell/CMD with desktop PowerPoint installed."
        )


def import_win32com() -> Any:
    try:
        import win32com.client  # type: ignore
    except ImportError as exc:
        die("Missing pywin32. Install with: py -m pip install pywin32")
        raise exc
    return win32com.client


def maybe_clear_com_cache() -> None:
    cache_root = Path(tempfile.gettempdir()) / "gen_py"
    if cache_root.exists():
        shutil.rmtree(cache_root, ignore_errors=True)


def resolve_path(base: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if not path.is_absolute():
        path = base / path
    return path.resolve()


def read_request(project_dir: Path, request_arg: str) -> tuple[Path, str]:
    request_path = resolve_path(project_dir, request_arg)
    if request_path is None:
        die("Request path could not be resolved.")
    if not request_path.exists():
        die(f"Request file not found: {request_path}")
    return request_path, request_path.read_text(encoding="utf-8", errors="replace")


def choose_template(project_dir: Path, explicit_template: str | None) -> Path | None:
    explicit = resolve_path(project_dir, explicit_template)
    if explicit:
        if not explicit.exists():
            die(f"Template/source deck not found: {explicit}")
        return explicit

    preferred_names = [
        "template.pptx",
        "template.pptm",
        "template.potx",
        "template.potm",
        "source.pptx",
        "source.pptm",
    ]
    for name in preferred_names:
        candidate = project_dir / name
        if candidate.exists():
            return candidate.resolve()

    candidates: list[Path] = []
    for pattern in ("*.pptx", "*.pptm", "*.potx", "*.potm"):
        candidates.extend(project_dir.glob(pattern))

    if len(candidates) == 1:
        return candidates[0].resolve()
    if len(candidates) > 1:
        die(
            "Multiple PowerPoint candidates found. Pass --template explicitly: "
            + ", ".join(str(path.name) for path in sorted(candidates))
        )
    return None


def init_project_workspace(project_dir: Path) -> dict[str, Any]:
    created_dirs: list[str] = []
    created_files: list[str] = []

    for rel in [
        "assets",
        "assets/downloads",
        "assets/downloads/pixabay",
        "assets/downloads/iconify",
        "data",
        "notes",
        "output",
        ".window-pptx",
        ".window-pptx/media",
        ".window-pptx/scripts",
        ".window-pptx/generated_assets",
        ".window-pptx/exports",
        ".window-pptx/audits",
        ".window-pptx/temp",
        ".window-pptx/logs",
        ".window-pptx/cache",
    ]:
        path = project_dir / rel
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(path))

    request_path = project_dir / "REQUEST.md"
    if not request_path.exists():
        request_path.write_text(REQUEST_TEMPLATE, encoding="utf-8")
        created_files.append(str(request_path))

    slide_map_path = project_dir / "SLIDE-MAP.md"
    if not slide_map_path.exists():
        slide_map_path.write_text(SLIDE_MAP_TEMPLATE, encoding="utf-8")
        created_files.append(str(slide_map_path))

    modules_path = project_dir / "MODULES.md"
    if not modules_path.exists():
        modules_path.write_text(MODULES_TEMPLATE, encoding="utf-8")
        created_files.append(str(modules_path))

    runner_path = project_dir / ".window-pptx" / "scripts" / "run_project.py"
    if not runner_path.exists():
        runner_path.write_text(PROJECT_RUNNER_TEMPLATE, encoding="utf-8")
        created_files.append(str(runner_path))

    return {"project_dir": str(project_dir), "created_dirs": created_dirs, "created_files": created_files}


def parse_slide_spec(spec: str) -> list[int]:
    result: list[int] = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if "-" in chunk:
            left, right = chunk.split("-", 1)
            start = int(left.strip())
            end = int(right.strip())
            if end < start:
                start, end = end, start
            result.extend(range(start, end + 1))
        else:
            result.append(int(chunk))
    seen: set[int] = set()
    ordered: list[int] = []
    for item in result:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def ascii_temp_copy_path(project_dir: Path, source: Path) -> Path:
    return project_dir / ".window-pptx" / "temp" / f"deck_temp_ascii{source.suffix}"


def ensure_ascii_temp_copy(project_dir: Path, source: Path) -> Path:
    target = ascii_temp_copy_path(project_dir, source)
    temp_dir = target.parent
    temp_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def extract_media_from_deck(deck_path: Path, media_dir: Path) -> dict[str, Any]:
    media_dir.mkdir(parents=True, exist_ok=True)
    extracted: list[str] = []
    with zipfile.ZipFile(deck_path) as zf:
        for name in zf.namelist():
            if not name.startswith("ppt/media/") or name.endswith("/"):
                continue
            target = media_dir / Path(name).name
            target.write_bytes(zf.read(name))
            extracted.append(str(target))
    return {"deck": str(deck_path), "media_dir": str(media_dir), "count": len(extracted), "files": extracted}


def export_slides_to_png(presentation: Any, slide_numbers: list[int], export_dir: Path) -> dict[str, Any]:
    export_dir.mkdir(parents=True, exist_ok=True)
    exported: list[str] = []
    max_count = int(presentation.Slides.Count)
    export_width, export_height = calculate_export_size(
        float(presentation.PageSetup.SlideWidth),
        float(presentation.PageSetup.SlideHeight),
    )
    for slide_number in slide_numbers:
        if slide_number < 1 or slide_number > max_count:
            continue
        target = export_dir / f"slide-{slide_number}.png"
        presentation.Slides(slide_number).Export(
            str(target),
            "PNG",
            export_width,
            export_height,
        )
        exported.append(str(target))
    return {"export_dir": str(export_dir), "slides": slide_numbers, "files": exported}


def export_all_slides_to_png(presentation: Any, export_dir: Path) -> dict[str, Any]:
    return export_slides_to_png(
        presentation,
        list(range(1, int(presentation.Slides.Count) + 1)),
        export_dir,
    )


def export_quality_v2_previews(
    presentation: Any,
    audit_dir: Path,
) -> dict[str, Any]:
    """Export a fresh pre-save PNG set that cannot reuse stale evidence."""

    preview_root = audit_dir / "quality-v2-previews"
    preview_root.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="pre-save-", dir=preview_root))
    return export_all_slides_to_png(presentation, run_dir)


EXCEL_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
OD_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
ET.register_namespace("", EXCEL_NS)

OBJECTIVE_INTAKE_FIELDS = {
    "TemplateID",
    "Category",
    "SourcePPTX",
    "SlideNo",
    "SlideCountInDeck",
    "PreviewPath",
    "PreviewUpdatedAt",
    "VisibleTextSummary",
    "ShapeCount",
    "ImageCount",
    "TableCount",
    "ChartCount",
    "IngestStatus",
    "IngestIssue",
    "LastAutoIngestedAt",
}

MANUAL_FIELDS = {
    "HumanReviewedTags",
    "ReviewStatus",
    "Reviewer",
    "LastReviewedDate",
    "Notes",
}

AI_RECOMMENDATION_FIELDS = [
    "VisualLayoutSummary",
    "ContentSlots",
    "StructureTag",
    "AIInitialTags",
    "BestFor",
    "AvoidFor",
    "MatchKeywords",
    "AIRecommendationReason",
    "SuggestedAdaptation",
    "RequiredInputs",
    "RiskNotes",
    "QualityScore",
    "ReuseComplexity",
    "EditabilityRisk",
    "CompositeScore",
    "AIQualityReason",
    "AutoRecommendStatus",
]

V2_LIBRARY_FIELDS = [
    "PreviewUpdatedAt",
    "ShapeCount",
    "ImageCount",
    "TableCount",
    "ChartCount",
    "IngestStatus",
    "IngestIssue",
    "LastAutoIngestedAt",
    *AI_RECOMMENDATION_FIELDS,
    "ManualLock",
]

CATEGORY_RULES = {
    "封面模板": {
        "structure": "封面标题",
        "slots": "标题, 副标题, 日期/Logo 可选",
        "tags": "封面模板, 开场页, 标题页",
        "best_for": "封面页、开场页、主题页",
        "avoid_for": "正文页、数据密集页、多模块说明页",
        "keywords": "封面, 标题, 开场, 主题, cover, title",
        "adaptation": "替换主标题、副标题和品牌信息，并统一当前 deck 主色。",
        "required": "主标题；副标题、日期、Logo 可选",
    },
    "一段内容": {
        "structure": "单段正文",
        "slots": "标题, 单段正文",
        "tags": "一段内容, 单段正文, 介绍页",
        "best_for": "简短介绍页、观点页、摘要页、一段正文说明",
        "avoid_for": "长文、多模块并列、复杂数据页",
        "keywords": "一段内容, 正文, 介绍, 摘要, paragraph, body",
        "adaptation": "替换标题和正文，正文过长时先压缩为一段核心观点。",
        "required": "标题；一段 60-140 字左右正文",
    },
    "人物介绍": {
        "structure": "人物履历",
        "slots": "姓名, 职位/身份, 简介, 照片可选",
        "tags": "人物介绍, 个人介绍, 团队介绍",
        "best_for": "个人介绍、团队成员介绍、嘉宾/讲师介绍",
        "avoid_for": "纯数据页、流程页、无人物主体的内容页",
        "keywords": "人物, 个人介绍, 团队, 简历, profile, bio",
        "adaptation": "替换姓名、身份、简介和头像，并保持人物信息层级清晰。",
        "required": "姓名；身份/职位；简介；头像可选",
    },
    "六段内容": {
        "structure": "六项卡片",
        "slots": "标题, 六个要点/模块",
        "tags": "六段内容, 六项并列, 模块页",
        "best_for": "6 个要点、6 个模块、6 项能力或 6 步说明",
        "avoid_for": "少于 4 项的内容、长段正文、单一重点页",
        "keywords": "六段, 六个要点, 六项, 模块, 6 points, six modules",
        "adaptation": "把内容压缩成 6 个平行短句，并统一每项标题长度。",
        "required": "标题；6 个并列要点或模块名称",
    },
}


def template_library_paths(project_dir: Path, args: argparse.Namespace) -> dict[str, Path]:
    skill_root = Path(__file__).resolve().parents[1]
    library_root = skill_root / "templates" / "template-library"
    preview_dir = resolve_path(project_dir, args.export_dir) if args.export_dir else library_root / "previews"
    if preview_dir is None:
        preview_dir = library_root / "previews"
    return {
        "skill_root": skill_root,
        "library_root": library_root,
        "reference_dir": library_root / "reference",
        "workbook_path": library_root / "template-library-review.xlsx",
        "preview_dir": preview_dir,
    }


def discover_template_category_decks(reference_dir: Path) -> list[Path]:
    if not reference_dir.exists():
        die(f"Template library reference directory not found: {reference_dir}")
    decks = sorted(path for path in reference_dir.glob("*.pptx") if not path.name.startswith("~$"))
    if not decks:
        die(f"No template category PPTX files found in: {reference_dir}")
    return decks


def category_from_deck(deck_path: Path) -> str:
    return deck_path.stem


def make_template_id(category: str, slide_no: int) -> str:
    return f"{category}::S{slide_no:03d}"


def col_name(index: int) -> str:
    name = ""
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def col_index(cell_ref: str) -> int:
    letters = "".join(ch for ch in cell_ref if ch.isalpha())
    index = 0
    for letter in letters:
        index = index * 26 + ord(letter.upper()) - 64
    return index


def cell_ref(column: int, row: int) -> str:
    return f"{col_name(column)}{row}"


def xlsx_text_from_cell(cell: ET.Element, shared_strings: list[str]) -> str:
    ns = f"{{{EXCEL_NS}}}"
    formula = cell.find(f"{ns}f")
    if formula is not None and formula.text:
        return "=" + formula.text
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        text_node = cell.find(f"{ns}is/{ns}t")
        return text_node.text if text_node is not None and text_node.text is not None else ""
    value_node = cell.find(f"{ns}v")
    if value_node is None or value_node.text is None:
        return ""
    if cell_type == "s":
        try:
            return shared_strings[int(value_node.text)]
        except Exception:
            return ""
    return value_node.text


def load_shared_strings(zf: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in zf.namelist():
        return []
    root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
    ns = f"{{{EXCEL_NS}}}"
    strings: list[str] = []
    for si in root.findall(f"{ns}si"):
        parts = [node.text or "" for node in si.findall(f".//{ns}t")]
        strings.append("".join(parts))
    return strings


def worksheet_target_for_sheet(zf: zipfile.ZipFile, sheet_name: str) -> str:
    workbook = ET.fromstring(zf.read("xl/workbook.xml"))
    rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    ns = f"{{{EXCEL_NS}}}"
    rel_attr = f"{{{OD_REL_NS}}}id"
    rel_id = None
    for sheet in workbook.findall(f"{ns}sheets/{ns}sheet"):
        if sheet.attrib.get("name") == sheet_name:
            rel_id = sheet.attrib.get(rel_attr)
            break
    if not rel_id:
        die(f"Workbook sheet not found: {sheet_name}")
    for rel in rels.findall(f"{{{REL_NS}}}Relationship"):
        if rel.attrib.get("Id") == rel_id:
            target = rel.attrib.get("Target", "")
            return target if target.startswith("xl/") else "xl/" + target.lstrip("/")
    die(f"Workbook relationship not found for sheet: {sheet_name}")


def read_xlsx_sheet_rows(workbook_path: Path, sheet_name: str) -> tuple[list[str], list[dict[str, str]], ET.Element]:
    with zipfile.ZipFile(workbook_path) as zf:
        target = worksheet_target_for_sheet(zf, sheet_name)
        shared_strings = load_shared_strings(zf)
        root = ET.fromstring(zf.read(target))
    ns = f"{{{EXCEL_NS}}}"
    sheet_data = root.find(f"{ns}sheetData")
    if sheet_data is None:
        return [], [], root
    matrix: dict[int, dict[int, str]] = {}
    for row in sheet_data.findall(f"{ns}row"):
        row_index = int(row.attrib.get("r", "0") or 0)
        matrix[row_index] = {}
        for cell in row.findall(f"{ns}c"):
            ref = cell.attrib.get("r", "A1")
            matrix[row_index][col_index(ref)] = xlsx_text_from_cell(cell, shared_strings)
    headers = [matrix.get(1, {}).get(i, "") for i in range(1, max(matrix.get(1, {}) or {0: ''}) + 1)]
    headers = [header for header in headers if header]
    rows: list[dict[str, str]] = []
    for row_index in sorted(index for index in matrix if index > 1):
        row_values = matrix[row_index]
        row_dict = {header: row_values.get(i + 1, "") for i, header in enumerate(headers)}
        if any(value != "" for value in row_dict.values()):
            rows.append(row_dict)
    return headers, rows, root


def xlsx_cell(column: int, row: int, value: str, style: str | None = None) -> ET.Element:
    cell = ET.Element(f"{{{EXCEL_NS}}}c", {"r": cell_ref(column, row)})
    if style:
        cell.set("s", style)
    if value.startswith("="):
        formula = ET.SubElement(cell, f"{{{EXCEL_NS}}}f")
        formula.text = value[1:]
        return cell
    cell.set("t", "inlineStr")
    inline = ET.SubElement(cell, f"{{{EXCEL_NS}}}is")
    text_node = ET.SubElement(inline, f"{{{EXCEL_NS}}}t")
    if value.strip() != value or "\n" in value:
        text_node.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")
    text_node.text = value
    return cell


def build_library_sheet_xml(headers: list[str], rows: list[dict[str, str]], old_root: ET.Element) -> bytes:
    ns = f"{{{EXCEL_NS}}}"
    root = ET.Element(f"{ns}worksheet")
    for tag in ("sheetViews", "cols"):
        existing = old_root.find(f"{ns}{tag}")
        if existing is not None:
            root.append(existing)
    sheet_data = ET.SubElement(root, f"{ns}sheetData")
    header_row = ET.SubElement(sheet_data, f"{ns}row", {"r": "1"})
    for column, header in enumerate(headers, start=1):
        header_row.append(xlsx_cell(column, 1, header, "1"))
    for row_index, row_dict in enumerate(rows, start=2):
        row = ET.SubElement(sheet_data, f"{ns}row", {"r": str(row_index)})
        for column, header in enumerate(headers, start=1):
            row.append(xlsx_cell(column, row_index, str(row_dict.get(header, ""))))
    merge_cells = old_root.find(f"{ns}mergeCells")
    if merge_cells is not None:
        root.append(merge_cells)
    auto_filter = ET.Element(f"{ns}autoFilter", {"ref": f"A1:{col_name(len(headers))}{max(len(rows) + 1, 1)}"})
    root.append(auto_filter)
    data_validations = old_root.find(f"{ns}dataValidations")
    if data_validations is not None:
        root.append(data_validations)
    page_margins = old_root.find(f"{ns}pageMargins")
    if page_margins is not None:
        root.append(page_margins)
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def write_xlsx_sheet_rows_preserving_workbook(workbook_path: Path, sheet_name: str, headers: list[str], rows: list[dict[str, str]], old_root: ET.Element) -> None:
    with zipfile.ZipFile(workbook_path) as source:
        target = worksheet_target_for_sheet(source, sheet_name)
        replacement = build_library_sheet_xml(headers, rows, old_root)
        temp_path = workbook_path.with_suffix(workbook_path.suffix + ".tmp")
        with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as dest:
            for item in source.infolist():
                if item.filename == target:
                    dest.writestr(item, replacement)
                else:
                    dest.writestr(item, source.read(item.filename))
    temp_path.replace(workbook_path)


def is_manual_locked(row: dict[str, str]) -> bool:
    return str(row.get("ManualLock", "")).strip().lower() in {"yes", "是", "true", "1", "locked"}


def is_usage_field(header: str) -> bool:
    lowered = header.lower()
    return any(token in lowered for token in ["usage", "used", "selection", "selected", "final", "feedback", "count", "rate"])


def merge_library_rows(headers: list[str], existing_rows: list[dict[str, str]], intake_rows: list[dict[str, str]]) -> tuple[list[str], list[dict[str, str]], dict[str, int]]:
    for field in V2_LIBRARY_FIELDS:
        if field not in headers:
            headers.append(field)
    for row in existing_rows:
        for header in headers:
            row.setdefault(header, "")
    rows_by_id = {row.get("TemplateID", ""): row for row in existing_rows if row.get("TemplateID")}
    stats = {"rows_added": 0, "rows_updated": 0, "rows_locked_objective_only": 0}
    for intake in intake_rows:
        template_id = intake.get("TemplateID", "")
        if template_id in rows_by_id:
            existing = rows_by_id[template_id]
            locked = is_manual_locked(existing)
            for header in headers:
                if header not in intake:
                    continue
                is_objective = header in OBJECTIVE_INTAKE_FIELDS
                if not is_objective and (header in MANUAL_FIELDS or is_usage_field(header)):
                    continue
                if locked and not is_objective:
                    continue
                existing[header] = str(intake.get(header, ""))
            if locked:
                stats["rows_locked_objective_only"] += 1
            else:
                stats["rows_updated"] += 1
        else:
            new_row = {header: str(intake.get(header, "")) for header in headers}
            existing_rows.append(new_row)
            rows_by_id[template_id] = new_row
            stats["rows_added"] += 1
    return headers, existing_rows, stats


def apply_library_formulas(headers: list[str], rows: list[dict[str, str]]) -> None:
    required = {"UseCount", "SelectedCount", "FinalUsedCount", "SelectedRate", "FinalUsedRate", "QualityScore", "CompositeScore"}
    if not required.issubset(set(headers)):
        return
    columns = {header: col_name(index) for index, header in enumerate(headers, start=1)}
    for index, row in enumerate(rows, start=2):
        use_count = f"{columns['UseCount']}{index}"
        selected_count = f"{columns['SelectedCount']}{index}"
        final_used_count = f"{columns['FinalUsedCount']}{index}"
        quality_score = f"{columns['QualityScore']}{index}"
        selected_rate = f"{columns['SelectedRate']}{index}"
        final_used_rate = f"{columns['FinalUsedRate']}{index}"
        row["SelectedRate"] = f"=IF({use_count}=0,0,{selected_count}/{use_count})"
        row["FinalUsedRate"] = f"=IF({use_count}=0,0,{final_used_count}/{use_count})"
        row["CompositeScore"] = f"={quality_score}*0.5+{selected_rate}*0.2+{final_used_rate}*0.2"


def summarize_visible_text(texts: list[str], limit: int = 400) -> str:
    summary = re.sub(r"\s+", " ", " ".join(text.strip() for text in texts if text.strip())).strip()
    if len(summary) > limit:
        return summary[: limit - 3] + "..."
    return summary


def safe_shape_text(shape: Any) -> str:
    try:
        if not shape.HasTextFrame:
            return ""
        if not shape.TextFrame.HasText:
            return ""
        return str(shape.TextFrame.TextRange.Text).strip()
    except Exception:
        return ""


def truthy_com_attr(shape: Any, attr: str) -> bool:
    try:
        return bool(getattr(shape, attr))
    except Exception:
        return False


def inspect_template_slide(slide: Any) -> dict[str, Any]:
    texts: list[str] = []
    shape_count = 0
    image_count = 0
    table_count = 0
    chart_count = 0
    for shape in iter_slide_shapes(slide):
        shape_count += 1
        text = safe_shape_text(shape)
        if text:
            texts.append(text)
        try:
            if int(get_attr(shape, "Type")) == 13:
                image_count += 1
        except Exception:
            pass
        if truthy_com_attr(shape, "HasTable"):
            table_count += 1
        if truthy_com_attr(shape, "HasChart"):
            chart_count += 1
    return {
        "VisibleTextSummary": summarize_visible_text(texts),
        "ShapeCount": shape_count,
        "ImageCount": image_count,
        "TableCount": table_count,
        "ChartCount": chart_count,
    }


def relative_to_skill(path: Path, skill_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(skill_root.resolve())).replace("\\", "/")
    except Exception:
        return str(path)


def export_template_preview(slide: Any, preview_dir: Path, category: str, slide_no: int) -> Path:
    preview_dir.mkdir(parents=True, exist_ok=True)
    category_stem = sanitize_filename(category, "")
    category_key = hashlib.sha1(category.encode("utf-8")).hexdigest()[:8]
    stem = f"{category_stem}-{category_key}" if category_stem else category_key
    target = preview_dir / f"{stem}__S{slide_no:03d}.png"
    slide.Export(str(target), "PNG", 1600, 900)
    return target


def risk_level(shape_count: int, image_count: int, table_count: int, chart_count: int) -> tuple[str, str, str]:
    complexity_label = "低"
    complexity_score = "1"
    if shape_count >= 35 or table_count or chart_count:
        complexity_label = "高"
        complexity_score = "5"
    elif shape_count >= 18 or image_count >= 3:
        complexity_label = "中"
        complexity_score = "3"
    risk = "低"
    if chart_count or table_count or image_count >= 5:
        risk = "高"
    elif image_count >= 2 or shape_count >= 30:
        risk = "中"
    return complexity_label, complexity_score, risk


def build_initial_intake_fields(category: str, objective: dict[str, Any], issue: str, now: str) -> dict[str, str]:
    rule = CATEGORY_RULES.get(category, {})
    shape_count = int(objective.get("ShapeCount", 0) or 0)
    image_count = int(objective.get("ImageCount", 0) or 0)
    table_count = int(objective.get("TableCount", 0) or 0)
    chart_count = int(objective.get("ChartCount", 0) or 0)
    complexity_label, complexity_score, risk = risk_level(shape_count, image_count, table_count, chart_count)
    risk_notes: list[str] = []
    if not objective.get("VisibleTextSummary"):
        risk_notes.append("未检测到可见文本；推荐前应查看预览确认文本槽位。")
    if table_count:
        risk_notes.append("包含表格，复用时需要准备结构化数据。")
    if chart_count:
        risk_notes.append("包含图表，复用时需要准备可替换数据。")
    if issue:
        risk_notes.append(issue)
    quality_score = "4"
    if complexity_label == "高" or risk == "高":
        quality_score = "3"
    if issue:
        quality_score = "2"
    status = "NeedsReview" if issue else "AutoRecommendable"
    visual = f"基于类别、可见文本和对象统计自动初标；形状 {shape_count} 个，图片 {image_count} 个，表格 {table_count} 个，图表 {chart_count} 个，复杂度 {complexity_label}。"
    if not rule:
        visual += " 未命中专用类别规则，推荐前应人工查看预览。"
    return {
        "VisualLayoutSummary": visual,
        "ContentSlots": rule.get("slots", "标题, 内容槽位待确认"),
        "StructureTag": rule.get("structure", category),
        "AIInitialTags": rule.get("tags", category),
        "BestFor": rule.get("best_for", f"{category} 类页面需求"),
        "AvoidFor": rule.get("avoid_for", "类别不匹配或信息结构差异较大的页面"),
        "MatchKeywords": rule.get("keywords", category),
        "AIRecommendationReason": f"类别为 {category}，结构与该类模板库来源匹配；可见文本和对象统计已完成入库。",
        "SuggestedAdaptation": rule.get("adaptation", "替换标题、正文和视觉元素，并对齐当前 deck 主色。"),
        "RequiredInputs": rule.get("required", "标题和页面核心内容"),
        "RiskNotes": " ".join(risk_notes),
        "QualityScore": quality_score,
        "ReuseComplexity": complexity_score,
        "EditabilityRisk": risk,
        "AIQualityReason": f"初始评分来自类别匹配、形状复杂度、图片/表格/图表数量和入库状态；当前状态：{status}。",
        "AutoRecommendStatus": status,
        "LastAutoIngestedAt": now,
    }


def open_template_presentation(app: Any, deck_path: Path) -> Any:
    validate_output_policy(
        OutputPolicy(
            source_path=deck_path,
            output_path=None,
            no_output_deck=True,
        )
    )
    with macro_security(app):
        return app.Presentations.Open(
            str(deck_path),
            MSO_TRUE,
            MSO_TRUE,
            MSO_FALSE,
        )


def intake_template_library(app: Any, project_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    paths = template_library_paths(project_dir, args)
    workbook_path = paths["workbook_path"]
    if not workbook_path.exists():
        die(f"Template library workbook not found: {workbook_path}")
    decks = discover_template_category_decks(paths["reference_dir"])
    now = datetime.now().isoformat(timespec="seconds")
    intake_rows: list[dict[str, str]] = []
    issues: list[dict[str, str]] = []
    previews_written = 0
    slides_scanned = 0
    for deck in decks:
        category = category_from_deck(deck)
        presentation = None
        try:
            presentation = open_template_presentation(app, deck)
            slide_count = int(presentation.Slides.Count)
            for slide_no in range(1, slide_count + 1):
                slides_scanned += 1
                slide = presentation.Slides(slide_no)
                issue = ""
                objective = {"VisibleTextSummary": "", "ShapeCount": 0, "ImageCount": 0, "TableCount": 0, "ChartCount": 0}
                try:
                    objective.update(inspect_template_slide(slide))
                except Exception as exc:
                    issue = f"基础解析失败：{exc}"
                preview_path = ""
                preview_updated_at = ""
                try:
                    preview = export_template_preview(slide, paths["preview_dir"], category, slide_no)
                    preview_path = relative_to_skill(preview, paths["skill_root"])
                    preview_updated_at = now
                    previews_written += 1
                except Exception as exc:
                    export_issue = f"预览导出失败：{exc}"
                    issue = f"{issue} {export_issue}".strip()
                fields = build_initial_intake_fields(category, objective, issue, now)
                source_pptx = relative_to_skill(deck, paths["skill_root"])
                row = {
                    "TemplateID": make_template_id(category, slide_no),
                    "Category": category,
                    "SourcePPTX": source_pptx,
                    "SlideNo": str(slide_no),
                    "SlideCountInDeck": str(slide_count),
                    "PreviewPath": preview_path,
                    "PreviewUpdatedAt": preview_updated_at,
                    "VisibleTextSummary": str(objective.get("VisibleTextSummary", "")),
                    "ShapeCount": str(objective.get("ShapeCount", "")),
                    "ImageCount": str(objective.get("ImageCount", "")),
                    "TableCount": str(objective.get("TableCount", "")),
                    "ChartCount": str(objective.get("ChartCount", "")),
                    "IngestStatus": "issue" if issue else "ok",
                    "IngestIssue": issue,
                    "ManualLock": "",
                    **fields,
                }
                intake_rows.append(row)
                if issue:
                    issues.append({"template_id": row["TemplateID"], "issue": issue})
        except Exception as exc:
            issue = {"deck": str(deck), "issue": f"PPTX 打开或扫描失败：{exc}"}
            issues.append(issue)
        finally:
            if presentation is not None:
                try:
                    presentation.Close()
                except Exception:
                    pass
    headers, rows, old_root = read_xlsx_sheet_rows(workbook_path, "Library")
    headers, merged_rows, stats = merge_library_rows(headers, rows, intake_rows)
    apply_library_formulas(headers, merged_rows)
    write_xlsx_sheet_rows_preserving_workbook(workbook_path, "Library", headers, merged_rows, old_root)
    return {
        "library_root": str(paths["library_root"]),
        "reference_dir": str(paths["reference_dir"]),
        "workbook": str(workbook_path),
        "preview_dir": str(paths["preview_dir"]),
        "decks_scanned": len(decks),
        "slides_scanned": slides_scanned,
        "previews_written": previews_written,
        "issues": issues,
        **stats,
    }


def rgb(r: int, g: int, b: int) -> int:
    return int(r) + (int(g) << 8) + (int(b) << 16)


def sanitize_filename(value: str, fallback: str = "asset") -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-")
    return clean[:96] or fallback


def read_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def append_asset_manifest(project_dir: Path, rows: list[dict[str, Any]]) -> Path:
    manifest_path = project_dir / ".window-pptx" / "asset_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest = read_json_file(manifest_path, {"assets": []})
    if not isinstance(manifest, dict):
        manifest = {"assets": []}
    assets = manifest.setdefault("assets", [])
    if not isinstance(assets, list):
        manifest["assets"] = []
        assets = manifest["assets"]
    assets.extend(rows)
    manifest["updated_at"] = datetime.now().isoformat(timespec="seconds")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def pixabay_search(args: argparse.Namespace, project_dir: Path) -> dict[str, Any]:
    api_key = os.environ.get("PIXABAY_API_KEY")
    if not api_key:
        die("Missing PIXABAY_API_KEY. Set it in the Windows/user environment; do not commit it.")
    if args.image_per_page < 3 or args.image_per_page > 200:
        die("--image-per-page must be between 3 and 200.")

    params: dict[str, Any] = {
        "key": api_key,
        "q": args.search_images,
        "lang": args.image_lang,
        "image_type": args.image_type,
        "orientation": args.image_orientation,
        "safesearch": "false" if args.unsafe_image_search else "true",
        "order": args.image_order,
        "page": args.image_page,
        "per_page": args.image_per_page,
    }
    if args.image_category:
        params["category"] = args.image_category
    if args.image_colors:
        params["colors"] = args.image_colors

    safe_params = {key: value for key, value in params.items() if key != "key"}
    request = Request(
        "https://pixabay.com/api/?" + urlencode(params),
        headers={"User-Agent": "window-pptx-skill/1.0"},
    )
    with urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    hits = payload.get("hits", [])
    normalized_hits: list[dict[str, Any]] = []
    for hit in hits:
        normalized_hits.append(
            {
                "id": hit.get("id"),
                "tags": hit.get("tags"),
                "type": hit.get("type"),
                "pageURL": hit.get("pageURL"),
                "previewURL": hit.get("previewURL"),
                "webformatURL": hit.get("webformatURL"),
                "largeImageURL": hit.get("largeImageURL"),
                "fullHDURL": hit.get("fullHDURL"),
                "imageURL": hit.get("imageURL"),
                "vectorURL": hit.get("vectorURL"),
                "imageWidth": hit.get("imageWidth"),
                "imageHeight": hit.get("imageHeight"),
                "downloads": hit.get("downloads"),
                "likes": hit.get("likes"),
                "user": hit.get("user"),
                "user_id": hit.get("user_id"),
            }
        )

    result = {
        "source": "pixabay",
        "query": args.search_images,
        "params": safe_params,
        "total": payload.get("total"),
        "totalHits": payload.get("totalHits"),
        "hits": normalized_hits,
        "notes": [
            "Do not hotlink Pixabay result URLs in the final deck.",
            "Download selected assets locally and keep pageURL/user attribution in asset_manifest.json.",
        ],
    }
    cache_dir = project_dir / ".window-pptx" / "cache" / "pixabay"
    cache_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = cache_dir / f"search-{stamp}-{sanitize_filename(args.search_images)}.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["manifest_path"] = str(target)
    return result


def download_image(project_dir: Path, url: str, source_row: dict[str, Any] | None = None) -> dict[str, Any]:
    downloads_dir = project_dir / "assets" / "downloads" / "pixabay"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    stem = sanitize_filename(str((source_row or {}).get("id") or Path(url).stem or "pixabay-image"))
    suffix = Path(url.split("?", 1)[0]).suffix
    if suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp", ".svg"}:
        suffix = ".jpg"
    target = downloads_dir / f"{stem}{suffix}"
    counter = 2
    while target.exists():
        target = downloads_dir / f"{stem}-{counter}{suffix}"
        counter += 1

    request = Request(url, headers={"User-Agent": "window-pptx-skill/1.0"})
    with urlopen(request, timeout=60) as response:
        target.write_bytes(response.read())

    row = {
        "provider": "pixabay",
        "local_path": str(target),
        "downloaded_at": datetime.now().isoformat(timespec="seconds"),
        "source_url": url,
        "pageURL": (source_row or {}).get("pageURL"),
        "user": (source_row or {}).get("user"),
        "tags": (source_row or {}).get("tags"),
        "license_note": "Pixabay API asset. Keep source page/user in the project manifest.",
    }
    manifest_path = append_asset_manifest(project_dir, [row])
    return {"downloaded": row, "asset_manifest": str(manifest_path)}


def normalize_icon_id(value: str) -> tuple[str, str]:
    clean = value.strip().lstrip("/")
    if ":" in clean:
        prefix, name = clean.split(":", 1)
    elif "/" in clean:
        prefix, name = clean.split("/", 1)
        name = name.removesuffix(".svg")
    else:
        die("Iconify icon id must look like bi:tag-fill or bi/tag-fill.svg.")
    prefix = prefix.strip().lower()
    name = name.strip().removesuffix(".svg")
    if not prefix or not name:
        die("Iconify icon id must include both prefix and icon name.")
    return prefix, name


def iconify_svg_url(icon_id: str, args: argparse.Namespace) -> str:
    prefix, name = normalize_icon_id(icon_id)
    params: dict[str, Any] = {}
    if args.icon_color:
        params["color"] = args.icon_color
    if args.icon_width:
        params["width"] = args.icon_width
    if args.icon_height:
        params["height"] = args.icon_height
    if args.icon_flip:
        params["flip"] = args.icon_flip
    if args.icon_rotate:
        params["rotate"] = args.icon_rotate
    url = f"https://api.iconify.design/{quote(prefix)}/{quote(name)}.svg"
    if params:
        url += "?" + urlencode(params)
    return url


def normalize_icon_prefix(value: str) -> str:
    prefix = value.strip().lower().removesuffix(":").removesuffix("/").removesuffix("-")
    if not prefix:
        die("Iconify icon prefix cannot be empty.")
    return prefix


def fetch_iconify_search(query: str, limit: int, prefix: str | None = None) -> dict[str, Any]:
    params: dict[str, Any] = {"query": query, "limit": limit}
    if prefix:
        params["prefix"] = prefix
    request = Request(
        "https://api.iconify.design/search?" + urlencode(params),
        headers={"User-Agent": "window-pptx-skill/1.0"},
    )
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def iconify_search(args: argparse.Namespace, project_dir: Path) -> dict[str, Any]:
    if args.icon_limit < 1 or args.icon_limit > 999:
        die("--icon-limit must be between 1 and 999.")

    prefixes = [normalize_icon_prefix(prefix) for prefix in args.icon_prefix]
    payloads: list[dict[str, Any]] = []
    icons: list[str] = []

    if prefixes:
        for prefix in prefixes:
            payload = fetch_iconify_search(args.search_icons, args.icon_limit, prefix)
            payloads.append({"prefix": prefix, "total": payload.get("total"), "collections": payload.get("collections", {})})
            icons.extend(str(icon) for icon in payload.get("icons", []) if icon)
    else:
        payload = fetch_iconify_search(args.search_icons, args.icon_limit)
        payloads.append({"total": payload.get("total"), "collections": payload.get("collections", {})})
        icons.extend(str(icon) for icon in payload.get("icons", []) if icon)

    deduped_icons = list(dict.fromkeys(icons))[: args.icon_limit]
    result = {
        "source": "iconify",
        "query": args.search_icons,
        "params": {"query": args.search_icons, "limit": args.icon_limit, "prefixes": prefixes},
        "icons": deduped_icons,
        "total": len(deduped_icons),
        "api_payloads": payloads,
        "notes": [
            "Download selected SVG icons locally before inserting them into a deck.",
            "Keep icon id, API URL, color, dimensions, flip, and rotate parameters in asset_manifest.json.",
        ],
    }
    cache_dir = project_dir / ".window-pptx" / "cache" / "iconify"
    cache_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = cache_dir / f"search-{stamp}-{sanitize_filename(args.search_icons)}.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["manifest_path"] = str(target)
    return result


def download_icon(project_dir: Path, icon_id: str, args: argparse.Namespace) -> dict[str, Any]:
    prefix, name = normalize_icon_id(icon_id)
    downloads_dir = project_dir / "assets" / "downloads" / "iconify" / prefix
    downloads_dir.mkdir(parents=True, exist_ok=True)
    target = downloads_dir / f"{sanitize_filename(name, 'icon')}.svg"
    counter = 2
    while target.exists():
        target = downloads_dir / f"{sanitize_filename(name, 'icon')}-{counter}.svg"
        counter += 1

    url = iconify_svg_url(f"{prefix}:{name}", args)
    request = Request(url, headers={"User-Agent": "window-pptx-skill/1.0"})
    with urlopen(request, timeout=30) as response:
        target.write_bytes(response.read())

    row = {
        "provider": "iconify",
        "local_path": str(target),
        "downloaded_at": datetime.now().isoformat(timespec="seconds"),
        "icon_id": f"{prefix}:{name}",
        "source_url": url,
        "params": {
            "color": args.icon_color,
            "width": args.icon_width,
            "height": args.icon_height,
            "flip": args.icon_flip,
            "rotate": args.icon_rotate,
        },
        "license_note": "Iconify API SVG asset. Keep icon id and source URL in the project manifest.",
    }
    manifest_path = append_asset_manifest(project_dir, [row])
    return {"downloaded": row, "asset_manifest": str(manifest_path)}


def add_master_watermark(presentation: Any, text: str, opacity: float) -> dict[str, Any]:
    master = presentation.SlideMaster
    width = float(presentation.PageSetup.SlideWidth)
    height = float(presentation.PageSetup.SlideHeight)
    shape_name = "AIMAGICIAN_MASTER_WATERMARK"
    clamped_opacity = max(0.0, min(1.0, opacity))

    try:
        for index in range(int(master.Shapes.Count), 0, -1):
            shape = master.Shapes(index)
            if str(get_attr(shape, "Name")) == shape_name:
                shape.Delete()
    except Exception:
        pass

    box = master.Shapes.AddTextbox(
        MSO_TEXT_ORIENTATION_HORIZONTAL,
        width * 0.08,
        height * 0.38,
        width * 0.84,
        height * 0.16,
    )
    box.Name = shape_name
    box.Rotation = -28
    box.TextFrame.TextRange.Text = text
    font = box.TextFrame.TextRange.Font
    font.Size = max(36, int(width / 13))
    font.Bold = MSO_TRUE
    gray = int(255 - (145 * clamped_opacity))
    font.Color.RGB = rgb(gray, gray, gray)
    try:
        box.Fill.Visible = MSO_FALSE
        box.Line.Visible = MSO_FALSE
    except Exception:
        pass
    return {
        "watermark": text,
        "shape_name": shape_name,
        "location": "SlideMaster",
        "opacity_requested": opacity,
        "opacity_used": clamped_opacity,
        "note": "Implemented as light gray master text for broad PowerPoint COM compatibility.",
    }


def iter_slide_shapes(slide: Any) -> list[Any]:
    shapes: list[Any] = []
    try:
        count = int(slide.Shapes.Count)
    except Exception:
        return shapes
    for index in range(1, count + 1):
        try:
            shapes.append(slide.Shapes(index))
        except Exception:
            continue
    return shapes


def shape_text(shape: Any) -> str:
    try:
        if not shape.HasTextFrame:
            return ""
        if not shape.TextFrame.HasText:
            return ""
        return str(shape.TextFrame.TextRange.Text)
    except Exception:
        return ""


def audit_presentation(presentation: Any, project_dir: Path) -> dict[str, Any]:
    fonts: set[str] = set()
    slides: list[dict[str, Any]] = []
    animation_rows: list[dict[str, Any]] = []

    for slide_index in range(1, int(presentation.Slides.Count) + 1):
        slide = presentation.Slides(slide_index)
        texts: list[str] = []
        picture_count = 0
        shape_count = 0
        for shape in iter_slide_shapes(slide):
            shape_count += 1
            text = shape_text(shape).strip()
            if text:
                texts.append(text[:200])
                try:
                    fonts.add(str(shape.TextFrame.TextRange.Font.Name))
                except Exception:
                    pass
            try:
                if int(get_attr(shape, "Type")) == 13:
                    picture_count += 1
            except Exception:
                pass

        try:
            sequence = slide.TimeLine.MainSequence
            for effect_index in range(1, int(sequence.Count) + 1):
                effect = sequence(effect_index)
                animation_rows.append(
                    {
                        "slide": slide_index,
                        "index": effect_index,
                        "shape": str(get_attr(effect.Shape, "Name")),
                        "effect_type": get_attr(effect, "EffectType"),
                        "trigger_type": get_attr(effect.Timing, "TriggerType"),
                        "duration": get_attr(effect.Timing, "Duration"),
                        "delay": get_attr(effect.Timing, "TriggerDelayTime"),
                    }
                )
        except Exception:
            pass

        slides.append(
            {
                "slide": slide_index,
                "name": str(get_attr(slide, "Name")),
                "shape_count": shape_count,
                "picture_count": picture_count,
                "text_samples": texts[:5],
            }
        )

    result = {
        "audited_at": datetime.now().isoformat(timespec="seconds"),
        "slide_count": int(presentation.Slides.Count),
        "page_size": {
            "width": float(presentation.PageSetup.SlideWidth),
            "height": float(presentation.PageSetup.SlideHeight),
        },
        "fonts_seen": sorted(font for font in fonts if font and font != MISSING),
        "slides": slides,
        "animations": animation_rows,
    }
    audit_dir = project_dir / ".window-pptx" / "audits"
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_path = audit_dir / "deck_audit.json"
    audit_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["audit_path"] = str(audit_path)
    return result


def get_attr(obj: Any, name: str) -> Any:
    try:
        value = getattr(obj, name)
    except Exception:
        return MISSING
    try:
        if callable(value):
            return MISSING
    except Exception:
        return MISSING
    return value


def boolish(value: Any) -> Any:
    if value in (True, False):
        return bool(value)
    if value == MSO_TRUE:
        return True
    if value == MSO_FALSE:
        return False
    return value


def collection_items(collection: Any) -> list[Any]:
    try:
        count = int(collection.Count)
    except Exception:
        return []
    items = []
    for index in range(1, count + 1):
        try:
            items.append(collection.Item(index))
        except Exception:
            continue
    return items


def list_com_addins(app: Any) -> list[dict[str, Any]]:
    try:
        collection = app.COMAddIns
    except Exception:
        return []

    rows: list[dict[str, Any]] = []
    for item in collection_items(collection):
        rows.append(
            {
                "description": str(get_attr(item, "Description")),
                "prog_id": str(get_attr(item, "ProgID")),
                "guid": str(get_attr(item, "Guid")),
                "connect": boolish(get_attr(item, "Connect")),
            }
        )
    return rows


def list_powerpoint_addins(app: Any) -> list[dict[str, Any]]:
    try:
        collection = app.AddIns
    except Exception:
        return []

    rows: list[dict[str, Any]] = []
    for item in collection_items(collection):
        rows.append(
            {
                "name": str(get_attr(item, "Name")),
                "full_name": str(get_attr(item, "FullName")),
                "loaded": boolish(get_attr(item, "Loaded")),
            }
        )
    return rows


def import_probe_modules() -> tuple[Any, Any, Any]:
    try:
        import pythoncom  # type: ignore
        import win32com.client.dynamic  # type: ignore
        import winreg  # type: ignore
    except ImportError as exc:
        die(f"Missing Windows COM probe dependency: {exc}")
        raise exc
    return pythoncom, win32com.client.dynamic, winreg


def registry_access(winreg: Any, view_flag: int = 0) -> int:
    return int(getattr(winreg, "KEY_READ", 0)) | int(view_flag)


def registry_view_specs(winreg: Any) -> list[tuple[str, int]]:
    specs = [
        ("64", int(getattr(winreg, "KEY_WOW64_64KEY", 0))),
        ("32", int(getattr(winreg, "KEY_WOW64_32KEY", 0))),
    ]
    available = [(name, flag) for name, flag in specs if flag]
    return available or [("default", 0)]


def office_registry_view_specs(
    winreg: Any, root_name: str
) -> list[tuple[str, int]]:
    # HKCU\Software is shared across WOW64 views.  Applying both flags there
    # returns the same physical key twice, so inventory it once.
    if root_name == "HKCU":
        return [("shared", 0)]
    return registry_view_specs(winreg)


def registry_get(
    winreg: Any,
    root: Any,
    path: str,
    value_name: str = "",
    *,
    view_flag: int = 0,
) -> Any:
    try:
        with winreg.OpenKey(root, path, 0, registry_access(winreg, view_flag)) as key:
            value, _ = winreg.QueryValueEx(key, value_name)
            return value
    except Exception:
        return None


def registry_key_values(
    winreg: Any,
    root: Any,
    path: str,
    *,
    view_flag: int = 0,
) -> dict[str, Any] | None:
    try:
        with winreg.OpenKey(root, path, 0, registry_access(winreg, view_flag)) as key:
            values: dict[str, Any] = {}
            index = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, index)
                    values[name or "(Default)"] = value
                    index += 1
                except OSError:
                    break
            return values
    except Exception:
        return None


def clsid_registry_view_snapshot(
    winreg: Any,
    progid: str,
    view_name: str,
    view_flag: int,
) -> dict[str, Any]:
    clsid = registry_get(
        winreg,
        winreg.HKEY_CLASSES_ROOT,
        rf"{progid}\CLSID",
        view_flag=view_flag,
    )
    result: dict[str, Any] = {
        "progid": progid,
        "registry_view": view_name,
        "clsid": clsid,
    }
    if not clsid:
        return result

    clsid_key = rf"CLSID\{clsid}"
    result.update(
        {
            "friendly_name": registry_get(
                winreg, winreg.HKEY_CLASSES_ROOT, clsid_key, view_flag=view_flag
            ),
            "typelib": registry_get(
                winreg,
                winreg.HKEY_CLASSES_ROOT,
                rf"{clsid_key}\TypeLib",
                view_flag=view_flag,
            ),
            "version": registry_get(
                winreg,
                winreg.HKEY_CLASSES_ROOT,
                rf"{clsid_key}\Version",
                view_flag=view_flag,
            ),
            "local_server32": registry_get(
                winreg,
                winreg.HKEY_CLASSES_ROOT,
                rf"{clsid_key}\LocalServer32",
                view_flag=view_flag,
            ),
            "inproc_server32": registry_get(
                winreg,
                winreg.HKEY_CLASSES_ROOT,
                rf"{clsid_key}\InprocServer32",
                view_flag=view_flag,
            ),
        }
    )
    return result


def clsid_registry_snapshot(winreg: Any, progid: str) -> dict[str, Any]:
    views = {
        view_name: clsid_registry_view_snapshot(
            winreg, progid, view_name, view_flag
        )
        for view_name, view_flag in registry_view_specs(winreg)
    }
    preferred = next(
        (snapshot for snapshot in views.values() if snapshot.get("clsid")),
        next(iter(views.values())),
    )
    return {**preferred, "views": views}


def office_addin_registry_snapshot(winreg: Any, progid: str) -> list[dict[str, Any]]:
    rows = []
    roots = [
        ("HKCU", winreg.HKEY_CURRENT_USER),
        ("HKLM", winreg.HKEY_LOCAL_MACHINE),
    ]
    path = rf"Software\Microsoft\Office\PowerPoint\Addins\{progid}"
    for root_name, root in roots:
        for view_name, view_flag in office_registry_view_specs(winreg, root_name):
            values = registry_key_values(
                winreg, root, path, view_flag=view_flag
            )
            if values is not None:
                rows.append(
                    {
                        "root": root_name,
                        "registry_view": view_name,
                        "path": path,
                        "values": values,
                    }
                )
    return rows


def import_registry_module() -> Any:
    try:
        import winreg  # type: ignore
    except ImportError as exc:
        die(f"Missing Windows registry dependency: {exc}")
        raise exc
    return winreg


def list_registered_com_addins() -> list[dict[str, Any]]:
    """List PowerPoint COM add-ins from registration without starting Office."""

    winreg = import_registry_module()
    roots = [
        ("HKCU", winreg.HKEY_CURRENT_USER),
        ("HKLM", winreg.HKEY_LOCAL_MACHINE),
    ]
    base_path = r"Software\Microsoft\Office\PowerPoint\Addins"
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for root_name, root in roots:
        for view_name, view_flag in office_registry_view_specs(winreg, root_name):
            try:
                with winreg.OpenKey(
                    root, base_path, 0, registry_access(winreg, view_flag)
                ) as key:
                    index = 0
                    progids: list[str] = []
                    while True:
                        try:
                            progids.append(str(winreg.EnumKey(key, index)))
                            index += 1
                        except OSError:
                            break
            except OSError:
                continue
            for progid in progids:
                identity = (root_name, view_name, progid.lower())
                if identity in seen:
                    continue
                seen.add(identity)
                path = rf"{base_path}\{progid}"
                values = registry_key_values(
                    winreg, root, path, view_flag=view_flag
                ) or {}
                clsid = clsid_registry_view_snapshot(
                    winreg, progid, view_name, view_flag
                ).get("clsid")
                load_behavior = values.get("LoadBehavior")
                rows.append(
                    {
                        "description": str(
                            values.get("Description")
                            or values.get("FriendlyName")
                            or progid
                        ),
                        "prog_id": progid,
                        "guid": str(clsid or MISSING),
                        "connect": None,
                        "load_behavior": load_behavior,
                        "manifest": values.get("Manifest"),
                        "source": "registry",
                        "root": root_name,
                        "registry_view": view_name,
                        "path": path,
                    }
                )
    return rows


def invoke_kind_name(pythoncom: Any, value: int) -> str:
    names = {
        pythoncom.INVOKE_FUNC: "method",
        pythoncom.INVOKE_PROPERTYGET: "property_get",
        pythoncom.INVOKE_PROPERTYPUT: "property_put",
        pythoncom.INVOKE_PROPERTYPUTREF: "property_putref",
    }
    return names.get(value, str(value))


def type_kind_name(pythoncom: Any, value: int) -> str:
    names = {
        pythoncom.TKIND_ENUM: "enum",
        pythoncom.TKIND_RECORD: "record",
        pythoncom.TKIND_MODULE: "module",
        pythoncom.TKIND_INTERFACE: "interface",
        pythoncom.TKIND_DISPATCH: "dispatch",
        pythoncom.TKIND_COCLASS: "coclass",
        pythoncom.TKIND_ALIAS: "alias",
        pythoncom.TKIND_UNION: "union",
    }
    return names.get(value, str(value))


def member_flags(pythoncom: Any, value: int) -> list[str]:
    mapping = {
        "restricted": getattr(pythoncom, "FUNCFLAG_FRESTRICTED", 1),
        "source": getattr(pythoncom, "FUNCFLAG_FSOURCE", 2),
        "bindable": getattr(pythoncom, "FUNCFLAG_FBINDABLE", 4),
        "request_edit": getattr(pythoncom, "FUNCFLAG_FREQUESTEDIT", 8),
        "display_bind": getattr(pythoncom, "FUNCFLAG_FDISPLAYBIND", 16),
        "default_bind": getattr(pythoncom, "FUNCFLAG_FDEFAULTBIND", 32),
        "hidden": getattr(pythoncom, "FUNCFLAG_FHIDDEN", 64),
        "uses_get_last_error": getattr(pythoncom, "FUNCFLAG_FUSESGETLASTERROR", 128),
        "default_collelem": getattr(pythoncom, "FUNCFLAG_FDEFAULTCOLLELEM", 256),
        "uidefault": getattr(pythoncom, "FUNCFLAG_FUIDEFAULT", 512),
        "nonbrowsable": getattr(pythoncom, "FUNCFLAG_FNONBROWSABLE", 1024),
        "replaceable": getattr(pythoncom, "FUNCFLAG_FREPLACEABLE", 2048),
        "immediate_bind": getattr(pythoncom, "FUNCFLAG_FIMMEDIATEBIND", 4096),
    }
    return [name for name, bit in mapping.items() if value & bit]


def inspect_typeinfo_from_dispatch(pythoncom: Any, obj: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "available": False,
        "methods": [],
        "properties": [],
        "variables": [],
        "errors": [],
    }

    try:
        typeinfo = obj._oleobj_.GetTypeInfo()
    except Exception as exc:
        result["errors"].append(f"GetTypeInfo failed: {exc}")
        return result

    try:
        typeattr = typeinfo.GetTypeAttr()
        result["available"] = True
        result["guid"] = str(typeattr.iid)
        result["type_kind"] = type_kind_name(pythoncom, typeattr.typekind)
        result["function_count"] = int(typeattr.cFuncs)
        result["variable_count"] = int(typeattr.cVars)
    except Exception as exc:
        result["errors"].append(f"GetTypeAttr failed: {exc}")
        return result

    try:
        documentation = typeinfo.GetDocumentation(-1)
        result["documentation"] = {
            "name": documentation[0],
            "doc": documentation[1],
            "help_context": documentation[2],
            "help_file": documentation[3],
        }
    except Exception as exc:
        result["errors"].append(f"GetDocumentation failed: {exc}")

    for index in range(int(result.get("function_count", 0))):
        try:
            desc = typeinfo.GetFuncDesc(index)
            names = typeinfo.GetNames(desc.memid)
            row = {
                "memid": int(desc.memid),
                "name": names[0] if names else f"memid_{desc.memid}",
                "args": names[1:],
                "invoke_kind": invoke_kind_name(pythoncom, desc.invkind),
                "param_count": len(desc.args),
                "optional_param_count": int(desc.cParamsOpt),
                "flags": member_flags(pythoncom, int(desc.wFuncFlags)),
            }
            if row["invoke_kind"] == "method":
                result["methods"].append(row)
            else:
                result["properties"].append(row)
        except Exception as exc:
            result["errors"].append(f"GetFuncDesc[{index}] failed: {exc}")

    for index in range(int(result.get("variable_count", 0))):
        try:
            desc = typeinfo.GetVarDesc(index)
            names = typeinfo.GetNames(desc.memid)
            result["variables"].append(
                {
                    "memid": int(desc.memid),
                    "name": names[0] if names else f"var_{desc.memid}",
                }
            )
        except Exception as exc:
            result["errors"].append(f"GetVarDesc[{index}] failed: {exc}")

    return result


def probe_direct_dispatch(dynamic: Any, pythoncom: Any, progid: str) -> dict[str, Any]:
    result: dict[str, Any] = {"progid": progid, "created": False}
    try:
        obj = dynamic.Dispatch(progid)
        result["created"] = True
        result["typeinfo"] = inspect_typeinfo_from_dispatch(pythoncom, obj)
    except Exception as exc:
        result["error"] = str(exc)
    return result


def probe_addin_object(app: Any, pythoncom: Any, progid: str) -> dict[str, Any]:
    result: dict[str, Any] = {"progid": progid, "has_object": False}
    try:
        addin = app.COMAddIns.Item(progid)
        result["description"] = str(get_attr(addin, "Description"))
        result["connect"] = boolish(get_attr(addin, "Connect"))
        result["guid"] = str(get_attr(addin, "Guid"))
        obj = addin.Object
        if obj is None:
            result["object_is_none"] = True
            return result
        result["has_object"] = True
        result["typeinfo"] = inspect_typeinfo_from_dispatch(pythoncom, obj)
    except Exception as exc:
        result["error"] = str(exc)
    return result


def probe_plugin_apis(app: Any, progids: list[str]) -> dict[str, Any]:
    """Inspect registration only; live dispatch can load or block third-party code."""

    del app
    winreg = import_registry_module()
    return {
        "mode": "registry_only",
        "probed_progids": progids,
        "registry": {progid: clsid_registry_snapshot(winreg, progid) for progid in progids},
        "office_addin_registry": {
            progid: office_addin_registry_snapshot(winreg, progid) for progid in progids
        },
        "direct_dispatch": {
            progid: {
                "skipped": True,
                "reason": "Live COM dispatch is disabled in safe inspection mode.",
            }
            for progid in progids
        },
        "addin_object": {
            progid: {
                "skipped": True,
                "reason": "PowerPoint startup and add-in Object access are disabled in safe inspection mode.",
            }
            for progid in progids
        },
        "notes": [
            "This probe reads registry metadata only and does not start PowerPoint.",
            "Live type information is intentionally unavailable in safe mode.",
            "It does not invoke business methods exposed by the add-ins.",
        ],
    }


def open_or_create_presentation(app: Any, template: Path | None, visible: bool) -> Any:
    with_window = MSO_TRUE if visible else MSO_FALSE
    with macro_security(app):
        if template:
            return app.Presentations.Open(
                str(template),
                MSO_TRUE,
                MSO_TRUE,
                with_window,
            )
        return app.Presentations.Add(with_window)


def truncate_lines(text: str, max_lines: int = 14, max_chars: int = 1100) -> str:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    summary = "\n".join(lines[:max_lines])
    if len(summary) > max_chars:
        summary = summary[: max_chars - 3] + "..."
    return summary or "REQUEST.md was empty."


def add_request_summary_slide(presentation: Any, request_text: str, template: Path | None) -> None:
    slide_count = int(presentation.Slides.Count)
    slide = presentation.Slides.Add(slide_count + 1, PP_LAYOUT_BLANK)

    title = slide.Shapes.AddTextbox(
        MSO_TEXT_ORIENTATION_HORIZONTAL,
        48,
        36,
        620,
        52,
    )
    title.TextFrame.TextRange.Text = "Request Summary"
    title.TextFrame.TextRange.Font.Size = 30
    title.TextFrame.TextRange.Font.Bold = MSO_TRUE

    body = slide.Shapes.AddTextbox(
        MSO_TEXT_ORIENTATION_HORIZONTAL,
        48,
        110,
        820,
        380,
    )
    template_line = f"Template: {template.name}" if template else "Template: new blank deck"
    body.TextFrame.TextRange.Text = template_line + "\n\n" + truncate_lines(request_text)
    body.TextFrame.TextRange.Font.Size = 16

    footer = slide.Shapes.AddTextbox(
        MSO_TEXT_ORIENTATION_HORIZONTAL,
        48,
        505,
        820,
        36,
    )
    footer.TextFrame.TextRange.Text = (
        "Generated by window-pptx helper at "
        + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    footer.TextFrame.TextRange.Font.Size = 10


def candidate_result_metadata(result: CandidateResult) -> dict[str, Any]:
    """Convert transactional evidence to the JSON-compatible facade shape."""

    return {
        "output_path": str(result.output_path),
        "promoted": result.promoted,
        "candidate_path": str(result.candidate_path) if result.candidate_path else None,
        "source_hash_before": result.source_hash_before,
        "source_hash_after": result.source_hash_after,
        "validation_steps": list(result.validation_steps),
        "cleanup_errors": list(result.cleanup_errors),
    }


def save_outputs(
    presentation: Any,
    app: Any,
    policy: OutputPolicy,
    export_pdf: bool,
) -> tuple[dict[str, str], dict[str, Any]]:
    """Transactionally save compatible outputs plus validation evidence."""

    result = save_candidate(
        presentation,
        app,
        policy,
        export_pdf=export_pdf,
    )
    outputs = {"pptx": str(result.output_path)}
    if export_pdf:
        outputs["pdf"] = str(result.output_path.with_suffix(".pdf"))
    return outputs, candidate_result_metadata(result)


def print_addins(addins: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(addins, ensure_ascii=False, indent=2))
        return

    print("PowerPoint COM Add-ins:")
    for row in addins["com_addins"]:
        print(
            f"- {row.get('description')} | ProgID={row.get('prog_id')} "
            f"| GUID={row.get('guid')} | Connect={row.get('connect')}"
        )
    if not addins["com_addins"]:
        print("- none")

    print("\nPowerPoint AddIns:")
    for row in addins["powerpoint_addins"]:
        print(
            f"- {row.get('name')} | FullName={row.get('full_name')} "
            f"| Loaded={row.get('loaded')}"
        )
    if not addins["powerpoint_addins"]:
        print("- none")


def read_ooxml_slide_size(template: Path | None) -> SlideSize | None:
    """Read slide dimensions without starting PowerPoint; invalid packages fall back."""

    if template is None:
        return None
    try:
        with zipfile.ZipFile(template) as archive:
            root = ET.fromstring(archive.read("ppt/presentation.xml"))
        node = root.find("{http://schemas.openxmlformats.org/presentationml/2006/main}sldSz")
        if node is None:
            return None
        width = int(node.attrib["cx"]) / 914400
        height = int(node.attrib["cy"]) / 914400
        if not all(1 <= value <= 56 for value in (width, height)):
            return None
        return SlideSize(width, height)
    except (KeyError, OSError, ValueError, ET.ParseError, zipfile.BadZipFile):
        return None


def write_brief_generation_artifacts(
    generation: BriefGeneration,
    audit_dir: Path,
    post_render_repair_passes: Sequence[StageRepairPass] = (),
) -> dict[str, str]:
    """Persist the fact-safe narrative and direction decisions beside QA evidence."""

    audit_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "narrative_plan": audit_dir / "narrative-plan.json",
        "visual_plan": audit_dir / "visual-plan.json",
        "asset_plan": audit_dir / "asset-plan.json",
        "asset_materialization": audit_dir / "asset-materialization.json",
        "composition_plan": audit_dir / "composition-plan.json",
        "quality_report_v3": audit_dir / "quality-report.v3.json",
        "generation_manifest": audit_dir / "generation-manifest.json",
        "repair_log_v2": audit_dir / "repair-log.v2.json",
    }
    if generation.template_selection_plan is not None:
        artifacts["template_selection_plan"] = (
            audit_dir / "template-selection-plan.json"
        )
        artifacts["slide_blueprints"] = audit_dir / "slide-blueprints.json"
        artifacts["candidate_materialization"] = (
            audit_dir / "candidate-materialization-report.json"
        )
    artifacts["narrative_plan"].write_text(
        json.dumps(
            generation.compilation.narrative.to_dict(),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    artifacts["visual_plan"].write_text(
        json.dumps(
            generation.visual_plan.to_dict(), ensure_ascii=False, indent=2
        )
        + "\n",
        encoding="utf-8",
    )
    artifacts["asset_plan"].write_text(
        json.dumps(
            generation.asset_plan.to_dict(), ensure_ascii=False, indent=2
        )
        + "\n",
        encoding="utf-8",
    )
    artifacts["asset_materialization"].write_text(
        json.dumps(
            generation.asset_materialization.to_dict(),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    artifacts["composition_plan"].write_text(
        json.dumps(
            generation.composition_plan.to_dict(),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if generation.template_selection_plan is not None:
        artifacts["template_selection_plan"].write_text(
            json.dumps(
                generation.template_selection_plan.to_dict(),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        artifacts["slide_blueprints"].write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "blueprints": [
                        item.to_dict() for item in generation.slide_blueprints
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        artifacts["candidate_materialization"].write_text(
            json.dumps(
                (
                    generation.candidate_materialization.to_dict()
                    if generation.candidate_materialization is not None
                    else None
                ),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    artifacts["quality_report_v3"].write_text(
        json.dumps(
            inspect_generation_quality_v3(generation).to_dict(),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    if generation.direction is not None:
        artifacts["direction_decision"] = audit_dir / "direction-decision.json"
        artifacts["direction_decision"].write_text(
            json.dumps(
                generation.direction.to_dict(),
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    artifacts["generation_manifest"].write_text(
        json.dumps(
            generation.to_dict(include_render_plan=False),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    repair_passes = [
        {
            "stage": item.stage,
            "before_vector": list(item.before_vector),
            "after_vector": list(item.after_vector),
            "accepted": item.accepted,
            "rolled_back": item.rolled_back,
            "failure_code": item.failure_code,
        }
        for item in generation.pre_render_repair_passes
    ]
    for item in post_render_repair_passes[:1]:
        repair_passes.append(
            {
                "stage": item.stage,
                "before_vector": list(item.before_vector),
                "after_vector": list(item.after_vector),
                "accepted": item.accepted,
                "rolled_back": item.rolled_back,
                "failure_code": item.failure_code,
            }
        )
    artifacts["repair_log_v2"].write_text(
        json.dumps(
            {"schema_version": "2.0", "passes": repair_passes[:2]},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {key: str(value) for key, value in artifacts.items()}


def main(
    argv: Sequence[str] | None = None,
    *,
    com_client: Any | None = None,
) -> int:
    args = parse_args(argv)
    project_dir = Path(args.project_dir).expanduser().resolve(strict=False)
    output_path = resolve_path(project_dir, args.output)
    if output_path is None:
        die("Output path could not be resolved.")

    template: Path | None = None
    prepared_compiled: dict[str, Any] | None = None
    prepared_render_plan = None
    prepared_render_size: SlideSize | None = None
    prepared_asset_bindings = {}
    prepared_brief_generation: BriefGeneration | None = None
    prepared_normalized_brief: dict[str, Any] | None = None
    prepared_normalization_changes: tuple[str, ...] = ()
    prepared_brand_spec_path: Path | None = None
    prepared_asset_manifest_path: Path | None = None
    prepared_backend: BackendSelection | None = None
    prepared_template_pack: TemplatePack | None = None
    prepared_template_bindings: dict[str, str] | None = None
    prepared_template_selection: TemplateSelectionPlan | None = None
    prepared_slide_blueprints: tuple[SlideBlueprint, ...] = ()
    if args.render_template_pack:
        binding_path = resolve_path(project_dir, args.template_bindings)
        if binding_path is None:
            die("TemplatePack binding path could not be resolved.")
        pack_identifier: str | Path = args.template_pack
        pack_path = resolve_path(project_dir, args.template_pack)
        if pack_path is not None and pack_path.is_file():
            pack_identifier = pack_path
        prepared_template_pack = load_template_pack(pack_identifier)
        binding_pack_id, prepared_template_bindings = load_template_bindings(
            binding_path
        )
        if binding_pack_id != prepared_template_pack.id:
            die(
                "TemplatePack binding id does not match the selected pack: "
                f"{binding_pack_id} != {prepared_template_pack.id}"
            )
        if args.template_selection_plan:
            selection_path = resolve_path(
                project_dir, args.template_selection_plan
            )
            blueprint_path = resolve_path(project_dir, args.slide_blueprints)
            if (
                selection_path is None
                or blueprint_path is None
                or not selection_path.is_file()
                or not blueprint_path.is_file()
            ):
                die("Template selection sidecar path is missing")
            prepared_template_selection = selection_plan_from_payload(
                json.loads(selection_path.read_text(encoding="utf-8"))
            )
            prepared_slide_blueprints = slide_blueprints_from_payload(
                json.loads(blueprint_path.read_text(encoding="utf-8"))
            )
            registry = load_registry_v3()
            spine = registry.spines.get(prepared_template_selection.spine_id)
            if (
                spine is None
                or spine.pack.v1_pack.id != prepared_template_pack.id
            ):
                die(
                    "Template selection spine does not match --template-pack"
                )
        template = prepared_template_pack.template_path
        validate_output_policy(
            OutputPolicy(
                source_path=template,
                output_path=output_path,
                dry_run=args.dry_run,
                no_output_deck=args.no_output_deck,
                allow_overwrite=False,
            )
        )
        if args.no_output_deck:
            die("--render-template-pack requires an output deck")
    elif args.compile_deck_plan or args.render_deck_plan:
        deck_plan_path = resolve_path(project_dir, args.deck_plan)
        if deck_plan_path is None:
            die("DeckPlan path could not be resolved.")
        deck_plan = load_deck_plan(deck_plan_path)
        if args.compile_deck_plan:
            prepared_compiled = compile_deck_plan(deck_plan)
        else:
            if not project_dir.exists():
                die(f"Project folder not found: {project_dir}")
            template = choose_template(project_dir, args.template)
            preflight_policy = OutputPolicy(
                source_path=template,
                output_path=output_path,
                dry_run=args.dry_run,
                no_output_deck=args.no_output_deck,
                allow_overwrite=args.allow_overwrite,
            )
            validate_output_policy(preflight_policy)
            if (
                template is not None
                and template.resolve(strict=False) == output_path.resolve(strict=False)
            ):
                raise OutputPolicyError(
                    "The renderer cannot use a same-path source/output transaction."
                )
            prepared_render_size = (
                SlideSize(args.slide_width_in, args.slide_height_in)
                if args.slide_width_in is not None
                else read_ooxml_slide_size(template) or SlideSize(13.333, 7.5)
            )
            if args.asset_manifest:
                asset_manifest_path = resolve_path(project_dir, args.asset_manifest)
                if asset_manifest_path is None:
                    die("Asset manifest path could not be resolved.")
                prepared_asset_manifest_path = asset_manifest_path
                prepared_asset_bindings = load_asset_bindings(asset_manifest_path)
            prepared_compiled, prepared_render_plan = compile_render_plan(
                deck_plan,
                slide_size=prepared_render_size,
                installed_fonts=set(args.installed_font) or discover_installed_fonts(),
                theme_id=args.theme_id,
                asset_bindings=prepared_asset_bindings,
            )
    elif args.normalize_brief_plan or args.compile_brief_plan or args.render_brief_plan:
        fact_store_path = resolve_path(project_dir, args.fact_store)
        brief_plan_path = resolve_path(project_dir, args.brief_plan)
        if fact_store_path is None or brief_plan_path is None:
            die("FactStore or BriefPlan path could not be resolved.")
        fact_store = load_fact_store(fact_store_path)
        try:
            brief_text = brief_plan_path.read_text(encoding="utf-8")
        except OSError as exc:
            die(f"BriefPlan could not be read: {exc}")
        if args.normalize_brief_plan:
            prepared_normalized_brief, normalization_trace = normalize_brief_plan(
                brief_text
            )
            prepared_normalization_changes = normalization_trace.changes
        else:
            retry_payloads: list[str] = []
            for retry_value in args.brief_retry_plan:
                retry_path = resolve_path(project_dir, retry_value)
                if retry_path is None:
                    die("BriefPlan retry path could not be resolved.")
                try:
                    retry_payloads.append(retry_path.read_text(encoding="utf-8"))
                except OSError as exc:
                    die(f"BriefPlan retry could not be read: {exc}")

            fallback_scenario_id: str | None = None
            for candidate_text in (brief_text, *retry_payloads):
                candidate = candidate_text.strip()
                fenced = re.fullmatch(
                    r"```(?:json)?\s*(.*?)\s*```", candidate, re.I | re.S
                )
                if fenced is not None:
                    candidate = fenced.group(1)
                try:
                    candidate_payload = json.loads(candidate)
                except json.JSONDecodeError:
                    continue
                scenario_value = (
                    candidate_payload.get("scenario_id")
                    if isinstance(candidate_payload, dict)
                    else None
                )
                if isinstance(scenario_value, str) and scenario_value.strip():
                    fallback_scenario_id = scenario_value.strip()
                    break
            if fallback_scenario_id is None:
                die(
                    "No parseable scenario_id was found in the BriefPlan attempts; "
                    "a fact-safe default cannot choose an archetype."
                )

            brand_spec = None
            if args.brand_spec:
                brand_spec_path = resolve_path(project_dir, args.brand_spec)
                if brand_spec_path is None:
                    die("BrandSpec path could not be resolved.")
                prepared_brand_spec_path = brand_spec_path
                brand_spec = load_brand_spec(brand_spec_path)
            if args.render_brief_plan:
                if not project_dir.exists():
                    die(f"Project folder not found: {project_dir}")
                template = choose_template(project_dir, args.template)
                preflight_policy = OutputPolicy(
                    source_path=template,
                    output_path=output_path,
                    dry_run=args.dry_run,
                    no_output_deck=args.no_output_deck,
                    allow_overwrite=args.allow_overwrite,
                )
                validate_output_policy(preflight_policy)
                if (
                    template is not None
                    and template.resolve(strict=False)
                    == output_path.resolve(strict=False)
                ):
                    raise OutputPolicyError(
                        "The renderer cannot use a same-path source/output transaction."
                    )
                prepared_render_size = (
                    SlideSize(args.slide_width_in, args.slide_height_in)
                    if args.slide_width_in is not None
                    else read_ooxml_slide_size(template) or SlideSize(13.333, 7.5)
                )
                if args.asset_manifest:
                    asset_manifest_path = resolve_path(project_dir, args.asset_manifest)
                    if asset_manifest_path is None:
                        die("Asset manifest path could not be resolved.")
                    prepared_asset_manifest_path = asset_manifest_path
                    prepared_asset_bindings = load_asset_bindings(asset_manifest_path)
            installed_fonts = set(args.installed_font) or discover_installed_fonts()
            image_generator = None
            asset_output_dir = None
            if args.generate_assets_with_agnes:
                api_key = os.environ.get("AGNES_API_KEY")
                if not api_key:
                    die(
                        "AGNES_API_KEY is required with "
                        "--generate-assets-with-agnes"
                    )
                image_generator = AgnesDirectClient(
                    api_key=api_key,
                    timeout_seconds=90,
                    max_retries=2,
                ).generate_clean_image
                asset_output_dir = resolve_path(
                    project_dir, args.asset_output_dir
                )
            prepared_brief_generation = prepare_brief_generation(
                fact_store,
                brief_text,
                slide_size=prepared_render_size,
                installed_fonts=installed_fonts,
                theme_id=args.theme_id,
                brand_spec=brand_spec,
                brand_spec_source=(
                    str(prepared_brand_spec_path)
                    if prepared_brand_spec_path is not None
                    else None
                ),
                asset_bindings=prepared_asset_bindings,
                asset_manifest_source=(
                    str(prepared_asset_manifest_path)
                    if prepared_asset_manifest_path is not None
                    else None
                ),
                image_generator=image_generator,
                asset_output_dir=asset_output_dir,
                direction_mode=args.direction_mode,
                direction_id=args.direction_id,
                design_system_version=args.design_system_version,
                build_render=args.render_brief_plan,
                brief_retry_payloads=tuple(retry_payloads),
                use_safe_default=True,
                fallback_scenario_id=fallback_scenario_id,
            )
            prepared_normalized_brief = json.loads(
                json.dumps(
                    {
                        "schema_version": prepared_brief_generation.compilation.brief_plan.schema_version,
                        "scenario_id": prepared_brief_generation.compilation.brief_plan.scenario_id,
                        "groups": [
                            {
                                "id": group.id,
                                "fact_refs": list(group.fact_refs),
                                **(
                                    {"beat_hint": group.beat_hint}
                                    if group.beat_hint is not None
                                    else {}
                                ),
                                **(
                                    {"semantic_hint": group.semantic_hint}
                                    if group.semantic_hint is not None
                                    else {}
                                ),
                                "importance": group.importance,
                            }
                            for group in prepared_brief_generation.compilation.brief_plan.groups
                        ],
                        "preferences": prepared_brief_generation.compilation.brief_plan.preferences_dict(),
                    }
                )
            )
            prepared_normalization_changes = (
                prepared_brief_generation.compilation.normalization_trace.changes
            )
            prepared_compiled = prepared_brief_generation.compiled_deck
            prepared_render_plan = prepared_brief_generation.render_plan

    if args.render_deck_plan or args.render_brief_plan:
        if prepared_render_plan is None:
            raise RuntimeError("governed renderer preflight did not produce a RenderPlan")
        prepared_backend = negotiate_backend(
            args.backend,
            prepared_render_plan,
            output_path=output_path,
            require_physical_template=template is not None,
        )

    if args.dry_run:
        emit_result(
            build_dry_run_result(args, project_dir),
            args.json,
            sys.stdout,
            sys.stderr,
        )
        return 0

    if args.render_assembly_plan:
        try:
            raw_project_dir = Path(args.project_dir).expanduser()
            if raw_project_dir.is_symlink():
                raise PhysicalAssemblyError(
                    f"PROJECT_ROOT_SYMLINK_REJECTED: {raw_project_dir}"
                )
            project_dir = raw_project_dir.resolve(strict=True)
            output_path = resolve_project_file(
                args.output,
                project_dir,
                label="OUTPUT",
                require_file=False,
            )
            assembly_plan_path = resolve_project_file(
                args.assembly_plan,
                project_dir,
                label="ASSEMBLY_PLAN",
            )
            private_root = resolve_private_root(explicit=args.assembly_private_root)
            if args.assembly_library:
                raw_library = Path(args.assembly_library).expanduser()
                library_path = (
                    raw_library.resolve(strict=False)
                    if raw_library.is_absolute()
                    else (private_root / raw_library).resolve(strict=False)
                )
            else:
                library_path = private_root / "v61" / "library-v4.json"
            try:
                library_path.relative_to(project_dir)
            except ValueError:
                pass
            else:
                raise PhysicalAssemblyError(
                    "LIBRARY_MUST_REMAIN_OUTSIDE_PROJECT_ROOT"
                )
            if not library_path.is_file():
                die("Compiled page-template library could not be resolved.")
            index = load_library_index(library_path)
            lookup = {template.page_id: template for template in index.page_templates}
            plan = load_assembly_plan(
                assembly_plan_path,
                lookup,
                project_root=project_dir,
            )
            locked_fact_store_path = resolve_project_file(
                args.fact_store,
                project_dir,
                label="FACT_STORE",
            )
            locked_asset_manifest_path = resolve_project_file(
                args.asset_manifest,
                project_dir,
                label="ASSET_MANIFEST",
            )
            locked_connective_copy_path = resolve_project_file(
                args.connective_copy,
                project_dir,
                label="CONNECTIVE_COPY",
            )
            report = assemble_physical_deck(
                plan,
                output_path,
                library_index_sha256=__import__("hashlib").sha256(
                    library_path.read_bytes()
                ).hexdigest(),
                fact_store_path=locked_fact_store_path,
                fact_store_sha256=args.fact_store_sha256,
                asset_manifest_path=locked_asset_manifest_path,
                asset_manifest_sha256=args.asset_manifest_sha256,
                connective_copy_path=locked_connective_copy_path,
                connective_copy_sha256=args.connective_copy_sha256,
                project_root=project_dir,
                require_locked_authority=True,
                require_libreoffice=True,
                max_output_size_bytes=(
                    args.assembly_max_output_size_bytes
                    or DEFAULT_MAX_OUTPUT_SIZE_BYTES
                ),
            )
            report_path = (
                resolve_project_file(
                    args.assembly_report,
                    project_dir,
                    label="ASSEMBLY_REPORT",
                    require_file=False,
                )
                if args.assembly_report
                else project_dir / ".window-pptx" / "audits" / "physical-assembly-report.json"
            )
            report_digest = write_assembly_report(report, report_path)
            report_validation = validate_physical_report(report_path, project_dir)
            if (
                report.status != "pass"
                or report_validation.get("status") != "pass"
                or not output_path.is_file()
            ):
                output_path.unlink(missing_ok=True)
                die(
                    "Physical assembly report validation failed: "
                    + json.dumps(report_validation, ensure_ascii=False)
                )
            qa = run_physical_rule_qa(output_path, plan=plan)
            qa_path = (
                resolve_project_file(
                    args.assembly_rule_qa_report,
                    project_dir,
                    label="ASSEMBLY_RULE_QA_REPORT",
                    require_file=False,
                )
                if args.assembly_rule_qa_report
                else project_dir / ".window-pptx" / "audits" / "physical-rule-qa.json"
            )
            qa_digest = write_rule_qa_report(qa, qa_path)
            if qa.status != "pass":
                output_path.unlink(missing_ok=True)
        except (PageTemplateError, PhysicalAssemblyError, OSError, ValueError) as exc:
            die(f"Physical assembly failed: {exc}")
        payload = report.to_dict()
        payload["report_digest"] = report_digest
        payload["independent_report_validation"] = report_validation
        payload["rule_qa"] = qa.to_dict()
        payload["rule_qa_digest"] = qa_digest
        emit_result(
            {
                "physical_assembly": payload,
                "assembly_plan": str(assembly_plan_path),
                "fact_store": str(locked_fact_store_path),
                "asset_manifest": str(locked_asset_manifest_path),
                "connective_copy": str(locked_connective_copy_path),
                "library": str(library_path),
                "private_root": str(private_root),
                "report": str(report_path),
            },
            args.json,
            sys.stdout,
            sys.stderr,
        )
        return 0 if report.status == "pass" and qa.status == "pass" else 1

    if args.render_template_pack:
        if prepared_template_pack is None or prepared_template_bindings is None:
            raise RuntimeError("TemplatePack preflight did not produce an adaptation plan")
        audit_dir = project_dir / ".window-pptx" / "audits"
        candidate_materialization = None
        if prepared_template_selection is not None:
            candidate_materialization, report = materialize_physical_selection(
                prepared_template_selection,
                prepared_slide_blueprints,
                prepared_template_bindings,
                output_path,
            )
        else:
            report = adapt_template_pack(
                prepared_template_pack,
                prepared_template_bindings,
                output_path,
            )
        report_path = write_adaptation_report(
            report,
            audit_dir / "template-adaptation-report.json",
        )
        slide_size = read_ooxml_slide_size(prepared_template_pack.template_path)
        if slide_size is None:
            raise RuntimeError("TemplatePack source has no readable slide size")
        proof = LibreOfficeVerifier().verify(
            output_path,
            artifact_dir=audit_dir / "template-portable-proof",
            expected_slide_count=prepared_template_pack.slide_count,
            slide_size=slide_size,
        )
        reference_quality = assess_reference_grade_quality(
            output_path,
            png_paths=proof.png_paths,
            expected_slide_count=prepared_template_pack.slide_count,
        )
        reference_quality_path = write_reference_quality_report(
            reference_quality,
            audit_dir / "reference-quality-report.json",
        )
        if not reference_quality.passed:
            output_path.unlink(missing_ok=True)
            raise RuntimeError(
                "TemplatePack candidate failed the reference-grade visual complexity gate"
            )
        candidate_materialization_path: Path | None = None
        if candidate_materialization is not None:
            candidate_materialization_path = (
                audit_dir / "candidate-materialization-report.json"
            )
            candidate_materialization_path.write_text(
                json.dumps(
                    candidate_materialization.to_dict(),
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
        exported_pdf: str | None = None
        if args.export_pdf:
            pdf_output = output_path.with_suffix(".pdf")
            shutil.copy2(proof.pdf_path, pdf_output)
            exported_pdf = str(pdf_output)
        emit_result(
            {
                "template_pack_adaptation": {
                    "template_pack_id": report.template_pack_id,
                    "source_sha256": report.source_sha256,
                    "output_sha256": report.output_sha256,
                    "changed_parts": list(report.changed_parts),
                    "slot_change_count": len(report.slot_changes),
                    "unchanged_part_count": report.unchanged_part_count,
                },
                "adaptation_report": str(report_path),
                "portable_verification": proof.to_dict(),
                "reference_quality": reference_quality.to_dict(),
                "reference_quality_report": str(reference_quality_path),
                "candidate_materialization": (
                    candidate_materialization.to_dict()
                    if candidate_materialization is not None
                    else None
                ),
                "candidate_materialization_report": (
                    str(candidate_materialization_path)
                    if candidate_materialization_path is not None
                    else None
                ),
                "exported_pdf": exported_pdf,
            },
            args.json,
            sys.stdout,
            sys.stderr,
        )
        return 0

    if args.com_doctor:
        emit_result(
            {"powerpoint_com_doctor": doctor_powerpoint().to_dict()},
            args.json,
            sys.stdout,
            sys.stderr,
        )
        return 0

    if args.certify_pptx:
        certification_target = resolve_path(project_dir, args.certify_pptx)
        verification_report = resolve_path(
            project_dir,
            args.portable_verification_report,
        )
        if certification_target is None:
            die("PowerPoint certification target could not be resolved.")
        if verification_report is None:
            die("Portable verification report could not be resolved.")
        validate_portable_certification_input(
            certification_target,
            verification_report,
        )
        certification = certify_powerpoint(
            certification_target,
            artifact_dir=(
                project_dir
                / ".window-pptx"
                / "audits"
                / "powerpoint-certification"
            ),
        )
        emit_result(
            {"powerpoint_certification": certification.to_dict()},
            args.json,
            sys.stdout,
            sys.stderr,
        )
        return 0

    if args.compile_deck_plan:
        emit_result(
            {"compiled_deck": prepared_compiled},
            args.json,
            sys.stdout,
            sys.stderr,
        )
        return 0

    if args.normalize_brief_plan:
        emit_result(
            {
                "normalized_brief_plan": prepared_normalized_brief,
                "normalization_trace": list(prepared_normalization_changes),
            },
            args.json,
            sys.stdout,
            sys.stderr,
        )
        return 0

    if args.compile_brief_plan or (
        args.render_brief_plan
        and prepared_brief_generation is not None
        and prepared_brief_generation.interaction_required
    ):
        if prepared_brief_generation is None:
            raise RuntimeError("BriefPlan preflight did not produce a generation")
        emit_result(
            prepared_brief_generation.to_dict(),
            args.json,
            sys.stdout,
            sys.stderr,
        )
        return 0

    if not project_dir.exists():
        if args.init_project:
            project_dir.mkdir(parents=True, exist_ok=True)
        else:
            die(f"Project folder not found: {project_dir}")

    init_result: dict[str, Any] | None = None
    if args.init_project:
        init_result = init_project_workspace(project_dir)

    if args.list_addins or args.probe_plugin_apis:
        require_windows()
        inspection_result: dict[str, Any] = {}
        if args.list_addins:
            inspection_result["addins"] = {
                "mode": "registry_only",
                "com_addins": list_registered_com_addins(),
                "powerpoint_addins": [],
                "notes": [
                    "Safe inspection does not start PowerPoint or load add-in code.",
                    "Loaded PowerPoint .ppa/.ppam add-ins are unavailable in registry-only mode.",
                ],
            }
        if args.probe_plugin_apis:
            progids = args.plugin_progid or ["iSlideTools.Public", "Slibe.OKPlus"]
            inspection_result["plugin_api_probe"] = probe_plugin_apis(None, progids)

        if args.json:
            emit_result(inspection_result, True, sys.stdout, sys.stderr)
        else:
            if "addins" in inspection_result:
                print_addins(inspection_result["addins"], False)
            if "plugin_api_probe" in inspection_result:
                print("PowerPoint plugin API probe:")
                emit_result(
                    inspection_result["plugin_api_probe"],
                    False,
                    sys.stdout,
                    sys.stderr,
                )
        return 0

    # Resolve deck inputs only for routes that consume a presentation.  Pure
    # asset/report routes with --no-output-deck must not be coupled to unrelated
    # PPT files or an otherwise unused --output value.
    deck_output_requested = not args.no_output_deck
    deck_input_requested = deck_output_requested or any(
        [
            args.render_deck_plan,
            args.render_brief_plan,
            args.extract_media,
            args.export_slides,
            args.add_master_watermark,
            args.export_qa,
            args.audit_deck,
            args.make_ascii_temp_copy,
        ]
    )
    if not args.intake_template_library and deck_input_requested:
        if template is None:
            template = choose_template(project_dir, args.template)
        if deck_output_requested:
            validate_output_policy(
                OutputPolicy(
                    source_path=template,
                    output_path=output_path,
                    dry_run=False,
                    no_output_deck=False,
                    allow_overwrite=args.allow_overwrite,
                )
            )
            if (
                template is not None
                and template.resolve(strict=False) == output_path.resolve(strict=False)
            ):
                raise OutputPolicyError(
                    "A same-path overwrite is unsafe while the source presentation is open; "
                    "use a distinct output path."
                )
        if args.make_ascii_temp_copy:
            if template is None:
                die(
                    "No template/source deck available for --make-ascii-temp-copy. "
                    "Pass --template explicitly."
                )
            staging_target = ascii_temp_copy_path(project_dir, template)
            conflicts = {template.resolve(strict=False)}
            if deck_output_requested:
                conflicts.add(output_path.resolve(strict=False))
            if staging_target.resolve(strict=False) in conflicts:
                raise OutputPolicyError(
                    "ASCII staging path conflicts with the source or output path."
                )

    non_com_results: dict[str, Any] = {}

    search_result: dict[str, Any] | None = None
    if args.search_images:
        search_result = pixabay_search(args, project_dir)
        non_com_results["pixabay_search"] = search_result
        if args.download_top_image:
            first = next((hit for hit in search_result.get("hits", []) if hit.get("largeImageURL") or hit.get("webformatURL")), None)
            if first is None:
                die("No downloadable image URL found in Pixabay results.")
            non_com_results["pixabay_download"] = download_image(
                project_dir,
                str(first.get("largeImageURL") or first.get("webformatURL")),
                first,
            )

    if args.download_image:
        non_com_results["pixabay_download"] = download_image(project_dir, args.download_image)

    icon_search_result: dict[str, Any] | None = None
    if args.search_icons:
        icon_search_result = iconify_search(args, project_dir)
        non_com_results["iconify_search"] = icon_search_result
        if args.download_top_icon:
            first_icon = next((icon for icon in icon_search_result.get("icons", []) if icon), None)
            if first_icon is None:
                die("No downloadable icon found in Iconify results.")
            non_com_results["iconify_download"] = download_icon(project_dir, str(first_icon), args)

    if args.download_icon:
        non_com_results["iconify_download"] = download_icon(project_dir, args.download_icon, args)

    portable_render_requested = (
        (args.render_deck_plan or args.render_brief_plan)
        and prepared_backend is not None
        and prepared_backend.backend_id == "pptxgenjs"
    )
    if portable_render_requested:
        if prepared_compiled is None or prepared_render_plan is None:
            raise RuntimeError("portable renderer preflight did not produce a plan")
        if args.verification == "powerpoint" and platform.system().casefold() != "windows":
            die(
                "PowerPoint certification requires native Windows. Use "
                "--verification portable for OOXML + LibreOffice/Poppler verification."
            )
        audit_dir = project_dir / ".window-pptx" / "audits"
        html_proof: Path | None = None
        html_proof_error: str | None = None
        if not args.no_html_proof:
            try:
                html_proof = write_html_proof(
                    prepared_render_plan,
                    audit_dir / "render-proof.html",
                )
            except (OSError, ValueError) as exc:
                html_proof_error = f"optional HTML proof was not written: {exc}"
        brief_v2_findings = ()
        if args.render_brief_plan:
            if prepared_brief_generation is None:
                raise RuntimeError("BriefPlan renderer lost generation evidence")
            write_brief_generation_artifacts(prepared_brief_generation, audit_dir)
            brief_v2_findings = (
                *generation_quality_findings(prepared_brief_generation),
                *inspect_design_quality(prepared_brief_generation),
            )
        output_policy = OutputPolicy(
            source_path=template,
            output_path=output_path,
            dry_run=False,
            no_output_deck=args.no_output_deck,
            allow_overwrite=args.allow_overwrite,
        )
        certifier = None
        if args.verification == "powerpoint":
            certifier = lambda candidate, artifact_dir: certify_powerpoint(
                candidate,
                artifact_dir=artifact_dir,
            ).to_dict()
        pipeline_result = execute_portable_render_plan(
            prepared_compiled,
            prepared_render_plan,
            output_policy=output_policy,
            audit_dir=audit_dir,
            requested_backend=prepared_backend.backend_id,
            verification_level=args.verification,
            export_pdf=args.export_pdf,
            quality_v2_findings=brief_v2_findings,
            powerpoint_certifier=certifier,
        )

        rendered_export_result: dict[str, Any] | None = None
        rendered_qa_result: dict[str, Any] | None = None
        verification = pipeline_result.verification
        proof_pngs = (
            verification.libreoffice.png_paths if verification is not None else ()
        )
        if args.export_slides:
            requested_slides = parse_slide_spec(args.export_slides)
            invalid = [
                slide_number
                for slide_number in requested_slides
                if slide_number < 1 or slide_number > len(proof_pngs)
            ]
            if invalid:
                die(
                    "Requested slide export is outside the rendered deck: "
                    + ", ".join(str(value) for value in invalid)
                )
            export_dir = (
                resolve_path(project_dir, args.export_dir)
                or (project_dir / ".window-pptx" / "exports")
            )
            export_dir.mkdir(parents=True, exist_ok=True)
            exported_paths: list[str] = []
            for slide_number in requested_slides:
                target = export_dir / f"slide-{slide_number:03d}.png"
                shutil.copy2(proof_pngs[slide_number - 1], target)
                exported_paths.append(str(target))
            rendered_export_result = {
                "slide_numbers": requested_slides,
                "paths": exported_paths,
                "source": "libreoffice-poppler-proof",
            }
        if args.export_qa:
            qa_dir = project_dir / ".window-pptx" / "exports" / "qa"
            qa_dir.mkdir(parents=True, exist_ok=True)
            qa_paths: list[str] = []
            for index, source in enumerate(proof_pngs, start=1):
                target = qa_dir / f"slide-{index:03d}.png"
                shutil.copy2(source, target)
                qa_paths.append(str(target))
            rendered_qa_result = {
                "slide_count": len(qa_paths),
                "paths": qa_paths,
                "source": "libreoffice-poppler-proof",
            }
        generation_artifacts = None
        if args.render_brief_plan and prepared_brief_generation is not None:
            generation_artifacts = write_brief_generation_artifacts(
                prepared_brief_generation,
                audit_dir,
            )
        emit_result(
            {
                "render_pipeline": pipeline_result.to_dict(),
                "html_proof": str(html_proof) if html_proof is not None else None,
                "html_proof_error": html_proof_error,
                "slide_export": rendered_export_result,
                "qa_export": rendered_qa_result,
                "quality_v2_artifact": pipeline_result.artifacts.get(
                    "quality_report_v2"
                ),
                "generation_artifacts": generation_artifacts,
            },
            args.json,
            sys.stdout,
            sys.stderr,
        )
        return 0

    com_needed = any(
        [
            args.render_deck_plan,
            args.render_brief_plan,
            args.export_slides,
            args.intake_template_library,
            args.add_master_watermark,
            args.export_qa,
            args.audit_deck,
        ]
    ) or not args.no_output_deck

    if args.extract_media and args.no_output_deck and not args.export_slides:
        if template is None:
            die("No template/source deck available for --extract-media. Pass --template explicitly.")
        media_dir = resolve_path(project_dir, args.media_dir) or (project_dir / ".window-pptx" / "media")
        media_result = extract_media_from_deck(template, media_dir)
        non_com_results["media_extraction"] = media_result

    if not com_needed:
        result = {"init_project": init_result, **non_com_results}
        if not args.json:
            print("window-pptx non-COM run complete")
        emit_result(result, args.json, sys.stdout, sys.stderr)
        return 0

    if args.render_brief_plan and prepared_brief_generation is not None:
        # Persist model-independent preflight evidence before any Windows/COM
        # dependency can fail. A successful render replaces the repair log with
        # the final transaction evidence later in this function.
        write_brief_generation_artifacts(
            prepared_brief_generation,
            project_dir / ".window-pptx" / "audits",
        )

    require_windows()
    if args.clear_com_cache:
        maybe_clear_com_cache()
    client = com_client if com_client is not None else import_win32com()

    handle: PowerPointHandle | None = None
    presentation = None

    try:
        handle = dispatch_powerpoint(args.attach_existing, client)
        if (
            args.render_deck_plan or args.render_brief_plan
        ) and handle.dispatch_mode == "dynamic_dispatch_fallback":
            raise ComSessionError(
                "Governed rendering requires an owned DispatchEx PowerPoint session; "
                "dynamic Dispatch ownership cannot be proven."
            )
        app = handle.app
        if args.visible:
            try:
                app.Visible = MSO_TRUE
            except Exception:
                pass

        if args.intake_template_library:
            intake_result = intake_template_library(app, project_dir, args)
            if not args.json:
                print("Template library intake complete")
            emit_result(
                {"template_library_intake": intake_result}
                if args.json
                else intake_result,
                args.json,
                sys.stdout,
                sys.stderr,
            )
            return 0

        request_path: Path | None = None
        request_text = ""
        effective_template = template

        validate_output_policy(
            OutputPolicy(
                source_path=template,
                output_path=output_path,
                dry_run=False,
                no_output_deck=args.no_output_deck,
                allow_overwrite=args.allow_overwrite,
            )
        )
        if (
            not args.no_output_deck
            and template is not None
            and template.resolve(strict=False) == output_path.resolve(strict=False)
        ):
            raise OutputPolicyError(
                "A same-path overwrite is unsafe while the source presentation is open; "
                "use a distinct output path."
            )

        if args.extract_media:
            if template is None:
                die("No template/source deck available for --extract-media. Pass --template explicitly.")
            media_dir = resolve_path(project_dir, args.media_dir) or (project_dir / ".window-pptx" / "media")
            media_result = extract_media_from_deck(template, media_dir)
            if args.no_output_deck and not args.export_slides:
                if not args.json:
                    print("Media extraction complete")
                emit_result(
                    {"media_extraction": media_result}
                    if args.json
                    else media_result,
                    args.json,
                    sys.stdout,
                    sys.stderr,
                )
                return 0

        if args.make_ascii_temp_copy:
            if template is None:
                die("No template/source deck available for --make-ascii-temp-copy. Pass --template explicitly.")
            staging_target = ascii_temp_copy_path(project_dir, template)
            resolved_staging = staging_target.resolve(strict=False)
            if resolved_staging in {
                template.resolve(strict=False),
                output_path.resolve(strict=False),
            }:
                raise OutputPolicyError(
                    "ASCII staging path conflicts with the source or output path."
                )
            effective_template = ensure_ascii_temp_copy(project_dir, template)

        output_policy = OutputPolicy(
            source_path=effective_template,
            output_path=output_path,
            dry_run=False,
            no_output_deck=args.no_output_deck,
            allow_overwrite=args.allow_overwrite,
        )
        validate_output_policy(output_policy)
        if (
            effective_template is not None
            and effective_template.resolve(strict=False)
            == output_path.resolve(strict=False)
        ):
            raise OutputPolicyError(
                "A same-path overwrite is unsafe while the source presentation is open; "
                "use a distinct output path."
            )

        presentation = open_or_create_presentation(app, effective_template, args.visible)

        if args.render_deck_plan or args.render_brief_plan:
            if prepared_compiled is None or prepared_render_plan is None:
                raise RuntimeError("governed renderer preflight did not produce a plan")
            audit_dir = project_dir / ".window-pptx" / "audits"
            brief_v2_findings = None
            preview_exporter = None
            quality_v2_slide_ids = None
            if args.render_brief_plan:
                if prepared_brief_generation is None:
                    raise RuntimeError("BriefPlan renderer lost generation evidence")
                brief_v2_findings = (
                    *generation_quality_findings(prepared_brief_generation),
                    *inspect_design_quality(prepared_brief_generation),
                )
                preview_exporter = lambda current: export_quality_v2_previews(
                    current,
                    audit_dir,
                )
                quality_v2_slide_ids = tuple(
                    slide.source_id for slide in prepared_render_plan.slides
                )
            try:
                pipeline_result = execute_render_plan(
                    prepared_compiled,
                    prepared_render_plan,
                    presentation=presentation,
                    app=app,
                    output_policy=output_policy,
                    export_pdf=args.export_pdf,
                    audit_dir=audit_dir,
                    max_repair_passes=1 if args.render_brief_plan else 2,
                    quality_v2_findings=brief_v2_findings,
                    preview_exporter=preview_exporter,
                    quality_v2_slide_ids=quality_v2_slide_ids,
                )
            except QualityV2GateError as exc:
                if prepared_brief_generation is not None:
                    write_brief_generation_artifacts(
                        prepared_brief_generation,
                        audit_dir,
                    )
                raise
            except QualityGateError as exc:
                if args.render_brief_plan and prepared_brief_generation is not None:
                    write_brief_generation_artifacts(
                        prepared_brief_generation,
                        audit_dir,
                    )
                raise
            rendered_export_result: dict[str, Any] | None = None
            if args.export_slides:
                rendered_export_result = export_slides_to_png(
                    presentation,
                    parse_slide_spec(args.export_slides),
                    resolve_path(project_dir, args.export_dir)
                    or (project_dir / ".window-pptx" / "exports"),
                )
            rendered_qa_result: dict[str, Any] | None = None
            if args.export_qa:
                rendered_qa_result = export_all_slides_to_png(
                    presentation,
                    project_dir / ".window-pptx" / "exports" / "qa",
                )
            quality_artifacts: dict[str, str] | None = None
            quality_v2_artifact = pipeline_result.quality_v2_artifacts.get(
                "quality_report_v2"
            )
            if isinstance(pipeline_result.inspection, QualityReport) and isinstance(
                pipeline_result.repair, RepairLog
            ):
                quality_artifacts = write_quality_artifacts(
                    pipeline_result.inspection,
                    pipeline_result.repair,
                    audit_dir,
                )
            generation_artifacts: dict[str, str] | None = None
            if args.render_brief_plan:
                if prepared_brief_generation is None:
                    raise RuntimeError("BriefPlan renderer lost generation evidence")
                generation_artifacts = write_brief_generation_artifacts(
                    prepared_brief_generation,
                    audit_dir,
                    pipeline_result.post_render_repair_passes,
                )
            emit_result(
                {
                    "render_pipeline": pipeline_result.to_dict(),
                    "slide_export": rendered_export_result,
                    "qa_export": rendered_qa_result,
                    "quality_artifacts": quality_artifacts,
                    "quality_v2_artifact": quality_v2_artifact,
                    "generation_artifacts": generation_artifacts,
                },
                args.json,
                sys.stdout,
                sys.stderr,
            )
            return 0

        should_add_summary = not any(
            [
                args.render_deck_plan,
                args.render_brief_plan,
                args.add_master_watermark,
                args.audit_deck,
                args.export_qa,
                args.export_slides,
            ]
        )
        if should_add_summary:
            request_path, request_text = read_request(project_dir, args.request)
            add_request_summary_slide(presentation, request_text, template)

        watermark_result: dict[str, Any] | None = None
        if args.add_master_watermark:
            watermark_result = add_master_watermark(
                presentation,
                args.add_master_watermark,
                args.watermark_opacity,
            )

        export_result: dict[str, Any] | None = None
        if args.export_slides:
            export_dir = resolve_path(project_dir, args.export_dir) or (project_dir / ".window-pptx" / "exports")
            export_result = export_slides_to_png(
                presentation,
                parse_slide_spec(args.export_slides),
                export_dir,
            )

        qa_export_result: dict[str, Any] | None = None
        if args.export_qa:
            qa_export_result = export_all_slides_to_png(
                presentation,
                project_dir / ".window-pptx" / "exports" / "qa",
            )

        audit_result: dict[str, Any] | None = None
        if args.audit_deck:
            audit_result = audit_presentation(presentation, project_dir)

        outputs: dict[str, str] = {}
        transaction_result: dict[str, Any] | None = None
        if not args.no_output_deck:
            outputs, transaction_result = save_outputs(
                presentation,
                app,
                output_policy,
                args.export_pdf,
            )

        result = {
            "project_dir": str(project_dir),
            "init_project": init_result,
            **non_com_results,
            "request": str(request_path) if request_path else None,
            "template": str(template) if template else None,
            "effective_template": str(effective_template) if effective_template else None,
            "outputs": outputs,
            "transaction": transaction_result,
            "addins_inventory_written": False,
            "slide_export": export_result,
            "qa_export": qa_export_result,
            "deck_audit": audit_result,
            "master_watermark": watermark_result,
        }
        if not args.json:
            print("window-pptx run complete")
        emit_result(result, args.json, sys.stdout, sys.stderr)
    finally:
        active_error = sys.exc_info()[0] is not None
        if handle is not None:
            if presentation is not None:
                handle.close_presentation(presentation, keep_open=args.keep_open)
            handle.quit(keep_open=args.keep_open)
            if handle.cleanup_errors:
                message = "PowerPoint cleanup failed: " + " | ".join(
                    handle.cleanup_errors
                )
                if active_error:
                    print(message, file=sys.stderr)
                else:
                    raise WindowPptxError(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
