import { supportedTargets, type SupportedTarget } from "../model/targets";
import { isInstallScope, isResetScope, type InstallScope, type ResetScope } from "../model/scopes";
import type {
  BootstrapCommand,
  DoctorCommand,
  InstallCommand,
  InspectCommand,
  ListCommand,
  FormatSkillsCommand,
  ParsedCli,
  ResetCommand,
  SearchCommand,
  TuiCommand,
  UninstallCommand
} from "../bootstrap/command-types";

const supportedTargetSet = new Set<SupportedTarget>(supportedTargets);
const supportedCommands = [
  "tui",
  "bootstrap",
  "search",
  "install",
  "uninstall",
  "reset",
  "format-skills",
  "list",
  "inspect",
  "doctor"
] as const;

type SupportedCommand = (typeof supportedCommands)[number];

export function parseCli(argv: string[]): ParsedCli {
  const args = [...argv];
  const firstArg = args[0];
  const command =
    !firstArg || firstArg.startsWith("-") ? "tui" : consumeCommand(args.shift()!);

  const targetSelections: SupportedTarget[] = [];
  let dryRun = false;
  let clean = false;
  let json = false;
  let help = false;
  let includeArchived = false;
  let installAll = false;
  let yes = false;
  let homeDir: string | undefined;
  let scope: InstallScope | ResetScope | undefined;
  let projectDir: string | undefined;
  let category: string | undefined;
  let subcategory: string | undefined;
  const tags: string[] = [];
  let formatMode: "check" | "write" | undefined;
  const positional: string[] = [];

  while (args.length > 0) {
    const argument = args.shift()!;

    switch (argument) {
      case "--dry-run":
        if (command !== "bootstrap" && command !== "install" && command !== "reset") {
          throw new Error(`Unsupported argument for ${command}: ${argument}`);
        }
        dryRun = true;
        break;
      case "--check":
        if (command !== "format-skills") {
          throw new Error(`Unsupported argument for ${command}: ${argument}`);
        }
        formatMode = "check";
        break;
      case "--write":
        if (command !== "format-skills") {
          throw new Error(`Unsupported argument for ${command}: ${argument}`);
        }
        formatMode = "write";
        break;
      case "--install-all":
        if (command !== "reset") {
          throw new Error(`Unsupported argument for ${command}: ${argument}`);
        }
        installAll = true;
        break;
      case "--yes":
      case "-y":
        if (command !== "reset") {
          throw new Error(`Unsupported argument for ${command}: ${argument}`);
        }
        yes = true;
        break;
      case "--include-archived":
        if (command !== "search" && command !== "install") {
          throw new Error(`Unsupported argument for ${command}: ${argument}`);
        }
        includeArchived = true;
        break;
      case "--clean":
        if (command !== "bootstrap") {
          throw new Error(`Unsupported argument for ${command}: ${argument}`);
        }
        clean = true;
        break;
      case "--json":
        json = true;
        break;
      case "--help":
      case "-h":
        help = true;
        break;
      case "--targets":
      case "--target":
        targetSelections.push(...parseTargetArgument(args.shift(), argument));
        break;
      case "--scope":
        scope = command === "reset"
          ? parseResetScopeArgument(args.shift(), argument)
          : parseInstallScopeArgument(args.shift(), argument);
        break;
      case "--project":
        projectDir = parsePathArgument(args.shift(), argument);
        break;
      case "--home":
        homeDir = parsePathArgument(args.shift(), argument);
        break;
      case "--category":
        if (command !== "search" && command !== "install") {
          throw new Error(`Unsupported argument for ${command}: ${argument}`);
        }
        category = parseSlugArgument(args.shift(), argument);
        break;
      case "--subcategory":
        if (command !== "search" && command !== "install") {
          throw new Error(`Unsupported argument for ${command}: ${argument}`);
        }
        subcategory = parseSlugArgument(args.shift(), argument);
        break;
      case "--tag":
      case "--tags":
        if (command !== "search" && command !== "install") {
          throw new Error(`Unsupported argument for ${command}: ${argument}`);
        }
        tags.push(...parseSlugListArgument(args.shift(), argument));
        break;
      default:
        if (argument.startsWith("-")) {
          throw new Error(`Unsupported argument: ${argument}`);
        }
        positional.push(argument);
    }
  }

  const base = {
    targets: targetSelections.length > 0 ? dedupeTargets(targetSelections) : [...supportedTargets],
    json,
    help,
    ...(homeDir ? { homeDir } : {})
  };

  switch (command) {
    case "tui":
      return {
        command,
        ...base,
        ...(projectDir ? { projectDir } : {})
      } satisfies TuiCommand;
    case "bootstrap":
      rejectScopeForBootstrap(scope, projectDir);
      return {
        command,
        dryRun,
        ...(clean ? { clean: true } : {}),
        ...base
      } satisfies BootstrapCommand;
    case "search":
      assertInstallScopeForCommand(command, scope);
      return {
        command,
        query: positional.length > 0 ? positional.join(" ") : undefined,
        scope: scope ?? "global",
        ...(projectDir ? { projectDir } : {}),
        ...(includeArchived ? { includeArchived: true } : {}),
        ...(category ? { category } : {}),
        ...(subcategory ? { subcategory } : {}),
        ...(tags.length > 0 ? { tags: dedupeStrings(tags) } : {}),
        ...base
      } satisfies SearchCommand;
    case "install":
      assertScopedMutation(command, scope, positional, Boolean(category || subcategory || tags.length > 0));
      return {
        command,
        assetIds: positional,
        scope,
        dryRun,
        ...(projectDir ? { projectDir } : {}),
        ...(includeArchived ? { includeArchived: true } : {}),
        ...(category ? { category } : {}),
        ...(subcategory ? { subcategory } : {}),
        ...(tags.length > 0 ? { tags: dedupeStrings(tags) } : {}),
        ...base
      } satisfies InstallCommand;
    case "uninstall":
      assertScopedMutation(command, scope, positional);
      return {
        command,
        assetIds: positional,
        scope,
        ...(projectDir ? { projectDir } : {}),
        ...base
      } satisfies UninstallCommand;
    case "reset":
      assertResetCommand(scope, targetSelections.length, positional, installAll);
      return {
        command,
        scope,
        ...(projectDir ? { projectDir } : {}),
        installAll,
        yes,
        dryRun,
        ...base
      } satisfies ResetCommand;
    case "format-skills":
      assertFormatSkillsCommand(scope, projectDir, positional, formatMode);
      return {
        command,
        mode: formatMode ?? "check",
        ...base
      } satisfies FormatSkillsCommand;
    case "list":
      assertInstallScopeForCommand(command, scope);
      return {
        command,
        scope: scope ?? "global",
        ...(projectDir ? { projectDir } : {}),
        ...base
      } satisfies ListCommand;
    case "inspect":
      assertInstallScopeForCommand(command, scope);
      return {
        command,
        scope: scope ?? "global",
        ...(projectDir ? { projectDir } : {}),
        ...base
      } satisfies InspectCommand;
    case "doctor":
      assertInstallScopeForCommand(command, scope);
      return {
        command,
        scope: scope ?? "global",
        ...(projectDir ? { projectDir } : {}),
        ...base
      } satisfies DoctorCommand;
  }
}

function consumeCommand(command: string): SupportedCommand {
  if (!(supportedCommands as readonly string[]).includes(command)) {
    throw new Error(`Unsupported command: ${command}`);
  }

  return command as SupportedCommand;
}

function parseTargetArgument(value: string | undefined, flag: string): SupportedTarget[] {
  if (!value) {
    throw new Error(`Missing value for ${flag}`);
  }

  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean)
    .map(parseTarget);
}

function parseTarget(target: string): SupportedTarget {
  if (!supportedTargetSet.has(target as SupportedTarget)) {
    throw new Error(`Unsupported target: ${target}`);
  }

  return target as SupportedTarget;
}

function parsePathArgument(value: string | undefined, flag: string): string {
  if (!value) {
    throw new Error(`Missing value for ${flag}`);
  }

  return value;
}

function parseSlugArgument(value: string | undefined, flag: string): string {
  if (!value) {
    throw new Error(`Missing value for ${flag}`);
  }

  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value)) {
    throw new Error(`Unsupported ${flag} value: ${value}`);
  }

  return value;
}

function parseSlugListArgument(value: string | undefined, flag: string): string[] {
  if (!value) {
    throw new Error(`Missing value for ${flag}`);
  }

  return value
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean)
    .map((entry) => parseSlugArgument(entry, flag));
}

function parseInstallScopeArgument(value: string | undefined, flag: string): InstallScope {
  if (!value) {
    throw new Error(`Missing value for ${flag}`);
  }

  if (value === "all") {
    throw new Error("Scope all is only supported for reset");
  }

  if (!isInstallScope(value)) {
    throw new Error(`Unsupported scope: ${value}`);
  }

  return value;
}

function parseResetScopeArgument(value: string | undefined, flag: string): ResetScope {
  if (!value) {
    throw new Error(`Missing value for ${flag}`);
  }

  if (!isResetScope(value)) {
    throw new Error(`Unsupported scope: ${value}`);
  }

  return value;
}

function assertInstallScopeForCommand(
  command: "search" | "list" | "inspect" | "doctor",
  scope: InstallScope | ResetScope | undefined
): asserts scope is InstallScope | undefined {
  if (scope === "all") {
    throw new Error("Scope all is only supported for reset");
  }
}

function assertScopedMutation(
  command: "install" | "uninstall",
  scope: InstallScope | ResetScope | undefined,
  assetIds: string[],
  hasSelector = false
): asserts scope is InstallScope {
  if (!scope) {
    throw new Error(`Missing required --scope for ${command}`);
  }

  if (scope === "all") {
    throw new Error("Scope all is only supported for reset");
  }

  if (assetIds.length === 0 && !hasSelector) {
    throw new Error(`Missing skill id for ${command}`);
  }
}

function assertFormatSkillsCommand(
  scope: InstallScope | ResetScope | undefined,
  projectDir: string | undefined,
  positional: string[],
  mode: "check" | "write" | undefined
): void {
  rejectScopeForBootstrap(scope, projectDir);

  if (positional.length > 0) {
    throw new Error("format-skills does not accept skill ids");
  }

  if (mode && mode !== "check" && mode !== "write") {
    throw new Error(`Unsupported format-skills mode: ${mode}`);
  }
}

function assertResetCommand(
  scope: InstallScope | ResetScope | undefined,
  selectedTargetCount: number,
  positional: string[],
  installAll: boolean
): asserts scope is ResetScope {
  if (!scope) {
    throw new Error("Missing required --scope for reset");
  }

  if (selectedTargetCount !== 1) {
    throw new Error("reset requires exactly one --target");
  }

  if (positional.length > 0) {
    throw new Error("reset does not accept skill ids; use --install-all");
  }

  if (!installAll) {
    throw new Error("reset requires --install-all");
  }
}

function rejectScopeForBootstrap(
  scope: InstallScope | ResetScope | undefined,
  projectDir: string | undefined
): void {
  if (scope || projectDir) {
    throw new Error("bootstrap does not support --scope or --project; use install/uninstall for scoped changes");
  }
}

function dedupeTargets(targets: SupportedTarget[]): SupportedTarget[] {
  return [...new Set(targets)];
}

function dedupeStrings(values: string[]): string[] {
  return [...new Set(values)];
}
