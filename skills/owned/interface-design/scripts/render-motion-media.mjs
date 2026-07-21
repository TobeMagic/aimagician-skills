#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { access, mkdir, rm } from "node:fs/promises";
import { resolve, join } from "node:path";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);

function usage() {
  return [
    "Usage: render-motion-media.mjs --input <source.html|url> --output-dir <dir> [options]",
    "Options:",
    "  --name <basename>       Output basename (default: product-loop)",
    "  --width <px>            Viewport width (default: 1600)",
    "  --height <px>           Viewport height (default: 900)",
    "  --duration <seconds>    Duration (default: 8)",
    "  --fps <frames>          Frames per second (default: 24)",
    "  --poster-time <seconds> Poster capture time (default: 6.4)",
    "  --ffmpeg <path>         ffmpeg binary (default: FFMPEG_BIN or ffmpeg)",
    "  --poster-only           Render one WebP still and skip frame/video capture",
    "  --keep-frames           Keep generated PNG frame directory",
    "",
    "The source must expose window.__VISUAL_READY__ and window.__setDesignTime(seconds)."
  ].join("\n");
}

function parseNumber(value, option, minimum) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < minimum) throw new Error(`${option} must be >= ${minimum}`);
  return parsed;
}

function parseArgs(argv) {
  const options = {
    input: undefined,
    outputDir: undefined,
    name: "product-loop",
    width: 1600,
    height: 900,
    duration: 8,
    fps: 24,
    posterTime: 6.4,
    ffmpeg: process.env.FFMPEG_BIN || "ffmpeg",
    keepFrames: false,
    posterOnly: false
  };

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") return { ...options, help: true };
    if (token === "--keep-frames") {
      options.keepFrames = true;
      continue;
    }
    if (token === "--poster-only") {
      options.posterOnly = true;
      continue;
    }
    if (!["--input", "--output-dir", "--name", "--width", "--height", "--duration", "--fps", "--poster-time", "--ffmpeg"].includes(token)) {
      throw new Error(`Unknown option: ${token}`);
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`${token} requires a value`);
    index += 1;
    if (token === "--input") options.input = value;
    if (token === "--output-dir") options.outputDir = value;
    if (token === "--name") options.name = value;
    if (token === "--width") options.width = parseNumber(value, token, 1);
    if (token === "--height") options.height = parseNumber(value, token, 1);
    if (token === "--duration") options.duration = parseNumber(value, token, 0.1);
    if (token === "--fps") options.fps = parseNumber(value, token, 1);
    if (token === "--poster-time") options.posterTime = parseNumber(value, token, 0);
    if (token === "--ffmpeg") options.ffmpeg = value;
  }

  if (!options.input) throw new Error("--input is required");
  if (!options.outputDir) throw new Error("--output-dir is required");
  if (!/^[A-Za-z0-9._-]+$/.test(options.name)) throw new Error("--name may contain only letters, numbers, dot, underscore, and dash");
  if (!options.posterOnly && options.posterTime > options.duration) throw new Error("--poster-time cannot exceed --duration");
  options.width = Math.round(options.width);
  options.height = Math.round(options.height);
  options.fps = Math.round(options.fps);
  return options;
}

function sourceUrl(input) {
  return /^(https?:|file:)/.test(input) ? input : pathToFileURL(resolve(input)).href;
}

function runFfmpeg(binary, args) {
  execFileSync(binary, args, { stdio: "inherit" });
}

async function loadPlaywright() {
  try {
    return require("playwright");
  } catch (error) {
    throw new Error(`Playwright is required. Install it in the project or expose its node_modules through NODE_PATH. ${error.message}`);
  }
}

async function main(options) {
  if (!/^(https?:|file:)/.test(options.input)) await access(resolve(options.input));
  const outputDir = resolve(options.outputDir);
  const frameDir = join(outputDir, `.${options.name}-frames`);
  const posterPng = join(outputDir, `.${options.name}-poster.png`);
  const posterWebp = join(outputDir, options.posterOnly ? `${options.name}.webp` : `${options.name}-poster.webp`);
  const videoPath = join(outputDir, `${options.name}.mp4`);
  await mkdir(outputDir, { recursive: true });
  await rm(frameDir, { recursive: true, force: true });
  await mkdir(frameDir, { recursive: true });

  const { chromium } = await loadPlaywright();
  const browser = await chromium.launch({ headless: true, args: ["--disable-dev-shm-usage"] });
  const consoleErrors = [];
  let page;
  try {
    const openPage = async () => {
      const nextPage = await browser.newPage({ viewport: { width: options.width, height: options.height }, deviceScaleFactor: 1 });
      nextPage.on("console", (message) => {
        if (message.type() === "error") consoleErrors.push(message.text());
      });
      nextPage.on("pageerror", (error) => consoleErrors.push(error.message));
      await nextPage.emulateMedia({ reducedMotion: "reduce" });
      await nextPage.goto(sourceUrl(options.input), { waitUntil: "load" });
      await nextPage.waitForFunction(() => window.__VISUAL_READY__ === true, undefined, { timeout: 30_000 });
      await nextPage.evaluate(() => document.fonts?.ready);
      const hasClock = await nextPage.evaluate(() => typeof window.__setDesignTime === "function");
      if (!hasClock) throw new Error("Source does not expose window.__setDesignTime(seconds)");
      return nextPage;
    };

    const setTime = async (targetPage, seconds) => {
      await targetPage.evaluate((time) => window.__setDesignTime(time), seconds);
      await targetPage.evaluate(() => new Promise((resolveFrame) => requestAnimationFrame(() => requestAnimationFrame(resolveFrame))));
    };

    page = await openPage();
    await setTime(page, options.posterTime);
    await page.screenshot({ path: posterPng, type: "png" });

    if (!options.posterOnly) {
      const frameCount = Math.ceil(options.duration * options.fps);
      const batchSize = options.fps * 2;
      for (let frame = 0; frame < frameCount; frame += 1) {
        if (frame % batchSize === 0) {
          await page.close();
          page = await openPage();
        }
        await setTime(page, frame / options.fps);
        await page.screenshot({
          path: join(frameDir, `frame-${String(frame).padStart(6, "0")}.png`),
          type: "png"
        });
      }
    }

    if (consoleErrors.length > 0) throw new Error(`Browser errors during capture:\n${consoleErrors.join("\n")}`);
  } finally {
    if (page && !page.isClosed()) await page.close();
    await browser.close();
  }

  runFfmpeg(options.ffmpeg, ["-y", "-i", posterPng, "-c:v", "libwebp", "-quality", "92", posterWebp]);
  if (!options.posterOnly) {
    const keyframeInterval = options.fps * 2;
    runFfmpeg(options.ffmpeg, [
      "-y", "-framerate", String(options.fps), "-i", join(frameDir, "frame-%06d.png"),
      "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p",
      "-g", String(keyframeInterval), "-keyint_min", String(keyframeInterval), "-sc_threshold", "0",
      "-movflags", "+faststart", "-an", videoPath
    ]);
  }

  await rm(posterPng, { force: true });
  if (!options.keepFrames) await rm(frameDir, { recursive: true, force: true });
  process.stdout.write(`${JSON.stringify({
    source: sourceUrl(options.input),
    poster: posterWebp,
    video: options.posterOnly ? null : videoPath,
    width: options.width,
    height: options.height,
    duration: options.duration,
    fps: options.fps,
    frames: options.posterOnly ? 0 : Math.ceil(options.duration * options.fps)
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
