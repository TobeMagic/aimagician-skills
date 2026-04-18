import { mkdtemp, mkdir, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { loadCatalog } from "../../src/catalog/load-catalog";
import { normalizeSources } from "../../src/catalog/normalize";
import { fixturesRoot } from "../../src/shared/paths";
import { parse } from "yaml";

const tempDirectories: string[] = [];

afterEach(async () => {
  const { rm } = await import("node:fs/promises");
  await Promise.allSettled(
    tempDirectories.splice(0).map((directory) =>
      rm(directory, { recursive: true, force: true })
    )
  );
});

describe("normalizeSources", () => {
  it("applies default all-target behavior plus source-level and asset-level overrides", async () => {
    const fixturePath = join(fixturesRoot, "catalog", "target-overrides.yaml");
    const fixture = parse(await readFile(fixturePath, "utf8")) as {
      skills: unknown;
      plugins: unknown;
    };

    const root = await mkdtemp(join(tmpdir(), "aimagician-skills-targets-"));
    tempDirectories.push(root);

    const skillsRoot = join(root, "skills");
    const pluginsRoot = join(root, "plugins");
    await mkdir(skillsRoot, { recursive: true });
    await mkdir(pluginsRoot, { recursive: true });

    await writeFile(join(skillsRoot, "fixture.yaml"), stringifySection(fixture.skills), "utf8");
    await writeFile(
      join(pluginsRoot, "fixture.yaml"),
      stringifySection(fixture.plugins),
      "utf8"
    );

    const catalog = await loadCatalog({ skillsRoot, pluginsRoot });
    const assets = normalizeSources(catalog.activeSources);

    const shipEverywhere = assets.find((asset) => asset.id === "ship-everywhere");
    const sourceDefault = assets.find((asset) => asset.id === "source-default");
    const geminiNative = assets.find((asset) => asset.id === "gemini-native");
    const browserTools = assets.find((asset) => asset.id === "browser-tools");
    const opencodeOnly = assets.find((asset) => asset.id === "opencode-only");

    expect(shipEverywhere?.effectiveTargets).toEqual([
      "codex",
      "claude",
      "opencode",
      "gemini",
      "hermes",
      "cursor"
    ]);
    expect(sourceDefault?.effectiveTargets).toEqual(["claude", "opencode"]);
    expect(geminiNative?.effectiveTargets).toEqual(["gemini"]);
    expect(geminiNative?.targetStates.gemini.warnings).toContain(
      "Needs target-native GEMINI.md rendering"
    );
    expect(browserTools?.effectiveTargets).toEqual(["opencode", "codex"]);
    expect(browserTools?.targetStates.codex.warnings).toContain(
      "Codex plugin adapters are not available"
    );
    expect(opencodeOnly?.effectiveTargets).toEqual(["opencode"]);
  });
});

function stringifySection(section: unknown): string {
  return JSON.stringify(section, null, 2);
}
