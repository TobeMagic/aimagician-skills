# Runtime And Source Neutrality

A general Skill must describe capabilities and contracts, not the environment of its source repository.

## Blockers

- Claims that the Skill only works in one agent runtime without an intentional runtime-specific scope.
- Hard-coded home-directory installation paths as the only workflow.
- Plugin, hook, auto-update, or bootstrap instructions unrelated to the user outcome.
- Creator names, communities, social links, badges, result-card branding, or promotional language.
- Commands that silently branch, commit, revert, install, publish, or mutate user configuration.
- References to unavailable source-repository files.
- Tool names without a capability fallback when equivalent runtimes are expected.

## Allowed Runtime Detail

Runtime-specific commands are allowed when:

1. the requested operation actually depends on that runtime;
2. the section is clearly scoped;
3. a capability-level fallback is provided where possible;
4. the trigger does not misroute other runtimes.

## Scan

Search all shipped runtime files, excluding ignored source mirrors:

```bash
rg -n -i 'npx skills add|auto.?update|creator|follow me|github\.com/.+/(nuwa|darwin|cangjie)|~/.claude/skills|git (checkout -b|commit|revert)' <skill-dir>
```

Review matches in context. Some terms such as `creator` may be legitimate sibling Skill names; the gate is whether the text adds source identity or hidden environment mutation.

## Release Gate

Every shipped path must resolve inside the owned Skill. External mirrors can support audit work but must remain ignored, uninstalled, and absent from package output.
