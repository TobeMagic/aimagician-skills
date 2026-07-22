#!/usr/bin/env node

import { access, mkdir, readFile, stat, writeFile } from "node:fs/promises";
import { extname, join, resolve } from "node:path";
import { pathToFileURL } from "node:url";

function usage() {
  return [
    "Usage: render-narration-tts.mjs --manifest <narration.json> --adapter <adapter.mjs> --output-dir <dir>",
    "",
    "The adapter must export async synthesize({ id, text, voice, locale, outputPath }).",
    "It may return { words: [{ text, start, end, char_start? }] } for portable exact cue timing.",
    "Provider credentials remain in environment variables owned by the adapter."
  ].join("\n");
}

function parseArgs(argv) {
  const options = {};
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") return { help: true };
    if (!["--manifest", "--adapter", "--output-dir"].includes(token)) throw new Error(`Unknown option: ${token}`);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`${token} requires a value`);
    options[token.slice(2)] = value;
    index += 1;
  }
  if (!options.manifest || !options.adapter || !options["output-dir"]) {
    throw new Error("--manifest, --adapter, and --output-dir are required");
  }
  return options;
}

function validateManifest(manifest) {
  if (manifest.schema_version !== 1) throw new Error("Narration manifest schema_version must be 1");
  if (!Array.isArray(manifest.segments) || manifest.segments.length === 0) {
    throw new Error("Narration manifest must contain at least one segment");
  }
  const ids = new Set();
  for (const segment of manifest.segments) {
    if (!segment.id || !/^[A-Za-z0-9._-]+$/.test(segment.id)) throw new Error("Every segment needs a safe id");
    if (ids.has(segment.id)) throw new Error(`Duplicate narration segment id: ${segment.id}`);
    ids.add(segment.id);
    if (typeof segment.text !== "string" || segment.text.trim().length === 0) {
      throw new Error(`Narration segment ${segment.id} has no text`);
    }
  }
}

async function main(options) {
  const manifestPath = resolve(options.manifest);
  const adapterPath = resolve(options.adapter);
  const outputDir = resolve(options["output-dir"]);
  await access(adapterPath);
  const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
  validateManifest(manifest);

  const adapter = await import(pathToFileURL(adapterPath).href);
  if (typeof adapter.synthesize !== "function") throw new Error("Adapter does not export synthesize()");
  await mkdir(outputDir, { recursive: true });

  const outputs = [];
  for (const segment of manifest.segments) {
    const suffix = segment.format ? `.${String(segment.format).replace(/^\./, "")}` : ".wav";
    const filename = segment.filename ?? `${segment.id}${suffix}`;
    if (extname(filename).length === 0 || filename.includes("/") || filename.includes("\\")) {
      throw new Error(`Unsafe narration filename for ${segment.id}`);
    }
    const outputPath = join(outputDir, filename);
    const result = await adapter.synthesize({
      id: segment.id,
      text: segment.text,
      voice: segment.voice ?? manifest.defaults?.voice,
      locale: segment.locale ?? manifest.defaults?.locale,
      outputPath
    });
    const outputStat = await stat(outputPath);
    let wordsPath = null;
    if (Array.isArray(result?.words) && result.words.length > 0) {
      const words = result.words.map((word, index) => {
        const start = Number(word.start);
        const end = Number(word.end);
        if (typeof word.text !== "string" || !Number.isFinite(start) || !Number.isFinite(end) || start < 0 || end < start) {
          throw new Error(`Adapter returned invalid word timing ${index} for ${segment.id}`);
        }
        const normalized = { text: word.text, start, end };
        if (Number.isFinite(Number(word.char_start)) && Number(word.char_start) >= 0) normalized.char_start = Number(word.char_start);
        return normalized;
      });
      wordsPath = join(outputDir, `${segment.id}.words.json`);
      await writeFile(wordsPath, `${JSON.stringify({ schema_version: 1, id: segment.id, words }, null, 2)}\n`, "utf8");
    }
    outputs.push({ id: segment.id, path: outputPath, bytes: outputStat.size, words_path: wordsPath });
  }

  process.stdout.write(`${JSON.stringify({ manifest: manifestPath, adapter: adapterPath, outputs }, null, 2)}\n`);
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) process.stdout.write(`${usage()}\n`);
  else await main(options);
} catch (error) {
  process.stderr.write(`${error.message}\n\n${usage()}\n`);
  process.exitCode = 2;
}
