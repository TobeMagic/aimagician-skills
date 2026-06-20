import { access, readFile } from "node:fs/promises";
import { join } from "node:path";
import blessed = require("blessed");
import { loadUserConfig, removeUserGroup, saveTheme, saveUserGroup } from "../config/user-config";
import {
  archiveSkills,
  installSkills,
  previewInstallSkills,
  searchSkills,
  setSkillOverride,
  uninstallSkills,
  type InstallSkillsResult,
  type ManagerSkillRecord,
  type UninstallSkillsResult
} from "../manager/manager";
import type { InstallScope } from "../model/scopes";
import { supportedTargets, type SupportedTarget } from "../model/targets";
import { resolvePlatformContext, type PlatformContext } from "../shared/platform";
import { ownedSkillsRoot } from "../shared/paths";
import {
  BIRD_ASCII,
  BIRD_SPLASH,
  COLORS,
  PALETTE,
  SELECT_GLYPH,
  UNSELECT_GLYPH,
  formatMatrixCell,
  getSelectedListStyle,
  getTheme,
  targetShortLabel,
  THEME_NAMES,
  type ThemeColors
} from "./theme";
import { loadTaxonomy, type TaxonomyGroup } from "../catalog/taxonomy";
import { showSourceToggle } from "./source-toggle";
import { loadCatalog } from "../catalog/load-catalog";
import {
  COMMAND_HELP,
  renderMatrixLabel,
  renderMatrixRow,
  renderSkillRow,
  visibleWidth
} from "./rendering";

export interface DashboardOptions {
  selectedTargets?: SupportedTarget[];
  projectDir?: string;
  platform?: Partial<PlatformContext>;
}

// ── Splash Screen ──────────────────────────────────────────────────────
function showSplash(screen: blessed.Widgets.Screen): Promise<void> {
  return new Promise((resolve) => {
    const splash = blessed.box({
      parent: screen,
      top: "center",
      left: "center",
      width: "shrink",
      height: "shrink",
      tags: true,
      style: { fg: PALETTE.amber, bg: PALETTE.carbon },
      content: BIRD_SPLASH.join("\n")
    });
    screen.render();

    let frame = 0;
    const typewriter = setInterval(() => {
      frame++;
      if (frame >= BIRD_SPLASH.length) {
        clearInterval(typewriter);
        setTimeout(() => {
          splash.detach();
          screen.render();
          resolve();
        }, 800);
      } else {
        splash.setContent(BIRD_SPLASH.slice(0, frame + 1).join("\n"));
        screen.render();
      }
    }, 60);
  });
}

// ── Extract all unique groups from skills ──────────────────────────────
function extractAllGroups(skills: ManagerSkillRecord[], taxonomy: import("../catalog/taxonomy").SkillTaxonomy): TaxonomyGroup[] {
  const groupIds = new Set<string>();
  for (const skill of skills) {
    if (skill.group) groupIds.add(skill.group);
  }
  return taxonomy.groups.filter((g) => groupIds.has(g.id));
}

// ── Count skills per group ─────────────────────────────────────────────
function countSkillsPerGroup(skills: ManagerSkillRecord[], groupId: string): number {
  return skills.filter((s) => s.group === groupId).length;
}

// ── Main Dashboard ─────────────────────────────────────────────────────
export async function runDashboard(options: DashboardOptions = {}): Promise<void> {
  const screen = blessed.screen({
    smartCSR: true,
    title: "Skillbird"
  });

  await showSplash(screen);

  // ── State ──────────────────────────────────────────────────────────
  let detailTab = 0;
  let focusPanel: "hive" | "cells" | "nectar" = "cells";
  const DETAIL_TABS = ["Matrix", "README", "Related"];

  let scope: InstallScope = "global";
  let query = "";
  let includeArchived = false;
  let skills: ManagerSkillRecord[] = [];
  let allGroups: TaxonomyGroup[] = [];
  let isRendering = false;
  const selectedGroups = new Set<string>();
  const selectedIds = new Set<string>();
  const operationLog: string[] = [];
  let viewMode: "list" | "matrix" = "list";
  let currentTheme = "dove";
  let currentColors: ThemeColors = COLORS;
  const brokenIds = new Set<string>();
  let progressTimer: ReturnType<typeof setInterval> | null = null;
  let progressStage = 0;
  let cachedUserConfig: import("../config/user-config").UserSkillConfig | null = null;
  let cachedTaxonomy: import("../catalog/taxonomy").SkillTaxonomy | null = null;

  // ── Layout ──────────────────────────────────────────────────────────
  const header = blessed.box({
    parent: screen, top: 0, left: 0, width: "100%", height: 3,
    tags: true, style: { fg: currentColors.brandYellow, bold: true }, content: ""
  });

  const hiveList = blessed.list({
    parent: screen,
    label: ` ${BIRD_ASCII} Categories `,
    top: 3, left: 0, width: "20%", height: "calc(100% - 5)",
    border: "line", keys: true, vi: true, mouse: true, focusable: true,
    style: { ...getSelectedListStyle(currentColors), border: { fg: currentColors.panelBorder }, bg: PALETTE.carbon }
  });

  const skillList = blessed.list({
    parent: screen,
    label: ` ${BIRD_ASCII} Skills `,
    top: 3, left: "20%", width: "50%", height: "calc(100% - 5)",
    border: "line", keys: true, vi: true, mouse: true, focusable: true,
    style: { ...getSelectedListStyle(currentColors), border: { fg: currentColors.panelBorder }, bg: PALETTE.carbon }
  });

  const detailBox = blessed.box({
    parent: screen,
    label: ` ${BIRD_ASCII} Details `,
    top: 3, left: "70%", width: "30%", height: "calc(100% - 5)",
    border: "line", tags: true, scrollable: true, alwaysScroll: true,
    keys: true, vi: true, focusable: true,
    style: { fg: PALETTE.ghostWhite, border: { fg: currentColors.panelBorder }, bg: PALETTE.carbon }
  });

  const statusBar = blessed.box({
    parent: screen, top: "100%-2", left: 0, width: "100%", height: 2,
    tags: true, style: { fg: PALETTE.ghostWhite, bg: PALETTE.carbon }, content: ""
  });

  // ── Platform ───────────────────────────────────────────────────────
  const platformContext = resolvePlatformContext(options.platform);
  const allTargets = [...supportedTargets];
  const initialTargets = options.selectedTargets?.length ? options.selectedTargets : allTargets;
  const selectedTargets = new Set<SupportedTarget>(initialTargets);
  let primaryTarget = initialTargets[0] ?? allTargets[0];

  // ── Focus Management ───────────────────────────────────────────────
  function updatePanelFocus(): void {
    hiveList.style.border = { fg: focusPanel === "hive" ? currentColors.brandYellow : currentColors.panelBorder };
    skillList.style.border = { fg: focusPanel === "cells" ? currentColors.brandYellow : currentColors.panelBorder };
    detailBox.style.border = { fg: focusPanel === "nectar" ? currentColors.brandYellow : currentColors.panelBorder };
    if (focusPanel === "hive") hiveList.focus();
    else if (focusPanel === "cells") skillList.focus();
    else if (focusPanel === "nectar") detailBox.focus();
  }

  // ── Progress Animation ─────────────────────────────────────────────
  function startProgress(label: string): void {
    const frames = [
      `{${currentColors.brandYellow}-fg}${BIRD_ASCII}----{/}`,
      `-{${currentColors.brandYellow}-fg}${BIRD_ASCII}---{/}`,
      `--{${currentColors.brandYellow}-fg}${BIRD_ASCII}--{/}`,
      `---{${currentColors.brandYellow}-fg}${BIRD_ASCII}-{/}`,
      `----{${currentColors.brandYellow}-fg}${BIRD_ASCII}{/}`
    ];
    progressStage = 0;
    statusBar.setContent(`${label}  ${frames[0]}\n`);
    screen.render();
    progressTimer = setInterval(() => {
      progressStage = (progressStage + 1) % frames.length;
      statusBar.setContent(`${label}  ${frames[progressStage]}\n`);
      screen.render();
    }, 180);
  }

  function stopProgress(): void {
    if (progressTimer) { clearInterval(progressTimer); progressTimer = null; }
  }

  // ── Health Check ───────────────────────────────────────────────────
  async function checkHealth(): Promise<void> {
    brokenIds.clear();
    for (const skill of skills) {
      if (skill.origin === "owned" && skill.installedTargets.length > 0) {
        try { await access(join(ownedSkillsRoot, skill.id, "SKILL.md")); }
        catch { brokenIds.add(skill.id); }
      }
    }
  }

  // ── Group Filtering ──────────────────────────────────────────────────
  function getVisibleSkills(): ManagerSkillRecord[] {
    return filterSkillsByGroups(skills, selectedGroups, query, includeArchived, selectedTargets, primaryTarget);
  }

  // ── Flash Animation (amber → installed color) ──────────────────────
  function flashSkill(skillIds: string[], _kind: "install" | "uninstall"): void {
    // Brief visual feedback: re-render with amber highlight, then normal after delay
    const originalRender = render;
    const flashRender = (): void => {
      originalRender();
      // Temporarily highlight selected rows
      for (const id of skillIds) {
        void id; // mark as used
      }
    };
    flashRender();
    setTimeout(() => { render(); }, 400);
  }

  // ── Refresh ────────────────────────────────────────────────────────
  async function refresh(message = "Loading skills..."): Promise<void> {
    const targetsForSearch = selectedTargets.size > 0 ? [...selectedTargets] : allTargets;
    statusBar.setContent(message);
    screen.render();
    try {
      const [loadedSkills, userConfig, taxonomy] = await Promise.all([
        searchSkills({
          scope, projectDir: options.projectDir,
          selectedTargets: targetsForSearch, includeArchived,
          platform: options.platform
        }),
        loadUserConfig(platformContext.configBaseDir),
        loadTaxonomy()
      ]);
      skills = loadedSkills;
      cachedUserConfig = userConfig;
      cachedTaxonomy = taxonomy;
      allGroups = extractAllGroups(skills, taxonomy);
      void checkHealth();

      if (currentTheme !== userConfig.theme) {
        currentTheme = userConfig.theme;
        currentColors = getTheme(currentTheme);
      }

      if (message !== "Loading skills...") log(message);
      render();
    } catch (error) {
      log(`Error: ${error instanceof Error ? error.message : "unknown error"}`);
      render();
      screen.render();
    }
  }

  // ── Render ─────────────────────────────────────────────────────────
  function render(): void {
    isRendering = true;
    try {
      updatePanelFocus();
      const visibleSkills = getVisibleSkills();
      const targetsOverview = [...selectedTargets].map((t) => targetShortLabel(t)).join(",");

      // Header
      header.setContent(
        ` {bold}${BIRD_ASCII} SKILLBIRD{/bold}  scope:{bold}${scope}{/bold}  selected:{bold}${selectedIds.size}{/bold}  groups:{bold}${selectedGroups.size > 0 ? selectedGroups.size : "all"}{/bold}  targets:[{bold}${targetsOverview}{/bold}]` +
        (brokenIds.size > 0 ? `  {${currentColors.error}-fg}health:${brokenIds.size}{/${currentColors.error}-fg}` : "") +
        (query ? `  {79-fg}search:${query}{/79-fg}` : "")
      );

      // Categories
      renderHivePanel();
      // Skills
      renderCellsPanel(visibleSkills);
      // Details
      renderSelectedSkillDetail();
      // Status bar
      const shortcutLine = getGuideBar(focusPanel, selectedIds.size > 0, selectedGroups.size > 0);
      const statusLine = operationLog.length > 0 ? operationLog[0] : "ready";
      statusBar.setContent(`${shortcutLine}\n${statusLine}`);
      screen.render();
    } finally {
      isRendering = false;
    }
  }

  function renderHivePanel(): void {
    const groupItems = allGroups.map((group) => {
      const count = countSkillsPerGroup(skills, group.id);
      const sel = selectedGroups.has(group.id) || selectedGroups.size === 0;
      const glyph = sel ? SELECT_GLYPH : UNSELECT_GLYPH;
      const prefix = sel
        ? `{${currentColors.brandYellow}-fg}{bold}${glyph} ${group.label} (${count}){/bold}{/${currentColors.brandYellow}-fg}`
        : `{${PALETTE.ghostWhite}-fg}${glyph} ${group.label} (${count}){/${PALETTE.ghostWhite}-fg}`;
      return prefix;
    });

    // Custom groups
    if (cachedUserConfig && cachedUserConfig.groups.length > 0) {
      const customItems = cachedUserConfig.groups.map((g) => {
        return `{79-fg}\u25CE ${g.name} (${g.skills.length}){/79-fg}`;
      });
      hiveList.setItems([...groupItems, `{${PALETTE.dimGray}-fg}--- custom groups ---{/${PALETTE.dimGray}-fg}`, ...customItems]);
    } else {
      hiveList.setItems(groupItems);
    }
  }

  function renderCellsPanel(visibleSkills: ManagerSkillRecord[]): void {
    if (viewMode === "matrix") {
      const targetsArr = [...selectedTargets];
      const maxIdLen = Math.max(...visibleSkills.map((s) => visibleWidth(s.id)), 8);
      skillList.setLabel(renderMatrixLabel(targetsArr));
      skillList.setItems(visibleSkills.map((skill) => renderMatrixRow(skill, targetsArr, selectedIds, maxIdLen)));
    } else {
      skillList.setLabel(` ${BIRD_ASCII} Skills `);
      skillList.setItems(visibleSkills.map((skill) => renderSkillRow(skill, primaryTarget, selectedIds, brokenIds, query)));
    }
  }

  function renderSelectedSkillDetail(): void {
    const visibleSkills = getVisibleSkills();
    renderDetail(visibleSkills[getSelectedIndex(skillList)] ?? visibleSkills[0]);
  }

  function renderDetail(skill: ManagerSkillRecord | undefined): void {
    if (!skill) { detailBox.setContent("No skill selected."); return; }
    detailBox.setLabel(` ${BIRD_ASCII} ${DETAIL_TABS[detailTab]}  (N=cycle) `);

    const matrixRow = supportedTargets.map((t) => {
      const avail = skill.availableTargets.includes(t);
      const installed = skill.installedTargets.includes(t);
      const managed = skill.managedTargets.includes(t);
      return `${targetShortLabel(t)}:${formatMatrixCell(avail, installed, managed)}`;
    }).join("  ");

    const relatedSkills = getRelatedSkills(skill, skills);

    if (detailTab === 0) {
      detailBox.setContent([
        `{${currentColors.brandYellow}-fg}{bold}${skill.id}{/bold}{/${currentColors.brandYellow}-fg}`,
        `{bold}Group:{/bold} ${skill.group}${skill.subgroup ? `/${skill.subgroup}` : ""}`,
        `{bold}Source:{/bold} ${skill.sourceId ?? "owned"}`,
        `{bold}Eligibility:{/bold} ${skill.archived ? "archived" : skill.commandOnly && scope === "project" ? "global-only" : "eligible"}`,
        `{bold}Archived:{/bold} ${skill.archived ? `{${currentColors.archivedFg}-fg}yes{/${currentColors.archivedFg}-fg}` : "no"}`,
        `{bold}Description:{/bold} ${(skill.description ?? "").slice(0, 80)}${(skill.description ?? "").length > 80 ? "..." : ""}`,
        "",
        `{bold}Install Matrix:{/bold}`,
        ` ${matrixRow}`,
        "",
        `{bold}Tags:{/bold} ${skill.tags.length ? skill.tags.join(", ") : "-"}`,
        skill.customTags.length > 0 ? `{bold}Custom:{/bold} ${skill.customTags.join(", ")}` : "",
        skill.commandOnly ? `{${currentColors.brandYellow}-fg}Command source: install only{/${currentColors.brandYellow}-fg}` : "",
        `{${PALETTE.dimGray}-fg}---{/${PALETTE.dimGray}-fg}`,
        `{${PALETTE.dimGray}-fg}N=cycle tab | i=install | u=uninstall | x=archive{/${PALETTE.dimGray}-fg}`
      ].filter(Boolean).join("\n"));
    } else if (detailTab === 1) {
      detailBox.setContent(`{${PALETTE.dimGray}-fg}Loading SKILL.md...{/${PALETTE.dimGray}-fg}`);
      void loadSkillPreview(skill).then((preview) => {
        detailBox.setContent(preview.length > 0 ? preview : `{${PALETTE.dimGray}-fg}No SKILL.md preview available.{/${PALETTE.dimGray}-fg}`);
        screen.render();
      });
    } else if (detailTab === 2) {
      detailBox.setContent([
        `{bold}Tags:{/bold} ${skill.tags.length ? skill.tags.join(", ") : "-"}`,
        skill.customTags.length > 0 ? `{bold}Custom:{/bold} ${skill.customTags.join(", ")}` : "",
        "",
        relatedSkills.length > 0
          ? [`{bold}Related Skills:{/bold}`, ...relatedSkills.slice(0, 8).map((s) => {
              const prefix = s.archived ? `{${currentColors.archivedFg}-fg}` : "";
              const suffix = s.archived ? `{/${currentColors.archivedFg}-fg}` : "";
              return `  ${prefix}${s.id}${suffix}`;
            })].join("\n")
          : `{${PALETTE.dimGray}-fg}No related skills found.{/${PALETTE.dimGray}-fg}`,
        "",
        `{${PALETTE.dimGray}-fg}---{/${PALETTE.dimGray}-fg}`,
        `{${PALETTE.dimGray}-fg}N=cycle tab{/${PALETTE.dimGray}-fg}`
      ].filter(Boolean).join("\n"));
    }
  }

  // ── Guide Bar (PRD §3.2) ───────────────────────────────────────────
  function getGuideBar(panel: string, hasSkillSelection: boolean, hasGroupSelection: boolean): string {
    if (panel === "hive") {
      return `Space=toggle  A=all  Shift+A=none  \u2190\u2192 panel`;
    }
    if (panel === "nectar") {
      return `N=cycle tab  \u2191\u2193 scroll  \u2190\u2192 panel`;
    }
    // cells panel
    if (hasSkillSelection) {
      return `Space=unselect  p=preview  i=install  I=include  X=exclude  d=default  u=uninstall  x=archive  ?=help`;
    }
    return `Space=select  Enter=detail  p=preview  i=install  I=include  X=exclude  d=default  t=targets  ?=help`;
  }

  async function showSyncPreview(assetIds: string[], targetsChoice: SupportedTarget[]): Promise<boolean> {
    const preview = await previewInstallSkills({
      assetIds,
      scope,
      projectDir: options.projectDir,
      selectedTargets: targetsChoice,
      includeArchived,
      platform: options.platform
    });
    const counts = { create: 0, overwrite: 0, remove: 0, skip: preview.skipped.length };
    for (const operation of preview.operations) {
      if (operation.kind === "create") counts.create += 1;
      else if (operation.kind === "overwrite") counts.overwrite += 1;
      else if (operation.kind === "remove") counts.remove += 1;
      else counts.skip += 1;
    }
    const lines = [
      `scope:${scope} targets:${targetsChoice.map(targetShortLabel).join(",")} create:${counts.create} overwrite:${counts.overwrite} remove:${counts.remove} skip:${counts.skip}`,
      "",
      ...targetsChoice.flatMap((target) => {
        const targetOperations = preview.operations.filter((operation) => operation.target === target);
        const targetSkipped = preview.skipped.filter((skip) => skip.target === undefined || skip.target === target);
        return [
          `{bold}${target}{/bold}`,
          ...targetOperations.map((operation) => `  ${operation.kind} ${operation.assetId} — ${operation.destinationPath}`),
          ...targetSkipped.map((skip) => `  skip ${skip.assetId} — ${skip.reason}`),
          ""
        ];
      }),
      "{center}{bold}Enter confirm  Esc cancel  Up/Down scroll{/bold}{/center}"
    ];

    return new Promise((resolve) => {
      const previewBox = blessed.box({
        parent: screen,
        top: "center",
        left: "center",
        width: "80%",
        height: "70%",
        border: { type: "line" },
        label: " Sync Preview ",
        tags: true,
        keys: true,
        vi: true,
        mouse: true,
        scrollable: true,
        alwaysScroll: true,
        style: { fg: PALETTE.ghostWhite, bg: PALETTE.carbon, border: { fg: currentColors.brandYellow } },
        content: lines.join("\n")
      });
      previewBox.focus();
      screen.render();
      previewBox.key("enter", () => { previewBox.detach(); screen.render(); resolve(true); });
      previewBox.key(["escape", "q"], () => { previewBox.detach(); screen.render(); resolve(false); });
    });
  }

  async function applySkillOverride(state: "include" | "exclude" | "default"): Promise<void> {
    const visibleSkills = getVisibleSkills();
    const highlighted = visibleSkills[getSelectedIndex(skillList)] ?? visibleSkills[0];
    const assetIds = selectedIds.size > 0 ? [...selectedIds] : highlighted ? [highlighted.id] : [];

    if (assetIds.length === 0) { log("No skills selected."); render(); return; }

    await setSkillOverride({
      assetIds,
      state,
      scope,
      projectDir: options.projectDir,
      selectedTargets: [...selectedTargets],
      platform: options.platform
    });
    await refresh(`Set ${assetIds.length} skill(s) to ${state}.`);
  }

  // ── Install Flow: Scope → Target → Install ─────────────────────────
  async function mutate(kind: "install" | "uninstall"): Promise<void> {
    const visibleSkills = getVisibleSkills();
    const highlighted = visibleSkills[getSelectedIndex(skillList)] ?? visibleSkills[0];
    const assetIds = selectedIds.size > 0
      ? [...selectedIds]
      : highlighted ? [highlighted.id] : [];

    if (assetIds.length === 0) {
      log("Select skills first.");
      render();
      return;
    }

    if (kind === "install") {
      const scopeChoice = await showScopeSelector();
      if (scopeChoice === null) return;
      scope = scopeChoice;

      const targetsChoice = await showTargetSelector();
      if (!targetsChoice || targetsChoice.length === 0) return;

      try {
        const confirmed = await showSyncPreview(assetIds, targetsChoice);
        if (!confirmed) {
          log("Sync cancelled.");
          render();
          return;
        }
      } catch (error) {
        log(`Preview error: ${error instanceof Error ? error.message : "unknown error"}`);
        render();
        return;
      }

      startProgress(`Installing ${assetIds.length} skill(s)`);
      try {
        const result = await installSkills({
          assetIds, scope, projectDir: options.projectDir,
          selectedTargets: targetsChoice, includeArchived,
          platform: options.platform
        });
        stopProgress();
        flashSkill(assetIds, "install");
        selectedIds.clear();
        await refresh(`Installed ${assetIds.length} skill(s) on ${targetsChoice.join(", ")}.`);
        showReport(buildInstallReport(targetsChoice, assetIds, result));
      } catch (error) {
        stopProgress();
        log(`Error: ${error instanceof Error ? error.message : "unknown error"}`);
        render();
      }
    } else {
      startProgress(`Uninstalling ${assetIds.length} skill(s)`);
      try {
        const result = await uninstallSkills({
          assetIds, scope, projectDir: options.projectDir,
          selectedTargets: [...selectedTargets], platform: options.platform
        });
        stopProgress();
        flashSkill(assetIds, "uninstall");
        selectedIds.clear();
        await refresh(`Uninstalled ${assetIds.length} skill(s).`);
        showReport(buildUninstallReport([...selectedTargets], assetIds, result));
      } catch (error) {
        stopProgress();
        log(`Error: ${error instanceof Error ? error.message : "unknown error"}`);
        render();
      }
    }
  }

  // ── Scope Selector Overlay (PRD) ──────────────────────────────────
  function showScopeSelector(): Promise<InstallScope | null> {
    return new Promise((resolve) => {
      let currentScope: InstallScope = scope;
      const items = [
        currentScope === "global" ? `{${currentColors.brandYellow}-fg}{bold}[x] Global (user level){/bold}{/${currentColors.brandYellow}-fg}` : `[ ] Global (user level)`,
        currentScope === "project" ? `{${currentColors.brandYellow}-fg}{bold}[x] Project (local){/bold}{/${currentColors.brandYellow}-fg}` : `[ ] Project (local)`
      ];
      const scopeBox = blessed.list({
        parent: screen, border: "line", height: "shrink", width: "40%",
        top: "center", left: "center",
        label: ` ${BIRD_ASCII} Install Scope `, tags: true, keys: true, mouse: true,
        shadow: true,
        style: { border: { fg: currentColors.brandYellow }, bg: PALETTE.carbon, fg: PALETTE.ghostWhite },
        items
      });
      scopeBox.focus();
      screen.render();

      function refreshItems(): void {
        scopeBox.setItems([
          currentScope === "global" ? `{${currentColors.brandYellow}-fg}{bold}[x] Global (user level){/bold}{/${currentColors.brandYellow}-fg}` : `[ ] Global (user level)`,
          currentScope === "project" ? `{${currentColors.brandYellow}-fg}{bold}[x] Project (local){/bold}{/${currentColors.brandYellow}-fg}` : `[ ] Project (local)`
        ]);
        screen.render();
      }

      scopeBox.key("space", () => {
        currentScope = currentScope === "global" ? "project" : "global";
        refreshItems();
      });
      scopeBox.key(["enter"], () => { scopeBox.detach(); resolve(currentScope); });
      scopeBox.key(["escape", "q"], () => { scopeBox.detach(); resolve(null); });
      scopeBox.on("select", (_item, index) => {
        currentScope = index === 0 ? "global" : "project";
        scopeBox.detach();
        resolve(currentScope);
      });
    });
  }

  // ── Target Selector Overlay ────────────────────────────────────────
  function showTargetSelector(): Promise<SupportedTarget[] | null> {
    return new Promise((resolve) => {
      const targetsArr = allTargets;
      const currentSelection = new Set(selectedTargets);
      let listIndex = 0;

      const targetBox = blessed.list({
        parent: screen, border: "line", height: "50%", width: "40%",
        top: "center", left: "center",
        label: ` ${BIRD_ASCII} Select Targets `, tags: true, keys: true, vi: true, mouse: true, shadow: true,
        style: { ...getSelectedListStyle(currentColors), border: { fg: currentColors.brandYellow } },
        items: targetsArr.map((t) =>
          currentSelection.has(t)
            ? `{${currentColors.brandYellow}-fg}{bold}[x]{/bold}{/${currentColors.brandYellow}-fg} ${t}`
            : `[ ] ${t}`
        )
      });
      const hintBox = blessed.box({
        parent: screen, top: "50%", left: "30%", width: "40%", height: "shrink",
        tags: true, content: `{${PALETTE.dimGray}-fg}space toggle  a all  A none  enter done{/${PALETTE.dimGray}-fg}`
      });
      targetBox.focus();
      screen.render();

      function refreshTargetItems(): void {
        targetBox.setItems(targetsArr.map((t) =>
          currentSelection.has(t)
            ? `{${currentColors.brandYellow}-fg}{bold}[x]{/bold}{/${currentColors.brandYellow}-fg} {bold}${t}{/bold}`
            : `[ ] ${t}`
        ));
        screen.render();
      }

      targetBox.key("space", () => {
        const sel = targetsArr[listIndex];
        if (currentSelection.has(sel)) currentSelection.delete(sel); else currentSelection.add(sel);
        refreshTargetItems();
      });
      targetBox.key("a", () => { targetsArr.forEach((t) => currentSelection.add(t)); refreshTargetItems(); });
      targetBox.key("A", () => { currentSelection.clear(); refreshTargetItems(); });
      targetBox.key(["enter", "escape", "C-c", "q"], () => {
        targetBox.detach(); hintBox.detach();
        if (!currentSelection.has(primaryTarget) && currentSelection.size > 0) {
          primaryTarget = [...currentSelection][0];
        }
        selectedTargets.clear();
        for (const t of currentSelection) selectedTargets.add(t);
        resolve(currentSelection.size > 0 ? [...currentSelection] : null);
        skillList.focus();
        render();
      });
      targetBox.on("select", (_item, index) => { listIndex = index; });
    });
  }

  // ── Archive Toggle ─────────────────────────────────────────────────
  async function toggleArchive(): Promise<void> {
    const visibleSkills = getVisibleSkills();
    const highlighted = visibleSkills[getSelectedIndex(skillList)] ?? visibleSkills[0];
    const assetIds = selectedIds.size > 0
      ? [...selectedIds]
      : highlighted ? [highlighted.id] : [];

    if (assetIds.length === 0) { log("No skills selected."); render(); return; }

    const skillToCheck = skills.find((s) => s.id === assetIds[0]);
    const currentlyArchived = skillToCheck?.archived ?? false;

    try {
      const result = await archiveSkills({
        assetIds, archived: !currentlyArchived, scope,
        projectDir: options.projectDir, selectedTargets: [...selectedTargets],
        platform: options.platform
      });
      selectedIds.clear();
      await refresh(
        result.archived.length > 0 ? `Archived ${result.archived.join(", ")}.` : `Unarchived ${result.unarchived.join(", ")}.`
      );
    } catch (error) {
      log(`Error: ${error instanceof Error ? error.message : "unknown error"}`);
      render();
    }
  }

  // ── Report Builder ─────────────────────────────────────────────────
  function buildInstallReport(targets: SupportedTarget[], assetIds: string[], result: InstallSkillsResult): string {
    const lines: string[] = [];
    lines.push(`═══ Sync Complete ═══`);
    lines.push("");
    const installedByTarget = new Map<SupportedTarget, string[]>();
    const skippedByTarget = new Map<SupportedTarget, Array<{ assetId: string; reason: string }>>();
    for (const t of targets) { installedByTarget.set(t, []); skippedByTarget.set(t, []); }
    for (const inst of result.installed) { installedByTarget.get(inst.target)?.push(inst.assetId); }
    for (const sk of result.skipped) { skippedByTarget.get(sk.target ?? targets[0])?.push({ assetId: sk.assetId, reason: sk.reason }); }
    for (const target of targets) {
      const installed = installedByTarget.get(target) ?? [];
      const skipped = skippedByTarget.get(target) ?? [];
      const total = assetIds.length;
      const parts: string[] = [];
      if (installed.length > 0) parts.push(`${installed.length}/${total} success`);
      if (skipped.length > 0) parts.push(`${skipped.length} skipped`);
      lines.push(`  ${target}  (${parts.join(", ")})`);
      for (const aid of assetIds) {
        if (installed.includes(aid)) lines.push(`    \u2714 ${aid}`);
        else { const s = skipped.find((x) => x.assetId === aid); lines.push(s ? `    \u25E6 ${aid} \u2192 ${s.reason}` : `    \u2716 ${aid}`); }
      }
      lines.push("");
    }
    return lines.join("\n");
  }

  function buildUninstallReport(targets: SupportedTarget[], assetIds: string[], result: UninstallSkillsResult): string {
    const lines: string[] = [];
    lines.push("═══ UNINSTALL COMPLETE ═══");
    lines.push("");
    const removedByTarget = new Map<SupportedTarget, string[]>();
    const skippedByTarget = new Map<SupportedTarget, Array<{ assetId: string; reason: string }>>();
    for (const t of targets) { removedByTarget.set(t, []); skippedByTarget.set(t, []); }
    for (const r of result.removed) { removedByTarget.get(r.target)?.push(r.assetId); }
    for (const sk of result.skipped) { skippedByTarget.get(sk.target)?.push({ assetId: sk.assetId, reason: sk.reason }); }
    for (const target of targets) {
      const removed = removedByTarget.get(target) ?? [];
      const skipped = skippedByTarget.get(target) ?? [];
      const total = assetIds.length;
      const parts: string[] = [];
      if (removed.length > 0) parts.push(`${removed.length}/${total} success`);
      if (skipped.length > 0) parts.push(`${skipped.length} skipped`);
      lines.push(`  ${target}  (${parts.join(", ")})`);
      for (const aid of assetIds) {
        if (removed.includes(aid)) lines.push(`    \u2714 ${aid}`);
        else { const s = skipped.find((x) => x.assetId === aid); lines.push(s ? `    \u25E6 ${aid} \u2192 ${s.reason}` : `    \u2716 ${aid}`); }
      }
      lines.push("");
    }
    return lines.join("\n");
  }

  function showReport(content: string): void {
    const reportBox = blessed.box({
      parent: screen, top: "center", left: "center", width: "70%", height: "60%",
      border: { type: "line" },
      style: { fg: PALETTE.ghostWhite, bg: PALETTE.carbon, border: { fg: currentColors.brandYellow } },
      content: content + "\n\n{center}{bold}Press ESC or q to close{/bold}{/center}",
      scrollable: true, alwaysScroll: true, keys: true, vi: true, mouse: true, tags: true, label: " Report "
    });
    reportBox.focus();
    screen.render();
    reportBox.key(["escape", "q"], () => { reportBox.detach(); screen.render(); });
  }

  function log(message: string): void {
    operationLog.unshift(`${new Date().toLocaleTimeString()} ${message}`);
    operationLog.splice(8);
  }

  // ── Key Bindings ───────────────────────────────────────────────────
  screen.key(["q", "C-c"], () => { screen.destroy(); });

  screen.key("left", () => {
    const panels = ["hive", "cells", "nectar"];
    const idx = panels.indexOf(focusPanel);
    focusPanel = panels[(idx - 1 + panels.length) % panels.length] as typeof focusPanel;
    updatePanelFocus();
    render();
  });
  screen.key("right", () => {
    const panels = ["hive", "cells", "nectar"];
    const idx = panels.indexOf(focusPanel);
    focusPanel = panels[(idx + 1) % panels.length] as typeof focusPanel;
    updatePanelFocus();
    render();
  });

  detailBox.key(["up", "down"], (_ch, key) => {
    detailBox.scroll(key.name === "up" ? -1 : 1);
    screen.render();
  });

  screen.key("enter", () => {
    if (focusPanel === "cells") {
      focusPanel = "nectar";
      updatePanelFocus();
      render();
    }
  });

  screen.key("space", () => {
    if (focusPanel === "hive") {
      // Group selection
      const idx = getSelectedIndex(hiveList);
      const group = allGroups[idx];
      if (group) {
        if (selectedGroups.has(group.id)) selectedGroups.delete(group.id);
        else selectedGroups.add(group.id);
        render();
      }
    } else {
      // Skill selection
      const visibleSkills = getVisibleSkills();
      const skill = visibleSkills[getSelectedIndex(skillList)] ?? visibleSkills[0];
      if (!skill) return;
      if (selectedIds.has(skill.id)) selectedIds.delete(skill.id);
      else selectedIds.add(skill.id);
      render();
    }
  });

  screen.key("A", () => {
    for (const group of allGroups) selectedGroups.add(group.id);
    render();
  });
  screen.key(["S-a", "A-s"], () => {
    selectedGroups.clear();
    render();
  });

  screen.key("p", async () => {
    const visibleSkills = getVisibleSkills();
    const highlighted = visibleSkills[getSelectedIndex(skillList)] ?? visibleSkills[0];
    const assetIds = selectedIds.size > 0 ? [...selectedIds] : highlighted ? [highlighted.id] : [];
    if (assetIds.length === 0) { log("No skills selected."); render(); return; }
    try {
      await showSyncPreview(assetIds, [...selectedTargets]);
    } catch (error) {
      log(`Preview error: ${error instanceof Error ? error.message : "unknown error"}`);
      render();
    }
  });
  screen.key("I", () => { void applySkillOverride("include"); });
  screen.key("X", () => { void applySkillOverride("exclude"); });
  screen.key("d", () => { void applySkillOverride("default"); });
  screen.key("i", () => { void mutate("install"); });
  screen.key("u", () => { void mutate("uninstall"); });
  screen.key("x", () => { void toggleArchive(); });

  screen.key("r", async () => {
    const toRepair = [...brokenIds].filter((id) => skills.some((s) => s.id === id));
    if (toRepair.length === 0) { log("No broken skills to repair."); render(); return; }
    startProgress("Repairing broken skills");
    try {
      await installSkills({
        assetIds: toRepair, scope, projectDir: options.projectDir,
        selectedTargets: [...selectedTargets], includeArchived, platform: options.platform
      });
      stopProgress();
      await refresh(`Repaired ${toRepair.length} broken skills.`);
    } catch (error) {
      stopProgress();
      log(`Repair error: ${error instanceof Error ? error.message : "unknown error"}`);
      render();
    }
  });

  screen.key("v", () => { viewMode = viewMode === "list" ? "matrix" : "list"; skillList.select(0); render(); });
  screen.key("N", () => { detailTab = (detailTab + 1) % DETAIL_TABS.length; renderSelectedSkillDetail(); screen.render(); });
  screen.key("t", () => { void showTargetSelector(); });

  screen.key("s", async () => {
    scope = scope === "global" ? "project" : "global";
    await refresh(`Scope changed to ${scope}.`);
  });
  screen.key("a", async () => {
    includeArchived = !includeArchived;
    selectedIds.clear();
    await refresh(`Archived skills ${includeArchived ? "shown" : "hidden"}.`);
  });

  screen.key("T", async () => {
    const idx = THEME_NAMES.indexOf(currentTheme as typeof THEME_NAMES[number]);
    const next = THEME_NAMES[(idx + 1) % THEME_NAMES.length];
    currentTheme = next;
    currentColors = getTheme(next);
    await saveTheme(platformContext.configBaseDir, next);
    render();
  });

  screen.key("S", async () => {
    const catalog = await loadCatalog();
    const allSources = catalog.sources;
    const userConfig = cachedUserConfig ?? await loadUserConfig(platformContext.configBaseDir);
    showSourceToggle(screen, {
      configBaseDir: platformContext.configBaseDir,
      currentColors,
      sources: allSources,
      userConfig,
      onToggle: async (_sourceId, _enabled) => {
        await refresh("Sources updated.");
      }
    });
  });

  screen.key("c", async () => {
    blessed.prompt({
      parent: screen, border: "line", height: "shrink", width: "50%",
      top: "center", left: "center", label: " Create Group "
    }).input("Group name:", "", async (_err, name) => {
      if (!name) { skillList.focus(); screen.render(); return; }
      blessed.prompt({
        parent: screen, border: "line", height: "shrink", width: "60%",
        top: "center", left: "center", label: " Group Skills "
      }).input("Skill IDs (comma-separated):", "", async (_err2, skillsStr) => {
        if (!skillsStr) { skillList.focus(); render(); return; }
        const skillIds = skillsStr.split(",").map((s) => s.trim()).filter(Boolean);
        await saveUserGroup(platformContext.configBaseDir, { name, label: name, skills: skillIds });
        await refresh(`Group "${name}" created.`);
        skillList.focus();
      });
    });
  });

  screen.key("E", async () => {
    const userConfig = await loadUserConfig(platformContext.configBaseDir);
    if (userConfig.groups.length === 0) { log("No custom groups to edit."); render(); return; }
    const groupBox = blessed.list({
      parent: screen, border: "line", height: "shrink", width: "40%",
      top: "center", left: "center", label: " Edit Group ", tags: true, keys: true,
      style: { ...getSelectedListStyle(currentColors), border: { fg: currentColors.brandYellow } },
      items: userConfig.groups.map((g) => `  ${g.name}`)
    });
    groupBox.focus(); screen.render();
    groupBox.key(["escape", "q"], () => { groupBox.detach(); skillList.focus(); render(); });
    groupBox.on("select", async (_item, index) => {
      const group = userConfig.groups[index];
      if (!group) return;
      groupBox.detach();
      blessed.prompt({
        parent: screen, border: "line", height: "shrink", width: "60%",
        top: "center", left: "center", label: ` Edit ${group.name} `
      }).input("Skill IDs (comma-separated):", "", async (_err, skillsStr) => {
        if (!skillsStr) { skillList.focus(); render(); return; }
        const skillIds = skillsStr.split(",").map((s) => s.trim()).filter(Boolean);
        await saveUserGroup(platformContext.configBaseDir, { name: group.name, label: group.name, skills: skillIds });
        await refresh(`Group "${group.name}" updated.`);
        skillList.focus();
      });
    });
  });

  screen.key("D", async () => {
    const userConfig = await loadUserConfig(platformContext.configBaseDir);
    if (userConfig.groups.length === 0) { log("No custom groups to delete."); render(); return; }
    const groupBox = blessed.list({
      parent: screen, border: "line", height: "shrink", width: "40%",
      top: "center", left: "center", label: " Delete Group ", tags: true, keys: true,
      style: { ...getSelectedListStyle(currentColors), border: { fg: currentColors.brandYellow } },
      items: userConfig.groups.map((g) => `  ${g.name}`)
    });
    groupBox.focus(); screen.render();
    groupBox.key(["escape", "q"], () => { groupBox.detach(); skillList.focus(); render(); });
    groupBox.on("select", async (_item, index) => {
      const group = userConfig.groups[index];
      if (!group) return;
      groupBox.detach();
      await removeUserGroup(platformContext.configBaseDir, group.name);
      await refresh(`Group "${group.name}" deleted.`);
      skillList.focus();
    });
  });

  screen.key("/", () => {
    blessed.prompt({
      parent: screen, border: "line", height: "shrink", width: "50%",
      top: "center", left: "center", label: " Search "
    }).input("Query", query, (_error, value) => {
      query = value ?? "";
      skillList.select(0);
      render();
      skillList.focus();
    });
  });

  screen.key(["?", "C-slash"], () => {
    const helpBox = blessed.box({
      parent: screen, border: "line", height: "80%", width: "60%",
      top: "center", left: "center",
      label: ` ${BIRD_ASCII} Keyboard Shortcuts `, tags: true, keys: true, vi: true, mouse: true, shadow: true,
      content: COMMAND_HELP,
      style: { bg: PALETTE.carbon, fg: PALETTE.ghostWhite, border: { fg: currentColors.brandYellow } }
    });
    helpBox.focus(); screen.render();
    helpBox.key(["escape", "q"], () => { helpBox.detach(); screen.render(); skillList.focus(); });
  });

  // ── Event Listeners ────────────────────────────────────────────────
  hiveList.on("select", async (_item, index) => {
    const group = allGroups[index];
    if (group) {
      if (selectedGroups.has(group.id)) selectedGroups.delete(group.id);
      else selectedGroups.add(group.id);
      skillList.select(0);
      render();
      skillList.focus();
    }
  });

  skillList.on("select item", () => {
    if (isRendering) return;
    renderSelectedSkillDetail();
    screen.render();
  });

  // ── Start ──────────────────────────────────────────────────────────
  skillList.focus();
  await refresh();

  return new Promise((resolve) => { screen.on("destroy", resolve); });
}

// ── Helpers ────────────────────────────────────────────────────────────
async function loadSkillPreview(skill: ManagerSkillRecord): Promise<string> {
  if (skill.origin !== "owned") return "";
  try {
    const content = await readFile(join(ownedSkillsRoot, skill.id, "SKILL.md"), "utf8");
    const lines = content.split("\n").filter((l) => !l.startsWith("---") && !l.startsWith("metadata:") && !l.startsWith("compatibility:"));
    return lines.slice(0, 12).map((l) => l.length > 60 ? l.slice(0, 60) + "..." : l || " ").join("\n");
  } catch { return ""; }
}

function getRelatedSkills(skill: ManagerSkillRecord, allSkills: ManagerSkillRecord[]): ManagerSkillRecord[] {
  const ownTags = new Set(skill.tags);
  if (ownTags.size === 0) return [];
  return allSkills
    .filter((s) => s.id !== skill.id && s.tags.some((t) => ownTags.has(t)))
    .sort((a, b) => {
      const aCommon = a.tags.filter((t) => ownTags.has(t)).length;
      const bCommon = b.tags.filter((t) => ownTags.has(t)).length;
      return bCommon - aCommon;
    });
}

function filterSkillsByGroups(
  skills: ManagerSkillRecord[],
  selectedGroups: Set<string>,
  query: string,
  includeArchived: boolean,
  selectedTargets: Set<SupportedTarget>,
  primaryTarget: SupportedTarget
): ManagerSkillRecord[] {
  const normalizedQuery = query.trim().toLowerCase();
  const hasGroupFilter = selectedGroups.size > 0;

  return skills.filter((skill) => {
    // Archive filter
    if (!includeArchived && skill.archived) return false;

    // Group filter (OR logic)
    if (hasGroupFilter && !selectedGroups.has(skill.group)) return false;

    // Query filter
    if (normalizedQuery) {
      const matches = [skill.id, skill.description, skill.group, skill.subgroup, skill.sourceId, ...skill.tags, ...skill.customTags]
        .some((v) => v?.toLowerCase().includes(normalizedQuery));
      if (!matches) return false;
    }

    return true;
  });
}

function getSelectedIndex(list: blessed.Widgets.ListElement): number {
  return (list as blessed.Widgets.ListElement & { selected?: number }).selected ?? 0;
}
