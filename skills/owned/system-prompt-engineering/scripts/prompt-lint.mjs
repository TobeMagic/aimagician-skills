#!/usr/bin/env node

import { readFile } from "node:fs/promises";

const BASE_SECTIONS = [
  ["objective", /(^|\n)#{1,3}\s+(objective|goal)\b/i],
  ["authority", /(^|\n)#{1,3}\s+.*(authority|instruction hierarchy|trust hierarchy)/i],
  ["workflow", /(^|\n)#{1,3}\s+.*(workflow|operating|behavior|decision)/i],
  ["safety", /(^|\n)#{1,3}\s+.*(safety|privacy|trust|security)/i],
  ["output", /(^|\n)#{1,3}\s+.*(output|response|format)/i],
  ["failure", /(^|\n)#{1,3}\s+.*(failure|fallback|escalation|stop condition)/i],
  ["evaluation", /(^|\n)#{1,3}\s+.*(evaluation|self-check|verification|completion)/i]
];

const SENSITIVE_PATTERNS = [
  ["credential-assignment", /\b(api[_ -]?key|access[_ -]?token|secret|password)\s*[:=]\s*[^\s<{][^\s]*/gi],
  ["private-key", /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/g]
];

function parseArgs(argv) {
  const json = argv.includes("--json");
  const positional = argv.filter((arg) => arg !== "--json");
  if (positional.length !== 1) {
    throw new Error("Usage: node prompt-lint.mjs <system-prompt.md> [--json]");
  }
  return { path: positional[0], json };
}

function lineForIndex(content, index) {
  return content.slice(0, index).split(/\r?\n/).length;
}

function lint(content) {
  const issues = [];
  for (const [section, pattern] of BASE_SECTIONS) {
    if (!pattern.test(content)) {
      issues.push({ severity: "error", code: `missing-${section}`, message: `Missing ${section} contract.` });
    }
  }

  const conditional = [
    {
      active: /\b(tool|function call|action|browser|shell|api)\b/i.test(content),
      ok: /\b(permission|confirm|read-only|prohibited|side effect)\b/i.test(content),
      code: "missing-tool-permissions",
      message: "Tool-capable prompt does not define permissions or side effects."
    },
    {
      active: /\b(memory|remember|persistent|retention)\b/i.test(content),
      ok: /\b(delete|deletion|forget|correct|correction)\b/i.test(content),
      code: "missing-memory-control",
      message: "Memory-capable prompt does not define correction or deletion."
    },
    {
      active: /\b(search|browse|retriev|research)\b/i.test(content),
      ok: /\b(citation|cite|source|ground)\b/i.test(content),
      code: "missing-grounding",
      message: "Search-capable prompt does not define sources or citations."
    },
    {
      active: /\b(delegate|subagent|worker|multi-agent)\b/i.test(content),
      ok: /\b(scope|allowed|forbidden|validate|review)\b/i.test(content),
      code: "missing-delegation-boundary",
      message: "Delegation-capable prompt does not define scope or result validation."
    }
  ];

  for (const check of conditional) {
    if (check.active && !check.ok) {
      issues.push({ severity: "error", code: check.code, message: check.message });
    }
  }

  for (const [code, pattern] of SENSITIVE_PATTERNS) {
    for (const match of content.matchAll(pattern)) {
      issues.push({
        severity: "error",
        code,
        message: "Possible embedded credential or private key; inspect without printing the value.",
        line: lineForIndex(content, match.index ?? 0)
      });
    }
  }

  if (content.length > 30000) {
    issues.push({
      severity: "warning",
      code: "large-stable-prompt",
      message: "Stable prompt exceeds 30,000 characters; consider progressive disclosure."
    });
  }

  return issues.sort((left, right) =>
    left.severity.localeCompare(right.severity) ||
    left.code.localeCompare(right.code) ||
    (left.line ?? 0) - (right.line ?? 0)
  );
}

function renderText(path, issues) {
  const errors = issues.filter((issue) => issue.severity === "error").length;
  const warnings = issues.filter((issue) => issue.severity === "warning").length;
  return [
    `Prompt: ${path}`,
    `Status: ${errors > 0 ? "invalid" : "valid"}`,
    `Errors: ${errors}`,
    `Warnings: ${warnings}`,
    ...issues.map((issue) =>
      `${issue.severity.toUpperCase()} ${issue.code}${issue.line ? ` line ${issue.line}` : ""}: ${issue.message}`
    )
  ].join("\n");
}

try {
  const options = parseArgs(process.argv.slice(2));
  const content = await readFile(options.path, "utf8");
  const issues = lint(content);
  const result = {
    schemaVersion: 1,
    path: options.path,
    status: issues.some((issue) => issue.severity === "error") ? "invalid" : "valid",
    issues
  };
  process.stdout.write(`${options.json ? JSON.stringify(result, null, 2) : renderText(options.path, issues)}\n`);
  if (result.status === "invalid") process.exitCode = 1;
} catch (error) {
  process.stderr.write(`${error instanceof Error ? error.message : "Unknown lint error"}\n`);
  process.exitCode = 2;
}

