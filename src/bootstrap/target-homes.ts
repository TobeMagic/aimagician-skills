import { posix, win32 } from "node:path";
import type { SupportedTarget } from "../model/targets";
import {
  resolvePlatformContext,
  type PlatformContext
} from "../shared/platform";

export const directSkillTargets = ["codex", "claude", "opencode"] as const;
export const pluginFileTargets = ["opencode"] as const;

export type DirectSkillTarget = (typeof directSkillTargets)[number];
export type PluginFileTarget = (typeof pluginFileTargets)[number];

export interface DirectTargetHome {
  target: DirectSkillTarget;
  rootDir: string;
  skillsDir: string;
}

export interface ClaudeTargetHome extends DirectTargetHome {
  target: "claude";
  settingsPath: string;
}

export interface OpenCodeTargetHome extends DirectTargetHome {
  target: "opencode";
  pluginsDir: string;
}

export interface GeminiTargetHome {
  target: "gemini";
  rootDir: string;
  extensionsDir: string;
}

export interface ResolvedTargetHomes {
  codex: DirectTargetHome;
  claude: ClaudeTargetHome;
  opencode: OpenCodeTargetHome;
  gemini: GeminiTargetHome;
}

export function isDirectSkillTarget(
  target: SupportedTarget
): target is DirectSkillTarget {
  return (directSkillTargets as readonly string[]).includes(target);
}

export function isPluginFileTarget(
  target: SupportedTarget
): target is PluginFileTarget {
  return (pluginFileTargets as readonly string[]).includes(target);
}

export function resolveTargetHomes(
  overrides: Partial<PlatformContext> = {}
): ResolvedTargetHomes {
  const platformContext = resolvePlatformContext(overrides);
  const pathApi = platformContext.platform === "windows" ? win32 : posix;
  const codexRoot = pathApi.join(platformContext.homeDir, ".codex");
  const claudeRoot = pathApi.join(platformContext.homeDir, ".claude");
  const opencodeRoot = pathApi.join(platformContext.configBaseDir, "opencode");
  const geminiRoot = pathApi.join(platformContext.homeDir, ".gemini");

  return {
    codex: {
      target: "codex",
      rootDir: codexRoot,
      skillsDir: pathApi.join(codexRoot, "skills")
    },
    claude: {
      target: "claude",
      rootDir: claudeRoot,
      skillsDir: pathApi.join(claudeRoot, "skills"),
      settingsPath: pathApi.join(claudeRoot, "settings.json")
    },
    opencode: {
      target: "opencode",
      rootDir: opencodeRoot,
      skillsDir: pathApi.join(opencodeRoot, "skills"),
      pluginsDir: pathApi.join(opencodeRoot, "plugins")
    },
    gemini: {
      target: "gemini",
      rootDir: geminiRoot,
      extensionsDir: pathApi.join(geminiRoot, "extensions")
    }
  };
}

export function resolveDirectTargetHomes(
  overrides: Partial<PlatformContext> = {}
): Record<DirectSkillTarget, DirectTargetHome> {
  const homes = resolveTargetHomes(overrides);

  return {
    codex: homes.codex,
    claude: homes.claude,
    opencode: homes.opencode
  };
}
