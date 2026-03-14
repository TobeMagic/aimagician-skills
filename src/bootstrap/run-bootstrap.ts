import { writeFile } from "node:fs/promises";
import type { CatalogLoadOptions } from "../catalog/load-catalog";
import { type SupportedTarget, supportedTargets } from "../model/targets";
import {
  resolvePlatformContext,
  type PlatformContext
} from "../shared/platform";
import {
  executeCommandSkillSources,
  previewCommandSkillSources,
  type CommandSourceReport
} from "./command-sources";
import { syncDirectTargets } from "./direct-target-sync";
import { ensureBootstrapWorkspace, resolveBootstrapWorkspace } from "./workspace";
import {
  loadManifest,
  manifestsEqual,
  writeManifest,
  type BootstrapManifest,
  type BootstrapManifestDirectInstall
} from "./manifest";
import {
  prepareBootstrapRun,
  type BootstrapPlan
} from "./plan-bootstrap";
import { resolveDirectSkillInstalls } from "./source-resolution";
import {
  isDirectSkillTarget,
  resolveDirectTargetHomes
} from "./target-homes";

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
  skillsDir?: string;
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
  commandReports: CommandSourceReport[];
}

export async function runBootstrap(
  options: RunBootstrapOptions = {}
): Promise<BootstrapRunResult> {
  const selectedTargets = options.selectedTargets ?? [...supportedTargets];
  const prepared = await prepareBootstrapRun({
    selectedTargets,
    catalog: options.catalog
  });
  const platformContext = resolvePlatformContext(options.platform);
  const workspace = options.dryRun
    ? resolveBootstrapWorkspace(platformContext)
    : await ensureBootstrapWorkspace(platformContext);
  const targetHomes = resolveDirectTargetHomes(platformContext);
  const selectedDirectTargets = selectedTargets.filter(isDirectSkillTarget);

  if (options.dryRun) {
    return {
      mode: "dry-run",
      changed: false,
      workspaceRoot: workspace.rootDir,
      manifestPath: workspace.manifestPath,
      planPath: workspace.planPath,
      plan: prepared.plan,
      targetReports: createPreviewTargetReports(prepared.plan, targetHomes),
      commandReports: previewCommandSkillSources(
        prepared.normalizedAssets,
        selectedDirectTargets
      )
    };
  }

  const previousManifest = await loadManifest(workspace.manifestPath);
  const retainedDirectInstalls = previousManifest?.directInstalls.filter(
    (install) => !selectedDirectTargets.includes(install.target)
  ) ?? [];
  const resolvedInstalls = await resolveDirectSkillInstalls({
    catalog: prepared.catalog,
    normalizedAssets: prepared.normalizedAssets,
    workspaceRoot: workspace.rootDir,
    selectedTargets: selectedDirectTargets,
    githubRepoOverrides: options.githubRepoOverrides
  });
  const directSyncResults = await syncDirectTargets({
    targetHomes,
    selectedTargets: selectedDirectTargets,
    installs: resolvedInstalls,
    previousInstalls: previousManifest?.directInstalls ?? []
  });
  const commandReports = await executeCommandSkillSources({
    normalizedAssets: prepared.normalizedAssets,
    selectedTargets: selectedDirectTargets,
    workspaceRoot: workspace.rootDir,
    platformContext,
    targetHomes
  });
  const nextManifest = createManifest(
    prepared.plan,
    options.now,
    [
      ...retainedDirectInstalls,
      ...directSyncResults.flatMap((result) => result.manifestInstalls)
    ]
  );
  const changed = !manifestsEqual(previousManifest, nextManifest);
  const targetReports = createAppliedTargetReports(prepared.plan, targetHomes, directSyncResults);

  await writeFile(
    workspace.planPath,
    JSON.stringify(
      {
        ...prepared.plan,
        targetReports,
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
    commandReports
  };
}

function createManifest(
  plan: BootstrapPlan,
  now: string | undefined,
  directInstalls: BootstrapManifestDirectInstall[]
): BootstrapManifest {
  return {
    version: 2,
    updatedAt: now ?? new Date().toISOString(),
    selectedTargets: plan.selectedTargets,
    assets: plan.assets.map((asset) => ({
      id: asset.id,
      origin: asset.origin,
      kind: asset.kind,
      sourceId: asset.sourceId,
      selectedTargets: asset.selectedTargets
    })),
    directInstalls: [...directInstalls].sort(compareDirectInstall)
  };
}

function createPreviewTargetReports(
  plan: BootstrapPlan,
  targetHomes: ReturnType<typeof resolveDirectTargetHomes>
): BootstrapTargetReport[] {
  return plan.selectedTargets.map((target) => {
    const installedSkillIds = listSkillIdsForTarget(plan, target);

    if (isDirectSkillTarget(target)) {
      return {
        target,
        status: "planned",
        installedSkillIds,
        skillsDir: targetHomes[target].skillsDir
      };
    }

    return {
      target,
      status: "deferred",
      installedSkillIds,
      reason: "Gemini direct target adapter lands in Phase 4"
    };
  });
}

function createAppliedTargetReports(
  plan: BootstrapPlan,
  targetHomes: ReturnType<typeof resolveDirectTargetHomes>,
  directSyncResults: Awaited<ReturnType<typeof syncDirectTargets>>
): BootstrapTargetReport[] {
  const resultsByTarget = new Map(
    directSyncResults.map((result) => [result.target, result] as const)
  );

  return plan.selectedTargets.map((target) => {
    if (isDirectSkillTarget(target)) {
      const result = resultsByTarget.get(target);

      return {
        target,
        status: "synced",
        installedSkillIds: result?.installedSkillIds ?? [],
        skillsDir: targetHomes[target].skillsDir
      };
    }

    return {
      target,
      status: "deferred",
      installedSkillIds: listSkillIdsForTarget(plan, target),
      reason: "Gemini direct target adapter lands in Phase 4"
    };
  });
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

function compareDirectInstall(
  left: BootstrapManifestDirectInstall,
  right: BootstrapManifestDirectInstall
): number {
  return (
    left.target.localeCompare(right.target) ||
    left.assetId.localeCompare(right.assetId) ||
    left.destinationDir.localeCompare(right.destinationDir) ||
    (left.sourceId ?? "").localeCompare(right.sourceId ?? "")
  );
}
