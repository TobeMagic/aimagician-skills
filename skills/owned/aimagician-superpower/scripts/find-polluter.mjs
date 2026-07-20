#!/usr/bin/env node

import { spawn } from "node:child_process";
import { access, readFile } from "node:fs/promises";
import { constants } from "node:fs";
import { resolve } from "node:path";

async function exists(path) {
  try {
    await access(path, constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

function parseArgs(argv) {
  const separator = argv.indexOf("--");
  if (separator < 0 || separator === argv.length - 1) {
    throw new Error("Usage: find-polluter.mjs --watch PATH (--candidate FILE ... | --files-from FILE) [--cwd PATH] [--format text|json] -- command [args containing {file}]");
  }
  const options = {
    watch: undefined,
    candidates: [],
    filesFrom: undefined,
    cwd: process.cwd(),
    format: "text",
    command: argv[separator + 1],
    args: argv.slice(separator + 2)
  };
  for (let index = 0; index < separator; index += 1) {
    const token = argv[index];
    const next = argv[index + 1];
    if (!["--watch", "--candidate", "--files-from", "--cwd", "--format"].includes(token) || next === undefined) {
      throw new Error(`Invalid option: ${token}`);
    }
    index += 1;
    if (token === "--watch") options.watch = next;
    if (token === "--candidate") options.candidates.push(next);
    if (token === "--files-from") options.filesFrom = next;
    if (token === "--cwd") options.cwd = resolve(next);
    if (token === "--format") options.format = next;
  }
  if (!options.watch) throw new Error("--watch is required");
  if (!options.args.some((argument) => argument.includes("{file}"))) throw new Error("Command arguments must contain {file}");
  if (!new Set(["text", "json"]).has(options.format)) throw new Error("--format must be text or json");
  options.watch = resolve(options.cwd, options.watch);
  return options;
}

function runCandidate(options, candidate) {
  const args = options.args.map((argument) => argument.replaceAll("{file}", candidate));
  return new Promise((resolveResult) => {
    const child = spawn(options.command, args, { cwd: options.cwd, shell: false, stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk.toString(); });
    child.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
    child.on("error", (error) => resolveResult({ exitCode: null, output: error.message }));
    child.on("close", (exitCode) => resolveResult({ exitCode, output: (stderr || stdout).trim().slice(0, 500) }));
  });
}

async function run(argv) {
  const options = parseArgs(argv);
  if (await exists(options.watch)) {
    return {
      ok: false,
      outcome: "initial-state-dirty",
      watch: options.watch,
      message: "The watched path already exists; remove it manually only if safe, then retry."
    };
  }
  if (options.filesFrom) {
    const lines = (await readFile(resolve(options.cwd, options.filesFrom), "utf8"))
      .split(/\r?\n/)
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith("#"));
    options.candidates.push(...lines);
  }
  options.candidates = [...new Set(options.candidates)];
  if (options.candidates.length === 0) throw new Error("Provide at least one --candidate or --files-from entry");

  const attempts = [];
  for (const candidate of options.candidates) {
    const result = await runCandidate(options, candidate);
    const polluted = await exists(options.watch);
    attempts.push({ candidate, exitCode: result.exitCode, polluted, output: result.output });
    if (polluted) {
      return {
        ok: false,
        outcome: "polluter-found",
        watch: options.watch,
        polluter: candidate,
        attempts
      };
    }
  }
  return {
    ok: true,
    outcome: "clean",
    watch: options.watch,
    polluter: null,
    attempts
  };
}

try {
  const formatIndex = process.argv.indexOf("--format");
  const format = formatIndex >= 0 ? process.argv[formatIndex + 1] : "text";
  const result = await run(process.argv.slice(2));
  if (format === "json") {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  } else if (result.outcome === "polluter-found") {
    process.stdout.write(`Polluter found: ${result.polluter}\nCreated: ${result.watch}\nThe watched path was preserved for inspection.\n`);
  } else if (result.outcome === "initial-state-dirty") {
    process.stdout.write(`${result.message}\nWatched path: ${result.watch}\n`);
  } else {
    process.stdout.write(`No polluter found across ${result.attempts.length} candidates.\n`);
  }
  if (result.outcome === "polluter-found") process.exitCode = 1;
  if (result.outcome === "initial-state-dirty") process.exitCode = 2;
} catch (error) {
  process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 2;
}
