import { readFile, readdir } from "node:fs/promises";
import { join, relative } from "node:path";
import { describe, expect, it } from "vitest";

const ownedSkillsRoot = join(process.cwd(), "skills", "owned");
const docsRoot = join(process.cwd(), "docs");

describe("consolidated owned skill content", () => {
  it("keeps aimagician-superpower source-neutral with a lightweight router and complete progressive disclosure", async () => {
    const skillRoot = join(ownedSkillsRoot, "aimagician-superpower");
    const skill = await readOwnedSkill("aimagician-superpower");
    const capabilityIndex = await readFile(join(skillRoot, "references", "capabilities", "index.md"), "utf8");
    const modulePaths = [
      "references/capabilities/intake-and-boundary.md",
      "references/capabilities/state-and-continuity.md",
      "references/capabilities/project-memory.md",
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

    expect(skill.split("\n").length).toBeLessThanOrEqual(180);
    expect(skill).toContain("Classify Before Acting");
    expect(skill).toContain("Recover Only the Context That Matters");
    expect(skill).toContain("Quick and Standard");
    expect(skill).toContain("Requirement Evidence Map");
    expect(skill).toContain("Failure Handling and Escalation");
    expect(skill).toContain("conditional routes, never default preflight");
    expect(skill).toContain("scripts/workflow.mjs");
    expect(skill).not.toContain("preferred_companions:");

    for (const modulePath of modulePaths) expect(capabilityIndex).toContain(modulePath.replace("references/capabilities/", ""));
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
      "assets/templates/project-memory.md",
      "assets/templates/daily-memory.md",
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
    expect(skill).toContain("Route ordinary native PowerPoint delivery to the PPT skill");
    expect(skill).toContain("HTML-first PDF or PPTX conversion");
    expect(skill).not.toContain("design-md-brand-router");
    expect(brands).toContain("apple");
    expect(appleDesign).toContain("Apple");
  });

  it("keeps CLI agent delegation provider-based, bounded, and independently validated", async () => {
    const skillRoot = join(ownedSkillsRoot, "cli-agent-delegator");
    const skill = await readOwnedSkill("cli-agent-delegator");
    const opencodeProvider = await readFile(join(skillRoot, "references", "providers", "opencode.md"), "utf8");
    const promptContract = await readFile(join(skillRoot, "references", "prompt-contract.md"), "utf8");
    const discoveryTask = await readFile(join(skillRoot, "references", "task-types", "discovery-and-research.md"), "utf8");
    const operationsTask = await readFile(join(skillRoot, "references", "task-types", "bounded-operations-and-execution.md"), "utf8");
    const reviewTask = await readFile(join(skillRoot, "references", "task-types", "independent-review-and-audit.md"), "utf8");

    expect(skill).toContain("Dispatch Trigger Gate");
    expect(skill).toContain("wording alone is not sufficient");
    expect(skill).toContain("Bounded-Operation Gate");
    expect(skill).toContain("does not impose tool-level access control");
    expect(skill).toContain("strict-read-only");
    expect(skill).toContain("read-and-run");
    expect(skill).toContain("bounded-write");
    expect(opencodeProvider).toContain("Event-Based Waiting");
    expect(opencodeProvider).toContain("never a fixed five-second poll count or fixed maximum elapsed duration");
    expect(promptContract).toContain("REQUIRED_SKILLS");
    expect(promptContract).toContain("Child-Agent Inheritance");
    expect(discoveryTask).toContain("Deep web research");
    expect(discoveryTask).toContain("Visual or image inspection");
    expect(operationsTask).toContain("isolated worktree");
    expect(reviewTask).toContain("Blocker");
    expect(reviewTask).toContain("Important");
    expect(reviewTask).toContain("Nitpick");
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

  it("keeps Linear as a project preference routed through Composio", async () => {
    const preference = await readFile(join(process.cwd(), ".planning", "preferences", "linear.md"), "utf8");
    expect(preference).toContain("Composio CLI");
    expect(preference).toContain("do not use Linear MCP");
    expect(preference).toContain("must not block code delivery");
    await expect(readOwnedSkill("linear-issue-workflow")).rejects.toThrow();
  });

  it("keeps PR protections repository-specific and tracker work post-delivery", async () => {
    const pr = await readOwnedSkill("github-pr-workflow");
    expect(pr).toContain("Never assume `dev`, `develop`, `main`, `master`");
    expect(pr).toContain("actual merge protections");
    expect(pr).toContain("optional Linear status/comment/closure");
    expect(pr).toContain("as a reason to delay a verified PR");
    expect(pr).toContain("Do not run `gh auth status` as routine PR evidence");
    expect(pr).toContain("Do not guess GraphQL schema types");
  });

  it("keeps cloud target binding explicit and uses the real Cloud SQL restore command", async () => {
    const cloud = await readOwnedSkill("gcloud-ops-workflow");
    const cloudSql = await readFile(join(ownedSkillsRoot, "gcloud-ops-workflow", "references", "cloud-sql.md"), "utf8");
    expect(cloud).toContain("Do not use `gcloud config` or `gcloud auth list` to infer a target");
    expect(cloudSql).toContain("gcloud sql backups restore <backup-id-or-name>");
    expect(cloudSql).toContain("Do not invent a `gcloud sql restore-backup` command");
  });

  it("keeps the skill-authoring evaluation loop in skill-creator", async () => {
    const skill = await readOwnedSkill("skill-creator");
    expect(skill).toContain("baseline");
    expect(skill).toContain("with-skill");
    expect(skill).toContain("quality/skill-evals/<skill-id>/evals.json");
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

  it("archives mcp-builder outside the active owner set", async () => {
    const skill = await readFile(join(process.cwd(), "skills", "archived", "mcp-builder", "SKILL.md"), "utf8");
    expect(skill).toContain("structuredContent");
    await expect(readOwnedSkill("mcp-builder")).rejects.toThrow();
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
