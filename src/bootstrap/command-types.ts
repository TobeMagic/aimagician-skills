import type { SupportedTarget } from "../model/targets";
import type { InstallScope, ResetScope } from "../model/scopes";

export interface BaseCliCommand {
  targets: SupportedTarget[];
  json: boolean;
  help: boolean;
  homeDir?: string;
}

export interface BootstrapCommand extends BaseCliCommand {
  command: "bootstrap";
  dryRun: boolean;
  clean?: boolean;
}

export interface ListCommand extends BaseCliCommand {
  command: "list";
  scope: InstallScope;
  projectDir?: string;
}

export interface InspectCommand extends BaseCliCommand {
  command: "inspect";
  scope: InstallScope;
  projectDir?: string;
}

export interface DoctorCommand extends BaseCliCommand {
  command: "doctor";
  scope: InstallScope;
  projectDir?: string;
}

export interface TuiCommand extends BaseCliCommand {
  command: "tui";
  projectDir?: string;
}

export interface SearchCommand extends BaseCliCommand {
  command: "search";
  query?: string;
  scope: InstallScope;
  projectDir?: string;
  includeArchived?: boolean;
}

export interface InstallCommand extends BaseCliCommand {
  command: "install";
  assetIds: string[];
  scope: InstallScope;
  projectDir?: string;
  includeArchived?: boolean;
}

export interface UninstallCommand extends BaseCliCommand {
  command: "uninstall";
  assetIds: string[];
  scope: InstallScope;
  projectDir?: string;
}

export interface ResetCommand extends BaseCliCommand {
  command: "reset";
  scope: ResetScope;
  projectDir?: string;
  installAll: boolean;
  yes: boolean;
  dryRun: boolean;
}

export type ParsedCli =
  | TuiCommand
  | BootstrapCommand
  | SearchCommand
  | InstallCommand
  | UninstallCommand
  | ResetCommand
  | ListCommand
  | InspectCommand
  | DoctorCommand;

export interface CommandOutput {
  exitCode: number;
  stdout: string;
  stderr: string;
}
