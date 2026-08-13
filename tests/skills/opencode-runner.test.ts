import { execFile, spawn } from "node:child_process";
import { chmod, mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { once } from "node:events";
import { afterEach, describe, expect, it } from "vitest";
import {
  DEFAULT_QUOTA_FALLBACK_MODEL,
  buildModelChain,
  buildVisualReasoningPrompt,
  classifyOpenCodeFailure,
  createCancellationController,
  freeCandidates,
  isTerminalUsageEvent,
  parseVerboseModels,
  prepareFrozenReview,
  quotaPolicyForModel,
  resolveModelRoute,
  runModelChain
} from "../../skills/owned/cli-agent-delegator/scripts/opencode-run.mjs";

const execFileAsync = promisify(execFile);
const tempDirectories: string[] = [];
const DEEPSEEK = "opencode/deepseek-v4-flash-free";
const OTHER_PROVIDER = "sub2api_anthropic/claude-opus-free";

afterEach(async () => {
  await Promise.allSettled(tempDirectories.splice(0).map((directory) => rm(directory, { recursive: true, force: true })));
});

const verboseModels = `
opencode/deepseek-v4-flash-free
{"id":"deepseek-v4-flash-free","providerID":"opencode","name":"DeepSeek V4 Flash Free","status":"active","cost":{"input":0,"output":0},"limit":{"context":200000,"output":128000},"capabilities":{"reasoning":true,"toolcall":true,"input":{"text":true,"image":false}}}
opencode/mimo-v2.5-free
{"id":"mimo-v2.5-free","providerID":"opencode","name":"MiMo V2.5 Free","status":"active","cost":{"input":0,"output":0},"limit":{"context":200000,"output":32000},"capabilities":{"reasoning":true,"toolcall":true,"input":{"text":true,"image":true}}}
sub2api_anthropic/claude-opus-free
{"id":"claude-opus-free","providerID":"sub2api_anthropic","name":"Claude Opus Free","status":"active","cost":{"input":0,"output":0},"limit":{"context":200000,"output":64000},"capabilities":{"reasoning":true,"toolcall":true,"input":{"text":true,"image":false}}}
catalog/text-only-free
{"id":"text-only-free","providerID":"catalog","name":"Catalog Text Only","status":"active","cost":{"input":0,"output":0},"limit":{"context":100000,"output":16000},"capabilities":{"reasoning":true,"toolcall":false,"input":{"text":true,"image":false}}}
agnes/agnes-2.0-flash
{"id":"agnes-2.0-flash","providerID":"agnes","name":"Agnes 2.0 Flash","status":"active","cost":{"input":0,"output":0},"limit":{"context":0,"output":0},"capabilities":{"reasoning":false,"toolcall":true,"input":{"text":true,"image":false}}}
`;

describe("OpenCode dynamic model runner", () => {
  it("parses provider metadata and exposes free models across providers", () => {
    const models = parseVerboseModels(verboseModels);
    expect(models.map((model) => model.id)).toEqual([
      DEEPSEEK,
      "opencode/mimo-v2.5-free",
      OTHER_PROVIDER,
      "catalog/text-only-free",
      DEFAULT_QUOTA_FALLBACK_MODEL
    ]);
    expect(models.find((model) => model.id === DEFAULT_QUOTA_FALLBACK_MODEL)).toMatchObject({
      free: true,
      imageInput: false,
      capabilitySource: "provider-metadata"
    });
  });

  it("requires an explicit controller selection and accepts any eligible free worker", () => {
    const models = parseVerboseModels(verboseModels);
    expect(resolveModelRoute({ models })).toMatchObject({ status: "selection-required" });
    expect(resolveModelRoute({ models, requestedModel: OTHER_PROVIDER })).toMatchObject({
      status: "selected",
      model: { id: OTHER_PROVIDER },
      reason: "controller-selection"
    });
    expect(resolveModelRoute({ models, requestedModel: "catalog/text-only-free" })).toMatchObject({
      status: "invalid-selection"
    });
  });

  it("builds the declared chain, appends Agnes once, and records quota-policy provenance", () => {
    const models = parseVerboseModels(verboseModels);
    const route = buildModelChain({
      models,
      primaryModel: OTHER_PROVIDER,
      fallbackModels: [DEEPSEEK, "opencode/mimo-v2.5-free"]
    });
    expect(route).toMatchObject({
      status: "selected",
      declaredChain: [OTHER_PROVIDER, DEEPSEEK, "opencode/mimo-v2.5-free"],
      effectiveChain: [OTHER_PROVIDER, DEEPSEEK, "opencode/mimo-v2.5-free", DEFAULT_QUOTA_FALLBACK_MODEL]
    });
    expect(route.chain?.map((model) => [model.id, model.quotaScope])).toEqual([
      [OTHER_PROVIDER, `model:${OTHER_PROVIDER}`],
      [DEEPSEEK, "shared:opencode"],
      ["opencode/mimo-v2.5-free", "shared:opencode"],
      [DEFAULT_QUOTA_FALLBACK_MODEL, "unlimited:agnes"]
    ]);
    expect(quotaPolicyForModel(route.chain![0])).toMatchObject({
      quotaScopeSource: "user-policy-v1",
      quotaScopeConfidence: "user-asserted"
    });
  });

  it("rejects duplicate models and Agnes before the final declared position", () => {
    const models = parseVerboseModels(verboseModels);
    expect(buildModelChain({ models, primaryModel: DEEPSEEK, fallbackModels: [DEEPSEEK] })).toMatchObject({
      status: "invalid-chain",
      reason: expect.stringContaining("unique")
    });
    expect(buildModelChain({
      models,
      primaryModel: DEEPSEEK,
      fallbackModels: [DEFAULT_QUOTA_FALLBACK_MODEL, OTHER_PROVIDER]
    })).toMatchObject({ status: "invalid-chain", reason: expect.stringContaining("only as the final model") });
  });

  it("classifies transition failures without treating ordinary prose as quota evidence", () => {
    expect(classifyOpenCodeFailure("AI_APICallError: Rate limit exceeded", 1)).toBe("usage-limit");
    expect(classifyOpenCodeFailure("HTTP 429 resource_exhausted", 1)).toBe("usage-limit");
    expect(classifyOpenCodeFailure("invalid api key", 1)).toBe("authentication");
    expect(classifyOpenCodeFailure("model not found", 1)).toBe("model-unavailable");
    expect(classifyOpenCodeFailure("network error ECONNRESET", 1)).toBe("network");
    expect(classifyOpenCodeFailure("worker returned an incomplete report", 1)).toBe("worker-failure");
    expect(isTerminalUsageEvent("stream error AI_APICallError: Rate limit exceeded")).toBe(true);
    expect(isTerminalUsageEvent("timestamp=2026-08-03T00:00:00Z level=ERROR message=provider_error status=429 rate limit exceeded")).toBe(true);
    expect(isTerminalUsageEvent('{"type":"error","code":429,"message":"quota exhausted"}')).toBe(true);
    expect(isTerminalUsageEvent("the research report discusses API quota design")).toBe(false);
    expect(isTerminalUsageEvent("return /(?:stream error|AI_APICallError)[\\s\\S]{0,400}(?:rate limit|quota)/i.test(value);")).toBe(false);
    expect(isTerminalUsageEvent("- AI_APICallError and HTTP 429 are examples of quota failures")).toBe(false);
    expect(isTerminalUsageEvent("AI_APICallError: Rate limit exceeded")).toBe(false);
    expect(isTerminalUsageEvent("AI_APICallError+rate: usage-limit")).toBe(false);
  });

  it("distinguishes discoverable free models from tool-capable workers", () => {
    const models = parseVerboseModels(verboseModels);
    expect(freeCandidates(models).map((model) => model.id)).toEqual([
      DEFAULT_QUOTA_FALLBACK_MODEL,
      DEEPSEEK,
      "opencode/mimo-v2.5-free",
      OTHER_PROVIDER
    ]);
    expect(freeCandidates(models, { requireTools: false }).map((model) => model.id)).toContain("catalog/text-only-free");
  });

  it("runs list mode and skips a quota-invalidated Zen sibling before another provider", async () => {
    const fixture = await makeFakeOpenCode();
    const list = await execFileAsync(process.execPath, [fixture.runner, "--list-models", "--format", "json", "--refresh-models"], {
      env: fixture.env,
      maxBuffer: 8 * 1024 * 1024
    });
    const listed = JSON.parse(list.stdout) as { schemaVersion: number; models: Array<{ id: string; workerEligible: boolean }> };
    expect(listed.schemaVersion).toBe(2);
    expect(listed.models.find((model) => model.id === "catalog/text-only-free")).toMatchObject({ workerEligible: false });

    const promptFile = join(fixture.root, "prompt.txt");
    await writeFile(promptFile, "Return a bounded test report.", "utf8");
    const run = await execFileAsync(process.execPath, [
      fixture.runner,
      "--dir", fixture.root,
      "--prompt-file", promptFile,
      "--model", DEEPSEEK,
      "--fallback-model", "opencode/mimo-v2.5-free",
      "--fallback-model", OTHER_PROVIDER
    ], { env: fixture.env, maxBuffer: 8 * 1024 * 1024 });
    const resultLine = run.stderr.split("\n").find((line) => line.startsWith("OPENCODE_DELEGATION_RESULT "));
    expect(resultLine).toBeDefined();
    const result = JSON.parse(resultLine!.slice("OPENCODE_DELEGATION_RESULT ".length));
    expect(result).toMatchObject({
      runStatus: "DONE",
      primaryModel: DEEPSEEK,
      finalModel: OTHER_PROVIDER,
      invalidatedQuotaScopes: ["shared:opencode"]
    });
    expect(result.transitions).toEqual(expect.arrayContaining([
      expect.objectContaining({ type: "quota-scope-invalidated", model: DEEPSEEK }),
      expect.objectContaining({ type: "skipped-invalidated", model: "opencode/mimo-v2.5-free" })
    ]));
  });

  it("labels visual evidence as controller-provided rather than an OpenCode attachment", () => {
    const prompt = buildVisualReasoningPrompt("Review the screenshot.", {
      provider: "agnes",
      model: "agnes-2.0-flash",
      analysis: "A blue button is clipped."
    });
    expect(prompt).toContain("Controller-Provided Visual Evidence");
    expect(prompt).toContain("Do not claim that OpenCode or the reasoning model read the original files");
    expect(prompt).toContain('"analysis": "A blue button is clipped."');
  });

  it("does not start a fallback chain after controller cancellation", async () => {
    const models = parseVerboseModels(verboseModels);
    const route = buildModelChain({ models, primaryModel: DEEPSEEK, fallbackModels: [OTHER_PROVIDER] });
    const cancellation = createCancellationController();
    cancellation.request("test-cancel");

    const result = await runModelChain({
      directory: process.cwd(),
      chain: route.chain!,
      prompt: "This must not launch a worker.",
      cancellation
    });

    expect(result.cancelled).toBe(true);
    expect(result.attempts).toEqual([]);
    expect(result.transitions).toEqual([]);
  });

  it("propagates a controller signal to the worker and reports cancellation without fallback", async () => {
    const fixture = await makeFakeOpenCode();
    const promptFile = join(fixture.root, "cancel-prompt.txt");
    await writeFile(promptFile, "Wait for cancellation.", "utf8");
    const child = spawn(process.execPath, [
      fixture.runner,
      "--dir", fixture.root,
      "--prompt-file", promptFile,
      "--model", DEEPSEEK,
      "--fallback-model", OTHER_PROVIDER
    ], {
      env: { ...fixture.env, SLOW_RUN: "1" },
      stdio: ["ignore", "pipe", "pipe"]
    });
    let stderr = "";
    let stdout = "";
    let resolveWorkerStarted: (() => void) | undefined;
    const workerStarted = new Promise<void>((resolve) => {
      resolveWorkerStarted = resolve;
    });
    child.stdout.on("data", (chunk) => {
      stdout += chunk.toString();
      if (stdout.includes("ses_fake_waiting")) resolveWorkerStarted?.();
    });
    child.stderr.on("data", (chunk) => {
      stderr += chunk.toString();
    });
    await workerStarted;
    child.kill("SIGTERM");
    const [exitCode] = await once(child, "close") as [number | null, NodeJS.Signals | null];

    expect(exitCode).toBe(130);
    const resultLine = stderr.split("\n").find((line) => line.startsWith("OPENCODE_DELEGATION_RESULT "));
    expect(resultLine).toBeDefined();
    const result = JSON.parse(resultLine!.slice("OPENCODE_DELEGATION_RESULT ".length));
    expect(result).toMatchObject({ runStatus: "CANCELLED", finalModel: DEEPSEEK });
    expect(result.attemptChain).toHaveLength(1);
    expect(result.attemptChain[0]).toMatchObject({ classification: "cancelled" });
  });

  it("reviews an exact commit in a disposable worktree and detects review-point drift", async () => {
    const repository = await mkdtemp(join(tmpdir(), "opencode-frozen-review-"));
    tempDirectories.push(repository);
    await execFileAsync("git", ["init"], { cwd: repository });
    await execFileAsync("git", ["config", "user.name", "Review Test"], { cwd: repository });
    await execFileAsync("git", ["config", "user.email", "review@example.invalid"], { cwd: repository });
    await writeFile(join(repository, "README.md"), "# Frozen\n", "utf8");
    await execFileAsync("git", ["add", "README.md"], { cwd: repository });
    await execFileAsync("git", ["commit", "-m", "test: frozen review"], { cwd: repository });

    const review = await prepareFrozenReview({ directory: repository, reviewRef: "HEAD", reviewWorktree: undefined });
    expect(review.kind).toBe("commit");
    expect(review.commit).toMatch(/^[0-9a-f]{40}$/);
    expect((await review.verify()).stable).toBe(true);
    await writeFile(join(review.directory, "README.md"), "# Mutated during review\n", "utf8");
    expect((await review.verify()).stable).toBe(false);
    const temporary = review.directory;
    await review.cleanup();
    const worktrees = await execFileAsync("git", ["worktree", "list", "--porcelain"], { cwd: repository });
    expect(worktrees.stdout).not.toContain(temporary);
  });
});

async function makeFakeOpenCode() {
  const root = await mkdtemp(join(tmpdir(), "opencode-runner-cli-"));
  tempDirectories.push(root);
  const bin = join(root, "bin");
  await mkdir(bin);
  const executable = join(bin, "opencode");
  await writeFile(executable, `#!/usr/bin/env node
const args = process.argv.slice(2);
if (args[0] === "models") { process.stdout.write(${JSON.stringify(verboseModels)}); process.exit(0); }
if (args[0] === "run") {
  const model = args[args.indexOf("-m") + 1];
  if (process.env.SLOW_RUN === "1") { process.stdout.write("session ses_fake_waiting\\n"); setInterval(() => {}, 1_000); }
  else if (model === ${JSON.stringify(DEEPSEEK)}) { process.stderr.write("stream error AI_APICallError: HTTP 429 rate limit exceeded\\n"); process.exit(1); }
  else { process.stdout.write("session ses_fake_success\\nDONE " + model + "\\n"); process.exit(0); }
}
process.exit(2);
`, "utf8");
  await chmod(executable, 0o755);
  return {
    root,
    runner: join(process.cwd(), "skills", "owned", "cli-agent-delegator", "scripts", "opencode-run.mjs"),
    env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, XDG_CACHE_HOME: join(root, "cache") }
  };
}
