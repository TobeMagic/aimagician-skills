import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const ownedRoot = join(process.cwd(), "skills", "owned");

describe("core Skill runtime purity", () => {
  it("keeps source provenance out of active core Skill instructions", async () => {
    const skills = ["webapp-testing", "skill-creator", "llm-know-how-wiki"];
    const forbidden = ["Source Decisions", "anthropic-skill-creator", "superpowers-skill-authoring", "Karpathy", "Hermes Agent"];
    for (const id of skills) {
      const content = await readFile(join(ownedRoot, id, "SKILL.md"), "utf8");
      for (const token of forbidden) expect(content).not.toContain(token);
    }
  });
});
