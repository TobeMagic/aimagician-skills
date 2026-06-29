import { constants } from "node:fs";
import { access, mkdir, mkdtemp, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { runCli } from "../../src/cli/index";

const tempDirectories: string[] = [];

afterEach(async () => {
  await Promise.allSettled(
    tempDirectories.splice(0).map((directory) =>
      rm(directory, { recursive: true, force: true })
    )
  );
});

describe("v4 Skillbird acceptance", () => {
  it("previews then applies a global build category bundle in an isolated home", async () => {
    const root = await createTempRoot();
    const homeDir = join(root, "home");
    await mkdir(homeDir, { recursive: true });

    const preview = await runCli([
      "install",
      "--category",
      "build",
      "--scope",
      "global",
      "--target",
      "claude",
      "--home",
      homeDir,
      "--dry-run",
      "--json"
    ]);

    expect(preview.exitCode).toBe(0);
    const previewJson = JSON.parse(preview.stdout) as InstallJson;
    expect(previewJson.scope).toBe("global");
    expect(previewJson.dryRun).toBe(true);
    expect(installedIds(previewJson)).toEqual(expect.arrayContaining([
      "aimagician-superpower",
      "skill-creator",
      "webapp-testing"
    ]));
    expect(installedIds(previewJson)).not.toContain("code-guidelines");
    expect(previewJson.skipped).toContainEqual({
      assetId: "playwright-skill",
      reason: "source-default-disabled"
    });
    await expectMissing(join(homeDir, ".claude", "skills", "aimagician-superpower", "SKILL.md"));

    const applied = await runCli([
      "install",
      "--category",
      "build",
      "--scope",
      "global",
      "--target",
      "claude",
      "--home",
      homeDir,
      "--json"
    ]);

    expect(applied.exitCode).toBe(0);
    const appliedJson = JSON.parse(applied.stdout) as InstallJson;
    expect(appliedJson.dryRun).toBe(false);
    expect(installedIds(appliedJson)).toEqual(expect.arrayContaining([
      "aimagician-superpower",
      "skill-creator",
      "webapp-testing"
    ]));
    expect(installedIds(appliedJson)).not.toContain("code-guidelines");
    await expectPath(join(homeDir, ".claude", "skills", "aimagician-superpower", "SKILL.md"));
    await expectPath(join(homeDir, ".local", "state", "aimagician-superpower", "manifest.json"));
  });

  it("previews then applies a project documents category bundle", async () => {
    const root = await createTempRoot();
    const homeDir = join(root, "home");
    const projectDir = join(root, "project");
    await mkdir(homeDir, { recursive: true });
    await mkdir(projectDir, { recursive: true });

    const preview = await runCli([
      "install",
      "--category",
      "documents",
      "--scope",
      "project",
      "--project",
      projectDir,
      "--target",
      "claude",
      "--home",
      homeDir,
      "--dry-run",
      "--json"
    ]);

    expect(preview.exitCode).toBe(0);
    const previewJson = JSON.parse(preview.stdout) as InstallJson;
    expect(previewJson.scope).toBe("project");
    expect(previewJson.workspaceRoot).toBe(join(projectDir, ".skillbird"));
    expect(previewJson.dryRun).toBe(true);
    expect(installedIds(previewJson)).toEqual(expect.arrayContaining([
      "docx",
      "pdf",
      "pptx",
      "xlsx"
    ]));
    await expectMissing(join(projectDir, ".claude", "skills", "docx", "SKILL.md"));

    const applied = await runCli([
      "install",
      "--category",
      "documents",
      "--scope",
      "project",
      "--project",
      projectDir,
      "--target",
      "claude",
      "--home",
      homeDir,
      "--json"
    ]);

    expect(applied.exitCode).toBe(0);
    const appliedJson = JSON.parse(applied.stdout) as InstallJson;
    expect(appliedJson.dryRun).toBe(false);
    expect(installedIds(appliedJson)).toEqual(expect.arrayContaining([
      "docx",
      "pdf",
      "pptx",
      "xlsx"
    ]));
    await expectPath(join(projectDir, ".claude", "skills", "docx", "SKILL.md"));
    await expectPath(join(projectDir, ".skillbird", "manifest.json"));
  });

  it("previews the active design bundle without archived design experiments", async () => {
    const root = await createTempRoot();
    const homeDir = join(root, "home");
    await mkdir(homeDir, { recursive: true });

    const preview = await runCli([
      "install",
      "--category",
      "design",
      "--scope",
      "global",
      "--target",
      "codex",
      "--home",
      homeDir,
      "--dry-run",
      "--json"
    ]);

    expect(preview.exitCode).toBe(0);
    const previewJson = JSON.parse(preview.stdout) as InstallJson;
    expect(installedIds(previewJson)).toEqual(expect.arrayContaining([
      "interface-design",
      "modelscope_imagegen"
    ]));
    expect(installedIds(previewJson)).not.toContain("cloudflare-image-gen");
    expect(installedIds(previewJson)).not.toContain("design-md-brand-router");
    expect(installedIds(previewJson)).not.toContain("multilingual-diversity-loop");
  });

  it("previews the operate bundle with the CLI agent orchestrator", async () => {
    const root = await createTempRoot();
    const homeDir = join(root, "home");
    await mkdir(homeDir, { recursive: true });

    const preview = await runCli([
      "install",
      "--category",
      "operate",
      "--scope",
      "project",
      "--target",
      "codex",
      "--home",
      homeDir,
      "--dry-run",
      "--json"
    ]);

    expect(preview.exitCode).toBe(0);
    const previewJson = JSON.parse(preview.stdout) as InstallJson;
    expect(installedIds(previewJson)).toEqual(expect.arrayContaining([
      "cli-agent-orchestrator",
      "composio-tool-router",
      "gcloud-ops-workflow",
      "github-pr-workflow",
      "linear-issue-workflow",
      "parallel-worktree-pr-flow"
    ]));
    expect(installedIds(previewJson)).not.toContain("agentic-repo-explorer");
  });

  it("keeps PTY smoke and category styling coverage tied to Skillbird", async () => {
    const tuiSmoke = await readFile("tests/tui/tui-pty-smoke.test.ts", "utf8");
    const dashboard = await readFile("src/tui/dashboard.ts", "utf8");

    expect(tuiSmoke).toContain("runDashboardInPty");
    expect(tuiSmoke).toContain("Skillbird");
    expect(dashboard).toContain("Categories");
  });
});

interface InstallJson {
  scope: "global" | "project";
  workspaceRoot: string;
  dryRun: boolean;
  installed: Array<{ assetId: string }>;
  skipped: Array<{ assetId: string; reason: string }>;
}

async function createTempRoot(): Promise<string> {
  const root = await mkdtemp(join(tmpdir(), "skillbird-v4-"));
  tempDirectories.push(root);
  return root;
}

function installedIds(result: InstallJson): string[] {
  return result.installed.map((install) => install.assetId).sort();
}

async function expectPath(path: string): Promise<void> {
  await access(path, constants.F_OK);
}

async function expectMissing(path: string): Promise<void> {
  await expect(access(path, constants.F_OK)).rejects.toMatchObject({ code: "ENOENT" });
}
