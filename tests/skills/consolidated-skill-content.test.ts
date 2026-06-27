import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const ownedSkillsRoot = join(process.cwd(), "skills", "owned");
const docsRoot = join(process.cwd(), "docs");

describe("consolidated owned skill content", () => {
  it("keeps aimagician-superpower pure while preserving the full workflow contract", async () => {
    const skill = await readOwnedSkill("aimagician-superpower");
    const modulePaths = [
      "references/capabilities/intake-and-boundary.md",
      "references/capabilities/state-and-continuity.md",
      "references/capabilities/research-and-discovery.md",
      "references/capabilities/ideation-and-scope.md",
      "references/capabilities/planning-modes.md",
      "references/capabilities/execution-modes.md",
      "references/capabilities/verification-and-uat.md",
      "references/capabilities/audit-and-closure.md",
      "references/capabilities/domain-gates.md"
    ];
    const modules = await Promise.all(
      modulePaths.map((modulePath) =>
        readFile(join(ownedSkillsRoot, "aimagician-superpower", modulePath), "utf8")
      )
    );
    const runtimeContent = [skill, ...modules].join("\n");
    const mergeAudit = await readFile(
      join(docsRoot, "superpowers", "aimagician-superpower-capability-merge.md"),
      "utf8"
    );

    expect(runtimeContent).not.toContain("GSD");
    expect(runtimeContent).not.toContain("Superpowers");
    expect(runtimeContent).not.toContain("code-guidelines");
    expect(runtimeContent).not.toContain("Source Decisions");
    expect(runtimeContent).not.toContain("Consolidation Rules");
    expect(runtimeContent).not.toContain("Installing external workflow frameworks");
    expect(runtimeContent).not.toContain("auto-update hooks");
    expect(runtimeContent).not.toContain("installer");
    expect(runtimeContent).not.toContain("source-routing");

    expect(skill).toContain("Establish Target And Boundary");
    expect(skill).toContain("Discuss Baseline Requirements");
    expect(skill).toContain("Research And Brainstorm");
    expect(skill).toContain("Re-Discuss Boundaries And Assumptions");
    expect(skill).toContain("Plan");
    expect(skill).toContain("Execute");
    expect(skill).toContain("Verify");
    expect(skill).toContain("Audit");
    expect(skill).toContain("Handoff And Complete");
    expect(skill).toContain("CONTEXT.md");
    expect(skill).toContain("DISCUSSION-LOG.md");
    expect(skill).toContain("RESEARCH.md");
    expect(skill).toContain("VALIDATION.md");
    expect(skill).toContain("UAT.md");
    expect(skill).toContain("AUDIT.md");
    expect(skill).toContain("SUMMARY.md");
    expect(skill).toContain("Verification Dimensions");
    expect(skill).toContain("Research Rules");
    expect(skill).toContain("dependency waves");
    expect(skill).toContain("Execution Discipline");
    expect(skill).toContain("Surgical edits");
    expect(skill).toContain("Evidence-driven completion");

    for (const modulePath of modulePaths) {
      expect(skill).toContain(modulePath);
    }

    expect(modules.join("\n")).toContain("Phase plan");
    expect(modules.join("\n")).toContain("TDD plan");
    expect(modules.join("\n")).toContain("Parallel Worker Rules");
    expect(modules.join("\n")).toContain("UAT Scenarios");
    expect(modules.join("\n")).toContain("Audit Checklist");
    expect(modules.join("\n")).toContain("Debugging");
    expect(modules.join("\n")).toContain("Secrets And Environment");

    expect(mergeAudit).toContain("GSD command files: 67");
    expect(mergeAudit).toContain("GSD agent files: 33");
    expect(mergeAudit).toContain("GSD workflow files under `get-shit-done/workflows`: 107");
    expect(mergeAudit).toContain("Superpowers skill roots: 14");
    expect(mergeAudit).toContain("Superpowers `brainstorming`");
    expect(mergeAudit).toContain("GSD `plan-phase`");
    expect(mergeAudit).toContain("code-guidelines");
  });

  it("keeps brand DESIGN.md routing inside interface-design", async () => {
    const skill = await readOwnedSkill("interface-design");
    const brands = await readFile(
      join(ownedSkillsRoot, "interface-design", "references", "brand-design-md", "brands.json"),
      "utf8"
    );
    const appleDesign = await readFile(
      join(
        ownedSkillsRoot,
        "interface-design",
        "references",
        "brand-design-md",
        "design-md",
        "apple.DESIGN.md"
      ),
      "utf8"
    );

    expect(skill).toContain("Brand DESIGN.md Routing");
    expect(skill).toContain("references/brand-design-md/brands.json");
    expect(skill).toContain("references/brand-design-md/design-md/*.DESIGN.md");
    expect(skill).toContain("brand/design reference used");
    expect(skill).not.toContain("design-md-brand-router");
    expect(brands).toContain("apple");
    expect(appleDesign).toContain("Apple");
  });

  it("keeps CLI agent orchestration provider-based and strict by default", async () => {
    const skill = await readOwnedSkill("cli-agent-orchestrator");
    const opencodeProvider = await readFile(
      join(ownedSkillsRoot, "cli-agent-orchestrator", "references", "providers", "opencode.md"),
      "utf8"
    );
    const explorationTask = await readFile(
      join(ownedSkillsRoot, "cli-agent-orchestrator", "references", "task-types", "exploration.md"),
      "utf8"
    );
    const reportTemplate = await readFile(
      join(
        ownedSkillsRoot,
        "cli-agent-orchestrator",
        "references",
        "report-templates",
        "exploration-report.md"
      ),
      "utf8"
    );

    expect(skill).toContain("references/providers/opencode.md");
    expect(skill).toContain("references/task-types/exploration.md");
    expect(skill).toContain("Discuss-First Boundary Gate");
    expect(skill).toContain("strict read-only by default");
    expect(skill).toContain("review, planning, verification, audit, summarization, comparison");
    expect(skill).not.toContain("agentic-repo-explorer");

    expect(opencodeProvider).toContain("opencode models");
    expect(opencodeProvider).toContain("opencode run --dir");
    expect(opencodeProvider).toContain("opencode/deepseek-v4-flash-free");
    expect(opencodeProvider).toContain("opencode/nemotron-3-ultra-free");
    expect(opencodeProvider).toContain("opencode export");

    expect(explorationTask).toContain("not limited to repositories");
    expect(explorationTask).toContain("Do not modify files");
    expect(explorationTask).toContain("Do not run destructive commands");
    expect(explorationTask).toContain("Relevant Sources");

    expect(reportTemplate).toContain("# CLI Agent Exploration Report");
    expect(reportTemplate).toContain("Allowed scope");
    expect(reportTemplate).toContain("Reliability Notes");
  });

  it("keeps the Claude and Superpowers skill-authoring evaluation loop in skill-creator", async () => {
    const skill = await readOwnedSkill("skill-creator");

    expect(skill).toContain("baseline");
    expect(skill).toContain("with-skill");
    expect(skill).toContain("evals/evals.json");
    expect(skill).toContain("quantitative assertions");
    expect(skill).toContain("Progressive Disclosure");
    expect(skill).toContain("description = trigger");
  });

  it("keeps the robust browser-testing probe workflow in webapp-testing", async () => {
    const skill = await readOwnedSkill("webapp-testing");

    expect(skill).toContain("with_server.py --help");
    expect(skill).toContain("networkidle");
    expect(skill).toContain("Reconnaissance-Then-Action");
    expect(skill).toContain("/tmp");
  });

  it("keeps the MCP design and evaluation details in mcp-builder", async () => {
    const skill = await readOwnedSkill("mcp-builder");

    expect(skill).toContain("structuredContent");
    expect(skill).toContain("annotations");
    expect(skill).toContain("readOnlyHint");
    expect(skill).toContain("destructiveHint");
    expect(skill).toContain("10 read-only questions");
    expect(skill).toContain("MCP Inspector");
  });
});

async function readOwnedSkill(id: string): Promise<string> {
  return readFile(join(ownedSkillsRoot, id, "SKILL.md"), "utf8");
}
