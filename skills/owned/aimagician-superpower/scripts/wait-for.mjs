#!/usr/bin/env node

import { spawn } from "node:child_process";

function parseArgs(argv) {
  const separator = argv.indexOf("--");
  if (separator < 0 || separator === argv.length - 1) {
    throw new Error("Usage: wait-for.mjs [--description TEXT] [--interval-ms N] [--timeout-ms N] [--format text|json] -- command [args...]");
  }
  const options = {
    description: "condition command to succeed",
    intervalMs: 250,
    timeoutMs: 30000,
    format: "text",
    command: argv[separator + 1],
    args: argv.slice(separator + 2)
  };
  for (let index = 0; index < separator; index += 1) {
    const token = argv[index];
    const next = argv[index + 1];
    if (!["--description", "--interval-ms", "--timeout-ms", "--format"].includes(token) || next === undefined) {
      throw new Error(`Invalid option: ${token}`);
    }
    index += 1;
    if (token === "--description") options.description = next;
    if (token === "--interval-ms") options.intervalMs = Number(next);
    if (token === "--timeout-ms") options.timeoutMs = Number(next);
    if (token === "--format") options.format = next;
  }
  if (!Number.isInteger(options.intervalMs) || options.intervalMs < 10) throw new Error("--interval-ms must be an integer >= 10");
  if (!Number.isInteger(options.timeoutMs) || options.timeoutMs < options.intervalMs) throw new Error("--timeout-ms must be an integer >= interval");
  if (!new Set(["text", "json"]).has(options.format)) throw new Error("--format must be text or json");
  return options;
}

function delay(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

function runAttempt(command, args) {
  return new Promise((resolve) => {
    const child = spawn(command, args, { shell: false, stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk.toString(); });
    child.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
    child.on("error", (error) => resolve({ exitCode: null, stdout, stderr: error.message }));
    child.on("close", (exitCode) => resolve({ exitCode, stdout, stderr }));
  });
}

function clipped(value) {
  const cleaned = value.trim();
  return cleaned.length > 500 ? `${cleaned.slice(0, 500)}...` : cleaned;
}

async function run(argv) {
  const options = parseArgs(argv);
  const started = Date.now();
  let attempts = 0;
  let last = { exitCode: null, stdout: "", stderr: "" };
  while (Date.now() - started <= options.timeoutMs) {
    attempts += 1;
    last = await runAttempt(options.command, options.args);
    if (last.exitCode === 0) {
      return {
        ok: true,
        description: options.description,
        attempts,
        elapsedMs: Date.now() - started,
        lastExitCode: 0
      };
    }
    if (Date.now() - started + options.intervalMs > options.timeoutMs) break;
    await delay(options.intervalMs);
  }
  return {
    ok: false,
    description: options.description,
    attempts,
    elapsedMs: Date.now() - started,
    lastExitCode: last.exitCode,
    lastError: clipped(last.stderr || last.stdout || "Condition command did not succeed")
  };
}

try {
  const formatIndex = process.argv.indexOf("--format");
  const format = formatIndex >= 0 ? process.argv[formatIndex + 1] : "text";
  const result = await run(process.argv.slice(2));
  if (format === "json") {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  } else if (result.ok) {
    process.stdout.write(`Condition met: ${result.description} (${result.attempts} attempts, ${result.elapsedMs}ms)\n`);
  } else {
    process.stdout.write(`Condition timed out: ${result.description} (${result.attempts} attempts, ${result.elapsedMs}ms)\nLast error: ${result.lastError}\n`);
  }
  if (!result.ok) process.exitCode = 1;
} catch (error) {
  process.stderr.write(`${error instanceof Error ? error.message : String(error)}\n`);
  process.exitCode = 2;
}
