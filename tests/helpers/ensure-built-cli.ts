import { execFile } from "node:child_process";
import { access, mkdir, readdir, rm, stat, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const stampPath = join(process.cwd(), "node_modules", ".cache", "aimagician-superpower-build.stamp");

export async function ensureBuiltCli(): Promise<void> {
  if (await isDistReady()) {
    return;
  }

  const lockDir = join(process.cwd(), "node_modules", ".cache", "aimagician-superpower-build.lock");
  await mkdir(join(process.cwd(), "node_modules", ".cache"), { recursive: true });

  for (;;) {
    try {
      await mkdir(lockDir, { recursive: false });
      break;
    } catch (error) {
      if ((error as NodeJS.ErrnoException).code !== "EEXIST") {
        throw error;
      }

      await sleep(250);
      if (await isDistReady()) {
        return;
      }
    }
  }

  try {
    if (!(await isDistReady())) {
      await execFileAsync("npm", ["run", "build"], { cwd: process.cwd() });
      await writeFile(stampPath, new Date().toISOString(), "utf8");
    }
  } finally {
    await rm(lockDir, { recursive: true, force: true });
  }
}

async function isDistReady(): Promise<boolean> {
  try {
    await access(join(process.cwd(), "dist", "cli", "index.js"));
    await access(join(process.cwd(), "dist", "catalog", "schemas.js"));
    await access(join(process.cwd(), "dist", "model", "assets.js"));
    return !await sourceIsNewerThanStamp();
  } catch {
    return false;
  }
}

async function sourceIsNewerThanStamp(): Promise<boolean> {
  try {
    const stamp = await stat(stampPath);
    const newestSource = await newestMtime([
      join(process.cwd(), "src"),
      join(process.cwd(), "package.json"),
      join(process.cwd(), "tsconfig.json")
    ]);
    return newestSource > stamp.mtimeMs;
  } catch {
    return true;
  }
}

async function newestMtime(paths: string[]): Promise<number> {
  let newest = 0;
  for (const path of paths) {
    const item = await stat(path);
    newest = Math.max(newest, item.mtimeMs);
    if (item.isDirectory()) {
      const entries = await readdir(path);
      newest = Math.max(newest, await newestMtime(entries.map((entry) => join(path, entry))));
    }
  }
  return newest;
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
