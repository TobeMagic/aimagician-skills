#!/usr/bin/env node

import { access, mkdir, readFile, stat } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

function usage() {
  return [
    "Usage: render-with-adapter.mjs --manifest <render.json> --adapter <adapter.mjs> --output-dir <dir>",
    "",
    "The project-owned adapter must export async render({ manifest, manifestPath, outputDir }).",
    "Use this only when the local deterministic renderer cannot satisfy the required 3D, shader, alpha, or scale contract."
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
  if (!options.manifest || !options.adapter || !options["output-dir"]) throw new Error("--manifest, --adapter, and --output-dir are required");
  return options;
}

async function main(options) {
  const manifestPath = resolve(options.manifest);
  const adapterPath = resolve(options.adapter);
  const outputDir = resolve(options["output-dir"]);
  const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
  if (manifest.schema_version !== 1 || !manifest.source || !manifest.format) throw new Error("Render manifest requires schema_version 1, source, and format");
  await access(adapterPath);
  await mkdir(outputDir, { recursive: true });
  const adapter = await import(pathToFileURL(adapterPath).href);
  if (typeof adapter.render !== "function") throw new Error("Adapter does not export render()");
  const result = await adapter.render({ manifest, manifestPath, outputDir });
  const outputs = Array.isArray(result?.outputs) ? result.outputs : [];
  if (outputs.length === 0) throw new Error("Adapter returned no outputs");
  const verified = [];
  for (const output of outputs) {
    const path = resolve(outputDir, output);
    await access(path);
    verified.push({ path, bytes: (await stat(path)).size });
  }
  process.stdout.write(`${JSON.stringify({ adapter: adapterPath, manifest: manifestPath, outputs: verified }, null, 2)}\n`);
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) process.stdout.write(`${usage()}\n`);
  else await main(options);
} catch (error) {
  process.stderr.write(`${error.message}\n\n${usage()}\n`);
  process.exitCode = 2;
}
