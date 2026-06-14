import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { formatOwnedSkills } from "../../src/manager/skill-format";

const tempDirectories: string[] = [];

afterEach(async () => {
  await Promise.allSettled(
    tempDirectories.splice(0).map((directory) =>
      rm(directory, { recursive: true, force: true })
    )
  );
});

describe("formatOwnedSkills", () => {
  it("reports missing classification fields in check mode", async () => {
    const fixture = await createFormatterFixture();

    const result = await formatOwnedSkills({
      ownedSkillsRoot: fixture.ownedSkillsRoot,
      taxonomyPath: fixture.taxonomyPath,
      mode: "check"
    });

    expect(result.changed).toBe(false);
    expect(result.records).toEqual([
      {
        id: "daily-ops",
        status: "needs-update",
        category: "build",
        subcategory: "workflow",
        tags: ["workflow", "verification"],
        issues: ["missing-category", "missing-subcategory", "missing-tags"]
      }
    ]);
  });

  it("writes classification frontmatter from taxonomy", async () => {
    const fixture = await createFormatterFixture();

    const result = await formatOwnedSkills({
      ownedSkillsRoot: fixture.ownedSkillsRoot,
      taxonomyPath: fixture.taxonomyPath,
      mode: "write"
    });

    const skillFile = await readFile(join(fixture.ownedSkillsRoot, "daily-ops", "SKILL.md"), "utf8");

    expect(result.changed).toBe(true);
    expect(skillFile).toContain("category: build");
    expect(skillFile).toContain("subcategory: workflow");
    expect(skillFile).toContain("tags:");
    expect(skillFile).toContain("  - workflow");
    expect(skillFile).toContain("  - verification");
  });
});

async function createFormatterFixture() {
  const root = await mkdtemp(join(tmpdir(), "skillbird-format-"));
  tempDirectories.push(root);

  const ownedSkillsRoot = join(root, "skills", "owned");
  const taxonomyPath = join(root, "catalog", "taxonomy.yaml");
  await mkdir(join(ownedSkillsRoot, "daily-ops"), { recursive: true });
  await mkdir(join(root, "catalog"), { recursive: true });
  await writeFile(
    join(ownedSkillsRoot, "daily-ops", "SKILL.md"),
    [
      "---",
      "name: daily-ops",
      "description: Use when operating daily workflows.",
      "---",
      "",
      "# Daily Ops"
    ].join("\n"),
    "utf8"
  );
  await writeFile(
    taxonomyPath,
    [
      "groups:",
      "  - id: build",
      "    label: Build",
      "skills:",
      "  daily-ops:",
      "    group: build",
      "    subgroup: workflow",
      "    tags: [workflow, verification]"
    ].join("\n"),
    "utf8"
  );

  return { ownedSkillsRoot, taxonomyPath };
}
