#!/usr/bin/env node

const KINDS = {
  analysis: {
    focus: "Map the current system before choosing implementation locations.",
    stages: ["recover-context", "trace-representative-flow", "map-boundaries", "assess-blast-radius", "resolve-unknowns"],
    artifacts: ["engineering-context-map"],
    checks: ["facts-have-evidence", "data-and-control-flow-explained", "critical-claims-spot-checked"]
  },
  discovery: {
    focus: "Advance a large uncertain objective one evidence-producing frontier at a time.",
    stages: ["destination-and-non-goals", "known-decisions-and-vocabulary", "map-frontier-and-fog", "smallest-distinguishing-probe", "update-discovery-map", "next-bounded-slice"],
    artifacts: ["progressive-discovery-map", "engineering-context-map"],
    checks: ["unknowns-are-explicit", "next-probe-is-bounded", "critical-claims-spot-checked", "no-plan-through-fog"]
  },
  feature: {
    focus: "Deliver observable behavior through a narrow end-to-end slice.",
    stages: ["behavior-contract", "context-map", "design-options", "tracer-slice", "boundary-cases", "integration-verification"],
    artifacts: ["engineering-context-map", "engineering-design-record", "engineering-change-brief"],
    checks: ["test-seams-defined", "compatibility-reviewed", "normal-failure-recovery-covered"]
  },
  bug: {
    focus: "Prove and repair the earliest controllable root cause.",
    stages: ["feedback-loop", "minimal-reproduction", "ranked-hypotheses", "instrument", "root-cause-fix", "regression-and-cleanup"],
    artifacts: ["engineering-context-map", "engineering-change-brief"],
    checks: ["reproduction-goes-red", "probe-distinguishes-hypotheses", "temporary-instrumentation-removed"]
  },
  refactor: {
    focus: "Improve structure while preserving observable behavior.",
    stages: ["behavior-baseline", "dependency-map", "target-design", "expand-contract", "consumer-migration", "old-path-removal"],
    artifacts: ["engineering-context-map", "engineering-design-record", "engineering-change-brief"],
    checks: ["characterization-tests-pass", "compatibility-window-owned", "semantic-and-mechanical-changes-reviewable"]
  },
  performance: {
    focus: "Optimize a measured bottleneck without weakening correctness.",
    stages: ["workload-and-budget", "baseline", "bottleneck-proof", "bounded-change", "equivalent-benchmark", "regression-signal"],
    artifacts: ["engineering-context-map", "engineering-design-record", "engineering-change-brief"],
    checks: ["equivalent-runs-compared", "correctness-under-load", "repeatable-measurement"]
  },
  architecture: {
    focus: "Change ownership or dependency direction through a reversible migration.",
    stages: ["domain-model", "current-constraint", "design-twice", "migration-plan", "tracer-migration", "rollout-and-old-path-removal"],
    artifacts: ["engineering-context-map", "engineering-design-record", "engineering-change-brief"],
    checks: ["no-change-option-compared", "data-compatibility-defined", "rollback-and-observability-defined"]
  },
  prototype: {
    focus: "Resolve one material uncertainty with a disposable, runnable experiment.",
    stages: ["falsifiable-uncertainty", "choose-prototype-type", "define-evidence-stop", "build-runnable-probe", "exercise-representative-and-failure-cases", "promote-revise-discard"],
    artifacts: ["engineering-prototype-brief"],
    checks: ["single-uncertainty", "one-command-runnable", "no-hidden-production-coupling", "verdict-has-evidence"]
  }
};

const RISKS = new Set(["low", "medium", "high"]);
const FORMATS = new Set(["text", "json"]);

function usage() {
  return [
    "Usage: engineering-route.mjs --kind <analysis|discovery|feature|bug|refactor|performance|architecture|prototype> [--risk low|medium|high] [--format text|json]",
    "",
    "Returns a read-only engineering route. It never edits the project."
  ].join("\n");
}

function parseArgs(argv) {
  const options = { kind: undefined, risk: "medium", format: "text" };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") return { ...options, help: true };
    if (!["--kind", "--risk", "--format"].includes(token)) throw new Error(`Unknown option: ${token}`);
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`${token} requires a value`);
    index += 1;
    if (token === "--kind") options.kind = value;
    if (token === "--risk") options.risk = value;
    if (token === "--format") options.format = value;
  }
  if (!options.kind) throw new Error("--kind is required");
  if (!KINDS[options.kind]) throw new Error(`Unsupported kind: ${options.kind}`);
  if (!RISKS.has(options.risk)) throw new Error(`Unsupported risk: ${options.risk}`);
  if (!FORMATS.has(options.format)) throw new Error(`Unsupported format: ${options.format}`);
  return options;
}

function buildRoute(options) {
  const route = KINDS[options.kind];
  const independentReview = options.risk === "low"
    ? ["specification-and-quality-self-check"]
    : options.risk === "medium"
      ? ["fresh-specification-review", "fresh-quality-review"]
      : ["fresh-specification-review", "fresh-quality-review", "specialist-risk-review"];

  return {
    kind: options.kind,
    risk: options.risk,
    focus: route.focus,
    stages: route.stages,
    artifacts: route.artifacts,
    checks: route.checks,
    review_axes: [
      "specification-compliance",
      "engineering-standards-compliance",
      "correctness-and-edge-cases",
      "tests-and-determinism",
      "security-and-data",
      "maintainability-and-locality",
      "performance-and-operability",
      "diff-hygiene"
    ],
    review_passes: ["specification-compliance", "engineering-standards"],
    independent_review: independentReview,
    completion: "Every accepted requirement has fresh passing evidence; failures, skipped checks, and residual risk are explicit."
  };
}

function renderText(route) {
  const lines = [
    `Engineering route: ${route.kind} (${route.risk})`,
    `Focus: ${route.focus}`,
    "Stages:"
  ];
  route.stages.forEach((stage, index) => lines.push(`${index + 1}. ${stage}`));
  lines.push(`Artifacts: ${route.artifacts.join(", ")}`);
  lines.push(`Checks: ${route.checks.join(", ")}`);
  lines.push(`Independent review: ${route.independent_review.join(", ")}`);
  lines.push(`Completion: ${route.completion}`);
  return lines.join("\n");
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    process.stdout.write(`${usage()}\n`);
  } else {
    const route = buildRoute(options);
    process.stdout.write(options.format === "json" ? `${JSON.stringify(route, null, 2)}\n` : `${renderText(route)}\n`);
  }
} catch (error) {
  process.stderr.write(`${error.message}\n\n${usage()}\n`);
  process.exitCode = 2;
}
