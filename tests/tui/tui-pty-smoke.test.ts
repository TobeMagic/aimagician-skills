import { constants } from "node:fs";
import { access, mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync, spawn, spawnSync } from "node:child_process";
import { afterEach, describe, expect, it } from "vitest";

const tempDirectories: string[] = [];

afterEach(async () => {
  await Promise.allSettled(
    tempDirectories.splice(0).map((directory) =>
      rm(directory, { recursive: true, force: true })
    )
  );
});

describe("dashboard PTY smoke", () => {
  const runIfPtyAvailable = process.platform === "win32" || !hasScriptCommand() ? it.skip : it;

  runIfPtyAvailable("opens the dashboard and resets cursor skills end-to-end", async () => {
    const fixture = await createTuiFixture();

    execFileSync("npm", ["run", "build"], {
      cwd: process.cwd(),
      stdio: "ignore"
    });

    const output = await runDashboardInPty(fixture, [
      { input: "r", delayAfter: 2_500 },
      { input: "q", delayAfter: 0 }
    ]);

    expect(output).toContain("Skillbee");
    await expectMissing(join(fixture.homeDir, ".cursor", "skills", "old-global", "SKILL.md"));
    await expectMissing(join(fixture.projectDir, ".cursor", "skills", "old-project", "SKILL.md"));
    await expectPath(join(fixture.homeDir, ".cursor", "skills", "demo-skill", "SKILL.md"));
    await expectPath(join(fixture.projectDir, ".cursor", "skills", "demo-skill", "SKILL.md"));
    await expectMissing(join(fixture.projectDir, ".cursor", "skills", "retired-skill", "SKILL.md"));
  }, 120_000);

  runIfPtyAvailable("navigates the skill list without recursive render failure", async () => {
    const fixture = await createTuiFixture();

    execFileSync("npm", ["run", "build"], {
      cwd: process.cwd(),
      stdio: "ignore"
    });

    const output = await runDashboardInPty(fixture, [
      { input: "\x1b[B", delayAfter: 150 },
      { input: "\x1b[B", delayAfter: 150 },
      { input: "\x1b[A", delayAfter: 150 },
      { input: "q", delayAfter: 0 }
    ]);

    expect(output).toContain("Skillbee");
    expect(output).not.toContain("Maximum call stack size exceeded");
  }, 120_000);
});

async function createTuiFixture() {
  const root = await mkdtemp(join(tmpdir(), "skillbee-tui-"));
  tempDirectories.push(root);

  const projectDir = join(root, "project");
  const homeDir = join(root, "home");
  const ownedSkillsRoot = join(root, "fixture", "skills", "owned");
  const archivedSkillsRoot = join(root, "fixture", "skills", "archived");
  const skillsRoot = join(root, "fixture", "catalog", "skills");
  const pluginsRoot = join(root, "fixture", "catalog", "plugins");
  const taxonomyPath = join(root, "fixture", "catalog", "taxonomy.yaml");
  const globalStaleSkill = join(homeDir, ".cursor", "skills", "old-global");
  const projectStaleSkill = join(projectDir, ".cursor", "skills", "old-project");

  await mkdir(join(ownedSkillsRoot, "demo-skill"), { recursive: true });
  await mkdir(join(ownedSkillsRoot, "second-skill"), { recursive: true });
  await mkdir(join(archivedSkillsRoot, "retired-skill"), { recursive: true });
  await mkdir(skillsRoot, { recursive: true });
  await mkdir(pluginsRoot, { recursive: true });
  await mkdir(globalStaleSkill, { recursive: true });
  await mkdir(projectStaleSkill, { recursive: true });

  await writeFile(join(ownedSkillsRoot, "demo-skill", "SKILL.md"), "# Demo Skill\n", "utf8");
  await writeFile(join(ownedSkillsRoot, "second-skill", "SKILL.md"), "# Second Skill\n", "utf8");
  await writeFile(join(archivedSkillsRoot, "retired-skill", "SKILL.md"), "# Retired Skill\n", "utf8");
  await writeFile(join(globalStaleSkill, "SKILL.md"), "# Old Global\n", "utf8");
  await writeFile(join(projectStaleSkill, "SKILL.md"), "# Old Project\n", "utf8");
  await writeFile(join(skillsRoot, "skills.yaml"), "sources: []\n", "utf8");
  await writeFile(join(pluginsRoot, "plugins.yaml"), "sources: []\n", "utf8");
  await writeFile(
    taxonomyPath,
    [
      "groups:",
      "  - id: coding",
      "    label: Coding",
      "skills:",
      "  demo-skill:",
      "    group: coding",
      "    tags: [demo]",
      "  second-skill:",
      "    group: coding",
      "    tags: [demo]"
    ].join("\n"),
    "utf8"
  );

  return {
    root,
    projectDir,
    homeDir,
    ownedSkillsRoot,
    archivedSkillsRoot,
    skillsRoot,
    pluginsRoot,
    taxonomyPath
  };
}

async function runDashboardInPty(
  fixture: Awaited<ReturnType<typeof createTuiFixture>>,
  actions: Array<{ input: string; delayAfter: number }>
): Promise<string> {
  const command = [
    shellQuote(process.execPath),
    "dist/cli/index.js",
    "--target",
    "cursor",
    "--project",
    shellQuote(fixture.projectDir)
  ].join(" ");
  const child = spawn("script", ["-qfec", command, "/dev/null"], {
    cwd: process.cwd(),
    env: {
      ...process.env,
      TERM: "xterm-256color",
      AIMAGICIAN_HOME_DIR: fixture.homeDir,
      AIMAGICIAN_CONFIG_HOME: join(fixture.homeDir, ".config"),
      AIMAGICIAN_STATE_BASE_DIR: join(fixture.homeDir, ".local", "state"),
      AIMAGICIAN_WORKSPACE_ROOT: join(fixture.root, "global-workspace"),
      AIMAGICIAN_OWNED_SKILLS_ROOT: fixture.ownedSkillsRoot,
      AIMAGICIAN_ARCHIVED_SKILLS_ROOT: fixture.archivedSkillsRoot,
      AIMAGICIAN_SKILLS_CATALOG_ROOT: fixture.skillsRoot,
      AIMAGICIAN_PLUGINS_CATALOG_ROOT: fixture.pluginsRoot,
      AIMAGICIAN_TAXONOMY_PATH: fixture.taxonomyPath
    },
    stdio: ["pipe", "pipe", "pipe"]
  });
  let output = "";

  child.stdout.on("data", (chunk) => {
    output += chunk.toString();
  });
  child.stderr.on("data", (chunk) => {
    output += chunk.toString();
  });

  await delay(1_000);
  for (const action of actions) {
    child.stdin.write(action.input);
    if (action.delayAfter > 0) {
      await delay(action.delayAfter);
    }
  }
  child.stdin.end();

  const exitCode = await new Promise<number | null>((resolve) => {
    child.on("exit", resolve);
  });

  expect(exitCode, output).toBe(0);
  return output;
}

function hasScriptCommand(): boolean {
  return spawnSync("script", ["--version"], { stdio: "ignore" }).status === 0;
}

function shellQuote(value: string): string {
  return `'${value.replace(/'/g, "'\\''")}'`;
}

function delay(milliseconds: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function expectPath(path: string): Promise<void> {
  await access(path, constants.F_OK);
}

async function expectMissing(path: string): Promise<void> {
  await expect(access(path, constants.F_OK)).rejects.toMatchObject({ code: "ENOENT" });
}
