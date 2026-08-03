import { access, readdir } from "node:fs/promises";
import { constants } from "node:fs";
import { basename, extname, join } from "node:path";
import {
  loadManifest,
  type BootstrapManifestCommandInstall,
  type BootstrapManifestManagedInstall
} from "../bootstrap/manifest";
import { resolveTargetHomes } from "../bootstrap/target-homes";
import { resolveBootstrapWorkspace } from "../bootstrap/workspace";
import { supportedTargets, type SupportedTarget } from "../model/targets";
import type { InstallScope } from "../model/scopes";
import {
  resolvePlatformContext,
  type PlatformContext
} from "../shared/platform";
import { digestManagedContent } from "../shared/content-digest";
import { shouldCopyManagedSource } from "../bootstrap/copy-filter";

export interface LiveTargetAsset {
  id: string;
  kind: "skill" | "plugin";
  installArea: "skills" | "plugins" | "extensions" | "rules";
  path: string;
  managed: boolean;
}

export interface TargetManagedInstallStatus {
  assetId: string;
  kind: "skill" | "plugin";
  installArea: "skills" | "plugins" | "extensions" | "rules";
  destinationPath: string;
  present: boolean;
  sourcePath?: string;
  expectedDigest?: string;
  actualDigest?: string;
  integrity: "match" | "drift" | "missing" | "unverified";
}

export interface TargetCommandInstallStatus {
  sourceId: string;
  assetIds: string[];
  targets: SupportedTarget[];
  command: string;
}

export interface TargetInspection {
  target: SupportedTarget;
  status: "healthy" | "issues" | "empty";
  skillsDir?: string;
  pluginsDir?: string;
  extensionsDir?: string;
  rulesDir?: string;
  detectedAssets: LiveTargetAsset[];
  managedInstalls: TargetManagedInstallStatus[];
  commandInstalls: TargetCommandInstallStatus[];
  issues: string[];
}

export interface InstallationInspection {
  scope: InstallScope;
  workspaceRoot: string;
  manifestPath: string;
  manifestExists: boolean;
  selectedTargets: SupportedTarget[];
  status: "healthy" | "issues" | "no-manifest";
  targets: TargetInspection[];
}

export interface InspectInstallationOptions {
  selectedTargets?: SupportedTarget[];
  scope?: InstallScope;
  projectDir?: string;
  platform?: Partial<PlatformContext>;
}

export async function inspectInstallation(
  options: InspectInstallationOptions = {}
): Promise<InstallationInspection> {
  const scope = options.scope ?? "global";
  const platformContext = resolvePlatformContext(options.platform);
  const workspace = resolveBootstrapWorkspace({
    ...platformContext,
    scope,
    projectDir: options.projectDir
  });
  const manifest = await loadManifest(workspace.manifestPath);
  const targetHomes = resolveTargetHomes({
    ...platformContext,
    scope,
    projectDir: options.projectDir
  });
  const selectedTargets =
    options.selectedTargets ??
    manifest?.selectedTargets ??
    [...supportedTargets];

  const targets = await Promise.all(
    selectedTargets.map((target) =>
      inspectTarget(
        target,
        targetHomes,
        manifest?.managedInstalls ?? [],
        manifest?.commandInstalls ?? []
      )
    )
  );
  const status =
    !manifest ? "no-manifest" :
    targets.some((target) => target.status === "issues") ? "issues" :
    "healthy";

  return {
    scope,
    workspaceRoot: workspace.rootDir,
    manifestPath: workspace.manifestPath,
    manifestExists: manifest !== null,
    selectedTargets,
    status,
    targets
  };
}

async function inspectTarget(
  target: SupportedTarget,
  targetHomes: ReturnType<typeof resolveTargetHomes>,
  managedInstalls: BootstrapManifestManagedInstall[],
  commandInstalls: BootstrapManifestCommandInstall[]
): Promise<TargetInspection> {
  const liveAssets: LiveTargetAsset[] = [];
  const installs = managedInstalls
    .filter((install) => install.target === target)
    .sort(compareManagedInstall);
  const targetCommandInstalls = commandInstalls
    .filter((install) => install.targets.includes(target))
    .sort(compareCommandInstall);
  const managedStatuses = await Promise.all(installs.map(inspectManagedInstall));
  const managedPaths = new Set(managedStatuses.map((install) => install.destinationPath));
  const issues = managedStatuses.flatMap((install) => {
    if (!install.present) {
      return [`Missing managed ${install.kind} "${install.assetId}" at ${install.destinationPath}`];
    }
    if (install.integrity === "drift") {
      return [
        `Content drift for managed ${install.kind} "${install.assetId}" at ${install.destinationPath}`
      ];
    }
    return [];
  });

  switch (target) {
    case "codex":
      liveAssets.push(...await detectSkillDirectories(targetHomes.codex.skillsDir, managedPaths));
      break;
    case "claude":
      liveAssets.push(...await detectSkillDirectories(targetHomes.claude.skillsDir, managedPaths));
      break;
    case "opencode":
      liveAssets.push(...await detectSkillDirectories(targetHomes.opencode.skillsDir, managedPaths));
      liveAssets.push(...await detectPluginFiles(targetHomes.opencode.pluginsDir, managedPaths));
      break;
    case "hermes":
      liveAssets.push(...await detectSkillDirectories(targetHomes.hermes.skillsDir, managedPaths));
      break;
    case "cursor":
      liveAssets.push(...await detectSkillDirectories(targetHomes.cursor.skillsDir, managedPaths));
      break;
    case "copilot":
      liveAssets.push(...await detectSkillDirectories(targetHomes.copilot.skillsDir, managedPaths));
      break;
    case "gemini":
      liveAssets.push(...await detectGeminiExtensions(targetHomes.gemini.extensionsDir, managedPaths));
      break;
  }

  const status =
    issues.length > 0 ? "issues" :
    liveAssets.length === 0 &&
    managedStatuses.length === 0 &&
    targetCommandInstalls.length === 0 ? "empty" :
    "healthy";

  return {
    target,
    status,
    skillsDir:
      target === "gemini" ? undefined :
      target === "cursor" ? targetHomes.cursor.skillsDir :
      target === "copilot" ? targetHomes.copilot.skillsDir :
      target === "hermes" ? targetHomes.hermes.skillsDir :
      target === "opencode" ? targetHomes.opencode.skillsDir :
      target === "claude" ? targetHomes.claude.skillsDir :
      targetHomes.codex.skillsDir,
    pluginsDir: target === "opencode" ? targetHomes.opencode.pluginsDir : undefined,
    extensionsDir: target === "gemini" ? targetHomes.gemini.extensionsDir : undefined,
    rulesDir: undefined,
    detectedAssets: liveAssets.sort(compareLiveAsset),
    managedInstalls: managedStatuses,
    commandInstalls: targetCommandInstalls,
    issues
  };
}

async function inspectManagedInstall(
  install: BootstrapManifestManagedInstall
): Promise<TargetManagedInstallStatus> {
  const present = await pathExists(install.destinationPath);
  if (!present) {
    return {
      assetId: install.assetId,
      kind: install.kind,
      installArea: install.installArea,
      destinationPath: install.destinationPath,
      present: false,
      sourcePath: install.sourcePath,
      expectedDigest: install.sourceDigest,
      integrity: "missing"
    };
  }

  const actualDigest = await digestManagedContent(install.destinationPath, {
    filter: shouldCopyManagedSource
  });
  let expectedDigest = install.sourceDigest;
  if (install.sourcePath && await pathExists(install.sourcePath)) {
    expectedDigest = await digestManagedContent(install.sourcePath, {
      filter: shouldCopyManagedSource
    });
  }

  return {
    assetId: install.assetId,
    kind: install.kind,
    installArea: install.installArea,
    destinationPath: install.destinationPath,
    present: true,
    sourcePath: install.sourcePath,
    expectedDigest,
    actualDigest,
    integrity: expectedDigest
      ? expectedDigest === actualDigest ? "match" : "drift"
      : "unverified"
  };
}

async function detectSkillDirectories(
  rootDir: string,
  managedPaths: Set<string>
): Promise<LiveTargetAsset[]> {
  const entries = await safeReadDir(rootDir);
  const assets: LiveTargetAsset[] = [];

  for (const entry of entries) {
    if (!entry.isDirectory()) {
      continue;
    }

    const assetPath = join(rootDir, entry.name);

    if (!await pathExists(join(assetPath, "SKILL.md"))) {
      continue;
    }

    assets.push({
      id: entry.name,
      kind: "skill",
      installArea: "skills",
      path: assetPath,
      managed: managedPaths.has(assetPath)
    });
  }

  return assets;
}

async function detectGeminiExtensions(
  rootDir: string,
  managedPaths: Set<string>
): Promise<LiveTargetAsset[]> {
  const entries = await safeReadDir(rootDir);
  const assets: LiveTargetAsset[] = [];

  for (const entry of entries) {
    if (!entry.isDirectory()) {
      continue;
    }

    const assetPath = join(rootDir, entry.name);

    if (!await pathExists(join(assetPath, "gemini-extension.json"))) {
      continue;
    }

    assets.push({
      id: entry.name,
      kind: "skill",
      installArea: "extensions",
      path: assetPath,
      managed: managedPaths.has(assetPath)
    });
  }

  return assets;
}

async function detectPluginFiles(
  rootDir: string,
  managedPaths: Set<string>
): Promise<LiveTargetAsset[]> {
  const entries = await safeReadDir(rootDir);
  const assets: LiveTargetAsset[] = [];

  for (const entry of entries) {
    if (!entry.isFile()) {
      continue;
    }

    const extension = extname(entry.name).toLowerCase();

    if (![".js", ".cjs", ".mjs", ".ts", ".cts", ".mts"].includes(extension)) {
      continue;
    }

    const assetPath = join(rootDir, entry.name);

    assets.push({
      id: basename(entry.name, extension),
      kind: "plugin",
      installArea: "plugins",
      path: assetPath,
      managed: managedPaths.has(assetPath)
    });
  }

  return assets;
}

async function safeReadDir(path: string) {
  try {
    return await readdir(path, { withFileTypes: true });
  } catch (error) {
    if ((error as NodeJS.ErrnoException).code === "ENOENT") {
      return [];
    }

    throw error;
  }
}

async function pathExists(path: string): Promise<boolean> {
  try {
    await access(path, constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

function compareManagedInstall(
  left: BootstrapManifestManagedInstall,
  right: BootstrapManifestManagedInstall
): number {
  return [
    left.kind.localeCompare(right.kind),
    left.installArea.localeCompare(right.installArea),
    left.assetId.localeCompare(right.assetId),
    left.destinationPath.localeCompare(right.destinationPath)
  ].find((result) => result !== 0) ?? 0;
}

function compareLiveAsset(
  left: LiveTargetAsset,
  right: LiveTargetAsset
): number {
  return [
    left.kind.localeCompare(right.kind),
    left.installArea.localeCompare(right.installArea),
    left.id.localeCompare(right.id)
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
