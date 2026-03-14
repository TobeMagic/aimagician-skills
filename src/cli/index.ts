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
    changed: result.changed,
    targetReports: result.targetReports,
    pluginReports: result.pluginReports,
    commandReports: result.commandReports
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
    `Changes applied: ${preview.changed ? "yes" : "no"}`,
    ...preview.targetReports.map((report) => renderTargetReport(report)),
    ...preview.pluginReports.map((report) => renderPluginReport(report)),
    ...preview.commandReports.map((report) => renderCommandReport(report))
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

function renderTargetReport(
  report: Awaited<ReturnType<typeof runBootstrap>>["targetReports"][number]
): string {
  const skillCount = report.installedSkillIds.length;
  const pluginCount = report.installedPluginIds.length;

  if (report.status === "deferred") {
    return `Target ${report.target}: deferred (${report.reason})`;
  }

  const location =
    report.skillsDir ? ` @ ${report.skillsDir}` :
    report.extensionsDir ? ` @ ${report.extensionsDir}` :
    "";

  const pluginSummary =
    pluginCount > 0
      ? `, ${pluginCount} plugins${report.pluginsDir ? ` @ ${report.pluginsDir}` : ""}`
      : "";

  return `Target ${report.target}: ${report.status} (${skillCount} skills${pluginSummary})${location}`;
}

function renderPluginReport(
  report: Awaited<ReturnType<typeof runBootstrap>>["pluginReports"][number]
): string {
  const destination = report.destinationPath ? ` @ ${report.destinationPath}` : "";
  const reason = report.reason ? ` (${report.reason})` : "";

  return `Plugin ${report.assetId} -> ${report.target}: ${report.status}${destination}${reason}`;
}

function renderCommandReport(
  report: Awaited<ReturnType<typeof runBootstrap>>["commandReports"][number]
): string {
  return `Command source ${report.sourceId}: ${report.status} (${report.assetIds.length} skills -> ${report.targets.join(", ")})`;
}

if (require.main === module) {
  void main();
}
