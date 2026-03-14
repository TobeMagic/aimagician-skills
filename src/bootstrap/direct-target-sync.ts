import { basename, join, normalize, sep } from "node:path";
import { cp, mkdir, rm } from "node:fs/promises";
import type { BootstrapManifestDirectInstall } from "./manifest";
import type { ResolvedDirectSkillInstall } from "./source-resolution";
import type { DirectTargetHome, DirectSkillTarget } from "./target-homes";

export interface SyncDirectTargetsOptions {
  targetHomes: Record<DirectSkillTarget, DirectTargetHome>;
  selectedTargets: DirectSkillTarget[];
  installs: ResolvedDirectSkillInstall[];
  previousInstalls: BootstrapManifestDirectInstall[];
}

export interface DirectTargetSyncResult {
  target: DirectSkillTarget;
  skillsDir: string;
  installedSkillIds: string[];
  manifestInstalls: BootstrapManifestDirectInstall[];
}

export async function syncDirectTargets(
  options: SyncDirectTargetsOptions
): Promise<DirectTargetSyncResult[]> {
  const results: DirectTargetSyncResult[] = [];

  for (const target of options.selectedTargets) {
    const targetHome = options.targetHomes[target];
    const desiredInstalls = options.installs
      .filter((install) => install.target === target)
      .sort((left, right) => left.assetId.localeCompare(right.assetId));
    const previousInstalls = options.previousInstalls
      .filter((install) => install.target === target)
      .sort((left, right) => left.assetId.localeCompare(right.assetId));
    const desiredPaths = new Set(
      desiredInstalls.map((install) => normalize(joinTargetPath(targetHome.skillsDir, install.assetId)))
    );

    await mkdir(targetHome.skillsDir, { recursive: true });

    for (const install of previousInstalls) {
      const normalizedPath = normalize(install.destinationDir);

      if (desiredPaths.has(normalizedPath)) {
        continue;
      }

      if (isManagedChildDirectory(normalizedPath, targetHome.skillsDir)) {
        await rm(normalizedPath, { recursive: true, force: true });
      }
    }

    const manifestInstalls: BootstrapManifestDirectInstall[] = [];

    for (const install of desiredInstalls) {
      const destinationDir = joinTargetPath(targetHome.skillsDir, install.assetId);

      await rm(destinationDir, { recursive: true, force: true });
      await cp(install.sourceDir, destinationDir, {
        recursive: true,
        force: true,
        filter: (source) => basename(source) !== ".git"
      });

      manifestInstalls.push({
        target,
        assetId: install.assetId,
        origin: install.origin,
        sourceId: install.sourceId,
        destinationDir
      });
    }

    results.push({
      target,
      skillsDir: targetHome.skillsDir,
      installedSkillIds: manifestInstalls.map((install) => install.assetId),
      manifestInstalls
    });
  }

  return results;
}

function isManagedChildDirectory(path: string, skillsDir: string): boolean {
  const normalizedSkillsDir = normalize(skillsDir);

  return (
    path !== normalizedSkillsDir &&
    path.startsWith(`${normalizedSkillsDir}${sep}`)
  );
}

function joinTargetPath(skillsDir: string, assetId: string): string {
  return join(skillsDir, assetId);
}
