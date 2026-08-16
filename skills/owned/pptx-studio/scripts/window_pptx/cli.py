"""Command-line parsing and result formatting for pptx-studio."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence, TextIO


NO_SAVE_WARNING = (
    "pptx-studio: warning: --no-save is deprecated; "
    "use --no-output-deck instead."
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse pptx-studio arguments, including an explicit argument sequence."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate governed editable PPTX with the portable PptxGenJS backend, "
            "or explicitly select legacy PowerPoint COM operations."
        )
    )
    parser.add_argument("--project-dir", required=True, help="PowerPoint project folder.")
    parser.add_argument("--request", default="REQUEST.md", help="Request file name or path.")
    parser.add_argument("--template", help="Template/source deck path. Defaults to auto-detect.")
    parser.add_argument("--output", default="output/final.pptx", help="Output PPTX path.")
    parser.add_argument(
        "--backend",
        default="auto",
        choices=["auto", "pptxgenjs", "com"],
        help=(
            "Governed render backend. auto selects the portable PptxGenJS "
            "backend; COM remains an explicit legacy/high-feature route."
        ),
    )
    parser.add_argument(
        "--verification",
        default=None,
        choices=["portable", "powerpoint"],
        help=(
            "Verification level. portable requires OOXML + LibreOffice/Poppler; "
            "powerpoint adds read-only PowerPoint certification."
        ),
    )
    parser.add_argument(
        "--deck-plan",
        help="DeckPlan v1 JSON path, relative to --project-dir unless absolute.",
    )
    generation_route = parser.add_mutually_exclusive_group()
    generation_route.add_argument(
        "--compile-deck-plan",
        action="store_true",
        help="Validate and compile DeckPlan JSON without starting PowerPoint.",
    )
    generation_route.add_argument(
        "--render-deck-plan",
        action="store_true",
        help="Compile and render DeckPlan JSON through the governed backend pipeline.",
    )
    parser.add_argument(
        "--fact-store",
        help="Trusted FactStore v1 JSON path for weak-model or physical-assembly routes.",
    )
    parser.add_argument(
        "--fact-store-sha256",
        help="Externally locked FactStore file SHA-256 for physical assembly.",
    )
    parser.add_argument(
        "--brief-plan",
        help="Restricted BriefPlan v1 JSON path for the weak-model route.",
    )
    parser.add_argument(
        "--brief-retry-plan",
        action="append",
        default=[],
        help=(
            "Optional replacement BriefPlan after a structured validation failure; "
            "repeat at most twice. After all supplied attempts fail, the compiler "
            "uses a deterministic fact-safe default."
        ),
    )
    generation_route.add_argument(
        "--normalize-brief-plan",
        action="store_true",
        help="Normalize harmless BriefPlan serialization aliases without rendering.",
    )
    generation_route.add_argument(
        "--compile-brief-plan",
        action="store_true",
        help="Compile FactStore + BriefPlan into NarrativePlan, DeckPlan, and CompiledDeck.",
    )
    generation_route.add_argument(
        "--render-brief-plan",
        action="store_true",
        help="Compile and render the governed weak-model route through the selected backend.",
    )
    generation_route.add_argument(
        "--render-template-pack",
        action="store_true",
        help=(
            "Adapt an authorized physical TemplatePack through portable OOXML "
            "slot replacement, then verify it with LibreOffice/Poppler."
        ),
    )
    generation_route.add_argument(
        "--render-assembly-plan",
        action="store_true",
        help=(
            "Assemble an editable PPTX by physically reusing certified page "
            "templates selected in an AssemblyPlan v1."
        ),
    )
    parser.add_argument(
        "--assembly-plan",
        help="AssemblyPlan v1 JSON path for --render-assembly-plan.",
    )
    parser.add_argument(
        "--assembly-library",
        help="Compiled page-template library-v4 JSON path.",
    )
    parser.add_argument(
        "--assembly-private-root",
        help="Private template-library root; never resolved from the client folder.",
    )
    parser.add_argument(
        "--assembly-report",
        help="Physical assembly report path. Defaults under .pptx-studio/audits.",
    )
    parser.add_argument(
        "--assembly-rule-qa-report",
        help="Physical rule-QA report path. Defaults under .pptx-studio/audits.",
    )
    parser.add_argument(
        "--assembly-max-output-size-bytes",
        type=int,
        default=33_941_179,
        help="Maximum accepted physical PPTX size. Default: 33941179 bytes.",
    )
    parser.add_argument(
        "--template-pack",
        help="Registered TemplatePack id or manifest path for --render-template-pack.",
    )
    parser.add_argument(
        "--template-bindings",
        help="TemplatePack binding JSON path, relative to --project-dir unless absolute.",
    )
    parser.add_argument(
        "--template-selection-plan",
        help=(
            "Optional production template-selection-plan.json. Must be paired "
            "with --slide-blueprints on --render-template-pack."
        ),
    )
    parser.add_argument(
        "--slide-blueprints",
        help=(
            "Optional production slide-blueprints.json. Must be paired with "
            "--template-selection-plan on --render-template-pack."
        ),
    )
    parser.add_argument(
        "--brand-spec",
        help="Optional trusted BrandSpec v1 JSON path for governed rendering.",
    )
    parser.add_argument(
        "--direction-mode",
        default="auto",
        choices=["auto", "interactive", "locked"],
        help="Art-direction decision mode for the BriefPlan route. Default: auto.",
    )
    parser.add_argument(
        "--direction-id",
        help="Registered art-direction id; required only with --direction-mode locked.",
    )
    parser.add_argument(
        "--design-system-version",
        default="art-direction-v1",
        choices=["legacy-v5", "art-direction-v1"],
        help="Governed design-system selector. Default: art-direction-v1.",
    )
    parser.add_argument(
        "--theme-id",
        help="Trusted governed theme override for a render route.",
    )
    parser.add_argument(
        "--installed-font",
        action="append",
        default=[],
        help="Verified installed font name for deterministic rendering; repeatable.",
    )
    parser.add_argument(
        "--asset-manifest",
        help=(
            "Governed render asset manifest JSON, relative to --project-dir unless "
            "absolute. Each binding must include Phase 24 provenance evidence."
        ),
    )
    parser.add_argument(
        "--asset-manifest-sha256",
        help="Externally locked asset-manifest file SHA-256 for physical assembly.",
    )
    parser.add_argument(
        "--connective-copy",
        help="Locked connective-copy v1 JSON path for physical assembly.",
    )
    parser.add_argument(
        "--connective-copy-sha256",
        help="Externally locked connective-copy file SHA-256 for physical assembly.",
    )
    parser.add_argument(
        "--generate-assets-with-agnes",
        action="store_true",
        help=(
            "Materialize eligible BriefPlan visual intents through the direct "
            "Agnes image route. Requires AGNES_API_KEY and --render-brief-plan."
        ),
    )
    parser.add_argument(
        "--asset-output-dir",
        default=".pptx-studio/generated-assets",
        help=(
            "Frozen generated-asset directory, relative to --project-dir unless "
            "absolute. Used only with --generate-assets-with-agnes."
        ),
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
        help="Create standard pptx-studio workspace folders plus planning files if missing.",
    )
    parser.add_argument(
        "--extract-media",
        action="store_true",
        help="Extract ppt/media assets from the template/source deck into .pptx-studio/media or --media-dir.",
    )
    parser.add_argument(
        "--media-dir",
        help="Directory for extracted media. Defaults to .pptx-studio/media under the project.",
    )
    parser.add_argument(
        "--export-slides",
        help="Comma-separated slide numbers/ranges to export to PNG, e.g. 4,6,8-10.",
    )
    parser.add_argument(
        "--export-dir",
        help="Directory for exported slide PNGs. Defaults to .pptx-studio/exports under the project.",
    )
    parser.add_argument(
        "--make-ascii-temp-copy",
        action="store_true",
        help="Copy the template/source deck to an ASCII temp filename under .pptx-studio/temp before COM work.",
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
    parser.add_argument(
        "--com-doctor",
        action="store_true",
        help="Inspect PowerPoint/_Application TypeLib registration without changing it.",
    )
    parser.add_argument(
        "--certify-pptx",
        help=(
            "Read-only PowerPoint certification target. Fails closed if an existing "
            "POWERPNT.EXE process prevents unique ownership proof."
        ),
    )
    parser.add_argument(
        "--portable-verification-report",
        help=(
            "portable-verification.json that hash-binds --certify-pptx to a "
            "passed PptxGenJS + OOXML + LibreOffice/Poppler result."
        ),
    )
    parser.add_argument(
        "--no-html-proof",
        action="store_true",
        help=(
            "Skip the optional deterministic RenderPlan-derived HTML proof. "
            "This never changes PPTX generation or portable hard gates."
        ),
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
        help="Export all slides to .pptx-studio/exports/qa for visual QA.",
    )
    parser.add_argument(
        "--audit-deck",
        action="store_true",
        help="Write .pptx-studio/audits/deck_audit.json with slide, font, shape, and animation metadata.",
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
    verification_was_explicit = args.verification is not None
    if args.backend == "com":
        if verification_was_explicit:
            parser.error(
                "--verification applies only to the portable backend; explicit "
                "COM uses its legacy PowerPoint reopen/export gates"
            )
        args.verification = "legacy-com"
    else:
        args.verification = args.verification or "portable"
    deck_route = args.compile_deck_plan or args.render_deck_plan
    brief_route = (
        args.normalize_brief_plan
        or args.compile_brief_plan
        or args.render_brief_plan
    )
    template_pack_route = args.render_template_pack
    assembly_route = args.render_assembly_plan
    if deck_route and not args.deck_plan:
        parser.error("--deck-plan is required for DeckPlan compile/render routes")
    if brief_route and (not args.fact_store or not args.brief_plan):
        parser.error(
            "--fact-store and --brief-plan are required for BriefPlan routes"
        )
    if template_pack_route and (not args.template_pack or not args.template_bindings):
        parser.error(
            "--template-pack and --template-bindings are required for "
            "--render-template-pack"
        )
    if assembly_route and not args.dry_run and not all(
        (
            args.assembly_plan,
            args.fact_store,
            args.fact_store_sha256,
            args.asset_manifest,
            args.asset_manifest_sha256,
            args.connective_copy,
            args.connective_copy_sha256,
        )
    ):
        parser.error(
            "--assembly-plan, --fact-store, --fact-store-sha256, "
            "--asset-manifest, --asset-manifest-sha256, --connective-copy, "
            "and --connective-copy-sha256 are required for "
            "--render-assembly-plan"
        )
    if any(
        (
            args.assembly_library,
            args.assembly_private_root,
            args.assembly_report,
            args.assembly_rule_qa_report,
        )
    ) and not assembly_route:
        parser.error(
            "--assembly-library/--assembly-private-root/--assembly-report/"
            "--assembly-rule-qa-report "
            "require --render-assembly-plan"
        )
    if (args.template_pack or args.template_bindings) and not template_pack_route:
        parser.error(
            "--template-pack/--template-bindings require --render-template-pack"
        )
    selection_sidecars = bool(args.template_selection_plan), bool(args.slide_blueprints)
    if selection_sidecars[0] != selection_sidecars[1]:
        parser.error(
            "--template-selection-plan and --slide-blueprints must be supplied together"
        )
    if any(selection_sidecars) and not template_pack_route:
        parser.error(
            "template selection sidecars require --render-template-pack"
        )
    if len(args.brief_retry_plan) > 2:
        parser.error("--brief-retry-plan may be repeated at most twice")
    if args.brief_retry_plan and (
        not brief_route or args.normalize_brief_plan
    ):
        parser.error(
            "--brief-retry-plan requires --compile-brief-plan or --render-brief-plan"
        )
    if args.direction_mode == "locked" and not args.direction_id:
        parser.error("--direction-id is required with --direction-mode locked")
    if args.direction_id and args.direction_mode != "locked":
        parser.error("--direction-id requires --direction-mode locked")
    if (args.direction_mode != "auto" or args.direction_id) and not brief_route:
        parser.error("art-direction controls require a BriefPlan route")
    if args.brand_spec and not args.render_brief_plan:
        parser.error("--brand-spec requires --render-brief-plan")
    if (args.slide_width_in is None) != (args.slide_height_in is None):
        parser.error("--slide-width-in and --slide-height-in must be provided together")
    if args.slide_width_in is not None and not all(
        1 <= value <= 56
        for value in (args.slide_width_in, args.slide_height_in)
    ):
        parser.error("slide dimensions must be between 1 and 56 inches")
    if (args.render_deck_plan or args.render_brief_plan) and args.attach_existing:
        parser.error("governed render routes cannot use --attach-existing")
    if args.asset_manifest and not (
        args.render_deck_plan or args.render_brief_plan or assembly_route
    ):
        parser.error("--asset-manifest requires a render route")
    if (
        args.fact_store_sha256
        or args.asset_manifest_sha256
        or args.connective_copy
        or args.connective_copy_sha256
    ) and not assembly_route:
        parser.error(
            "physical authority paths/hashes require --render-assembly-plan"
        )
    if args.assembly_max_output_size_bytes < 1:
        parser.error("--assembly-max-output-size-bytes must be positive")
    if args.generate_assets_with_agnes and not args.render_brief_plan:
        parser.error(
            "--generate-assets-with-agnes requires --render-brief-plan"
        )
    if (args.backend != "auto" or args.verification != "portable") and not (
        args.render_deck_plan or args.render_brief_plan or template_pack_route or assembly_route
    ):
        parser.error("--backend/--verification require a governed render route")
    if template_pack_route and (
        args.backend != "auto" or args.verification != "portable"
    ):
        parser.error(
            "TemplatePack adaptation uses portable OOXML and portable verification"
        )
    if args.no_html_proof and not (args.render_deck_plan or args.render_brief_plan):
        parser.error("--no-html-proof requires a governed render route")
    if args.com_doctor and (
        deck_route or brief_route or template_pack_route or assembly_route or args.certify_pptx
    ):
        parser.error("--com-doctor cannot be combined with generation or certification")
    if args.certify_pptx and (deck_route or brief_route or template_pack_route or assembly_route):
        parser.error("--certify-pptx is a standalone verification route")
    if args.certify_pptx and not args.portable_verification_report:
        parser.error(
            "--portable-verification-report is required with --certify-pptx"
        )
    if args.portable_verification_report and not args.certify_pptx:
        parser.error(
            "--portable-verification-report requires --certify-pptx"
        )
    conflicting_deck_actions = {
        "init_project",
        "search_images",
        "download_image",
        "download_top_image",
        "search_icons",
        "download_icon",
        "download_top_icon",
        "intake_template_library",
        "extract_media",
        "list_addins",
        "probe_plugin_apis",
        "add_master_watermark",
        "export_slides",
        "export_qa",
        "audit_deck",
    }
    if deck_route or brief_route or template_pack_route or assembly_route:
        route_conflicts = set(conflicting_deck_actions)
        if args.render_deck_plan or args.render_brief_plan:
            route_conflicts -= {"export_slides", "export_qa"}
        conflicts = sorted(
            name for name in route_conflicts if getattr(args, name)
        )
        if conflicts:
            parser.error(
                "governed generation routes cannot be combined with: "
                + ", ".join(f"--{name.replace('_', '-')}" for name in conflicts)
            )
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
        "normalize_brief_plan",
        "compile_brief_plan",
        "render_brief_plan",
        "render_template_pack",
        "render_assembly_plan",
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
        "com_doctor",
        "certify_pptx",
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

    if args.com_doctor or args.certify_pptx:
        return {
            "schema_version": "1.0",
            "mode": "dry-run",
            "would_run": collect_requested_actions(args),
            "would_write": (
                []
                if args.com_doctor
                else [str(base / ".pptx-studio" / "audits" / "powerpoint-certification")]
            ),
            "warnings": warnings,
        }

    if args.render_brief_plan and args.direction_mode == "interactive":
        return {
            "schema_version": "1.0",
            "mode": "dry-run",
            "would_run": collect_requested_actions(args),
            "would_write": [],
            "warnings": [
                *warnings,
                "Interactive art-direction selection stops before COM and file writes.",
            ],
        }

    if args.init_project:
        would_write.extend(
            str(base / name)
            for name in ("REQUEST.md", "MODULES.md", "SLIDE_MAP.md", "scripts/run_window_pptx.py")
        )
    if args.search_images:
        would_write.append(str(base / ".pptx-studio" / "cache" / "pixabay"))
    if args.download_image or args.download_top_image:
        would_write.extend(
            [
                str(base / "assets" / "downloads" / "pixabay"),
                str(base / ".pptx-studio" / "asset_manifest.json"),
            ]
        )
    if args.search_icons:
        would_write.append(str(base / ".pptx-studio" / "cache" / "iconify"))
    if args.download_icon or args.download_top_icon:
        would_write.extend(
            [
                str(base / "assets" / "downloads" / "iconify"),
                str(base / ".pptx-studio" / "asset_manifest.json"),
            ]
        )
    if args.intake_template_library:
        would_write.append(str(base / ".pptx-studio"))
    if args.extract_media:
        media_dir = args.media_dir or ".pptx-studio/media"
        would_write.append(str(_requested_path(base, media_dir)))
    if args.make_ascii_temp_copy:
        would_write.append(str(base / ".pptx-studio" / "temp"))
    if args.export_slides:
        export_dir = args.export_dir or ".pptx-studio/exports"
        would_write.append(str(_requested_path(base, export_dir)))
    if args.export_qa:
        would_write.append(str(base / ".pptx-studio" / "exports" / "qa"))
    if args.audit_deck:
        would_write.append(str(base / ".pptx-studio" / "audits" / "deck_audit.json"))
    if args.render_deck_plan or args.render_brief_plan:
        if args.backend == "com":
            would_write.extend(
                [
                    str(base / ".pptx-studio" / "audits" / "quality-report.json"),
                    str(base / ".pptx-studio" / "audits" / "repair-log.json"),
                ]
            )
        else:
            would_write.extend(
                [
                    str(base / ".pptx-studio" / "audits" / "quality-report.v2.json"),
                    str(base / ".pptx-studio" / "audits" / "portable-proof"),
                ]
            )
            if not args.no_html_proof:
                would_write.append(
                    str(base / ".pptx-studio" / "audits" / "render-proof.html")
                )
    if args.render_template_pack:
        would_write.extend(
            [
                str(base / ".pptx-studio" / "audits" / "template-adaptation-report.json"),
                str(base / ".pptx-studio" / "audits" / "template-portable-proof"),
            ]
        )
        if args.template_selection_plan:
            would_write.append(
                str(
                    base
                    / ".pptx-studio"
                    / "audits"
                    / "candidate-materialization-report.json"
                )
            )
    if args.render_assembly_plan:
        would_write.extend(
            [
                str(base / ".pptx-studio" / "audits" / "physical-assembly-report.json"),
                str(_requested_path(base, args.output)),
            ]
        )
    if args.render_brief_plan:
        would_write.extend(
            [
                str(base / ".pptx-studio" / "audits" / "quality-report.v2.json"),
                str(base / ".pptx-studio" / "audits" / "repair-log.v2.json"),
                str(base / ".pptx-studio" / "audits" / "quality-v2-previews"),
                str(base / ".pptx-studio" / "audits" / "narrative-plan.json"),
                str(
                    base
                    / ".pptx-studio"
                    / "audits"
                    / "asset-materialization.json"
                ),
                str(base / ".pptx-studio" / "audits" / "generation-manifest.json"),
                str(base / ".pptx-studio" / "audits" / "template-selection-plan.json"),
                str(base / ".pptx-studio" / "audits" / "slide-blueprints.json"),
                str(
                    base
                    / ".pptx-studio"
                    / "audits"
                    / "candidate-materialization-report.json"
                ),
            ]
        )
        if args.generate_assets_with_agnes:
            generated = Path(args.asset_output_dir)
            would_write.append(
                str(generated if generated.is_absolute() else base / generated)
            )
        if args.design_system_version == "art-direction-v1":
            would_write.append(
                str(base / ".pptx-studio" / "audits" / "direction-decision.json")
            )
    non_render_compile = (
        args.compile_deck_plan
        or args.normalize_brief_plan
        or args.compile_brief_plan
    )
    if (
        not args.no_output_deck
        and not args.intake_template_library
        and not non_render_compile
    ):
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
        print(f"pptx-studio: could not serialize result: {exc}", file=stream_err)
        raise
    stream_out.write(rendered + "\n")


__all__ = [
    "build_dry_run_result",
    "collect_requested_actions",
    "emit_result",
    "parse_args",
]
