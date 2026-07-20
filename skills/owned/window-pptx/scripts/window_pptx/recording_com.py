"""Small in-memory recording substitute for the PowerPoint COM boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .assets import read_raster_dimensions


def _image_size_points(path: Path) -> tuple[float, float]:
    """Read raster dimensions without accepting arbitrary placeholder bytes."""

    width_px, height_px = read_raster_dimensions(path)
    # PowerPoint imports raster images at 96 DPI, or 0.75 points per pixel.
    return width_px * 0.75, height_px * 0.75


@dataclass(frozen=True)
class RecordingCall:
    operation: str
    target: str
    arguments: tuple[Any, ...] = ()


@dataclass
class RecordingColor:
    RGB: int = 0


@dataclass
class RecordingFill:
    ForeColor: RecordingColor = field(default_factory=RecordingColor)
    visible: bool = True

    def Solid(self) -> None:
        self.visible = True


@dataclass
class RecordingLine:
    ForeColor: RecordingColor = field(default_factory=RecordingColor)
    Weight: float = 0.0
    Visible: int = -1


@dataclass
class RecordingFont:
    Name: str = ""
    Size: float = 0.0
    Color: RecordingColor = field(default_factory=RecordingColor)


@dataclass
class RecordingTextRange:
    Text: str = ""
    Font: RecordingFont = field(default_factory=RecordingFont)


@dataclass
class RecordingTextFrame:
    TextRange: RecordingTextRange = field(default_factory=RecordingTextRange)
    MarginLeft: float = 0.0
    MarginRight: float = 0.0
    MarginTop: float = 0.0
    MarginBottom: float = 0.0
    WordWrap: int = -1
    AutoSize: int = 0


@dataclass
class RecordingTags:
    values: dict[str, str] = field(default_factory=dict)

    def Add(self, key: str, value: str) -> None:
        self.values[key] = value


@dataclass
class RecordingCrop:
    ShapeWidth: float = 0.0
    ShapeHeight: float = 0.0
    PictureWidth: float = 0.0
    PictureHeight: float = 0.0
    PictureOffsetX: float = 0.0
    PictureOffsetY: float = 0.0


@dataclass
class RecordingPictureFormat:
    Crop: RecordingCrop = field(default_factory=RecordingCrop)


@dataclass
class RecordingHyperlink:
    Address: str = ""
    SubAddress: str = ""


@dataclass
class RecordingActionSetting:
    Hyperlink: RecordingHyperlink = field(default_factory=RecordingHyperlink)


class RecordingActionSettings:
    def __init__(self) -> None:
        self._settings: dict[int, RecordingActionSetting] = {}

    def __call__(self, index: int) -> RecordingActionSetting:
        return self._settings.setdefault(index, RecordingActionSetting())

    def Item(self, index: int) -> RecordingActionSetting:
        return self(index)


@dataclass
class RecordingCellShape:
    TextFrame: RecordingTextFrame = field(default_factory=RecordingTextFrame)
    Fill: RecordingFill = field(default_factory=RecordingFill)
    Line: RecordingLine = field(default_factory=RecordingLine)


@dataclass
class RecordingTableCell:
    Shape: RecordingCellShape = field(default_factory=RecordingCellShape)


class RecordingTable:
    def __init__(self, rows: int, columns: int) -> None:
        self.rows = rows
        self.columns = columns
        self._cells = {
            (row, column): RecordingTableCell()
            for row in range(1, rows + 1)
            for column in range(1, columns + 1)
        }

    def Cell(self, row: int, column: int) -> RecordingTableCell:
        return self._cells[(row, column)]


class RecordingChartData:
    def __init__(self) -> None:
        self.activated = False

    def Activate(self) -> None:
        self.activated = True


class RecordingChart:
    def __init__(self) -> None:
        self.ChartData = RecordingChartData()
        self.HasTitle = 0
        self.HasLegend = 0
        self.DisplayBlanksAs = 1
        self.spec: Any = None

    def _set_data(self, spec: Any) -> None:
        self.spec = spec


class RecordingSequence:
    def __init__(self) -> None:
        self.effects: list[tuple[Any, int, int, int]] = []

    def AddEffect(
        self, shape: Any, effect_id: int, level: int, trigger: int
    ) -> tuple[Any, int, int, int]:
        effect = (shape, effect_id, level, trigger)
        self.effects.append(effect)
        return effect


class RecordingTimeline:
    def __init__(self) -> None:
        self.MainSequence = RecordingSequence()


class RecordingShape:
    def __init__(
        self,
        owner: "RecordingPresentation",
        kind: str,
        left: float,
        top: float,
        width: float,
        height: float,
        parent: "RecordingShapes | None" = None,
    ) -> None:
        self._owner = owner
        self.kind = kind
        self._parent = parent
        self.Left = left
        self.Top = top
        self.Width = 800.0 if width < 0 else width
        self.Height = 600.0 if height < 0 else height
        self.Name = ""
        self.Tags = RecordingTags()
        self.Fill = RecordingFill()
        self.Line = RecordingLine()
        self.TextFrame = RecordingTextFrame()
        self.PictureFormat = RecordingPictureFormat()
        self.ActionSettings = RecordingActionSettings()
        self.Chart: RecordingChart | None = None
        self.Table: RecordingTable | None = None
        self.LockAspectRatio = 0
        self.editable = True
        self.GroupItems: tuple[RecordingShape, ...] = ()

    def ZOrder(self, command: int) -> None:
        self._owner._record("z-order", self.Name, command)

    def Delete(self) -> None:
        if self._parent is None or self not in self._parent.items:
            raise RuntimeError("recording shape is not attached to a collection")
        self._owner._record(
            "delete-shape",
            self.Name or self.kind,
            self._parent._target,
        )
        self._parent.items.remove(self)


class RecordingShapeRange:
    def __init__(
        self,
        owner: "RecordingPresentation",
        shapes: "RecordingShapes",
        names: tuple[str, ...],
    ) -> None:
        self._owner = owner
        self._shapes = shapes
        self._names = names

    def Group(self) -> RecordingShape:
        self._owner._record("group", "|".join(self._names), *self._names)
        members = [self._shapes.by_name(name) for name in self._names]
        left = min(item.Left for item in members)
        top = min(item.Top for item in members)
        right = max(item.Left + item.Width for item in members)
        bottom = max(item.Top + item.Height for item in members)
        for item in members:
            self._shapes.items.remove(item)
        group = RecordingShape(
            self._owner,
            "group",
            left,
            top,
            right - left,
            bottom - top,
            self._shapes,
        )
        group.GroupItems = tuple(members)
        self._shapes.items.append(group)
        return group


class RecordingShapes:
    def __init__(self, owner: "RecordingPresentation", target: str) -> None:
        self._owner = owner
        self._target = target
        self.items: list[RecordingShape] = []

    @property
    def Count(self) -> int:
        return len(self.items)

    def by_name(self, name: str) -> RecordingShape:
        matches = [shape for shape in self.items if shape.Name == name]
        if len(matches) != 1:
            raise KeyError(f"shape range name is missing or ambiguous: {name}")
        return matches[0]

    def Item(self, key: int | str) -> RecordingShape:
        return self.items[key - 1] if isinstance(key, int) else self.by_name(key)

    def _add(
        self,
        operation: str,
        kind: str,
        left: float,
        top: float,
        width: float,
        height: float,
        *extra: Any,
    ) -> RecordingShape:
        self._owner._record(
            operation,
            self._target,
            *extra,
            left,
            top,
            width,
            height,
        )
        shape = RecordingShape(
            self._owner, kind, left, top, width, height, self
        )
        self.items.append(shape)
        return shape


    def AddTextbox(
        self,
        orientation: int,
        left: float,
        top: float,
        width: float,
        height: float,
    ) -> RecordingShape:
        return self._add(
            "add-textbox", "text", left, top, width, height, orientation
        )

    def AddShape(
        self,
        shape_type: int,
        left: float,
        top: float,
        width: float,
        height: float,
    ) -> RecordingShape:
        return self._add(
            "add-shape", "shape", left, top, width, height, shape_type
        )

    def AddPicture(
        self,
        filename: str,
        link_to_file: int,
        save_with_document: int,
        left: float,
        top: float,
        width: float = -1,
        height: float = -1,
    ) -> RecordingShape:
        natural_width, natural_height = _image_size_points(Path(filename))
        return self._add(
            "add-picture",
            "image",
            left,
            top,
            natural_width if width < 0 else width,
            natural_height if height < 0 else height,
            filename,
            link_to_file,
            save_with_document,
        )

    def AddChart2(
        self,
        style: int,
        chart_type: int,
        left: float,
        top: float,
        width: float,
        height: float,
        new_layout: int,
    ) -> RecordingShape:
        shape = self._add(
            "add-chart",
            "chart",
            left,
            top,
            width,
            height,
            style,
            chart_type,
            new_layout,
        )
        shape.Chart = RecordingChart()
        return shape

    def AddTable(
        self,
        rows: int,
        columns: int,
        left: float,
        top: float,
        width: float,
        height: float,
    ) -> RecordingShape:
        shape = self._add(
            "add-table",
            "table",
            left,
            top,
            width,
            height,
            rows,
            columns,
        )
        shape.Table = RecordingTable(rows, columns)
        return shape

    def Range(self, names: Iterable[str]) -> RecordingShapeRange:
        normalized = tuple(names)
        if not normalized or len(normalized) != len(set(normalized)):
            raise ValueError("shape range names must be unique and non-empty")
        for name in normalized:
            self.by_name(name)
        self._owner._record("shape-range", self._target, *normalized)
        return RecordingShapeRange(self._owner, self, normalized)


class RecordingSlide:
    def __init__(
        self,
        owner: "RecordingPresentation",
        collection: "RecordingSlides",
        index: int,
    ) -> None:
        self._owner = owner
        self._collection = collection
        self.index = index
        self.Shapes = RecordingShapes(owner, f"slide-{index}")
        self.FollowMasterBackground = -1
        self.SlideID = 255 + index
        self.notes_text = ""
        self.TimeLine = RecordingTimeline()

    def Delete(self) -> None:
        self._owner._record("delete-slide", f"slide-{self.index}", self.index)
        self._collection.items.remove(self)
        self._collection.renumber()

    def Export(
        self,
        filename: str,
        filter_name: str,
        width: int,
        height: int,
    ) -> None:
        self._owner._record(
            "export-slide",
            f"slide-{self.index}",
            filename,
            filter_name,
            width,
            height,
        )


class RecordingSlides:
    def __init__(self, owner: "RecordingPresentation") -> None:
        self._owner = owner
        self.items: list[RecordingSlide] = []

    @property
    def Count(self) -> int:
        return len(self.items)

    def renumber(self) -> None:
        for index, slide in enumerate(self.items, start=1):
            slide.index = index

    def Item(self, index: int) -> RecordingSlide:
        if type(index) is not int or not 1 <= index <= len(self.items):
            raise IndexError(f"slide index out of range: {index}")
        return self.items[index - 1]

    def __call__(self, index: int) -> RecordingSlide:
        return self.Item(index)

    def Add(self, index: int, layout: int) -> RecordingSlide:
        self._owner._record("add-slide", "slides", index, layout)
        if type(index) is not int or not 1 <= index <= len(self.items) + 1:
            raise IndexError(f"slide insert index out of range: {index}")
        slide = RecordingSlide(self._owner, self, index)
        self.items.insert(index - 1, slide)
        self.renumber()
        return slide


@dataclass
class RecordingPageSetup:
    SlideWidth: float = 0.0
    SlideHeight: float = 0.0


class RecordingMaster:
    def __init__(self, owner: "RecordingPresentation") -> None:
        self.Shapes = RecordingShapes(owner, "slide-master")


class RecordingPresentation:
    """PowerPoint-shaped object that records deterministic renderer calls."""

    def __init__(
        self,
        *,
        fail_operation: str | None = None,
        initial_slide_count: int = 0,
        initial_master_shape_count: int = 0,
    ) -> None:
        self.calls: list[RecordingCall] = []
        self.fail_operation = fail_operation
        self.PageSetup = RecordingPageSetup()
        self.Slides = RecordingSlides(self)
        for index in range(1, initial_slide_count + 1):
            self.Slides.items.append(RecordingSlide(self, self.Slides, index))
        self.SlideMaster = RecordingMaster(self)
        for index in range(1, initial_master_shape_count + 1):
            shape = RecordingShape(
                self,
                "legacy-master-shape",
                0,
                0,
                100,
                100,
                self.SlideMaster.Shapes,
            )
            shape.Name = f"legacy_master_{index}"
            self.SlideMaster.Shapes.items.append(shape)
        self.close_calls = 0

    def _record(self, operation: str, target: str, *arguments: Any) -> None:
        self._maybe_fail(operation)
        self.calls.append(RecordingCall(operation, target, tuple(arguments)))

    def _maybe_fail(self, operation: str) -> None:
        if self.fail_operation == operation:
            raise RuntimeError(f"injected recording COM failure: {operation}")

    def Close(self) -> None:
        self.close_calls += 1
        self._record("close-presentation", "presentation")


__all__ = ["RecordingCall", "RecordingPresentation"]
