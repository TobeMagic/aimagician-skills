import { mkdir } from "node:fs/promises";
import { join } from "node:path";
import {
  resolvePlatformContext,
  type BootstrapPlatform,
  type PlatformContext
} from "../shared/platform";

export interface BootstrapWorkspace {
  platform: BootstrapPlatform;
  rootDir: string;
  manifestPath: string;
  planPath: string;
}

export async function ensureBootstrapWorkspace(
  overrides: Partial<PlatformContext> = {}
): Promise<BootstrapWorkspace> {
  const platformContext = resolvePlatformContext(overrides);
  const rootDir = platformContext.workspaceRoot;

  await mkdir(rootDir, { recursive: true });

  return createWorkspace(rootDir, platformContext.platform);
}

export function resolveBootstrapWorkspace(
  overrides: Partial<PlatformContext> = {}
): BootstrapWorkspace {
  const platformContext = resolvePlatformContext(overrides);

  return createWorkspace(platformContext.workspaceRoot, platformContext.platform);
}

function createWorkspace(
  rootDir: string,
  platform: BootstrapPlatform
): BootstrapWorkspace {
  return {
    platform,
    rootDir,
    manifestPath: join(rootDir, "manifest.json"),
    planPath: join(rootDir, "plan.json")
  };
}
