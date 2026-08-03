#!/usr/bin/env node

import { existsSync, readFileSync, statSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

function usage() {
  return `Usage:
  node audit-skill.mjs --skill <skill-dir-or-SKILL.md> [--effect-score 0-10] [--format text|json]

Static audit:
  Scores dimensions 1-7 and 9. Dimension 8 remains NOT_RUN unless
  --effect-score is supplied from a controlled behavioral evaluation.

The command is read-only. It never modifies files, Git state, or installs.`;
}

function parseArgs(argv) {
  const args = { format: "text" };
  for (let i = 0; i < argv.length; i += 1) {
    const value = argv[i];
    if (value === "--help" || value === "-h") args.help = true;
    else if (value === "--skill") args.skill = argv[++i];
    else if (value === "--effect-score") args.effectScore = Number(argv[++i]);
    else if (value === "--format") args.format = argv[++i];
    else throw new Error(`Unknown argument: ${value}`);
  }
  if (!args.help && !args.skill) throw new Error("--skill is required");
  if (!["text", "json"].includes(args.format)) throw new Error("--format must be text or json");
  if (args.effectScore !== undefined && (!Number.isFinite(args.effectScore) || args.effectScore < 0 || args.effectScore > 10)) {
    throw new Error("--effect-score must be a number from 0 to 10");
  }
  return args;
}

function frontmatter(content) {
  const match = content.match(/^---\s*\n([\s\S]*?)\n---\s*\n/);
  if (!match) return { raw: "", values: {} };
  const values = {};
  for (const line of match[1].split("\n")) {
    const field = line.match(/^([a-zA-Z_][\w-]*):\s*(.*)$/);
    if (field) values[field[1]] = field[2].trim();
  }
  return { raw: match[1], values };
}

function clamp(value) {
  return Math.max(0, Math.min(10, Math.round(value)));
}

function dimension(id, name, weight, score, evidence) {
  return { id, name, weight, score: clamp(score), evidence };
}

function referencedPaths(content) {
  const found = new Set();
  const pattern = /(?:^|[`( ])((?:references|scripts|assets|evals)\/[A-Za-z0-9_./-]+\.[A-Za-z0-9_-]+)(?=$|[`) ,:])/gm;
  for (const match of content.matchAll(pattern)) found.add(match[1]);
  return [...found];
}

function audit(skillArg, effectScore) {
  const supplied = resolve(skillArg);
  const skillFile = statSync(supplied).isDirectory() ? join(supplied, "SKILL.md") : supplied;
  if (!existsSync(skillFile)) throw new Error(`SKILL.md not found: ${skillFile}`);
  const root = dirname(skillFile);
  const content = readFileSync(skillFile, "utf8");
  const fm = frontmatter(content);
  const headings = [...content.matchAll(/^#{2,3}\s+.+$/gm)].map((match) => match[0]);
  const refs = referencedPaths(content);
  const missing = refs.filter((path) => !existsSync(join(root, path)));
  const lines = content.split("\n").length;

  const triggerSignals = /(Use when|Use for|Trigger for|触发)/i.test(fm.values.description || "");
  const nonTriggerSignals = /(Do not use|Route|不适用)/i.test(`${fm.values.description || ""}\n${content}`);
  const requiredFrontmatter = ["name", "description", "category", "subcategory", "tags"];
  const frontmatterFields = requiredFrontmatter.filter((key) => fm.raw.includes(`${key}:`)).length;

  const dimensions = [
    dimension(1, "frontmatter_trigger", 7,
      frontmatterFields * 1.4 + (triggerSignals ? 2 : 0) + (nonTriggerSignals ? 1 : 0),
      `${frontmatterFields}/${requiredFrontmatter.length} required fields; trigger=${triggerSignals}; non_trigger=${nonTriggerSignals}`),
    dimension(2, "workflow_clarity", 12,
      3 + Math.min(4, (content.match(/^###\s+\d+\.?/gm) || []).length) + (/Inputs?|Outputs?|Completion Contract/i.test(content) ? 2 : 0) + (/Workflow|Pipeline|Loop/i.test(content) ? 1 : 0),
      `${(content.match(/^###\s+\d+\.?/gm) || []).length} numbered stages; explicit contract=${/Inputs?|Outputs?|Completion Contract/i.test(content)}`),
    dimension(3, "failure_modes", 12,
      (/Failure Handling|Failure Modes/i.test(content) ? 4 : 0) + (/\|\s*Trigger\s*\|[\s\S]*\|\s*Fallback\s*\|/i.test(content) ? 4 : 0) + (/\b(if|when)\b[\s\S]{0,160}\b(fallback|stop|restore|route|retry)\b/i.test(content) ? 2 : 0),
      `failure_section=${/Failure Handling|Failure Modes/i.test(content)}; three-part branch=${/\|\s*Trigger\s*\|[\s\S]*\|\s*Fallback\s*\|/i.test(content)}`),
    dimension(4, "checkpoints", 6,
      Math.min(10, (content.match(/\bCHECKPOINT\b/g) || []).length * 3 + (/\b(confirm|confirmation|approval|acceptance)\b/i.test(content) ? 2 : 0)),
      `${(content.match(/\bCHECKPOINT\b/g) || []).length} explicit checkpoints`),
    dimension(5, "actionable_specificity", 18,
      2 + Math.min(3, (content.match(/```(?:bash|json|text|yaml)?/g) || []).length) + Math.min(3, (content.match(/^\d+\.\s+/gm) || []).length / 3) + (/--[a-z][\w-]+|<[\w-]+>|\.json|\.md/i.test(content) ? 2 : 0),
      `${(content.match(/```(?:bash|json|text|yaml)?/g) || []).length} code blocks; ${(content.match(/^\d+\.\s+/gm) || []).length} ordered actions`),
    dimension(6, "resource_integration", 4,
      refs.length === 0 ? 5 : (missing.length === 0 ? 10 : Math.max(0, 10 - missing.length * 3)),
      `${refs.length} referenced resources; missing=${missing.length}`),
    dimension(7, "architecture_clarity", 12,
      3 + Math.min(3, headings.length / 3) + (nonTriggerSignals ? 2 : 0) + (lines <= 450 ? 2 : lines <= 650 ? 1 : 0),
      `${headings.length} section headings; ${lines} lines; sibling boundary=${nonTriggerSignals}`),
    dimension(8, "real_task_effectiveness", 23,
      effectScore === undefined ? 0 : effectScore,
      effectScore === undefined ? "NOT_RUN: provide --effect-score only after controlled behavioral evaluation" : "Externally supplied controlled evaluation score"),
    dimension(9, "anti_patterns_guardrails", 6,
      (/Prohibited Actions|Guardrails|Anti-pattern|Do not/i.test(content) ? 5 : 0) + Math.min(5, (content.match(/\b(Do not|Never|禁止|不得)\b/gi) || []).length),
      `${(content.match(/\b(Do not|Never|禁止|不得)\b/gi) || []).length} explicit prohibitions`)
  ];

  const staticWeighted = dimensions
    .filter((item) => item.id !== 8)
    .reduce((sum, item) => sum + item.score * item.weight / 10, 0);
  const total = effectScore === undefined
    ? null
    : Number((staticWeighted + dimensions[7].score * dimensions[7].weight / 10).toFixed(1));

  return {
    skill_file: skillFile,
    status: missing.length ? "fail" : effectScore === undefined ? "static_only" : "complete",
    dimensions,
    static_weighted_score: Number(staticWeighted.toFixed(1)),
    total_score: total,
    effectiveness: effectScore === undefined ? "NOT_RUN" : "SUPPLIED",
    referenced_resources: refs,
    missing_resources: missing
  };
}

try {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) {
    console.log(usage());
    process.exit(0);
  }
  const result = audit(args.skill, args.effectScore);
  if (args.format === "json") {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log(`Skill: ${result.skill_file}`);
    for (const item of result.dimensions) {
      const score = item.id === 8 && result.effectiveness === "NOT_RUN" ? "NOT_RUN" : `${item.score}/10`;
      console.log(`${item.id}. ${item.name}: ${score} (weight ${item.weight})`);
      console.log(`   ${item.evidence}`);
    }
    console.log(`Static weighted score: ${result.static_weighted_score}/77`);
    console.log(`Total score: ${result.total_score ?? "NOT_RUN"}`);
    if (result.missing_resources.length) console.log(`Missing resources: ${result.missing_resources.join(", ")}`);
  }
  process.exitCode = result.missing_resources.length ? 1 : 0;
} catch (error) {
  console.error(error.message);
  console.error(usage());
  process.exitCode = 2;
}
