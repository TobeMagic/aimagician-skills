#!/usr/bin/env python3
"""Run three independent direct-vision portfolio reviews for V6 closure."""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import subprocess


ANALYZER = Path("/home/aimagician/.codex/skills/vision-analysis/scripts/analyze.mjs")


def _review(
    portfolio: str,
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
        timeout=360,
    )
    if completed.returncode != 0:
        result: dict[str, object] = {
            "status": "ERROR",
            "portfolio": portfolio,
            "returncode": completed.returncode,
            "stderr": completed.stderr[-4000:],
        }
    else:
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            result = {
                "status": "ERROR",
                "portfolio": portfolio,
                "error": f"invalid analyzer JSON: {exc}",
                "stdout": completed.stdout[-4000:],
            }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{portfolio}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-dir", type=Path, required=True)
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--images-per-portfolio", type=int, default=5)
    args = parser.parse_args()

    grouped: dict[str, tuple[Path, ...]] = {}
    for portfolio_dir in sorted(args.packet_dir.glob("portfolio-*")):
        if portfolio_dir.is_dir():
            grouped[portfolio_dir.name] = tuple(sorted(portfolio_dir.glob("*.png")))
    invalid = {
        name: len(images)
        for name, images in grouped.items()
        if len(images) != args.images_per_portfolio
    }
    if len(grouped) != 3 or invalid:
        raise SystemExit(
            f"expected three portfolios with {args.images_per_portfolio} image(s) each; "
            f"observed={len(grouped)}, invalid={invalid}"
        )

    results: dict[str, dict[str, object]] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {
            pool.submit(
                _review,
                portfolio,
                images,
                prompt=args.prompt_file.resolve(),
                output_dir=args.output_dir.resolve(),
            ): portfolio
            for portfolio, images in grouped.items()
        }
        for future in as_completed(futures):
            portfolio = futures[future]
            result = future.result()
            results[portfolio] = result
            print(portfolio, result.get("status", "UNKNOWN"), flush=True)

    report = {
        "schema_version": "window-pptx-v6-portfolio-reviews.v1",
        "protocol": "one direct multimodal subprocess and fresh context per portfolio",
        "portfolio_count": len(results),
        "results": results,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "portfolio-review-suite-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0 if all(result.get("status") != "ERROR" for result in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
