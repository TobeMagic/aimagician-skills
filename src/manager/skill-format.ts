import { readFile, writeFile } from "node:fs/promises";
import { basename, dirname } from "node:path";
import fg from "fast-glob";
import { parse, stringify } from "yaml";
import { loadTaxonomy } from "../catalog/taxonomy";
import { ownedSkillsRoot as defaultOwnedSkillsRoot } from "../shared/paths";

export type SkillFormatMode = "check" | "write";

export interface FormatOwnedSkillsOptions {
  ownedSkillsRoot?: string;
  taxonomyPath?: string;
  mode: SkillFormatMode;
}

export interface SkillFormatRecord {
  id: string;
  status: "ok" | "needs-update" | "missing-taxonomy";
  category?: string;
  subcategory?: string;
  tags: string[];
  issues: string[];
}

export interface FormatOwnedSkillsResult {
  mode: SkillFormatMode;
  changed: boolean;
  records: SkillFormatRecord[];
}

interface ParsedSkillFile {
  frontmatter: Record<string, unknown>;
  body: string;
}

export async function formatOwnedSkills(
  options: FormatOwnedSkillsOptions
): Promise<FormatOwnedSkillsResult> {
  const ownedRoot = options.ownedSkillsRoot ?? defaultOwnedSkillsRoot;
  const taxonomy = await loadTaxonomy(options.taxonomyPath);
  const skillFiles = await fg(["*/SKILL.md"], {
    cwd: ownedRoot,
    absolute: true,
    onlyFiles: true,
    suppressErrors: true
  });
  const records: SkillFormatRecord[] = [];
  let changed = false;

  for (const skillFile of skillFiles.sort()) {
    const id = basename(dirname(skillFile));
    const taxonomyEntry = taxonomy.skills[id];

    if (!taxonomyEntry) {
      records.push({
        id,
        status: "missing-taxonomy",
        tags: [],
        issues: ["missing-taxonomy"]
      });
      continue;
    }

    const parsed = parseSkillFile(await readFile(skillFile, "utf8"));
    const category = taxonomyEntry.group;
    const subcategory = taxonomyEntry.subgroup;
    const tags = taxonomyEntry.tags;
    const issues = createClassificationIssues(parsed.frontmatter, category, subcategory, tags);

    records.push({
      id,
      status: issues.length > 0 ? "needs-update" : "ok",
      ...(category ? { category } : {}),
      ...(subcategory ? { subcategory } : {}),
      tags,
      issues
    });

    if (options.mode === "write" && issues.length > 0) {
      const nextFrontmatter = {
        ...parsed.frontmatter,
        ...(category ? { category } : {}),
        ...(subcategory ? { subcategory } : {}),
        tags
      };
      await writeFile(skillFile, serializeSkillFile(nextFrontmatter, parsed.body), "utf8");
      changed = true;
    }
  }

  return {
    mode: options.mode,
    changed,
    records
  };
}

function parseSkillFile(contents: string): ParsedSkillFile {
  const match = contents.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?/);
  if (!match) {
    return { frontmatter: {}, body: contents };
  }

  const frontmatterRaw = match[1] ?? "";
  const body = contents.slice(match[0].length).replace(/^\r?\n/, "");

  return {
    frontmatter: parse(frontmatterRaw) ?? {},
    body
  };
}

function serializeSkillFile(frontmatter: Record<string, unknown>, body: string): string {
  return `---\n${stringify(frontmatter).trimEnd()}\n---\n\n${body}`;
}

function createClassificationIssues(
  frontmatter: Record<string, unknown>,
  category: string | undefined,
  subcategory: string | undefined,
  tags: string[]
): string[] {
  const issues: string[] = [];

  if (category && frontmatter.category !== category) {
    issues.push("missing-category");
  }

  if (subcategory && frontmatter.subcategory !== subcategory) {
    issues.push("missing-subcategory");
  }

  if (!Array.isArray(frontmatter.tags) || !sameStringArray(frontmatter.tags, tags)) {
    issues.push("missing-tags");
  }

  return issues;
}

function sameStringArray(left: unknown[], right: string[]): boolean {
  return left.length === right.length &&
    left.every((value, index) => value === right[index]);
}
