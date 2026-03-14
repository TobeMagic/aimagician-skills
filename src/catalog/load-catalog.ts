import { readFile } from "node:fs/promises";
import { basename, dirname } from "node:path";
import fg from "fast-glob";
import { parse } from "yaml";
import type { CatalogSection } from "../model/assets";
import {
  ownedSkillsRoot,
  pluginsCatalogRoot,
  skillsCatalogRoot
} from "../shared/paths";
import type {
  LoadedCatalog,
  LoadedCatalogFile,
  LoadedCatalogSection,
  OwnedSkillRecord
} from "./source-types";
import { parseCatalogFile } from "./schemas";

export interface CatalogLoadOptions {
  ownedSkillsRoot?: string;
  skillsRoot?: string;
  pluginsRoot?: string;
}

export async function loadCatalog(
  options: CatalogLoadOptions = {}
): Promise<LoadedCatalog> {
  const ownedSkills = await discoverOwnedSkills(
    options.ownedSkillsRoot ??
      process.env.AIMAGICIAN_OWNED_SKILLS_ROOT ??
      ownedSkillsRoot
  );
  const skills = await loadCatalogSection(
    "skills",
    options.skillsRoot ??
      process.env.AIMAGICIAN_SKILLS_CATALOG_ROOT ??
      skillsCatalogRoot
  );
  const plugins = await loadCatalogSection(
    "plugins",
    options.pluginsRoot ??
      process.env.AIMAGICIAN_PLUGINS_CATALOG_ROOT ??
      pluginsCatalogRoot
  );

  const sources = [...skills.sources, ...plugins.sources];
  const activeSources = [...skills.activeSources, ...plugins.activeSources];

  return {
    ownedSkills,
    skills,
    plugins,
    sources,
    activeSources
  };
}

export async function discoverOwnedSkills(
  rootDir: string = ownedSkillsRoot
): Promise<OwnedSkillRecord[]> {
  const matches = await fg(["*/SKILL.md"], {
    cwd: rootDir,
    onlyFiles: true,
    absolute: true,
    suppressErrors: true
  });

  return matches.map((skillFile) => {
    const skillDir = dirname(skillFile);

    return {
      id: basename(skillDir),
      skillDir,
      skillFile
    };
  });
}

export async function loadCatalogSection(
  section: CatalogSection,
  rootDir: string
): Promise<LoadedCatalogSection> {
  const matches = await fg(["*.yaml", "*.yml"], {
    cwd: rootDir,
    onlyFiles: true,
    absolute: true,
    suppressErrors: true
  });

  const files = await Promise.all(
    matches.map(async (filePath) => loadCatalogFile(section, filePath))
  );

  const sources = files.flatMap((file) => file.sources);
  const activeSources = files.flatMap((file) => file.activeSources);

  return {
    section,
    rootDir,
    files,
    sources,
    activeSources
  };
}

async function loadCatalogFile(
  section: CatalogSection,
  filePath: string
): Promise<LoadedCatalogFile> {
  const contents = await readFile(filePath, "utf8");
  const rawDocument = parse(contents) ?? {};
  const parsed = parseCatalogFile(section, rawDocument);

  const sources = parsed.sources.map((source) => ({
    ...source,
    enabled: source.enabled ?? true,
    section,
    originFile: filePath
  }));

  return {
    section,
    filePath,
    sources,
    activeSources: sources.filter((source) => source.enabled)
  };
}
