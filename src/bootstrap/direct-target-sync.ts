import { dirname, normalize, sep } from "node:path";
import { cp, mkdir, rm } from "node:fs/promises";
import type { SupportedTarget } from "../model/targets";
import type { BootstrapManifestManagedInstall } from "./manifest";
import type { ResolvedManagedInstall } from "./source-resolution";

export interface SyncManagedInstallsOptions {
  allowedRootsByTarget: Record<SupportedTarget, string[]>;
  selectedTargets: SupportedTarget[];
  installs: ResolvedManagedInstall[];
  previousInstalls: BootstrapManifestManagedInstall[];
}

export interface ManagedInstallSyncResult {
  target: SupportedTarget;
  installs: BootstrapManifestManagedInstall[];
}

export async function syncManagedInstalls(
  options: SyncManagedInstallsOptions
): Promise<ManagedInstallSyncResult[]> {
  const results: ManagedInstallSyncResult[] = [];

  for (const target of options.selectedTargets) {
    const desiredInstalls = options.installs
      .filter((install) => install.target === target)
      .sort(compareInstallRecord);
    const previousInstalls = options.previousInstalls
      .filter((install) => install.target === target)
      .sort(compareManifestInstall);
    const desiredPaths = new Set(
      desiredInstalls.map((install) => normalize(install.destinationPath))
    );
    const allowedRoots = options.allowedRootsByTarget[target] ?? [];

    for (const root of allowedRoots) {
      await mkdir(root, { recursive: true });
    }

    for (const install of previousInstalls) {
      const normalizedPath = normalize(install.destinationPath);

      if (desiredPaths.has(normalizedPath)) {
        continue;
      }

      if (isManagedPath(normalizedPath, allowedRoots)) {
        await rm(normalizedPath, {
          recursive: install.installType === "directory",
          force: true
        });
      }
    }

    const appliedInstalls: BootstrapManifestManagedInstall[] = [];

    for (const install of desiredInstalls) {
      await mkdir(dirname(install.destinationPath), { recursive: true });
      await rm(install.destinationPath, {
        recursive: install.installType === "directory",
        force: true
      });
      await cp(install.sourcePath, install.destinationPath, {
        recursive: install.installType === "directory",
        force: true,
        filter: (source) => !source.endsWith(`${sep}.git`) && !source.includes(`${sep}.git${sep}`)
      });

      appliedInstalls.push({
        target,
        assetId: install.assetId,
        kind: install.kind,
        origin: install.origin,
        sourceId: install.sourceId,
        destinationPath: install.destinationPath,
        installType: install.installType,
        installArea: install.installArea
      });
    }

    results.push({
      target,
      installs: appliedInstalls
    });
  }

  return results;
}

function isManagedPath(path: string, allowedRoots: string[]): boolean {
  return allowedRoots.some((root) => {
    const normalizedRoot = normalize(root);

    return path !== normalizedRoot && path.startsWith(`${normalizedRoot}${sep}`);
  });
}

function compareInstallRecord(
  left: ResolvedManagedInstall,
  right: ResolvedManagedInstall
): number {
  return [
    left.target.localeCompare(right.target),
    left.kind.localeCompare(right.kind),
    left.assetId.localeCompare(right.assetId),
    left.destinationPath.localeCompare(right.destinationPath),
    (left.sourceId ?? "").localeCompare(right.sourceId ?? "")
  ].find((result) => result !== 0) ?? 0;
}

function compareManifestInstall(
  left: BootstrapManifestManagedInstall,
  right: BootstrapManifestManagedInstall
): number {
  return [
    left.target.localeCompare(right.target),
    left.kind.localeCompare(right.kind),
    left.assetId.localeCompare(right.assetId),
    left.destinationPath.localeCompare(right.destinationPath),
    (left.sourceId ?? "").localeCompare(right.sourceId ?? "")
  ].find((result) => result !== 0) ?? 0;
}
