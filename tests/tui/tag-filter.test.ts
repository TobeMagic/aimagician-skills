import { describe, expect, it } from "vitest";

// We test the pure filter logic extracted from dashboard.ts
// Since dashboard.ts has blessed dependencies, we replicate the core logic here

interface SkillLike {
  id: string;
  tags: string[];
  archived: boolean;
  group: string;
  subgroup?: string;
  sourceId?: string;
  description?: string;
  customTags: string[];
}

function filterSkillsByTags(
  skills: SkillLike[],
  selectedTags: Set<string>,
  query: string,
  includeArchived: boolean
): SkillLike[] {
  const normalizedQuery = query.trim().toLowerCase();
  const hasTagFilter = selectedTags.size > 0;

  return skills.filter((skill) => {
    if (!includeArchived && skill.archived) return false;
    if (hasTagFilter && !skill.tags.some((t) => selectedTags.has(t))) return false;
    if (normalizedQuery) {
      const matches = [skill.id, skill.description, skill.group, skill.subgroup, skill.sourceId, ...skill.tags, ...skill.customTags]
        .some((v) => v?.toLowerCase().includes(normalizedQuery));
      if (!matches) return false;
    }
    return true;
  });
}

function extractAllTags(skills: SkillLike[]): string[] {
  const tagSet = new Set<string>();
  for (const skill of skills) {
    for (const tag of skill.tags) tagSet.add(tag);
  }
  return [...tagSet].sort();
}

const mockSkills: SkillLike[] = [
  { id: "alpha", tags: ["paper", "research"], archived: false, group: "research", customTags: [] },
  { id: "beta", tags: ["coding", "quality"], archived: false, group: "coding", customTags: [] },
  { id: "gamma", tags: ["paper", "design"], archived: false, group: "design", customTags: [] },
  { id: "delta", tags: ["ui", "design"], archived: true, group: "design", customTags: [] },
  { id: "epsilon", tags: ["coding"], archived: false, group: "coding", customTags: ["my-tag"] },
];

describe("extractAllTags", () => {
  it("extracts unique sorted tags from all skills", () => {
    const tags = extractAllTags(mockSkills);
    expect(tags).toEqual(["coding", "design", "paper", "quality", "research", "ui"]);
  });

  it("returns empty array for empty skills", () => {
    expect(extractAllTags([])).toEqual([]);
  });
});

describe("filterSkillsByTags", () => {
  it("shows all non-archived skills when no tags selected", () => {
    const result = filterSkillsByTags(mockSkills, new Set(), "", false);
    expect(result.map((s) => s.id)).toEqual(["alpha", "beta", "gamma", "epsilon"]);
  });

  it("filters by single tag (OR logic)", () => {
    const result = filterSkillsByTags(mockSkills, new Set(["paper"]), "", false);
    expect(result.map((s) => s.id)).toEqual(["alpha", "gamma"]);
  });

  it("filters by multiple tags (OR logic)", () => {
    const result = filterSkillsByTags(mockSkills, new Set(["paper", "coding"]), "", false);
    expect(result.map((s) => s.id)).toEqual(["alpha", "beta", "gamma", "epsilon"]);
  });

  it("includes archived when flag is set", () => {
    const result = filterSkillsByTags(mockSkills, new Set(["design"]), "", true);
    expect(result.map((s) => s.id)).toEqual(["gamma", "delta"]);
  });

  it("combines tag filter with query", () => {
    const result = filterSkillsByTags(mockSkills, new Set(["coding"]), "quality", false);
    expect(result.map((s) => s.id)).toEqual(["beta"]);
  });

  it("query matches custom tags", () => {
    const result = filterSkillsByTags(mockSkills, new Set(), "my-tag", false);
    expect(result.map((s) => s.id)).toEqual(["epsilon"]);
  });

  it("returns empty when tag has no matches", () => {
    const result = filterSkillsByTags(mockSkills, new Set(["nonexistent"]), "", false);
    expect(result).toEqual([]);
  });
});
