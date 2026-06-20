import { execFile } from "node:child_process";
import { constants } from "node:fs";
import { access, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { afterEach, describe, expect, it } from "vitest";

const execFileAsync = promisify(execFile);
const tempDirectories: string[] = [];
const skillRoot = join(process.cwd(), "skills", "owned", "llm-know-how-wiki");
const python = process.env.PYTHON ?? "python";

afterEach(async () => {
  await Promise.allSettled(
    tempDirectories.splice(0).map((directory) =>
      rm(directory, { recursive: true, force: true })
    )
  );
});

describe("llm-know-how-wiki secret inventory", () => {
  it("copies workspace secrets into the local vault without leaking reports or modifying sources", async () => {
    const root = await mkdtemp(join(tmpdir(), "llm-wiki-secret-inventory-"));
    tempDirectories.push(root);
    const wikiRoot = join(root, "LLM-know-how-wiki");
    const repoA = join(root, "service-a");
    const repoB = join(root, "service-b");
    await mkdir(repoA, { recursive: true });
    await mkdir(repoB, { recursive: true });
    await execFileAsync("git", ["init"], { cwd: repoA });
    await execFileAsync("git", ["init"], { cwd: repoB });

    const openAiKey = "sk-test_123456789012345678901234567890";
    const npmToken = "npm_secret_token_1234567890abcdef";
    const envContents = `OPENAI_API_KEY=${openAiKey}\n`;
    const npmrcContents = `//registry.npmjs.org/:_authToken=${npmToken}\n`;
    await writeFile(join(repoA, ".env"), envContents, "utf8");
    await writeFile(join(repoB, ".npmrc"), npmrcContents, "utf8");

    await execFileAsync(python, [join(skillRoot, "scripts", "init_wiki.py"), wikiRoot], { cwd: root });
    const { stdout } = await execFileAsync(
      python,
      [
        join(skillRoot, "scripts", "secret_inventory.py"),
        "--workspace",
        root,
        "--wiki-root",
        wikiRoot,
        "--json"
      ],
      { cwd: root, maxBuffer: 1024 * 1024 }
    );

    const result = JSON.parse(stdout) as {
      findings: number;
      vault_write: boolean;
      vault_added: number;
      registry_added: number;
      snapshot: string;
    };
    expect(result.findings).toBeGreaterThanOrEqual(2);
    expect(result.vault_write).toBe(true);
    expect(result.vault_added).toBe(2);
    expect(result.registry_added).toBe(2);
    expect(stdout).not.toContain(openAiKey);
    expect(stdout).not.toContain(npmToken);

    const vault = await readFile(join(wikiRoot, "secrets", "vault.local.env"), "utf8");
    const registry = await readFile(join(wikiRoot, "secrets", "registry.yaml"), "utf8");
    const report = await readFile(result.snapshot, "utf8");
    expect(vault).toContain(openAiKey);
    expect(vault).toContain(npmToken);
    expect(registry).not.toContain(openAiKey);
    expect(registry).not.toContain(npmToken);
    expect(report).not.toContain(openAiKey);
    expect(report).not.toContain(npmToken);
    expect(report).toContain("sha256:");
    expect(await readFile(join(repoA, ".env"), "utf8")).toBe(envContents);
    expect(await readFile(join(repoB, ".npmrc"), "utf8")).toBe(npmrcContents);

    await execFileAsync(python, [join(skillRoot, "scripts", "scan_sensitive.py"), wikiRoot], { cwd: root });
    const includeVault = await execFileAllowFailure(
      python,
      [join(skillRoot, "scripts", "scan_sensitive.py"), wikiRoot, "--include-vault"],
      root
    );
    expect(includeVault.exitCode).toBe(1);
    expect(includeVault.stdout).not.toContain(openAiKey);
    expect(includeVault.stdout).not.toContain(npmToken);
    expect(includeVault.stdout).toContain("<redacted:");
    await expect(access(join(wikiRoot, "raw", "secret_inventory"), constants.F_OK)).resolves.toBeUndefined();

    const leakedWikiSecret = "wiki_leaked_token_1234567890";
    await writeFile(join(wikiRoot, "raw", "imports", ".env"), `LEAKED_TOKEN=${leakedWikiSecret}\n`, "utf8");
    const wikiLeakScan = await execFileAllowFailure(
      python,
      [join(skillRoot, "scripts", "scan_sensitive.py"), wikiRoot],
      root
    );
    expect(wikiLeakScan.exitCode).toBe(1);
    expect(wikiLeakScan.stdout).not.toContain(leakedWikiSecret);
    expect(wikiLeakScan.stdout).toContain("raw/imports/.env");
  });
});

async function execFileAllowFailure(command: string, args: string[], cwd: string): Promise<{ exitCode: number; stdout: string; stderr: string }> {
  try {
    const result = await execFileAsync(command, args, { cwd, maxBuffer: 1024 * 1024 });
    return { exitCode: 0, stdout: result.stdout, stderr: result.stderr };
  } catch (error) {
    const failure = error as { code?: number; stdout?: string; stderr?: string };
    return {
      exitCode: typeof failure.code === "number" ? failure.code : 1,
      stdout: failure.stdout ?? "",
      stderr: failure.stderr ?? ""
    };
  }
}
