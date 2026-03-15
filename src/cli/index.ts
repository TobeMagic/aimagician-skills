#!/usr/bin/env node

import type { CommandOutput, ParsedCli } from "../bootstrap/command-types";
import { runBootstrap } from "../bootstrap/run-bootstrap";
import { inspectInstallation } from "../inspection/inspect-installation";
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

    if (parsed.command === "bootstrap") {
      const result = await runBootstrap({
        selectedTargets: parsed.targets,
        dryRun: parsed.dryRun,
        platform: parsed.homeDir ? { homeDir: parsed.homeDir } : undefined
      });

      return {
        exitCode: 0,
        stdout: parsed.json
          ? JSON.stringify(createBootstrapPreview(parsed, result), null, 2)
          : renderBootstrapPreview(parsed, result),
        stderr: ""
      };
    }

    const inspection = await inspectInstallation({
      selectedTargets: parsed.targets,
      platform: parsed.homeDir ? { homeDir: parsed.homeDir } : undefined
    });

    return {
      exitCode: 0,
      stdout: parsed.json
        ? JSON.stringify(createInspectionPreview(parsed.command, inspection), null, 2)
        : renderInspection(parsed.command, inspection),
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

function createInspectionPreview(
  command: "list" | "inspect" | "doctor",
  inspection: Awaited<ReturnType<typeof inspectInstallation>>
) {
  if (command === "doctor") {
    return {
      command,
      status: inspection.status,
      workspaceRoot: inspection.workspaceRoot,
      manifestPath: inspection.manifestPath,
      manifestExists: inspection.manifestExists,
      targets: inspection.targets.map((target) => ({
        target: target.target,
        status: target.status,
        managedCount: target.managedInstalls.length,
        detectedCount: target.detectedAssets.length,
        issues: target.issues
      }))
    };
  }

  return {
    command,
    ...inspection
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

function renderInspection(
  command: "list" | "inspect" | "doctor",
  inspection: Awaited<ReturnType<typeof inspectInstallation>>
): string {
  switch (command) {
    case "list":
      return renderList(inspection);
    case "inspect":
      return renderInspect(inspection);
    case "doctor":
      return renderDoctor(inspection);
  }
}

function renderHelp(): string {
  return [
    "Usage: aimagician-skills <command> [--target claude] [--json]",
    "",
    "Commands:",
    "  bootstrap     Run the bootstrap workflow (default command)",
    "  list          Show detected assets per target",
    "  inspect       Show detailed target inspection output",
    "  doctor        Verify managed installs against live target homes",
    "",
    "Options:",
    "  --targets     Comma-separated targets to include",
    "  --target      Single target override (repeatable)",
    "  --home        Override the effective home directory (default: current ~/)",
    "  --dry-run     Print bootstrap intent without applying changes (bootstrap only)",
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

function renderList(
  inspection: Awaited<ReturnType<typeof inspectInstallation>>
): string {
  return [
    "AImagician Skills list",
    `Workspace: ${inspection.workspaceRoot}`,
    `Manifest: ${inspection.manifestExists ? "present" : "missing"}`,
    ...inspection.targets.flatMap((target) => {
      const skills = target.detectedAssets
        .filter((asset) => asset.kind === "skill")
        .map((asset) => asset.id);
      const plugins = target.detectedAssets
        .filter((asset) => asset.kind === "plugin")
        .map((asset) => asset.id);

      return [
        `Target ${target.target}: ${target.status}`,
        `  skills: ${skills.length > 0 ? skills.join(", ") : "none"}`,
        `  plugins: ${plugins.length > 0 ? plugins.join(", ") : "none"}`
      ];
    })
  ].join("\n");
}

function renderInspect(
  inspection: Awaited<ReturnType<typeof inspectInstallation>>
): string {
  return [
    "AImagician Skills inspect",
    `Workspace: ${inspection.workspaceRoot}`,
    `Manifest path: ${inspection.manifestPath}`,
    ...inspection.targets.flatMap((target) => [
      `Target ${target.target}: ${target.status}`,
      `  skills dir: ${target.skillsDir ?? "-"}`,
      `  plugins dir: ${target.pluginsDir ?? "-"}`,
      `  extensions dir: ${target.extensionsDir ?? "-"}`,
      `  managed installs: ${target.managedInstalls.length}`,
      `  detected assets: ${target.detectedAssets.length}`,
      `  issues: ${target.issues.length > 0 ? target.issues.join(" | ") : "none"}`
    ])
  ].join("\n");
}

function renderDoctor(
  inspection: Awaited<ReturnType<typeof inspectInstallation>>
): string {
  return [
    "AImagician Skills doctor",
    `Status: ${inspection.status}`,
    `Manifest: ${inspection.manifestExists ? inspection.manifestPath : "missing"}`,
    ...inspection.targets.flatMap((target) => [
      `Target ${target.target}: ${target.status} (${target.managedInstalls.length} managed, ${target.detectedAssets.length} detected)`,
      ...(target.issues.length > 0 ? target.issues.map((issue) => `  issue: ${issue}`) : ["  issue: none"])
    ])
  ].join("\n");
}

if (require.main === module) {
  void main();
}
