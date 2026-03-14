import { execFile } from "node:child_process";
import { access, mkdtemp, readFile } from "node:fs/promises";
import { constants } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { afterEach, describe, expect, it } from "vitest";

const execFileAsync = promisify(execFile);
const tempDirectories: string[] = [];

afterEach(async () => {
  const { rm } = await import("node:fs/promises");
  await Promise.allSettled(
    tempDirectories.splice(0).map((directory) =>
      rm(directory, { recursive: true, force: true })
    )
  );
});

describe("bootstrap package smoke", () => {
  it("builds, packs, and runs the compiled bootstrap CLI in an isolated workspace", async () => {
    const workspaceRoot = await mkdtemp(join(tmpdir(), "aimagician-smoke-"));
    tempDirectories.push(workspaceRoot);

    await runPackageCommand("run build");
    await runPackageCommand("pack --dry-run");

    const { stdout } = await execFileAsync(
      process.execPath,
      ["dist/cli/index.js", "bootstrap", "--target", "claude", "--json"],
      {
        cwd: process.cwd(),
        env: {
          ...process.env,
          AIMAGICIAN_WORKSPACE_ROOT: workspaceRoot
        }
      }
    );

    const result = JSON.parse(stdout) as {
      mode: string;
      targets: string[];
      workspaceRoot: string;
      assetCount: number;
      changed: boolean;
    };
    const manifestPath = join(workspaceRoot, "manifest.json");

    expect(result.mode).toBe("apply");
    expect(result.targets).toEqual(["claude"]);
    expect(result.workspaceRoot).toBe(workspaceRoot);
    expect(result.assetCount).toBeGreaterThan(0);
    expect(result.changed).toBe(true);
    await access(manifestPath, constants.F_OK);

    const manifest = JSON.parse(await readFile(manifestPath, "utf8")) as {
      assets: Array<{ id: string }>;
    };
    expect(manifest.assets.map((asset) => asset.id)).toContain("gsd");
  }, 30000);
});

async function runPackageCommand(command: string): Promise<void> {
  if (process.platform === "win32") {
    await execFileAsync(process.env.ComSpec ?? "cmd.exe", ["/d", "/s", "/c", `npm.cmd ${command}`], {
      cwd: process.cwd()
    });
    return;
  }

  await execFileAsync("sh", ["-lc", `npm ${command}`], {
    cwd: process.cwd()
  });
}
