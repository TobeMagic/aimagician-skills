import { execFile } from "node:child_process";
import { access, mkdir, rm, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export async function ensureBuiltCli(): Promise<void> {
  if (await isDistReady()) {
    return;
  }

  const lockDir = join(process.cwd(), "node_modules", ".cache", "aimagician-superpower-build.lock");
  const stampPath = join(process.cwd(), "node_modules", ".cache", "aimagician-superpower-build.stamp");
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
    return true;
  } catch {
    return false;
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}
