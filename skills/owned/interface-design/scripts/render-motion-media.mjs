#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { access, mkdir, rm, stat } from "node:fs/promises";
import { resolve, join } from "node:path";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const ALLOWED_FORMATS = new Set(["poster", "mp4", "gif", "webm", "mov", "png-sequence"]);

function usage() {
  return [
    "Usage: render-motion-media.mjs --input <source.html|url> --output-dir <dir> [options]",
    "Options:",
    "  --name <basename>       Output basename (default: product-loop)",
    "  --width <px>            Capture width (default: 1600)",
    "  --height <px>           Capture height (default: 900)",
    "  --duration <seconds>    Duration (default: 8)",
    "  --fps <frames>          MP4 frames per second (default: 24)",
    "  --poster-time <seconds> Poster capture time (default: 6.4)",
    "  --formats <list>        poster,mp4,gif,webm,mov,png-sequence (default: poster,mp4)",
    "  --gif-width <px>        GIF width (default: min(capture width, 960))",
    "  --gif-fps <frames>      GIF frames per second (default: min(fps, 12))",
    "  --gif-loop <mode>       forever or once (default: forever)",
    "  --gif-max-mb <number>   Optional fail-closed GIF size budget",
    "  --ffmpeg <path>         ffmpeg binary (default: FFMPEG_BIN or ffmpeg)",
    "  --poster-only           Backward-compatible alias for --formats poster",
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

function parseFormats(value) {
  const formats = [...new Set(value.split(",").map((item) => item.trim().toLowerCase()).filter(Boolean))];
  if (formats.length === 0) throw new Error("--formats must contain at least one format");
  for (const format of formats) if (!ALLOWED_FORMATS.has(format)) throw new Error(`Unsupported format: ${format}`);
  return formats;
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
    formats: ["poster", "mp4"],
    gifWidth: undefined,
    gifFps: undefined,
    gifLoop: "forever",
    gifMaxMb: undefined,
    ffmpeg: process.env.FFMPEG_BIN || "ffmpeg",
    keepFrames: false,
    posterOnlyCompat: false,
    formatsExplicit: false
  };

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") return { ...options, help: true };
    if (token === "--keep-frames") {
      options.keepFrames = true;
      continue;
    }
    if (token === "--poster-only") {
      options.posterOnlyCompat = true;
      continue;
    }
    if (!["--input", "--output-dir", "--name", "--width", "--height", "--duration", "--fps", "--poster-time", "--formats", "--gif-width", "--gif-fps", "--gif-loop", "--gif-max-mb", "--ffmpeg"].includes(token)) {
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
    if (token === "--formats") {
      options.formats = parseFormats(value);
      options.formatsExplicit = true;
    }
    if (token === "--gif-width") options.gifWidth = parseNumber(value, token, 1);
    if (token === "--gif-fps") options.gifFps = parseNumber(value, token, 1);
    if (token === "--gif-loop") options.gifLoop = value;
    if (token === "--gif-max-mb") options.gifMaxMb = parseNumber(value, token, 0.01);
    if (token === "--ffmpeg") options.ffmpeg = value;
  }

  if (!options.input) throw new Error("--input is required");
  if (!options.outputDir) throw new Error("--output-dir is required");
  if (!/^[A-Za-z0-9._-]+$/.test(options.name)) throw new Error("--name may contain only letters, numbers, dot, underscore, and dash");
  if (options.posterOnlyCompat && options.formatsExplicit) throw new Error("--poster-only cannot be combined with --formats");
  if (options.posterOnlyCompat) options.formats = ["poster"];
  if (!new Set(["forever", "once"]).has(options.gifLoop)) throw new Error("--gif-loop must be forever or once");
  if (options.formats.includes("poster") && options.posterTime > options.duration) throw new Error("--poster-time cannot exceed --duration");

  options.width = Math.round(options.width);
  options.height = Math.round(options.height);
  options.fps = Math.round(options.fps);
  options.gifWidth = Math.round(options.gifWidth ?? Math.min(options.width, 960));
  options.gifFps = Math.round(options.gifFps ?? Math.min(options.fps, 12));
  const fullRateFormats = ["mp4", "webm", "mov", "png-sequence"];
  options.captureFps = Math.max(fullRateFormats.some((format) => options.formats.includes(format)) ? options.fps : 0, options.formats.includes("gif") ? options.gifFps : 0);
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

async function fileBytes(path) {
  if (!path) return null;
  return (await stat(path)).size;
}

async function main(options) {
  if (!/^(https?:|file:)/.test(options.input)) await access(resolve(options.input));
  const outputDir = resolve(options.outputDir);
  const frameDir = join(outputDir, options.formats.includes("png-sequence") ? `${options.name}-frames` : `.${options.name}-frames`);
  const posterPng = join(outputDir, `.${options.name}-poster.png`);
  const palettePng = join(outputDir, `.${options.name}-palette.png`);
  const posterPath = options.formats.includes("poster")
    ? join(outputDir, options.posterOnlyCompat ? `${options.name}.webp` : `${options.name}-poster.webp`)
    : null;
  const videoPath = options.formats.includes("mp4") ? join(outputDir, `${options.name}.mp4`) : null;
  const gifPath = options.formats.includes("gif") ? join(outputDir, `${options.name}.gif`) : null;
  const webmPath = options.formats.includes("webm") ? join(outputDir, `${options.name}.webm`) : null;
  const movPath = options.formats.includes("mov") ? join(outputDir, `${options.name}.mov`) : null;
  await mkdir(outputDir, { recursive: true });
  await rm(frameDir, { recursive: true, force: true });
  if (options.captureFps > 0) await mkdir(frameDir, { recursive: true });

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
    if (posterPath) {
      await setTime(page, options.posterTime);
      await page.screenshot({ path: posterPng, type: "png", omitBackground: true });
    }

    if (options.captureFps > 0) {
      const frameCount = Math.ceil(options.duration * options.captureFps);
      const batchSize = options.captureFps * 2;
      for (let frame = 0; frame < frameCount; frame += 1) {
        if (frame % batchSize === 0) {
          await page.close();
          page = await openPage();
        }
        await setTime(page, frame / options.captureFps);
        await page.screenshot({
          path: join(frameDir, `frame-${String(frame).padStart(6, "0")}.png`),
          type: "png",
          omitBackground: true
        });
      }
    }

    if (consoleErrors.length > 0) throw new Error(`Browser errors during capture:\n${consoleErrors.join("\n")}`);
  } finally {
    if (page && !page.isClosed()) await page.close();
    await browser.close();
  }

  if (posterPath) runFfmpeg(options.ffmpeg, ["-y", "-i", posterPng, "-c:v", "libwebp", "-quality", "92", posterPath]);
  if (videoPath) {
    const keyframeInterval = options.fps * 2;
    const videoFilter = options.captureFps === options.fps ? [] : ["-vf", `fps=${options.fps}`];
    runFfmpeg(options.ffmpeg, [
      "-y", "-framerate", String(options.captureFps), "-i", join(frameDir, "frame-%06d.png"),
      ...videoFilter,
      "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p",
      "-g", String(keyframeInterval), "-keyint_min", String(keyframeInterval), "-sc_threshold", "0",
      "-movflags", "+faststart", "-an", videoPath
    ]);
  }
  if (gifPath) {
    const scaleFilter = `fps=${options.gifFps},scale=${options.gifWidth}:-1:flags=lanczos`;
    runFfmpeg(options.ffmpeg, [
      "-y", "-framerate", String(options.captureFps), "-i", join(frameDir, "frame-%06d.png"),
      "-vf", `${scaleFilter},palettegen=stats_mode=diff`,
      "-frames:v", "1", "-update", "1", palettePng
    ]);
    runFfmpeg(options.ffmpeg, [
      "-y", "-framerate", String(options.captureFps), "-i", join(frameDir, "frame-%06d.png"), "-i", palettePng,
      "-filter_complex", `[0:v]${scaleFilter}[scaled];[scaled][1:v]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle`,
      "-loop", options.gifLoop === "forever" ? "0" : "-1", gifPath
    ]);
  }
  if (webmPath) {
    runFfmpeg(options.ffmpeg, [
      "-y", "-framerate", String(options.captureFps), "-i", join(frameDir, "frame-%06d.png"),
      "-vf", `fps=${options.fps}`, "-c:v", "libvpx-vp9", "-lossless", "1",
      "-pix_fmt", "yuva420p", "-auto-alt-ref", "0", "-an", webmPath
    ]);
  }
  if (movPath) {
    runFfmpeg(options.ffmpeg, [
      "-y", "-framerate", String(options.captureFps), "-i", join(frameDir, "frame-%06d.png"),
      "-vf", `fps=${options.fps}`, "-c:v", "prores_ks", "-profile:v", "4",
      "-pix_fmt", "yuva444p10le", "-an", movPath
    ]);
  }

  await rm(posterPng, { force: true });
  await rm(palettePng, { force: true });
  if (!options.keepFrames && !options.formats.includes("png-sequence")) await rm(frameDir, { recursive: true, force: true });

  const posterBytes = await fileBytes(posterPath);
  const videoBytes = await fileBytes(videoPath);
  const gifBytes = await fileBytes(gifPath);
  const webmBytes = await fileBytes(webmPath);
  const movBytes = await fileBytes(movPath);
  const result = {
    source: sourceUrl(options.input),
    formats: options.formats,
    poster: posterPath,
    video: videoPath,
    gif: gifPath,
    webm: webmPath,
    mov: movPath,
    png_sequence: options.formats.includes("png-sequence") ? frameDir : null,
    width: options.width,
    height: options.height,
    duration: options.duration,
    fps: options.fps,
    frames: options.captureFps > 0 ? Math.ceil(options.duration * options.captureFps) : 0,
    capture_fps: options.captureFps,
    gif_width: gifPath ? options.gifWidth : null,
    gif_height: gifPath ? Math.round(options.height * options.gifWidth / options.width) : null,
    gif_fps: gifPath ? options.gifFps : null,
    gif_loop: gifPath ? options.gifLoop : null,
    bytes: { poster: posterBytes, video: videoBytes, gif: gifBytes, webm: webmBytes, mov: movBytes }
  };
  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  if (gifBytes !== null && options.gifMaxMb !== undefined && gifBytes > options.gifMaxMb * 1024 * 1024) {
    throw new Error(`GIF size ${(gifBytes / 1024 / 1024).toFixed(2)} MiB exceeds ${options.gifMaxMb} MiB; artifact retained for inspection`);
  }
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) process.stdout.write(`${usage()}\n`);
  else await main(options);
} catch (error) {
  process.stderr.write(`${error.message}\n\n${usage()}\n`);
  process.exitCode = 2;
}
