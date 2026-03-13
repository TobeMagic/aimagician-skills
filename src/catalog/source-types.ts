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
  assets: CatalogAssetInput[];
}

export interface GithubSourceInput extends BaseCatalogSourceInput {
  type: "github";
  github: {
    repo: string;
    ref?: string;
    path?: string;
  };
}

export interface CommandSourceInput extends BaseCatalogSourceInput {
  type: "command";
  command: {
    run: string;
    shell?: string;
    cwd?: string;
  };
}

export type CatalogSourceInput = GithubSourceInput | CommandSourceInput;

export interface CatalogFileInput {
  sources: CatalogSourceInput[];
}

export type CatalogSourceRecord = (CatalogSourceInput & {
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
