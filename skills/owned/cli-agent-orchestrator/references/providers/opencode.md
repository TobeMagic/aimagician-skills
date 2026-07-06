# OpenCode Provider

Use this provider when the orchestration task should be delegated to OpenCode. OpenCode is currently the default explorer backend.

## Behavior Notes

- `opencode` is often quiet until it produces a final report. No immediate final output is usually a long-run indication, not an error.
- For long-running exploration, prefer explicit log output and heartbeat-driven waiting so the caller does not time out without feedback.

## Preflight

1. Verify the binary:

```bash
command -v opencode
opencode --version
```

2. Inspect available models:

```bash
opencode models
```

3. Inspect installed run syntax:

```bash
opencode run --help
```

4. Resolve the source path. If the task has a project or directory scope:

```bash
test -d "<source_path>"
```

If no path is provided, use the current working directory only after confirming that it is the intended scope.

## Installation

If OpenCode is missing, install only with a user-level package manager or official install script. Do not use `sudo` unless the user explicitly authorizes it.

Preferred options:

```bash
npm install -g opencode-ai
```

or:

```bash
curl -fsSL https://opencode.ai/install | bash
```

After installing:

```bash
opencode --version
opencode models
```

If the binary exists but is not executable:

```bash
chmod +x "<opencode_binary_path>"
```

If the binary is not on `PATH`, fix the user-level shell path and re-run `command -v opencode`.

## Config Merge

Global config path:

```text
~/.config/opencode/opencode.json
```

Rules:

- If config exists, merge missing keys only.
- Do not replace unrelated provider, model, plugin, MCP, instruction, or project settings.
- If merge cannot be done safely, stop and report the needed manual merge.
- Record whether config changed.

Minimal exploration config:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "*": "allow",
    "external_directory": {
      "~/.config/opencode/get-shit-done/*": "allow"
    },
    "read": {
      "~/.config/opencode/get-shit-done/*": "allow"
    }
  },
  "mcp": {
    "linear": {
      "type": "remote",
      "url": "https://mcp.linear.app/mcp",
      "enabled": true
    },
    "notion": {
      "type": "remote",
      "url": "https://mcp.notion.com/mcp",
      "enabled": true
    }
  }
}
```

## Model Selection

Prefer the first available model in this order:

1. `opencode/deepseek-v4-flash-free`
2. `opencode/nemotron-3-ultra-free`
3. `opencode/north-mini-code-free`
4. `opencode/mimo-v2.5-free`
5. `opencode/big-pickle`

If none are available:

- report the available models;
- choose the strongest clearly free model only if obvious;
- otherwise ask for a model decision or stop with a fallback recommendation.

If the selected model fails, retry once with the next available priority model. Do not fabricate results after two failures.

## Execution

Default non-interactive command (prefer this form when supported):

```bash
opencode run --dir "<source_path>" -m "<model>" --format json --print-logs --log-level INFO "<prompt>"
```

On some versions, the prompt can be passed as the trailing positional message argument instead of `--prompt`; this is the safe canonical form:

```bash
opencode run -m "<model>" --print-logs --log-level INFO "<prompt>"
```

If the installed version only supports a different syntax, adapt based on `opencode run --help`.

### Runtime Observation Rule

- Keep the run command connected until process exit.
- If there is no final result, do not assume failure immediately. Treat as long-running and continue.
- Use a 30-second initial wait before deciding to label as "still processing".
- Poll for progress every 5 seconds.
- If no stdout/stderr heartbeat appears for 45 seconds, emit one visible waiting status.
- If still running after 90 seconds, emit a long-run status and continue.
- If no terminal completion after 180 seconds, stop and classify as a timeout failure unless a caller-specific override allows longer.
- On timeout/failure, retry once with the next priority model unless the failure is command/permission/config related.

Rules:

- Do not use the TUI by default.
- Use `--print-logs` by default for delegated runs so progress is visible.
- Use debug/log flags only when diagnosing a failed run.
- Do not pass `--dangerously-skip-permissions` for default exploration.
- Capture stdout, stderr, exit status, model, final elapsed time, and command shape.
- Always record heartbeat behavior (whether logs were emitted and whether no-output periods occurred).
- If JSON output is available, preserve it for summarization.

## Session Export

After a successful run:

```bash
mkdir -p .planning/explorations
opencode session list --format json --max-count 5
opencode export "<sessionID>" --sanitize > ".planning/explorations/opencode-<timestamp>.json"
```

If `session list` is unavailable:

```bash
opencode session
opencode export "<sessionID>" --sanitize > ".planning/explorations/opencode-<timestamp>.json"
```

If export fails, mark session export as unavailable and continue.

## Failure Handling

If OpenCode is unavailable:

- report the failing command;
- report whether installation was attempted;
- include the error output;
- propose fallback options.

If no acceptable model is available:

- list available models;
- explain why no priority model was selected;
- ask for a model decision or suggest a safe fallback.

If run fails:

- classify the failure before retry:
  - Command or environment failure (missing binary, invalid path, permissions, config mismatch): report directly, do not retry blindly.
  - Model/provider failure (session error, model unavailable, transient provider error): retry once with the next available priority model.
  - No-output timeout with no process error: retry once with the same model if command shape is unchanged; if still failing, retry once with next priority model.
- retry at most once per model, and stop after two total attempts unless user explicitly authorizes a longer run.
- otherwise return the failure report without inventing findings.
