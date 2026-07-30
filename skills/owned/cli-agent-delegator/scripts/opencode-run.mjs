#!/usr/bin/env node

import { spawn } from "node:child_process";
import { execFile } from "node:child_process";
import { mkdir, mkdtemp, readFile, rename, rm, stat, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { homedir, tmpdir } from "node:os";
import { dirname, join, relative, resolve, sep } from "node:path";
import { promisify } from "node:util";
import { pathToFileURL } from "node:url";
import { analyzeImages } from "../../vision-analysis/scripts/analyze.mjs";

const execFileAsync = promisify(execFile);

export const DEFAULT_TEXT_MODEL = "opencode/deepseek-v4-flash-free";
export const DEFAULT_QUOTA_FALLBACK_MODEL = "agnes/agnes-2.0-flash";
export const CACHE_TTL_MS = 24 * 60 * 60 * 1000;

const ANSI_PATTERN = /\u001b\[[0-?]*[ -/]*[@-~]/g;
const MODEL_ID_PATTERN = /^([a-z0-9._-]+\/[a-z0-9._-]+)\s*$/gim;
const MAX_CAPTURED_OUTPUT = 2 * 1024 * 1024;

function cachePath() {
  const root = process.env.XDG_CACHE_HOME || join(homedir(), ".cache");
  return join(root, "aimagician-superpower", "cli-agent-delegator", "opencode-models.json");
}

function stripAnsi(value) {
  return value.replace(ANSI_PATTERN, "");
}

function scanJsonObject(source, start) {
  let depth = 0;
  let inString = false;
  let escaped = false;

  for (let index = start; index < source.length; index += 1) {
    const char = source[index];
    if (inString) {
      if (escaped) {
        escaped = false;
      } else if (char === "\\") {
        escaped = true;
      } else if (char === "\"") {
        inString = false;
      }
      continue;
    }
    if (char === "\"") {
      inString = true;
    } else if (char === "{") {
      depth += 1;
    } else if (char === "}") {
      depth -= 1;
      if (depth === 0) return source.slice(start, index + 1);
    }
  }
  return null;
}

function numericLeaves(value) {
  if (typeof value === "number") return [value];
  if (!value || typeof value !== "object") return [];
  return Object.values(value).flatMap(numericLeaves);
}

function normalizeModel(fullId, metadata) {
  const input = metadata.capabilities?.input ?? {};
  const costValues = numericLeaves(metadata.cost);
  return {
    id: fullId,
    provider: metadata.providerID ?? fullId.split("/")[0],
    name: metadata.name ?? metadata.id ?? fullId,
    status: metadata.status ?? "unknown",
    free: costValues.length > 0 && costValues.every((value) => value === 0),
    context: metadata.limit?.context ?? null,
    output: metadata.limit?.output ?? null,
    reasoning: metadata.capabilities?.reasoning === true,
    toolcall: metadata.capabilities?.toolcall === true,
    textInput: input.text !== false,
    imageInput: input.image === true,
    capabilitySource: "provider-metadata",
    capabilityNote: null
  };
}

export function parseVerboseModels(rawOutput) {
  const source = stripAnsi(rawOutput);
  const models = [];
  let match;

  while ((match = MODEL_ID_PATTERN.exec(source)) !== null) {
    let objectStart = MODEL_ID_PATTERN.lastIndex;
    while (/\s/.test(source[objectStart] ?? "")) objectStart += 1;
    if (source[objectStart] !== "{") continue;
    const objectText = scanJsonObject(source, objectStart);
    if (!objectText) continue;
    try {
      models.push(normalizeModel(match[1], JSON.parse(objectText)));
    } catch {
      // Ignore one malformed provider record while preserving usable models.
    }
  }

  return models;
}

function isUsableFreeModel(model) {
  return model.free && !new Set(["deprecated", "inactive", "disabled"]).has(model.status);
}

export function freeCandidates(models, { exclude = [] } = {}) {
  const excluded = new Set(exclude);
  return models
    .filter((model) => isUsableFreeModel(model))
    .filter((model) => model.textInput)
    .filter((model) => model.provider === "opencode")
    .filter((model) => !excluded.has(model.id))
    .sort((left, right) => left.id.localeCompare(right.id));
}

export function resolveModelRoute({
  models,
  requestedModel,
  textDefault = process.env.AIMAGICIAN_OPENCODE_TEXT_MODEL || DEFAULT_TEXT_MODEL
}) {
  const candidates = freeCandidates(models);
  const byId = new Map(candidates.map((model) => [model.id, model]));

  if (requestedModel) {
    const selected = byId.get(requestedModel);
    if (!selected) {
      return {
        status: "invalid-selection",
        reason: `${requestedModel} is not an active free OpenCode reasoning model`,
        candidates
      };
    }
    if (byId.has(textDefault) && requestedModel !== textDefault) {
      return {
        status: "invalid-selection",
        reason: `${textDefault} is available and remains the required reasoning default`,
        candidates
      };
    }
    return { status: "selected", model: selected, reason: "controller-selection", candidates };
  }

  const selected = byId.get(textDefault);
  if (selected) {
    return {
      status: "selected",
      model: selected,
      reason: "default-text-model",
      candidates
    };
  }

  return {
    status: "selection-required",
    reason: `${textDefault} is not available; the controller must choose a task-appropriate free reasoning model`,
    candidates
  };
}

export function classifyOpenCodeFailure(output, exitCode) {
  if (exitCode === 0) return "success";
  const value = stripAnsi(output);
  if (isTerminalUsageEvent(value)) {
    return "usage-limit";
  }
  if (/(?:model[^.\n]*(?:not found|unknown|unavailable|disabled)|unknown model|invalid model)/i.test(value)) {
    return "model-unavailable";
  }
  if (/(?:unauthorized|forbidden|invalid api key|authentication|credential)/i.test(value)) {
    return "authentication";
  }
  if (/(?:permission denied|operation not permitted|access denied)/i.test(value)) {
    return "permission";
  }
  if (/(?:unknown option|invalid option|unexpected argument|unknown argument|usage:\s*opencode)/i.test(value)) {
    return "command-syntax";
  }
  if (/(?:ECONNRESET|ENOTFOUND|ETIMEDOUT|network error|socket hang up)/i.test(value)) {
    return "network";
  }
  return "worker-failure";
}

export function isTerminalUsageEvent(chunk) {
  const value = stripAnsi(chunk);
  return /(?:stream error|AI_APICallError|AI_RetryError|provider[^.\n]*(?:error|reject)|(?:status|code)[^0-9]{0,8}429|HTTP\s*429)[\s\S]{0,400}(?:rate[ -]?limit|usage[ -]?(?:limit|quota)|quota|resource[_ ]exhausted|429)/i.test(value);
}

async function readCachedModels(path, now = Date.now()) {
  try {
    const info = await stat(path);
    if (now - info.mtimeMs > CACHE_TTL_MS) return null;
    const parsed = JSON.parse(await readFile(path, "utf8"));
    return Array.isArray(parsed.models) ? parsed.models : null;
  } catch {
    return null;
  }
}

async function writeCache(path, models) {
  await mkdir(dirname(path), { recursive: true });
  const temporary = `${path}.${process.pid}.tmp`;
  await writeFile(temporary, `${JSON.stringify({ refreshedAt: new Date().toISOString(), models }, null, 2)}\n`, "utf8");
  await rename(temporary, path);
}

export async function discoverModels({ refresh = false, path = cachePath() } = {}) {
  if (!refresh) {
    const cached = await readCachedModels(path);
    if (cached?.length) return { models: cached, source: "cache", cachePath: path };
  }

  const result = await execFileAsync("opencode", ["models", "--verbose"], {
    encoding: "utf8",
    maxBuffer: 32 * 1024 * 1024
  });
  const models = parseVerboseModels(`${result.stdout}\n${result.stderr}`);
  if (models.length === 0) {
    throw new Error("OpenCode returned no parseable model metadata");
  }
  await writeCache(path, models);
  return { models, source: "live", cachePath: path };
}

function appendTail(current, chunk) {
  const next = `${current}${chunk}`;
  return next.length <= MAX_CAPTURED_OUTPUT ? next : next.slice(-MAX_CAPTURED_OUTPUT);
}

function extractSessionId(output) {
  const matches = [...stripAnsi(output).matchAll(/\b(ses_[a-zA-Z0-9]+)\b/g)];
  return matches.at(-1)?.[1] ?? null;
}

async function runOnce({ directory, model, prompt }) {
  const args = [
    "run",
    "--dir", directory,
    "-m", model,
    "--print-logs",
    "--log-level", "INFO"
  ];
  args.push(prompt);

  return await new Promise((resolveResult) => {
    const child = spawn("opencode", args, { stdio: ["ignore", "pipe", "pipe"] });
    let output = "";
    let terminalUsageObserved = false;
    let settled = false;

    const forward = (target, chunk) => {
      const text = chunk.toString();
      output = appendTail(output, text);
      target.write(chunk);
      if (!terminalUsageObserved && isTerminalUsageEvent(text)) {
        terminalUsageObserved = true;
        child.kill("SIGTERM");
      }
    };

    child.stdout.on("data", (chunk) => forward(process.stdout, chunk));
    child.stderr.on("data", (chunk) => forward(process.stderr, chunk));
    child.on("error", (error) => {
      if (settled) return;
      settled = true;
      output = appendTail(output, error.message);
      resolveResult({
        model,
        exitCode: 2,
        classification: classifyOpenCodeFailure(output, 2),
        session: extractSessionId(output),
        output
      });
    });
    child.on("close", (exitCode, signal) => {
      if (settled) return;
      settled = true;
      const normalizedExit = exitCode ?? (signal ? 1 : 2);
      resolveResult({
        model,
        exitCode: normalizedExit,
        signal: signal ?? null,
        classification: terminalUsageObserved ? "usage-limit" : classifyOpenCodeFailure(output, normalizedExit),
        session: extractSessionId(output),
        output
      });
    });
  });
}

function fallbackWaitMs(attempt) {
  return Math.min(1_000 * (2 ** Math.min(Math.max(attempt - 1, 0), 6)), 60_000);
}

async function runQuotaFallback({ directory, model, prompt, attempts }) {
  let rateLimitEvents = 0;
  let transientRetries = 0;
  while (true) {
    const result = await runOnce({ directory, model, prompt });
    attempts.push(result);
    if (result.classification === "usage-limit") {
      rateLimitEvents += 1;
      const waitMs = fallbackWaitMs(rateLimitEvents);
      process.stderr.write(`OPENCODE_DELEGATION_EVENT ${JSON.stringify({
        type: "fallback-rate-limit",
        model,
        rateLimitEvents,
        waitMs
      })}\n`);
      await new Promise((resolveWait) => setTimeout(resolveWait, waitMs));
      continue;
    }
    if (result.classification === "network" && transientRetries < 3) {
      transientRetries += 1;
      const waitMs = [1_000, 2_000, 4_000][transientRetries - 1];
      process.stderr.write(`OPENCODE_DELEGATION_EVENT ${JSON.stringify({
        type: "fallback-transient-retry",
        model,
        transientRetries,
        waitMs
      })}\n`);
      await new Promise((resolveWait) => setTimeout(resolveWait, waitMs));
      continue;
    }
    return { result, rateLimitEvents, transientRetries };
  }
}

export function buildVisualReasoningPrompt(prompt, visualEvidence) {
  return `${prompt.trim()}

# Controller-Provided Visual Evidence

The controller loaded the owned \`vision-analysis\` skill and used its authorized direct API path.
Treat the following report as visual evidence. Do not claim that OpenCode or the reasoning model read the original files.
Separate facts in the report from your own inference and preserve any uncertainty.

\`\`\`json
${JSON.stringify(visualEvidence, null, 2)}
\`\`\`
`;
}

async function git(directory, args, options = {}) {
  return execFileAsync("git", args, {
    cwd: directory,
    encoding: options.encoding ?? "utf8",
    maxBuffer: 32 * 1024 * 1024
  });
}

async function resolveReviewRef(directory, reference) {
  const result = await git(directory, ["rev-parse", "--verify", `${reference}^{commit}`]);
  return result.stdout.trim();
}

async function worktreeFingerprint(directory) {
  const hash = createHash("sha256");
  const head = await git(directory, ["rev-parse", "HEAD"]);
  const status = await git(directory, ["status", "--porcelain=v1", "-z", "--untracked-files=all"]);
  const diff = await git(directory, ["diff", "--binary", "HEAD"]);
  hash.update(`HEAD\0${head.stdout.trim()}\0STATUS\0${status.stdout}\0DIFF\0${diff.stdout}\0`);

  const untracked = await git(directory, ["ls-files", "--others", "--exclude-standard", "-z"]);
  for (const relativePath of untracked.stdout.split("\0").filter(Boolean).sort()) {
    const path = resolve(directory, relativePath);
    const relation = relative(resolve(directory), path);
    if (relation === ".." || relation.startsWith(`..${sep}`)) continue;
    hash.update(`UNTRACKED\0${relativePath}\0`);
    try {
      hash.update(await readFile(path));
    } catch (error) {
      hash.update(`UNREADABLE:${error instanceof Error ? error.message : String(error)}`);
    }
  }
  return hash.digest("hex");
}

export async function prepareFrozenReview({ directory, reviewRef, reviewWorktree }) {
  if (reviewRef) {
    const commit = await resolveReviewRef(directory, reviewRef);
    const temporary = await mkdtemp(join(tmpdir(), "aimagician-opencode-review-"));
    await git(directory, ["worktree", "add", "--detach", temporary, commit]);
    const fingerprint = await worktreeFingerprint(temporary);
    return {
      kind: "commit",
      requested: reviewRef,
      commit,
      directory: temporary,
      fingerprint,
      async verify() {
        const after = await worktreeFingerprint(temporary);
        return { stable: after === fingerprint, before: fingerprint, after };
      },
      async cleanup() {
        try {
          await git(directory, ["worktree", "remove", "--force", temporary]);
        } finally {
          await rm(temporary, { recursive: true, force: true });
        }
      }
    };
  }

  const target = resolve(reviewWorktree);
  const commit = (await git(target, ["rev-parse", "HEAD"])).stdout.trim();
  const fingerprint = await worktreeFingerprint(target);
  return {
    kind: "worktree",
    requested: reviewWorktree,
    commit,
    directory: target,
    fingerprint,
    async verify() {
      const after = await worktreeFingerprint(target);
      return { stable: after === fingerprint, before: fingerprint, after };
    },
    async cleanup() {}
  };
}

function frozenReviewPrompt(prompt, review) {
  return `${prompt.trim()}

# Frozen Review Point

- Kind: ${review.kind}
- Requested review point: ${review.requested}
- Resolved commit: ${review.commit}
- Review directory: ${review.directory}
- Initial worktree fingerprint: ${review.fingerprint}

Review only this frozen directory and revision state. Do not modify files, create commits, switch revisions, or inspect a newer source checkout. Report the resolved commit and fingerprint in the final review.
`;
}

function parseArgs(argv) {
  const options = {
    files: [],
    taskType: "quick",
    modality: "text",
    refreshModels: false,
    dryRun: false,
    allowExternalUpload: false
  };

  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const value = () => {
      const next = argv[index + 1];
      if (!next || next.startsWith("--")) throw new Error(`${argument} requires a value`);
      index += 1;
      return next;
    };
    if (argument === "--dir") options.directory = value();
    else if (argument === "--task-type") options.taskType = value();
    else if (argument === "--modality") options.modality = value();
    else if (argument === "--prompt-file") options.promptFile = value();
    else if (argument === "--model") options.model = value();
    else if (argument === "--review-ref") options.reviewRef = value();
    else if (argument === "--review-worktree") options.reviewWorktree = value();
    else if (argument === "--file") options.files.push(value());
    else if (argument === "--allow-external-upload") options.allowExternalUpload = true;
    else if (argument === "--refresh-models") options.refreshModels = true;
    else if (argument === "--dry-run") options.dryRun = true;
    else if (argument === "--help" || argument === "-h") options.help = true;
    else throw new Error(`Unknown argument: ${argument}`);
  }
  return options;
}

function usage() {
  return `Usage:
  node scripts/opencode-run.mjs --dir <path> --prompt-file <path> [options]

Options:
  --task-type <quick|discovery|research|review|audit>
  --modality <text|vision>
  --model <id>              Controller choice when the default is unavailable
  --review-ref <git-ref>    Review/audit an exact commit in a temporary detached worktree
  --review-worktree <path>  Review/audit one worktree and fail if its fingerprint changes
  --file <path-or-url>      Repeat for visual inputs
  --allow-external-upload  Required for vision-analysis API calls
  --refresh-models          Refresh cached opencode models --verbose metadata
  --dry-run                 Resolve and print the route without running OpenCode
`;
}

function publicModel(model) {
  return {
    id: model.id,
    provider: model.provider,
    status: model.status,
    context: model.context,
    reasoning: model.reasoning,
    toolcall: model.toolcall,
    imageInput: model.imageInput,
    capabilitySource: model.capabilitySource
  };
}

async function main(argv) {
  const options = parseArgs(argv);
  if (options.help) {
    process.stdout.write(usage());
    return 0;
  }
  if (!options.directory || !options.promptFile) {
    throw new Error("--dir and --prompt-file are required");
  }
  if (!new Set(["text", "vision"]).has(options.modality)) {
    throw new Error("--modality must be text or vision");
  }
  if (!new Set(["quick", "discovery", "research", "review", "audit"]).has(options.taskType)) {
    throw new Error("--task-type must be quick, discovery, research, review, or audit");
  }
  if (options.modality === "vision" && options.files.length === 0) {
    throw new Error("Vision work requires at least one --file image");
  }
  if (options.modality === "vision" && !options.allowExternalUpload) {
    throw new Error("Vision work requires --allow-external-upload");
  }
  if (options.modality === "text" && options.files.length > 0) {
    throw new Error("--file is only valid with --modality vision");
  }
  if (options.reviewRef && options.reviewWorktree) {
    throw new Error("--review-ref and --review-worktree are mutually exclusive");
  }
  if (new Set(["review", "audit"]).has(options.taskType) && !options.reviewRef && !options.reviewWorktree) {
    throw new Error("Review and audit work requires --review-ref or --review-worktree");
  }
  if (!new Set(["review", "audit"]).has(options.taskType) && (options.reviewRef || options.reviewWorktree)) {
    throw new Error("--review-ref and --review-worktree are only valid for review or audit work");
  }

  const directory = resolve(options.directory);
  const prompt = await readFile(resolve(options.promptFile), "utf8");
  const inventory = await discoverModels({ refresh: options.refreshModels });
  const route = resolveModelRoute({
    models: inventory.models,
    requestedModel: options.model
  });

  const baseReport = {
    taskType: options.taskType,
    modality: options.modality,
    inventorySource: inventory.source,
    routeStatus: route.status,
    routeReason: route.reason,
    candidates: route.candidates.map(publicModel)
  };

  if (route.status !== "selected") {
    process.stdout.write(`${JSON.stringify(baseReport, null, 2)}\n`);
    return 3;
  }
  if (options.dryRun) {
    process.stdout.write(`${JSON.stringify({
      ...baseReport,
      selectedModel: route.model.id,
      visualAcquisition: options.modality === "vision"
        ? { skill: "vision-analysis", backend: "agnes", status: "planned" }
        : null,
      commandShape: options.modality === "vision"
        ? "vision-analysis -> text evidence -> opencode run --dir <path> -m <reasoning-model> --print-logs --log-level INFO <positional-prompt>"
        : "opencode run --dir <path> -m <reasoning-model> --print-logs --log-level INFO <positional-prompt>",
      frozenReview: options.reviewRef
        ? { kind: "commit", requested: options.reviewRef }
        : options.reviewWorktree
          ? { kind: "worktree", requested: resolve(options.reviewWorktree) }
          : null
    }, null, 2)}\n`);
    return 0;
  }

  let workerPrompt = prompt;
  let visualAcquisition = null;
  if (options.modality === "vision") {
    visualAcquisition = await analyzeImages({
      imageInputs: options.files,
      prompt: `Act as a visual evidence extractor for a downstream CLI agent.\n\n${prompt}`,
      allowExternalUpload: options.allowExternalUpload,
      onEvent: (event) => process.stderr.write(`VISION_ANALYSIS_EVENT ${JSON.stringify(event)}\n`)
    });
    workerPrompt = buildVisualReasoningPrompt(prompt, visualAcquisition);
  }

  const frozenReview = options.reviewRef || options.reviewWorktree
    ? await prepareFrozenReview({
      directory,
      reviewRef: options.reviewRef,
      reviewWorktree: options.reviewWorktree
    })
    : null;
  const executionDirectory = frozenReview?.directory ?? directory;
  if (frozenReview) workerPrompt = frozenReviewPrompt(workerPrompt, frozenReview);

  try {
    const attempts = [];
    const primary = await runOnce({
      directory: executionDirectory,
      model: route.model.id,
      prompt: workerPrompt
    });
    attempts.push(primary);

    let final = primary;
    let fallbackReason = null;
    let fallbackRateLimitEvents = 0;
    let fallbackTransientRetries = 0;
    const fallbackModel = process.env.AIMAGICIAN_OPENCODE_QUOTA_FALLBACK_MODEL || DEFAULT_QUOTA_FALLBACK_MODEL;
    if (primary.classification === "usage-limit" && primary.model !== fallbackModel) {
      const agnes = inventory.models.find((model) => model.id === fallbackModel && isUsableFreeModel(model));
      if (agnes) {
        fallbackReason = "explicit-usage-limit";
        const fallback = await runQuotaFallback({
          directory: executionDirectory,
          model: fallbackModel,
          prompt: workerPrompt,
          attempts
        });
        final = fallback.result;
        fallbackRateLimitEvents = fallback.rateLimitEvents;
        fallbackTransientRetries = fallback.transientRetries;
      } else {
        fallbackReason = "agnes-unavailable-after-usage-limit";
      }
    }

    if (primary.classification === "model-unavailable" && primary.model === DEFAULT_TEXT_MODEL) {
      const refreshed = await discoverModels({ refresh: true });
      const candidates = freeCandidates(refreshed.models, { exclude: [DEFAULT_TEXT_MODEL] });
      process.stderr.write(`OPENCODE_DELEGATION_RESULT ${JSON.stringify({
        ...baseReport,
        routeStatus: "selection-required",
        routeReason: `${DEFAULT_TEXT_MODEL} failed as unavailable; controller selection is required`,
        candidates: candidates.map(publicModel),
        primaryModel: primary.model,
        finalModel: primary.model,
        attemptChain: attempts.map(({ output, ...attempt }) => attempt),
        fallbackReason: null,
        frozenReview: frozenReview ? {
          kind: frozenReview.kind,
          requested: frozenReview.requested,
          commit: frozenReview.commit,
          fingerprint: frozenReview.fingerprint
        } : null
      })}\n`);
      return 3;
    }

    const frozenVerification = frozenReview ? await frozenReview.verify() : null;
    const report = {
      ...baseReport,
      primaryModel: primary.model,
      finalModel: final.model,
      attemptChain: attempts.map(({ output, ...attempt }) => attempt),
      fallbackReason,
      visualAcquisition,
      fallbackRateLimitEvents,
      fallbackTransientRetries,
      session: final.session,
      frozenReview: frozenReview ? {
        kind: frozenReview.kind,
        requested: frozenReview.requested,
        commit: frozenReview.commit,
        fingerprint: frozenReview.fingerprint,
        stable: frozenVerification.stable,
        finalFingerprint: frozenVerification.after
      } : null,
      runStatus: final.exitCode === 0 && frozenVerification?.stable !== false ? "DONE" : "BLOCKED"
    };
    process.stderr.write(`OPENCODE_DELEGATION_RESULT ${JSON.stringify(report)}\n`);
    return final.exitCode === 0 && frozenVerification?.stable !== false ? 0 : 1;
  } finally {
    if (frozenReview) await frozenReview.cleanup();
  }
}

const isEntryPoint = process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href;
if (isEntryPoint) {
  main(process.argv.slice(2))
    .then((exitCode) => {
      process.exitCode = exitCode;
    })
    .catch((error) => {
      process.stderr.write(`OPENCODE_DELEGATION_ERROR ${JSON.stringify({
        message: error instanceof Error ? error.message : String(error)
      })}\n`);
      process.exitCode = 2;
    });
}
