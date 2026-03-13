import type {
  SupportedTarget,
  TargetCapabilityMap,
  TargetSelection
} from "./targets";

export const catalogSections = ["skills", "plugins"] as const;

export type CatalogSection = (typeof catalogSections)[number];

export const assetKinds = ["skill", "plugin"] as const;

export type AssetKind = (typeof assetKinds)[number];

export const sourceKinds = ["github", "command"] as const;

export type SourceKind = (typeof sourceKinds)[number];

export interface GithubLocator {
  repo: string;
  ref?: string;
  path?: string;
}

export interface CommandLocator {
  run: string;
  shell?: string;
  cwd?: string;
}

export interface NormalizedTargetState {
  target: SupportedTarget;
  selected: boolean;
  capabilities: TargetCapabilityMap;
  warnings: string[];
}

export interface NormalizedAsset {
  id: string;
  sourceId: string;
  section: CatalogSection;
  kind: AssetKind;
  sourceType: SourceKind;
  originFile: string;
  description?: string;
  relativePath?: string;
  sourceTargets?: TargetSelection;
  assetTargets?: TargetSelection;
  effectiveTargets: SupportedTarget[];
  targetStates: Record<SupportedTarget, NormalizedTargetState>;
  locator:
    | { type: "github"; github: GithubLocator }
    | { type: "command"; command: CommandLocator };
}
