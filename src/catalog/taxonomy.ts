import { readFile } from "node:fs/promises";
import { parse } from "yaml";
import { z } from "zod";
import { installScopes, type InstallScope } from "../model/scopes";
import { supportedTargets, type SupportedTarget } from "../model/targets";
import { toRepositoryPath } from "../shared/paths";

const slugSchema = z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/);
const skillIdSchema = z.string().regex(/^[a-z0-9]+(?:[-_][a-z0-9]+)*$/);

const groupSchema = z
  .object({
    id: slugSchema,
    label: z.string().min(1),
    description: z.string().min(1).optional()
  })
  .strict();

const skillTaxonomySchema = z
  .object({
    group: slugSchema.optional(),
    subgroup: slugSchema.optional(),
    tags: z.array(slugSchema).optional(),
    recommendedScopes: z.array(z.enum(installScopes)).optional(),
    recommendedTargets: z.array(z.enum(supportedTargets)).optional(),
    description: z.string().min(1).optional()
  })
  .strict();

const taxonomySchema = z
  .object({
    groups: z.array(groupSchema).optional(),
    skills: z.record(skillIdSchema, skillTaxonomySchema).optional()
  })
  .strict();

export interface TaxonomyGroup {
  id: string;
  label: string;
  description?: string;
}

export interface SkillTaxonomyEntry {
  group?: string;
  subgroup?: string;
  tags: string[];
  recommendedScopes: InstallScope[];
  recommendedTargets: SupportedTarget[];
  description?: string;
}

export interface SkillTaxonomy {
  groups: TaxonomyGroup[];
  skills: Record<string, SkillTaxonomyEntry>;
}

export const defaultTaxonomyPath = toRepositoryPath("catalog", "taxonomy.yaml");

export async function loadTaxonomy(path: string = process.env.AIMAGICIAN_TAXONOMY_PATH ?? defaultTaxonomyPath): Promise<SkillTaxonomy> {
  try {
    const contents = await readFile(path, "utf8");
    const parsed = taxonomySchema.parse(parse(contents) ?? {});

    return {
      groups: parsed.groups ?? [],
      skills: Object.fromEntries(
        Object.entries(parsed.skills ?? {}).map(([id, entry]) => [
          id,
          {
            ...entry,
            tags: entry.tags ?? [],
            recommendedScopes: entry.recommendedScopes ?? [],
            recommendedTargets: entry.recommendedTargets ?? []
          }
        ])
      )
    };
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return { groups: [], skills: {} };
    }

    throw error;
  }
}

export function resolveSkillTaxonomy(
  taxonomy: SkillTaxonomy,
  skillId: string
): SkillTaxonomyEntry {
  return taxonomy.skills[skillId] ?? {
    group: "uncategorized",
    tags: [],
    recommendedScopes: [],
    recommendedTargets: []
  };
}
