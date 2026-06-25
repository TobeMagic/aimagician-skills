import { dirname, normalize, sep } from "node:path";
import { cp, mkdir, rm } from "node:fs/promises";
import type { SupportedTarget } from "../model/targets";
import type { BootstrapManifestManagedInstall } from "./manifest";
import type { ResolvedManagedInstall } from "./source-resolution";
import { shouldCopyManagedSource } from "./copy-filter";

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

export type ManagedInstallSyncOperation =
  | ManagedInstallWriteOperation
  | ManagedInstallRemoveOperation
  | ManagedInstallSkipOperation;

export interface ManagedInstallWriteOperation {
  kind: "create" | "overwrite";
  target: SupportedTarget;
  assetId: string;
  assetKind: "skill" | "plugin";
  origin: "owned" | "external";
  sourceId?: string;
  sourcePath: string;
  destinationPath: string;
  installType: "directory" | "file";
  installArea: "skills" | "plugins" | "extensions" | "rules";
}

export interface ManagedInstallRemoveOperation {
  kind: "remove";
  target: SupportedTarget;
  assetId: string;
  assetKind: "skill" | "plugin";
  origin: "owned" | "external";
  sourceId?: string;
  destinationPath: string;
  installType: "directory" | "file";
  installArea: "skills" | "plugins" | "extensions" | "rules";
}

export interface ManagedInstallSkipOperation {
  kind: "skip";
  target: SupportedTarget;
  assetId: string;
  assetKind: "skill" | "plugin";
  origin: "owned" | "external";
  sourceId?: string;
  destinationPath: string;
  installType: "directory" | "file";
  installArea: "skills" | "plugins" | "extensions" | "rules";
  reason: "outside-allowed-roots";
}

export function planManagedInstallSync(
  options: SyncManagedInstallsOptions
): ManagedInstallSyncOperation[] {
  const operations: ManagedInstallSyncOperation[] = [];

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
    const previousPaths = new Set(
      previousInstalls.map((install) => normalize(install.destinationPath))
    );
    const allowedRoots = options.allowedRootsByTarget[target] ?? [];

    for (const install of previousInstalls) {
      const normalizedPath = normalize(install.destinationPath);

      if (desiredPaths.has(normalizedPath)) {
        continue;
      }

      if (isManagedPath(normalizedPath, allowedRoots)) {
        operations.push(toRemoveOperation(install));
      } else {
        operations.push(toSkipOperation(install));
      }
    }

    for (const install of desiredInstalls) {
      operations.push(toWriteOperation(install, previousPaths));
    }
  }

  return operations.sort(compareSyncOperations);
}

export async function syncManagedInstalls(
  options: SyncManagedInstallsOptions
): Promise<ManagedInstallSyncResult[]> {
  const operations = planManagedInstallSync(options);
  const installsByTarget = new Map<SupportedTarget, BootstrapManifestManagedInstall[]>();

  for (const target of options.selectedTargets) {
    const allowedRoots = options.allowedRootsByTarget[target] ?? [];

    for (const root of allowedRoots) {
      await mkdir(root, { recursive: true });
    }

    installsByTarget.set(target, []);
  }

  for (const operation of operations) {
    if (operation.kind === "skip") {
      continue;
    }

    if (operation.kind === "remove") {
      await rm(operation.destinationPath, {
        recursive: operation.installType === "directory",
        force: true
      });
      continue;
    }

    await mkdir(dirname(operation.destinationPath), { recursive: true });
    await rm(operation.destinationPath, {
      recursive: operation.installType === "directory",
      force: true
    });
    await cp(operation.sourcePath, operation.destinationPath, {
      recursive: operation.installType === "directory",
      force: true,
      filter: shouldCopyManagedSource
    });

    installsByTarget.get(operation.target)?.push({
      target: operation.target,
      assetId: operation.assetId,
      kind: operation.assetKind,
      origin: operation.origin,
      sourceId: operation.sourceId,
      destinationPath: operation.destinationPath,
      installType: operation.installType,
      installArea: operation.installArea
    });
  }

  return options.selectedTargets.map((target) => ({
    target,
    installs: installsByTarget.get(target) ?? []
  }));
}

function isManagedPath(path: string, allowedRoots: string[]): boolean {
  return allowedRoots.some((root) => {
    const normalizedRoot = normalize(root);

    return path !== normalizedRoot && path.startsWith(`${normalizedRoot}${sep}`);
  });
}

function toRemoveOperation(
  install: BootstrapManifestManagedInstall
): ManagedInstallRemoveOperation {
  return {
    kind: "remove",
    target: install.target,
    assetId: install.assetId,
    assetKind: install.kind,
    origin: install.origin,
    sourceId: install.sourceId,
    destinationPath: install.destinationPath,
    installType: install.installType,
    installArea: install.installArea
  };
}

function toSkipOperation(
  install: BootstrapManifestManagedInstall
): ManagedInstallSkipOperation {
  return {
    kind: "skip",
    target: install.target,
    assetId: install.assetId,
    assetKind: install.kind,
    origin: install.origin,
    sourceId: install.sourceId,
    destinationPath: install.destinationPath,
    installType: install.installType,
    installArea: install.installArea,
    reason: "outside-allowed-roots"
  };
}

function toWriteOperation(
  install: ResolvedManagedInstall,
  previousPaths: Set<string>
): ManagedInstallWriteOperation {
  return {
    kind: previousPaths.has(normalize(install.destinationPath)) ? "overwrite" : "create",
    target: install.target,
    assetId: install.assetId,
    assetKind: install.kind,
    origin: install.origin,
    sourceId: install.sourceId,
    sourcePath: install.sourcePath,
    destinationPath: install.destinationPath,
    installType: install.installType,
    installArea: install.installArea
  };
}

function compareSyncOperations(
  left: ManagedInstallSyncOperation,
  right: ManagedInstallSyncOperation
): number {
  return [
    operationPriority(left.kind) - operationPriority(right.kind),
    left.target.localeCompare(right.target),
    left.assetId.localeCompare(right.assetId),
    left.destinationPath.localeCompare(right.destinationPath),
    (left.sourceId ?? "").localeCompare(right.sourceId ?? "")
  ].find((result) => result !== 0) ?? 0;
}

function operationPriority(kind: ManagedInstallSyncOperation["kind"]): number {
  return { remove: 0, skip: 1, overwrite: 2, create: 3 }[kind];
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
