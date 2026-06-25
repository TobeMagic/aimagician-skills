import { basename, normalize, sep } from "node:path";

const LOCAL_REFERENCE_REPOS_SEGMENT = `${sep}references${sep}_external_repos`;

export function shouldCopyManagedSource(sourcePath: string): boolean {
  const normalized = normalize(sourcePath);
  if (basename(normalized) === ".git" || normalized.includes(`${sep}.git${sep}`)) {
    return false;
  }
  return !(
    normalized.endsWith(LOCAL_REFERENCE_REPOS_SEGMENT) ||
    normalized.includes(`${LOCAL_REFERENCE_REPOS_SEGMENT}${sep}`)
  );
}
