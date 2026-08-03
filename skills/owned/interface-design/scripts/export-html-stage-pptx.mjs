#!/usr/bin/env node

import { createRequire } from "node:module";
import { createReadStream } from "node:fs";
import { access, mkdir, mkdtemp, readFile, rm, stat } from "node:fs/promises";
import { createServer } from "node:http";
import { tmpdir } from "node:os";
import { basename, dirname, extname, join, relative, resolve, sep } from "node:path";

const require = createRequire(import.meta.url);

function usage() {
  return [
    "Usage: export-html-stage-pptx.mjs --html <deck.html> --out <deck.pptx> --mode fidelity [options]",
    "Options:",
    "  --mode fidelity       Required. A single-file interactive stage exports as full-slide images.",
    "  --width <px>          Capture width (default: 1600)",
    "  --height <px>         Capture height (default: 900)",
    "  --settle-ms <ms>      Wait after each navigation event (default: 1200)",
    "  --notes <notes.json>  Optional array or slide-number-to-notes map",
    "  --overwrite           Replace an existing output",
    "",
    "Supported sources:",
    "  1. <deck-stage> with direct child <section> slides",
    "  2. #deck with .slide children and a global go(index) navigator",
    "",
    "Editable HTML-first PPTX requires independent slide HTML files and export-html-deck-pptx.mjs."
  ].join("\n");
}

function parseArgs(argv) {
  const options = { width: 1600, height: 900, settleMs: 1200, overwrite: false };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") return { ...options, help: true };
    if (token === "--overwrite") {
      options.overwrite = true;
      continue;
    }
    if (!["--html", "--out", "--mode", "--width", "--height", "--settle-ms", "--notes"].includes(token)) {
      throw new Error(`Unknown option: ${token}`);
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`${token} requires a value`);
    index += 1;
    const key = token === "--settle-ms" ? "settleMs" : token.slice(2);
    options[key] = value;
  }
  if (!options.html) throw new Error("--html is required");
  if (!options.out) throw new Error("--out is required");
  if (options.mode !== "fidelity") {
    throw new Error("--mode fidelity is required; single-file interactive decks cannot claim native object editability");
  }
  options.width = Number(options.width);
  options.height = Number(options.height);
  options.settleMs = Number(options.settleMs);
  if (!Number.isInteger(options.width) || options.width < 320) throw new Error("--width must be an integer >= 320");
  if (!Number.isInteger(options.height) || options.height < 180) throw new Error("--height must be an integer >= 180");
  if (!Number.isInteger(options.settleMs) || options.settleMs < 0) throw new Error("--settle-ms must be a non-negative integer");
  if (extname(options.out).toLowerCase() !== ".pptx") throw new Error("--out must use the .pptx suffix");
  return options;
}

async function exists(path) {
  try {
    await access(path);
    return true;
  } catch {
    return false;
  }
}

async function loadNotes(path) {
  if (!path) return [];
  const value = JSON.parse(await readFile(resolve(path), "utf8"));
  if (!Array.isArray(value) && (!value || typeof value !== "object")) {
    throw new Error("--notes must contain an array or object");
  }
  return value;
}

function noteFor(notes, index) {
  if (Array.isArray(notes)) return notes[index];
  return notes[String(index + 1)] ?? notes[`slide-${index + 1}`];
}

function addNotes(slide, notes, index) {
  const value = noteFor(notes, index);
  if (!value) return;
  if (typeof slide.addNotes !== "function") throw new Error("Installed pptxgenjs does not support speaker notes");
  slide.addNotes(Array.isArray(value) ? value.map(String) : [String(value)]);
}

function loadDependencies() {
  try {
    const playwright = require("playwright");
    const loaded = require("pptxgenjs");
    return { chromium: playwright.chromium, PptxGenJS: loaded.default ?? loaded };
  } catch (error) {
    throw new Error(`Playwright and pptxgenjs are required in the deck project. ${error.message}`);
  }
}

function presentationGeometry(width, height) {
  const ratio = width / height;
  if (ratio >= 1) return { width: 13.333, height: 13.333 / ratio };
  return { width: 13.333 * ratio, height: 13.333 };
}

const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".gif": "image/gif",
  ".html": "text/html; charset=utf-8",
  ".jpeg": "image/jpeg",
  ".jpg": "image/jpeg",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".mp4": "video/mp4",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".webm": "video/webm",
  ".woff": "font/woff",
  ".woff2": "font/woff2"
};

async function startStaticServer(source) {
  const root = dirname(source);
  const server = createServer(async (request, response) => {
    try {
      const pathname = decodeURIComponent(new URL(request.url ?? "/", "http://127.0.0.1").pathname);
      const requested = pathname === "/" ? basename(source) : pathname.replace(/^\/+/, "");
      const file = resolve(root, requested);
      const fromRoot = relative(root, file);
      if (fromRoot.startsWith(`..${sep}`) || fromRoot === ".." || fromRoot.includes("\0")) {
        response.writeHead(403).end("Forbidden");
        return;
      }
      const fileStat = await stat(file);
      if (!fileStat.isFile()) {
        response.writeHead(404).end("Not found");
        return;
      }
      response.writeHead(200, {
        "Content-Type": contentTypes[extname(file).toLowerCase()] ?? "application/octet-stream",
        "Cache-Control": "no-store"
      });
      createReadStream(file).pipe(response);
    } catch (error) {
      response.writeHead(error?.code === "ENOENT" ? 404 : 500).end(error?.code === "ENOENT" ? "Not found" : "Server error");
    }
  });
  await new Promise((resolveListen, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolveListen);
  });
  const address = server.address();
  if (!address || typeof address === "string") throw new Error("Could not allocate a local stage server");
  return {
    url: `http://127.0.0.1:${address.port}/${encodeURIComponent(basename(source))}`,
    close: () => new Promise((resolveClose, reject) => server.close((error) => error ? reject(error) : resolveClose()))
  };
}

async function inspectContract(page) {
  return page.evaluate(() => {
    const stage = document.querySelector("deck-stage");
    if (stage) {
      const slides = stage.querySelectorAll(":scope > section");
      if (slides.length === 0) throw new Error("<deck-stage> has no direct <section> slides");
      return { kind: "deck-stage", slideCount: slides.length };
    }
    const deck = document.querySelector("#deck");
    const slides = deck?.querySelectorAll(":scope > .slide");
    if (slides?.length) {
      return { kind: "horizontal-deck", slideCount: slides.length };
    }
    throw new Error("Expected <deck-stage> sections or #deck > .slide");
  });
}

async function prepareCapture(page, kind) {
  await page.evaluate((sourceKind) => {
    const style = document.createElement("style");
    style.dataset.htmlStageExport = "";
    style.textContent = `
      #nav, #hint, #overview, [data-deck-stage-overview] { display: none !important; }
      deck-stage::part(shell-actions), deck-stage::part(progress) { display: none !important; }
    `;
    document.head.appendChild(style);
    if (sourceKind === "deck-stage") {
      document.querySelector("deck-stage")?.setAttribute("data-exporting", "");
    }
  }, kind);
}

async function navigate(page, kind, index, settleMs) {
  await page.evaluate(({ sourceKind, slideIndex }) => {
    if (sourceKind === "deck-stage") {
      const stage = document.querySelector("deck-stage");
      if (typeof stage?.goTo !== "function") throw new Error("<deck-stage> does not expose goTo(index)");
      stage.goTo(slideIndex);
      return;
    }
    if (typeof window.go === "function") {
      window.go(slideIndex);
      return;
    }
    const deck = document.querySelector("#deck");
    if (!deck) throw new Error("#deck was not found");
    deck.style.transition = "none";
    deck.style.transform = `translateX(${-slideIndex * 100}vw)`;
  }, { sourceKind: kind, slideIndex: index });
  if (settleMs > 0) await page.waitForTimeout(settleMs);
}

async function main(options) {
  const source = resolve(options.html);
  const output = resolve(options.out);
  if (!options.overwrite && await exists(output)) {
    throw new Error(`Output already exists: ${output}; pass --overwrite to replace it`);
  }

  const notes = await loadNotes(options.notes);
  const { chromium, PptxGenJS } = loadDependencies();
  const scratch = await mkdtemp(join(tmpdir(), "html-stage-pptx-"));
  const sourceServer = await startStaticServer(source);
  const browserErrors = [];
  let browser;
  let contract;

  try {
    browser = await chromium.launch({ headless: true, args: ["--disable-dev-shm-usage"] });
    const page = await browser.newPage({
      viewport: { width: options.width, height: options.height },
      deviceScaleFactor: 1
    });
    page.on("console", (message) => {
      if (message.type() === "error") browserErrors.push(message.text());
    });
    page.on("pageerror", (error) => browserErrors.push(error.message));
    await page.goto(sourceServer.url, { waitUntil: "load" });
    await page.evaluate(() => document.fonts?.ready);
    const hasReadyContract = await page.evaluate(() => "__VISUAL_READY__" in window);
    if (hasReadyContract) {
      await page.waitForFunction(() => window.__VISUAL_READY__ === true, undefined, { timeout: 30_000 });
    }

    contract = await inspectContract(page);
    await prepareCapture(page, contract.kind);

    const geometry = presentationGeometry(options.width, options.height);
    const presentation = new PptxGenJS();
    presentation.defineLayout({ name: "HTML_STAGE", width: geometry.width, height: geometry.height });
    presentation.layout = "HTML_STAGE";
    presentation.author = "";
    presentation.company = "";
    presentation.subject = "Fidelity HTML stage presentation";
    presentation.title = basename(output, ".pptx");

    for (let index = 0; index < contract.slideCount; index += 1) {
      await navigate(page, contract.kind, index, options.settleMs);
      const imagePath = join(scratch, `${String(index + 1).padStart(4, "0")}.png`);
      await page.screenshot({ path: imagePath, type: "png", fullPage: false });
      const slide = presentation.addSlide();
      slide.addImage({ path: imagePath, x: 0, y: 0, w: geometry.width, h: geometry.height });
      addNotes(slide, notes, index);
    }

    if (browserErrors.length > 0) {
      throw new Error(`Browser errors during stage capture:\n${browserErrors.join("\n")}`);
    }
    await mkdir(dirname(output), { recursive: true });
    await presentation.writeFile({ fileName: output });
    await page.close();
  } finally {
    if (browser) await browser.close();
    await sourceServer.close();
    await rm(scratch, { recursive: true, force: true });
  }

  const outputStat = await stat(output);
  process.stdout.write(`${JSON.stringify({
    source,
    source_kind: contract.kind,
    output,
    mode: "fidelity",
    editable: false,
    slide_count: contract.slideCount,
    width: options.width,
    height: options.height,
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
