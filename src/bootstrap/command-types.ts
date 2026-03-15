import type { SupportedTarget } from "../model/targets";

export interface BaseCliCommand {
  targets: SupportedTarget[];
  json: boolean;
  help: boolean;
  homeDir?: string;
}

export interface BootstrapCommand extends BaseCliCommand {
  command: "bootstrap";
  dryRun: boolean;
}

export interface ListCommand extends BaseCliCommand {
  command: "list";
}

export interface InspectCommand extends BaseCliCommand {
  command: "inspect";
}

export interface DoctorCommand extends BaseCliCommand {
  command: "doctor";
}

export type ParsedCli =
  | BootstrapCommand
  | ListCommand
  | InspectCommand
  | DoctorCommand;

export interface CommandOutput {
  exitCode: number;
  stdout: string;
  stderr: string;
}
