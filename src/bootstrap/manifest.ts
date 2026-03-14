import { readFile, writeFile } from "node:fs/promises";
import type { SupportedTarget } from "../model/targets";
import type { DirectSkillTarget } from "./target-homes";

export interface BootstrapManifestAsset {
  id: string;
  origin: "owned" | "external";
  kind: "skill" | "plugin";
  sourceId?: string;
  selectedTargets: SupportedTarget[];
}

export interface BootstrapManifestDirectInstall {
  target: DirectSkillTarget;
  assetId: string;
  origin: "owned" | "external";
  sourceId?: string;
  destinationDir: string;
}

export interface BootstrapManifest {
  version: 2;
  updatedAt: string;
  selectedTargets: SupportedTarget[];
  assets: BootstrapManifestAsset[];
  directInstalls: BootstrapManifestDirectInstall[];
}

export async function loadManifest(path: string): Promise<BootstrapManifest | null> {
  try {
    const contents = await readFile(path, "utf8");
    const parsed = JSON.parse(contents) as Partial<BootstrapManifest> & {
      version?: number;
    };

    return {
      version: 2,
      updatedAt: parsed.updatedAt ?? "",
      selectedTargets: parsed.selectedTargets ?? [],
      assets: parsed.assets ?? [],
      directInstalls: parsed.directInstalls ?? []
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
