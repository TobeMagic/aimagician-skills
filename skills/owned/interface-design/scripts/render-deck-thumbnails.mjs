#!/usr/bin/env node

import { createRequire } from "node:module";
import { mkdir, readdir, writeFile } from "node:fs/promises";
import { basename, join, relative, resolve } from "node:path";
import { pathToFileURL } from "node:url";

function usage() {
  return [
    "Usage: render-deck-thumbnails.mjs --slides <dir> --output-dir <dir>",
    "       [--canvas-width <px>] [--canvas-height <px>] [--thumbnail-width <px>] [--quality <1-100>] [--manifest <path>]",
    "",
    "Renders deterministic JPEG thumbnails for a multi-file HTML deck after fonts, images, and optional window.__VISUAL_READY__ are ready.",
    "Requires playwright and sharp in the project or NODE_PATH."
  ].join("\n");
}

function parseInteger(value, name, min, max) {
  const parsed = Number(value);
  if (!Number.isInteger(parsed) || parsed < min || parsed > max) throw new Error(`${name} must be an integer from ${min} to ${max}`);
  return parsed;
}

function parseArgs(argv) {
  const options = { canvas_width: 1920, canvas_height: 1080, thumbnail_width: 1600, quality: 86 };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") return { help: true };
    if (!["--slides", "--output-dir", "--canvas-width", "--canvas-height", "--thumbnail-width", "--quality", "--manifest"].includes(token)) {
      throw new Error(`Unknown option: ${token}`);
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`${token} requires a value`);
    index += 1;
    options[token.slice(2).replaceAll("-", "_")] = value;
  }
  if (!options.slides || !options.output_dir) throw new Error("--slides and --output-dir are required");
  options.canvas_width = parseInteger(options.canvas_width, "--canvas-width", 320, 7680);
  options.canvas_height = parseInteger(options.canvas_height, "--canvas-height", 240, 4320);
  options.thumbnail_width = parseInteger(options.thumbnail_width, "--thumbnail-width", 160, options.canvas_width);
  options.quality = parseInteger(options.quality, "--quality", 1, 100);
  return options;
}

async function loadDependencies() {
  const require = createRequire(import.meta.url);
  try {
    return { chromium: require("playwright").chromium, sharp: require("sharp") };
  } catch (error) {
    throw new Error(`Missing optional dependency: ${error.message}. Install playwright and sharp in the project.`);
  }
}

async function main(options) {
  const slidesDir = resolve(options.slides);
  const outputDir = resolve(options.output_dir);
  const manifestPath = resolve(options.manifest ?? join(outputDir, "thumbnail-manifest.json"));
  const files = (await readdir(slidesDir, { withFileTypes: true }))
    .filter((entry) => entry.isFile() && entry.name.toLowerCase().endsWith(".html"))
    .map((entry) => entry.name)
    .sort((left, right) => left.localeCompare(right, undefined, { numeric: true }));
  if (files.length === 0) throw new Error(`No HTML slides found in ${slidesDir}`);
  await mkdir(outputDir, { recursive: true });
  const { chromium, sharp } = await loadDependencies();
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: options.canvas_width, height: options.canvas_height }, deviceScaleFactor: 1 });
  const entries = [];
  let browserErrors = [];
  page.on("pageerror", (error) => browserErrors.push(`pageerror: ${error.message}`));
  page.on("console", (message) => {
    if (message.type() === "error") browserErrors.push(`console: ${message.text()}`);
  });
  page.on("requestfailed", (request) => browserErrors.push(`request: ${request.url()} (${request.failure()?.errorText ?? "failed"})`));
  try {
    for (const filename of files) {
      browserErrors = [];
      await page.goto(pathToFileURL(join(slidesDir, filename)).href, { waitUntil: "load" });
      await page.waitForFunction(() => {
        const fontsReady = !document.fonts || document.fonts.status === "loaded";
        const imagesReady = [...document.images].every((image) => image.complete && image.naturalWidth > 0);
        return fontsReady && imagesReady;
      }, undefined, { timeout: 30_000 });
      const exposesReady = await page.evaluate(() => Object.prototype.hasOwnProperty.call(window, "__VISUAL_READY__"));
      if (exposesReady) await page.waitForFunction(() => window.__VISUAL_READY__ === true, undefined, { timeout: 30_000 });
      const exposesTime = await page.evaluate(() => typeof window.__setDesignTime === "function");
      if (exposesTime) {
        await page.evaluate(() => window.__setDesignTime(0));
        await page.evaluate(() => new Promise((resolveFrame) => requestAnimationFrame(() => requestAnimationFrame(resolveFrame))));
      }
      if (browserErrors.length > 0) throw new Error(`${filename} has browser errors: ${browserErrors.join(" | ")}`);
      const png = await page.screenshot({ type: "png", clip: { x: 0, y: 0, width: options.canvas_width, height: options.canvas_height } });
      const screenshotStats = await sharp(png).stats();
      if (!Number.isFinite(screenshotStats.entropy) || screenshotStats.entropy < 0.005) throw new Error(`${filename} rendered a blank or near-uniform thumbnail`);
      const outputName = `${basename(filename, ".html")}.jpg`;
      const outputPath = join(outputDir, outputName);
      const info = await sharp(png).resize({ width: options.thumbnail_width }).jpeg({ quality: options.quality, mozjpeg: true }).toFile(outputPath);
      entries.push({ slide: relative(slidesDir, join(slidesDir, filename)), thumbnail: relative(outputDir, outputPath), width: info.width, height: info.height, bytes: info.size });
    }
  } finally {
    await browser.close();
  }
  const manifest = { schema_version: 1, canvas: { width: options.canvas_width, height: options.canvas_height }, thumbnail_width: options.thumbnail_width, quality: options.quality, slides: entries };
  await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  process.stdout.write(`${JSON.stringify({ manifest: manifestPath, rendered: entries.length, slides: files.length }, null, 2)}\n`);
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) process.stdout.write(`${usage()}\n`);
  else await main(options);
} catch (error) {
  process.stderr.write(`${error.message}\n\n${usage()}\n`);
  process.exitCode = 2;
}
