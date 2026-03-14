import { posix, win32 } from "node:path";
import type { SupportedTarget } from "../model/targets";
import {
  resolvePlatformContext,
  type PlatformContext
} from "../shared/platform";

export const directSkillTargets = ["codex", "claude", "opencode"] as const;

export type DirectSkillTarget = (typeof directSkillTargets)[number];

export interface DirectTargetHome {
  target: DirectSkillTarget;
  rootDir: string;
  skillsDir: string;
}

export function isDirectSkillTarget(
  target: SupportedTarget
): target is DirectSkillTarget {
  return (directSkillTargets as readonly string[]).includes(target);
}

export function resolveDirectTargetHomes(
  overrides: Partial<PlatformContext> = {}
): Record<DirectSkillTarget, DirectTargetHome> {
  const platformContext = resolvePlatformContext(overrides);
  const pathApi = platformContext.platform === "windows" ? win32 : posix;
  const codexRoot = pathApi.join(platformContext.homeDir, ".codex");
  const claudeRoot = pathApi.join(platformContext.homeDir, ".claude");
  const opencodeRoot = pathApi.join(platformContext.configBaseDir, "opencode");

  return {
    codex: {
      target: "codex",
      rootDir: codexRoot,
      skillsDir: pathApi.join(codexRoot, "skills")
    },
    claude: {
      target: "claude",
      rootDir: claudeRoot,
      skillsDir: pathApi.join(claudeRoot, "skills")
    },
    opencode: {
      target: "opencode",
      rootDir: opencodeRoot,
      skillsDir: pathApi.join(opencodeRoot, "skills")
    }
  };
}
