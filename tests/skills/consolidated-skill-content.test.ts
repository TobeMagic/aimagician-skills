import { readFile, readdir } from "node:fs/promises";
import { join, relative } from "node:path";
import { describe, expect, it } from "vitest";

const ownedSkillsRoot = join(process.cwd(), "skills", "owned");
const docsRoot = join(process.cwd(), "docs");

describe("consolidated owned skill content", () => {
  it("keeps aimagician-superpower source-neutral while exposing the complete workflow router", async () => {
    const skillRoot = join(ownedSkillsRoot, "aimagician-superpower");
    const skill = await readOwnedSkill("aimagician-superpower");
    const modulePaths = [
      "references/capabilities/intake-and-boundary.md",
      "references/capabilities/state-and-continuity.md",
      "references/capabilities/spec-driven-development.md",
      "references/capabilities/research-and-discovery.md",
      "references/capabilities/engineering-exploration.md",
      "references/capabilities/ideation-and-scope.md",
      "references/capabilities/engineering-design.md",
      "references/capabilities/planning-modes.md",
      "references/capabilities/agent-orchestration.md",
      "references/capabilities/execution-modes.md",
      "references/capabilities/engineering-delivery.md",
      "references/capabilities/debugging-and-forensics.md",
      "references/capabilities/engineering-review.md",
      "references/capabilities/verification-and-uat.md",
      "references/capabilities/audit-and-closure.md",
      "references/capabilities/domain-gates.md"
    ];
    const modules = await Promise.all(modulePaths.map((modulePath) => readFile(join(skillRoot, modulePath), "utf8")));
    const runtimeFiles = await readRuntimeFiles(skillRoot);
    const runtimeContent = runtimeFiles.map((file) => file.content).join("\n");
    const mergeAudit = await readFile(join(docsRoot, "superpowers", "aimagician-superpower-capability-merge.md"), "utf8");

    for (const forbidden of [
      "GSD", "Superpowers", "code-guidelines", "Source Decisions", "Consolidation Rules",
      "Installing external workflow frameworks", "auto-update hooks", "source-routing"
    ]) {
      expect(runtimeContent).not.toContain(forbidden);
    }

    expect(skill).toContain("Mandatory Start And Resume Gate");
    expect(skill).toContain("Read this `SKILL.md` again");
    expect(skill).toContain("project knowledge base");
    expect(skill).toContain("Workload And Specification Gate");
    expect(skill).toContain("Discuss Baseline Requirements");
    expect(skill).toContain("Research And Brainstorm");
    expect(skill).toContain("Re-Discuss And Lock");
    expect(skill).toContain("Plan And Review");
    expect(skill).toContain("Execute And Checkpoint");
    expect(skill).toContain("Verify And UAT");
    expect(skill).toContain("Handoff And Complete");
    expect(skill).toContain("Never present a partial implementation as complete");
    expect(skill).toContain("scripts/workflow.mjs");
    expect(skill).toMatch(/preferred_companions:[\s\S]*?- skill-creator[\s\S]*?compatibility:/);
    expect(skill).toContain("`execute` additionally requires completed research, discussion, context, and accepted plans");

    for (const modulePath of modulePaths) expect(skill).toContain(modulePath);
    expect(modules.join("\n")).toContain("ambiguity = 1 -");
    expect(modules.join("\n")).toContain("Specification reviewer");
    expect(modules.join("\n")).toContain("Condition-Based Waiting");
    expect(modules.join("\n")).toContain("test-first");
    expect(modules.join("\n")).toContain("Evidence Record");

    expect(runtimeFiles.map((file) => file.path)).toEqual(expect.arrayContaining([
      "assets/templates/phase-spec.md",
      "assets/templates/engineering-context-map.md",
      "assets/templates/engineering-design-record.md",
      "assets/templates/engineering-change-brief.md",
      "assets/templates/engineering-review.md",
      "evals/evals.json",
      "references/roles/implementer.md",
      "references/roles/spec-reviewer.md",
      "references/roles/quality-reviewer.md",
      "scripts/workflow.mjs",
      "scripts/engineering-route.mjs",
      "scripts/wait-for.mjs",
      "scripts/find-polluter.mjs"
    ]));

    expect(mergeAudit).toContain("GSD command files: 67");
    expect(mergeAudit).toContain("GSD agent files: 33");
    expect(mergeAudit).toContain("GSD workflow files under `get-shit-done/workflows`: 107 total, including 106 Markdown workflows");
    expect(mergeAudit).toContain("Superpowers skill roots: 14");
  });

  it("keeps brand DESIGN.md routing inside interface-design", async () => {
    const skill = await readOwnedSkill("interface-design");
    const brands = await readFile(join(ownedSkillsRoot, "interface-design", "references", "brand-design-md", "brands.json"), "utf8");
    const appleDesign = await readFile(join(ownedSkillsRoot, "interface-design", "references", "brand-design-md", "design-md", "apple.DESIGN.md"), "utf8");
    expect(skill).toContain("Brand DESIGN.md Routing");
    expect(skill).toContain("references/brand-design-md/brands.json");
    expect(skill).toContain("references/brand-design-md/design-md/*.DESIGN.md");
    expect(skill).toContain("HTML Based Universal Design");
    expect(skill).toContain("assets/patterns/decision-rules.json");
    expect(skill).toContain("scripts/design-router.mjs");
    expect(skill).toContain("Route native PowerPoint delivery to the PPT skill instead");
    expect(skill).not.toContain("design-md-brand-router");
    expect(brands).toContain("apple");
    expect(appleDesign).toContain("Apple");
  });

  it("keeps CLI agent orchestration provider-based and strict by default", async () => {
    const skill = await readOwnedSkill("cli-agent-orchestrator");
    const opencodeProvider = await readFile(join(ownedSkillsRoot, "cli-agent-orchestrator", "references", "providers", "opencode.md"), "utf8");
    const explorationTask = await readFile(join(ownedSkillsRoot, "cli-agent-orchestrator", "references", "task-types", "exploration.md"), "utf8");
    expect(skill).toContain("Exploration Priority Rule");
    expect(skill).toContain("use OpenCode first");
    expect(skill).toContain("strict read-only by default");
    expect(opencodeProvider).toContain("event-based waiting");
    expect(opencodeProvider).toContain("Do not impose a hard wall-clock timeout");
    expect(explorationTask).toContain("not limited to repositories");
    expect(explorationTask).toContain("Do not modify files");
  });

  it("adds Composio as a service-scoped SaaS tool router without turning it into MCP builder", async () => {
    const skill = await readOwnedSkill("composio-tool-router");
    const cliWorkflow = await readFile(join(ownedSkillsRoot, "composio-tool-router", "references", "cli-workflow.md"), "utf8");
    const safety = await readFile(join(ownedSkillsRoot, "composio-tool-router", "references", "safety-and-boundaries.md"), "utf8");
    expect(skill).toContain("category: operate");
    expect(skill).toContain("schema-on-demand");
    expect(cliWorkflow).toContain("composio tools list linear --limit 50");
    expect(cliWorkflow).toContain("--dry-run");
    expect(safety).toContain("Never print API keys");
  });

  it("keeps the skill-authoring evaluation loop in skill-creator", async () => {
    const skill = await readOwnedSkill("skill-creator");
    expect(skill).toContain("baseline");
    expect(skill).toContain("with-skill");
    expect(skill).toContain("evals/evals.json");
    expect(skill).toContain("quantitative assertions");
    expect(skill).toContain("Progressive Disclosure");
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
    expect(skill).toContain("MCP Inspector");
  });
});

async function readRuntimeFiles(root: string): Promise<Array<{ path: string; content: string }>> {
  const files: Array<{ path: string; content: string }> = [];
  async function visit(directory: string): Promise<void> {
    for (const entry of await readdir(directory, { withFileTypes: true })) {
      if (entry.name === "_external_repos") continue;
      const fullPath = join(directory, entry.name);
      if (entry.isDirectory()) await visit(fullPath);
      if (entry.isFile()) files.push({ path: relative(root, fullPath).replaceAll("\\", "/"), content: await readFile(fullPath, "utf8") });
    }
  }
  await visit(root);
  return files.sort((left, right) => left.path.localeCompare(right.path));
}

async function readOwnedSkill(id: string): Promise<string> {
  return readFile(join(ownedSkillsRoot, id, "SKILL.md"), "utf8");
}
