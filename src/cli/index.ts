#!/usr/bin/env node

import type { CommandOutput, ParsedCli } from "../bootstrap/command-types";
import { runBootstrap } from "../bootstrap/run-bootstrap";
import { parseCli } from "./parse-cli";

export async function runCli(argv: string[]): Promise<CommandOutput> {
  try {
    const parsed = parseCli(argv);

    if (parsed.help) {
      return {
        exitCode: 0,
        stdout: renderHelp(),
        stderr: ""
      };
    }

    const result = await runBootstrap({
      selectedTargets: parsed.targets,
      dryRun: parsed.dryRun
    });

    return {
      exitCode: 0,
      stdout: parsed.json
        ? JSON.stringify(createBootstrapPreview(parsed, result), null, 2)
        : renderBootstrapPreview(parsed, result),
      stderr: ""
    };
  } catch (error) {
    return {
      exitCode: 1,
      stdout: "",
      stderr: error instanceof Error ? error.message : "Unknown CLI error"
    };
  }
}

export async function main(argv: string[] = process.argv.slice(2)): Promise<void> {
  const result = await runCli(argv);

  if (result.stdout) {
    process.stdout.write(`${result.stdout}\n`);
  }

  if (result.stderr) {
    process.stderr.write(`${result.stderr}\n`);
  }

  if (result.exitCode !== 0) {
    process.exitCode = result.exitCode;
  }
}

function createBootstrapPreview(parsed: ParsedCli, result: Awaited<ReturnType<typeof runBootstrap>>) {
  return {
    command: parsed.command,
    mode: result.mode,
    targets: parsed.targets,
    workspaceRoot: result.workspaceRoot,
    assetCount: result.plan.assets.length,
    ownedSkillCount: result.plan.ownedSkillIds.length,
    changed: result.changed
  };
}

function renderBootstrapPreview(
  parsed: ParsedCli,
  result: Awaited<ReturnType<typeof runBootstrap>>
): string {
  const preview = createBootstrapPreview(parsed, result);

  return [
    "AImagician Skills bootstrap",
    `Mode: ${preview.mode}`,
    `Targets: ${preview.targets.join(", ")}`,
    `Workspace: ${preview.workspaceRoot}`,
    `Owned skills: ${preview.ownedSkillCount}`,
    `Planned assets: ${preview.assetCount}`,
    `Changes applied: ${preview.changed ? "yes" : "no"}`
  ].join("\n");
}

function renderHelp(): string {
  return [
    "Usage: aimagician-skills [bootstrap] [--targets codex,claude] [--dry-run] [--json]",
    "",
    "Commands:",
    "  bootstrap     Run the bootstrap workflow (default command)",
    "",
    "Options:",
    "  --targets     Comma-separated targets to include",
    "  --target      Single target override (repeatable)",
    "  --dry-run     Print bootstrap intent without applying changes",
    "  --json        Render machine-readable output",
    "  -h, --help    Show command help"
  ].join("\n");
}

if (require.main === module) {
  void main();
}
