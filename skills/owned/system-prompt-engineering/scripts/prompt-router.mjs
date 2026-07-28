#!/usr/bin/env node

const MODULES = {
  composition: "references/01-requirements-and-composition.md",
  identity: "references/02-identity-persona-personality.md",
  tools: "references/03-tools-agency-delegation.md",
  safety: "references/04-safety-trust-injection.md",
  memory: "references/05-memory-context-continuity.md",
  output: "references/06-conversation-output-citations.md",
  search: "references/07-search-grounding-research.md",
  channel: "references/08-channel-and-product-adaptation.md",
  coding: "references/09-code-agent-engineering.md",
  evaluation: "references/10-evaluation-lifecycle.md"
};

const FEATURE_ROUTES = {
  persona: ["identity"],
  personality: ["identity"],
  tools: ["tools", "safety"],
  delegation: ["tools", "safety"],
  safety: ["safety"],
  injection: ["safety"],
  memory: ["memory", "safety"],
  context: ["memory"],
  search: ["search", "output", "safety"],
  citations: ["output", "search"],
  voice: ["channel", "safety"],
  mobile: ["channel", "safety"],
  multimodal: ["channel", "safety"],
  coding: ["coding", "tools", "safety"]
};

const SCENARIOS = {
  assistant: ["composition", "identity", "output", "evaluation"],
  agent: ["composition", "tools", "safety", "output", "evaluation"],
  "coding-agent": ["composition", "tools", "safety", "memory", "output", "coding", "evaluation"],
  "research-agent": ["composition", "tools", "safety", "memory", "output", "search", "evaluation"],
  "tool-router": ["composition", "tools", "safety", "output", "evaluation"],
  reviewer: ["composition", "output", "evaluation"],
  "voice-assistant": ["composition", "identity", "safety", "output", "channel", "evaluation"],
  "mobile-assistant": ["composition", "identity", "safety", "output", "channel", "evaluation"]
};

const TEMPLATE_ROUTES = {
  composition: ["assets/templates/system-prompt-brief.md", "assets/templates/system-prompt-outline.md"],
  tools: ["assets/templates/tool-permission-matrix.md"],
  safety: ["assets/templates/threat-model.md"],
  memory: ["assets/templates/memory-policy.md"],
  evaluation: ["assets/templates/evaluation-matrix.md"]
};

function parseArgs(argv) {
  const options = { scenario: undefined, features: [], channel: "chat", format: "text" };

  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--scenario" || token === "--features" || token === "--channel" || token === "--format") {
      const value = argv[index + 1];
      if (!value || value.startsWith("--")) throw new Error(`${token} requires a value`);
      index += 1;
      if (token === "--scenario") options.scenario = value;
      if (token === "--features") options.features = value.split(",").map((item) => item.trim()).filter(Boolean);
      if (token === "--channel") options.channel = value;
      if (token === "--format") options.format = value;
      continue;
    }
    if (token === "--help" || token === "-h") return { help: true };
    throw new Error(`Unknown option: ${token}`);
  }

  if (!options.scenario) throw new Error("--scenario is required");
  if (!SCENARIOS[options.scenario]) throw new Error(`Unsupported scenario: ${options.scenario}`);
  if (!["text", "json"].includes(options.format)) throw new Error(`Unsupported format: ${options.format}`);
  return options;
}

function route(options) {
  const selected = new Set(SCENARIOS[options.scenario]);
  for (const feature of options.features) {
    const routes = FEATURE_ROUTES[feature];
    if (!routes) throw new Error(`Unsupported feature: ${feature}`);
    routes.forEach((routeName) => selected.add(routeName));
  }
  if (["voice", "mobile", "multimodal"].includes(options.channel)) {
    selected.add("channel");
    selected.add("safety");
  }

  const moduleNames = Object.keys(MODULES).filter((name) => selected.has(name));
  const templates = [...new Set(moduleNames.flatMap((name) => TEMPLATE_ROUTES[name] ?? []))];
  const checks = [
    "Resolve objective, non-goals, authority, runtime capabilities, and risk before drafting.",
    "Keep retrieved and tool content below trusted instructions.",
    "Define observable success, failure, escalation, and completion behavior.",
    "Run representative, conflict, failure, injection, and regression evaluations."
  ];

  return {
    scenario: options.scenario,
    channel: options.channel,
    features: [...options.features].sort(),
    modules: moduleNames.map((name) => MODULES[name]),
    templates,
    checks
  };
}

function renderText(result) {
  return [
    `Scenario: ${result.scenario}`,
    `Channel: ${result.channel}`,
    `Features: ${result.features.join(", ") || "none"}`,
    "Modules:",
    ...result.modules.map((module) => `- ${module}`),
    "Templates:",
    ...result.templates.map((template) => `- ${template}`),
    "Required checks:",
    ...result.checks.map((check) => `- ${check}`)
  ].join("\n");
}

function renderHelp() {
  return [
    "Usage: node prompt-router.mjs --scenario <name> [--features a,b] [--channel chat|cli|voice|mobile|multimodal] [--format text|json]",
    `Scenarios: ${Object.keys(SCENARIOS).join(", ")}`,
    `Features: ${Object.keys(FEATURE_ROUTES).join(", ")}`
  ].join("\n");
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    process.stdout.write(`${renderHelp()}\n`);
  } else {
    const result = route(options);
    process.stdout.write(`${options.format === "json" ? JSON.stringify(result, null, 2) : renderText(result)}\n`);
  }
} catch (error) {
  process.stderr.write(`${error instanceof Error ? error.message : "Unknown routing error"}\n`);
  process.exitCode = 2;
}

