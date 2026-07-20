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


def _block_units(block: ContentBlock) -> int:
    if block.items:
        return max(1, len(block.items))
    if block.text:
        return max(1, (len(block.text) + 159) // 160)
    return 1


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


def _split_block(block: ContentBlock, density: str) -> tuple[ContentBlock, ...]:
    limit = max(1, ITEM_LIMITS[block.kind] + DENSITY_ITEM_ADJUSTMENT[density])
    if block.items and len(block.items) > limit:
        chunks: list[ContentBlock] = []
        for offset in range(0, len(block.items), limit):
            number = offset // limit + 1
            block_id = block.id if number == 1 else f"{block.id}--part-{number}"
            chunks.append(
                replace(
                    block,
                    id=block_id,
                    items=block.items[offset : offset + limit],
                )
            )
        return tuple(chunks)
    if block.text:
        text_chunks = _split_text(block.text, DENSITY_TEXT_LIMIT[density])
        if len(text_chunks) > 1:
            return tuple(
                replace(
                    block,
                    id=block.id if number == 1 else f"{block.id}--part-{number}",
                    text=text,
                )
                for number, text in enumerate(text_chunks, start=1)
            )
    return (block,)


def _pack_small_blocks(
    blocks: tuple[ContentBlock, ...], unit_limit: int
) -> list[tuple[ContentBlock, ...]]:
    pages: list[tuple[ContentBlock, ...]] = []
    current: list[ContentBlock] = []
    units = 0
    for block in blocks:
        block_units = _block_units(block)
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
