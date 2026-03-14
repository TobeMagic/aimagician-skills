import { execFile } from "node:child_process";
import { access, mkdtemp, mkdir, readFile, writeFile } from "node:fs/promises";
import { constants } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { afterEach, describe, expect, it } from "vitest";

const execFileAsync = promisify(execFile);
const tempDirectories: string[] = [];

afterEach(async () => {
  const { rm } = await import("node:fs/promises");
  await Promise.allSettled(
    tempDirectories.splice(0).map((directory) =>
      rm(directory, { recursive: true, force: true })
    )
  );
});

describe("bootstrap package smoke", () => {
  it("builds, packs, and runs the compiled bootstrap CLI in an isolated workspace", async () => {
    const workspaceRoot = await mkdtemp(join(tmpdir(), "aimagician-smoke-"));
    const homeDir = join(workspaceRoot, "home");
    const fixture = await createSmokeFixture(workspaceRoot);
    tempDirectories.push(workspaceRoot);

    await runPackageCommand("run build");
    await runPackageCommand("pack --dry-run");

    const { stdout } = await execFileAsync(
      process.execPath,
      ["dist/cli/index.js", "bootstrap", "--target", "claude", "--json"],
      {
        cwd: process.cwd(),
        env: {
          ...process.env,
          AIMAGICIAN_WORKSPACE_ROOT: workspaceRoot,
          AIMAGICIAN_HOME_DIR: homeDir,
          AIMAGICIAN_CONFIG_HOME: join(homeDir, ".config"),
          AIMAGICIAN_OWNED_SKILLS_ROOT: fixture.ownedSkillsRoot,
          AIMAGICIAN_SKILLS_CATALOG_ROOT: fixture.skillsRoot,
          AIMAGICIAN_PLUGINS_CATALOG_ROOT: fixture.pluginsRoot,
          AIMAGICIAN_GITHUB_REPO_OVERRIDES: JSON.stringify({
            "aimagician/external-skills": fixture.externalRepoRoot
          })
        }
      }
    );

    const result = JSON.parse(stdout) as {
      mode: string;
      targets: string[];
      workspaceRoot: string;
      assetCount: number;
      changed: boolean;
      targetReports: Array<{ target: string; status: string; skillsDir?: string }>;
    };
    const manifestPath = join(workspaceRoot, "manifest.json");
    const claudeSkillPath = join(homeDir, ".claude", "skills", "gsd", "SKILL.md");

    expect(result.mode).toBe("apply");
    expect(result.targets).toEqual(["claude"]);
    expect(result.workspaceRoot).toBe(workspaceRoot);
    expect(result.assetCount).toBeGreaterThan(0);
    expect(result.changed).toBe(true);
    expect(result.targetReports).toMatchObject([
      {
        target: "claude",
        status: "synced",
        skillsDir: join(homeDir, ".claude", "skills")
      }
    ]);
    await access(manifestPath, constants.F_OK);
    await access(claudeSkillPath, constants.F_OK);

    const manifest = JSON.parse(await readFile(manifestPath, "utf8")) as {
      assets: Array<{ id: string }>;
    };
    expect(manifest.assets.map((asset) => asset.id)).toContain("gsd");
  }, 30000);
});

async function runPackageCommand(command: string): Promise<void> {
  if (process.platform === "win32") {
    await execFileAsync(process.env.ComSpec ?? "cmd.exe", ["/d", "/s", "/c", `npm.cmd ${command}`], {
      cwd: process.cwd()
    });
    return;
  }

  await execFileAsync("sh", ["-lc", `npm ${command}`], {
    cwd: process.cwd()
  });
}

async function createSmokeFixture(root: string) {
  const ownedSkillsRoot = join(root, "fixture", "skills", "owned");
  const skillsRoot = join(root, "fixture", "catalog", "skills");
  const pluginsRoot = join(root, "fixture", "catalog", "plugins");
  const externalRepoRoot = join(root, "fixture", "external-source");

  await mkdir(join(ownedSkillsRoot, "daily-ops"), { recursive: true });
  await mkdir(join(skillsRoot), { recursive: true });
  await mkdir(join(pluginsRoot), { recursive: true });
  await mkdir(join(externalRepoRoot, "skills", "gsd"), { recursive: true });

  await writeFile(join(ownedSkillsRoot, "daily-ops", "SKILL.md"), "# Daily Ops\n", "utf8");
  await writeFile(join(externalRepoRoot, "skills", "gsd", "SKILL.md"), "# GSD\n", "utf8");
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
      "      - id: gsd",
      "        kind: skill",
      "        path: gsd/SKILL.md"
    ].join("\n"),
    "utf8"
  );
  await writeFile(join(pluginsRoot, "plugins.yaml"), "sources: []\n", "utf8");

  return {
    ownedSkillsRoot,
    skillsRoot,
    pluginsRoot,
    externalRepoRoot
  };
}
