import { createHash } from "node:crypto";
import { lstat, readFile, readdir, readlink } from "node:fs/promises";
import { basename, join, relative, sep } from "node:path";

export interface ContentDigestOptions {
  filter?: (path: string) => boolean;
}

export async function digestManagedContent(
  root: string,
  options: ContentDigestOptions = {}
): Promise<string> {
  const hash = createHash("sha256");
  const rootStats = await lstat(root);

  if (!rootStats.isDirectory()) {
    appendRecord(hash, await createRecord(root, ".", rootStats));
    return `sha256:${hash.digest("hex")}`;
  }

  const records = await collectRecords(root, root, options);
  records.sort((left, right) => left.relativePath.localeCompare(right.relativePath));
  for (const record of records) appendRecord(hash, record);
  return `sha256:${hash.digest("hex")}`;
}

interface DigestRecord {
  kind: "file" | "link" | "other";
  relativePath: string;
  content: Buffer | string;
}

async function collectRecords(
  root: string,
  directory: string,
  options: ContentDigestOptions
): Promise<DigestRecord[]> {
  const entries = await readdir(directory, { withFileTypes: true });
  const records = await Promise.all(entries.map(async (entry) => {
    const path = join(directory, entry.name);
    if (options.filter && !options.filter(path)) return [];
    const relativePath = normalizeDigestPath(relative(root, path) || basename(path));
    const stats = await lstat(path);
    if (stats.isDirectory()) {
      return collectRecords(root, path, options);
    }
    return [await createRecord(path, relativePath, stats)];
  }));
  return records.flat();
}

async function createRecord(
  path: string,
  relativePath: string,
  stats: Awaited<ReturnType<typeof lstat>>
): Promise<DigestRecord> {
  if (stats.isSymbolicLink()) {
    return { kind: "link", relativePath, content: await readlink(path) };
  }
  if (stats.isFile()) {
    return { kind: "file", relativePath, content: await readFile(path) };
  }
  return { kind: "other", relativePath, content: String(stats.mode) };
}

function appendRecord(
  hash: ReturnType<typeof createHash>,
  record: DigestRecord
): void {
  const marker = record.kind === "file" ? "F" : record.kind === "link" ? "L" : "O";
  hash.update(`${marker}\0${record.relativePath}\0`);
  hash.update(record.content);
  hash.update("\0");
}

function normalizeDigestPath(path: string): string {
  return sep === "/" ? path : path.split(sep).join("/");
}
