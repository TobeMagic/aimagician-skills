import { constants } from "node:fs";
import { access, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import {
  archiveSkills,
  installSkills,
  previewInstallSkills,
  resetSkills,
  searchSkills,
  setSkillOverride,
  uninstallSkills
} from "../../src/manager/manager";

const tempDirectories: string[] = [];

afterEach(async () => {
  await Promise.allSettled(
    tempDirectories.splice(0).map((directory) =>
      rm(directory, { recursive: true, force: true })
    )
  );
});

describe("manager operations", () => {
  it("searches catalog skills with taxonomy and project install status", async () => {
    const fixture = await createManagerFixture();

    const beforeInstall = await searchSkills({
      query: "daily",
      scope: "project",
      projectDir: fixture.projectDir,
      selectedTargets: ["claude"],
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides
    });

    expect(beforeInstall.map((skill) => ({
      id: skill.id,
      group: skill.group,
      subgroup: skill.subgroup,
      installedTargets: skill.installedTargets
    }))).toEqual([
      {
        id: "daily-ops",
        group: "build",
        subgroup: "workflow",
        installedTargets: []
      }
    ]);

    await installSkills({
      assetIds: ["daily-ops"],
      scope: "project",
      projectDir: fixture.projectDir,
      selectedTargets: ["claude"],
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides,
      now: "2026-05-24T10:00:00Z"
    });

    const afterInstall = await searchSkills({
      query: "daily",
      scope: "project",
      projectDir: fixture.projectDir,
      selectedTargets: ["claude"],
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides
    });

    expect(afterInstall[0]?.installedTargets).toEqual(["claude"]);
  });

  it("hides archived owned skills by default and shows them when requested", async () => {
    const fixture = await createManagerFixture();

    const defaultSkills = await searchSkills({
      scope: "project",
      projectDir: fixture.projectDir,
      selectedTargets: ["claude"],
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides
    });
    const withArchived = await searchSkills({
      scope: "project",
      projectDir: fixture.projectDir,
      selectedTargets: ["claude"],
      includeArchived: true,
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides
    });

    expect(defaultSkills.map((skill) => skill.id)).not.toContain("retired-helper");
    expect(withArchived.find((skill) => skill.id === "retired-helper")).toMatchObject({
      id: "retired-helper",
      archived: true
    });

    const hiddenArchivedInstall = await installSkills({
      assetIds: ["retired-helper"],
      scope: "project",
      projectDir: fixture.projectDir,
      selectedTargets: ["claude"],
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides,
      dryRun: true
    });
    const archivedInstall = await installSkills({
      assetIds: ["retired-helper"],
      scope: "project",
      projectDir: fixture.projectDir,
      selectedTargets: ["claude"],
      includeArchived: true,
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides,
      now: "2026-05-24T10:30:00Z"
    });

    expect(hiddenArchivedInstall.skipped).toEqual([
      {
        assetId: "retired-helper",
        reason: "not-found"
      }
    ]);
    expect(archivedInstall.installed.map((install) => install.assetId)).toEqual(["retired-helper"]);
    await expectPath(join(fixture.projectDir, ".claude", "skills", "retired-helper", "SKILL.md"));
  });


  it("keeps archive overrides isolated between project and global scopes", async () => {
    const fixture = await createManagerFixture();

    await archiveSkills({
      assetIds: ["daily-ops"],
      archived: true,
      scope: "project",
      projectDir: fixture.projectDir,
      selectedTargets: ["claude"],
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides
    });

    const projectSkills = await searchSkills({
      scope: "project",
      projectDir: fixture.projectDir,
      selectedTargets: ["claude"],
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides
    });
    const globalSkills = await searchSkills({
      scope: "global",
      selectedTargets: ["claude"],
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides
    });

    expect(projectSkills.map((skill) => skill.id)).not.toContain("daily-ops");
    expect(globalSkills.map((skill) => skill.id)).toContain("daily-ops");
  });

  it("installs selected skills into project-native target homes and uninstalls only managed skills", async () => {
    const fixture = await createManagerFixture();

    const installResult = await installSkills({
      assetIds: ["daily-ops", "external-helper"],
      scope: "project",
      projectDir: fixture.projectDir,
      selectedTargets: ["claude"],
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides,
      now: "2026-05-24T11:00:00Z"
    });

    expect(installResult.installed.map((install) => install.assetId).sort()).toEqual([
      "daily-ops",
      "external-helper"
    ]);
    await expectPath(join(fixture.projectDir, ".claude", "skills", "daily-ops", "SKILL.md"));
    await expectPath(join(fixture.projectDir, ".claude", "skills", "external-helper", "SKILL.md"));
    await expectMissing(join(fixture.projectDir, ".claude", "skills", "research-helper", "SKILL.md"));

    const manifest = JSON.parse(
      await readFile(join(fixture.projectDir, ".skillbird", "manifest.json"), "utf8")
    ) as {
      selectedTargets: string[];
      managedInstalls: Array<{ target: string; assetId: string; destinationPath: string }>;
    };

    expect(manifest.selectedTargets).toEqual(["claude"]);
    expect(manifest.managedInstalls.map((install) => install.assetId).sort()).toEqual([
      "daily-ops",
      "external-helper"
    ]);

    const manualSkillDir = join(fixture.projectDir, ".claude", "skills", "manual-skill");
    await mkdir(manualSkillDir, { recursive: true });
    await writeFile(join(manualSkillDir, "SKILL.md"), "# Manual Skill\n", "utf8");

    const uninstallResult = await uninstallSkills({
      assetIds: ["daily-ops", "manual-skill"],
      scope: "project",
      projectDir: fixture.projectDir,
      selectedTargets: ["claude"],
      platform: fixture.platform,
      now: "2026-05-24T12:00:00Z"
    });

    expect(uninstallResult.removed.map((install) => install.assetId)).toEqual(["daily-ops"]);
    expect(uninstallResult.skipped).toEqual([
      {
        assetId: "manual-skill",
        target: "claude",
        reason: "not-managed"
      }
    ]);
    await expectMissing(join(fixture.projectDir, ".claude", "skills", "daily-ops", "SKILL.md"));
    await expectPath(join(fixture.projectDir, ".claude", "skills", "external-helper", "SKILL.md"));
    await expectPath(join(manualSkillDir, "SKILL.md"));
  });

  it("installs skills selected by category without explicit asset ids", async () => {
    const fixture = await createManagerFixture();

    const installResult = await installSkills({
      assetIds: [],
      category: "build",
      scope: "project",
      projectDir: fixture.projectDir,
      selectedTargets: ["claude"],
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides,
      now: "2026-05-24T11:30:00Z"
    });

    expect(installResult.installed.map((install) => install.assetId).sort()).toEqual([
      "daily-ops",
      "external-helper"
    ]);
  });


  it("shows default-disabled source skills in search but skips bulk install unless included", async () => {
    const fixture = await createManagerFixture();

    const searchResults = await searchSkills({
      query: "business",
      scope: "global",
      selectedTargets: ["claude"],
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides
    });

    expect(searchResults.map((skill) => skill.id)).toContain("business-helper");

    const bulkInstall = await installSkills({
      assetIds: ["business-helper"],
      scope: "global",
      selectedTargets: ["claude"],
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides,
      dryRun: true
    });

    expect(bulkInstall.skipped).toContainEqual({
      assetId: "business-helper",
      reason: "source-default-disabled"
    });
  });

  it("lets explicit include install from default-disabled sources while exclude wins", async () => {
    const fixture = await createManagerFixture();
    const globalConfigPath = join(fixture.platform.configBaseDir, "skillbird", "global", "config.yaml");
    await mkdir(join(fixture.platform.configBaseDir, "skillbird", "global"), { recursive: true });

    await writeFile(
      globalConfigPath,
      [
        "version: 1",
        "includedIds:",
        "  - business-helper"
      ].join("\n"),
      "utf8"
    );

    const includedInstall = await installSkills({
      assetIds: ["business-helper"],
      scope: "global",
      selectedTargets: ["claude"],
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides,
      dryRun: true
    });

    expect(includedInstall.skipped).toEqual([]);
    expect(includedInstall.installed.map((install) => install.assetId)).toEqual(["business-helper"]);

    await writeFile(
      globalConfigPath,
      [
        "version: 1",
        "includedIds:",
        "  - business-helper",
        "excludedIds:",
        "  - business-helper"
      ].join("\n"),
      "utf8"
    );

    const excludedInstall = await installSkills({
      assetIds: ["business-helper"],
      scope: "global",
      selectedTargets: ["claude"],
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides,
      dryRun: true
    });

    expect(excludedInstall.skipped).toContainEqual({
      assetId: "business-helper",
      reason: "excluded"
    });
  });

  it("previews install sync without writing target files", async () => {
    const fixture = await createManagerFixture();

    const preview = await previewInstallSkills({
      assetIds: ["daily-ops"],
      scope: "project",
      projectDir: fixture.projectDir,
      selectedTargets: ["claude"],
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides
    });

    expect(preview.operations.map((operation) => ({ kind: operation.kind, assetId: operation.assetId }))).toEqual([
      { kind: "create", assetId: "daily-ops" }
    ]);
    expect(preview.targetReports).toEqual([
      {
        target: "claude",
        plannedSkillIds: ["daily-ops"],
        skippedSkillIds: [],
        removeSkillIds: [],
        overwriteSkillIds: []
      }
    ]);
    await expectMissing(join(fixture.projectDir, ".claude", "skills", "daily-ops", "SKILL.md"));
  });

  it("persists scoped include exclude and default skill overrides", async () => {
    const fixture = await createManagerFixture();

    await setSkillOverride({
      assetIds: ["business-helper"],
      state: "include",
      scope: "project",
      projectDir: fixture.projectDir,
      platform: fixture.platform
    });
    let config = await readFile(join(fixture.projectDir, ".skillbird", "config.yaml"), "utf8");
    expect(config).toContain("includedIds:");
    expect(config).toContain("business-helper");

    await setSkillOverride({
      assetIds: ["business-helper"],
      state: "exclude",
      scope: "project",
      projectDir: fixture.projectDir,
      platform: fixture.platform
    });
    config = await readFile(join(fixture.projectDir, ".skillbird", "config.yaml"), "utf8");
    expect(config).toContain("excludedIds:");
    expect(config).toContain("business-helper");

    await setSkillOverride({
      assetIds: ["business-helper"],
      state: "default",
      scope: "project",
      projectDir: fixture.projectDir,
      platform: fixture.platform
    });
    config = await readFile(join(fixture.projectDir, ".skillbird", "config.yaml"), "utf8");
    expect(config).toContain("includedIds: []");
    expect(config).toContain("excludedIds: []");
  });

  it("resets cursor across global and project scopes before reinstalling all active skills", async () => {
    const fixture = await createManagerFixture();
    const globalStaleSkill = join(fixture.platform.homeDir, ".cursor", "skills", "old-global");
    const projectStaleSkill = join(fixture.projectDir, ".cursor", "skills", "old-project");

    await mkdir(globalStaleSkill, { recursive: true });
    await mkdir(projectStaleSkill, { recursive: true });
    await writeFile(join(globalStaleSkill, "SKILL.md"), "# Old Global\n", "utf8");
    await writeFile(join(projectStaleSkill, "SKILL.md"), "# Old Project\n", "utf8");

    const result = await resetSkills({
      target: "cursor",
      scope: "all",
      projectDir: fixture.projectDir,
      installAll: true,
      yes: true,
      catalog: fixture.catalog,
      taxonomyPath: fixture.taxonomyPath,
      platform: fixture.platform,
      githubRepoOverrides: fixture.githubRepoOverrides,
      now: "2026-05-24T13:00:00Z"
    });

    expect(result.scopes.map((entry) => entry.scope)).toEqual(["global", "project"]);
    await expectMissing(join(globalStaleSkill, "SKILL.md"));
    await expectMissing(join(projectStaleSkill, "SKILL.md"));
    await expectPath(join(fixture.platform.homeDir, ".cursor", "skills", "daily-ops", "SKILL.md"));
    await expectPath(join(fixture.platform.homeDir, ".cursor", "skills", "external-helper", "SKILL.md"));
    await expectPath(join(fixture.projectDir, ".cursor", "skills", "daily-ops", "SKILL.md"));
    await expectPath(join(fixture.projectDir, ".cursor", "skills", "external-helper", "SKILL.md"));
    await expectMissing(join(fixture.projectDir, ".cursor", "skills", "retired-helper", "SKILL.md"));
  });
});

async function createManagerFixture() {
  const root = await mkdtemp(join(tmpdir(), "aimagician-manager-"));
  tempDirectories.push(root);

  const projectDir = join(root, "project");
  const homeDir = join(root, "home");
  const ownedSkillsRoot = join(root, "fixture", "skills", "owned");
  const archivedSkillsRoot = join(root, "fixture", "skills", "archived");
  const skillsRoot = join(root, "fixture", "catalog", "skills");
  const pluginsRoot = join(root, "fixture", "catalog", "plugins");
  const externalRepoRoot = join(root, "fixture", "external-source");
  const businessRepoRoot = join(root, "fixture", "business-source");
  const taxonomyPath = join(root, "fixture", "catalog", "taxonomy.yaml");

  await mkdir(projectDir, { recursive: true });
  await mkdir(join(ownedSkillsRoot, "daily-ops"), { recursive: true });
  await mkdir(join(ownedSkillsRoot, "research-helper"), { recursive: true });
  await mkdir(join(archivedSkillsRoot, "retired-helper"), { recursive: true });
  await mkdir(skillsRoot, { recursive: true });
  await mkdir(pluginsRoot, { recursive: true });
  await mkdir(join(externalRepoRoot, "skills", "external-helper"), { recursive: true });
  await mkdir(join(businessRepoRoot, "skills", "business-helper"), { recursive: true });

  await writeFile(join(ownedSkillsRoot, "daily-ops", "SKILL.md"), "# Daily Ops\n", "utf8");
  await writeFile(join(ownedSkillsRoot, "research-helper", "SKILL.md"), "# Research Helper\n", "utf8");
  await writeFile(join(archivedSkillsRoot, "retired-helper", "SKILL.md"), "# Retired Helper\n", "utf8");
  await writeFile(join(externalRepoRoot, "skills", "external-helper", "SKILL.md"), "# External Helper\n", "utf8");
  await writeFile(join(businessRepoRoot, "skills", "business-helper", "SKILL.md"), "# Business Helper\n", "utf8");
  await writeFile(
    join(skillsRoot, "skills.yaml"),
    [
      "sources:",
      "  - id: external-skills",
      "    type: github",
      "    enabled: true",
      "    github:",
      "      repo: aimagician/external-skills",
      "      path: skills",
      "    assets:",
      "      - path: external-helper",
      "  - id: business-skills",
      "    type: github",
      "    enabled: false",
      "    description: Business source",
      "    github:",
      "      repo: aimagician/business-skills",
      "      path: skills",
      "    assets:",
      "      - path: business-helper",
      "  - id: disabled-undiscovered",
      "    type: github",
      "    enabled: false",
      "    description: Disabled source without declared assets must not be cloned during search",
      "    github:",
      "      repo: aimagician/missing-undiscovered-skills",
      "      path: skills"
    ].join("\n"),
    "utf8"
  );
  await writeFile(join(pluginsRoot, "plugins.yaml"), "sources: []\n", "utf8");
  await writeFile(
    taxonomyPath,
    [
      "groups:",
      "  - id: build",
      "    label: Build",
      "  - id: research",
      "    label: Research",
      "skills:",
      "  daily-ops:",
      "    group: build",
      "    subgroup: workflow",
      "    tags: [workflow]",
      "    recommendedScopes: [project]",
      "    recommendedTargets: [claude]",
      "  external-helper:",
      "    group: build",
      "    subgroup: workflow",
      "    tags: [external]",
      "  business-helper:",
      "    group: strategy",
      "    tags: [business]"
    ].join("\n"),
    "utf8"
  );

  return {
    root,
    projectDir,
    taxonomyPath,
    catalog: {
      ownedSkillsRoot,
      archivedSkillsRoot,
      skillsRoot,
      pluginsRoot
    },
    platform: {
      platform: "linux" as const,
      homeDir,
      configBaseDir: join(homeDir, ".config"),
      stateBaseDir: join(homeDir, ".local", "state"),
      workspaceRoot: join(root, "global-workspace")
    },
    githubRepoOverrides: {
      "aimagician/external-skills": externalRepoRoot,
      "aimagician/business-skills": businessRepoRoot
    }
  };
}

async function expectPath(path: string): Promise<void> {
  await access(path, constants.F_OK);
}

async function expectMissing(path: string): Promise<void> {
  await expect(access(path, constants.F_OK)).rejects.toMatchObject({ code: "ENOENT" });
}
