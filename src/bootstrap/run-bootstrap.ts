import { writeFile } from "node:fs/promises";
import type { CatalogLoadOptions } from "../catalog/load-catalog";
import { type SupportedTarget, supportedTargets } from "../model/targets";
import type { PlatformContext } from "../shared/platform";
import { ensureBootstrapWorkspace, resolveBootstrapWorkspace } from "./workspace";
import {
  loadManifest,
  manifestsEqual,
  writeManifest,
  type BootstrapManifest
} from "./manifest";
import {
  buildBootstrapPlan,
  type BootstrapPlan
} from "./plan-bootstrap";

export interface RunBootstrapOptions {
  selectedTargets?: SupportedTarget[];
  dryRun?: boolean;
  now?: string;
  catalog?: CatalogLoadOptions;
  platform?: Partial<PlatformContext>;
}

export interface BootstrapRunResult {
  mode: "dry-run" | "apply";
  changed: boolean;
  workspaceRoot: string;
  manifestPath: string;
  planPath: string;
  plan: BootstrapPlan;
}

export async function runBootstrap(
  options: RunBootstrapOptions = {}
): Promise<BootstrapRunResult> {
  const selectedTargets = options.selectedTargets ?? [...supportedTargets];
  const plan = await buildBootstrapPlan({
    selectedTargets,
    catalog: options.catalog
  });
  const workspace = options.dryRun
    ? resolveBootstrapWorkspace(options.platform)
    : await ensureBootstrapWorkspace(options.platform);

  if (options.dryRun) {
    return {
      mode: "dry-run",
      changed: false,
      workspaceRoot: workspace.rootDir,
      manifestPath: workspace.manifestPath,
      planPath: workspace.planPath,
      plan
    };
  }

  const nextManifest = createManifest(plan, options.now);
  const previousManifest = await loadManifest(workspace.manifestPath);
  const changed = !manifestsEqual(previousManifest, nextManifest);

  await writeFile(workspace.planPath, JSON.stringify(plan, null, 2), "utf8");
  await writeManifest(workspace.manifestPath, nextManifest);

  return {
    mode: "apply",
    changed,
    workspaceRoot: workspace.rootDir,
    manifestPath: workspace.manifestPath,
    planPath: workspace.planPath,
    plan
  };
}

function createManifest(
  plan: BootstrapPlan,
  now: string | undefined
): BootstrapManifest {
  return {
    version: 1,
    updatedAt: now ?? new Date().toISOString(),
    selectedTargets: plan.selectedTargets,
    assets: plan.assets.map((asset) => ({
      id: asset.id,
      origin: asset.origin,
      kind: asset.kind,
      sourceId: asset.sourceId,
      selectedTargets: asset.selectedTargets
    }))
  };
}
