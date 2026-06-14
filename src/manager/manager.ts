import { mkdir, rm } from "node:fs/promises";
import { dirname, join, normalize, sep } from "node:path";
import type { CatalogLoadOptions } from "../catalog/load-catalog";
import type { NormalizedAsset } from "../model/assets";
import { loadTaxonomy, resolveSkillTaxonomy } from "../catalog/taxonomy";
import {
  loadScopedUserConfig,
  saveScopedUserConfig,
  type UserSkillConfig
} from "../config/user-config";
import {
  executeCommandSkillSources,
  materializeGeneratedCommandSkillSources,
  previewCommandSkillSources,
  type CommandSourceReport
} from "../bootstrap/command-sources";
import {
  loadManifest,
  writeManifest,
  type BootstrapManifest,
  type BootstrapManifestAsset,
  type BootstrapManifestManagedInstall
} from "../bootstrap/manifest";
import { prepareBootstrapRun, type PlannedAsset } from "../bootstrap/plan-bootstrap";
import { resolveManagedSkillInstalls, type ResolvedManagedInstall } from "../bootstrap/source-resolution";
import { resolveTargetHomes, type ResolvedTargetHomes } from "../bootstrap/target-homes";
import {
  planManagedInstallSync,
  syncManagedInstalls,
  type ManagedInstallSyncOperation
} from "../bootstrap/direct-target-sync";
import { ensureBootstrapWorkspace, resolveBootstrapWorkspace } from "../bootstrap/workspace";
import type { InstallScope, ResetScope } from "../model/scopes";
import { supportedTargets, type SupportedTarget } from "../model/targets";
import { resolvePlatformContext, type PlatformContext } from "../shared/platform";
import { inspectInstallation } from "../inspection/inspect-installation";

export interface ManagerBaseOptions {
  selectedTargets?: SupportedTarget[];
  scope: InstallScope;
  projectDir?: string;
  platform?: Partial<PlatformContext>;
  catalog?: CatalogLoadOptions;
  taxonomyPath?: string;
  githubRepoOverrides?: Record<string, string>;
  includeArchived?: boolean;
}

export interface ManagerSkillRecord {
  id: string;
  origin: "owned" | "external";
  sourceId?: string;
  group: string;
  subgroup?: string;
  tags: string[];
  customTags: string[];
  description?: string;
  recommendedScopes: InstallScope[];
  recommendedTargets: SupportedTarget[];
  availableTargets: SupportedTarget[];
  installedTargets: SupportedTarget[];
  managedTargets: SupportedTarget[];
  commandOnly: boolean;
  archived: boolean;
}

export interface SearchSkillsOptions extends ManagerBaseOptions {
  query?: string;
  category?: string;
  subcategory?: string;
  tags?: string[];
}

export interface InstallSkillsOptions extends ManagerBaseOptions {
  assetIds: string[];
  category?: string;
  subcategory?: string;
  tags?: string[];
  now?: string;
  dryRun?: boolean;
}

export interface UninstallSkillsOptions extends Pick<ManagerBaseOptions, "scope" | "projectDir" | "platform"> {
  assetIds: string[];
  selectedTargets?: SupportedTarget[];
  now?: string;
}

export interface ResetSkillsOptions extends Omit<ManagerBaseOptions, "selectedTargets" | "scope" | "includeArchived"> {
  target: SupportedTarget;
  scope: ResetScope;
  installAll: boolean;
  yes?: boolean;
  dryRun?: boolean;
  now?: string;
}

export interface PreviewInstallTargetReport {
  target: SupportedTarget;
  plannedSkillIds: string[];
  skippedSkillIds: string[];
  removeSkillIds: string[];
  overwriteSkillIds: string[];
}

export interface PreviewInstallSkillsResult {
  scope: InstallScope;
  workspaceRoot: string;
  manifestPath: string;
  operations: ManagedInstallSyncOperation[];
  skipped: Array<{ assetId: string; target?: SupportedTarget; reason: string }>;
  targetReports: PreviewInstallTargetReport[];
}
export interface InstallSkillsResult {
  scope: InstallScope;
  workspaceRoot: string;
  manifestPath: string;
  dryRun: boolean;
  installed: BootstrapManifestManagedInstall[];
  commandReports: CommandSourceReport[];
  skipped: Array<{ assetId: string; target?: SupportedTarget; reason: string }>;
  changed: boolean;
}

export interface UninstallSkillsResult {
  scope: InstallScope;
  workspaceRoot: string;
  manifestPath: string;
  removed: BootstrapManifestManagedInstall[];
  skipped: Array<{ assetId: string; target: SupportedTarget; reason: "not-managed" }>;
  changed: boolean;
}

export interface ResetScopeResult {
  scope: InstallScope;
  workspaceRoot: string;
  manifestPath: string;
  removedRoots: string[];
  installed: BootstrapManifestManagedInstall[];
  commandReports: CommandSourceReport[];
  skipped: Array<{ assetId: string; target?: SupportedTarget; reason: string }>;
}

export interface ResetSkillsResult {
  target: SupportedTarget;
  scopes: ResetScopeResult[];
  dryRun: boolean;
}

export interface ArchiveSkillsOptions extends ManagerBaseOptions {
  assetIds: string[];
  archived: boolean;
}

export interface ArchiveSkillsResult {
  archived: string[];
  unarchived: string[];
}

type InstallEligibility = { eligible: true } | { eligible: false; reason: string };

export async function searchSkills(options: SearchSkillsOptions): Promise<ManagerSkillRecord[]> {
  const selectedTargets = options.selectedTargets ?? [...supportedTargets];
  const platformContext = resolvePlatformContext(options.platform);
  const workspace = resolveBootstrapWorkspace({
    ...platformContext,
    scope: options.scope,
    projectDir: options.projectDir
  });
  const [prepared, taxonomy, inspection, userConfig] = await Promise.all([
    prepareBootstrapRun({
      selectedTargets,
      catalog: options.catalog,
      workspaceRoot: workspace.rootDir,
      githubRepoOverrides: options.githubRepoOverrides,
      includeArchived: options.includeArchived ?? false,
      includeDisabledSources: true
    }),
    loadTaxonomy(options.taxonomyPath),
    inspectInstallation({
      selectedTargets,
      scope: options.scope,
      projectDir: options.projectDir,
      platform: platformContext
    }),
    loadScopedUserConfig({
      configBaseDir: platformContext.configBaseDir,
      scope: options.scope,
      projectDir: options.projectDir
    })
  ]);
  const normalizedById = new Map(prepared.normalizedAssets.map((asset) => [asset.id, asset]));
  const ownedAssetIds = new Set(
    prepared.plan.assets
      .filter((asset) => asset.origin === "owned")
      .map((asset) => asset.id)
  );
  const installedById = new Map<string, Set<SupportedTarget>>();
  const managedById = new Map<string, Set<SupportedTarget>>();

  for (const target of inspection.targets) {
    for (const asset of target.detectedAssets) {
      if (asset.kind !== "skill") {
        continue;
      }

      addTarget(installedById, asset.id, target.target);
      if (asset.managed) {
        addTarget(managedById, asset.id, target.target);
      }
    }
  }

  const query = options.query?.trim().toLowerCase();
  const skills = prepared.plan.assets
    .filter((asset) => asset.kind === "skill")
    .map<ManagerSkillRecord>((asset) => {
      const taxonomyEntry = resolveSkillTaxonomy(taxonomy, asset.id);
      const normalized = asset.origin === "external" ? normalizedById.get(asset.id) : undefined;

      return {
        id: asset.id,
        origin: asset.origin,
        sourceId: asset.sourceId,
        group: taxonomyEntry.group ?? "uncategorized",
        subgroup: taxonomyEntry.subgroup,
        tags: taxonomyEntry.tags,
        customTags: userConfig.customTags[asset.id] ?? [],
        description: taxonomyEntry.description ?? normalized?.description,
        recommendedScopes: taxonomyEntry.recommendedScopes,
        recommendedTargets: taxonomyEntry.recommendedTargets,
        availableTargets: asset.selectedTargets,
        installedTargets: [...(installedById.get(asset.id) ?? new Set())].sort(),
        managedTargets: [...(managedById.get(asset.id) ?? new Set())].sort(),
        commandOnly: normalized?.locator.type === "command" && !normalized.locator.command.adapter,
        archived: asset.archived === true || userConfig.archivedIds.includes(asset.id)
      };
    })
    .filter((skill) => skill.origin !== "external" || !ownedAssetIds.has(skill.id))
    .filter((skill) => skill.archived || taxonomy.skills[skill.id] !== undefined)
    .filter((skill) => options.includeArchived === true || !skill.archived)
    .filter((skill) => matchesSelectors(skill, options))
    .filter((skill) => matchesQuery(skill, query))
    .sort(compareManagerSkill);

  return skills;
}

export async function setSkillOverride(
  options: ManagerBaseOptions & { assetIds: string[]; state: "include" | "exclude" | "default" }
): Promise<UserSkillConfig> {
  const platformContext = resolvePlatformContext(options.platform);
  const configOptions = {
    configBaseDir: platformContext.configBaseDir,
    scope: options.scope,
    projectDir: options.projectDir
  };
  const config = await loadScopedUserConfig(configOptions);
  const includedIds = new Set(config.includedIds);
  const excludedIds = new Set(config.excludedIds);

  for (const assetId of options.assetIds) {
    includedIds.delete(assetId);
    excludedIds.delete(assetId);

    if (options.state === "include") {
      includedIds.add(assetId);
    } else if (options.state === "exclude") {
      excludedIds.add(assetId);
    }
  }

  config.includedIds = [...includedIds].sort();
  config.excludedIds = [...excludedIds].sort();
  await saveScopedUserConfig(configOptions, config);

  return config;
}

export async function previewInstallSkills(
  options: InstallSkillsOptions
): Promise<PreviewInstallSkillsResult> {
  const selectedTargets = options.selectedTargets ?? [...supportedTargets];
  const selectedIds = await resolveSelectedAssetIds(options, selectedTargets);
  const platformContext = resolvePlatformContext(options.platform);
  const workspace = resolveBootstrapWorkspace({
    ...platformContext,
    scope: options.scope,
    projectDir: options.projectDir
  });
  const targetHomes = resolveTargetHomes({
    ...platformContext,
    scope: options.scope,
    projectDir: options.projectDir
  });
  const userConfig = await loadScopedUserConfig({
    configBaseDir: platformContext.configBaseDir,
    scope: options.scope,
    projectDir: options.projectDir
  });
  const prepared = await prepareBootstrapRun({
    selectedTargets,
    catalog: options.catalog,
    workspaceRoot: workspace.rootDir,
    githubRepoOverrides: options.githubRepoOverrides,
    includeArchived: options.includeArchived ?? false,
    includeDisabledSources: true
  });
  const ownedAssetIds = createOwnedAssetIdSet(prepared.plan.assets);
  const selectedAssets = prepared.normalizedAssets.filter((asset) =>
    selectedIds.has(asset.id) && !ownedAssetIds.has(asset.id)
  );
  const eligibilityById = new Map<string, InstallEligibility>(selectedAssets.map((asset) => [
    asset.id,
    resolveInstallEligibility(asset, userConfig, options.scope)
  ]));
  const eligibleAssets = selectedAssets.filter((asset) => isInstallEligible(eligibilityById.get(asset.id)));
  const missingIds = [...selectedIds].filter((id) => !prepared.plan.assets.some((asset) => asset.id === id));
  const skipped = [
    ...missingIds.map((assetId) => ({ assetId, reason: "not-found" })),
    ...selectedAssets
      .map((asset) => ({ assetId: asset.id, reason: installIneligibilityReason(eligibilityById.get(asset.id)) }))
      .filter((skip): skip is { assetId: string; reason: string } => skip.reason !== undefined)
  ];
  const managedInstalls = await resolveManagedSkillInstalls({
    catalog: prepared.catalog,
    normalizedAssets: eligibleAssets,
    workspaceRoot: workspace.rootDir,
    selectedTargets,
    targetHomes,
    githubRepoOverrides: options.githubRepoOverrides,
    includeArchived: options.includeArchived ?? false
  });
  const selectedManagedInstalls = managedInstalls
    .filter((install) => selectedIds.has(install.assetId))
    .sort(compareResolvedInstall);
  const previousManifest = await loadManifest(workspace.manifestPath);
  const operations = planManagedInstallSync({
    allowedRootsByTarget: createAllowedRootsByTarget(targetHomes),
    selectedTargets,
    installs: selectedManagedInstalls,
    previousInstalls: previousManifest?.managedInstalls ?? []
  });

  return {
    scope: options.scope,
    workspaceRoot: workspace.rootDir,
    manifestPath: workspace.manifestPath,
    operations,
    skipped,
    targetReports: createPreviewTargetReports(selectedTargets, operations, skipped)
  };
}

function createPreviewTargetReports(
  selectedTargets: SupportedTarget[],
  operations: ManagedInstallSyncOperation[],
  skipped: Array<{ assetId: string; target?: SupportedTarget; reason: string }>
): PreviewInstallTargetReport[] {
  return selectedTargets.map((target) => ({
    target,
    plannedSkillIds: operations
      .filter((operation) => operation.target === target && operation.assetKind === "skill" && operation.kind === "create")
      .map((operation) => operation.assetId)
      .sort(),
    skippedSkillIds: skipped
      .filter((skip) => skip.target === undefined || skip.target === target)
      .map((skip) => skip.assetId)
      .sort(),
    removeSkillIds: operations
      .filter((operation) => operation.target === target && operation.assetKind === "skill" && operation.kind === "remove")
      .map((operation) => operation.assetId)
      .sort(),
    overwriteSkillIds: operations
      .filter((operation) => operation.target === target && operation.assetKind === "skill" && operation.kind === "overwrite")
      .map((operation) => operation.assetId)
      .sort()
  }));
}

export async function installSkills(options: InstallSkillsOptions): Promise<InstallSkillsResult> {
  const selectedTargets = options.selectedTargets ?? [...supportedTargets];
  const selectedIds = await resolveSelectedAssetIds(options, selectedTargets);
  const platformContext = resolvePlatformContext(options.platform);
  const workspace = options.dryRun
    ? resolveBootstrapWorkspace({ ...platformContext, scope: options.scope, projectDir: options.projectDir })
    : await ensureBootstrapWorkspace({ ...platformContext, scope: options.scope, projectDir: options.projectDir });
  const targetHomes = resolveTargetHomes({
    ...platformContext,
    scope: options.scope,
    projectDir: options.projectDir
  });
  const userConfig = await loadScopedUserConfig({
    configBaseDir: platformContext.configBaseDir,
    scope: options.scope,
    projectDir: options.projectDir
  });
  const prepared = await prepareBootstrapRun({
    selectedTargets,
    catalog: options.catalog,
    workspaceRoot: workspace.rootDir,
    githubRepoOverrides: options.githubRepoOverrides,
    includeArchived: options.includeArchived ?? false,
    includeDisabledSources: true
  });
  const ownedAssetIds = createOwnedAssetIdSet(prepared.plan.assets);
  const selectedAssets = prepared.normalizedAssets.filter((asset) =>
    selectedIds.has(asset.id) && !ownedAssetIds.has(asset.id)
  );
  const eligibilityById = new Map<string, InstallEligibility>(selectedAssets.map((asset) => [
    asset.id,
    resolveInstallEligibility(asset, userConfig, options.scope)
  ]));
  const eligibleAssets = selectedAssets.filter((asset) => isInstallEligible(eligibilityById.get(asset.id)));
  const missingIds = [...selectedIds].filter((id) => !prepared.plan.assets.some((asset) => asset.id === id));
  const ineligibleSkipped = selectedAssets
    .map((asset) => ({ assetId: asset.id, reason: installIneligibilityReason(eligibilityById.get(asset.id)) }))
    .filter((skip): skip is { assetId: string; reason: string } => skip.reason !== undefined);
  const generatedCommandSources = await materializeGeneratedCommandSkillSources({
    normalizedAssets: eligibleAssets,
    selectedTargets,
    workspaceRoot: workspace.rootDir,
    platformContext,
    targetHomes
  });
  const managedInstalls = await resolveManagedSkillInstalls({
    catalog: prepared.catalog,
    normalizedAssets: eligibleAssets,
    workspaceRoot: workspace.rootDir,
    selectedTargets,
    targetHomes,
    githubRepoOverrides: options.githubRepoOverrides,
    materializedCommandSourceDirs: generatedCommandSources.materializedDirs,
    includeArchived: options.includeArchived ?? false
  });
  const selectedManagedInstalls = managedInstalls
    .filter((install) => selectedIds.has(install.assetId))
    .sort(compareResolvedInstall);
  const directCommandReports = options.dryRun
    ? previewCommandSkillSources(eligibleAssets, selectedTargets)
    : await executeCommandSkillSources({
        normalizedAssets: eligibleAssets,
        selectedTargets,
        workspaceRoot: workspace.rootDir,
        platformContext,
        targetHomes
      });
  const commandReports = [
    ...generatedCommandSources.reports,
    ...directCommandReports
  ].sort((left, right) => left.sourceId.localeCompare(right.sourceId));
  const skipped = [
    ...missingIds.map((assetId) => ({
      assetId,
      reason: "not-found"
    })),
    ...ineligibleSkipped
  ];

  if (options.dryRun) {
    return {
      scope: options.scope,
      workspaceRoot: workspace.rootDir,
      manifestPath: workspace.manifestPath,
      dryRun: true,
      installed: selectedManagedInstalls.map(toManifestInstall),
      commandReports,
      skipped,
      changed: selectedManagedInstalls.length > 0 || commandReports.length > 0
    };
  }

  const previousManifest = await loadManifest(workspace.manifestPath);
  const previousInstalls = previousManifest?.managedInstalls ?? [];
  const allowedRootsByTarget = createAllowedRootsByTarget(targetHomes);

  await syncManagedInstalls({
    allowedRootsByTarget,
    selectedTargets,
    installs: selectedManagedInstalls,
    previousInstalls
  });

  const nextManifest = mergeInstalledManifest(
    previousManifest,
    selectedTargets,
    prepared.plan.assets.filter((asset) => selectedIds.has(asset.id) && isInstallEligible(eligibilityById.get(asset.id))),
    selectedManagedInstalls.map(toManifestInstall),
    commandReports,
    options.now
  );

  await writeManifest(workspace.manifestPath, nextManifest);

  return {
    scope: options.scope,
    workspaceRoot: workspace.rootDir,
    manifestPath: workspace.manifestPath,
    dryRun: false,
    installed: selectedManagedInstalls.map(toManifestInstall),
    commandReports,
    skipped,
    changed: JSON.stringify(previousManifest) !== JSON.stringify(nextManifest)
  };
}

export async function uninstallSkills(options: UninstallSkillsOptions): Promise<UninstallSkillsResult> {
  const selectedTargets = options.selectedTargets ?? [...supportedTargets];
  const selectedIds = new Set(options.assetIds);
  const platformContext = resolvePlatformContext(options.platform);
  const workspace = resolveBootstrapWorkspace({
    ...platformContext,
    scope: options.scope,
    projectDir: options.projectDir
  });
  const targetHomes = resolveTargetHomes({
    ...platformContext,
    scope: options.scope,
    projectDir: options.projectDir
  });
  const previousManifest = await loadManifest(workspace.manifestPath);
  const allowedRootsByTarget = createAllowedRootsByTarget(targetHomes);
  const removed = (previousManifest?.managedInstalls ?? [])
    .filter((install) =>
      install.kind === "skill" &&
      selectedTargets.includes(install.target) &&
      selectedIds.has(install.assetId)
    )
    .sort(compareManifestInstall);
  const removedKeys = new Set(removed.map(createManagedInstallKey));
  const removedTargetsByAsset = new Map<string, Set<SupportedTarget>>();

  for (const install of removed) {
    if (isManagedPath(normalize(install.destinationPath), allowedRootsByTarget[install.target] ?? [])) {
      await rm(install.destinationPath, {
        recursive: install.installType === "directory",
        force: true
      });
    }
    addTarget(removedTargetsByAsset, install.assetId, install.target);
  }

  const skipped: UninstallSkillsResult["skipped"] = [];
  for (const assetId of options.assetIds) {
    for (const target of selectedTargets) {
      if (!removed.some((install) => install.assetId === assetId && install.target === target)) {
        skipped.push({ assetId, target, reason: "not-managed" });
      }
    }
  }

  if (!previousManifest) {
    return {
      scope: options.scope,
      workspaceRoot: workspace.rootDir,
      manifestPath: workspace.manifestPath,
      removed: [],
      skipped,
      changed: false
    };
  }

  const remainingManagedInstalls = previousManifest.managedInstalls
    .filter((install) => !removedKeys.has(createManagedInstallKey(install)))
    .sort(compareManifestInstall);
  const remainingAssets = previousManifest.assets
    .map((asset) => removeTargetsFromAsset(asset, removedTargetsByAsset.get(asset.id)))
    .filter((asset): asset is BootstrapManifestAsset => asset.selectedTargets.length > 0);
  const nextManifest: BootstrapManifest = {
    ...previousManifest,
    updatedAt: options.now ?? new Date().toISOString(),
    selectedTargets: uniqueTargets(remainingManagedInstalls.map((install) => install.target)),
    assets: remainingAssets,
    managedInstalls: remainingManagedInstalls
  };

  await mkdir(workspace.rootDir, { recursive: true });
  await writeManifest(workspace.manifestPath, nextManifest);

  return {
    scope: options.scope,
    workspaceRoot: workspace.rootDir,
    manifestPath: workspace.manifestPath,
    removed,
    skipped,
    changed: removed.length > 0
  };
}

export async function resetSkills(options: ResetSkillsOptions): Promise<ResetSkillsResult> {
  if (!options.dryRun && !options.yes) {
    throw new Error("reset requires --yes unless --dry-run is used");
  }

  if (!options.installAll) {
    throw new Error("reset currently requires --install-all");
  }

  const scopes: InstallScope[] = options.scope === "all"
    ? ["global", "project"]
    : [options.scope];
  const scopeResults: ResetScopeResult[] = [];

  for (const scope of scopes) {
    const platformContext = resolvePlatformContext(options.platform);
    const workspace = options.dryRun
      ? resolveBootstrapWorkspace({ ...platformContext, scope, projectDir: options.projectDir })
      : await ensureBootstrapWorkspace({ ...platformContext, scope, projectDir: options.projectDir });
    const targetHomes = resolveTargetHomes({
      ...platformContext,
      scope,
      projectDir: options.projectDir
    });
    const removedRoots = createAllowedRootsByTarget(targetHomes)[options.target];
    const activeSkills = await searchSkills({
      scope,
      projectDir: options.projectDir,
      selectedTargets: [options.target],
      catalog: options.catalog,
      taxonomyPath: options.taxonomyPath,
      githubRepoOverrides: options.githubRepoOverrides,
      platform: platformContext,
      includeArchived: false
    });
    const assetIds = activeSkills
      .filter((skill) =>
        !skill.archived &&
        !skill.commandOnly &&
        skill.availableTargets.includes(options.target)
      )
      .map((skill) => skill.id);

    if (!options.dryRun) {
      for (const root of removedRoots.filter(Boolean)) {
        await rm(root, { recursive: true, force: true });
        await mkdir(root, { recursive: true });
      }
      await removeTargetFromManifest(workspace.manifestPath, options.target, options.now);
    }

    const installResult = await installSkills({
      assetIds,
      scope,
      projectDir: options.projectDir,
      selectedTargets: [options.target],
      catalog: options.catalog,
      taxonomyPath: options.taxonomyPath,
      githubRepoOverrides: options.githubRepoOverrides,
      platform: platformContext,
      dryRun: options.dryRun,
      now: options.now,
      includeArchived: false
    });

    scopeResults.push({
      scope,
      workspaceRoot: workspace.rootDir,
      manifestPath: workspace.manifestPath,
      removedRoots: [...removedRoots],
      installed: installResult.installed,
      commandReports: installResult.commandReports,
      skipped: installResult.skipped
    });
  }

  return {
    target: options.target,
    scopes: scopeResults,
    dryRun: options.dryRun ?? false
  };
}

export async function archiveSkills(options: ArchiveSkillsOptions): Promise<ArchiveSkillsResult> {
  const selectedTargets = options.selectedTargets ?? [...supportedTargets];
  const platformContext = resolvePlatformContext(options.platform);

  const config = await loadScopedUserConfig({
    configBaseDir: platformContext.configBaseDir,
    scope: options.scope,
    projectDir: options.projectDir
  });

  if (options.archived) {
    const archivedIds = new Set(config.archivedIds);
    for (const id of options.assetIds) {
      archivedIds.add(id);
    }
    config.archivedIds = [...archivedIds].sort();
  } else {
    const unarchivedIds = new Set(options.assetIds);
    config.archivedIds = config.archivedIds.filter((id) => !unarchivedIds.has(id));
  }

  await saveScopedUserConfig({
    configBaseDir: platformContext.configBaseDir,
    scope: options.scope,
    projectDir: options.projectDir
  }, config);

  return {
    archived: options.archived ? options.assetIds : [],
    unarchived: options.archived ? [] : options.assetIds
  };
}

function isInstallEligible(eligibility: InstallEligibility | undefined): boolean {
  return eligibility?.eligible === true;
}

function installIneligibilityReason(eligibility: InstallEligibility | undefined): string | undefined {
  return eligibility?.eligible === false ? eligibility.reason : undefined;
}

function resolveInstallEligibility(
  asset: NormalizedAsset,
  config: UserSkillConfig,
  scope: InstallScope
): InstallEligibility {
  if (config.excludedIds.includes(asset.id)) {
    return { eligible: false, reason: "excluded" };
  }

  if (scope === "project" && asset.sourceType === "command") {
    return { eligible: false, reason: "command-source-global-only" };
  }

  if (!asset.sourceEnabled && !config.includedIds.includes(asset.id)) {
    return { eligible: false, reason: "source-default-disabled" };
  }

  return { eligible: true };
}

function matchesQuery(skill: ManagerSkillRecord, query: string | undefined): boolean {
  if (!query) {
    return true;
  }

  return [
    skill.id,
    skill.sourceId,
    skill.group,
    skill.subgroup,
    skill.description,
    ...skill.tags,
    ...skill.customTags
  ].some((value) => value?.toLowerCase().includes(query));
}

function matchesSelectors(
  skill: ManagerSkillRecord,
  selectors: { category?: string; subcategory?: string; tags?: string[] }
): boolean {
  if (selectors.category && skill.group !== selectors.category) {
    return false;
  }

  if (selectors.subcategory && skill.subgroup !== selectors.subcategory) {
    return false;
  }

  const requiredTags = selectors.tags ?? [];
  if (requiredTags.length > 0) {
    const skillTags = new Set([...skill.tags, ...skill.customTags]);
    return requiredTags.every((tag) => skillTags.has(tag));
  }

  return true;
}

async function resolveSelectedAssetIds(
  options: InstallSkillsOptions,
  selectedTargets: SupportedTarget[]
): Promise<Set<string>> {
  const selectedIds = new Set(options.assetIds);

  if (!options.category && !options.subcategory && !options.tags?.length) {
    return selectedIds;
  }

  const matchedSkills = await searchSkills({
    ...options,
    selectedTargets,
    query: undefined
  });

  for (const skill of matchedSkills) {
    selectedIds.add(skill.id);
  }

  return selectedIds;
}

function mergeInstalledManifest(
  previousManifest: BootstrapManifest | null,
  selectedTargets: SupportedTarget[],
  assets: PlannedAsset[],
  installs: BootstrapManifestManagedInstall[],
  commandReports: CommandSourceReport[],
  now: string | undefined
): BootstrapManifest {
  const managedByKey = new Map<string, BootstrapManifestManagedInstall>();
  const assetsByKey = new Map<string, BootstrapManifestAsset>();
  const commandBySource = new Map<string, BootstrapManifest["commandInstalls"][number]>();

  for (const install of previousManifest?.managedInstalls ?? []) {
    managedByKey.set(createManagedInstallKey(install), install);
  }
  for (const install of installs) {
    managedByKey.set(createManagedInstallKey(install), install);
  }

  for (const asset of previousManifest?.assets ?? []) {
    assetsByKey.set(createAssetKey(asset), asset);
  }
  for (const asset of assets) {
    const key = createAssetKey(asset);
    const existing = assetsByKey.get(key);

    assetsByKey.set(key, {
      id: asset.id,
      origin: asset.origin,
      kind: asset.kind,
      sourceId: asset.sourceId,
      ...(asset.archived ? { archived: true } : {}),
      selectedTargets: uniqueTargets([
        ...(existing?.selectedTargets ?? []),
        ...asset.selectedTargets.filter((target) => selectedTargets.includes(target))
      ])
    });
  }

  for (const install of previousManifest?.commandInstalls ?? []) {
    commandBySource.set(install.sourceId, install);
  }
  for (const report of commandReports) {
    commandBySource.set(report.sourceId, {
      sourceId: report.sourceId,
      assetIds: [...report.assetIds].sort(),
      targets: [...report.targets].sort(),
      command: report.command
    });
  }

  const managedInstalls = [...managedByKey.values()].sort(compareManifestInstall);

  return {
    version: 3,
    updatedAt: now ?? new Date().toISOString(),
    selectedTargets: uniqueTargets([
      ...(previousManifest?.selectedTargets ?? []),
      ...selectedTargets
    ]),
    assets: [...assetsByKey.values()].sort(compareAsset),
    managedInstalls,
    commandInstalls: [...commandBySource.values()].sort((left, right) =>
      left.sourceId.localeCompare(right.sourceId)
    )
  };
}

function toManifestInstall(install: ResolvedManagedInstall): BootstrapManifestManagedInstall {
  return {
    target: install.target,
    assetId: install.assetId,
    kind: install.kind,
    origin: install.origin,
    sourceId: install.sourceId,
    destinationPath: install.destinationPath,
    installType: install.installType,
    installArea: install.installArea
  };
}

async function removeTargetFromManifest(
  manifestPath: string,
  target: SupportedTarget,
  now: string | undefined
): Promise<void> {
  const previousManifest = await loadManifest(manifestPath);

  if (!previousManifest) {
    return;
  }

  const assets = previousManifest.assets
    .map((asset) => ({
      ...asset,
      selectedTargets: asset.selectedTargets.filter((selectedTarget) => selectedTarget !== target)
    }))
    .filter((asset): asset is BootstrapManifestAsset => asset.selectedTargets.length > 0)
    .sort(compareAsset);
  const managedInstalls = previousManifest.managedInstalls
    .filter((install) => install.target !== target)
    .sort(compareManifestInstall);
  const commandInstalls = previousManifest.commandInstalls
    .map((install) => ({
      ...install,
      targets: install.targets.filter((selectedTarget) => selectedTarget !== target)
    }))
    .filter((install) => install.targets.length > 0)
    .sort((left, right) => left.sourceId.localeCompare(right.sourceId));
  const nextManifest: BootstrapManifest = {
    ...previousManifest,
    updatedAt: now ?? new Date().toISOString(),
    selectedTargets: uniqueTargets([
      ...assets.flatMap((asset) => asset.selectedTargets),
      ...managedInstalls.map((install) => install.target),
      ...commandInstalls.flatMap((install) => install.targets)
    ]),
    assets,
    managedInstalls,
    commandInstalls
  };

  await mkdir(dirname(manifestPath), { recursive: true });
  await writeManifest(manifestPath, nextManifest);
}

function removeTargetsFromAsset(
  asset: BootstrapManifestAsset,
  targetsToRemove: Set<SupportedTarget> | undefined
): BootstrapManifestAsset {
  if (!targetsToRemove) {
    return asset;
  }

  return {
    ...asset,
    selectedTargets: asset.selectedTargets.filter((target) => !targetsToRemove.has(target))
  };
}

function createManagedInstallKey(install: Pick<BootstrapManifestManagedInstall, "target" | "kind" | "assetId" | "destinationPath">): string {
  return `${install.target}:${install.kind}:${install.assetId}:${install.destinationPath}`;
}

function createAssetKey(asset: Pick<BootstrapManifestAsset, "kind" | "origin" | "id" | "sourceId">): string {
  return `${asset.kind}:${asset.origin}:${asset.sourceId ?? ""}:${asset.id}`;
}

function createOwnedAssetIdSet(assets: Array<Pick<BootstrapManifestAsset, "origin" | "id">>): Set<string> {
  return new Set(
    assets
      .filter((asset) => asset.origin === "owned")
      .map((asset) => asset.id)
  );
}

function createAllowedRootsByTarget(targetHomes: ResolvedTargetHomes): Record<SupportedTarget, string[]> {
  return {
    codex: [targetHomes.codex.skillsDir],
    claude: [targetHomes.claude.skillsDir],
    opencode: [targetHomes.opencode.skillsDir, targetHomes.opencode.pluginsDir],
    gemini: [targetHomes.gemini.extensionsDir],
    hermes: [targetHomes.hermes.skillsDir],
    cursor: [targetHomes.cursor.skillsDir],
    copilot: [targetHomes.copilot.skillsDir]
  };
}

function isManagedPath(path: string, allowedRoots: string[]): boolean {
  return allowedRoots.some((root) => {
    const normalizedRoot = normalize(root);

    return path !== normalizedRoot && path.startsWith(`${normalizedRoot}${sep}`);
  });
}

function addTarget(map: Map<string, Set<SupportedTarget>>, assetId: string, target: SupportedTarget): void {
  const targets = map.get(assetId) ?? new Set<SupportedTarget>();
  targets.add(target);
  map.set(assetId, targets);
}

function uniqueTargets(targets: SupportedTarget[]): SupportedTarget[] {
  return [...new Set(targets)].sort();
}

function compareManagerSkill(left: ManagerSkillRecord, right: ManagerSkillRecord): number {
  return [
    Number(right.archived) - Number(left.archived),
    left.group.localeCompare(right.group),
    (left.subgroup ?? "").localeCompare(right.subgroup ?? ""),
    left.id.localeCompare(right.id)
  ].find((result) => result !== 0) ?? 0;
}

function compareResolvedInstall(left: ResolvedManagedInstall, right: ResolvedManagedInstall): number {
  return [
    left.target.localeCompare(right.target),
    left.assetId.localeCompare(right.assetId),
    left.destinationPath.localeCompare(right.destinationPath)
  ].find((result) => result !== 0) ?? 0;
}

function compareManifestInstall(
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

function compareAsset(left: BootstrapManifestAsset, right: BootstrapManifestAsset): number {
  return [
    left.kind.localeCompare(right.kind),
    left.id.localeCompare(right.id),
    (left.sourceId ?? "").localeCompare(right.sourceId ?? "")
  ].find((result) => result !== 0) ?? 0;
}
