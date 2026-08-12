#!/usr/bin/env python3
"""Build deterministic five-deck portfolio packets for the V6 closure review."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from window_pptx.evidence import (  # noqa: E402
    validate_portable_slide_pngs,
    write_contact_sheet,
)


PORTFOLIOS: dict[str, tuple[tuple[str, tuple[int, ...]], ...]] = {
    "portfolio-a": (
        ("annual-work-report-reference-anchor", (1, 3, 7, 13, 15)),
        ("project-proposal-reference-anchor", (1, 3, 11, 13, 20)),
        ("market-analysis-reference-anchor", (1, 3, 11, 13, 20)),
        ("training-course-reference-anchor", (1, 3, 11, 13, 20)),
        ("ecommerce-marketing-plan-reference-anchor", (1, 3, 11, 13, 20)),
    ),
    "portfolio-b": (
        ("campus-competition-defense-reference-anchor", (1, 3, 9, 13, 18)),
        ("business-operations-review-reference-anchor", (1, 3, 11, 13, 20)),
        ("product-launch-reference-anchor", (1, 3, 11, 13, 20)),
        ("investor-pitch-reference-anchor", (1, 3, 11, 13, 20)),
        ("brand-company-introduction-reference-anchor", (1, 3, 11, 13, 20)),
    ),
    "portfolio-c": (
        ("academic-thesis-defense-reference-anchor", (1, 3, 10, 13, 19)),
        ("sales-proposal-reference-anchor", (1, 3, 11, 13, 20)),
        ("strategy-planning-reference-anchor", (1, 3, 11, 13, 20)),
        ("data-analysis-report-reference-anchor", (1, 3, 11, 13, 20)),
        ("project-kickoff-reference-anchor", (1, 3, 11, 13, 20)),
    ),
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_packets(proof_root: Path, output_dir: Path) -> dict[str, object]:
    """Build one five-slide contact sheet for every deck in each portfolio."""

    output_dir.mkdir(parents=True, exist_ok=True)
    observed: set[str] = set()
    manifest_portfolios: dict[str, list[dict[str, object]]] = {}
    for portfolio, decks in PORTFOLIOS.items():
        portfolio_dir = output_dir / portfolio
        portfolio_dir.mkdir(parents=True, exist_ok=True)
        records: list[dict[str, object]] = []
        for deck, slide_numbers in decks:
            if deck in observed:
                raise ValueError(f"deck appears in more than one portfolio: {deck}")
            observed.add(deck)
            source_dir = proof_root / deck / "portable-proof"
            pages = tuple(source_dir / f"slide-{number:03d}.png" for number in slide_numbers)
            missing = tuple(str(page) for page in pages if not page.is_file())
            if missing:
                raise FileNotFoundError(f"missing portable pages for {deck}: {missing}")
            staged_dir = portfolio_dir / "_sources" / deck / "portable-proof"
            staged_dir.mkdir(parents=True, exist_ok=True)
            staged_pages: list[Path] = []
            for index, page in enumerate(pages, start=1):
                staged_page = staged_dir / f"slide-{index:03d}.png"
                shutil.copyfile(page, staged_page)
                staged_pages.append(staged_page)
            target = portfolio_dir / f"{len(records) + 1:02d}-{deck}.png"
            if not target.is_file():
                write_contact_sheet(
                    staged_pages,
                    target,
                    slide_numbers=slide_numbers,
                    banner=f"DECK {len(records) + 1} · {deck.removesuffix('-reference-anchor')}",
                )
            cover_target = (
                output_dir
                / "cover-only"
                / portfolio
                / f"{len(records) + 1:02d}-{deck}.png"
            )
            cover_target.parent.mkdir(parents=True, exist_ok=True)
            if not cover_target.is_file():
                shutil.copyfile(source_dir / "slide-001.png", cover_target)

            all_pages = validate_portable_slide_pngs(
                tuple(sorted(source_dir.glob("slide-*.png")))
            )
            if len(all_pages) < 3:
                raise ValueError(f"deck requires at least three pages for split review: {deck}")
            base, remainder = divmod(len(all_pages), 3)
            split_sizes = tuple(base + (1 if item < remainder else 0) for item in range(3))
            split_records: list[dict[str, object]] = []
            cursor = 0
            for part, size in zip(("A", "B", "C"), split_sizes, strict=True):
                selected_pages = all_pages[cursor : cursor + size]
                actual_numbers = tuple(range(cursor + 1, cursor + size + 1))
                cursor += size
                split_source = (
                    output_dir / "_split-sources" / deck / part / "portable-proof"
                )
                split_source.mkdir(parents=True, exist_ok=True)
                staged_split: list[Path] = []
                for index, page in enumerate(selected_pages, start=1):
                    staged_page = split_source / f"slide-{index:03d}.png"
                    shutil.copyfile(page, staged_page)
                    staged_split.append(staged_page)
                split_target = output_dir / "split" / f"{deck}-{part}.png"
                if not split_target.is_file():
                    write_contact_sheet(
                        staged_split,
                        split_target,
                        slide_numbers=actual_numbers,
                        banner=(
                            f"Candidate only · Slides "
                            f"{actual_numbers[0]:02d}-{actual_numbers[-1]:02d}"
                        ),
                    )
                split_records.append(
                    {
                        "part": part,
                        "slide_numbers": list(actual_numbers),
                        "sheet": str(split_target.resolve()),
                        "sheet_sha256": _sha256(split_target),
                    }
                )

            records.append(
                {
                    "deck": deck,
                    "slide_numbers": list(slide_numbers),
                    "sheet": str(target.resolve()),
                    "sheet_sha256": _sha256(target),
                    "cover": str(cover_target.resolve()),
                    "cover_sha256": _sha256(cover_target),
                    "split_review": split_records,
                    "source_sha256": [_sha256(page) for page in pages],
                }
            )
        cover_sheet_source = (
            output_dir / "_cover-sheet-sources" / portfolio / "portable-proof"
        )
        cover_sheet_source.mkdir(parents=True, exist_ok=True)
        cover_sheet_pages: list[Path] = []
        for index, record in enumerate(records, start=1):
            staged_cover = cover_sheet_source / f"slide-{index:03d}.png"
            shutil.copyfile(Path(str(record["cover"])), staged_cover)
            cover_sheet_pages.append(staged_cover)
        cover_sheet = output_dir / "cover-sheets" / portfolio / f"{portfolio}.png"
        if not cover_sheet.is_file():
            write_contact_sheet(
                cover_sheet_pages,
                cover_sheet,
                slide_numbers=range(1, len(cover_sheet_pages) + 1),
                banner=f"{portfolio.upper()} · FIVE DISTINCT SCENARIO COVERS",
            )
        for record in records:
            record["cover_sheet"] = str(cover_sheet.resolve())
            record["cover_sheet_sha256"] = _sha256(cover_sheet)
        manifest_portfolios[portfolio] = records

    manifest: dict[str, object] = {
        "schema_version": "window-pptx-v6-portfolio-packets.v1",
        "protocol": (
            "three disjoint cover portfolios plus one three-part complete-deck "
            "packet per scenario; all evidence comes from real portable slides"
        ),
        "proof_root": str(proof_root.resolve()),
        "portfolio_count": len(manifest_portfolios),
        "deck_count": len(observed),
        "portfolios": manifest_portfolios,
    }
    (output_dir / "portfolio-packet-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--proof-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = build_packets(args.proof_root.resolve(), args.output_dir.resolve())
    print(
        json.dumps(
            {
                "portfolio_count": manifest["portfolio_count"],
                "deck_count": manifest["deck_count"],
                "manifest": str((args.output_dir / "portfolio-packet-manifest.json").resolve()),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
