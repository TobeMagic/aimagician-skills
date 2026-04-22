#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_TIMEOUT = 45
DEFAULT_OUTPUT = "./DESIGN.md"
DEFAULT_DEST_DIR = "./design-md"
DESIGN_URL_TEMPLATE = "https://getdesign.md/design-md/{brand}/DESIGN.md"


def load_brand_catalog() -> list[str]:
    assets_path = Path(__file__).resolve().parent.parent / "assets" / "brands.json"
    data = json.loads(assets_path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not all(isinstance(x, str) for x in data):
        raise SystemExit(f"Invalid brand catalog format: {assets_path}")
    return sorted(set(data))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch DESIGN.md files from getdesign.md for selected brands."
    )
    parser.add_argument(
        "--brand",
        action="append",
        default=[],
        help="Brand id to fetch. Repeat for multiple brands.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Fetch all brands from assets/brands.json.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available brands and exit.",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=(
            "Output path for single-brand mode. "
            f"Default: {DEFAULT_OUTPUT}"
        ),
    )
    parser.add_argument(
        "--dest-dir",
        default=DEFAULT_DEST_DIR,
        help=(
            "Destination directory for multi-brand mode. "
            f"Default: {DEFAULT_DEST_DIR}"
        ),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Request timeout in seconds. Default: {DEFAULT_TIMEOUT}",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned actions without downloading.",
    )
    return parser.parse_args()


def fetch_design_md(brand: str, timeout: int) -> str:
    url = DESIGN_URL_TEMPLATE.format(brand=brand)
    request = urllib.request.Request(
        url=url,
        headers={
            "User-Agent": "aimagician-design-md-router/1.0",
            "Accept": "text/markdown,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
    if not body.strip():
        raise RuntimeError(f"Empty response body: {url}")
    return body


def sanitize_filename(brand: str) -> str:
    return brand.replace("/", "_")


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def resolve_brands(args: argparse.Namespace, catalog: list[str]) -> list[str]:
    if args.all:
        return catalog

    selected = sorted(set(args.brand))
    if not selected:
        raise SystemExit("No brands selected. Use --brand or --all.")

    unknown = [x for x in selected if x not in catalog]
    if unknown:
        raise SystemExit(
            "Unknown brand(s): "
            + ", ".join(unknown)
            + ". Use --list to see supported brand ids."
        )
    return selected


def main() -> int:
    args = parse_args()
    catalog = load_brand_catalog()

    if args.list:
        for brand in catalog:
            print(brand)
        return 0

    brands = resolve_brands(args, catalog)

    single_mode = len(brands) == 1 and not args.all
    failures: list[str] = []

    for brand in brands:
        if single_mode:
            output_path = Path(args.output).expanduser().resolve()
        else:
            output_path = (
                Path(args.dest_dir).expanduser().resolve()
                / f"{sanitize_filename(brand)}.DESIGN.md"
            )

        if args.dry_run:
            print(f"[dry-run] {brand} -> {output_path}")
            continue

        try:
            content = fetch_design_md(brand=brand, timeout=args.timeout)
            write_file(output_path, content)
            print(f"Fetched {brand} -> {output_path}")
        except urllib.error.HTTPError as exc:
            failures.append(f"{brand}: HTTP {exc.code}")
        except urllib.error.URLError as exc:
            failures.append(f"{brand}: network error: {exc}")
        except Exception as exc:
            failures.append(f"{brand}: {exc}")

    if failures:
        print("Failed downloads:", file=sys.stderr)
        for item in failures:
            print(f"- {item}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
