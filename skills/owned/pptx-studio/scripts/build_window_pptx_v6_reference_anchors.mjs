#!/usr/bin/env node
/**
 * Build the Phase 46 reference-grade anchors.
 *
 * Unlike the rejected Phase 39/40 card grammar, this renderer uses an explicit
 * page choreography with image-led covers, display typography, native charts,
 * diagrams, tables, and scenario-specific rhythm. Models never own geometry.
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
const DISPLAY = "Microsoft YaHei";
const MONO = "Aptos";
const argv = process.argv.slice(2);
const arg = (name, fallback = null) => {
  const index = argv.indexOf(name);
  return index >= 0 ? argv[index + 1] : fallback;
};
const briefDir = path.resolve(arg("--brief-dir", ""));
const outputDir = path.resolve(arg("--output-dir", ""));
const assetDir = path.resolve(arg("--asset-dir", ""));
const ordinaryPlanDirArg = arg("--ordinary-plan-dir", null);
const ordinaryPlanDir = ordinaryPlanDirArg ? path.resolve(ordinaryPlanDirArg) : null;
if (!briefDir || !outputDir || !assetDir) {
  throw new Error("usage: build_window_pptx_v6_reference_anchors.mjs --brief-dir DIR --output-dir DIR --asset-dir DIR");
}
fs.mkdirSync(outputDir, { recursive: true });

const themes = {
  work: {
    bg: "F6F1E8", ink: "006A55", deep: "06483B", accent: "C5A35E",
    surface: "FFFDF9", pale: "E8DFC9", muted: "65736D", white: "FFFFFF",
    hero: path.join(assetDir, "work-hero.png"),
    title: "年度工作总结", subtitle: "把增长、效率与治理，变成可复制的经营能力",
  },
  campus: {
    bg: "06192C", ink: "F4FBFB", deep: "0A263D", accent: "12C7BA",
    surface: "11354D", pale: "CDEDEC", muted: "9CC2C3", white: "FFFFFF",
    warm: "F0B45A", hero: path.join(assetDir, "campus-hero.png"),
    title: "澄域 · 校园\n水环境预警系统", subtitle: "从单校 84 天试点，走向可复制的校园安全基础设施",
  },
  academic: {
    bg: "F4F0E7", ink: "173B5A", deep: "081B36", accent: "E36B4C",
    surface: "FFFDF8", pale: "DDE8EC", muted: "687B88", white: "FFFFFF",
    cyan: "54C8E8", hero: path.join(assetDir, "academic-hero.png"),
    title: "面向交通流预测的\n多尺度动态图 Transformer", subtitle: "硕士学位论文答辩 · 证据、边界与可复现性",
  },
};

Object.assign(themes, {
  cobalt: {
    ...themes.academic, bg: "F3F6FA", ink: "173B67", deep: "092A55",
    accent: "2F72E8", surface: "FFFFFF", pale: "DCE8F8", muted: "60748D",
    hero: themes.academic.hero,
  },
  coral: {
    ...themes.work, bg: "FBF3EE", ink: "733B2E", deep: "4A2430",
    accent: "F06C55", surface: "FFFDFC", pale: "F3D8CE", muted: "806C67",
    hero: themes.work.hero,
  },
  violet: {
    ...themes.campus, bg: "0D1027", ink: "F8F5FF", deep: "17123B",
    accent: "A778FF", surface: "25204E", pale: "DCD0F7", muted: "B7AED2",
    warm: "FFB454", hero: themes.campus.hero,
  },
  lime: {
    ...themes.campus, bg: "F2F5E9", ink: "273A2B", deep: "163126",
    accent: "81B622", surface: "FFFFFF", pale: "DCE8C9", muted: "657264",
    warm: "E3A92B", hero: themes.campus.hero,
  },
  magenta: {
    ...themes.work, bg: "FFF5F8", ink: "6E2047", deep: "43162F",
    accent: "E94B8A", surface: "FFFFFF", pale: "F5D7E4", muted: "826575",
    hero: themes.work.hero,
  },
  amber: {
    ...themes.academic, bg: "FFF9E9", ink: "4F3C18", deep: "33250F",
    accent: "E2A71B", surface: "FFFEFA", pale: "F2E5B8", muted: "7F7359",
    hero: themes.academic.hero,
  },
  aqua: {
    ...themes.academic, bg: "F2FBFA", ink: "123B42", deep: "082E36",
    accent: "008F86", surface: "FFFFFF", pale: "C9E7E4", muted: "496A6E",
    hero: themes.academic.hero,
  },
  navy: {
    ...themes.academic, bg: "F1F5F9", ink: "17324D", deep: "102A43",
    accent: "1D8FE1", surface: "FFFFFF", pale: "D8E7F3", muted: "60758A",
    hero: themes.academic.hero,
  },
  terra: {
    ...themes.work, bg: "F8F0EA", ink: "65372D", deep: "3B2325",
    accent: "C96F4A", surface: "FFFDFC", pale: "EFD8CC", muted: "7A665E",
    hero: themes.work.hero,
  },
  slate: {
    ...themes.academic, bg: "F2F5F6", ink: "243642", deep: "192A33",
    accent: "2E9B91", surface: "FFFFFF", pale: "D8E7E6", muted: "667982",
    hero: themes.academic.hero,
  },
});

for (const theme of Object.values(themes)) {
  if (!fs.existsSync(theme.hero)) throw new Error(`missing hero image: ${theme.hero}`);
}

const sha256 = (file) => crypto.createHash("sha256").update(fs.readFileSync(file)).digest("hex");

function readBrief(name) {
  const sourcePath = path.join(briefDir, `${name}.project-brief-pack.v1.json`);
  const data = JSON.parse(fs.readFileSync(sourcePath, "utf8"));
  if (data.state !== "Locked" && data.status !== "Locked") throw new Error(`${name} brief is not Locked`);
  const ordinaryPlanPath = ordinaryPlanDir ? path.join(ordinaryPlanDir, `${name}.brief-plan.v1.json`) : null;
  const ordinaryPlan = ordinaryPlanPath && fs.existsSync(ordinaryPlanPath)
    ? JSON.parse(fs.readFileSync(ordinaryPlanPath, "utf8"))
    : null;
  return {
    ...data,
    sourcePath,
    sourceSha256: sha256(sourcePath),
    facts: Object.fromEntries(data.fact_store.facts.map((fact) => [fact.id, fact])),
    ordinaryPlan,
    ordinaryPlanPath,
  };
}

const value = (brief, id) => {
  if (!brief.facts[id]) throw new Error(`missing fact: ${id}`);
  return brief.facts[id].value;
};

function deck(theme) {
  const pptx = new pptxgen();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "AImagician Window-PPTX";
  pptx.company = "AImagician";
  pptx.subject = "Phase 46 reference-grade editable anchor";
  pptx.lang = "zh-CN";
  pptx.theme = { headFontFace: FONT, bodyFontFace: FONT, lang: "zh-CN" };
  pptx.defineSlideMaster({
    title: "BODY",
    background: { color: theme.bg },
    objects: [
      { line: { x: 0.52, y: 0.3, w: 12.25, h: 0, line: { color: theme.accent, width: 1.1, transparency: 24 } } },
      { text: { text: "WINDOW-PPTX / REFERENCE ANCHOR", options: { x: 0.55, y: 0.12, w: 4.5, h: 0.18, fontFace: MONO, fontSize: 5.5, charSpacing: 2, color: theme.muted, margin: 0 } } },
    ],
    slideNumber: { x: 12.2, y: 7.1, w: 0.45, h: 0.2, color: theme.muted, fontFace: MONO, fontSize: 7 },
  });
  return pptx;
}

function text(slide, value, x, y, w, h, size, color, options = {}) {
  slide.addText(String(value), {
    x, y, w, h, fontFace: options.fontFace || FONT, fontSize: size, color,
    margin: options.margin ?? 0, bold: options.bold ?? false,
    align: options.align || "left", valign: options.valign || "mid",
    fit: "shrink", breakLine: false, charSpacing: options.charSpacing || 0,
    paraSpaceAfterPt: options.paraSpaceAfterPt || 0, isTextBox: true,
  });
}

function box(slide, x, y, w, h, fill, radius = 0.12, line = null, transparency = 0) {
  slide.addShape(SHAPE.roundRect, {
    x, y, w, h, rectRadius: radius,
    fill: { color: fill, transparency },
    line: line || { color: fill, transparency: 100 },
  });
}

function fullImage(slide, image) {
  slide.addImage({ path: image, x: 0, y: 0, w: W, h: H });
}

function veil(slide, color, transparency = 30, x = 0, y = 0, w = W, h = H) {
  slide.addShape(SHAPE.rect, {
    x, y, w, h,
    fill: { color, transparency },
    line: { color, transparency: 100 },
  });
}

function notes(slide, factIds = [], composition = "") {
  slide.addNotes([
    `FACT_IDS: ${factIds.join(", ") || "NONE"}`,
    `COMPOSITION: ${composition}`,
    "All text, shapes, charts, tables, and diagrams remain native editable objects.",
  ].join("\n"));
}

function header(slide, theme, index, kicker, titleValue, width = 11.2) {
  text(slide, kicker.toUpperCase(), 0.62, 0.5, 4.2, 0.25, 7, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.2 });
  text(slide, titleValue, 0.62, 0.82, width, 0.72, 24, theme.ink, { bold: true });
  text(slide, String(index).padStart(2, "0"), 11.9, 0.55, 0.82, 0.5, 18, theme.accent, { fontFace: MONO, bold: true, align: "right" });
}

function addRings(slide, theme, cx = 10.8, cy = 4.0, count = 6) {
  for (let i = 0; i < count; i += 1) {
    const d = 1.0 + i * 0.65;
    slide.addShape(SHAPE.ellipse, {
      x: cx - d / 2, y: cy - d / 2, w: d, h: d,
      fill: { color: theme.bg, transparency: 100 },
      line: { color: theme.accent, width: 0.8, transparency: 40 + i * 6 },
    });
  }
}

function addDiagonalBands(slide, theme, dark = false) {
  const c = dark ? theme.accent : theme.pale;
  slide.addShape(SHAPE.parallelogram, {
    x: 6.4, y: 0.55, w: 7.2, h: 0.78, rotate: -4,
    fill: { color: c, transparency: dark ? 25 : 8 }, line: { color: c, transparency: 100 },
  });
  slide.addShape(SHAPE.parallelogram, {
    x: 8.0, y: 6.2, w: 5.9, h: 0.4, rotate: -4,
    fill: { color: theme.accent, transparency: 18 }, line: { color: theme.accent, transparency: 100 },
  });
}

function heroCover(pptx, theme, eyebrow, titleValue, subtitle, meta, dark = false) {
  const slide = pptx.addSlide();
  fullImage(slide, theme.hero);
  veil(slide, dark ? theme.deep : theme.bg, dark ? 8 : 58, 0, 0, 7.8, H);
  slide.addShape(SHAPE.parallelogram, {
    x: -0.35, y: 0.4, w: 7.8, h: 6.55, rotate: -3,
    fill: { color: dark ? theme.deep : theme.bg, transparency: dark ? 0 : 5 },
    line: { color: theme.accent, width: 1.2, transparency: 30 },
  });
  text(slide, eyebrow, 0.75, 0.7, 4.8, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.6 });
  text(slide, titleValue, 0.72, 1.22, 6.8, 2.15, dark ? 42 : 47, dark ? theme.white : theme.ink, { fontFace: DISPLAY, bold: true });
  slide.addShape(SHAPE.line, { x: 0.78, y: 3.75, w: 1.25, h: 0, line: { color: theme.accent, width: 4 } });
  text(slide, subtitle, 0.78, 3.98, 5.8, 0.72, dark ? 16 : 14, dark ? theme.white : theme.muted, { bold: true });
  text(slide, meta, 0.8, 6.08, 5.4, 0.4, dark ? 10 : 8, dark ? theme.white : theme.ink, { fontFace: MONO, charSpacing: 1, bold: dark });
  text(slide, "2026", 11.2, 6.35, 1.4, 0.46, 16, theme.accent, { fontFace: MONO, bold: true, align: "right" });
  notes(slide, [], "hero-cover");
}

function signatureMotif(slide, theme, signature, x = 8.25, y = 1.25, w = 4.25, h = 4.75, dark = false) {
  const ink = dark ? theme.white : theme.ink;
  const surface = dark ? theme.surface : theme.white;
  const muted = dark ? theme.pale : theme.muted;
  if (signature === "architecture") {
    [0, 1, 2, 3].forEach((item) => {
      const inset = item * 0.32;
      box(slide, x + inset, y + h - 1.0 - item * 0.92, w - inset * 2, 0.64, item === 3 ? theme.accent : surface, 0.06, { color: theme.accent, width: 1, transparency: 25 });
      text(slide, ["SOURCE", "FACT", "SERVICE", "GOVERN"][item], x + inset + 0.18, y + h - 0.88 - item * 0.92, 1.6, 0.25, 7, item === 3 ? theme.white : ink, { fontFace: MONO, bold: true, charSpacing: 1.2 });
    });
  } else if (signature === "product") {
    [0, 1, 2].forEach((item) => {
      const px = x + item * 0.52;
      const py = y + item * 0.45;
      box(slide, px, py, 3.15, 3.55, item === 1 ? theme.deep : surface, 0.12, { color: theme.accent, width: 1.2, transparency: 15 });
      box(slide, px + 0.25, py + 0.35, 2.65, 0.28, theme.accent, 0.04);
      [0, 1, 2].forEach((row) => box(slide, px + 0.25, py + 0.88 + row * 0.55, 2.25 - row * 0.28, 0.22, item === 1 ? theme.surface : theme.pale, 0.04));
    });
  } else if (signature === "funnel") {
    [0, 1, 2].forEach((item) => {
      const fw = 4.0 - item * 0.9;
      slide.addShape(SHAPE.chevron, {
        x: x + (w - fw) / 2, y: y + 0.5 + item * 1.15, w: fw, h: 0.78,
        fill: { color: item === 2 ? theme.accent : item === 1 ? surface : theme.deep },
        line: { color: theme.accent, transparency: item === 1 ? 20 : 100 },
      });
    });
  } else if (signature === "quadrant") {
    slide.addShape(SHAPE.line, { x: x + 0.4, y: y + h - 0.45, w: w - 0.65, h: 0, line: { color: ink, width: 1.3, endArrowType: "triangle" } });
    slide.addShape(SHAPE.line, { x: x + w / 2, y: y + h - 0.3, w: 0, h: -(h - 0.65), line: { color: ink, width: 1.3, endArrowType: "triangle" } });
    [[0.9, 2.8, 0.55], [2.6, 0.7, 0.88], [3.15, 2.9, 0.65], [1.05, 1.05, 0.48]].forEach(([dx, dy, d], item) => {
      slide.addShape(SHAPE.ellipse, { x: x + dx, y: y + dy, w: d, h: d, fill: { color: item === 1 ? theme.accent : theme.deep, transparency: 5 }, line: { color: theme.white, width: 1 } });
    });
  } else if (signature === "flywheel" || signature === "constellation") {
    addRings(slide, theme, x + w / 2, y + h / 2, signature === "flywheel" ? 5 : 7);
    const points = [[2.0, 0.45], [3.5, 1.85], [2.8, 3.65], [0.7, 3.2], [0.35, 1.2]];
    points.forEach(([dx, dy], item) => {
      if (signature === "flywheel" && item > 0) {
        const [px, py] = points[item - 1];
        slide.addShape(SHAPE.line, { x: x + px + 0.25, y: y + py + 0.25, w: dx - px, h: dy - py, line: { color: theme.accent, width: 1.7, endArrowType: "triangle" } });
      }
      slide.addShape(SHAPE.ellipse, { x: x + dx, y: y + dy, w: 0.52, h: 0.52, fill: { color: item === 0 ? theme.accent : theme.deep }, line: { color: theme.white, width: 1 } });
    });
  } else if (signature === "ranking") {
    [0.92, 0.76, 0.62, 0.48, 0.34].forEach((ratio, item) => {
      text(slide, `0${item + 1}`, x, y + 0.45 + item * 0.72, 0.42, 0.25, 7, muted, { fontFace: MONO, bold: true });
      box(slide, x + 0.55, y + 0.45 + item * 0.72, (w - 0.65) * ratio, 0.27, item < 2 ? theme.accent : surface, 0.04);
    });
  } else if (signature === "investor") {
    [0.42, 0.66, 0.88, 1.0].forEach((ratio, item) => {
      const barH = 0.6 + ratio * 2.5;
      box(slide, x + 0.35 + item * 0.9, y + h - barH - 0.45, 0.62, barH, item === 3 ? theme.accent : surface, 0.04);
      text(slide, `Y${item + 1}`, x + 0.35 + item * 0.9, y + h - 0.32, 0.62, 0.2, 7, muted, { fontFace: MONO, bold: true, align: "center" });
    });
    slide.addShape(SHAPE.line, { x: x + 0.55, y: y + h - 1.7, w: 3.15, h: -2.15, line: { color: theme.accent, width: 2.2, endArrowType: "triangle" } });
  } else if (signature === "calendar") {
    text(slide, "28-DAY CAMPAIGN", x + 0.15, y + 0.05, w - 0.3, 0.3, 8, ink, { fontFace: MONO, bold: true, align: "center", charSpacing: 1.2 });
    for (let week = 0; week < 4; week += 1) {
      const py = y + 0.65 + week * 0.82;
      text(slide, `W${week + 1}`, x + 0.05, py + 0.15, 0.42, 0.22, 7, muted, { fontFace: MONO, bold: true });
      for (let day = 0; day < 7; day += 1) {
        box(slide, x + 0.55 + day * 0.5, py, 0.38, 0.5, day <= week + 2 ? theme.accent : surface, 0.03, { color: theme.accent, width: 0.6, transparency: 35 });
      }
    }
  } else if (signature === "horizon") {
    [["2027", 3.3], ["2028", 2.5], ["2029", 1.7]].forEach(([year, py], item) => {
      slide.addShape(SHAPE.line, { x: x + 0.35, y: y + py, w: w - 0.7, h: 0, line: { color: item === 2 ? theme.accent : ink, width: item === 2 ? 3 : 1.2, transparency: item === 2 ? 0 : 45 } });
      text(slide, year, x + 0.35, y + py - 0.42, 0.7, 0.25, 8, item === 2 ? theme.accent : muted, { fontFace: MONO, bold: true });
      slide.addShape(SHAPE.ellipse, { x: x + 1.35 + item * 0.9, y: y + py - 0.13, w: 0.26, h: 0.26, fill: { color: item === 2 ? theme.accent : theme.deep }, line: { color: theme.white, width: 0.8 } });
    });
  } else if (signature === "journey") {
    slide.addShape(SHAPE.line, { x: x + 0.35, y: y + h / 2, w: w - 0.7, h: 0, line: { color: theme.accent, width: 3, endArrowType: "triangle" } });
    ["SEGMENT", "TRIGGER", "OFFER", "REVIEW"].forEach((labelValue, item) => {
      const px = x + 0.45 + item * 1.0;
      slide.addShape(SHAPE.ellipse, { x: px, y: y + h / 2 - 0.28, w: 0.56, h: 0.56, fill: { color: item === 3 ? theme.accent : theme.deep }, line: { color: theme.white, width: 1 } });
      text(slide, labelValue, px - 0.25, y + h / 2 + 0.48, 1.05, 0.24, 6, muted, { fontFace: MONO, bold: true, align: "center" });
    });
  } else if (signature === "governance") {
    box(slide, x + 0.85, y + 0.25, 2.55, 0.62, theme.accent, 0.06);
    [0, 1, 2].forEach((item) => {
      const px = x + item * 1.45;
      box(slide, px, y + 2.65, 1.2, 0.78, item === 1 ? theme.accent : surface, 0.06, { color: theme.accent, width: 1, transparency: 20 });
      slide.addShape(SHAPE.line, { x: x + 2.12, y: y + 0.87, w: px + 0.6 - (x + 2.12), h: 1.78, line: { color: theme.accent, width: 1.4 } });
    });
  } else {
    [0, 1, 2, 3].forEach((item) => {
      const px = x + item * 0.93;
      const py = signature === "staircase" ? y + 3.4 - item * 0.75 : y + 1.1 + (item % 2) * 1.15;
      const ph = signature === "staircase" ? 0.65 + item * 0.75 : 0.78;
      box(slide, px, py, 0.75, ph, item === 3 ? theme.accent : surface, 0.05, { color: theme.accent, width: 1, transparency: 20 });
      if (item < 3) slide.addShape(SHAPE.line, { x: px + 0.75, y: py + ph / 2, w: 0.2, h: 0, line: { color: theme.accent, width: 1.4, endArrowType: "triangle" } });
    });
  }
}

function scenarioCover(pptx, theme, config, brief) {
  const dark = ["violet"].includes(config.themeKey);
  const slide = pptx.addSlide();
  const requestedHero = config.heroAsset ? path.join(assetDir, config.heroAsset) : null;
  const scenarioHero = requestedHero && fs.existsSync(requestedHero) ? requestedHero : null;
  const centered = ["product", "flywheel", "constellation"].includes(config.signature);
  const banded = ["funnel", "ranking", "calendar", "investor", "governance"].includes(config.signature);
  const journey = ["journey", "horizon", "staircase"].includes(config.signature);
  slide.background = { color: dark || centered && config.signature === "flywheel" ? theme.deep : theme.bg };
  if (centered) {
    const centeredDark = dark || config.signature === "flywheel" || Boolean(scenarioHero);
    if (scenarioHero) {
      slide.addImage({ path: scenarioHero, x: 0, y: 0, w: W, h: H, sizing: { type: "cover", w: W, h: H } });
      veil(slide, theme.deep, 35);
    }
    addRings(slide, theme, 6.65, 3.75, config.signature === "constellation" ? 8 : 6);
    text(slide, "WINDOW-PPTX / SCENARIO EDITION", 4.1, 0.48, 5.1, 0.26, 7, theme.accent, { fontFace: MONO, bold: true, align: "center", charSpacing: 2.4 });
    text(slide, config.title, 1.2, 1.05, 10.9, 1.5, 42, centeredDark ? theme.white : theme.ink, { bold: true, align: "center" });
    if (!scenarioHero) signatureMotif(slide, theme, config.signature, 4.55, 2.55, 4.25, 3.25, centeredDark);
    text(slide, config.subtitle, 2.2, 5.72, 8.9, 0.52, 13, centeredDark ? theme.pale : theme.muted, { bold: true, align: "center" });
    text(slide, `${brief.audience.primary} · ${brief.timing.presentation_minutes} MIN · 2026`, 3.2, 6.55, 6.9, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, align: "center", charSpacing: 1 });
  } else if (banded) {
    if (scenarioHero) {
      slide.addImage({ path: scenarioHero, x: 7.15, y: 0, w: 6.18, h: 4.62, sizing: { type: "cover", w: 6.18, h: 4.62 } });
      veil(slide, theme.bg, 58, 7.15, 0, 6.18, 4.62);
    }
    slide.addShape(SHAPE.rect, { x: 0, y: 4.62, w: W, h: 2.88, fill: { color: theme.deep }, line: { color: theme.deep, transparency: 100 } });
    text(slide, config.signature.toUpperCase(), 9.1, 0.52, 3.45, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, align: "right", charSpacing: 2 });
    text(slide, config.title, 0.72, 0.8, 7.45, 2.0, 43, theme.ink, { bold: true });
    if (!scenarioHero) signatureMotif(slide, theme, config.signature, 8.25, 0.95, 4.15, 3.25, false);
    text(slide, config.subtitle, 0.78, 5.05, 7.25, 0.72, 14, theme.white, { bold: true });
    text(slide, `${brief.audience.primary} · ${brief.timing.presentation_minutes} MIN`, 0.78, 6.42, 6.1, 0.28, 8, theme.pale, { fontFace: MONO, bold: true, charSpacing: 1 });
    text(slide, "2026", 11.1, 6.22, 1.3, 0.45, 16, theme.accent, { fontFace: MONO, bold: true, align: "right" });
  } else if (journey) {
    if (scenarioHero) {
      slide.addImage({ path: scenarioHero, x: 4.85, y: 0, w: 8.48, h: H, sizing: { type: "cover", w: 8.48, h: H } });
      veil(slide, theme.bg, 42, 4.85, 0, 8.48, H);
    }
    slide.addShape(SHAPE.rect, { x: 0, y: 0, w: 4.85, h: H, fill: { color: theme.deep }, line: { color: theme.deep, transparency: 100 } });
    text(slide, "WINDOW-PPTX / PATH EDITION", 0.65, 0.62, 3.55, 0.26, 7, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2 });
    text(slide, config.title, 0.65, 1.2, 3.7, 2.35, 36, theme.white, { bold: true });
    text(slide, config.subtitle, 0.68, 4.05, 3.55, 1.0, 12, theme.pale, { bold: true });
    if (!scenarioHero) signatureMotif(slide, theme, config.signature, 6.0, 1.15, 5.7, 4.9, false);
    text(slide, `${brief.audience.primary} · ${brief.timing.presentation_minutes} MIN`, 5.95, 6.35, 4.9, 0.28, 8, theme.ink, { fontFace: MONO, bold: true, charSpacing: 1 });
    text(slide, "2026", 11.25, 6.17, 1.1, 0.45, 15, theme.accent, { fontFace: MONO, bold: true, align: "right" });
  } else {
    if (scenarioHero) {
      slide.addImage({ path: scenarioHero, x: 7.75, y: 0, w: 5.58, h: H, sizing: { type: "cover", w: 5.58, h: H } });
    }
    slide.addShape(SHAPE.rect, { x: 0, y: 0, w: 0.18, h: H, fill: { color: theme.accent }, line: { color: theme.accent, transparency: 100 } });
    slide.addShape(SHAPE.rect, { x: 7.75, y: 0, w: 5.58, h: H, fill: { color: dark ? theme.deep : theme.pale, transparency: dark ? 0 : 22 }, line: { color: theme.accent, transparency: 100 } });
    text(slide, "WINDOW-PPTX / SCENARIO EDITION", 0.72, 0.62, 4.8, 0.26, 7, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.4 });
    text(slide, config.title, 0.72, 1.2, 6.5, 2.15, dark ? 39 : 42, dark ? theme.white : theme.ink, { bold: true });
    slide.addShape(SHAPE.line, { x: 0.75, y: 3.75, w: 1.15, h: 0, line: { color: theme.accent, width: 4 } });
    text(slide, config.subtitle, 0.75, 4.02, 6.15, 0.84, 14, dark ? theme.pale : theme.muted, { bold: true });
    text(slide, `${brief.audience.primary} · ${brief.timing.presentation_minutes} MIN`, 0.75, 6.18, 5.8, 0.3, 8, dark ? theme.white : theme.ink, { fontFace: MONO, bold: true, charSpacing: 1 });
    text(slide, config.signature.toUpperCase(), 8.18, 0.62, 4.25, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, align: "right", charSpacing: 2 });
    if (!scenarioHero) signatureMotif(slide, theme, config.signature, 8.2, 1.25, 4.3, 4.85, dark);
    text(slide, "2026", 10.95, 6.35, 1.45, 0.4, 15, theme.accent, { fontFace: MONO, bold: true, align: "right" });
  }
  notes(slide, [], `scenario-cover-${config.signature}`);
}

function scenarioSummary(pptx, theme, index, config, metrics, factIds) {
  const slide = pptx.addSlide("BODY");
  header(slide, theme, index, "Executive readout / scenario grammar", `${config.sections[0][0]}：${config.sections[0][1]}`);
  const metric = (item) => metrics[item % metrics.length];
  const metricText = (item, x, y, w, color = theme.ink, align = "left") => {
    const current = metric(item);
    text(slide, current.value, x, y, w, 0.52, 24, color, { bold: true, align });
    text(slide, current.label, x, y + 0.55, w, 0.28, 9, color, { bold: true, align });
    text(slide, current.detail, x, y + 0.87, w, 0.24, 7, color === theme.white ? theme.pale : theme.muted, { align });
  };
  if (config.signature === "architecture") {
    [0, 1, 2, 3].forEach((item) => {
      const y = 1.65 + item * 1.22;
      const inset = item * 0.42;
      box(slide, 0.85 + inset, y, 11.55 - inset * 2, 0.9, item === 3 ? theme.accent : item === 0 ? theme.deep : theme.surface, 0.07, { color: theme.accent, width: 1, transparency: 25 });
      text(slide, ["01 · 数据范围", "02 · 事实底座", "03 · 服务能力", "04 · 治理决策"][item], 1.12 + inset, y + 0.17, 2.5, 0.3, 11, item === 0 || item === 3 ? theme.white : theme.ink, { bold: true });
      text(slide, metric(item).value, 9.1 - inset, y + 0.12, 2.6, 0.4, 20, item === 0 || item === 3 ? theme.white : theme.ink, { bold: true, align: "right" });
      text(slide, metric(item).label, 8.0 - inset, y + 0.53, 3.7, 0.22, 8, item === 0 || item === 3 ? theme.pale : theme.muted, { align: "right" });
    });
  } else if (config.signature === "funnel") {
    [0, 1, 2, 3].forEach((item) => {
      const fw = 10.7 - item * 1.65;
      const x = 6.65 - fw / 2;
      const y = 1.65 + item * 1.13;
      slide.addShape(SHAPE.chevron, { x, y, w: fw, h: 0.82, fill: { color: item === 3 ? theme.accent : item === 0 ? theme.deep : theme.surface }, line: { color: theme.accent, width: 1, transparency: 25 } });
      text(slide, metric(item).label, x + 0.35, y + 0.22, fw - 3.2, 0.3, 11, item === 0 || item === 3 ? theme.white : theme.ink, { bold: true });
      text(slide, metric(item).value, x + fw - 2.7, y + 0.13, 2.0, 0.42, 18, item === 0 || item === 3 ? theme.white : theme.ink, { bold: true, align: "right" });
    });
  } else if (config.signature === "quadrant") {
    [[0.85, 1.65], [6.75, 1.65], [0.85, 4.05], [6.75, 4.05]].forEach(([x, y], item) => {
      box(slide, x, y, 5.7, 1.95, item === 1 ? theme.deep : item === 2 ? theme.accent : theme.surface, 0.1, { color: theme.accent, width: 1, transparency: 25 });
      metricText(item, x + 0.35, y + 0.32, 4.95, item === 1 || item === 2 ? theme.white : theme.ink);
    });
  } else if (config.signature === "product") {
    box(slide, 4.45, 1.65, 4.45, 4.8, theme.deep, 0.12, { color: theme.accent, width: 1.2, transparency: 15 });
    text(slide, "TRUSTED ANSWER", 4.82, 2.0, 3.7, 0.28, 7, theme.pale, { fontFace: MONO, bold: true, charSpacing: 1.4 });
    box(slide, 4.82, 2.52, 3.72, 0.45, theme.accent, 0.07);
    [2.9, 3.35, 2.25].forEach((width, row) => box(slide, 4.82, 3.28 + row * 0.55, width, 0.23, theme.surface, 0.04));
    [[0.75, 1.85], [9.3, 1.85], [0.75, 4.4], [9.3, 4.4]].forEach(([x, y], item) => {
      box(slide, x, y, 3.05, 1.75, item < 2 ? theme.surface : theme.pale, 0.09, { color: theme.accent, width: 1, transparency: 30 });
      const current = metric(item);
      text(slide, current.label, x + 0.25, y + 0.22, 2.55, 0.28, 9, theme.accent, { fontFace: MONO, bold: true, charSpacing: 0.8 });
      text(slide, current.value, x + 0.25, y + 0.58, 2.55, 0.5, 24, theme.ink, { bold: true });
      text(slide, current.detail, x + 0.25, y + 1.18, 2.55, 0.24, 8, theme.muted, { bold: true });
    });
  } else if (config.signature === "flywheel" || config.signature === "constellation") {
    addRings(slide, theme, 6.65, 4.05, config.signature === "flywheel" ? 5 : 7);
    const nodes = [[5.98, 1.62], [9.75, 3.15], [7.42, 5.35], [2.25, 4.5]];
    nodes.forEach(([x, y], item) => {
      box(slide, x, y, 2.25, 1.05, item === 0 ? theme.accent : theme.deep, 0.1);
      text(slide, metric(item).value, x + 0.18, y + 0.12, 1.88, 0.38, 18, theme.white, { bold: true, align: "center" });
      text(slide, metric(item).label, x + 0.18, y + 0.55, 1.88, 0.24, 8, theme.pale, { bold: true, align: "center" });
    });
  } else if (config.signature === "investor") {
    box(slide, 0.85, 1.65, 4.05, 4.75, theme.deep, 0.1);
    text(slide, "GROWTH PROOF", 1.15, 2.02, 3.45, 0.28, 7, theme.pale, { fontFace: MONO, bold: true, charSpacing: 1.4 });
    text(slide, metric(0).value, 1.12, 2.55, 3.5, 0.8, 38, theme.white, { bold: true });
    text(slide, metric(0).label, 1.15, 3.42, 3.3, 0.32, 11, theme.pale, { bold: true });
    [0.38, 0.58, 0.78, 1.0].forEach((ratio, item) => {
      const barH = 0.45 + ratio * 1.65;
      box(slide, 1.2 + item * 0.78, 5.78 - barH, 0.5, barH, item === 3 ? theme.accent : theme.surface, 0.03);
    });
    [1, 2, 3].forEach((item) => {
      const y = 1.72 + (item - 1) * 1.55;
      box(slide, 5.45, y, 6.85, 1.2, item === 2 ? theme.accent : theme.surface, 0.08, { color: theme.accent, width: 1, transparency: 25 });
      metricText(item, 5.78, y + 0.14, 5.95, item === 2 ? theme.white : theme.ink);
    });
  } else if (config.signature === "ranking") {
    metrics.forEach((current, item) => {
      const y = 1.75 + item * 1.2;
      text(slide, `0${item + 1}`, 0.85, y + 0.08, 0.55, 0.32, 12, theme.accent, { fontFace: MONO, bold: true });
      text(slide, current.label, 1.55, y, 2.5, 0.34, 12, theme.ink, { bold: true });
      slide.addShape(SHAPE.line, { x: 4.15, y: y + 0.25, w: 4.65, h: 0, line: { color: theme.pale, width: 12, beginArrowType: "none" } });
      slide.addShape(SHAPE.line, { x: 4.15, y: y + 0.25, w: 4.65 - item * 0.72, h: 0, line: { color: item < 2 ? theme.accent : theme.deep, width: 12 } });
      text(slide, current.value, 9.15, y - 0.08, 2.15, 0.5, 22, theme.ink, { bold: true, align: "right" });
      text(slide, current.detail, 11.45, y + 0.03, 1.0, 0.3, 7, theme.muted, { align: "right" });
    });
  } else if (config.signature === "governance") {
    box(slide, 4.35, 1.55, 4.65, 0.9, theme.deep, 0.08);
    text(slide, "SCOPE / SUCCESS / ESCALATION", 4.65, 1.83, 4.05, 0.3, 10, theme.white, { fontFace: MONO, bold: true, align: "center", charSpacing: 1 });
    metrics.slice(0, 3).forEach((current, item) => {
      const x = 0.85 + item * 4.02;
      box(slide, x, 3.15, 3.55, 2.35, item === 1 ? theme.accent : theme.surface, 0.1, { color: theme.accent, width: 1, transparency: 25 });
      metricText(item, x + 0.3, 3.55, 2.95, item === 1 ? theme.white : theme.ink, "center");
      slide.addShape(SHAPE.line, { x: 6.67, y: 2.45, w: x + 1.78 - 6.67, h: 0.7, line: { color: theme.accent, width: 1.5 } });
    });
    metricText(3, 4.8, 5.83, 3.7, theme.ink, "center");
  } else if (config.signature === "staircase") {
    const learningStages = ["案例拆解", "小组练习", "观察反馈", "迁移任务"];
    metrics.forEach((current, item) => {
      const x = 0.85 + item * 3.02;
      const y = 5.35 - item * 0.82;
      const h = 0.9 + item * 0.82;
      box(slide, x, y, 2.55, h, item === 3 ? theme.accent : item === 2 ? theme.deep : theme.surface, 0.08, { color: theme.accent, width: 1, transparency: 25 });
      text(slide, `0${item + 1} / ${learningStages[item]}`, x + 0.2, y + 0.18, 2.15, 0.3, 10, item >= 2 ? theme.white : theme.ink, { bold: true });
      text(slide, current.value, x + 0.2, y + 0.62, 2.15, 0.48, 22, item >= 2 ? theme.white : theme.ink, { bold: true });
      text(slide, current.label, x + 0.2, y + h - 0.48, 2.15, 0.25, 8, item >= 2 ? theme.pale : theme.muted, { bold: true });
    });
  } else {
    metrics.forEach((current, item) => {
      const x = 0.85 + item * 3.02;
      const y = config.signature === "staircase" ? 5.35 - item * 0.82 : 2.0 + (item % 2) * 1.5;
      const h = config.signature === "staircase" ? 0.9 + item * 0.82 : 1.25;
      box(slide, x, y, 2.55, h, item === 3 ? theme.accent : item === 2 ? theme.deep : theme.surface, 0.08, { color: theme.accent, width: 1, transparency: 25 });
      text(slide, current.value, x + 0.2, y + 0.15, 2.15, 0.42, 19, item >= 2 ? theme.white : theme.ink, { bold: true });
      text(slide, current.label, x + 0.2, y + h - 0.48, 2.15, 0.25, 8, item >= 2 ? theme.pale : theme.muted, { bold: true });
      if (item < 3) slide.addShape(SHAPE.line, { x: x + 2.55, y: y + h / 2, w: 0.48, h: 0, line: { color: theme.accent, width: 2, endArrowType: "triangle" } });
    });
  }
  notes(slide, factIds, `scenario-summary-${config.signature}`);
}

function scenarioClosing(pptx, theme, config, brief) {
  const slide = pptx.addSlide();
  slide.background = { color: theme.deep };
  const centered = ["product", "flywheel", "constellation"].includes(config.signature);
  const banded = ["funnel", "ranking", "calendar", "investor", "governance", "quadrant", "horizon"].includes(config.signature);
  const journey = ["journey", "staircase"].includes(config.signature);
  if (centered) {
    addRings(slide, theme, 6.65, 3.65, 7);
    text(slide, `NEXT / ${config.sections[2][0]}`, 4.2, 0.62, 4.9, 0.3, 8, theme.accent, { fontFace: MONO, bold: true, align: "center", charSpacing: 2.2 });
    text(slide, config.decision, 1.25, 1.55, 10.85, 2.45, 38, theme.white, { bold: true, align: "center" });
    text(slide, config.subtitle, 2.15, 4.55, 9.05, 0.7, 12, theme.pale, { bold: true, align: "center" });
    text(slide, `${brief.audience.primary} · DECISION READY`, 3.3, 6.35, 6.75, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, align: "center", charSpacing: 1.5 });
  } else if (banded) {
    text(slide, `NEXT / ${config.sections[2][0]}`, 0.75, 0.62, 4.8, 0.3, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.2 });
    text(slide, config.decision, 0.72, 1.25, 11.4, 2.0, 39, theme.white, { bold: true });
    if (config.signature === "investor") {
      box(slide, 9.25, 0.68, 3.0, 0.62, theme.accent, 0.08);
      text(slide, "¥30M / PRE-A", 9.55, 0.83, 2.42, 0.3, 13, theme.white, { fontFace: MONO, bold: true, align: "center", charSpacing: 1 });
    }
    config.sections.forEach(([titleValue], item) => {
      const x = 0.75 + item * 4.05;
      box(slide, x, 4.45, 3.55, 1.2, item === 2 ? theme.accent : theme.surface, 0.08);
      text(slide, `0${item + 1}`, x + 0.22, 4.68, 0.45, 0.28, 9, item === 2 ? theme.white : theme.accent, { fontFace: MONO, bold: true });
      text(slide, titleValue, x + 0.78, 4.58, 2.45, 0.45, 14, item === 2 ? theme.white : theme.ink, { bold: true });
    });
    text(slide, `${brief.audience.primary} · DECISION READY`, 0.78, 6.48, 5.8, 0.28, 8, theme.pale, { fontFace: MONO, bold: true, charSpacing: 1 });
  } else if (journey) {
    slide.addShape(SHAPE.rect, { x: 0, y: 0, w: 4.55, h: H, fill: { color: theme.accent }, line: { color: theme.accent, transparency: 100 } });
    config.sections.forEach(([titleValue], item) => {
      const y = 1.3 + item * 1.55;
      text(slide, `0${item + 1}`, 0.62, y, 0.52, 0.32, 10, theme.white, { fontFace: MONO, bold: true });
      text(slide, titleValue, 1.35, y - 0.1, 2.55, 0.5, 16, theme.white, { bold: true });
      if (item < 2) slide.addShape(SHAPE.line, { x: 0.88, y: y + 0.48, w: 0, h: 1.05, line: { color: theme.white, width: 2, transparency: 25 } });
    });
    text(slide, `NEXT / ${config.sections[2][0]}`, 5.15, 0.72, 4.9, 0.3, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.2 });
    text(slide, config.decision, 5.12, 1.55, 7.15, 2.65, 36, theme.white, { bold: true });
    text(slide, `${config.subtitle}\n目标受众：${brief.audience.primary}`, 5.18, 4.72, 6.6, 1.0, 12, theme.pale, { bold: true });
  } else {
    slide.addShape(SHAPE.rect, { x: 0, y: 0, w: 0.2, h: H, fill: { color: theme.accent }, line: { color: theme.accent, transparency: 100 } });
    text(slide, `NEXT / ${config.sections[2][0]}`, 0.75, 0.7, 4.8, 0.3, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.2 });
    text(slide, config.decision, 0.72, 1.45, 7.0, 2.45, 36, theme.white, { bold: true });
    slide.addShape(SHAPE.line, { x: 0.78, y: 4.42, w: 1.2, h: 0, line: { color: theme.accent, width: 4 } });
    text(slide, `${config.subtitle}\n目标受众：${brief.audience.primary}`, 0.78, 4.75, 6.55, 0.95, 12, theme.pale, { bold: true });
    text(slide, config.signature.toUpperCase(), 8.45, 1.45, 3.85, 0.34, 8, theme.accent, { fontFace: MONO, bold: true, align: "right", charSpacing: 2 });
    config.sections.forEach(([titleValue], item) => {
      const y = 2.15 + item * 1.2;
      text(slide, `0${item + 1}`, 8.45, y, 0.5, 0.3, 10, theme.accent, { fontFace: MONO, bold: true });
      slide.addShape(SHAPE.line, { x: 9.05, y: y + 0.17, w: 0.65, h: 0, line: { color: theme.accent, width: 2 } });
      text(slide, titleValue, 9.95, y - 0.06, 2.35, 0.4, 15, theme.white, { bold: true, align: "right" });
    });
    text(slide, "THANK YOU / DECISION READY", 8.4, 6.38, 3.95, 0.28, 7, theme.accent, { fontFace: MONO, bold: true, align: "right", charSpacing: 1.5 });
  }
  notes(slide, [], `scenario-closing-${config.signature}`);
}

function agenda(pptx, theme, items, dark = false) {
  const slide = pptx.addSlide();
  slide.background = { color: dark ? theme.deep : theme.bg };
  addDiagonalBands(slide, theme, dark);
  text(slide, "目录", 0.6, 0.48, 2.8, 1.0, 54, dark ? theme.white : theme.ink, { bold: true });
  text(slide, "CONTENTS / NARRATIVE", 2.7, 0.83, 3.6, 0.25, 7, theme.accent, { fontFace: MONO, charSpacing: 2 });
  items.forEach((item, i) => {
    const y = 1.75 + i * 1.12;
    text(slide, `0${i + 1}`, 0.78, y, 0.66, 0.42, 15, theme.accent, { fontFace: MONO, bold: true });
    slide.addShape(SHAPE.line, { x: 1.62, y: y + 0.22, w: 1.3, h: 0, line: { color: theme.accent, width: 2, transparency: 30 } });
    text(slide, item[0], 3.2, y - 0.06, 3.15, 0.5, 18, dark ? theme.white : theme.ink, { bold: true });
    text(slide, item[1], 6.55, y - 0.01, 5.35, 0.42, 10, dark ? theme.pale : theme.muted);
  });
  notes(slide, [], "agenda-editorial");
}

function chapter(pptx, theme, n, titleValue, statement, dark = true) {
  const slide = pptx.addSlide();
  slide.background = { color: dark ? theme.deep : theme.bg };
  addRings(slide, theme, 10.95, 3.8, 7);
  text(slide, `0${n}`, 9.4, 0.62, 3.0, 1.15, 68, theme.accent, { fontFace: MONO, bold: true, align: "right" });
  text(slide, `SECTION 0${n}`, 0.72, 0.82, 2.8, 0.25, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.6 });
  text(slide, titleValue, 0.7, 1.55, 7.8, 1.25, 46, dark ? theme.white : theme.ink, { bold: true });
  slide.addShape(SHAPE.line, { x: 0.75, y: 3.13, w: 1.4, h: 0, line: { color: theme.accent, width: 4 } });
  text(slide, statement, 0.75, 3.5, 6.5, 1.15, 16, dark ? theme.pale : theme.muted);
  notes(slide, [], "chapter-reset");
}

function campusChapter(pptx, theme, n, titleValue, statement, mode) {
  const dark = mode !== "field";
  const slide = pptx.addSlide();
  slide.background = { color: dark ? theme.deep : theme.bg };
  text(slide, `SECTION 0${n}`, 0.72, 0.82, 2.8, 0.25, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.6 });
  text(slide, titleValue, 0.7, 1.55, 6.3, 1.2, 46, dark ? theme.white : theme.ink, { bold: true });
  slide.addShape(SHAPE.line, { x: 0.75, y: 3.13, w: 1.4, h: 0, line: { color: theme.accent, width: 4 } });
  text(slide, statement, 0.75, 3.5, 6.1, 1.15, 16, dark ? theme.pale : theme.muted);
  text(slide, `0${n}`, 10.95, 0.62, 1.45, 0.9, 48, theme.accent, { fontFace: MONO, bold: true, align: "right" });

  if (mode === "field") {
    const points = [
      [8.15, 2.05, "源"],
      [10.55, 3.1, "网"],
      [8.72, 5.18, "端"],
      [11.45, 5.55, "行"],
    ];
    points.forEach(([x, y, label], i) => {
      if (i > 0) {
        const [px, py] = points[i - 1];
        slide.addShape(SHAPE.line, { x: px + 0.28, y: py + 0.28, w: x - px, h: y - py, line: { color: theme.accent, width: 2, transparency: 20, endArrowType: "triangle" } });
      }
      slide.addShape(SHAPE.ellipse, { x, y, w: 0.62, h: 0.62, fill: { color: i === 3 ? theme.warm : theme.accent, transparency: 6 }, line: { color: theme.white, width: 1.4 } });
      text(slide, label, x, y + 0.08, 0.62, 0.35, 15, i === 3 ? theme.deep : theme.white, { bold: true, align: "center" });
      slide.addShape(SHAPE.arc, { x: x - 0.3, y: y - 0.3, w: 1.22, h: 1.22, adjustPoint: 0.25, rotate: i * 28, fill: { color: theme.bg, transparency: 100 }, line: { color: theme.accent, width: 1, transparency: 38 } });
    });
  } else if (mode === "system") {
    const layers = [
      ["感知", "22 节点", 8.0, 1.85, 3.65],
      ["边缘", "10 分钟", 8.55, 2.75, 3.1],
      ["融合", "证据链", 9.1, 3.65, 2.55],
      ["行动", "42 分钟", 9.65, 4.55, 2.0],
    ];
    layers.forEach(([label, valueText, x, y, w], i) => {
      box(slide, x, y, w, 0.68, i === 3 ? theme.accent : theme.surface, 0.14, { color: theme.accent, width: 1.1, transparency: 18 }, i === 3 ? 0 : 12);
      text(slide, label, x + 0.2, y + 0.12, 1.0, 0.32, 11, i === 3 ? theme.deep : theme.white, { bold: true });
      text(slide, valueText, x + w - 1.25, y + 0.12, 1.05, 0.32, 10, i === 3 ? theme.deep : theme.accent, { fontFace: MONO, bold: true, align: "right" });
    });
    slide.addShape(SHAPE.line, { x: 9.84, y: 1.48, w: 0, h: 4.35, line: { color: theme.accent, width: 2, transparency: 18, endArrowType: "triangle" } });
  } else {
    const campuses = [
      [8.0, 4.72, 0.8, "01"],
      [9.55, 3.15, 1.18, "03"],
      [11.45, 1.75, 1.55, "05"],
    ];
    campuses.forEach(([x, y, d, label], i) => {
      slide.addShape(SHAPE.ellipse, { x: x - d / 2, y: y - d / 2, w: d, h: d, fill: { color: theme.deep, transparency: 100 }, line: { color: i === 2 ? theme.warm : theme.accent, width: 2.2, transparency: i * 7 } });
      slide.addShape(SHAPE.ellipse, { x: x - 0.12, y: y - 0.12, w: 0.24, h: 0.24, fill: { color: i === 2 ? theme.warm : theme.accent }, line: { color: theme.white, transparency: 25 } });
      text(slide, label, x - 0.32, y + d / 2 + 0.14, 0.64, 0.28, 9, theme.white, { fontFace: MONO, bold: true, align: "center" });
      if (i > 0) {
        const [px, py] = campuses[i - 1];
        slide.addShape(SHAPE.line, { x: px, y: py, w: x - px, h: y - py, line: { color: theme.accent, width: 1.6, transparency: 22, endArrowType: "triangle" } });
      }
    });
    text(slide, "从单校证据到多校复制", 7.35, 6.05, 5.1, 0.42, 13, theme.pale, { bold: true, align: "center" });
  }
  notes(slide, [], `campus-chapter-${mode}`);
}

function bigMetrics(pptx, theme, index, titleValue, metrics, factIds, dark = false) {
  const slide = pptx.addSlide("BODY");
  slide.background = { color: dark ? theme.deep : theme.bg };
  header(slide, theme, index, "Executive readout", titleValue);
  metrics.forEach((m, i) => {
    const x = 0.7 + i * 3.05;
    if (i === 0) {
      box(slide, x, 1.75, 2.8, 4.45, theme.deep);
      const focalSize = String(m.value).length > 5 ? 27 : 38;
      text(slide, m.value, x + 0.24, 2.15, 2.3, 1.15, focalSize, theme.white, { bold: true });
      text(slide, m.label, x + 0.25, 3.38, 2.25, 0.42, 10, theme.accent, { fontFace: MONO, bold: true });
      slide.addShape(SHAPE.line, { x: x + 0.25, y: 4.12, w: 1.9, h: 0, line: { color: theme.accent, width: 2 } });
      text(slide, m.detail, x + 0.25, 4.38, 2.2, 1.1, 12, theme.pale);
    } else {
      text(slide, m.value, x, 2.15, 2.7, 1.15, 34, theme.ink, { bold: true });
      text(slide, m.label, x, 3.35, 2.5, 0.42, 9, theme.accent, { fontFace: MONO, bold: true });
      slide.addShape(SHAPE.line, { x, y: 4.08, w: 2.25, h: 0, line: { color: theme.pale, width: 1.5 } });
      text(slide, m.detail, x, 4.35, 2.45, 1.0, 11, theme.muted);
    }
  });
  notes(slide, factIds, "asymmetric-big-metrics");
}

function metricLedger(pptx, theme, index, titleValue, metrics, factIds) {
  const slide = pptx.addSlide("BODY");
  slide.background = { color: theme.bg };
  header(slide, theme, index, "Evidence / decision ledger", titleValue);
  metrics.slice(0, 4).forEach((metric, item) => {
    const y = 1.72 + item * 1.17;
    const active = item === 0;
    box(slide, 0.72, y, 11.85, 0.91, active ? theme.deep : theme.surface, 0.08, {
      color: active ? theme.deep : theme.pale,
      width: 1,
      transparency: active ? 100 : 35,
    });
    text(slide, `0${item + 1}`, 0.98, y + 0.24, 0.52, 0.28, 10, theme.accent, { fontFace: MONO, bold: true });
    text(slide, metric.label, 1.72, y + 0.19, 3.15, 0.36, 15, active ? theme.white : theme.ink, { bold: true });
    text(slide, metric.detail, 4.95, y + 0.22, 3.25, 0.3, 10, active ? theme.pale : theme.muted);
    text(slide, metric.value, 9.0, y + 0.12, 3.05, 0.52, 23, active ? theme.white : theme.ink, { bold: true, align: "right" });
  });
  text(slide, "同一组事实以“核验清单”而非摘要卡片重述，用于进入决策前的逐项确认。", 0.78, 6.47, 9.6, 0.34, 10, theme.muted);
  notes(slide, factIds, "metric-decision-ledger");
}

function chartScene(pptx, theme, index, titleValue, series, sideValue, sideLabel, factIds, chartType = "line") {
  const slide = pptx.addSlide("BODY");
  slide.background = { color: theme.bg };
  header(slide, theme, index, "Evidence / trajectory", titleValue);
  box(slide, 0.65, 1.75, 8.45, 4.75, theme.surface);
  slide.addChart(chartType === "bar" ? CHART.bar : CHART.line, series, {
    x: 0.95, y: 2.05, w: 7.85, h: 3.85,
    catAxisLabelFontFace: FONT, catAxisLabelFontSize: 9,
    valAxisLabelFontFace: MONO, valAxisLabelFontSize: 8,
    showLegend: series.length > 1, legendPos: "b",
    showTitle: false, showValue: chartType === "bar",
    chartColors: [theme.ink, theme.accent, theme.muted, theme.pale],
    showCatName: false, showValAxisTitle: false,
    valGridLine: { color: theme.pale, transparency: 15 },
    showCatAxisTitle: false, showValAxis: true,
    lineSize: 3, markerSize: 7,
  });
  box(slide, 9.45, 1.75, 3.15, 4.75, theme.deep);
  text(slide, sideValue, 9.82, 2.25, 2.4, 1.0, 34, theme.white, { bold: true });
  text(slide, sideLabel, 9.85, 3.25, 2.15, 0.35, 8, theme.accent, { fontFace: MONO, bold: true });
  slide.addShape(SHAPE.line, { x: 9.85, y: 3.85, w: 1.8, h: 0, line: { color: theme.accent, width: 2 } });
  text(slide, "趋势不是装饰：它回答“变化是否持续、目标是否可信”。", 9.85, 4.15, 2.05, 1.15, 12, theme.pale);
  notes(slide, factIds, chartType === "bar" ? "chart-scene-bar" : "chart-scene-line");
}

function beforeAfter(pptx, theme, index, titleValue, before, after, factIds) {
  const slide = pptx.addSlide("BODY");
  slide.background = { color: theme.bg };
  header(slide, theme, index, "Before / after", titleValue);
  box(slide, 0.7, 1.75, 5.0, 4.5, theme.surface);
  box(slide, 7.6, 1.75, 5.0, 4.5, theme.deep);
  text(slide, "BEFORE", 1.05, 2.05, 2, 0.3, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2 });
  text(slide, before.value, 1.0, 2.55, 3.8, 1.1, 42, theme.ink, { bold: true });
  text(slide, before.label, 1.05, 3.65, 3.8, 0.5, 14, theme.muted, { bold: true });
  text(slide, before.detail, 1.05, 4.45, 3.8, 0.85, 12, theme.muted);
  text(slide, "AFTER", 7.95, 2.05, 2, 0.3, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2 });
  text(slide, after.value, 7.9, 2.55, 3.8, 1.1, 42, theme.white, { bold: true });
  text(slide, after.label, 7.95, 3.65, 3.8, 0.5, 14, theme.accent, { bold: true });
  text(slide, after.detail, 7.95, 4.45, 3.8, 0.85, 12, theme.pale);
  slide.addShape(SHAPE.chevron, {
    x: 5.85, y: 3.05, w: 1.5, h: 1.6,
    fill: { color: theme.accent }, line: { color: theme.accent },
  });
  notes(slide, factIds, "before-after-diptych");
}

function processFlow(pptx, theme, index, titleValue, steps, factIds) {
  const slide = pptx.addSlide("BODY");
  slide.background = { color: theme.bg };
  header(slide, theme, index, "System / process", titleValue);
  steps.forEach((step, i) => {
    const x = 0.65 + i * 3.08;
    const active = i === steps.length - 1;
    box(slide, x, 2.0 + (i % 2) * 0.32, 2.55, 3.4, active ? theme.deep : theme.surface);
    text(slide, `0${i + 1}`, x + 0.22, 2.22 + (i % 2) * 0.32, 0.65, 0.35, 12, theme.accent, { fontFace: MONO, bold: true });
    text(slide, step.title, x + 0.22, 2.9 + (i % 2) * 0.32, 2.0, 0.7, 18, active ? theme.white : theme.ink, { bold: true });
    text(slide, step.detail, x + 0.22, 3.8 + (i % 2) * 0.32, 2.0, 0.95, 11, active ? theme.pale : theme.muted);
    if (i < steps.length - 1) {
      slide.addShape(SHAPE.chevron, {
        x: x + 2.62, y: 3.2, w: 0.38, h: 0.75,
        fill: { color: theme.accent }, line: { color: theme.accent },
      });
    }
  });
  notes(slide, factIds, "staggered-process");
}

function matrix(pptx, theme, index, titleValue, cards, factIds) {
  const slide = pptx.addSlide("BODY");
  slide.background = { color: theme.bg };
  header(slide, theme, index, "Decision matrix", titleValue);
  cards.forEach((card, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.68 + col * 4.13;
    const y = 1.75 + row * 2.25;
    box(slide, x, y, 3.78, 1.85, i === 0 ? theme.deep : theme.surface);
    text(slide, card.kicker, x + 0.23, y + 0.18, 1.8, 0.25, 7, theme.accent, { fontFace: MONO, bold: true, charSpacing: 1.5 });
    text(slide, card.title, x + 0.23, y + 0.55, 3.2, 0.48, 15, i === 0 ? theme.white : theme.ink, { bold: true });
    text(slide, card.detail, x + 0.23, y + 1.05, 3.15, 0.55, 10, i === 0 ? theme.pale : theme.muted);
  });
  notes(slide, factIds, "six-cell-matrix");
}

function academicEvidenceGrid(pptx, theme, index, titleValue, cards, factIds) {
  const slide = pptx.addSlide("BODY");
  slide.background = { color: theme.bg };
  header(slide, theme, index, "Evidence / horizon × mechanism", titleValue);
  text(slide, "FORECAST HORIZON", 0.72, 1.55, 2.4, 0.25, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 1.8 });
  text(slide, "ABLATION EVIDENCE", 0.72, 4.12, 2.4, 0.25, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 1.8 });
  cards.forEach((card, i) => {
    const col = i % 3;
    const row = Math.floor(i / 3);
    const x = 0.72 + col * 4.08;
    const y = row === 0 ? 1.92 : 4.48;
    box(slide, x, y, 3.72, 1.82, row === 0 && col === 0 ? theme.deep : row === 0 ? theme.surface : theme.pale, 0.1, { color: row === 0 ? theme.accent : theme.ink, width: 1.15, transparency: 52 });
    text(slide, card.kicker, x + 0.22, y + 0.18, 1.45, 0.25, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 1.2 });
    text(slide, card.title, x + 0.22, y + 0.58, 2.95, 0.5, 20, row === 0 && col === 0 ? theme.white : theme.ink, { bold: true });
    text(slide, card.detail, x + 0.22, y + 1.23, 3.05, 0.34, 11, row === 0 && col === 0 ? theme.pale : theme.muted, { bold: true });
    if (col < 2) {
      slide.addShape(SHAPE.line, { x: x + 3.9, y, w: 0, h: 1.82, line: { color: theme.accent, width: 1, transparency: 60 } });
    }
  });
  notes(slide, factIds, "academic-evidence-grid");
}

function campusMarketExpansion(pptx, theme, index, titleValue, brief, factIds) {
  const slide = pptx.addSlide("BODY");
  slide.background = { color: theme.bg };
  header(slide, theme, index, "Market / evidence path", titleValue);
  const stages = [
    { x: 1.65, y: 3.65, d: 2.15, value: value(brief, "market").toLocaleString(), label: "TAM / 全国高校", color: theme.deep },
    { x: 4.75, y: 3.65, d: 2.15, value: value(brief, "serviceable-market").toLocaleString(), label: "SAM / 可服务校", color: theme.accent },
    { x: 7.85, y: 3.65, d: 2.15, value: "3–5", label: "下一轮验证校", color: theme.warm },
  ];
  stages.forEach((stage, i) => {
    slide.addShape(SHAPE.ellipse, { x: stage.x - stage.d / 2, y: stage.y - stage.d / 2, w: stage.d, h: stage.d, fill: { color: stage.color, transparency: i === 0 ? 0 : 6 }, line: { color: theme.white, transparency: 22, width: 1.2 } });
    text(slide, stage.value, stage.x - stage.d / 2, stage.y - 0.38, stage.d, 0.68, 29, i === 0 ? theme.white : theme.deep, { fontFace: MONO, bold: true, align: "center" });
    text(slide, stage.label, stage.x - stage.d / 2 + 0.12, stage.y + 0.36, stage.d - 0.24, 0.42, 11, i === 0 ? theme.pale : theme.deep, { bold: true, align: "center" });
    if (i < stages.length - 1) {
      const next = stages[i + 1];
      slide.addShape(SHAPE.line, { x: stage.x + stage.d / 2 + 0.18, y: stage.y, w: next.x - next.d / 2 - stage.x - stage.d / 2 - 0.36, h: 0, line: { color: theme.accent, width: 2.4, transparency: 18, endArrowType: "triangle" } });
    }
  });
  box(slide, 10.2, 2.58, 2.35, 2.15, theme.deep, 0.18);
  text(slide, "复制", 10.55, 2.92, 1.65, 0.62, 29, theme.white, { bold: true, align: "center" });
  text(slide, "证据 / 交付 / 服务\n三套模板标准化", 10.48, 3.62, 1.8, 0.7, 11, theme.pale, { bold: true, align: "center" });
  slide.addShape(SHAPE.line, { x: 0.82, y: 6.1, w: 11.7, h: 0, line: { color: theme.accent, width: 1.2, transparency: 38 } });
  text(slide, "不是从 4,120 所同时起跑，而是用 3–5 校建立可迁移的证据密度。", 0.82, 6.28, 9.4, 0.36, 12, theme.muted, { bold: true });
  notes(slide, factIds, "campus-market-expansion-map");
}

function campusStakeholderValue(pptx, theme, index, titleValue, brief, factIds) {
  const slide = pptx.addSlide("BODY");
  slide.background = { color: theme.bg };
  header(slide, theme, index, "Stakeholder value / delivery", titleValue);
  const columns = [
    { role: "STUDENT", title: "更早收到可信信号", detail: "减少不确定感，知道何时需要行动", offer: "硬件一次部署", valueText: `BOM ¥${value(brief, "bom")}` },
    { role: "STAFF", title: "更快定位异常节点", detail: "减少无效巡检，聚焦现场处置", offer: "项目制交付", valueText: `建议售价 ¥${value(brief, "price")}` },
    { role: "MANAGER", title: "可追溯责任闭环", detail: "把事件、动作和结果纳入治理", offer: "年度服务", valueText: `¥${value(brief, "service-fee")}/年` },
  ];
  columns.forEach((column, i) => {
    const x = 0.72 + i * 4.08;
    box(slide, x, 1.75, 3.72, 4.75, i === 0 ? theme.deep : theme.surface, 0.16, { color: i === 0 ? theme.deep : theme.accent, width: 1.25, transparency: 46 });
    text(slide, `0${i + 1} / ${column.role}`, x + 0.26, 2.05, 2.75, 0.3, 9, theme.accent, { fontFace: MONO, bold: true, charSpacing: 1.3 });
    text(slide, column.title, x + 0.26, 2.58, 3.05, 0.72, 21, i === 0 ? theme.white : theme.ink, { bold: true });
    text(slide, column.detail, x + 0.26, 3.42, 3.05, 0.65, 12, i === 0 ? theme.pale : theme.muted, { bold: true });
    slide.addShape(SHAPE.line, { x: x + 0.26, y: 4.42, w: 3.0, h: 0, line: { color: theme.accent, width: 1.5, transparency: 35 } });
    text(slide, "DELIVERY MODEL", x + 0.26, 4.72, 2.4, 0.26, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 1.4 });
    text(slide, column.offer, x + 0.26, 5.16, 2.95, 0.42, 16, i === 0 ? theme.white : theme.ink, { bold: true });
    text(slide, column.valueText, x + 0.26, 5.72, 2.95, 0.38, 13, i === 0 ? theme.pale : theme.muted, { fontFace: MONO, bold: true });
  });
  notes(slide, factIds, "campus-stakeholder-value-columns");
}

function campusObservationMap(pptx, theme, index, titleValue, factIds) {
  const slide = pptx.addSlide();
  fullImage(slide, theme.hero);
  veil(slide, theme.deep, 26);
  veil(slide, theme.deep, 4, 0, 0, 5.15, H);
  text(slide, "FIELD MAP / LIVE PILOT", 0.68, 0.55, 3.8, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.2 });
  text(slide, titleValue, 0.65, 0.92, 5.2, 1.2, 29, theme.white, { bold: true });
  text(slide, "一条可行动的观测链路", 0.68, 2.42, 3.6, 0.35, 12, theme.pale, { bold: true });
  const zones = [
    ["01", "水源 / 储水", "建立入口与蓄水基线"],
    ["02", "管网节点", "识别压力、流量与水质变化"],
    ["03", "高频使用端", "宿舍、食堂、教学楼重点覆盖"],
  ];
  zones.forEach((zone, i) => {
    const y = 3.0 + i * 1.0;
    text(slide, zone[0], 0.72, y, 0.5, 0.35, 11, theme.accent, { fontFace: MONO, bold: true });
    slide.addShape(SHAPE.line, { x: 1.35, y: y + 0.18, w: 0.65, h: 0, line: { color: theme.accent, width: 2 } });
    text(slide, zone[1], 2.2, y - 0.05, 1.7, 0.4, 14, theme.white, { bold: true });
    text(slide, zone[2], 3.85, y - 0.02, 2.5, 0.4, 9, theme.pale);
  });
  const nodes = [
    [8.1, 2.0, "SOURCE"], [10.35, 1.42, "NODE 07"], [11.25, 3.05, "NODE 14"],
    [8.7, 4.3, "NODE 19"], [10.1, 5.35, "DORM"], [11.82, 5.0, "CANTEEN"],
  ];
  nodes.forEach(([x, y, label], i) => {
    if (i > 0) {
      const [px, py] = nodes[i - 1];
      slide.addShape(SHAPE.line, { x: px + 0.15, y: py + 0.15, w: x - px, h: y - py, line: { color: theme.white, width: 3.6, transparency: 72 } });
      slide.addShape(SHAPE.line, { x: px + 0.15, y: py + 0.15, w: x - px, h: y - py, line: { color: theme.accent, width: 2.2, transparency: 8, beginArrowType: "none", endArrowType: "triangle" } });
    }
    slide.addShape(SHAPE.ellipse, {
      x, y, w: 0.32, h: 0.32,
      fill: { color: i === nodes.length - 1 ? theme.warm : theme.accent },
      line: { color: theme.white, width: 1.2, transparency: 15 },
      shadow: { type: "outer", color: theme.accent, opacity: 0.35, blur: 3, angle: 45, distance: 1 },
    });
    text(slide, label, x - 0.2, y + 0.4, 1.0, 0.22, 6, theme.white, { fontFace: MONO, bold: true });
  });
  box(slide, 7.68, 5.95, 4.75, 0.72, theme.deep, 0.12, { color: theme.accent, transparency: 20, width: 1 }, 8);
  text(slide, "22 个节点  →  10 分钟采样  →  事件中心闭环", 7.95, 6.13, 4.2, 0.3, 11, theme.white, { bold: true, align: "center" });
  notes(slide, factIds, "photo-led-campus-observation-map");
}

function campusArchitecture(pptx, theme, index, titleValue, factIds) {
  const slide = pptx.addSlide();
  slide.background = { color: theme.bg };
  text(slide, "SYSTEM BLUEPRINT / NATIVE", 0.65, 0.52, 4.0, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.2 });
  text(slide, titleValue, 0.62, 0.9, 8.4, 0.85, 27, theme.white, { bold: true });
  const layers = [
    { x: 0.72, title: "感知层", label: "22 NODES", detail: "水质 · 压力 · 流量", color: theme.accent },
    { x: 3.47, title: "边缘层", label: "EDGE", detail: "清洗 · 缺失 · 切片", color: theme.cyan || theme.accent },
    { x: 6.22, title: "平台层", label: "FUSION", detail: "规则 × 模型 × 证据", color: theme.warm },
    { x: 8.97, title: "应用层", label: "ACTION", detail: "告警 · 解释 · 复盘", color: theme.accent },
  ];
  layers.forEach((layer, i) => {
    box(slide, layer.x, 2.18, 2.12, 3.15, i === 2 ? theme.surface : theme.deep, 0.16, { color: layer.color, width: i === 2 ? 2.2 : 1.2, transparency: 15 }, i === 2 ? 0 : 10);
    text(slide, `0${i + 1}`, layer.x + 0.18, 2.42, 0.42, 0.3, 10, layer.color, { fontFace: MONO, bold: true });
    slide.addShape(SHAPE.ellipse, { x: layer.x + 0.72, y: 2.8, w: 0.68, h: 0.68, fill: { color: layer.color, transparency: 10 }, line: { color: theme.white, transparency: 35, width: 1 } });
    text(slide, layer.label, layer.x + 0.34, 3.62, 1.44, 0.38, 14, theme.white, { fontFace: MONO, bold: true, align: "center" });
    text(slide, layer.title, layer.x + 0.22, 4.18, 1.68, 0.42, 17, theme.white, { bold: true, align: "center" });
    text(slide, layer.detail, layer.x + 0.18, 4.72, 1.76, 0.35, 9, theme.pale, { align: "center" });
    if (i < layers.length - 1) {
      slide.addShape(SHAPE.chevron, { x: layer.x + 2.22, y: 3.35, w: 0.42, h: 0.72, fill: { color: theme.accent, transparency: 5 }, line: { color: theme.accent, transparency: 100 } });
    }
  });
  box(slide, 11.42, 2.18, 1.18, 3.15, theme.accent, 0.16);
  text(slide, "42", 11.55, 2.76, 0.9, 0.72, 28, theme.bg, { fontFace: MONO, bold: true, align: "center" });
  text(slide, "MIN", 11.55, 3.46, 0.9, 0.28, 9, theme.bg, { fontFace: MONO, bold: true, align: "center" });
  text(slide, "提前量", 11.55, 4.25, 0.9, 0.36, 11, theme.bg, { bold: true, align: "center" });
  slide.addShape(SHAPE.line, { x: 0.75, y: 6.0, w: 11.8, h: 0, line: { color: theme.accent, width: 1.2, transparency: 35 } });
  text(slide, "信号不是终点：每一层都必须为下一层提供可验证、可追溯的输入。", 0.75, 6.2, 8.8, 0.42, 12, theme.pale);
  notes(slide, factIds, "layered-campus-system-blueprint");
}

function campusProductScene(pptx, theme, index, titleValue, brief, factIds) {
  const slide = pptx.addSlide();
  slide.background = { color: theme.bg };
  text(slide, "PRODUCT PROOF / EDITABLE", 0.65, 0.52, 4.0, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.2 });
  text(slide, titleValue, 0.62, 0.9, 8.5, 0.85, 27, theme.white, { bold: true });
  box(slide, 0.68, 1.9, 7.1, 4.85, theme.deep, 0.18, { color: theme.accent, width: 1.2, transparency: 28 }, 3);
  text(slide, "澄域 / CAMPUS WATER OPS", 1.0, 2.18, 3.6, 0.3, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 1.8 });
  text(slide, "校园态势总览", 1.0, 2.55, 2.8, 0.55, 22, theme.white, { bold: true });
  const bars = [0.82, 0.56, 0.7, 0.4, 0.92, 0.64, 0.76];
  bars.forEach((v, i) => {
    slide.addShape(SHAPE.rect, { x: 1.04 + i * 0.72, y: 5.78 - v * 2.4, w: 0.38, h: v * 2.4, fill: { color: i === 4 ? theme.warm : theme.accent, transparency: i === 4 ? 0 : 18 }, line: { color: theme.accent, transparency: 100 } });
  });
  slide.addShape(SHAPE.line, { x: 0.98, y: 5.8, w: 5.25, h: 0, line: { color: theme.pale, width: 1, transparency: 48 } });
  box(slide, 6.15, 2.55, 1.25, 1.25, theme.accent);
  text(slide, `${value(brief, "lead-time")}`, 6.3, 2.75, 0.95, 0.55, 24, theme.bg, { fontFace: MONO, bold: true, align: "center" });
  text(slide, "MIN", 6.3, 3.3, 0.95, 0.22, 7, theme.bg, { fontFace: MONO, bold: true, align: "center" });
  const specs = [
    ["BOM", `¥${value(brief, "bom")}`, "传感、通信、结构、安装"],
    ["PRICE", `¥${value(brief, "price")}`, "单校建议售价"],
    ["SERVICE", `¥${value(brief, "service-fee")}/Y`, "年度运维与模型服务"],
  ];
  specs.forEach((spec, i) => {
    const y = 1.95 + i * 1.48;
    text(slide, spec[0], 8.32, y, 1.3, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 1.6 });
    text(slide, spec[1], 8.3, y + 0.34, 3.3, 0.62, 28, theme.white, { fontFace: MONO, bold: true });
    text(slide, spec[2], 8.32, y + 0.96, 3.45, 0.33, 10, theme.pale);
    slide.addShape(SHAPE.line, { x: 8.3, y: y + 1.34, w: 3.7, h: 0, line: { color: theme.accent, transparency: 55, width: 1 } });
  });
  notes(slide, factIds, "native-product-dashboard-and-commercial-proof");
}

function academicHeroCover(pptx, theme) {
  const slide = pptx.addSlide();
  fullImage(slide, theme.hero);
  veil(slide, theme.deep, 4, 0, 0, 7.55, H);
  slide.addShape(SHAPE.parallelogram, {
    x: -0.45, y: 0.25, w: 7.8, h: 6.95, rotate: -2.5,
    fill: { color: theme.deep, transparency: 0 },
    line: { color: theme.accent, width: 1.4, transparency: 12 },
  });
  text(slide, "THESIS DEFENSE / EVIDENCE FIRST", 0.78, 0.62, 4.8, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.5 });
  text(slide, "面向交通流预测", 0.78, 1.18, 4.8, 0.46, 17, theme.cyan, { bold: true });
  text(slide, "多尺度动态图\nTransformer", 0.75, 1.7, 6.25, 1.72, 38, theme.white, { fontFace: DISPLAY, bold: true });
  text(slide, "MDG", 4.82, 0.88, 2.2, 1.12, 44, theme.accent, { fontFace: MONO, bold: true, align: "right" });
  slide.addShape(SHAPE.line, { x: 0.8, y: 3.68, w: 1.45, h: 0, line: { color: theme.accent, width: 4 } });
  const tags = [
    ["01", "DYNAMIC GRAPH", "状态驱动关系"],
    ["02", "MULTISCALE", "局部—区域—全局"],
    ["03", "CURRICULUM", "短窗到长窗"],
  ];
  tags.forEach((tag, i) => {
    const x = 0.8 + i * 2.05;
    box(slide, x, 4.12, 1.82, 1.05, i === 0 ? theme.accent : theme.deep, 0.1, { color: i === 0 ? theme.accent : theme.cyan, width: 1.1, transparency: 20 });
    text(slide, tag[0], x + 0.14, 4.27, 0.38, 0.26, 9, i === 0 ? theme.deep : theme.accent, { fontFace: MONO, bold: true });
    text(slide, tag[1], x + 0.14, 4.52, 1.52, 0.24, 8, i === 0 ? theme.deep : theme.white, { fontFace: MONO, bold: true });
    text(slide, tag[2], x + 0.14, 4.8, 1.5, 0.22, 8, i === 0 ? theme.deep : theme.pale, { bold: true });
  });
  text(slide, "硕士学位论文答辩  ·  证据 / 边界 / 可复现", 0.82, 6.25, 5.55, 0.36, 10, theme.white, { fontFace: MONO, bold: true, charSpacing: 0.8 });
  text(slide, "2026", 11.15, 6.35, 1.45, 0.42, 16, theme.accent, { fontFace: MONO, bold: true, align: "right" });
  notes(slide, [], "academic-method-integrated-hero-cover");
}

function academicGraphArchitecture(pptx, theme, index, titleValue, factIds) {
  const slide = pptx.addSlide();
  slide.background = { color: theme.deep };
  text(slide, "MODEL ARCHITECTURE / STATE-DRIVEN", 0.65, 0.52, 4.6, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.1 });
  text(slide, titleValue, 0.62, 0.9, 8.9, 0.85, 27, theme.white, { bold: true });
  const stages = [
    [1.05, 3.45, "INPUT", "节点状态\n时间编码"],
    [4.0, 2.3, "DYNAMIC", "状态驱动\n图关系"],
    [7.0, 4.1, "MULTISCALE", "局部 / 区域\n全局融合"],
    [10.45, 2.72, "FORECAST", "15 / 30 / 60\n分钟预测"],
  ];
  stages.forEach(([x, y, label, detail], i) => {
    if (i < stages.length - 1) {
      const [nx, ny] = stages[i + 1];
      slide.addShape(SHAPE.line, { x: x + 0.9, y: y + 0.45, w: nx - x - 0.15, h: ny - y, line: { color: theme.cyan, width: 2, transparency: 12, endArrowType: "triangle" } });
    }
    for (let n = 0; n < 4; n += 1) {
      const angle = (n / 4) * Math.PI * 2;
      const nx = x + 0.42 + Math.cos(angle) * 0.62;
      const ny = y + 0.42 + Math.sin(angle) * 0.62;
      slide.addShape(SHAPE.line, { x: x + 0.42, y: y + 0.42, w: nx - x - 0.22, h: ny - y - 0.22, line: { color: i === 1 ? theme.accent : theme.cyan, transparency: 35, width: 1 } });
      slide.addShape(SHAPE.ellipse, { x: nx, y: ny, w: 0.16, h: 0.16, fill: { color: i === 1 ? theme.accent : theme.cyan }, line: { color: theme.white, transparency: 45 } });
    }
    slide.addShape(SHAPE.ellipse, { x, y, w: 0.85, h: 0.85, fill: { color: i === 1 ? theme.accent : theme.cyan, transparency: 10 }, line: { color: theme.white, width: 1.4, transparency: 15 } });
    text(slide, `0${i + 1}`, x + 0.16, y + 0.2, 0.52, 0.4, 12, theme.deep, { fontFace: MONO, bold: true, align: "center" });
    text(slide, label, x - 0.5, y + 1.32, 1.9, 0.32, 9, i === 1 ? theme.accent : theme.cyan, { fontFace: MONO, bold: true, align: "center" });
    text(slide, detail, x - 0.55, y + 1.7, 2.0, 0.65, 11, theme.pale, { align: "center" });
  });
  text(slide, "关系随状态更新，尺度随任务交互，难度随训练阶段递进。", 0.75, 6.45, 8.0, 0.4, 13, theme.white, { bold: true });
  notes(slide, factIds, "dynamic-graph-architecture-scene");
}

function academicMultiscaleScene(pptx, theme, index, titleValue, factIds) {
  const slide = pptx.addSlide("BODY");
  slide.background = { color: theme.bg };
  header(slide, theme, index, "Representation / multiscale", titleValue);
  const centers = [
    { d: 1.1, color: theme.accent, label: "LOCAL", detail: "相邻节点\n细粒度扰动" },
    { d: 2.45, color: theme.cyan, label: "REGIONAL", detail: "功能区\n中程传播" },
    { d: 4.0, color: theme.ink, label: "GLOBAL", detail: "路网级\n长周期模式" },
  ];
  centers.slice().reverse().forEach((ring) => {
    slide.addShape(SHAPE.ellipse, { x: 3.65 - ring.d / 2, y: 4.05 - ring.d / 2, w: ring.d, h: ring.d, fill: { color: theme.bg, transparency: 100 }, line: { color: ring.color, width: 2.2, transparency: 5 } });
  });
  for (let i = 0; i < 6; i += 1) {
    const a = (i / 6) * Math.PI * 2;
    const r = i % 3 === 0 ? 1.75 : i % 2 === 0 ? 1.05 : 0.48;
    const x = 3.55 + Math.cos(a) * r;
    const y = 3.95 + Math.sin(a) * r;
    slide.addShape(SHAPE.ellipse, { x, y, w: 0.24, h: 0.24, fill: { color: i % 3 === 0 ? theme.ink : i % 2 === 0 ? theme.cyan : theme.accent }, line: { color: theme.white, width: 1 } });
  }
  centers.forEach((ring, i) => {
    const y = 1.95 + i * 1.35;
    box(slide, 7.18, y - 0.16, 4.95, 0.92, i === 0 ? theme.deep : theme.surface, 0.1, { color: ring.color, width: 1.1, transparency: 48 });
    text(slide, `0${i + 1}`, 7.42, y + 0.06, 0.5, 0.3, 11, ring.color, { fontFace: MONO, bold: true });
    text(slide, ring.label, 8.1, y + 0.02, 1.55, 0.36, 15, i === 0 ? theme.white : theme.ink, { fontFace: MONO, bold: true });
    text(slide, ring.detail.replace("\n", " · "), 9.55, y + 0.02, 2.25, 0.4, 12, i === 0 ? theme.pale : theme.muted, { bold: true });
  });
  box(slide, 7.22, 5.92, 4.85, 0.72, theme.deep);
  text(slide, "门控融合  →  单一、可训练的联合表征", 7.45, 6.12, 4.38, 0.3, 11, theme.white, { bold: true, align: "center" });
  notes(slide, factIds, "concentric-multiscale-representation");
}

function academicCurriculum(pptx, theme, index, titleValue, factIds) {
  const slide = pptx.addSlide("BODY");
  header(slide, theme, index, "Training protocol / curriculum", titleValue);
  const steps = [
    { x: 0.82, y: 4.95, w: 2.5, h: 1.1, title: "短窗稳定", sub: "15 min · 基础周期" },
    { x: 3.32, y: 4.1, w: 2.5, h: 1.95, title: "逐步扩展", sub: "30 min · 扰动增强" },
    { x: 5.82, y: 3.15, w: 2.5, h: 2.9, title: "统一评估", sub: "60 min · 固定协议" },
    { x: 8.32, y: 2.05, w: 3.65, h: 4.0, title: "五次重复", sub: "均值 + 标准差" },
  ];
  steps.forEach((step, i) => {
    box(slide, step.x, step.y, step.w, step.h, i === 3 ? theme.deep : i === 2 ? theme.pale : theme.surface, 0.08, { color: i === 3 ? theme.deep : theme.accent, transparency: i === 3 ? 100 : 55, width: 1 });
    text(slide, `0${i + 1}`, step.x + 0.2, step.y + 0.18, 0.5, 0.3, 10, theme.accent, { fontFace: MONO, bold: true });
    text(slide, step.title, step.x + 0.2, step.y + 0.55, step.w - 0.4, 0.48, 17, i === 3 ? theme.white : theme.ink, { bold: true });
    text(slide, step.sub, step.x + 0.2, step.y + step.h - 0.5, step.w - 0.4, 0.28, 9, i === 3 ? theme.pale : theme.muted);
  });
  slide.addShape(SHAPE.line, { x: 1.0, y: 6.38, w: 11.2, h: -4.72, line: { color: theme.accent, width: 2, transparency: 10, endArrowType: "triangle" } });
  text(slide, "PREDICTION DIFFICULTY", 9.25, 1.18, 2.8, 0.25, 7, theme.accent, { fontFace: MONO, bold: true, charSpacing: 1.8, align: "right" });
  notes(slide, factIds, "ascending-curriculum-staircase");
}

function dataTable(pptx, theme, index, titleValue, rows, factIds) {
  const slide = pptx.addSlide("BODY");
  header(slide, theme, index, "Evidence / table", titleValue);
  slide.addTable(rows, {
    x: 0.7, y: 1.8, w: 11.95, h: 4.65,
    border: { color: theme.pale, width: 1 },
    fill: theme.surface, color: theme.ink,
    fontFace: FONT, fontSize: 11, margin: 0.1,
    rowH: 0.55,
    bold: false,
    autoFit: false,
    valign: "mid",
  });
  notes(slide, factIds, "native-evidence-table");
}

function statement(pptx, theme, index, kicker, titleValue, detail, dark = true) {
  const slide = pptx.addSlide();
  slide.background = { color: dark ? theme.deep : theme.bg };
  addDiagonalBands(slide, theme, dark);
  text(slide, kicker.toUpperCase(), 0.75, 0.72, 3.8, 0.28, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 2.4 });
  text(slide, titleValue, 0.72, 1.45, 9.7, 2.05, 38, dark ? theme.white : theme.ink, { bold: true });
  slide.addShape(SHAPE.line, { x: 0.78, y: 4.05, w: 1.5, h: 0, line: { color: theme.accent, width: 4 } });
  text(slide, detail, 0.78, 4.42, 7.8, 1.0, 15, dark ? theme.pale : theme.muted);
  text(slide, String(index).padStart(2, "0"), 11.35, 5.95, 1.15, 0.75, 28, theme.accent, { fontFace: MONO, bold: true, align: "right" });
  notes(slide, [], "editorial-statement");
}

function heroClosing(pptx, theme, titleValue, detail, dark = false) {
  const slide = pptx.addSlide();
  fullImage(slide, theme.hero);
  veil(slide, dark ? theme.deep : theme.bg, dark ? 0 : 8, 0, 0, 7.8, H);
  addRings(slide, theme, 10.5, 3.7, 5);
  text(slide, "THANK YOU", 1.08, 0.82, 3.5, 0.3, 8, theme.accent, { fontFace: MONO, bold: true, charSpacing: 3 });
  text(slide, titleValue, 1.05, 1.58, 6.2, 1.65, 42, dark ? theme.white : theme.ink, { bold: true });
  slide.addShape(SHAPE.line, { x: 1.12, y: 3.75, w: 1.45, h: 0, line: { color: theme.accent, width: 4 } });
  text(slide, detail, 1.12, 4.15, 5.45, 0.85, dark ? 17 : 16, dark ? theme.white : theme.ink, { bold: true });
  notes(slide, [], "hero-closing");
}

function buildWork(brief) {
  const theme = themes.work;
  const pptx = deck(theme);
  const pages = [];
  const add = (role, family, density, candidate) => pages.push({ slide_id: `work-${String(pages.length + 1).padStart(2, "0")}`, role, family, density, candidate_id: candidate });
  heroCover(pptx, theme, "ANNUAL OPERATING REVIEW", theme.title, theme.subtitle, "经营委员会 · 2026.12 · 数据截至 Q4");
  add("cover", "hero-cover", "sparse", "physical:8bbb2d4929291ae2a82ac05746fbc02418661a38ad5f7f78b031f62fa7e131c4:001");
  agenda(pptx, theme, [["年度答卷", "目标不是平均主义，而是识别兑现与偏差"], ["价值落地", "治理、迁移、自助分析形成经营闭环"], ["组织能力", "让指标、责任与复盘机制真正运转"], ["明年行动", "三项优先级需要当场批准"]]);
  add("agenda", "agenda-editorial", "medium", "physical:8be034592bf51420bd402f6af0fa60f60e76720446f71b89f307c36abdf7055e:001");
  chapter(pptx, theme, 1, "年度答卷", "四个数字，先定义这一年的经营质量。");
  add("section", "chapter-reset", "sparse", "native:section.centered");
  bigMetrics(pptx, theme, 4, "增长不是单点突破，而是客户、效率、质量同时向上", [
    { value: value(brief, "customers-actual"), label: "CUSTOMERS", detail: `目标 ${value(brief, "customers-target")} 家 · 超额 4 家` },
    { value: `${value(brief, "self-service-actual")}%`, label: "SELF SERVICE", detail: `高于目标 ${value(brief, "self-service-target")}%` },
    { value: `${value(brief, "availability-q4")}%`, label: "AVAILABILITY", detail: "核心平台可用性继续改善" },
    { value: `¥${value(brief, "annual-savings")}M`, label: "ANNUAL SAVING", detail: "经财务确认的年度化估算" },
  ], ["customers-actual", "customers-target", "self-service-actual", "availability-q4", "annual-savings"]);
  add("summary", "asymmetric-big-metrics", "medium", "native:focal-statement.editorial-left");
  chartScene(pptx, theme, 5, "客户增长连续四季上行，Q4 越过年度目标", [{
    name: "客户数", labels: ["Q1", "Q2", "Q3", "Q4"], values: ["customer-count-q1", "customer-count-q2", "customer-count-q3", "customer-count-q4"].map((id) => value(brief, id)),
  }], `${value(brief, "customers-actual")} 家`, "Q4 CUSTOMERS", ["customer-count-q1", "customer-count-q2", "customer-count-q3", "customer-count-q4"]);
  add("data", "chart-scene-line", "dense", "native:trend-line.editorial");
  chartScene(pptx, theme, 6, "月活从 1,840 增至 4,260，使用深度跟上客户扩张", [{
    name: "月活", labels: ["Q1", "Q2", "Q3", "Q4"], values: ["monthly-active-users-q1", "monthly-active-users-q2", "monthly-active-users-q3", "monthly-active-users-q4"].map((id) => value(brief, id)),
  }], "2.3×", "Q1 → Q4", ["monthly-active-users-q1", "monthly-active-users-q4"]);
  add("data", "chart-scene-line", "dense", "native:trend-line.editorial");
  dataTable(pptx, theme, 7, "效率、质量与成本同时改善，增长没有透支底盘", [
    [
      { text: "指标", options: { bold: true, color: theme.white, fill: theme.deep } },
      { text: "Q1", options: { bold: true, color: theme.white, fill: theme.deep } },
      { text: "Q2", options: { bold: true, color: theme.white, fill: theme.deep } },
      { text: "Q3", options: { bold: true, color: theme.white, fill: theme.deep } },
      { text: "Q4", options: { bold: true, color: theme.white, fill: theme.deep } },
    ],
    ["自助分析率", "38%", "46%", "57%", "68%"],
    ["报表 SLA", "89%", "92%", "95%", "97%"],
    ["P1 事故", "6", "4", "3", "2"],
    ["千次查询成本", "¥8.4", "¥7.6", "¥6.9", "¥6.1"],
  ], ["self-service-rate-q1", "self-service-rate-q4", "report-sla-q1", "report-sla-q4", "p1-incidents-q1", "p1-incidents-q4", "query-cloud-cost-q1", "query-cloud-cost-q4"]);
  add("table", "native-evidence-table", "dense", "native:table.editorial");
  chapter(pptx, theme, 2, "价值落地", "把“指标多”变成“指标可信、可复用、有人负责”。");
  add("section", "chapter-reset", "sparse", "native:section.centered");
  beforeAfter(pptx, theme, 9, "指标治理把重复口径压缩为可复用资产", {
    value: value(brief, "duplicates-before"), label: "重复指标口径", detail: "口径冲突、重复建设、责任不清晰",
  }, {
    value: value(brief, "duplicates-after"), label: "剩余核心口径", detail: `${value(brief, "governed-metrics")} 项指标完成治理并纳入责任体系`,
  }, ["duplicates-before", "duplicates-after", "governed-metrics"]);
  add("comparison", "before-after-diptych", "medium", "native:comparison.editorial");
  processFlow(pptx, theme, 10, "从需求到价值：四步闭环替代一次性交付", [
    { title: "定义问题", detail: "围绕经营决策，而不是功能清单。" },
    { title: "统一口径", detail: "事实、指标、数据责任一次绑定。" },
    { title: "共创验证", detail: "用真实业务场景验证可用性。" },
    { title: "运营复盘", detail: "SLA、采用、成本共同进入复盘。" },
  ], []);
  add("process", "staggered-process", "medium", "physical:f30afd654c12b57d0be8993d5505ae1a46a27221c9a615f1a46993b58c4248b7:001");
  matrix(pptx, theme, 11, "组织能力不是头像墙，而是六个可交付角色", [
    { kicker: "GOVERNANCE", title: "指标治理", detail: "统一口径、责任人与变更机制" },
    { kicker: "DATA", title: "数据工程", detail: "质量、血缘、成本和可用性" },
    { kicker: "PRODUCT", title: "自助分析", detail: "模板、引导与采用率运营" },
    { kicker: "CUSTOMER", title: "客户迁移", detail: `${value(brief, "unmigrated-customers")} 家待迁移客户专项推进` },
    { kicker: "FINANCE", title: "价值确认", detail: "成本与节省口径由财务确认" },
    { kicker: "REVIEW", title: "经营复盘", detail: "季度事实、偏差和动作闭环" },
  ], ["unmigrated-customers"]);
  add("organization", "six-cell-matrix", "dense", "physical:9e78d6233d8d7388ea578dcacc84dda930961c03e3035c7294ea23a17d05e4b6:001");
  chapter(pptx, theme, 3, "明年行动", "资源不平均分配：聚焦治理、迁移和自助分析。");
  add("section", "chapter-reset", "sparse", "native:section.centered");
  processFlow(pptx, theme, 13, "四个季度，把优先级变成可验收里程碑", [
    { title: "Q1 · 定责", detail: "17 项无主指标全部明确责任。" },
    { title: "Q2 · 迁移", detail: "完成 3 家重点客户迁移。" },
    { title: "Q3 · 深化", detail: "自助分析场景扩展到核心团队。" },
    { title: "Q4 · 复制", detail: "形成可复制的治理与迁移套件。" },
  ], ["unowned-metrics", "unmigrated-customers"]);
  add("roadmap", "staggered-process", "medium", "physical:27dd147759da5f877b0c99adbb97f020ad70f3dd9fa2a490b1e96bff397c324c:001");
  statement(pptx, theme, 14, "Decision ask", "批准三项优先级：\n治理优先、迁移收口、采用深化", "2027 年的目标不是再做更多页面，而是让已经验证的能力规模化。");
  add("decision", "editorial-statement", "sparse", "native:focal-statement.centered");
  heroClosing(pptx, theme, "工作未完待续，\n能力开始复利", "让每一次增长，都能被事实解释、被团队复制、被客户感知。");
  add("closing", "hero-closing", "sparse", "physical:1fe4436abbca3fd507e9256c68dab9b1d7adda8a1179592ce25f1ac575460eee:001");
  return { pptx, pages, scenario: "annual-work-report", theme: "work-reference-emerald-gold" };
}

function buildCampus(brief) {
  const theme = themes.campus;
  const light = {
    ...theme,
    bg: "F3EFE6",
    ink: "123B4B",
    deep: "07304A",
    accent: "00AFA5",
    surface: "FFFDF8",
    pale: "D7E6E2",
    muted: "5E7378",
  };
  const pptx = deck(theme);
  const pages = [];
  const add = (role, family, density, candidate) => pages.push({ slide_id: `campus-${String(pages.length + 1).padStart(2, "0")}`, role, family, density, candidate_id: candidate });
  heroCover(pptx, light, "CAMPUS INNOVATION / FINAL", theme.title, theme.subtitle, "省赛终审 · 22 MIN · 真实单校试点", false);
  add("cover", "hero-cover", "sparse", "native:cover.editorial");
  agenda(pptx, light, [["为什么现在", "真实需求、现有盲区与可验证问题"], ["我们做了什么", "感知、边缘、云端与运维闭环"], ["为什么可行", "84 天数据、算法效果与市场模型"], ["下一步决定", "多校验证、质量门槛与资源请求"]], false);
  add("agenda", "agenda-editorial", "medium", "native:agenda.grid-four");
  bigMetrics(pptx, light, 3, "84 天真实试点，把“可演示”推进到“可验证”", [
    { value: `${value(brief, "pilot-days")} 天`, label: "PILOT", detail: "完整覆盖一个校园运行周期" },
    { value: value(brief, "sensor-nodes"), label: "传感节点 / SENSOR NODES", detail: `${value(brief, "sampling-interval")} 分钟采样一次` },
    { value: `${value(brief, "valid-rate")}%`, label: "有效数据率 / VALID DATA", detail: `${value(brief, "valid-records").toLocaleString()} 条有效记录` },
    { value: `${value(brief, "lead-time")} min`, label: "平均提前量 / LEAD TIME", detail: "为现场处置争取提前量" },
  ], ["pilot-days", "sensor-nodes", "sampling-interval", "valid-rate", "valid-records", "lead-time"], false);
  add("summary", "asymmetric-big-metrics", "medium", "native:focal-statement.editorial-left");
  campusChapter(pptx, light, 1, "为什么现在", "校园水环境的风险不是没有数据，而是没有形成行动链路。", "field");
  add("section", "chapter-reset", "sparse", "native:section.centered");
  matrix(pptx, light, 5, "91 位访谈者给出同一个信号：发现晚、解释难、协同慢", [
    { kicker: "STUDENT / 38", title: "更早知道", detail: "异常水色、异味和积水需要可信提醒" },
    { kicker: "STAFF / 29", title: "更快定位", detail: "从“哪里有问题”到“哪个节点异常”" },
    { kicker: "MANAGER / 24", title: "更好复盘", detail: "事件、处置与结果需要形成证据链" },
    { kicker: "BLIND SPOT", title: "人工巡检", detail: "固定频次无法覆盖突发变化" },
    { kicker: "BLIND SPOT", title: "离线记录", detail: "数据分散，无法统一解释" },
    { kicker: "BLIND SPOT", title: "责任交接", detail: "跨部门沟通依赖人工转述" },
  ], ["student-interviews", "staff-interviews", "manager-interviews"]);
  add("research", "six-cell-matrix", "dense", "native:multi-card.editorial");
  campusObservationMap(pptx, theme, 6, "一校三类关键区域，构成从水源到使用端的观测地图", ["sensor-nodes"]);
  add("map", "photo-led-campus-observation-map", "medium", "physical:0a0006845139e20a68111886b2035da5deb69bcc4d13d47c8c82829d86dc9365:001");
  campusChapter(pptx, theme, 2, "我们做了什么", "把传感节点、边缘判断、云端证据和现场处置连接成一个产品。", "system");
  add("section", "chapter-reset", "sparse", "native:section.centered");
  campusArchitecture(pptx, theme, 8, "从 10 分钟采样到 42 分钟提前量：四层原生架构", ["sensor-nodes", "sampling-interval", "lead-time"]);
  add("architecture", "layered-campus-system-blueprint", "dense", "physical:9e78d6233d8d7388ea578dcacc84dda930961c03e3035c7294ea23a17d05e4b6:001");
  campusProductScene(pptx, theme, 9, "样机不是概念图：产品界面、成本与服务边界都可解释", brief, ["bom", "price", "service-fee", "lead-time"]);
  add("product", "native-product-dashboard-and-commercial-proof", "medium", "native:product-showcase.dashboard");
  chartScene(pptx, light, 10, "数据完整性足以支撑试点效果评估", [{
    name: "记录", labels: ["理论", "有效"], values: [value(brief, "theoretical-records"), value(brief, "valid-records")],
  }], `${value(brief, "valid-rate")}%`, "VALID RATE", ["theoretical-records", "valid-records", "valid-rate"], "bar");
  add("data", "chart-scene-bar", "dense", "native:bar-chart.editorial");
  bigMetrics(pptx, light, 11, "告警质量必须同时回答：覆盖多少、打扰多少、是否平衡", [
    { value: `${value(brief, "precision")}%`, label: "PRECISION", detail: `${value(brief, "alerts")} 次告警 / ${value(brief, "confirmed-alerts")} 次确认` },
    { value: `${value(brief, "recall")}%`, label: "RECALL", detail: `${value(brief, "actual-events")} 次真实事件` },
    { value: `${value(brief, "f1")}%`, label: "F1 BALANCE", detail: "覆盖与打扰之间的综合平衡" },
    { value: `${value(brief, "lead-time")} min`, label: "LEAD TIME", detail: "从发现到可行动的提前量" },
  ], ["precision", "recall", "f1", "alerts", "confirmed-alerts", "actual-events", "lead-time"], false);
  add("metrics", "asymmetric-big-metrics", "medium", "native:focal-statement.editorial-left");
  beforeAfter(pptx, light, 12, "巡检投入从每周 9.6 小时降至 4.1 小时", {
    value: value(brief, "hours-before"), label: "小时 / 周", detail: "固定频次人工巡检",
  }, {
    value: value(brief, "hours-pilot"), label: "小时 / 周", detail: "风险触发式现场复核",
  }, ["hours-before", "hours-pilot"]);
  add("comparison", "before-after-diptych", "medium", "native:comparison.editorial");
  campusChapter(pptx, theme, 3, "为什么可行", "技术、产品、市场和服务模型同时成立，才值得进入多校验证。", "scale");
  add("section", "chapter-reset", "sparse", "native:section.centered");
  campusMarketExpansion(pptx, light, 14, "市场不是 4,120 所起跑，而是从 3–5 校验证复制", brief, ["market", "serviceable-market"]);
  add("market", "campus-market-expansion-map", "medium", "native:funnel.editorial");
  campusStakeholderValue(pptx, light, 15, "同一套系统，为三类角色创造不同价值", brief, ["bom", "price", "service-fee"]);
  add("business-model", "campus-stakeholder-value-columns", "dense", "physical:a85b234f697c6b46045ba29b4d6cd82b3776cfa63048e01b9b233627e6a0c31a:001");
  processFlow(pptx, light, 16, "下一阶段不是扩张，而是逐级验证复制条件", [
    { title: "M1 · 完整性", detail: "每校数据完整率稳定达标" },
    { title: "M2 · 告警质量", detail: "明确不同场景阈值与误报边界" },
    { title: "M3 · 运维工时", detail: "验证跨校部署后的真实维护成本" },
    { title: "M4 · 复制", detail: "形成标准交付、培训与服务包" },
  ], []);
  add("roadmap", "staggered-process", "medium", "physical:27dd147759da5f877b0c99adbb97f020ad70f3dd9fa2a490b1e96bff397c324c:001");
  statement(pptx, light, 17, "Decision ask", "请让项目进入省赛终审，\n并批准 3–5 校验证", "我们已经证明链路可运行；下一步要证明它能跨校园复制。", false);
  add("decision", "editorial-statement", "sparse", "native:focal-statement.centered");
  heroClosing(pptx, light, "让每一次异常，\n都更早被看见", "把被动响应，变成可解释、可行动、可复盘的校园安全基础设施。", false);
  add("closing", "hero-closing", "sparse", "native:cta.centered");
  return { pptx, pages, scenario: "campus-competition-defense", theme: "campus-editorial-water-daylight" };
}

function buildAcademic(brief) {
  const theme = themes.academic;
  const pptx = deck(theme);
  const pages = [];
  const add = (role, family, density, candidate) => pages.push({ slide_id: `academic-${String(pages.length + 1).padStart(2, "0")}`, role, family, density, candidate_id: candidate });
  academicHeroCover(pptx, theme);
  add("cover", "academic-method-integrated-hero-cover", "sparse", "native:cover.editorial");
  agenda(pptx, theme, [["研究问题", "现有方法的三个断点与研究问题"], ["方法设计", "动态图、多尺度交互与课程训练"], ["实验结果", "对比、消融、鲁棒性与效率证据"], ["结论边界", "贡献、限制与答辩决定"]], true);
  add("agenda", "agenda-editorial", "medium", "native:agenda.grid-four");
  bigMetrics(pptx, theme, 3, "问题、方法、证据和边界，在一页内闭环", [
    { value: "2", label: "DATASETS", detail: "METR-LA / PEMS-BAY" },
    { value: "3", label: "HORIZONS", detail: "15 / 30 / 60 分钟" },
    { value: "2.58", label: "BEST MAE", detail: "METR-LA · 15 min" },
    { value: "3.18M", label: "PARAMS", detail: "10.6 ms 推理延迟" },
  ], ["metr-sensors", "pems-sensors", "mae-mdgformer-metr-la-15min", "params-ours", "latency-ours"]);
  add("abstract", "asymmetric-big-metrics", "medium", "native:focal-statement.editorial-left");
  chapter(pptx, theme, 1, "研究问题", "固定图假设、单尺度交互和训练稳定性，共同限制长期预测。", false);
  add("section", "chapter-reset", "sparse", "native:section.centered");
  matrix(pptx, theme, 5, "现有方法的三个断点，构成本文的设计空间", [
    { kicker: "GAP 01", title: "图结构是静态的", detail: "事故、潮汐与临时管制会改变节点关系" },
    { kicker: "GAP 02", title: "尺度表达单一", detail: "局部拥堵与区域传播需要同时解释" },
    { kicker: "GAP 03", title: "长程训练不稳定", detail: "预测窗增长时误差与梯度共同放大" },
    { kicker: "EVIDENCE", title: "动态关系", detail: "需要逐时更新的可解释图结构" },
    { kicker: "EVIDENCE", title: "多尺度", detail: "节点、区域和全局交互统一建模" },
    { kicker: "EVIDENCE", title: "课程训练", detail: "从短窗到长窗逐级增加难度" },
  ], []);
  add("gaps", "six-cell-matrix", "dense", "native:multi-card.editorial");
  processFlow(pptx, theme, 6, "三个问题对应三个可证伪实验", [
    { title: "RQ1", detail: "动态图是否改善突发变化下的预测？" },
    { title: "RQ2", detail: "多尺度交互是否稳定提升长预测窗？" },
    { title: "RQ3", detail: "课程训练能否降低长程训练波动？" },
    { title: "验证", detail: "对比、消融、鲁棒性与效率共同回答" },
  ], []);
  add("research-questions", "staggered-process", "medium", "native:process.editorial");
  beforeAfter(pptx, theme, 7, "两套公开交通网络，统一切分与预测窗", {
    value: value(brief, "metr-sensors"), label: "METR-LA SENSORS", detail: `${value(brief, "metr-observations").toLocaleString()} 步 · ${value(brief, "sample-minutes")} 分钟采样`,
  }, {
    value: value(brief, "pems-sensors"), label: "PEMS-BAY SENSORS", detail: `${value(brief, "pems-observations").toLocaleString()} 步 · 70/10/20 切分`,
  }, ["metr-sensors", "metr-observations", "pems-sensors", "pems-observations", "sample-minutes", "split-train", "split-valid", "split-test"]);
  add("datasets", "before-after-diptych", "medium", "native:comparison.editorial");
  chapter(pptx, theme, 2, "方法设计", "关系不是固定邻接表，而是随交通状态更新的多尺度表示。", false);
  add("section", "chapter-reset", "sparse", "native:section.centered");
  academicGraphArchitecture(pptx, theme, 9, "三条研究断点，逐一映射到四阶段动态图架构", []);
  add("architecture", "dynamic-graph-architecture-scene", "dense", "physical:a85b234f697c6b46045ba29b4d6cd82b3776cfa63048e01b9b233627e6a0c31a:001");
  beforeAfter(pptx, theme, 10, "关系不是固定邻接表，而是随交通状态更新", {
    value: "STATIC", label: "固定拓扑", detail: "同一结构解释所有时段与事件",
  }, {
    value: "DYNAMIC", label: "状态驱动图", detail: "边权与传播路径随窗口逐步更新",
  }, []);
  add("method", "before-after-diptych", "medium", "native:comparison.editorial");
  academicMultiscaleScene(pptx, theme, 11, "一个感受野不足以同时解释局部扰动与长程周期", []);
  add("method", "concentric-multiscale-representation", "medium", "physical:0d2ea3cd692d1eb170c91773ba04f5d4675cf188a73acf25e24cdeb502ba5f8d:001");
  academicCurriculum(pptx, theme, 12, "训练协议像课程：逐步增加预测难度，而非假装最优", ["std-15", "std-30", "std-60"]);
  add("training", "ascending-curriculum-staircase", "medium", "physical:27dd147759da5f877b0c99adbb97f020ad70f3dd9fa2a490b1e96bff397c324c:001");
  chapter(pptx, theme, 3, "实验结果", "完整对比优于强基线；消融、鲁棒性和效率共同解释“为什么”。", false);
  add("section", "chapter-reset", "sparse", "native:section.centered");
  chartScene(pptx, theme, 14, "三个预测窗，MDGFormer 均优于最强对照", [
    { name: "STFGNN", labels: ["15 min", "30 min", "60 min"], values: ["mae-stfgnn-metr-la-15min", "mae-stfgnn-metr-la-30min", "mae-stfgnn-metr-la-60min"].map((id) => value(brief, id)) },
    { name: "MDGFormer", labels: ["15 min", "30 min", "60 min"], values: ["mae-mdgformer-metr-la-15min", "mae-mdgformer-metr-la-30min", "mae-mdgformer-metr-la-60min"].map((id) => value(brief, id)) },
  ], "−0.14", "60 MIN / VS STFGNN", ["mae-stfgnn-metr-la-15min", "mae-stfgnn-metr-la-30min", "mae-stfgnn-metr-la-60min", "mae-mdgformer-metr-la-15min", "mae-mdgformer-metr-la-30min", "mae-mdgformer-metr-la-60min"], "bar");
  add("benchmark", "chart-scene-bar", "dense", "native:bar-chart.editorial");
  academicEvidenceGrid(pptx, theme, 15, "预测窗越长，多尺度动态图的优势越明显", [
    { kicker: "15 MIN", title: "2.58 MAE", detail: "相对 STFGNN 改善 0.08" },
    { kicker: "30 MIN", title: "2.92 MAE", detail: "相对 STFGNN 改善 0.10" },
    { kicker: "60 MIN", title: "3.31 MAE", detail: "相对 STFGNN 改善 0.14" },
    { kicker: "ABLATION", title: "− Dynamic", detail: `${value(brief, "ablation-static")} MAE` },
    { kicker: "ABLATION", title: "− Multiscale", detail: `${value(brief, "ablation-scale")} MAE` },
    { kicker: "ABLATION", title: "− Curriculum", detail: `${value(brief, "ablation-curriculum")} MAE` },
  ], ["ablation-full", "ablation-static", "ablation-scale", "ablation-curriculum"]);
  add("ablation", "academic-evidence-grid", "dense", "native:multi-card.editorial");
  beforeAfter(pptx, theme, 16, "缺失数据增加时，模型仍保持更低误差", {
    value: value(brief, "missing-gwn-20"), label: "GRAPH WAVENET / 20%", detail: "缺失比例上升，误差明显扩大",
  }, {
    value: value(brief, "missing-ours-20"), label: "MDGFORMER / 20%", detail: `相对降低 ${(value(brief, "missing-gwn-20") - value(brief, "missing-ours-20")).toFixed(2)} MAE`,
  }, ["missing-gwn-20", "missing-ours-20"]);
  add("robustness", "before-after-diptych", "medium", "native:comparison.editorial");
  chapter(pptx, theme, 4, "结论与边界", "贡献必须与证据强度一致；限制必须进入后续研究，而不是藏在页脚。", false);
  add("section", "chapter-reset", "sparse", "native:section.centered");
  statement(pptx, theme, 18, "Contribution / decision", "动态图、多尺度交互与课程训练，\n共同支撑长程交通流预测", "建议确认论文达到答辩要求；同时补充真实道路事件验证、更多数据集和部署成本分析。", true);
  add("conclusion", "editorial-statement", "sparse", "native:focal-statement.centered");
  heroClosing(pptx, theme, "证据支持答辩，\n边界指导修改", "本文结果来自标准化合成实验日志，仅用于工作流评测，不代表已发表论文结果。", true);
  add("closing", "hero-closing", "sparse", "native:cta.centered");
  return { pptx, pages, scenario: "academic-thesis-defense", theme: "academic-multiscale-night" };
}

const scenarioConfigs = {
  "business-operations-review": {
    title: "连锁门店季度经营复盘", themeKey: "work", signature: "quadrant", heroAsset: "ops-office.jpeg",
    subtitle: "从增长结果回到门店、库存与会员经营动作",
    sections: [["经营诊断", "先确认增长质量，再定位区域与门店差异"], ["问题拆解", "库存、缺货与低效门店形成同一条因果链"], ["行动决策", "整改、调拨和促销资源按优先级落位"]],
    decision: "批准 14 家低效门店整改、库存调拨与下季度促销优先级",
  },
  "project-proposal": {
    title: "制造企业质量数据中台项目提案", themeKey: "cobalt", signature: "architecture", heroAsset: "manufacturing-laser.png",
    subtitle: "16 周建立跨工厂质量事实底座与联合治理机制",
    sections: [["现状与机会", "质量数据分散，人工报表吞噬改进时间"], ["方案与路径", "数据、指标、场景和治理四层协同"], ["范围与决策", "一期范围、预算、里程碑和联合项目组"]],
    decision: "批准 16 周一期范围、360 万元预算和联合项目组",
  },
  "product-launch": {
    title: "企业知识助手产品发布会", themeKey: "aqua", signature: "product", heroAsset: "ai-product.png",
    subtitle: "让可信知识从文档深处进入每一次业务决策",
    sections: [["为什么现在", "知识资产增长速度已经超过人工检索能力"], ["产品如何工作", "检索、回答、证据与治理形成完整体验"], ["上市行动", "试用、定价和伙伴联合销售同步启动"]],
    decision: "开放 30 天试用，并启动 8 家伙伴联合销售计划",
  },
  "market-analysis": {
    title: "中国工业视觉质检软件市场分析", themeKey: "coral", signature: "funnel", heroAsset: "market-globe.jpeg",
    subtitle: "在 68 亿元市场中选择最可赢的两条行业线",
    sections: [["市场判断", "规模增长并不等于每个行业都值得进入"], ["竞争与需求", "访谈、付费意愿和竞争密度共同筛选赛道"], ["战略选择", "汽车零部件优先，消费电子同步验证"]],
    decision: "批准汽车零部件与消费电子两条优先行业线",
  },
  "sales-proposal": {
    title: "区域银行智能营销销售提案", themeKey: "navy", signature: "journey", heroAsset: "sales-city.png",
    subtitle: "以三个月联合验证，把响应率提升转化为可审计回报",
    sections: [["客户机会", "存量客户规模可观，活动响应仍有结构性空间"], ["联合方案", "数据、分群、触达和复盘形成闭环"], ["商务决策", "明确试点范围、预算、目标与退出条件"]],
    decision: "批准三个月联合验证和 120 万元一期采购预算",
  },
  "investor-pitch": {
    title: "工业能效 SaaS Pre-A 轮融资演示", themeKey: "violet", signature: "investor", heroAsset: "investor-tech.jpeg",
    subtitle: "用可复制增长与健康单位经济证明下一阶段规模化",
    sections: [["增长证明", "ARR、客户与留存共同验证产品市场匹配"], ["商业引擎", "高毛利订阅与可控获客形成增长飞轮"], ["融资命题", "资金用途与 24 个月里程碑清晰可验证"]],
    decision: "进入尽调并讨论 3000 万元 Pre-A 轮投资",
  },
  "strategy-planning": {
    title: "2027–2029 海外增长战略规划", themeKey: "terra", signature: "horizon", heroAsset: "strategy-factory.png",
    subtitle: "东南亚优先、欧洲验证：用资源取舍换三年确定性",
    sections: [["战略事实", "海外业务已有基础，但资源仍然分散"], ["区域选择", "增长、进入难度与产品适配决定优先级"], ["三年路径", "市场、产品和组织能力分阶段投入"]],
    decision: "批准东南亚优先、欧洲验证的三年资源配置方案",
  },
  "data-analysis-report": {
    title: "订阅产品流失驱动因素分析", themeKey: "academic", signature: "ranking", heroAsset: "data-isometric.png",
    subtitle: "把 48,200 个账户的信号转化为 90 天增长实验",
    sections: [["问题定义", "总体流失率掩盖了三个高风险人群"], ["驱动证据", "入门、支持与低使用共同解释可干预空间"], ["实验决策", "围绕前三项驱动因素建立可证伪实验"]],
    decision: "批准前三项流失驱动因素的 90 天实验计划",
  },
  "training-course": {
    title: "一线经理结构化复盘培训", themeKey: "amber", signature: "staircase", heroAsset: "training-presenter.png",
    subtitle: "180 分钟，从讲道理到完成一次可观察的团队复盘",
    sections: [["学习目标", "复盘不是回顾，而是用事实改善下一次行动"], ["课堂体验", "案例、练习、反馈与评估形成学习闭环"], ["迁移落地", "30 天内把方法带回真实团队场景"]],
    decision: "每位学员完成一次可观察、可行动的团队复盘",
  },
  "brand-company-introduction": {
    title: "新能源材料公司品牌与能力介绍", themeKey: "lime", signature: "constellation", heroAsset: "brand-green.png",
    subtitle: "从研发、制造到客户验证，建立可信而克制的品牌叙事",
    sections: [["我们是谁", "八年成长形成研发与制造双重底盘"], ["我们能做什么", "专利、产线、产能与市场覆盖共同证明能力"], ["合作下一步", "从能力认知进入客户验证与联合开发"]],
    decision: "推动目标客户进入样品验证或合作洽谈",
  },
  "project-kickoff": {
    title: "集团 ERP 云迁移项目启动会", themeKey: "slate", signature: "governance", heroAsset: "kickoff-digital.png",
    subtitle: "23 家主体、4 个批次、14 个月：先把协同规则说清楚",
    sections: [["共同目标", "范围、成功标准与不可突破约束统一"], ["治理与路径", "决策、交付、升级和批次迁移形成机制"], ["立即行动", "关键里程碑、九项风险与首月任务落位"]],
    decision: "确认范围、治理机制、关键里程碑和风险升级路径",
  },
  "ecommerce-marketing-plan": {
    title: "双十一全域电商增长方案", themeKey: "magenta", signature: "calendar", heroAsset: "campaign-runner.jpeg",
    subtitle: "28 天战役，把预算、货品、内容和会员经营编成同一节奏",
    sections: [["增长命题", "1.2 亿元目标需要拆成可执行的经营杠杆"], ["战役编排", "渠道、内容、货品与供应链按节奏协同"], ["预算决策", "1800 万元资源绑定 ROAS 与新客目标"]],
    decision: "批准 1800 万元预算分配、货品策略和战役节奏",
  },
};

const claimLabels = {
  revenue: "季度收入", "revenue-growth": "收入同比", "gross-margin": "毛利率",
  "same-store-growth": "同店增长", "inventory-days": "库存周转", "stockout-rate": "缺货率",
  sites: "工厂范围", "source-systems": "源系统", "quality-records": "质量记录",
  "manual-report-hours": "人工报表", "phase-one-weeks": "一期周期", budget: "预算",
  "pilot-customers": "试点客户", "documents-indexed": "索引文档", "answer-acceptance": "回答采纳率",
  "median-response": "响应时间", tam: "TAM", sam: "SAM", som: "SOM", "market-cagr": "市场 CAGR",
  customers: "客户规模", campaigns: "月均活动", "response-rate": "当前响应率",
  "target-response": "试点目标", arr: "ARR", "arr-growth": "ARR 同比", "net-retention": "净收入留存",
  "overseas-revenue": "海外收入", "overseas-share": "海外占比", "target-share": "目标占比",
  accounts: "分析账户", "churn-rate": "月流失率", "model-auc": "模型 AUC",
  learners: "班级人数", duration: "课程时长", modules: "课程模块",
  founded: "成立年份", employees: "员工", patents: "专利", "annual-capacity": "年产能",
  entities: "业务主体", users: "用户", interfaces: "接口", waves: "迁移批次",
  "gmv-target": "GMV 目标", "roas-target": "ROAS 目标", "new-customer-target": "新客目标",
};

const scopeLabels = {
  design: "课程设计", assessment: "学习评估", transfer: "训后迁移",
  scope: "一期范围", baseline: "当前基线", proposal: "方案目标",
  target: "目标值", launch: "上市阶段", campaign: "战役周期",
  company: "公司历程", plan: "执行计划", kickoff: "启动阶段",
  research: "调研样本", estimate: "审慎估算", round: "本轮融资",
  experiment: "实验记录", validation: "验证集", median: "中位数",
};

function displayScope(fact) {
  const scope = String(fact.time_scope || "锁定事实");
  return scopeLabels[scope] || scope;
}

function displayFact(fact) {
  const source = fact.value ?? fact.text ?? "—";
  const raw = typeof source === "number" ? source.toLocaleString("zh-CN") : String(source);
  return `${raw}${fact.unit || ""}`;
}

function factTitle(fact) {
  const key = fact.claim_key || fact.kind || fact.id;
  return claimLabels[key] || String(key).replaceAll("-", " ").toUpperCase();
}

function assetRoleLabel(asset) {
  const role = String(asset.role || asset.id || "material");
  const labels = {
    "product-hero": "产品主视觉",
    "ui-mockup": "界面实机画面",
    "demo-journey": "演示旅程",
    "brand-hero": "品牌主视觉",
    "team-portrait": "团队肖像",
    "evidence-chart": "证据图表",
    "market-map": "市场地图",
    "customer-proof": "客户证据",
  };
  return labels[role] || role.replaceAll("-", " ").toUpperCase();
}

function scenarioSignature(pptx, theme, index, config, facts) {
  const slide = pptx.addSlide("BODY");
  header(slide, theme, index, "Scenario signature / governed visual", config.sections[1][0]);
  const label = (factIndex) => {
    const fact = facts[factIndex % facts.length];
    return `${factTitle(fact)}\n${displayFact(fact)}`;
  };
  const darkFill = theme.deep;
  if (config.signature === "architecture") {
    const layerTitles = [
      factTitle(facts[0]),
      factTitle(facts[1]),
      factTitle(facts[2]),
      config.sections[2][0],
    ];
    [0, 1, 2, 3].forEach((item) => {
      const x = 1.0 + item * 0.72;
      const y = 5.5 - item * 1.02;
      const w = 10.9 - item * 1.44;
      box(slide, x, y, w, 0.74, item === 3 ? theme.accent : item === 0 ? darkFill : theme.surface, 0.08, { color: theme.accent, width: 1.1, transparency: 30 });
      text(slide, layerTitles[item], x + 0.28, y + 0.16, 3.6, 0.34, 13, item === 0 ? theme.white : theme.ink, { bold: true });
      text(slide, label(item), x + w - 2.6, y + 0.1, 2.25, 0.48, 9, item === 0 ? theme.pale : theme.muted, { align: "right", bold: true });
    });
  } else if (config.signature === "product") {
    [0, 1, 2].forEach((item) => {
      const x = 0.85 + item * 4.02;
      box(slide, x, 1.8 + item * 0.28, 3.45, 4.45 - item * 0.35, item === 1 ? darkFill : theme.surface, 0.12, { color: theme.accent, width: 1.2, transparency: 25 });
      text(slide, ["01 / SEARCH", "02 / ANSWER", "03 / GOVERN"][item], x + 0.3, 2.08 + item * 0.28, 2.85, 0.28, 7, item === 1 ? theme.pale : theme.muted, { fontFace: MONO, bold: true, charSpacing: 1.2 });
      if (item === 0) {
        box(slide, x + 0.3, 2.62, 2.85, 0.48, theme.pale, 0.08);
        text(slide, "输入业务问题…", x + 0.52, 2.73, 2.3, 0.24, 9, theme.muted);
        ["销售政策", "项目复盘", "产品规范"].forEach((labelValue, row) => {
          box(slide, x + 0.3, 3.35 + row * 0.52, 2.85, 0.34, row === 0 ? theme.accent : theme.surface, 0.05, { color: theme.accent, width: 0.8, transparency: 45 });
          text(slide, labelValue, x + 0.5, 3.41 + row * 0.52, 2.2, 0.22, 8, row === 0 ? theme.white : theme.ink, { bold: true });
        });
      } else if (item === 1) {
        text(slide, "结论先行", x + 0.3, 2.75, 2.85, 0.34, 13, theme.white, { bold: true });
        [2.0, 2.45, 1.65].forEach((width, row) => box(slide, x + 0.3, 3.35 + row * 0.45, width, 0.2, theme.surface, 0.03));
        box(slide, x + 0.3, 4.95, 2.85, 0.56, theme.accent, 0.06);
        text(slide, "3 条原文证据 · 可追溯", x + 0.48, 5.08, 2.5, 0.25, 8, theme.white, { bold: true });
      } else {
        [["权限策略", "24"], ["知识空间", "18"], ["审计事件", "1,284"]].forEach(([labelValue, count], row) => {
          text(slide, labelValue, x + 0.3, 2.72 + row * 0.72, 1.65, 0.28, 9, theme.ink, { bold: true });
          text(slide, count, x + 2.0, 2.65 + row * 0.72, 1.1, 0.34, 14, theme.accent, { fontFace: MONO, bold: true, align: "right" });
          slide.addShape(SHAPE.line, { x: x + 0.3, y: 3.1 + row * 0.72, w: 2.85, h: 0, line: { color: theme.pale, width: 1 } });
        });
      }
      text(slide, ["可信检索", "证据回答", "管理治理"][item], x + 0.3, 5.62, 2.85, 0.38, 15, item === 1 ? theme.white : theme.ink, { bold: true });
    });
  } else if (config.signature === "funnel") {
    const widths = [9.8, 7.2, 4.8];
    widths.forEach((w, item) => {
      const x = 6.7 - w / 2;
      const y = 1.85 + item * 1.48;
      slide.addShape(SHAPE.chevron, { x, y, w, h: 1.0, fill: { color: item === 2 ? theme.accent : item === 1 ? theme.pale : darkFill, transparency: item === 1 ? 0 : 4 }, line: { color: theme.bg, transparency: 100 } });
      text(slide, ["TAM · 全市场", "SAM · 优先行业", "SOM · 可赢目标"][item], x + 0.35, y + 0.23, w - 2.9, 0.36, 15, item === 1 ? theme.ink : theme.white, { bold: true });
      text(slide, label(item), x + w - 2.55, y + 0.17, 2.0, 0.5, 11, item === 1 ? theme.ink : theme.white, { bold: true, align: "right" });
    });
  } else if (config.signature === "quadrant") {
    slide.addShape(SHAPE.line, { x: 1.15, y: 5.95, w: 10.4, h: 0, line: { color: theme.ink, width: 1.4, endArrowType: "triangle" } });
    slide.addShape(SHAPE.line, { x: 6.35, y: 6.1, w: 0, h: -4.4, line: { color: theme.ink, width: 1.4, endArrowType: "triangle" } });
    text(slide, "经营贡献 →", 9.05, 6.16, 2.5, 0.3, 11, theme.ink, { fontFace: MONO, bold: true, align: "right" });
    text(slide, "改善紧迫度 ↑", 6.55, 1.48, 2.1, 0.3, 11, theme.ink, { fontFace: MONO, bold: true });
    text(slide, "立即整改", 6.72, 1.88, 1.25, 0.25, 9, theme.accent, { bold: true });
    text(slide, "重点放大", 10.1, 1.88, 1.25, 0.25, 9, theme.accent, { bold: true, align: "right" });
    text(slide, "观察维护", 1.35, 5.52, 1.25, 0.25, 9, theme.muted, { bold: true });
    text(slide, "效率优化", 9.95, 5.52, 1.4, 0.25, 9, theme.muted, { bold: true, align: "right" });
    [[3.0, 4.35, 0.75], [8.9, 2.2, 1.25], [9.25, 4.62, 0.95], [4.2, 2.75, 0.62]].forEach(([x, y, d], item) => {
      slide.addShape(SHAPE.ellipse, { x, y, w: d, h: d, fill: { color: item === 1 ? theme.accent : darkFill, transparency: 10 }, line: { color: theme.white, width: 1 } });
      text(slide, label(item), x - 0.45, y + d + 0.08, 1.65, 0.5, 9, theme.ink, { align: "center", bold: true });
    });
  } else if (config.signature === "flywheel" || config.signature === "constellation") {
    addRings(slide, theme, 6.55, 4.05, config.signature === "flywheel" ? 5 : 7);
    const nodes = config.signature === "flywheel"
      ? [[6.15, 1.65], [9.3, 3.4], [7.4, 5.58], [3.3, 4.7], [3.65, 2.15]]
      : [[6.18, 3.62], [3.0, 2.05], [9.55, 2.0], [2.55, 5.2], [9.8, 5.15], [6.1, 5.75]];
    nodes.forEach(([x, y], item) => {
      if (item > 0) slide.addShape(SHAPE.line, { x: 6.48, y: 3.98, w: x - 6.25, h: y - 3.78, line: { color: theme.accent, width: 1.3, transparency: 30 } });
      if (config.signature === "flywheel" && item > 0) {
        const [px, py] = nodes[item - 1];
        slide.addShape(SHAPE.line, { x: px + 0.35, y: py + 0.35, w: x - px, h: y - py, line: { color: theme.accent, width: 2, transparency: 10, endArrowType: "triangle" } });
      }
      slide.addShape(SHAPE.ellipse, { x, y, w: item === 0 ? 0.82 : 0.62, h: item === 0 ? 0.82 : 0.62, fill: { color: item === 0 ? theme.accent : darkFill }, line: { color: theme.white, width: 1 } });
      text(slide, item === 0 ? "CORE" : `0${item}`, x - 0.12, y + 0.14, 1.05, 0.28, 9, theme.white, { fontFace: MONO, bold: true, align: "center" });
      if (item > 0) text(slide, factTitle(facts[item % facts.length]), x - 0.6, y + 0.72, 1.8, 0.32, 9, theme.ink, { bold: true, align: "center" });
    });
  } else if (config.signature === "investor") {
    const chosen = facts.filter((fact) => typeof fact.value === "number").slice(0, 4);
    box(slide, 0.85, 1.72, 3.3, 4.6, darkFill, 0.1);
    text(slide, "ARR", 1.18, 2.12, 2.65, 0.3, 8, theme.pale, { fontFace: MONO, bold: true, charSpacing: 1.5 });
    text(slide, displayFact(chosen[0]), 1.15, 2.65, 2.7, 0.72, 32, theme.white, { bold: true });
    text(slide, "增长结果", 1.18, 3.5, 2.6, 0.32, 11, theme.pale, { bold: true });
    [0.36, 0.55, 0.76, 1.0].forEach((ratio, item) => {
      const barH = 0.42 + ratio * 1.35;
      box(slide, 1.2 + item * 0.62, 5.75 - barH, 0.38, barH, item === 3 ? theme.accent : theme.surface, 0.03);
    });
    chosen.slice(1).forEach((fact, item) => {
      const y = 1.85 + item * 1.42;
      box(slide, 4.75, y, 7.55, 1.05, item === 1 ? theme.accent : theme.surface, 0.08, { color: theme.accent, width: 1, transparency: 25 });
      text(slide, factTitle(fact), 5.08, y + 0.18, 3.2, 0.3, 11, item === 1 ? theme.white : theme.ink, { bold: true });
      text(slide, displayFact(fact), 9.45, y + 0.1, 2.45, 0.45, 20, item === 1 ? theme.white : theme.ink, { bold: true, align: "right" });
      if (item < 2) slide.addShape(SHAPE.line, { x: 8.45, y: y + 1.05, w: 0, h: 0.37, line: { color: theme.accent, width: 2, endArrowType: "triangle" } });
    });
    text(slide, "增长 → 留存 → 毛利：同一条单位经济证据链", 4.78, 6.15, 7.45, 0.3, 9, theme.muted, { bold: true, align: "right" });
  } else if (config.signature === "ranking") {
    const rateFacts = facts.filter((fact) => typeof fact.value === "number" && String(fact.unit || "").includes("%"));
    const chosen = (rateFacts.length >= 3 ? rateFacts : facts.filter((fact) => typeof fact.value === "number")).slice(0, 6);
    const max = Math.max(...chosen.map((fact) => Number(fact.value)), 1);
    text(slide, "同口径流失率比较 · BAR LENGTH = 月流失率", 0.9, 1.48, 5.8, 0.24, 7, theme.muted, { fontFace: MONO, bold: true, charSpacing: 1.2 });
    chosen.forEach((fact, item) => {
      const y = 2.0 + item * 0.84;
      text(slide, factTitle(fact), 0.9, y, 2.35, 0.3, 10, theme.ink, { bold: true });
      box(slide, 3.25, y + 0.02, 7.25, 0.38, theme.pale, 0.06);
      box(slide, 3.25, y + 0.02, Math.max(0.35, 7.25 * (Number(fact.value) / max)), 0.38, item < 3 ? theme.accent : theme.deep, 0.06);
      text(slide, displayFact(fact), 10.82, y - 0.02, 1.45, 0.4, 12, theme.ink, { fontFace: MONO, bold: true, align: "right" });
    });
  } else if (config.signature === "calendar") {
    const stages = ["预热蓄水", "内容种草", "爆发转化", "返场复购"];
    stages.forEach((stage, week) => {
      const y = 1.72 + week * 1.22;
      text(slide, `W${week + 1}`, 0.85, y + 0.25, 0.55, 0.3, 10, theme.accent, { fontFace: MONO, bold: true });
      text(slide, stage, 1.55, y + 0.18, 1.45, 0.34, 12, theme.ink, { bold: true });
      for (let day = 0; day < 7; day += 1) {
        const active = day <= week + 2;
        box(slide, 3.25 + day * 0.78, y, 0.62, 0.78, active ? theme.accent : theme.surface, 0.04, { color: theme.accent, width: 0.7, transparency: 35 });
        text(slide, String(week * 7 + day + 1).padStart(2, "0"), 3.25 + day * 0.78, y + 0.24, 0.62, 0.22, 7, active ? theme.white : theme.muted, { fontFace: MONO, bold: true, align: "center" });
      }
      text(slide, displayFact(facts[(week + 4) % facts.length]), 9.35, y + 0.12, 2.6, 0.42, 16, week === 3 ? theme.accent : theme.ink, { bold: true, align: "right" });
    });
  } else if (config.signature === "horizon") {
    [["2027 / 聚焦", "东南亚优先，建立本地化样板"], ["2028 / 复制", "产品与渠道能力跨市场复用"], ["2029 / 放大", "欧洲验证，海外占比进入目标区间"]].forEach(([year, detail], item) => {
      const y = 1.8 + item * 1.55;
      slide.addShape(SHAPE.line, { x: 0.95, y: y + 0.52, w: 10.95, h: 0, line: { color: item === 2 ? theme.accent : theme.pale, width: item === 2 ? 4 : 2 } });
      slide.addShape(SHAPE.ellipse, { x: 2.4 + item * 2.85, y: y + 0.22, w: 0.6, h: 0.6, fill: { color: item === 2 ? theme.accent : theme.deep }, line: { color: theme.white, width: 1 } });
      text(slide, year, 0.95, y - 0.08, 2.2, 0.36, 13, theme.ink, { bold: true });
      text(slide, detail, 6.1, y - 0.08, 5.55, 0.36, 11, theme.muted, { bold: true, align: "right" });
    });
  } else if (config.signature === "journey") {
    const stages = ["客户分群", "意图触发", "个性化触达", "响应复盘"];
    slide.addShape(SHAPE.line, { x: 1.15, y: 3.62, w: 10.7, h: 0, line: { color: theme.accent, width: 4, endArrowType: "triangle" } });
    stages.forEach((stage, item) => {
      const x = 1.15 + item * 2.85;
      slide.addShape(SHAPE.ellipse, { x, y: 3.2, w: 0.85, h: 0.85, fill: { color: item === 3 ? theme.accent : darkFill }, line: { color: theme.white, width: 1 } });
      text(slide, `0${item + 1}`, x, 3.45, 0.85, 0.24, 8, theme.white, { fontFace: MONO, bold: true, align: "center" });
      text(slide, stage, x - 0.55, 2.25, 1.95, 0.42, 13, theme.ink, { bold: true, align: "center" });
      text(slide, label(item + 4), x - 0.72, 4.45, 2.3, 0.68, 9, theme.muted, { bold: true, align: "center" });
    });
  } else if (config.signature === "staircase") {
    [0, 1, 2, 3].forEach((item) => {
      const x = 0.85 + item * 2.95;
      const y = 5.35 - item * 0.82;
      const h = 0.85 + item * 0.82;
      box(slide, x, y, 2.5, h, item === 3 ? darkFill : item === 2 ? theme.accent : theme.surface, 0.08, { color: theme.accent, width: 1, transparency: 25 });
      text(slide, ["启动", "验证", "扩展", "复盘"][item], x + 0.2, y + 0.18, 1.2, 0.32, 13, item >= 2 ? theme.white : theme.ink, { bold: true });
      text(slide, label(item + 4), x + 0.2, y + h - 0.62, 2.05, 0.48, 9, item >= 2 ? theme.pale : theme.muted, { bold: true });
      if (item < 3) slide.addShape(SHAPE.line, { x: x + 2.5, y: y + h / 2, w: 0.45, h: 0, line: { color: theme.accent, width: 2, endArrowType: "triangle" } });
    });
  } else if (config.signature === "governance") {
    box(slide, 4.55, 1.55, 4.2, 0.8, darkFill);
    text(slide, "联合指导委员会", 4.8, 1.77, 3.7, 0.34, 17, theme.white, { bold: true, align: "center" });
    slide.addShape(SHAPE.line, { x: 6.65, y: 2.35, w: 0, h: 0.58, line: { color: theme.accent, width: 2 } });
    [0, 1, 2].forEach((item) => {
      const x = 1.05 + item * 4.02;
      box(slide, x, 3.0, 3.3, 1.05, item === 1 ? theme.accent : theme.surface, 0.08, { color: theme.accent, width: 1.1, transparency: 20 });
      text(slide, ["业务决策", "项目交付", "风险升级"][item], x + 0.2, 3.22, 2.9, 0.32, 15, item === 1 ? theme.white : theme.ink, { bold: true, align: "center" });
      text(slide, label(item + 4), x + 0.2, 3.6, 2.9, 0.32, 8, item === 1 ? theme.white : theme.muted, { align: "center" });
      slide.addShape(SHAPE.line, { x: 6.65, y: 2.7, w: x + 1.65 - 6.65, h: 0.3, line: { color: theme.accent, width: 1.5 } });
    });
  } else {
    processFlow(pptx, theme, index, config.sections[1][0], [
      { title: "识别", detail: label(0) }, { title: "触达", detail: label(1) },
      { title: "转化", detail: label(2) }, { title: "复盘", detail: label(3) },
    ], facts.slice(0, 4).map((fact) => fact.id));
    pptx._slides.splice(pptx._slides.length - 2, 1);
  }
  notes(slide, facts.slice(0, 6).map((fact) => fact.id), `scenario-signature-${config.signature}`);
}

function semanticPlanScene(pptx, theme, index, brief, config, facts) {
  const preferredSemanticByScenario = {
    "brand-company-introduction": ["composition", "matrix"],
    "strategy-planning": ["composition", "matrix"],
    "data-analysis-report": ["comparison", "risk"],
    "project-kickoff": ["risk", "comparison"],
    "product-launch": ["process", "sequence", "timeline"],
    "ecommerce-marketing-plan": ["timeline", "sequence", "process"],
  };
  const groups = brief.ordinaryPlan?.groups || [];
  const preferred = preferredSemanticByScenario[brief.scenario_id] || [];
  const first = groups.find((group) => preferred.includes(group.semantic_hint)) || groups[0];
  const semantic = first?.semantic_hint || "roadmap";
  const refs = first?.fact_refs || facts.slice(0, 4).map((fact) => fact.id);
  const referencedFacts = refs.map((id) => facts.find((fact) => fact.id === id)).filter(Boolean);
  const selected = [
    ...referencedFacts,
    ...facts.filter((fact) => !referencedFacts.some((selectedFact) => selectedFact.id === fact.id)),
  ].slice(0, Math.max(4, referencedFacts.length));
  if (["comparison", "risk"].includes(semantic) && selected.length >= 2) {
    beforeAfter(pptx, theme, index, `决策对照：${config.sections[2][1]}`, {
      value: displayFact(selected[0]), label: factTitle(selected[0]), detail: displayScope(selected[0]),
    }, {
      value: displayFact(selected[1]), label: factTitle(selected[1]), detail: displayScope(selected[1]),
    }, refs);
    return "semantic-comparison";
  }
  if (["matrix", "quadrant", "composition", "funnel"].includes(semantic)) {
    matrix(pptx, theme, index, `行动矩阵：${config.sections[2][1]}`, selected.slice(0, 6).map((fact, item) => ({
      kicker: `GROUP ${item + 1}`, title: factTitle(fact), detail: displayFact(fact),
    })), refs);
    return "semantic-matrix";
  }
  if (["metrics", "trend", "table"].includes(semantic)) {
    metricLedger(pptx, theme, index, `结果边界：${config.sections[2][1]}`, selected.slice(0, 4).map((fact) => ({
      value: displayFact(fact), label: factTitle(fact), detail: displayScope(fact),
    })), refs);
    return "semantic-metric-ledger";
  }
  processFlow(pptx, theme, index, `验证路径：${config.sections[2][1]}`, selected.slice(0, 4).map((fact) => ({
    title: factTitle(fact), detail: displayFact(fact),
  })), refs);
  return "semantic-process";
}

function buildScenarioDeck(brief, config) {
  const theme = themes[config.themeKey];
  const pptx = deck(theme);
  const sourceFacts = brief.fact_store.facts;
  const sourceMetrics = sourceFacts.filter((fact) => fact.value !== undefined && fact.value !== null);
  const orderedRefs = brief.ordinaryPlan
    ? brief.ordinaryPlan.groups.flatMap((group) => group.fact_refs)
    : [];
  const factById = Object.fromEntries(sourceMetrics.map((fact) => [fact.id, fact]));
  const facts = [
    ...orderedRefs.map((id) => factById[id]).filter(Boolean),
    ...sourceMetrics.filter((fact) => !orderedRefs.includes(fact.id)),
  ];
  const pages = [];
  const prefix = brief.scenario_id.split("-").map((part) => part[0]).join("").slice(0, 8);
  const add = (role, family, density, candidate = `native:${family}`) => pages.push({
    slide_id: `${prefix}-${String(pages.length + 1).padStart(2, "0")}`,
    role, family, density, candidate_id: candidate,
  });

  scenarioCover(pptx, theme, config, brief);
  add("cover", `scenario-cover-${config.signature}`, "sparse", `native:cover.${config.signature}`);
  agenda(pptx, theme, config.sections.map(([titleValue, detail]) => [titleValue, detail]), ["violet"].includes(config.themeKey));
  add("agenda", "agenda-editorial", "medium", "native:agenda.grid-four");
  scenarioSummary(pptx, theme, 3, config, facts.slice(0, 4).map((fact) => ({
    value: displayFact(fact), label: factTitle(fact), detail: displayScope(fact),
  })), facts.slice(0, 4).map((fact) => fact.id));
  add("executive-summary", `scenario-summary-${config.signature}`, "medium", `native:summary.${config.signature}`);

  chapter(pptx, theme, 1, config.sections[0][0], config.sections[0][1], ["violet", "cobalt"].includes(config.themeKey));
  add("section", "chapter-reset", "sparse", "native:section.centered");
  dataTable(pptx, theme, 5, "八项锁定事实构成决策底座，不用空洞观点替代证据", [
    [
      { text: "指标", options: { bold: true, color: theme.white, fill: theme.deep } },
      { text: "数值", options: { bold: true, color: theme.white, fill: theme.deep } },
      { text: "时间 / 范围", options: { bold: true, color: theme.white, fill: theme.deep } },
    ],
    ...facts.map((fact) => [factTitle(fact), displayFact(fact), displayScope(fact)]),
  ], facts.map((fact) => fact.id));
  add("evidence", "native-evidence-table", "dense", "native:table.editorial");
  matrix(pptx, theme, 6, "从事实到判断：把八项指标组织成六个管理视角", facts.slice(0, 6).map((fact, index) => ({
    kicker: `EVIDENCE 0${index + 1}`,
    title: factTitle(fact),
    detail: `${displayFact(fact)} · ${displayScope(fact)}`,
  })), facts.slice(0, 6).map((fact) => fact.id));
  add("diagnosis", "six-cell-matrix", "dense", "native:multi-card.editorial");

  chapter(pptx, theme, 2, config.sections[1][0], config.sections[1][1], false);
  add("section", "chapter-reset", "sparse", "native:section.centered");
  processFlow(pptx, theme, 8, "把战略主张拆成四个可交付、可验收的动作", [
    { title: "01 · 对齐事实", detail: "确认口径、范围、基线与限制。" },
    { title: "02 · 聚焦杠杆", detail: "选择对决策影响最大的两到三项。" },
    { title: "03 · 小步验证", detail: "用明确周期、负责人和指标验证。" },
    { title: "04 · 复盘复制", detail: "达到门槛后再扩张资源与范围。" },
  ], facts.slice(4, 8).map((fact) => fact.id));
  add("solution", "staggered-process", "medium", "native:process.editorial");
  beforeAfter(pptx, theme, 9, "用目标态与约束态之间的差距定义行动", {
    value: displayFact(facts[0]), label: factTitle(facts[0]), detail: `${displayScope(facts[0])} · 当前事实`,
  }, {
    value: displayFact(facts[7]), label: factTitle(facts[7]), detail: `${displayScope(facts[7])} · 决策锚点`,
  }, [facts[0].id, facts[7].id]);
  add("comparison", "before-after-diptych", "medium", "native:comparison.editorial");
  bigMetrics(pptx, theme, 10, "资源、周期、规模和结果必须在同一页接受检验", facts.slice(4, 8).map((fact) => ({
    value: displayFact(fact), label: factTitle(fact), detail: displayScope(fact),
  })), facts.slice(4, 8).map((fact) => fact.id), false);
  add("proof", "asymmetric-big-metrics", "medium", "native:focal-statement.editorial-left");

  scenarioSignature(pptx, theme, 11, config, facts);
  add("scenario-signature", `scenario-signature-${config.signature}`, "dense", `native:scenario.${config.signature}`);
  chapter(pptx, theme, 3, config.sections[2][0], config.sections[2][1], ["violet"].includes(config.themeKey));
  add("section", "chapter-reset", "sparse", "native:section.centered");
  const semanticFamily = semanticPlanScene(pptx, theme, 13, brief, config, facts);
  add("model-semantic", semanticFamily, "medium", `native:${semanticFamily}`);
  processFlow(pptx, theme, 14, "从决定到执行：四个里程碑均绑定负责人和证据", [
    { title: "M1 · 定义", detail: "锁定范围、口径与责任人。" },
    { title: "M2 · 验证", detail: "用最小可行范围验证核心假设。" },
    { title: "M3 · 扩展", detail: "达到门槛后扩展场景与资源。" },
    { title: "M4 · 复盘", detail: "按事实复盘并决定继续或停止。" },
  ], facts.slice(0, 4).map((fact) => fact.id));
  add("roadmap", "staggered-process", "medium", "native:roadmap.editorial");
  statement(pptx, theme, 15, "Decision ask", config.decision, "同意后进入责任人、里程碑、验证指标和风险升级机制的正式执行。", ["violet", "cobalt"].includes(config.themeKey));
  add("decision", "editorial-statement", "sparse", "native:focal-statement.centered");

  chapter(pptx, theme, 4, "证据附录", "来源、素材、限制和禁止性声明均可追溯，不把不确定性藏在页脚。", false);
  add("section", "chapter-reset", "sparse", "native:section.centered");
  dataTable(pptx, theme, 17, "事实索引：每项数值都保留时间范围与来源定位", [
    [
      { text: "事实 ID", options: { bold: true, color: theme.white, fill: theme.deep } },
      { text: "指标 / 声明", options: { bold: true, color: theme.white, fill: theme.deep } },
      { text: "值 / 范围", options: { bold: true, color: theme.white, fill: theme.deep } },
    ],
    ...facts.slice(0, 8).map((fact) => [fact.id, factTitle(fact), `${displayFact(fact)} · ${displayScope(fact)}`]),
  ], facts.slice(0, 8).map((fact) => fact.id));
  add("appendix", "native-evidence-table", "dense", "native:table.source-index");
  const assets = brief.assets.slice(0, 6);
  matrix(pptx, theme, 18, "素材角色不是占位图：每一项都绑定用途、权利和降级策略", assets.map((asset, item) => ({
    kicker: `ASSET 0${item + 1}`,
    title: assetRoleLabel(asset),
    detail: `${asset.required ? "关键素材" : "辅助素材"} · 项目内已绑定`,
  })), []);
  add("appendix", "six-cell-matrix", "dense", "native:asset-role.matrix");
  statement(pptx, theme, 19, "Boundary / prohibited claims", "边界先于修辞，\n未经验证的收益与背书不得进入成稿", brief.prohibitions.join("；"), false);
  add("appendix", "editorial-statement", "sparse", "native:focal-statement.boundary");
  scenarioClosing(pptx, theme, config, brief);
  add("closing", `scenario-closing-${config.signature}`, "sparse", `native:cta.${config.signature}`);
  return {
    pptx, pages, scenario: brief.scenario_id,
    theme: `${config.themeKey}-scenario-editorial`, heroTheme: config.themeKey,
    heroAsset: config.heroAsset && fs.existsSync(path.join(assetDir, config.heroAsset))
      ? config.heroAsset
      : null,
  };
}

function manifestFor(result, file, brief) {
  const defaultThemeKey = result.scenario.startsWith("annual") ? "work" : result.scenario.startsWith("campus") ? "campus" : "academic";
  const heroPath = result.heroAsset
    ? path.join(assetDir, result.heroAsset)
    : themes[result.heroTheme || defaultThemeKey].hero;
  const manifest = {
    schema_version: "anchor-deck-blueprint.v1",
    scenario_id: result.scenario,
    theme_id: result.theme,
    source_brief: path.relative(process.cwd(), brief.sourcePath),
    source_brief_sha256: brief.sourceSha256,
    output_file: path.basename(file),
    output_sha256: sha256(file),
    slide_count: result.pages.length,
    native_editable: true,
    whole_slide_rasterization: false,
    generated_hero_assets: [{
      path: path.basename(heroPath),
      sha256: sha256(heroPath),
      policy: "local-project-bound-image",
    }],
    candidate_policy: {
      physical_prefix: "certified-private influence or bounded asset source; not reported as whole-slide materialization",
      native_prefix: "governed anchor-native composition",
      reference_only_materialized: false,
    },
    slides: result.pages,
  };
  if (brief.ordinaryPlan && brief.ordinaryPlanPath) {
    manifest.ordinary_model_plan = {
      path: path.relative(process.cwd(), brief.ordinaryPlanPath),
      sha256: sha256(brief.ordinaryPlanPath),
      authority: "semantic-fact-grouping-and-order-only",
    };
  }
  return manifest;
}

const jobs = [
  ["annual-work-report", buildWork],
  ["campus-competition-defense", buildCampus],
  ["academic-thesis-defense", buildAcademic],
];
if (argv.includes("--all-scenarios")) {
  for (const [scenario, config] of Object.entries(scenarioConfigs)) {
    jobs.push([scenario, (brief) => buildScenarioDeck(brief, config)]);
  }
}

const outputs = [];
for (const [briefName, builder] of jobs) {
  const brief = readBrief(briefName);
  const result = builder(brief);
  const output = path.join(outputDir, `${briefName}-reference-anchor.pptx`);
  await result.pptx.writeFile({ fileName: output, compression: true });
  const manifest = manifestFor(result, output, brief);
  fs.writeFileSync(`${output}.manifest.json`, `${JSON.stringify(manifest, null, 2)}\n`);
  outputs.push({ output, sha256: manifest.output_sha256, slide_count: manifest.slide_count });
}

process.stdout.write(`${JSON.stringify({ status: "PASS", outputs }, null, 2)}\n`);
