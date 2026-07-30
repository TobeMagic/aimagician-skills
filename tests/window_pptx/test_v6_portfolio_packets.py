from __future__ import annotations

import importlib.util
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    ROOT
    / "skills"
    / "owned"
    / "window-pptx"
    / "scripts"
    / "build_window_pptx_v6_portfolio_packets.py"
)
SPEC = importlib.util.spec_from_file_location("v6_portfolio_packets", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_portfolio_registry_is_complete_and_disjoint() -> None:
    decks = [
        deck
        for portfolio in MODULE.PORTFOLIOS.values()
        for deck, slide_numbers in portfolio
        if len(slide_numbers) == 5
    ]
    assert set(MODULE.PORTFOLIOS) == {"portfolio-a", "portfolio-b", "portfolio-c"}
    assert len(decks) == 15
    assert len(set(decks)) == 15


def test_build_packets_uses_declared_real_pages(tmp_path: Path) -> None:
    proof_root = tmp_path / "proofs"
    for decks in MODULE.PORTFOLIOS.values():
        for deck, slide_numbers in decks:
            portable = proof_root / deck / "portable-proof"
            portable.mkdir(parents=True)
            for number in range(1, max(slide_numbers) + 1):
                Image.new("RGB", (1600, 900), (number, number, number)).save(
                    portable / f"slide-{number:03d}.png"
                )

    manifest = MODULE.build_packets(proof_root, tmp_path / "packets")

    assert manifest["portfolio_count"] == 3
    assert manifest["deck_count"] == 15
    assert sum(len(records) for records in manifest["portfolios"].values()) == 15
    assert all(
        len(record["source_sha256"]) == 5
        for records in manifest["portfolios"].values()
        for record in records
    )
    assert all(
        len(record["split_review"]) == 3
        for records in manifest["portfolios"].values()
        for record in records
    )
    assert all(
        Path(records[0]["cover_sheet"]).is_file()
        for records in manifest["portfolios"].values()
    )
