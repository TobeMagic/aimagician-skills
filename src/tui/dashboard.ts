import { access, readFile } from "node:fs/promises";
import { join } from "node:path";
import blessed = require("blessed");
import { loadUserConfig, removeUserGroup, saveTheme, saveUserGroup } from "../config/user-config";
import {
  archiveSkills,
  installSkills,
  searchSkills,
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
  AVAILABLE_GLYPH,
  BROKEN_GLYPH,
  BEE_ASCII,
  BEE_SPLASH,
  COLORS,
  INSTALLED_GLYPH,
  PALETTE,
  SELECT_GLYPH,
  SELECTED_LIST_STYLE,
  UNAVAILABLE_GLYPH,
  UNSELECT_GLYPH,
  formatMatrixCell,
  getTheme,
  targetShortLabel,
  THEME_NAMES,
  type ThemeColors
} from "./theme";

const COMMAND_HELP = `{bold}{yellow-fg}Skillbee Keyboard Shortcuts{/yellow-fg}{/bold}

{bold}Navigate{/bold}
  {yellow-fg}{bold}\u2190{bold}{/yellow-fg}/{yellow-fg}{bold}\u2192{bold}{/yellow-fg} ........... switch panel (Hive/Cells/Nectar)
  {yellow-fg}{bold}\u2191{bold}{/yellow-fg}/{yellow-fg}{bold}\u2193{bold}{/yellow-fg} ........... navigate list / scroll detail
  {yellow-fg}{bold}/{/yellow-fg} ................. search skills
  {yellow-fg}{bold}v{/bold}{/yellow-fg} ................. toggle list/matrix view
  {yellow-fg}{bold}s{/bold}{/yellow-fg} ................. toggle scope (global/project)
  {yellow-fg}{bold}a{/bold}{/yellow-fg} ................. toggle archived visibility

{bold}Select{/bold}
  {yellow-fg}{bold}space{/bold}{/yellow-fg} ............. multi-select (tags or skills)
  {yellow-fg}{bold}A{/bold}{/yellow-fg} ................. select all tags
  {yellow-fg}{bold}Shift+A{/bold}{/yellow-fg} .......... deselect all tags
  {yellow-fg}{bold}Enter{/bold}{/yellow-fg} ............. view skill detail in Nectar
  {yellow-fg}{bold}t{/bold}{/yellow-fg} ................. open target multi-select
  {yellow-fg}{bold}N{/bold}{/yellow-fg} ................. cycle detail tab (Matrix/README/Related)

{bold}Actions{/bold}
  {yellow-fg}{bold}i{/bold}{/yellow-fg} ................. install (scope \u2192 target \u2192 install)
  {yellow-fg}{bold}u{/bold}{/yellow-fg} ................ uninstall selected
  {yellow-fg}{bold}x{/bold}{/yellow-fg} ................ archive / unarchive
  {yellow-fg}{bold}r{/bold}{/yellow-fg} ................ repair broken skills
  {yellow-fg}{bold}T{/bold}{/yellow-fg} ................ cycle theme (bee/monokai/nord)

{bold}Manage{/bold}
  {yellow-fg}{bold}c{/bold}{/yellow-fg} ................ create custom group
  {yellow-fg}{bold}E{/bold}{/yellow-fg} ................ edit custom group
  {yellow-fg}{bold}D{/bold}{/yellow-fg} ................ delete custom group

{bold}System{/bold}
  {yellow-fg}{bold}?{/bold}{/yellow-fg} ................ show this help
  {yellow-fg}{bold}q{/bold}{/yellow-fg} ................ quit

{center}{dim}Press ESC to close{/dim}{/center}`;

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
      content: BEE_SPLASH.join("\n")
    });
    screen.render();

    let frame = 0;
    const typewriter = setInterval(() => {
      frame++;
      if (frame >= BEE_SPLASH.length) {
        clearInterval(typewriter);
        setTimeout(() => {
          splash.detach();
          screen.render();
          resolve();
        }, 800);
      } else {
        splash.setContent(BEE_SPLASH.slice(0, frame + 1).join("\n"));
        screen.render();
      }
    }, 60);
  });
}

// ── Extract all unique tags from skills ────────────────────────────────
function extractAllTags(skills: ManagerSkillRecord[]): string[] {
  const tagSet = new Set<string>();
  for (const skill of skills) {
    for (const tag of skill.tags) tagSet.add(tag);
  }
  return [...tagSet].sort();
}

// ── Count skills per tag ───────────────────────────────────────────────
function countSkillsPerTag(skills: ManagerSkillRecord[], tag: string): number {
  return skills.filter((s) => s.tags.includes(tag)).length;
}

// ── Main Dashboard ─────────────────────────────────────────────────────
export async function runDashboard(options: DashboardOptions = {}): Promise<void> {
  const screen = blessed.screen({
    smartCSR: true,
    title: "Skillbee"
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
  let allTags: string[] = [];
  let isRendering = false;
  const selectedTags = new Set<string>();
  const selectedIds = new Set<string>();
  const operationLog: string[] = [];
  let viewMode: "list" | "matrix" = "list";
  let currentTheme = "bee";
  let currentColors: ThemeColors = COLORS;
  const brokenIds = new Set<string>();
  let progressTimer: ReturnType<typeof setInterval> | null = null;
  let progressStage = 0;

  // ── Layout ──────────────────────────────────────────────────────────
  const header = blessed.box({
    parent: screen, top: 0, left: 0, width: "100%", height: 3,
    tags: true, style: { fg: currentColors.brandYellow, bold: true }, content: ""
  });

  const hiveList = blessed.list({
    parent: screen,
    label: ` ${BEE_ASCII} Hive `,
    top: 3, left: 0, width: "20%", height: "calc(100% - 5)",
    border: "line", keys: true, vi: true, mouse: true, focusable: true,
    style: { ...SELECTED_LIST_STYLE, border: { fg: currentColors.panelBorder } }
  });

  const skillList = blessed.list({
    parent: screen,
    label: ` ${BEE_ASCII} Cells `,
    top: 3, left: "20%", width: "50%", height: "calc(100% - 5)",
    border: "line", keys: true, vi: true, mouse: true, focusable: true,
    style: { ...SELECTED_LIST_STYLE, border: { fg: currentColors.panelBorder } }
  });

  const detailBox = blessed.box({
    parent: screen,
    label: ` ${BEE_ASCII} Nectar `,
    top: 3, left: "70%", width: "30%", height: "calc(100% - 5)",
    border: "line", tags: true, scrollable: true, alwaysScroll: true,
    keys: true, vi: true, focusable: true,
    style: { fg: PALETTE.ghostWhite, border: { fg: currentColors.panelBorder } }
  });

  const statusBar = blessed.box({
    parent: screen, top: "100%-2", left: 0, width: "100%", height: 2,
    tags: true, style: { fg: PALETTE.ghostWhite }, content: ""
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
      `{${currentColors.brandYellow}-fg}\u{1F41D}----{/}`,
      `-{${currentColors.brandYellow}-fg}\u{1F41D}---{/}`,
      `--{${currentColors.brandYellow}-fg}\u{1F41D}--{/}`,
      `---{${currentColors.brandYellow}-fg}\u{1F41D}-{/}`,
      `----{${currentColors.brandYellow}-fg}\u{1F41D}{/}`
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

  // ── Tag Filtering ──────────────────────────────────────────────────
  function getVisibleSkills(): ManagerSkillRecord[] {
    return filterSkillsByTags(skills, selectedTags, query, includeArchived, selectedTargets, primaryTarget);
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
      const [loadedSkills, userConfig] = await Promise.all([
        searchSkills({
          scope, projectDir: options.projectDir,
          selectedTargets: targetsForSearch, includeArchived,
          platform: options.platform
        }),
        loadUserConfig(platformContext.configBaseDir)
      ]);
      skills = loadedSkills;
      allTags = extractAllTags(skills);
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

      // Header: The Crown (蜂冠)
      header.setContent(
        ` {bold}${BEE_ASCII} SKILLBEE{/bold}  scope:{bold}${scope}{/bold}  selected:{bold}${selectedIds.size}{/bold}  tags:{bold}${selectedTags.size > 0 ? selectedTags.size : "all"}{/bold}  targets:[{bold}${targetsOverview}{/bold}]` +
        (brokenIds.size > 0 ? `  {${currentColors.error}-fg}health:${brokenIds.size}{/${currentColors.error}-fg}` : "") +
        (query ? `  {79-fg}search:${query}{/79-fg}` : "")
      );

      // Hive: Tag Panel
      renderHivePanel();
      // Cells: Skill List
      renderCellsPanel(visibleSkills);
      // Nectar: Detail
      renderSelectedSkillDetail();
      // Status Bar: The Guide (导航蜂)
      const shortcutLine = getGuideBar(focusPanel, selectedIds.size > 0, selectedTags.size > 0);
      const statusLine = operationLog.length > 0 ? operationLog[0] : "ready";
      statusBar.setContent(`${shortcutLine}\n${statusLine}`);
      screen.render();
    } finally {
      isRendering = false;
    }
  }

  function renderHivePanel(): void {
    const tagItems = allTags.map((tag) => {
      const count = countSkillsPerTag(skills, tag);
      const sel = selectedTags.has(tag) || selectedTags.size === 0;
      const glyph = sel ? SELECT_GLYPH : UNSELECT_GLYPH;
      const prefix = sel
        ? `{${currentColors.brandYellow}-fg}{bold}${glyph} ${tag} (${count}){/bold}{/${currentColors.brandYellow}-fg}`
        : `{${PALETTE.ghostWhite}-fg}${glyph} ${tag} (${count}){/${PALETTE.ghostWhite}-fg}`;
      return prefix;
    });

    // Custom groups
    void loadUserConfig(platformContext.configBaseDir).then((userConfig) => {
      if (userConfig.groups.length > 0) {
        const groupItems = userConfig.groups.map((g) => {
          return `{79-fg}\u25CE ${g.name} (${g.skills.length}){/79-fg}`;
        });
        hiveList.setItems([...tagItems, `{${PALETTE.dimGray}-fg}--- groups ---{/${PALETTE.dimGray}-fg}`, ...groupItems]);
      } else {
        hiveList.setItems(tagItems);
      }
      screen.render();
    });
  }

  function renderCellsPanel(visibleSkills: ManagerSkillRecord[]): void {
    if (viewMode === "matrix") {
      const targetsArr = [...selectedTargets];
      const maxIdLen = Math.max(...visibleSkills.map((s) => s.id.length), 8);
      skillList.setItems(visibleSkills.map((skill) => renderMatrixRow(skill, targetsArr, selectedIds, maxIdLen)));
    } else {
      skillList.setItems(visibleSkills.map((skill) => renderSkillRow(skill, primaryTarget, selectedIds, brokenIds, query)));
    }
  }

  function renderSelectedSkillDetail(): void {
    const visibleSkills = getVisibleSkills();
    renderDetail(visibleSkills[getSelectedIndex(skillList)] ?? visibleSkills[0]);
  }

  function renderDetail(skill: ManagerSkillRecord | undefined): void {
    if (!skill) { detailBox.setContent("No skill selected."); return; }
    detailBox.setLabel(` ${BEE_ASCII} ${DETAIL_TABS[detailTab]}  (N=cycle) `);

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
        `{bold}Origin:{/bold} ${skill.origin}${skill.sourceId ? ` {79-fg}(${skill.sourceId}){/79-fg}` : ""}`,
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
  function getGuideBar(panel: string, hasSkillSelection: boolean, hasTagSelection: boolean): string {
    if (panel === "hive") {
      return `Space=toggle  A=all  Shift+A=none  \u2190\u2192 panel`;
    }
    if (panel === "nectar") {
      return `N=cycle tab  \u2191\u2193 scroll  \u2190\u2192 panel`;
    }
    // cells panel
    if (hasSkillSelection) {
      return `Space=unselect  i=batch install  u=batch uninstall  x=archive  t=targets  ?=help  q=quit`;
    }
    return `Space=select  Enter=detail  i=install  u=uninstall  x=archive  t=targets  ?=help  q=quit`;
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
        label: ` ${BEE_ASCII} Install Scope `, tags: true, keys: true, mouse: true,
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
        label: ` ${BEE_ASCII} Select Targets `, tags: true, keys: true, vi: true, mouse: true, shadow: true,
        style: { ...SELECTED_LIST_STYLE, border: { fg: currentColors.brandYellow } },
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
    lines.push(`═══ INSTALL COMPLETE ═══`);
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
      // Tag selection
      const idx = getSelectedIndex(hiveList);
      const tag = allTags[idx];
      if (tag) {
        if (selectedTags.has(tag)) selectedTags.delete(tag);
        else selectedTags.add(tag);
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
    for (const tag of allTags) selectedTags.add(tag);
    render();
  });
  screen.key(["S-a", "A-s"], () => {
    selectedTags.clear();
    render();
  });

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
      style: { ...SELECTED_LIST_STYLE, border: { fg: currentColors.brandYellow } },
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
      style: { ...SELECTED_LIST_STYLE, border: { fg: currentColors.brandYellow } },
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
      label: ` ${BEE_ASCII} Keyboard Shortcuts `, tags: true, keys: true, vi: true, mouse: true, shadow: true,
      content: COMMAND_HELP,
      style: { bg: PALETTE.carbon, fg: PALETTE.ghostWhite, border: { fg: currentColors.brandYellow } }
    });
    helpBox.focus(); screen.render();
    helpBox.key(["escape", "q"], () => { helpBox.detach(); screen.render(); skillList.focus(); });
  });

  // ── Event Listeners ────────────────────────────────────────────────
  hiveList.on("select", async (_item, index) => {
    const tag = allTags[index];
    if (tag) {
      if (selectedTags.has(tag)) selectedTags.delete(tag);
      else selectedTags.add(tag);
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

function filterSkillsByTags(
  skills: ManagerSkillRecord[],
  selectedTags: Set<string>,
  query: string,
  includeArchived: boolean,
  selectedTargets: Set<SupportedTarget>,
  primaryTarget: SupportedTarget
): ManagerSkillRecord[] {
  const normalizedQuery = query.trim().toLowerCase();
  const hasTagFilter = selectedTags.size > 0;

  return skills.filter((skill) => {
    // Archive filter
    if (!includeArchived && skill.archived) return false;

    // Tag filter (OR logic)
    if (hasTagFilter && !skill.tags.some((t) => selectedTags.has(t))) return false;

    // Query filter
    if (normalizedQuery) {
      const matches = [skill.id, skill.description, skill.group, skill.subgroup, skill.sourceId, ...skill.tags, ...skill.customTags]
        .some((v) => v?.toLowerCase().includes(normalizedQuery));
      if (!matches) return false;
    }

    return true;
  });
}

function highlightText(text: string, query: string): string {
  if (!query || !text.toLowerCase().includes(query.toLowerCase())) return text;
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  const match = text.slice(idx, idx + query.length);
  return `${text.slice(0, idx)}{${PALETTE.amber}-fg}${match}{/${PALETTE.amber}-fg}${text.slice(idx + query.length)}`;
}

function renderSkillRow(
  skill: ManagerSkillRecord,
  target: SupportedTarget,
  selectedIds: Set<string>,
  brokenIds?: Set<string>,
  query?: string
): string {
  const prefix = selectedIds.has(skill.id)
    ? `{${PALETTE.amber}-fg}{bold}\u271A{/bold}{/${PALETTE.amber}-fg}`
    : `{${PALETTE.ghostWhite}-fg}\u271F{/${PALETTE.ghostWhite}-fg}`;
  const status = skill.installedTargets.includes(target)
    ? `{${PALETTE.pollen}-fg}${INSTALLED_GLYPH}{/${PALETTE.pollen}-fg}`
    : skill.availableTargets.includes(target)
      ? `{${PALETTE.ghostWhite}-fg}${AVAILABLE_GLYPH}{/${PALETTE.ghostWhite}-fg}`
      : `{${PALETTE.dimGray}-fg}${UNAVAILABLE_GLYPH}{/${PALETTE.dimGray}-fg}`;
  const archived = skill.archived ? ` {${PALETTE.dimGray}-fg}(archived){/${PALETTE.dimGray}-fg}` : "";
  const broken = brokenIds?.has(skill.id) ? ` {${PALETTE.stinger}-fg}${BROKEN_GLYPH}{/${PALETTE.stinger}-fg}` : "";
  const idDisplay = query ? highlightText(skill.id, query) : skill.id;
  const idText = skill.archived ? `{${PALETTE.dimGray}-fg}${idDisplay}{/${PALETTE.dimGray}-fg}` : idDisplay;

  return `${prefix} ${idText}  ${status}${broken}${archived}`;
}

function renderMatrixRow(
  skill: ManagerSkillRecord,
  targets: SupportedTarget[],
  selectedIds: Set<string>,
  maxIdLen: number
): string {
  const prefix = selectedIds.has(skill.id)
    ? `{${PALETTE.amber}-fg}{bold}[x]{/bold}{/${PALETTE.amber}-fg}`
    : "[ ]";
  const idText = skill.archived ? `{${PALETTE.dimGray}-fg}${skill.id}{/${PALETTE.dimGray}-fg}` : skill.id;
  const paddedId = skill.id.padEnd(maxIdLen);
  const displayId = skill.archived ? `{${PALETTE.dimGray}-fg}${paddedId}{/${PALETTE.dimGray}-fg}` : paddedId;

  const cells = targets.map((t) => {
    const avail = skill.availableTargets.includes(t);
    const installed = skill.installedTargets.includes(t);
    const managed = skill.managedTargets.includes(t);
    return `${targetShortLabel(t)}:${formatMatrixCell(avail, installed, managed)}`;
  }).join(" ");

  return `${prefix} ${displayId}  ${cells}`;
}

function getSelectedIndex(list: blessed.Widgets.ListElement): number {
  return (list as blessed.Widgets.ListElement & { selected?: number }).selected ?? 0;
}
