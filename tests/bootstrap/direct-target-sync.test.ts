import { access, mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { constants } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { runBootstrap } from "../../src/bootstrap/run-bootstrap";

const tempDirectories: string[] = [];

afterEach(async () => {
  await Promise.allSettled(
    tempDirectories.splice(0).map((directory) =>
      rm(directory, { recursive: true, force: true })
    )
  );
});

describe("direct target sync", () => {
  it("copies owned and GitHub-resolved skills into Codex, Claude Code, and OpenCode homes", async () => {
    const fixture = await createFixtureRepository();
    const workspaceRoot = join(fixture.root, "workspace");
    const homeDir = join(fixture.root, "home");

    const result = await runBootstrap({
      selectedTargets: ["codex", "claude", "opencode", "gemini"],
      catalog: fixture.catalog,
      platform: {
        platform: "linux",
        homeDir,
        configBaseDir: join(homeDir, ".config"),
        stateBaseDir: fixture.root,
        workspaceRoot
      },
      githubRepoOverrides: {
        "aimagician/external-skills": fixture.externalRepoRoot
      },
      now: "2026-03-14T03:00:00Z"
    });

    expect(result.mode).toBe("apply");
    expect(result.targetReports).toMatchObject([
      {
        target: "codex",
        status: "synced",
        installedSkillIds: ["daily-ops", "gsd"],
        skillsDir: expect.stringMatching(/[\\/]?\.codex[\\/]skills$/)
      },
      {
        target: "claude",
        status: "synced",
        installedSkillIds: ["daily-ops", "gsd"],
        skillsDir: expect.stringMatching(/[\\/]?\.claude[\\/]skills$/)
      },
      {
        target: "opencode",
        status: "synced",
        installedSkillIds: ["daily-ops", "gsd"],
        skillsDir: expect.stringMatching(/[\\/]?\.config[\\/]opencode[\\/]skills$/)
      },
      {
        target: "gemini",
        status: "synced",
        installedSkillIds: ["daily-ops", "gsd"],
        extensionsDir: expect.stringMatching(/[\\/]?\.gemini[\\/]extensions$/)
      }
    ]);

    await expectSkillInstalled(homeDir, ".codex", "daily-ops", "# Daily Ops\n");
    await expectSkillInstalled(homeDir, ".claude", "daily-ops", "# Daily Ops\n");
    await expectSkillInstalled(homeDir, ".config/opencode", "daily-ops", "# Daily Ops\n");
    await expectSkillInstalled(homeDir, ".codex", "gsd", "# GSD\n");
    await expectSkillInstalled(homeDir, ".claude", "gsd", "# GSD\n");
    await expectSkillInstalled(homeDir, ".config/opencode", "gsd", "# GSD\n");
    await access(
      join(homeDir, ".gemini", "extensions", "daily-ops", "gemini-extension.json"),
      constants.F_OK
    );
    await access(
      join(homeDir, ".gemini", "extensions", "gsd", "gemini-extension.json"),
      constants.F_OK
    );

    const copiedHelper = await readFile(
      join(homeDir, ".codex", "skills", "daily-ops", "notes.txt"),
      "utf8"
    );
    expect(copiedHelper).toBe("owned helper\n");
    const geminiContext = await readFile(
      join(homeDir, ".gemini", "extensions", "daily-ops", "GEMINI.md"),
      "utf8"
    );
    expect(geminiContext).toContain("# Daily Ops");
  }, 15000);

  it("prunes stale managed installs on selected targets and keeps unmanaged directories", async () => {
    const fixture = await createFixtureRepository();
    const workspaceRoot = join(fixture.root, "workspace");
    const homeDir = join(fixture.root, "home");

    await runBootstrap({
      selectedTargets: ["codex"],
      catalog: fixture.catalog,
      platform: {
        platform: "linux",
        homeDir,
        configBaseDir: join(homeDir, ".config"),
        stateBaseDir: fixture.root,
        workspaceRoot
      },
      githubRepoOverrides: {
        "aimagician/external-skills": fixture.externalRepoRoot
      },
      now: "2026-03-14T03:00:00Z"
    });

    await mkdir(join(homeDir, ".codex", "skills", "manual-skill"), { recursive: true });
    await writeFile(
      join(homeDir, ".codex", "skills", "manual-skill", "SKILL.md"),
      "# Manual\n",
      "utf8"
    );

    await rm(join(fixture.root, "skills", "owned", "daily-ops"), {
      recursive: true,
      force: true
    });
    await writeFile(join(fixture.catalog.skillsRoot, "skills.yaml"), "sources: []\n", "utf8");

    const rerun = await runBootstrap({
      selectedTargets: ["codex"],
      catalog: fixture.catalog,
      platform: {
        platform: "linux",
        homeDir,
        configBaseDir: join(homeDir, ".config"),
        stateBaseDir: fixture.root,
        workspaceRoot
      },
      githubRepoOverrides: {
        "aimagician/external-skills": fixture.externalRepoRoot
      },
      now: "2026-03-14T03:00:00Z"
    });

    expect(rerun.changed).toBe(true);
    await expectMissing(join(homeDir, ".codex", "skills", "daily-ops", "SKILL.md"));
    await expectMissing(join(homeDir, ".codex", "skills", "gsd", "SKILL.md"));
    await access(join(homeDir, ".codex", "skills", "manual-skill", "SKILL.md"), constants.F_OK);
  });

  it("updates only the selected direct targets and leaves unselected targets untouched", async () => {
    const fixture = await createFixtureRepository();
    const workspaceRoot = join(fixture.root, "workspace");
    const homeDir = join(fixture.root, "home");

    await runBootstrap({
      selectedTargets: ["codex", "claude"],
      catalog: fixture.catalog,
      platform: {
        platform: "linux",
        homeDir,
        configBaseDir: join(homeDir, ".config"),
        stateBaseDir: fixture.root,
        workspaceRoot
      },
      githubRepoOverrides: {
        "aimagician/external-skills": fixture.externalRepoRoot
      },
      now: "2026-03-14T03:00:00Z"
    });

    await rm(join(fixture.root, "skills", "owned", "daily-ops"), {
      recursive: true,
      force: true
    });
    await writeFile(join(fixture.catalog.skillsRoot, "skills.yaml"), "sources: []\n", "utf8");

    await runBootstrap({
      selectedTargets: ["claude"],
      catalog: fixture.catalog,
      platform: {
        platform: "linux",
        homeDir,
        configBaseDir: join(homeDir, ".config"),
        stateBaseDir: fixture.root,
        workspaceRoot
      },
      githubRepoOverrides: {
        "aimagician/external-skills": fixture.externalRepoRoot
      },
      now: "2026-03-14T03:00:00Z"
    });

    await access(join(homeDir, ".codex", "skills", "daily-ops", "SKILL.md"), constants.F_OK);
    await access(join(homeDir, ".codex", "skills", "gsd", "SKILL.md"), constants.F_OK);
    await expectMissing(join(homeDir, ".claude", "skills", "daily-ops", "SKILL.md"));
    await expectMissing(join(homeDir, ".claude", "skills", "gsd", "SKILL.md"));
  });

  it("executes command-based skill sources with target-aware environment variables", async () => {
    const fixture = await createFixtureRepository({ includeCommandSource: true });
    const workspaceRoot = join(fixture.root, "workspace");
    const homeDir = join(fixture.root, "home");

    const result = await runBootstrap({
      selectedTargets: ["claude", "opencode"],
      catalog: fixture.catalog,
      platform: {
        platform: "windows",
        homeDir,
        configBaseDir: join(homeDir, ".config"),
        stateBaseDir: fixture.root,
        workspaceRoot
      },
      githubRepoOverrides: {
        "aimagician/external-skills": fixture.externalRepoRoot
      },
      now: "2026-03-14T03:00:00Z"
    });

    expect(result.commandReports).toEqual([
      {
        sourceId: "delegated-tools",
        assetIds: ["command-helper"],
        targets: ["claude", "opencode"],
        command: `${process.execPath} ${fixture.commandScriptPath}`,
        status: "executed"
      }
    ]);

    await access(
      join(homeDir, ".claude", "skills", "command-helper", "SKILL.md"),
      constants.F_OK
    );
    await access(
      join(homeDir, ".config", "opencode", "skills", "command-helper", "SKILL.md"),
      constants.F_OK
    );
  }, 15000);

  it("installs OpenCode plugin assets and reports explicit skips for unsupported plugin targets", async () => {
    const fixture = await createFixtureRepository({ includePluginSource: true });
    const workspaceRoot = join(fixture.root, "workspace");
    const homeDir = join(fixture.root, "home");

    const result = await runBootstrap({
      selectedTargets: ["claude", "opencode"],
      catalog: fixture.catalog,
      platform: {
        platform: "linux",
        homeDir,
        configBaseDir: join(homeDir, ".config"),
        stateBaseDir: fixture.root,
        workspaceRoot
      },
      githubRepoOverrides: {
        "aimagician/external-skills": fixture.externalRepoRoot
      },
      now: "2026-03-14T03:00:00Z"
    });

    expect(result.pluginReports).toEqual([
      {
        assetId: "audit-helper",
        sourceId: "opencode-plugins",
        target: "claude",
        status: "skipped",
        reason: "Claude Code plugin automation remains marketplace- and consent-driven, so bootstrap skips it"
      },
      {
        assetId: "audit-helper",
        sourceId: "opencode-plugins",
        target: "opencode",
        status: "installed",
        destinationPath: join(homeDir, ".config", "opencode", "plugins", "audit-helper.ts")
      }
    ]);

    await access(
      join(homeDir, ".config", "opencode", "plugins", "audit-helper.ts"),
      constants.F_OK
    );
  });
});

async function createFixtureRepository(
  options: { includeCommandSource?: boolean; includePluginSource?: boolean } = {}
) {
  const root = await mkdtemp(join(tmpdir(), "aimagician-direct-targets-"));
  tempDirectories.push(root);

  const ownedSkillsRoot = join(root, "skills", "owned");
  const skillsRoot = join(root, "catalog", "skills");
  const pluginsRoot = join(root, "catalog", "plugins");
  const externalRepoRoot = join(root, "external-source");
  const commandScriptPath = join(root, "delegate-install.js");

  await mkdir(join(ownedSkillsRoot, "daily-ops"), { recursive: true });
  await mkdir(join(skillsRoot), { recursive: true });
  await mkdir(join(pluginsRoot), { recursive: true });
  await mkdir(join(externalRepoRoot, "skills", "gsd"), { recursive: true });
  await mkdir(join(externalRepoRoot, "plugins"), { recursive: true });

  await writeFile(join(ownedSkillsRoot, "daily-ops", "SKILL.md"), "# Daily Ops\n", "utf8");
  await writeFile(join(ownedSkillsRoot, "daily-ops", "notes.txt"), "owned helper\n", "utf8");
  await writeFile(join(externalRepoRoot, "skills", "gsd", "SKILL.md"), "# GSD\n", "utf8");
  await writeFile(join(externalRepoRoot, "skills", "gsd", "README.md"), "external helper\n", "utf8");
  await writeFile(
    join(externalRepoRoot, "plugins", "audit-helper.ts"),
    "export default async function auditHelper() {}\n",
    "utf8"
  );
  await writeFile(
    commandScriptPath,
    [
      "const { mkdirSync, writeFileSync } = require('node:fs');",
      "const { join } = require('node:path');",
      "const targets = (process.env.AIMAGICIAN_TARGETS || '').split(',').filter(Boolean);",
      "const homes = {",
      "  claude: process.env.AIMAGICIAN_CLAUDE_SKILLS_DIR,",
      "  opencode: process.env.AIMAGICIAN_OPENCODE_SKILLS_DIR,",
      "  codex: process.env.AIMAGICIAN_CODEX_SKILLS_DIR",
      "};",
      "for (const target of targets) {",
      "  const root = homes[target];",
      "  if (!root) continue;",
      "  const skillDir = join(root, 'command-helper');",
      "  mkdirSync(skillDir, { recursive: true });",
      "  writeFileSync(join(skillDir, 'SKILL.md'), '# Command Helper\\n', 'utf8');",
      "}"
    ].join("\n"),
    "utf8"
  );
  await writeFile(
    join(skillsRoot, "skills.yaml"),
    [
      "sources:",
      "  - id: external-skills",
      "    type: github",
      "    github:",
      "      repo: aimagician/external-skills",
      "      path: skills",
      "    assets:",
      "      - path: gsd",
      ...(options.includeCommandSource
        ? [
            "  - id: delegated-tools",
            "    type: command",
            "    targets:",
            "      include:",
            "        - claude",
            "        - opencode",
            "    command:",
            `      run: '${process.execPath} ${commandScriptPath}'`,
            "    assets:",
            "      - id: command-helper"
          ]
        : [])
    ].join("\n"),
    "utf8"
  );
  await writeFile(
    join(pluginsRoot, "plugins.yaml"),
    options.includePluginSource
      ? [
          "sources:",
          "  - id: opencode-plugins",
          "    type: github",
          "    targets:",
          "      include:",
          "        - opencode",
          "        - claude",
          "    github:",
          "      repo: aimagician/external-skills",
          "      path: plugins",
          "    assets:",
          "      - path: audit-helper.ts"
        ].join("\n")
      : "sources: []\n",
    "utf8"
  );

  return {
    root,
    externalRepoRoot,
    commandScriptPath,
    catalog: {
      ownedSkillsRoot,
      skillsRoot,
      pluginsRoot
    }
  };
}

async function expectSkillInstalled(
  homeDir: string,
  targetRoot: string,
  skillId: string,
  skillContents: string
): Promise<void> {
  const skillPath = join(homeDir, targetRoot, "skills", skillId, "SKILL.md");
  const contents = await readFile(skillPath, "utf8");

  expect(contents).toBe(skillContents);
}

async function expectMissing(path: string): Promise<void> {
  await expect(access(path, constants.F_OK)).rejects.toMatchObject({
    code: "ENOENT"
  });
}
