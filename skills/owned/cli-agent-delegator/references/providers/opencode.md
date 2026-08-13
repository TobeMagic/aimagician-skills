# OpenCode Provider

OpenCode is the current CLI worker for discovery, research, visual inspection, bounded operations, short isolated implementation, verification, and independent review. The main Agent supplies the delegation contract and validates material claims.

## Known-Good Fast Path

The managed environment is validated against OpenCode 1.17.x. Its `run` command accepts the prompt as the trailing positional message, not `--prompt`. For routine delegation, do not rediscover the binary, version, model list, or help text before every run.

Prefer the owned runtime because it caches model metadata, requires an explicit controller decision, follows an ordered fallback chain, streams logs, and records every transition. List candidates without requiring a project or prompt:

```bash
node scripts/opencode-run.mjs --list-models --format table
node scripts/opencode-run.mjs --list-models --format json --refresh-models
```

The table is for fast human choice. JSON includes provider-declared capabilities, discovery and worker eligibility, context/output limits, quota-scope policy, policy provenance, and the inventory timestamp. Refresh only after a provider/configuration change, stale cache, model error, or explicit request.

Every execution names the controller-selected primary model. Repeat `--fallback-model` in descending preference order:

```bash
node scripts/opencode-run.mjs \
  --dir "<source_path>" \
  --task-type "<quick|discovery|research|review|audit>" \
  --modality text \
  --model "<best_suitable_free_model>" \
  --fallback-model "<next_suitable_free_model>" \
  --prompt-file "<prompt_file>"
```

For `review` and `audit`, add exactly one:

```bash
--review-ref "<commit_or_ref>"
--review-worktree "<stable_worktree_path>"
```

`--review-ref` resolves the commit and reviews it in a temporary detached worktree. `--review-worktree` hashes HEAD, tracked changes, and untracked contents before and after the run. Any drift blocks the review result.

Use `--dry-run` to inspect the route without starting a worker and `--refresh-models` only after a model/config change, an unavailable-model result, or an explicit request. The runtime reads `opencode models --verbose`; it does not probe version, help, and model commands before every task.

The equivalent direct command for one selected model is:

```bash
opencode run --dir "<source_path>" \
  -m "<controller_selected_model>" \
  --print-logs --log-level INFO \
  "<detailed_prompt>"
```

The owned runtime is preferred for fallbacks. It preserves the same prompt, waits for the failed process to exit, and advances only on an accepted failure class. The controller may select DeepSeek V4 Flash Free when it is the best current fit, but neither DeepSeek nor any other model is a universal default. Do not infer quality from provider order; select from current metadata and known task fit.

The runtime automatically appends Agnes once as the final fallback when it is an active free tool-capable model. Its equivalent final direct attempt is:

```bash
opencode run --dir "<source_path>" \
  -m "agnes/agnes-2.0-flash" \
  --print-logs --log-level INFO \
  "<same_detailed_prompt>"
```

Do not run environment probes between fallback attempts. Confirm that the current process has exited before advancing. Do not switch merely because a progressing run is slow or temporarily quiet.

For visual input, use the owned runtime. It invokes `vision-analysis` through the direct Agnes API, keeps the images out of OpenCode attachments, and passes the sanitized report to the explicitly selected text reasoning route:

```bash
node scripts/opencode-run.mjs \
  --dir "<source_path>" \
  --task-type "<discovery|research|review|audit>" \
  --modality vision \
  --model "<controller_selected_reasoning_model>" \
  --file "<image_path_or_https_url>" \
  --prompt-file "<prompt_file>" \
  --allow-external-upload
```

The prompt contract must list `vision-analysis` in `REQUIRED_SKILLS`. If the direct visual backend is unavailable, return `NEEDS_CONTEXT` or `BLOCKED`; do not infer OpenCode attachment support from a model name and do not silently select an unverified visual backend.

For any task, phase, milestone, release, or delivery completion audit that requires independence, use a fresh controller-selected reasoning route and the owned frozen-review runner. Visual deliverables first add a sanitized `vision-analysis` evidence report:

```bash
node scripts/opencode-run.mjs \
  --dir "<source_path>" \
  --task-type audit \
  --modality text \
  --model "<controller_selected_audit_model>" \
  --fallback-model "<next_best_audit_model>" \
  --prompt-file "<completion_audit_prompt_file>" \
  --review-ref "<exact_commit>"
```

The audit must still use a fresh independent session, frozen review point, original-request traceability, requirement matrix, finding severities, and controller spot-check. Model neutrality does not permit implementer self-approval or controller self-review. For visual deliverables, collect observable evidence with a vision-capable worker and include it in the final independent audit.

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

Agnes may be configured as an OpenCode text provider with model `agnes/agnes-2.0-flash`. Direct visual acquisition reads `AGNES_API_KEY` through `vision-analysis`. Never place, print, export, or commit the key.

## Model Routing

Use this route:

1. List active free text models from the owned cache; refresh after relevant configuration changes, stale metadata, model errors, or explicit request.
2. The controller selects the best suitable worker from task difficulty, context size, reasoning/tool needs, known current quality, and provider availability. Record the rationale; never let the runtime silently choose the primary.
3. The controller declares zero or more fallback models in descending preference. Models must be unique, active, free, text-capable, and tool-capable.
4. The runtime appends `agnes/agnes-2.0-flash` exactly once as the final fallback when available. Agnes remains the unlimited safety fallback, not a mandatory primary or second choice.
5. A usage/quota/rate-limit event invalidates the model's declared quota scope. Under policy `user-policy-v1`, all `opencode/*` Zen models share `shared:opencode`; every other provider uses `model:<full-id>`; Agnes uses `unlimited:agnes`. These scopes are user-asserted policy metadata, not provider-discovered facts.
6. A model-unavailable event invalidates only that model. Authentication invalidates the normalized provider. Network errors retry the same model three times, then stop. Permission, command-syntax, generic worker, worker-quality, and controller-cancellation failures stop without fallback.
7. If Agnes reports a rate limit, keep retrying with progress events until success or cancellation. Never switch models merely because an active run is slow or temporarily quiet.
8. `vision-analysis` acquires pixels through its authorized Agnes API backend and returns sanitized text evidence. The controller then chooses the text reasoning model using the same policy.
9. If no suitable free model or verified visual backend is usable, return `NEEDS_CONTEXT` or `BLOCKED`; never silently select a paid or unknown model.

A provider rate limit is a model event, not an inactivity timeout. Apply only the invalidation scope recorded in the result and continue through the declared order. Do not misclassify a progressing long run as rate-limited.

For visual work, never attach the image to OpenCode for Agnes. The runtime calls `vision-analysis`, then labels the returned report as controller-provided visual evidence before starting text reasoning. If the image cannot be loaded or upload is not explicitly authorized, return `NEEDS_CONTEXT`; do not guess from filenames.

`opencode models --verbose` supplies live status, cost, context, and declared capabilities for reasoning-model discovery. The runtime does not override Agnes image metadata because OpenCode attachment support and direct Agnes API multimodality are different capabilities.

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
- capture command shape, stdout/stderr, exit status, primary model, final model, attempt chain, fallback reason, session, and final run health;
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
4. Stop on process exit, clear CLI error, provider rejection, permission/config failure, user cancellation, or confirmed stale state. On controller cancellation, the owned runtime terminates the active worker and the entire model chain reports `CANCELLED`; it must not start any fallback. A terminal quota event may stop the failed process immediately; fallback still waits for process exit. An Agnes rate limit produces retry events instead of a false completion.
5. Never start the fallback model while the original process is still alive.
6. After an accepted transition event, preserve the error and start the next non-invalidated declared model using the exact same prompt and task contract; do not repeat preflight probes. Continue indefinitely only for Agnes rate-limit events.
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
- **Usage/quota/rate-limit:** preserve evidence, invalidate only the recorded quota scope, and start the next non-invalidated declared model after the process exits.
- **Agnes rate-limit:** emit progress and keep retrying until success or cancellation.
- **Model unavailable:** invalidate that model and continue through the declared chain; refresh inventory before the next separate dispatch.
- **Authentication:** invalidate the normalized provider and continue through the declared chain.
- **Network:** retry the same model three times, then stop and preserve the classification.
- **Permission, command syntax, generic provider, or worker quality:** stop; do not convert the failure into a model fallback.
- **Controller cancellation:** terminate the active child, report `CANCELLED`, and do not advance to another model.
- **Task contract:** missing skill, source, decision, scope, or write path. Return `NEEDS_CONTEXT`.
- **Confirmed stale:** process/session no longer advances without a terminal result. Report last activity and health evidence; retry only after the original process has ended or been explicitly stopped.
- **Worker result quality:** incomplete or unsupported report. Use one narrower follow-up prompt; do not rerun the same vague request.
