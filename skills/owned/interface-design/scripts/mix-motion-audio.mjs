#!/usr/bin/env node

import { execFileSync } from "node:child_process";
import { access, mkdir, readFile, stat } from "node:fs/promises";
import { dirname, resolve } from "node:path";

function usage() {
  return [
    "Usage: mix-motion-audio.mjs --manifest <audio-cues.json> --output <video.mp4> [--ffmpeg <path>]",
    "",
    "The manifest names a source video and licensed voice, music, or effect clips.",
    "It never downloads media and never reads or prints provider credentials."
  ].join("\n");
}

function parseArgs(argv) {
  const options = { ffmpeg: process.env.FFMPEG_BIN || "ffmpeg" };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") return { ...options, help: true };
    if (!["--manifest", "--output", "--ffmpeg"].includes(token)) throw new Error(`Unknown option: ${token}`);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`${token} requires a value`);
    options[token.slice(2)] = value;
    index += 1;
  }
  if (!options.manifest || !options.output) throw new Error("--manifest and --output are required");
  return options;
}

function numeric(value, fallback, label, minimum = 0) {
  if (value === undefined) return fallback;
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed < minimum) throw new Error(`${label} must be >= ${minimum}`);
  return parsed;
}

async function main(options) {
  const manifestPath = resolve(options.manifest);
  const baseDir = dirname(manifestPath);
  const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
  if (manifest.schema_version !== 1) throw new Error("Audio cue manifest schema_version must be 1");
  if (!manifest.video) throw new Error("Audio cue manifest requires video");
  if (!Array.isArray(manifest.clips) || manifest.clips.length === 0) throw new Error("Audio cue manifest requires clips");

  const videoPath = resolve(baseDir, manifest.video);
  await access(videoPath);
  const inputs = ["-i", videoPath];
  const filters = [];
  const buses = { voice: [], music: [], effect: [] };
  for (let index = 0; index < manifest.clips.length; index += 1) {
    const clip = manifest.clips[index];
    if (!clip.path) throw new Error(`Clip ${index + 1} requires path`);
    const type = clip.type ?? "effect";
    if (!Object.hasOwn(buses, type)) throw new Error(`Clip ${index + 1} type must be voice, music, or effect`);
    const clipPath = resolve(baseDir, clip.path);
    await access(clipPath);
    inputs.push("-i", clipPath);

    const startMs = Math.round(numeric(clip.start, 0, `clips[${index}].start`) * 1000);
    const gainDb = numeric(clip.gain_db, 0, `clips[${index}].gain_db`, -60);
    const fadeIn = numeric(clip.fade_in, 0, `clips[${index}].fade_in`);
    const fadeOut = numeric(clip.fade_out, 0, `clips[${index}].fade_out`);
    const duration = clip.duration === undefined ? undefined : numeric(clip.duration, undefined, `clips[${index}].duration`, 0.01);
    const chain = [`[${index + 1}:a]aresample=48000`, `adelay=${startMs}|${startMs}`, `volume=${gainDb}dB`];
    if (fadeIn > 0) chain.push(`afade=t=in:st=${startMs / 1000}:d=${fadeIn}`);
    if (fadeOut > 0 && duration) chain.push(`afade=t=out:st=${startMs / 1000 + Math.max(0, duration - fadeOut)}:d=${fadeOut}`);
    if (duration) chain.push(`atrim=end=${startMs / 1000 + duration}`);
    const label = `a${index}`;
    filters.push(`${chain.join(",")}[${label}]`);
    buses[type].push(`[${label}]`);
  }

  const mixBus = (type) => {
    const members = buses[type];
    if (members.length === 0) return undefined;
    const output = `${type}bus`;
    if (members.length === 1) filters.push(`${members[0]}anull[${output}]`);
    else filters.push(`${members.join("")}amix=inputs=${members.length}:normalize=0:dropout_transition=0[${output}]`);
    return output;
  };
  const voiceBus = mixBus("voice");
  const musicBus = mixBus("music");
  const effectBus = mixBus("effect");
  const finalInputs = [];
  let ducking = false;
  if (voiceBus && musicBus) {
    const threshold = numeric(manifest.ducking?.threshold, 0.03, "ducking.threshold", 0.0001);
    const ratio = numeric(manifest.ducking?.ratio, 8, "ducking.ratio", 1);
    const attack = numeric(manifest.ducking?.attack_ms, 20, "ducking.attack_ms", 0.1);
    const release = numeric(manifest.ducking?.release_ms, 350, "ducking.release_ms", 1);
    filters.push(`[${voiceBus}]asplit=2[voicefinal][voicekeyraw]`);
    filters.push(`[voicekeyraw]apad[voicekey]`);
    filters.push(`[${musicBus}][voicekey]sidechaincompress=threshold=${threshold}:ratio=${ratio}:attack=${attack}:release=${release}[musicducked]`);
    finalInputs.push("[voicefinal]", "[musicducked]");
    ducking = true;
  } else {
    if (voiceBus) finalInputs.push(`[${voiceBus}]`);
    if (musicBus) finalInputs.push(`[${musicBus}]`);
  }
  if (effectBus) finalInputs.push(`[${effectBus}]`);
  const targetLufs = numeric(manifest.target_lufs, -16, "target_lufs", -40);
  filters.push(`${finalInputs.join("")}amix=inputs=${finalInputs.length}:normalize=0:dropout_transition=0,loudnorm=I=${targetLufs}:TP=-1.5:LRA=11,aresample=48000[aout]`);
  const output = resolve(options.output);
  await mkdir(dirname(output), { recursive: true });
  execFileSync(options.ffmpeg, [
    "-y", ...inputs,
    "-filter_complex", filters.join(";"),
    "-map", "0:v:0", "-map", "[aout]",
    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", output
  ], { stdio: "inherit" });
  const outputStat = await stat(output);
  process.stdout.write(`${JSON.stringify({ manifest: manifestPath, output, clips: manifest.clips.length, ducking, target_lufs: targetLufs, bytes: outputStat.size }, null, 2)}\n`);
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) process.stdout.write(`${usage()}\n`);
  else await main(options);
} catch (error) {
  process.stderr.write(`${error.message}\n\n${usage()}\n`);
  process.exitCode = 2;
}
