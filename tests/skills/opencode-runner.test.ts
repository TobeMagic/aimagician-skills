import { describe, expect, it } from "vitest";
import {
  DEFAULT_TEXT_MODEL,
  DEFAULT_VISION_MODEL,
  classifyOpenCodeFailure,
  freeCandidates,
  isTerminalUsageEvent,
  parseVerboseModels,
  resolveModelRoute
} from "../../skills/owned/cli-agent-delegator/scripts/opencode-run.mjs";

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
  it("parses verbose metadata and applies the verified Agnes vision override", () => {
    const models = parseVerboseModels(verboseModels);
    expect(models.map((model) => model.id)).toEqual([
      DEFAULT_TEXT_MODEL,
      "opencode/mimo-v2.5-free",
      DEFAULT_VISION_MODEL
    ]);
    expect(models.find((model) => model.id === DEFAULT_VISION_MODEL)).toMatchObject({
      free: true,
      imageInput: true,
      capabilitySource: "verified-override"
    });
  });

  it("uses DeepSeek for text and Agnes for vision", () => {
    const models = parseVerboseModels(verboseModels);
    expect(resolveModelRoute({ models, modality: "text" })).toMatchObject({
      status: "selected",
      model: { id: DEFAULT_TEXT_MODEL },
      reason: "default-text-model"
    });
    expect(resolveModelRoute({ models, modality: "vision" })).toMatchObject({
      status: "selected",
      model: { id: DEFAULT_VISION_MODEL },
      reason: "default-vision-model"
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
      reason: expect.stringContaining("required non-visual default")
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

  it("filters visual candidates from capabilities rather than model names", () => {
    const models = parseVerboseModels(verboseModels);
    expect(freeCandidates(models, { modality: "vision" }).map((model) => model.id)).toEqual([
      DEFAULT_VISION_MODEL,
      "opencode/mimo-v2.5-free"
    ]);
  });
});
