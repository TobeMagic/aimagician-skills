"""Narrow editable PowerPoint renderer for governed core render commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .render_plan import (
    ChartSpec,
    DiagramSpec,
    RenderObject,
    RenderPlan,
    RenderSlide,
    TableSpec,
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
PP_MOUSE_CLICK = 1
MSO_ANIM_EFFECT_FADE = 10
MSO_ANIM_TRIGGER_AFTER_PREVIOUS = 3
MSO_ANIM_TRIGGER_ON_PAGE_CLICK = 1
XL_CHART_TYPES = {
    "line": 4,
    "column": 51,
    "bar": 57,
    "doughnut": -4120,
    "stacked-column": 52,
    "scatter": -4169,
}


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
        slides_by_id: dict[str, Any] = {}
        for render_slide in plan.slides:
            try:
                slide = presentation.Slides.Add(render_slide.index, PP_LAYOUT_BLANK)
                slide.FollowMasterBackground = MSO_TRUE
                slides_by_id[render_slide.source_id] = slide
            except Exception as exc:
                raise RenderError(
                    f"slide {render_slide.source_id} creation failed: {exc}"
                ) from exc

        for render_slide in plan.slides:
            slide = slides_by_id[render_slide.source_id]
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

            for item, shape in created.values():
                if item.hyperlink is not None:
                    try:
                        self._apply_hyperlink(
                            shape,
                            item.hyperlink,
                            slides_by_id,
                            presentation,
                        )
                    except Exception as exc:
                        raise RenderError(
                            f"slide {render_slide.source_id} hyperlink "
                            f"{item.name} failed: {exc}"
                        ) from exc
            if render_slide.speaker_notes is not None:
                try:
                    self._set_speaker_notes(
                        slide, render_slide.speaker_notes, presentation
                    )
                except Exception as exc:
                    raise RenderError(
                        f"slide {render_slide.source_id} speaker notes failed: {exc}"
                    ) from exc

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
            try:
                self._apply_motion(
                    slide,
                    render_slide,
                    created,
                    {group_id: group for _layer, group_id, group in layered_groups},
                    presentation,
                )
            except Exception as exc:
                raise RenderError(
                    f"slide {render_slide.source_id} motion failed: {exc}"
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
        elif item.kind == "chart" and isinstance(item.advanced, ChartSpec):
            shape = self._render_chart(
                slide, item, item.advanced, left, top, width, height, presentation
            )
        elif item.kind == "table" and isinstance(item.advanced, TableSpec):
            shape = self._render_table(
                slide, item, item.advanced, left, top, width, height, presentation
            )
        elif item.kind == "diagram" and isinstance(item.advanced, DiagramSpec):
            shape = self._render_diagram(
                slide, item, item.advanced, left, top, width, height, presentation
            )
        else:
            raise RenderError(f"unsupported render object kind: {item.kind}")

        shape.Name = item.name
        shape.Tags.Add("window-pptx:id", item.id)
        shape.Tags.Add("window-pptx:component", item.component)
        shape.Tags.Add("window-pptx:editable", "true")
        if item.kind not in {"image", "chart", "table", "diagram"}:
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

    def _render_chart(
        self,
        slide: Any,
        item: RenderObject,
        spec: ChartSpec,
        left: float,
        top: float,
        width: float,
        height: float,
        presentation: Any,
    ) -> Any:
        shape = slide.Shapes.AddChart2(
            -1,
            XL_CHART_TYPES[spec.chart_type],
            left,
            top,
            width,
            height,
            MSO_TRUE,
        )
        chart = shape.Chart
        fake_setter = getattr(chart, "_set_data", None)
        if callable(fake_setter):
            fake_setter(spec)
        else:
            chart.ChartData.Activate()
            workbook = chart.ChartData.Workbook
            try:
                sheet = workbook.Worksheets(1)
                sheet.Cells.Clear()
                if spec.chart_type == "scatter":
                    collection = chart.SeriesCollection()
                    while int(collection.Count) > 0:
                        collection(1).Delete()
                    for series_index, series in enumerate(spec.series):
                        x_column = series_index * 2 + 1
                        y_column = x_column + 1
                        sheet.Cells(1, x_column).Value = f"{series.name} X"
                        sheet.Cells(1, y_column).Value = f"{series.name} Y"
                        for row, (x_value, y_value) in enumerate(
                            zip(series.x_values, series.values), start=2
                        ):
                            sheet.Cells(row, x_column).Value = x_value
                            sheet.Cells(row, y_column).Value = y_value
                        native_series = collection.NewSeries()
                        native_series.Name = series.name
                        native_series.XValues = sheet.Range(
                            sheet.Cells(2, x_column),
                            sheet.Cells(len(series.x_values) + 1, x_column),
                        )
                        native_series.Values = sheet.Range(
                            sheet.Cells(2, y_column),
                            sheet.Cells(len(series.values) + 1, y_column),
                        )
                else:
                    sheet.Cells(1, 1).Value = "Category"
                    for column, series in enumerate(spec.series, start=2):
                        sheet.Cells(1, column).Value = series.name
                    for row, category in enumerate(spec.categories, start=2):
                        sheet.Cells(row, 1).Value = category
                        for column, series in enumerate(spec.series, start=2):
                            sheet.Cells(row, column).Value = series.values[row - 2]
                    chart.SetSourceData(
                        sheet.Range(
                            sheet.Cells(1, 1),
                            sheet.Cells(
                                len(spec.categories) + 1,
                                len(spec.series) + 1,
                            ),
                        )
                    )
            finally:
                close = getattr(workbook, "Close", None)
                if callable(close):
                    close()
        chart.HasTitle = MSO_FALSE
        chart.HasLegend = MSO_TRUE if len(spec.series) > 1 else MSO_FALSE
        # xlNotPlotted: missing category/series pairs remain honest gaps rather
        # than being rendered as invented zero values.
        chart.DisplayBlanksAs = 1
        if not callable(fake_setter):
            native_series_collection = chart.SeriesCollection()
            for index in range(1, int(native_series_collection.Count) + 1):
                native_series = native_series_collection(index)
                if spec.chart_type == "line":
                    native_series.Format.Line.ForeColor.RGB = _office_rgb(
                        item.line_color
                    )
                    native_series.Format.Line.Weight = 2.25
                else:
                    native_series.Format.Fill.Solid()
                    native_series.Format.Fill.ForeColor.RGB = _office_rgb(
                        item.line_color
                    )
        _record(
            presentation,
            "set-chart-data",
            spec.chart_type,
            tuple(spec.categories),
            tuple((series.name, series.values, series.x_values) for series in spec.series),
        )
        return shape

    def _render_table(
        self,
        slide: Any,
        item: RenderObject,
        spec: TableSpec,
        left: float,
        top: float,
        width: float,
        height: float,
        presentation: Any,
    ) -> Any:
        shape = slide.Shapes.AddTable(
            len(spec.rows) + 1,
            len(spec.columns),
            left,
            top,
            width,
            height,
        )
        for row_index, row in enumerate((spec.columns, *spec.rows), start=1):
            for column_index, value in enumerate(row, start=1):
                cell_shape = shape.Table.Cell(row_index, column_index).Shape
                cell_shape.TextFrame.TextRange.Text = value
                cell_shape.TextFrame.TextRange.Font.Name = item.font_name
                cell_shape.TextFrame.TextRange.Font.Size = item.font_size_pt
                cell_shape.TextFrame.TextRange.Font.Color.RGB = _office_rgb(
                    item.fill_color if row_index == 1 else item.text_color
                )
                cell_shape.Fill.Solid()
                cell_shape.Fill.ForeColor.RGB = _office_rgb(
                    item.line_color if row_index == 1 else item.fill_color
                )
                _record(
                    presentation,
                    "set-table-cell",
                    f"{row_index}:{column_index}",
                    value,
                )
        return shape

    def _render_diagram(
        self,
        slide: Any,
        item: RenderObject,
        spec: DiagramSpec,
        left: float,
        top: float,
        width: float,
        height: float,
        presentation: Any,
    ) -> Any:
        count = len(spec.nodes)
        if count < 1:
            raise RenderError("diagram has no governed nodes")
        names: list[str] = []
        if spec.diagram_type == "funnel":
            node_height = height / count
            boxes = []
            for index in range(count):
                ratio = 1.0 - (0.42 * index / max(1, count - 1))
                node_width = width * ratio
                boxes.append(
                    (
                        left + (width - node_width) / 2,
                        top + index * node_height,
                        node_width,
                        node_height * 0.82,
                    )
                )
        elif spec.diagram_type in {"matrix", "quadrant"}:
            columns = 2
            rows = (count + 1) // 2
            gap = 8.0
            cell_width = (width - gap) / columns
            cell_height = (height - gap * max(0, rows - 1)) / rows
            boxes = [
                (
                    left + (index % columns) * (cell_width + gap),
                    top + (index // columns) * (cell_height + gap),
                    cell_width,
                    cell_height,
                )
                for index in range(count)
            ]
        else:
            gap = min(18.0, width * 0.025)
            node_width = (width - gap * max(0, count - 1)) / count
            node_height = height * 0.62
            boxes = [
                (
                    left + index * (node_width + gap),
                    top
                    + (
                        height * 0.08 * (index % 2)
                        if spec.diagram_type == "roadmap"
                        else (height - node_height) / 2
                    ),
                    node_width,
                    node_height,
                )
                for index in range(count)
            ]

        for index, (node, box) in enumerate(zip(spec.nodes, boxes), start=1):
            node_shape = slide.Shapes.AddShape(MSO_SHAPE_RECTANGLE, *box)
            node_shape.Name = f"{item.name}__node_{index:02d}"
            node_shape.Tags.Add("window-pptx:diagram", spec.diagram_type)
            node_shape.Tags.Add("window-pptx:editable", "true")
            node_shape.Fill.Solid()
            node_shape.Fill.ForeColor.RGB = _office_rgb(item.fill_color)
            node_shape.Line.Visible = MSO_TRUE
            node_shape.Line.ForeColor.RGB = _office_rgb(item.line_color)
            node_shape.TextFrame.TextRange.Text = (
                node.label if node.detail is None else f"{node.label}\n{node.detail}"
            )
            node_shape.TextFrame.TextRange.Font.Name = item.font_name
            node_shape.TextFrame.TextRange.Font.Size = item.font_size_pt
            node_shape.TextFrame.TextRange.Font.Color.RGB = _office_rgb(
                item.text_color
            )
            names.append(node_shape.Name)
            _record(
                presentation,
                "add-diagram-node",
                node_shape.Name,
                spec.diagram_type,
                node.label,
                *box,
            )
        if len(names) == 1:
            return slide.Shapes.Item(names[0])
        group = slide.Shapes.Range(tuple(names)).Group()
        group.Name = f"{item.name}__diagram"
        group.Tags.Add("window-pptx:diagram", spec.diagram_type)
        group.Tags.Add("window-pptx:editable", "true")
        return group

    def _apply_hyperlink(
        self,
        shape: Any,
        target: str,
        slides_by_id: dict[str, Any],
        presentation: Any,
    ) -> None:
        group_items = getattr(shape, "GroupItems", None)
        if isinstance(group_items, tuple):
            targets = list(group_items) or [shape]
        elif group_items is not None and hasattr(group_items, "Count"):
            targets = [
                group_items.Item(index)
                for index in range(1, int(group_items.Count) + 1)
            ]
        else:
            targets = [shape]
        for target_shape in targets:
            hyperlink = target_shape.ActionSettings(PP_MOUSE_CLICK).Hyperlink
            if target.startswith("slide:"):
                target_id = target.removeprefix("slide:")
                target_slide = slides_by_id[target_id]
                target_index = getattr(
                    target_slide, "SlideIndex", getattr(target_slide, "index", 0)
                )
                hyperlink.Address = ""
                hyperlink.SubAddress = (
                    f"{target_slide.SlideID},{target_index},{target_id}"
                )
            else:
                hyperlink.Address = target
                hyperlink.SubAddress = ""
        _record(presentation, "add-hyperlink", shape.Name, target)

    def _set_speaker_notes(
        self, slide: Any, notes: str, presentation: Any
    ) -> None:
        if hasattr(slide, "notes_text"):
            slide.notes_text = notes
        else:
            placeholders = slide.NotesPage.Shapes.Placeholders
            target = None
            for index in range(1, int(placeholders.Count) + 1):
                candidate = placeholders.Item(index)
                if bool(candidate.HasTextFrame) and int(candidate.PlaceholderFormat.Type) == 2:
                    target = candidate
                    break
            if target is None:
                target = placeholders.Item(2)
            target.TextFrame.TextRange.Text = notes
        slide_index = getattr(slide, "SlideIndex", getattr(slide, "index", "?"))
        _record(presentation, "set-speaker-notes", f"slide-{slide_index}", notes)

    def _apply_motion(
        self,
        slide: Any,
        render_slide: RenderSlide,
        created: dict[str, tuple[RenderObject, Any]],
        groups: dict[str, Any],
        presentation: Any,
    ) -> None:
        if render_slide.motion == "off":
            return
        targets: list[Any] = []
        trigger = MSO_ANIM_TRIGGER_AFTER_PREVIOUS
        if render_slide.motion == "subtle-fade":
            group_id = f"wp_s{render_slide.index:03d}_content"
            if group_id in groups:
                targets = [groups[group_id]]
            else:
                targets = [
                    shape
                    for item, shape in created.values()
                    if item.component not in {"footer", "decoration"}
                ]
        else:
            trigger = MSO_ANIM_TRIGGER_ON_PAGE_CLICK
            targets = [
                shape
                for item, shape in created.values()
                if item.component not in {"title", "footer", "decoration"}
            ]
        for shape in targets:
            slide.TimeLine.MainSequence.AddEffect(
                shape,
                MSO_ANIM_EFFECT_FADE,
                0,
                trigger,
            )
            _record(
                presentation,
                "add-motion-effect",
                shape.Name,
                render_slide.motion,
                trigger,
            )

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
