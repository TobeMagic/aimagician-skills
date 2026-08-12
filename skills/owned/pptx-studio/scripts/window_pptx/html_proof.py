"""Deterministic RenderPlan-derived HTML proof.

This preview is deliberately downstream of RenderPlan.  It is never parsed to
create the PPTX and never accepts model-authored HTML or CSS.
"""

from __future__ import annotations

import html
from pathlib import Path

from .render_plan import ChartSpec, DiagramSpec, RenderObject, RenderPlan, TableSpec, validate_render_plan


def _style(item: RenderObject) -> str:
    return ";".join(
        (
            f"left:{item.x}in",
            f"top:{item.y}in",
            f"width:{item.width}in",
            f"height:{item.height}in",
            f"z-index:{item.layer}",
            f"font-family:{html.escape(item.font_name, quote=True)}",
            f"font-size:{item.font_size_pt}pt",
            f"color:{item.text_color}",
            f"background:{item.fill_color}",
            f"border-color:{item.line_color}",
        )
    )


def _content(item: RenderObject) -> str:
    if item.kind == "image" and item.source_path is not None:
        return (
            f'<img src="{html.escape(item.source_path.resolve().as_uri(), quote=True)}" '
            'alt="" draggable="false">'
        )
    if isinstance(item.advanced, TableSpec):
        header = "".join(f"<th>{html.escape(value)}</th>" for value in item.advanced.columns)
        rows = "".join(
            "<tr>" + "".join(f"<td>{html.escape(value)}</td>" for value in row) + "</tr>"
            for row in item.advanced.rows
        )
        return f"<table><thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table>"
    if isinstance(item.advanced, ChartSpec):
        suffix = (
            "%"
            if (item.advanced.value_unit or "").strip().casefold()
            in {"%", "percent", "percentage"}
            else ""
        )
        values = " · ".join(
            f"{html.escape(series.name)}: "
            + ", ".join(
                "—" if value is None else f"{value:g}{suffix}"
                for value in series.values
            )
            for series in item.advanced.series
        )
        return f'<div class="proof-chart">{html.escape(values)}</div>'
    if isinstance(item.advanced, DiagramSpec):
        return "".join(
            f'<div class="proof-node">{html.escape(node.label)}</div>'
            for node in item.advanced.nodes
        )
    if item.text_runs is not None:
        return "".join(
            (
                '<span style="'
                f'font-size:{run.font_size_pt}pt;color:{run.text_color};'
                f'font-weight:{"700" if run.bold else "400"};'
                f'font-style:{"italic" if run.italic else "normal"}'
                f'">{html.escape(run.text)}</span>'
                + ("<br>" if run.break_after else "")
            )
            for run in item.text_runs
        )
    return html.escape(item.text or "").replace("\n", "<br>")


def render_html_proof(plan: RenderPlan) -> str:
    validate_render_plan(plan)
    slides: list[str] = []
    for slide in plan.slides:
        objects = "".join(
            (
                f'<div class="object kind-{item.kind}" '
                f'data-window-pptx-id="{html.escape(item.id, quote=True)}" '
                f'data-object-name="{html.escape(item.name, quote=True)}" '
                f'style="{_style(item)}">{_content(item)}</div>'
            )
            for item in sorted(slide.objects, key=lambda value: (value.layer, value.name))
        )
        slides.append(
            f'<section class="slide" data-slide-id="{html.escape(slide.source_id, quote=True)}" '
            f'style="background:{slide.background_color}">{objects}</section>'
        )
    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="generator" content="window-pptx RenderPlan HTML proof">'
        "<style>"
        "*{box-sizing:border-box}html,body{margin:0;background:#222}"
        f".slide{{position:relative;overflow:hidden;width:{plan.slide_size.width}in;"
        f"height:{plan.slide_size.height}in;margin:24px auto;box-shadow:0 8px 28px #0008}}"
        ".object{position:absolute;overflow:hidden;border:1px solid transparent;white-space:pre-wrap}"
        ".object img{width:100%;height:100%;object-fit:cover;display:block}"
        ".object table{width:100%;height:100%;border-collapse:collapse}"
        ".object th,.object td{border:1px solid currentColor;padding:4px}"
        ".proof-chart{display:flex;align-items:center;justify-content:center;width:100%;height:100%}"
        ".kind-diagram{display:flex;gap:8px;align-items:center;justify-content:center}"
        ".proof-node{border:1px solid currentColor;padding:8px}"
        "</style></head><body>"
        + "".join(slides)
        + "</body></html>\n"
    )


def write_html_proof(plan: RenderPlan, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html_proof(plan), encoding="utf-8", newline="\n")
    return output


__all__ = ["render_html_proof", "write_html_proof"]
