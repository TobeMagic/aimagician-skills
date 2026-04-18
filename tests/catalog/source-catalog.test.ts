import { mkdtemp, mkdir, writeFile } from "node:fs/promises";
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
  it("loads the live repository catalogs and preserves github sources that default to all assets", async () => {
    const catalog = await loadCatalog({
      skillsRoot: skillsCatalogRoot,
      pluginsRoot: pluginsCatalogRoot
    });

    expect(catalog.skills.sources.length).toBeGreaterThanOrEqual(2);
    expect(catalog.plugins.sources.length).toBeGreaterThanOrEqual(1);
    expect(catalog.activeSources.map((source) => source.id)).toEqual(
      expect.arrayContaining([
        "claude-official",
        "gsd",
        "claude-official-plugins"
      ])
    );
    expect(
      catalog.skills.sources.find((source) => source.id === "claude-official")
    ).toMatchObject({
      type: "github"
    });
    expect(
      catalog.skills.sources.find((source) => source.id === "gsd")
    ).toMatchObject({
      type: "command"
    });
    expect(
      catalog.plugins.sources.find((source) => source.id === "claude-official-plugins")
    ).toMatchObject({
      type: "github"
    });
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

    await writeFile(
      join(skillsRoot, "skills.yaml"),
      [
        "sources:",
        "  - id: claude-official",
        "    type: github",
        "    github:",
        "      repo: anthropics/skills",
        "      path: skills",
        "  - id: local-bootstrap",
        "    type: command",
        "    enabled: false",
        "    command:",
        "      run: node scripts/install-local-bootstrap.js",
        "    assets:",
        "      - id: bootstrap-tools",
        "        kind: skill"
      ].join("\n"),
      "utf8"
    );
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
    expect(catalog.ownedSkills.map((skill) => skill.id).sort()).toEqual([
      "daily-ops",
      "release-notes"
    ]);
  });
});
