import { describe, expect, it } from "vitest";

// We test the pure filter logic extracted from dashboard.ts
// Since dashboard.ts has blessed dependencies, we replicate the core logic here

interface SkillLike {
  id: string;
  group: string;
  tags: string[];
  archived: boolean;
  subgroup?: string;
  sourceId?: string;
  description?: string;
  customTags: string[];
}

interface TaxonomyGroupLike {
  id: string;
  label: string;
}

function filterSkillsByGroups(
  skills: SkillLike[],
  selectedGroups: Set<string>,
  query: string,
  includeArchived: boolean
): SkillLike[] {
  const normalizedQuery = query.trim().toLowerCase();
  const hasGroupFilter = selectedGroups.size > 0;

  return skills.filter((skill) => {
    if (!includeArchived && skill.archived) return false;
    if (hasGroupFilter && !selectedGroups.has(skill.group)) return false;
    if (normalizedQuery) {
      const matches = [skill.id, skill.description, skill.group, skill.subgroup, skill.sourceId, ...skill.tags, ...skill.customTags]
        .some((v) => v?.toLowerCase().includes(normalizedQuery));
      if (!matches) return false;
    }
    return true;
  });
}

function extractAllGroups(skills: SkillLike[], taxonomyGroups: TaxonomyGroupLike[]): TaxonomyGroupLike[] {
  const groupIds = new Set<string>();
  for (const skill of skills) {
    if (skill.group) groupIds.add(skill.group);
  }
  return taxonomyGroups.filter((g) => groupIds.has(g.id));
}

const mockTaxonomyGroups: TaxonomyGroupLike[] = [
  { id: "coding", label: "Coding" },
  { id: "research", label: "Research" },
  { id: "design", label: "Design" },
  { id: "documents", label: "Documents" }
];

const mockSkills: SkillLike[] = [
  { id: "alpha", group: "research", tags: ["paper", "research"], archived: false, customTags: [] },
  { id: "beta", group: "coding", tags: ["coding", "quality"], archived: false, customTags: [] },
  { id: "gamma", group: "design", tags: ["paper", "design"], archived: false, customTags: [] },
  { id: "delta", group: "design", tags: ["ui", "design"], archived: true, customTags: [] },
  { id: "epsilon", group: "coding", tags: ["coding"], archived: false, customTags: ["my-tag"] }
];

describe("extractAllGroups", () => {
  it("extracts unique groups from skills and returns matching taxonomy groups", () => {
    const groups = extractAllGroups(mockSkills, mockTaxonomyGroups);
    // Returns groups in taxonomy order (coding, research, design)
    expect(groups.map((g) => g.id)).toEqual(["coding", "research", "design"]);
  });

  it("returns empty array for empty skills", () => {
    expect(extractAllGroups([], mockTaxonomyGroups)).toEqual([]);
  });

  it("returns empty array when no taxonomy groups match", () => {
    expect(extractAllGroups(mockSkills, [])).toEqual([]);
  });
});

describe("filterSkillsByGroups", () => {
  it("shows all non-archived skills when no groups selected", () => {
    const result = filterSkillsByGroups(mockSkills, new Set(), "", false);
    expect(result.map((s) => s.id)).toEqual(["alpha", "beta", "gamma", "epsilon"]);
  });

  it("filters by single group", () => {
    const result = filterSkillsByGroups(mockSkills, new Set(["coding"]), "", false);
    expect(result.map((s) => s.id)).toEqual(["beta", "epsilon"]);
  });

  it("filters by multiple groups (OR logic)", () => {
    const result = filterSkillsByGroups(mockSkills, new Set(["coding", "design"]), "", false);
    expect(result.map((s) => s.id)).toEqual(["beta", "gamma", "epsilon"]);
  });

  it("includes archived when flag is set", () => {
    const result = filterSkillsByGroups(mockSkills, new Set(["design"]), "", true);
    expect(result.map((s) => s.id)).toEqual(["gamma", "delta"]);
  });

  it("combines group filter with query", () => {
    const result = filterSkillsByGroups(mockSkills, new Set(["coding"]), "quality", false);
    expect(result.map((s) => s.id)).toEqual(["beta"]);
  });

  it("query matches custom tags", () => {
    const result = filterSkillsByGroups(mockSkills, new Set(), "my-tag", false);
    expect(result.map((s) => s.id)).toEqual(["epsilon"]);
  });

  it("returns empty when group has no matches", () => {
    const result = filterSkillsByGroups(mockSkills, new Set(["nonexistent"]), "", false);
    expect(result).toEqual([]);
  });
});
