import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join, dirname } from "node:path";
import { parse, stringify } from "yaml";
import { z } from "zod";

const userGroupSchema = z
  .object({
    name: z.string().min(1),
    label: z.string().min(1),
    skills: z.array(z.string().min(1))
  })
  .strict();

const userConfigSchema = z
  .object({
    version: z.literal(1),
    groups: z.array(userGroupSchema).optional(),
    archivedIds: z.array(z.string().min(1)).optional(),
    customTags: z.record(z.string(), z.array(z.string().min(1))).optional(),
    theme: z.string().optional()
  })
  .strict();

export interface UserDefinedGroup {
  name: string;
  label: string;
  skills: string[];
}

export interface UserSkillConfig {
  version: 1;
  groups: UserDefinedGroup[];
  archivedIds: string[];
  customTags: Record<string, string[]>;
  theme: string;
}

export function userConfigDir(configBaseDir: string): string {
  return join(configBaseDir, "skillbee");
}

export function userConfigPath(configBaseDir: string): string {
  return join(userConfigDir(configBaseDir), "user-config.yaml");
}

export function defaultUserConfig(): UserSkillConfig {
  return {
    version: 1,
    groups: [],
    archivedIds: [],
    customTags: {},
    theme: "bee"
  };
}

export async function loadUserConfig(configBaseDir: string): Promise<UserSkillConfig> {
  const path = userConfigPath(configBaseDir);

  try {
    const contents = await readFile(path, "utf8");
    const parsed = userConfigSchema.parse(parse(contents) ?? {});

    return {
      version: 1,
      groups: parsed.groups ?? [],
      archivedIds: parsed.archivedIds ?? [],
      customTags: parsed.customTags ?? {},
      theme: parsed.theme ?? "bee"
    };
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return defaultUserConfig();
    }

    throw error;
  }
}

export async function saveUserConfig(
  configBaseDir: string,
  config: UserSkillConfig
): Promise<void> {
  const path = userConfigPath(configBaseDir);

  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, stringify(config), "utf8");
}

export async function addArchivedIds(
  configBaseDir: string,
  skillIds: string[]
): Promise<UserSkillConfig> {
  const config = await loadUserConfig(configBaseDir);
  const existing = new Set(config.archivedIds);

  for (const id of skillIds) {
    existing.add(id);
  }

  config.archivedIds = [...existing].sort();
  await saveUserConfig(configBaseDir, config);

  return config;
}

export async function removeArchivedIds(
  configBaseDir: string,
  skillIds: string[]
): Promise<UserSkillConfig> {
  const config = await loadUserConfig(configBaseDir);
  const remove = new Set(skillIds);

  config.archivedIds = config.archivedIds.filter((id) => !remove.has(id));
  await saveUserConfig(configBaseDir, config);

  return config;
}

export async function setCustomTags(
  configBaseDir: string,
  skillId: string,
  tags: string[]
): Promise<UserSkillConfig> {
  const config = await loadUserConfig(configBaseDir);

  if (tags.length > 0) {
    config.customTags[skillId] = tags;
  } else {
    delete config.customTags[skillId];
  }

  await saveUserConfig(configBaseDir, config);

  return config;
}

export async function saveUserGroup(
  configBaseDir: string,
  group: UserDefinedGroup
): Promise<UserSkillConfig> {
  const config = await loadUserConfig(configBaseDir);
  const index = config.groups.findIndex((existing) => existing.name === group.name);

  if (index >= 0) {
    config.groups[index] = group;
  } else {
    config.groups.push(group);
  }

  await saveUserConfig(configBaseDir, config);

  return config;
}

export async function removeUserGroup(
  configBaseDir: string,
  groupName: string
): Promise<UserSkillConfig> {
  const config = await loadUserConfig(configBaseDir);

  config.groups = config.groups.filter((group) => group.name !== groupName);
  await saveUserConfig(configBaseDir, config);

  return config;
}

export async function saveTheme(
  configBaseDir: string,
  theme: string
): Promise<UserSkillConfig> {
  const config = await loadUserConfig(configBaseDir);
  config.theme = theme;
  await saveUserConfig(configBaseDir, config);
  return config;
}
