import { posix, win32 } from "node:path";
import type { InstallScope } from "../model/scopes";
import type { SupportedTarget } from "../model/targets";
import {
  resolvePlatformContext,
  type PlatformContext
} from "../shared/platform";

export const directSkillTargets = ["codex", "claude", "opencode", "hermes", "copilot"] as const;
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

export interface HermesTargetHome extends DirectTargetHome {
  target: "hermes";
}

export interface CursorTargetHome {
  target: "cursor";
  rootDir: string;
  skillsDir: string;
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
  hermes: HermesTargetHome;
  cursor: CursorTargetHome;
  copilot: DirectTargetHome;
}

export interface ResolveTargetHomesOptions extends Partial<PlatformContext> {
  scope?: InstallScope;
  projectDir?: string;
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
  overrides: ResolveTargetHomesOptions = {}
): ResolvedTargetHomes {
  const platformContext = resolvePlatformContext(overrides);
  const pathApi = platformContext.platform === "windows" ? win32 : posix;
  const baseDir = overrides.scope === "project"
    ? overrides.projectDir ?? process.cwd()
    : platformContext.homeDir;
  const codexRoot = pathApi.join(baseDir, ".codex");
  const claudeRoot = pathApi.join(baseDir, ".claude");
  const opencodeRoot = overrides.scope === "project"
    ? pathApi.join(baseDir, ".opencode")
    : pathApi.join(platformContext.configBaseDir, "opencode");
  const geminiRoot = pathApi.join(baseDir, ".gemini");
  const hermesRoot = pathApi.join(baseDir, ".hermes");
  const cursorRoot = pathApi.join(baseDir, ".cursor");
  const copilotRoot = overrides.scope === "project"
    ? pathApi.join(baseDir, ".github")
    : pathApi.join(baseDir, ".copilot");

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
    },
    hermes: {
      target: "hermes",
      rootDir: hermesRoot,
      skillsDir: pathApi.join(hermesRoot, "skills")
    },
    cursor: {
      target: "cursor",
      rootDir: cursorRoot,
      skillsDir: pathApi.join(cursorRoot, "skills")
    },
    copilot: {
      target: "copilot",
      rootDir: copilotRoot,
      skillsDir: pathApi.join(copilotRoot, "skills")
    }
  };
}

export function resolveDirectTargetHomes(
  overrides: ResolveTargetHomesOptions = {}
): Record<DirectSkillTarget, DirectTargetHome> {
  const homes = resolveTargetHomes(overrides);

  return {
    codex: homes.codex,
    claude: homes.claude,
    opencode: homes.opencode,
    hermes: homes.hermes,
    copilot: homes.copilot
  };
}
