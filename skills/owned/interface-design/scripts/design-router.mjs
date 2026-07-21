#!/usr/bin/env node

import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const SCRIPT_DIR = dirname(fileURLToPath(import.meta.url));
const PATTERN_DIR = join(SCRIPT_DIR, "..", "assets", "patterns");
const TASKS = new Set([
  "landing", "dashboard", "app-prototype", "html-presentation", "component", "audit", "redesign",
  "readme-cover", "poster", "product-demo", "creative-coding"
]);
const DELIVERABLES = new Set(["html", "image", "video", "pptx", "hybrid"]);
const PLATFORMS = new Set(["cross-platform", "windows"]);
const FORMATS = new Set(["text", "json"]);

function usage() {
  return [
    "Usage: design-router.mjs --task <landing|dashboard|app-prototype|html-presentation|component|audit|redesign|readme-cover|poster|product-demo|creative-coding> --deliverable <html|image|video|pptx|hybrid>",
    "       [--signals trends,comparison] [--platform cross-platform|windows] [--format text|json]",
    "",
    "Returns a read-only design route. It never edits the project."
  ].join("\n");
}

function parseArgs(argv) {
  const options = { task: undefined, deliverable: undefined, signals: [], platform: "cross-platform", format: "text" };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") return { ...options, help: true };
    if (!["--task", "--deliverable", "--signals", "--platform", "--format"].includes(token)) {
      throw new Error(`Unknown option: ${token}`);
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`${token} requires a value`);
    index += 1;
    if (token === "--task") options.task = value;
    if (token === "--deliverable") options.deliverable = value;
    if (token === "--signals") options.signals = value.split(",").map((item) => item.trim()).filter(Boolean);
    if (token === "--platform") options.platform = value;
    if (token === "--format") options.format = value;
  }

  if (!TASKS.has(options.task)) throw new Error(`Unsupported or missing task: ${options.task ?? "<missing>"}`);
  if (!DELIVERABLES.has(options.deliverable)) throw new Error(`Unsupported or missing deliverable: ${options.deliverable ?? "<missing>"}`);
  if (!PLATFORMS.has(options.platform)) throw new Error(`Unsupported platform: ${options.platform}`);
  if (!FORMATS.has(options.format)) throw new Error(`Unsupported format: ${options.format}`);
  return options;
}

async function loadJson(name) {
  return JSON.parse(await readFile(join(PATTERN_DIR, name), "utf8"));
}

function ruleMatches(rule, options) {
  const tasks = rule.when?.tasks ?? [];
  const signals = rule.when?.signals_any ?? [];
  const taskMatches = tasks.length === 0 || tasks.includes(options.task);
  const signalMatches = signals.length === 0 || signals.some((signal) => options.signals.includes(signal));
  return taskMatches && signalMatches;
}

function unique(values) {
  return [...new Set(values)];
}

function modeFor(task, deliverable) {
  if (deliverable === "pptx") return "route";
  if (deliverable === "hybrid") return "prototype";
  if (deliverable === "image" || deliverable === "video") return "asset";
  if (task === "app-prototype") return "prototype";
  if (task === "audit") return "audit";
  if (task === "redesign") return "redesign";
  return "build";
}

function ownerFor(options) {
  const nativeOwner = options.platform === "windows" ? "window-pptx" : "pptx";
  if (["html", "image", "video"].includes(options.deliverable)) {
    return { owners: ["interface-design"], final_owner: "interface-design", handoff: false };
  }
  if (options.deliverable === "pptx") {
    return { owners: [nativeOwner], final_owner: nativeOwner, handoff: false };
  }
  return { owners: ["interface-design", nativeOwner], final_owner: nativeOwner, handoff: true };
}

async function buildRoute(options) {
  const [layoutsData, componentsData, rulesData, checksData] = await Promise.all([
    loadJson("layout-patterns.json"),
    loadJson("component-patterns.json"),
    loadJson("decision-rules.json"),
    loadJson("quality-checks.json")
  ]);
  const layoutIds = new Set(layoutsData.patterns.map((pattern) => pattern.id));
  const componentIds = new Set(componentsData.components.map((component) => component.id));
  const matchingRules = rulesData.rules
    .filter((rule) => ruleMatches(rule, options))
    .sort((left, right) => right.priority - left.priority || left.id.localeCompare(right.id));
  const layouts = unique(matchingRules.flatMap((rule) => rule.suggest.layouts));
  const components = unique(matchingRules.flatMap((rule) => rule.suggest.components));

  for (const id of layouts) if (!layoutIds.has(id)) throw new Error(`Rule references unknown layout: ${id}`);
  for (const id of components) if (!componentIds.has(id)) throw new Error(`Rule references unknown component: ${id}`);

  const ownership = ownerFor(options);
  const qualityChecks = checksData.checks
    .filter((check) => check.deliverables.includes(options.deliverable))
    .filter((check) => check.applies_to.includes("all") || check.applies_to.includes(options.task))
    .map((check) => ({ id: check.id, severity: check.severity }));

  return {
    task: options.task,
    deliverable: options.deliverable,
    mode: modeFor(options.task, options.deliverable),
    platform: options.platform,
    signals: options.signals,
    ...ownership,
    matched_rules: matchingRules.map((rule) => rule.id),
    suggested_layouts: ownership.owners.includes("interface-design") ? layouts : [],
    suggested_components: ownership.owners.includes("interface-design") ? components : [],
    required_quality_checks: qualityChecks,
    boundary: options.deliverable === "pptx"
      ? "Native PowerPoint production and QA belong to the PPT owner."
      : options.deliverable === "hybrid"
        ? "HTML establishes the accepted visual direction; the PPT owner rebuilds and verifies the native deck from ppt-handoff.md."
        : options.deliverable === "image"
          ? "The final still is rendered from an editable, evidence-backed visual source and verified at full and distribution size."
          : options.deliverable === "video"
            ? "The final motion asset uses deterministic browser time, a static poster fallback, and encoded-frame validation."
            : "The final artifact is browser-native HTML/CSS/JS."
  };
}

function renderText(route) {
  return [
    `Design route: ${route.task} -> ${route.deliverable}`,
    `Owners: ${route.owners.join(" -> ")}`,
    `Final owner: ${route.final_owner}`,
    `Mode: ${route.mode}`,
    `Layouts: ${route.suggested_layouts.join(", ") || "none"}`,
    `Components: ${route.suggested_components.join(", ") || "none"}`,
    `Quality gates: ${route.required_quality_checks.map((check) => `${check.id}:${check.severity}`).join(", ")}`,
    `Boundary: ${route.boundary}`
  ].join("\n");
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    process.stdout.write(`${usage()}\n`);
  } else {
    const route = await buildRoute(options);
    process.stdout.write(options.format === "json" ? `${JSON.stringify(route, null, 2)}\n` : `${renderText(route)}\n`);
  }
} catch (error) {
  process.stderr.write(`${error.message}\n\n${usage()}\n`);
  process.exitCode = 2;
}
