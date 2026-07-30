import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { afterEach, describe, expect, it } from "vitest";
import {
  DEFAULT_QUOTA_FALLBACK_MODEL,
  DEFAULT_TEXT_MODEL,
  buildVisualReasoningPrompt,
  classifyOpenCodeFailure,
  freeCandidates,
  isTerminalUsageEvent,
  parseVerboseModels,
  prepareFrozenReview,
  resolveModelRoute
} from "../../skills/owned/cli-agent-delegator/scripts/opencode-run.mjs";

const execFileAsync = promisify(execFile);
const tempDirectories: string[] = [];

afterEach(async () => {
  await Promise.allSettled(tempDirectories.splice(0).map((directory) => rm(directory, { recursive: true, force: true })));
});

const verboseModels = `
opencode/deepseek-v4-flash-free
{
  "id": "deepseek-v4-flash-free",
  "providerID": "opencode",
  "name": "DeepSeek V4 Flash Free",
  "status": "active",
  "cost": { "input": 0, "output": 0, "cache": { "read": 0, "write": 0 } },
  "limit": { "context": 200000, "output": 128000 },
  "capabilities": {
    "reasoning": true,
    "toolcall": true,
    "input": { "text": true, "image": false }
  }
}
opencode/mimo-v2.5-free
{
  "id": "mimo-v2.5-free",
  "providerID": "opencode",
  "name": "MiMo V2.5 Free",
  "status": "active",
  "cost": { "input": 0, "output": 0 },
  "limit": { "context": 200000, "output": 32000 },
  "capabilities": {
    "reasoning": true,
    "toolcall": true,
    "input": { "text": true, "image": true }
  }
}
agnes/agnes-2.0-flash
{
  "id": "agnes-2.0-flash",
  "providerID": "agnes",
  "name": "Agnes 2.0 Flash",
  "status": "active",
  "cost": { "input": 0, "output": 0 },
  "limit": { "context": 0, "output": 0 },
  "capabilities": {
    "reasoning": false,
    "toolcall": true,
    "input": { "text": true, "image": false }
  }
}
`;

describe("OpenCode dynamic model runner", () => {
  it("parses provider metadata without inventing OpenCode image capabilities", () => {
    const models = parseVerboseModels(verboseModels);
    expect(models.map((model) => model.id)).toEqual([
      DEFAULT_TEXT_MODEL,
      "opencode/mimo-v2.5-free",
      DEFAULT_QUOTA_FALLBACK_MODEL
    ]);
    expect(models.find((model) => model.id === DEFAULT_QUOTA_FALLBACK_MODEL)).toMatchObject({
      free: true,
      imageInput: false,
      capabilitySource: "provider-metadata"
    });
  });

  it("uses DeepSeek reasoning after both text and visual evidence acquisition", () => {
    const models = parseVerboseModels(verboseModels);
    expect(resolveModelRoute({ models, modality: "text" })).toMatchObject({
      status: "selected",
      model: { id: DEFAULT_TEXT_MODEL },
      reason: "default-text-model"
    });
    expect(resolveModelRoute({ models, modality: "vision" })).toMatchObject({
      status: "selected",
      model: { id: DEFAULT_TEXT_MODEL },
      reason: "default-text-model"
    });
  });

  it("returns free candidates for controller judgment when DeepSeek is absent", () => {
    const models = parseVerboseModels(verboseModels).filter((model) => model.id !== DEFAULT_TEXT_MODEL);
    const route = resolveModelRoute({ models, modality: "text" });
    expect(route).toMatchObject({ status: "selection-required" });
    expect(route.candidates.map((model) => model.id)).toEqual(["opencode/mimo-v2.5-free"]);
    expect(resolveModelRoute({
      models,
      modality: "text",
      requestedModel: "opencode/mimo-v2.5-free"
    })).toMatchObject({
      status: "selected",
      model: { id: "opencode/mimo-v2.5-free" },
      reason: "controller-selection"
    });
  });

  it("does not allow an alternate text model while DeepSeek is available", () => {
    const models = parseVerboseModels(verboseModels);
    expect(resolveModelRoute({
      models,
      modality: "text",
      requestedModel: "opencode/mimo-v2.5-free"
    })).toMatchObject({
      status: "invalid-selection",
      reason: expect.stringContaining("required reasoning default")
    });
  });

  it("classifies only explicit quota evidence as an Agnes fallback condition", () => {
    expect(classifyOpenCodeFailure("AI_APICallError: Rate limit exceeded", 1)).toBe("usage-limit");
    expect(classifyOpenCodeFailure("HTTP 429 resource_exhausted", 1)).toBe("usage-limit");
    expect(classifyOpenCodeFailure("invalid api key", 1)).toBe("authentication");
    expect(classifyOpenCodeFailure("model not found", 1)).toBe("model-unavailable");
    expect(classifyOpenCodeFailure("network error ECONNRESET", 1)).toBe("network");
    expect(classifyOpenCodeFailure("worker returned an incomplete report", 1)).toBe("worker-failure");
    expect(classifyOpenCodeFailure("ps output contains a prompt discussing usage/quota/rate-limit", 1)).toBe("worker-failure");
    expect(isTerminalUsageEvent("stream error AI_APICallError: Rate limit exceeded")).toBe(true);
    expect(isTerminalUsageEvent("the research report discusses API quota design")).toBe(false);
  });

  it("keeps free-model candidates limited to OpenCode reasoning models", () => {
    const models = parseVerboseModels(verboseModels);
    expect(freeCandidates(models, { modality: "vision" }).map((model) => model.id)).toEqual([
      DEFAULT_TEXT_MODEL,
      "opencode/mimo-v2.5-free"
    ]);
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

  it("reviews an exact commit in a disposable worktree and detects review-point drift", async () => {
    const repository = await mkdtemp(join(tmpdir(), "opencode-frozen-review-"));
    tempDirectories.push(repository);
    await execFileAsync("git", ["init"], { cwd: repository });
    await execFileAsync("git", ["config", "user.name", "Review Test"], { cwd: repository });
    await execFileAsync("git", ["config", "user.email", "review@example.invalid"], { cwd: repository });
    await writeFile(join(repository, "README.md"), "# Frozen\n", "utf8");
    await execFileAsync("git", ["add", "README.md"], { cwd: repository });
    await execFileAsync("git", ["commit", "-m", "test: frozen review"], { cwd: repository });

    const review = await prepareFrozenReview({
      directory: repository,
      reviewRef: "HEAD",
      reviewWorktree: undefined
    });
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
