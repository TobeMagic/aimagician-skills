"""Small in-memory recording substitute for the PowerPoint COM boundary."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable


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


class RecordingShape:
    def __init__(
        self,
        owner: "RecordingPresentation",
        kind: str,
        left: float,
        top: float,
        width: float,
        height: float,
    ) -> None:
        self._owner = owner
        self.kind = kind
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
        self.LockAspectRatio = 0
        self.editable = True

    def ZOrder(self, command: int) -> None:
        self._owner._record("z-order", self.Name, command)


class RecordingShapeRange:
    def __init__(
        self,
        owner: "RecordingPresentation",
        names: tuple[str, ...],
    ) -> None:
        self._owner = owner
        self._names = names

    def Group(self) -> RecordingShape:
        self._owner._record("group", "|".join(self._names), *self._names)
        group = RecordingShape(self._owner, "group", 0, 0, 0, 0)
        group.Name = "group"
        return group


class RecordingShapes:
    def __init__(self, owner: "RecordingPresentation", target: str) -> None:
        self._owner = owner
        self._target = target
        self.items: list[RecordingShape] = []

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
        self._owner._maybe_fail(operation)
        self._owner._record(
            operation,
            self._target,
            *extra,
            left,
            top,
            width,
            height,
        )
        shape = RecordingShape(self._owner, kind, left, top, width, height)
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
        return self._add(
            "add-picture",
            "image",
            left,
            top,
            width,
            height,
            filename,
            link_to_file,
            save_with_document,
        )

    def Range(self, names: Iterable[str]) -> RecordingShapeRange:
        normalized = tuple(names)
        self._owner._record("shape-range", self._target, *normalized)
        return RecordingShapeRange(self._owner, normalized)


class RecordingSlide:
    def __init__(self, owner: "RecordingPresentation", index: int) -> None:
        self.index = index
        self.Shapes = RecordingShapes(owner, f"slide-{index}")
        self.FollowMasterBackground = -1


class RecordingSlides:
    def __init__(self, owner: "RecordingPresentation") -> None:
        self._owner = owner
        self.items: list[RecordingSlide] = []

    def Add(self, index: int, layout: int) -> RecordingSlide:
        self._owner._maybe_fail("add-slide")
        self._owner._record("add-slide", "slides", index, layout)
        slide = RecordingSlide(self._owner, index)
        self.items.append(slide)
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

    def __init__(self, *, fail_operation: str | None = None) -> None:
        self.calls: list[RecordingCall] = []
        self.fail_operation = fail_operation
        self.PageSetup = RecordingPageSetup()
        self.Slides = RecordingSlides(self)
        self.SlideMaster = RecordingMaster(self)
        self.close_calls = 0

    def _record(self, operation: str, target: str, *arguments: Any) -> None:
        self.calls.append(RecordingCall(operation, target, tuple(arguments)))

    def _maybe_fail(self, operation: str) -> None:
        if self.fail_operation == operation:
            raise RuntimeError(f"injected recording COM failure: {operation}")

    def Close(self) -> None:
        self.close_calls += 1
        self._record("close-presentation", "presentation")


__all__ = ["RecordingCall", "RecordingPresentation"]
