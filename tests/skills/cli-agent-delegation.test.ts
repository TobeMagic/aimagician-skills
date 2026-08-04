import { access, readFile } from "node:fs/promises";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const ownedRoot = join(process.cwd(), "skills", "owned");
const delegatorRoot = join(ownedRoot, "cli-agent-delegator");
const superpowerRoot = join(ownedRoot, "aimagician-superpower");

describe("cli-agent-delegator capability contract", () => {
  it("renames the owned skill without leaving an alias or tombstone", async () => {
    await expect(access(join(delegatorRoot, "SKILL.md"))).resolves.toBeUndefined();
    await expect(access(join(ownedRoot, "cli-agent-orchestrator", "SKILL.md"))).rejects.toThrow();

    const skill = await readFile(join(delegatorRoot, "SKILL.md"), "utf8");
    expect(skill).toMatch(/^---\nname: cli-agent-delegator\n/);
    expect(skill).toContain("category: operate");
    expect(skill).toContain("subcategory: agent-orchestration");
  });

  it("puts broad exploration, checks, research, vision, and reviews on the trigger surface", async () => {
    const skill = await readFile(join(delegatorRoot, "SKILL.md"), "utf8");
    const description = frontmatterDescription(skill);

    expect(description).toMatch(/^Use for broad or multi-source exploration/);
    for (const trigger of [
      "broad or multi-source exploration",
      "deep web research",
      "image inspection",
      "bounded git/test/report/write work",
      "whenever a locked simple short execution task can be offloaded",
      "independent plan/code/spec/verification review"
    ]) {
      expect(description).toContain(trigger);
    }

    expect(description).toContain("completion audit only for high-risk, planning-managed, deployable, policy-required, or explicitly requested work");
    expect(skill).toContain("read-only one- or two-file lookup: no forced delegation");
    expect(skill).toContain("Before the main Agent starts a broad scan or mechanical verification");
    expect(skill).toContain("This gate applies even when the user says only");
    expect(skill).toContain("Default Short-Task Gate");
    expect(skill).toContain("Delegate a simple short task by default when all of these are true");
    expect(skill).toContain("Worker-Side Loading Gate");
    expect(skill).toContain("Do not rely on worker self-selection from task wording");
    expect(skill).toContain("the controller must put `cli-agent-delegator` and every domain skill in `REQUIRED_SKILLS`");
    expect(skill).toContain("Mentioning a skill in prose does not satisfy this gate");
  });

  it("requires complete context, owned skill loading, bounded permissions, and inherited child scope", async () => {
    const prompt = await readFile(join(delegatorRoot, "references", "prompt-contract.md"), "utf8");

    for (const field of [
      "TASK_TYPE",
      "MODALITY",
      "SOURCE_OF_TRUTH",
      "ORIGINAL_REQUESTS",
      "ACCEPTED_DECISIONS",
      "KNOWN_CONTEXT",
      "REQUIRED_SKILLS",
      "ALLOWED_SCOPE",
      "FORBIDDEN_SCOPE",
      "PERMISSION_MODE",
      "WRITE_SCOPE",
      "GIT_POLICY",
      "MODEL_POLICY",
      "CHILD_AGENT_POLICY",
      "STOP_AND_ESCALATE_WHEN"
    ]) {
      expect(prompt).toContain(field);
    }

    expect(prompt).toContain("load every skill named in REQUIRED_SKILLS");
    expect(prompt).toContain("return NEEDS_CONTEXT");
    expect(prompt).toContain("Child-Agent Inheritance");
    expect(prompt).toContain("full-repository diffs");
  });

  it("routes vision through direct evidence and requires controller-selected model chains", async () => {
    const provider = await readFile(join(delegatorRoot, "references", "providers", "opencode.md"), "utf8");
    const runner = await readFile(join(delegatorRoot, "scripts", "opencode-run.mjs"), "utf8");

    expect(provider).toContain("Known-Good Fast Path");
    expect(provider).toContain("`vision-analysis` acquires pixels through its authorized Agnes API backend");
    expect(provider).toContain("controller selects the best suitable worker");
    expect(provider).toContain("The controller declares zero or more fallback models");
    expect(provider).toContain("shared:opencode");
    expect(provider).toContain("user-policy-v1");
    expect(provider).toContain("Network errors retry the same model three times");
    expect(provider).toContain('-m "<controller_selected_model>"');
    expect(provider).toContain('-m "agnes/agnes-2.0-flash"');
    expect(provider).toContain('"<same_detailed_prompt>"');
    expect(provider).toContain('--prompt-file "<completion_audit_prompt_file>"');
    expect(provider).toContain('--review-ref "<exact_commit>"');
    expect(provider).toContain("--allow-external-upload");
    expect(provider).toContain("never attach the image to OpenCode for Agnes");
    expect(provider).not.toContain('-f "<image_path>"');
    expect(provider).not.toMatch(/opencode run[^\n]*--prompt/);
    expect(provider).toContain("prompt as the trailing positional message");
    expect(runner).toContain('execFileAsync("opencode", ["models", "--verbose"]');
    expect(runner).toContain("buildModelChain");
    expect(runner).toContain("quota-scope-invalidated");
    expect(runner).toContain("provider-invalidated");
    expect(runner).toContain("buildVisualReasoningPrompt");
    expect(runner).toContain("analyzeImages");
    expect(runner).toContain('"selection-required"');
    expect(runner).not.toContain("VERIFIED_CAPABILITY_OVERRIDES");
  });

  it("uses direct commands by default and limits environment probes to diagnostics", async () => {
    const provider = await readFile(join(delegatorRoot, "references", "providers", "opencode.md"), "utf8");
    const skill = await readFile(join(delegatorRoot, "SKILL.md"), "utf8");

    expect(provider).toContain("do not rediscover the binary, version, model list, or help text before every run");
    expect(provider).toContain("Do not run environment probes between fallback attempts");
    expect(provider).toContain("Diagnostic Preflight");
    expect(provider).toContain("Do not execute this whole bundle as routine ceremony");
    expect(provider).toContain("Run diagnostics only for first-time setup in a new environment");
    expect(skill).toContain("Use the known-good fast path");
    expect(skill).toContain("Do not repeat binary, version, model-list, or help probes");
    expect(skill).toContain("Every run supplies `--model`");
    expect(skill).toContain("The runtime appends Agnes once as the final fallback when available");
  });

  it("waits on activity events instead of elapsed-time limits", async () => {
    const provider = await readFile(join(delegatorRoot, "references", "providers", "opencode.md"), "utf8");

    expect(provider).toContain("Event-Based Waiting");
    expect(provider).toContain("never a fixed five-second poll count or fixed maximum elapsed duration");
    expect(provider).toContain("While the process is alive and events continue, keep waiting");
    expect(provider).toContain("Never start the fallback model while the original process is still alive");
    expect(provider).toContain("an interval is only an observation cadence, not a deadline");
  });

  it("supports bounded writes but keeps commits, pushes, and dirty worktrees gated", async () => {
    const operations = await readFile(join(delegatorRoot, "references", "task-types", "bounded-operations-and-execution.md"), "utf8");

    expect(operations).toContain("clean isolated worktree");
    expect(operations).toContain("exact write scope");
    expect(operations).toContain("Default is `no-commit`");
    expect(operations).toContain("Push is never implied by commit permission");
    expect(operations).toContain("before/after git status");
  });

  it("enforces risk-scaled OpenCode review gates and one severity taxonomy", async () => {
    const review = await readFile(join(delegatorRoot, "references", "task-types", "independent-review-and-audit.md"), "utf8");
    const orchestration = await readFile(join(superpowerRoot, "references", "capabilities", "agent-orchestration.md"), "utf8");
    const qualityReviewer = await readFile(join(superpowerRoot, "references", "roles", "quality-reviewer.md"), "utf8");

    expect(review).toContain("One- or two-file read-only lookup");
    expect(review).toContain("Decisive controller verification");
    expect(review).toContain("Plan review before execution; specification review; quality review; verifier");
    expect(review).toContain("Fresh whole-result auditor");
    expect(review).toContain("original-request traceability");
    expect(review).toContain("Use exactly");
    expect(orchestration).toContain("cli-agent-delegator");
    expect(orchestration).toContain("phase audit, and milestone or completion audit");
    expect(qualityReviewer).toContain("`Blocker`, `Important`, and `Nitpick`");
    expect(qualityReviewer).not.toContain("Critical, Important, and Minor");
  });

  it("captures the trigger regression where the main agent scans skill, docs, and tests itself", async () => {
    const evals = JSON.parse(await readFile(join(delegatorRoot, "evals", "evals.json"), "utf8")) as {
      scenarios: Array<{ id: string; should_trigger: boolean; expected: string[]; forbidden: string[] }>;
    };
    const scenario = evals.scenarios.find((candidate) => candidate.id === "trigger-regression-main-agent-multifile-scan");
    const researchScenario = evals.scenarios.find((candidate) => candidate.id === "deep-web-research");

    expect(scenario).toBeDefined();
    expect(scenario).toMatchObject({ should_trigger: true });
    expect(scenario?.expected).toContain("delegate the multi-file audit first");
    expect(scenario?.forbidden).toContain("main agent performs the whole multi-file scan itself");
    expect(researchScenario?.expected).toContain("explicit controller-selected model");
    expect(researchScenario?.expected).toContain("ordered fallback chain");
    expect(researchScenario?.forbidden).toContain("repeat version, model-list, or help probes before routine execution");
  });
});

function frontmatterDescription(skill: string): string {
  const match = skill.match(/^---\n[\s\S]*?^description: (.+)$/m);
  if (!match) throw new Error("Skill description is missing");
  return match[1];
}
