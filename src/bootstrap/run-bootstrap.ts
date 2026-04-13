import { writeFile } from "node:fs/promises";
import type { CatalogLoadOptions } from "../catalog/load-catalog";
import { type SupportedTarget, supportedTargets } from "../model/targets";
import {
  resolvePlatformContext,
  type PlatformContext
} from "../shared/platform";
import {
  executeCommandSkillSources,
  materializeGeneratedCommandSkillSources,
  previewCommandSkillSources,
  type CommandSourceReport
} from "./command-sources";
import { syncManagedInstalls } from "./direct-target-sync";
import {
  loadManifest,
  manifestsEqual,
  writeManifest,
  type BootstrapManifest,
  type BootstrapManifestCommandInstall,
  type BootstrapManifestManagedInstall
} from "./manifest";
import {
  prepareBootstrapRun,
  type BootstrapPlan
} from "./plan-bootstrap";
import {
  previewPluginReports,
  resolvePluginInstalls,
  type BootstrapPluginReport
} from "./plugin-resolution";
import { resolveManagedSkillInstalls } from "./source-resolution";
import { resolveTargetHomes, type ResolvedTargetHomes } from "./target-homes";
import { ensureBootstrapWorkspace, resolveBootstrapWorkspace } from "./workspace";

export interface RunBootstrapOptions {
  selectedTargets?: SupportedTarget[];
  dryRun?: boolean;
  now?: string;
  catalog?: CatalogLoadOptions;
  platform?: Partial<PlatformContext>;
  githubRepoOverrides?: Record<string, string>;
}

export interface BootstrapTargetReport {
  target: SupportedTarget;
  status: "planned" | "synced" | "deferred";
  installedSkillIds: string[];
  installedPluginIds: string[];
  skillsDir?: string;
  pluginsDir?: string;
  extensionsDir?: string;
  reason?: string;
}

export interface BootstrapRunResult {
  mode: "dry-run" | "apply";
  changed: boolean;
  workspaceRoot: string;
  manifestPath: string;
  planPath: string;
  plan: BootstrapPlan;
  targetReports: BootstrapTargetReport[];
  pluginReports: BootstrapPluginReport[];
  commandReports: CommandSourceReport[];
}

export async function runBootstrap(
  options: RunBootstrapOptions = {}
): Promise<BootstrapRunResult> {
  const selectedTargets = options.selectedTargets ?? [...supportedTargets];
  const platformContext = resolvePlatformContext(options.platform);
  const prepared = await prepareBootstrapRun({
    selectedTargets,
    catalog: options.catalog,
    workspaceRoot: platformContext.workspaceRoot,
    githubRepoOverrides: options.githubRepoOverrides
  });
  const workspace = options.dryRun
    ? resolveBootstrapWorkspace(platformContext)
    : await ensureBootstrapWorkspace(platformContext);
  const targetHomes = resolveTargetHomes(platformContext);

  if (options.dryRun) {
    const pluginReports = await previewPluginReports({
      normalizedAssets: prepared.normalizedAssets,
      selectedTargets,
      targetHomes
    });

    return {
      mode: "dry-run",
      changed: false,
      workspaceRoot: workspace.rootDir,
      manifestPath: workspace.manifestPath,
      planPath: workspace.planPath,
      plan: prepared.plan,
      targetReports: createPreviewTargetReports(prepared.plan, targetHomes, pluginReports),
      pluginReports,
      commandReports: previewCommandSkillSources(prepared.normalizedAssets, selectedTargets)
    };
  }

  const previousManifest = await loadManifest(workspace.manifestPath);
  const retainedManagedInstalls = previousManifest?.managedInstalls.filter(
    (install) => !selectedTargets.includes(install.target)
  ) ?? [];
  const generatedCommandSkillSources = await materializeGeneratedCommandSkillSources({
    normalizedAssets: prepared.normalizedAssets,
    selectedTargets,
    workspaceRoot: workspace.rootDir,
    platformContext,
    targetHomes
  });
  const skillInstalls = await resolveManagedSkillInstalls({
    catalog: prepared.catalog,
    normalizedAssets: prepared.normalizedAssets,
    workspaceRoot: workspace.rootDir,
    selectedTargets,
    targetHomes,
    githubRepoOverrides: options.githubRepoOverrides,
    materializedCommandSourceDirs: generatedCommandSkillSources.materializedDirs
  });
  const pluginResolution = await resolvePluginInstalls({
    normalizedAssets: prepared.normalizedAssets,
    selectedTargets,
    targetHomes,
    workspaceRoot: workspace.rootDir,
    githubRepoOverrides: options.githubRepoOverrides
  });
  const managedSyncResults = await syncManagedInstalls({
    allowedRootsByTarget: createAllowedRootsByTarget(targetHomes),
    selectedTargets,
    installs: [...skillInstalls, ...pluginResolution.installs],
    previousInstalls: previousManifest?.managedInstalls ?? []
  });
  const directCommandReports = await executeCommandSkillSources({
    normalizedAssets: prepared.normalizedAssets,
    selectedTargets,
    workspaceRoot: workspace.rootDir,
    platformContext,
    targetHomes
  });
  const commandReports = [
    ...generatedCommandSkillSources.reports,
    ...directCommandReports
  ].sort((left, right) => left.sourceId.localeCompare(right.sourceId));
  const nextManifest = createManifest(
    prepared.plan,
    options.now,
    [
      ...retainedManagedInstalls,
      ...managedSyncResults.flatMap((result) => result.installs)
    ],
    commandReports
  );
  const changed = !manifestsEqual(previousManifest, nextManifest);
  const targetReports = createAppliedTargetReports(
    prepared.plan,
    targetHomes,
    managedSyncResults,
    pluginResolution.reports
  );

  await writeFile(
    workspace.planPath,
    JSON.stringify(
      {
        ...prepared.plan,
        targetReports,
        pluginReports: pluginResolution.reports,
        commandReports
      },
      null,
      2
    ),
    "utf8"
  );
  await writeManifest(workspace.manifestPath, nextManifest);

  return {
    mode: "apply",
    changed,
    workspaceRoot: workspace.rootDir,
    manifestPath: workspace.manifestPath,
    planPath: workspace.planPath,
    plan: prepared.plan,
    targetReports,
    pluginReports: pluginResolution.reports,
    commandReports
  };
}

function createManifest(
  plan: BootstrapPlan,
  now: string | undefined,
  managedInstalls: BootstrapManifestManagedInstall[],
  commandReports: CommandSourceReport[]
): BootstrapManifest {
  return {
    version: 3,
    updatedAt: now ?? new Date().toISOString(),
    selectedTargets: plan.selectedTargets,
    assets: plan.assets.map((asset) => ({
      id: asset.id,
      origin: asset.origin,
      kind: asset.kind,
      sourceId: asset.sourceId,
      selectedTargets: asset.selectedTargets
    })),
    managedInstalls: [...managedInstalls].sort(compareManagedInstall),
    commandInstalls: commandReports
      .map<BootstrapManifestCommandInstall>((report) => ({
        sourceId: report.sourceId,
        assetIds: [...report.assetIds].sort(),
        targets: [...report.targets].sort(),
        command: report.command
      }))
      .sort(compareCommandInstall)
  };
}

function createPreviewTargetReports(
  plan: BootstrapPlan,
  targetHomes: ResolvedTargetHomes,
  pluginReports: BootstrapPluginReport[]
): BootstrapTargetReport[] {
  return plan.selectedTargets.map((target) => ({
    target,
    status: "planned",
    installedSkillIds: listSkillIdsForTarget(plan, target),
    installedPluginIds: listPluginIdsForTarget(pluginReports, target, "planned"),
    ...resolveReportLocations(targetHomes, target)
  }));
}

function createAppliedTargetReports(
  plan: BootstrapPlan,
  targetHomes: ResolvedTargetHomes,
  managedSyncResults: Awaited<ReturnType<typeof syncManagedInstalls>>,
  pluginReports: BootstrapPluginReport[]
): BootstrapTargetReport[] {
  const installsByTarget = new Map(
    managedSyncResults.map((result) => [result.target, result.installs] as const)
  );

  return plan.selectedTargets.map((target) => {
    const installs = installsByTarget.get(target) ?? [];

    return {
      target,
      status: "synced",
      installedSkillIds: installs
        .filter((install) => install.kind === "skill")
        .map((install) => install.assetId)
        .sort(),
      installedPluginIds: listPluginIdsForTarget(pluginReports, target, "installed"),
      ...resolveReportLocations(targetHomes, target)
    };
  });
}

function resolveReportLocations(
  targetHomes: ResolvedTargetHomes,
  target: SupportedTarget
): Pick<BootstrapTargetReport, "skillsDir" | "pluginsDir" | "extensionsDir"> {
  switch (target) {
    case "codex":
      return { skillsDir: targetHomes.codex.skillsDir };
    case "claude":
      return { skillsDir: targetHomes.claude.skillsDir };
    case "opencode":
      return {
        skillsDir: targetHomes.opencode.skillsDir,
        pluginsDir: targetHomes.opencode.pluginsDir
      };
    case "gemini":
      return { extensionsDir: targetHomes.gemini.extensionsDir };
    default:
      return {};
  }
}

function listSkillIdsForTarget(
  plan: BootstrapPlan,
  target: SupportedTarget
): string[] {
  return plan.assets
    .filter((asset) => asset.kind === "skill" && asset.selectedTargets.includes(target))
    .map((asset) => asset.id)
    .sort();
}

function listPluginIdsForTarget(
  pluginReports: BootstrapPluginReport[],
  target: SupportedTarget,
  status: "planned" | "installed"
): string[] {
  return pluginReports
    .filter((report) => report.target === target && report.status === status)
    .map((report) => report.assetId)
    .sort();
}

function createAllowedRootsByTarget(
  targetHomes: ResolvedTargetHomes
): Record<SupportedTarget, string[]> {
  return {
    codex: [targetHomes.codex.skillsDir],
    claude: [targetHomes.claude.skillsDir],
    opencode: [targetHomes.opencode.skillsDir, targetHomes.opencode.pluginsDir],
    gemini: [targetHomes.gemini.extensionsDir]
  };
}

function compareManagedInstall(
  left: BootstrapManifestManagedInstall,
  right: BootstrapManifestManagedInstall
): number {
  return [
    left.target.localeCompare(right.target),
    left.kind.localeCompare(right.kind),
    left.assetId.localeCompare(right.assetId),
    left.destinationPath.localeCompare(right.destinationPath),
    (left.sourceId ?? "").localeCompare(right.sourceId ?? "")
  ].find((result) => result !== 0) ?? 0;
}

function compareCommandInstall(
  left: BootstrapManifestCommandInstall,
  right: BootstrapManifestCommandInstall
): number {
  return [
    left.sourceId.localeCompare(right.sourceId),
    left.command.localeCompare(right.command),
    left.assetIds.join(",").localeCompare(right.assetIds.join(",")),
    left.targets.join(",").localeCompare(right.targets.join(","))
  ].find((result) => result !== 0) ?? 0;
}
