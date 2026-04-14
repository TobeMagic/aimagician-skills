export const supportedTargets = ["codex", "claude", "opencode", "gemini", "hermes"] as const;

export type SupportedTarget = (typeof supportedTargets)[number];

export const capabilityKinds = ["skill", "plugin", "extension", "command"] as const;

export type CapabilityKind = (typeof capabilityKinds)[number];

export const capabilityStatuses = ["supported", "unsupported", "unknown"] as const;

export type CapabilityStatus = (typeof capabilityStatuses)[number];

export interface CapabilitySupport {
  support: CapabilityStatus;
  reason?: string;
}

export type TargetCapabilityMap = Partial<Record<CapabilityKind, CapabilitySupport>>;

export type TargetCapabilityMatrix = Partial<Record<SupportedTarget, TargetCapabilityMap>>;

export interface TargetSelection {
  include?: SupportedTarget[];
  exclude?: SupportedTarget[];
  capabilities?: TargetCapabilityMatrix;
}

export const allSupportedTargets = [...supportedTargets];

export function uniqueTargets(targets: readonly SupportedTarget[]): SupportedTarget[] {
  return [...new Set(targets)];
}

export function resolveSelectedTargets(selection?: TargetSelection): SupportedTarget[] {
  const include = uniqueTargets(selection?.include ?? allSupportedTargets);
  const exclude = new Set(selection?.exclude ?? []);

  return include.filter((target) => !exclude.has(target));
}

export function cloneCapabilityMatrix(
  matrix?: TargetCapabilityMatrix
): TargetCapabilityMatrix | undefined {
  if (!matrix) {
    return undefined;
  }

  const clone: TargetCapabilityMatrix = {};

  for (const target of supportedTargets) {
    const capabilities = matrix[target];
    if (!capabilities) {
      continue;
    }

    clone[target] = { ...capabilities };
  }

  return clone;
}

export function mergeCapabilityMatrices(
  base?: TargetCapabilityMatrix,
  override?: TargetCapabilityMatrix
): TargetCapabilityMatrix | undefined {
  if (!base && !override) {
    return undefined;
  }

  const merged = cloneCapabilityMatrix(base) ?? {};

  for (const target of supportedTargets) {
    const overrideCapabilities = override?.[target];
    if (!overrideCapabilities) {
      continue;
    }

    merged[target] = {
      ...(merged[target] ?? {}),
      ...overrideCapabilities
    };
  }

  return merged;
}
