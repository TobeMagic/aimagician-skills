import { spawn } from "node:child_process";
import { access, mkdtemp, mkdir, readFile, rm, symlink, unlink, writeFile } from "node:fs/promises";
import { constants } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";

const tempDirectories: string[] = [];
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
    expect(previewResult.planned).toContain(".planning/phases/01-runtime/01-SPEC.md");
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
    await writeFile(fixture.auditPath, "# Audit\n\n**Status:** Complete\n\n## Closure\n\nAll requirements passed.\n", "utf8");
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

- **Current:** No runtime validation command exists.
- **Target:** The runtime validates the controlled phase artifact contract.
- **Acceptance:** A valid fixture exits zero and an invalid fixture reports a stable finding code.

### ASR-02: Trace evidence

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
