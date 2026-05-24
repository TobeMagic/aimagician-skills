#!/usr/bin/env python3
"""Conservative Windows PowerPoint COM helper for the window-pptx skill."""

from __future__ import annotations

import argparse
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
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


MISSING = "<unavailable>"
MSO_FALSE = 0
MSO_TRUE = -1
PP_LAYOUT_BLANK = 12
MSO_TEXT_ORIENTATION_HORIZONTAL = 1
PP_FIXED_FORMAT_TYPE_PDF = 2
PP_FIXED_FORMAT_INTENT_PRINT = 2
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run PowerPoint COM checks and a minimal request-summary edit."
    )
    parser.add_argument("--project-dir", required=True, help="PowerPoint project folder.")
    parser.add_argument("--request", default="REQUEST.md", help="Request file name or path.")
    parser.add_argument("--template", help="Template/source deck path. Defaults to auto-detect.")
    parser.add_argument("--output", default="output/final.pptx", help="Output PPTX path.")
    parser.add_argument(
        "--init-project",
        action="store_true",
        help="Create standard window-pptx workspace folders plus planning files if missing.",
    )
    parser.add_argument(
        "--extract-media",
        action="store_true",
        help="Extract ppt/media assets from the template/source deck into .window-pptx/media or --media-dir.",
    )
    parser.add_argument(
        "--media-dir",
        help="Directory for extracted media. Defaults to .window-pptx/media under the project.",
    )
    parser.add_argument(
        "--export-slides",
        help="Comma-separated slide numbers/ranges to export to PNG, e.g. 4,6,8-10.",
    )
    parser.add_argument(
        "--export-dir",
        help="Directory for exported slide PNGs. Defaults to .window-pptx/exports under the project.",
    )
    parser.add_argument(
        "--make-ascii-temp-copy",
        action="store_true",
        help="Copy the template/source deck to an ASCII temp filename under .window-pptx/temp before COM work.",
    )
    parser.add_argument("--list-addins", action="store_true", help="Print PowerPoint add-in inventory.")
    parser.add_argument(
        "--probe-plugin-apis",
        action="store_true",
        help="Read COM registration/type information for add-in ProgIDs without invoking business methods.",
    )
    parser.add_argument(
        "--plugin-progid",
        action="append",
        default=[],
        help="Add-in ProgID to probe. Can be repeated. Defaults to iSlideTools.Public and Slibe.OKPlus when probing.",
    )
    parser.add_argument(
        "--clear-com-cache",
        action="store_true",
        help="Remove the current user's temp gen_py cache before creating COM objects.",
    )
    parser.add_argument("--export-pdf", action="store_true", help="Export a PDF next to the PPTX.")
    parser.add_argument(
        "--search-images",
        help="Search Pixabay images with PIXABAY_API_KEY and write a source manifest. Does not require PowerPoint COM.",
    )
    parser.add_argument(
        "--download-image",
        help="Download one image URL into assets/downloads/pixabay and update the asset manifest.",
    )
    parser.add_argument(
        "--download-top-image",
        action="store_true",
        help="After --search-images, download the first available largeImageURL/webformatURL result.",
    )
    parser.add_argument("--image-lang", default="zh", help="Pixabay language code. Default: zh.")
    parser.add_argument(
        "--image-type",
        default="all",
        choices=["all", "photo", "illustration", "vector"],
        help="Pixabay image_type filter.",
    )
    parser.add_argument(
        "--image-orientation",
        default="all",
        choices=["all", "horizontal", "vertical"],
        help="Pixabay orientation filter.",
    )
    parser.add_argument("--image-category", help="Pixabay category filter.")
    parser.add_argument("--image-colors", help="Pixabay colors filter.")
    parser.add_argument(
        "--image-order",
        default="popular",
        choices=["popular", "latest"],
        help="Pixabay result order.",
    )
    parser.add_argument("--image-page", type=int, default=1, help="Pixabay result page.")
    parser.add_argument(
        "--image-per-page",
        type=int,
        default=20,
        help="Pixabay results per page, 3-200.",
    )
    parser.add_argument(
        "--unsafe-image-search",
        action="store_true",
        help="Disable Pixabay safesearch. Keep disabled by default for presentation work.",
    )
    parser.add_argument(
        "--add-master-watermark",
        help="Add or replace a master-level text watermark on the Slide Master.",
    )
    parser.add_argument(
        "--watermark-opacity",
        type=float,
        default=0.16,
        help="Desired watermark opacity from 0 to 1. Implemented as light gray text for broad COM compatibility.",
    )
    parser.add_argument(
        "--export-qa",
        action="store_true",
        help="Export all slides to .window-pptx/exports/qa for visual QA.",
    )
    parser.add_argument(
        "--audit-deck",
        action="store_true",
        help="Write .window-pptx/audits/deck_audit.json with slide, font, shape, and animation metadata.",
    )
    parser.add_argument("--visible", action="store_true", help="Open the presentation window visibly.")
    parser.add_argument(
        "--attach-existing",
        action="store_true",
        help="Attach to an existing PowerPoint instance instead of creating an isolated one.",
    )
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--no-save", action="store_true", help="Run checks without saving output.")
    parser.add_argument(
        "--keep-open",
        action="store_true",
        help="Leave PowerPoint open after the run. Use carefully with --attach-existing.",
    )
    return parser.parse_args()


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


def ensure_ascii_temp_copy(project_dir: Path, source: Path) -> Path:
    temp_dir = project_dir / ".window-pptx" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    target = temp_dir / "deck_temp_ascii.pptx"
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
    for slide_number in slide_numbers:
        if slide_number < 1 or slide_number > max_count:
            continue
        target = export_dir / f"slide-{slide_number}.png"
        presentation.Slides(slide_number).Export(str(target), "PNG", 1600, 900)
        exported.append(str(target))
    return {"export_dir": str(export_dir), "slides": slide_numbers, "files": exported}


def export_all_slides_to_png(presentation: Any, export_dir: Path) -> dict[str, Any]:
    return export_slides_to_png(
        presentation,
        list(range(1, int(presentation.Slides.Count) + 1)),
        export_dir,
    )


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


def dispatch_powerpoint(win32com: Any, attach_existing: bool, visible: bool) -> Any:
    try:
        if attach_existing:
            app = win32com.Dispatch("PowerPoint.Application")
        else:
            app = win32com.DispatchEx("PowerPoint.Application")
    except Exception:
        # Fall back to late binding when a broken makepy/gen_py cache prevents wrapping.
        import win32com.client.dynamic  # type: ignore

        app = win32com.client.dynamic.Dispatch("PowerPoint.Application")

    if visible:
        try:
            app.Visible = MSO_TRUE
        except Exception:
            pass
    return app


def open_or_create_presentation(app: Any, template: Path | None, visible: bool) -> Any:
    with_window = MSO_TRUE if visible else MSO_FALSE
    if template:
        return app.Presentations.Open(str(template), MSO_TRUE, MSO_TRUE, with_window)
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


def save_outputs(presentation: Any, output_path: Path, export_pdf: bool) -> dict[str, str]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    presentation.SaveAs(str(output_path))
    result = {"pptx": str(output_path)}

    if export_pdf:
        pdf_path = output_path.with_suffix(".pdf")
        presentation.ExportAsFixedFormat(
            str(pdf_path),
            PP_FIXED_FORMAT_TYPE_PDF,
            PP_FIXED_FORMAT_INTENT_PRINT,
        )
        result["pdf"] = str(pdf_path)

    return result


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


def main() -> None:
    args = parse_args()
    project_dir = Path(args.project_dir).resolve()
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

    com_needed = any(
        [
            args.list_addins,
            args.probe_plugin_apis,
            args.export_slides,
            args.add_master_watermark,
            args.export_qa,
            args.audit_deck,
        ]
    ) or not args.no_save

    if args.extract_media and args.no_save and not args.export_slides:
        template = choose_template(project_dir, args.template)
        if template is None:
            die("No template/source deck available for --extract-media. Pass --template explicitly.")
        media_dir = resolve_path(project_dir, args.media_dir) or (project_dir / ".window-pptx" / "media")
        media_result = extract_media_from_deck(template, media_dir)
        non_com_results["media_extraction"] = media_result

    if not com_needed:
        result = {"init_project": init_result, **non_com_results}
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("window-pptx non-COM run complete")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    require_windows()
    if args.clear_com_cache:
        maybe_clear_com_cache()
    win32com = import_win32com()

    app = None
    presentation = None
    created_isolated_app = not args.attach_existing

    try:
        app = dispatch_powerpoint(win32com, args.attach_existing, args.visible)
        addins = {
            "com_addins": list_com_addins(app),
            "powerpoint_addins": list_powerpoint_addins(app),
        }

        if args.probe_plugin_apis:
            progids = args.plugin_progid or ["iSlideTools.Public", "Slibe.OKPlus"]
            probe = probe_plugin_apis(app, progids)
            inventory_dir = project_dir / ".window-pptx"
            inventory_dir.mkdir(parents=True, exist_ok=True)
            (inventory_dir / "plugin_api_probe.json").write_text(
                json.dumps(probe, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            if args.json:
                print(json.dumps(probe, ensure_ascii=False, indent=2))
            else:
                print("PowerPoint plugin API probe:")
                print(json.dumps(probe, ensure_ascii=False, indent=2))
            if args.no_save:
                return

        if args.list_addins and args.no_save:
            print_addins(addins, args.json)
            return

        request_path: Path | None = None
        request_text = ""
        template = choose_template(project_dir, args.template)
        effective_template = template

        if args.extract_media:
            if template is None:
                die("No template/source deck available for --extract-media. Pass --template explicitly.")
            media_dir = resolve_path(project_dir, args.media_dir) or (project_dir / ".window-pptx" / "media")
            media_result = extract_media_from_deck(template, media_dir)
            if args.no_save and not args.export_slides:
                if args.json:
                    print(json.dumps({"media_extraction": media_result}, ensure_ascii=False, indent=2))
                else:
                    print("Media extraction complete")
                    print(json.dumps(media_result, ensure_ascii=False, indent=2))
                return

        if args.make_ascii_temp_copy:
            if template is None:
                die("No template/source deck available for --make-ascii-temp-copy. Pass --template explicitly.")
            effective_template = ensure_ascii_temp_copy(project_dir, template)

        if args.list_addins:
            inventory_dir = project_dir / ".window-pptx"
            inventory_dir.mkdir(parents=True, exist_ok=True)
            (inventory_dir / "addins.json").write_text(
                json.dumps(addins, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print_addins(addins, args.json)

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
        if not args.no_save:
            outputs = save_outputs(presentation, output_path, args.export_pdf)

        result = {
            "project_dir": str(project_dir),
            "init_project": init_result,
            **non_com_results,
            "request": str(request_path) if request_path else None,
            "template": str(template) if template else None,
            "effective_template": str(effective_template) if effective_template else None,
            "outputs": outputs,
            "addins_inventory_written": bool(args.list_addins),
            "slide_export": export_result,
            "qa_export": qa_export_result,
            "deck_audit": audit_result,
            "master_watermark": watermark_result,
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print("window-pptx run complete")
            print(json.dumps(result, ensure_ascii=False, indent=2))
    finally:
        if presentation is not None and not args.keep_open:
            try:
                presentation.Close()
            except Exception:
                pass
        if app is not None and created_isolated_app and not args.keep_open:
            try:
                app.Quit()
            except Exception:
                pass


if __name__ == "__main__":
    main()
