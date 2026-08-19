import { execFile } from "node:child_process";
import { mkdtemp, readdir, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { afterEach, describe, expect, it } from "vitest";

const execFileAsync = promisify(execFile);
const root = process.cwd();
const ownedRoot = join(root, "skills", "owned");
const archivedRoot = join(root, "skills", "archived");
const registryScript = join(ownedRoot, "agent-workstream-orchestrator", "scripts", "workstream_registry.py");
const temporary: string[] = [];

afterEach(async () => {
  await Promise.allSettled(temporary.splice(0).map((path) => rm(path, { recursive: true, force: true })));
});

describe("runtime-pure Skill architecture", () => {
  it("keeps eval corpora outside every active Skill package", async () => {
    const ids = await readdir(ownedRoot);
    for (const id of ids) {
      await expect(readdir(join(ownedRoot, id, "evals"))).rejects.toThrow();
    }
    expect(await readdir(join(root, "quality", "skill-evals"))).toEqual(
      expect.arrayContaining(["aimagician-superpower", "aimagician-superpower-slim-2026-08-13", "skill-optimizer", "pptx-studio"])
    );
  });

  it("archives obsolete Skills and removes their active routing", async () => {
    const archived = ["pptx", "modelscope_imagegen", "mcp-builder", "linear-issue-workflow", "cli-agent-delegator"];
    const owned = await readdir(ownedRoot);
    const taxonomy = await readFile(join(root, "catalog", "taxonomy.yaml"), "utf8");
    for (const id of archived) {
      expect(owned).not.toContain(id);
      expect(await readFile(join(archivedRoot, id, "SKILL.md"), "utf8")).toContain("name:");
      expect(taxonomy).not.toMatch(new RegExp(`^  ${id}:`, "m"));
    }
  });

  it("routes memory and independent sessions through progressive capability modules", async () => {
    const engineering = await readFile(join(ownedRoot, "aimagician-superpower", "SKILL.md"), "utf8");
    const capabilityIndex = await readFile(join(ownedRoot, "aimagician-superpower", "references", "capabilities", "index.md"), "utf8");
    const orchestration = await readFile(join(ownedRoot, "agent-workstream-orchestrator", "SKILL.md"), "utf8");
    expect(capabilityIndex).toContain("project-memory.md");
    expect(engineering).toContain(".planning/memory/");
    expect(engineering).toContain("conditional routes, never default preflight");
    expect(orchestration).toContain("Route By Coupling, Risk, And Cost");
    expect(orchestration).toContain("Session is silent but still emits progress events");
    expect(orchestration).toContain("INTEGRATED");
    expect(orchestration).not.toContain("GSD");
    expect(orchestration).not.toContain("provider lane");
  });

  it("previews, writes, validates, and lists a bounded workstream registry", async () => {
    const project = await mkdtemp(join(tmpdir(), "workstream-registry-"));
    temporary.push(project);

    const preview = await execFileAsync("python3", [registryScript, "init", "--root", project]);
    expect(preview.stdout).toContain("PREVIEW");

    await execFileAsync("python3", [registryScript, "init", "--root", project, "--write"]);
    await execFileAsync("python3", [
      registryScript,
      "add",
      "--root",
      project,
      "--id",
      "test-report",
      "--objective",
      "Run focused tests and report evidence",
      "--provider",
      "opencode",
      "--mode",
      "read-only",
      "--write"
    ]);
    const validation = await execFileAsync("python3", [registryScript, "validate", "--root", project]);
    const listing = await execFileAsync("python3", [registryScript, "list", "--root", project]);
    expect(validation.stdout).toContain("VALID");
    expect(listing.stdout).toContain("test-report\tplanned\tread-only\topencode");
  });
});
