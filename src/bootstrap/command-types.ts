import type { SupportedTarget } from "../model/targets";

export interface BootstrapCommand {
  command: "bootstrap";
  targets: SupportedTarget[];
  dryRun: boolean;
  json: boolean;
  help: boolean;
}

export type ParsedCli = BootstrapCommand;

export interface CommandOutput {
  exitCode: number;
  stdout: string;
  stderr: string;
}
