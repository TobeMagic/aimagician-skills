import { mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import {
  addArchivedIds,
  defaultUserConfig,
  loadScopedUserConfig,
  loadUserConfig,
  removeArchivedIds,
  removeUserGroup,
  saveScopedUserConfig,
  saveUserConfig,
  saveUserGroup,
  setCustomTags,
  scopedUserConfigPath,
  userConfigPath
} from "../../src/config/user-config";

const tempDirectories: string[] = [];

afterEach(async () => {
  await Promise.allSettled(
    tempDirectories.splice(0).map((directory) =>
      rm(directory, { recursive: true, force: true })
    )
  );
});
describe("user-config", () => {
  it("returns default config when file does not exist", async () => {
    const root = await mkdtemp(join(tmpdir(), "skillbird-config-"));
    tempDirectories.push(root);

    const config = await loadUserConfig(root);

    expect(config).toEqual(defaultUserConfig());
  });

  it("loads and saves user config", async () => {
    const root = await mkdtemp(join(tmpdir(), "skillbird-config-"));
    tempDirectories.push(root);

    const config = defaultUserConfig();
    config.groups = [{ name: "my-dev", label: "My Dev", skills: ["code-guidelines", "debugging"] }];
    config.archivedIds = ["old-skill"];
    config.customTags = { "my-skill": ["favorite", "daily"] };

    await saveUserConfig(root, config);
    const loaded = await loadUserConfig(root);

    expect(loaded).toEqual(config);
  });

  it("manages archived ids", async () => {
    const root = await mkdtemp(join(tmpdir(), "skillbird-config-"));
    tempDirectories.push(root);

    const afterAdd = await addArchivedIds(root, ["skill-a", "skill-b"]);
    expect(afterAdd.archivedIds).toEqual(["skill-a", "skill-b"]);

    const afterRemove = await removeArchivedIds(root, ["skill-a"]);
    expect(afterRemove.archivedIds).toEqual(["skill-b"]);

    const loaded = await loadUserConfig(root);
    expect(loaded.archivedIds).toEqual(["skill-b"]);
  });

  it("manages custom tags per skill", async () => {
    const root = await mkdtemp(join(tmpdir(), "skillbird-config-"));
    tempDirectories.push(root);

    const afterSet = await setCustomTags(root, "my-skill", ["favorite", "daily"]);
    expect(afterSet.customTags).toEqual({ "my-skill": ["favorite", "daily"] });

    const afterClear = await setCustomTags(root, "my-skill", []);
    expect(afterClear.customTags).toEqual({});
  });

  it("manages user groups", async () => {
    const root = await mkdtemp(join(tmpdir(), "skillbird-config-"));
    tempDirectories.push(root);

    const group = { name: "my-dev", label: "My Dev", skills: ["code-guidelines"] };
    const afterAdd = await saveUserGroup(root, group);
    expect(afterAdd.groups).toHaveLength(1);
    expect(afterAdd.groups[0]).toEqual(group);

    const updated = { ...group, skills: ["code-guidelines", "debugging"] };
    const afterUpdate = await saveUserGroup(root, updated);
    expect(afterUpdate.groups).toHaveLength(1);
    expect(afterUpdate.groups[0].skills).toEqual(["code-guidelines", "debugging"]);

    const afterRemove = await removeUserGroup(root, "my-dev");
    expect(afterRemove.groups).toHaveLength(0);
  });

  it("persists to a readable YAML file", async () => {
    const root = await mkdtemp(join(tmpdir(), "skillbird-config-"));
    tempDirectories.push(root);

    const config = defaultUserConfig();
    config.groups = [{ name: "tools", label: "Tools", skills: ["skill-a"] }];
    config.archivedIds = ["old-tool"];
    config.customTags = { "skill-a": ["important"] };
    await saveUserConfig(root, config);

    const raw = await readFile(userConfigPath(root), "utf8");

    expect(raw).toContain("groups:");
    expect(raw).toContain("name: tools");
    expect(raw).toContain("archivedIds:");
    expect(raw).toContain("old-tool");
    expect(raw).toContain("customTags:");
  });

  it("resolves global and project override config paths independently", async () => {
    const root = await mkdtemp(join(tmpdir(), "skillbird-config-"));
    const projectDir = await mkdtemp(join(tmpdir(), "skillbird-project-"));
    tempDirectories.push(root, projectDir);

    expect(scopedUserConfigPath({ configBaseDir: root, scope: "global" })).toBe(
      join(root, "skillbird", "global", "config.yaml")
    );
    expect(scopedUserConfigPath({ configBaseDir: root, scope: "project", projectDir })).toBe(
      join(projectDir, ".skillbird", "config.yaml")
    );
  });

  it("loads and saves global and project override configs without cross-scope interference", async () => {
    const root = await mkdtemp(join(tmpdir(), "skillbird-config-"));
    const projectDir = await mkdtemp(join(tmpdir(), "skillbird-project-"));
    tempDirectories.push(root, projectDir);

    const globalConfig = defaultUserConfig();
    globalConfig.theme = "monokai";
    globalConfig.archivedIds = ["global-only"];

    const projectConfig = defaultUserConfig();
    projectConfig.theme = "nord";
    projectConfig.archivedIds = ["project-only"];

    await saveScopedUserConfig({ configBaseDir: root, scope: "global" }, globalConfig);
    await saveScopedUserConfig({ configBaseDir: root, scope: "project", projectDir }, projectConfig);

    await expect(loadScopedUserConfig({ configBaseDir: root, scope: "global" })).resolves.toMatchObject({
      theme: "monokai",
      archivedIds: ["global-only"]
    });
    await expect(loadScopedUserConfig({ configBaseDir: root, scope: "project", projectDir })).resolves.toMatchObject({
      theme: "nord",
      archivedIds: ["project-only"]
    });

    await expect(loadUserConfig(root)).resolves.toEqual(defaultUserConfig());
  });

});
