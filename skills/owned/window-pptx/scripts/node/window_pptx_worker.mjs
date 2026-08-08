#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";

import JSZip from "jszip";
import PptxGenJS from "pptxgenjs";

const PROTOCOL_VERSION = "1.0";
const BACKEND_ID = "pptxgenjs";
const SUPPORTED_KINDS = new Set(["text", "shape", "image", "table", "chart", "diagram"]);
const SUPPORTED_CHARTS = new Set(["line", "column", "bar", "doughnut", "stacked-column", "scatter"]);
const SUPPORTED_DIAGRAMS = new Set(["process", "timeline", "matrix", "quadrant", "funnel", "roadmap"]);
const ROUND_COMPONENTS = new Set([
  "card", "kpi", "comparison-panel", "risk-panel", "recommendation-panel",
  "team-member", "quote", "process-step", "timeline-node", "matrix-cell",
]);
const EMPHASIS_COMPONENTS = new Set([
  "card", "kpi", "comparison-panel", "risk-panel", "recommendation-panel",
  "team-member", "cta", "process-step", "timeline-node", "matrix-cell",
]);
const REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships";
const OFFICE_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships";

class ProtocolError extends Error {}

function fail(message) {
  throw new ProtocolError(message);
}

function assertObject(value, label) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) fail(`${label} must be an object`);
  return value;
}

function assertOnlyKeys(value, allowed, label) {
  assertObject(value, label);
  const unknown = Object.keys(value).filter((key) => !allowed.has(key));
  if (unknown.length) fail(`${label} contains unknown fields: ${unknown.sort().join(", ")}`);
}

function assertString(value, label, { nullable = false, nonempty = true } = {}) {
  if (nullable && value === null) return;
  if (typeof value !== "string" || (nonempty && !value.trim())) fail(`${label} must be ${nullable ? "null or " : ""}a non-empty string`);
}

function assertArray(value, label) {
  if (!Array.isArray(value)) fail(`${label} must be an array`);
}

function assertFiniteNumber(value, label, { positive = false, nonnegative = false } = {}) {
  if (typeof value !== "number" || !Number.isFinite(value)) fail(`${label} must be finite`);
  if (positive && value <= 0) fail(`${label} must be positive`);
  if (nonnegative && value < 0) fail(`${label} must be non-negative`);
}

function assertColor(value, label) {
  if (typeof value !== "string" || !/^#[0-9A-Fa-f]{6}$/.test(value)) fail(`${label} must use #RRGGBB`);
}

function validateAdvanced(advanced, kind, label) {
  if (!["chart", "table", "diagram"].includes(kind)) {
    if (advanced !== null) fail(`${label} must be null for ${kind}`);
    return;
  }
  assertObject(advanced, label);
  if (advanced.kind !== kind) fail(`${label}.kind must match object kind`);
  if (kind === "chart") {
    assertOnlyKeys(advanced, new Set(["kind", "chart_type", "categories", "series", "value_unit"]), label);
    if (!SUPPORTED_CHARTS.has(advanced.chart_type)) fail(`${label}.chart_type is unsupported`);
    assertArray(advanced.categories, `${label}.categories`);
    advanced.categories.forEach((item, index) => assertString(item, `${label}.categories[${index}]`, { nonempty: false }));
    assertArray(advanced.series, `${label}.series`);
    if (!advanced.series.length) fail(`${label}.series must not be empty`);
    advanced.series.forEach((series, index) => {
      const seriesLabel = `${label}.series[${index}]`;
      assertOnlyKeys(series, new Set(["name", "values", "x_values"]), seriesLabel);
      assertString(series.name, `${seriesLabel}.name`);
      assertArray(series.values, `${seriesLabel}.values`);
      if (series.values.length !== advanced.categories.length) fail(`${seriesLabel}.values length must match categories`);
      series.values.forEach((item, valueIndex) => {
        if (item !== null) assertFiniteNumber(item, `${seriesLabel}.values[${valueIndex}]`);
      });
      if (Object.hasOwn(series, "x_values")) {
        assertArray(series.x_values, `${seriesLabel}.x_values`);
        series.x_values.forEach((item, valueIndex) => assertFiniteNumber(item, `${seriesLabel}.x_values[${valueIndex}]`));
      }
    });
    if (Object.hasOwn(advanced, "value_unit")) assertString(advanced.value_unit, `${label}.value_unit`);
    return;
  }
  if (kind === "table") {
    assertOnlyKeys(advanced, new Set(["kind", "columns", "rows"]), label);
    assertArray(advanced.columns, `${label}.columns`);
    if (!advanced.columns.length) fail(`${label}.columns must not be empty`);
    advanced.columns.forEach((item, index) => assertString(item, `${label}.columns[${index}]`, { nonempty: false }));
    assertArray(advanced.rows, `${label}.rows`);
    advanced.rows.forEach((row, rowIndex) => {
      assertArray(row, `${label}.rows[${rowIndex}]`);
      if (row.length !== advanced.columns.length) fail(`${label}.rows[${rowIndex}] width must match columns`);
      row.forEach((item, columnIndex) => assertString(item, `${label}.rows[${rowIndex}][${columnIndex}]`, { nonempty: false }));
    });
    return;
  }
  assertOnlyKeys(advanced, new Set(["kind", "diagram_type", "nodes"]), label);
  if (!SUPPORTED_DIAGRAMS.has(advanced.diagram_type)) fail(`${label}.diagram_type is unsupported`);
  assertArray(advanced.nodes, `${label}.nodes`);
  if (!advanced.nodes.length) fail(`${label}.nodes must not be empty`);
  advanced.nodes.forEach((node, index) => {
    const nodeLabel = `${label}.nodes[${index}]`;
    assertOnlyKeys(node, new Set(["label", "detail"]), nodeLabel);
    assertString(node.label, `${nodeLabel}.label`);
    if (Object.hasOwn(node, "detail")) assertString(node.detail, `${nodeLabel}.detail`, { nullable: true, nonempty: false });
  });
}

function validateRequest(request) {
  assertOnlyKeys(request, new Set(["protocol_version", "output_path", "render_plan"]), "request");
  if (request.protocol_version !== PROTOCOL_VERSION) fail("unsupported protocol_version");
  assertString(request.output_path, "request.output_path");
  if (path.extname(request.output_path).toLowerCase() !== ".pptx") fail("output_path must end in .pptx");
  const plan = assertObject(request.render_plan, "request.render_plan");
  assertOnlyKeys(plan, new Set([
    "schema_version", "compiler_version", "project_title", "theme_id", "brand", "locale",
    "installed_fonts", "slide_size", "background_color", "slides", "findings", "theme_events",
  ]), "request.render_plan");
  if (plan.schema_version !== "1.0") fail("unsupported render plan schema_version");
  assertString(plan.compiler_version, "render_plan.compiler_version");
  assertString(plan.project_title, "render_plan.project_title");
  assertString(plan.theme_id, "render_plan.theme_id");
  assertOnlyKeys(plan.brand, new Set([
    "primary", "accent", "positive", "warning", "negative", "background", "heading_font", "body_font",
  ]), "render_plan.brand");
  for (const [key, value] of Object.entries(plan.brand)) {
    if (value !== null) {
      if (key.endsWith("font")) assertString(value, `render_plan.brand.${key}`);
      else assertColor(value, `render_plan.brand.${key}`);
    }
  }
  assertString(plan.locale, "render_plan.locale");
  assertArray(plan.installed_fonts, "render_plan.installed_fonts");
  plan.installed_fonts.forEach((font, index) => assertString(font, `render_plan.installed_fonts[${index}]`));
  assertOnlyKeys(plan.slide_size, new Set(["width_in", "height_in"]), "render_plan.slide_size");
  assertFiniteNumber(plan.slide_size.width_in, "render_plan.slide_size.width_in", { positive: true });
  assertFiniteNumber(plan.slide_size.height_in, "render_plan.slide_size.height_in", { positive: true });
  assertColor(plan.background_color, "render_plan.background_color");
  assertArray(plan.findings, "render_plan.findings");
  plan.findings.forEach((finding, index) => {
    assertOnlyKeys(finding, new Set(["code", "path", "message", "severity"]), `render_plan.findings[${index}]`);
  });
  assertArray(plan.theme_events, "render_plan.theme_events");
  plan.theme_events.forEach((event, index) => {
    assertOnlyKeys(event, new Set(["code", "field", "requested", "resolved"]), `render_plan.theme_events[${index}]`);
  });
  assertArray(plan.slides, "render_plan.slides");
  if (!plan.slides.length) fail("render_plan.slides must not be empty");
  const slideIds = new Set();
  const objectNames = new Set();
  plan.slides.forEach((slide, slideOffset) => {
    const slideLabel = `render_plan.slides[${slideOffset}]`;
    assertOnlyKeys(slide, new Set([
      "source_id", "index", "role", "title", "family_id", "layout_id", "item_count",
      "requested_density", "resolved_density", "background_color", "objects", "speaker_notes", "motion",
      "composition_id", "variant_id", "emphasis", "energy", "fact_refs",
      "component_intents", "asset_intents", "motif_id", "motif_variant", "motif_intensity",
      "direction_annotation",
    ]), slideLabel);
    assertString(slide.source_id, `${slideLabel}.source_id`);
    if (slideIds.has(slide.source_id)) fail(`${slideLabel}.source_id is duplicated`);
    slideIds.add(slide.source_id);
    if (slide.index !== slideOffset + 1) fail(`${slideLabel}.index must be sequential`);
    ["role", "family_id", "layout_id", "requested_density", "resolved_density"].forEach((key) => assertString(slide[key], `${slideLabel}.${key}`));
    assertString(slide.title, `${slideLabel}.title`, { nullable: true, nonempty: false });
    assertFiniteNumber(slide.item_count, `${slideLabel}.item_count`, { nonnegative: true });
    assertColor(slide.background_color, `${slideLabel}.background_color`);
    assertString(slide.speaker_notes, `${slideLabel}.speaker_notes`, { nullable: true, nonempty: false });
    ["composition_id", "variant_id", "motif_id", "motif_variant", "motif_intensity"].forEach(
      (key) => assertString(slide[key], `${slideLabel}.${key}`, { nullable: true, nonempty: false }),
    );
    if (slide.direction_annotation !== null) {
      assertArray(slide.direction_annotation, `${slideLabel}.direction_annotation`);
      if (slide.direction_annotation.length !== 2) fail(`${slideLabel}.direction_annotation must contain two labels`);
      slide.direction_annotation.forEach((value, index) => assertString(value, `${slideLabel}.direction_annotation[${index}]`));
    }
    if (!["quiet", "standard", "hero"].includes(slide.emphasis)) fail(`${slideLabel}.emphasis is invalid`);
    if (!["pause", "flow", "peak"].includes(slide.energy)) fail(`${slideLabel}.energy is invalid`);
    ["fact_refs", "component_intents", "asset_intents"].forEach((key) => {
      assertArray(slide[key], `${slideLabel}.${key}`);
      slide[key].forEach((value, index) => assertString(value, `${slideLabel}.${key}[${index}]`));
    });
    if (slide.motion !== "off") fail(`${slideLabel}.motion is unsupported by pptxgenjs`);
    assertArray(slide.objects, `${slideLabel}.objects`);
    slide.objects.forEach((item, objectOffset) => {
      const itemLabel = `${slideLabel}.objects[${objectOffset}]`;
      assertOnlyKeys(item, new Set([
        "id", "name", "component", "kind", "bounds_in", "layer", "group_id", "native_editable",
        "text", "source_path", "asset_record", "font_name", "font_size_pt", "text_color",
        "fill_color", "line_color", "advanced", "semantic_source", "hyperlink", "text_runs",
      ]), itemLabel);
      ["id", "name", "component", "kind", "font_name"].forEach((key) => assertString(item[key], `${itemLabel}.${key}`));
      if (!SUPPORTED_KINDS.has(item.kind)) fail(`${itemLabel}.kind is unsupported`);
      if (objectNames.has(item.name)) fail(`${itemLabel}.name is duplicated`);
      objectNames.add(item.name);
      assertOnlyKeys(item.bounds_in, new Set(["x", "y", "width", "height"]), `${itemLabel}.bounds_in`);
      assertFiniteNumber(item.bounds_in.x, `${itemLabel}.bounds_in.x`, { nonnegative: true });
      assertFiniteNumber(item.bounds_in.y, `${itemLabel}.bounds_in.y`, { nonnegative: true });
      assertFiniteNumber(item.bounds_in.width, `${itemLabel}.bounds_in.width`, { positive: true });
      assertFiniteNumber(item.bounds_in.height, `${itemLabel}.bounds_in.height`, { positive: true });
      assertFiniteNumber(item.layer, `${itemLabel}.layer`, { nonnegative: true });
      assertString(item.group_id, `${itemLabel}.group_id`, { nullable: true, nonempty: false });
      if (item.native_editable !== true) fail(`${itemLabel}.native_editable must be true`);
      assertString(item.text, `${itemLabel}.text`, { nullable: true, nonempty: false });
      if (item.text_runs !== undefined && item.text_runs !== null) {
        assertArray(item.text_runs, `${itemLabel}.text_runs`);
        if (!item.text_runs.length || item.text === null) fail(`${itemLabel}.text_runs requires canonical text`);
        let reconstructed = "";
        item.text_runs.forEach((run, runOffset) => {
          const runLabel = `${itemLabel}.text_runs[${runOffset}]`;
          assertOnlyKeys(run, new Set([
            "text", "font_size_pt", "text_color", "bold", "italic", "break_after",
          ]), runLabel);
          assertString(run.text, `${runLabel}.text`);
          assertFiniteNumber(run.font_size_pt, `${runLabel}.font_size_pt`, { positive: true });
          assertColor(run.text_color, `${runLabel}.text_color`);
          if (typeof run.bold !== "boolean" || typeof run.italic !== "boolean" || typeof run.break_after !== "boolean") {
            fail(`${runLabel} style flags must be boolean`);
          }
          reconstructed += run.text + (run.break_after ? "\n" : "");
        });
        if (item.text_runs.at(-1).break_after || reconstructed !== item.text) {
          fail(`${itemLabel}.text_runs must reconstruct canonical text`);
        }
      }
      assertString(item.source_path, `${itemLabel}.source_path`, { nullable: true, nonempty: false });
      if (item.kind === "image" && item.source_path === null) fail(`${itemLabel}.source_path is required for image`);
      if (item.kind !== "image" && item.source_path !== null) fail(`${itemLabel}.source_path is only valid for image`);
      if (item.asset_record !== null) {
        assertOnlyKeys(item.asset_record, new Set([
          "id", "kind", "style", "aspect_ratio", "quality", "source", "license", "retrieved_at",
          "width_px", "height_px", "icon_family",
        ]), `${itemLabel}.asset_record`);
      }
      assertFiniteNumber(item.font_size_pt, `${itemLabel}.font_size_pt`, { positive: true });
      assertColor(item.text_color, `${itemLabel}.text_color`);
      assertColor(item.fill_color, `${itemLabel}.fill_color`);
      assertColor(item.line_color, `${itemLabel}.line_color`);
      assertString(item.semantic_source, `${itemLabel}.semantic_source`, { nullable: true, nonempty: false });
      assertString(item.hyperlink, `${itemLabel}.hyperlink`, { nullable: true, nonempty: false });
      validateAdvanced(item.advanced, item.kind, `${itemLabel}.advanced`);
    });
  });
  for (const slide of plan.slides) {
    for (const item of slide.objects) {
      if (item.hyperlink?.startsWith("slide:") && !slideIds.has(item.hyperlink.slice(6))) {
        fail(`hyperlink target is unknown: ${item.hyperlink}`);
      }
    }
  }
  return plan;
}

function color(value) {
  return value.slice(1).toUpperCase();
}

function mixHex(base, target, targetRatio) {
  const left = base.replace(/^#/, "");
  const right = target.replace(/^#/, "");
  const channel = (offset) => Math.round(
    Number.parseInt(left.slice(offset, offset + 2), 16) * (1 - targetRatio)
    + Number.parseInt(right.slice(offset, offset + 2), 16) * targetRatio,
  ).toString(16).padStart(2, "0");
  return `${channel(0)}${channel(2)}${channel(4)}`.toUpperCase();
}

function contrastText(hex) {
  const source = hex.replace(/^#/, "");
  const channels = [0, 2, 4].map((offset) => {
    const value = Number.parseInt(source.slice(offset, offset + 2), 16) / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  const luminance = 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
  return luminance > 0.42 ? "111827" : "F8FAFC";
}

function xmlEscape(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function regexEscape(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function sentinel(item, { id = item.id, kind = item.kind, component = item.component, group = item.group_id ?? "" } = {}) {
  return `window-pptx:id=${id};kind=${kind};component=${component};editable=true;group=${group};`;
}

function objectOptions(item) {
  const bounds = item.bounds_in;
  return {
    x: bounds.x,
    y: bounds.y,
    w: bounds.width,
    h: bounds.height,
    objectName: item.name,
    altText: sentinel(item),
  };
}

function textPayload(item) {
  if (!Array.isArray(item.text_runs)) return item.text ?? "";
  return item.text_runs.map((run) => ({
    text: run.text,
    options: {
      fontFace: item.font_name,
      fontSize: run.font_size_pt,
      color: color(run.text_color),
      bold: run.bold,
      italic: run.italic,
      breakLine: run.break_after,
    },
  }));
}

function addText(slide, item, planSlide) {
  const centeredLayout = planSlide.layout_id.endsWith(".centered")
    && !new Set(["big-number.centered", "focal-statement.centered", "cta.centered"]).has(planSlide.layout_id);
  const centered = centeredLayout || item.component === "cta";
  const bodyTopAligned = item.component === "body-text"
    && !centeredLayout
    && planSlide.role !== "cover";
  slide.addText(textPayload(item), {
    ...objectOptions(item),
    fontFace: item.font_name,
    fontSize: item.font_size_pt,
    color: color(item.text_color),
    bold: Array.isArray(item.text_runs) ? false : item.component === "title" || item.component === "cta",
    italic: Array.isArray(item.text_runs) ? false : item.component === "quote",
    align: centered ? "center" : "left",
    margin: item.component === "footer" ? 0 : [4, 6, 4, 6],
    valign: bodyTopAligned ? "top" : "mid",
    breakLine: false,
    fit: "none",
    line: { color: color(item.line_color), transparency: 100 },
    fill: { color: color(item.fill_color), transparency: 100 },
  });
}

function addShape(slide, pptx, item, planSlide) {
  const shape = ROUND_COMPONENTS.has(item.component) ? pptx.ShapeType.roundRect : pptx.ShapeType.rect;
  const decoration = item.component === "decoration";
  const accent = item.component === "accent";
  const artName = item.group_id?.endsWith("_art") ? item.name : "";
  const strongDecoration = decoration
    && /(?:top_rule|bottom_rule|section_rule|closing_rule|wayfinding_path|content_rail|matrix_axis)/.test(artName);
  const strongAccent = accent && Boolean(artName);
  const titleFieldAccent = strongAccent && /title_field/.test(artName);
  const elevated = ROUND_COMPONENTS.has(item.component) && !decoration && !accent;
  const editorialHeroCard = planSlide.layout_id.endsWith(".editorial-three")
    && item.name.endsWith("_one");
  const splitHeroPanel = new Set(["comparison.split"]).has(planSlide.layout_id)
    && item.name.endsWith("_primary");
  const options = {
    ...objectOptions(item),
    fontFace: item.font_name,
    fontSize: item.font_size_pt,
    color: color(item.text_color),
    bold: Array.isArray(item.text_runs) ? false : EMPHASIS_COMPONENTS.has(item.component),
    italic: Array.isArray(item.text_runs) ? false : item.component === "quote",
    margin: decoration || accent ? 0 : editorialHeroCard || splitHeroPanel
      ? [14, 16, 14, 16]
      : [9, 11, 9, 11],
    valign: "mid",
    align: (item.component === "kpi"
        && planSlide.layout_id.endsWith(".centered")
        && planSlide.layout_id !== "big-number.centered")
      || (item.component === "quote" && planSlide.layout_id.endsWith(".centered"))
      || planSlide.role === "agenda"
      ? "center"
      : "left",
    fill: {
      color: color(item.fill_color),
      transparency: strongDecoration
        ? 20
        : strongAccent
        ? titleFieldAccent ? 0 : 15
        : decoration
        ? 88
        : accent
        ? 82
        : 0,
    },
    line: {
      color: color(item.line_color),
      width: decoration ? 0.5 : 0.8,
      transparency: decoration || accent ? 100 : 62,
    },
    shadow: elevated
      ? { type: "outer", color: "000000", opacity: 0.12, blur: 1.5, angle: 45, offset: 1 }
      : undefined,
    radius: 0.08,
    shape,
  };
  if (item.text !== null) slide.addText(textPayload(item), options);
  else slide.addShape(shape, options);
}

function resolvedPrimary(plan) {
  for (const slide of plan.slides) {
    for (const item of slide.objects) {
      if (item.line_color) return color(item.line_color);
    }
  }
  return "245B8F";
}

function masterObjects(role, plan, primary) {
  const width = plan.slide_size.width_in;
  const height = plan.slide_size.height_in;
  const invisibleLine = { color: primary, transparency: 100 };
  const rail = {
    rect: {
      x: 0,
      y: 0,
      w: role === "cover" || role === "closing" ? 0.14 : 0.07,
      h: height,
      fill: { color: primary },
      line: invisibleLine,
    },
  };
  if (role === "cover") {
    return [
      rail,
      {
        rect: {
          x: width - 1.35,
          y: 0,
          w: 1.35,
          h: 0.08,
          fill: { color: primary },
          line: invisibleLine,
        },
      },
      {
        rect: {
          x: width - 0.60,
          y: height - 1.72,
          w: 0.60,
          h: 0.10,
          fill: { color: primary, transparency: 76 },
          line: invisibleLine,
        },
      },
      {
        rect: {
          x: width - 1.00,
          y: height - 1.37,
          w: 1.00,
          h: 0.10,
          fill: { color: primary, transparency: 84 },
          line: invisibleLine,
        },
      },
      {
        rect: {
          x: width - 1.40,
          y: height - 1.02,
          w: 1.40,
          h: 0.10,
          fill: { color: primary, transparency: 91 },
          line: invisibleLine,
        },
      },
    ];
  }
  if (role === "agenda" || role === "section") {
    return [
      rail,
      {
        rect: {
          x: 0,
          y: 0,
          w: width,
          h: 1.28,
          fill: { color: primary, transparency: 94 },
          line: invisibleLine,
        },
      },
      {
        rect: {
          x: width - 1.05,
          y: 0,
          w: 1.05,
          h: 0.08,
          fill: { color: primary },
          line: invisibleLine,
        },
      },
    ];
  }
  if (role === "closing") {
    return [
      rail,
      {
        rect: {
          x: 0,
          y: height - 1.12,
          w: width,
          h: 1.12,
          fill: { color: primary, transparency: 93 },
          line: invisibleLine,
        },
      },
      {
        rect: {
          x: width - 1.35,
          y: 0,
          w: 1.35,
          h: 0.08,
          fill: { color: primary },
          line: invisibleLine,
        },
      },
    ];
  }
  return [
    rail,
    {
      rect: {
        x: width - 1.05,
        y: 0,
        w: 1.05,
        h: 0.08,
        fill: { color: primary },
        line: invisibleLine,
      },
    },
  ];
}

function masterRole(planSlide) {
  if (["cover", "agenda", "section", "closing"].includes(planSlide.role)) return planSlide.role;
  return "content";
}

function addImage(slide, item) {
  const options = objectOptions(item);
  slide.addImage({
    ...options,
    path: item.source_path,
    sizing: { type: "cover", x: options.x, y: options.y, w: options.w, h: options.h },
  });
}

function tableRows(item) {
  const spec = item.advanced;
  const primary = color(item.line_color);
  const surface = color(item.fill_color);
  const alternate = mixHex(surface, primary, 0.055);
  const header = spec.columns.map((text) => ({
    text,
    options: {
      bold: true,
      color: contrastText(primary),
      fill: primary,
      fontFace: item.font_name,
      fontSize: item.font_size_pt,
      valign: "mid",
      align: "left",
    },
  }));
  const body = spec.rows.map((row, rowIndex) => row.map((text) => ({
    text,
    options: {
      color: color(item.text_color),
      fill: rowIndex % 2 === 0 ? surface : alternate,
      fontFace: item.font_name,
      fontSize: Math.max(8, item.font_size_pt - 1),
      valign: "mid",
      align: /^\s*[-+]?(?:[$€£¥]\s*)?\d[\d,.]*(?:\s*%|\s*[A-Za-z]{0,5})?\s*$/.test(text)
        ? "right"
        : "left",
    },
  })));
  return [header, ...body];
}

function addTable(slide, item) {
  const options = objectOptions(item);
  const borderColor = mixHex(color(item.line_color), color(item.fill_color), 0.72);
  slide.addTable(tableRows(item), {
    ...options,
    border: { type: "solid", color: borderColor, pt: 0.6 },
    margin: [3, 5, 3, 5],
    autoPage: false,
    rowH: options.h / (item.advanced.rows.length + 1),
    colW: Array(item.advanced.columns.length).fill(options.w / item.advanced.columns.length),
  });
}

function addChart(slide, pptx, item) {
  const spec = item.advanced;
  const primary = color(item.line_color);
  const surface = color(item.fill_color);
  const gridColor = mixHex(primary, surface, 0.84);
  const data = spec.chart_type === "scatter"
    ? [
      {
        name: "X Axis",
        values: spec.series[0].x_values?.length
          ? spec.series[0].x_values
          : spec.categories.map((value, index) => Number.isFinite(Number(value)) ? Number(value) : index + 1),
      },
      ...spec.series.map((series) => ({
        name: series.name,
        labels: spec.categories,
        values: series.values,
      })),
    ]
    : spec.series.map((series) => ({
      name: series.name,
      labels: spec.categories,
      values: series.values,
    }));
  let chartType = pptx.ChartType.line;
  const options = {
    ...objectOptions(item),
    chartColors: [
      primary,
      mixHex(primary, "FFFFFF", 0.34),
      mixHex(primary, "000000", 0.18),
      mixHex(primary, "FFFFFF", 0.58),
      mixHex(primary, "000000", 0.34),
    ],
    showTitle: false,
    showLegend: data.length > 1 || spec.chart_type === "doughnut",
    legendPos: "b",
    legendColor: color(item.text_color),
    legendFontFace: item.font_name,
    legendFontSize: Math.max(8, item.font_size_pt - 3),
    showValue: spec.chart_type !== "scatter" && spec.categories.length <= 6,
    showCatName: spec.chart_type === "doughnut",
    showPercent: spec.chart_type === "doughnut",
    fontFace: item.font_name,
    fontSize: Math.max(8, item.font_size_pt - 2),
    catAxisLabelFontFace: item.font_name,
    catAxisLabelFontSize: Math.max(8, item.font_size_pt - 2),
    valAxisLabelFontFace: item.font_name,
    valAxisLabelFontSize: Math.max(8, item.font_size_pt - 2),
    catAxisLineShow: false,
    valAxisLineShow: false,
    valGridLine: { color: gridColor, size: 0.5, style: "solid" },
    dataLabelColor: color(item.text_color),
    dataLabelFontBold: true,
    dataLabelFontFace: item.font_name,
    dataLabelFontSize: Math.max(8, item.font_size_pt - 3),
    showLeaderLines: spec.chart_type === "doughnut",
    showBorder: false,
    chartArea: { border: { type: "none" }, fill: { color: surface, transparency: 100 } },
    plotArea: { border: { type: "none" }, fill: { color: surface, transparency: 100 } },
  };
  if (spec.chart_type === "column" || spec.chart_type === "bar" || spec.chart_type === "stacked-column") {
    chartType = pptx.ChartType.bar;
    options.barDir = spec.chart_type === "bar" ? "bar" : "col";
    options.barGrouping = spec.chart_type === "stacked-column" ? "stacked" : "clustered";
    options.dataLabelPosition = spec.chart_type === "bar" ? "outEnd" : "outEnd";
  } else if (spec.chart_type === "doughnut") {
    chartType = pptx.ChartType.doughnut;
    options.holeSize = 55;
  } else if (spec.chart_type === "scatter") {
    chartType = pptx.ChartType.scatter;
    options.lineSize = 1.5;
    options.lineDataSymbol = "circle";
  }
  if (/^(?:%|percent|percentage)$/i.test(spec.value_unit ?? "")) {
    options.valAxisMinVal = 0;
    options.valAxisMaxVal = 100;
    options.valAxisMajorUnit = 20;
    options.valAxisLabelFormatCode = '0"%"';
    options.dataLabelFormatCode = '0"%"';
    options.showValAxisTitle = true;
    options.valAxisTitle = "Percent";
    options.valAxisTitleColor = color(item.text_color);
    options.valAxisTitleFontFace = item.font_name;
    options.valAxisTitleFontSize = Math.max(8, item.font_size_pt - 3);
  }
  slide.addChart(chartType, data, options);
}

function diagramGeometry(item, nodeCount, index) {
  const { x, y, width: w, height: h } = item.bounds_in;
  const type = item.advanced.diagram_type;
  const gap = 0.12;
  if (type === "matrix" || type === "quadrant") {
    const columns = 2;
    const rows = Math.ceil(nodeCount / columns);
    const cellW = (w - gap) / columns;
    const cellH = (h - gap * (rows - 1)) / rows;
    return { x: x + (index % columns) * (cellW + gap), y: y + Math.floor(index / columns) * (cellH + gap), w: cellW, h: cellH };
  }
  if (type === "funnel") {
    const cellH = (h - gap * (nodeCount - 1)) / nodeCount;
    const ratio = 1 - (index / Math.max(1, nodeCount)) * 0.35;
    const cellW = w * ratio;
    return { x: x + (w - cellW) / 2, y: y + index * (cellH + gap), w: cellW, h: cellH };
  }
  if (type === "timeline") {
    if (nodeCount === 1) {
      const cellW = w * 0.62;
      const cellH = h * 0.45;
      return { x: x + (w - cellW) / 2, y: y + (h - cellH) / 2, w: cellW, h: cellH };
    }
    const cellW = (w - gap * (nodeCount - 1)) / nodeCount;
    const cellH = h * 0.55;
    return {
      x: x + index * (cellW + gap),
      y: y + (h - cellH) / 2,
      w: cellW,
      h: cellH,
    };
  }
  if (type === "roadmap") {
    if (nodeCount === 1) {
      const cellW = w * 0.62;
      const cellH = h * 0.45;
      return { x: x + (w - cellW) / 2, y: y + (h - cellH) / 2, w: cellW, h: cellH };
    }
    const cellW = (w - gap * (nodeCount - 1)) / nodeCount;
    const cellH = h * 0.58;
    return { x: x + index * (cellW + gap), y: y + (index % 2 === 0 ? 0 : h - cellH), w: cellW, h: cellH };
  }
  const cellW = (w - gap * (nodeCount - 1)) / nodeCount;
  if (type === "process") {
    const cellH = h * 0.58;
    return {
      x: x + index * (cellW + gap),
      y: y + (h - cellH) / 2,
      w: cellW,
      h: cellH,
    };
  }
  return { x: x + index * (cellW + gap), y, w: cellW, h };
}

function addDiagram(slide, pptx, item) {
  const frame = objectOptions(item);
  slide.addShape(pptx.ShapeType.rect, {
    ...frame,
    fill: { color: color(item.fill_color), transparency: 100 },
    line: { color: color(item.line_color), transparency: 100 },
  });
  const nodes = item.advanced.nodes;
  nodes.forEach((node, index) => {
    const bounds = diagramGeometry(item, nodes.length, index);
    const singleMilestone = nodes.length === 1
      && new Set(["timeline", "roadmap"]).has(item.advanced.diagram_type);
    const childName = `${item.name}__node_${String(index + 1).padStart(2, "0")}`;
    const childId = `${item.id}.node.${index + 1}`;
    const childSentinel = sentinel(item, {
      id: childId,
      kind: "shape",
      component: "diagram-node",
      group: item.group_id ?? item.id,
    });
    const text = node.detail ? `${node.label}\n${node.detail}` : node.label;
    const highlightFirstMatrixNode = index === 0
      && new Set(["matrix", "quadrant"]).has(item.advanced.diagram_type);
    const nodeFill = highlightFirstMatrixNode
      ? color(item.line_color)
      : color(item.fill_color);
    const nodeText = highlightFirstMatrixNode
      ? contrastText(item.line_color)
      : color(item.text_color);
    slide.addText(text, {
      ...bounds,
      objectName: childName,
      altText: childSentinel,
      shape: singleMilestone ? pptx.ShapeType.rect : pptx.ShapeType.roundRect,
      fontFace: item.font_name,
      fontSize: item.advanced.diagram_type === "timeline"
        ? Math.max(18, item.font_size_pt)
        : Math.max(9, item.font_size_pt - 1),
      color: nodeText,
      bold: true,
      align: singleMilestone ? "left" : "center",
      valign: "mid",
      margin: singleMilestone ? [8, 12, 8, 12] : 4,
      fill: { color: nodeFill },
      line: {
        color: color(item.line_color),
        width: new Set(["matrix", "quadrant"]).has(item.advanced.diagram_type)
          ? 1.5
          : 1,
      },
    });
  });
  return nodes.length;
}

function patchCnvPr(xml, objectName, description, hyperlink) {
  const encodedName = xmlEscape(objectName);
  const pattern = new RegExp(`<p:cNvPr\\b[^>]*\\bname="${regexEscape(encodedName)}"[^>]*(?:\\/>|>)`);
  const match = xml.match(pattern);
  if (!match) fail(`generated package is missing object ${objectName}`);
  let opening = match[0];
  const encodedDescription = xmlEscape(description);
  if (/\sdescr="[^"]*"/.test(opening)) opening = opening.replace(/\sdescr="[^"]*"/, ` descr="${encodedDescription}"`);
  else opening = opening.replace(/\s*\/?>$/, (ending) => ` descr="${encodedDescription}"${ending}`);
  if (!hyperlink) return xml.replace(pattern, opening);
  const click = `<a:hlinkClick r:id="${hyperlink.relId}"${hyperlink.internal ? ' action="ppaction://hlinksldjump"' : ""}/>`;
  if (opening.endsWith("/>")) {
    opening = `${opening.slice(0, -2)}>${click}</p:cNvPr>`;
    return xml.replace(pattern, opening);
  }
  const start = match.index + match[0].length;
  return `${xml.slice(0, match.index)}${opening}${click}${xml.slice(start)}`;
}

function nextRelationshipId(relsXml) {
  let maximum = 0;
  for (const match of relsXml.matchAll(/\bId="rId(\d+)"/g)) maximum = Math.max(maximum, Number(match[1]));
  return `rId${maximum + 1}`;
}

function addRelationship(relsXml, relation) {
  const targetMode = relation.external ? ' TargetMode="External"' : "";
  const entry = `<Relationship Id="${relation.relId}" Type="${OFFICE_REL_NS}/${relation.type}" Target="${xmlEscape(relation.target)}"${targetMode}/>`;
  if (!relsXml.includes("</Relationships>")) fail("generated slide relationships are malformed");
  return relsXml.replace("</Relationships>", `${entry}</Relationships>`);
}

async function patchPackage(buffer, plan) {
  const zip = await JSZip.loadAsync(buffer);
  const contentTypes = zip.file("[Content_Types].xml");
  if (!contentTypes) fail("generated package is missing [Content_Types].xml");
  let contentTypesXml = await contentTypes.async("string");
  if (!contentTypesXml.includes('PartName="/_rels/.rels"')) {
    contentTypesXml = contentTypesXml.replace(
      "</Types>",
      '<Override PartName="/_rels/.rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/></Types>',
    );
    zip.file("[Content_Types].xml", contentTypesXml);
  }
  for (let slideIndex = 0; slideIndex < plan.slides.length; slideIndex += 1) {
    const slide = plan.slides[slideIndex];
    const slidePart = `ppt/slides/slide${slideIndex + 1}.xml`;
    const relsPart = `ppt/slides/_rels/slide${slideIndex + 1}.xml.rels`;
    const slideFile = zip.file(slidePart);
    if (!slideFile) fail(`generated package is missing ${slidePart}`);
    let slideXml = await slideFile.async("string");
    let relsXml;
    const relsFile = zip.file(relsPart);
    if (relsFile) relsXml = await relsFile.async("string");
    else relsXml = `<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="${REL_NS}"></Relationships>`;
    for (const item of slide.objects) {
      let hyperlink = null;
      if (item.hyperlink) {
        const relId = nextRelationshipId(relsXml);
        if (item.hyperlink.startsWith("slide:")) {
          const targetIndex = plan.slides.findIndex((candidate) => candidate.source_id === item.hyperlink.slice(6));
          hyperlink = { relId, internal: true };
          relsXml = addRelationship(relsXml, { relId, type: "slide", target: `../slides/slide${targetIndex + 1}.xml`, external: false });
        } else {
          hyperlink = { relId, internal: false };
          relsXml = addRelationship(relsXml, { relId, type: "hyperlink", target: item.hyperlink, external: true });
        }
      }
      slideXml = patchCnvPr(slideXml, item.name, sentinel(item), hyperlink);
      if (item.kind === "diagram") {
        item.advanced.nodes.forEach((_, index) => {
          const childName = `${item.name}__node_${String(index + 1).padStart(2, "0")}`;
          const childDescription = sentinel(item, {
            id: `${item.id}.node.${index + 1}`,
            kind: "shape",
            component: "diagram-node",
            group: item.group_id ?? item.id,
          });
          slideXml = patchCnvPr(slideXml, childName, childDescription, null);
        });
      }
    }
    zip.file(slidePart, slideXml);
    zip.file(relsPart, relsXml);
  }
  const chartItems = plan.slides.flatMap((slide) => [...slide.objects]
    .sort((left, right) => left.layer - right.layer || left.name.localeCompare(right.name))
    .filter((item) => item.kind === "chart"));
  for (let chartIndex = 0; chartIndex < chartItems.length; chartIndex += 1) {
    const chartPart = `ppt/charts/chart${chartIndex + 1}.xml`;
    const chartFile = zip.file(chartPart);
    if (!chartFile) fail(`generated package is missing ${chartPart}`);
    const chartXml = (await chartFile.async("string")).replace(
      /<c:numCache>[\s\S]*?<\/c:numCache>/g,
      (cache) => cache.replace(/<c:v>(-?\d+)<\/c:v>/g, '<c:v>$1.0</c:v>'),
    );
    zip.file(chartPart, chartXml);
  }
  const fixedDate = new Date(Date.UTC(1980, 0, 1, 0, 0, 0));
  const embeddingNames = Object.keys(zip.files)
    .filter((name) => /^ppt\/embeddings\/[^/]+\.xlsx$/i.test(name))
    .sort();
  for (const embeddingName of embeddingNames) {
    const embedded = await JSZip.loadAsync(await zip.file(embeddingName).async("nodebuffer"));
    const core = embedded.file("docProps/core.xml");
    if (core) {
      const normalizedCore = (await core.async("string")).replace(
        /<dcterms:(created|modified)\b([^>]*)>[^<]*<\/dcterms:\1>/g,
        '<dcterms:$1$2>2000-01-01T00:00:00Z</dcterms:$1>',
      );
      embedded.file("docProps/core.xml", normalizedCore);
    }
    for (const entry of Object.values(embedded.files)) entry.date = fixedDate;
    zip.file(embeddingName, await embedded.generateAsync({
      type: "nodebuffer",
      compression: "DEFLATE",
      compressionOptions: { level: 6 },
    }));
  }
  for (const entry of Object.values(zip.files)) entry.date = fixedDate;
  return zip.generateAsync({ type: "nodebuffer", compression: "DEFLATE", compressionOptions: { level: 6 } });
}

async function render(request) {
  const plan = validateRequest(request);
  const outputPath = path.resolve(request.output_path);
  const pptx = new PptxGenJS();
  const layoutName = "WINDOW_PPTX_CUSTOM";
  pptx.defineLayout({ name: layoutName, width: plan.slide_size.width_in, height: plan.slide_size.height_in });
  pptx.layout = layoutName;
  pptx.author = "window-pptx";
  pptx.company = "window-pptx";
  pptx.subject = "Governed editable PPTX";
  pptx.title = plan.project_title;
  pptx.lang = plan.locale;
  pptx.theme = {
    headFontFace: plan.brand.heading_font ?? plan.installed_fonts[0] ?? "Arial",
    bodyFontFace: plan.brand.body_font ?? plan.installed_fonts[0] ?? "Arial",
    lang: plan.locale,
  };
  const primary = resolvedPrimary(plan);
  const masterNames = new Map();
  for (const role of ["cover", "agenda", "section", "content", "closing"]) {
    const masterName = `WINDOW_PPTX_MASTER_${role.toUpperCase()}`;
    masterNames.set(role, masterName);
    pptx.defineSlideMaster({
      title: masterName,
      background: { color: color(plan.background_color) },
      objects: masterObjects(role, plan, primary),
    });
  }
  const objectNames = plan.slides.flatMap((slide) => slide.objects.map((item) => item.name));
  const groupNames = new Set();
  let diagramChildCount = 0;
  for (const planSlide of plan.slides) {
    const masterName = masterNames.get(masterRole(planSlide));
    const slide = pptx.addSlide({ masterName });
    slide.background = { color: color(planSlide.background_color) };
    const objects = [...planSlide.objects].sort((left, right) => left.layer - right.layer || left.name.localeCompare(right.name));
    for (const item of objects) {
      if (item.group_id) groupNames.add(item.group_id);
      if (item.kind === "text") addText(slide, item, planSlide);
      else if (item.kind === "shape") addShape(slide, pptx, item, planSlide);
      else if (item.kind === "image") addImage(slide, item);
      else if (item.kind === "table") addTable(slide, item);
      else if (item.kind === "chart") addChart(slide, pptx, item);
      else if (item.kind === "diagram") diagramChildCount += addDiagram(slide, pptx, item);
    }
    if (planSlide.speaker_notes) slide.addNotes(planSlide.speaker_notes);
  }
  const raw = await pptx.write({ outputType: "nodebuffer", compression: true });
  const patched = await patchPackage(raw, plan);
  await fs.mkdir(path.dirname(outputPath), { recursive: true });
  await fs.writeFile(outputPath, patched, { flag: "wx" });
  return {
    protocol_version: PROTOCOL_VERSION,
    ok: true,
    backend_id: BACKEND_ID,
    backend_version: String(pptx.version ?? "4.0.1"),
    output_path: outputPath,
    slide_count: plan.slides.length,
    planned_object_count: objectNames.length,
    native_editable_count: objectNames.length + diagramChildCount,
    diagram_child_count: diagramChildCount,
    object_names: objectNames,
    group_names: [...groupNames].sort(),
    warnings: [],
  };
}

async function readRequest(argv) {
  if (argv.length === 0) {
    const chunks = [];
    for await (const chunk of process.stdin) chunks.push(chunk);
    return JSON.parse(Buffer.concat(chunks).toString("utf8"));
  }
  if (argv.length === 2 && ["--request", "--request-file"].includes(argv[0])) {
    return JSON.parse(await fs.readFile(argv[1], "utf8"));
  }
  fail("usage: window_pptx_worker.mjs [--doctor | --request FILE]");
}

async function main() {
  if (process.argv.length === 3 && process.argv[2] === "--doctor") {
    const pptx = new PptxGenJS();
    process.stdout.write(`${JSON.stringify({ protocol_version: PROTOCOL_VERSION, ok: true, backend_id: BACKEND_ID, backend_version: String(pptx.version ?? "4.0.1"), node_version: process.version })}\n`);
    return;
  }
  const request = await readRequest(process.argv.slice(2));
  const report = await render(request);
  process.stdout.write(`${JSON.stringify(report)}\n`);
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : String(error);
  process.stderr.write(`${JSON.stringify({ protocol_version: PROTOCOL_VERSION, ok: false, error: message })}\n`);
  process.exitCode = 1;
});
