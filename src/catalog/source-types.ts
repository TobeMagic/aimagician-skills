import type { AssetKind, CatalogSection } from "../model/assets";
import type { TargetSelection } from "../model/targets";

export interface CatalogAssetInput {
  id: string;
  kind: AssetKind;
  path?: string;
  description?: string;
  targets?: TargetSelection;
}

interface BaseCatalogSourceInput {
  id: string;
  enabled?: boolean;
  description?: string;
  version?: string;
  targets?: TargetSelection;
}

export interface GithubSourceInput extends BaseCatalogSourceInput {
  type: "github";
  assets?: CatalogAssetInput[];
  github: {
    repo: string;
    ref?: string;
    path?: string;
  };
}

export interface CommandSourceInput extends BaseCatalogSourceInput {
  type: "command";
  assets: CatalogAssetInput[];
  command: {
    run: string;
    shell?: string;
    cwd?: string;
  };
}

export type CatalogSourceInput = GithubSourceInput | CommandSourceInput;

export type CatalogResolvedSourceInput =
  | (Omit<GithubSourceInput, "assets"> & { type: "github"; assets: CatalogAssetInput[] })
  | CommandSourceInput;

export interface CatalogFileInput {
  sources: CatalogSourceInput[];
}

export type CatalogSourceRecord = (CatalogSourceInput & {
  enabled: boolean;
  section: CatalogSection;
  originFile: string;
});

export type CatalogResolvedSourceRecord = (CatalogResolvedSourceInput & {
  enabled: boolean;
  section: CatalogSection;
  originFile: string;
});

export interface OwnedSkillRecord {
  id: string;
  skillDir: string;
  skillFile: string;
}

export interface LoadedCatalogFile {
  section: CatalogSection;
  filePath: string;
  sources: CatalogSourceRecord[];
  activeSources: CatalogSourceRecord[];
}

export interface LoadedCatalogSection {
  section: CatalogSection;
  rootDir: string;
  files: LoadedCatalogFile[];
  sources: CatalogSourceRecord[];
  activeSources: CatalogSourceRecord[];
}

export interface LoadedCatalog {
  ownedSkills: OwnedSkillRecord[];
  skills: LoadedCatalogSection;
  plugins: LoadedCatalogSection;
  sources: CatalogSourceRecord[];
  activeSources: CatalogSourceRecord[];
}
