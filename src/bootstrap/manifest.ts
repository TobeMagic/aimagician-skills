import { readFile, writeFile } from "node:fs/promises";
import type { SupportedTarget } from "../model/targets";

export interface BootstrapManifestAsset {
  id: string;
  origin: "owned" | "external";
  kind: "skill" | "plugin";
  sourceId?: string;
  selectedTargets: SupportedTarget[];
}

export interface BootstrapManifest {
  version: 1;
  updatedAt: string;
  selectedTargets: SupportedTarget[];
  assets: BootstrapManifestAsset[];
}

export async function loadManifest(path: string): Promise<BootstrapManifest | null> {
  try {
    const contents = await readFile(path, "utf8");
    return JSON.parse(contents) as BootstrapManifest;
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
