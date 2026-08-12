"""Public contracts for governed chart/table data surfaces.

The agent receives a named business-data contract, never a chart relationship,
workbook cell, source label, shape ID or OOXML locator.  The physical adapter
uses the matching opaque binding map only after it proves the selected package
and slide fingerprint.  The first contract below covers the revenue-composition
page in the certified annual-work-report reference family; more contracts are
additive records, not new agent authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


class StructuredDataError(ValueError):
    """A business dataset is not compatible with a certified data surface."""


@dataclass(frozen=True)
class StructuredField:
    name: str
    kind: str
    count: int
    # Per-item limits are part of the public contract.  They let a weaker
    # model safely choose a compact display format before it writes a request,
    # while source shape IDs and geometry remain private.
    max_chars: tuple[int, ...]

    def public_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "kind": self.kind,
            "count": self.count,
            "max_chars": list(self.max_chars),
        }


@dataclass(frozen=True)
class StructuredDataContract:
    contract_id: str
    package_sha256: str
    slide_number: int
    fields: tuple[StructuredField, ...]
    # Each opaque peer group is an already-certified chart/workbook alias.
    # These identifiers never leave this module or the physical assembly
    # report; agents only receive ``fields`` above.
    peer_groups: Mapping[str, tuple[str, ...]]
    # Native text slots are the visible labels/cards associated with the same
    # data. They are deliberately private, just like peer groups: public
    # clients provide semantic values, never shape IDs or geometry.
    text_slots: Mapping[str, tuple[str, ...]]

    def public_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "fields": [field.public_dict() for field in self.fields],
        }


# This package is the user-provided, certified 15-page annual-work-report
# reference.  Its chart page is only admitted when all five customer-provided
# category labels and ratios are available; the template's historical values
# are never used as a default.
_WORK_REPORT_SHA = "59b104d31bf3f44c15d407adefe51425c9dcd8bb5c5d1e2212fb38753dc72839"
_CONTRACTS: tuple[StructuredDataContract, ...] = (
    StructuredDataContract(
        contract_id="hospital-finance-revenue-composition-v1",
        package_sha256=_WORK_REPORT_SHA,
        slide_number=5,
        fields=(
            StructuredField("series_label", "text", 1, (8,)),
            StructuredField("categories", "text", 5, (5, 6, 5, 5, 5)),
            StructuredField("ratios", "percentage", 5, (5, 5, 4, 4, 4)),
            StructuredField("amounts", "number", 5, (10, 8, 10, 10, 8)),
        ),
        peer_groups={
            "series_label": ("peer_a7dccbdf223dc8d3fdde7c77",),
            "categories": (
                "peer_c3b8c0eab5c705b3c5a372e9",
                "peer_351ef9fc4ae10ff299cd576f",
                "peer_ad4caabe19353e84a2c45fa5",
                "peer_a0867d511ae54bdbe64e6c7f",
                "peer_651543baf37d572cd1804151",
            ),
            "ratios": (
                "peer_3a14beb981aa01e093b50212",
                "peer_f00eae35e9456821f4c43444",
                "peer_371608879ed0f775c1e3eb74",
                "peer_535d1e27c003fb78b26034dc",
                "peer_e61e900868dc765df343917e",
            ),
        },
        text_slots={
            "categories": ("shape_43", "shape_34", "shape_15", "shape_25", "shape_20"),
            "ratios": ("shape_44", "shape_35", "shape_16", "shape_26", "shape_21"),
            "amounts": ("shape_45", "shape_36", "shape_17", "shape_27", "shape_22"),
        },
    ),
)


def contract_for_source(package_sha256: str, slide_number: int) -> StructuredDataContract | None:
    for contract in _CONTRACTS:
        if contract.package_sha256 == package_sha256 and contract.slide_number == slide_number:
            return contract
    return None


def contract_by_id(contract_id: str) -> StructuredDataContract | None:
    for contract in _CONTRACTS:
        if contract.contract_id == contract_id:
            return contract
    return None


def validate_values(contract: StructuredDataContract, values: Mapping[str, Any]) -> dict[str, tuple[str, ...]]:
    """Validate a complete semantic data payload without source-slot access."""

    expected = {field.name: field for field in contract.fields}
    if set(values) != set(expected):
        raise StructuredDataError("STRUCTURED_DATA_FIELDS_INVALID")
    result: dict[str, tuple[str, ...]] = {}
    for name, field in expected.items():
        if len(field.max_chars) != field.count or any(limit < 1 for limit in field.max_chars):
            raise StructuredDataError("STRUCTURED_DATA_PRIVATE_MAPPING_INVALID")
        raw = values[name]
        sequence = raw if isinstance(raw, list) else [raw]
        if not isinstance(sequence, list) or len(sequence) != field.count:
            raise StructuredDataError(f"STRUCTURED_DATA_CARDINALITY_INVALID:{name}")
        if any(not isinstance(value, str) or not value.strip() for value in sequence):
            raise StructuredDataError(f"STRUCTURED_DATA_VALUE_INVALID:{name}")
        if any(len(value) > limit for value, limit in zip(sequence, field.max_chars, strict=True)):
            raise StructuredDataError(f"STRUCTURED_DATA_VALUE_CAPACITY_EXCEEDED:{name}")
        result[name] = tuple(sequence)
    return result


def expand_contract_values(contract: StructuredDataContract, values: Mapping[str, Any]) -> dict[str, str]:
    """Return opaque peer-group replacements after public-value validation."""

    checked = validate_values(contract, values)
    expanded: dict[str, str] = {}
    for field in contract.fields:
        groups = contract.peer_groups.get(field.name, ())
        if not groups:
            continue
        if len(groups) != field.count:
            raise StructuredDataError("STRUCTURED_DATA_PRIVATE_MAPPING_INVALID")
        for group, value in zip(groups, checked[field.name], strict=True):
            if group in expanded:
                raise StructuredDataError("STRUCTURED_DATA_PRIVATE_MAPPING_DUPLICATE")
            expanded[group] = value
    return expanded


def expand_contract_text_values(contract: StructuredDataContract, values: Mapping[str, Any]) -> dict[str, str]:
    """Return certified visible-card replacements, keyed by private slot ID."""

    checked = validate_values(contract, values)
    expanded: dict[str, str] = {}
    for field in contract.fields:
        slots = contract.text_slots.get(field.name, ())
        if not slots:
            continue
        if len(slots) != field.count:
            raise StructuredDataError("STRUCTURED_DATA_PRIVATE_TEXT_MAPPING_INVALID")
        for slot_id, value in zip(slots, checked[field.name], strict=True):
            if slot_id in expanded:
                raise StructuredDataError("STRUCTURED_DATA_PRIVATE_TEXT_MAPPING_DUPLICATE")
            expanded[slot_id] = value
    return expanded


__all__ = [
    "StructuredDataContract",
    "StructuredDataError",
    "contract_by_id",
    "contract_for_source",
    "expand_contract_values",
    "expand_contract_text_values",
    "validate_values",
]
