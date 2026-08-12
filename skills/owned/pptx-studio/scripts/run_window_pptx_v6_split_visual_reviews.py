#!/usr/bin/env python3
"""Run one fresh direct-vision context per split V6 deck."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess


ANALYZER = Path("/home/aimagician/.codex/skills/vision-analysis/scripts/analyze.mjs")


def _review(
    deck: str,
    images: tuple[Path, ...],
    *,
    prompt: Path,
    output_dir: Path,
) -> dict[str, object]:
    command = [
        "node",
        str(ANALYZER),
        *[value for image in images for value in ("--image", str(image))],
        "--prompt-file",
        str(prompt),
        "--allow-external-upload",
        "--json",
    ]
    completed = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if completed.returncode != 0:
        result: dict[str, object] = {
            "status": "ERROR",
            "deck": deck,
            "returncode": completed.returncode,
            "stderr": completed.stderr[-4000:],
        }
    else:
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            result = {
                "status": "ERROR",
                "deck": deck,
                "error": f"invalid analyzer JSON: {exc}",
                "stdout": completed.stdout[-4000:],
            }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{deck}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--split-dir", type=Path, required=True)
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument(
        "--deck",
        action="append",
        default=[],
        help="Optional exact deck stem to review; repeat for multiple decks.",
    )
    args = parser.parse_args()

    grouped: dict[str, list[Path]] = {}
    for image in sorted(args.split_dir.glob("*.png")):
        deck, separator, part = image.stem.rpartition("-")
        if separator and part in {"A", "B", "C"}:
            grouped.setdefault(deck, []).append(image.resolve())
    if args.deck:
        requested = set(args.deck)
        missing = requested - set(grouped)
        if missing:
            raise SystemExit(f"requested deck groups are missing: {sorted(missing)}")
        grouped = {deck: paths for deck, paths in grouped.items() if deck in requested}
    invalid = {deck: paths for deck, paths in grouped.items() if len(paths) != 3}
    expected = len(set(args.deck)) if args.deck else 15
    if len(grouped) != expected or invalid:
        raise SystemExit(
            f"expected {expected} complete A/B/C groups, observed={len(grouped)}, "
            f"invalid={sorted(invalid)}"
        )

    results: dict[str, dict[str, object]] = {}
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                _review,
                deck,
                tuple(paths),
                prompt=args.prompt_file.resolve(),
                output_dir=args.output_dir.resolve(),
            ): deck
            for deck, paths in grouped.items()
        }
        for future in as_completed(futures):
            deck = futures[future]
            result = future.result()
            results[deck] = result
            print(deck, result.get("status", "UNKNOWN"), flush=True)

    report = {
        "schema_version": "window-pptx-v6-split-visual-reviews.v1",
        "protocol": "one direct vision subprocess and fresh context per deck",
        "deck_count": len(results),
        "results": results,
    }
    (args.output_dir / "visual-review-suite-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if all(result.get("status") != "ERROR" for result in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
