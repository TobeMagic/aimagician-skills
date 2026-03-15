import { supportedTargets, type SupportedTarget } from "../model/targets";
import type {
  BootstrapCommand,
  DoctorCommand,
  InspectCommand,
  ListCommand,
  ParsedCli
} from "../bootstrap/command-types";

const supportedTargetSet = new Set<SupportedTarget>(supportedTargets);
const supportedCommands = ["bootstrap", "list", "inspect", "doctor"] as const;

type SupportedCommand = (typeof supportedCommands)[number];

export function parseCli(argv: string[]): ParsedCli {
  const args = [...argv];
  const firstArg = args[0];
  const command =
    !firstArg || firstArg.startsWith("-") ? "bootstrap" : consumeCommand(args.shift()!);

  const targetSelections: SupportedTarget[] = [];
  let dryRun = false;
  let json = false;
  let help = false;
  let homeDir: string | undefined;

  while (args.length > 0) {
    const argument = args.shift()!;

    switch (argument) {
      case "--dry-run":
        if (command !== "bootstrap") {
          throw new Error(`Unsupported argument for ${command}: ${argument}`);
        }
        dryRun = true;
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
      case "--home":
        homeDir = parsePathArgument(args.shift(), argument);
        break;
      default:
        throw new Error(`Unsupported argument: ${argument}`);
    }
  }

  const base = {
    targets: targetSelections.length > 0 ? dedupeTargets(targetSelections) : [...supportedTargets],
    json,
    help,
    ...(homeDir ? { homeDir } : {})
  };

  switch (command) {
    case "bootstrap":
      return {
        command,
        dryRun,
        ...base
      } satisfies BootstrapCommand;
    case "list":
      return {
        command,
        ...base
      } satisfies ListCommand;
    case "inspect":
      return {
        command,
        ...base
      } satisfies InspectCommand;
    case "doctor":
      return {
        command,
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

function dedupeTargets(targets: SupportedTarget[]): SupportedTarget[] {
  return [...new Set(targets)];
}
