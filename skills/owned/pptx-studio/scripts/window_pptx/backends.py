"""Backend capability negotiation for governed RenderPlan execution.

The model never selects a renderer.  A validated RenderPlan declares the
capabilities it needs and this module either chooses a backend that satisfies
them or fails before any candidate file is created.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path

from .render_plan import RenderPlan, validate_render_plan


class CapabilityError(ValueError):
    """The selected backend cannot preserve a required RenderPlan capability."""


@dataclass(frozen=True)
class BackendCapabilities:
    backend_id: str
    native_text: bool
    native_shape: bool
    native_image: bool
    native_table: bool
    native_chart: bool
    master_layout: bool
    speaker_notes: bool
    hyperlinks: bool
    logical_diagram: bool
    physical_template_import: bool
    macro_enabled_output: bool
    powerpoint_template_output: bool
    shape_grouping: bool
    shape_animation: bool
    powerpoint_render: bool
    headless_render: bool

    def to_dict(self) -> dict[str, bool | str]:
        return {
            item.name: getattr(self, item.name)
            for item in fields(self)
        }


@dataclass(frozen=True)
class BackendSelection:
    backend_id: str
    capabilities: BackendCapabilities
    required_capabilities: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "backend_id": self.backend_id,
            "capabilities": self.capabilities.to_dict(),
            "required_capabilities": list(self.required_capabilities),
        }


_BACKENDS = {
    "pptxgenjs": BackendCapabilities(
        backend_id="pptxgenjs",
        native_text=True,
        native_shape=True,
        native_image=True,
        native_table=True,
        native_chart=True,
        master_layout=True,
        speaker_notes=True,
        hyperlinks=True,
        logical_diagram=True,
        physical_template_import=False,
        macro_enabled_output=False,
        powerpoint_template_output=False,
        shape_grouping=False,
        shape_animation=False,
        powerpoint_render=False,
        headless_render=True,
    ),
    "com": BackendCapabilities(
        backend_id="com",
        native_text=True,
        native_shape=True,
        native_image=True,
        native_table=True,
        native_chart=True,
        master_layout=True,
        speaker_notes=True,
        hyperlinks=True,
        logical_diagram=True,
        physical_template_import=True,
        macro_enabled_output=True,
        powerpoint_template_output=True,
        shape_grouping=True,
        shape_animation=True,
        powerpoint_render=True,
        headless_render=False,
    ),
}


def backend_capabilities(backend_id: str) -> BackendCapabilities:
    try:
        return _BACKENDS[backend_id]
    except KeyError as exc:
        raise CapabilityError(f"unknown render backend: {backend_id}") from exc


def required_capabilities(
    plan: RenderPlan,
    *,
    output_path: Path | None = None,
    require_physical_template: bool = False,
) -> tuple[str, ...]:
    validate_render_plan(plan)
    required = {"master_layout"}
    if require_physical_template:
        required.add("physical_template_import")
    if output_path is not None:
        suffix = output_path.suffix.casefold()
        if suffix in {".pptm", ".potm"}:
            required.add("macro_enabled_output")
        if suffix in {".potx", ".potm"}:
            required.add("powerpoint_template_output")
    for slide in plan.slides:
        if slide.speaker_notes:
            required.add("speaker_notes")
        if slide.motion != "off":
            required.add("shape_animation")
        for item in slide.objects:
            required.add(
                {
                    "text": "native_text",
                    "shape": "native_shape",
                    "image": "native_image",
                    "table": "native_table",
                    "chart": "native_chart",
                    "diagram": "logical_diagram",
                }[item.kind]
            )
            if item.hyperlink:
                required.add("hyperlinks")
    return tuple(sorted(required))


def negotiate_backend(
    requested: str,
    plan: RenderPlan,
    *,
    output_path: Path | None = None,
    require_physical_template: bool = False,
) -> BackendSelection:
    if requested not in {"auto", *tuple(_BACKENDS)}:
        raise CapabilityError(f"unknown render backend: {requested}")
    backend_id = "pptxgenjs" if requested == "auto" else requested
    capabilities = backend_capabilities(backend_id)
    required = required_capabilities(
        plan,
        output_path=output_path,
        require_physical_template=require_physical_template,
    )
    missing = tuple(
        capability
        for capability in required
        if not bool(getattr(capabilities, capability))
    )
    if missing:
        raise CapabilityError(
            f"backend {backend_id} lacks required capabilities: "
            + ", ".join(missing)
        )
    return BackendSelection(backend_id, capabilities, required)


__all__ = [
    "BackendCapabilities",
    "BackendSelection",
    "CapabilityError",
    "backend_capabilities",
    "negotiate_backend",
    "required_capabilities",
]
