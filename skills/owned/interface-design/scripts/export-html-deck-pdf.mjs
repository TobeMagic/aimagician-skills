#!/usr/bin/env node

import { createRequire } from "node:module";
import { mkdir, readdir, stat, writeFile } from "node:fs/promises";
import { dirname, extname, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);

function usage() {
  return [
    "Usage: export-html-deck-pdf.mjs --slides <dir> --out <deck.pdf> [options]",
    "Options:",
    "  --width <px>      Browser viewport width (default: 1600)",
    "  --height <px>     Browser viewport height (default: 900)",
    "  --settle-ms <ms>  Additional font/animation settling time (default: 250)",
    "",
    "Each HTML file becomes one vector-text PDF page, ordered by filename."
  ].join("\n");
}

function parseArgs(argv) {
  const options = { width: 1600, height: 900, "settle-ms": 250 };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") return { ...options, help: true };
    if (!["--slides", "--out", "--width", "--height", "--settle-ms"].includes(token)) {
      throw new Error(`Unknown option: ${token}`);
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`${token} requires a value`);
    options[token.slice(2)] = value;
    index += 1;
  }
  if (!options.slides || !options.out) throw new Error("--slides and --out are required");
  if (extname(options.out).toLowerCase() !== ".pdf") throw new Error("--out must use the .pdf suffix");
  for (const key of ["width", "height", "settle-ms"]) options[key] = Number(options[key]);
  if (!Number.isInteger(options.width) || options.width < 320) throw new Error("--width must be an integer >= 320");
  if (!Number.isInteger(options.height) || options.height < 180) throw new Error("--height must be an integer >= 180");
  if (!Number.isInteger(options["settle-ms"]) || options["settle-ms"] < 0) throw new Error("--settle-ms must be an integer >= 0");
  return options;
}

function loadDependencies() {
  try {
    const { chromium } = require("playwright");
    const { PDFDocument } = require("pdf-lib");
    return { chromium, PDFDocument };
  } catch (error) {
    throw new Error(`Playwright and pdf-lib are required in the deck project. ${error.message}`);
  }
}

async function main(options) {
  const slidesDir = resolve(options.slides);
  const output = resolve(options.out);
  const files = (await readdir(slidesDir)).filter((file) => extname(file).toLowerCase() === ".html").sort();
  if (files.length === 0) throw new Error(`No HTML slides found in ${slidesDir}`);

  const { chromium, PDFDocument } = loadDependencies();
  const browser = await chromium.launch({ headless: true, args: ["--disable-dev-shm-usage"] });
  const pageBuffers = [];
  const browserErrors = [];
  try {
    for (const filename of files) {
      const page = await browser.newPage({ viewport: { width: options.width, height: options.height } });
      page.on("console", (message) => {
        if (message.type() === "error") browserErrors.push(`${filename}: ${message.text()}`);
      });
      page.on("pageerror", (error) => browserErrors.push(`${filename}: ${error.message}`));
      await page.goto(pathToFileURL(resolve(slidesDir, filename)).href, { waitUntil: "load" });
      await page.evaluate(() => document.fonts?.ready);
      const hasReadyContract = await page.evaluate(() => "__VISUAL_READY__" in window);
      if (hasReadyContract) await page.waitForFunction(() => window.__VISUAL_READY__ === true, undefined, { timeout: 30_000 });
      if (options["settle-ms"] > 0) await page.waitForTimeout(options["settle-ms"]);
      await page.emulateMedia({ media: "screen" });
      pageBuffers.push(await page.pdf({
        width: `${options.width}px`,
        height: `${options.height}px`,
        printBackground: true,
        margin: { top: 0, right: 0, bottom: 0, left: 0 },
        preferCSSPageSize: false
      }));
      await page.close();
    }
  } finally {
    await browser.close();
  }
  if (browserErrors.length > 0) throw new Error(`Browser errors during PDF export:\n${browserErrors.join("\n")}`);

  const merged = await PDFDocument.create();
  for (const buffer of pageBuffers) {
    const source = await PDFDocument.load(buffer);
    const pages = await merged.copyPages(source, source.getPageIndices());
    for (const page of pages) merged.addPage(page);
  }
  const bytes = await merged.save();
  await mkdir(dirname(output), { recursive: true });
  await writeFile(output, bytes);
  const outputStat = await stat(output);
  process.stdout.write(`${JSON.stringify({ source: slidesDir, output, pages: files.length, files, vector_text: true, bytes: outputStat.size }, null, 2)}\n`);
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) process.stdout.write(`${usage()}\n`);
  else await main(options);
} catch (error) {
  process.stderr.write(`${error.message}\n\n${usage()}\n`);
  process.exitCode = 2;
}
