import { access, readdir } from "node:fs/promises";
import { constants } from "node:fs";
import { basename, extname, join } from "node:path";
import type {
  CatalogAssetInput,
  CatalogResolvedAssetInput,
  CatalogResolvedSourceRecord,
  CatalogSourceRecord
} from "../catalog/source-types";
import type { CatalogSection } from "../model/assets";
import { materializeGithubSource } from "./source-resolution";

export interface ExpandGithubSourceAssetsOptions {
  sources: CatalogSourceRecord[];
  workspaceRoot: string;
  githubRepoOverrides?: Record<string, string>;
}

export async function expandGithubSourceAssets(
  options: ExpandGithubSourceAssetsOptions
): Promise<CatalogResolvedSourceRecord[]> {
  const expandedSources: CatalogResolvedSourceRecord[] = [];
  const checkoutRoots = new Map<string, string>();

  for (const source of options.sources) {
    if (source.type !== "github") {
      expandedSources.push({
        ...source,
        assets: resolveDeclaredAssets(
          source.assets?.length ? source.assets : [{ id: source.id }],
          source.section,
          source.id
        )
      });
      continue;
    }

    if ((source.assets?.length ?? 0) > 0) {
      expandedSources.push({
        ...source,
        assets: resolveDeclaredAssets(source.assets ?? [], source.section, source.id)
      });
      continue;
    }

    const cacheKey =
      `${source.id}:${source.github.repo}:${source.github.ref ?? "HEAD"}`;
    let checkoutRoot = checkoutRoots.get(cacheKey);

    if (!checkoutRoot) {
      checkoutRoot = await materializeGithubSource(
        source.id,
        source.github.repo,
        source.github.ref,
        options.workspaceRoot,
        options.githubRepoOverrides
      );
      checkoutRoots.set(cacheKey, checkoutRoot);
    }

    expandedSources.push({
      ...source,
      assets: await discoverGithubAssets(
        source.section,
        checkoutRoot,
        source.github.path,
        source.id
      )
    });
  }

  return expandedSources;
}

async function discoverGithubAssets(
  section: CatalogSection,
  checkoutRoot: string,
  githubPath: string | undefined,
  sourceId: string
): Promise<CatalogResolvedAssetInput[]> {
  const baseDir = githubPath ? join(checkoutRoot, githubPath) : checkoutRoot;
  const entries = await readdir(baseDir, { withFileTypes: true });
  const assets =
    section === "skills"
      ? await discoverGithubSkillAssets(baseDir, entries.map((entry) => entry.name))
      : discoverGithubPluginAssets(entries.map((entry) => ({
          name: entry.name,
          isDirectory: entry.isDirectory(),
          isFile: entry.isFile()
        })));

  if (assets.length === 0) {
    throw new Error(
      `GitHub source ${sourceId} did not discover any ${section} assets under ${baseDir}`
    );
  }

  assertUniqueAssetIds(assets, sourceId);

  return assets.sort((left, right) => left.id.localeCompare(right.id));
}

async function discoverGithubSkillAssets(
  baseDir: string,
  names: string[]
): Promise<CatalogResolvedAssetInput[]> {
  const assets: CatalogResolvedAssetInput[] = [];

  for (const name of names.sort((left, right) => left.localeCompare(right))) {
    if (name.startsWith(".")) {
      continue;
    }

    const skillDir = join(baseDir, name);
    const skillFile = join(skillDir, "SKILL.md");

    try {
      await access(skillFile, constants.F_OK);
      assets.push({
        id: name,
        kind: "skill",
        path: name
      });
    } catch {
      continue;
    }
  }

  return assets;
}

function discoverGithubPluginAssets(
  entries: Array<{ name: string; isDirectory: boolean; isFile: boolean }>
): CatalogResolvedAssetInput[] {
  const assets: CatalogResolvedAssetInput[] = [];

  for (const entry of entries.sort((left, right) => left.name.localeCompare(right.name))) {
    if (entry.name.startsWith(".")) {
      continue;
    }

    if (entry.isDirectory) {
      assets.push({
        id: entry.name,
        kind: "plugin",
        path: entry.name
      });
      continue;
    }

    if (entry.isFile && isSupportedPluginFile(entry.name)) {
      assets.push({
        id: basename(entry.name, extname(entry.name)),
        kind: "plugin",
        path: entry.name
      });
    }
  }

  return assets;
}

function resolveDeclaredAssets(
  assets: CatalogAssetInput[],
  section: CatalogSection,
  sourceId: string
): CatalogResolvedAssetInput[] {
  const resolved = assets.map((asset) => resolveDeclaredAsset(asset, section, sourceId));

  assertUniqueAssetIds(resolved, sourceId);

  return resolved.sort((left, right) => left.id.localeCompare(right.id));
}

function resolveDeclaredAsset(
  asset: CatalogAssetInput,
  section: CatalogSection,
  sourceId: string
): CatalogResolvedAssetInput {
  const id = asset.id ?? deriveAssetIdFromPath(asset.path);

  if (!id) {
    throw new Error(
      `Source ${sourceId} has an asset without an id or a path that can derive one`
    );
  }

  if (!isValidSlug(id)) {
    throw new Error(
      `Source ${sourceId} resolved invalid asset id "${id}". Use lowercase kebab-case.`
    );
  }

  return {
    id,
    kind: asset.kind ?? inferAssetKind(section),
    path: asset.path,
    description: asset.description,
    targets: asset.targets
  };
}

function inferAssetKind(section: CatalogSection): CatalogResolvedAssetInput["kind"] {
  return section === "skills" ? "skill" : "plugin";
}

function deriveAssetIdFromPath(pathValue: string | undefined): string | null {
  if (!pathValue) {
    return null;
  }

  const segments = pathValue.split(/[\\/]+/).filter(Boolean);
  const lastSegment = segments.at(-1);

  if (!lastSegment) {
    return null;
  }

  if (lastSegment.toLowerCase() === "skill.md") {
    return segments.at(-2) ?? null;
  }

  const extension = extname(lastSegment).toLowerCase();

  if (extension) {
    return basename(lastSegment, extension);
  }

  return lastSegment;
}

function isSupportedPluginFile(fileName: string): boolean {
  return [".js", ".cjs", ".mjs", ".ts", ".cts", ".mts"].includes(
    extname(fileName).toLowerCase()
  );
}

function assertUniqueAssetIds(
  assets: Array<{ id: string }>,
  sourceId: string
): void {
  const seen = new Set<string>();

  for (const asset of assets) {
    if (seen.has(asset.id)) {
      throw new Error(
        `GitHub source ${sourceId} discovered duplicate asset id "${asset.id}"`
      );
    }

    seen.add(asset.id);
  }
}

function isValidSlug(value: string): boolean {
  return /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value);
}
