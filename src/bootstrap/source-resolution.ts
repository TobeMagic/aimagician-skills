import { execFile } from "node:child_process";
import { constants } from "node:fs";
import { access, mkdir, rm } from "node:fs/promises";
import { dirname, join } from "node:path";
import { promisify } from "node:util";
import type { LoadedCatalog } from "../catalog/source-types";
import type { NormalizedAsset } from "../model/assets";
import { directSkillTargets, type DirectSkillTarget } from "./target-homes";

const execFileAsync = promisify(execFile);

export interface ResolveDirectSkillInstallsOptions {
  catalog: LoadedCatalog;
  normalizedAssets: NormalizedAsset[];
  workspaceRoot: string;
  selectedTargets: DirectSkillTarget[];
  githubRepoOverrides?: Record<string, string>;
}

export interface ResolvedDirectSkillInstall {
  target: DirectSkillTarget;
  assetId: string;
  origin: "owned" | "external";
  sourceId?: string;
  sourceDir: string;
}

export async function resolveDirectSkillInstalls(
  options: ResolveDirectSkillInstallsOptions
): Promise<ResolvedDirectSkillInstall[]> {
  const installs: ResolvedDirectSkillInstall[] = [];
  const checkoutRoots = new Map<string, string>();

  for (const skill of options.catalog.ownedSkills) {
    for (const target of options.selectedTargets) {
      installs.push({
        target,
        assetId: skill.id,
        origin: "owned",
        sourceDir: skill.skillDir
      });
    }
  }

  for (const asset of options.normalizedAssets) {
    if (asset.kind !== "skill" || asset.locator.type !== "github") {
      continue;
    }

    const selectedTargets = asset.effectiveTargets.filter(
      (target): target is DirectSkillTarget =>
        (directSkillTargets as readonly string[]).includes(target) &&
        options.selectedTargets.includes(target as DirectSkillTarget)
    );

    if (selectedTargets.length === 0) {
      continue;
    }

    const cacheKey = `${asset.sourceId}:${asset.locator.github.repo}:${asset.locator.github.ref ?? "HEAD"}`;
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
      installs.push({
        target,
        assetId: asset.id,
        origin: "external",
        sourceId: asset.sourceId,
        sourceDir
      });
    }
  }

  return installs.sort(compareInstallRecord);
}

async function materializeGithubSource(
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

function readGithubRepoOverridesFromEnv(): Record<string, string> {
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

async function resolveGithubAssetSourceDir(
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
  left: ResolvedDirectSkillInstall,
  right: ResolvedDirectSkillInstall
): number {
  return [
    left.target.localeCompare(right.target),
    left.assetId.localeCompare(right.assetId),
    (left.sourceId ?? "").localeCompare(right.sourceId ?? ""),
    left.origin.localeCompare(right.origin)
  ].find((result) => result !== 0) ?? 0;
}
