import { execFileSync } from "node:child_process";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const ownedRoot = join(process.cwd(), "skills", "owned");
const engineeringRoot = join(ownedRoot, "aimagician-superpower");
const designRoot = join(ownedRoot, "interface-design");
const engineeringRouter = join(engineeringRoot, "scripts", "engineering-route.mjs");
const designRouter = join(designRoot, "scripts", "design-router.mjs");

describe("expert engineering capability architecture", () => {
  it("routes every engineering task type through task-specific methods and risk-scaled review", () => {
    const expectedStages: Record<string, string> = {
      analysis: "trace-representative-flow",
      discovery: "smallest-distinguishing-probe",
      feature: "tracer-slice",
      bug: "ranked-hypotheses",
      refactor: "expand-contract",
      performance: "bottleneck-proof",
      architecture: "design-twice",
      prototype: "build-runnable-probe"
    };

    for (const [kind, expectedStage] of Object.entries(expectedStages)) {
      const route = runJson(engineeringRouter, ["--kind", kind, "--risk", "high", "--format", "json"]);
      expect(route).toMatchObject({ kind, risk: "high" });
      expect(route.stages).toContain(expectedStage);
      expect(route.review_axes).toEqual(expect.arrayContaining([
        "specification-compliance",
        "engineering-standards-compliance",
        "correctness-and-edge-cases",
        "tests-and-determinism",
        "security-and-data",
        "maintainability-and-locality",
        "performance-and-operability"
      ]));
      expect(route.independent_review).toContain("specialist-risk-review");
      expect(route.review_passes).toEqual(["specification-compliance", "engineering-standards"]);
    }
  });

  it("exposes progressive engineering modules, durable artifacts, and behavior scenarios", async () => {
    const skill = await readFile(join(engineeringRoot, "SKILL.md"), "utf8");
    const modulePaths = [
      "references/capabilities/engineering-exploration.md",
      "references/capabilities/prototyping-and-progressive-discovery.md",
      "references/capabilities/engineering-design.md",
      "references/capabilities/engineering-delivery.md",
      "references/capabilities/engineering-review.md"
    ];
    const templatePaths = [
      "assets/templates/engineering-context-map.md",
      "assets/templates/engineering-design-record.md",
      "assets/templates/engineering-change-brief.md",
      "assets/templates/engineering-review.md",
      "assets/templates/engineering-prototype-brief.md",
      "assets/templates/progressive-discovery-map.md"
    ];

    for (const path of [...modulePaths, ...templatePaths]) {
      expect(skill).toContain(path);
      expect((await readFile(join(engineeringRoot, path), "utf8")).trim().length).toBeGreaterThan(200);
    }

    const modules = (await Promise.all(modulePaths.map((path) => readFile(join(engineeringRoot, path), "utf8")))).join("\n");
    expect(modules).toContain("representative happy path");
    expect(modules).toContain("Design at least two materially different solutions");
    expect(modules).toContain("tracer slice");
    expect(modules).toContain("expand-contract");
    expect(modules).toContain("Specification Compliance");
    expect(modules).toContain("Progressive Discovery Map");
    expect(modules).toContain("highest observable practical seam");

    const evals = JSON.parse(await readFile(join(engineeringRoot, "evals", "evals.json"), "utf8")) as EvalFile;
    expect(evals.scenarios.map((scenario) => scenario.id)).toEqual(expect.arrayContaining([
      "engineering-codebase-analysis",
      "engineering-feature-development",
      "engineering-root-cause-fix",
      "engineering-wide-refactor",
      "progressive-discovery-frontier",
      "bounded-engineering-prototype"
    ]));
  });
});

describe("HTML universal design capability architecture", () => {
  it("keeps every decision-rule reference resolvable and every id unique", async () => {
    const layouts = await readPatternFile("layout-patterns.json", "patterns");
    const components = await readPatternFile("component-patterns.json", "components");
    const rules = await readPatternFile("decision-rules.json", "rules") as Array<Pattern & { suggest: { layouts: string[]; components: string[] } }>;
    const checks = await readPatternFile("quality-checks.json", "checks");

    for (const collection of [layouts, components, rules, checks]) {
      expect(new Set(collection.map((item) => item.id)).size).toBe(collection.length);
    }

    const layoutIds = new Set(layouts.map((item) => item.id));
    const componentIds = new Set(components.map((item) => item.id));
    for (const rule of rules) {
      for (const id of rule.suggest.layouts) expect(layoutIds.has(id)).toBe(true);
      for (const id of rule.suggest.components) expect(componentIds.has(id)).toBe(true);
    }
    expect(layouts.length).toBeGreaterThanOrEqual(12);
    expect(components.length).toBeGreaterThanOrEqual(16);
    expect(checks.filter((check) => check.severity === "blocker").length).toBeGreaterThanOrEqual(4);
    for (const check of checks) {
      expect(check.deliverables).toBeDefined();
      expect(check.deliverables?.length).toBeGreaterThan(0);
      for (const deliverable of check.deliverables ?? []) expect(["html", "image", "video", "hybrid", "pptx"]).toContain(deliverable);
    }
  });

  it("routes landing, dashboard, app prototype, and HTML presentation to browser-native patterns", () => {
    const landing = runDesign(["--task", "landing", "--deliverable", "html", "--signals", "narrative"]);
    expect(landing).toMatchObject({ owners: ["interface-design"], final_owner: "interface-design", mode: "build" });
    expect(landing.suggested_layouts).toContain("product-first-story");

    const dashboard = runDesign(["--task", "dashboard", "--deliverable", "html", "--signals", "trends,comparison,many-records"]);
    expect(dashboard.suggested_layouts).toEqual(expect.arrayContaining(["command-center-dashboard", "metric-to-detail", "split-comparison"]));
    expect(dashboard.suggested_components).toEqual(expect.arrayContaining(["time-series-chart", "comparison-matrix", "data-table"]));
    expect(dashboard.required_quality_checks).toEqual(expect.arrayContaining([expect.objectContaining({ id: "data-integrity", severity: "high" })]));

    const prototype = runDesign(["--task", "app-prototype", "--deliverable", "html"]);
    expect(prototype).toMatchObject({ mode: "prototype" });
    expect(prototype.suggested_layouts).toContain("app-shell-prototype");
    expect(prototype.suggested_components).toContain("prototype-shell");

    const presentation = runDesign(["--task", "html-presentation", "--deliverable", "html"]);
    expect(presentation.suggested_layouts).toContain("html-slide-sequence");
    expect(presentation.suggested_components).toContain("slide-frame");
  });

  it("enforces native PowerPoint and hybrid ownership without browser-workflow leakage", () => {
    const native = runDesign(["--task", "html-presentation", "--deliverable", "pptx", "--platform", "windows"]);
    expect(native).toMatchObject({ owners: ["window-pptx"], final_owner: "window-pptx", handoff: false, mode: "route" });
    expect(native.suggested_layouts).toEqual([]);
    expect(native.suggested_components).toEqual([]);
    expect(native.required_quality_checks.map((check: Pattern) => check.id)).toEqual([
      "artifact-owner",
      "real-content",
      "native-ppt-boundary",
      "evidence-captured"
    ]);
    expect(native.required_quality_checks.map((check: Pattern) => check.id)).not.toContain("browser-opens");

    const hybrid = runDesign(["--task", "html-presentation", "--deliverable", "hybrid", "--platform", "cross-platform"]);
    expect(hybrid).toMatchObject({ owners: ["interface-design", "pptx"], final_owner: "pptx", handoff: true, mode: "prototype" });
    expect(hybrid.boundary).toContain("ppt-handoff.md");
  });

  it("routes repository covers, posters, product video, and creative coding through visual asset gates", () => {
    const cover = runDesign(["--task", "readme-cover", "--deliverable", "image", "--signals", "developer-tool,terminal"]);
    expect(cover).toMatchObject({ owners: ["interface-design"], final_owner: "interface-design", mode: "asset" });
    expect(cover.suggested_layouts).toContain("repository-product-hero");
    expect(cover.suggested_components).toEqual(expect.arrayContaining(["project-wordmark", "terminal-product-proof", "media-fallback"]));
    expect(cover.required_quality_checks).toEqual(expect.arrayContaining([
      expect.objectContaining({ id: "repository-product-proof", severity: "blocker" }),
      expect.objectContaining({ id: "distribution-readability", severity: "high" })
    ]));

    const poster = runDesign(["--task", "poster", "--deliverable", "image"]);
    expect(poster.suggested_layouts).toContain("campaign-poster");

    const video = runDesign(["--task", "product-demo", "--deliverable", "video", "--signals", "workflow,motion"]);
    expect(video.suggested_layouts).toEqual(expect.arrayContaining(["demo-story-sequence", "creative-coding-stage"]));
    expect(video.required_quality_checks).toEqual(expect.arrayContaining([
      expect.objectContaining({ id: "deterministic-time", severity: "blocker" }),
      expect.objectContaining({ id: "static-fallback", severity: "blocker" }),
      expect.objectContaining({ id: "frame-integrity", severity: "high" })
    ]));

    const creative = runDesign(["--task", "creative-coding", "--deliverable", "html"]);
    expect(creative.suggested_layouts).toContain("creative-coding-stage");
  });

  it("routes the main prompt through all design modules and keeps runtime source-neutral", async () => {
    const skill = await readFile(join(designRoot, "SKILL.md"), "utf8");
    const modules = [
      "delivery-routing.md",
      "context-and-direction.md",
      "information-architecture.md",
      "visual-system.md",
      "components-and-interaction.md",
      "prototypes-and-data.md",
      "motion-and-html-presentations.md",
      "brand-and-product-assets.md",
      "repository-branding-and-marketing.md",
      "creative-coding-and-motion-media.md",
      "implementation-and-verification.md"
    ];
    for (const module of modules) {
      const path = `references/capabilities/${module}`;
      expect(skill).toContain(path);
      expect((await readFile(join(designRoot, path), "utf8")).trim().length).toBeGreaterThan(300);
    }

    expect(skill).toContain("HTML Based Universal Design");
    expect(skill).toContain("Brand DESIGN.md Routing");
    expect(skill).toContain("Route native PowerPoint delivery to the PPT skill instead");
    expect(skill).toContain("320, 375, 414, 768");
    expect(skill).toContain("two or three materially different direction previews");

    const coreFiles = [
      "SKILL.md",
      ...modules.map((module) => `references/capabilities/${module}`),
      "scripts/design-router.mjs",
      "evals/evals.json"
    ];
    const content = (await Promise.all(coreFiles.map((path) => readFile(join(designRoot, path), "utf8")))).join("\n");
    for (const forbidden of ["mattpocock", "Hallmark", "Huashu", "Nutlope", "alchaincyf", "github.com/"]) {
      expect(content).not.toContain(forbidden);
    }

    const evals = JSON.parse(await readFile(join(designRoot, "evals", "evals.json"), "utf8")) as EvalFile;
    expect(evals.scenarios.map((scenario) => scenario.id)).toEqual(expect.arrayContaining([
      "premium-product-landing",
      "operational-dashboard",
      "interactive-app-prototype",
      "browser-presentation",
      "native-powerpoint-boundary",
      "hybrid-presentation-handoff",
      "github-readme-cover",
      "marketing-poster",
      "product-demo-video",
      "creative-coding-visual"
    ]));
  });

  it("ships reusable repository and deterministic motion assets", async () => {
    const paths = [
      "assets/templates/brand-spec.md",
      "assets/templates/repository-visual-brief.md",
      "assets/templates/motion-storyboard.md",
      "assets/starter/repository-hero.html",
      "assets/starter/motion-stage.js",
      "scripts/render-motion-media.mjs"
    ];
    for (const path of paths) {
      expect((await readFile(join(designRoot, path), "utf8")).trim().length).toBeGreaterThan(200);
    }
    const help = execFileSync(process.execPath, [join(designRoot, "scripts", "render-motion-media.mjs"), "--help"], { encoding: "utf8" });
    expect(help).toContain("window.__setDesignTime(seconds)");
  });
});

describe("README visual capability collaboration", () => {
  const readmeRoot = join(ownedRoot, "github-readme-highstar");

  it("triggers for repository branding and routes visual production without one-shot image generation", async () => {
    const skill = await readFile(join(readmeRoot, "SKILL.md"), "utf8");
    expect(skill).toContain("README 封面 / Banner / Hero");
    expect(skill).toContain("interface-design");
    expect(skill).toContain("项目理解");
    expect(skill).toContain("静态 Poster");
    expect(skill).not.toContain("modelscope_imagegen");
    expect(skill).not.toContain("cloudflare-image-gen");

    const integration = await readFile(join(readmeRoot, "references", "readme-visual-integration.md"), "utf8");
    expect(integration).toContain("Launcher ready-state image");
    expect(integration).toContain("deterministic source");
    const evals = JSON.parse(await readFile(join(readmeRoot, "evals", "evals.json"), "utf8")) as EvalFile;
    expect(evals.scenarios.map((scenario) => scenario.id)).toEqual(expect.arrayContaining([
      "repository-cover",
      "repository-demo-video",
      "readme-structure-only"
    ]));
  });
});

describe("owned skill trigger contracts", () => {
  it("routes common user wording without requiring explicit skill names", async () => {
    const interfaceFrontmatter = frontmatter(await readFile(join(designRoot, "SKILL.md"), "utf8"));
    const engineeringFrontmatter = frontmatter(await readFile(join(engineeringRoot, "SKILL.md"), "utf8"));
    const readmeFrontmatter = frontmatter(await readFile(join(ownedRoot, "github-readme-highstar", "SKILL.md"), "utf8"));
    const pptxFrontmatter = frontmatter(await readFile(join(ownedRoot, "pptx", "SKILL.md"), "utf8"));

    expect(interfaceFrontmatter).toContain("README covers");
    expect(interfaceFrontmatter).toContain("demo videos");
    expect(interfaceFrontmatter).toContain("app prototypes");
    expect(interfaceFrontmatter).toContain("Route native PowerPoint delivery to the PPT skill instead");
    expect(readmeFrontmatter).toContain("README 封面");
    expect(engineeringFrontmatter).toContain("implementing changes");
    expect(engineeringFrontmatter).toContain("debugging");
    expect(engineeringFrontmatter).toContain("refactoring");
    expect(pptxFrontmatter).toContain(".pptx");
    expect(pptxFrontmatter).toContain("deck");
  });
});

function runDesign(args: string[]): Record<string, any> {
  return runJson(designRouter, [...args, "--format", "json"]);
}

function runJson(script: string, args: string[]): Record<string, any> {
  return JSON.parse(execFileSync(process.execPath, [script, ...args], { encoding: "utf8" })) as Record<string, any>;
}

function frontmatter(content: string): string {
  const closingDelimiter = content.indexOf("\n---", 4);
  if (closingDelimiter < 0) throw new Error("SKILL.md frontmatter is not closed");
  return content.slice(0, closingDelimiter + 4);
}

async function readPatternFile(file: string, key: string): Promise<Pattern[]> {
  const parsed = JSON.parse(await readFile(join(designRoot, "assets", "patterns", file), "utf8")) as Record<string, Pattern[]>;
  return parsed[key];
}

interface Pattern {
  id: string;
  severity?: string;
  deliverables?: string[];
}

interface EvalFile {
  scenarios: Array<{ id: string }>;
}
