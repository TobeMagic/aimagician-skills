#!/usr/bin/env node

import { execFileSync, spawnSync } from "node:child_process";
import { createHash } from "node:crypto";
import { mkdir, readFile, stat, writeFile } from "node:fs/promises";
import { basename, join, resolve } from "node:path";

function usage() {
  return [
    "Usage: prepare-motion-review.mjs --input <media> --output-dir <dir> [options]",
    "Options:",
    "  --context <file>         Optional approved brief or director notes",
    "  --review-instructions <file> Optional project-specific semantic-review additions",
    "  --samples <count>        Representative frames (default: 7)",
    "  --freeze-seconds <n>     Freeze threshold (default: 3)",
    "  --ffmpeg <path>          Default: FFMPEG_BIN or ffmpeg",
    "  --ffprobe <path>         Default: FFPROBE_BIN or ffprobe",
    "",
    "Produces objective freeze/silence evidence, review frames, a manifest, and a provider-neutral semantic-review prompt."
  ].join("\n");
}

function parseArgs(argv) {
  const options = { samples: 7, "freeze-seconds": 3, ffmpeg: process.env.FFMPEG_BIN || "ffmpeg", ffprobe: process.env.FFPROBE_BIN || "ffprobe" };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") return { ...options, help: true };
    if (!["--input", "--output-dir", "--context", "--review-instructions", "--samples", "--freeze-seconds", "--ffmpeg", "--ffprobe"].includes(token)) throw new Error(`Unknown option: ${token}`);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`${token} requires a value`);
    options[token.slice(2)] = value;
    index += 1;
  }
  if (!options.input || !options["output-dir"]) throw new Error("--input and --output-dir are required");
  options.samples = Number(options.samples);
  options["freeze-seconds"] = Number(options["freeze-seconds"]);
  if (!Number.isInteger(options.samples) || options.samples < 3 || options.samples > 30) throw new Error("--samples must be an integer from 3 to 30");
  if (!Number.isFinite(options["freeze-seconds"]) || options["freeze-seconds"] <= 0) throw new Error("--freeze-seconds must be > 0");
  return options;
}

function probe(binary, input, ffmpeg) {
  try {
    return JSON.parse(execFileSync(binary, ["-v", "error", "-show_streams", "-show_format", "-of", "json", input], { encoding: "utf8" }));
  } catch {
    const fallback = spawnSync(ffmpeg, ["-hide_banner", "-i", input, "-f", "null", "-"], { encoding: "utf8" });
    const stderr = String(fallback.stderr ?? "");
    const durationMatch = stderr.match(/Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)/);
    if (!durationMatch) throw new Error("Unable to probe media with ffprobe or ffmpeg");
    const duration = Number(durationMatch[1]) * 3600 + Number(durationMatch[2]) * 60 + Number(durationMatch[3]);
    return { format: { duration }, streams: [{ codec_type: "video" }, ...(stderr.includes("Audio:") ? [{ codec_type: "audio" }] : [])] };
  }
}

function detect(binary, args) {
  const result = spawnSync(binary, args, { encoding: "utf8", stdio: ["ignore", "ignore", "pipe"] });
  if (result.error) throw result.error;
  if (result.status !== 0) throw new Error(String(result.stderr).trim());
  return String(result.stderr ?? "");
}

function parseTriples(text, prefix) {
  const values = [];
  const starts = [...text.matchAll(new RegExp(`${prefix}_start: ?([0-9.]+)`, "g"))].map((match) => Number(match[1]));
  const ends = [...text.matchAll(new RegExp(`${prefix}_end: ?([0-9.]+)`, "g"))].map((match) => Number(match[1]));
  const durations = [...text.matchAll(new RegExp(`${prefix}_duration: ?([0-9.]+)`, "g"))].map((match) => Number(match[1]));
  for (let index = 0; index < Math.max(starts.length, ends.length, durations.length); index += 1) {
    values.push({ start: starts[index], end: ends[index], duration: durations[index] });
  }
  return values;
}

async function main(options) {
  const input = resolve(options.input);
  const outputDir = resolve(options["output-dir"]);
  const frameDir = join(outputDir, "frames");
  await mkdir(frameDir, { recursive: true });
  const metadata = probe(options.ffprobe, input, options.ffmpeg);
  const duration = Number(metadata.format?.duration ?? metadata.streams?.find((stream) => stream.codec_type === "video")?.duration);
  if (!Number.isFinite(duration) || duration <= 0) throw new Error("Unable to determine media duration");
  const hasAudio = metadata.streams?.some((stream) => stream.codec_type === "audio") ?? false;

  const freezeLog = detect(options.ffmpeg, ["-v", "info", "-i", input, "-vf", `freezedetect=n=-60dB:d=${options["freeze-seconds"]}`, "-an", "-f", "null", "-"]);
  const silenceLog = hasAudio
    ? detect(options.ffmpeg, ["-v", "info", "-i", input, "-af", "silencedetect=noise=-40dB:d=0.2", "-vn", "-f", "null", "-"])
    : "";
  const frames = [];
  for (let index = 0; index < options.samples; index += 1) {
    const second = duration * ((index + 0.5) / options.samples);
    const filename = `${String(index + 1).padStart(2, "0")}-${second.toFixed(2)}s.png`;
    const path = join(frameDir, filename);
    execFileSync(options.ffmpeg, ["-v", "error", "-y", "-ss", String(second), "-i", input, "-frames:v", "1", path], { stdio: "pipe" });
    const bytes = await readFile(path);
    frames.push({ second: Number(second.toFixed(3)), file: join("frames", filename), sha256: createHash("sha256").update(bytes).digest("hex") });
  }

  const context = options.context ? await readFile(resolve(options.context), "utf8") : "No approved context file was supplied.";
  const reviewInstructions = options["review-instructions"]
    ? await readFile(resolve(options["review-instructions"]), "utf8")
    : "No project-specific review additions were supplied.";
  const manifest = {
    schema_version: 1,
    input,
    input_bytes: (await stat(input)).size,
    duration,
    has_audio: hasAudio,
    freeze_intervals: parseTriples(freezeLog, "freeze"),
    silence_intervals: parseTriples(silenceLog, "silence"),
    frames
  };
  const prompt = `# Motion Semantic Review\n\n## Approved Context\n\n${context}\n\n## Project Review Additions\n\n${reviewInstructions}\n\n## Objective Evidence\n\nRead review-manifest.json and inspect every image under frames/. Treat objective detections as evidence, not automatic design defects.\n\n## Review Checklist\n\n1. Missing, black, clipped, corrupted, or overlapping elements.\n2. Text legibility, spelling, hierarchy, safe crop, and downscaled readability.\n3. Narrative continuity, shared-element continuity, and unintended hard cuts.\n4. Product truth and whether the visible proof supports the approved context.\n5. Pace, holds, freeze intervals, visual density, and repeated frames.\n6. Composition balance, focus, brand specificity, and template-like decoration.\n7. If audio exists, correlate silence intervals with intended holds; do not claim to hear audio from still frames.\n\nSeparate blocker, high, medium, suggestion, and uncertainty. Cite frame filenames and timestamps. Do not invent events between sampled frames. The caller selects the authorized review model; this package remains provider-neutral.\n`;
  await writeFile(join(outputDir, "review-manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`);
  await writeFile(join(outputDir, "review-prompt.md"), prompt);
  process.stdout.write(`${JSON.stringify({ input: basename(input), output_dir: outputDir, duration, has_audio: hasAudio, frames: frames.length, freezes: manifest.freeze_intervals.length, silences: manifest.silence_intervals.length }, null, 2)}\n`);
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) process.stdout.write(`${usage()}\n`);
  else await main(options);
} catch (error) {
  process.stderr.write(`${error.message}\n\n${usage()}\n`);
  process.exitCode = 2;
}
