import { describe, expect, it } from "vitest";
import { join } from "node:path";
import {
  fixturesRoot,
  ownedSkillsRoot,
  pluginsCatalogRoot,
  repositoryRoot,
  skillsCatalogRoot,
  toRepositoryPath
} from "../../src/shared/paths";

describe("repository scaffold", () => {
  it("exposes the canonical roots for later plans", () => {
    expect(ownedSkillsRoot).toBe(join(repositoryRoot, "skills", "owned"));
    expect(skillsCatalogRoot).toBe(join(repositoryRoot, "catalog", "skills"));
    expect(pluginsCatalogRoot).toBe(join(repositoryRoot, "catalog", "plugins"));
    expect(fixturesRoot).toBe(join(repositoryRoot, "tests", "fixtures"));
    expect(toRepositoryPath("src")).toBe(join(repositoryRoot, "src"));
  });
});
