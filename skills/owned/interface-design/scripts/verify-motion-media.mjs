#!/usr/bin/env node

import { execFileSync, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdtemp, readFile, rm, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import { extname, join, resolve } from "node:path";

function usage() {
  return [
    "Usage: verify-motion-media.mjs --input <media> [contract options]",
    "Options:",
    "  --width <px> --height <px> --duration <seconds> --fps <number>",
    "  --max-mb <number>       Fail when the file exceeds the budget",
    "  --require-loop          Require an infinite GIF loop",
    "  --require-alpha         Require an encoded alpha channel",
    "  --ffmpeg <path>         Default: FFMPEG_BIN or ffmpeg",
    "  --ffprobe <path>        Default: FFPROBE_BIN or ffprobe",
    "  --json                  Machine-readable output"
  ].join("\n");
}

function parseArgs(argv) {
  const options = {
    ffmpeg: process.env.FFMPEG_BIN || "ffmpeg",
    ffprobe: process.env.FFPROBE_BIN || "ffprobe",
    json: false,
    requireLoop: false,
    requireAlpha: false
  };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") return { ...options, help: true };
    if (token === "--json") {
      options.json = true;
      continue;
    }
    if (token === "--require-loop") {
      options.requireLoop = true;
      continue;
    }
    if (token === "--require-alpha") {
      options.requireAlpha = true;
      continue;
    }
    if (!["--input", "--width", "--height", "--duration", "--fps", "--max-mb", "--ffmpeg", "--ffprobe"].includes(token)) {
      throw new Error(`Unknown option: ${token}`);
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`${token} requires a value`);
    options[token.slice(2).replace("-", "_")] = value;
    index += 1;
  }
  if (!options.input) throw new Error("--input is required");
  for (const key of ["width", "height", "duration", "fps", "max_mb"]) {
    if (options[key] !== undefined) {
      options[key] = Number(options[key]);
      if (!Number.isFinite(options[key]) || options[key] <= 0) throw new Error(`--${key.replace("_", "-")} must be > 0`);
    }
  }
  return options;
}

function rational(value) {
  if (!value || value === "0/0") return undefined;
  const [left, right] = String(value).split("/").map(Number);
  if (!Number.isFinite(left)) return undefined;
  return right ? left / right : left;
}

function run(binary, args) {
  return execFileSync(binary, args, { encoding: "utf8", stdio: ["ignore", "pipe", "pipe"] });
}

async function gifLoopCount(path) {
  const bytes = await readFile(path);
  const marker = Buffer.from("NETSCAPE2.0", "ascii");
  const index = bytes.indexOf(marker);
  if (index < 0 || index + 14 >= bytes.length) return undefined;
  return bytes[index + 13] | (bytes[index + 14] << 8);
}

async function sampleFrames({ input, duration, fps, ffmpeg }) {
  if (!duration || duration <= 0) return [];
  const scratch = await mkdtemp(join(tmpdir(), "motion-media-verify-"));
  try {
    const samples = [];
    const lastFrameTime = Math.max(0, duration - (fps ? 1 / fps : Math.min(0.1, duration / 4)));
    for (const [label, ratio] of [["start", 0.1], ["middle", 0.5], ["end", 0.9]]) {
      const target = Math.min(Math.max(0, duration * ratio), lastFrameTime);
      const path = join(scratch, `${label}.png`);
      execFileSync(ffmpeg, ["-v", "error", "-y", "-ss", String(target), "-i", input, "-frames:v", "1", path], { stdio: "pipe" });
      const bytes = await readFile(path);
      samples.push({ label, second: Number(target.toFixed(3)), sha256: createHash("sha256").update(bytes).digest("hex") });
    }
    return samples;
  } finally {
    await rm(scratch, { recursive: true, force: true });
  }
}

async function inspect(options) {
  const input = resolve(options.input);
  const metadata = JSON.parse(run(options.ffprobe, ["-v", "error", "-show_streams", "-show_format", "-of", "json", input]));
  const stream = metadata.streams?.find((candidate) => candidate.codec_type === "video");
  if (!stream) throw new Error("No video stream found");
  const inputStat = await stat(input);
  const duration = Number(stream.duration ?? metadata.format?.duration);
  const fps = rational(stream.avg_frame_rate ?? stream.r_frame_rate);
  const frames = stream.nb_frames && stream.nb_frames !== "N/A" ? Number(stream.nb_frames) : undefined;
  const type = extname(input).toLowerCase().replace(/^\./, "");
  const loopCount = type === "gif" ? await gifLoopCount(input) : undefined;
  const hasAlpha = String(stream.pix_fmt ?? "").startsWith("yuva") || String(stream.tags?.alpha_mode ?? "") === "1";
  const errors = [];

  if (options.width !== undefined && stream.width !== options.width) errors.push(`width ${stream.width} != ${options.width}`);
  if (options.height !== undefined && stream.height !== options.height) errors.push(`height ${stream.height} != ${options.height}`);
  if (options.duration !== undefined && Math.abs(duration - options.duration) > 0.2) {
    errors.push(`duration ${duration.toFixed(3)} != ${options.duration}`);
  }
  if (options.fps !== undefined && (!fps || Math.abs(fps - options.fps) > 0.6)) {
    errors.push(`fps ${fps ?? "unknown"} != ${options.fps}`);
  }
  if (options.max_mb !== undefined && inputStat.size > options.max_mb * 1024 * 1024) {
    errors.push(`size ${(inputStat.size / 1024 / 1024).toFixed(2)} MiB exceeds ${options.max_mb} MiB`);
  }
  if (options.requireLoop && type !== "gif") errors.push("--require-loop is only valid for GIF input");
  if (options.requireLoop && loopCount !== 0) errors.push(`GIF loop count is ${loopCount ?? "missing"}, expected infinite`);
  if (options.requireAlpha && !hasAlpha) errors.push(`alpha channel is missing (pixel format ${stream.pix_fmt ?? "unknown"})`);

  let blackDetection = "pass";
  const blackProbe = spawnSync(options.ffmpeg, [
    "-v", "info", "-i", input,
    "-vf", "blackdetect=d=0.15:pic_th=0.98:pix_th=0.02", "-an", "-f", "null", "-"
  ], { encoding: "utf8", stdio: ["ignore", "ignore", "pipe"] });
  if (blackProbe.error) throw blackProbe.error;
  const blackStderr = String(blackProbe.stderr ?? "");
  if (blackProbe.status !== 0) throw new Error(`ffmpeg black-frame probe failed: ${blackStderr.trim()}`);
  if (blackStderr.includes("black_start:")) {
    blackDetection = "fail";
    errors.push("black frame interval detected");
  }

  const samples = await sampleFrames({ input, duration, fps, ffmpeg: options.ffmpeg });
  if (new Set(samples.map((sample) => sample.sha256)).size < 2 && duration > 0.5) {
    errors.push("representative frames are identical; motion may be stalled");
  }

  return {
    input,
    type,
    codec: stream.codec_name,
    width: stream.width,
    height: stream.height,
    duration,
    fps,
    frames,
    bytes: inputStat.size,
    loop_count: loopCount,
    alpha: hasAlpha,
    black_detection: blackDetection,
    representative_frames: samples,
    pass: errors.length === 0,
    errors
  };
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    process.stdout.write(`${usage()}\n`);
  } else {
    const report = await inspect(options);
    process.stdout.write(options.json ? `${JSON.stringify(report, null, 2)}\n` : `${report.pass ? "PASS" : "FAIL"}: ${report.input}\n${report.errors.join("\n")}\n`);
    if (!report.pass) process.exitCode = 2;
  }
} catch (error) {
  process.stderr.write(`${error.message}\n\n${usage()}\n`);
  process.exitCode = 2;
}
