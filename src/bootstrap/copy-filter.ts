import { basename, normalize, sep } from "node:path";

const LOCAL_REFERENCE_REPOS_SEGMENT = `${sep}references${sep}_external_repos`;
const TRANSIENT_DIRECTORY_NAMES = new Set([
  ".git",
  ".pytest_cache",
  "node_modules",
  "__pycache__"
]);
const PYTHON_BYTECODE_SUFFIXES = [".pyc", ".pyo"];

export function shouldCopyManagedSource(sourcePath: string): boolean {
  const normalized = normalize(sourcePath);
  const pathSegments = normalized.split(sep);
  if (pathSegments.some((segment) => TRANSIENT_DIRECTORY_NAMES.has(segment))) {
    return false;
  }
  const filename = basename(normalized).toLowerCase();
  if (PYTHON_BYTECODE_SUFFIXES.some((suffix) => filename.endsWith(suffix))) {
    return false;
  }
  return !(
    normalized.endsWith(LOCAL_REFERENCE_REPOS_SEGMENT) ||
    normalized.includes(`${LOCAL_REFERENCE_REPOS_SEGMENT}${sep}`)
  );
}
