import { execFileSync } from "node:child_process";
import { mkdtemp, readFile, readdir, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
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
  }, 30_000);

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
  }, 30_000);
});

describe("HTML universal design capability architecture", () => {
  it("keeps every decision-rule reference resolvable and every id unique", async () => {
    const layouts = await readPatternFile("layout-patterns.json", "patterns");
    const components = await readPatternFile("component-patterns.json", "components");
    const rules = await readPatternFile("decision-rules.json", "rules") as Array<Pattern & { suggest: { layouts: string[]; components: string[] } }>;
    const checks = await readPatternFile("quality-checks.json", "checks");
    const outputContracts = await readPatternFile("output-contract-patterns.json", "contracts");
    const tasteAnchors = await readPatternFile("taste-anchor-patterns.json", "anchors");
    const motionRecipes = await readPatternFile("motion-scene-recipes.json", "recipes");
    const antiTemplateRules = await readPatternFile("anti-template-rules.json", "rules");

    for (const collection of [layouts, components, rules, checks, outputContracts, tasteAnchors, motionRecipes, antiTemplateRules]) {
      expect(new Set(collection.map((item) => item.id)).size).toBe(collection.length);
      expect(collection.every((item) => item.id.length > 0)).toBe(true);
    }

    const layoutIds = new Set(layouts.map((item) => item.id));
    const componentIds = new Set(components.map((item) => item.id));
    for (const rule of rules) {
      for (const id of rule.suggest.layouts) expect(layoutIds.has(id)).toBe(true);
      for (const id of rule.suggest.components) expect(componentIds.has(id)).toBe(true);
    }
    expect(layouts.length).toBeGreaterThanOrEqual(12);
    expect(components.length).toBeGreaterThanOrEqual(16);
    expect(checks.length).toBeGreaterThanOrEqual(43);
    expect(checks.filter((check) => check.severity === "blocker").length).toBeGreaterThanOrEqual(4);
    for (const check of checks) {
      expect(check.deliverables).toBeDefined();
      expect(check.deliverables?.length).toBeGreaterThan(0);
      for (const deliverable of check.deliverables ?? []) expect(["html", "image", "video", "gif", "pdf", "hybrid", "pptx"]).toContain(deliverable);
    }

    const directionLibrary = JSON.parse(await readFile(join(designRoot, "assets", "patterns", "visual-direction-patterns.json"), "utf8")) as {
      patterns: Array<Pattern & { html_implementation_score: number; font_profile: string }>;
      font_stack_profiles: Record<string, string>;
    };
    expect(directionLibrary.patterns).toHaveLength(40);
    expect(new Set(directionLibrary.patterns.map((pattern) => pattern.id)).size).toBe(40);
    for (const pattern of directionLibrary.patterns) {
      expect(pattern.html_implementation_score).toBeGreaterThanOrEqual(1);
      expect(pattern.html_implementation_score).toBeLessThanOrEqual(5);
      expect(directionLibrary.font_stack_profiles[pattern.font_profile]).toBeTruthy();
    }
  });

  it("routes landing, dashboard, app prototype, and HTML presentation to browser-native patterns", () => {
    const landing = runDesign(["--task", "landing", "--deliverable", "html", "--signals", "narrative"]);
    expect(landing).toMatchObject({ owners: ["interface-design"], final_owner: "interface-design", mode: "build" });
    expect(landing.suggested_layouts).toContain("product-first-story");
    expect(landing.output_contracts).toEqual(expect.arrayContaining([expect.objectContaining({ id: "landing-page" })]));
    expect(landing.anti_template_rules).toEqual(expect.arrayContaining([expect.objectContaining({ id: "generic-hero" })]));

    const dashboard = runDesign(["--task", "dashboard", "--deliverable", "html", "--signals", "trends,comparison,many-records"]);
    expect(dashboard.suggested_layouts).toEqual(expect.arrayContaining(["command-center-dashboard", "metric-to-detail", "split-comparison"]));
    expect(dashboard.suggested_components).toEqual(expect.arrayContaining(["time-series-chart", "comparison-matrix", "data-table"]));
    expect(dashboard.required_quality_checks).toEqual(expect.arrayContaining([expect.objectContaining({ id: "data-integrity", severity: "high" })]));
    expect(dashboard.taste_anchors).toEqual(expect.arrayContaining([expect.objectContaining({ id: "operational-saas" })]));

    const prototype = runDesign(["--task", "app-prototype", "--deliverable", "html"]);
    expect(prototype).toMatchObject({ mode: "prototype" });
    expect(prototype.suggested_layouts).toEqual(expect.arrayContaining(["app-shell-prototype", "device-prototype-gallery"]));
    expect(prototype.suggested_components).toEqual(expect.arrayContaining(["prototype-shell", "device-frame", "tweak-panel"]));
    expect(prototype.output_contracts).toEqual(expect.arrayContaining([expect.objectContaining({ id: "app-prototype" })]));

    const presentation = runDesign(["--task", "html-presentation", "--deliverable", "html"]);
    expect(presentation.suggested_layouts).toContain("html-slide-sequence");
    expect(presentation.suggested_components).toContain("slide-frame");
    expect(presentation.output_contracts).toEqual(expect.arrayContaining([expect.objectContaining({ id: "html-slide" })]));
  });

  it("keeps explicit HTML-first PPTX inside interface-design and requires editability selection", () => {
    const undecided = runDesign(["--task", "html-presentation", "--deliverable", "pptx", "--pipeline", "html-first"]);
    expect(undecided).toMatchObject({
      owners: ["interface-design"],
      final_owner: "interface-design",
      mode: "decision",
      pptx_mode: "unspecified",
      decision_required: { id: "html-pptx-editability", options: ["editable", "fidelity"] }
    });
    expect(undecided.boundary).toContain("ask the user");

    const editable = runDesign(["--task", "html-presentation", "--deliverable", "pptx", "--pipeline", "html-first", "--pptx-mode", "editable", "--signals", "html-first,editable-pptx"]);
    expect(editable).toMatchObject({ owners: ["interface-design"], final_owner: "interface-design", mode: "asset", pptx_mode: "editable", decision_required: null });
    expect(editable.required_quality_checks).toEqual(expect.arrayContaining([
      expect.objectContaining({ id: "editable-dom-contract", severity: "blocker" }),
      expect.objectContaining({ id: "native-object-editability", severity: "blocker" })
    ]));
    expect(editable.required_quality_checks.map((check: Pattern) => check.id)).not.toContain("native-ppt-boundary");

    const fidelity = runDesign(["--task", "html-presentation", "--deliverable", "pptx", "--pipeline", "html-first", "--pptx-mode", "fidelity"]);
    expect(fidelity.boundary).toContain("not object-editable");
    expect(fidelity.required_quality_checks).toEqual(expect.arrayContaining([expect.objectContaining({ id: "fidelity-disclosure", severity: "blocker" })]));
  });

  it("enforces native PowerPoint and hybrid ownership without browser-workflow leakage", () => {
    const native = runDesign(["--task", "html-presentation", "--deliverable", "pptx", "--platform", "windows"]);
    expect(native).toMatchObject({ owners: ["window-pptx"], final_owner: "window-pptx", handoff: false, mode: "route" });
    expect(native.suggested_layouts).toEqual([]);
    expect(native.suggested_components).toEqual([]);
    expect(native.output_contracts).toEqual([]);
    expect(native.taste_anchors).toEqual([]);
    expect(native.motion_recipes).toEqual([]);
    expect(native.anti_template_rules).toEqual([]);
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
    expect(cover.output_contracts).toEqual(expect.arrayContaining([expect.objectContaining({ id: "social-cover" })]));
    expect(cover.taste_anchors).toEqual(expect.arrayContaining([expect.objectContaining({ id: "developer-tool" })]));
    expect(cover.required_quality_checks).toEqual(expect.arrayContaining([
      expect.objectContaining({ id: "repository-product-proof", severity: "blocker" }),
      expect.objectContaining({ id: "distribution-readability", severity: "high" })
    ]));

    const poster = runDesign(["--task", "poster", "--deliverable", "image"]);
    expect(poster.suggested_layouts).toContain("campaign-poster");

    const infographic = runDesign(["--task", "infographic", "--deliverable", "image", "--signals", "comparison,process"]);
    expect(infographic.suggested_layouts).toContain("evidence-infographic");
    expect(infographic.suggested_components).toEqual(expect.arrayContaining(["stat-block", "annotated-diagram"]));
    expect(infographic.required_quality_checks).toEqual(expect.arrayContaining([
      expect.objectContaining({ id: "asset-provenance", severity: "blocker" }),
      expect.objectContaining({ id: "infographic-evidence", severity: "blocker" })
    ]));
    expect(infographic.output_contracts).toEqual(expect.arrayContaining([expect.objectContaining({ id: "vertical-infographic" })]));

    const video = runDesign(["--task", "product-demo", "--deliverable", "video", "--signals", "workflow,motion"]);
    expect(video.suggested_layouts).toEqual(expect.arrayContaining(["demo-story-sequence", "creative-coding-stage"]));
    expect(video.required_quality_checks).toEqual(expect.arrayContaining([
      expect.objectContaining({ id: "deterministic-time", severity: "blocker" }),
      expect.objectContaining({ id: "static-fallback", severity: "blocker" }),
      expect.objectContaining({ id: "frame-integrity", severity: "high" })
    ]));
    expect(video.motion_recipes).toEqual([expect.objectContaining({ id: "product-proof-loop" })]);

    const gif = runDesign(["--task", "product-demo", "--deliverable", "gif", "--signals", "workflow,motion"]);
    expect(gif).toMatchObject({ owners: ["interface-design"], final_owner: "interface-design", mode: "asset" });
    expect(gif.required_quality_checks).toEqual(expect.arrayContaining([
      expect.objectContaining({ id: "deterministic-time", severity: "blocker" }),
      expect.objectContaining({ id: "gif-loop-budget", severity: "blocker" })
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
      "html-first-presentations.md",
      "react-browser-setup.md",
      "brand-and-product-assets.md",
      "repository-branding-and-marketing.md",
      "creative-coding-and-motion-media.md",
      "audio-and-narration.md",
      "motion-rendering-safety.md",
      "implementation-and-verification.md"
    ];
    for (const module of modules) {
      const path = `references/capabilities/${module}`;
      expect(skill).toContain(path);
      expect((await readFile(join(designRoot, path), "utf8")).trim().length).toBeGreaterThan(300);
    }

    expect(skill).toContain("HTML Based Universal Design");
    expect(skill).toContain("Brand DESIGN.md Routing");
    expect(skill).toContain("Route ordinary native PowerPoint delivery to the PPT skill");
    expect(skill).toContain("320, 375, 414, 768");
    expect(skill).toContain("exactly three materially different, real direction previews");

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
      "creative-coding-visual",
      "readme-autoplay-gif",
      "html-first-editable-pptx",
      "html-first-fidelity-pptx",
      "html-first-pptx-decision",
      "device-prototype-variants",
      "narrated-launch-film",
      "evidence-infographic"
    ]));
  });

  it("ships reusable repository and deterministic motion assets", async () => {
    const paths = [
      "assets/templates/brand-spec.md",
      "assets/templates/repository-visual-brief.md",
      "assets/templates/motion-storyboard.md",
      "assets/templates/direction-decision.md",
      "assets/templates/director-notes.md",
      "assets/templates/narration-manifest.json",
      "assets/templates/narration-script.md",
      "assets/templates/audio-cues.json",
      "assets/templates/render-manifest.json",
      "assets/patterns/anti-template-rules.json",
      "assets/patterns/motion-scene-recipes.json",
      "assets/patterns/output-contract-patterns.json",
      "assets/patterns/taste-anchor-patterns.json",
      "assets/starter/repository-hero.html",
      "assets/starter/motion-stage.js",
      "assets/starter/deck-index.html",
      "assets/starter/deck-stage.js",
      "assets/starter/design-comparison.jsx",
      "assets/starter/tweak-panel.jsx",
      "assets/starter/gsap-deterministic-stage.js",
      "assets/starter/gallery-wall-stage.js",
      "assets/starter/publication-slide.html",
      "assets/starter/ios-frame.jsx",
      "assets/starter/android-frame.jsx",
      "assets/starter/macos-window.jsx",
      "assets/starter/browser-window.jsx",
      "assets/starter/narration-stage.jsx",
      "scripts/render-motion-media.mjs",
      "scripts/verify-motion-media.mjs",
      "scripts/export-html-deck-pptx.mjs",
      "scripts/export-html-deck-pdf.mjs",
      "scripts/export-html-stage-pdf.mjs",
      "scripts/render-narration-tts.mjs",
      "scripts/compile-narration-timeline.mjs",
      "scripts/fetch-wikimedia-assets.mjs",
      "scripts/render-deck-thumbnails.mjs",
      "scripts/mix-motion-audio.mjs",
      "scripts/prepare-motion-review.mjs",
      "scripts/render-with-adapter.mjs"
    ];
    for (const path of paths) {
      expect((await readFile(join(designRoot, path), "utf8")).trim().length).toBeGreaterThan(200);
    }
    const help = execFileSync(process.execPath, [join(designRoot, "scripts", "render-motion-media.mjs"), "--help"], { encoding: "utf8" });
    expect(help).toContain("window.__setDesignTime(seconds)");
    expect(help).toContain("--formats <list>");
    expect(help).toContain("--gif-loop <mode>");
    expect(help).toContain("webm,mov,png-sequence");

    const pptxHelp = execFileSync(process.execPath, [join(designRoot, "scripts", "export-html-deck-pptx.mjs"), "--help"], { encoding: "utf8" });
    expect(pptxHelp).toContain("--mode <editable|fidelity>");
    const deckPdfHelp = execFileSync(process.execPath, [join(designRoot, "scripts", "export-html-deck-pdf.mjs"), "--help"], { encoding: "utf8" });
    expect(deckPdfHelp).toContain("vector-text PDF page");
    const stagePdfHelp = execFileSync(process.execPath, [join(designRoot, "scripts", "export-html-stage-pdf.mjs"), "--help"], { encoding: "utf8" });
    expect(stagePdfHelp).toContain("<deck-stage>");
    const verifyHelp = execFileSync(process.execPath, [join(designRoot, "scripts", "verify-motion-media.mjs"), "--help"], { encoding: "utf8" });
    expect(verifyHelp).toContain("--require-loop");
    expect(verifyHelp).toContain("--require-alpha");
    const narrationHelp = execFileSync(process.execPath, [join(designRoot, "scripts", "render-narration-tts.mjs"), "--help"], { encoding: "utf8" });
    expect(narrationHelp).toContain("synthesize({ id, text, voice, locale, outputPath })");
    const mixHelp = execFileSync(process.execPath, [join(designRoot, "scripts", "mix-motion-audio.mjs"), "--help"], { encoding: "utf8" });
    expect(mixHelp).toContain("licensed voice, music, or effect clips");
    const reviewHelp = execFileSync(process.execPath, [join(designRoot, "scripts", "prepare-motion-review.mjs"), "--help"], { encoding: "utf8" });
    expect(reviewHelp).toContain("provider-neutral semantic-review prompt");
    expect(reviewHelp).toContain("--review-instructions");
    const adapterHelp = execFileSync(process.execPath, [join(designRoot, "scripts", "render-with-adapter.mjs"), "--help"], { encoding: "utf8" });
    expect(adapterHelp).toContain("project-owned adapter");
    const fetchHelp = execFileSync(process.execPath, [join(designRoot, "scripts", "fetch-wikimedia-assets.mjs"), "--help"], { encoding: "utf8" });
    expect(fetchHelp).toContain("source, author, license, URL, and SHA-256 evidence");
    const thumbnailHelp = execFileSync(process.execPath, [join(designRoot, "scripts", "render-deck-thumbnails.mjs"), "--help"], { encoding: "utf8" });
    expect(thumbnailHelp).toContain("window.__VISUAL_READY__");
    const timelineHelp = execFileSync(process.execPath, [join(designRoot, "scripts", "compile-narration-timeline.mjs"), "--help"], { encoding: "utf8" });
    expect(timelineHelp).toContain("## scene-id");

    const temp = await mkdtemp(join(tmpdir(), "interface-narration-"));
    try {
      const scriptPath = join(temp, "script.md");
      const manifestPath = join(temp, "narration.json");
      await writeFile(scriptPath, "# Demo\n\n## opening\nStart here. [[cue:proof]]Show proof.\n\n## close\nFinish clearly.\n", "utf8");
      const compiled = JSON.parse(execFileSync(process.execPath, [
        join(designRoot, "scripts", "compile-narration-timeline.mjs"),
        "--script", scriptPath,
        "--manifest", manifestPath
      ], { encoding: "utf8" })) as Record<string, any>;
      const narration = JSON.parse(await readFile(manifestPath, "utf8")) as Record<string, any>;
      expect(compiled).toMatchObject({ segments: 2 });
      expect(narration.segments).toEqual([
        expect.objectContaining({ id: "opening", text: "Start here. Show proof." }),
        expect.objectContaining({ id: "close", text: "Finish clearly." })
      ]);

      const adapterPath = join(temp, "adapter.mjs");
      const audioDir = join(temp, "audio");
      await writeFile(adapterPath, [
        'import { writeFile } from "node:fs/promises";',
        'export async function synthesize({ text, outputPath }) {',
        '  await writeFile(outputPath, Buffer.from("RIFF"));',
        '  return { words: [{ text: text.split(/\\s+/)[0], start: 0, end: 0.2, char_start: 0 }] };',
        '}'
      ].join("\n"), "utf8");
      const tts = JSON.parse(execFileSync(process.execPath, [
        join(designRoot, "scripts", "render-narration-tts.mjs"),
        "--manifest", manifestPath,
        "--adapter", adapterPath,
        "--output-dir", audioDir
      ], { encoding: "utf8" })) as Record<string, any>;
      expect(tts.outputs).toHaveLength(2);
      expect(JSON.parse(await readFile(join(audioDir, "opening.words.json"), "utf8"))).toMatchObject({
        id: "opening",
        words: [expect.objectContaining({ start: 0, end: 0.2, char_start: 0 })]
      });
    } finally {
      await rm(temp, { recursive: true, force: true });
    }

    const audioCues = JSON.parse(await readFile(join(designRoot, "assets", "templates", "audio-cues.json"), "utf8") as string) as Record<string, any>;
    expect(audioCues.ducking).toMatchObject({ ratio: 8, attack_ms: 20, release_ms: 350 });
  }, 30_000);

  it("keeps every installed interface-design runtime file source-neutral", async () => {
    const files = await collectRuntimeFiles(designRoot);
    const content = (await Promise.all(files.map((path) => readFile(path, "utf8").catch(() => "")))).join("\n");
    for (const forbidden of ["huashu", "alchaincyf", "花叔", "Created by Huashu", "npx skills add", "design-gate-hook", "tts-doubao"]) {
      expect(content.toLowerCase()).not.toContain(forbidden.toLowerCase());
    }
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
    expect(skill).toContain("自动播放 GIF");
    expect(skill).not.toContain("modelscope_imagegen");
    expect(skill).not.toContain("cloudflare-image-gen");

    const integration = await readFile(join(readmeRoot, "references", "readme-visual-integration.md"), "utf8");
    expect(integration).toContain("Launcher ready-state image");
    expect(integration).toContain("deterministic source");
    expect(integration).toContain("tracked GIF");
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
    expect(interfaceFrontmatter).toMatch(/narrated demo\s+videos/);
    expect(interfaceFrontmatter).toContain("app prototypes");
    expect(interfaceFrontmatter).toContain("infographics");
    expect(interfaceFrontmatter).toContain("HTML-first PDF or PPTX conversion");
    expect(interfaceFrontmatter).toContain("Route ordinary native PowerPoint delivery to the PPT skill");
    expect(readmeFrontmatter).toContain("README 封面");
    expect(engineeringFrontmatter).toContain("implementing changes");
    expect(engineeringFrontmatter).toContain("debugging");
    expect(engineeringFrontmatter).toContain("refactoring");
    expect(pptxFrontmatter).toContain(".pptx");
    expect(pptxFrontmatter).toContain("deck");
  });

  it("prefers the free Agnes model for long-running OpenCode delegation", async () => {
    const provider = await readFile(join(ownedRoot, "cli-agent-orchestrator", "references", "providers", "opencode.md"), "utf8");
    expect(provider.indexOf("agnes/agnes-2.0-flash")).toBeLessThan(provider.indexOf("opencode/deepseek-v4-flash-free"));
    expect(provider).toContain("provider limit is a model failure event");
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

async function collectRuntimeFiles(root: string): Promise<string[]> {
  const files: string[] = [];
  async function walk(directory: string): Promise<void> {
    for (const entry of await readdir(directory, { withFileTypes: true })) {
      if (entry.name === "_external_repos") continue;
      const path = join(directory, entry.name);
      if (entry.isDirectory()) await walk(path);
      else files.push(path);
    }
  }
  await walk(root);
  return files;
}
