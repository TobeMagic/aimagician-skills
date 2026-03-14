import type { NormalizedAsset } from "../model/assets";
import { supportedTargets, type SupportedTarget } from "../model/targets";
import type { CatalogLoadOptions } from "../catalog/load-catalog";
import { loadCatalog } from "../catalog/load-catalog";
import { normalizeSources } from "../catalog/normalize";
import type { LoadedCatalog } from "../catalog/source-types";
import type { BootstrapManifestAsset } from "./manifest";

export interface PlannedAsset extends BootstrapManifestAsset {
  warnings: string[];
}

export interface BootstrapPlan {
  selectedTargets: SupportedTarget[];
  ownedSkillIds: string[];
  assets: PlannedAsset[];
}

export interface BuildBootstrapPlanOptions {
  selectedTargets?: SupportedTarget[];
  catalog?: CatalogLoadOptions;
}

export interface PreparedBootstrapRun {
  selectedTargets: SupportedTarget[];
  catalog: LoadedCatalog;
  normalizedAssets: NormalizedAsset[];
  plan: BootstrapPlan;
}

export async function buildBootstrapPlan(
  options: BuildBootstrapPlanOptions = {}
): Promise<BootstrapPlan> {
  return (await prepareBootstrapRun(options)).plan;
}

export async function prepareBootstrapRun(
  options: BuildBootstrapPlanOptions = {}
): Promise<PreparedBootstrapRun> {
  const selectedTargets = options.selectedTargets ?? [...supportedTargets];
  const catalog = await loadCatalog(options.catalog);
  const normalizedAssets = normalizeSources(catalog.activeSources);

  return {
    selectedTargets,
    catalog,
    normalizedAssets,
    plan: createPlan(catalog, normalizedAssets, selectedTargets)
  };
}

function createPlan(
  catalog: LoadedCatalog,
  normalizedAssets: NormalizedAsset[],
  selectedTargets: SupportedTarget[]
): BootstrapPlan {
  return {
    selectedTargets,
    ownedSkillIds: catalog.ownedSkills.map((skill) => skill.id).sort(),
    assets: [
      ...catalog.ownedSkills.map<PlannedAsset>((skill) => ({
        id: skill.id,
        origin: "owned",
        kind: "skill",
        selectedTargets,
        warnings: []
      })),
      ...normalizedAssets
        .map((asset) => toPlannedAsset(asset, selectedTargets))
        .filter((asset) => asset.selectedTargets.length > 0)
    ]
  };
}

function toPlannedAsset(
  asset: NormalizedAsset,
  selectedTargets: SupportedTarget[]
): PlannedAsset {
  const effectiveTargets = asset.effectiveTargets.filter((target) =>
    selectedTargets.includes(target)
  );
  const warnings = effectiveTargets.flatMap(
    (target) => asset.targetStates[target]?.warnings ?? []
  );

  return {
    id: asset.id,
    origin: "external",
    kind: asset.kind,
    sourceId: asset.sourceId,
    selectedTargets: effectiveTargets,
    warnings
  };
}
