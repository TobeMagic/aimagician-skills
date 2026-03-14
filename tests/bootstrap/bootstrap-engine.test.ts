import { mkdtemp, mkdir, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { runBootstrap } from "../../src/bootstrap/run-bootstrap";
import { resolvePlatformContext } from "../../src/shared/platform";

const tempDirectories: string[] = [];

afterEach(async () => {
  const { rm } = await import("node:fs/promises");
  await Promise.allSettled(
    tempDirectories.splice(0).map((directory) =>
      rm(directory, { recursive: true, force: true })
    )
  );
});

describe("runBootstrap", () => {
  it("resolves cross-platform user workspace roots", () => {
    const windows = resolvePlatformContext({
      platform: "windows",
      homeDir: "C:\\Users\\AImagician",
      stateBaseDir: "C:\\Users\\AImagician\\AppData\\Local"
    });
    const linux = resolvePlatformContext({
      platform: "linux",
      homeDir: "/home/aimagician",
      stateBaseDir: "/home/aimagician/.local/state"
    });

    expect(windows.workspaceRoot).toBe(
      "C:\\Users\\AImagician\\AppData\\Local\\aimagician-skills"
    );
    expect(linux.workspaceRoot).toBe("/home/aimagician/.local/state/aimagician-skills");
  });

  it("writes deterministic bootstrap state and avoids duplicate manifest records on rerun", async () => {
    const fixture = await createFixtureRepository();
    const workspaceRoot = join(fixture.root, "workspace");

    const firstRun = await runBootstrap({
      catalog: fixture.catalog,
      githubRepoOverrides: {
        "aimagician/repo-skills": fixture.externalRepoRoot
      },
      platform: { platform: "windows", homeDir: fixture.root, configBaseDir: join(fixture.root, ".config"), stateBaseDir: fixture.root, workspaceRoot },
      now: "2026-03-14T01:00:00Z"
    });

    const secondRun = await runBootstrap({
      catalog: fixture.catalog,
      githubRepoOverrides: {
        "aimagician/repo-skills": fixture.externalRepoRoot
      },
      platform: { platform: "windows", homeDir: fixture.root, configBaseDir: join(fixture.root, ".config"), stateBaseDir: fixture.root, workspaceRoot },
      now: "2026-03-14T01:00:00Z"
    });

    const manifest = JSON.parse(await readFile(firstRun.manifestPath, "utf8")) as {
      version: number;
      assets: Array<{ id: string }>;
      managedInstalls: Array<{ target: string; assetId: string; kind: string; installArea: string }>;
    };
    const plan = JSON.parse(await readFile(firstRun.planPath, "utf8")) as {
      selectedTargets: string[];
      ownedSkillIds: string[];
    };

    expect(firstRun.changed).toBe(true);
    expect(secondRun.changed).toBe(false);
    expect(plan.selectedTargets).toEqual(["codex", "claude", "opencode", "gemini"]);
    expect(plan.ownedSkillIds).toEqual(["daily-ops"]);
    expect(manifest.version).toBe(3);
    expect(manifest.assets.map((asset) => asset.id)).toEqual([
      "daily-ops",
      "claude-sync",
      "bootstrap-tools"
    ]);
    expect(
      manifest.managedInstalls.map((install) => ({
        target: install.target,
        assetId: install.assetId,
        kind: install.kind,
        installArea: install.installArea
      }))
    ).toEqual([
      { target: "claude", assetId: "claude-sync", kind: "skill", installArea: "skills" },
      { target: "claude", assetId: "daily-ops", kind: "skill", installArea: "skills" },
      { target: "codex", assetId: "claude-sync", kind: "skill", installArea: "skills" },
      { target: "codex", assetId: "daily-ops", kind: "skill", installArea: "skills" },
      { target: "gemini", assetId: "claude-sync", kind: "skill", installArea: "extensions" },
      { target: "gemini", assetId: "daily-ops", kind: "skill", installArea: "extensions" },
      { target: "opencode", assetId: "claude-sync", kind: "skill", installArea: "skills" },
      { target: "opencode", assetId: "daily-ops", kind: "skill", installArea: "skills" }
    ]);
  }, 15000);

  it("respects selected target overrides during bootstrap planning", async () => {
    const fixture = await createFixtureRepository();

    const result = await runBootstrap({
      dryRun: true,
      selectedTargets: ["claude"],
      catalog: fixture.catalog,
      githubRepoOverrides: {
        "aimagician/repo-skills": fixture.externalRepoRoot
      },
      platform: { platform: "linux", homeDir: fixture.root, stateBaseDir: fixture.root }
    });

    expect(result.mode).toBe("dry-run");
    expect(result.plan.assets.map((asset) => ({
      id: asset.id,
      targets: asset.selectedTargets
    }))).toEqual([
      { id: "daily-ops", targets: ["claude"] },
      { id: "claude-sync", targets: ["claude"] },
      { id: "bootstrap-tools", targets: ["claude"] }
    ]);
  });

  it("reports planned and skipped plugin outcomes during dry-run", async () => {
    const fixture = await createFixtureRepository({ includePluginSource: true });

    const result = await runBootstrap({
      dryRun: true,
      selectedTargets: ["claude", "opencode"],
      catalog: fixture.catalog,
      githubRepoOverrides: {
        "aimagician/repo-skills": fixture.externalRepoRoot
      },
      platform: { platform: "linux", homeDir: fixture.root, stateBaseDir: fixture.root }
    });

    expect(result.pluginReports).toEqual([
      {
        assetId: "audit-helper",
        sourceId: "plugin-repo",
        target: "claude",
        status: "skipped",
        reason: "Claude Code plugin automation remains marketplace- and consent-driven, so bootstrap skips it"
      },
      {
        assetId: "audit-helper",
        sourceId: "plugin-repo",
        target: "opencode",
        status: "planned",
        destinationPath: join(fixture.root, ".config", "opencode", "plugins", "audit-helper.ts")
      }
    ]);
  });
});

async function createFixtureRepository(
  options: { includePluginSource?: boolean } = {}
) {
  const root = await mkdtemp(join(tmpdir(), "aimagician-bootstrap-"));
  tempDirectories.push(root);

  const ownedSkillsRoot = join(root, "skills", "owned");
  const skillsRoot = join(root, "catalog", "skills");
  const pluginsRoot = join(root, "catalog", "plugins");
  const externalRepoRoot = join(root, "external-source");
  const commandScriptPath = join(root, "bootstrap-command.js");

  await mkdir(join(ownedSkillsRoot, "daily-ops"), { recursive: true });
  await mkdir(skillsRoot, { recursive: true });
  await mkdir(pluginsRoot, { recursive: true });
  await mkdir(join(externalRepoRoot, "claude-sync"), { recursive: true });
  await mkdir(join(externalRepoRoot, "plugins"), { recursive: true });

  await writeFile(join(ownedSkillsRoot, "daily-ops", "SKILL.md"), "# Daily Ops\n", "utf8");
  await writeFile(join(externalRepoRoot, "claude-sync", "SKILL.md"), "# Claude Sync\n", "utf8");
  await writeFile(
    join(externalRepoRoot, "plugins", "audit-helper.ts"),
    "export default async function auditHelper() {}\n",
    "utf8"
  );
  await writeFile(commandScriptPath, "process.exit(0);\n", "utf8");
  await writeFile(
    join(skillsRoot, "skills.yaml"),
    [
      "sources:",
      "  - id: repo-skills",
      "    type: github",
      "    github:",
      "      repo: aimagician/repo-skills",
      "    assets:",
      "      - id: claude-sync",
      "        kind: skill",
      "  - id: bootstrap-command",
      "    type: command",
      "    targets:",
      "      include:",
      "        - claude",
      "        - opencode",
      "    command:",
      `      run: '${process.execPath} ${commandScriptPath}'`,
      "    assets:",
      "      - id: bootstrap-tools",
      "        kind: skill"
    ].join("\n"),
    "utf8"
  );
  await writeFile(
    join(pluginsRoot, "plugins.yaml"),
    options.includePluginSource
      ? [
          "sources:",
          "  - id: plugin-repo",
          "    type: github",
          "    targets:",
          "      include:",
          "        - claude",
          "        - opencode",
          "    github:",
          "      repo: aimagician/repo-skills",
          "      path: plugins",
          "    assets:",
          "      - id: audit-helper",
          "        kind: plugin",
          "        path: audit-helper.ts"
        ].join("\n")
      : "sources: []\n",
    "utf8"
  );

  return {
    root,
    externalRepoRoot,
    catalog: {
      ownedSkillsRoot,
      skillsRoot,
      pluginsRoot
    }
  };
}
