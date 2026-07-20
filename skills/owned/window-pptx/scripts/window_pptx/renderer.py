"""Narrow editable PowerPoint renderer for governed core render commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .render_plan import (
    RenderObject,
    RenderPlan,
    inches_to_points,
    validate_render_plan,
)


MSO_FALSE = 0
MSO_TRUE = -1
MSO_TEXT_ORIENTATION_HORIZONTAL = 1
MSO_SHAPE_RECTANGLE = 1
MSO_BRING_TO_FRONT = 0
MSO_SEND_TO_BACK = 1
PP_LAYOUT_BLANK = 12


class RenderError(RuntimeError):
    """A COM mutation failed with governed slide/object context."""


@dataclass(frozen=True)
class RenderReport:
    slide_count: int
    native_editable_count: int
    object_names: tuple[str, ...]
    group_names: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "slide_count": self.slide_count,
            "native_editable_count": self.native_editable_count,
            "object_names": list(self.object_names),
            "group_names": list(self.group_names),
        }


def _office_rgb(value: str) -> int:
    if not isinstance(value, str) or len(value) != 7 or not value.startswith("#"):
        raise RenderError(f"invalid governed color: {value!r}")
    try:
        red = int(value[1:3], 16)
        green = int(value[3:5], 16)
        blue = int(value[5:7], 16)
    except ValueError as exc:
        raise RenderError(f"invalid governed color: {value!r}") from exc
    return red | (green << 8) | (blue << 16)


def _record(presentation: Any, operation: str, target: str, *args: Any) -> None:
    recorder = getattr(presentation, "_record", None)
    if callable(recorder):
        recorder(operation, target, *args)


class PowerPointRenderer:
    """Apply a pure RenderPlan using only editable native PowerPoint objects."""

    def render(self, plan: RenderPlan, presentation: Any) -> RenderReport:
        validate_render_plan(plan)
        try:
            while int(presentation.Slides.Count) > 0:
                presentation.Slides.Item(1).Delete()
            presentation.PageSetup.SlideWidth = inches_to_points(
                plan.slide_size.width
            )
            presentation.PageSetup.SlideHeight = inches_to_points(
                plan.slide_size.height
            )
            _record(
                presentation,
                "set-page-size",
                "presentation",
                presentation.PageSetup.SlideWidth,
                presentation.PageSetup.SlideHeight,
            )
            self._render_master(plan, presentation)
        except RenderError:
            raise
        except Exception as exc:
            raise RenderError(f"presentation setup failed: {exc}") from exc

        object_names: list[str] = []
        group_names: list[str] = []
        for render_slide in plan.slides:
            try:
                slide = presentation.Slides.Add(render_slide.index, PP_LAYOUT_BLANK)
                slide.FollowMasterBackground = MSO_TRUE
            except Exception as exc:
                raise RenderError(
                    f"slide {render_slide.source_id} creation failed: {exc}"
                ) from exc

            created: dict[str, tuple[RenderObject, Any]] = {}
            for item in render_slide.objects:
                try:
                    shape = self._render_object(slide, item, presentation)
                except Exception as exc:
                    if isinstance(exc, RenderError):
                        message = str(exc)
                    else:
                        message = str(exc)
                    raise RenderError(
                        f"slide {render_slide.source_id} object {item.name} failed: "
                        f"{message}"
                    ) from exc
                created[item.name] = (item, shape)
                object_names.append(item.name)

            groups: dict[str, list[str]] = {}
            for item, _shape in created.values():
                if item.group_id is not None:
                    groups.setdefault(item.group_id, []).append(item.name)
            for item, shape in sorted(
                created.values(), key=lambda pair: (pair[0].layer, pair[0].name)
            ):
                try:
                    shape.ZOrder(MSO_BRING_TO_FRONT)
                except Exception as exc:
                    raise RenderError(
                        f"slide {render_slide.source_id} z-order {item.name} failed: {exc}"
                    ) from exc
            layered_groups: list[tuple[int, str, Any]] = []
            for group_id in sorted(groups):
                names = tuple(groups[group_id])
                if len(names) < 2:
                    continue
                try:
                    group = slide.Shapes.Range(names).Group()
                    group.Name = group_id
                    group.Tags.Add("window-pptx:group", group_id)
                except Exception as exc:
                    raise RenderError(
                        f"slide {render_slide.source_id} group {group_id} failed: {exc}"
                    ) from exc
                group_names.append(group_id)
                layered_groups.append(
                    (
                        max(created[name][0].layer for name in names),
                        group_id,
                        group,
                    )
                )
            layered_objects = [
                (item.layer, item.name, shape)
                for item, shape in created.values()
                if item.group_id is None or len(groups[item.group_id]) < 2
            ]
            for _layer, name, shape in sorted(layered_groups + layered_objects):
                try:
                    shape.ZOrder(MSO_BRING_TO_FRONT)
                except Exception as exc:
                    raise RenderError(
                        f"slide {render_slide.source_id} final z-order {name} failed: {exc}"
                    ) from exc

        return RenderReport(
            slide_count=len(plan.slides),
            native_editable_count=len(object_names),
            object_names=tuple(object_names),
            group_names=tuple(group_names),
        )

    def _render_master(self, plan: RenderPlan, presentation: Any) -> None:
        shapes = presentation.SlideMaster.Shapes
        while int(shapes.Count) > 0:
            shapes.Item(1).Delete()
        shape = shapes.AddShape(
            MSO_SHAPE_RECTANGLE,
            0,
            0,
            inches_to_points(plan.slide_size.width),
            inches_to_points(plan.slide_size.height),
        )
        shape.Name = "wp_master_background"
        shape.Tags.Add("window-pptx:id", "master.background")
        shape.Fill.Solid()
        shape.Fill.ForeColor.RGB = _office_rgb(plan.background_color)
        shape.Line.Visible = MSO_FALSE
        shape.ZOrder(MSO_SEND_TO_BACK)
        _record(presentation, "master-background", shape.Name, plan.background_color)

    def _render_object(
        self, slide: Any, item: RenderObject, presentation: Any
    ) -> Any:
        left = inches_to_points(item.x)
        top = inches_to_points(item.y)
        width = inches_to_points(item.width)
        height = inches_to_points(item.height)
        if item.kind == "text":
            shape = slide.Shapes.AddTextbox(
                MSO_TEXT_ORIENTATION_HORIZONTAL, left, top, width, height
            )
        elif item.kind == "shape":
            shape = slide.Shapes.AddShape(
                MSO_SHAPE_RECTANGLE, left, top, width, height
            )
        elif item.kind == "image":
            if item.source_path is None:
                raise RenderError("image command has no trusted source path")
            shape = slide.Shapes.AddPicture(
                str(item.source_path), MSO_FALSE, MSO_TRUE, left, top, -1, -1
            )
            self._crop_cover(shape, left, top, width, height, presentation)
        else:
            raise RenderError(f"unsupported render object kind: {item.kind}")

        shape.Name = item.name
        shape.Tags.Add("window-pptx:id", item.id)
        shape.Tags.Add("window-pptx:component", item.component)
        shape.Tags.Add("window-pptx:editable", "true")
        if item.kind != "image":
            shape.Fill.Solid()
            shape.Fill.ForeColor.RGB = _office_rgb(item.fill_color)
            if item.kind == "text":
                shape.Line.Visible = MSO_FALSE
            else:
                shape.Line.Visible = MSO_TRUE
                shape.Line.ForeColor.RGB = _office_rgb(item.line_color)
                shape.Line.Weight = 1.0
        if item.text:
            text_range = shape.TextFrame.TextRange
            text_range.Text = item.text
            text_range.Font.Name = item.font_name
            text_range.Font.Size = item.font_size_pt
            text_range.Font.Color.RGB = _office_rgb(item.text_color)
            shape.TextFrame.MarginLeft = 8
            shape.TextFrame.MarginRight = 8
            shape.TextFrame.MarginTop = 6
            shape.TextFrame.MarginBottom = 6
            shape.TextFrame.WordWrap = MSO_TRUE
        return shape

    def _crop_cover(
        self,
        shape: Any,
        left: float,
        top: float,
        width: float,
        height: float,
        presentation: Any,
    ) -> None:
        natural_width = float(shape.Width)
        natural_height = float(shape.Height)
        if natural_width <= 0 or natural_height <= 0:
            raise RenderError("image has invalid natural dimensions")
        scale = max(width / natural_width, height / natural_height)
        crop = shape.PictureFormat.Crop
        crop.ShapeWidth = width
        crop.ShapeHeight = height
        crop.PictureWidth = natural_width * scale
        crop.PictureHeight = natural_height * scale
        crop.PictureOffsetX = 0
        crop.PictureOffsetY = 0
        shape.Left = left
        shape.Top = top
        shape.Width = width
        shape.Height = height
        _record(
            presentation,
            "crop-cover",
            "image",
            left,
            top,
            width,
            height,
            crop.PictureWidth,
            crop.PictureHeight,
        )


__all__ = ["PowerPointRenderer", "RenderError", "RenderReport"]
