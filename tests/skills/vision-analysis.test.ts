import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  VisionAnalysisError,
  analyzeImages,
  buildPayload,
  requestAnalysis,
  sanitizeRemoteUrl,
  sleepWithSignal
} from "../../skills/owned/vision-analysis/scripts/analyze.mjs";

const tempDirectories: string[] = [];

afterEach(async () => {
  await Promise.allSettled(tempDirectories.splice(0).map((path) => rm(path, { recursive: true, force: true })));
});

describe("vision-analysis", () => {
  it("requires explicit upload authorization before reading images or calling Agnes", async () => {
    const fetchImpl = vi.fn();
    await expect(analyzeImages({
      imageInputs: ["missing.png"],
      prompt: "Inspect the image",
      apiKey: "secret-test-key",
      allowExternalUpload: false,
      fetchImpl
    })).rejects.toMatchObject({
      code: "UPLOAD_AUTHORIZATION_REQUIRED",
      exitCode: 2
    });
    expect(fetchImpl).not.toHaveBeenCalled();
  });

  it("encodes a local PNG in memory and returns sanitized provenance", async () => {
    const directory = await mkdtemp(join(tmpdir(), "vision-analysis-"));
    tempDirectories.push(directory);
    const imagePath = join(directory, "private-screen.png");
    const image = Buffer.concat([
      Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]),
      Buffer.from("safe-test-image")
    ]);
    await writeFile(imagePath, image);

    const fetchImpl = vi.fn(async (_url: URL, init: RequestInit) => {
      const body = JSON.parse(String(init.body));
      expect(init.headers).toMatchObject({ authorization: "Bearer secret-test-key" });
      expect(body.messages[0].content[1].image_url.url).toMatch(/^data:image\/png;base64,/);
      return jsonResponse({
        choices: [{ message: { content: "The image contains a test marker." } }],
        usage: { prompt_tokens: 10, completion_tokens: 8 }
      });
    });

    const result = await analyzeImages({
      imageInputs: [imagePath],
      prompt: "Describe only visible facts.",
      apiKey: "secret-test-key",
      allowExternalUpload: true,
      fetchImpl
    });

    expect(result).toMatchObject({
      status: "success",
      provider: "agnes",
      model: "agnes-2.0-flash",
      inputs: [{
        kind: "local",
        name: "private-screen.png",
        mime: "image/png",
        bytes: image.length,
        sha256: expect.stringMatching(/^[a-f0-9]{64}$/)
      }],
      attempts: { total: 1, rateLimitEvents: 0, transientRetries: 0 },
      analysis: "The image contains a test marker."
    });
    expect(JSON.stringify(result)).not.toContain(directory);
    expect(JSON.stringify(result)).not.toContain("secret-test-key");
    expect(JSON.stringify(result)).not.toContain("base64");
  });

  it("sanitizes HTTPS URLs and rejects credentialed or private URLs", () => {
    expect(sanitizeRemoteUrl("https://example.com/image.png?token=secret#part")).toMatchObject({
      display: "https://example.com/image.png",
      digest: expect.stringMatching(/^[a-f0-9]{64}$/)
    });
    expect(() => sanitizeRemoteUrl("https://user:pass@example.com/image.png")).toThrowError(
      expect.objectContaining({ code: "INPUT_URL_CREDENTIALS" })
    );
    expect(() => sanitizeRemoteUrl("https://127.0.0.1/image.png")).toThrowError(
      expect.objectContaining({ code: "INPUT_URL_PRIVATE" })
    );
    expect(() => sanitizeRemoteUrl("http://example.com/image.png")).toThrowError(
      expect.objectContaining({ code: "INPUT_URL_PROTOCOL" })
    );
  });

  it("keeps retrying 429 responses and honors retry-after until success", async () => {
    const responses = [
      new Response("limited", { status: 429, headers: { "retry-after": "0.01" } }),
      new Response("limited", { status: 429 }),
      jsonResponse({ choices: [{ message: { content: "done" } }] })
    ];
    const fetchImpl = vi.fn(async () => responses.shift()!);
    const waits: number[] = [];
    const events: Array<Record<string, unknown>> = [];

    const result = await requestAnalysis({
      endpoint: new URL("https://example.com/v1/chat/completions"),
      apiKey: "secret-test-key",
      payload: buildPayload({ prompt: "inspect", model: "test", imageParts: [] }),
      fetchImpl,
      sleep: async (milliseconds) => {
        waits.push(milliseconds);
      },
      onEvent: (event) => events.push(event)
    });

    expect(result).toMatchObject({
      analysis: "done",
      attempts: { total: 3, rateLimitEvents: 2, transientRetries: 0 }
    });
    expect(waits).toEqual([10, 2_000]);
    expect(events.map((event) => event.type)).toEqual(["rate-limit", "rate-limit"]);
  });

  it("cancels an active rate-limit wait without waiting for the delay to expire", async () => {
    vi.useFakeTimers();
    const controller = new AbortController();
    const wait = sleepWithSignal(60_000, controller.signal);
    controller.abort();
    await expect(wait).rejects.toMatchObject({ code: "CANCELLED", exitCode: 130 });
    expect(vi.getTimerCount()).toBe(0);
    vi.useRealTimers();
  });

  it("retries network and server failures three times, then succeeds", async () => {
    const responses = [
      new Response("server error", { status: 500 }),
      new Response("server error", { status: 503 }),
      new Response("timeout", { status: 408 }),
      jsonResponse({ choices: [{ message: { content: "recovered" } }] })
    ];
    const fetchImpl = vi.fn(async () => responses.shift()!);
    const waits: number[] = [];

    const result = await requestAnalysis({
      endpoint: new URL("https://example.com/v1/chat/completions"),
      apiKey: "secret-test-key",
      payload: buildPayload({ prompt: "inspect", model: "test", imageParts: [] }),
      fetchImpl,
      sleep: async (milliseconds) => {
        waits.push(milliseconds);
      }
    });

    expect(result).toMatchObject({
      analysis: "recovered",
      attempts: { total: 4, rateLimitEvents: 0, transientRetries: 3 }
    });
    expect(waits).toEqual([1_000, 2_000, 4_000]);
  });

  it("fails non-retriable 4xx responses immediately without leaking the key", async () => {
    const fetchImpl = vi.fn(async () => new Response("invalid secret-test-key", { status: 401 }));
    await expect(requestAnalysis({
      endpoint: new URL("https://example.com/v1/chat/completions"),
      apiKey: "secret-test-key",
      payload: buildPayload({ prompt: "inspect", model: "test", imageParts: [] }),
      fetchImpl,
      sleep: async () => {}
    })).rejects.toEqual(expect.objectContaining<VisionAnalysisError>({
      code: "HTTP_NON_RETRIABLE",
      message: expect.not.stringContaining("secret-test-key")
    }));
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });
});

function jsonResponse(payload: unknown): Response {
  return new Response(JSON.stringify(payload), {
    status: 200,
    headers: { "content-type": "application/json" }
  });
}
