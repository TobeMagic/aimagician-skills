import { homedir, platform as getNodePlatform } from "node:os";
import { posix, win32 } from "node:path";

export type BootstrapPlatform = "windows" | "linux";

export interface PlatformContext {
  platform: BootstrapPlatform;
  homeDir: string;
  stateBaseDir: string;
  workspaceRoot: string;
}

export function resolvePlatformContext(
  overrides: Partial<PlatformContext> = {}
): PlatformContext {
  const platform = overrides.platform ?? detectPlatform();
  const homeDir = overrides.homeDir ?? homedir();
  const stateBaseDir =
    overrides.stateBaseDir ??
    process.env.AIMAGICIAN_STATE_BASE_DIR ??
    resolveStateBaseDir(platform, homeDir);

  return {
    platform,
    homeDir,
    stateBaseDir,
    workspaceRoot:
      overrides.workspaceRoot ??
      process.env.AIMAGICIAN_WORKSPACE_ROOT ??
      (platform === "windows"
        ? win32.join(stateBaseDir, "aimagician-skills")
        : posix.join(stateBaseDir, "aimagician-skills"))
  };
}

export function detectPlatform(): BootstrapPlatform {
  return getNodePlatform() === "win32" ? "windows" : "linux";
}

function resolveStateBaseDir(platform: BootstrapPlatform, homeDir: string): string {
  if (platform === "windows") {
    return (
      process.env.LOCALAPPDATA ??
      process.env.APPDATA ??
      win32.join(homeDir, "AppData", "Local")
    );
  }

  return process.env.XDG_STATE_HOME ?? posix.join(homeDir, ".local", "state");
}
