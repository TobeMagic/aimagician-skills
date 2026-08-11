import { execFile } from "node:child_process";
import { mkdtemp, readFile, realpath, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { afterEach, describe, expect, it } from "vitest";

const execFileAsync = promisify(execFile);
const tempDirectories: string[] = [];
const workflowScript = join(
  process.cwd(),
  "skills",
  "owned",
  "aimagician-superpower",
  "scripts",
  "workflow.mjs"
);
const bootstrapScript = join(
  process.cwd(),
  "skills",
  "owned",
  "agent-workstream-orchestrator",
  "scripts",
  "bootstrap_worktrees.py"
);

afterEach(async () => {
  await Promise.allSettled(
    tempDirectories.splice(0).map((directory) =>
      rm(directory, { recursive: true, force: true })
    )
  );
});

describe("agent workstream optional worktree integration", () => {
  it.skipIf(process.platform === "win32")(
    "automatically attaches new worktrees to local-private planning",
    async () => {
      const repository = await mkdtemp(join(tmpdir(), "parallel-planning-repo-"));
      const worktreeParent = await mkdtemp(join(tmpdir(), "parallel-planning-worktree-"));
      tempDirectories.push(repository, worktreeParent);
      await execFileAsync("git", ["init"], { cwd: repository });
      await execFileAsync("git", ["config", "user.name", "Parallel Test"], { cwd: repository });
      await execFileAsync("git", ["config", "user.email", "parallel@example.invalid"], { cwd: repository });
      await writeFile(join(repository, "README.md"), "# Fixture\n", "utf8");
      await execFileAsync("git", ["add", "README.md"], { cwd: repository });
      await execFileAsync("git", ["commit", "-m", "test: initialize"], { cwd: repository });
      const branch = (await execFileAsync("git", ["branch", "--show-current"], { cwd: repository })).stdout.trim();

      await execFileAsync(process.execPath, [
        workflowScript,
        "planning",
        "--project",
        repository,
        "--action",
        "init",
        "--mode",
        "local-private",
        "--write",
        "--format",
        "json"
      ]);

      const target = join(worktreeParent, "lane-one");
      const registry = join(repository, "workstreams.json");
      await writeFile(registry, JSON.stringify({
        base_branch: branch,
        default_bootstrap_statuses: ["planned"],
        shared_surfaces: [".planning/**"],
        streams: [{
          id: "lane-one",
          label: "Lane One",
          mode: "worktree",
          group: "test",
          branch: "test/lane-one",
          worktree: target,
          status: "planned",
          priority: 1,
          write_scope: ["src/lane-one/**"],
          manifest_path: "manifests/lane-one.json"
        }]
      }), "utf8");

      const result = await execFileAsync("python3", [
        bootstrapScript,
        "--registry-file",
        registry,
        "--repo-root",
        repository,
        "--execute"
      ], { cwd: repository });

      expect(result.stdout).toContain("attached shared local-private planning");
      expect(await realpath(join(target, ".planning"))).toBe(await realpath(join(repository, ".planning")));
      expect(await readFile(join(repository, ".git", "info", "exclude"), "utf8")).toContain("/.planning");
    },
    15000
  );
});
