#!/usr/bin/env node

import { createRequire } from "node:module";
import { access, mkdir, mkdtemp, readFile, readdir, rm, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { basename, dirname, extname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);

function usage() {
  return [
    "Usage: export-html-deck-pptx.mjs --slides <dir> --out <deck.pptx> --mode <editable|fidelity> [options]",
    "Options:",
    "  --mode editable|fidelity  Required conversion contract",
    "  --width <px>              Fidelity capture width (default: 1600)",
    "  --height <px>             Fidelity capture height (default: 900)",
    "  --notes <notes.json>      Optional filename-to-speaker-notes map",
    "  --overwrite               Replace an existing output",
    "",
    "editable: translates compatible DOM elements into native PowerPoint objects.",
    "fidelity: renders each HTML slide as a full-slide image; visual fidelity is retained but objects are not editable."
  ].join("\n");
}

function parseArgs(argv) {
  const options = { width: 1600, height: 900, overwrite: false };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") return { ...options, help: true };
    if (token === "--overwrite") {
      options.overwrite = true;
      continue;
    }
    if (!["--slides", "--out", "--mode", "--width", "--height", "--notes"].includes(token)) {
      throw new Error(`Unknown option: ${token}`);
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`${token} requires a value`);
    index += 1;
    options[token.slice(2)] = value;
  }
  if (!options.slides) throw new Error("--slides is required");
  if (!options.out) throw new Error("--out is required");
  if (!new Set(["editable", "fidelity"]).has(options.mode)) {
    throw new Error("--mode must be editable or fidelity; the editability decision cannot be inferred safely");
  }
  options.width = Number(options.width);
  options.height = Number(options.height);
  if (!Number.isInteger(options.width) || options.width < 320) throw new Error("--width must be an integer >= 320");
  if (!Number.isInteger(options.height) || options.height < 180) throw new Error("--height must be an integer >= 180");
  if (extname(options.out).toLowerCase() !== ".pptx") throw new Error("--out must use the .pptx suffix");
  return options;
}

async function loadDependencies() {
  let PptxGenJS;
  try {
    const loaded = require("pptxgenjs");
    PptxGenJS = loaded.default ?? loaded;
  } catch (error) {
    throw new Error(`pptxgenjs is required. Install it in the deck project. ${error.message}`);
  }
  return { PptxGenJS };
}

async function outputExists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

async function loadNotes(path) {
  if (!path) return {};
  const parsed = JSON.parse(await readFile(resolve(path), "utf8"));
  if (!parsed || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error("--notes must contain a JSON object keyed by slide filename");
  }
  return parsed;
}

function addNotes(slide, notes, filename) {
  const value = notes[filename];
  if (!value) return;
  if (typeof slide.addNotes !== "function") throw new Error("Installed pptxgenjs does not support speaker notes");
  slide.addNotes(Array.isArray(value) ? value.join("\n") : String(value));
}

async function renderEditable({ files, slidesDir, notes, presentation }) {
  let htmlToPptx;
  try {
    htmlToPptx = require("./html-to-pptx.cjs");
  } catch (error) {
    throw new Error(`Unable to load the HTML-to-PPTX translator. ${error.message}`);
  }
  const placeholders = {};
  for (const filename of files) {
    const result = await htmlToPptx(join(slidesDir, filename), presentation);
    addNotes(result.slide, notes, filename);
    placeholders[filename] = result.placeholders;
  }
  return { placeholders };
}

async function renderFidelity({ files, slidesDir, notes, presentation, width, height }) {
  let chromium;
  try {
    ({ chromium } = require("playwright"));
  } catch (error) {
    throw new Error(`Playwright is required for fidelity mode. ${error.message}`);
  }

  const scratch = await mkdtemp(join(tmpdir(), "html-deck-pptx-"));
  const browserErrors = [];
  const browser = await chromium.launch({ headless: true, args: ["--disable-dev-shm-usage"] });
  try {
    for (let index = 0; index < files.length; index += 1) {
      const filename = files[index];
      const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 });
      page.on("console", (message) => {
        if (message.type() === "error") browserErrors.push(`${filename}: ${message.text()}`);
      });
      page.on("pageerror", (error) => browserErrors.push(`${filename}: ${error.message}`));
      await page.goto(pathToFileURL(join(slidesDir, filename)).href, { waitUntil: "load" });
      await page.evaluate(() => document.fonts?.ready);
      const hasReadyContract = await page.evaluate(() => "__VISUAL_READY__" in window);
      if (hasReadyContract) {
        await page.waitForFunction(() => window.__VISUAL_READY__ === true, undefined, { timeout: 30_000 });
      }
      const imagePath = join(scratch, `${String(index + 1).padStart(4, "0")}.png`);
      await page.screenshot({ path: imagePath, type: "png" });
      await page.close();

      const slide = presentation.addSlide();
      slide.addImage({ path: imagePath, x: 0, y: 0, w: 13.333, h: 7.5 });
      addNotes(slide, notes, filename);
    }
  } finally {
    await browser.close();
  }
  if (browserErrors.length > 0) throw new Error(`Browser errors during fidelity capture:\n${browserErrors.join("\n")}`);
  return { scratch };
}

async function main(options) {
  const slidesDir = resolve(options.slides);
  const output = resolve(options.out);
  const files = (await readdir(slidesDir)).filter((file) => extname(file).toLowerCase() === ".html").sort();
  if (files.length === 0) throw new Error(`No HTML slides found in ${slidesDir}`);
  if (!options.overwrite && await outputExists(output)) throw new Error(`Output already exists: ${output}; pass --overwrite to replace it`);

  const notes = await loadNotes(options.notes);
  const { PptxGenJS } = await loadDependencies();
  const presentation = new PptxGenJS();
  presentation.layout = "LAYOUT_WIDE";
  presentation.author = "";
  presentation.subject = options.mode === "editable" ? "Editable HTML-derived presentation" : "Fidelity HTML-derived presentation";
  presentation.title = basename(output, ".pptx");
  presentation.company = "";
  presentation.lang = "en-US";

  let scratch;
  try {
    const result = options.mode === "editable"
      ? await renderEditable({ files, slidesDir, notes, presentation })
      : await renderFidelity({ files, slidesDir, notes, presentation, width: options.width, height: options.height });
    scratch = result.scratch;
    await mkdir(dirname(output), { recursive: true });
    await presentation.writeFile({ fileName: output });
  } finally {
    if (scratch) await rm(scratch, { recursive: true, force: true });
  }

  const outputStat = await stat(output);
  process.stdout.write(`${JSON.stringify({
    source: slidesDir,
    output,
    mode: options.mode,
    editable: options.mode === "editable",
    slides: files,
    slide_count: files.length,
    width: options.mode === "fidelity" ? options.width : 1280,
    height: options.mode === "fidelity" ? options.height : 720,
    bytes: outputStat.size
  }, null, 2)}\n`);
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) process.stdout.write(`${usage()}\n`);
  else await main(options);
} catch (error) {
  process.stderr.write(`${error.message}\n\n${usage()}\n`);
  process.exitCode = 2;
}
