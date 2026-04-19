import { execFile } from "node:child_process";
import { access, constants, mkdir, rm } from "node:fs/promises";
import { isAbsolute, join, win32 } from "node:path";
import { promisify } from "node:util";
import type { NormalizedAsset } from "../model/assets";
import type { SupportedTarget } from "../model/targets";
import { repositoryRoot } from "../shared/paths";
import type { PlatformContext } from "../shared/platform";
import type { ResolvedTargetHomes } from "./target-homes";

const execFileAsync = promisify(execFile);

export interface CommandSourceReport {
  sourceId: string;
  assetIds: string[];
  targets: SupportedTarget[];
  command: string;
  status: "planned" | "executed";
}

export interface ExecuteCommandSkillSourcesOptions {
  normalizedAssets: NormalizedAsset[];
  selectedTargets: SupportedTarget[];
  workspaceRoot: string;
  platformContext: PlatformContext;
  targetHomes: ResolvedTargetHomes;
}

export interface MaterializeGeneratedCommandSkillSourcesResult {
  materializedDirs: Map<string, Partial<Record<SupportedTarget, string>>>;
  reports: CommandSourceReport[];
}

interface CommandSourceGroup {
  sourceId: string;
  assetIds: Set<string>;
  targets: Set<SupportedTarget>;
  command: {
    run: string;
    shell?: string;
    cwd?: string;
    adapter?: {
      type: "generated-skills";
      paths: Partial<Record<SupportedTarget, string>>;
    };
  };
}

export function previewCommandSkillSources(
  normalizedAssets: NormalizedAsset[],
  selectedTargets: SupportedTarget[]
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
    if (isGeneratedSkillsAdapter(group.command)) {
      continue;
    }

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

export async function materializeGeneratedCommandSkillSources(
  options: ExecuteCommandSkillSourcesOptions
): Promise<MaterializeGeneratedCommandSkillSourcesResult> {
  const groups = [...groupCommandSkillSources(options.normalizedAssets, options.selectedTargets)];
  const materializedDirs = new Map<string, Partial<Record<SupportedTarget, string>>>();
  const reports: CommandSourceReport[] = [];

  for (const [, group] of groups) {
    if (!isGeneratedSkillsAdapter(group.command)) {
      continue;
    }

    const stagingRoot = await materializeGeneratedCommandGroup(group, options);
    const resolvedDirs: Partial<Record<SupportedTarget, string>> = {};

    for (const target of group.targets) {
      const relativeDir = group.command.adapter.paths[target];

      if (!relativeDir) {
        continue;
      }

      const sourceDir = join(stagingRoot, relativeDir);
      await assertSkillDirectory(sourceDir, `${group.sourceId}:${target}`);
      resolvedDirs[target] = sourceDir;
    }

    materializedDirs.set(group.sourceId, resolvedDirs);
    reports.push({
      sourceId: group.sourceId,
      assetIds: [...group.assetIds].sort(),
      targets: [...group.targets].sort(),
      command: group.command.run,
      status: "executed"
    });
  }

  return { materializedDirs, reports };
}

function groupCommandSkillSources(
  normalizedAssets: NormalizedAsset[],
  selectedTargets: SupportedTarget[]
): Map<string, CommandSourceGroup> {
  const groups = new Map<string, CommandSourceGroup>();

  for (const asset of normalizedAssets) {
    if (asset.kind !== "skill" || asset.locator.type !== "command") {
      continue;
    }

    const matchingTargets = asset.effectiveTargets.filter((target) =>
      selectedTargets.includes(target)
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
  const env = createCommandEnvironment(group, options);

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

async function materializeGeneratedCommandGroup(
  group: CommandSourceGroup,
  options: ExecuteCommandSkillSourcesOptions
): Promise<string> {
  const stagingRoot = join(options.workspaceRoot, "generated-command-sources", group.sourceId);

  await rm(stagingRoot, { recursive: true, force: true });
  await mkdir(stagingRoot, { recursive: true });

  const env = createCommandEnvironment(group, options);

  try {
    if (options.platformContext.platform === "windows") {
      await execFileAsync(group.command.shell ?? (process.env.ComSpec ?? "cmd.exe"), [
        "/d",
        "/s",
        "/c",
        group.command.run
      ], { cwd: stagingRoot, env });
    } else {
      await execFileAsync(group.command.shell ?? "sh", ["-lc", group.command.run], {
        cwd: stagingRoot,
        env
      });
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : "unknown command failure";
    throw new Error(`Failed to execute command source ${group.sourceId}: ${message}`);
  }

  return stagingRoot;
}

function resolveCommandCwd(commandCwd: string | undefined): string {
  if (!commandCwd) {
    return repositoryRoot;
  }

  return isAbsolute(commandCwd) ? commandCwd : join(repositoryRoot, commandCwd);
}

function isGeneratedSkillsAdapter(
  command: CommandSourceGroup["command"]
): command is CommandSourceGroup["command"] & {
  adapter: { type: "generated-skills"; paths: Partial<Record<SupportedTarget, string>> };
} {
  return command.adapter?.type === "generated-skills";
}

function createCommandEnvironment(
  group: CommandSourceGroup,
  options: ExecuteCommandSkillSourcesOptions
): NodeJS.ProcessEnv {
  const baseEnv: NodeJS.ProcessEnv = {
    ...process.env,
    AIMAGICIAN_TARGETS: [...group.targets].sort().join(","),
    AIMAGICIAN_SOURCE_ID: group.sourceId,
    AIMAGICIAN_ASSET_IDS: [...group.assetIds].sort().join(","),
    AIMAGICIAN_WORKSPACE_ROOT: options.workspaceRoot,
    AIMAGICIAN_HOME_DIR: options.platformContext.homeDir,
    AIMAGICIAN_CODEX_SKILLS_DIR: options.targetHomes.codex.skillsDir,
    AIMAGICIAN_CLAUDE_SKILLS_DIR: options.targetHomes.claude.skillsDir,
    AIMAGICIAN_OPENCODE_SKILLS_DIR: options.targetHomes.opencode.skillsDir,
    AIMAGICIAN_GEMINI_EXTENSIONS_DIR: options.targetHomes.gemini.extensionsDir,
    AIMAGICIAN_HERMES_SKILLS_DIR: options.targetHomes.hermes.skillsDir,
    AIMAGICIAN_CURSOR_SKILLS_DIR: options.targetHomes.cursor.skillsDir,
    HOME: options.platformContext.homeDir
  };

  if (options.platformContext.platform === "windows") {
    const homeDir = options.platformContext.homeDir;
    const homePath = resolveWindowsHomePath(homeDir);

    return {
      ...baseEnv,
      USERPROFILE: homeDir,
      HOMEDRIVE: resolveWindowsHomeDrive(homeDir),
      HOMEPATH: homePath,
      APPDATA: options.platformContext.configBaseDir,
      LOCALAPPDATA: options.platformContext.stateBaseDir
    };
  }

  return {
    ...baseEnv,
    XDG_CONFIG_HOME: options.platformContext.configBaseDir,
    XDG_STATE_HOME: options.platformContext.stateBaseDir
  };
}

async function assertSkillDirectory(sourceDir: string, assetId: string): Promise<void> {
  try {
    await access(join(sourceDir, "SKILL.md"), constants.F_OK);
  } catch {
    throw new Error(
      `Resolved generated skill directory for ${assetId} does not contain SKILL.md: ${sourceDir}`
    );
  }
}

function resolveWindowsHomeDrive(homeDir: string): string {
  const parsed = win32.parse(homeDir);
  return parsed.root.slice(0, 2);
}

function resolveWindowsHomePath(homeDir: string): string {
  const drive = resolveWindowsHomeDrive(homeDir);
  return homeDir.startsWith(drive) ? homeDir.slice(drive.length) : homeDir;
}
