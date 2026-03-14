import { extname, join } from "node:path";
import { stat } from "node:fs/promises";
import type { NormalizedAsset } from "../model/assets";
import type { SupportedTarget } from "../model/targets";
import {
  materializeGithubSource,
  resolveGithubAssetPath,
  type ResolvedManagedInstall
} from "./source-resolution";
import type { ResolvedTargetHomes } from "./target-homes";

export interface BootstrapPluginReport {
  assetId: string;
  sourceId: string;
  target: SupportedTarget;
  status: "planned" | "installed" | "skipped";
  destinationPath?: string;
  reason?: string;
}

export interface ResolvePluginInstallsOptions {
  normalizedAssets: NormalizedAsset[];
  selectedTargets: SupportedTarget[];
  targetHomes: ResolvedTargetHomes;
  workspaceRoot: string;
  githubRepoOverrides?: Record<string, string>;
}

export async function previewPluginReports(
  options: Pick<ResolvePluginInstallsOptions, "normalizedAssets" | "selectedTargets" | "targetHomes">
): Promise<BootstrapPluginReport[]> {
  return options.normalizedAssets
    .flatMap((asset) => createPreviewReportsForAsset(asset, options.selectedTargets, options.targetHomes))
    .sort(comparePluginReport);
}

export async function resolvePluginInstalls(
  options: ResolvePluginInstallsOptions
): Promise<{
  installs: ResolvedManagedInstall[];
  reports: BootstrapPluginReport[];
}> {
  const installs: ResolvedManagedInstall[] = [];
  const reports: BootstrapPluginReport[] = [];
  const checkoutRoots = new Map<string, string>();

  for (const asset of options.normalizedAssets) {
    if (asset.kind !== "plugin") {
      continue;
    }

    for (const report of createPreviewReportsForAsset(asset, options.selectedTargets, options.targetHomes)) {
      if (report.status === "skipped") {
        reports.push(report);
        continue;
      }

      if (asset.locator.type !== "github") {
        reports.push({
          ...report,
          status: "skipped",
          reason: "Plugin auto-install currently supports GitHub-backed assets only"
        });
        continue;
      }

      const cacheKey =
        `${asset.sourceId}:${asset.locator.github.repo}:${asset.locator.github.ref ?? "HEAD"}`;
      let checkoutRoot = checkoutRoots.get(cacheKey);

      if (!checkoutRoot) {
        checkoutRoot = await materializeGithubSource(
          asset.sourceId,
          asset.locator.github.repo,
          asset.locator.github.ref,
          options.workspaceRoot,
          options.githubRepoOverrides
        );
        checkoutRoots.set(cacheKey, checkoutRoot);
      }

      const sourcePath = await resolveGithubAssetPath(
        checkoutRoot,
        asset.locator.github.path,
        asset.relativePath,
        asset.id
      );
      const sourceStats = await stat(sourcePath);

      if (!sourceStats.isFile()) {
        reports.push({
          ...report,
          status: "skipped",
          reason: "OpenCode plugin installs currently require a JavaScript or TypeScript file asset"
        });
        continue;
      }

      installs.push({
        target: report.target,
        assetId: asset.id,
        kind: "plugin",
        origin: "external",
        sourceId: asset.sourceId,
        sourcePath,
        destinationPath: report.destinationPath!,
        installType: "file",
        installArea: "plugins"
      });
      reports.push({
        ...report,
        status: "installed"
      });
    }
  }

  return {
    installs: installs.sort(compareManagedInstall),
    reports: reports.sort(comparePluginReport)
  };
}

function createPreviewReportsForAsset(
  asset: NormalizedAsset,
  selectedTargets: SupportedTarget[],
  targetHomes: ResolvedTargetHomes
): BootstrapPluginReport[] {
  if (asset.kind !== "plugin") {
    return [];
  }

  return asset.effectiveTargets
    .filter((target) => selectedTargets.includes(target))
    .map((target) => createPreviewReport(asset, target, targetHomes));
}

function createPreviewReport(
  asset: NormalizedAsset,
  target: SupportedTarget,
  targetHomes: ResolvedTargetHomes
): BootstrapPluginReport {
  const unsupportedReason = asset.targetStates[target]?.warnings[0];

  if (unsupportedReason) {
    return {
      assetId: asset.id,
      sourceId: asset.sourceId,
      target,
      status: "skipped",
      reason: unsupportedReason
    };
  }

  if (target === "opencode") {
    const extension = resolvePluginExtension(asset.relativePath);

    if (!extension) {
      return {
        assetId: asset.id,
        sourceId: asset.sourceId,
        target,
        status: "skipped",
        reason: "OpenCode plugin assets need an explicit JavaScript or TypeScript file path"
      };
    }

    return {
      assetId: asset.id,
      sourceId: asset.sourceId,
      target,
      status: "planned",
      destinationPath: join(targetHomes.opencode.pluginsDir, `${asset.id}${extension}`)
    };
  }

  return {
    assetId: asset.id,
    sourceId: asset.sourceId,
    target,
    status: "skipped",
    reason: resolveUnsupportedPluginReason(target)
  };
}

function resolvePluginExtension(relativePath: string | undefined): string | null {
  if (!relativePath) {
    return null;
  }

  const extension = extname(relativePath).toLowerCase();

  return [".js", ".cjs", ".mjs", ".ts", ".cts", ".mts"].includes(extension)
    ? extension
    : null;
}

function resolveUnsupportedPluginReason(target: SupportedTarget): string {
  switch (target) {
    case "codex":
      return "Codex does not expose a stable user-level plugin install path for this bootstrap";
    case "claude":
      return "Claude Code plugin automation remains marketplace- and consent-driven, so bootstrap skips it";
    case "gemini":
      return "Gemini support in this phase is generated skill extensions, not plugin catalog installs";
    default:
      return `Plugin installs are not supported for ${target}`;
  }
}

function comparePluginReport(
  left: BootstrapPluginReport,
  right: BootstrapPluginReport
): number {
  return [
    left.target.localeCompare(right.target),
    left.assetId.localeCompare(right.assetId),
    left.status.localeCompare(right.status),
    (left.reason ?? "").localeCompare(right.reason ?? "")
  ].find((result) => result !== 0) ?? 0;
}

function compareManagedInstall(
  left: ResolvedManagedInstall,
  right: ResolvedManagedInstall
): number {
  return [
    left.target.localeCompare(right.target),
    left.kind.localeCompare(right.kind),
    left.assetId.localeCompare(right.assetId),
    left.destinationPath.localeCompare(right.destinationPath)
  ].find((result) => result !== 0) ?? 0;
}
