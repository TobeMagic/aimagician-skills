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
from window_pptx.com_session import dispatch_powerpoint, macro_security
from window_pptx.errors import OutputPolicyError
from window_pptx.models import CandidateResult, OutputPolicy, PowerPointHandle
from window_pptx.output_policy import calculate_export_size, validate_output_policy
from window_pptx.transaction import save_candidate


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
        app.COMAddIns.Update()
    except Exception:
        pass

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


def registry_get(winreg: Any, root: Any, path: str, value_name: str = "") -> Any:
    try:
        with winreg.OpenKey(root, path) as key:
            value, _ = winreg.QueryValueEx(key, value_name)
            return value
    except Exception:
        return None


def registry_key_values(winreg: Any, root: Any, path: str) -> dict[str, Any] | None:
    try:
        with winreg.OpenKey(root, path) as key:
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


def clsid_registry_snapshot(winreg: Any, progid: str) -> dict[str, Any]:
    clsid = registry_get(winreg, winreg.HKEY_CLASSES_ROOT, rf"{progid}\CLSID")
    result: dict[str, Any] = {"progid": progid, "clsid": clsid}
    if not clsid:
        return result

    clsid_key = rf"CLSID\{clsid}"
    result.update(
        {
            "friendly_name": registry_get(winreg, winreg.HKEY_CLASSES_ROOT, clsid_key),
            "typelib": registry_get(winreg, winreg.HKEY_CLASSES_ROOT, rf"{clsid_key}\TypeLib"),
            "version": registry_get(winreg, winreg.HKEY_CLASSES_ROOT, rf"{clsid_key}\Version"),
            "local_server32": registry_get(
                winreg, winreg.HKEY_CLASSES_ROOT, rf"{clsid_key}\LocalServer32"
            ),
            "inproc_server32": registry_get(
                winreg, winreg.HKEY_CLASSES_ROOT, rf"{clsid_key}\InprocServer32"
            ),
        }
    )
    return result


def office_addin_registry_snapshot(winreg: Any, progid: str) -> list[dict[str, Any]]:
    rows = []
    roots = [
        ("HKCU", winreg.HKEY_CURRENT_USER),
        ("HKLM", winreg.HKEY_LOCAL_MACHINE),
    ]
    paths = [
        rf"Software\Microsoft\Office\PowerPoint\Addins\{progid}",
        rf"Software\WOW6432Node\Microsoft\Office\PowerPoint\Addins\{progid}",
    ]
    for root_name, root in roots:
        for path in paths:
            values = registry_key_values(winreg, root, path)
            if values is not None:
                rows.append({"root": root_name, "path": path, "values": values})
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
    pythoncom, dynamic, winreg = import_probe_modules()
    return {
        "probed_progids": progids,
        "registry": {progid: clsid_registry_snapshot(winreg, progid) for progid in progids},
        "office_addin_registry": {
            progid: office_addin_registry_snapshot(winreg, progid) for progid in progids
        },
        "direct_dispatch": {
            progid: probe_direct_dispatch(dynamic, pythoncom, progid) for progid in progids
        },
        "addin_object": {progid: probe_addin_object(app, pythoncom, progid) for progid in progids},
        "notes": [
            "This probe only reads COM registration and type information.",
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


def main(
    argv: Sequence[str] | None = None,
    *,
    com_client: Any | None = None,
) -> int:
    args = parse_args(argv)
    project_dir = Path(args.project_dir).expanduser()
    if args.dry_run:
        emit_result(
            build_dry_run_result(args, project_dir),
            args.json,
            sys.stdout,
            sys.stderr,
        )
        return 0

    project_dir = project_dir.resolve()
    if not project_dir.exists():
        if args.init_project:
            project_dir.mkdir(parents=True, exist_ok=True)
        else:
            die(f"Project folder not found: {project_dir}")

    init_result: dict[str, Any] | None = None
    if args.init_project:
        init_result = init_project_workspace(project_dir)

    output_path = resolve_path(project_dir, args.output)
    if output_path is None:
        die("Output path could not be resolved.")

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

    com_needed = any(
        [
            args.list_addins,
            args.probe_plugin_apis,
            args.export_slides,
            args.intake_template_library,
            args.add_master_watermark,
            args.export_qa,
            args.audit_deck,
        ]
    ) or not args.no_output_deck

    if args.extract_media and args.no_output_deck and not args.export_slides:
        template = choose_template(project_dir, args.template)
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

    require_windows()
    if args.clear_com_cache:
        maybe_clear_com_cache()
    client = com_client if com_client is not None else import_win32com()

    handle: PowerPointHandle | None = None
    presentation = None

    try:
        handle = dispatch_powerpoint(args.attach_existing, client)
        app = handle.app
        if args.visible:
            try:
                app.Visible = MSO_TRUE
            except Exception:
                pass

        if args.list_addins or args.probe_plugin_apis:
            inspection_result: dict[str, Any] = {}
            if args.list_addins:
                inspection_result["addins"] = {
                    "com_addins": list_com_addins(app),
                    "powerpoint_addins": list_powerpoint_addins(app),
                }
            if args.probe_plugin_apis:
                progids = args.plugin_progid or ["iSlideTools.Public", "Slibe.OKPlus"]
                inspection_result["plugin_api_probe"] = probe_plugin_apis(app, progids)

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
        template = choose_template(project_dir, args.template)
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

        should_add_summary = not any(
            [
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
        if handle is not None:
            if presentation is not None:
                handle.close_presentation(presentation, keep_open=args.keep_open)
            handle.quit(keep_open=args.keep_open)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
