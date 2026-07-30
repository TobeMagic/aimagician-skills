#!/usr/bin/env node

import { createHash } from "node:crypto";
import { readFile, stat } from "node:fs/promises";
import { basename, resolve } from "node:path";
import { pathToFileURL } from "node:url";

export const DEFAULT_AGNES_BASE_URL = "https://apihub.agnes-ai.com/v1";
export const DEFAULT_AGNES_VISION_MODEL = "agnes-2.0-flash";
export const DEFAULT_REQUEST_TIMEOUT_MS = 120_000;
export const DEFAULT_MAX_IMAGE_BYTES = 20 * 1024 * 1024;
export const DEFAULT_MAX_IMAGES = 8;

const TRANSIENT_DELAYS_MS = [1_000, 2_000, 4_000];
const MAX_RATE_LIMIT_DELAY_MS = 60_000;

export class VisionAnalysisError extends Error {
  constructor(code, message, { exitCode = 1, cause } = {}) {
    super(message, { cause });
    this.name = "VisionAnalysisError";
    this.code = code;
    this.exitCode = exitCode;
  }
}

function sha256(value) {
  return createHash("sha256").update(value).digest("hex");
}

function redact(value, apiKey = "") {
  let result = String(value ?? "");
  if (apiKey) result = result.replaceAll(apiKey, "[REDACTED]");
  result = result.replace(/Bearer\s+[A-Za-z0-9._~+/-]+/gi, "Bearer [REDACTED]");
  return result.slice(0, 1_000);
}

function detectMime(buffer) {
  if (buffer.length >= 8 && buffer.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))) {
    return "image/png";
  }
  if (buffer.length >= 3 && buffer[0] === 0xff && buffer[1] === 0xd8 && buffer[2] === 0xff) {
    return "image/jpeg";
  }
  if (buffer.length >= 6 && new Set(["GIF87a", "GIF89a"]).has(buffer.subarray(0, 6).toString("ascii"))) {
    return "image/gif";
  }
  if (
    buffer.length >= 12
    && buffer.subarray(0, 4).toString("ascii") === "RIFF"
    && buffer.subarray(8, 12).toString("ascii") === "WEBP"
  ) {
    return "image/webp";
  }
  return null;
}

function isObviousPrivateHost(hostname) {
  const host = hostname.toLowerCase().replace(/^\[|\]$/g, "");
  if (host === "localhost" || host === "::1" || host.endsWith(".local")) return true;
  if (/^127\./.test(host) || /^10\./.test(host) || /^192\.168\./.test(host) || /^169\.254\./.test(host)) return true;
  const match = host.match(/^172\.(\d+)\./);
  if (match && Number(match[1]) >= 16 && Number(match[1]) <= 31) return true;
  return /^(?:fc|fd|fe8|fe9|fea|feb)[0-9a-f:]*$/i.test(host);
}

export function sanitizeRemoteUrl(value) {
  let url;
  try {
    url = new URL(value);
  } catch {
    throw new VisionAnalysisError("INPUT_URL_INVALID", "Image URL is invalid", { exitCode: 2 });
  }
  if (url.protocol !== "https:") {
    throw new VisionAnalysisError("INPUT_URL_PROTOCOL", "Remote images require HTTPS", { exitCode: 2 });
  }
  if (url.username || url.password) {
    throw new VisionAnalysisError("INPUT_URL_CREDENTIALS", "Remote image URLs must not contain credentials", { exitCode: 2 });
  }
  if (isObviousPrivateHost(url.hostname)) {
    throw new VisionAnalysisError("INPUT_URL_PRIVATE", "Remote image URL points to a local or private host", { exitCode: 2 });
  }
  return {
    requestUrl: url.toString(),
    display: `${url.origin}${url.pathname}`,
    digest: sha256(`${url.origin}${url.pathname}`)
  };
}

export async function loadImageInput(value, { maxBytes = DEFAULT_MAX_IMAGE_BYTES } = {}) {
  if (/^https:/i.test(value)) {
    const remote = sanitizeRemoteUrl(value);
    return {
      requestPart: { type: "image_url", image_url: { url: remote.requestUrl } },
      metadata: {
        kind: "https",
        name: remote.display,
        mime: null,
        bytes: null,
        sha256: remote.digest
      }
    };
  }

  const path = resolve(value);
  let info;
  try {
    info = await stat(path);
  } catch (error) {
    throw new VisionAnalysisError("INPUT_FILE_UNREADABLE", `Image file is not readable: ${basename(path)}`, {
      exitCode: 2,
      cause: error
    });
  }
  if (!info.isFile()) {
    throw new VisionAnalysisError("INPUT_FILE_INVALID", `Image input is not a file: ${basename(path)}`, { exitCode: 2 });
  }
  if (info.size > maxBytes) {
    throw new VisionAnalysisError(
      "INPUT_FILE_TOO_LARGE",
      `Image exceeds the ${maxBytes} byte limit: ${basename(path)}`,
      { exitCode: 2 }
    );
  }
  const buffer = await readFile(path);
  const mime = detectMime(buffer);
  if (!mime) {
    throw new VisionAnalysisError(
      "INPUT_MIME_UNSUPPORTED",
      `Supported image formats are PNG, JPEG, WebP, and GIF: ${basename(path)}`,
      { exitCode: 2 }
    );
  }
  return {
    requestPart: {
      type: "image_url",
      image_url: { url: `data:${mime};base64,${buffer.toString("base64")}` }
    },
    metadata: {
      kind: "local",
      name: basename(path),
      mime,
      bytes: buffer.length,
      sha256: sha256(buffer)
    }
  };
}

export function buildPayload({ prompt, model, imageParts }) {
  return {
    model,
    messages: [
      {
        role: "user",
        content: [
          { type: "text", text: prompt },
          ...imageParts
        ]
      }
    ]
  };
}

function parseRetryAfter(value, now = Date.now()) {
  if (!value) return null;
  const seconds = Number(value);
  if (Number.isFinite(seconds) && seconds >= 0) return Math.ceil(seconds * 1_000);
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) ? Math.max(0, timestamp - now) : null;
}

function rateLimitDelay(rateLimitEvents, retryAfter) {
  return Math.min(
    retryAfter ?? 1_000 * (2 ** Math.min(Math.max(rateLimitEvents - 1, 0), 6)),
    MAX_RATE_LIMIT_DELAY_MS
  );
}

export function sleepWithSignal(milliseconds, signal) {
  if (signal?.aborted) {
    return Promise.reject(new VisionAnalysisError("CANCELLED", "Vision analysis was cancelled", { exitCode: 130 }));
  }
  return new Promise((resolveSleep, rejectSleep) => {
    const timer = setTimeout(() => {
      signal?.removeEventListener("abort", onAbort);
      resolveSleep();
    }, milliseconds);
    const onAbort = () => {
      clearTimeout(timer);
      signal?.removeEventListener("abort", onAbort);
      rejectSleep(new VisionAnalysisError("CANCELLED", "Vision analysis was cancelled", { exitCode: 130 }));
    };
    signal?.addEventListener("abort", onAbort, { once: true });
  });
}

async function fetchWithTimeout(fetchImpl, url, init, timeoutMs, outerSignal) {
  const controller = new AbortController();
  let timedOut = false;
  const onAbort = () => controller.abort(outerSignal?.reason);
  if (outerSignal?.aborted) onAbort();
  else outerSignal?.addEventListener("abort", onAbort, { once: true });
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort(new Error("request timeout"));
  }, timeoutMs);
  timer.unref?.();
  try {
    return await fetchImpl(url, { ...init, signal: controller.signal });
  } catch (error) {
    if (outerSignal?.aborted) {
      throw new VisionAnalysisError("CANCELLED", "Vision analysis was cancelled", { exitCode: 130, cause: error });
    }
    if (timedOut) {
      throw new VisionAnalysisError("REQUEST_TIMEOUT", `Agnes request exceeded ${timeoutMs}ms`, { cause: error });
    }
    throw error;
  } finally {
    clearTimeout(timer);
    outerSignal?.removeEventListener("abort", onAbort);
  }
}

async function responseBody(response) {
  try {
    return await response.text();
  } catch {
    return "";
  }
}

function extractAnalysis(payload) {
  const content = payload?.choices?.[0]?.message?.content;
  if (typeof content === "string" && content.trim()) return content.trim();
  if (Array.isArray(content)) {
    const text = content
      .map((item) => typeof item === "string" ? item : item?.text)
      .filter((item) => typeof item === "string" && item.trim())
      .join("\n")
      .trim();
    if (text) return text;
  }
  throw new VisionAnalysisError("RESPONSE_INVALID", "Agnes returned no usable analysis text");
}

export async function requestAnalysis({
  endpoint,
  apiKey,
  payload,
  fetchImpl = globalThis.fetch,
  sleep = sleepWithSignal,
  signal,
  timeoutMs = DEFAULT_REQUEST_TIMEOUT_MS,
  onEvent = () => {}
}) {
  let attempts = 0;
  let rateLimitEvents = 0;
  let transientRetries = 0;

  while (true) {
    if (signal?.aborted) {
      throw new VisionAnalysisError("CANCELLED", "Vision analysis was cancelled", { exitCode: 130 });
    }
    attempts += 1;
    let response;
    try {
      response = await fetchWithTimeout(fetchImpl, endpoint, {
        method: "POST",
        headers: {
          authorization: `Bearer ${apiKey}`,
          "content-type": "application/json"
        },
        body: JSON.stringify(payload)
      }, timeoutMs, signal);
    } catch (error) {
      if (error instanceof VisionAnalysisError && error.code === "CANCELLED") throw error;
      if (transientRetries >= TRANSIENT_DELAYS_MS.length) {
        throw new VisionAnalysisError(
          error instanceof VisionAnalysisError ? error.code : "NETWORK_FAILURE",
          redact(error instanceof Error ? error.message : error, apiKey),
          { cause: error }
        );
      }
      const waitMs = TRANSIENT_DELAYS_MS[transientRetries];
      transientRetries += 1;
      onEvent({ type: "transient-retry", attempt: attempts, retry: transientRetries, waitMs });
      await sleep(waitMs, signal);
      continue;
    }

    if (response.status === 429) {
      await responseBody(response);
      rateLimitEvents += 1;
      const waitMs = rateLimitDelay(rateLimitEvents, parseRetryAfter(response.headers.get("retry-after")));
      onEvent({ type: "rate-limit", attempt: attempts, rateLimitEvents, waitMs });
      await sleep(waitMs, signal);
      continue;
    }

    if (response.status === 408 || response.status >= 500) {
      const body = await responseBody(response);
      if (transientRetries >= TRANSIENT_DELAYS_MS.length) {
        throw new VisionAnalysisError(
          "HTTP_TRANSIENT_EXHAUSTED",
          `Agnes HTTP ${response.status} after transient retries: ${redact(body, apiKey)}`
        );
      }
      const waitMs = TRANSIENT_DELAYS_MS[transientRetries];
      transientRetries += 1;
      onEvent({
        type: "transient-retry",
        attempt: attempts,
        retry: transientRetries,
        status: response.status,
        waitMs
      });
      await sleep(waitMs, signal);
      continue;
    }

    if (!response.ok) {
      const body = await responseBody(response);
      throw new VisionAnalysisError(
        "HTTP_NON_RETRIABLE",
        `Agnes HTTP ${response.status}: ${redact(body, apiKey)}`
      );
    }

    const body = await responseBody(response);
    let parsed;
    try {
      parsed = JSON.parse(body);
    } catch (error) {
      throw new VisionAnalysisError("RESPONSE_JSON_INVALID", "Agnes returned invalid JSON", { cause: error });
    }
    return {
      analysis: extractAnalysis(parsed),
      usage: parsed.usage ?? null,
      attempts: { total: attempts, rateLimitEvents, transientRetries }
    };
  }
}

export async function analyzeImages({
  imageInputs,
  prompt,
  allowExternalUpload,
  apiKey = process.env.AGNES_API_KEY,
  baseUrl = process.env.AGNES_API_BASE_URL || DEFAULT_AGNES_BASE_URL,
  model = process.env.AGNES_VISION_MODEL || DEFAULT_AGNES_VISION_MODEL,
  timeoutMs = Number(process.env.AGNES_REQUEST_TIMEOUT_MS || DEFAULT_REQUEST_TIMEOUT_MS),
  maxBytes = DEFAULT_MAX_IMAGE_BYTES,
  maxImages = DEFAULT_MAX_IMAGES,
  fetchImpl,
  sleep,
  signal,
  onEvent
}) {
  if (!allowExternalUpload) {
    throw new VisionAnalysisError(
      "UPLOAD_AUTHORIZATION_REQUIRED",
      "External image analysis requires --allow-external-upload",
      { exitCode: 2 }
    );
  }
  if (!apiKey) {
    throw new VisionAnalysisError("AGNES_API_KEY_MISSING", "AGNES_API_KEY is required", { exitCode: 2 });
  }
  if (!prompt?.trim()) {
    throw new VisionAnalysisError("PROMPT_REQUIRED", "A non-empty prompt is required", { exitCode: 2 });
  }
  if (!Array.isArray(imageInputs) || imageInputs.length === 0) {
    throw new VisionAnalysisError("IMAGE_REQUIRED", "At least one --image is required", { exitCode: 2 });
  }
  if (imageInputs.length > maxImages) {
    throw new VisionAnalysisError("IMAGE_LIMIT", `At most ${maxImages} images are allowed`, { exitCode: 2 });
  }
  if (!Number.isFinite(timeoutMs) || timeoutMs <= 0) {
    throw new VisionAnalysisError("TIMEOUT_INVALID", "AGNES_REQUEST_TIMEOUT_MS must be positive", { exitCode: 2 });
  }

  let endpoint;
  try {
    endpoint = new URL("chat/completions", `${baseUrl.replace(/\/+$/, "")}/`);
  } catch {
    throw new VisionAnalysisError("BASE_URL_INVALID", "AGNES_API_BASE_URL is invalid", { exitCode: 2 });
  }
  if (endpoint.protocol !== "https:") {
    throw new VisionAnalysisError("BASE_URL_PROTOCOL", "AGNES_API_BASE_URL requires HTTPS", { exitCode: 2 });
  }

  const loaded = await Promise.all(imageInputs.map((input) => loadImageInput(input, { maxBytes })));
  const payload = buildPayload({
    prompt: prompt.trim(),
    model,
    imageParts: loaded.map((item) => item.requestPart)
  });
  const result = await requestAnalysis({
    endpoint,
    apiKey,
    payload,
    fetchImpl,
    sleep,
    signal,
    timeoutMs,
    onEvent
  });
  return {
    status: "success",
    provider: "agnes",
    model,
    endpoint: endpoint.origin,
    inputs: loaded.map((item) => item.metadata),
    attempts: result.attempts,
    analysis: result.analysis,
    usage: result.usage
  };
}

export function parseArgs(argv) {
  const options = { images: [], json: false, allowExternalUpload: false };
  for (let index = 0; index < argv.length; index += 1) {
    const argument = argv[index];
    const value = () => {
      const next = argv[index + 1];
      if (!next || next.startsWith("--")) {
        throw new VisionAnalysisError("ARGUMENT_VALUE_REQUIRED", `${argument} requires a value`, { exitCode: 2 });
      }
      index += 1;
      return next;
    };
    if (argument === "--image") options.images.push(value());
    else if (argument === "--prompt") options.prompt = value();
    else if (argument === "--prompt-file") options.promptFile = value();
    else if (argument === "--model") options.model = value();
    else if (argument === "--base-url") options.baseUrl = value();
    else if (argument === "--allow-external-upload") options.allowExternalUpload = true;
    else if (argument === "--json") options.json = true;
    else if (argument === "--help" || argument === "-h") options.help = true;
    else throw new VisionAnalysisError("ARGUMENT_UNKNOWN", `Unknown argument: ${argument}`, { exitCode: 2 });
  }
  if (options.prompt && options.promptFile) {
    throw new VisionAnalysisError("PROMPT_CONFLICT", "Use either --prompt or --prompt-file", { exitCode: 2 });
  }
  return options;
}

function usage() {
  return `Usage:
  node scripts/analyze.mjs --image <path-or-https-url> [--image <value> ...]
    (--prompt <text> | --prompt-file <path>) --allow-external-upload [--json]

Options:
  --model <id>                 Override AGNES_VISION_MODEL
  --base-url <https-url>       Override AGNES_API_BASE_URL
  --allow-external-upload      Required consent for every image invocation
  --json                       Emit structured JSON
`;
}

async function main(argv) {
  const options = parseArgs(argv);
  if (options.help) {
    process.stdout.write(usage());
    return 0;
  }
  const prompt = options.promptFile
    ? await readFile(resolve(options.promptFile), "utf8")
    : options.prompt;
  const controller = new AbortController();
  const cancel = () => controller.abort();
  process.once("SIGINT", cancel);
  process.once("SIGTERM", cancel);
  try {
    const result = await analyzeImages({
      imageInputs: options.images,
      prompt,
      allowExternalUpload: options.allowExternalUpload,
      model: options.model,
      baseUrl: options.baseUrl,
      signal: controller.signal,
      onEvent: (event) => process.stderr.write(`VISION_ANALYSIS_EVENT ${JSON.stringify(event)}\n`)
    });
    process.stdout.write(options.json ? `${JSON.stringify(result, null, 2)}\n` : `${result.analysis}\n`);
    return 0;
  } finally {
    process.removeListener("SIGINT", cancel);
    process.removeListener("SIGTERM", cancel);
  }
}

const isEntryPoint = process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href;
if (isEntryPoint) {
  main(process.argv.slice(2))
    .then((exitCode) => {
      process.exitCode = exitCode;
    })
    .catch((error) => {
      const normalized = error instanceof VisionAnalysisError
        ? error
        : new VisionAnalysisError("UNEXPECTED", error instanceof Error ? error.message : String(error), { cause: error });
      process.stderr.write(`VISION_ANALYSIS_ERROR ${JSON.stringify({
        code: normalized.code,
        message: redact(normalized.message)
      })}\n`);
      process.exitCode = normalized.exitCode;
    });
}
