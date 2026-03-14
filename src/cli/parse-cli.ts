import { supportedTargets, type SupportedTarget } from "../model/targets";
import type { BootstrapCommand, ParsedCli } from "../bootstrap/command-types";

const supportedTargetSet = new Set<SupportedTarget>(supportedTargets);

export function parseCli(argv: string[]): ParsedCli {
  const args = [...argv];
  const firstArg = args[0];
  const command =
    !firstArg || firstArg.startsWith("-") ? "bootstrap" : consumeCommand(args.shift()!);

  if (command !== "bootstrap") {
    throw new Error(`Unsupported command: ${command}`);
  }

  const targetSelections: SupportedTarget[] = [];
  let dryRun = false;
  let json = false;
  let help = false;

  while (args.length > 0) {
    const argument = args.shift()!;

    switch (argument) {
      case "--dry-run":
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
      default:
        throw new Error(`Unsupported argument: ${argument}`);
    }
  }

  return {
    command: "bootstrap",
    targets: targetSelections.length > 0 ? dedupeTargets(targetSelections) : [...supportedTargets],
    dryRun,
    json,
    help
  } satisfies BootstrapCommand;
}

function consumeCommand(command: string): "bootstrap" {
  if (command !== "bootstrap") {
    throw new Error(`Unsupported command: ${command}`);
  }

  return command;
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

function dedupeTargets(targets: SupportedTarget[]): SupportedTarget[] {
  return [...new Set(targets)];
}
