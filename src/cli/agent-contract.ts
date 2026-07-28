import type { CommandOutput } from "../bootstrap/command-types";
import { supportedTargets, type SupportedTarget } from "../model/targets";

export const agentSchemaVersion = 1;

export type AgentCommandMode = "read" | "preview" | "apply";
export type AgentCommandStatus = "ok" | "partial" | "error";

export interface AgentMessage {
  code: string;
  message: string;
  target?: SupportedTarget;
  assetId?: string;
}

export interface AgentEnvelope<T = unknown> {
  schemaVersion: 1;
  command: string;
  status: AgentCommandStatus;
  mode: AgentCommandMode;
  data: T;
  warnings: AgentMessage[];
  errors: AgentMessage[];
  nextActions: string[];
}

export interface AgentOutputOptions<T> {
  command: string;
  status?: AgentCommandStatus;
  mode: AgentCommandMode;
  data: T;
  warnings?: AgentMessage[];
  errors?: AgentMessage[];
  nextActions?: string[];
  exitCode?: number;
}

export function createAgentOutput<T>(options: AgentOutputOptions<T>): CommandOutput {
  const envelope: AgentEnvelope<T> = {
    schemaVersion: agentSchemaVersion,
    command: options.command,
    status: options.status ?? "ok",
    mode: options.mode,
    data: options.data,
    warnings: options.warnings ?? [],
    errors: options.errors ?? [],
    nextActions: options.nextActions ?? []
  };

  return {
    exitCode: options.exitCode ?? 0,
    stdout: JSON.stringify(envelope, null, 2),
    stderr: ""
  };
}

export function createAgentError(
  command: string,
  code: string,
  message: string,
  exitCode: 1 | 2
): CommandOutput {
  return createAgentOutput({
    command,
    status: "error",
    mode: "read",
    data: {},
    errors: [{ code, message: stripAnsi(message) }],
    exitCode
  });
}

export function createAgentCapabilities() {
  return {
    targets: [...supportedTargets],
    scopes: ["global", "project"],
    resetScopes: ["global", "project", "all"],
    commands: [
      command("capabilities", "read", false, "Describe the stable Agent CLI contract."),
      command("search", "read", false, "Search packaged skills by query or taxonomy."),
      command("list", "read", false, "List detected assets for selected targets and scope."),
      command("inspect", "read", false, "Return detailed installation state."),
      command("doctor", "read", false, "Validate managed installs; unhealthy state exits 1."),
      command("bootstrap", "write", true, "Synchronize the complete selected target set."),
      command("install", "write", true, "Install selected or taxonomy-filtered skills."),
      command("uninstall", "write", true, "Remove only managed skill installs."),
      command("reset", "write", true, "Clear and reinstall an explicitly selected target scope."),
      command("format-skills", "write", true, "Check or repair owned skill taxonomy frontmatter.")
    ],
    mutationContract: {
      default: "preview",
      applyFlag: "--yes",
      explicitPreviewFlag: "--dry-run",
      conflict: "--yes and --dry-run cannot be combined in Agent mode"
    },
    exitCodes: {
      "0": "Success, preview success, or idempotent no-op.",
      "1": "Execution, validation, or doctor health failure.",
      "2": "CLI usage or argument error.",
      "3": "Partial result: at least one required target or requested asset was not completed."
    },
    examples: [
      "skillbird capabilities --agent",
      "skillbird search workflow --scope global --agent",
      "skillbird install aimagician-superpower --scope global --target codex --agent",
      "skillbird install aimagician-superpower --scope global --target codex --agent --yes",
      "skillbird doctor --scope global --targets codex,opencode --agent"
    ]
  };
}

function command(
  name: string,
  kind: "read" | "write",
  confirmationRequired: boolean,
  description: string
) {
  return { name, kind, confirmationRequired, description };
}

function stripAnsi(value: string): string {
  return value.replace(/\u001B\[[0-?]*[ -/]*[@-~]/g, "");
}

