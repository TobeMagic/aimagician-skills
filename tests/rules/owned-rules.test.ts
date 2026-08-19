import { access, readFile, readdir } from "node:fs/promises";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const root = process.cwd();
const ownedRulesRoot = join(root, "rules", "owned");
const ownedSkillsRoot = join(root, "skills", "owned");
const memoryRoot = join(root, "memory", "owned", "project-memory-policy");

const expectedRules = [
  "code-guidelines",
  "review-before-edit",
  "native-capability-first",
  "host-native-delegation",
  "git-safety",
  "memory-pointer"
];

describe("owned rules and memory policy", () => {
  it("keeps the six generic always-on rules outside the skill install set", async () => {
    const ruleIds = (await readdir(ownedRulesRoot)).sort();
    expect(ruleIds).toEqual([...expectedRules].sort());

    for (const id of expectedRules) {
      const rule = await readFile(join(ownedRulesRoot, id, "RULE.md"), "utf8");
      expect(rule).toMatch(/^---\nname: /);
      expect(rule).toContain("alwaysApply: true");
      await expect(access(join(ownedSkillsRoot, id, "SKILL.md"))).rejects.toThrow();
    }
  });

  it("loads vision-analysis only when native vision is missing", async () => {
    const skill = await readFile(join(ownedSkillsRoot, "vision-analysis", "SKILL.md"), "utf8");
    expect(skill).toContain("cannot see images");
    expect(skill).toContain("Do not use when this session already has a reliable native image tool");
  });

  it("points memory at both the user store and the project store", async () => {
    const policy = await readFile(join(memoryRoot, "MEMORY.md"), "utf8");
    const pointer = await readFile(join(ownedRulesRoot, "memory-pointer", "RULE.md"), "utf8");
    expect(policy).toContain("~/.skillbird/memory/");
    expect(policy).toContain(".planning/memory/");
    expect(pointer).toContain("~/.skillbird/memory/memory.md");
    expect(pointer).toContain(".planning/memory/memory.md");
    await access(join(memoryRoot, "templates", "user-memory.md"));
    await access(join(memoryRoot, "templates", "project-memory.md"));
    await access(join(memoryRoot, "templates", "daily-memory.md"));
  });
});
