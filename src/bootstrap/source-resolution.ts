import { execFile } from "node:child_process";
import { constants } from "node:fs";
import { access, mkdir, rm } from "node:fs/promises";
import { dirname, join } from "node:path";
import { promisify } from "node:util";
import type { LoadedCatalog } from "../catalog/source-types";
import type { NormalizedAsset } from "../model/assets";
import type { SupportedTarget } from "../model/targets";
import { materializeCursorRule } from "./cursor-rule";
import { materializeGeminiExtension } from "./gemini-extension";
import type { ResolvedTargetHomes } from "./target-homes";

const execFileAsync = promisify(execFile);

export interface ResolveManagedSkillInstallsOptions {
  catalog: LoadedCatalog;
  normalizedAssets: NormalizedAsset[];
  workspaceRoot: string;
  selectedTargets: SupportedTarget[];
  targetHomes: ResolvedTargetHomes;
  githubRepoOverrides?: Record<string, string>;
  materializedCommandSourceDirs?: Map<string, Partial<Record<SupportedTarget, string>>>;
}

export interface ResolvedManagedInstall {
  target: SupportedTarget;
  assetId: string;
  kind: "skill" | "plugin";
  origin: "owned" | "external";
  sourceId?: string;
  sourcePath: string;
  destinationPath: string;
  installType: "directory" | "file";
  installArea: "skills" | "plugins" | "extensions" | "rules";
}

export async function resolveManagedSkillInstalls(
  options: ResolveManagedSkillInstallsOptions
): Promise<ResolvedManagedInstall[]> {
  const installs: ResolvedManagedInstall[] = [];
  const checkoutRoots = new Map<string, string>();

  for (const skill of options.catalog.ownedSkills) {
    for (const target of options.selectedTargets) {
      const install = await createOwnedSkillInstall(
        skill.id,
        skill.skillDir,
        target,
        options.targetHomes,
        options.workspaceRoot
      );

      if (install) {
        installs.push(install);
      }
    }
  }

  for (const asset of options.normalizedAssets) {
    if (asset.kind !== "skill") {
      continue;
    }

    const selectedTargets = asset.effectiveTargets.filter((target) =>
      options.selectedTargets.includes(target)
    );

    if (selectedTargets.length === 0) {
      continue;
    }

    if (asset.locator.type === "github") {
      const cacheKey =
        `${asset.sourceId}:${asset.locator.github.repo}:${asset.locator.github.ref ?? "HEAD"}`;
      let checkoutRoot = checkoutRoots.get(cacheKey);

      if (!checkoutRoot) {
        checkoutRoot = await materializeGithubSource(
          asset.sourceId,
          asset.locator.github.repo,
          asset.locator.github.ref,
          options.workspaceRoot,
          options.githubRepoOverrides
        );
        checkoutRoots.set(cacheKey, checkoutRoot);
      }

      const sourceDir = await resolveGithubAssetSourceDir(
        checkoutRoot,
        asset.locator.github.path,
        asset.relativePath,
        asset.id
      );

      for (const target of selectedTargets) {
        const install = await createExternalSkillInstall(
          asset.id,
          asset.sourceId,
          sourceDir,
          target,
          options.targetHomes,
          options.workspaceRoot
        );

        if (install) {
          installs.push(install);
        }
      }

      continue;
    }

    if (asset.locator.type !== "command" || asset.locator.command.adapter?.type !== "generated-skills") {
      continue;
    }

    const generatedDirs = options.materializedCommandSourceDirs?.get(asset.sourceId);

    if (!generatedDirs) {
      throw new Error(`Missing materialized command source output for ${asset.sourceId}`);
    }

    for (const target of selectedTargets) {
      const sourceDir = generatedDirs[target];

      if (!sourceDir) {
        continue;
      }

      const install = await createExternalSkillInstall(
        asset.id,
        asset.sourceId,
        sourceDir,
        target,
        options.targetHomes,
        options.workspaceRoot
      );

      if (install) {
        installs.push(install);
      }
    }
  }

  return installs.sort(compareInstallRecord);
}

async function createOwnedSkillInstall(
  assetId: string,
  sourceDir: string,
  target: SupportedTarget,
  targetHomes: ResolvedTargetHomes,
  workspaceRoot: string
): Promise<ResolvedManagedInstall | null> {
  const destination = await resolveSkillInstallDestination(
    assetId,
    sourceDir,
    target,
    targetHomes,
    workspaceRoot
  );

  if (!destination) {
    return null;
  }

  return {
    target,
    assetId,
    kind: "skill",
    origin: "owned",
    sourceId: undefined,
    sourcePath: destination.sourcePath,
    destinationPath: destination.destinationPath,
    installType: "directory",
    installArea: destination.installArea
  };
}

async function createExternalSkillInstall(
  assetId: string,
  sourceId: string,
  sourceDir: string,
  target: SupportedTarget,
  targetHomes: ResolvedTargetHomes,
  workspaceRoot: string
): Promise<ResolvedManagedInstall | null> {
  const destination = await resolveSkillInstallDestination(
    assetId,
    sourceDir,
    target,
    targetHomes,
    workspaceRoot
  );

  if (!destination) {
    return null;
  }

  return {
    target,
    assetId,
    kind: "skill",
    origin: "external",
    sourceId,
    sourcePath: destination.sourcePath,
    destinationPath: destination.destinationPath,
    installType: "directory",
    installArea: destination.installArea
  };
}

async function resolveSkillInstallDestination(
  assetId: string,
  sourceDir: string,
  target: SupportedTarget,
  targetHomes: ResolvedTargetHomes,
  workspaceRoot: string
): Promise<{
  sourcePath: string;
  destinationPath: string;
  installArea: "skills" | "extensions" | "rules";
} | null> {
  switch (target) {
    case "codex":
      return {
        sourcePath: sourceDir,
        destinationPath: join(targetHomes.codex.skillsDir, assetId),
        installArea: "skills"
      };
    case "claude":
      return {
        sourcePath: sourceDir,
        destinationPath: join(targetHomes.claude.skillsDir, assetId),
        installArea: "skills"
      };
    case "opencode":
      return {
        sourcePath: sourceDir,
        destinationPath: join(targetHomes.opencode.skillsDir, assetId),
        installArea: "skills"
      };
    case "hermes":
      return {
        sourcePath: sourceDir,
        destinationPath: join(targetHomes.hermes.skillsDir, assetId),
        installArea: "skills"
      };
    case "cursor":
      return {
        sourcePath: await materializeCursorRule({
          assetId,
          sourceDir,
          workspaceRoot
        }),
        destinationPath: join(targetHomes.cursor.rulesDir, `${assetId}.mdc`),
        installArea: "rules"
      };
    case "gemini":
      return {
        sourcePath: await materializeGeminiExtension({
          assetId,
          sourceDir,
          workspaceRoot
        }),
        destinationPath: join(targetHomes.gemini.extensionsDir, assetId),
        installArea: "extensions"
      };
    default:
      return null;
  }
}

export async function materializeGithubSource(
  sourceId: string,
  repo: string,
  ref: string | undefined,
  workspaceRoot: string,
  githubRepoOverrides: Record<string, string> | undefined
): Promise<string> {
  const overridePath = githubRepoOverrides?.[repo] ?? readGithubRepoOverridesFromEnv()[repo];

  if (overridePath) {
    return overridePath;
  }

  const sourcesRoot = join(workspaceRoot, "sources", "github");
  const checkoutRoot = join(sourcesRoot, sourceId);

  await rm(checkoutRoot, { recursive: true, force: true });
  await mkdir(sourcesRoot, { recursive: true });

  try {
    await execFileAsync("git", [
      "clone",
      "--quiet",
      `https://github.com/${repo}.git`,
      checkoutRoot
    ]);

    if (ref) {
      await execFileAsync("git", ["checkout", "--quiet", ref], {
        cwd: checkoutRoot
      });
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : "unknown git error";
    throw new Error(`Failed to resolve GitHub source ${repo}: ${message}`);
  }

  return checkoutRoot;
}

export function readGithubRepoOverridesFromEnv(): Record<string, string> {
  const raw = process.env.AIMAGICIAN_GITHUB_REPO_OVERRIDES;

  if (!raw) {
    return {};
  }

  try {
    const parsed = JSON.parse(raw) as Record<string, string>;
    return parsed ?? {};
  } catch (error) {
    const message = error instanceof Error ? error.message : "invalid JSON";
    throw new Error(`Invalid AIMAGICIAN_GITHUB_REPO_OVERRIDES value: ${message}`);
  }
}

export async function resolveGithubAssetSourceDir(
  checkoutRoot: string,
  githubPath: string | undefined,
  relativePath: string | undefined,
  assetId: string
): Promise<string> {
  const baseDir = githubPath ? join(checkoutRoot, githubPath) : checkoutRoot;
  const candidatePath = relativePath ? join(baseDir, relativePath) : join(baseDir, assetId);
  const sourceDir = looksLikeSkillFile(relativePath) ? dirname(candidatePath) : candidatePath;

  await assertSkillDirectory(sourceDir, assetId);

  return sourceDir;
}

export async function resolveGithubAssetPath(
  checkoutRoot: string,
  githubPath: string | undefined,
  relativePath: string | undefined,
  assetId: string
): Promise<string> {
  const baseDir = githubPath ? join(checkoutRoot, githubPath) : checkoutRoot;
  const candidatePath = relativePath ? join(baseDir, relativePath) : join(baseDir, assetId);

  try {
    await access(candidatePath, constants.F_OK);
  } catch {
    throw new Error(`Resolved asset path for ${assetId} does not exist: ${candidatePath}`);
  }

  return candidatePath;
}

async function assertSkillDirectory(sourceDir: string, assetId: string): Promise<void> {
  try {
    await access(join(sourceDir, "SKILL.md"), constants.F_OK);
  } catch {
    throw new Error(
      `Resolved skill directory for ${assetId} does not contain SKILL.md: ${sourceDir}`
    );
  }
}

function looksLikeSkillFile(relativePath: string | undefined): boolean {
  return relativePath?.toLowerCase().endsWith("/skill.md") === true ||
    relativePath?.toLowerCase().endsWith("\\skill.md") === true ||
    relativePath === "SKILL.md";
}

function compareInstallRecord(
  left: ResolvedManagedInstall,
  right: ResolvedManagedInstall
): number {
  return [
    left.target.localeCompare(right.target),
    left.kind.localeCompare(right.kind),
    left.assetId.localeCompare(right.assetId),
    (left.sourceId ?? "").localeCompare(right.sourceId ?? ""),
    left.destinationPath.localeCompare(right.destinationPath)
  ].find((result) => result !== 0) ?? 0;
}
