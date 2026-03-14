import { readFile, writeFile } from "node:fs/promises";
import type { SupportedTarget } from "../model/targets";

export interface BootstrapManifestAsset {
  id: string;
  origin: "owned" | "external";
  kind: "skill" | "plugin";
  sourceId?: string;
  selectedTargets: SupportedTarget[];
}

export interface BootstrapManifestManagedInstall {
  target: SupportedTarget;
  assetId: string;
  kind: "skill" | "plugin";
  origin: "owned" | "external";
  sourceId?: string;
  destinationPath: string;
  installType: "directory" | "file";
  installArea: "skills" | "plugins" | "extensions";
}

export interface BootstrapManifest {
  version: 3;
  updatedAt: string;
  selectedTargets: SupportedTarget[];
  assets: BootstrapManifestAsset[];
  managedInstalls: BootstrapManifestManagedInstall[];
}

export async function loadManifest(path: string): Promise<BootstrapManifest | null> {
  try {
    const contents = await readFile(path, "utf8");
    const parsed = JSON.parse(contents) as Partial<BootstrapManifest> & {
      version?: number;
      directInstalls?: Array<{
        target: SupportedTarget;
        assetId: string;
        origin: "owned" | "external";
        sourceId?: string;
        destinationDir: string;
      }>;
    };
    const managedInstalls =
      parsed.managedInstalls ??
      parsed.directInstalls?.map<BootstrapManifestManagedInstall>((install) => ({
        target: install.target,
        assetId: install.assetId,
        kind: "skill",
        origin: install.origin,
        sourceId: install.sourceId,
        destinationPath: install.destinationDir,
        installType: "directory",
        installArea: "skills"
      })) ??
      [];

    return {
      version: 3,
      updatedAt: parsed.updatedAt ?? "",
      selectedTargets: parsed.selectedTargets ?? [],
      assets: parsed.assets ?? [],
      managedInstalls
    };
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return null;
    }

    throw error;
  }
}

export async function writeManifest(
  path: string,
  manifest: BootstrapManifest
): Promise<void> {
  await writeFile(path, JSON.stringify(manifest, null, 2), "utf8");
}

export function manifestsEqual(
  left: BootstrapManifest | null,
  right: BootstrapManifest
): boolean {
  if (!left) {
    return false;
  }

  return JSON.stringify(left) === JSON.stringify(right);
}
