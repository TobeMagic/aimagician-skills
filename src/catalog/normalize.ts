import type { NormalizedAsset, NormalizedTargetState } from "../model/assets";
import { supportedTargets } from "../model/targets";
import {
  mergeCapabilityMatrices,
  resolveSelectedTargets,
  uniqueTargets,
  type SupportedTarget,
  type TargetSelection
} from "../model/targets";
import type { CatalogResolvedSourceRecord } from "./source-types";

export function normalizeSources(sources: CatalogResolvedSourceRecord[]): NormalizedAsset[] {
  return sources.flatMap((source) =>
    source.assets.map((asset) => normalizeSourceAsset(source, asset))
  );
}

export function mergeTargetSelections(
  sourceTargets?: TargetSelection,
  assetTargets?: TargetSelection
): TargetSelection {
  const include = uniqueTargets(
    assetTargets?.include ?? sourceTargets?.include ?? supportedTargets
  );
  const exclude = uniqueTargets([
    ...(sourceTargets?.exclude ?? []),
    ...(assetTargets?.exclude ?? [])
  ]);
  const capabilities = mergeCapabilityMatrices(
    sourceTargets?.capabilities,
    assetTargets?.capabilities
  );

  return {
    include,
    exclude: exclude.length > 0 ? exclude : undefined,
    capabilities
  };
}

export function normalizeSourceAsset(
  source: CatalogResolvedSourceRecord,
  asset: CatalogResolvedSourceRecord["assets"][number]
): NormalizedAsset {
  const effectiveSelection = mergeTargetSelections(source.targets, asset.targets);
  const effectiveTargets = resolveSelectedTargets(effectiveSelection);

  const targetStates = Object.fromEntries(
    supportedTargets.map((target) => [
      target,
      createTargetState(target, effectiveTargets, effectiveSelection, asset.kind)
    ])
  ) as Record<SupportedTarget, NormalizedTargetState>;

  const locator =
    source.type === "github"
      ? { type: "github" as const, github: source.github }
      : { type: "command" as const, command: source.command };

  return {
    id: asset.id,
    sourceId: source.id,
    section: source.section,
    kind: asset.kind,
    sourceType: source.type,
    originFile: source.originFile,
    description: asset.description ?? source.description,
    relativePath: asset.path,
    sourceTargets: source.targets,
    assetTargets: asset.targets,
    effectiveTargets,
    targetStates,
    locator
  };
}

function createTargetState(
  target: SupportedTarget,
  effectiveTargets: SupportedTarget[],
  selection: TargetSelection,
  assetKind: CatalogResolvedSourceRecord["assets"][number]["kind"]
): NormalizedTargetState {
  const selected = effectiveTargets.includes(target);
  const capabilities = selection.capabilities?.[target] ?? {};
  const warnings: string[] = [];

  for (const [capability, support] of Object.entries(capabilities)) {
    if (selected && support?.support === "unsupported") {
      warnings.push(
        support.reason ??
          `${assetKind} asset requires unsupported ${capability} capability on ${target}`
      );
    }
  }

  return {
    target,
    selected,
    capabilities,
    warnings
  };
}
