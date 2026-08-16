"""Private, labeled contact sheets for Gaojie visual selection evidence."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from pathlib import Path
from typing import Any


def _font(size: int) -> Any:
    from PIL import ImageFont

    candidates = (
        Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
        Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    )
    for candidate in candidates:
        if candidate.is_file():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def _atomic_image(image: Any, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".png",
        dir=target.parent,
    )
    os.close(fd)
    try:
        image.save(temporary, format="PNG", optimize=True)
        os.replace(temporary, target)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def _atomic_json(value: dict[str, Any], target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(
        prefix=f".{target.name}.",
        suffix=".json",
        dir=target.parent,
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def _safe_component(value: str, fallback: str) -> str:
    normalized = "".join(
        character if character.isalnum() or character in "-_ " else "_"
        for character in value.strip()
    ).strip(" .")
    return normalized[:80] or fallback


def _fit_preview(path: Path, width: int, height: int) -> Any:
    from PIL import Image, ImageOps

    with Image.open(path) as source:
        source.load()
        image = source.convert("RGB")
    return ImageOps.contain(image, (width, height))


def _category_sheet(
    *,
    category_name: str,
    category_id: str,
    entries: list[tuple[str, Path]],
    columns: int,
) -> Any:
    from PIL import Image, ImageDraw

    cell_width = 360
    image_height = 203
    label_height = 42
    gap = 20
    margin = 32
    header_height = 78
    rows = max(1, (len(entries) + columns - 1) // columns)
    width = margin * 2 + columns * cell_width + (columns - 1) * gap
    height = (
        header_height
        + margin
        + rows * (image_height + label_height)
        + (rows - 1) * gap
        + margin
    )
    canvas = Image.new("RGB", (width, height), "#101318")
    draw = ImageDraw.Draw(canvas)
    draw.text(
        (margin, 22),
        f"{int(category_id):03d}  {category_name}",
        fill="#F5F1E8",
        font=_font(30),
    )
    draw.text(
        (width - margin, 30),
        f"{len(entries)} selected",
        fill="#AEB6C2",
        font=_font(18),
        anchor="ra",
    )

    for index, (item_id, preview_path) in enumerate(entries):
        row, column = divmod(index, columns)
        left = margin + column * (cell_width + gap)
        top = header_height + margin + row * (image_height + label_height + gap)
        draw.rounded_rectangle(
            (left - 2, top - 2, left + cell_width + 2, top + image_height + 2),
            radius=8,
            fill="#2A3039",
        )
        preview = _fit_preview(preview_path, cell_width, image_height)
        x = left + (cell_width - preview.width) // 2
        y = top + (image_height - preview.height) // 2
        canvas.paste(preview, (x, y))
        draw.text(
            (left, top + image_height + 10),
            f"{index + 1:02d}  {item_id[:12]}",
            fill="#D7DCE3",
            font=_font(17),
        )
    return canvas


def build_gaojie_contact_sheets(
    private_root: Path | str,
    *,
    columns: int = 3,
) -> dict[str, Any]:
    """Build category and overview sheets from the secret-free sync state."""

    if not 2 <= columns <= 5:
        raise ValueError("columns must be between two and five")
    root = Path(private_root).resolve()
    state_path = root / "state" / "gaojie-sync.json"
    try:
        state_bytes = state_path.read_bytes()
        state = json.loads(state_bytes)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("Gaojie sync state is missing or unreadable") from exc
    if state.get("schema_version") != "gaojie-sync.v2":
        raise ValueError("Gaojie sync state schema is unsupported")
    categories = state.get("categories")
    inventory = state.get("inventory")
    selections = state.get("selections")
    if not all(isinstance(value, dict) for value in (categories, inventory, selections)):
        raise ValueError("Gaojie sync state is incomplete")

    output_root = root / "evidence" / "gaojie"
    category_root = output_root / "categories"
    records: list[dict[str, Any]] = []
    generated: list[tuple[dict[str, Any], Path]] = []
    for category_key in sorted(
        categories,
        key=lambda key: int(categories[key]["category_id"]),
    ):
        category = categories[category_key]
        selection = selections.get(category_key, {})
        selected_ids = selection.get("selected_item_ids", [])
        entries: list[tuple[str, Path]] = []
        missing: list[str] = []
        for item_id in selected_ids:
            item = inventory.get(item_id, {})
            relative = item.get("preview_path")
            candidate = (root / relative).resolve() if isinstance(relative, str) else None
            if (
                candidate is None
                or not candidate.is_file()
                or root not in candidate.parents
            ):
                missing.append(item_id)
                continue
            entries.append((item_id, candidate))
        category_id = str(category["category_id"])
        category_name = str(category["name"])
        filename = (
            f"{int(category_id):03d}-"
            f"{_safe_component(category_name, category_id)}.png"
        )
        target = category_root / filename
        sheet = _category_sheet(
            category_name=category_name,
            category_id=category_id,
            entries=entries,
            columns=columns,
        )
        _atomic_image(sheet, target)
        record = {
            "category_key_sha256": hashlib.sha256(
                category_key.encode("utf-8")
            ).hexdigest(),
            "category_id": category_id,
            "category_name": category_name,
            "selected_count": len(selected_ids),
            "rendered_count": len(entries),
            "missing_item_ids": missing,
            "sheet_path": target.relative_to(root).as_posix(),
            "selection_rule_version": selection.get("rule_version"),
            "selection_gain": selection.get("selection_gain"),
        }
        records.append(record)
        generated.append((record, target))

    from PIL import Image, ImageDraw, ImageOps

    overview_columns = 4
    tile_width = 360
    tile_height = 245
    gap = 18
    margin = 28
    header = 72
    rows = max(1, (len(generated) + overview_columns - 1) // overview_columns)
    overview = Image.new(
        "RGB",
        (
            margin * 2 + overview_columns * tile_width + 3 * gap,
            header + margin + rows * tile_height + (rows - 1) * gap + margin,
        ),
        "#0B0E12",
    )
    draw = ImageDraw.Draw(overview)
    draw.text(
        (margin, 20),
        "Gaojie private template diversity overview",
        fill="#F5F1E8",
        font=_font(28),
    )
    for index, (record, sheet_path) in enumerate(generated):
        row, column = divmod(index, overview_columns)
        left = margin + column * (tile_width + gap)
        top = header + margin + row * (tile_height + gap)
        with Image.open(sheet_path) as source:
            thumbnail = ImageOps.contain(source.convert("RGB"), (tile_width, 205))
        overview.paste(
            thumbnail,
            (
                left + (tile_width - thumbnail.width) // 2,
                top,
            ),
        )
        draw.text(
            (left, top + 212),
            f"{int(record['category_id']):03d} {record['category_name']}",
            fill="#D7DCE3",
            font=_font(17),
        )
    overview_path = output_root / "overview.png"
    _atomic_image(overview, overview_path)

    report = {
        "schema_version": "gaojie-contact-sheets.v1",
        "status": (
            "PASS"
            if records and all(not record["missing_item_ids"] for record in records)
            else "PARTIAL"
        ),
        "state_sha256": hashlib.sha256(state_bytes).hexdigest(),
        "category_count": len(records),
        "selected_count": sum(record["selected_count"] for record in records),
        "rendered_count": sum(record["rendered_count"] for record in records),
        "overview_path": overview_path.relative_to(root).as_posix(),
        "categories": records,
    }
    _atomic_json(report, output_root / "contact-sheets.json")
    return report


def build_certified_core_contact_sheets(
    private_root: Path | str,
    *,
    pages: list[dict[str, Any]],
    batch_size: int = 20,
    columns: int = 4,
    output_label: str = "certified-core-full",
) -> dict[str, Any]:
    """Render deterministic full-coverage sheets for routed private pages."""

    if type(batch_size) is not int or not 1 <= batch_size <= 40:
        raise ValueError("batch_size must be between one and forty")
    if type(columns) is not int or not 2 <= columns <= 5:
        raise ValueError("columns must be between two and five")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", output_label):
        raise ValueError("output_label must be a safe lowercase slug")
    root = Path(private_root).resolve()
    page_ids = [str(page.get("page_id", "")) for page in pages]
    if any(not page_id for page_id in page_ids) or len(set(page_ids)) != len(page_ids):
        raise ValueError("contact-sheet page IDs must be unique and nonempty")
    output_root = root / "evidence" / "gaojie" / output_label
    sheets: list[dict[str, Any]] = []
    covered: list[str] = []

    from PIL import Image, ImageDraw

    for batch_index, start in enumerate(range(0, len(pages), batch_size), start=1):
        batch = pages[start : start + batch_size]
        cell_width = 320
        preview_height = 180
        label_height = 54
        gap = 16
        margin = 24
        header = 64
        rows = max(1, (len(batch) + columns - 1) // columns)
        canvas = Image.new(
            "RGB",
            (
                margin * 2 + columns * cell_width + (columns - 1) * gap,
                header + margin + rows * (preview_height + label_height)
                + (rows - 1) * gap + margin,
            ),
            "#0B0E12",
        )
        draw = ImageDraw.Draw(canvas)
        draw.text(
            (margin, 18),
            f"Certified core full coverage · batch {batch_index:02d}",
            fill="#F5F1E8",
            font=_font(25),
        )
        batch_ids: list[str] = []
        for index, page in enumerate(batch):
            relative = page.get("png_path")
            path = (root / relative).resolve() if isinstance(relative, str) else None
            if path is None or root not in path.parents or not path.is_file():
                raise ValueError("contact-sheet render is missing or escapes private root")
            row, column = divmod(index, columns)
            left = margin + column * (cell_width + gap)
            top = header + margin + row * (preview_height + label_height + gap)
            preview = _fit_preview(path, cell_width, preview_height)
            canvas.paste(
                preview,
                (
                    left + (cell_width - preview.width) // 2,
                    top + (preview_height - preview.height) // 2,
                ),
            )
            page_id = str(page["page_id"])
            pool = str(page.get("pool", "unrouted"))
            draw.text(
                (left, top + preview_height + 7),
                f"{start + index + 1:03d}  {page_id[:12]}",
                fill="#E5E7EB",
                font=_font(15),
            )
            draw.text(
                (left, top + preview_height + 29),
                pool[:38],
                fill="#93A4B8",
                font=_font(13),
            )
            covered.append(page_id)
            batch_ids.append(page_id)
        target = output_root / f"batch-{batch_index:02d}.png"
        _atomic_image(canvas, target)
        sheets.append({
            "batch_index": batch_index,
            "page_ids": batch_ids,
            "sheet_path": target.relative_to(root).as_posix(),
        })
    report = {
        "schema_version": "gaojie-certified-contact-sheets.v1",
        "status": "PASS" if covered == page_ids else "PARTIAL",
        "source_page_count": len(pages),
        "covered_page_count": len(covered),
        "covered_page_ids": covered,
        "sheet_count": len(sheets),
        "sheets": sheets,
    }
    _atomic_json(report, output_root / "contact-sheets.json")
    return report
