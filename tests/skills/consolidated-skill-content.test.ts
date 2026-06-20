import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const ownedSkillsRoot = join(process.cwd(), "skills", "owned");

describe("consolidated owned skill content", () => {
  it("keeps the merged GSD and Superpowers planning contract in aimagician-superpower", async () => {
    const skill = await readOwnedSkill("aimagician-superpower");

    expect(skill).toContain("CONTEXT.md");
    expect(skill).toContain("DISCUSSION-LOG.md");
    expect(skill).toContain("RESEARCH.md");
    expect(skill).toContain("VALIDATION.md");
    expect(skill).toContain("UAT.md");
    expect(skill).toContain("8 Verification Dimensions");
    expect(skill).toContain("Package Legitimacy");
    expect(skill).toContain("dependency waves");
    expect(skill).toContain("Built-In Code Discipline");
    expect(skill).toContain("Surgical changes");
    expect(skill).toContain("Goal-driven verification");
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
