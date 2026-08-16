"""Shared deterministic text wrapping estimates for governed PPTX slots."""

from __future__ import annotations

from dataclasses import dataclass
import math
import re
import unicodedata


@dataclass(frozen=True)
class TextLayoutEstimate:
    required_lines: int
    available_lines: int
    approximate_character_capacity: int

    @property
    def fits(self) -> bool:
        return self.required_lines <= self.available_lines


def _glyph_units(text: str) -> float:
    units = 0.0
    for character in text:
        if character.isspace():
            units += 0.33
        elif unicodedata.east_asian_width(character) in {"W", "F"}:
            units += 1.0
        elif unicodedata.category(character).startswith("P"):
            units += 0.45
        elif character in "ilIjtfr1":
            units += 0.30
        elif character in "mwMW@%":
            units += 0.82
        elif character.isupper():
            units += 0.62
        elif character.isdigit():
            units += 0.56
        else:
            # Calibrated against common Office-compatible sans fonts.  A
            # uniform 0.58-em assumption incorrectly rejected ordinary Latin
            # cover titles that LibreOffice and PowerPoint both keep on one
            # line.  CJK remains explicitly full-width above.
            units += 0.52
    return units


def _wrapped_lines(explicit_line: str, width_units: float) -> int:
    words = re.findall(r"\S+", explicit_line)
    if not words:
        return 1
    lines = 1
    occupied = 0.0
    for word in words:
        word_width = _glyph_units(word)
        separator = 0.33 if occupied else 0.0
        if occupied and occupied + separator + word_width <= width_units:
            occupied += separator + word_width
            continue
        if occupied:
            lines += 1
            occupied = 0.0
        if word_width <= width_units:
            occupied = word_width
            continue
        full_lines = max(1, math.ceil(word_width / width_units))
        lines += full_lines - 1
        remainder = math.fmod(word_width, width_units)
        occupied = remainder if remainder > 1e-9 else width_units
    return lines


def estimate_text_layout(
    text: str,
    *,
    width_in: float,
    height_in: float,
    font_size_pt: float,
    horizontal_padding_pt: float = 16.0,
    vertical_padding_pt: float = 12.0,
    line_height: float = 1.25,
) -> TextLayoutEstimate:
    """Estimate word wrapping and preserve every explicit authored line."""

    numeric = (
        width_in,
        height_in,
        font_size_pt,
        horizontal_padding_pt,
        vertical_padding_pt,
        line_height,
    )
    if any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(float(value))
        for value in numeric
    ):
        raise ValueError("text layout inputs must be finite numbers")
    if width_in <= 0 or height_in <= 0 or font_size_pt <= 0 or line_height <= 0:
        raise ValueError("text layout geometry and type size must be positive")
    if horizontal_padding_pt < 0 or vertical_padding_pt < 0:
        raise ValueError("text layout padding must be non-negative")

    usable_width = max(1.0, float(width_in) * 72.0 - horizontal_padding_pt)
    usable_height = max(1.0, float(height_in) * 72.0 - vertical_padding_pt)
    width_units = max(0.1, usable_width / float(font_size_pt))
    available_lines = max(
        1,
        int(usable_height / (float(font_size_pt) * float(line_height))),
    )
    required_lines = sum(
        _wrapped_lines(explicit_line, width_units)
        for explicit_line in str(text).split("\n")
    )
    approximate_character_capacity = available_lines * max(
        1,
        int(usable_width / (float(font_size_pt) * 0.58)),
    )
    return TextLayoutEstimate(
        required_lines=required_lines,
        available_lines=available_lines,
        approximate_character_capacity=approximate_character_capacity,
    )


__all__ = ["TextLayoutEstimate", "estimate_text_layout"]
