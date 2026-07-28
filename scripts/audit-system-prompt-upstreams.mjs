#!/usr/bin/env node

import { access, readdir } from "node:fs/promises";
import { resolve } from "node:path";
import { execFileSync } from "node:child_process";

const BASELINES = {
  sourceSkills: "252cd5251641ea0f3bb67878a684785651ccd09d",
  promptCorpus: "87578587f873183f90dc8205d665527d5e4ee560"
};

const EXPECTED_SKILLS = [
  "agent-delegation",
  "citation-system",
  "code-engineering",
  "context-management",
  "conversation-flow",
  "injection-defense",
  "memory-system",
  "mobile-adaptation",
  "output-formatting",
  "persona-design",
  "personality-system",
  "safety-guardrails",
  "search-integration",
  "tool-specification",
  "voice-optimization"
];

function gitHead(path) {
  return execFileSync("git", ["-C", path, "rev-parse", "HEAD"], { encoding: "utf8" }).trim();
}

async function directories(path, requiredFile) {
  const entries = (await readdir(path, { withFileTypes: true }))
    .filter((entry) => entry.isDirectory() && entry.name !== ".git")
    .map((entry) => entry.name)
    .sort();
  if (!requiredFile) return entries;

  const matched = [];
  for (const entry of entries) {
    try {
      await access(resolve(path, entry, requiredFile));
      matched.push(entry);
    } catch {
      // Non-skill working directories are intentionally excluded.
    }
  }
  return matched;
}

function symmetricDifference(left, right) {
  const leftSet = new Set(left);
  const rightSet = new Set(right);
  return [
    ...left.filter((value) => !rightSet.has(value)).map((value) => ({ kind: "unexpected", value })),
    ...right.filter((value) => !leftSet.has(value)).map((value) => ({ kind: "missing", value }))
  ];
}

const args = new Set(process.argv.slice(2));
const root = resolve(process.cwd(), ".planning", "references");
const sourceSkills = resolve(root, "system-prompt-skills");
const promptCorpus = resolve(root, "system_prompts_leaks");

try {
  const sourceSkillsHead = gitHead(sourceSkills);
  const promptCorpusHead = gitHead(promptCorpus);
  const sourceSkillDirs = await directories(sourceSkills, "SKILL.md");
  const corpusGroups = await directories(promptCorpus);
  const capabilityDelta = symmetricDifference(sourceSkillDirs, EXPECTED_SKILLS);
  const shaChanged =
    sourceSkillsHead !== BASELINES.sourceSkills ||
    promptCorpusHead !== BASELINES.promptCorpus;
  const status = capabilityDelta.length > 0 || shaChanged ? "review-required" : "baseline-match";
  const result = {
    schemaVersion: 1,
    status,
    sources: {
      sourceSkills: { head: sourceSkillsHead, baseline: BASELINES.sourceSkills, skills: sourceSkillDirs },
      promptCorpus: { head: promptCorpusHead, baseline: BASELINES.promptCorpus, groups: corpusGroups }
    },
    capabilityDelta,
    action: status === "baseline-match"
      ? "No upstream capability review is required."
      : "Review changed source commits and capability paths; do not mutate owned skills automatically."
  };

  if (args.has("--json")) {
    process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
  } else {
    process.stdout.write([
      `Status: ${result.status}`,
      `Source skills: ${sourceSkillsHead} (${sourceSkillDirs.length} capabilities)`,
      `Prompt corpus: ${promptCorpusHead} (${corpusGroups.length} top-level groups)`,
      `Capability delta: ${capabilityDelta.length}`,
      `Action: ${result.action}`
    ].join("\n") + "\n");
  }
  if (status !== "baseline-match") process.exitCode = 3;
} catch (error) {
  const message = error instanceof Error ? error.message : "Unknown upstream audit error";
  if (args.has("--json")) {
    process.stdout.write(`${JSON.stringify({
      schemaVersion: 1,
      status: "error",
      errors: [{ code: "upstream-unavailable", message }]
    }, null, 2)}\n`);
  } else {
    process.stderr.write(`${message}\n`);
  }
  process.exitCode = 2;
}
