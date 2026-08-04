import { execFile, spawn } from "node:child_process";
import { access, mkdtemp, mkdir, readFile, realpath, rm, symlink, unlink, writeFile } from "node:fs/promises";
import { constants } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { promisify } from "node:util";
import { afterEach, describe, expect, it } from "vitest";

const tempDirectories: string[] = [];
const execFileAsync = promisify(execFile);
const skillRoot = join(process.cwd(), "skills", "owned", "aimagician-superpower");
const workflowScript = join(skillRoot, "scripts", "workflow.mjs");
const waitScript = join(skillRoot, "scripts", "wait-for.mjs");
const polluterScript = join(skillRoot, "scripts", "find-polluter.mjs");

afterEach(async () => {
  await Promise.allSettled(tempDirectories.splice(0).map((directory) => rm(directory, { recursive: true, force: true })));
});

describe("aimagician-superpower workflow runtime", () => {
  it("previews initialization, writes only on request, and never overwrites existing artifacts", async () => {
    const project = await makeProject();
    const preview = await runNode(workflowScript, ["init", "--project", project, "--phase", "01-runtime", "--format", "json"]);
    expect(preview.exitCode).toBe(0);
    const previewResult = JSON.parse(preview.stdout) as { mode: string; planned: string[] };
    expect(previewResult.mode).toBe("preview");
    expect(previewResult.planned).toContain(".planning/PROJECT.md");
    expect(previewResult.planned).toContain(".planning/CONTEXT.md");
    expect(previewResult.planned).toContain(".planning/phases/01-runtime/01-SPEC.md");
    expect(previewResult.planned).toContain(".planning/REQUESTS.md");
    await expect(access(join(project, ".planning"), constants.F_OK)).rejects.toMatchObject({ code: "ENOENT" });

    const apply = await runNode(workflowScript, [
      "init", "--project", project, "--phase", "01-runtime", "--risk", "high",
      "--extensions", "ui,ai,security-ops", "--write", "--format", "json"
    ]);
    expect(apply.exitCode).toBe(0);
    await access(join(project, ".planning", "phases", "01-runtime", "01-UI-SPEC.md"), constants.F_OK);
    await access(join(project, ".planning", "phases", "01-runtime", "01-AI-SPEC.md"), constants.F_OK);
    await access(join(project, ".planning", "phases", "01-runtime", "01-SECURITY-OPS-SPEC.md"), constants.F_OK);

    const requirementsPath = join(project, ".planning", "REQUIREMENTS.md");
    await writeFile(requirementsPath, "# User-owned requirements\n", "utf8");
    const rerun = await runNode(workflowScript, ["init", "--project", project, "--phase", "01-runtime", "--write", "--format", "json"]);
    expect(rerun.exitCode).toBe(0);
    expect(await readFile(requirementsPath, "utf8")).toBe("# User-owned requirements\n");
    expect((JSON.parse(rerun.stdout) as { skipped: string[] }).skipped).toContain(".planning/REQUIREMENTS.md");
  });

  it("creates one lightweight task record, blocks missing audit evidence, and accepts legacy Agnes records", async () => {
    const project = await makeProject();
    const apply = await runNode(workflowScript, [
      "init", "--project", project, "--task", "quick-fix", "--write", "--format", "json"
    ]);
    expect(apply.exitCode).toBe(0);
    expect(JSON.parse(apply.stdout)).toMatchObject({
      task: "quick-fix",
      planned: expect.arrayContaining([".planning/tasks/quick-fix.md"])
    });

    const incomplete = await runNode(workflowScript, [
      "validate", "--project", project, "--task", "quick-fix", "--gate", "complete", "--format", "json"
    ]);
    expect(incomplete.exitCode).toBe(1);
    expect((JSON.parse(incomplete.stdout) as { findings: Array<{ code: string }> }).findings.map((item) => item.code)).toEqual(
      expect.arrayContaining(["TASK_PLACEHOLDER", "TASK_CHECKLIST_OPEN", "AUDIT_SESSION_MISSING"])
    );

    await writeFile(join(project, ".planning", "REQUESTS.md"), validRequests(), "utf8");
    await writeFile(join(project, ".planning", "tasks", "quick-fix.md"), validTask(), "utf8");
    const complete = await runNode(workflowScript, [
      "validate", "--project", project, "--task", "quick-fix", "--gate", "complete", "--format", "json"
    ]);
    expect(complete.exitCode).toBe(0);
    expect(JSON.parse(complete.stdout)).toMatchObject({
      ok: true,
      task: "quick-fix",
      status: "passed"
    });
  });

  it("shares local-private planning across worktrees and rejects stale or concurrent writers", async () => {
    const project = await makeGitProject();
    const initialized = await runNode(workflowScript, [
      "planning", "--project", project, "--action", "init", "--mode", "local-private", "--write", "--format", "json"
    ]);
    expect(initialized.exitCode).toBe(0);
    expect(JSON.parse(initialized.stdout)).toMatchObject({
      ok: true,
      mode: "local-private",
      attached: true,
      revision: 0
    });

    const worktreeParent = await makeProject();
    const worktree = join(worktreeParent, "secondary");
    await execFileAsync("git", ["worktree", "add", "-b", "test/local-private-secondary", worktree, "HEAD"], { cwd: project });
    const detached = await runNode(workflowScript, [
      "planning", "--project", worktree, "--action", "status", "--format", "json"
    ]);
    expect(detached.exitCode).toBe(1);
    expect(JSON.parse(detached.stdout)).toMatchObject({
      mode: "local-private",
      attached: false,
      findings: [expect.objectContaining({ code: "PLANNING_NOT_ATTACHED" })]
    });

    const attached = await runNode(workflowScript, [
      "planning", "--project", worktree, "--action", "attach", "--write", "--format", "json"
    ]);
    expect(attached.exitCode).toBe(0);
    expect(await realpath(join(worktree, ".planning"))).toBe(await realpath(join(project, ".planning")));
    expect(await readFile(join(project, ".git", "info", "exclude"), "utf8")).toContain("/.planning");

    const locked = await runNode(workflowScript, [
      "planning", "--project", project, "--action", "lock", "--owner", "primary",
      "--expected-revision", "0", "--format", "json"
    ]);
    expect(locked.exitCode).toBe(0);
    const lease = (JSON.parse(locked.stdout) as { lease: string }).lease;

    const concurrent = await runNode(workflowScript, [
      "planning", "--project", worktree, "--action", "lock", "--owner", "secondary",
      "--expected-revision", "0", "--format", "json"
    ]);
    expect(concurrent.exitCode).toBe(2);
    expect(JSON.parse(concurrent.stdout)).toMatchObject({
      findings: [expect.objectContaining({ code: "PLANNING_LOCK_HELD" })]
    });

    const unlocked = await runNode(workflowScript, [
      "planning", "--project", project, "--action", "unlock", "--lease", lease,
      "--outcome", "updated", "--format", "json"
    ]);
    expect(unlocked.exitCode).toBe(0);
    expect(JSON.parse(unlocked.stdout)).toMatchObject({ revision: 1 });

    const stale = await runNode(workflowScript, [
      "planning", "--project", worktree, "--action", "lock", "--owner", "secondary",
      "--expected-revision", "0", "--format", "json"
    ]);
    expect(stale.exitCode).toBe(2);
    expect(JSON.parse(stale.stdout)).toMatchObject({
      findings: [expect.objectContaining({ code: "PLANNING_REVISION_CONFLICT" })]
    });
  });

  it("separates premerge readiness from deployable postmerge completion", async () => {
    const project = await makeProject();
    await mkdir(join(project, ".planning", "tasks"), { recursive: true });
    await writeFile(join(project, ".planning", "REQUESTS.md"), validRequests(), "utf8");
    const taskPath = join(project, ".planning", "tasks", "delivery-check.md");
    await writeFile(taskPath, validDeliveryTask(), "utf8");

    const premerge = await runNode(workflowScript, [
      "validate", "--project", project, "--task", "delivery-check", "--gate", "premerge", "--format", "json"
    ]);
    expect(premerge.exitCode).toBe(0);
    expect(JSON.parse(premerge.stdout)).toMatchObject({ ok: true, gate: "premerge" });

    const postmergeBlocked = await runNode(workflowScript, [
      "validate", "--project", project, "--task", "delivery-check", "--gate", "postmerge", "--format", "json"
    ]);
    expect(postmergeBlocked.exitCode).toBe(1);
    expect((JSON.parse(postmergeBlocked.stdout) as { findings: Array<{ code: string }> }).findings.map((item) => item.code))
      .toEqual(expect.arrayContaining([
        "DELIVERY_MERGE_SHA_INVALID",
        "DELIVERY_POSTMERGE_NOT_PASSED",
        "DELIVERY_ARTIFACT_MISMATCH",
        "DELIVERY_ONLINE_NOT_CONFIRMED"
      ]));

    await writeFile(taskPath, validDeliveryTask({
      mergeSha: "1234567abcdef",
      postmerge: "PASS",
      artifactMatch: "MATCH",
      decision: "ONLINE_CONFIRMED"
    }), "utf8");
    const postmerge = await runNode(workflowScript, [
      "validate", "--project", project, "--task", "delivery-check", "--gate", "postmerge", "--format", "json"
    ]);
    expect(postmerge.exitCode).toBe(0);
    expect(JSON.parse(postmerge.stdout)).toMatchObject({ ok: true, gate: "postmerge" });
  });

  it("accepts model-neutral audits and rejects unsupported Agnes fallback claims", async () => {
    const project = await makeProject();
    await mkdir(join(project, ".planning", "tasks"), { recursive: true });
    await writeFile(join(project, ".planning", "REQUESTS.md"), validRequests(), "utf8");
    await writeFile(join(project, ".planning", "tasks", "quick-fix.md"), validNeutralTask(), "utf8");

    const complete = await runNode(workflowScript, [
      "validate", "--project", project, "--task", "quick-fix", "--gate", "complete", "--format", "json"
    ]);
    expect(complete.exitCode).toBe(0);

    await writeFile(
      join(project, ".planning", "tasks", "quick-fix.md"),
      validNeutralTask()
        .replaceAll("opencode/deepseek-v4-flash-free", "agnes/agnes-2.0-flash")
        .replace("Fallback reason:** NONE", "Fallback reason:** generic provider failure"),
      "utf8"
    );
    const invalidFallback = await runNode(workflowScript, [
      "validate", "--project", project, "--task", "quick-fix", "--gate", "complete", "--format", "json"
    ]);
    expect(invalidFallback.exitCode).toBe(1);
    expect((JSON.parse(invalidFallback.stdout) as { findings: Array<{ code: string }> }).findings)
      .toContainEqual(expect.objectContaining({ code: "AUDIT_AGNES_FALLBACK_INVALID" }));
  });

  it("requires model rationale and chain provenance for v2 audit records while preserving legacy records", async () => {
    const project = await makeProject();
    await mkdir(join(project, ".planning", "tasks"), { recursive: true });
    await writeFile(join(project, ".planning", "REQUESTS.md"), validRequests(), "utf8");
    const taskPath = join(project, ".planning", "tasks", "quick-fix.md");
    await writeFile(taskPath, validNeutralTask().replace(
      "- **Provider:** OpenCode",
      "- **Result schema:** v2\n- **Provider:** OpenCode"
    ), "utf8");
    const incomplete = await runNode(workflowScript, [
      "validate", "--project", project, "--task", "quick-fix", "--gate", "complete", "--format", "json"
    ]);
    expect(incomplete.exitCode).toBe(1);
    expect((JSON.parse(incomplete.stdout) as { findings: Array<{ code: string }> }).findings.map((item) => item.code))
      .toEqual(expect.arrayContaining([
        "AUDIT_MODEL_RATIONALE_MISSING",
        "AUDIT_DECLARED_CHAIN_MISSING",
        "AUDIT_EFFECTIVE_CHAIN_MISSING",
        "AUDIT_TRANSITIONS_MISSING"
      ]));

    await writeFile(taskPath, validNeutralTask().replace(
      "- **Provider:** OpenCode",
      `- **Result schema:** v2
- **Provider:** OpenCode
- **Model selection rationale:** Best active free model for a bounded audit.
- **Declared model chain:** \`opencode/deepseek-v4-flash-free\`
- **Effective model chain:** \`opencode/deepseek-v4-flash-free -> agnes/agnes-2.0-flash\`
- **Model transitions:** NONE`
    ), "utf8");
    const complete = await runNode(workflowScript, [
      "validate", "--project", project, "--task", "quick-fix", "--gate", "complete", "--format", "json"
    ]);
    expect(complete.exitCode).toBe(0);
  });

  it("blocks planning-managed alignment when canonical project context is missing or unresolved", async () => {
    const fixture = await makeInitializedPhase();
    await writeFile(fixture.specPath, validSpec(), "utf8");
    await unlink(join(fixture.project, ".planning", "CONTEXT.md"));
    const missing = await runNode(workflowScript, [
      "validate", "--project", fixture.project, "--phase", "01", "--gate", "align", "--format", "json"
    ]);
    expect(missing.exitCode).toBe(1);
    expect((JSON.parse(missing.stdout) as { findings: Array<{ code: string }> }).findings)
      .toContainEqual(expect.objectContaining({ code: "CONTEXT_MIGRATION_REQUIRED" }));

    await writeValidPlanningContext(fixture.project);
    await writeFile(join(fixture.project, ".planning", "PROJECT.md"), "# Project\n\n## Purpose\n\nTBD\n", "utf8");
    const unresolved = await runNode(workflowScript, [
      "validate", "--project", fixture.project, "--phase", "01", "--gate", "align", "--format", "json"
    ]);
    expect(unresolved.exitCode).toBe(1);
    expect((JSON.parse(unresolved.stdout) as { findings: Array<{ code: string }> }).findings.map((item) => item.code))
      .toEqual(expect.arrayContaining(["ALIGN_PROJECT_SECTION_MISSING", "ALIGN_PROJECT_PLACEHOLDER"]));
  });

  it("enforces specification scoring and reports stable finding codes", async () => {
    const fixture = await makeInitializedPhase();
    await writeFile(fixture.specPath, validSpec().replace("**Ambiguity:** 0.12", "**Ambiguity:** 0.40"), "utf8");
    const result = await runNode(workflowScript, [
      "validate", "--project", fixture.project, "--phase", "01", "--gate", "spec", "--format", "json"
    ]);
    expect(result.exitCode).toBe(1);
    const parsed = JSON.parse(result.stdout) as { ok: boolean; findings: Array<{ code: string }> };
    expect(parsed.ok).toBe(false);
    expect(parsed.findings.map((item) => item.code)).toContain("SPEC_AMBIGUITY_GATE");
    expect(parsed.findings.map((item) => item.code)).toContain("SPEC_AMBIGUITY_MISMATCH");
  });

  it("rejects a plan that does not map every locked requirement", async () => {
    const fixture = await makeInitializedPhase();
    await writeFile(fixture.specPath, validSpec(), "utf8");
    await writeFile(fixture.planPath, validPlan().replaceAll("ASR-02", "ASR-01"), "utf8");
    const result = await runNode(workflowScript, [
      "validate", "--project", fixture.project, "--phase", "01-runtime", "--gate", "plan", "--format", "json"
    ]);
    expect(result.exitCode).toBe(1);
    const parsed = JSON.parse(result.stdout) as { findings: Array<{ code: string; requirement: string | null }> };
    expect(parsed.findings).toContainEqual(expect.objectContaining({ code: "PLAN_REQUIREMENT_UNMAPPED", requirement: "ASR-02" }));
  });

  it("blocks execution when the selected phase or specification goal drifts from active planning", async () => {
    const fixture = await makeInitializedPhase();
    await writeFile(fixture.specPath, validSpec(), "utf8");

    const aligned = await runNode(workflowScript, [
      "validate", "--project", fixture.project, "--phase", "01", "--gate", "align", "--format", "json"
    ]);
    expect(aligned.exitCode).toBe(0);
    expect(JSON.parse(aligned.stdout)).toMatchObject({
      ok: true,
      milestone: "test-v1",
      goal: "Agents can validate workflow state and requirement evidence deterministically."
    });

    await writeFile(fixture.specPath, validSpec().replace(
      "Agents can validate workflow state and requirement evidence deterministically.",
      "Agents can ship unrelated work."
    ), "utf8");
    const goalDrift = await runNode(workflowScript, [
      "validate", "--project", fixture.project, "--phase", "01", "--gate", "align", "--format", "json"
    ]);
    expect(goalDrift.exitCode).toBe(1);
    expect((JSON.parse(goalDrift.stdout) as { findings: Array<{ code: string }> }).findings)
      .toContainEqual(expect.objectContaining({ code: "ALIGN_GOAL_DRIFT" }));

    await writeFile(fixture.specPath, validSpec(), "utf8");
    await writeFile(join(fixture.project, ".planning", "STATE.md"), validState().replace("current_phase: 01", "current_phase: 02"), "utf8");
    const phaseDrift = await runNode(workflowScript, [
      "validate", "--project", fixture.project, "--phase", "01", "--gate", "align", "--format", "json"
    ]);
    expect(phaseDrift.exitCode).toBe(1);
    expect((JSON.parse(phaseDrift.stdout) as { findings: Array<{ code: string }> }).findings)
      .toContainEqual(expect.objectContaining({ code: "ALIGN_PHASE_DRIFT" }));
  });

  it("requires research, renewed discussion, context, and plan acceptance before execution", async () => {
    const fixture = await makeInitializedPhase();
    await writeFile(fixture.specPath, validSpec(), "utf8");
    await writeFile(fixture.planPath, validPlan(), "utf8");

    const researchState = await runNode(workflowScript, ["next", "--project", fixture.project, "--phase", "01", "--format", "json"]);
    expect(researchState.exitCode).toBe(0);
    expect(JSON.parse(researchState.stdout)).toMatchObject({ status: "research" });

    const blocked = await runNode(workflowScript, [
      "validate", "--project", fixture.project, "--phase", "01", "--gate", "execute", "--format", "json"
    ]);
    expect(blocked.exitCode).toBe(1);
    expect((JSON.parse(blocked.stdout) as { findings: Array<{ code: string }> }).findings.map((item) => item.code)).toEqual(
      expect.arrayContaining(["RESEARCH_PLACEHOLDER", "DISCUSSION_PLACEHOLDER", "CONTEXT_PLACEHOLDER"])
    );

    await writeFile(fixture.researchPath, validResearch(), "utf8");
    const discussionState = await runNode(workflowScript, ["next", "--project", fixture.project, "--phase", "01", "--format", "json"]);
    expect(JSON.parse(discussionState.stdout)).toMatchObject({ status: "re-discuss" });

    await writeFile(fixture.discussionPath, validDiscussion(), "utf8");
    await writeFile(fixture.contextPath, validContext(), "utf8");
    await writeFile(fixture.planPath, validPlan().replace("**Status:** Accepted", "**Status:** Planned"), "utf8");
    const reviewState = await runNode(workflowScript, ["next", "--project", fixture.project, "--phase", "01", "--format", "json"]);
    expect(JSON.parse(reviewState.stdout)).toMatchObject({ status: "review-plan" });
    expect((JSON.parse(reviewState.stdout) as { findings: Array<{ code: string }> }).findings).toContainEqual(
      expect.objectContaining({ code: "PLAN_NOT_ACCEPTED" })
    );

    await writeFile(fixture.planPath, validPlan(), "utf8");
    const ready = await runNode(workflowScript, [
      "validate", "--project", fixture.project, "--phase", "01", "--gate", "execute", "--format", "json"
    ]);
    expect(ready.exitCode).toBe(0);
    expect(JSON.parse(ready.stdout)).toMatchObject({ ok: true, gate: "execute", status: "passed" });
  });

  it("traces locked requirements through plans and legacy verification evidence to completion", async () => {
    const fixture = await makeInitializedPhase();
    await writeFile(fixture.specPath, validSpec(), "utf8");
    await writeFile(fixture.planPath, validPlan(), "utf8");
    await writeFile(fixture.researchPath, validResearch(), "utf8");
    await writeFile(fixture.discussionPath, validDiscussion(), "utf8");
    await writeFile(fixture.contextPath, validContext(), "utf8");
    await unlink(fixture.validationPath);
    await writeFile(join(fixture.phaseDir, "01-VERIFICATION.md"), validValidation(), "utf8");
    await writeFile(fixture.auditPath, validAudit(), "utf8");
    await writeFile(fixture.summaryPath, "# Summary\n\n**Status:** Complete\n\n## Outcome\n\nRuntime behavior is verified.\n", "utf8");

    const trace = await runNode(workflowScript, ["trace", "--project", fixture.project, "--phase", "1", "--format", "json"]);
    expect(trace.exitCode).toBe(0);
    expect((JSON.parse(trace.stdout) as { items: Array<{ id: string; planned: boolean; evidenceStatus: string }> }).items).toEqual([
      expect.objectContaining({ id: "ASR-01", planned: true, evidenceStatus: "PASS" }),
      expect.objectContaining({ id: "ASR-02", planned: true, evidenceStatus: "PASS" })
    ]);

    const complete = await runNode(workflowScript, [
      "validate", "--project", fixture.project, "--phase", "01", "--gate", "complete", "--format", "json"
    ]);
    expect(complete.exitCode).toBe(0);
    expect(JSON.parse(complete.stdout)).toMatchObject({ ok: true, gate: "complete", status: "passed" });

    const next = await runNode(workflowScript, ["next", "--project", fixture.project, "--phase", "01", "--format", "json"]);
    expect(next.exitCode).toBe(0);
    expect(JSON.parse(next.stdout)).toMatchObject({ status: "complete", nextAction: "No workflow action remains for this phase." });
  });

  it("requires an explicit project-context promotion decision after adoption", async () => {
    const fixture = await makeInitializedPhase();
    await writeFile(fixture.specPath, validSpec(), "utf8");
    await writeFile(fixture.planPath, validPlan(), "utf8");
    await writeFile(fixture.researchPath, validResearch(), "utf8");
    await writeFile(fixture.discussionPath, validDiscussion(), "utf8");
    await writeFile(fixture.contextPath, validContext(), "utf8");
    await writeFile(fixture.validationPath, validValidation(), "utf8");
    await writeFile(fixture.auditPath, validAudit(), "utf8");
    await writeFile(join(fixture.project, ".planning", "config.json"), JSON.stringify({
      context_schema: 1,
      context_adoption_phase: 1
    }), "utf8");
    await writeFile(fixture.summaryPath, "# Summary\n\n**Status:** Complete\n\n## Outcome\n\nRuntime behavior is verified.\n", "utf8");

    const missing = await runNode(workflowScript, [
      "validate", "--project", fixture.project, "--phase", "01", "--gate", "complete", "--format", "json"
    ]);
    expect(missing.exitCode).toBe(1);
    expect((JSON.parse(missing.stdout) as { findings: Array<{ code: string }> }).findings)
      .toContainEqual(expect.objectContaining({ code: "CONTEXT_PROMOTION_MISSING" }));

    await writeFile(fixture.summaryPath, `# Summary

**Status:** Complete

## Outcome

Runtime behavior is verified.

## Project Context Promotion

| Action | Context ID | Project context entry | Source phase | Result |
|---|---|---|---|---|
| NO_CHANGE | NONE | No durable cross-phase change | 01 | PASS |
`, "utf8");
    const complete = await runNode(workflowScript, [
      "validate", "--project", fixture.project, "--phase", "01", "--gate", "complete", "--format", "json"
    ]);
    expect(complete.exitCode).toBe(0);
  });

  it("does not accept passing requirement tests without roadmap goal evidence", async () => {
    const fixture = await makeInitializedPhase();
    await writeFile(fixture.specPath, validSpec(), "utf8");
    await writeFile(fixture.planPath, validPlan(), "utf8");
    await writeFile(fixture.researchPath, validResearch(), "utf8");
    await writeFile(fixture.discussionPath, validDiscussion(), "utf8");
    await writeFile(fixture.contextPath, validContext(), "utf8");
    await writeFile(fixture.validationPath, validValidation().replace(
      /\n## Goal Evidence[\s\S]*$/,
      ""
    ), "utf8");
    await writeFile(fixture.auditPath, validAudit(), "utf8");
    await writeFile(fixture.summaryPath, "# Summary\n\n**Status:** Complete\n\n## Outcome\n\nRequirements passed.\n", "utf8");

    const complete = await runNode(workflowScript, [
      "validate", "--project", fixture.project, "--phase", "01", "--gate", "complete", "--format", "json"
    ]);
    expect(complete.exitCode).toBe(1);
    expect((JSON.parse(complete.stdout) as { findings: Array<{ code: string }> }).findings)
      .toContainEqual(expect.objectContaining({ code: "GOAL_EVIDENCE_NOT_PASSED", requirement: "GOAL-01-01" }));
  });

  it("requires controlled-exception metadata for a task while a phase is active", async () => {
    const project = await makeProject();
    await runNode(workflowScript, ["init", "--project", project, "--task", "urgent-fix", "--write", "--format", "json"]);
    await writeFile(join(project, ".planning", "REQUESTS.md"), validRequests(), "utf8");
    await writeFile(join(project, ".planning", "STATE.md"), validState(), "utf8");
    await writeValidPlanningContext(project);
    await writeFile(join(project, ".planning", "tasks", "urgent-fix.md"), validNeutralTask().replaceAll("quick-fix", "urgent-fix"), "utf8");

    const missing = await runNode(workflowScript, [
      "validate", "--project", project, "--task", "urgent-fix", "--gate", "align", "--format", "json"
    ]);
    expect(missing.exitCode).toBe(1);
    expect((JSON.parse(missing.stdout) as { findings: Array<{ code: string }> }).findings.map((item) => item.code))
      .toEqual(expect.arrayContaining(["TASK_PARENT_PHASE_MISSING", "TASK_PARENT_MILESTONE_DRIFT", "TASK_EXCEPTION_STATUS_INVALID"]));

    await writeFile(join(project, ".planning", "tasks", "urgent-fix.md"), validControlledTask(), "utf8");
    const approved = await runNode(workflowScript, [
      "validate", "--project", project, "--task", "urgent-fix", "--gate", "align", "--format", "json"
    ]);
    expect(approved.exitCode).toBe(0);
    expect(JSON.parse(approved.stdout)).toMatchObject({ ok: true, task: "urgent-fix", gate: "align" });
  });

  it("validates a milestone only after every phase goal, requirement, audit, and summary passes", async () => {
    const fixture = await makeInitializedPhase();
    await writeFile(fixture.specPath, validSpec(), "utf8");
    await writeFile(fixture.planPath, validPlan(), "utf8");
    await writeFile(fixture.researchPath, validResearch(), "utf8");
    await writeFile(fixture.discussionPath, validDiscussion(), "utf8");
    await writeFile(fixture.contextPath, validContext(), "utf8");
    await writeFile(fixture.validationPath, validValidation(), "utf8");
    await writeFile(fixture.auditPath, validAudit(), "utf8");
    await writeFile(join(fixture.project, ".planning", "config.json"), JSON.stringify({
      context_schema: 1,
      context_adoption_phase: 1
    }), "utf8");
    await writeFile(fixture.summaryPath, `# Summary

**Status:** Complete

## Outcome

Runtime behavior is verified.

## Project Context Promotion

| Action | Context ID | Project context entry | Source phase | Result |
|---|---|---|---|---|
| NO_CHANGE | NONE | No durable cross-phase change | 01 | PASS |
`, "utf8");
    await writeFile(join(fixture.project, ".planning", "ROADMAP.md"), validRoadmap("Complete"), "utf8");
    await writeFile(join(fixture.project, ".planning", "REQUIREMENTS.md"), validProjectRequirements("Complete"), "utf8");

    const initialized = await runNode(workflowScript, [
      "init", "--project", fixture.project, "--milestone", "test-v1", "--write", "--format", "json"
    ]);
    expect(initialized.exitCode).toBe(0);
    const milestoneDir = join(fixture.project, ".planning", "milestones", "test-v1");
    await writeFile(join(milestoneDir, "MILESTONE-AUDIT.md"), validMilestoneAudit(), "utf8");
    await writeFile(join(milestoneDir, "MILESTONE-SUMMARY.md"), "# Milestone Summary\n\n**Status:** Complete\n\n## Outcome\n\nAll phase goals passed.\n", "utf8");

    const missingPromotion = await runNode(workflowScript, [
      "validate", "--project", fixture.project, "--milestone", "test-v1", "--gate", "complete", "--format", "json"
    ]);
    expect(missingPromotion.exitCode).toBe(1);
    expect((JSON.parse(missingPromotion.stdout) as { findings: Array<{ code: string }> }).findings)
      .toContainEqual(expect.objectContaining({ code: "MILESTONE_CONTEXT_PROMOTION_MISSING" }));

    await writeFile(join(milestoneDir, "MILESTONE-SUMMARY.md"), `# Milestone Summary

**Status:** Complete

## Outcome

All phase goals passed.

## Project Context Promotion

| Action | Context ID | Project context entry | Source milestone | Result |
|---|---|---|---|---|
| PROMOTE | CTX-ARCH-00 | Prefixes must not match another context ID | test-v1 | PASS |
`, "utf8");

    const prefixCollision = await runNode(workflowScript, [
      "validate", "--project", fixture.project, "--milestone", "test-v1", "--gate", "complete", "--format", "json"
    ]);
    expect(prefixCollision.exitCode).toBe(1);
    expect((JSON.parse(prefixCollision.stdout) as { findings: Array<{ code: string }> }).findings)
      .toContainEqual(expect.objectContaining({ code: "MILESTONE_CONTEXT_PROMOTION_ENTRY_MISSING" }));

    await writeFile(join(milestoneDir, "MILESTONE-SUMMARY.md"), `# Milestone Summary

**Status:** Complete

## Outcome

All phase goals passed.

## Project Context Promotion

| Action | Context ID | Project context entry | Source milestone | Result |
|---|---|---|---|---|
| PROMOTE | CTX-ARCH-001 | Validation remains non-mutating | test-v1 | PASS |
`, "utf8");

    const complete = await runNode(workflowScript, [
      "validate", "--project", fixture.project, "--milestone", "test-v1", "--gate", "complete", "--format", "json"
    ]);
    expect(complete.exitCode).toBe(0);
    expect(JSON.parse(complete.stdout)).toMatchObject({ ok: true, milestone: "test-v1", status: "passed" });
  });

  it("rejects unsafe phase traversal without creating files", async () => {
    const project = await makeProject();
    const result = await runNode(workflowScript, [
      "init", "--project", project, "--phase", "../outside", "--write", "--format", "json"
    ]);
    expect(result.exitCode).toBe(2);
    expect(JSON.parse(result.stdout)).toMatchObject({
      ok: false,
      findings: [expect.objectContaining({ code: "PHASE_INVALID" })]
    });
    await expect(access(join(project, ".planning"), constants.F_OK)).rejects.toMatchObject({ code: "ENOENT" });
  });

  it.skipIf(process.platform === "win32")("rejects initialization through a planning symlink outside the project", async () => {
    const project = await makeProject();
    const external = await makeProject();
    await symlink(external, join(project, ".planning"), "dir");

    const result = await runNode(workflowScript, [
      "init", "--project", project, "--phase", "01-runtime", "--write", "--format", "json"
    ]);
    expect(result.exitCode).toBe(2);
    expect(JSON.parse(result.stdout)).toMatchObject({
      ok: false,
      findings: [expect.objectContaining({ code: "PATH_OUTSIDE_PROJECT" })]
    });
    await expect(access(join(external, "REQUIREMENTS.md"), constants.F_OK)).rejects.toMatchObject({ code: "ENOENT" });
  });
});

describe("aimagician-superpower debugging helpers", () => {
  it("waits on a real command condition and emits structured progress", async () => {
    const result = await runNode(waitScript, [
      "--description", "node exits successfully", "--timeout-ms", "1000", "--format", "json",
      "--", process.execPath, "-e", "process.exit(0)"
    ]);
    expect(result.exitCode).toBe(0);
    expect(JSON.parse(result.stdout)).toMatchObject({ ok: true, attempts: 1, lastExitCode: 0 });
  });

  it("finds a filesystem polluter and preserves the created state", async () => {
    const project = await makeProject();
    const watched = join(project, "unexpected-state");
    const probe = `if (process.argv[1].includes('polluter')) require('node:fs').writeFileSync(${JSON.stringify(watched)}, 'evidence')`;
    const result = await runNode(polluterScript, [
      "--watch", watched,
      "--candidate", "clean.test.ts",
      "--candidate", "polluter.test.ts",
      "--format", "json",
      "--", process.execPath, "-e", probe, "{file}"
    ], project);
    expect(result.exitCode).toBe(1);
    expect(JSON.parse(result.stdout)).toMatchObject({
      ok: false,
      outcome: "polluter-found",
      polluter: "polluter.test.ts"
    });
    expect(await readFile(watched, "utf8")).toBe("evidence");

    const dirtyRetry = await runNode(polluterScript, [
      "--watch", watched, "--candidate", "clean.test.ts", "--format", "json",
      "--", process.execPath, "-e", "process.exit(0)", "{file}"
    ], project);
    expect(dirtyRetry.exitCode).toBe(2);
    expect(JSON.parse(dirtyRetry.stdout)).toMatchObject({ outcome: "initial-state-dirty" });
  });
});

async function makeProject(): Promise<string> {
  const project = await mkdtemp(join(tmpdir(), "aimagician-workflow-"));
  tempDirectories.push(project);
  return project;
}

async function makeGitProject(): Promise<string> {
  const project = await makeProject();
  await execFileAsync("git", ["init"], { cwd: project });
  await execFileAsync("git", ["config", "user.name", "Workflow Test"], { cwd: project });
  await execFileAsync("git", ["config", "user.email", "workflow@example.invalid"], { cwd: project });
  await writeFile(join(project, "README.md"), "# Fixture\n", "utf8");
  await execFileAsync("git", ["add", "README.md"], { cwd: project });
  await execFileAsync("git", ["commit", "-m", "test: initialize fixture"], { cwd: project });
  return project;
}

async function makeInitializedPhase(): Promise<{
  project: string;
  phaseDir: string;
  specPath: string;
  planPath: string;
  researchPath: string;
  discussionPath: string;
  contextPath: string;
  validationPath: string;
  auditPath: string;
  summaryPath: string;
}> {
  const project = await makeProject();
  const result = await runNode(workflowScript, ["init", "--project", project, "--phase", "01-runtime", "--write", "--format", "json"]);
  expect(result.exitCode).toBe(0);
  await writeFile(join(project, ".planning", "REQUESTS.md"), validRequests(), "utf8");
  await writeFile(join(project, ".planning", "STATE.md"), validState(), "utf8");
  await writeFile(join(project, ".planning", "ROADMAP.md"), validRoadmap(), "utf8");
  await writeFile(join(project, ".planning", "REQUIREMENTS.md"), validProjectRequirements(), "utf8");
  await writeValidPlanningContext(project);
  const phaseDir = join(project, ".planning", "phases", "01-runtime");
  return {
    project,
    phaseDir,
    specPath: join(phaseDir, "01-SPEC.md"),
    planPath: join(phaseDir, "01-01-PLAN.md"),
    researchPath: join(phaseDir, "01-RESEARCH.md"),
    discussionPath: join(phaseDir, "01-DISCUSSION-LOG.md"),
    contextPath: join(phaseDir, "01-CONTEXT.md"),
    validationPath: join(phaseDir, "01-VALIDATION.md"),
    auditPath: join(phaseDir, "01-AUDIT.md"),
    summaryPath: join(phaseDir, "01-SUMMARY.md")
  };
}

async function writeValidPlanningContext(project: string): Promise<void> {
  await writeFile(join(project, ".planning", "PROJECT.md"), `# Project

**Updated:** 2026-08-03

## Purpose

Provide deterministic workflow validation for engineering agents.

## Current Milestone

- Milestone: test-v1
- Goal: Validate runtime workflow behavior.

## Scope

- In scope: Workflow runtime and tests.
- Out of scope: Production deployment.

## Constraints

- Preserve dependency-free execution.

## Key Decisions

- Planning artifacts are the durable source of truth.
`, "utf8");
  await writeFile(join(project, ".planning", "CONTEXT.md"), `# Project Context

**Context schema:** v1
**Adoption source:** USR-TEST-001
**Last reviewed:** 2026-08-03

## Architecture Snapshot

The workflow runtime reads Markdown planning artifacts and emits deterministic findings.

## Stable Boundaries And Invariants

| ID | Contract | Canonical source | Status |
|---|---|---|---|
| CTX-ARCH-001 | Validation is non-mutating. | \`workflow.mjs\` | Active |

## Durable Decisions

| ID | Decision | Source | Status | Supersedes |
|---|---|---|---|---|
| CTX-DEC-001 | Keep validation dependency-free. | USR-TEST-001 | Active | NONE |

## Verification And Delivery Baseline

- Run focused runtime tests before closure.

## Source Routing

| Source ID | Topic | Path | Policy | Authority |
|---|---|---|---|---|
| SRC-STATE | Active checkpoint | \`.planning/STATE.md\` | MUST_READ on resume | Planning state |

## Superseded Decisions

- None.

## Open Questions

- None.
`, "utf8");
}

function validSpec(): string {
  return `# Phase 01: Runtime - Specification

**Created:** 2026-07-20
**Status:** Locked
**Risk:** medium
**User-facing:** no
**Requirements:** 2

## Goal

Agents can validate workflow state and requirement evidence deterministically.

## Background

The skill previously provided prose guidance without executable artifact checks.

## Requirements

### ASR-01: Validate artifacts

- **Source requests:** USR-TEST-001
- **Current:** No runtime validation command exists.
- **Target:** The runtime validates the controlled phase artifact contract.
- **Acceptance:** A valid fixture exits zero and an invalid fixture reports a stable finding code.

### ASR-02: Trace evidence

- **Source requests:** USR-TEST-001
- **Current:** Requirement coverage is reviewed manually.
- **Target:** The runtime maps each locked requirement to a plan and evidence status.
- **Acceptance:** Trace output reports both requirements as planned with PASS evidence.

## Boundaries

### In Scope

- Dependency-free Markdown artifact checks.

### Out Of Scope

- Automatic commits or hooks - mutation remains explicit.

## Constraints

- Node standard library only and cross-platform paths.

## Acceptance Criteria

- [ ] ASR-01 has concrete passing evidence.
- [ ] ASR-02 has concrete passing evidence.

## Blocking Questions

- None.

## Ambiguity Report

- **Goal clarity:** 0.90
- **Boundary clarity:** 0.90
- **Constraint clarity:** 0.80
- **Acceptance clarity:** 0.90
- **Ambiguity:** 0.12

## Decision Log

| Round | Perspective | Question | Decision |
|---:|---|---|---|
| 1 | Reality | What is missing? | Executable gates and traceability. |
`;
}

function validRequests(): string {
  return `# Request Ledger

## USR-TEST-001: Workflow runtime

**Status:** Accepted
**Source:** Test requirement

### Original Request

Provide deterministic workflow validation and traceability.

### Derived Requirements

- ASR-01
- ASR-02
`;
}

function validState(): string {
  return `---
milestone: test-v1
current_phase: 01
status: in_progress
---

# Project State

**Milestone:** test-v1
**Current phase:** 01
**Status:** In Progress
`;
}

function validRoadmap(status = "In Progress"): string {
  return `# Roadmap

## Milestone test-v1 - Runtime

### Phase 01: Runtime

**Goal:** Agents can validate workflow state and requirement evidence deterministically.
**Requirements:** [ASR-01, ASR-02]
**Status:** ${status}
**Success Criteria**:

1. **GOAL-01-01:** Valid and invalid workflow states produce deterministic outcomes.
`;
}

function validProjectRequirements(status = "In Progress"): string {
  return `# Requirements

## Traceability

| Requirement | Phase | Status |
|---|---|---|
| ASR-01 | Phase 01 | ${status} |
| ASR-02 | Phase 01 | ${status} |
`;
}

function validResearch(): string {
  return `# Phase 01: Runtime - Research

**Updated:** 2026-07-20

## Objective

Confirm the smallest dependency-free runtime and compatibility surface.

## Local Evidence

| Source | Fact | Relevance |
|---|---|---|
| Existing CLI | Node ESM is already supported. | The runtime can use the standard library. |

## External Evidence

| Source | Fact | Relevance |
|---|---|---|
| None required | - | Local behavior is sufficient. |

## Options

| Option | Benefits | Costs and risks | Verification |
|---|---|---|---|
| Node ESM | No install step | Markdown parsing stays intentionally bounded | Execute fixture tests |

## Recommendation

Use a skill-local Node ESM runtime with controlled artifact contracts.

## Assumptions To Confirm

- None.
`;
}

function validDiscussion(): string {
  return `# Phase 01: Runtime - Discussion Log

**Updated:** 2026-07-20

## Decisions

| Topic | Options considered | Decision | Reason |
|---|---|---|---|
| Runtime | Shell or Node | Node ESM | Cross-platform structured output |

## Assumptions

| Assumption | Status | Evidence or action |
|---|---|---|
| Node is available | Confirmed | Skill compatibility contract |

## Rejected Options

- Shell-only parsing because behavior would vary by platform.

## Deferred Work

- None.
`;
}

function validContext(): string {
  return `# Phase 01: Runtime - Context

**Updated:** 2026-07-20
**Specification:** \`01-SPEC.md\`

## Locked Requirements

- Read ASR-01 and ASR-02 from the locked specification.

## Implementation Decisions

- Use dependency-free Node ESM and stable JSON finding codes.

## Existing Patterns To Preserve

- Preserve PLAN.md and legacy VERIFICATION.md compatibility.

## Allowed Scope

- The owned skill runtime and focused tests.

## Forbidden Scope

- User files outside the selected project and phase.

## Integration And Compatibility

- Existing project planning artifacts are never overwritten.
`;
}

function validPlan(): string {
  return `# Runtime Plan

**Requirements:** ASR-01, ASR-02
**Status:** Accepted

## Objective

Implement and test the dependency-free workflow runtime.

## Tasks

### Task 1: Runtime gates

**Requirements:** ASR-01

Implement controlled artifact validation and stable findings.

### Task 2: Evidence trace

**Requirements:** ASR-02

Map specification IDs to plans and validation evidence.

## Verification

\`\`\`bash
npm test -- --run tests/skills/aimagician-superpower-runtime.test.ts
\`\`\`

## Rollback And Recovery

Remove the owned runtime files without touching project artifacts.
`;
}

function validValidation(): string {
  return `# Runtime Validation

## Requirement Evidence

| Requirement | Status | Evidence | Observed result |
|---|---|---|---|
| ASR-01 | PASS | focused runtime test | Valid and invalid fixtures behave as specified. |
| ASR-02 | PASS | trace test | Both requirements are planned and evidenced. |

## Goal Evidence

| Goal criterion | Status | Evidence | Observed result |
|---|---|---|---|
| GOAL-01-01 | PASS | alignment and completion tests | Goal drift fails and aligned work passes. |
`;
}

function validAudit(): string {
  return `# Runtime Audit

## Auditor Run

- **Provider:** OpenCode
- **Primary model:** \`opencode/deepseek-v4-flash-free\`
- **Model:** \`opencode/deepseek-v4-flash-free\`
- **Attempt chain:** \`opencode/deepseek-v4-flash-free: success\`
- **Fallback reason:** NONE
- **Session:** ses_test_complete
- **Run status:** DONE
- **Review point:** test-fixture-head
- **Controller spot-check:** PASS - decisive fixture assertions were rerun.

## Requirement Coverage

| Source request | Requirement | Planned | Evidence | Audit | Decision |
|---|---|---|---|---|---|
| USR-TEST-001 | ASR-01 | Yes | PASS | PASS | Complete |
| USR-TEST-001 | ASR-02 | Yes | PASS | PASS | Complete |

## Goal Coverage

| Goal criterion | Planned | Evidence | Audit | Decision |
|---|---|---|---|---|
| GOAL-01-01 | Yes | PASS | PASS | Complete |

## Finding Counts

- **Blocker:** 0
- **Important:** 0
- **Nitpick:** 0

## Closure Decision

**Status:** Complete
**Reason:** Requirements and evidence passed independent review.
`;
}

function validTask(): string {
  return `# Task: quick-fix

**Task ID:** quick-fix
**Status:** Complete
**Source request:** USR-TEST-001
**Review point:** test-fixture-head

## Original Request

Apply and verify a bounded quick fix.

## Accepted Decisions

- Keep the change inside the fixture.

## Checklist

- [x] TASK-REQ-001: Implement and verify the fix.

## Evidence

| Requirement | Evidence | Status |
|---|---|---|
| TASK-REQ-001 | Focused test passed. | PASS |

## Agnes Completion Audit

- **Provider:** OpenCode
- **Model:** \`agnes/agnes-2.0-flash\`
- **Session:** ses_task_complete
- **Run status:** DONE
- **Review point:** test-fixture-head
- **Requirement matrix:** PASS
- **Blocker:** 0
- **Important:** 0
- **Nitpick:** 0
- **Controller spot-check:** PASS - focused evidence was inspected.

## Final Decision

**Status:** Complete
**Reason:** Checklist, evidence, and audit passed.
`;
}

function validNeutralTask(): string {
  return `# Task: quick-fix

**Task ID:** quick-fix
**Status:** Complete
**Source request:** USR-TEST-001
**Review point:** test-fixture-head

## Original Request

Apply and verify a bounded quick fix.

## Accepted Decisions

- Keep the change inside the fixture.

## Checklist

- [x] TASK-REQ-001: Implement and verify the fix.

## Evidence

| Requirement | Evidence | Status |
|---|---|---|
| TASK-REQ-001 | Focused test passed. | PASS |

## Independent Completion Audit

- **Provider:** OpenCode
- **Primary model:** \`opencode/deepseek-v4-flash-free\`
- **Model:** \`opencode/deepseek-v4-flash-free\`
- **Attempt chain:** \`opencode/deepseek-v4-flash-free: success\`
- **Fallback reason:** NONE
- **Session:** ses_task_complete
- **Run status:** DONE
- **Review point:** test-fixture-head
- **Requirement matrix:** PASS
- **Blocker:** 0
- **Important:** 0
- **Nitpick:** 0
- **Controller spot-check:** PASS - focused evidence was inspected.

## Final Decision

**Status:** Complete
**Reason:** Checklist, evidence, and audit passed.
`;
}

function validControlledTask(): string {
  return validNeutralTask()
    .replaceAll("quick-fix", "urgent-fix")
    .replace(
      "**Source request:** USR-TEST-001",
      `**Source request:** USR-TEST-001
**Parent milestone:** test-v1
**Parent phase:** 01
**Exception status:** Approved
**Approval source:** USR-TEST-001
**Return checkpoint:** Resume the active runtime validation phase.`
    );
}

function validDeliveryTask({
  mergeSha = "NOT_RUN",
  postmerge = "NOT_RUN",
  artifactMatch = "NOT_RUN",
  decision = "NOT_RUN"
}: {
  mergeSha?: string;
  postmerge?: string;
  artifactMatch?: string;
  decision?: string;
} = {}): string {
  return validNeutralTask()
    .replaceAll("quick-fix", "delivery-check")
    .replace(
      "## Independent Completion Audit",
      `## Delivery Contract

- **Delivery contract:** v1
- **Delivery class:** Deployable
- **Context coverage:** PASS
- **Local verification:** PASS
- **CI verification:** PASS
- **Preview verification:** N/A
- **Online-only exceptions:** N/A
- **Artifact provenance:** PASS
- **Premerge decision:** MERGE_READY
- **Implementation merge SHA:** ${mergeSha}
- **Postmerge verification:** ${postmerge}
- **Deployed artifact match:** ${artifactMatch}
- **Provenance exception:** NONE
- **Recovery status:** NOT_REQUIRED
- **Postmerge decision:** ${decision}

## Independent Completion Audit`
    );
}

function validMilestoneAudit(): string {
  return `# Milestone test-v1 - Audit

## Auditor Run

- **Provider:** OpenCode
- **Primary model:** \`opencode/deepseek-v4-flash-free\`
- **Model:** \`opencode/deepseek-v4-flash-free\`
- **Attempt chain:** \`opencode/deepseek-v4-flash-free: success\`
- **Fallback reason:** NONE
- **Session:** ses_milestone_complete
- **Run status:** DONE
- **Review point:** test-fixture-head
- **Controller spot-check:** PASS - phase evidence and goal outcomes were rerun.

## Requirement And Goal Coverage

| Phase | Item | Evidence | Audit | Decision |
|---|---|---|---|---|
| 01 | ASR-01 | PASS | PASS | Complete |
| 01 | ASR-02 | PASS | PASS | Complete |
| 01 | GOAL-01-01 | PASS | PASS | Complete |

## Finding Counts

- **Blocker:** 0
- **Important:** 0
- **Nitpick:** 0

## Closure Decision

**Status:** Complete
**Reason:** Every phase goal and requirement passed.
`;
}

function runNode(script: string, args: string[], cwd = process.cwd()): Promise<{ exitCode: number; stdout: string; stderr: string }> {
  return new Promise((resolveResult) => {
    const child = spawn(process.execPath, [script, ...args], { cwd, stdio: ["ignore", "pipe", "pipe"] });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk.toString(); });
    child.stderr.on("data", (chunk) => { stderr += chunk.toString(); });
    child.on("error", (error) => resolveResult({ exitCode: 2, stdout, stderr: `${stderr}${error.message}` }));
    child.on("close", (exitCode) => resolveResult({ exitCode: exitCode ?? 2, stdout, stderr }));
  });
}
