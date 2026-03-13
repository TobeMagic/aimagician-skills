import { mkdtemp, mkdir, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { loadCatalog } from "../../src/catalog/load-catalog";
import { pluginsCatalogRoot, skillsCatalogRoot } from "../../src/shared/paths";

const tempDirectories: string[] = [];

afterEach(async () => {
  await Promise.allSettled(
    tempDirectories.splice(0).map(async (directory) => {
      await import("node:fs/promises").then(({ rm }) =>
        rm(directory, { recursive: true, force: true })
      );
    })
  );
});

describe("loadCatalog", () => {
  it("loads example skill and plugin catalogs with shared source vocabulary", async () => {
    const catalog = await loadCatalog({
      skillsRoot: skillsCatalogRoot,
      pluginsRoot: pluginsCatalogRoot
    });

    expect(catalog.skills.sources).toHaveLength(2);
    expect(catalog.plugins.sources).toHaveLength(1);
    expect(catalog.activeSources.map((source) => source.id)).toEqual([
      "claude-official",
      "opencode-browser"
    ]);
    expect(catalog.ownedSkills).toHaveLength(0);
    expect(catalog.skills.sources[0]?.type).toBe("github");
    expect(catalog.plugins.sources[0]?.type).toBe("command");
  });

  it("keeps disabled sources in config while filtering them from active resolution", async () => {
    const root = await mkdtemp(join(tmpdir(), "aimagician-skills-catalog-"));
    tempDirectories.push(root);

    const skillsRoot = join(root, "skills");
    const pluginsRoot = join(root, "plugins");
    const ownedSkillsRoot = join(root, "owned");
    await mkdir(skillsRoot, { recursive: true });
    await mkdir(pluginsRoot, { recursive: true });
    await mkdir(join(ownedSkillsRoot, "release-notes"), { recursive: true });
    await mkdir(join(ownedSkillsRoot, "daily-ops"), { recursive: true });

    const skillYaml = await readFile(join(skillsCatalogRoot, "example.yaml"), "utf8");
    await writeFile(join(skillsRoot, "example.yaml"), skillYaml, "utf8");
    await writeFile(
      join(ownedSkillsRoot, "release-notes", "SKILL.md"),
      "# Release Notes\n",
      "utf8"
    );
    await writeFile(
      join(ownedSkillsRoot, "daily-ops", "SKILL.md"),
      "# Daily Ops\n",
      "utf8"
    );
    await writeFile(
      join(pluginsRoot, "example.yaml"),
      [
        "sources:",
        "  - id: opencode-plugin",
        "    type: command",
        "    enabled: false",
        "    command:",
        "      run: opencode plugin add browser-tools",
        "    assets:",
        "      - id: browser-tools",
        "        kind: plugin"
      ].join("\n"),
      "utf8"
    );

    const catalog = await loadCatalog({
      ownedSkillsRoot,
      skillsRoot,
      pluginsRoot
    });

    expect(catalog.sources.map((source) => source.id)).toEqual([
      "claude-official",
      "local-bootstrap",
      "opencode-plugin"
    ]);
    expect(catalog.activeSources.map((source) => source.id)).toEqual([
      "claude-official"
    ]);
    expect(catalog.sources.find((source) => source.id === "local-bootstrap")?.enabled).toBe(
      false
    );
    expect(catalog.ownedSkills.map((skill) => skill.id)).toEqual([
      "daily-ops",
      "release-notes"
    ]);
  });
});
