import { describe, expect, it } from "vitest";
import { parseCli } from "../../src/cli/parse-cli";
import { runCli } from "../../src/cli/index";

describe("parseCli", () => {
  it("defaults to bootstrap and all supported targets", () => {
    expect(parseCli([])).toEqual({
      command: "bootstrap",
      targets: ["codex", "claude", "opencode", "gemini"],
      dryRun: false,
      json: false,
      help: false
    });
  });

  it("supports explicit target overrides and flags", () => {
    expect(
      parseCli(["bootstrap", "--targets", "claude,opencode", "--dry-run", "--json"])
    ).toEqual({
      command: "bootstrap",
      targets: ["claude", "opencode"],
      dryRun: true,
      json: true,
      help: false
    });
  });

  it("rejects unsupported targets", () => {
    expect(() => parseCli(["bootstrap", "--target", "bogus"])).toThrow(
      "Unsupported target: bogus"
    );
  });
});

describe("runCli", () => {
  it("renders a readable bootstrap preview", async () => {
    const result = await runCli(["--dry-run", "--target", "claude"]);

    expect(result.exitCode).toBe(0);
    expect(result.stderr).toBe("");
    expect(result.stdout).toContain("AImagician Skills bootstrap");
    expect(result.stdout).toContain("Mode: dry-run");
    expect(result.stdout).toContain("Targets: claude");
  });

  it("renders help output when requested", async () => {
    const result = await runCli(["--help"]);

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("Usage: aimagician-skills");
    expect(result.stdout).toContain("bootstrap");
  });
});
