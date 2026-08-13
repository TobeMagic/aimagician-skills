import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const skillRoot = join(process.cwd(), "skills", "owned", "aimagician-superpower");
const moduleNames = [
  "intake-and-boundary.md",
  "state-and-continuity.md",
  "project-memory.md",
  "spec-driven-development.md",
  "research-and-discovery.md",
  "engineering-exploration.md",
  "prototyping-and-progressive-discovery.md",
  "ideation-and-scope.md",
  "engineering-design.md",
  "planning-modes.md",
  "agent-orchestration.md",
  "execution-modes.md",
  "engineering-delivery.md",
  "local-first-delivery.md",
  "debugging-and-forensics.md",
  "engineering-review.md",
  "verification-and-uat.md",
  "audit-and-closure.md",
  "domain-gates.md"
];

describe("aimagician-superpower lightweight control plane", () => {
  it("keeps default delivery concise and expands only by risk", async () => {
    const skill = await readFile(join(skillRoot, "SKILL.md"), "utf8");
    expect(skill.split("\n").length).toBeLessThanOrEqual(180);
    expect(skill).toContain("smallest reliable route");
    expect(skill).toContain("Do not force planning records, a wiki, a worktree, external agents, or an independent audit on a `Quick` task.");
    expect(skill).toContain("Quick and Standard");
    expect(skill).toContain("High, phase, milestone, or deployable work");
    expect(skill).toContain("Requirement Evidence Map");
    expect(skill).toContain("CHECKPOINT - pre-delivery");
    expect(skill).not.toContain("preferred_companions:");
  });

  it("preserves every specialized capability behind the progressive-disclosure index", async () => {
    const index = await readFile(join(skillRoot, "references", "capabilities", "index.md"), "utf8");
    for (const moduleName of moduleNames) {
      expect(index).toContain(`](${moduleName})`);
    }
  });

  it("keeps a deterministic pressure-scenario contract outside runtime skill content", async () => {
    const path = join(process.cwd(), "quality", "skill-evals", "aimagician-superpower-slim-2026-08-13", "evals.json");
    const evaluation = JSON.parse(await readFile(path, "utf8")) as { evaluation_type: string; scenarios: Array<{ id: string; expected: string[]; forbidden: string[] }> };
    expect(evaluation.evaluation_type).toBe("deterministic-routing-regression");
    expect(evaluation.scenarios).toHaveLength(5);
    for (const scenario of evaluation.scenarios) {
      expect(scenario.expected.length).toBeGreaterThan(0);
      expect(scenario.forbidden.length).toBeGreaterThan(0);
    }
  });
});
