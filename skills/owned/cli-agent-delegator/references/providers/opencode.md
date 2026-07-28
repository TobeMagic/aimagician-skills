# OpenCode Provider

OpenCode is the current CLI worker for discovery, research, visual inspection, bounded operations, short isolated implementation, verification, and independent review. The main Agent supplies the delegation contract and validates material claims.

## Known-Good Fast Path

The managed environment is validated against OpenCode 1.17.x. Its `run` command accepts the prompt as the trailing positional message, not `--prompt`. For routine delegation, do not rediscover the binary, version, model list, or help text before every run.

Use this primary command directly for ordinary non-visual work:

```bash
opencode run --dir "<source_path>" \
  -m "opencode/deepseek-v4-flash-free" \
  --print-logs --log-level INFO \
  "<detailed_prompt>"
```

If that run ends with an explicit rate limit, provider rejection, unavailable-model error, or other model failure, preserve the error and rerun the exact same prompt once with Agnes:

```bash
opencode run --dir "<source_path>" \
  -m "agnes/agnes-2.0-flash" \
  --print-logs --log-level INFO \
  "<same_detailed_prompt>"
```

Do not run environment probes between the primary and fallback commands. Confirm that the DeepSeek process has exited before starting Agnes. Do not switch models merely because a progressing run is slow or temporarily quiet.

For visual input, use Agnes as the first command:

```bash
opencode run --dir "<source_path>" \
  -m "agnes/agnes-2.0-flash" \
  -f "<image_path>" \
  --print-logs --log-level INFO \
  "<detailed_prompt>"
```

For every task, phase, milestone, release, or delivery completion audit, use Agnes as the first and required model:

```bash
opencode run --dir "<source_path>" \
  -m "agnes/agnes-2.0-flash" \
  --print-logs --log-level INFO \
  "<completion_audit_prompt>"
```

Do not try DeepSeek first for a completion audit. If Agnes fails, report the audit as unavailable and do not claim completion; do not substitute an implementer or controller self-review.

## Diagnostic Preflight

Run diagnostics only for first-time setup in a new environment, a known runtime or configuration change, a missing-command or invalid-syntax failure, a model/provider configuration failure, or an explicit user request. Use the narrowest command that diagnoses the observed failure:

```bash
command -v opencode
opencode --version
opencode models
opencode run --help
```

Do not execute this whole bundle as routine ceremony.

When a repository or local source is in scope:

```bash
test -d "<source_path>"
git -C "<source_path>" status --short --branch
```

Confirm that every required owned skill is installed for OpenCode. The worker must load those skills before substantive work and return `NEEDS_CONTEXT` if one is unavailable.

If OpenCode is missing, install only after installation is within the accepted scope. Prefer a user-level package manager or the official installer:

```bash
npm install -g opencode-ai
```

or:

```bash
curl -fsSL https://opencode.ai/install | bash
```

Then run the narrow diagnostics required to verify the repaired failure. If the binary exists but is not executable, use `chmod +x "<opencode_binary_path>"` only on that user-owned binary. If it is outside `PATH`, add its user-level bin directory to the shell path. Never use `sudo` without explicit authorization. Record any installation or config change.

## Configuration

User config normally lives at:

```text
~/.config/opencode/opencode.json
```

Inspect existing configuration before changing it. Merge only the exact missing provider or permission key; never replace unrelated models, plugins, MCP servers, instructions, or project settings. A globally permissive OpenCode config does not expand the delegated task: prompt scope, isolated worktree, and the permission mode remain authoritative.

When the user explicitly authorizes fully autonomous non-interactive OpenCode permissions, merge this minimal policy instead of replacing the config:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "permission": {
    "*": "allow"
  }
}
```

Do not add unrelated MCP servers, external directories, or framework-specific paths as part of this merge.

Agnes may be configured as a provider with model `agnes/agnes-2.0-flash`. Read its API key from the user's environment or existing provider config. Never place, print, export, or commit the key.

## Model Routing

Use this route:

1. `opencode/deepseek-v4-flash-free` for ordinary non-visual discovery, web research, tests, git inspection, bounded implementation, and review.
2. `agnes/agnes-2.0-flash` when the task requires image understanding.
3. `agnes/agnes-2.0-flash` when DeepSeek is unavailable, rate-limited, rejects the request, or otherwise fails.
4. If neither model is usable, report the available model list and request a decision instead of silently choosing a paid or unknown model.
5. `agnes/agnes-2.0-flash` is mandatory and primary for completion audits, independent of the ordinary-task route above.

A provider rate limit is a model failure event, not an inactivity timeout. Do not wait forever on a clear rate-limit error, and do not misclassify a progressing long run as rate-limited.

For visual work, Agnes is primary rather than fallback. Attach the exact image using the syntax supported by `opencode run --help` (commonly `-f <path>`). If the image cannot be loaded, return `NEEDS_CONTEXT`; do not fall back to a non-visual model and guess.

## Execution Syntax

OpenCode 1.17.x accepts the prompt as the trailing positional message. Do not use the obsolete `--prompt` form. Inspect installed help only when a command-syntax failure or runtime change makes the known-good contract invalid.

Canonical non-interactive command:

```bash
opencode run --dir "<source_path>" -m "<model>" --print-logs --log-level INFO "<detailed_prompt>"
```

Use structured output only when the installed version supports the required format reliably:

```bash
opencode run --dir "<source_path>" -m "<model>" --format json --print-logs --log-level INFO "<detailed_prompt>"
```

Rules:

- use non-interactive mode, not the TUI;
- pass the complete prompt contract from `../prompt-contract.md`;
- do not use auto-approval flags as a substitute for bounded permissions;
- capture command shape, stdout/stderr, exit status, model, and final run health;
- keep the process attached until natural completion or a valid stop condition.

## Event-Based Waiting

OpenCode may be quiet between tool calls or before its final synthesis. Waiting is based on activity and process state, never a fixed five-second poll count or fixed maximum elapsed duration.

Activity events include:

- new stdout/stderr or provider logs;
- streamed model output;
- tool-call start or completion;
- file, URL, command, or test references;
- stage transitions and progress markers;
- session, message, provider-request, or tracking updates.

Rules:

1. While the process is alive and events continue, keep waiting until it exits naturally.
2. A quiet interval is not failure. Poll process and session health and remain attached.
3. Confirm stale state only when neither process/provider health nor session/event state is advancing. Record the last event and the evidence used to classify it.
4. Stop on process exit, clear CLI error, provider rejection or rate limit, permission/config failure, user cancellation, or confirmed stale state.
5. Never start the fallback model while the original process is still alive.
6. After a provider/model failure, preserve the error and retry once with the routed fallback using the exact same prompt and task contract; do not repeat preflight probes.
7. Do not fabricate a final result when a run fails or is stopped.

The controller may poll at any convenient interval, but an interval is only an observation cadence, not a deadline.

## Writes And Worktrees

For `bounded-write`, the main Agent creates the isolated worktree before invoking OpenCode. Put the exact worktree in `--dir`, list exact write paths in the prompt, and forbid writes outside them. Capture git status before and after. OpenCode may create a local commit only when the prompt explicitly allows it after independent review. Push is separately authorized.

For `read-and-run`, tests may create caches or artifacts. Report those paths and leave cleanup to the controller unless exact cleanup permission was supplied.

## Session Export

Session export writes a file and is disabled by default. Use it only when the prompt gives an exact allowed destination:

```bash
opencode session list --format json --max-count 5
opencode export "<sessionID>" --sanitize > "<allowed_output_path>"
```

If the installed version uses `opencode session` instead of `session list`, adapt from help output. If export fails, mark it unavailable and continue; never expose secrets in an export.

## Failure Classification

- **Command/environment:** missing binary, invalid path or syntax, executable problem. Correct only within scope; otherwise return `NEEDS_CONTEXT` or `BLOCKED`.
- **Permission/config:** required access or safe merge unavailable. Stop; do not broaden permission silently.
- **Model/provider:** unavailable model, rate limit, provider error, rejected request. Preserve evidence and follow the model route.
- **Task contract:** missing skill, source, decision, scope, or write path. Return `NEEDS_CONTEXT`.
- **Confirmed stale:** process/session no longer advances without a terminal result. Report last activity and health evidence; retry only after the original process has ended or been explicitly stopped.
- **Worker result quality:** incomplete or unsupported report. Use one narrower follow-up prompt; do not rerun the same vague request.
