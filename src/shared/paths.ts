import { join, normalize } from "node:path";

export const repositoryRoot = normalize(join(__dirname, "..", ".."));

export const skillsRoot = join(repositoryRoot, "skills");
export const ownedSkillsRoot = join(skillsRoot, "owned");

export const catalogRoot = join(repositoryRoot, "catalog");
export const skillsCatalogRoot = join(catalogRoot, "skills");
export const pluginsCatalogRoot = join(catalogRoot, "plugins");

export const testsRoot = join(repositoryRoot, "tests");
export const fixturesRoot = join(testsRoot, "fixtures");

export const repositoryRoots = {
  repositoryRoot,
  skillsRoot,
  ownedSkillsRoot,
  catalogRoot,
  skillsCatalogRoot,
  pluginsCatalogRoot,
  testsRoot,
  fixturesRoot
} as const;

export function toRepositoryPath(...segments: string[]): string {
  return join(repositoryRoot, ...segments);
}
