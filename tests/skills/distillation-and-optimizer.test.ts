import { execFileSync } from "node:child_process";
import { readFile, readdir } from "node:fs/promises";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const ownedRoot = join(process.cwd(), "skills", "owned");

async function runtimeFiles(root: string): Promise<string[]> {
  const found: string[] = [];
  async function walk(path: string): Promise<void> {
    for (const entry of await readdir(path, { withFileTypes: true })) {
      if (entry.name === "_external_repos") continue;
      const full = join(path, entry.name);
      if (entry.isDirectory()) await walk(full);
      else if (/\.(md|json|mjs|js|py|sh)$/.test(entry.name)) found.push(full);
    }
  }
  await walk(root);
  return found;
}

describe("distillation and Skill optimization capabilities", () => {
  const expected = [
    {
      id: "knowledge-distillation",
      category: "research",
      resources: [
        "references/distillation-method.md",
        "references/extractor-contracts.md",
        "references/output-contract.md",
        "assets/templates/source-overview.md",
        "assets/templates/generated-skill.md",
        "assets/templates/test-prompts.json",
        "scripts/validate-distillation.mjs",
        "evals/evals.json"
      ],
      scenarios: [
        "book-to-skills",
        "summary-non-trigger",
        "missing-source-gate"
      ]
    },
    {
      id: "perspective-distillation",
      category: "research",
      resources: [
        "references/research-and-synthesis.md",
        "references/agent-task-contracts.md",
        "references/perspective-skill-contract.md",
        "references/validation-and-update.md",
        "scripts/quality_check.py",
        "scripts/merge_research.py",
        "scripts/srt_to_transcript.py",
        "scripts/download_subtitles.sh",
        "evals/evals.json"
      ],
      scenarios: [
        "named-public-person",
        "need-diagnosis",
        "private-person-safety",
        "deceptive-impersonation-boundary"
      ]
    },
    {
      id: "skill-optimizer",
      category: "build",
      resources: [
        "references/rubric.md",
        "references/experiment-protocol.md",
        "references/runtime-neutrality.md",
        "scripts/audit-skill.mjs",
        "assets/templates/optimization-report.md",
        "assets/templates/experiment-record.json",
        "assets/templates/judge-contract.md",
        "evals/evals.json"
      ],
      scenarios: [
        "behavioral-skill-optimization",
        "dirty-worktree-audit",
        "new-skill-boundary",
        "ordinary-code-review-boundary"
      ]
    }
  ];

  it("ships complete source-neutral owned Skill packages", async () => {
    for (const item of expected) {
      const root = join(ownedRoot, item.id);
      const skill = await readFile(join(root, "SKILL.md"), "utf8");
      expect(skill).toContain(`name: ${item.id}`);
      expect(skill).toContain(`category: ${item.category}`);
      for (const resource of item.resources) {
        expect((await readFile(join(root, resource), "utf8")).trim().length).toBeGreaterThan(100);
      }

      const files = await runtimeFiles(root);
      const content = (await Promise.all(files.map((path) => readFile(path, "utf8")))).join("\n");
      for (const forbidden of [
        "alchaincyf",
        "kangarooking",
        "huashu-design",
        "darwin-skill",
        "cangjie-skill",
        "nuwa-skill"
      ]) {
        expect(content.toLowerCase()).not.toContain(forbidden);
      }
      expect(skill.toLowerCase()).not.toContain("npx skills add");

      if (item.scenarios.length > 0) {
        const evals = JSON.parse(await readFile(join(root, "evals", "evals.json"), "utf8")) as {
          scenarios: Array<{ id: string }>;
        };
        expect(evals.scenarios.map((scenario) => scenario.id)).toEqual(expect.arrayContaining(item.scenarios));
      }
    }
  });

  it("registers all three Skills in the six-category taxonomy", async () => {
    const taxonomy = await readFile(join(process.cwd(), "catalog", "taxonomy.yaml"), "utf8");
    expect(taxonomy).toMatch(/\n  knowledge-distillation:\n[\s\S]*?group: research/);
    expect(taxonomy).toMatch(/\n  perspective-distillation:\n[\s\S]*?group: research/);
    expect(taxonomy).toMatch(/\n  skill-optimizer:\n[\s\S]*?group: build/);
  });

  it("provides read-only executable audits and helper validation", () => {
    const optimizer = join(ownedRoot, "skill-optimizer", "scripts", "audit-skill.mjs");
    const help = execFileSync(process.execPath, [optimizer, "--help"], { encoding: "utf8" });
    expect(help).toContain("The command is read-only");
    expect(help).toContain("--effect-score");

    const audit = JSON.parse(execFileSync(process.execPath, [
      optimizer,
      "--skill", join(ownedRoot, "skill-optimizer"),
      "--format", "json"
    ], { encoding: "utf8" })) as {
      status: string;
      effectiveness: string;
      total_score: number | null;
      missing_resources: string[];
    };
    expect(audit).toMatchObject({
      status: "static_only",
      effectiveness: "NOT_RUN",
      total_score: null,
      missing_resources: []
    });

    const distillationHelp = execFileSync(process.execPath, [
      join(ownedRoot, "knowledge-distillation", "scripts", "validate-distillation.mjs"),
      "--help"
    ], { encoding: "utf8" });
    expect(distillationHelp).toContain("--root <distillation-root>");
  });
});
