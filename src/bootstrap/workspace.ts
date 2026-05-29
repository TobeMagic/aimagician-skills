import { mkdir } from "node:fs/promises";
import { join } from "node:path";
import {
  resolvePlatformContext,
  type BootstrapPlatform,
  type PlatformContext
} from "../shared/platform";
import type { InstallScope } from "../model/scopes";

export interface BootstrapWorkspace {
  platform: BootstrapPlatform;
  rootDir: string;
  manifestPath: string;
  planPath: string;
}

export interface BootstrapWorkspaceOptions extends Partial<PlatformContext> {
  scope?: InstallScope;
  projectDir?: string;
}

export async function ensureBootstrapWorkspace(
  overrides: BootstrapWorkspaceOptions = {}
): Promise<BootstrapWorkspace> {
  const platformContext = resolvePlatformContext(overrides);
  const rootDir = resolveWorkspaceRoot(platformContext, overrides);

  await mkdir(rootDir, { recursive: true });

  return createWorkspace(rootDir, platformContext.platform);
}

export function resolveBootstrapWorkspace(
  overrides: BootstrapWorkspaceOptions = {}
): BootstrapWorkspace {
  const platformContext = resolvePlatformContext(overrides);

  return createWorkspace(resolveWorkspaceRoot(platformContext, overrides), platformContext.platform);
}

function resolveWorkspaceRoot(
  platformContext: PlatformContext,
  options: BootstrapWorkspaceOptions
): string {
  if (options.scope === "project") {
    return join(options.projectDir ?? process.cwd(), ".aimagician-skills");
  }

  return platformContext.workspaceRoot;
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
