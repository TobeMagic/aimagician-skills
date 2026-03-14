import { execFile } from "node:child_process";
import { isAbsolute, join } from "node:path";
import { promisify } from "node:util";
import type { NormalizedAsset } from "../model/assets";
import { repositoryRoot } from "../shared/paths";
import type { PlatformContext } from "../shared/platform";
import type { DirectSkillTarget, DirectTargetHome } from "./target-homes";

const execFileAsync = promisify(execFile);

export interface CommandSourceReport {
  sourceId: string;
  assetIds: string[];
  targets: DirectSkillTarget[];
  command: string;
  status: "planned" | "executed";
}

export interface ExecuteCommandSkillSourcesOptions {
  normalizedAssets: NormalizedAsset[];
  selectedTargets: DirectSkillTarget[];
  workspaceRoot: string;
  platformContext: PlatformContext;
  targetHomes: Record<DirectSkillTarget, DirectTargetHome>;
}

interface CommandSourceGroup {
  sourceId: string;
  assetIds: Set<string>;
  targets: Set<DirectSkillTarget>;
  command: {
    run: string;
    shell?: string;
    cwd?: string;
  };
}

export function previewCommandSkillSources(
  normalizedAssets: NormalizedAsset[],
  selectedTargets: DirectSkillTarget[]
): CommandSourceReport[] {
  return [...groupCommandSkillSources(normalizedAssets, selectedTargets)].map(
    ([, group]) => ({
      sourceId: group.sourceId,
      assetIds: [...group.assetIds].sort(),
      targets: [...group.targets].sort(),
      command: group.command.run,
      status: "planned"
    })
  );
}

export async function executeCommandSkillSources(
  options: ExecuteCommandSkillSourcesOptions
): Promise<CommandSourceReport[]> {
  const groups = [...groupCommandSkillSources(options.normalizedAssets, options.selectedTargets)];
  const reports: CommandSourceReport[] = [];

  for (const [, group] of groups) {
    await runCommandGroup(group, options);

    reports.push({
      sourceId: group.sourceId,
      assetIds: [...group.assetIds].sort(),
      targets: [...group.targets].sort(),
      command: group.command.run,
      status: "executed"
    });
  }

  return reports;
}

function groupCommandSkillSources(
  normalizedAssets: NormalizedAsset[],
  selectedTargets: DirectSkillTarget[]
): Map<string, CommandSourceGroup> {
  const groups = new Map<string, CommandSourceGroup>();

  for (const asset of normalizedAssets) {
    if (asset.kind !== "skill" || asset.locator.type !== "command") {
      continue;
    }

    const matchingTargets = asset.effectiveTargets.filter(
      (target): target is DirectSkillTarget =>
        selectedTargets.includes(target as DirectSkillTarget)
    );

    if (matchingTargets.length === 0) {
      continue;
    }

    const existing = groups.get(asset.sourceId);

    if (existing) {
      existing.assetIds.add(asset.id);
      for (const target of matchingTargets) {
        existing.targets.add(target);
      }
      continue;
    }

    groups.set(asset.sourceId, {
      sourceId: asset.sourceId,
      assetIds: new Set([asset.id]),
      targets: new Set(matchingTargets),
      command: asset.locator.command
    });
  }

  return new Map([...groups.entries()].sort(([left], [right]) => left.localeCompare(right)));
}

async function runCommandGroup(
  group: CommandSourceGroup,
  options: ExecuteCommandSkillSourcesOptions
): Promise<void> {
  const cwd = resolveCommandCwd(group.command.cwd);
  const env = {
    ...process.env,
    AIMAGICIAN_TARGETS: [...group.targets].sort().join(","),
    AIMAGICIAN_SOURCE_ID: group.sourceId,
    AIMAGICIAN_ASSET_IDS: [...group.assetIds].sort().join(","),
    AIMAGICIAN_WORKSPACE_ROOT: options.workspaceRoot,
    AIMAGICIAN_HOME_DIR: options.platformContext.homeDir,
    AIMAGICIAN_CODEX_SKILLS_DIR: options.targetHomes.codex.skillsDir,
    AIMAGICIAN_CLAUDE_SKILLS_DIR: options.targetHomes.claude.skillsDir,
    AIMAGICIAN_OPENCODE_SKILLS_DIR: options.targetHomes.opencode.skillsDir
  };

  try {
    if (options.platformContext.platform === "windows") {
      await execFileAsync(group.command.shell ?? (process.env.ComSpec ?? "cmd.exe"), [
        "/d",
        "/s",
        "/c",
        group.command.run
      ], { cwd, env });
      return;
    }

    await execFileAsync(group.command.shell ?? "sh", ["-lc", group.command.run], {
      cwd,
      env
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "unknown command failure";
    throw new Error(`Failed to execute command source ${group.sourceId}: ${message}`);
  }
}

function resolveCommandCwd(commandCwd: string | undefined): string {
  if (!commandCwd) {
    return repositoryRoot;
  }

  return isAbsolute(commandCwd) ? commandCwd : join(repositoryRoot, commandCwd);
}
