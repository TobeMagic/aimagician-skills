export const installScopes = ["global", "project"] as const;
export const resetScopes = ["global", "project", "all"] as const;

export type InstallScope = (typeof installScopes)[number];
export type ResetScope = (typeof resetScopes)[number];

export function isInstallScope(value: string): value is InstallScope {
  return (installScopes as readonly string[]).includes(value);
}

export function isResetScope(value: string): value is ResetScope {
  return (resetScopes as readonly string[]).includes(value);
}
