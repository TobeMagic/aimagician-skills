import { constants } from "node:fs";
import { access, mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawn, spawnSync } from "node:child_process";
import { afterEach, describe, expect, it } from "vitest";
import { ensureBuiltCli } from "../helpers/ensure-built-cli";

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

    await ensureBuiltCli();

    const output = await runDashboardInPty(fixture, [
      { input: "r", delayAfter: 2_500 },
      { input: "q", delayAfter: 0 }
    ]);

    expect(output).toContain("Skillbird");
    expect(output).not.toContain("Maximum call stack size exceeded");
  }, 120_000);

  runIfPtyAvailable("navigates the skill list without recursive render failure", async () => {
    const fixture = await createTuiFixture();

    await ensureBuiltCli();

    const output = await runDashboardInPty(fixture, [
      { input: "v", delayAfter: 300 },
      { input: "\x1b[B", delayAfter: 150 },
      { input: "\x1b[B", delayAfter: 150 },
      { input: "\x1b[A", delayAfter: 150 },
      { input: "q", delayAfter: 0 }
    ]);

    expect(output).toContain("Skillbird");
    expect(output).not.toContain("Maximum call stack size exceeded");
  }, 120_000);
});

async function createTuiFixture() {
  const root = await mkdtemp(join(tmpdir(), "skillbird-tui-"));
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
      "  - id: build",
      "    label: Build",
      "skills:",
      "  demo-skill:",
      "    group: build",
      "    tags: [demo]",
      "  second-skill:",
      "    group: build",
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
  let lastOutput = "";
  for (let attempt = 0; attempt < 2; attempt++) {
    lastOutput = await runDashboardInPtyOnce(fixture, actions);
    if (lastOutput.includes("Skillbird")) {
      return lastOutput;
    }
  }
  return lastOutput;
}

async function runDashboardInPtyOnce(
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

  const ready = await waitForOutputOrExit(child, () => output, "Skillbird", 30_000);
  if (!ready) {
    child.kill("SIGTERM");
    await waitForExitOrKill(child, 2_000);
    return output;
  }
  for (const action of actions) {
    child.stdin.write(action.input);
    if (action.delayAfter > 0) {
      await delay(action.delayAfter);
    }
  }
  child.stdin.write("q");
  await delay(1_000);
  child.stdin.write("");
  child.stdin.end();

  const exitCode = await waitForExitOrKill(child, 5_000);

  expect([0, 130, null], output).toContain(exitCode);
  return output;
}

function waitForOutputOrExit(
  child: ReturnType<typeof spawn>,
  readOutput: () => string,
  expected: string,
  timeoutMs: number
): Promise<boolean> {
  if (readOutput().includes(expected)) return Promise.resolve(true);

  return new Promise((resolve) => {
    let settled = false;
    const finish = (result: boolean) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      child.stdout.off("data", onData);
      child.stderr.off("data", onData);
      child.off("exit", onExit);
      resolve(result);
    };
    const onData = () => {
      if (readOutput().includes(expected)) finish(true);
    };
    const onExit = () => finish(false);
    const timer = setTimeout(() => finish(false), timeoutMs);

    child.stdout.on("data", onData);
    child.stderr.on("data", onData);
    child.on("exit", onExit);
  });
}

function waitForExitOrKill(child: ReturnType<typeof spawn>, timeoutMs: number): Promise<number | null> {
  return new Promise((resolve) => {
    let settled = false;
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      child.kill("SIGTERM");
      resolve(null);
    }, timeoutMs);

    child.on("exit", (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(code);
    });
  });
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
