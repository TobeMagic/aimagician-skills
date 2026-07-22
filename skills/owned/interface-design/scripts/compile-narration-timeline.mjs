#!/usr/bin/env node

import { execFileSync, spawnSync } from "node:child_process";
import { access, mkdir, readFile, writeFile } from "node:fs/promises";
import { dirname, extname, join, resolve } from "node:path";

function usage() {
  return [
    "Usage: compile-narration-timeline.mjs --script <script.md> --manifest <narration.json>",
    "       [--audio-dir <dir> --timeline <timeline.json>] [--voiceover <voiceover.wav>] [--gap <seconds>] [--format <wav|mp3>]",
    "       [--voice <intent>] [--locale <locale>] [--ffprobe <binary>] [--ffmpeg <binary>]",
    "",
    "Parses ## scene-id sections and [[cue:id]] markers into a provider-neutral TTS manifest.",
    "With generated audio clips, measures real durations and writes a NarrationStage timeline; optional <scene>.words.json sidecars provide exact word/cue timing."
  ].join("\n");
}

function parseArgs(argv) {
  const options = { gap: 0.35, format: "wav", ffprobe: "ffprobe", ffmpeg: "ffmpeg" };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") return { help: true };
    if (!["--script", "--manifest", "--audio-dir", "--timeline", "--voiceover", "--gap", "--format", "--voice", "--locale", "--ffprobe", "--ffmpeg"].includes(token)) {
      throw new Error(`Unknown option: ${token}`);
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`${token} requires a value`);
    index += 1;
    options[token.slice(2).replace("-", "_")] = value;
  }
  if (!options.script || !options.manifest) throw new Error("--script and --manifest are required");
  options.gap = Number(options.gap);
  if (!Number.isFinite(options.gap) || options.gap < 0 || options.gap > 10) throw new Error("--gap must be from 0 to 10 seconds");
  if (!/^[A-Za-z0-9]+$/.test(options.format)) throw new Error("--format must be a safe extension such as wav or mp3");
  if ((options.audio_dir || options.voiceover) && !options.timeline) throw new Error("--timeline is required with --audio-dir or --voiceover");
  if (options.timeline && !options.audio_dir) throw new Error("--audio-dir is required with --timeline");
  return options;
}

function sceneId(value) {
  const id = value.trim().toLowerCase().replace(/[^a-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "");
  if (!id) throw new Error(`Invalid scene heading: ${value}`);
  return id;
}

function parseScript(source) {
  const sections = [];
  let current = null;
  for (const line of source.replace(/\r\n/g, "\n").split("\n")) {
    const heading = line.match(/^##\s+(.+?)\s*$/);
    if (heading) {
      if (current) sections.push(current);
      current = { id: sceneId(heading[1]), lines: [] };
    } else if (current) {
      current.lines.push(line);
    }
  }
  if (current) sections.push(current);
  if (sections.length === 0) throw new Error("Narration script contains no ## scene-id sections");
  const sceneIds = new Set();
  const cueIds = new Set();
  return sections.map((section) => {
    if (sceneIds.has(section.id)) throw new Error(`Duplicate scene id: ${section.id}`);
    sceneIds.add(section.id);
    const raw = section.lines.join("\n").replace(/\s+/g, " ").trim();
    const cues = [];
    let text = "";
    let cursor = 0;
    const marker = /\[\[cue:([A-Za-z0-9._-]+)\]\]/g;
    for (let match = marker.exec(raw); match; match = marker.exec(raw)) {
      text += raw.slice(cursor, match.index);
      const id = match[1];
      if (cueIds.has(id)) throw new Error(`Duplicate cue id: ${id}`);
      cueIds.add(id);
      cues.push({ id, char_offset: text.length });
      cursor = match.index + match[0].length;
    }
    text += raw.slice(cursor);
    text = text.trim();
    if (!text) throw new Error(`Scene ${section.id} has no spoken text`);
    for (const cue of cues) cue.char_offset = Math.min(cue.char_offset, text.length);
    return { id: section.id, text, cues };
  });
}

function durationOf(path, ffprobe, ffmpeg) {
  try {
    const output = execFileSync(ffprobe, ["-v", "error", "-show_entries", "format=duration", "-of", "json", path], { encoding: "utf8" });
    const duration = Number(JSON.parse(output).format?.duration);
    if (Number.isFinite(duration) && duration > 0) return duration;
  } catch {
    // A standalone ffprobe is not present in every ffmpeg distribution.
  }
  const probe = spawnSync(ffmpeg, ["-hide_banner", "-i", path, "-f", "null", "-"], { encoding: "utf8" });
  const match = String(probe.stderr ?? "").match(/Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)/);
  if (!match) throw new Error(`Could not measure positive audio duration: ${path}`);
  const duration = Number(match[1]) * 3600 + Number(match[2]) * 60 + Number(match[3]);
  if (!Number.isFinite(duration) || duration <= 0) throw new Error(`Could not measure positive audio duration: ${path}`);
  return duration;
}

async function readWords(path) {
  try {
    const parsed = JSON.parse(await readFile(path, "utf8"));
    const words = Array.isArray(parsed) ? parsed : parsed.words;
    if (!Array.isArray(words)) return [];
    return words.filter((word) => typeof word.text === "string" && Number.isFinite(Number(word.start)) && Number.isFinite(Number(word.end)) && Number(word.start) >= 0 && Number(word.end) >= Number(word.start))
      .map((word) => ({ text: word.text, start: Number(word.start), end: Number(word.end), char_start: Number.isFinite(Number(word.char_start)) ? Number(word.char_start) : null }));
  } catch (error) {
    if (error.code === "ENOENT") return [];
    throw error;
  }
}

function cueTime(cue, scene, words, duration) {
  if (words.length > 0) {
    const withOffsets = words.filter((word) => word.char_start !== null);
    if (withOffsets.length > 0) {
      const word = withOffsets.find((item) => item.char_start >= cue.char_offset) ?? withOffsets.at(-1);
      return { offset: Math.min(duration, word.start), source: "word-timestamps" };
    }
    const tokenIndex = scene.text.slice(0, cue.char_offset).trim().split(/\s+/).filter(Boolean).length;
    const word = words[Math.min(tokenIndex, words.length - 1)];
    return { offset: Math.min(duration, word.start), source: "word-timestamps" };
  }
  return { offset: duration * (cue.char_offset / Math.max(1, scene.text.length)), source: "proportional-estimate" };
}

function renderVoiceover(clips, totalDuration, outputPath, ffmpeg) {
  const args = ["-y"];
  for (const clip of clips) args.push("-i", clip.path);
  const filters = clips.map((clip, index) => `[${index}:a]adelay=${Math.round(clip.start * 1000)}|${Math.round(clip.start * 1000)},apad=pad_dur=${totalDuration.toFixed(6)}[a${index}]`);
  filters.push(`${clips.map((_, index) => `[a${index}]`).join("")}amix=inputs=${clips.length}:normalize=0:dropout_transition=0,atrim=duration=${totalDuration.toFixed(6)},aresample=48000[aout]`);
  args.push("-filter_complex", filters.join(";"), "-map", "[aout]");
  if (extname(outputPath).toLowerCase() === ".mp3") args.push("-c:a", "libmp3lame", "-b:a", "192k");
  else args.push("-c:a", "pcm_s16le");
  args.push(outputPath);
  execFileSync(ffmpeg, args, { stdio: "inherit" });
}

async function main(options) {
  const scriptPath = resolve(options.script);
  const manifestPath = resolve(options.manifest);
  const scenes = parseScript(await readFile(scriptPath, "utf8"));
  const manifest = {
    schema_version: 1,
    defaults: { locale: options.locale ?? "project-approved-locale", voice: options.voice ?? "project-approved-voice" },
    segments: scenes.map((scene) => ({ id: scene.id, text: scene.text, format: options.format }))
  };
  await mkdir(dirname(manifestPath), { recursive: true });
  await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  if (!options.audio_dir) {
    process.stdout.write(`${JSON.stringify({ script: scriptPath, manifest: manifestPath, segments: scenes.length }, null, 2)}\n`);
    return;
  }

  const audioDir = resolve(options.audio_dir);
  let cursor = 0;
  const timelineScenes = [];
  const clips = [];
  for (const scene of scenes) {
    const audioPath = join(audioDir, `${scene.id}.${options.format}`);
    await access(audioPath);
    const duration = durationOf(audioPath, options.ffprobe, options.ffmpeg);
    const words = await readWords(join(audioDir, `${scene.id}.words.json`));
    const absoluteWords = words.map((word) => ({ ...word, absoluteStart: cursor + word.start, absoluteEnd: cursor + word.end }));
    const cues = scene.cues.map((cue) => {
      const timing = cueTime(cue, scene, words, duration);
      return { id: cue.id, absoluteTime: cursor + timing.offset, timing_source: timing.source };
    });
    timelineScenes.push({
      id: scene.id,
      start: cursor,
      end: cursor + duration,
      duration,
      cues,
      chunks: [{ text: scene.text, absoluteStart: cursor, absoluteEnd: cursor + duration, words: absoluteWords }]
    });
    clips.push({ id: scene.id, path: audioPath, start: cursor, duration });
    cursor += duration + options.gap;
  }
  const totalDuration = Math.max(0, cursor - options.gap);
  const timelinePath = resolve(options.timeline);
  const timeline = { schema_version: 1, totalDuration, gap: options.gap, scenes: timelineScenes };
  await mkdir(dirname(timelinePath), { recursive: true });
  await writeFile(timelinePath, `${JSON.stringify(timeline, null, 2)}\n`, "utf8");
  let voiceoverPath = null;
  if (options.voiceover) {
    voiceoverPath = resolve(options.voiceover);
    await mkdir(dirname(voiceoverPath), { recursive: true });
    renderVoiceover(clips, totalDuration, voiceoverPath, options.ffmpeg);
  }
  const estimatedCues = timelineScenes.flatMap((scene) => scene.cues).filter((cue) => cue.timing_source === "proportional-estimate").length;
  process.stdout.write(`${JSON.stringify({ script: scriptPath, manifest: manifestPath, timeline: timelinePath, voiceover: voiceoverPath, segments: scenes.length, total_duration: totalDuration, estimated_cues: estimatedCues }, null, 2)}\n`);
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) process.stdout.write(`${usage()}\n`);
  else await main(options);
} catch (error) {
  process.stderr.write(`${error.message}\n\n${usage()}\n`);
  process.exitCode = 2;
}
