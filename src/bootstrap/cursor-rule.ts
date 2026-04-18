import { mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { parse } from "yaml";

export interface MaterializeCursorRuleOptions {
  assetId: string;
  sourceDir: string;
  workspaceRoot: string;
}

interface ParsedSkillMarkdown {
  description?: string;
  body: string;
}

export async function materializeCursorRule(
  options: MaterializeCursorRuleOptions
): Promise<string> {
  const generatedRoot = join(
    options.workspaceRoot,
    "generated",
    "cursor",
    options.assetId
  );
  const rulePath = join(generatedRoot, `${options.assetId}.mdc`);
  const originalSkill = await readFile(join(options.sourceDir, "SKILL.md"), "utf8");
  const parsedSkill = parseSkillMarkdown(originalSkill);

  await rm(generatedRoot, { recursive: true, force: true });
  await mkdir(generatedRoot, { recursive: true });
  await writeFile(
    rulePath,
    createCursorRule(options.assetId, parsedSkill),
    "utf8"
  );

  return rulePath;
}

function parseSkillMarkdown(skillMarkdown: string): ParsedSkillMarkdown {
  const trimmed = skillMarkdown.trim();
  const frontmatterMatch = /^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/m.exec(trimmed);

  if (!frontmatterMatch) {
    return {
      body: trimmed
    };
  }
  const [, yamlFrontmatter, markdownBody] = frontmatterMatch;

  try {
    const parsed = parse(yamlFrontmatter) as { description?: string } | null;

    return {
      description: sanitizeDescription(parsed?.description),
      body: markdownBody
    };
  } catch {
    return {
      body: markdownBody
    };
  }
}

function sanitizeDescription(description: string | undefined): string | undefined {
  if (!description) {
    return undefined;
  }

  const collapsed = description
    .replace(/\s+/g, " ")
    .replace(/`/g, "'")
    .trim();

  return collapsed.length > 0 ? collapsed : undefined;
}

function createCursorRule(
  assetId: string,
  skill: ParsedSkillMarkdown
): string {
  const description =
    skill.description ??
    `Use the ${assetId} repository-managed skill when its workflow matches the current task.`;

  return [
    "---",
    `description: "${escapeYamlDoubleQuoted(description)}"`,
    "alwaysApply: false",
    "---",
    "",
    `# ${assetId}`,
    "",
    `This Cursor rule is generated from the repository-managed skill \`${assetId}\`.`,
    "Apply it when the task matches the skill's description or when you want to reuse its workflow.",
    "",
    skill.body,
    ""
  ].join("\n");
}

function escapeYamlDoubleQuoted(value: string): string {
  return value
    .replace(/\\/g, "\\\\")
    .replace(/"/g, '\\"');
}
