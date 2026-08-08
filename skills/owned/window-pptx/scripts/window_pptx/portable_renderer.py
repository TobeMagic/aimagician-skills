"""Skill-local PptxGenJS adapter for portable, editable PPTX rendering."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .render_plan import RenderPlan, validate_render_plan
from .transaction import validate_ooxml_package


PROTOCOL_VERSION = "1.0"
PINNED_PPTXGENJS_VERSION = "4.0.1"


class PortableRenderError(RuntimeError):
    """The portable worker failed closed before returning a valid PPTX."""


@dataclass(frozen=True)
class BackendRenderResult:
    """Evidence returned by a successful backend render."""

    backend_id: str
    backend_version: str
    output_path: Path
    slide_count: int
    planned_object_count: int
    native_editable_count: int
    diagram_child_count: int
    object_names: tuple[str, ...]
    group_names: tuple[str, ...]
    warnings: tuple[str, ...]
    protocol_version: str = PROTOCOL_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "protocol_version": self.protocol_version,
            "backend_id": self.backend_id,
            "backend_version": self.backend_version,
            "output_path": str(self.output_path),
            "slide_count": self.slide_count,
            "planned_object_count": self.planned_object_count,
            "native_editable_count": self.native_editable_count,
            "diagram_child_count": self.diagram_child_count,
            "object_names": list(self.object_names),
            "group_names": list(self.group_names),
            "warnings": list(self.warnings),
        }


class PptxGenJSRenderer:
    """Execute a validated RenderPlan through the pinned skill-local Node worker."""

    def __init__(
        self,
        *,
        skill_root: Path | None = None,
        node_binary: str | Path | None = None,
        timeout_seconds: float = 120.0,
    ) -> None:
        self.skill_root = (
            Path(skill_root).resolve()
            if skill_root is not None
            else Path(__file__).resolve().parents[2]
        )
        self.node_dir = self.skill_root / "scripts" / "node"
        self.worker_path = self.node_dir / "window_pptx_worker.mjs"
        selected_node = str(node_binary) if node_binary is not None else shutil.which("node")
        if not selected_node:
            raise PortableRenderError("Node.js is required for the pptxgenjs backend")
        self.node_binary = selected_node
        if not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self.timeout_seconds = float(timeout_seconds)

    def _assert_runtime(self) -> None:
        if not self.worker_path.is_file():
            raise PortableRenderError(f"portable worker is missing: {self.worker_path}")
        package = self.node_dir / "node_modules" / "pptxgenjs" / "package.json"
        if not package.is_file():
            raise PortableRenderError(
                "skill-local PptxGenJS dependencies are missing; run npm ci in "
                f"{self.node_dir}"
            )
        try:
            metadata = json.loads(package.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PortableRenderError(
                f"installed PptxGenJS metadata is unreadable: {exc}"
            ) from exc
        installed_version = (
            metadata.get("version") if isinstance(metadata, dict) else None
        )
        if installed_version != PINNED_PPTXGENJS_VERSION:
            raise PortableRenderError(
                "portable backend requires exact PptxGenJS "
                f"{PINNED_PPTXGENJS_VERSION}; installed={installed_version!r}"
            )

    def _run_worker(self, request: dict[str, object]) -> dict[str, Any]:
        self._assert_runtime()
        encoded = json.dumps(
            request,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        )
        try:
            completed = subprocess.run(
                [self.node_binary, str(self.worker_path)],
                input=encoded,
                cwd=self.node_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="strict",
                timeout=self.timeout_seconds,
                check=False,
                shell=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise PortableRenderError(
                f"pptxgenjs worker timed out after {self.timeout_seconds:g} seconds"
            ) from exc
        except OSError as exc:
            raise PortableRenderError(f"could not start pptxgenjs worker: {exc}") from exc
        if completed.returncode != 0:
            detail = completed.stderr.strip() or completed.stdout.strip() or "unknown worker error"
            try:
                error_payload = json.loads(detail.splitlines()[-1])
            except json.JSONDecodeError:
                error_payload = None
            if isinstance(error_payload, dict) and isinstance(error_payload.get("error"), str):
                detail = error_payload["error"]
            raise PortableRenderError(f"pptxgenjs worker failed: {detail}")
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        if len(lines) != 1:
            raise PortableRenderError("pptxgenjs worker returned an invalid response envelope")
        try:
            payload = json.loads(lines[0])
        except json.JSONDecodeError as exc:
            raise PortableRenderError("pptxgenjs worker returned malformed JSON") from exc
        if not isinstance(payload, dict):
            raise PortableRenderError("pptxgenjs worker response must be an object")
        return payload

    @staticmethod
    def _parse_result(payload: dict[str, Any], expected_output: Path) -> BackendRenderResult:
        allowed = {
            "protocol_version",
            "ok",
            "backend_id",
            "backend_version",
            "output_path",
            "slide_count",
            "planned_object_count",
            "native_editable_count",
            "diagram_child_count",
            "object_names",
            "group_names",
            "warnings",
        }
        unknown = set(payload) - allowed
        if unknown:
            raise PortableRenderError(
                "pptxgenjs worker response contains unknown fields: "
                + ", ".join(sorted(unknown))
            )
        if payload.get("protocol_version") != PROTOCOL_VERSION or payload.get("ok") is not True:
            raise PortableRenderError("pptxgenjs worker response protocol is unsupported")
        if payload.get("backend_id") != "pptxgenjs":
            raise PortableRenderError("pptxgenjs worker reported the wrong backend")
        backend_version = payload.get("backend_version")
        output_path = payload.get("output_path")
        if not isinstance(backend_version, str) or not backend_version:
            raise PortableRenderError("pptxgenjs worker omitted its backend version")
        if backend_version != PINNED_PPTXGENJS_VERSION:
            raise PortableRenderError(
                "pptxgenjs worker version drifted from the exact pin: "
                f"expected {PINNED_PPTXGENJS_VERSION}, observed {backend_version}"
            )
        if not isinstance(output_path, str):
            raise PortableRenderError("pptxgenjs worker omitted its output path")
        actual_output = Path(output_path).resolve()
        if actual_output != expected_output:
            raise PortableRenderError("pptxgenjs worker output path drifted from the request")

        def integer(field: str) -> int:
            value = payload.get(field)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise PortableRenderError(f"pptxgenjs worker returned invalid {field}")
            return value

        def strings(field: str) -> tuple[str, ...]:
            value = payload.get(field)
            if not isinstance(value, list) or not all(
                isinstance(item, str) for item in value
            ):
                raise PortableRenderError(f"pptxgenjs worker returned invalid {field}")
            return tuple(value)

        return BackendRenderResult(
            backend_id="pptxgenjs",
            backend_version=backend_version,
            output_path=actual_output,
            slide_count=integer("slide_count"),
            planned_object_count=integer("planned_object_count"),
            native_editable_count=integer("native_editable_count"),
            diagram_child_count=integer("diagram_child_count"),
            object_names=strings("object_names"),
            group_names=strings("group_names"),
            warnings=strings("warnings"),
        )

    def doctor(self) -> dict[str, Any]:
        """Return the pinned worker/runtime version without creating a presentation."""

        self._assert_runtime()
        try:
            completed = subprocess.run(
                [self.node_binary, str(self.worker_path), "--doctor"],
                cwd=self.node_dir,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="strict",
                timeout=min(self.timeout_seconds, 30.0),
                check=False,
                shell=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise PortableRenderError(f"pptxgenjs worker doctor failed: {exc}") from exc
        if completed.returncode != 0:
            raise PortableRenderError(
                "pptxgenjs worker doctor failed: "
                + (completed.stderr.strip() or "unknown error")
            )
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise PortableRenderError("pptxgenjs worker doctor returned malformed JSON") from exc
        if (
            not isinstance(result, dict)
            or result.get("ok") is not True
            or result.get("backend_id") != "pptxgenjs"
            or result.get("protocol_version") != PROTOCOL_VERSION
        ):
            raise PortableRenderError("pptxgenjs worker doctor returned invalid evidence")
        return result

    def render(self, plan: RenderPlan, output_path: Path) -> BackendRenderResult:
        """Render *plan* to a new PPTX path and return backend evidence."""

        validate_render_plan(plan)
        output = Path(output_path).resolve()
        if output.suffix.casefold() != ".pptx":
            raise PortableRenderError("portable backend output must end in .pptx")
        if output.exists():
            raise PortableRenderError(f"portable backend refuses to overwrite: {output}")
        for slide in plan.slides:
            if slide.motion != "off":
                raise PortableRenderError(
                    "pptxgenjs backend does not support shape motion; select COM or disable motion"
                )
        output.parent.mkdir(parents=True, exist_ok=True)
        request: dict[str, object] = {
            "protocol_version": PROTOCOL_VERSION,
            "output_path": str(output),
            "render_plan": plan.to_dict(),
        }
        try:
            payload = self._run_worker(request)
            result = self._parse_result(payload, output)
            validate_ooxml_package(output)
        except Exception:
            if output.exists():
                output.unlink()
            raise
        expected_names = tuple(
            item.name for slide in plan.slides for item in slide.objects
        )
        if result.slide_count != len(plan.slides):
            output.unlink(missing_ok=True)
            raise PortableRenderError("pptxgenjs worker slide count drifted from RenderPlan")
        if result.planned_object_count != len(expected_names):
            output.unlink(missing_ok=True)
            raise PortableRenderError("pptxgenjs worker object count drifted from RenderPlan")
        if result.object_names != expected_names:
            output.unlink(missing_ok=True)
            raise PortableRenderError("pptxgenjs worker object identity order drifted from RenderPlan")
        if result.native_editable_count < len(expected_names):
            output.unlink(missing_ok=True)
            raise PortableRenderError("pptxgenjs worker did not preserve native editability")
        return result


__all__ = [
    "BackendRenderResult",
    "PptxGenJSRenderer",
    "PortableRenderError",
]
