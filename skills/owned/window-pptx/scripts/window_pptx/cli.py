"""Command-line parsing and result formatting for window-pptx."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence, TextIO


NO_SAVE_WARNING = (
    "window-pptx: warning: --no-save is deprecated; "
    "use --no-output-deck instead."
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse window-pptx arguments, including an explicit argument sequence."""

    parser = argparse.ArgumentParser(
        description="Run PowerPoint COM checks and a minimal request-summary edit."
    )
    parser.add_argument("--project-dir", required=True, help="PowerPoint project folder.")
    parser.add_argument("--request", default="REQUEST.md", help="Request file name or path.")
    parser.add_argument("--template", help="Template/source deck path. Defaults to auto-detect.")
    parser.add_argument("--output", default="output/final.pptx", help="Output PPTX path.")
    parser.add_argument(
        "--deck-plan",
        help="DeckPlan v1 JSON path, relative to --project-dir unless absolute.",
    )
    deck_plan_route = parser.add_mutually_exclusive_group()
    deck_plan_route.add_argument(
        "--compile-deck-plan",
        action="store_true",
        help="Validate and compile DeckPlan JSON without starting PowerPoint.",
    )
    deck_plan_route.add_argument(
        "--render-deck-plan",
        action="store_true",
        help="Compile and render DeckPlan JSON through the governed COM pipeline.",
    )
    parser.add_argument(
        "--theme-id",
        help="Trusted governed theme override for --render-deck-plan.",
    )
    parser.add_argument(
        "--installed-font",
        action="append",
        default=[],
        help="Verified installed font name for deterministic rendering; repeatable.",
    )
    parser.add_argument(
        "--slide-width-in",
        type=float,
        help="Explicit slide width in inches for governed rendering.",
    )
    parser.add_argument(
        "--slide-height-in",
        type=float,
        help="Explicit slide height in inches for governed rendering.",
    )
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
    parser.add_argument(
        "--intake-template-library",
        action="store_true",
        help="Scan built-in template-library PPTX decks, export previews, and update template-library-review.xlsx.",
    )
    parser.add_argument("--list-addins", action="store_true", help="Print PowerPoint add-in inventory.")
    parser.add_argument(
        "--probe-plugin-apis",
        action="store_true",
        help="Read 32/64-bit registry metadata for add-in ProgIDs without starting PowerPoint or dispatching add-in code.",
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
        "--search-icons",
        help="Search Iconify icons by keyword and cache results. Does not require PowerPoint COM.",
    )
    parser.add_argument(
        "--icon-prefix",
        action="append",
        default=[],
        help="Filter Iconify results by icon set prefix such as mdi or bi. Can be repeated.",
    )
    parser.add_argument(
        "--icon-limit",
        type=int,
        default=50,
        help="Iconify search result limit, 1-999.",
    )
    parser.add_argument(
        "--download-icon",
        help="Download one Iconify icon id such as bi:tag-fill into assets/downloads/iconify.",
    )
    parser.add_argument(
        "--download-top-icon",
        action="store_true",
        help="After --search-icons, download the first matching Iconify result.",
    )
    parser.add_argument("--icon-color", help="Icon SVG color, e.g. #FF5722 or currentColor.")
    parser.add_argument("--icon-width", help="Icon SVG width parameter, e.g. 64 or 1em.")
    parser.add_argument("--icon-height", help="Icon SVG height parameter, e.g. 64 or 1em.")
    parser.add_argument("--icon-flip", choices=["horizontal", "vertical"], help="Iconify SVG flip parameter.")
    parser.add_argument("--icon-rotate", help="Iconify SVG rotate parameter, e.g. 90deg, 1, 2, or 3.")
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
    parser.add_argument("--dry-run", action="store_true", help="Describe requested actions without side effects.")
    parser.add_argument(
        "--no-output-deck",
        action="store_true",
        help="Run requested checks without saving an output deck.",
    )
    parser.add_argument(
        "--allow-overwrite",
        action="store_true",
        help="Explicitly allow the output deck to replace the source deck.",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Deprecated alias for --no-output-deck.",
    )
    parser.add_argument(
        "--keep-open",
        action="store_true",
        help="Leave PowerPoint open after the run. Use carefully with --attach-existing.",
    )
    args = parser.parse_args(argv)
    if (args.compile_deck_plan or args.render_deck_plan) and not args.deck_plan:
        parser.error("--deck-plan is required for DeckPlan compile/render routes")
    if (args.slide_width_in is None) != (args.slide_height_in is None):
        parser.error("--slide-width-in and --slide-height-in must be provided together")
    if args.slide_width_in is not None and (
        args.slide_width_in <= 0 or args.slide_height_in <= 0
    ):
        parser.error("slide dimensions must be positive")
    if args.no_save:
        print(NO_SAVE_WARNING, file=sys.stderr)
        args.no_output_deck = True
    return args


def collect_requested_actions(args: argparse.Namespace) -> list[str]:
    """Return requested operations without touching the filesystem or network."""

    actions: list[str] = []
    for attribute in (
        "compile_deck_plan",
        "render_deck_plan",
        "init_project",
        "search_images",
        "download_image",
        "search_icons",
        "download_icon",
        "intake_template_library",
        "extract_media",
        "make_ascii_temp_copy",
        "list_addins",
        "probe_plugin_apis",
        "clear_com_cache",
        "add_master_watermark",
        "export_slides",
        "export_qa",
        "audit_deck",
        "export_pdf",
    ):
        if getattr(args, attribute, False):
            actions.append(attribute)
    if getattr(args, "download_top_image", False):
        actions.append("download_top_image")
    if getattr(args, "download_top_icon", False):
        actions.append("download_top_icon")
    if not actions:
        actions.append("generate_deck")
    return actions


def _requested_path(project_dir: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else project_dir / path


def build_dry_run_result(args: argparse.Namespace, project_dir: str | Path) -> dict[str, Any]:
    """Build the side-effect-free dry-run payload."""

    base = Path(project_dir)
    would_write: list[str] = []
    warnings = [NO_SAVE_WARNING] if args.no_save else []

    if args.list_addins or args.probe_plugin_apis:
        terminal_actions = [
            action
            for action in collect_requested_actions(args)
            if action in {"list_addins", "probe_plugin_apis"}
        ]
        return {
            "schema_version": "1.0",
            "mode": "dry-run",
            "would_run": terminal_actions,
            "would_write": [],
            "warnings": warnings,
        }

    if args.init_project:
        would_write.extend(
            str(base / name)
            for name in ("REQUEST.md", "MODULES.md", "SLIDE_MAP.md", "scripts/run_window_pptx.py")
        )
    if args.search_images:
        would_write.append(str(base / ".window-pptx" / "cache" / "pixabay"))
    if args.download_image or args.download_top_image:
        would_write.extend(
            [
                str(base / "assets" / "downloads" / "pixabay"),
                str(base / ".window-pptx" / "asset_manifest.json"),
            ]
        )
    if args.search_icons:
        would_write.append(str(base / ".window-pptx" / "cache" / "iconify"))
    if args.download_icon or args.download_top_icon:
        would_write.extend(
            [
                str(base / "assets" / "downloads" / "iconify"),
                str(base / ".window-pptx" / "asset_manifest.json"),
            ]
        )
    if args.intake_template_library:
        would_write.append(str(base / ".window-pptx"))
    if args.extract_media:
        media_dir = args.media_dir or ".window-pptx/media"
        would_write.append(str(_requested_path(base, media_dir)))
    if args.make_ascii_temp_copy:
        would_write.append(str(base / ".window-pptx" / "temp"))
    if args.export_slides:
        export_dir = args.export_dir or ".window-pptx/exports"
        would_write.append(str(_requested_path(base, export_dir)))
    if args.export_qa:
        would_write.append(str(base / ".window-pptx" / "exports" / "qa"))
    if args.audit_deck:
        would_write.append(str(base / ".window-pptx" / "audits" / "deck_audit.json"))
    if not args.no_output_deck and not args.intake_template_library:
        output_path = _requested_path(base, args.output)
        would_write.append(str(output_path))
        if args.export_pdf:
            would_write.append(str(output_path.with_suffix(".pdf")))

    return {
        "schema_version": "1.0",
        "mode": "dry-run",
        "would_run": collect_requested_actions(args),
        "would_write": list(dict.fromkeys(would_write)),
        "warnings": warnings,
    }


def emit_result(
    payload: Any,
    as_json: bool,
    stream_out: TextIO,
    stream_err: TextIO,
) -> None:
    """Write one complete result document to the selected output stream."""

    try:
        if as_json or not isinstance(payload, str):
            rendered = json.dumps(payload, ensure_ascii=False, indent=2)
        else:
            rendered = payload
    except (TypeError, ValueError) as exc:
        print(f"window-pptx: could not serialize result: {exc}", file=stream_err)
        raise
    stream_out.write(rendered + "\n")


__all__ = [
    "build_dry_run_result",
    "collect_requested_actions",
    "emit_result",
    "parse_args",
]
