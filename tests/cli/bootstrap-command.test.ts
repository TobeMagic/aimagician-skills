import { mkdtemp, mkdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { parseCli } from "../../src/cli/parse-cli";
import { runCli } from "../../src/cli/index";

const tempDirectories: string[] = [];

afterEach(async () => {
  await Promise.allSettled(
    tempDirectories.splice(0).map((directory) =>
      rm(directory, { recursive: true, force: true })
    )
  );
});

describe("parseCli", () => {
  it("defaults to bootstrap and all supported targets", () => {
    expect(parseCli([])).toEqual({
      command: "bootstrap",
      targets: ["codex", "claude", "opencode", "gemini", "hermes", "cursor"],
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

  it("supports overriding the effective home directory", () => {
    expect(
      parseCli(["bootstrap", "--target", "claude", "--home", "/tmp/test-home"])
    ).toEqual({
      command: "bootstrap",
      targets: ["claude"],
      dryRun: false,
      json: false,
      help: false,
      homeDir: "/tmp/test-home"
    });
  });

  it("supports verification commands", () => {
    expect(parseCli(["list", "--target", "gemini", "--json"])).toEqual({
      command: "list",
      targets: ["gemini"],
      json: true,
      help: false
    });
    expect(parseCli(["inspect", "--targets", "codex,claude"])).toEqual({
      command: "inspect",
      targets: ["codex", "claude"],
      json: false,
      help: false
    });
    expect(parseCli(["doctor"])).toEqual({
      command: "doctor",
      targets: ["codex", "claude", "opencode", "gemini", "hermes", "cursor"],
      json: false,
      help: false
    });
  });

  it("rejects unsupported targets and invalid dry-run usage", () => {
    expect(() => parseCli(["bootstrap", "--target", "bogus"])).toThrow(
      "Unsupported target: bogus"
    );
    expect(() => parseCli(["list", "--dry-run"])).toThrow(
      "Unsupported argument for list: --dry-run"
    );
  });
});

describe("runCli", () => {
  it("renders a readable bootstrap preview", async () => {
    const fixture = await createBootstrapFixture();

    await withFixtureEnv(fixture, async () => {
      const result = await runCli(["--dry-run", "--target", "claude"]);

      expect(result.exitCode).toBe(0);
      expect(result.stderr).toBe("");
      expect(result.stdout).toContain("AImagician Skills bootstrap");
      expect(result.stdout).toContain("Mode: dry-run");
      expect(result.stdout).toContain("Targets: claude");
      expect(result.stdout).toContain("Planned assets: 1");
    });
  }, 10000);

  it("renders list, inspect, and doctor output from a fake home", async () => {
    const fixture = await createInspectionFixture();

    await withFixtureEnv(fixture, async () => {
      const listResult = await runCli(["list", "--targets", "codex,opencode"]);
      expect(listResult.exitCode).toBe(0);
      expect(listResult.stdout).toContain("AImagician Skills list");
      expect(listResult.stdout).toContain("daily-ops");
      expect(listResult.stdout).toContain("audit-helper");
      expect(listResult.stdout).toContain("command sources: none");

      const inspectResult = await runCli(["inspect", "--target", "gemini"]);
      expect(inspectResult.exitCode).toBe(0);
      expect(inspectResult.stdout).toContain("AImagician Skills inspect");
      expect(inspectResult.stdout).toContain(".gemini");
      expect(inspectResult.stdout).toContain("command installs: gsd");

      const doctorResult = await runCli(["doctor", "--json", "--targets", "codex,opencode"]);
      expect(doctorResult.exitCode).toBe(0);
      expect(JSON.parse(doctorResult.stdout)).toMatchObject({
        command: "doctor",
        status: "healthy",
        targets: [
          { target: "codex", status: "healthy", managedCount: 1, commandCount: 0 },
          { target: "opencode", status: "healthy", managedCount: 1, commandCount: 0 }
        ]
      });
    });
  });

  it("renders help output when requested", async () => {
    const result = await runCli(["--help"]);

    expect(result.exitCode).toBe(0);
    expect(result.stdout).toContain("Usage: aimagician-skills");
    expect(result.stdout).toContain("list");
    expect(result.stdout).toContain("doctor");
    expect(result.stdout).toContain("--home");
  });
});

async function createInspectionFixture() {
  const root = await mkdtemp(join(tmpdir(), "aimagician-cli-"));
  tempDirectories.push(root);

  const homeDir = join(root, "home");
  const workspaceRoot = join(root, "workspace");
  const codexSkillDir = join(homeDir, ".codex", "skills", "daily-ops");
  const opencodePluginPath = join(homeDir, ".config", "opencode", "plugins", "audit-helper.ts");
  const geminiExtensionDir = join(homeDir, ".gemini", "extensions", "gsd");

  await mkdir(codexSkillDir, { recursive: true });
  await mkdir(join(homeDir, ".config", "opencode", "plugins"), { recursive: true });
  await mkdir(geminiExtensionDir, { recursive: true });
  await mkdir(workspaceRoot, { recursive: true });

  await writeFile(join(codexSkillDir, "SKILL.md"), "# Daily Ops\n", "utf8");
  await writeFile(opencodePluginPath, "export default async function auditHelper() {}\n", "utf8");
  await writeFile(join(geminiExtensionDir, "gemini-extension.json"), "{\"name\":\"gsd\",\"version\":\"1.0.0\"}\n", "utf8");
  await writeFile(
    join(workspaceRoot, "manifest.json"),
    JSON.stringify(
      {
        version: 3,
        updatedAt: "2026-03-14T11:20:00Z",
        selectedTargets: ["codex", "opencode", "gemini"],
        assets: [
          { id: "daily-ops", origin: "owned", kind: "skill", selectedTargets: ["codex"] },
          { id: "audit-helper", origin: "external", kind: "plugin", sourceId: "plugin-repo", selectedTargets: ["opencode"] },
          { id: "gsd", origin: "external", kind: "skill", sourceId: "external-skills", selectedTargets: ["gemini"] }
        ],
        commandInstalls: [
          {
            sourceId: "gsd",
            assetIds: ["gsd"],
            targets: ["gemini"],
            command: "npx get-shit-done-cc --all --global"
          }
        ],
        managedInstalls: [
          {
            target: "codex",
            assetId: "daily-ops",
            kind: "skill",
            origin: "owned",
            destinationPath: codexSkillDir,
            installType: "directory",
            installArea: "skills"
          },
          {
            target: "opencode",
            assetId: "audit-helper",
            kind: "plugin",
            origin: "external",
            sourceId: "plugin-repo",
            destinationPath: opencodePluginPath,
            installType: "file",
            installArea: "plugins"
          },
          {
            target: "gemini",
            assetId: "gsd",
            kind: "skill",
            origin: "external",
            sourceId: "external-skills",
            destinationPath: geminiExtensionDir,
            installType: "directory",
            installArea: "extensions"
          }
        ]
      },
      null,
      2
    ),
    "utf8"
  );

  return {
    homeDir,
    workspaceRoot,
    configHome: join(homeDir, ".config")
  };
}

async function createBootstrapFixture() {
  const root = await mkdtemp(join(tmpdir(), "aimagician-cli-bootstrap-"));
  tempDirectories.push(root);

  const homeDir = join(root, "home");
  const workspaceRoot = join(root, "workspace");
  const ownedSkillsRoot = join(root, "fixture", "skills", "owned");
  const skillsRoot = join(root, "fixture", "catalog", "skills");
  const pluginsRoot = join(root, "fixture", "catalog", "plugins");
  const externalRepoRoot = join(root, "fixture", "external-source");

  await mkdir(workspaceRoot, { recursive: true });
  await mkdir(ownedSkillsRoot, { recursive: true });
  await mkdir(skillsRoot, { recursive: true });
  await mkdir(pluginsRoot, { recursive: true });
  await mkdir(join(externalRepoRoot, "skills", "gsd"), { recursive: true });

  await writeFile(join(externalRepoRoot, "skills", "gsd", "SKILL.md"), "# GSD\n", "utf8");
  await writeFile(
    join(skillsRoot, "skills.yaml"),
    [
      "sources:",
      "  - id: external-skills",
      "    type: github",
      "    targets:",
      "      include:",
      "        - claude",
      "    github:",
      "      repo: aimagician/external-skills",
      "      path: skills"
    ].join("\n"),
    "utf8"
  );
  await writeFile(join(pluginsRoot, "plugins.yaml"), "sources: []\n", "utf8");

  return {
    homeDir,
    workspaceRoot,
    configHome: join(homeDir, ".config"),
    ownedSkillsRoot,
    skillsRoot,
    pluginsRoot,
    githubRepoOverrides: JSON.stringify({
      "aimagician/external-skills": externalRepoRoot
    })
  };
}

async function withFixtureEnv<T>(
  fixture: {
    homeDir: string;
    workspaceRoot: string;
    configHome: string;
    ownedSkillsRoot?: string;
    skillsRoot?: string;
    pluginsRoot?: string;
    githubRepoOverrides?: string;
  },
  callback: () => Promise<T>
): Promise<T> {
  const original = {
    AIMAGICIAN_HOME_DIR: process.env.AIMAGICIAN_HOME_DIR,
    AIMAGICIAN_CONFIG_HOME: process.env.AIMAGICIAN_CONFIG_HOME,
    AIMAGICIAN_WORKSPACE_ROOT: process.env.AIMAGICIAN_WORKSPACE_ROOT,
    AIMAGICIAN_OWNED_SKILLS_ROOT: process.env.AIMAGICIAN_OWNED_SKILLS_ROOT,
    AIMAGICIAN_SKILLS_CATALOG_ROOT: process.env.AIMAGICIAN_SKILLS_CATALOG_ROOT,
    AIMAGICIAN_PLUGINS_CATALOG_ROOT: process.env.AIMAGICIAN_PLUGINS_CATALOG_ROOT,
    AIMAGICIAN_GITHUB_REPO_OVERRIDES: process.env.AIMAGICIAN_GITHUB_REPO_OVERRIDES
  };

  process.env.AIMAGICIAN_HOME_DIR = fixture.homeDir;
  process.env.AIMAGICIAN_CONFIG_HOME = fixture.configHome;
  process.env.AIMAGICIAN_WORKSPACE_ROOT = fixture.workspaceRoot;
  if (fixture.ownedSkillsRoot) {
    process.env.AIMAGICIAN_OWNED_SKILLS_ROOT = fixture.ownedSkillsRoot;
  }
  if (fixture.skillsRoot) {
    process.env.AIMAGICIAN_SKILLS_CATALOG_ROOT = fixture.skillsRoot;
  }
  if (fixture.pluginsRoot) {
    process.env.AIMAGICIAN_PLUGINS_CATALOG_ROOT = fixture.pluginsRoot;
  }
  if (fixture.githubRepoOverrides) {
    process.env.AIMAGICIAN_GITHUB_REPO_OVERRIDES = fixture.githubRepoOverrides;
  }

  try {
    return await callback();
  } finally {
    restoreEnv("AIMAGICIAN_HOME_DIR", original.AIMAGICIAN_HOME_DIR);
    restoreEnv("AIMAGICIAN_CONFIG_HOME", original.AIMAGICIAN_CONFIG_HOME);
    restoreEnv("AIMAGICIAN_WORKSPACE_ROOT", original.AIMAGICIAN_WORKSPACE_ROOT);
    restoreEnv("AIMAGICIAN_OWNED_SKILLS_ROOT", original.AIMAGICIAN_OWNED_SKILLS_ROOT);
    restoreEnv("AIMAGICIAN_SKILLS_CATALOG_ROOT", original.AIMAGICIAN_SKILLS_CATALOG_ROOT);
    restoreEnv("AIMAGICIAN_PLUGINS_CATALOG_ROOT", original.AIMAGICIAN_PLUGINS_CATALOG_ROOT);
    restoreEnv("AIMAGICIAN_GITHUB_REPO_OVERRIDES", original.AIMAGICIAN_GITHUB_REPO_OVERRIDES);
  }
}

function restoreEnv(name: string, value: string | undefined) {
  if (value === undefined) {
    delete process.env[name];
    return;
  }

  process.env[name] = value;
}
