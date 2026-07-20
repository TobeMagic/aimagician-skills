"""Deterministic capacity and continuation rules for semantic slides."""

from __future__ import annotations

from dataclasses import replace

from .deck_plan import ContentBlock, SlideIntent


ITEM_LIMITS: dict[str, int] = {
    "bullets": 4,
    "metrics": 4,
    "comparison": 4,
    "sequence": 5,
    "timeline": 5,
    "trend": 10,
    "composition": 8,
    "matrix": 8,
    "risk": 4,
    "recommendation": 4,
    "quote": 1,
    "table": 8,
    "image": 3,
    "statement": 1,
    "generic": 4,
}
MAX_BLOCKS_PER_SLIDE = 3
DENSITY_ITEM_ADJUSTMENT = {"sparse": -1, "balanced": 0, "dense": 1}
DENSITY_UNIT_LIMIT = {"sparse": 6, "balanced": 8, "dense": 10}
DENSITY_TEXT_LIMIT = {"sparse": 480, "balanced": 720, "dense": 960}


def _text_units(text: str | None) -> int:
    return 0 if not text else max(1, (len(text) + 159) // 160)


def _item_units(item: object) -> int:
    if isinstance(item, str):
        return max(1, (len(item) + 159) // 160)
    if isinstance(item, dict):
        longest = max(
            (len(value) for value in item.values() if isinstance(value, str)),
            default=0,
        )
        return max(1, (longest + 159) // 160)
    return 1


def _block_units(block: ContentBlock) -> int:
    content_units = _text_units(block.text) + sum(
        _item_units(item) for item in block.items
    )
    return max(1, content_units)


def _split_text(text: str, limit: int) -> tuple[str, ...]:
    if len(text) <= limit:
        return (text,)
    chunks: list[str] = []
    offset = 0
    while offset < len(text):
        remaining = text[offset:]
        if len(remaining) <= limit:
            chunks.append(remaining)
            break
        window = remaining[:limit]
        boundaries = [
            window.rfind(marker) + len(marker)
            for marker in ("\n", "。", "！", "？", ". ", "; ", "；")
            if window.rfind(marker) >= 0
        ]
        cut = max(boundaries, default=limit)
        if cut < limit // 2:
            cut = limit
        chunks.append(remaining[:cut])
        offset += cut
    return tuple(chunks)


def _split_item_groups(
    items: tuple[object, ...], count_limit: int, unit_limit: int
) -> tuple[tuple[object, ...], ...]:
    if not items:
        return ()
    groups: list[tuple[object, ...]] = []
    current: list[object] = []
    units = 0
    for item in items:
        item_units = _item_units(item)
        if item_units > unit_limit:
            raise ValueError("one semantic item exceeds the registered density capacity")
        if current and (
            len(current) >= count_limit or units + item_units > unit_limit
        ):
            groups.append(tuple(current))
            current = []
            units = 0
        current.append(item)
        units += item_units
    if current:
        groups.append(tuple(current))
    return tuple(groups)


def _split_block(block: ContentBlock, density: str) -> tuple[ContentBlock, ...]:
    unit_limit = DENSITY_UNIT_LIMIT[density]
    count_limit = min(
        unit_limit,
        max(1, ITEM_LIMITS[block.kind] + DENSITY_ITEM_ADJUSTMENT[density]),
    )
    text_chunks = (
        _split_text(block.text, DENSITY_TEXT_LIMIT[density])
        if block.text
        else ()
    )
    item_groups = _split_item_groups(block.items, count_limit, unit_limit)
    if (
        len(text_chunks) <= 1
        and len(item_groups) <= 1
        and _block_units(block) <= unit_limit
    ):
        return (block,)

    parts: list[ContentBlock] = []
    parts.extend(replace(block, text=text, items=()) for text in text_chunks)
    parts.extend(replace(block, text=None, items=items) for items in item_groups)
    if not parts:
        return (block,)
    return tuple(
        replace(
            part,
            id=block.id if number == 1 else f"{block.id}--part-{number}",
        )
        for number, part in enumerate(parts, start=1)
    )


def _pack_small_blocks(
    blocks: tuple[ContentBlock, ...], unit_limit: int
) -> list[tuple[ContentBlock, ...]]:
    pages: list[tuple[ContentBlock, ...]] = []
    current: list[ContentBlock] = []
    units = 0
    for block in blocks:
        block_units = _block_units(block)
        if block_units > unit_limit:
            raise ValueError("normalized content block exceeds density capacity")
        if current and (
            len(current) >= MAX_BLOCKS_PER_SLIDE
            or units + block_units > unit_limit
        ):
            pages.append(tuple(current))
            current = []
            units = 0
        current.append(block)
        units += block_units
    if current:
        pages.append(tuple(current))
    return pages


def split_slide(
    slide: SlideIntent, *, density: str = "balanced"
) -> tuple[SlideIntent, ...]:
    """Split over-capacity content without dropping, padding, or reordering items."""

    if density not in DENSITY_ITEM_ADJUSTMENT:
        raise ValueError(f"unregistered density: {density}")
    unit_limit = DENSITY_UNIT_LIMIT[density]
    split_blocks = [_split_block(block, density) for block in slide.blocks]
    had_oversized_block = any(len(parts) > 1 for parts in split_blocks)
    if had_oversized_block:
        pages = [(part,) for parts in split_blocks for part in parts]
    elif (
        len(slide.blocks) <= MAX_BLOCKS_PER_SLIDE
        and sum(_block_units(block) for block in slide.blocks) <= unit_limit
    ):
        return (slide,)
    else:
        pages = _pack_small_blocks(slide.blocks, unit_limit)

    result: list[SlideIntent] = []
    for index, blocks in enumerate(pages, start=1):
        if index == 1:
            result.append(replace(slide, blocks=blocks))
            continue
        title = (
            f"{slide.title} · continued {index}" if slide.title is not None else None
        )
        result.append(
            replace(
                slide,
                id=f"{slide.id}--cont-{index}",
                title=title,
                blocks=blocks,
                continuation_of=slide.id,
            )
        )
    return tuple(result)
