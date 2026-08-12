#!/usr/bin/env node
/**
 * Build the three v6 flagship PPTX files as native editable compositions.
 *
 * The script consumes only locked ProjectBriefPack facts. It deliberately
 * owns geometry and art direction so a model never emits coordinates.
 */

import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { createRequire } from "node:module";

const require = createRequire(new URL("./node/package.json", import.meta.url));
const pptxgen = require("pptxgenjs");
const enumSource = new pptxgen();
const SHAPE = enumSource.ShapeType;
const CHART = enumSource.ChartType;

const W = 13.333;
const H = 7.5;
const FONT = "Microsoft YaHei";
const MONO = "Aptos";
const argv = process.argv.slice(2);
const arg = (name, fallback = null) => {
  const index = argv.indexOf(name);
  return index >= 0 ? argv[index + 1] : fallback;
};
const briefDir = arg("--brief-dir");
const outputDir = arg("--output-dir");
if (!briefDir || !outputDir) {
  throw new Error("usage: build_window_pptx_v6_flagships.mjs --brief-dir DIR --output-dir DIR");
}
fs.mkdirSync(outputDir, { recursive: true });

const themes = {
  work: {
    bg: "F4EFE3", ink: "173C31", muted: "65736C", accent: "B69558",
    surface: "FFFDF8", pale: "E6DDC8", good: "39755E", bad: "A65145",
    title: "年度工作总结", subtitle: "以客户价值为锚 · 用可验证成果回答增长",
    mark: "ANNUAL REVIEW / 2026",
  },
  campus: {
    bg: "071A2F", ink: "F2FAF9", muted: "A8C7C5", accent: "00B7A8",
    surface: "102C43", pale: "183D54", good: "50D2C2", bad: "FF876D",
    title: "澄域 · 校园水环境预警系统", subtitle: "从单校真实试点，走向可复制的校园安全基础设施",
    mark: "CAMPUS INNOVATION / FINAL",
  },
  academic: {
    bg: "F3F0E7", ink: "183B56", muted: "657780", accent: "D46A4C",
    surface: "FFFDF8", pale: "DFE6E4", good: "3A7467", bad: "B95C4A",
    chartColors: ["D46A4C", "183B56", "748C96", "B78B65"],
    title: "面向交通流预测的多尺度动态图 Transformer", subtitle: "硕士学位论文答辩 · 证据、边界与可复现性",
    mark: "THESIS DEFENSE / 2026",
  },
};

function readBrief(name) {
  const file = path.join(briefDir, `${name}.project-brief-pack.v1.json`);
  const value = JSON.parse(fs.readFileSync(file, "utf8"));
  if (value.state !== "Locked" && value.status !== "Locked") {
    throw new Error(`${name} is not Locked`);
  }
  const facts = Object.fromEntries(value.fact_store.facts.map((fact) => [fact.id, fact]));
  return { ...value, facts, sourcePath: file };
}

const val = (brief, id) => {
  const fact = brief.facts[id];
  if (!fact) throw new Error(`missing fact ${id}`);
  return fact.value;
};
const factText = (brief, id) => {
  const fact = brief.facts[id];
  if (!fact) throw new Error(`missing fact ${id}`);
  return fact.text;
};
const sha256 = (file) => crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");

function newDeck(theme) {
  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Window-PPTX v6";
  pptx.subject = "Reference-grade native-editable flagship";
  pptx.company = "AImagician";
  pptx.lang = "zh-CN";
  pptx.theme = {
    headFontFace: FONT,
    bodyFontFace: FONT,
    lang: "zh-CN",
  };
  pptx.defineSlideMaster({
    title: "V6_BODY",
    background: { color: theme.bg },
    objects: [
      { line: { x: 0.48, y: 0.28, w: 12.35, h: 0, line: { color: theme.accent, width: 1.2, transparency: 20 } } },
      { text: { text: theme.mark, options: { x: 0.52, y: 0.11, w: 4.6, h: 0.2, fontFace: MONO, fontSize: 5.8, charSpacing: 2.2, color: theme.muted, margin: 0, breakLine: false } } },
      { text: { text: "WINDOW-PPTX · NATIVE EDITABLE", options: { x: 8.7, y: 7.15, w: 4.1, h: 0.18, fontFace: MONO, fontSize: 5.4, charSpacing: 1.4, align: "right", color: theme.muted, margin: 0 } } },
    ],
    slideNumber: { x: 0.52, y: 7.10, w: 0.4, h: 0.22, color: theme.muted, fontFace: MONO, fontSize: 7 },
  });
  return pptx;
}

function addText(slide, text, x, y, w, h, size, color, options = {}) {
  slide.addText(String(text), {
    x, y, w, h, fontFace: options.fontFace || FONT, fontSize: size,
    color, margin: options.margin ?? 0, bold: options.bold ?? false,
    breakLine: false, valign: options.valign || "mid", align: options.align || "left",
    fit: "shrink", paraSpaceAfterPt: options.paraSpaceAfterPt || 0,
    charSpacing: options.charSpacing || 0, isTextBox: true,
  });
}

function addTitle(slide, theme, kicker, title, deckIndex) {
  addText(slide, kicker.toUpperCase(), 0.55, 0.52, 3.5, 0.24, 7, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2 });
  addText(slide, title, 0.55, 0.82, 11.5, 0.64, 25, theme.ink, { bold: true });
  addText(slide, String(deckIndex).padStart(2, "0"), 11.95, 0.63, 0.82, 0.58, 18, theme.accent, { fontFace: MONO, bold: true, align: "right" });
}

function addNotes(slide, factIds = [], note = "") {
  slide.addNotes([
    `FACT_IDS: ${factIds.join(", ") || "NONE"}`,
    note,
    "All values are sourced from the locked ProjectBriefPack. Objects are native-editable.",
  ].filter(Boolean).join("\n"));
}

function addMotif(slide, theme, kind = "radial", intensity = 1) {
  const line = { color: theme.accent, width: 0.8, transparency: 46 };
  if (kind === "radial") {
    for (let i = 0; i < 13; i += 1) {
      const angle = (-70 + i * 7) * Math.PI / 180;
      const x0 = 11.45, y0 = 6.55, r = 4.2 + (i % 3) * 0.25;
      slide.addShape(SHAPE.line, { x: x0, y: y0, w: Math.cos(angle) * r, h: Math.sin(angle) * r, line });
    }
    for (let i = 0; i < 3; i += 1) {
      slide.addShape(SHAPE.arc, {
        x: 9.6 - i * 0.28, y: 4.72 - i * 0.28, w: 3.6 + i * 0.56, h: 3.6 + i * 0.56,
        adjustPoint: 0.25, rotate: 6, line,
      });
    }
  } else if (kind === "signal") {
    for (let i = 0; i < 4; i += 1) {
      slide.addShape(SHAPE.arc, {
        x: 9.4 - i * 0.35, y: 0.8 - i * 0.35, w: 2.5 + i * 0.7, h: 2.5 + i * 0.7,
        rotate: 180, adjustPoint: 0.3, line: { ...line, transparency: 35 + i * 8 },
      });
    }
  } else {
    for (let i = 0; i < 9; i += 1) {
      slide.addShape(SHAPE.line, {
        x: 7.9 + i * 0.55, y: 0.65, w: 0, h: 5.9,
        line: { ...line, transparency: 75 },
      });
    }
    for (let i = 0; i < 7; i += 1) {
      slide.addShape(SHAPE.line, {
        x: 7.9, y: 0.65 + i * 0.78, w: 4.4, h: 0,
        line: { ...line, transparency: 75 },
      });
    }
  }
  if (intensity > 1) {
    slide.addShape(SHAPE.ellipse, {
      x: 10.9, y: 5.65, w: 0.52, h: 0.52,
      fill: { color: theme.accent, transparency: 12 }, line: { color: theme.accent, transparency: 100 },
    });
  }
}

function cover(pptx, theme, index, eyebrow, title, subtitle, meta, motif = "radial") {
  const slide = pptx.addSlide();
  slide.background = { color: theme.bg };
  addMotif(slide, theme, motif, 2);
  slide.addShape(SHAPE.line, { x: 0.65, y: 0.7, w: 0, h: 5.95, line: { color: theme.accent, width: 2 } });
  addText(slide, eyebrow, 0.95, 0.78, 4.5, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.4 });
  addText(slide, title, 0.95, 1.35, 8.45, 1.75, 50, theme.ink, { bold: true });
  addText(slide, subtitle, 0.98, 3.48, 6.9, 0.58, 14, theme.muted);
  addText(slide, meta, 0.98, 5.75, 5.8, 0.36, 10, theme.ink, { fontFace: MONO });
  addText(slide, String(index).padStart(2, "0"), 11.55, 6.55, 1.1, 0.5, 17, theme.accent, { fontFace: MONO, bold: true, align: "right" });
  addNotes(slide);
  return slide;
}

function agenda(pptx, theme, items, factIds = []) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Contents / Narrative Map", "目录不是清单，而是决策路径", 2);
  items.forEach((item, i) => {
    const y = 1.85 + i * 1.12;
    addText(slide, `0${i + 1}`, 0.75, y, 0.62, 0.35, 12, theme.accent, { fontFace: MONO, bold: true });
    slide.addShape(SHAPE.line, { x: 1.45, y: y + 0.18, w: 1.05, h: 0, line: { color: theme.pale, width: 1 } });
    addText(slide, item[0], 2.75, y - 0.05, 3.0, 0.46, 17, theme.ink, { bold: true });
    addText(slide, item[1], 6.05, y - 0.02, 5.35, 0.42, 11, theme.muted);
  });
  addMotif(slide, theme, "radial");
  addNotes(slide, factIds);
}

function section(pptx, theme, n, title, statement, motif = "radial") {
  const slide = pptx.addSlide();
  slide.background = { color: theme.ink };
  addMotif(slide, { ...theme, accent: theme.accent, ink: theme.bg }, motif, 2);
  addText(slide, `SECTION 0${n}`, 0.75, 0.75, 2.4, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.5 });
  addText(slide, title, 0.75, 1.55, 7.8, 1.15, 36, theme.bg, { bold: true });
  slide.addShape(SHAPE.line, { x: 0.78, y: 3.05, w: 1.4, h: 0, line: { color: theme.accent, width: 3 } });
  addText(slide, statement, 0.78, 3.35, 6.7, 1.15, 16, theme.pale);
  addText(slide, String(n).padStart(2, "0"), 11.35, 5.8, 1.1, 0.85, 30, theme.accent, { fontFace: MONO, bold: true, align: "right" });
  addNotes(slide);
}

function sectionAligned(pptx, theme, n, title, statement, motif = "radial") {
  const slide = pptx.addSlide();
  slide.background = { color: theme.bg };
  addMotif(slide, theme, motif, 2);
  slide.addShape(SHAPE.rect, {
    x: 0, y: 0, w: 0.22, h: H,
    fill: { color: theme.accent }, line: { color: theme.accent },
  });
  addText(slide, `SECTION 0${n}`, 0.85, 0.82, 2.8, 0.3, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.4 });
  addText(slide, title, 0.85, 1.72, 8.6, 0.95, 37, theme.ink, { bold: true });
  slide.addShape(SHAPE.line, { x: 0.88, y: 3.08, w: 1.65, h: 0, line: { color: theme.accent, width: 3 } });
  addText(slide, statement, 0.88, 3.42, 7.2, 1.2, 16, theme.muted);
  addText(slide, String(n).padStart(2, "0"), 10.35, 4.95, 1.95, 1.25, 50, theme.accent, { fontFace: MONO, bold: true, align: "right" });
  addNotes(slide);
}

function metricCards(pptx, theme, index, kicker, title, metrics, note, factIds = []) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, kicker, title, index);
  const count = metrics.length;
  const gap = 0.22;
  const width = (12.0 - gap * (count - 1)) / count;
  metrics.forEach((metric, i) => {
    const x = 0.65 + i * (width + gap);
    slide.addShape(SHAPE.roundRect, {
      x, y: 1.85, w: width, h: 3.75,
      rectRadius: 0.06, fill: { color: i === 0 ? theme.ink : theme.surface },
      line: { color: i === 0 ? theme.ink : theme.pale, width: 1 },
    });
    addText(slide, metric.label, x + 0.25, 2.14, width - 0.5, 0.35, 9, i === 0 ? theme.pale : theme.muted, { fontFace: MONO, bold: true });
    addText(slide, metric.value, x + 0.25, 2.72, width - 0.5, 0.82, 27, i === 0 ? theme.bg : theme.ink, { bold: true });
    addText(slide, metric.unit || "", x + 0.26, 3.52, width - 0.5, 0.26, 8, theme.accent, { fontFace: MONO, bold: true });
    slide.addShape(SHAPE.line, { x: x + 0.25, y: 4.05, w: width - 0.5, h: 0, line: { color: i === 0 ? theme.accent : theme.pale, width: 1 } });
    addText(slide, metric.detail, x + 0.25, 4.25, width - 0.5, 0.84, 12, i === 0 ? theme.pale : theme.muted);
  });
  addText(slide, note, 0.7, 6.06, 11.8, 0.42, 11, theme.muted);
  addNotes(slide, factIds);
  return slide;
}

function addMiniDonut(slide, theme, x, y, actual, target, label) {
  const achieved = Math.max(0, Math.min(actual, target));
  const remainder = Math.max(target - achieved, 0.0001);
  slide.addChart(CHART.doughnut, [{
    name: label,
    labels: ["achieved", "remaining"],
    values: [achieved, remainder],
  }], {
    x, y, w: 0.72, h: 0.72,
    holeSize: 72,
    showLegend: false,
    showTitle: false,
    showValue: false,
    chartColors: [theme.accent, theme.pale],
    showBorder: false,
  });
}

function lineChart(pptx, theme, index, kicker, title, series, callout, factIds = []) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, kicker, title, index);
  slide.addShape(SHAPE.roundRect, { x: 0.65, y: 1.75, w: 8.45, h: 4.65, fill: { color: theme.surface }, line: { color: theme.pale, width: 1 } });
  slide.addChart(CHART.line, series, {
    x: 0.95, y: 2.05, w: 7.85, h: 3.95,
    catAxisLabelFontFace: MONO, catAxisLabelFontSize: 12,
    valAxisLabelFontFace: MONO, valAxisLabelFontSize: 11,
    showLegend: series.length > 1, legendFontFace: MONO, legendFontSize: 10,
    legendPos: "b", showTitle: false, showValue: true, showCatName: false,
    showMarker: true, markerSize: 6, lineSize: 2.4,
    chartColors: theme.chartColors || [theme.accent, theme.good, theme.muted],
    showValAxisTitle: true, showCatAxisTitle: true,
    valAxisTitle: callout.axisTitle || "VALUE",
    valAxisTitleFontFace: MONO, valAxisTitleFontSize: 10,
    catAxisTitle: callout.catTitle || "PERIOD",
    catAxisTitleFontFace: MONO, catAxisTitleFontSize: 10,
    showValAxis: true, showCatAxis: true,
    valGridLine: { color: theme.pale, width: 1 },
    catAxisLineColor: theme.pale, valAxisLineColor: theme.pale,
    showBorder: false,
  });
  slide.addShape(SHAPE.roundRect, { x: 9.38, y: 1.75, w: 3.25, h: 4.65, fill: { color: theme.ink }, line: { color: theme.ink } });
  addText(slide, callout.value, 9.72, 2.25, 2.55, 0.9, 29, theme.bg, { bold: true });
  addText(slide, callout.label, 9.72, 3.18, 2.55, 0.35, 9, theme.accent, { fontFace: MONO, bold: true });
  addText(slide, callout.detail, 9.72, 3.82, 2.42, 1.25, 12, theme.pale);
  addText(slide, "SOURCE / LOCKED FACT STORE", 9.72, 5.68, 2.42, 0.25, 7, theme.accent, { fontFace: MONO, bold: true });
  addNotes(slide, factIds);
}

function barChart(pptx, theme, index, kicker, title, series, callout, factIds = []) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, kicker, title, index);
  slide.addShape(SHAPE.roundRect, { x: 0.65, y: 1.72, w: 9.05, h: 4.72, fill: { color: theme.surface }, line: { color: theme.pale, width: 1 } });
  slide.addChart(CHART.bar, series, {
    x: 0.98, y: 2.02, w: 8.42, h: 4.0,
    catAxisLabelFontFace: FONT, catAxisLabelFontSize: 11,
    valAxisLabelFontFace: MONO, valAxisLabelFontSize: 10,
    showLegend: series.length > 1, legendFontFace: MONO, legendFontSize: 10,
    legendPos: "b", showTitle: false, showValue: true,
    dataLabelFormatCode: "0.00",
    chartColors: theme.chartColors || [theme.accent, theme.good, theme.muted, theme.bad],
    showValAxisTitle: true, showCatAxisTitle: true,
    valAxisTitle: callout.axisTitle || "VALUE (LOWER IS BETTER)",
    valAxisTitleFontFace: MONO, valAxisTitleFontSize: 10,
    catAxisTitle: callout.catTitle || "HORIZON / VARIANT",
    catAxisTitleFontFace: MONO, catAxisTitleFontSize: 10,
    showValAxis: true, showCatAxis: true,
    valGridLine: { color: theme.pale, width: 1 },
    catAxisLineColor: theme.pale, valAxisLineColor: theme.pale,
    showBorder: false, gapWidthPct: 42,
  });
  slide.addShape(SHAPE.roundRect, { x: 9.95, y: 1.72, w: 2.68, h: 4.72, fill: { color: theme.ink }, line: { color: theme.ink } });
  addText(slide, callout.value, 10.25, 2.28, 2.05, 0.8, 26, theme.bg, { bold: true });
  addText(slide, callout.label, 10.25, 3.14, 2.05, 0.42, 8, theme.accent, { fontFace: MONO, bold: true });
  addText(slide, callout.detail, 10.25, 3.82, 2.03, 1.52, 11, theme.pale);
  addText(slide, "SOURCE / LOCKED FACT STORE", 10.25, 5.72, 2.03, 0.25, 7, theme.accent, { fontFace: MONO, bold: true });
  addNotes(slide, factIds);
}

function processSlide(pptx, theme, index, kicker, title, steps, conclusion, factIds = []) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, kicker, title, index);
  const gap = 0.18;
  const width = (11.9 - gap * (steps.length - 1)) / steps.length;
  steps.forEach((step, i) => {
    const x = 0.7 + i * (width + gap);
    const y = 2.05 + (i % 2) * 0.42;
    slide.addShape(SHAPE.roundRect, {
      x, y, w: width, h: 2.65,
      fill: { color: i === steps.length - 1 ? theme.ink : theme.surface },
      line: { color: i === steps.length - 1 ? theme.ink : theme.pale, width: 1 },
    });
    addText(slide, String(i + 1).padStart(2, "0"), x + 0.2, y + 0.22, 0.45, 0.3, 9, theme.accent, { fontFace: MONO, bold: true });
    addText(slide, step[0], x + 0.2, y + 0.68, width - 0.4, 0.48, 15, i === steps.length - 1 ? theme.bg : theme.ink, { bold: true });
    addText(slide, step[1], x + 0.2, y + 1.34, width - 0.4, 0.85, 10, i === steps.length - 1 ? theme.pale : theme.muted);
    if (i < steps.length - 1) {
      slide.addShape(SHAPE.chevron, { x: x + width - 0.08, y: y + 1.0, w: 0.28, h: 0.5, fill: { color: theme.accent }, line: { color: theme.accent } });
    }
  });
  addText(slide, conclusion, 0.72, 5.7, 11.8, 0.58, 12, theme.ink, { bold: true });
  addNotes(slide, factIds);
}

function comparisonSlide(pptx, theme, index, kicker, title, left, right, verdict, factIds = []) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, kicker, title, index);
  const panels = [left, right];
  panels.forEach((panel, i) => {
    const x = 0.7 + i * 6.05;
    slide.addShape(SHAPE.roundRect, { x, y: 1.82, w: 5.75, h: 3.95, fill: { color: i ? theme.ink : theme.surface }, line: { color: i ? theme.ink : theme.pale } });
    addText(slide, panel.label, x + 0.3, 2.12, 4.9, 0.35, 9, theme.accent, { fontFace: MONO, bold: true, charSpacing: 1.2 });
    addText(slide, panel.title, x + 0.3, 2.68, 4.9, 0.52, 19, i ? theme.bg : theme.ink, { bold: true });
    panel.items.forEach((item, j) => {
      slide.addShape(SHAPE.ellipse, { x: x + 0.32, y: 3.5 + j * 0.56, w: 0.13, h: 0.13, fill: { color: theme.accent }, line: { color: theme.accent } });
      addText(slide, item, x + 0.58, 3.35 + j * 0.56, 4.65, 0.42, 12, i ? theme.pale : theme.muted);
    });
  });
  slide.addShape(SHAPE.roundRect, { x: 3.52, y: 6.02, w: 6.3, h: 0.58, fill: { color: theme.accent }, line: { color: theme.accent } });
  addText(slide, verdict, 3.72, 6.08, 5.9, 0.4, 11, theme.bg, { bold: true, align: "center" });
  addNotes(slide, factIds);
}

function tableSlide(pptx, theme, index, kicker, title, headers, rows, callout, factIds = []) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, kicker, title, index);
  const data = [
    headers.map((text) => ({ text, options: { bold: true, color: theme.bg, fill: theme.ink, align: "center" } })),
    ...rows.map((row, rowIndex) => row.map((text, colIndex) => ({
      text: String(text),
      options: {
        color: theme.ink, fill: rowIndex % 2 ? theme.bg : theme.surface,
        bold: colIndex === 0, align: colIndex === 0 ? "left" : "center",
      },
    }))),
  ];
  slide.addTable(data, {
    x: 0.7, y: 1.82, w: 11.95, h: 4.45,
    border: { type: "solid", color: theme.pale, pt: 0.8 },
    fontFace: FONT, fontSize: 12, color: theme.ink,
    margin: 0.11, rowH: 0.6, valign: "mid",
    autoFit: false, breakLine: false,
  });
  const evidenceY = rows.length >= 6 ? 6.36 : 5.86;
  const evidenceH = rows.length >= 6 ? 0.5 : 0.72;
  slide.addShape(SHAPE.roundRect, { x: 0.72, y: evidenceY, w: 11.9, h: evidenceH, fill: { color: theme.surface }, line: { color: theme.pale, width: 1 } });
  addText(slide, callout, 1.0, evidenceY + (rows.length >= 6 ? 0.1 : 0.2), 11.34, 0.3, rows.length >= 6 ? 9.5 : 10.5, theme.ink, { bold: true, align: "center" });
  addNotes(slide, factIds);
}

function matrixSlide(pptx, theme, index, kicker, title, cells, axis, factIds = []) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, kicker, title, index);
  slide.addShape(SHAPE.line, { x: 1.4, y: 5.95, w: 9.65, h: 0, line: { color: theme.ink, width: 1.5, beginArrowType: "none", endArrowType: "triangle" } });
  slide.addShape(SHAPE.line, { x: 1.4, y: 5.95, w: 0, h: -3.85, line: { color: theme.ink, width: 1.5, endArrowType: "triangle" } });
  slide.addShape(SHAPE.line, { x: 6.23, y: 2.18, w: 0, h: 3.75, line: { color: theme.pale, width: 1, dash: "dash" } });
  slide.addShape(SHAPE.line, { x: 1.45, y: 4.06, w: 9.55, h: 0, line: { color: theme.pale, width: 1, dash: "dash" } });
  cells.forEach((cell, i) => {
    slide.addShape(SHAPE.roundRect, { x: cell.x, y: cell.y, w: cell.w, h: cell.h, fill: { color: i === 0 ? theme.ink : theme.surface }, line: { color: i === 0 ? theme.ink : theme.accent, width: 1.2 } });
    addText(slide, cell.title, cell.x + 0.18, cell.y + 0.14, cell.w - 0.36, 0.34, 12, i === 0 ? theme.bg : theme.ink, { bold: true });
    addText(slide, cell.detail, cell.x + 0.18, cell.y + 0.58, cell.w - 0.36, cell.h - 0.68, 9, i === 0 ? theme.pale : theme.muted);
  });
  addText(slide, axis.x, 9.75, 6.15, 1.4, 0.25, 8, theme.muted, { fontFace: MONO, align: "right" });
  addText(slide, axis.y, 0.58, 1.82, 1.45, 0.25, 8, theme.muted, { fontFace: MONO });
  addNotes(slide, factIds);
}

function cardsSlide(pptx, theme, index, kicker, title, cards, conclusion, factIds = []) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, kicker, title, index);
  const cols = cards.length <= 3 ? cards.length : 3;
  const rows = Math.ceil(cards.length / cols);
  const gap = 0.2;
  const width = (11.9 - gap * (cols - 1)) / cols;
  const height = rows === 1 ? 3.75 : 1.82;
  cards.forEach((card, i) => {
    const col = i % cols, row = Math.floor(i / cols);
    const x = 0.7 + col * (width + gap), y = 1.83 + row * (height + 0.18);
    slide.addShape(SHAPE.roundRect, { x, y, w: width, h: height, fill: { color: i === 0 ? theme.ink : theme.surface }, line: { color: i === 0 ? theme.ink : theme.pale } });
    addText(slide, card.tag || `0${i + 1}`, x + 0.22, y + 0.18, width - 0.44, 0.25, 7.5, theme.accent, { fontFace: MONO, bold: true, charSpacing: 1 });
    addText(slide, card.title, x + 0.22, y + 0.52, width - 0.44, 0.45, 14, i === 0 ? theme.bg : theme.ink, { bold: true });
    addText(slide, card.detail, x + 0.22, y + 1.03, width - 0.44, height - 1.2, 11, i === 0 ? theme.pale : theme.muted);
  });
  addText(slide, conclusion, 0.72, 6.25, 11.8, 0.36, 10, theme.ink, { bold: true });
  addNotes(slide, factIds);
}

function dataIntegritySlide(pptx, theme, index) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Pilot / Data Integrity", "84 天试点的数据完整性，足以支撑试点级效果评估", index);
  slide.addShape(SHAPE.roundRect, { x: 0.7, y: 1.78, w: 5.0, h: 4.65, fill: { color: theme.ink }, line: { color: theme.ink } });
  slide.addChart(CHART.doughnut, [{
    name: "记录完整性",
    labels: ["有效记录", "缺失记录"],
    values: [214680, 3048],
  }], {
    x: 1.0, y: 2.02, w: 3.25, h: 3.25,
    holeSize: 76, showLegend: false, showTitle: false, showValue: false,
    chartColors: [theme.accent, theme.muted], showBorder: false,
  });
  addText(slide, "98.6%", 1.67, 3.06, 1.9, 0.62, 27, theme.bg, { fontFace: MONO, bold: true, align: "center" });
  addText(slide, "VALID RATE", 1.72, 3.72, 1.8, 0.24, 8, theme.accent, { fontFace: MONO, bold: true, align: "center", charSpacing: 1.2 });
  addText(slide, "10 min", 4.18, 2.44, 1.05, 0.42, 18, theme.bg, { fontFace: MONO, bold: true, align: "right" });
  addText(slide, "采样间隔", 4.16, 2.91, 1.08, 0.28, 9, theme.pale, { align: "right" });
  addText(slide, "84 days", 4.02, 4.13, 1.22, 0.42, 18, theme.bg, { fontFace: MONO, bold: true, align: "right" });
  addText(slide, "连续试点", 4.16, 4.6, 1.08, 0.28, 9, theme.pale, { align: "right" });

  const facts = [
    ["THEORETICAL", "217,728", "理论记录"],
    ["VALID", "214,680", "有效记录"],
    ["MISSING", "3,048", "差额 · 1.4%"],
  ];
  facts.forEach((item, i) => {
    const y = 1.8 + i * 1.25;
    slide.addShape(SHAPE.roundRect, {
      x: 6.05, y, w: 5.9, h: 0.98,
      fill: { color: i === 1 ? theme.accent : theme.surface },
      line: { color: i === 1 ? theme.accent : theme.pale, width: 1 },
    });
    addText(slide, item[0], 6.35, y + 0.18, 1.55, 0.25, 8, i === 1 ? theme.bg : theme.muted, { fontFace: MONO, bold: true, charSpacing: 1 });
    addText(slide, item[1], 8.0, y + 0.13, 2.0, 0.4, 20, i === 1 ? theme.bg : theme.ink, { fontFace: MONO, bold: true });
    addText(slide, item[2], 10.15, y + 0.22, 1.45, 0.28, 10, i === 1 ? theme.bg : theme.muted, { align: "right" });
  });
  slide.addShape(SHAPE.line, { x: 6.05, y: 5.72, w: 5.9, h: 0, line: { color: theme.accent, width: 2 } });
  addText(slide, "结论 / 缺失率受控，但跨校部署仍需重新验证完整性。", 6.05, 5.91, 5.9, 0.42, 11, theme.ink, { bold: true });
  addNotes(slide, ["pilot-days", "sampling-interval", "theoretical-records", "valid-records", "valid-rate"]);
}

function alertQualitySlide(pptx, theme, index) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Pilot / Alert Quality", "告警质量必须同时回答：覆盖多少、打扰多少、是否平衡", index);
  slide.addShape(SHAPE.ellipse, { x: 4.55, y: 1.82, w: 3.0, h: 3.0, fill: { color: theme.ink }, line: { color: theme.accent, width: 3 } });
  slide.addShape(SHAPE.ellipse, { x: 4.9, y: 2.17, w: 2.3, h: 2.3, fill: { color: theme.surface }, line: { color: theme.surface } });
  addText(slide, "85.7%", 5.15, 2.86, 1.8, 0.55, 26, theme.ink, { fontFace: MONO, bold: true, align: "center" });
  addText(slide, "F1 / BALANCE", 5.2, 3.48, 1.7, 0.25, 8, theme.accent, { fontFace: MONO, bold: true, align: "center", charSpacing: 1 });
  [
    { x: 0.72, value: "81.1%", label: "PRECISION", detail: "30 次确认 / 37 次告警", color: theme.accent },
    { x: 8.4, value: "90.9%", label: "RECALL", detail: "30 次确认 / 33 次真实事件", color: theme.good },
  ].forEach((metric) => {
    slide.addShape(SHAPE.roundRect, { x: metric.x, y: 2.08, w: 3.55, h: 2.48, fill: { color: theme.surface }, line: { color: metric.color, width: 2 } });
    addText(slide, metric.value, metric.x + 0.28, 2.56, 2.98, 0.6, 27, theme.ink, { fontFace: MONO, bold: true });
    addText(slide, metric.label, metric.x + 0.3, 3.23, 2.95, 0.28, 8, metric.color, { fontFace: MONO, bold: true, charSpacing: 1.2 });
    addText(slide, metric.detail, metric.x + 0.3, 3.72, 2.92, 0.42, 11, theme.muted);
  });
  const chain = [
    ["37", "系统告警", "模型输出总量"],
    ["30", "人工确认", "precision 分子"],
    ["33", "真实事件", "recall 分母"],
  ];
  addText(slide, "EVIDENCE BASE / 三个样本量是质量指标的基数，不是流程步骤", 1.42, 4.82, 10.4, 0.28, 8.5, theme.accent, { fontFace: MONO, bold: true, align: "center" });
  chain.forEach((item, i) => {
    const x = 1.42 + i * 3.82;
    slide.addShape(SHAPE.roundRect, { x, y: 5.16, w: 3.28, h: 0.98, fill: { color: i === 1 ? theme.accent : theme.surface }, line: { color: i === 1 ? theme.accent : theme.pale } });
    addText(slide, item[0], x + 0.24, 5.34, 0.72, 0.36, 18, i === 1 ? theme.bg : theme.ink, { fontFace: MONO, bold: true });
    addText(slide, item[1], x + 1.02, 5.28, 1.7, 0.3, 11, i === 1 ? theme.bg : theme.ink, { bold: true });
    addText(slide, item[2], x + 1.02, 5.68, 1.9, 0.25, 8.5, i === 1 ? theme.bg : theme.muted);
  });
  addText(slide, "判读 / 高召回已建立安全底线；下一轮重点降低误报打扰。", 0.74, 6.4, 11.7, 0.34, 11, theme.ink, { bold: true, align: "center" });
  addNotes(slide, ["alerts", "confirmed-alerts", "actual-events", "precision", "recall", "f1"]);
}

function marketFunnelSlide(pptx, theme, index) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Market / Beachhead", "市场不是从 4,120 所起跑，而是从 3–5 校验证复制", index);
  const layers = [
    { x: 0.85, y: 1.92, w: 7.9, h: 1.18, value: "4,120", label: "TAM / 可触达校园总体假设", fill: theme.pale },
    { x: 1.75, y: 3.28, w: 6.1, h: 1.18, value: "620", label: "SAM / 当前团队可服务范围", fill: theme.surface },
    { x: 2.65, y: 4.64, w: 4.3, h: 1.18, value: "3–5", label: "NEXT / 多校差异化验证", fill: theme.accent },
  ];
  layers.forEach((layer, i) => {
    slide.addShape(SHAPE.chevron, { x: layer.x, y: layer.y, w: layer.w, h: layer.h, fill: { color: layer.fill }, line: { color: i === 2 ? theme.accent : theme.pale, width: 1 } });
    addText(slide, layer.value, layer.x + 0.32, layer.y + 0.24, 1.45, 0.5, 22, i === 2 ? theme.bg : theme.ink, { fontFace: MONO, bold: true });
    addText(slide, layer.label, layer.x + 1.85, layer.y + 0.34, layer.w - 2.35, 0.35, 11, i === 2 ? theme.bg : theme.muted, { bold: true });
  });
  slide.addShape(SHAPE.roundRect, { x: 9.15, y: 1.92, w: 3.12, h: 3.9, fill: { color: theme.ink }, line: { color: theme.ink } });
  addText(slide, "BEACHHEAD\nLOGIC", 9.48, 2.3, 2.45, 0.78, 15, theme.accent, { fontFace: MONO, bold: true });
  addText(slide, "01 选取差异化校园\n\n02 对齐统一验收\n\n03 比较复制成本\n\n04 再决定规模化", 9.48, 3.28, 2.38, 1.72, 11, theme.pale, { breakLine: false });
  addText(slide, "市场数字不是收入预测；当前关键是证明跨校园复制。", 9.48, 5.28, 2.38, 0.46, 10, theme.bg, { bold: true });
  addNotes(slide, ["market", "serviceable-market"]);
}

function prototypeExplodedSlide(pptx, theme, index) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Prototype / CAD-to-Field", "样机围绕安装、信号质量与可维护性分层设计", index);
  const layers = [
    ["01 / STRUCTURE", "结构防护", "安装、更换与防护路径"],
    ["02 / ELECTRONICS", "低功耗电子", "采集、本地缓存与通信"],
    ["03 / ALGORITHM", "边缘判断", "多信号组合与异常候选"],
    ["04 / OPERATIONS", "现场运维", "校准、巡检与故障自检"],
  ];
  layers.forEach((item, i) => {
    const x = 0.92 + i * 0.58;
    const y = 1.95 + i * 0.9;
    slide.addShape(SHAPE.roundRect, { x, y, w: 6.15, h: 0.72, fill: { color: i === 3 ? theme.accent : i % 2 ? theme.pale : theme.surface }, line: { color: i === 3 ? theme.accent : theme.pale, width: 1.2 } });
    addText(slide, item[0], x + 0.24, y + 0.16, 1.55, 0.28, 9, i === 3 ? theme.bg : theme.muted, { fontFace: MONO, bold: true });
    addText(slide, item[1], x + 1.9, y + 0.12, 1.35, 0.32, 14, i === 3 ? theme.bg : theme.ink, { bold: true });
    addText(slide, item[2], x + 3.32, y + 0.14, 2.45, 0.32, 11, i === 3 ? theme.bg : theme.muted);
    if (i < layers.length - 1) {
      slide.addShape(SHAPE.line, { x: x + 5.5, y: y + 0.73, w: 0.55, h: 0.88, line: { color: theme.accent, width: 1.5, dash: "dash" } });
    }
  });
  slide.addShape(SHAPE.roundRect, { x: 8.48, y: 1.93, w: 3.58, h: 4.35, fill: { color: theme.ink }, line: { color: theme.ink } });
  addText(slide, "¥ 1,860", 8.85, 2.42, 2.82, 0.62, 27, theme.bg, { fontFace: MONO, bold: true });
  addText(slide, "CURRENT BOM", 8.88, 3.06, 2.6, 0.26, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 1 });
  addText(slide, "维护设计检查", 8.88, 3.72, 2.55, 0.32, 12, theme.bg, { bold: true });
  addText(slide, "✓ 模块可更换\n✓ 断网可缓存\n✓ 状态可自检\n✓ 校准有记录", 8.88, 4.2, 2.45, 1.24, 11, theme.pale);
  addText(slide, "目标 / 不牺牲可靠性的前提下降本。", 8.88, 5.67, 2.48, 0.4, 10, theme.bg, { bold: true });
  addNotes(slide, ["bom"]);
}

function roadmapMilestonesSlide(pptx, theme, index) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Roadmap / Multi-Campus", "下一阶段不是扩张，而是逐级验证复制条件", index);
  slide.addShape(SHAPE.line, { x: 1.05, y: 5.55, w: 10.55, h: -3.18, line: { color: theme.accent, width: 3, endArrowType: "triangle" } });
  const milestones = [
    { x: 1.0, y: 4.85, tag: "M1", title: "选校", detail: "覆盖不同水源、规模与运维能力" },
    { x: 3.7, y: 4.02, tag: "M2", title: "对齐", detail: "统一部署、校准、事件和验收协议" },
    { x: 6.42, y: 3.18, tag: "M3", title: "运行", detail: "持续收集完整性、告警与处置证据" },
    { x: 9.12, y: 2.35, tag: "M4", title: "决策", detail: "判断模型、产品与服务是否可复制" },
  ];
  milestones.forEach((item, i) => {
    slide.addShape(SHAPE.ellipse, { x: item.x, y: item.y, w: 0.72, h: 0.72, fill: { color: i === 3 ? theme.accent : theme.ink }, line: { color: theme.accent, width: 2 } });
    addText(slide, item.tag, item.x + 0.11, item.y + 0.2, 0.5, 0.25, 9, i === 3 ? theme.bg : theme.accent, { fontFace: MONO, bold: true, align: "center" });
    const panelY = item.y + (i % 2 === 0 ? -1.3 : 0.92);
    slide.addShape(SHAPE.roundRect, { x: item.x - 0.35, y: panelY, w: 2.55, h: 1.05, fill: { color: i === 3 ? theme.ink : theme.surface }, line: { color: i === 3 ? theme.ink : theme.pale } });
    addText(slide, item.title, item.x - 0.12, panelY + 0.16, 1.98, 0.28, 13, i === 3 ? theme.bg : theme.ink, { bold: true });
    addText(slide, item.detail, item.x - 0.12, panelY + 0.5, 2.0, 0.38, 9.5, i === 3 ? theme.pale : theme.muted);
  });
  slide.addShape(SHAPE.roundRect, { x: 3.55, y: 6.12, w: 6.35, h: 0.54, fill: { color: theme.accent }, line: { color: theme.accent } });
  addText(slide, "GATE / 多校验证通过后，才讨论规模化销售。", 3.75, 6.2, 5.95, 0.3, 11, theme.bg, { fontFace: MONO, bold: true, align: "center" });
  addNotes(slide);
}

function campusVoiceSlide(pptx, theme, index) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Research / Voice of Campus", "91 位真实角色访谈，共同指向“早发现、可解释、少打扰”", index);
  slide.addShape(SHAPE.ellipse, { x: 0.78, y: 2.02, w: 3.65, h: 3.65, fill: { color: theme.accent }, line: { color: theme.accent } });
  addText(slide, "91", 1.35, 2.76, 2.5, 0.85, 38, theme.bg, { fontFace: MONO, bold: true, align: "center" });
  addText(slide, "INTERVIEWS", 1.43, 3.7, 2.34, 0.28, 9, theme.bg, { fontFace: MONO, bold: true, align: "center", charSpacing: 1.6 });
  addText(slide, "学生 · 后勤 · 管理者", 1.25, 4.42, 2.72, 0.35, 12, theme.bg, { bold: true, align: "center" });
  const voices = [
    ["38", "STUDENTS", "安全提示要清晰", "不制造无意义恐慌，处置结果可反馈。"],
    ["29", "STAFF", "事件证据要完整", "需要定位、时间线和可回看的处置记录。"],
    ["24", "MANAGERS", "复制成本要可控", "关注部署、维护负担与校级责任闭环。"],
  ];
  voices.forEach((item, i) => {
    const y = 1.82 + i * 1.45;
    slide.addShape(SHAPE.roundRect, { x: 5.0, y, w: 7.12, h: 1.16, fill: { color: i === 1 ? theme.ink : theme.surface }, line: { color: i === 1 ? theme.accent : theme.pale, width: 1.2 } });
    addText(slide, item[0], 5.3, y + 0.25, 0.72, 0.45, 22, i === 1 ? theme.accent : theme.ink, { fontFace: MONO, bold: true });
    addText(slide, item[1], 6.05, y + 0.34, 1.2, 0.25, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 1 });
    addText(slide, item[2], 7.32, y + 0.2, 1.95, 0.35, 15, i === 1 ? theme.bg : theme.ink, { bold: true });
    addText(slide, item[3], 9.28, y + 0.22, 2.48, 0.54, 12, i === 1 ? theme.pale : theme.muted);
  });
  slide.addShape(SHAPE.roundRect, { x: 5.0, y: 6.16, w: 7.12, h: 0.5, fill: { color: theme.accent }, line: { color: theme.accent } });
  addText(slide, "产品定义 / 不是多装传感器，而是把感知、判断和处置闭环。", 5.2, 6.24, 6.72, 0.28, 11, theme.bg, { bold: true, align: "center" });
  addNotes(slide, ["student-interviews", "staff-interviews", "manager-interviews"]);
}

function selfServiceTargetSlide(pptx, theme, index) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Adoption / Self Service", "自助分析率提升 30 个百分点，Q4 明确越过年度目标", index);
  const quarters = [
    ["Q1", 38],
    ["Q2", 46],
    ["Q3", 57],
    ["Q4", 68],
  ];
  const baseY = 5.78;
  const scale = 0.047;
  quarters.forEach((item, i) => {
    const x = 1.05 + i * 2.22;
    const height = item[1] * scale;
    slide.addShape(SHAPE.roundRect, {
      x, y: baseY - height, w: 1.35, h: height,
      fill: { color: i === 3 ? theme.accent : theme.ink },
      line: { color: i === 3 ? theme.accent : theme.ink },
    });
    addText(slide, `${item[1]}%`, x - 0.05, baseY - height - 0.52, 1.45, 0.4, 20, i === 3 ? theme.accent : theme.ink, { fontFace: MONO, bold: true, align: "center" });
    addText(slide, item[0], x + 0.2, baseY + 0.14, 0.95, 0.28, 9, theme.muted, { fontFace: MONO, bold: true, align: "center" });
  });
  const targetY = baseY - 65 * scale;
  slide.addShape(SHAPE.line, { x: 0.82, y: targetY, w: 8.75, h: 0, line: { color: theme.accent, width: 2.2, dash: "dash" } });
  slide.addShape(SHAPE.roundRect, { x: 7.74, y: targetY - 0.28, w: 1.68, h: 0.5, fill: { color: theme.bg }, line: { color: theme.accent, width: 1.2 } });
  addText(slide, "TARGET 65%", 7.9, targetY - 0.17, 1.34, 0.25, 9, theme.accent, { fontFace: MONO, bold: true, align: "center" });
  slide.addShape(SHAPE.roundRect, { x: 10.0, y: 1.78, w: 2.58, h: 4.48, fill: { color: theme.ink }, line: { color: theme.ink } });
  addText(slide, "+30pp", 10.34, 2.34, 1.92, 0.72, 28, theme.bg, { fontFace: MONO, bold: true });
  addText(slide, "Q1 → Q4", 10.37, 3.12, 1.85, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 1 });
  slide.addShape(SHAPE.line, { x: 10.35, y: 3.72, w: 1.88, h: 0, line: { color: theme.pale, width: 1 } });
  addText(slide, "68%", 10.35, 4.06, 1.05, 0.48, 21, theme.bg, { fontFace: MONO, bold: true });
  addText(slide, "Q4 实际", 11.3, 4.18, 0.78, 0.25, 9, theme.pale);
  addText(slide, "+3pp", 10.35, 4.88, 1.05, 0.45, 19, theme.accent, { fontFace: MONO, bold: true });
  addText(slide, "高于目标", 11.3, 5.0, 0.78, 0.25, 9, theme.pale);
  addText(slide, "结论 / 越过目标发生在 Q4，图形本身即可读出。", 10.35, 5.62, 1.9, 0.46, 10, theme.bg, { bold: true });
  addNotes(slide, ["self-service-rate-q1", "self-service-rate-q2", "self-service-rate-q3", "self-service-rate-q4", "self-service-target"]);
}

function customerGrowthTargetSlide(pptx, theme, index) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Growth / Customers", "客户数连续四季上行，Q4 越过 90 家年度目标", index);
  const points = [
    { x: 1.12, y: 5.45, q: "Q1", value: 46 },
    { x: 3.6, y: 4.63, q: "Q2", value: 59 },
    { x: 6.08, y: 3.55, q: "Q3", value: 76 },
    { x: 8.56, y: 2.42, q: "Q4", value: 94 },
  ];
  points.forEach((point, i) => {
    if (i < points.length - 1) {
      const next = points[i + 1];
      slide.addShape(SHAPE.line, { x: point.x + 0.34, y: point.y + 0.34, w: next.x - point.x, h: next.y - point.y, line: { color: theme.ink, width: 4 } });
    }
    slide.addShape(SHAPE.ellipse, { x: point.x, y: point.y, w: 0.68, h: 0.68, fill: { color: i === 3 ? theme.accent : theme.ink }, line: { color: theme.bg, width: 2 } });
    addText(slide, String(point.value), point.x - 0.26, point.y - 0.64, 1.2, 0.42, 19, i === 3 ? theme.accent : theme.ink, { fontFace: MONO, bold: true, align: "center" });
    addText(slide, point.q, point.x - 0.08, point.y + 0.82, 0.85, 0.28, 9, theme.muted, { fontFace: MONO, bold: true, align: "center" });
  });
  slide.addShape(SHAPE.line, { x: 0.88, y: 2.77, w: 8.98, h: 0, line: { color: theme.accent, width: 2, dash: "dash" } });
  slide.addShape(SHAPE.roundRect, { x: 6.85, y: 2.47, w: 1.7, h: 0.5, fill: { color: theme.bg }, line: { color: theme.accent, width: 1.2 } });
  addText(slide, "TARGET 90", 7.02, 2.59, 1.36, 0.24, 9, theme.accent, { fontFace: MONO, bold: true, align: "center" });
  slide.addShape(SHAPE.roundRect, { x: 10.15, y: 1.84, w: 2.3, h: 4.4, fill: { color: theme.ink }, line: { color: theme.ink } });
  addText(slide, "94", 10.48, 2.34, 1.66, 0.65, 30, theme.bg, { fontFace: MONO, bold: true });
  addText(slide, "Q4 CUSTOMERS", 10.5, 3.05, 1.62, 0.25, 8, theme.accent, { fontFace: MONO, bold: true });
  addText(slide, "+4", 10.5, 3.86, 1.2, 0.5, 23, theme.accent, { fontFace: MONO, bold: true });
  addText(slide, "高于年度目标", 10.5, 4.42, 1.52, 0.28, 10, theme.pale);
  addText(slide, "+104%", 10.5, 5.04, 1.45, 0.45, 19, theme.bg, { fontFace: MONO, bold: true });
  addText(slide, "Q1 → Q4", 10.5, 5.54, 1.52, 0.26, 9, theme.pale);
  addNotes(slide, ["customer-count-q1", "customer-count-q2", "customer-count-q3", "customer-count-q4", "customers-target", "customers-actual"]);
}

function academicBenchmarkHeroSlide(pptx, theme, index) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Benchmark / METR-LA", "三个预测窗，MDGFormer 均优于最强对照 STFGNN", index);
  slide.addChart(CHART.bar, [
    { name: "STFGNN", labels: ["15 min", "30 min", "60 min"], values: [2.66, 3.02, 3.45] },
    { name: "MDGFormer", labels: ["15 min", "30 min", "60 min"], values: [2.58, 2.92, 3.31] },
  ], {
    x: 0.78, y: 1.72, w: 11.8, h: 3.85,
    catAxisLabelFontFace: FONT, catAxisLabelFontSize: 12,
    valAxisLabelFontFace: MONO, valAxisLabelFontSize: 10,
    showLegend: true, legendFontFace: MONO, legendFontSize: 11,
    legendPos: "t", showTitle: false, showValue: true,
    dataLabelPosition: "outEnd", dataLabelColor: theme.ink, dataLabelFormatCode: "0.00",
    dataLabelFormatString: "0.00", dataLabelFontFace: MONO, dataLabelFontSize: 11,
    chartColors: [theme.ink, theme.accent],
    showValAxisTitle: true, valAxisTitle: "MAE ↓", valAxisTitleFontFace: MONO, valAxisTitleFontSize: 10,
    showCatAxisTitle: false, showValAxis: true, showCatAxis: true,
    valGridLine: { color: theme.pale, width: 1 },
    catAxisLineColor: theme.pale, valAxisLineColor: theme.pale,
    showBorder: false, gapWidthPct: 52,
  });
  const deltas = [
    ["15 MIN", "−0.08"],
    ["30 MIN", "−0.10"],
    ["60 MIN", "−0.14"],
  ];
  deltas.forEach((item, i) => {
    const x = 0.85 + i * 4.08;
    slide.addShape(SHAPE.roundRect, { x, y: 5.84, w: 3.65, h: 0.76, fill: { color: i === 2 ? theme.accent : theme.surface }, line: { color: i === 2 ? theme.accent : theme.pale } });
    addText(slide, `${item[0]} / VS STFGNN`, x + 0.24, 6.05, 1.65, 0.25, 8.5, i === 2 ? theme.bg : theme.muted, { fontFace: MONO, bold: true });
    addText(slide, item[1], x + 2.05, 5.96, 1.22, 0.38, 18, i === 2 ? theme.bg : theme.ink, { fontFace: MONO, bold: true, align: "right" });
  });
  addNotes(slide, ["mae-stfgnn-metr-la-15min", "mae-stfgnn-metr-la-30min", "mae-stfgnn-metr-la-60min", "mae-mdgformer-metr-la-15min", "mae-mdgformer-metr-la-30min", "mae-mdgformer-metr-la-60min"]);
}

function academicHorizonDeltaSlide(pptx, theme, index) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Result / Horizon", "预测窗越长，MDGFormer 相对最佳基线的优势越明显", index);
  const horizons = [
    { label: "15 MIN", baseline: 2.66, ours: 2.58, delta: "−0.08" },
    { label: "30 MIN", baseline: 3.02, ours: 2.92, delta: "−0.10" },
    { label: "60 MIN", baseline: 3.45, ours: 3.31, delta: "−0.14" },
  ];
  horizons.forEach((item, i) => {
    const x = 0.78 + i * 4.12;
    slide.addShape(SHAPE.roundRect, { x, y: 1.92, w: 3.72, h: 3.88, fill: { color: i === 2 ? theme.ink : theme.surface }, line: { color: i === 2 ? theme.ink : theme.pale } });
    addText(slide, item.label, x + 0.3, 2.24, 1.2, 0.28, 9, theme.accent, { fontFace: MONO, bold: true });
    addText(slide, "STFGNN", x + 0.3, 3.0, 1.12, 0.26, 8, i === 2 ? theme.pale : theme.muted, { fontFace: MONO, bold: true });
    addText(slide, String(item.baseline), x + 1.62, 2.83, 1.55, 0.48, 21, i === 2 ? theme.bg : theme.ink, { fontFace: MONO, bold: true, align: "right" });
    slide.addShape(SHAPE.line, { x: x + 0.32, y: 3.55, w: 3.05, h: 0, line: { color: theme.pale, width: 1 } });
    addText(slide, "MDGFORMER", x + 0.3, 3.9, 1.35, 0.26, 8, theme.accent, { fontFace: MONO, bold: true });
    addText(slide, String(item.ours), x + 1.62, 3.73, 1.55, 0.48, 21, i === 2 ? theme.bg : theme.ink, { fontFace: MONO, bold: true, align: "right" });
    slide.addShape(SHAPE.roundRect, { x: x + 0.3, y: 4.67, w: 3.08, h: 0.72, fill: { color: theme.accent }, line: { color: theme.accent } });
    addText(slide, item.delta, x + 0.55, 4.8, 2.58, 0.38, 20, theme.bg, { fontFace: MONO, bold: true, align: "center" });
  });
  addText(slide, "READOUT / 15 → 60 分钟，MAE 差值从 0.08 扩大到 0.14；方向一致但不等于机制因果。", 0.82, 6.28, 11.72, 0.36, 11, theme.ink, { bold: true, align: "center" });
  addNotes(slide, ["mae-stfgnn-metr-la-15min", "mae-stfgnn-metr-la-30min", "mae-stfgnn-metr-la-60min", "mae-mdgformer-metr-la-15min", "mae-mdgformer-metr-la-30min", "mae-mdgformer-metr-la-60min"]);
}

function academicAblationSlide(pptx, theme, index) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Ablation / Evidence Map", "三个模块均贡献增益，动态图移除后的退化最大", index);
  slide.addShape(SHAPE.ellipse, { x: 4.95, y: 2.05, w: 3.35, h: 3.35, fill: { color: theme.ink }, line: { color: theme.accent, width: 3 } });
  addText(slide, "3.31", 5.57, 2.87, 2.1, 0.7, 30, theme.bg, { fontFace: MONO, bold: true, align: "center" });
  addText(slide, "FULL MODEL / MAE", 5.62, 3.7, 2.0, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, align: "center" });
  const nodes = [
    { x: 0.75, y: 2.0, tag: "RQ1", title: "STATIC GRAPH", value: "3.46", delta: "+0.15" },
    { x: 1.3, y: 4.62, tag: "RQ2", title: "NO MULTISCALE", value: "3.42", delta: "+0.11" },
    { x: 9.32, y: 3.08, tag: "TRAINING", title: "NO CURRICULUM", value: "3.39", delta: "+0.08" },
  ];
  nodes.forEach((item, i) => {
    slide.addShape(SHAPE.roundRect, { x: item.x, y: item.y, w: 3.12, h: 1.38, fill: { color: i === 0 ? theme.accent : theme.surface }, line: { color: i === 0 ? theme.accent : theme.pale } });
    addText(slide, `${item.tag} / ${item.title}`, item.x + 0.24, item.y + 0.2, 2.62, 0.26, 8, i === 0 ? theme.bg : theme.muted, { fontFace: MONO, bold: true });
    addText(slide, item.value, item.x + 0.24, item.y + 0.6, 1.15, 0.42, 19, i === 0 ? theme.bg : theme.ink, { fontFace: MONO, bold: true });
    addText(slide, item.delta, item.x + 1.55, item.y + 0.6, 1.26, 0.42, 19, i === 0 ? theme.bg : theme.accent, { fontFace: MONO, bold: true, align: "right" });
    const targetX = i < 2 ? 4.95 : 8.3;
    const targetY = i === 0 ? 2.8 : i === 1 ? 4.45 : 3.65;
    slide.addShape(SHAPE.line, { x: i < 2 ? item.x + 3.12 : targetX, y: item.y + 0.7, w: i < 2 ? targetX - item.x - 3.12 : item.x - targetX, h: targetY - item.y - 0.7, line: { color: theme.accent, width: 1.8, dash: "dash" } });
  });
  addText(slide, "证据边界 / 消融支持模块贡献判断，不证明唯一因果机制。", 3.64, 6.18, 6.05, 0.42, 11, theme.ink, { bold: true, align: "center" });
  addNotes(slide, ["ablation-full", "ablation-static", "ablation-scale", "ablation-curriculum"]);
}

function campusMapSlide(pptx, theme, index) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Map / Use Context", "一校三类关键区域，形成从水源到使用端的观测地图", index);
  slide.addShape(SHAPE.roundRect, { x: 0.68, y: 1.78, w: 8.1, h: 4.72, fill: { color: theme.surface }, line: { color: theme.pale } });
  const nodes = [
    { x: 1.15, y: 3.0, label: "水源 / 储水", tag: "SOURCE" },
    { x: 3.85, y: 3.0, label: "管网节点", tag: "DISTRIBUTION" },
    { x: 6.55, y: 3.0, label: "高频使用端", tag: "ENDPOINT" },
  ];
  slide.addShape(SHAPE.line, { x: 2.55, y: 3.62, w: 1.22, h: 0, line: { color: theme.accent, width: 3, endArrowType: "triangle" } });
  slide.addShape(SHAPE.line, { x: 5.25, y: 3.62, w: 1.22, h: 0, line: { color: theme.accent, width: 3, endArrowType: "triangle" } });
  nodes.forEach((node, i) => {
    slide.addShape(SHAPE.ellipse, { x: node.x, y: node.y, w: 1.25, h: 1.25, fill: { color: i === 1 ? theme.accent : theme.ink }, line: { color: theme.accent, width: 2 } });
    addText(slide, String(i + 1).padStart(2, "0"), node.x + 0.37, node.y + 0.3, 0.5, 0.4, 15, i === 1 ? theme.bg : theme.accent, { fontFace: MONO, bold: true, align: "center" });
    addText(slide, node.label, node.x - 0.35, node.y + 1.42, 1.95, 0.35, 12, theme.ink, { bold: true, align: "center" });
    addText(slide, node.tag, node.x - 0.35, node.y + 1.8, 1.95, 0.25, 7, theme.muted, { fontFace: MONO, align: "center" });
  });
  const evidence = [
    ["持续感知", "记录异常持续时间"],
    ["路径定位", "减少盲目排查范围"],
    ["处置反馈", "连接风险与责任闭环"],
  ];
  evidence.forEach((item, i) => {
    const y = 1.9 + i * 1.42;
    slide.addShape(SHAPE.roundRect, { x: 9.1, y, w: 3.15, h: 1.12, fill: { color: i === 0 ? theme.ink : theme.pale }, line: { color: theme.pale } });
    addText(slide, `0${i + 1} / ${item[0]}`, 9.38, y + 0.18, 2.6, 0.3, 10, i === 0 ? theme.accent : theme.ink, { fontFace: MONO, bold: true });
    addText(slide, item[1], 9.38, y + 0.57, 2.55, 0.3, 10, i === 0 ? theme.bg : theme.muted);
  });
  addText(slide, "隐私边界：地图表达观测逻辑，不泄露真实校园坐标。", 9.12, 6.0, 3.0, 0.4, 9, theme.muted);
  addNotes(slide);
}

function dashboardMockupSlide(pptx, theme, index) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Product / Native Mockup", "一个看板回答三个问题：哪里异常、为什么、下一步做什么", index);
  slide.addShape(SHAPE.roundRect, { x: 0.68, y: 1.72, w: 8.72, h: 4.82, fill: { color: theme.surface }, line: { color: theme.pale, width: 1.2 } });
  slide.addShape(SHAPE.rect, { x: 0.68, y: 1.72, w: 8.72, h: 0.45, fill: { color: theme.ink }, line: { color: theme.ink } });
  ["FF876D", "F2C14E", "50D2C2"].forEach((color, i) => slide.addShape(SHAPE.ellipse, { x: 0.92 + i * 0.27, y: 1.87, w: 0.11, h: 0.11, fill: { color }, line: { color } }));
  slide.addShape(SHAPE.roundRect, { x: 1.0, y: 2.5, w: 4.25, h: 3.45, fill: { color: theme.pale }, line: { color: theme.pale } });
  addText(slide, "LIVE CAMPUS MAP", 1.25, 2.78, 2.2, 0.25, 8, theme.muted, { fontFace: MONO, bold: true });
  [[1.7,3.65],[3.1,4.6],[4.2,3.35]].forEach((point, i) => {
    slide.addShape(SHAPE.ellipse, { x: point[0], y: point[1], w: 0.36, h: 0.36, fill: { color: i === 1 ? theme.bad : theme.accent }, line: { color: theme.surface, width: 2 } });
  });
  slide.addShape(SHAPE.line, { x: 1.95, y: 3.88, w: 1.35, h: 0.8, line: { color: theme.accent, width: 2 } });
  slide.addShape(SHAPE.line, { x: 3.4, y: 4.55, w: 1.05, h: -1.0, line: { color: theme.accent, width: 2 } });
  addText(slide, "异常节点 07", 5.62, 2.65, 2.95, 0.4, 16, theme.ink, { bold: true });
  addText(slide, "浊度连续 30 min 偏离基线", 5.62, 3.15, 2.95, 0.35, 11, theme.muted);
  ["阈值证据已锁定", "相邻节点未同步", "建议现场复核"].forEach((text, i) => {
    slide.addShape(SHAPE.line, { x: 5.68, y: 3.88 + i * 0.62, w: 0.25, h: 0, line: { color: theme.accent, width: 3 } });
    addText(slide, text, 6.08, 3.68 + i * 0.62, 2.35, 0.38, 10, theme.ink);
  });
  slide.addShape(SHAPE.roundRect, { x: 9.72, y: 1.72, w: 2.9, h: 4.82, fill: { color: theme.ink }, line: { color: theme.ink } });
  addText(slide, "ACTION", 10.02, 2.1, 2.2, 0.28, 8, theme.accent, { fontFace: MONO, bold: true });
  addText(slide, "派发现场复核", 10.02, 2.62, 2.22, 0.55, 18, theme.bg, { bold: true });
  addText(slide, "责任人  后勤值班\n时限     42 min\n证据     3 条趋势", 10.02, 3.45, 2.15, 1.3, 11, theme.pale);
  slide.addShape(SHAPE.roundRect, { x: 10.02, y: 5.28, w: 2.1, h: 0.52, fill: { color: theme.accent }, line: { color: theme.accent } });
  addText(slide, "确认处置", 10.15, 5.34, 1.85, 0.35, 11, theme.bg, { bold: true, align: "center" });
  addNotes(slide);
}

function networkDatasetSlide(pptx, theme, index, brief) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Data / Two Networks", "两套公开交通网络，统一切分与预测窗", index);
  const panels = [
    { x: 0.72, title: "METR-LA", sensors: val(brief, "metr-sensors"), observations: val(brief, "metr-observations"), color: theme.ink },
    { x: 6.55, title: "PEMS-BAY", sensors: val(brief, "pems-sensors"), observations: val(brief, "pems-observations"), color: theme.accent },
  ];
  panels.forEach((panel, p) => {
    slide.addShape(SHAPE.roundRect, { x: panel.x, y: 1.78, w: 5.45, h: 4.62, fill: { color: p === 0 ? theme.ink : theme.surface }, line: { color: p === 0 ? theme.ink : theme.pale } });
    addText(slide, panel.title, panel.x + 0.32, 2.05, 2.4, 0.42, 16, p === 0 ? theme.bg : theme.ink, { fontFace: MONO, bold: true });
    addText(slide, `${panel.sensors}`, panel.x + 0.32, 2.65, 1.7, 0.65, 28, p === 0 ? theme.bg : theme.ink, { bold: true });
    addText(slide, "SENSORS", panel.x + 1.85, 2.82, 1.35, 0.25, 8, theme.accent, { fontFace: MONO, bold: true });
    const points = p === 0
      ? [[1.0,1.0],[1.7,0.55],[2.45,1.22],[3.15,0.72],[3.75,1.42],[2.2,2.05],[1.25,2.35],[3.55,2.55]]
      : [[0.85,0.65],[1.6,1.15],[2.35,0.55],[3.05,1.2],[3.85,0.72],[1.15,2.15],[2.25,2.35],[3.55,2.1],[4.15,1.65]];
    points.forEach((point, i) => {
      const x = panel.x + 0.55 + point[0], y = 3.08 + point[1];
      if (i > 0) {
        const previous = points[i - 1];
        slide.addShape(SHAPE.line, { x: panel.x + 0.61 + previous[0], y: 3.14 + previous[1], w: point[0] - previous[0], h: point[1] - previous[1], line: { color: p === 0 ? theme.pale : theme.muted, width: 1.2, transparency: 20 } });
      }
      slide.addShape(SHAPE.ellipse, { x, y, w: 0.18, h: 0.18, fill: { color: i % 3 === 0 ? theme.accent : panel.color }, line: { color: theme.bg, width: 1 } });
    });
    addText(slide, `${panel.observations.toLocaleString()} steps · 5 min sampling`, panel.x + 0.32, 5.85, 4.7, 0.3, 9, p === 0 ? theme.pale : theme.muted, { fontFace: MONO });
  });
  addText(slide, "统一协议 / 70% TRAIN · 10% VALID · 20% TEST", 3.75, 6.55, 5.8, 0.28, 9, theme.accent, { fontFace: MONO, bold: true, align: "center" });
  addNotes(slide, ["metr-sensors", "metr-observations", "pems-sensors", "pems-observations", "split-train", "split-valid", "split-test", "sample-minutes"]);
}

function dynamicGraphSlide(pptx, theme, index) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Module / Dynamic Graph", "关系不是固定邻接表，而是随交通状态更新", index);
  const origins = [1.15, 6.25];
  origins.forEach((origin, panel) => {
    slide.addShape(SHAPE.roundRect, { x: origin, y: 1.92, w: 4.1, h: 3.78, fill: { color: panel === 0 ? theme.surface : theme.ink }, line: { color: panel === 0 ? theme.pale : theme.ink } });
    addText(slide, panel === 0 ? "t₀ / NORMAL" : "t₁ / INCIDENT", origin + 0.3, 2.2, 2.0, 0.28, 8, theme.accent, { fontFace: MONO, bold: true });
    const nodes = [[0.75,1.25],[1.9,0.8],[2.95,1.45],[1.2,2.35],[2.55,2.55]];
    const links = panel === 0 ? [[0,1],[1,2],[0,3],[3,4],[2,4]] : [[0,1],[1,3],[3,4],[1,4],[2,4]];
    links.forEach((pair, i) => {
      const a = nodes[pair[0]], b = nodes[pair[1]];
      slide.addShape(SHAPE.line, { x: origin + 0.85 + a[0], y: 2.65 + a[1], w: b[0] - a[0], h: b[1] - a[1], line: { color: i === links.length - 1 ? theme.accent : theme.muted, width: i === links.length - 1 ? 3 : 1.4 } });
    });
    nodes.forEach((node, i) => slide.addShape(SHAPE.ellipse, { x: origin + 0.72 + node[0], y: 2.52 + node[1], w: 0.28, h: 0.28, fill: { color: i === 1 && panel === 1 ? theme.accent : panel === 0 ? theme.ink : theme.bg }, line: { color: theme.accent, width: 1 } }));
  });
  slide.addShape(SHAPE.chevron, { x: 5.45, y: 3.15, w: 0.55, h: 0.75, fill: { color: theme.accent }, line: { color: theme.accent } });
  addText(slide, "STATE\nUPDATE", 5.28, 4.02, 0.9, 0.65, 8, theme.muted, { fontFace: MONO, bold: true, align: "center" });
  addText(slide, "证据绑定：Static graph 消融在 60 min 上由 3.31 退化到 3.46。", 1.15, 6.2, 10.2, 0.4, 11, theme.ink, { bold: true, align: "center" });
  addNotes(slide, ["ablation-static", "ablation-full"]);
}

function multiScaleSlide(pptx, theme, index) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Module / Multi-Scale", "一个感受野不足以同时解释局部扰动与长程周期", index);
  const center = { x: 3.25, y: 3.92 };
  [3.15, 2.18, 1.22].forEach((diameter, i) => {
    slide.addShape(SHAPE.ellipse, {
      x: center.x - diameter / 2, y: center.y - diameter / 2,
      w: diameter, h: diameter,
      fill: { color: i === 2 ? theme.accent : theme.surface, transparency: i === 2 ? 0 : 100 },
      line: { color: i === 0 ? theme.muted : i === 1 ? theme.ink : theme.accent, width: 2.2, dash: i === 0 ? "dash" : "solid" },
    });
  });
  addText(slide, "NODE", 2.84, 3.72, 0.82, 0.32, 10, theme.bg, { fontFace: MONO, bold: true, align: "center" });
  const scales = [
    ["LOCAL", "相邻节点 / 短时扰动", "快速、具体"],
    ["REGIONAL", "区域传播 / 中程关联", "连接走廊"],
    ["GLOBAL", "跨区依赖 / 长程周期", "保持全局"],
  ];
  scales.forEach((item, i) => {
    const y = 1.9 + i * 1.42;
    slide.addShape(SHAPE.roundRect, { x: 6.15, y, w: 5.7, h: 1.05, fill: { color: i === 1 ? theme.ink : theme.surface }, line: { color: i === 1 ? theme.ink : theme.pale } });
    addText(slide, item[0], 6.45, y + 0.18, 1.35, 0.28, 8, theme.accent, { fontFace: MONO, bold: true });
    addText(slide, item[1], 7.8, y + 0.15, 2.75, 0.34, 13, i === 1 ? theme.bg : theme.ink, { bold: true });
    addText(slide, item[2], 10.55, y + 0.18, 0.9, 0.28, 8, i === 1 ? theme.pale : theme.muted, { fontFace: MONO, align: "right" });
  });
  addText(slide, "No-multiscale 消融：60 min MAE 由 3.31 退化至 3.42。", 6.18, 6.15, 5.6, 0.42, 11, theme.ink, { bold: true });
  addNotes(slide, ["ablation-scale", "ablation-full"]);
}

function efficiencyScatterSlide(pptx, theme, index, brief) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Complexity / Design Choice", "精度之外，参数量与延迟共同进入方法选择", index);
  slide.addShape(SHAPE.roundRect, { x: 0.72, y: 1.8, w: 8.55, h: 4.72, fill: { color: theme.surface }, line: { color: theme.pale } });
  slide.addShape(SHAPE.line, { x: 1.55, y: 5.72, w: 6.75, h: 0, line: { color: theme.ink, width: 1.4, endArrowType: "triangle" } });
  slide.addShape(SHAPE.line, { x: 1.55, y: 5.72, w: 0, h: -3.2, line: { color: theme.ink, width: 1.4, endArrowType: "triangle" } });
  addText(slide, "参数量 / M →", 6.85, 5.92, 1.45, 0.28, 8, theme.muted, { fontFace: MONO, align: "right" });
  addText(slide, "延迟 / ms ↑", 0.84, 2.12, 1.3, 0.28, 8, theme.muted, { fontFace: MONO });
  const points = [
    { x: 3.0, y: 4.5, label: "GWN", value: `${val(brief, "params-gwn")}M / ${val(brief, "latency-gwn")}ms`, color: theme.good },
    { x: 4.25, y: 3.75, label: "OURS", value: `${val(brief, "params-ours")}M / ${val(brief, "latency-ours")}ms`, color: theme.accent },
    { x: 6.75, y: 2.85, label: "STFGNN", value: `${val(brief, "params-stfgnn")}M / ${val(brief, "latency-stfgnn")}ms`, color: theme.muted },
  ];
  points.forEach((point, i) => {
    slide.addShape(SHAPE.ellipse, { x: point.x, y: point.y, w: i === 1 ? 0.62 : 0.45, h: i === 1 ? 0.62 : 0.45, fill: { color: point.color }, line: { color: theme.bg, width: 2 } });
    addText(slide, point.label, point.x - 0.18, point.y - 0.42, 1.0, 0.28, 9, theme.ink, { fontFace: MONO, bold: true, align: "center" });
    addText(slide, point.value, point.x - 0.45, point.y + 0.58, 1.55, 0.28, 8, theme.muted, { fontFace: MONO, align: "center" });
  });
  slide.addShape(SHAPE.roundRect, { x: 9.62, y: 1.8, w: 3.0, h: 4.72, fill: { color: theme.ink }, line: { color: theme.ink } });
  addText(slide, "DESIGN CHOICE", 9.95, 2.18, 2.3, 0.28, 8, theme.accent, { fontFace: MONO, bold: true });
  addText(slide, "3.18M\n10.6ms", 9.95, 2.82, 2.2, 1.05, 25, theme.bg, { bold: true });
  addText(slide, "位于轻量基线与更重结构之间；不声称绝对最优效率。", 9.95, 4.35, 2.18, 1.1, 11, theme.pale);
  addNotes(slide, ["params-ours", "latency-ours", "params-gwn", "latency-gwn", "params-stfgnn", "latency-stfgnn"]);
}

function businessModelSlide(pptx, theme, index, brief) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, "Business Model", "硬件 + 年服务：以可维护性而不是一次性销售为核心", index);
  const layers = [
    { tag: "BUILD", title: "硬件 BOM", value: `¥${val(brief, "bom")}`, detail: "传感 + 边缘节点 · 持续降本" },
    { tag: "DELIVER", title: "建议售价", value: `¥${val(brief, "price")}`, detail: "安装 + 设备使用 · 交付质量" },
    { tag: "SERVE", title: "年服务费", value: `¥${val(brief, "service-fee")}/年`, detail: "平台 + 升级 + 运维支持" },
  ];
  layers.forEach((item, i) => {
    const x = 0.72 + i * 4.02;
    slide.addShape(SHAPE.roundRect, { x, y: 2.0 + i * 0.28, w: 3.72, h: 3.42 - i * 0.28, fill: { color: i === 2 ? theme.ink : theme.surface }, line: { color: i === 2 ? theme.accent : theme.pale, width: 1.2 } });
    addText(slide, item.tag, x + 0.28, 2.28 + i * 0.28, 2.8, 0.28, 8, theme.accent, { fontFace: MONO, bold: true });
    addText(slide, item.title, x + 0.28, 2.82 + i * 0.28, 2.9, 0.42, 15, i === 2 ? theme.bg : theme.ink, { bold: true });
    addText(slide, item.value, x + 0.28, 3.45 + i * 0.28, 3.0, 0.62, 25, i === 2 ? theme.bg : theme.ink, { bold: true });
    addText(slide, item.detail, x + 0.28, 4.36 + i * 0.28, 2.95, 0.66, 10, i === 2 ? theme.pale : theme.muted);
    if (i < 2) slide.addShape(SHAPE.chevron, { x: x + 3.55, y: 3.45, w: 0.55, h: 0.72, fill: { color: theme.accent }, line: { color: theme.accent } });
  });
  addText(slide, "商业判断：一次性交付建立入口，持续服务承担长期价值与维护责任。", 0.75, 6.25, 11.5, 0.42, 11, theme.ink, { bold: true });
  addNotes(slide, ["bom", "price", "service-fee"]);
}

function workCaseSlide(pptx, theme, index, variant, brief) {
  const slide = pptx.addSlide("V6_BODY");
  if (variant === "migration") {
    addTitle(slide, theme, "Case 01 / Migration", "客户迁移：从高风险切换，变成分批可回退工程", index);
    const steps = [
      ["DISCOVER", "识别关键路径", "锁定切换窗口、回退点与责任人"],
      ["PILOT", "先迁高价值低耦合", "用成功样板建立标准作业"],
      ["SCALE", "尾部透明管理", "剩余客户进入专项方案"],
    ];
    slide.addShape(SHAPE.line, { x: 1.28, y: 3.75, w: 7.45, h: 0, line: { color: theme.accent, width: 3, endArrowType: "triangle" } });
    steps.forEach((step, i) => {
      const x = 1.0 + i * 3.05;
      slide.addShape(SHAPE.ellipse, { x, y: 3.25, w: 1.0, h: 1.0, fill: { color: i === 2 ? theme.ink : theme.surface }, line: { color: theme.accent, width: 2 } });
      addText(slide, `0${i + 1}`, x + 0.23, 3.5, 0.54, 0.36, 12, i === 2 ? theme.bg : theme.ink, { fontFace: MONO, bold: true, align: "center" });
      addText(slide, step[0], x - 0.35, 2.2, 1.7, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, align: "center" });
      addText(slide, step[1], x - 0.55, 2.58, 2.1, 0.42, 13, theme.ink, { bold: true, align: "center" });
      addText(slide, step[2], x - 0.55, 4.55, 2.1, 0.62, 9.5, theme.muted, { align: "center" });
    });
    slide.addShape(SHAPE.roundRect, { x: 10.02, y: 1.9, w: 2.4, h: 4.25, fill: { color: theme.ink }, line: { color: theme.ink } });
    addText(slide, `${val(brief, "unmigrated-customers")}`, 10.38, 2.55, 1.7, 0.85, 34, theme.bg, { bold: true, align: "center" });
    addText(slide, "TAIL CLIENTS", 10.38, 3.45, 1.7, 0.3, 8, theme.accent, { fontFace: MONO, bold: true, align: "center" });
    addText(slide, "可信度来自尾部透明，而不是只展示总体完成率。", 10.38, 4.25, 1.7, 1.1, 11, theme.pale, { align: "center" });
    addNotes(slide, ["unmigrated-customers"]);
  } else if (variant === "adoption") {
    addTitle(slide, theme, "Case 02 / Self Service", "自助分析：把“会用工具”升级为“能做决定”", index);
    slide.addShape(SHAPE.roundRect, { x: 0.72, y: 1.82, w: 4.1, h: 4.55, fill: { color: theme.ink }, line: { color: theme.ink } });
    slide.addChart(CHART.doughnut, [{ name: "acceptance", labels: ["accepted", "remaining"], values: [val(brief, "acceptance-rate"), 100 - val(brief, "acceptance-rate")] }], {
      x: 1.25, y: 2.18, w: 3.0, h: 2.65, holeSize: 72, showLegend: false, showValue: false,
      chartColors: [theme.accent, theme.muted], showBorder: false,
    });
    addText(slide, `${val(brief, "acceptance-rate")}%`, 1.83, 3.05, 1.85, 0.65, 28, theme.bg, { bold: true, align: "center" });
    addText(slide, "ACCEPTANCE", 1.82, 3.75, 1.9, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, align: "center" });
    addText(slide, `${val(brief, "governed-metrics")} 项治理指标成为统一事实入口`, 1.2, 5.15, 3.1, 0.55, 11, theme.pale, { align: "center" });
    const stages = [
      ["01", "业务问题", "以决策场景组织"],
      ["02", "指标证据", "口径与责任前置"],
      ["03", "使用反馈", "反哺产品路线图"],
    ];
    stages.forEach((item, i) => {
      const y = 1.92 + i * 1.42;
      slide.addShape(SHAPE.roundRect, { x: 5.2, y, w: 6.92, h: 1.06, fill: { color: i === 2 ? theme.pale : theme.surface }, line: { color: theme.pale } });
      addText(slide, item[0], 5.5, y + 0.23, 0.52, 0.3, 10, theme.accent, { fontFace: MONO, bold: true });
      addText(slide, item[1], 6.25, y + 0.18, 1.75, 0.36, 14, theme.ink, { bold: true });
      addText(slide, item[2], 8.3, y + 0.2, 3.25, 0.34, 11, theme.muted);
    });
    addText(slide, `Q4 自助分析率 ${val(brief, "self-service-actual")}%：下一步从“使用”转向“决策质量”。`, 5.22, 6.02, 6.85, 0.38, 11, theme.ink, { bold: true });
    addNotes(slide, ["governed-metrics", "acceptance-rate", "self-service-actual"]);
  } else {
    addTitle(slide, theme, "Case 03 / Cost", "查询成本：在使用增长时仍实现单位成本下降", index);
    slide.addShape(SHAPE.roundRect, { x: 0.72, y: 1.82, w: 8.1, h: 4.55, fill: { color: theme.surface }, line: { color: theme.pale } });
    slide.addChart(CHART.bar, [{ name: "每千次查询成本", labels: ["Q1", "Q4"], values: [val(brief, "query-cloud-cost-q1"), val(brief, "query-cloud-cost-q4")] }], {
      x: 1.08, y: 2.18, w: 7.3, h: 3.7, showLegend: false, showTitle: false,
      showValue: true, dataLabelFormatCode: "0.0", chartColors: [theme.accent],
      catAxisLabelFontFace: MONO, catAxisLabelFontSize: 10,
      valAxisLabelFontFace: MONO, valAxisLabelFontSize: 9,
      showValAxisTitle: true, valAxisTitle: "成本 / 元", valAxisTitleFontSize: 8,
      showCatAxisTitle: true, catAxisTitle: "每千次查询", catAxisTitleFontSize: 8,
      valGridLine: { color: theme.pale, width: 1 }, showBorder: false,
    });
    slide.addShape(SHAPE.roundRect, { x: 9.12, y: 1.82, w: 3.5, h: 4.55, fill: { color: theme.ink }, line: { color: theme.ink } });
    addText(slide, "−27%", 9.52, 2.35, 2.65, 0.82, 31, theme.bg, { bold: true });
    addText(slide, "UNIT COST", 9.52, 3.2, 2.4, 0.3, 8, theme.accent, { fontFace: MONO, bold: true });
    [["可用性", `${val(brief, "availability-q4")}%`], ["报告 SLA", `${val(brief, "report-sla-q4")}%`]].forEach((item, i) => {
      addText(slide, item[0], 9.52, 4.02 + i * 0.72, 1.4, 0.3, 10, theme.pale);
      addText(slide, item[1], 10.95, 3.95 + i * 0.72, 1.1, 0.4, 14, theme.bg, { bold: true, align: "right" });
    });
    addText(slide, "成本下降必须与可用性、SLA 同页解释。", 9.52, 5.55, 2.55, 0.52, 10, theme.pale);
    addNotes(slide, ["query-cloud-cost-q1", "query-cloud-cost-q4", "availability-q4", "report-sla-q4"]);
  }
}

function qaSlide(pptx, theme, index, label, question, answer, variant) {
  const slide = pptx.addSlide("V6_BODY");
  addTitle(slide, theme, `Q&A Backup / ${label}`, question, index);
  if (variant === 0) {
    slide.addShape(SHAPE.roundRect, { x: 0.72, y: 1.85, w: 7.2, h: 4.35, fill: { color: theme.surface }, line: { color: theme.pale } });
    addText(slide, "SHORT ANSWER", 1.05, 2.18, 2.2, 0.28, 8, theme.accent, { fontFace: MONO, bold: true });
    addText(slide, answer, 1.05, 2.72, 6.25, 1.35, 21, theme.ink, { bold: true });
    addText(slide, "边界：若问题超出锁定事实，现场记录为待验证，不即兴补数。", 1.05, 4.72, 6.2, 0.7, 11, theme.muted);
    slide.addShape(SHAPE.roundRect, { x: 8.22, y: 1.85, w: 4.4, h: 4.35, fill: { color: theme.ink }, line: { color: theme.ink } });
    addText(slide, "EVIDENCE", 8.62, 2.2, 2.2, 0.28, 8, theme.accent, { fontFace: MONO, bold: true });
    ["主 deck 已呈现", "数字来自锁定事实", "限制条件明确"].forEach((text, i) => addText(slide, `0${i + 1}  ${text}`, 8.62, 2.9 + i * 0.72, 3.2, 0.42, 12, theme.bg, { bold: i === 0 }));
  } else if (variant === 1) {
    slide.addShape(SHAPE.roundRect, { x: 0.72, y: 1.85, w: 11.9, h: 1.42, fill: { color: theme.ink }, line: { color: theme.ink } });
    addText(slide, answer, 1.05, 2.14, 11.1, 0.82, 20, theme.bg, { bold: true, align: "center" });
    ["WHAT WE KNOW", "WHAT WE DO NOT CLAIM", "NEXT PROOF"].forEach((text, i) => {
      const x = 0.72 + i * 4.02;
      slide.addShape(SHAPE.roundRect, { x, y: 3.62, w: 3.75, h: 2.22, fill: { color: i === 1 ? theme.pale : theme.surface }, line: { color: theme.pale } });
      addText(slide, text, x + 0.25, 3.92, 3.15, 0.3, 8, theme.accent, { fontFace: MONO, bold: true });
      addText(slide, i === 0 ? "锁定事实与试点证据" : i === 1 ? "不外推规模与因果" : "进入下一阶段验证", x + 0.25, 4.45, 3.15, 0.72, 13, theme.ink, { bold: true });
    });
  } else if (variant === 2) {
    const steps = [["01", "先给结论"], ["02", "再给证据"], ["03", "明确边界"]];
    steps.forEach((item, i) => {
      const x = 0.8 + i * 4.05;
      slide.addShape(SHAPE.ellipse, { x, y: 2.05, w: 1.0, h: 1.0, fill: { color: i === 0 ? theme.accent : theme.ink }, line: { color: theme.accent, width: 2 } });
      addText(slide, item[0], x + 0.24, 2.28, 0.52, 0.4, 13, i === 0 ? theme.bg : theme.accent, { fontFace: MONO, bold: true, align: "center" });
      addText(slide, item[1], x - 0.1, 3.22, 1.2, 0.42, 12, theme.ink, { bold: true, align: "center" });
      if (i < 2) slide.addShape(SHAPE.line, { x: x + 1.18, y: 2.55, w: 2.75, h: 0, line: { color: theme.accent, width: 2, endArrowType: "triangle" } });
    });
    slide.addShape(SHAPE.roundRect, { x: 1.42, y: 4.25, w: 10.5, h: 1.45, fill: { color: theme.surface }, line: { color: theme.pale } });
    addText(slide, answer, 1.78, 4.52, 9.8, 0.88, 18, theme.ink, { bold: true, align: "center" });
  } else if (variant === 3) {
    addText(slide, "ANSWER", 0.86, 2.05, 1.2, 0.28, 9, theme.accent, { fontFace: MONO, bold: true });
    addText(slide, answer, 0.86, 2.5, 7.2, 1.5, 23, theme.ink, { bold: true });
    slide.addShape(SHAPE.line, { x: 0.88, y: 4.42, w: 7.1, h: 0, line: { color: theme.accent, width: 3 } });
    ["锁定事实", "采购验证", "不外推"].forEach((text, i) => {
      const y = 2.04 + i * 1.18;
      slide.addShape(SHAPE.ellipse, { x: 9.15, y, w: 0.78, h: 0.78, fill: { color: i === 0 ? theme.accent : theme.ink }, line: { color: theme.accent, width: 1.5 } });
      addText(slide, `0${i + 1}`, 9.3, y + 0.2, 0.48, 0.28, 9, i === 0 ? theme.bg : theme.accent, { fontFace: MONO, bold: true, align: "center" });
      addText(slide, text, 10.18, y + 0.2, 1.75, 0.3, 13, theme.ink, { bold: true });
    });
  } else if (variant === 4) {
    slide.addShape(SHAPE.roundRect, { x: 0.78, y: 1.88, w: 3.1, h: 4.2, fill: { color: theme.ink }, line: { color: theme.ink } });
    addText(slide, "RISK", 1.12, 2.24, 1.4, 0.28, 9, theme.accent, { fontFace: MONO, bold: true });
    addText(slide, "维护负担\n拖垮团队", 1.12, 3.02, 2.3, 1.0, 23, theme.bg, { bold: true });
    addText(slide, "不是售后问题，\n而是验证门槛。", 1.12, 4.62, 2.25, 0.72, 13, theme.pale, { bold: true });
    ["校准纳入验收", "耗材纳入成本", "故障自检纳入产品"].forEach((text, i) => {
      const y = 2.08 + i * 1.25;
      slide.addShape(SHAPE.roundRect, { x: 4.4, y, w: 7.65, h: 0.9, fill: { color: i === 2 ? theme.accent : theme.surface }, line: { color: i === 2 ? theme.accent : theme.pale } });
      addText(slide, `0${i + 1}`, 4.7, y + 0.22, 0.55, 0.3, 10, i === 2 ? theme.bg : theme.accent, { fontFace: MONO, bold: true });
      addText(slide, text, 5.48, y + 0.18, 2.62, 0.34, 14, i === 2 ? theme.bg : theme.ink, { bold: true });
      addText(slide, i === 0 ? "验证维护频次" : i === 1 ? "记录真实负担" : "提前发现故障", 8.48, y + 0.22, 3.0, 0.3, 11, i === 2 ? theme.bg : theme.muted, { align: "right" });
    });
  } else {
    slide.addShape(SHAPE.roundRect, { x: 0.76, y: 1.9, w: 11.85, h: 1.55, fill: { color: theme.accent }, line: { color: theme.accent } });
    addText(slide, answer, 1.12, 2.22, 11.12, 0.82, 21, theme.bg, { bold: true, align: "center" });
    const gates = [["01", "完整性"], ["02", "告警质量"], ["03", "巡检工时"]];
    gates.forEach((item, i) => {
      const x = 1.08 + i * 4.0;
      slide.addShape(SHAPE.chevron, { x, y: 4.08, w: 3.45, h: 1.35, fill: { color: i === 2 ? theme.ink : theme.surface }, line: { color: i === 2 ? theme.ink : theme.pale } });
      addText(slide, item[0], x + 0.28, 4.38, 0.55, 0.3, 10, i === 2 ? theme.accent : theme.muted, { fontFace: MONO, bold: true });
      addText(slide, item[1], x + 1.0, 4.32, 1.82, 0.4, 15, i === 2 ? theme.bg : theme.ink, { bold: true });
    });
  }
  addNotes(slide);
}

function closingAligned(pptx, theme, index, title, statement, meta, motif = "radial") {
  const slide = pptx.addSlide();
  slide.background = { color: theme.bg };
  addMotif(slide, theme, motif, 2);
  slide.addShape(SHAPE.rect, { x: 0, y: 0, w: 0.22, h: H, fill: { color: theme.accent }, line: { color: theme.accent } });
  addText(slide, "THE DECISION STARTS NOW", 0.88, 0.82, 4.5, 0.3, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.2 });
  addText(slide, title, 0.88, 1.92, 8.8, 1.12, 38, theme.ink, { bold: true });
  addText(slide, statement, 0.9, 3.48, 7.8, 0.82, 16, theme.muted);
  slide.addShape(SHAPE.roundRect, { x: 8.92, y: 1.55, w: 3.32, h: 3.95, fill: { color: theme.ink }, line: { color: theme.ink } });
  addText(slide, "GO / NO-GO", 9.35, 2.0, 2.5, 0.3, 8, theme.accent, { fontFace: MONO, bold: true });
  addText(slide, "下一轮\n验证", 9.35, 2.75, 2.45, 1.35, 27, theme.bg, { bold: true });
  addText(slide, meta, 0.9, 5.85, 7.6, 0.48, 10, theme.muted);
  addText(slide, String(index).padStart(2, "0"), 11.18, 6.2, 1.1, 0.62, 20, theme.accent, { fontFace: MONO, bold: true, align: "right" });
  addNotes(slide);
}

function closing(pptx, theme, index, title, statement, meta, motif = "radial") {
  const slide = pptx.addSlide();
  slide.background = { color: theme.ink };
  addMotif(slide, theme, motif, 2);
  addText(slide, "THE DECISION STARTS NOW", 0.85, 0.85, 4.5, 0.3, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.2 });
  addText(slide, title, 0.85, 2.0, 8.3, 1.0, 38, theme.bg, { bold: true });
  addText(slide, statement, 0.88, 3.5, 7.3, 0.75, 16, theme.pale);
  slide.addShape(SHAPE.line, { x: 0.88, y: 5.65, w: 2.0, h: 0, line: { color: theme.accent, width: 3 } });
  addText(slide, meta, 0.88, 5.9, 7.0, 0.4, 10, theme.pale);
  addText(slide, String(index).padStart(2, "0"), 11.45, 6.35, 1.15, 0.6, 20, theme.accent, { fontFace: MONO, bold: true, align: "right" });
  addNotes(slide);
}

function buildWork(brief) {
  const t = themes.work, pptx = newDeck(t);
  cover(pptx, t, 1, "2026 · OPERATING REVIEW", t.title, t.subtitle, "经营委员会 · 2026.12 · 32 PAGES");
  agenda(pptx, t, [
    ["年度答卷", "目标兑现、增长质量与经营边界"],
    ["价值落地", "产品、治理与三个客户案例"],
    ["组织能力", "交付机制、团队与风险"],
    ["明年行动", "优先级、路线图与待批准事项"],
  ]);
  const executive = metricCards(pptx, t, 3, "Executive Summary", "四个数字，定义这一年的经营质量", [
    { label: "CUSTOMERS", value: val(brief, "customers-actual"), unit: "家", detail: `目标 ${val(brief, "customers-target")} 家，完成率 104%` },
    { label: "SELF SERVICE", value: `${val(brief, "self-service-actual")}%`, unit: "使用渗透", detail: `较目标高 ${val(brief, "self-service-actual") - val(brief, "self-service-target")} 个百分点` },
    { label: "AVAILABILITY", value: `${val(brief, "availability-q4")}%`, unit: "Q4", detail: "稳定性提升与事故下降同步发生" },
    { label: "ANNUAL SAVING", value: `¥${val(brief, "annual-savings")}M`, unit: "财务确认估算", detail: "边界：年度化估算，不等于回款收入" },
  ], "结论：增长、使用与稳定性三条曲线同向改善，但迁移尾部与指标责任仍需明年攻坚。",
  ["customers-actual", "customers-target", "self-service-actual", "self-service-target", "availability-q4", "annual-savings"]);
  addMiniDonut(executive, t, 2.05, 4.72, val(brief, "customers-actual"), val(brief, "customers-target"), "客户目标");
  section(pptx, t, 1, "年度答卷", "不只回答“做了多少”，更回答“为什么值得继续投入”。");
  const scorecard = metricCards(pptx, t, 5, "Annual Scorecard", "目标兑现不是平均主义：四项领先，一项需追赶", [
    { label: "CUSTOMERS", value: "104%", unit: "94 / 90", detail: "客户规模超目标 4 家" },
    { label: "SELF SERVICE", value: "105%", unit: "68 / 65", detail: "从被动报表走向自主分析" },
    { label: "PROJECTS", value: "83%", unit: "10 / 12", detail: "两项跨系统依赖造成延期" },
    { label: "NPS", value: "107%", unit: "45 / 42", detail: "案例共创提高续约信心" },
  ], "管理含义：2027 年不能只追加项目，必须同步治理跨系统依赖。",
  ["customers-target", "customers-actual", "self-service-target", "self-service-actual", "projects-on-time", "projects-total", "nps-target", "nps-actual"]);
  addMiniDonut(scorecard, t, 2.05, 4.72, val(brief, "projects-on-time"), val(brief, "projects-total"), "按期项目");
  customerGrowthTargetSlide(pptx, t, 6);
  lineChart(pptx, t, 7, "Adoption / MAU", "月活从 1,840 增至 4,260，使用深度追上客户扩张", [
    { name: "月活用户", labels: ["Q1", "Q2", "Q3", "Q4"], values: [1840, 2320, 3080, 4260] },
  ], { value: "4,260", label: "Q4 MONTHLY ACTIVE", detail: "较 Q1 增加 2,420 人，采用曲线持续加速。", axisTitle: "月活用户 / 人", catTitle: "季度" },
  ["monthly-active-users-q1", "monthly-active-users-q2", "monthly-active-users-q3", "monthly-active-users-q4"]);
  selfServiceTargetSlide(pptx, t, 8);
  lineChart(pptx, t, 9, "Reliability / SLA", "交付 SLA 与系统可用性同步改善", [
    { name: "报表 SLA", labels: ["Q1", "Q2", "Q3", "Q4"], values: [89, 92, 95, 97] },
    { name: "可用性", labels: ["Q1", "Q2", "Q3", "Q4"], values: [99.82, 99.88, 99.92, 99.95] },
  ], { value: "97%", label: "REPORT SLA / Q4", detail: "高可用不再只是技术指标，而是交付承诺。", axisTitle: "SLA 达成率 / %", catTitle: "季度" },
  ["report-sla-q1", "report-sla-q2", "report-sla-q3", "report-sla-q4", "availability-q1", "availability-q2", "availability-q3", "availability-q4"]);
  section(pptx, t, 2, "价值落地", "把增长解释为可复用的方法，而不是偶然的项目堆叠。");
  comparisonSlide(pptx, t, 11, "Governance / Before & After", "指标治理把重复口径从 126 项压缩到 41 项",
    { label: "BEFORE", title: "指标多，但不可复用", items: ["126 项重复指标", "口径归属不清", "跨团队重复核对"] },
    { label: "AFTER", title: "38 项核心指标受治理", items: ["重复指标降至 41 项", "责任与变更路径明确", "周查询 2,140 次"] },
    "治理不是后台工程：它直接减少解释成本，支撑自助分析扩张。",
    ["duplicates-before", "duplicates-after", "governed-metrics", "weekly-queries"]);
  processSlide(pptx, t, 12, "Delivery System", "从需求到价值：四步闭环替代一次性交付", [
    ["定义问题", "把决策、用户与成功标准写入需求"],
    ["统一口径", "事实、指标、权限与责任一次锁定"],
    ["共创验证", "用真实使用行为而非演示反馈验收"],
    ["运营复盘", "SLA、采用、成本和风险进入同一看板"],
  ], "结果：10/12 项目按期，延期来源可被定位为跨系统依赖，而非团队失控。",
  ["projects-on-time", "projects-total"]);
  workCaseSlide(pptx, t, 13, "migration", brief);
  workCaseSlide(pptx, t, 14, "adoption", brief);
  workCaseSlide(pptx, t, 15, "cost", brief);
  lineChart(pptx, t, 16, "Reliability / Incident", "P1 事故从 6 起降至 2 起，稳定性改善可验证", [
    { name: "P1 事故", labels: ["Q1", "Q2", "Q3", "Q4"], values: [6, 4, 3, 2] },
  ], { value: "−67%", label: "INCIDENT REDUCTION", detail: "事故下降与可用性上升同向，说明治理有效。", axisTitle: "P1 事故 / 起", catTitle: "季度" },
  ["p1-incidents-q1", "p1-incidents-q2", "p1-incidents-q3", "p1-incidents-q4"]);
  section(pptx, t, 3, "组织能力", "优秀结果不是英雄主义，而是结构、机制与透明度共同作用。");
  processSlide(pptx, t, 18, "Operating Model", "一个目标，四个责任环：事实与交付不再失联", [
    ["经营委员会", "批准优先级与资源边界"],
    ["业务 Owner", "定义问题、成功与采用"],
    ["数据产品", "组织口径、体验与节奏"],
    ["平台团队", "保障性能、安全与可用性"],
  ], "组织机制的核心不是更多会议，而是把每个指标和决定绑定到负责人。");
  const economics = metricCards(pptx, t, 19, "Efficiency / Economics", "规模扩大，但预算与单位成本保持受控", [
    { label: "BUDGET", value: "¥11.6M", unit: "实际", detail: "低于 12M 年度计划" },
    { label: "QUERY COST", value: "¥6.1", unit: "每千次", detail: "较 Q1 下降 2.3 元" },
    { label: "SAVING", value: "¥2.8M", unit: "年度化估算", detail: "经财务确认，非回款收入" },
  ], "经营边界：节省是效率证据，不应被包装成新增收入。", ["budget-plan", "budget-actual", "query-cloud-cost-q1", "query-cloud-cost-q4", "annual-savings", "work-boundary"]);
  addMiniDonut(economics, t, 2.42, 4.72, val(brief, "budget-actual"), val(brief, "budget-plan"), "预算执行");
  cardsSlide(pptx, t, 20, "Customer Success", "增长的下一步：把高采用机制复制到每一类客户", [
    { tag: "SIGNAL", title: "行为领先于问卷", detail: "以周查询、月活和自助率识别真实采用。" },
    { tag: "PLAYBOOK", title: "三类客户三套路径", detail: "新客户、迁移客户、成熟客户使用不同动作。" },
    { tag: "LOOP", title: "反馈回到路线图", detail: "接受率与业务问题共同决定产品优先级。" },
  ], "NPS 45 分是结果，不是终点；需要与行为指标共同管理。", ["nps-actual", "weekly-queries", "acceptance-rate"]);
  cardsSlide(pptx, t, 21, "Team & Recognition", "团队荣誉页：展示能力组合，而不是头像墙", [
    { tag: "PRODUCT", title: "业务翻译", detail: "把决策问题转译为产品与数据需求。" },
    { tag: "DATA", title: "治理与分析", detail: "统一事实、指标、模型和解释边界。" },
    { tag: "PLATFORM", title: "可靠性交付", detail: "性能、安全、成本与可用性一体化。" },
    { tag: "SUCCESS", title: "客户采用", detail: "共创、培训、运营与价值复盘闭环。" },
    { tag: "PMO", title: "节奏与依赖", detail: "跨团队风险透明、路径可回退。" },
    { tag: "FINANCE", title: "价值确认", detail: "所有节省与预算口径可追溯。" },
  ], "荣誉只作为结果注脚；能力组合才是明年复制的基础。");
  matrixSlide(pptx, t, 22, "Risk Portfolio", "风险必须进入优先级，而不是留在附录", [
    { x: 6.6, y: 2.42, w: 3.2, h: 1.22, title: "17 项无责任指标", detail: "高影响 / 高紧迫：立即明确 Owner 与下线策略" },
    { x: 2.05, y: 2.65, w: 2.9, h: 1.02, title: "3 家未迁移客户", detail: "高影响 / 可控：专项方案与回退窗口" },
    { x: 6.9, y: 4.45, w: 2.75, h: 0.96, title: "跨系统依赖", detail: "影响交付节奏，进入季度治理" },
    { x: 2.5, y: 4.52, w: 2.45, h: 0.88, title: "成本反弹", detail: "低概率，持续监控" },
  ], { x: "紧迫性 →", y: "影响度 ↑" }, ["unowned-metrics", "unmigrated-customers"]);
  section(pptx, t, 4, "明年行动", "资源不平均分配：聚焦治理、迁移和自助分析三个杠杆。");
  cardsSlide(pptx, t, 24, "2027 Priorities", "三项优先级共同指向：更可信、更可迁移、更自主", [
    { tag: "P1 / GOVERN", title: "治理责任闭环", detail: "解决 17 项无责任指标；建立变更、下线和审计机制。" },
    { tag: "P2 / MIGRATE", title: "客户迁移收口", detail: "完成剩余 3 家复杂客户迁移；保留可回退路径。" },
    { tag: "P3 / ADOPT", title: "自助分析深化", detail: "从 68% 使用率走向决策质量与场景覆盖。" },
  ], "三项投入不是并列项目：治理是底座，迁移释放规模，自助分析兑现价值。",
  ["unowned-metrics", "unmigrated-customers", "self-service-actual"]);
  processSlide(pptx, t, 25, "Roadmap / 2027", "四个季度，把优先级变成可验收里程碑", [
    ["Q1 · 定责", "清理无责任指标；锁定三家迁移方案"],
    ["Q2 · 迁移", "完成复杂客户首批切换与回退演练"],
    ["Q3 · 深化", "扩展自助分析场景与决策质量评估"],
    ["Q4 · 复制", "形成可复用治理与采用方法包"],
  ], "每季验收同时看事实治理、客户连续性与使用行为，避免单维度完成。");
  tableSlide(pptx, t, 26, "Investment / Guardrails", "资源分配以结果和边界为依据", ["投入方向", "为什么现在", "首要验收", "停止条件"], [
    ["数据治理", "17 项指标无责任", "责任覆盖与重复口径下降", "无业务 Owner 不扩建"],
    ["客户迁移", "剩余 3 家复杂客户", "切换成功且可回退", "连续性风险不可控则暂停"],
    ["自助分析", "68% 使用率已有基础", "场景覆盖与决策质量", "只有培训次数、无行为改善则调整"],
  ], "本页不承诺未锁定预算金额；仅定义批准后的投入逻辑与停止条件。",
  ["unowned-metrics", "unmigrated-customers", "self-service-actual"]);
  cardsSlide(pptx, t, 27, "Decision Ask", "本次会议需要批准的，不是 PPT，而是三个投入优先级", [
    { tag: "APPROVE 01", title: "治理优先", detail: "把责任、口径和变更机制列为底座投入。" },
    { tag: "APPROVE 02", title: "迁移收口", detail: "为三家复杂客户配置专项跨团队资源。" },
    { tag: "APPROVE 03", title: "采用深化", detail: "将自助分析从使用率推进到决策质量。" },
  ], factText(brief, "presentation-decision"), ["presentation-decision"]);
  closing(pptx, t, 28, "让增长成为可复制能力", "2026 证明方向成立；2027 要证明方法可以规模化。", "请批准：治理 → 迁移 → 自助分析 的投入顺序");
  tableSlide(pptx, t, 29, "Appendix A / KPI", "季度指标明细", ["指标", "Q1", "Q2", "Q3", "Q4"], [
    ["客户数", 46, 59, 76, 94],
    ["月活用户", 1840, 2320, 3080, 4260],
    ["自助分析率", "38%", "46%", "57%", "68%"],
    ["报表 SLA", "89%", "92%", "95%", "97%"],
    ["P1 事故", 6, 4, 3, 2],
    ["可用性", "99.82%", "99.88%", "99.92%", "99.95%"],
  ], "所有指标均来自锁定评测事实；无模型补数。",
  ["customer-count-q1", "customer-count-q2", "customer-count-q3", "customer-count-q4", "monthly-active-users-q1", "monthly-active-users-q2", "monthly-active-users-q3", "monthly-active-users-q4"]);
  tableSlide(pptx, t, 30, "Appendix B / Budget", "年度预算与价值边界", ["项目", "计划/基线", "实际/结果", "解释边界"], [
    ["年度预算", "12.0 百万元", "11.6 百万元", "预算内交付"],
    ["查询成本", "Q1 8.4 元/千次", "Q4 6.1 元/千次", "单位成本下降"],
    ["年度节省", "—", "2.8 百万元", "年度化估算，不等于收入"],
  ], factText(brief, "work-boundary"), ["budget-plan", "budget-actual", "query-cloud-cost-q1", "query-cloud-cost-q4", "annual-savings", "work-boundary"]);
  tableSlide(pptx, t, 31, "Appendix C / Definitions", "关键口径与事实责任", ["口径", "本报告定义", "责任"], [
    ["客户数", "当季活跃付费客户", "客户成功 / 财务"],
    ["自助分析率", "无需人工出数即可完成分析的活跃用户占比", "数据产品"],
    ["报表 SLA", "约定时限内交付比例", "平台 / 交付"],
    ["年度节省", "经财务确认的年度化估算", "财务"],
  ], "口径定义用于解释，不新增锁定事实值。");
  tableSlide(pptx, t, 32, "Appendix D / Evidence Index", "证据与可编辑对象索引", ["页码", "证据类型", "原生对象", "事实来源"], [
    ["05–09", "经营与季度趋势", "指标卡 / 折线图", "Locked FactStore"],
    ["11–16", "治理与案例", "对比 / 流程 / 卡片 / 图表", "Locked FactStore"],
    ["18–22", "组织、效率与风险", "流程 / 指标 / 矩阵", "Locked FactStore"],
    ["24–27", "优先级与决定", "卡片 / 路线图 / 表格", "Decision contract"],
  ], "全 deck 可编辑；没有整页截图。");
  return pptx;
}

function buildCampus(brief) {
  const t = themes.campus, pptx = newDeck(t);
  const campusCover = cover(pptx, t, 1, "PROVINCIAL FINAL · CAMPUS SAFETY", "澄域 · 校园水环境\n预警系统", t.subtitle, "省赛终审 · 22 MAIN + 4 APPENDIX + 6 Q&A", "signal");
  [["18", "NODES"], ["84", "DAYS"], ["01", "CAMPUS"]].forEach((item, i) => {
    const x = 8.45 + i * 1.28;
    campusCover.addShape(SHAPE.ellipse, { x, y: 4.65 - i * 0.42, w: 1.0, h: 1.0, fill: { color: i === 1 ? t.accent : t.pale, transparency: i === 1 ? 0 : 12 }, line: { color: t.accent, width: 1.5 } });
    addText(campusCover, item[0], x + 0.2, 4.82 - i * 0.42, 0.6, 0.34, 14, i === 1 ? t.bg : t.ink, { fontFace: MONO, bold: true, align: "center" });
    addText(campusCover, item[1], x - 0.06, 5.72 - i * 0.42, 1.12, 0.22, 6.5, t.muted, { fontFace: MONO, bold: true, align: "center" });
  });
  agenda(pptx, t, [
    ["为什么现在", "真实巡检痛点与校园水环境风险"],
    ["我们做了什么", "感知、预警、产品与 84 天试点"],
    ["为什么可行", "效果、成本、市场与团队能力"],
    ["下一步决定", "多校验证计划与省赛终审请求"],
  ]);
  metricCards(pptx, t, 3, "One-Slide Thesis", "84 天单校试点，证明预警链路可运行", [
    { label: "SENSORS", value: 18, unit: "节点", detail: "10 分钟一次采样" },
    { label: "VALID DATA", value: "98.6%", unit: "214,680 条", detail: "理论 217,728 条" },
    { label: "F1", value: "85.7%", unit: "试点告警", detail: "precision 81.1% / recall 90.9%" },
    { label: "LEAD TIME", value: "42 min", unit: "平均提前量", detail: "巡检工时从 9.6 降至 4.1 小时/周" },
  ], "边界：当前只证明单校、84 天试点有效；下一阶段必须进行多校验证。",
  ["sensor-nodes", "pilot-days", "valid-rate", "valid-records", "theoretical-records", "f1", "precision", "recall", "lead-time", "hours-before", "hours-pilot", "pilot-limitation"]);
  sectionAligned(pptx, t, 1, "为什么现在", "人工巡检发现晚、记录散、责任重；校园需要更早、更连续的信号。", "signal");
  comparisonSlide(pptx, t, 5, "Problem / Field Reality", "从“靠经验巡检”到“持续感知 + 有证据预警”",
    { label: "CURRENT", title: "人工巡检", items: ["每周 9.6 小时", "问题发现依赖经验", "记录分散、难以复盘"] },
    { label: "TARGET", title: "人机协同", items: ["传感器连续采样", "异常有时间与证据", "人工只处理高价值事件"] },
    "产品不替代管理人员，而是把有限巡检时间用在真正需要判断的事件上。",
    ["hours-before", "hours-pilot"]);
  campusVoiceSlide(pptx, t, 6);
  campusMapSlide(pptx, t, 7);
  sectionAligned(pptx, t, 2, "我们做了什么", "把传感节点、边缘判断、云端证据和处置协作连接成一个产品。", "signal");
  processSlide(pptx, t, 9, "Architecture", "从 10 分钟采样到 42 分钟提前量：四层原生架构", [
    ["感知层", "18 个节点持续采集水环境信号"],
    ["边缘层", "本地过滤、缓存与异常候选生成"],
    ["平台层", "事件聚合、证据时间线与告警评分"],
    ["应用层", "看板、处置、复盘与责任闭环"],
  ], "架构优先保障：断网可缓存、告警可解释、记录可追溯。",
  ["sensor-nodes", "sampling-interval", "lead-time"]);
  dashboardMockupSlide(pptx, t, 10);
  prototypeExplodedSlide(pptx, t, 11);
  dataIntegritySlide(pptx, t, 12);
  alertQualitySlide(pptx, t, 13);
  comparisonSlide(pptx, t, 14, "Pilot / Workflow", "试点把每周巡检工时从 9.6 小时降至 4.1 小时",
    { label: "BEFORE", title: "9.6 小时 / 周", items: ["固定频次全量巡检", "记录分散", "异常复盘困难"] },
    { label: "PILOT", title: "4.1 小时 / 周", items: ["按风险安排巡检", "事件证据集中", "处置结果可复核"] },
    "节省只在单校 84 天试点成立；外推到多校前必须再次验证。",
    ["hours-before", "hours-pilot", "pilot-limitation"]);
  sectionAligned(pptx, t, 3, "为什么可行", "技术、产品、经济性与市场路径必须同时成立。", "signal");
  cardsSlide(pptx, t, 16, "Value / Three Stakeholders", "同一套系统，为三类角色创造不同价值", [
    { tag: "STUDENT", title: "更早的安全信号", detail: "信息清晰，不制造恐慌，处置结果可反馈。" },
    { tag: "STAFF", title: "更少的无效巡检", detail: "把时间投入异常确认和现场判断。" },
    { tag: "MANAGER", title: "可追溯的责任闭环", detail: "看见风险、成本、处置和复盘证据。" },
  ], "下一步：用多校试点分别验证学生反馈、后勤工时和管理闭环。",
  ["student-interviews", "staff-interviews", "manager-interviews"]);
  businessModelSlide(pptx, t, 17, brief);
  marketFunnelSlide(pptx, t, 18);
  matrixSlide(pptx, t, 19, "Risk / Validation", "最危险的不是技术失败，而是把单校成功误当成规模成立", [
    { x: 6.6, y: 2.42, w: 3.3, h: 1.15, title: "跨校泛化", detail: "不同水源、管网与运维习惯可能改变模型表现" },
    { x: 2.2, y: 2.58, w: 2.8, h: 1.0, title: "误报打扰", detail: "precision 81.1%，需要优化阈值与解释" },
    { x: 6.8, y: 4.4, w: 2.9, h: 0.92, title: "维护成本", detail: "校准、耗材与现场支持尚需验证" },
    { x: 2.55, y: 4.48, w: 2.45, h: 0.85, title: "采购周期", detail: "以试点合作降低进入门槛" },
  ], { x: "不确定性 →", y: "影响度 ↑" }, ["precision", "pilot-limitation"]);
  cardsSlide(pptx, t, 20, "Team & IP", "团队页以可交付能力和知识产权路径组织", [
    { tag: "HARDWARE", title: "嵌入式与结构", detail: "传感、功耗、防护、安装与维护。" },
    { tag: "ALGORITHM", title: "时序异常检测", detail: "候选生成、解释与试点评估。" },
    { tag: "PRODUCT", title: "校园场景产品", detail: "用户研究、看板与处置流程。" },
    { tag: "FIELD", title: "现场试点", detail: "校准、运维与事件复核。" },
    { tag: "BUSINESS", title: "合作与验证", detail: "多校试点、服务模型与成本。" },
    { tag: "IP PATH", title: "可保护模块", detail: "结构、边缘策略与事件闭环分层保护。" },
  ], "不展示虚构奖项或专利号；仅陈述能力与规划。");
  roadmapMilestonesSlide(pptx, t, 21);
  closingAligned(pptx, t, 22, "请让项目进入下一轮验证", "我们已经证明链路能运行；现在需要证明它能跨校园复制。", "请求：认可进入省赛终审，并批准多校验证", "signal");
  tableSlide(pptx, t, 23, "Appendix A / Pilot Facts", "试点事实总表", ["维度", "事实", "数值", "边界"], [
    ["部署", "节点 / 天数 / 采样", "18 / 84 / 10 min", "单校"],
    ["数据", "有效 / 理论记录", "214,680 / 217,728", "98.6%"],
    ["告警", "告警 / 确认 / 真实", "37 / 30 / 33", "试点"],
    ["效果", "precision / recall / F1", "81.1 / 90.9 / 85.7%", "合成评测事实"],
  ], factText(brief, "pilot-limitation"),
  ["sensor-nodes", "pilot-days", "sampling-interval", "valid-records", "theoretical-records", "valid-rate", "alerts", "confirmed-alerts", "actual-events", "precision", "recall", "f1", "pilot-limitation"]);
  tableSlide(pptx, t, 24, "Appendix B / Economics", "产品经济性与市场假设", ["项目", "数值", "解释", "下一步"], [
    ["BOM", "1,860 元", "当前样机成本", "可靠性不降级的前提下降本"],
    ["售价", "2,980 元", "合成建议价", "用真实采购验证"],
    ["服务费", "680 元/年", "平台与服务假设", "验证续费价值"],
    ["市场", "4,120 / 620 所", "TAM / SAM 假设", "先做多校复制"],
  ], "市场与价格均为评测事实，不代表真实订单。", ["bom", "price", "service-fee", "market", "serviceable-market"]);
  tableSlide(pptx, t, 25, "Appendix C / Interview", "访谈角色与需求证据", ["角色", "人数", "核心问题", "产品响应"], [
    ["学生", 38, "安全感与信息清晰", "分级提示与反馈"],
    ["后勤人员", 29, "巡检效率与证据", "事件时间线"],
    ["管理者", 24, "责任、成本与复制", "看板与验收"],
  ], "共 91 人；访谈用于需求发现，不等于购买意向。", ["student-interviews", "staff-interviews", "manager-interviews"]);
  tableSlide(pptx, t, 26, "Appendix D / Evidence Index", "原生对象与事实索引", ["页码", "主题", "对象", "事实"], [
    ["03–07", "问题与洞察", "指标 / 对比 / 卡片", "访谈与试点"],
    ["09–14", "产品与效果", "流程 / 图表 / 指标", "试点日志"],
    ["16–21", "价值与可行性", "表格 / 矩阵 / 路线图", "成本与市场"],
    ["22", "决定", "结尾页", "Decision contract"],
  ], "整页可编辑，无截图式假产品。");
  const qa = [
    ["Q1", "为什么不直接扩到 620 所？", "单校试点尚不能证明跨校泛化；先做 3–5 校差异化验证。"],
    ["Q2", "81.1% precision 会不会打扰？", "是风险点；下一阶段优化阈值、证据解释与分级处置。"],
    ["Q3", "数据缺失怎么办？", "本地缓存、完整性监控和人工复核共同保障；当前有效率 98.6%。"],
    ["Q4", "价格有真实客户验证吗？", "没有；2,980 元与 680 元/年是合成评测事实，需采购验证。"],
    ["Q5", "如何避免硬件维护拖垮团队？", "将校准、耗材与故障自检纳入多校验收，而非销售后补课。"],
    ["Q6", "本轮希望评委批准什么？", "批准进入省赛终审；下一阶段完成 3–5 校验证，并以完整性、告警质量和巡检工时复审。"],
  ];
  qa.forEach((item, i) => qaSlide(pptx, t, 27 + i, item[0], item[1], item[2], i));
  return pptx;
}

function buildAcademic(brief) {
  const t = themes.academic, pptx = newDeck(t);
  cover(pptx, t, 1, "MASTER THESIS · EVIDENCE FIRST", "面向交通流预测的\n多尺度动态图 Transformer", t.subtitle, "26 MAIN + 6 APPENDIX · SYNTHETIC EVALUATION LOG", "grid");
  agenda(pptx, t, [
    ["研究问题", "交通流预测的动态图与多尺度依赖"],
    ["方法设计", "模型架构、训练策略与复杂度"],
    ["实验结果", "完整对比、消融、鲁棒性与效率"],
    ["结论边界", "贡献、限制与答辩修改建议"],
  ]);
  metricCards(pptx, t, 3, "Research Abstract", "问题、方法、证据和边界在一页内闭环", [
    { label: "DATASETS", value: "2", unit: "METR-LA / PEMS-BAY", detail: "207 / 325 个传感器" },
    { label: "HORIZONS", value: "3", unit: "15 / 30 / 60 min", detail: "统一 5 分钟采样" },
    { label: "BEST MAE", value: "2.58", unit: "METR-LA · 15 min", detail: "合成实验日志" },
    { label: "PARAMS", value: "3.18M", unit: "OURS", detail: "延迟 10.6 ms" },
  ], "所有 MDGFormer 结果均为标准化合成实验日志，不代表已发表结果。",
  ["metr-sensors", "pems-sensors", "sample-minutes", "mae-mdgformer-metr-la-15min", "params-ours", "latency-ours", "academic-limit"]);
  sectionAligned(pptx, t, 1, "研究问题", "固定图难以描述时变关系；单尺度建模难以同时覆盖局部与长程依赖。", "grid");
  cardsSlide(pptx, t, 5, "Problem / Three Gaps", "现有方法的三条断点，构成本文的设计空间", [
    { tag: "GAP 01", title: "图结构是静态的", detail: "高峰、事故与区域传播使传感器关系随时间变化。" },
    { tag: "GAP 02", title: "尺度表达单一", detail: "短期扰动与长程周期需要不同感受野。" },
    { tag: "GAP 03", title: "精度与效率分开讨论", detail: "实验需要同时报告误差、参数量与延迟。" },
  ], "研究目标：在统一证据框架下验证动态图、多尺度与训练策略的独立贡献。");
  processSlide(pptx, t, 6, "Research Questions", "三个问题对应三组可证伪实验", [
    ["RQ1", "动态图是否改善长预测窗误差？"],
    ["RQ2", "多尺度模块的增益是否独立存在？"],
    ["RQ3", "改进是否以不可接受的效率代价获得？"],
  ], "每个研究问题都绑定对比、消融或效率证据，不用架构图代替结论。");
  networkDatasetSlide(pptx, t, 7, brief);
  sectionAligned(pptx, t, 2, "方法设计", "模型不是组件堆叠：每个模块必须回答一个研究问题。", "grid");
  processSlide(pptx, t, 9, "Method / Architecture", "三条研究断点，逐一映射到四阶段架构", [
    ["输入编码", "统一历史窗口，为三项 RQ 建立可比输入"],
    ["动态图学习", "对应 GAP 01 / RQ1：状态相关关系"],
    ["多尺度交互", "对应 GAP 02 / RQ2：不同感受野"],
    ["多步预测", "对应 RQ3：长窗稳定性与效率证据"],
  ], "映射闭环：GAP 01 → 动态图消融；GAP 02 → 多尺度消融；RQ3 → 重复实验与效率对比。");
  dynamicGraphSlide(pptx, t, 10);
  multiScaleSlide(pptx, t, 11);
  processSlide(pptx, t, 12, "Training / Curriculum", "训练协议确保长预测窗不是偶然最优", [
    ["短窗稳定", "先学习较短预测窗的可靠模式"],
    ["逐步扩展", "增加预测长度与困难样本"],
    ["统一评估", "15 / 30 / 60 分钟均报告 MAE"],
    ["五次重复", "以标准差呈现稳定性"],
  ], "no-curriculum 消融与标准差共同回答训练稳定性。", ["ablation-curriculum", "std-15", "std-30", "std-60"]);
  efficiencyScatterSlide(pptx, t, 13, brief);
  sectionAligned(pptx, t, 3, "实验结果", "完整对比优先于漂亮单点：两个数据集、三个预测窗、四类证据。", "grid");
  academicBenchmarkHeroSlide(pptx, t, 15);
  barChart(pptx, t, 16, "Benchmark / PEMS-BAY", "PEMS-BAY：更大路网下，三个预测窗方向一致", [
    { name: "DCRNN", labels: ["15 min", "30 min", "60 min"], values: [1.38, 1.74, 2.07] },
    { name: "Graph WaveNet", labels: ["15 min", "30 min", "60 min"], values: [1.30, 1.63, 1.95] },
    { name: "STFGNN", labels: ["15 min", "30 min", "60 min"], values: [1.27, 1.59, 1.90] },
    { name: "MDGFormer", labels: ["15 min", "30 min", "60 min"], values: [1.23, 1.52, 1.82] },
  ], { value: "1.82", label: "60 MIN MAE", detail: "跨数据集方向一致；完整 HA 与基线表保留在 Appendix B。" },
  ["mae-ha-pems-bay-15min", "mae-ha-pems-bay-30min", "mae-ha-pems-bay-60min", "mae-dcrnn-pems-bay-15min", "mae-dcrnn-pems-bay-30min", "mae-dcrnn-pems-bay-60min", "mae-gwn-pems-bay-15min", "mae-gwn-pems-bay-30min", "mae-gwn-pems-bay-60min", "mae-stfgnn-pems-bay-15min", "mae-stfgnn-pems-bay-30min", "mae-stfgnn-pems-bay-60min", "mae-mdgformer-pems-bay-15min", "mae-mdgformer-pems-bay-30min", "mae-mdgformer-pems-bay-60min"]);
  academicHorizonDeltaSlide(pptx, t, 17);
  academicAblationSlide(pptx, t, 18);
  comparisonSlide(pptx, t, 19, "Robustness / Missing Data", "缺失率升高时，两种模型均退化；MDGFormer 保持更低误差",
    { label: "10% MISSING", title: "3.86 → 3.59", items: ["Graph WaveNet: 3.86", "MDGFormer: 3.59", "差值 0.27 MAE"] },
    { label: "20% MISSING", title: "4.28 → 3.91", items: ["Graph WaveNet: 4.28", "MDGFormer: 3.91", "差值 0.37 MAE"] },
    "鲁棒性优势随缺失率增加而扩大，但实验仍是合成日志。",
    ["missing-gwn-10", "missing-ours-10", "missing-gwn-20", "missing-ours-20"]);
  barChart(pptx, t, 20, "Stability / Repeated Runs", "五次重复实验：长预测窗波动增加，但保持可控", [
    { name: "METR-LA", labels: ["15 min", "30 min", "60 min"], values: [0.03, 0.04, 0.05] },
    { name: "PEMS-BAY", labels: ["15 min", "30 min", "60 min"], values: [0.02, 0.03, 0.04] },
  ], { value: "≤0.05", label: "STD / 5 RUNS", detail: "用于呈现合成实验重复性；不是统计显著性检验。" },
  ["std-15", "std-30", "std-60", "pems-std-15", "pems-std-30", "pems-std-60"]);
  tableSlide(pptx, t, 21, "Efficiency", "性能收益没有以数量级计算成本为代价", ["模型", "参数量", "推理延迟", "相对判断"], [
    ["Graph WaveNet", "3.06M", "9.4 ms", "最轻最快"],
    ["MDGFormer", "3.18M", "10.6 ms", "折中"],
    ["STFGNN", "3.67M", "12.1 ms", "更重更慢"],
  ], "硬件环境未在当前 brief 中锁定；不得把延迟外推为部署 SLA。",
  ["params-gwn", "latency-gwn", "params-ours", "latency-ours", "params-stfgnn", "latency-stfgnn"]);
  cardsSlide(pptx, t, 22, "Error Analysis", "结果之外，还需要解释失败发生在哪里", [
    { tag: "PEAK", title: "高峰突变", detail: "短时间传播结构变化快，动态图估计仍可能滞后。" },
    { tag: "INCIDENT", title: "异常事件", detail: "训练分布外事件缺少足够监督信号。" },
    { tag: "MISSING", title: "连续缺失", detail: "高缺失率下误差仍显著上升。" },
  ], "误差分析为方法讨论，不新增未锁定定量结论。");
  sectionAligned(pptx, t, 4, "结论与边界", "贡献必须与证据强度一致；限制必须进入主 deck。", "grid");
  cardsSlide(pptx, t, 24, "Contribution", "本文的三项贡献，分别由对比、消融与效率证据支撑", [
    { tag: "C1", title: "状态相关动态图", detail: "在长预测窗和消融中显示稳定增益。" },
    { tag: "C2", title: "多尺度时空交互", detail: "独立消融表明单尺度不足。" },
    { tag: "C3", title: "完整证据协议", detail: "同时报告跨数据集、鲁棒性、稳定性与效率。" },
  ], "不使用“首个”“SOTA”等未获证据支持的表述。");
  cardsSlide(pptx, t, 25, "Limitations", "四个限制决定下一步研究，而不是藏在页脚", [
    { tag: "L1", title: "合成实验日志", detail: "当前数值仅用于 PPT 工作流评测。" },
    { tag: "L2", title: "数据集范围有限", detail: "只有两套交通网络，外部有效性有限。" },
    { tag: "L3", title: "动态图解释有限", detail: "关系变化尚不能直接解释为因果。" },
    { tag: "L4", title: "部署证据缺失", detail: "延迟尚未绑定具体硬件与在线 SLA。" },
  ], factText(brief, "academic-limit"), ["academic-limit"]);
  closingAligned(pptx, t, 26, "证据支持答辩，边界指导修改", "请确认论文达到答辩要求，并形成针对外部有效性与部署证据的修改意见。", "所有结果为合成评测日志 · 不代表已发表论文结果", "grid");
  tableSlide(pptx, t, 27, "Appendix A / METR-LA", "完整 METR-LA 对比表", ["模型", "15", "30", "60"], [
    ["HA", 4.16, 4.96, 5.71], ["DCRNN", 2.77, 3.15, 3.60], ["GWN", 2.69, 3.07, 3.53], ["STFGNN", 2.66, 3.02, 3.45], ["MDGFormer", 2.58, 2.92, 3.31],
  ], "MAE；合成实验日志。");
  tableSlide(pptx, t, 28, "Appendix B / PEMS-BAY", "完整 PEMS-BAY 对比表", ["模型", "15", "30", "60"], [
    ["HA", 2.88, 3.47, 4.12], ["DCRNN", 1.38, 1.74, 2.07], ["GWN", 1.30, 1.63, 1.95], ["STFGNN", 1.27, 1.59, 1.90], ["MDGFormer", 1.23, 1.52, 1.82],
  ], "MAE；合成实验日志。");
  tableSlide(pptx, t, 29, "Appendix C / Ablation", "消融与模块对应关系", ["版本", "MAE", "移除模块", "对应 RQ"], [
    ["Full", 3.31, "—", "全部"], ["Static", 3.46, "动态图", "RQ1"], ["No-scale", 3.42, "多尺度", "RQ2"], ["No-curriculum", 3.39, "课程学习", "RQ2"],
  ], "METR-LA 60min；合成实验日志。");
  tableSlide(pptx, t, 30, "Appendix D / Robustness", "缺失数据完整结果", ["缺失率", "GWN", "MDGFormer", "差值"], [
    ["10%", 3.86, 3.59, 0.27], ["20%", 4.28, 3.91, 0.37],
  ], "MAE；差值仅描述当前日志。");
  tableSlide(pptx, t, 31, "Appendix E / Efficiency", "参数量与推理延迟", ["模型", "参数量", "延迟", "备注"], [
    ["GWN", "3.06M", "9.4ms", "效率基线"], ["MDGFormer", "3.18M", "10.6ms", "折中"], ["STFGNN", "3.67M", "12.1ms", "更重"],
  ], "硬件未锁定；不外推线上 SLA。");
  tableSlide(pptx, t, 32, "Appendix F / Evidence & Citation", "事实、来源与边界索引", ["类别", "来源", "用途", "边界"], [
    ["数据集元数据", "DCRNN public paper", "数据规模与背景", "公开来源"],
    ["模型结果", "synthetic experiment logs", "工作流评测", "非发表结果"],
    ["结论", "locked decision contract", "答辩判断", "不新增 SOTA/因果声明"],
  ], factText(brief, "academic-limit"), ["academic-limit", "presentation-decision"]);
  return pptx;
}

async function writeDeck(pptx, filename, brief, expectedSlides, certification) {
  const target = path.join(outputDir, filename);
  await pptx.writeFile({ fileName: target });
  const manifest = {
    schema_version: "1.0",
    file: filename,
    sha256: sha256(target),
    source_brief: brief.sourcePath,
    source_brief_sha256: sha256(brief.sourcePath),
    slide_count: expectedSlides,
    native_editable: true,
    whole_slide_rasterization: false,
    generator: "build_window_pptx_v6_flagships.mjs",
    certification,
  };
  fs.writeFileSync(`${target}.manifest.json`, `${JSON.stringify(manifest, null, 2)}\n`);
  return manifest;
}

const work = readBrief("annual-work-report");
const campus = readBrief("campus-competition-defense");
const academic = readBrief("academic-thesis-defense");
const manifests = [];
manifests.push(await writeDeck(buildWork(work), "annual-work-report-v6.pptx", work, 32, {
  spine_id: "institutional-work-summary",
  art_direction_id: "institutional-work-summary-v2",
  source_mode: "registered-composition-bridge",
  reference_sha256: "59b104d31bf3f44c15d407adefe51425c9dcd8bb5c5d1e2212fb38753dc72839",
}));
manifests.push(await writeDeck(buildCampus(campus), "campus-competition-defense-v6.pptx", campus, 32, {
  spine_id: "product-launch-stage",
  art_direction_id: "campus-innovation-stage-v2",
  source_mode: "registered-native-composition",
}));
manifests.push(await writeDeck(buildAcademic(academic), "academic-thesis-defense-v6.pptx", academic, 32, {
  spine_id: "data-research-editorial",
  art_direction_id: "academic-evidence-editorial-v2",
  source_mode: "registered-native-composition",
}));
process.stdout.write(`${JSON.stringify({ status: "PASS", output_dir: outputDir, manifests }, null, 2)}\n`);
