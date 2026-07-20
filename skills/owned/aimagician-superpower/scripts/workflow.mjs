#!/usr/bin/env node

import { access, mkdir, readFile, readdir, realpath, writeFile } from "node:fs/promises";
import { constants } from "node:fs";
import { basename, dirname, isAbsolute, join, relative, resolve, sep } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const SCRIPT_DIR = fileURLToPath(new URL(".", import.meta.url));
const TEMPLATE_DIR = resolve(SCRIPT_DIR, "..", "assets", "templates");
const COMMANDS = new Set(["init", "status", "validate", "trace", "next", "help"]);
const GATES = new Set(["spec", "plan", "execute", "complete"]);
const FORMATS = new Set(["text", "json"]);
const RISKS = new Set(["low", "medium", "high"]);
const EXTENSIONS = new Set(["ui", "ai", "security-ops"]);

const PROJECT_TEMPLATES = [
  ["project-requirements.md", "REQUIREMENTS.md"],
  ["project-roadmap.md", "ROADMAP.md"],
  ["project-state.md", "STATE.md"]
];

const PHASE_TEMPLATES = [
  ["phase-spec.md", "{prefix}-SPEC.md"],
  ["phase-context.md", "{prefix}-CONTEXT.md"],
  ["phase-discussion-log.md", "{prefix}-DISCUSSION-LOG.md"],
  ["phase-research.md", "{prefix}-RESEARCH.md"],
  ["phase-plan.md", "{prefix}-01-PLAN.md"],
  ["phase-validation.md", "{prefix}-VALIDATION.md"],
  ["phase-uat.md", "{prefix}-UAT.md"],
  ["phase-audit.md", "{prefix}-AUDIT.md"],
  ["phase-summary.md", "{prefix}-SUMMARY.md"]
];

const EXTENSION_TEMPLATES = {
  ui: ["extension-ui-spec.md", "{prefix}-UI-SPEC.md"],
  ai: ["extension-ai-spec.md", "{prefix}-AI-SPEC.md"],
  "security-ops": ["extension-security-ops-spec.md", "{prefix}-SECURITY-OPS-SPEC.md"]
};

const MINIMUM_SCORES = {
  goal: 0.75,
  boundary: 0.70,
  constraint: 0.65,
  acceptance: 0.70
};

class WorkflowError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}

function parseArgs(argv) {
  const command = argv[0] ?? "help";
  if (!COMMANDS.has(command)) {
    throw new WorkflowError("USAGE_UNKNOWN_COMMAND", `Unknown command: ${command}`);
  }

  const options = {
    command,
    project: process.cwd(),
    phase: undefined,
    format: "text",
    gate: "spec",
    risk: "medium",
    extensions: [],
    write: false
  };

  for (let index = 1; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--write") {
      options.write = true;
      continue;
    }

    const next = argv[index + 1];
    if (["--project", "--phase", "--format", "--gate", "--risk", "--extensions"].includes(token)) {
      if (!next || next.startsWith("--")) {
        throw new WorkflowError("USAGE_MISSING_VALUE", `${token} requires a value`);
      }
      index += 1;
      if (token === "--project") options.project = next;
      if (token === "--phase") options.phase = next;
      if (token === "--format") options.format = next;
      if (token === "--gate") options.gate = next;
      if (token === "--risk") options.risk = next;
      if (token === "--extensions") {
        options.extensions = next.split(",").map((value) => value.trim()).filter(Boolean);
      }
      continue;
    }

    if (token === "--help" || token === "-h") {
      options.command = "help";
      continue;
    }
    throw new WorkflowError("USAGE_UNKNOWN_OPTION", `Unknown option: ${token}`);
  }

  if (!FORMATS.has(options.format)) {
    throw new WorkflowError("USAGE_INVALID_FORMAT", `Unsupported format: ${options.format}`);
  }
  if (!GATES.has(options.gate)) {
    throw new WorkflowError("USAGE_INVALID_GATE", `Unsupported gate: ${options.gate}`);
  }
  if (!RISKS.has(options.risk)) {
    throw new WorkflowError("USAGE_INVALID_RISK", `Unsupported risk: ${options.risk}`);
  }
  for (const extension of options.extensions) {
    if (!EXTENSIONS.has(extension)) {
      throw new WorkflowError("USAGE_INVALID_EXTENSION", `Unsupported extension: ${extension}`);
    }
  }

  options.project = resolve(options.project);
  return options;
}

async function exists(path) {
  try {
    await access(path, constants.F_OK);
    return true;
  } catch {
    return false;
  }
}

function assertSafePhaseToken(value) {
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(value) || value.includes("..")) {
    throw new WorkflowError("PHASE_INVALID", `Unsafe phase identifier: ${value}`);
  }
}

function isInside(root, candidate) {
  const rel = relative(root, candidate);
  return rel === "" || (rel !== ".." && !rel.startsWith(`..${sep}`) && !isAbsolute(rel));
}

async function assertInside(root, path) {
  const resolvedRoot = resolve(root);
  const resolvedPath = resolve(path);
  if (!isInside(resolvedRoot, resolvedPath)) {
    throw new WorkflowError("PATH_OUTSIDE_PROJECT", `Refusing path outside project: ${path}`);
  }

  const canonicalRoot = await realpath(resolvedRoot);
  let existingAncestor = dirname(resolvedPath);
  while (!await exists(existingAncestor)) {
    const parent = dirname(existingAncestor);
    if (parent === existingAncestor) break;
    existingAncestor = parent;
  }
  const canonicalAncestor = await realpath(existingAncestor);
  if (!isInside(canonicalRoot, canonicalAncestor)) {
    throw new WorkflowError("PATH_OUTSIDE_PROJECT", `Refusing path through an external symlink: ${path}`);
  }
}

function extractScalar(content, label) {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const match = content.match(new RegExp(`^\\s*(?:[-*]\\s+)?\\*\\*${escaped}:\\*\\*\\s*(.+?)\\s*$`, "im"));
  return match?.[1]?.trim();
}

function extractStatePhase(content) {
  const yaml = content.match(/^current_phase:\s*["']?([^\n"']+)/m)?.[1]?.trim();
  return yaml ?? extractScalar(content, "Current phase")?.split(/\s+/)[0];
}

async function findPhase(project, requested, allowCreate = false) {
  const planningDir = join(project, ".planning");
  const phasesDir = join(planningDir, "phases");
  let phaseToken = requested;

  if (!phaseToken && await exists(join(planningDir, "STATE.md"))) {
    phaseToken = extractStatePhase(await readFile(join(planningDir, "STATE.md"), "utf8"));
  }

  if (!phaseToken) return null;
  assertSafePhaseToken(phaseToken);

  let directories = [];
  if (await exists(phasesDir)) {
    directories = (await readdir(phasesDir, { withFileTypes: true }))
      .filter((entry) => entry.isDirectory())
      .map((entry) => entry.name)
      .sort();
  }

  const exact = directories.find((entry) => entry === phaseToken);
  if (exact) return phaseInfo(phasesDir, exact);

  const numeric = phaseToken.match(/^\d+$/)?.[0];
  if (numeric) {
    const normalized = String(Number(numeric));
    const matches = directories.filter((entry) => {
      const prefix = entry.match(/^\d+/)?.[0];
      return prefix !== undefined && String(Number(prefix)) === normalized;
    });
    if (matches.length === 1) return phaseInfo(phasesDir, matches[0]);
    if (matches.length > 1) {
      throw new WorkflowError("PHASE_AMBIGUOUS", `Phase ${phaseToken} matches: ${matches.join(", ")}`);
    }
  }

  if (!allowCreate) {
    throw new WorkflowError("PHASE_NOT_FOUND", `Phase not found: ${phaseToken}`);
  }
  const createdName = numeric ? `${phaseToken.padStart(2, "0")}-phase` : phaseToken;
  return phaseInfo(phasesDir, createdName);
}

function phaseInfo(phasesDir, name) {
  const leading = name.match(/^\d+/)?.[0];
  const prefix = leading ?? name;
  const displayName = name.slice(prefix.length).replace(/^-+/, "").replace(/[-_]+/g, " ") || `Phase ${prefix}`;
  return { name, prefix, displayName, dir: join(phasesDir, name) };
}

function replaceTokens(content, context) {
  return content
    .replaceAll("{{PROJECT_NAME}}", context.projectName)
    .replaceAll("{{PHASE}}", context.phase?.name ?? "TBD")
    .replaceAll("{{PHASE_PREFIX}}", context.phase?.prefix ?? "TBD")
    .replaceAll("{{PHASE_NAME}}", context.phase?.displayName ?? "TBD")
    .replaceAll("{{RISK}}", context.risk)
    .replaceAll("{{DATE}}", context.date);
}

async function initArtifacts(options) {
  if (!await exists(options.project)) {
    throw new WorkflowError("PROJECT_NOT_FOUND", `Project directory not found: ${options.project}`);
  }
  const planningDir = join(options.project, ".planning");
  const phase = options.phase ? await findPhase(options.project, options.phase, true) : await findPhase(options.project, undefined, false).catch(() => null);
  const context = {
    projectName: basename(options.project),
    phase,
    risk: options.risk,
    date: new Date().toISOString().slice(0, 10)
  };
  const candidates = PROJECT_TEMPLATES.map(([template, destination]) => ({
    template: join(TEMPLATE_DIR, template),
    destination: join(planningDir, destination)
  }));

  if (phase) {
    for (const [template, destination] of PHASE_TEMPLATES) {
      candidates.push({
        template: join(TEMPLATE_DIR, template),
        destination: join(phase.dir, destination.replace("{prefix}", phase.prefix))
      });
    }
    for (const extension of options.extensions) {
      const [template, destination] = EXTENSION_TEMPLATES[extension];
      candidates.push({
        template: join(TEMPLATE_DIR, template),
        destination: join(phase.dir, destination.replace("{prefix}", phase.prefix))
      });
    }
  }

  const planned = [];
  const skipped = [];
  for (const candidate of candidates) {
    await assertInside(options.project, candidate.destination);
    if (await exists(candidate.destination)) {
      skipped.push(relative(options.project, candidate.destination));
      continue;
    }
    planned.push(relative(options.project, candidate.destination));
    if (!options.write) continue;
    await mkdir(dirname(candidate.destination), { recursive: true });
    const template = await readFile(candidate.template, "utf8");
    await writeFile(candidate.destination, replaceTokens(template, context), { encoding: "utf8", flag: "wx" });
  }

  return {
    ok: true,
    command: "init",
    mode: options.write ? "write" : "preview",
    project: options.project,
    phase: phase?.name ?? null,
    planned,
    skipped,
    findings: []
  };
}

async function loadPhase(project, requested) {
  if (!await exists(project)) {
    throw new WorkflowError("PROJECT_NOT_FOUND", `Project directory not found: ${project}`);
  }
  const phase = await findPhase(project, requested, false);
  if (!phase) {
    throw new WorkflowError("PHASE_REQUIRED", "Provide --phase or record current_phase in .planning/STATE.md");
  }
  const names = (await readdir(phase.dir, { withFileTypes: true }))
    .filter((entry) => entry.isFile())
    .map((entry) => entry.name)
    .sort();

  const select = (predicate) => names.filter(predicate).map((name) => join(phase.dir, name));
  const artifacts = {
    spec: select((name) => name.endsWith("-SPEC.md") && !/(?:-UI|-AI|-SECURITY-OPS)-SPEC\.md$/.test(name))[0],
    context: select((name) => /-CONTEXT\.md$/.test(name))[0],
    discussion: select((name) => /-DISCUSSION-LOG\.md$/.test(name))[0],
    research: select((name) => /-RESEARCH\.md$/.test(name))[0],
    plans: select((name) => name === "PLAN.md" || /-PLAN\.md$/.test(name)),
    validation: select((name) => /-(?:VALIDATION|VERIFICATION)\.md$/.test(name)),
    uat: select((name) => /-UAT\.md$/.test(name))[0],
    audit: select((name) => /-AUDIT\.md$/.test(name))[0],
    summary: select((name) => /-SUMMARY\.md$/.test(name))[0]
  };
  const contents = {};
  for (const [key, value] of Object.entries(artifacts)) {
    if (Array.isArray(value)) {
      contents[key] = await Promise.all(value.map(async (path) => ({ path, content: await readFile(path, "utf8") })));
    } else {
      contents[key] = value ? { path: value, content: await readFile(value, "utf8") } : null;
    }
  }
  return { project, phase, artifacts, contents };
}

function getSection(content, title) {
  const lines = content.split(/\r?\n/);
  const normalized = title.trim().toLowerCase();
  const start = lines.findIndex((line) => line.match(/^##\s+/)?.[0] && line.replace(/^##\s+/, "").trim().toLowerCase() === normalized);
  if (start < 0) return "";
  let end = lines.length;
  for (let index = start + 1; index < lines.length; index += 1) {
    if (/^##\s+/.test(lines[index])) {
      end = index;
      break;
    }
  }
  return lines.slice(start + 1, end).join("\n").trim();
}

function hasPlaceholder(content) {
  return /\bTBD\b|\{\{[^}]+\}\}|<(?:OBJECTIVE|CONTEXT|SCOPE|TASK|SPEC|PLAN|EVIDENCE)>/i.test(content);
}

function finding(code, message, artifact = null, requirement = null, severity = "error") {
  return { code, severity, artifact, requirement, message };
}

function validateSupportingArtifact(loaded, key, label, requiredSections) {
  const document = loaded.contents[key];
  const code = label.toUpperCase();
  if (!document) {
    return [finding(`${code}_MISSING`, `${label} artifact is required before execution`)];
  }

  const artifact = relative(loaded.project, document.path);
  const findings = [];
  if (hasPlaceholder(document.content)) {
    findings.push(finding(`${code}_PLACEHOLDER`, `${label} artifact still contains unresolved placeholders`, artifact));
  }
  for (const section of requiredSections) {
    if (!getSection(document.content, section)) {
      findings.push(finding(`${code}_SECTION_MISSING`, `${label} artifact is missing section: ${section}`, artifact));
    }
  }
  return findings;
}

function validateResearch(loaded) {
  return validateSupportingArtifact(loaded, "research", "RESEARCH", [
    "Objective", "Local Evidence", "Options", "Recommendation", "Assumptions To Confirm"
  ]);
}

function validateDeliberation(loaded) {
  return [
    ...validateSupportingArtifact(loaded, "discussion", "DISCUSSION", [
      "Decisions", "Assumptions", "Rejected Options", "Deferred Work"
    ]),
    ...validateSupportingArtifact(loaded, "context", "CONTEXT", [
      "Implementation Decisions", "Existing Patterns To Preserve", "Allowed Scope",
      "Forbidden Scope", "Integration And Compatibility"
    ])
  ];
}

function validatePreparation(loaded) {
  return [...validateResearch(loaded), ...validateDeliberation(loaded)];
}

function extractRequirements(content) {
  const heading = /^###\s+([A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+)(?::|\s+-|\s|$).*$/gm;
  const matches = [...content.matchAll(heading)];
  return matches.map((match, index) => {
    const start = match.index ?? 0;
    const end = matches[index + 1]?.index ?? content.length;
    const block = content.slice(start, end);
    return {
      id: match[1],
      block,
      current: extractScalar(block, "Current"),
      target: extractScalar(block, "Target"),
      acceptance: extractScalar(block, "Acceptance")
    };
  });
}

function extractRequirementReferences(content) {
  const references = new Set();
  const matches = content.matchAll(/^\*\*Requirements:\*\*\s*(.+)$/gim);
  for (const match of matches) {
    for (const id of match[1].match(/[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+/g) ?? []) {
      references.add(id);
    }
  }
  return references;
}

function parseScore(content, label) {
  const value = extractScalar(content, label);
  if (value === undefined) return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function validateSpec(loaded) {
  const findings = [];
  const artifact = loaded.artifacts.spec ? relative(loaded.project, loaded.artifacts.spec) : null;
  const content = loaded.contents.spec?.content;
  if (!content) {
    return { findings: [finding("SPEC_MISSING", "Phase specification is missing")], requirements: [] };
  }

  const requiredSections = [
    "Goal", "Background", "Requirements", "Boundaries", "Constraints",
    "Acceptance Criteria", "Blocking Questions", "Ambiguity Report", "Decision Log"
  ];
  for (const section of requiredSections) {
    if (!getSection(content, section)) {
      findings.push(finding("SPEC_SECTION_MISSING", `Missing section: ${section}`, artifact));
    }
  }
  if (hasPlaceholder(content)) {
    findings.push(finding("SPEC_PLACEHOLDER", "Specification still contains unresolved placeholders", artifact));
  }

  const status = extractScalar(content, "Status")?.toLowerCase();
  if (status !== "locked") {
    findings.push(finding("SPEC_NOT_LOCKED", "Specification status must be Locked", artifact));
  }
  const risk = extractScalar(content, "Risk")?.toLowerCase();
  if (!risk || !RISKS.has(risk)) {
    findings.push(finding("SPEC_RISK_INVALID", "Risk must be low, medium, or high", artifact));
  }
  const userFacing = extractScalar(content, "User-facing")?.toLowerCase();
  if (!new Set(["yes", "no"]).has(userFacing)) {
    findings.push(finding("SPEC_USER_FACING_INVALID", "User-facing must be yes or no", artifact));
  }

  const requirements = extractRequirements(content);
  if (requirements.length === 0) {
    findings.push(finding("SPEC_REQUIREMENTS_MISSING", "No stable requirement IDs were found", artifact));
  }
  const seen = new Set();
  for (const requirement of requirements) {
    if (seen.has(requirement.id)) {
      findings.push(finding("SPEC_REQUIREMENT_DUPLICATE", `Duplicate requirement: ${requirement.id}`, artifact, requirement.id));
    }
    seen.add(requirement.id);
    for (const [field, value] of [["Current", requirement.current], ["Target", requirement.target], ["Acceptance", requirement.acceptance]]) {
      if (!value || hasPlaceholder(value)) {
        findings.push(finding("SPEC_REQUIREMENT_FIELD_MISSING", `${requirement.id} is missing a concrete ${field} value`, artifact, requirement.id));
      }
    }
  }
  const declaredCount = Number(extractScalar(content, "Requirements"));
  if (!Number.isInteger(declaredCount) || declaredCount !== requirements.length) {
    findings.push(finding("SPEC_REQUIREMENT_COUNT_MISMATCH", `Declared requirement count must equal ${requirements.length}`, artifact));
  }

  const boundaries = getSection(content, "Boundaries");
  if (!/^###\s+In Scope/m.test(boundaries) || !/^###\s+Out Of Scope/m.test(boundaries)) {
    findings.push(finding("SPEC_BOUNDARIES_INCOMPLETE", "Boundaries require In Scope and Out Of Scope subsections", artifact));
  }

  const blocking = getSection(content, "Blocking Questions")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line.startsWith("-"));
  if (blocking.length === 0 || blocking.some((line) => !/^-\s+None\.?$/i.test(line))) {
    findings.push(finding("SPEC_BLOCKING_QUESTIONS", "Blocking questions must be resolved before lock", artifact));
  }

  const scores = {
    goal: parseScore(content, "Goal clarity"),
    boundary: parseScore(content, "Boundary clarity"),
    constraint: parseScore(content, "Constraint clarity"),
    acceptance: parseScore(content, "Acceptance clarity"),
    ambiguity: parseScore(content, "Ambiguity")
  };
  for (const [key, minimum] of Object.entries(MINIMUM_SCORES)) {
    const score = scores[key];
    if (score === undefined || score < 0 || score > 1) {
      findings.push(finding("SPEC_SCORE_INVALID", `${key} clarity must be a number from 0 to 1`, artifact));
    } else if (score < minimum) {
      findings.push(finding("SPEC_SCORE_BELOW_MINIMUM", `${key} clarity ${score.toFixed(2)} is below ${minimum.toFixed(2)}`, artifact));
    }
  }
  if (scores.ambiguity === undefined || scores.ambiguity < 0 || scores.ambiguity > 1) {
    findings.push(finding("SPEC_AMBIGUITY_INVALID", "Ambiguity must be a number from 0 to 1", artifact));
  } else {
    if (scores.ambiguity > 0.20) {
      findings.push(finding("SPEC_AMBIGUITY_GATE", `Ambiguity ${scores.ambiguity.toFixed(2)} exceeds 0.20`, artifact));
    }
    if (Object.keys(MINIMUM_SCORES).every((key) => scores[key] !== undefined)) {
      const calculated = 1 - (
        0.35 * scores.goal + 0.25 * scores.boundary +
        0.20 * scores.constraint + 0.20 * scores.acceptance
      );
      if (Math.abs(calculated - scores.ambiguity) > 0.015) {
        findings.push(finding("SPEC_AMBIGUITY_MISMATCH", `Ambiguity should be ${calculated.toFixed(2)} from the four clarity scores`, artifact));
      }
    }
  }

  const acceptanceItems = getSection(content, "Acceptance Criteria").match(/^- \[[ xX]\]\s+.+$/gm) ?? [];
  if (acceptanceItems.length < requirements.length) {
    findings.push(finding("SPEC_ACCEPTANCE_INCOMPLETE", "Acceptance Criteria must cover every requirement", artifact));
  }

  return { findings, requirements, risk, userFacing, status };
}

function validatePlan(loaded) {
  const spec = validateSpec(loaded);
  const findings = [...spec.findings];
  if (loaded.contents.plans.length === 0) {
    findings.push(finding("PLAN_MISSING", "No PLAN.md or *-PLAN.md artifact was found"));
    return { findings, requirements: spec.requirements, references: new Set() };
  }

  const references = new Set();
  for (const plan of loaded.contents.plans) {
    const artifact = relative(loaded.project, plan.path);
    if (hasPlaceholder(plan.content)) {
      findings.push(finding("PLAN_PLACEHOLDER", "Plan still contains unresolved placeholders", artifact));
    }
    for (const section of ["Objective", "Tasks", "Verification", "Rollback And Recovery"]) {
      if (!getSection(plan.content, section)) {
        findings.push(finding("PLAN_SECTION_MISSING", `Missing section: ${section}`, artifact));
      }
    }
    if (/^\s*false\s*$/m.test(getSection(plan.content, "Verification"))) {
      findings.push(finding("PLAN_VERIFICATION_INVALID", "Replace the placeholder verification command", artifact));
    }
    for (const id of extractRequirementReferences(plan.content)) references.add(id);
  }

  const known = new Set(spec.requirements.map((requirement) => requirement.id));
  for (const id of known) {
    if (!references.has(id)) {
      findings.push(finding("PLAN_REQUIREMENT_UNMAPPED", `${id} is not mapped to a plan`, null, id));
    }
  }
  for (const id of references) {
    if (!known.has(id)) {
      findings.push(finding("PLAN_UNKNOWN_REQUIREMENT", `${id} is referenced by a plan but absent from the specification`, null, id));
    }
  }

  return { findings, requirements: spec.requirements, references, userFacing: spec.userFacing };
}

function validateExecute(loaded) {
  const plan = validatePlan(loaded);
  const findings = [...validatePreparation(loaded), ...plan.findings];
  for (const document of loaded.contents.plans) {
    const artifact = relative(loaded.project, document.path);
    const status = extractScalar(document.content, "Status")?.toLowerCase();
    if (!new Set(["accepted", "approved"]).has(status)) {
      findings.push(finding("PLAN_NOT_ACCEPTED", "Plan status must be Accepted or Approved before execution", artifact));
    }
  }
  return { ...plan, findings };
}

function parseEvidence(documents) {
  const evidence = new Map();
  const unknownCandidates = new Set();
  for (const document of documents) {
    for (const line of document.content.split(/\r?\n/)) {
      if (!line.trim().startsWith("|")) continue;
      const cells = line.split("|").slice(1, -1).map((cell) => cell.trim());
      const id = cells[0];
      const status = cells[1]?.toUpperCase();
      if (!/^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$/.test(id ?? "")) continue;
      if (!new Set(["PASS", "FAIL", "NOT_RUN"]).has(status)) continue;
      unknownCandidates.add(id);
      const previous = evidence.get(id);
      if (!previous || previous.status !== "PASS") {
        evidence.set(id, {
          status,
          evidence: cells[2] ?? "",
          observed: cells[3] ?? "",
          artifact: document.path
        });
      }
    }
  }
  return { evidence, ids: unknownCandidates };
}

function traceLoaded(loaded) {
  const spec = validateSpec(loaded);
  const planReferences = new Set();
  for (const plan of loaded.contents.plans) {
    for (const id of extractRequirementReferences(plan.content)) planReferences.add(id);
  }
  const parsed = parseEvidence(loaded.contents.validation);
  const known = new Set(spec.requirements.map((requirement) => requirement.id));
  const items = spec.requirements.map((requirement) => {
    const record = parsed.evidence.get(requirement.id);
    return {
      id: requirement.id,
      planned: planReferences.has(requirement.id),
      evidenceStatus: record?.status ?? "NOT_RUN",
      evidence: record?.evidence ?? "",
      artifact: record ? relative(loaded.project, record.artifact) : null
    };
  });
  const findings = [];
  for (const item of items) {
    if (!item.planned) findings.push(finding("TRACE_UNPLANNED", `${item.id} is not mapped to a plan`, null, item.id));
    if (item.evidenceStatus === "NOT_RUN") findings.push(finding("TRACE_NO_EVIDENCE", `${item.id} has no passing evidence`, null, item.id));
    if (item.evidenceStatus === "FAIL") findings.push(finding("TRACE_FAILED", `${item.id} has failed evidence`, item.artifact, item.id));
  }
  for (const id of parsed.ids) {
    if (!known.has(id)) findings.push(finding("TRACE_UNKNOWN_REQUIREMENT", `${id} has evidence but is absent from the specification`, null, id));
  }
  return { findings, items, specFindings: spec.findings, userFacing: spec.userFacing };
}

function validateComplete(loaded) {
  const plan = validateExecute(loaded);
  const trace = traceLoaded(loaded);
  const findings = [...plan.findings, ...trace.findings];
  if (loaded.contents.validation.length === 0) {
    findings.push(finding("VALIDATION_MISSING", "Completion requires validation or verification evidence"));
  }
  if (!loaded.contents.audit) {
    findings.push(finding("AUDIT_MISSING", "Completion requires an audit artifact"));
  } else {
    const artifact = relative(loaded.project, loaded.contents.audit.path);
    if (hasPlaceholder(loaded.contents.audit.content)) findings.push(finding("AUDIT_PLACEHOLDER", "Audit contains unresolved placeholders", artifact));
    if (extractScalar(loaded.contents.audit.content, "Status")?.toLowerCase() !== "complete") {
      findings.push(finding("AUDIT_NOT_COMPLETE", "Audit status must be Complete", artifact));
    }
  }
  if (!loaded.contents.summary) {
    findings.push(finding("SUMMARY_MISSING", "Completion requires a summary artifact"));
  } else {
    const artifact = relative(loaded.project, loaded.contents.summary.path);
    if (hasPlaceholder(loaded.contents.summary.content)) findings.push(finding("SUMMARY_PLACEHOLDER", "Summary contains unresolved placeholders", artifact));
    if (extractScalar(loaded.contents.summary.content, "Status")?.toLowerCase() !== "complete") {
      findings.push(finding("SUMMARY_NOT_COMPLETE", "Summary status must be Complete", artifact));
    }
  }
  if (trace.userFacing === "yes") {
    if (!loaded.contents.uat) {
      findings.push(finding("UAT_MISSING", "User-facing work requires a UAT artifact"));
    } else {
      const artifact = relative(loaded.project, loaded.contents.uat.path);
      if (hasPlaceholder(loaded.contents.uat.content) || extractScalar(loaded.contents.uat.content, "Status")?.toUpperCase() !== "PASS") {
        findings.push(finding("UAT_NOT_PASSED", "User-facing UAT status must be PASS with no placeholders", artifact));
      }
    }
  }
  return { findings, items: trace.items };
}

async function validateCommand(options) {
  const loaded = await loadPhase(options.project, options.phase);
  let result;
  if (options.gate === "spec") result = validateSpec(loaded);
  if (options.gate === "plan") result = validatePlan(loaded);
  if (options.gate === "execute") result = validateExecute(loaded);
  if (options.gate === "complete") result = validateComplete(loaded);
  return {
    ok: result.findings.length === 0,
    command: "validate",
    project: options.project,
    phase: loaded.phase.name,
    gate: options.gate,
    status: result.findings.length === 0 ? "passed" : "failed",
    findings: result.findings
  };
}

async function traceCommand(options) {
  const loaded = await loadPhase(options.project, options.phase);
  const result = traceLoaded(loaded);
  return {
    ok: result.findings.length === 0 && result.specFindings.length === 0,
    command: "trace",
    project: options.project,
    phase: loaded.phase.name,
    status: result.findings.length === 0 ? "covered" : "gaps",
    items: result.items,
    findings: [...result.specFindings, ...result.findings]
  };
}

async function determineStatus(options) {
  const planningDir = join(options.project, ".planning");
  if (!await exists(planningDir)) {
    return { status: "uninitialized", nextAction: "Preview workflow.mjs init, then run it with --write." };
  }
  let loaded;
  try {
    loaded = await loadPhase(options.project, options.phase);
  } catch (error) {
    if (error instanceof WorkflowError && ["PHASE_REQUIRED", "PHASE_NOT_FOUND"].includes(error.code)) {
      return { status: "no-active-phase", nextAction: "Select an existing phase or initialize a named phase.", findings: [finding(error.code, error.message)] };
    }
    throw error;
  }

  const specContent = loaded.contents.spec?.content;
  if (!specContent) return phaseStatus(loaded, "needs-spec", "Discuss baseline requirements and create a draft specification.");
  const researchFindings = validateResearch(loaded);
  if (researchFindings.length > 0) {
    return phaseStatus(loaded, "research", "Complete grounded research before locking requirements or planning; reopen a locked specification if findings change it.", researchFindings);
  }
  const deliberationFindings = validateDeliberation(loaded);
  if (deliberationFindings.length > 0) {
    return phaseStatus(loaded, "re-discuss", "Re-discuss research findings, boundaries, assumptions, and implementation decisions.", deliberationFindings);
  }
  if (extractScalar(specContent, "Status")?.toLowerCase() !== "locked") {
    return phaseStatus(loaded, "lock-spec", "Resolve blocking questions, pass ambiguity scoring, and lock the specification.");
  }
  const spec = validateSpec(loaded);
  if (spec.findings.length > 0) return phaseStatus(loaded, "repair-spec", "Correct the locked specification until the spec gate passes.", spec.findings);
  if (loaded.contents.plans.length === 0) return phaseStatus(loaded, "plan", "Write and independently review a requirement-mapped implementation plan.");
  const plan = validatePlan(loaded);
  if (plan.findings.length > 0) return phaseStatus(loaded, "repair-plan", "Correct plan coverage or structure before execution.", plan.findings);
  const execute = validateExecute(loaded);
  if (execute.findings.length > 0) return phaseStatus(loaded, "review-plan", "Complete independent plan review and mark every executable plan Accepted or Approved.", execute.findings);
  if (loaded.contents.validation.length === 0) return phaseStatus(loaded, "execute-and-verify", "Execute dependency-ready tasks with review loops, then record validation evidence.");
  const trace = traceLoaded(loaded);
  if (trace.findings.length > 0) return phaseStatus(loaded, "verify", "Close requirement evidence gaps and rerun traceability.", trace.findings);
  if (!loaded.contents.audit) return phaseStatus(loaded, "audit", "Run the independent requirement, integration, and regression audit.");
  if (!loaded.contents.summary) return phaseStatus(loaded, "handoff", "Write the completion summary and durable handoff.");
  const complete = validateComplete(loaded);
  if (complete.findings.length > 0) return phaseStatus(loaded, "repair-closure", "Resolve closure findings before claiming completion.", complete.findings);
  return phaseStatus(loaded, "complete", "No workflow action remains for this phase.");
}

function phaseStatus(loaded, status, nextAction, findings = []) {
  return { phase: loaded.phase.name, status, nextAction, findings };
}

async function statusCommand(options, command) {
  if (!await exists(options.project)) {
    throw new WorkflowError("PROJECT_NOT_FOUND", `Project directory not found: ${options.project}`);
  }
  const state = await determineStatus(options);
  return {
    ok: !state.findings?.some((item) => item.severity === "error") || [
      "research", "re-discuss", "repair-spec", "repair-plan", "review-plan", "verify", "repair-closure"
    ].includes(state.status),
    command,
    project: options.project,
    phase: state.phase ?? null,
    status: state.status,
    nextAction: state.nextAction,
    findings: state.findings ?? []
  };
}

function usage() {
  return `AImagician workflow runtime

Usage:
  node scripts/workflow.mjs init [--project PATH] [--phase ID] [--risk LEVEL] [--extensions ui,ai,security-ops] [--write] [--format text|json]
  node scripts/workflow.mjs status [--project PATH] [--phase ID] [--format text|json]
  node scripts/workflow.mjs next [--project PATH] [--phase ID] [--format text|json]
  node scripts/workflow.mjs validate --gate spec|plan|execute|complete [--project PATH] [--phase ID] [--format text|json]
  node scripts/workflow.mjs trace [--project PATH] [--phase ID] [--format text|json]

Gate semantics:
  spec      Locked requirements, sections, scores, boundaries, and ambiguity
  plan      Specification validity, plan structure, and requirement mapping
  execute   Plan gate plus completed research, discussion, context, and plan acceptance
  complete  Execute gate plus passing evidence, UAT when needed, audit, and summary

init previews by default. Add --write to create missing files; existing files are never overwritten.`;
}

function renderText(result) {
  if (result.command === "help") return result.usage;
  const lines = [`Workflow ${result.command}`, `Project: ${result.project}`];
  if (result.phase) lines.push(`Phase: ${result.phase}`);
  if (result.mode) lines.push(`Mode: ${result.mode}`);
  if (result.gate) lines.push(`Gate: ${result.gate}`);
  if (result.status) lines.push(`Status: ${result.status}`);
  if (result.nextAction) lines.push(`Next: ${result.nextAction}`);
  if (result.planned) {
    lines.push(`Planned: ${result.planned.length}`);
    for (const path of result.planned) lines.push(`  + ${path}`);
    lines.push(`Skipped existing: ${result.skipped.length}`);
    for (const path of result.skipped) lines.push(`  = ${path}`);
  }
  if (result.items) {
    lines.push("Trace:");
    for (const item of result.items) {
      lines.push(`  ${item.id}: planned=${item.planned ? "yes" : "no"}, evidence=${item.evidenceStatus}`);
    }
  }
  if (result.findings?.length) {
    lines.push("Findings:");
    for (const item of result.findings) {
      const location = [item.artifact, item.requirement].filter(Boolean).join(":");
      lines.push(`  [${item.code}]${location ? ` ${location}` : ""} ${item.message}`);
    }
  }
  return lines.join("\n");
}

export async function runWorkflow(argv) {
  const options = parseArgs(argv);
  if (options.command === "help") return { ok: true, command: "help", usage: usage(), findings: [] };
  if (options.command === "init") return initArtifacts(options);
  if (options.command === "validate") return validateCommand(options);
  if (options.command === "trace") return traceCommand(options);
  if (options.command === "status" || options.command === "next") return statusCommand(options, options.command);
  throw new WorkflowError("USAGE_UNKNOWN_COMMAND", `Unknown command: ${options.command}`);
}

export async function main(argv = process.argv.slice(2)) {
  let format = argv.includes("--format") ? argv[argv.indexOf("--format") + 1] : "text";
  if (!FORMATS.has(format)) format = "text";
  try {
    const result = await runWorkflow(argv);
    process.stdout.write(`${format === "json" ? JSON.stringify(result, null, 2) : renderText(result)}\n`);
    if (!result.ok) process.exitCode = 1;
  } catch (error) {
    const code = error instanceof WorkflowError ? error.code : "RUNTIME_ERROR";
    const message = error instanceof Error ? error.message : String(error);
    const result = { ok: false, command: argv[0] ?? "help", findings: [finding(code, message)] };
    process.stdout.write(`${format === "json" ? JSON.stringify(result, null, 2) : renderText(result)}\n`);
    process.exitCode = 2;
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  await main();
}
