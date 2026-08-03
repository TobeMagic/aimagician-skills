#!/usr/bin/env node

import { access, readFile } from "node:fs/promises";
import { join, resolve } from "node:path";

function usage() {
  return "Usage: validate-distillation.mjs --root <distillation-root> [--format json|text]";
}

function parseArgs(argv) {
  const options = { format: "text" };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") return { ...options, help: true };
    if (!["--root", "--format"].includes(token)) throw new Error(`Unknown option: ${token}`);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`${token} requires a value`);
    index += 1;
    options[token.slice(2)] = value;
  }
  if (!options.root) throw new Error("--root is required");
  if (!["json", "text"].includes(options.format)) throw new Error("--format must be json or text");
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

async function main(options) {
  const root = resolve(options.root);
  const errors = [];
  const warnings = [];
  const required = [
    "PIPELINE_STATE.md",
    "distillation-manifest.json",
    "SOURCE_OVERVIEW.md",
    "verified.md",
    "INDEX.md",
    "GLOSSARY.md",
    "DIGEST.md"
  ];
  for (const file of required) {
    if (!await exists(join(root, file))) errors.push(`missing:${file}`);
  }

  let manifest;
  const manifestPath = join(root, "distillation-manifest.json");
  if (await exists(manifestPath)) {
    try {
      manifest = JSON.parse(await readFile(manifestPath, "utf8"));
    } catch (error) {
      errors.push(`invalid-manifest-json:${error.message}`);
    }
  }

  if (manifest) {
    if (!manifest.source?.title || !manifest.source?.type || !Array.isArray(manifest.source?.locations)) {
      errors.push("manifest-source-contract");
    }
    if (!Array.isArray(manifest.skills) || manifest.skills.length === 0) {
      errors.push("manifest-skills-empty");
    } else {
      const ids = new Set();
      for (const item of manifest.skills) {
        if (!item.id || !item.path) {
          errors.push("manifest-skill-id-or-path-missing");
          continue;
        }
        if (ids.has(item.id)) errors.push(`duplicate-skill:${item.id}`);
        ids.add(item.id);
        const skillRoot = resolve(root, item.path);
        for (const file of ["SKILL.md", "test-prompts.json", "test-results.md"]) {
          const path = join(skillRoot, file);
          if (!await exists(path)) errors.push(`missing:${item.path}/${file}`);
          if (file.endsWith(".json") && await exists(path)) {
            try {
              const parsed = JSON.parse(await readFile(path, "utf8"));
              if (!Array.isArray(parsed.scenarios) || parsed.scenarios.length < 4) {
                warnings.push(`insufficient-scenarios:${item.id}`);
              }
            } catch (error) {
              errors.push(`invalid-json:${item.path}/${file}:${error.message}`);
            }
          }
        }
      }
    }
  }

  const result = {
    root,
    status: errors.length === 0 ? "pass" : "fail",
    errors,
    warnings
  };
  if (options.format === "json") process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  else {
    process.stdout.write(`${result.status.toUpperCase()} ${root}\n`);
    for (const error of errors) process.stdout.write(`ERROR ${error}\n`);
    for (const warning of warnings) process.stdout.write(`WARN ${warning}\n`);
  }
  if (errors.length > 0) process.exitCode = 1;
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) process.stdout.write(`${usage()}\n`);
  else await main(options);
} catch (error) {
  process.stderr.write(`${error.message}\n${usage()}\n`);
  process.exitCode = 2;
}
