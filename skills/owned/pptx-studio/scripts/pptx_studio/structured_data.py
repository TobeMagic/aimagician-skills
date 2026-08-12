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
    # One item per public field value, each holding one or more opaque
    # chart/workbook/table targets.  These identifiers never leave this module
    # or the physical assembly report; agents only receive ``fields`` above.
    # One semantic value can therefore update every certified occurrence (for
    # example, a chart category and its linked workbook cache) without making
    # an agent repeat values or learn private identifiers.
    governed_targets: Mapping[str, tuple[tuple[str, ...], ...]]
    # Native text slots are the visible labels/cards associated with the same
    # data. They are deliberately private, just like peer groups: public
    # clients provide semantic values, never shape IDs or geometry.
    text_slots: Mapping[str, tuple[tuple[str, ...], ...]]

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
        governed_targets={
            "series_label": (("peer_a7dccbdf223dc8d3fdde7c77",),),
            "categories": tuple((item,) for item in (
                "peer_c3b8c0eab5c705b3c5a372e9", "peer_351ef9fc4ae10ff299cd576f",
                "peer_ad4caabe19353e84a2c45fa5", "peer_a0867d511ae54bdbe64e6c7f",
                "peer_651543baf37d572cd1804151",
            )),
            "ratios": tuple((item,) for item in (
                "peer_3a14beb981aa01e093b50212", "peer_f00eae35e9456821f4c43444",
                "peer_371608879ed0f775c1e3eb74", "peer_535d1e27c003fb78b26034dc",
                "peer_e61e900868dc765df343917e",
            )),
        },
        text_slots={
            "categories": tuple((item,) for item in ("shape_43", "shape_34", "shape_15", "shape_25", "shape_20")),
            "ratios": tuple((item,) for item in ("shape_44", "shape_35", "shape_16", "shape_26", "shape_21")),
            "amounts": tuple((item,) for item in ("shape_45", "shape_36", "shape_17", "shape_27", "shape_22")),
        },
    ),
    StructuredDataContract(
        contract_id="hospital-finance-medical-revenue-trend-v1",
        package_sha256=_WORK_REPORT_SHA,
        slide_number=6,
        fields=(
            StructuredField("trend_series_label", "text", 1, (8,)),
            StructuredField("trend_periods", "text", 3, (5, 5, 5)),
            StructuredField("trend_amounts", "number", 3, (12, 12, 12)),
            StructuredField("prior_share_series_label", "text", 1, (8,)),
            StructuredField("prior_share_categories", "text", 4, (7, 7, 7, 7)),
            StructuredField("prior_share_ratios", "percentage", 4, (6, 6, 6, 6)),
            StructuredField("current_share_series_label", "text", 1, (8,)),
            StructuredField("current_share_categories", "text", 4, (7, 7, 7, 7)),
            StructuredField("current_share_ratios", "percentage", 4, (6, 6, 6, 6)),
            StructuredField("comparison_labels", "text", 2, (9, 9)),
            StructuredField("headline_amounts", "number", 3, (16, 16, 16)),
            StructuredField("headline_metric_labels", "text", 2, (8, 5)),
            StructuredField("headline_metrics", "percentage", 2, (5, 5)),
        ),
        governed_targets={
            # The two workbook header cells are not rendered by the chart but
            # are retained in its embedded workbook.  They must move with the
            # customer series label so a physically reused page contains no
            # stale sample copy.  They remain aliases of one semantic field:
            # an agent neither sees nor supplies an implementation-only value.
            "trend_series_label": ((
                "peer_a277fe88de4355a941e5a019",
                "workbook_cell_55820963b28a0f8c52851b78",
                "workbook_cell_eb9d8d2acb2e5cadb59b5ded",
            ),),
            "trend_periods": tuple((item,) for item in ("peer_dc880db7c6ae0570c9418e9b", "peer_6c866209df37a66462c9b370", "peer_76e448f4f21f6c3ac7ed6468")),
            "trend_amounts": tuple((item,) for item in ("peer_991cb2dce1a1ca03eba5dbea", "peer_37e1e14b51c90c73d1f91336", "peer_e78029c54dfaf750dbd5181f")),
            "prior_share_series_label": (("peer_65a5336f48dc84182cfc731f",),),
            "prior_share_categories": tuple((item,) for item in ("peer_4c22b0d36feb551ff180cd43", "peer_9e374dd9ad0c6adc5ae5dfcc", "peer_6658172210657c5f9b5a6bcb", "peer_e16ee229e78521a459b0204e")),
            "prior_share_ratios": tuple((item,) for item in ("peer_f8e80657bc3be628e5b4aa22", "peer_372e812ac0bf000f9645f1d2", "peer_1c79160608f61244e874373f", "peer_53f75040c33a1f8e9961393b")),
            "current_share_series_label": (("peer_b11ced8b3ac599a47cf6ba0d",),),
            "current_share_categories": tuple((item,) for item in ("peer_432e51d67f880d42ce929819", "peer_58c539ede581871eafb2c93e", "peer_63904fa1f2bb9fbd76d9df90", "peer_eed7194fc9c5a929ad5d56a7")),
            "current_share_ratios": tuple((item,) for item in ("peer_033b7d2607e0cc95d5d679f8", "peer_2bb1ae5d0d29688b5a11a1b5", "peer_07116be095b672f145282594", "peer_74be7fd6db7dd1ff77fa3c6b")),
        },
        text_slots={
            "comparison_labels": tuple((item,) for item in ("shape_52", "shape_56")),
            "headline_amounts": tuple((item,) for item in ("shape_14", "shape_17", "shape_20")),
            "headline_metric_labels": tuple((item,) for item in ("shape_11", "shape_25")),
            "headline_metrics": tuple((item,) for item in ("shape_12", "shape_26")),
        },
    ),
    StructuredDataContract(
        contract_id="hospital-finance-expenditure-table-v1",
        package_sha256=_WORK_REPORT_SHA,
        slide_number=7,
        fields=(
            StructuredField("table_business_header", "text", 1, (5,)),
            StructuredField("table_time_header", "text", 1, (3,)),
            StructuredField("table_change_header", "text", 1, (3,)),
            StructuredField("current_year_label", "text", 1, (5,)),
            StructuredField("previous_year_label", "text", 1, (5,)),
            StructuredField("delta_amount_label", "text", 1, (5,)),
            StructuredField("delta_rate_label", "text", 1, (5,)),
            StructuredField("current_values", "number", 5, (12, 12, 12, 12, 12)),
            StructuredField("previous_values", "number", 5, (12, 12, 12, 12, 12)),
            StructuredField("delta_values", "number", 5, (12, 12, 12, 12, 12)),
            StructuredField("delta_rates", "percentage", 5, (7, 7, 7, 7, 7)),
            StructuredField("summary_labels", "text", 2, (5, 7)),
            StructuredField("summary_amounts", "number", 3, (16, 16, 16)),
            StructuredField("expense_labels", "text", 5, (7, 7, 7, 7, 7)),
        ),
        governed_targets={
            "table_business_header": (("table_cell_2c0759dd0707da0fe0e7d8ad",),),
            "table_time_header": (("table_cell_cf93b4bf1c0492d04fdd35cc",),),
            "table_change_header": (("table_cell_6cc729f599d307833e2eaecf",),),
            "current_year_label": (("table_cell_be48dc54ce7f63b997a33b5b",),),
            "previous_year_label": (("table_cell_9e96d3eda0cf2536104debf6",),),
            "delta_amount_label": (("table_cell_608b00f046e1930f37c4f805",),),
            "delta_rate_label": (("table_cell_3522ceab495ccee7b2944e15",),),
            "current_values": tuple((item,) for item in ("table_cell_32430ca774fb0d9b2aa158fb", "table_cell_9beffd1036f8f272192aaecb", "table_cell_41d3df671f23b38d6ec6293a", "table_cell_b1eb7848d629c452e33a90a5", "table_cell_63c9e1fa3e7512f3f0608018")),
            "previous_values": tuple((item,) for item in ("table_cell_c1b29a30a6dbf4a1d389b236", "table_cell_b8fa8dcc9328eb358d51693c", "table_cell_9552567c84b7b3bdd4c97040", "table_cell_26542d11e90973e039e2ac0c", "table_cell_79695968d016c48b92d9b011")),
            "delta_values": tuple((item,) for item in ("table_cell_df0afa46c19ab0dcbddef2d8", "table_cell_906abf24950dc8bae8503996", "table_cell_41264554b2d4081d2476b205", "table_cell_ef8b9c05c42f8a13de3ff0cd", "table_cell_14594e88a3f044ea2470bbea")),
            "delta_rates": tuple((item,) for item in ("table_cell_7b9deba6aa371875158924a9", "table_cell_87fafa99bd9ba4b4be3c1004", "table_cell_34467a4e16c98ed5f74f6033", "table_cell_97d0089cf5fff27383fa79fb", "table_cell_b13899c1a8aebd98fe71807a")),
        },
        text_slots={
            "summary_labels": tuple((item,) for item in ("shape_102", "shape_92")),
            "summary_amounts": tuple((item,) for item in ("shape_140", "shape_103", "shape_93")),
            "expense_labels": tuple((item,) for item in ("shape_34", "shape_53", "shape_71", "shape_74", "shape_77")),
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
        targets = contract.governed_targets.get(field.name, ())
        if not targets:
            continue
        if len(targets) != field.count:
            raise StructuredDataError("STRUCTURED_DATA_PRIVATE_MAPPING_INVALID")
        for aliases, value in zip(targets, checked[field.name], strict=True):
            if not aliases or any(not isinstance(item, str) or not item for item in aliases):
                raise StructuredDataError("STRUCTURED_DATA_PRIVATE_MAPPING_INVALID")
            for target in aliases:
                if target in expanded:
                    raise StructuredDataError("STRUCTURED_DATA_PRIVATE_MAPPING_DUPLICATE")
                expanded[target] = value
    return expanded


def expand_contract_text_values(contract: StructuredDataContract, values: Mapping[str, Any]) -> dict[str, str]:
    """Return certified visible-card replacements, keyed by private slot ID."""

    checked = validate_values(contract, values)
    expanded: dict[str, str] = {}
    for field in contract.fields:
        targets = contract.text_slots.get(field.name, ())
        if not targets:
            continue
        if len(targets) != field.count:
            raise StructuredDataError("STRUCTURED_DATA_PRIVATE_TEXT_MAPPING_INVALID")
        for aliases, value in zip(targets, checked[field.name], strict=True):
            if not aliases or any(not isinstance(item, str) or not item for item in aliases):
                raise StructuredDataError("STRUCTURED_DATA_PRIVATE_TEXT_MAPPING_INVALID")
            for slot_id in aliases:
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
