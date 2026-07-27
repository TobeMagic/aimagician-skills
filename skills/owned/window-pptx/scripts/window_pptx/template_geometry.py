"""Trusted rendered-mask geometry derived only from a hash-bound source PPTX."""

from __future__ import annotations

import math
import posixpath
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

from .template_pack import TemplatePack, TemplatePackError, sha256_file


PML = "http://schemas.openxmlformats.org/presentationml/2006/main"
DML = "http://schemas.openxmlformats.org/drawingml/2006/main"
CHART = "http://schemas.openxmlformats.org/drawingml/2006/chart"
REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PACKAGE_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"p": PML, "a": DML, "c": CHART, "r": REL, "pr": PACKAGE_REL}


@dataclass(frozen=True)
class VisualMask:
    """One normalized, source-derived editable rendered region."""

    slide: int
    target_kind: str
    target_id: str
    x: float
    y: float
    width: float
    height: float
    padding: float = 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "slide": self.slide,
            "target_kind": self.target_kind,
            "target_id": self.target_id,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "padding": self.padding,
        }


@dataclass(frozen=True)
class TemplateGeometryInventory:
    """Reviewable source-only geometry inventory."""

    template_pack_id: str
    template_sha256: str
    slide_count: int
    shape_target_count: int
    chart_target_count: int
    masks: tuple[VisualMask, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "template_pack_id": self.template_pack_id,
            "template_sha256": self.template_sha256,
            "slide_count": self.slide_count,
            "shape_target_count": self.shape_target_count,
            "chart_target_count": self.chart_target_count,
            "masks": [mask.to_dict() for mask in self.masks],
        }


# Affine tuple: x' = a*x + c*y + e; y' = b*x + d*y + f.
Affine = tuple[float, float, float, float, float, float]
IDENTITY: Affine = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def _compose(left: Affine, right: Affine) -> Affine:
    la, lb, lc, ld, le, lf = left
    ra, rb, rc, rd, re, rf = right
    return (
        la * ra + lc * rb,
        lb * ra + ld * rb,
        la * rc + lc * rd,
        lb * rc + ld * rd,
        la * re + lc * rf + le,
        lb * re + ld * rf + lf,
    )


def _translate(x: float, y: float) -> Affine:
    return (1.0, 0.0, 0.0, 1.0, x, y)


def _scale(x: float, y: float) -> Affine:
    return (x, 0.0, 0.0, y, 0.0, 0.0)


def _rotate(degrees: float) -> Affine:
    radians = math.radians(degrees)
    cosine = math.cos(radians)
    sine = math.sin(radians)
    return (cosine, sine, -sine, cosine, 0.0, 0.0)


def _apply(matrix: Affine, x: float, y: float) -> tuple[float, float]:
    a, b, c, d, e, f = matrix
    return (a * x + c * y + e, b * x + d * y + f)


def _required_number(node: ET.Element | None, attribute: str, context: str) -> float:
    if node is None:
        raise TemplatePackError(f"{context} is missing")
    raw = node.get(attribute)
    try:
        value = float(raw) if raw is not None else math.nan
    except ValueError as exc:
        raise TemplatePackError(f"{context}.{attribute} is invalid") from exc
    if not math.isfinite(value):
        raise TemplatePackError(f"{context}.{attribute} is invalid")
    return value


def _orientation(xfrm: ET.Element, off_x: float, off_y: float, cx: float, cy: float) -> Affine:
    rotation_raw = xfrm.get("rot", "0")
    try:
        rotation = float(rotation_raw) / 60000.0
    except ValueError as exc:
        raise TemplatePackError("shape rotation is invalid") from exc
    flip_x = -1.0 if xfrm.get("flipH") in {"1", "true"} else 1.0
    flip_y = -1.0 if xfrm.get("flipV") in {"1", "true"} else 1.0
    center_x = off_x + cx / 2.0
    center_y = off_y + cy / 2.0
    return _compose(
        _translate(center_x, center_y),
        _compose(
            _rotate(rotation),
            _compose(_scale(flip_x, flip_y), _translate(-center_x, -center_y)),
        ),
    )


def _shape_transform(xfrm: ET.Element) -> tuple[Affine, float, float]:
    off = xfrm.find("a:off", NS)
    ext = xfrm.find("a:ext", NS)
    off_x = _required_number(off, "x", "shape off")
    off_y = _required_number(off, "y", "shape off")
    cx = _required_number(ext, "cx", "shape ext")
    cy = _required_number(ext, "cy", "shape ext")
    if cx <= 0 or cy <= 0:
        raise TemplatePackError("shape extent must be positive")
    placed = _translate(off_x, off_y)
    return (_compose(_orientation(xfrm, off_x, off_y, cx, cy), placed), cx, cy)


def _group_transform(xfrm: ET.Element) -> Affine:
    off = xfrm.find("a:off", NS)
    ext = xfrm.find("a:ext", NS)
    child_off = xfrm.find("a:chOff", NS)
    child_ext = xfrm.find("a:chExt", NS)
    off_x = _required_number(off, "x", "group off")
    off_y = _required_number(off, "y", "group off")
    cx = _required_number(ext, "cx", "group ext")
    cy = _required_number(ext, "cy", "group ext")
    child_x = _required_number(child_off, "x", "group child off")
    child_y = _required_number(child_off, "y", "group child off")
    child_cx = _required_number(child_ext, "cx", "group child ext")
    child_cy = _required_number(child_ext, "cy", "group child ext")
    if cx <= 0 or cy <= 0 or child_cx <= 0 or child_cy <= 0:
        raise TemplatePackError("group extent must be positive")
    base = _compose(
        _translate(off_x, off_y),
        _compose(
            _scale(cx / child_cx, cy / child_cy),
            _translate(-child_x, -child_y),
        ),
    )
    return _compose(_orientation(xfrm, off_x, off_y, cx, cy), base)


def _direct_child(node: ET.Element, namespace: str, local_name: str) -> ET.Element | None:
    return node.find(f"{{{namespace}}}{local_name}")


def _shape_xfrm(shape: ET.Element) -> ET.Element:
    local = shape.tag.rsplit("}", 1)[-1]
    if local == "graphicFrame":
        xfrm = _direct_child(shape, PML, "xfrm")
    else:
        properties = _direct_child(shape, PML, "spPr")
        xfrm = _direct_child(properties, DML, "xfrm") if properties is not None else None
    if xfrm is None:
        raise TemplatePackError(f"{local} target has no supported transform")
    return xfrm


def _shape_id(shape: ET.Element) -> int:
    c_nv_pr = shape.find(".//p:cNvPr", NS)
    raw = c_nv_pr.get("id") if c_nv_pr is not None else None
    try:
        value = int(raw) if raw is not None else 0
    except ValueError as exc:
        raise TemplatePackError("shape cNvPr id is invalid") from exc
    if value < 1:
        raise TemplatePackError("shape cNvPr id is invalid")
    return value


def _normalized_bbox(
    matrix: Affine,
    width: float,
    height: float,
    *,
    slide_width: float,
    slide_height: float,
) -> tuple[float, float, float, float]:
    points = (
        _apply(matrix, 0.0, 0.0),
        _apply(matrix, width, 0.0),
        _apply(matrix, 0.0, height),
        _apply(matrix, width, height),
    )
    left = max(0.0, min(point[0] for point in points))
    top = max(0.0, min(point[1] for point in points))
    right = min(slide_width, max(point[0] for point in points))
    bottom = min(slide_height, max(point[1] for point in points))
    if right <= left or bottom <= top:
        raise TemplatePackError("target geometry is outside the slide or empty")
    values = (
        left / slide_width,
        top / slide_height,
        (right - left) / slide_width,
        (bottom - top) / slide_height,
    )
    return tuple(round(value, 9) for value in values)  # type: ignore[return-value]


def _slide_relationships(archive: zipfile.ZipFile, slide_number: int) -> dict[str, str]:
    path = f"ppt/slides/_rels/slide{slide_number}.xml.rels"
    if path not in archive.namelist():
        return {}
    root = ET.fromstring(archive.read(path))
    relationships: dict[str, str] = {}
    slide_path = f"ppt/slides/slide{slide_number}.xml"
    for relationship in root.findall("pr:Relationship", NS):
        relationship_id = relationship.get("Id")
        target = relationship.get("Target")
        if relationship_id and target:
            relationships[relationship_id] = posixpath.normpath(
                posixpath.join(posixpath.dirname(slide_path), target)
            )
    return relationships


def _walk_shapes(
    container: ET.Element,
    parent: Affine,
    *,
    slide_width: float,
    slide_height: float,
    relationships: dict[str, str],
    shapes: dict[int, tuple[float, float, float, float]],
    charts: dict[str, tuple[float, float, float, float]],
) -> None:
    for shape in container:
        local = shape.tag.rsplit("}", 1)[-1]
        if local == "grpSp":
            properties = _direct_child(shape, PML, "grpSpPr")
            xfrm = _direct_child(properties, DML, "xfrm") if properties is not None else None
            if xfrm is None:
                raise TemplatePackError("group target has no supported transform")
            _walk_shapes(
                shape,
                _compose(parent, _group_transform(xfrm)),
                slide_width=slide_width,
                slide_height=slide_height,
                relationships=relationships,
                shapes=shapes,
                charts=charts,
            )
            continue
        if local not in {"sp", "pic", "graphicFrame", "cxnSp"}:
            continue
        identifier = _shape_id(shape)
        if identifier in shapes:
            raise TemplatePackError(f"duplicate shape id {identifier}")
        try:
            local_transform, width, height = _shape_transform(_shape_xfrm(shape))
        except TemplatePackError as exc:
            # Zero-area decorative/connective objects are legal OOXML
            # bookkeeping. A declared slot targeting one will still fail later
            # as an unknown/invalid editable target.
            if str(exc) == "shape extent must be positive":
                continue
            raise
        bbox = _normalized_bbox(
            _compose(parent, local_transform),
            width,
            height,
            slide_width=slide_width,
            slide_height=slide_height,
        )
        shapes[identifier] = bbox
        if local == "graphicFrame":
            chart = shape.find(".//c:chart", NS)
            relationship_id = chart.get(f"{{{REL}}}id") if chart is not None else None
            if relationship_id is not None:
                chart_part = relationships.get(relationship_id)
                if chart_part is None:
                    raise TemplatePackError(
                        f"chart relationship {relationship_id} cannot be resolved"
                    )
                if chart_part in charts:
                    raise TemplatePackError(f"chart part {chart_part} has multiple frames")
                charts[chart_part] = bbox


def _read_source_geometry(
    template_path: Path,
    slide_count: int,
) -> tuple[
    dict[int, dict[int, tuple[float, float, float, float]]],
    dict[str, tuple[int, tuple[float, float, float, float]]],
]:
    with zipfile.ZipFile(template_path) as archive:
        presentation = ET.fromstring(archive.read("ppt/presentation.xml"))
        size = presentation.find("p:sldSz", NS)
        slide_width = _required_number(size, "cx", "presentation slide size")
        slide_height = _required_number(size, "cy", "presentation slide size")
        if slide_width <= 0 or slide_height <= 0:
            raise TemplatePackError("presentation slide size must be positive")
        all_shapes: dict[int, dict[int, tuple[float, float, float, float]]] = {}
        all_charts: dict[str, tuple[int, tuple[float, float, float, float]]] = {}
        for slide_number in range(1, slide_count + 1):
            slide_path = f"ppt/slides/slide{slide_number}.xml"
            if slide_path not in archive.namelist():
                raise TemplatePackError(f"source is missing {slide_path}")
            slide_root = ET.fromstring(archive.read(slide_path))
            tree = slide_root.find(".//p:spTree", NS)
            if tree is None:
                raise TemplatePackError(f"slide {slide_number} has no shape tree")
            root_parent = IDENTITY
            root_properties = _direct_child(tree, PML, "grpSpPr")
            root_xfrm = (
                _direct_child(root_properties, DML, "xfrm")
                if root_properties is not None
                else None
            )
            # PowerPoint commonly serializes the root spTree group transform as
            # all-zero bookkeeping. It is not a drawable group coordinate map.
            root_ext = root_xfrm.find("a:ext", NS) if root_xfrm is not None else None
            root_child_ext = (
                root_xfrm.find("a:chExt", NS) if root_xfrm is not None else None
            )
            if (
                root_xfrm is not None
                and _required_number(root_ext, "cx", "root group ext") > 0
                and _required_number(root_ext, "cy", "root group ext") > 0
                and _required_number(root_child_ext, "cx", "root group child ext") > 0
                and _required_number(root_child_ext, "cy", "root group child ext") > 0
            ):
                root_parent = _group_transform(root_xfrm)
            shapes: dict[int, tuple[float, float, float, float]] = {}
            charts: dict[str, tuple[float, float, float, float]] = {}
            _walk_shapes(
                tree,
                root_parent,
                slide_width=slide_width,
                slide_height=slide_height,
                relationships=_slide_relationships(archive, slide_number),
                shapes=shapes,
                charts=charts,
            )
            all_shapes[slide_number] = shapes
            for chart_part, bbox in charts.items():
                if chart_part in all_charts:
                    raise TemplatePackError(
                        f"chart part {chart_part} is used on multiple slides"
                    )
                all_charts[chart_part] = (slide_number, bbox)
    return all_shapes, all_charts


def propose_visual_masks(pack: TemplatePack) -> tuple[VisualMask, ...]:
    """Derive masks from declared targets without looking at rendered pixels."""

    shapes, charts = _read_source_geometry(pack.template_path, pack.slide_count)
    masks: list[VisualMask] = []
    for slot in sorted(pack.slots, key=lambda value: (value.slide, value.shape_id)):
        bbox = shapes.get(slot.slide, {}).get(slot.shape_id)
        if bbox is None:
            raise TemplatePackError(
                f"declared target slide {slot.slide} shape {slot.shape_id} is unknown"
            )
        masks.append(
            VisualMask(
                slide=slot.slide,
                target_kind="shape",
                target_id=str(slot.shape_id),
                x=bbox[0],
                y=bbox[1],
                width=bbox[2],
                height=bbox[3],
            )
        )
    for chart_part in sorted({slot.chart_part for slot in pack.chart_slots}):
        target = charts.get(chart_part)
        if target is None:
            raise TemplatePackError(f"declared chart target {chart_part} is unknown")
        slide_number, bbox = target
        masks.append(
            VisualMask(
                slide=slide_number,
                target_kind="chart",
                target_id=chart_part,
                x=bbox[0],
                y=bbox[1],
                width=bbox[2],
                height=bbox[3],
            )
        )
    return tuple(masks)


def build_template_geometry_inventory(pack: TemplatePack) -> TemplateGeometryInventory:
    """Build a hash-bound authoring inventory without mutating the pack."""

    observed_hash = sha256_file(pack.template_path)
    if observed_hash != pack.template_sha256:
        raise TemplatePackError(
            f"TemplatePack source hash mismatch: expected {pack.template_sha256}, "
            f"observed {observed_hash}"
        )
    masks = propose_visual_masks(pack)
    return TemplateGeometryInventory(
        template_pack_id=pack.id,
        template_sha256=observed_hash,
        slide_count=pack.slide_count,
        shape_target_count=len(pack.slots),
        chart_target_count=len({slot.chart_part for slot in pack.chart_slots}),
        masks=masks,
    )


def masks_for_slide(
    masks: Iterable[VisualMask],
    slide_number: int,
) -> tuple[VisualMask, ...]:
    return tuple(mask for mask in masks if mask.slide == slide_number)
