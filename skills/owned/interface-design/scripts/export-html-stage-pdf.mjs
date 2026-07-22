#!/usr/bin/env node

import { createRequire } from "node:module";
import { access, mkdir, stat } from "node:fs/promises";
import { dirname, extname, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);

function usage() {
  return [
    "Usage: export-html-stage-pdf.mjs --html <deck.html> --out <deck.pdf> [options]",
    "Options:",
    "  --width <px>      Slide width (default: 1600)",
    "  --height <px>     Slide height (default: 900)",
    "  --settle-ms <ms>  Additional font/animation settling time (default: 250)",
    "",
    "Flattens sections inside <deck-stage> into vector-text PDF pages."
  ].join("\n");
}

function parseArgs(argv) {
  const options = { width: 1600, height: 900, "settle-ms": 250 };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") return { ...options, help: true };
    if (!["--html", "--out", "--width", "--height", "--settle-ms"].includes(token)) {
      throw new Error(`Unknown option: ${token}`);
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`${token} requires a value`);
    options[token.slice(2)] = value;
    index += 1;
  }
  if (!options.html || !options.out) throw new Error("--html and --out are required");
  if (extname(options.out).toLowerCase() !== ".pdf") throw new Error("--out must use the .pdf suffix");
  for (const key of ["width", "height", "settle-ms"]) options[key] = Number(options[key]);
  if (!Number.isInteger(options.width) || options.width < 320) throw new Error("--width must be an integer >= 320");
  if (!Number.isInteger(options.height) || options.height < 180) throw new Error("--height must be an integer >= 180");
  if (!Number.isInteger(options["settle-ms"]) || options["settle-ms"] < 0) throw new Error("--settle-ms must be an integer >= 0");
  return options;
}

function loadPlaywright() {
  try {
    return require("playwright").chromium;
  } catch (error) {
    throw new Error(`Playwright is required in the deck project. ${error.message}`);
  }
}

async function main(options) {
  const input = resolve(options.html);
  const output = resolve(options.out);
  await access(input);
  const chromium = loadPlaywright();
  const browser = await chromium.launch({ headless: true, args: ["--disable-dev-shm-usage"] });
  const browserErrors = [];
  let sectionCount = 0;
  try {
    const page = await browser.newPage({ viewport: { width: options.width, height: options.height } });
    page.on("console", (message) => {
      if (message.type() === "error") browserErrors.push(message.text());
    });
    page.on("pageerror", (error) => browserErrors.push(error.message));
    await page.goto(pathToFileURL(input).href, { waitUntil: "load" });
    await page.evaluate(() => document.fonts?.ready);
    const hasReadyContract = await page.evaluate(() => "__VISUAL_READY__" in window);
    if (hasReadyContract) await page.waitForFunction(() => window.__VISUAL_READY__ === true, undefined, { timeout: 30_000 });
    if (options["settle-ms"] > 0) await page.waitForTimeout(options["settle-ms"]);

    sectionCount = await page.evaluate(({ width, height }) => {
      const stage = document.querySelector("deck-stage");
      if (!stage) throw new Error("<deck-stage> was not found");
      const sections = Array.from(stage.querySelectorAll(":scope > section"));
      if (sections.length === 0) throw new Error("No direct <section> children were found inside <deck-stage>");
      const style = document.createElement("style");
      style.textContent = `
        @page { size: ${width}px ${height}px; margin: 0; }
        html, body { margin: 0 !important; padding: 0 !important; background: #fff; }
        deck-stage { display: none !important; }
      `;
      document.head.appendChild(style);
      const container = document.createElement("div");
      container.id = "print-container";
      for (const section of sections) {
        section.style.cssText = `
          width: ${width}px !important;
          height: ${height}px !important;
          display: block !important;
          position: relative !important;
          overflow: hidden !important;
          break-after: page !important;
          page-break-after: always !important;
          margin: 0 !important;
          padding: 0 !important;
        `;
        container.appendChild(section);
      }
      sections.at(-1).style.breakAfter = "auto";
      sections.at(-1).style.pageBreakAfter = "auto";
      document.body.appendChild(container);
      return sections.length;
    }, { width: options.width, height: options.height });
    await mkdir(dirname(output), { recursive: true });
    await page.pdf({ path: output, width: `${options.width}px`, height: `${options.height}px`, printBackground: true, preferCSSPageSize: true });
    await page.close();
  } finally {
    await browser.close();
  }
  if (browserErrors.length > 0) throw new Error(`Browser errors during PDF export:\n${browserErrors.join("\n")}`);
  const outputStat = await stat(output);
  process.stdout.write(`${JSON.stringify({ source: input, output, pages: sectionCount, vector_text: true, bytes: outputStat.size }, null, 2)}\n`);
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) process.stdout.write(`${usage()}\n`);
  else await main(options);
} catch (error) {
  process.stderr.write(`${error.message}\n\n${usage()}\n`);
  process.exitCode = 2;
}
