#!/usr/bin/env node

import type { CommandOutput, ParsedCli } from "../bootstrap/command-types";
import { runBootstrap } from "../bootstrap/run-bootstrap";
import { inspectInstallation } from "../inspection/inspect-installation";
import {
  installSkills,
  resetSkills,
  searchSkills,
  uninstallSkills,
  type InstallSkillsResult,
  type ManagerSkillRecord,
  type ResetSkillsResult,
  type UninstallSkillsResult
} from "../manager/manager";
import {
  formatOwnedSkills,
  type FormatOwnedSkillsResult
} from "../manager/skill-format";
import { runDashboard } from "../tui/dashboard";
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

    if (parsed.command === "tui") {
      return {
        exitCode: 0,
        stdout: renderTuiNotice(),
        stderr: ""
      };
    }

    if (parsed.command === "bootstrap") {
      const result = await runBootstrap({
        selectedTargets: parsed.targets,
        dryRun: parsed.dryRun,
        clean: parsed.clean,
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

    if (parsed.command === "search") {
      const result = await searchSkills({
        query: parsed.query,
        category: parsed.category,
        subcategory: parsed.subcategory,
        tags: parsed.tags,
        scope: parsed.scope,
        projectDir: parsed.projectDir,
        selectedTargets: parsed.targets,
        includeArchived: parsed.includeArchived,
        platform: parsed.homeDir ? { homeDir: parsed.homeDir } : undefined
      });

      return {
        exitCode: 0,
        stdout: parsed.json
          ? JSON.stringify({ command: parsed.command, scope: parsed.scope, skills: result }, null, 2)
          : renderSearch(result),
        stderr: ""
      };
    }

    if (parsed.command === "install") {
      const result = await installSkills({
        assetIds: parsed.assetIds,
        category: parsed.category,
        subcategory: parsed.subcategory,
        tags: parsed.tags,
        scope: parsed.scope,
        projectDir: parsed.projectDir,
        selectedTargets: parsed.targets,
        includeArchived: parsed.includeArchived,
        dryRun: parsed.dryRun,
        platform: parsed.homeDir ? { homeDir: parsed.homeDir } : undefined
      });

      return {
        exitCode: 0,
        stdout: parsed.json
          ? JSON.stringify({ command: parsed.command, ...result }, null, 2)
          : renderInstall(result),
        stderr: ""
      };
    }

    if (parsed.command === "uninstall") {
      const result = await uninstallSkills({
        assetIds: parsed.assetIds,
        scope: parsed.scope,
        projectDir: parsed.projectDir,
        selectedTargets: parsed.targets,
        platform: parsed.homeDir ? { homeDir: parsed.homeDir } : undefined
      });

      return {
        exitCode: 0,
        stdout: parsed.json
          ? JSON.stringify({ command: parsed.command, ...result }, null, 2)
          : renderUninstall(result),
        stderr: ""
      };
    }

    if (parsed.command === "reset") {
      const result = await resetSkills({
        target: parsed.targets[0]!,
        scope: parsed.scope,
        projectDir: parsed.projectDir,
        installAll: parsed.installAll,
        yes: parsed.yes,
        dryRun: parsed.dryRun,
        platform: parsed.homeDir ? { homeDir: parsed.homeDir } : undefined
      });

      return {
        exitCode: 0,
        stdout: parsed.json
          ? JSON.stringify({ command: parsed.command, ...result }, null, 2)
          : renderReset(result),
        stderr: ""
      };
    }

    if (parsed.command === "format-skills") {
      const result = await formatOwnedSkills({ mode: parsed.mode });

      return {
        exitCode: result.records.some((record) => record.status !== "ok") && parsed.mode === "check" ? 1 : 0,
        stdout: parsed.json
          ? JSON.stringify({ command: parsed.command, ...result }, null, 2)
          : renderFormatSkills(result),
        stderr: ""
      };
    }

    const inspection = await inspectInstallation({
      selectedTargets: parsed.targets,
      scope: parsed.scope,
      projectDir: parsed.projectDir,
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
  const parsed = parseCli(argv);

  if (parsed.command === "tui" && !parsed.help && process.stdin.isTTY && process.stdout.isTTY) {
    await runDashboard({
      selectedTargets: parsed.targets,
      projectDir: parsed.projectDir,
      platform: parsed.homeDir ? { homeDir: parsed.homeDir } : undefined
    });
    return;
  }

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
      scope: inspection.scope,
      status: inspection.status,
      workspaceRoot: inspection.workspaceRoot,
      manifestPath: inspection.manifestPath,
      manifestExists: inspection.manifestExists,
      targets: inspection.targets.map((target) => ({
        target: target.target,
        status: target.status,
        managedCount: target.managedInstalls.length,
        commandCount: target.commandInstalls.length,
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
    "Skillbird bootstrap",
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
    "Usage: skillbird <command> [--target <codex|claude|opencode|gemini|hermes|cursor|copilot>] [--json]",
    "",
    "Commands:",
    "  tui           Open the skill manager dashboard (default command)",
    "  search        Search local packaged skills",
    "  install       Install selected skills, or preview with --dry-run (requires --scope)",
    "  uninstall     Uninstall managed skills only (requires --scope)",
    "  reset         Clear one target scope and reinstall all active skills",
    "  format-skills Check or write owned skill category frontmatter",
    "  bootstrap     Run the legacy all-selected bootstrap workflow",
    "  list          Show detected assets per target and scope",
    "  inspect       Show detailed target inspection output",
    "  doctor        Verify managed installs against live target homes",
    "",
    "Options:",
    "  --targets     Comma-separated targets to include",
    "  --target      Single target override (repeatable)",
    "  --scope       Scope for manager commands: global or project; reset also supports all",
    "  --project     Project directory for project scope (default: current directory)",
    "  --home        Override the effective home directory (default: current ~/)",
    "  --category    Search/install skills by category slug",
    "  --subcategory Search/install skills by subcategory slug",
    "  --tag, --tags Search/install skills by tag slug (comma-separated accepted)",
    "  --check       format-skills check mode (default)",
    "  --write       format-skills write mode",
    "  --install-all Reset-only flag: reinstall every active skill after clearing",
    "  --yes, -y     Confirm reset when applying changes",
    "  --include-archived  Show or install archived owned skills",
    "  --dry-run     Print bootstrap/install/reset intent without applying changes",
    "  --clean       Wipe all target skill/plugin dirs before install (bootstrap only)",
    "  --json        Render machine-readable output",
    "  -h, --help    Show command help"
  ].join("\n");
}

function renderTuiNotice(): string {
  return [
    "Skillbird dashboard",
    "Interactive dashboard support is available through the tui command in a terminal session.",
    "Use search/install/uninstall for non-interactive workflows."
  ].join("\n");
}

function renderSearch(skills: ManagerSkillRecord[]): string {
  return [
    "Skillbird search",
    ...skills.map((skill) => {
      const status = skill.installedTargets.length > 0
        ? `installed: ${skill.installedTargets.join(",")}`
        : "not installed";
      const source = skill.sourceId ? ` from ${skill.sourceId}` : "";
      const archiveStatus = skill.archived ? " archived" : "";

      return `${skill.id} [${skill.group}${skill.subgroup ? `/${skill.subgroup}` : ""}] ${status}${source}${archiveStatus}`;
    })
  ].join("\n");
}

function renderInstall(result: InstallSkillsResult): string {
  return [
    "Skillbird install",
    `Mode: ${result.dryRun ? "dry-run" : "apply"}`,
    `Scope: ${result.scope}`,
    `Workspace: ${result.workspaceRoot}`,
    `Installed: ${result.installed.length > 0 ? result.installed.map((install) => `${install.assetId}->${install.target}`).join(", ") : "none"}`,
    `Command sources: ${result.commandReports.length > 0 ? result.commandReports.map((report) => report.sourceId).join(", ") : "none"}`,
    `Skipped: ${result.skipped.length > 0 ? result.skipped.map((skip) => `${skip.assetId} (${skip.reason})`).join(", ") : "none"}`
  ].join("\n");
}

function renderUninstall(result: UninstallSkillsResult): string {
  return [
    "Skillbird uninstall",
    `Scope: ${result.scope}`,
    `Workspace: ${result.workspaceRoot}`,
    `Removed: ${result.removed.length > 0 ? result.removed.map((install) => `${install.assetId}->${install.target}`).join(", ") : "none"}`,
    `Skipped: ${result.skipped.length > 0 ? result.skipped.map((skip) => `${skip.assetId}->${skip.target} (${skip.reason})`).join(", ") : "none"}`
  ].join("\n");
}

function renderReset(result: ResetSkillsResult): string {
  return [
    "Skillbird reset",
    `Target: ${result.target}`,
    `Mode: ${result.dryRun ? "dry-run" : "apply"}`,
    ...result.scopes.flatMap((scopeResult) => [
      `Scope: ${scopeResult.scope}`,
      `  Workspace: ${scopeResult.workspaceRoot}`,
      `  Removed roots: ${scopeResult.removedRoots.length > 0 ? scopeResult.removedRoots.join(", ") : "none"}`,
      `  Installed: ${scopeResult.installed.length > 0 ? scopeResult.installed.map((install) => install.assetId).join(", ") : "none"}`,
      `  Command sources: ${scopeResult.commandReports.length > 0 ? scopeResult.commandReports.map((report) => report.sourceId).join(", ") : "none"}`,
      `  Skipped: ${scopeResult.skipped.length > 0 ? scopeResult.skipped.map((skip) => `${skip.assetId} (${skip.reason})`).join(", ") : "none"}`
    ])
  ].join("\n");
}

function renderFormatSkills(result: FormatOwnedSkillsResult): string {
  const issueRecords = result.records.filter((record) => record.status !== "ok");

  return [
    "Skillbird format-skills",
    `Mode: ${result.mode}`,
    `Changed: ${result.changed ? "yes" : "no"}`,
    `Checked: ${result.records.length}`,
    `Issues: ${issueRecords.length > 0 ? issueRecords.length : "none"}`,
    ...issueRecords.map((record) => {
      const classification = record.status === "missing-taxonomy"
        ? "missing taxonomy"
        : `${record.category ?? "uncategorized"}${record.subcategory ? `/${record.subcategory}` : ""}`;

      return `  ${record.id}: ${classification} (${record.issues.join(", ")})`;
    })
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
    report.rulesDir ? ` @ ${report.rulesDir}` :
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
    "Skillbird list",
    `Scope: ${inspection.scope}`,
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
        `  plugins: ${plugins.length > 0 ? plugins.join(", ") : "none"}`,
        `  command sources: ${target.commandInstalls.length > 0 ? target.commandInstalls.map((install) => install.sourceId).join(", ") : "none"}`
      ];
    })
  ].join("\n");
}

function renderInspect(
  inspection: Awaited<ReturnType<typeof inspectInstallation>>
): string {
  return [
    "Skillbird inspect",
    `Scope: ${inspection.scope}`,
    `Workspace: ${inspection.workspaceRoot}`,
    `Manifest path: ${inspection.manifestPath}`,
    ...inspection.targets.flatMap((target) => [
      `Target ${target.target}: ${target.status}`,
      `  skills dir: ${target.skillsDir ?? "-"}`,
      `  plugins dir: ${target.pluginsDir ?? "-"}`,
      `  extensions dir: ${target.extensionsDir ?? "-"}`,
      `  rules dir: ${target.rulesDir ?? "-"}`,
      `  managed installs: ${target.managedInstalls.length}`,
      `  command installs: ${target.commandInstalls.length > 0 ? target.commandInstalls.map((install) => install.sourceId).join(", ") : "none"}`,
      `  detected assets: ${target.detectedAssets.length}`,
      `  issues: ${target.issues.length > 0 ? target.issues.join(" | ") : "none"}`
    ])
  ].join("\n");
}

function renderDoctor(
  inspection: Awaited<ReturnType<typeof inspectInstallation>>
): string {
  return [
    "Skillbird doctor",
    `Scope: ${inspection.scope}`,
    `Status: ${inspection.status}`,
    `Manifest: ${inspection.manifestExists ? inspection.manifestPath : "missing"}`,
    ...inspection.targets.flatMap((target) => [
      `Target ${target.target}: ${target.status} (${target.managedInstalls.length} managed, ${target.commandInstalls.length} command, ${target.detectedAssets.length} detected)`,
      ...(target.issues.length > 0 ? target.issues.map((issue) => `  issue: ${issue}`) : ["  issue: none"])
    ])
  ].join("\n");
}

if (require.main === module) {
  void main();
}
