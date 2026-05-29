import { readFile } from "node:fs/promises";
import { join } from "node:path";
import blessed = require("blessed");
import { loadUserConfig, saveTheme } from "../config/user-config";
import {
  archiveSkills,
  installSkills,
  resetSkills,
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
  BEE_ASCII,
  COLORS,
  SELECTED_LIST_STYLE,
  formatMatrixCell,
  getTheme,
  targetShortLabel,
  THEME_NAMES,
  type ThemeColors
} from "./theme";

const USER_GROUP_PREFIX = "@ ";

export interface FilterState {
  installedStatus: "all" | "installed" | "uninstalled";
  filterTarget: SupportedTarget | null;
  tag: string | null;
}

const DEFAULT_FILTERS: FilterState = { installedStatus: "all", filterTarget: null, tag: null };

const COMMAND_HELP = `{bold}Skillbee Keyboard Shortcuts{/bold}

{bold}Browse{/bold}
  {yellow-fg}{bold}{up}{/bold}{/yellow-fg}/{yellow-fg}{bold}j{/bold}{/yellow-fg} ......... navigate up
  {yellow-fg}{bold}{down}{/bold}{/yellow-fg}/{yellow-fg}{bold}k{/bold}{/yellow-fg} ....... navigate down
  {yellow-fg}{bold}/{/bold}{/yellow-fg} ................ search skills
  {yellow-fg}{bold}f{/bold}{/yellow-fg} ................ open filter panel
  {yellow-fg}{bold}v{/bold}{/yellow-fg} ................ toggle list/matrix view
  {yellow-fg}{bold}s{/bold}{/yellow-fg} ................ toggle global/project scope
  {yellow-fg}{bold}g{/bold}{/yellow-fg} ................ toggle group sidebar
  {yellow-fg}{bold}a{/bold}{/yellow-fg} ................ toggle archived visibility

{bold}Select{/bold}
  {yellow-fg}{bold}space{/bold}{/yellow-fg} ........... multi-select skill
  {yellow-fg}{bold}t{/bold}{/yellow-fg} ................ open target multi-select
  {yellow-fg}{bold}tab{/bold}{/yellow-fg} .............. cycle single target

{bold}Actions{/bold}
  {yellow-fg}{bold}i{/bold}{/yellow-fg} ................ install selected skills
  {yellow-fg}{bold}u{/bold}{/yellow-fg} ............... uninstall selected skills
  {yellow-fg}{bold}x{/bold}{/yellow-fg} ............... archive/unarchive
  {yellow-fg}{bold}r{/bold}{/yellow-fg} ............... reset cursor

{bold}Manage{/bold}
  {yellow-fg}{bold}c{/bold}{/yellow-fg} ............... create custom group
  {yellow-fg}{bold}E{/bold}{/yellow-fg} ............... edit custom group
  {yellow-fg}{bold}D{/bold}{/yellow-fg} ............... delete custom group

{bold}System{/bold}
  {yellow-fg}{bold}?{/bold}{/yellow-fg} ............... show this help
  {yellow-fg}{bold}q{/bold}{/yellow-fg} ............... quit

{center}{bold}Press ESC to close{/bold}{/center}`;

export interface DashboardOptions {
  selectedTargets?: SupportedTarget[];
  projectDir?: string;
  platform?: Partial<PlatformContext>;
}

export async function runDashboard(options: DashboardOptions = {}): Promise<void> {
  const screen = blessed.screen({
    smartCSR: true,
    title: "Skillbee"
  });

  let groupVisible = false;
  let detailTab = 0;
  const DETAIL_TABS = ["Matrix", "README", "Related"];

  const header = blessed.box({
    parent: screen,
    top: 0,
    left: 0,
    width: "100%",
    height: 3,
    tags: true,
    style: { fg: COLORS.brandYellow, bold: true },
    content: ""
  });
  const groupList = blessed.list({
    parent: screen,
    label: ` ${BEE_ASCII} Groups `,
    top: 3,
    left: 0,
    width: "15%",
    height: "85%",
    border: "line",
    keys: true,
    mouse: true,
    hidden: true,
    style: SELECTED_LIST_STYLE
  });
  const skillList = blessed.list({
    parent: screen,
    label: ` ${BEE_ASCII} Skills `,
    top: 3,
    left: 0,
    width: "70%",
    height: "85%",
    border: "line",
    keys: true,
    vi: true,
    mouse: true,
    style: SELECTED_LIST_STYLE
  });
  const detailBox = blessed.box({
    parent: screen,
    label: ` ${BEE_ASCII} Detail `,
    top: 3,
    left: "70%",
    width: "30%",
    height: "85%",
    border: "line",
    tags: true,
    scrollable: true,
    alwaysScroll: true
  });
  const statusBar = blessed.box({
    parent: screen,
    top: "88%",
    left: 0,
    width: "100%",
    height: 2,
    tags: true,
    style: { fg: "white" },
    content: ""
  });

  const platformContext = resolvePlatformContext(options.platform);
  const allTargets = [...supportedTargets];
  const initialTargets = options.selectedTargets?.length ? options.selectedTargets : allTargets;
  const selectedTargets = new Set<SupportedTarget>(initialTargets);
  let primaryTarget = initialTargets[0] ?? allTargets[0];

  let filters: FilterState = { ...DEFAULT_FILTERS };

  let scope: InstallScope = "global";
  let query = "";
  let activeGroup = "all";
  let includeArchived = false;
  let skills: ManagerSkillRecord[] = [];
  let isRendering = false;
  let customGroupNames: string[] = [];
  let activeCustomGroupSkills: string[] | null = null;
  const selectedIds = new Set<string>();
  const operationLog: string[] = [];
  let viewMode: "list" | "matrix" = "list";
  let currentTheme = "bee";
  let currentColors: ThemeColors = COLORS;

  async function refresh(message = "Loading skills..."): Promise<void> {
    const targetsForSearch = selectedTargets.size > 0 ? [...selectedTargets] : allTargets;
    statusBar.setContent(message);
    screen.render();

    try {
      const [loadedSkills, userConfig] = await Promise.all([
        searchSkills({
          scope,
          projectDir: options.projectDir,
          selectedTargets: targetsForSearch,
          includeArchived,
          platform: options.platform
        }),
        loadUserConfig(platformContext.configBaseDir)
      ]);
      skills = loadedSkills;
      customGroupNames = userConfig.groups.map((g) => g.name);

      if (currentTheme !== userConfig.theme) {
        currentTheme = userConfig.theme;
        currentColors = getTheme(currentTheme);
      }

      if (activeGroup.startsWith(USER_GROUP_PREFIX)) {
        const groupName = activeGroup.slice(USER_GROUP_PREFIX.length);
        const group = userConfig.groups.find((g) => g.name === groupName);
        if (!group || group.skills.length === 0) {
          activeGroup = "all";
          activeCustomGroupSkills = null;
        } else {
          activeCustomGroupSkills = group.skills;
        }
      } else {
        activeCustomGroupSkills = null;
      }

      if (message !== "Loading skills...") {
        log(message);
      }
      render();
    } catch (error) {
      log(`Error: ${error instanceof Error ? error.message : "unknown error"}`);
      render();
      screen.render();
    }
  }

  function render(): void {
    isRendering = true;

    try {
      const taxonomyGroups = [...new Set(skills.map((skill) => skill.group))].sort();
      const allGroups = [
        "all",
        ...taxonomyGroups,
        ...(customGroupNames.length > 0 ? customGroupNames.map((name) => `${USER_GROUP_PREFIX}${name}`) : [])
      ];
      const visibleSkills = getVisibleSkills();

      header.setContent(
        ` {bold}${BEE_ASCII}  Skillbee{/bold}   scope:{bold}${scope}{/bold}  targets:{bold}${selectedTargets.size}{/bold}  selected:{bold}${selectedIds.size}{/bold}  visible:{bold}${visibleSkills.length}{/bold}  view:{bold}${viewMode}{/bold}${query ? `  {cyan-fg}search:${query}{/cyan-fg}` : ""}`
      );

      if (groupVisible) {
        groupList.show();
        skillList.left = "15%";
        skillList.width = "55%";
      } else {
        groupList.hide();
        skillList.left = 0;
        skillList.width = "70%";
      }
      groupList.setItems(allGroups.map((g) => (g === activeGroup ? `{bold}{yellow-fg}> ${g}{/bold}{/yellow-fg}` : `  ${g}`)));
      if (viewMode === "matrix") {
        const targetsArr = [...selectedTargets];
        const maxIdLen = Math.max(...visibleSkills.map((s) => s.id.length), 8);
        skillList.setItems(visibleSkills.map((skill) => renderMatrixRow(skill, targetsArr, selectedIds, maxIdLen)));
      } else {
        skillList.setItems(visibleSkills.map((skill) => renderSkillRow(skill, primaryTarget, selectedIds)));
      }
      renderSelectedSkillDetail();
      const filtersActive = filters.installedStatus !== "all" || filters.filterTarget || filters.tag;
      const shortcutLine = `i=install  u=uninstall  t=targets  f=filter  s=scope  g=groups  v=view  a=archive  ?=help  q=quit`;
      const statusLine = operationLog.length > 0
        ? `${operationLog[0]}${filtersActive ? "  {cyan-fg}[filtered]{/cyan-fg}" : ""}`
        : `ready  ${filtersActive ? "{cyan-fg}[filtered]{/cyan-fg}" : ""}`;
      statusBar.setContent(`${shortcutLine}\n${statusLine}`);
      screen.render();
    } finally {
      isRendering = false;
    }
  }

  function getVisibleSkills(): ManagerSkillRecord[] {
    return filterSkills(skills, activeGroup, query, activeCustomGroupSkills, filters, primaryTarget);
  }

  function renderSelectedSkillDetail(): void {
    const visibleSkills = getVisibleSkills();

    renderDetail(visibleSkills[getSelectedIndex(skillList)] ?? visibleSkills[0]);
  }

  function renderDetail(skill: ManagerSkillRecord | undefined): void {
    if (!skill) {
      detailBox.setContent("No skill selected.");
      return;
    }

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
        `{bold}{yellow-fg}${skill.id}{/yellow-fg}{/bold}`,
        `{bold}Group:{/bold} ${skill.group}${skill.subgroup ? `/${skill.subgroup}` : ""}`,
        `{bold}Origin:{/bold} ${skill.origin}${skill.sourceId ? ` {gray-fg}(${skill.sourceId}){/gray-fg}` : ""}`,
        `{bold}Archived:{/bold} ${skill.archived ? "{cyan-fg}yes{/cyan-fg}" : "no"}`,
        `{bold}Description:{/bold} ${(skill.description ?? "").slice(0, 80)}${(skill.description ?? "").length > 80 ? "..." : ""}`,
        "",
        `{bold}Install Matrix:{/bold}`,
        ` ${matrixRow}`,
        "",
        `{bold}Tags:{/bold} ${skill.tags.length ? skill.tags.join(", ") : "-"}`,
        skill.customTags.length > 0 ? `{bold}Custom:{/bold} ${skill.customTags.join(", ")}` : "",
        skill.commandOnly ? "{yellow-fg}Command source: install only{/yellow-fg}" : "",
        "{gray-fg}---{/gray-fg}",
        "{gray-fg}N=cycle tab | i=install | u=uninstall | x=archive{/gray-fg}"
      ].filter(Boolean).join("\n"));
    } else if (detailTab === 1) {
      detailBox.setContent("{gray-fg}Loading SKILL.md...{/gray-fg}");
      void loadSkillPreview(skill).then((preview) => {
        detailBox.setContent(
          preview.length > 0
            ? preview
            : "{gray-fg}No SKILL.md preview available.{/gray-fg}"
        );
        screen.render();
      });
    } else if (detailTab === 2) {
      detailBox.setContent([
        `{bold}Tags:{/bold} ${skill.tags.length ? skill.tags.join(", ") : "-"}`,
        skill.customTags.length > 0 ? `{bold}Custom:{/bold} ${skill.customTags.join(", ")}` : "",
        "",
        relatedSkills.length > 0
          ? [`{bold}Related Skills:{/bold}`, ...relatedSkills.slice(0, 8).map((s) => `  ${s.archived ? "{cyan-fg}" : ""}${s.id}${s.archived ? "{/cyan-fg}" : ""}`)].join("\n")
          : "{gray-fg}No related skills found.{/gray-fg}",
        "",
        "{gray-fg}---{/gray-fg}",
        "{gray-fg}N=cycle tab{/gray-fg}"
      ].filter(Boolean).join("\n"));
    }
  }

  async function mutate(kind: "install" | "uninstall"): Promise<void> {
    const visibleSkills = getVisibleSkills();
    const highlighted = visibleSkills[getSelectedIndex(skillList)] ?? visibleSkills[0];
    const assetIds = selectedIds.size > 0
      ? [...selectedIds]
      : highlighted ? [highlighted.id] : [];

    if (assetIds.length === 0) {
      statusBar.setContent("No skills selected.");
      screen.render();
      return;
    }

    const targetsArr = [...selectedTargets];
    statusBar.setContent(`${kind === "install" ? "Installing" : "Uninstalling"} ${assetIds.join(", ")} on ${targetsArr.join(", ")}...`);
    screen.render();

    try {
      let reportContent = "";
      if (kind === "install") {
        const result = await installSkills({
          assetIds,
          scope,
          projectDir: options.projectDir,
          selectedTargets: targetsArr,
          includeArchived,
          platform: options.platform
        });
        reportContent = buildInstallReport(targetsArr, assetIds, result);
      } else {
        const result = await uninstallSkills({
          assetIds,
          scope,
          projectDir: options.projectDir,
          selectedTargets: targetsArr,
          platform: options.platform
        });
        reportContent = buildUninstallReport(targetsArr, assetIds, result);
      }
      selectedIds.clear();
      await refresh(`${kind === "install" ? "Installed" : "Uninstalled"} ${assetIds.join(", ")} on ${targetsArr.join(", ")}.`);
      showReport(reportContent);
    } catch (error) {
      log(`Error: ${error instanceof Error ? error.message : "unknown error"}`);
      render();
    }
  }

  async function toggleArchive(): Promise<void> {
    const visibleSkills = getVisibleSkills();
    const highlighted = visibleSkills[getSelectedIndex(skillList)] ?? visibleSkills[0];
    const assetIds = selectedIds.size > 0
      ? [...selectedIds]
      : highlighted ? [highlighted.id] : [];

    if (assetIds.length === 0) {
      statusBar.setContent("No skills selected.");
      screen.render();
      return;
    }

    const skillToCheck = skills.find((s) => s.id === assetIds[0]);
    const currentlyArchived = skillToCheck?.archived ?? false;

    statusBar.setContent(`${currentlyArchived ? "Unarchiving" : "Archiving"} ${assetIds.join(", ")}...`);
    screen.render();

    try {
      const result = await archiveSkills({
        assetIds,
        archived: !currentlyArchived,
        scope,
        projectDir: options.projectDir,
        selectedTargets: [...selectedTargets],
        platform: options.platform
      });
      selectedIds.clear();
      await refresh(
        result.archived.length > 0
          ? `Archived ${result.archived.join(", ")}.`
          : `Unarchived ${result.unarchived.join(", ")}.`
      );
    } catch (error) {
      log(`Error: ${error instanceof Error ? error.message : "unknown error"}`);
      render();
    }
  }

  async function resetCursor(): Promise<void> {
    if (!selectedTargets.has("cursor")) {
      log("Reset is currently scoped to the cursor target.");
      render();
      return;
    }

    statusBar.setContent("Resetting cursor skills across global and project scopes...");
    screen.render();

    try {
      const result = await resetSkills({
        target: "cursor",
        scope: "all",
        projectDir: options.projectDir,
        installAll: true,
        yes: true,
        platform: options.platform
      });
      const installedCount = result.scopes.reduce((count, scopeResult) => count + scopeResult.installed.length, 0);
      selectedIds.clear();
      await refresh(`Reset cursor skills across ${result.scopes.length} scopes; installed ${installedCount} entries.`);
    } catch (error) {
      log(`Error: ${error instanceof Error ? error.message : "unknown error"}`);
      render();
    }
  }

  function buildInstallReport(targets: SupportedTarget[], assetIds: string[], result: InstallSkillsResult): string {
    const lines: string[] = [];
    const kind = result.commandReports.length > 0 ? "install (command)" : "install";
    lines.push(`═══ ${kind.toUpperCase()} COMPLETE ═══`);
    lines.push("");

    const installedByTarget = new Map<SupportedTarget, string[]>();
    const skippedByTarget = new Map<SupportedTarget, Array<{ assetId: string; reason: string }>>();
    for (const t of targets) {
      installedByTarget.set(t, []);
      skippedByTarget.set(t, []);
    }

    for (const inst of result.installed) {
      const arr = installedByTarget.get(inst.target);
      if (arr) arr.push(inst.assetId);
    }
    for (const sk of result.skipped) {
      const target = sk.target ?? targets[0];
      const arr = skippedByTarget.get(target);
      if (arr) arr.push({ assetId: sk.assetId, reason: sk.reason });
    }

    for (const target of targets) {
      const installed = installedByTarget.get(target) ?? [];
      const skipped = skippedByTarget.get(target) ?? [];
      const total = assetIds.length;
      const ok = installed.length;
      const skip = skipped.length;
      const fail = total - ok - skip;

      const parts: string[] = [];
      if (ok > 0) parts.push(`${ok}/${total} success`);
      if (skip > 0) parts.push(`${skip} skipped`);
      if (fail > 0) parts.push(`${fail} failed`);
      lines.push(`  ${target}  (${parts.join(", ")})`);

      for (const aid of assetIds) {
        if (installed.includes(aid)) {
          lines.push(`    ✓ ${aid}`);
        } else {
          const skippedInfo = skipped.find((s) => s.assetId === aid);
          if (skippedInfo) {
            lines.push(`    ○ ${aid} → ${skippedInfo.reason}`);
          } else {
            lines.push(`    ✗ ${aid}`);
          }
        }
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
    for (const t of targets) {
      removedByTarget.set(t, []);
      skippedByTarget.set(t, []);
    }

    for (const r of result.removed) {
      const arr = removedByTarget.get(r.target);
      if (arr) arr.push(r.assetId);
    }
    for (const sk of result.skipped) {
      const arr = skippedByTarget.get(sk.target);
      if (arr) arr.push({ assetId: sk.assetId, reason: sk.reason });
    }

    for (const target of targets) {
      const removed = removedByTarget.get(target) ?? [];
      const skipped = skippedByTarget.get(target) ?? [];
      const total = assetIds.length;
      const ok = removed.length;
      const skip = skipped.length;
      const fail = total - ok - skip;

      const parts: string[] = [];
      if (ok > 0) parts.push(`${ok}/${total} success`);
      if (skip > 0) parts.push(`${skip} skipped`);
      if (fail > 0) parts.push(`${fail} failed`);
      lines.push(`  ${target}  (${parts.join(", ")})`);

      for (const aid of assetIds) {
        if (removed.includes(aid)) {
          lines.push(`    ✓ ${aid}`);
        } else {
          const skippedInfo = skipped.find((s) => s.assetId === aid);
          if (skippedInfo) {
            lines.push(`    ○ ${aid} → ${skippedInfo.reason}`);
          } else {
            lines.push(`    ✗ ${aid}`);
          }
        }
      }
      lines.push("");
    }

    return lines.join("\n");
  }

  function showReport(content: string): void {
    const reportBox = blessed.box({
      parent: screen,
      top: "center",
      left: "center",
      width: "70%",
      height: "60%",
      border: { type: "line" },
      style: {
        fg: "white",
        bg: "black",
        border: { fg: currentColors.accent }
      },
      content: content + "\n\n{center}{bold}Press ESC or q to close{/bold}{/center}",
      scrollable: true,
      alwaysScroll: true,
      keys: true,
      vi: true,
      mouse: true,
      tags: true,
      label: " Report "
    });

    reportBox.focus();
    screen.render();

    reportBox.key(["escape", "q"], () => {
      reportBox.detach();
      screen.render();
    });
  }

  function log(message: string): void {
    operationLog.unshift(`${new Date().toLocaleTimeString()} ${message}`);
    operationLog.splice(8);
  }

  screen.key(["q", "C-c"], () => {
    screen.destroy();
  });
  screen.key("s", async () => {
    scope = scope === "global" ? "project" : "global";
    await refresh(`Scope changed to ${scope}.`);
  });
  screen.key("g", () => {
    groupVisible = !groupVisible;
    render();
  });
  screen.key("a", async () => {
    includeArchived = !includeArchived;
    selectedIds.clear();
    await refresh(`Archived skills ${includeArchived ? "shown" : "hidden"}.`);
  });
  screen.key("tab", async () => {
    const targetsArr = [...selectedTargets];
    if (targetsArr.length <= 1) {
      return;
    }

    const nextIndex = (targetsArr.indexOf(primaryTarget) + 1) % targetsArr.length;
    primaryTarget = targetsArr[nextIndex] ?? targetsArr[0];
    selectedIds.clear();
    await refresh(`Primary target changed to ${primaryTarget}.`);
  });
  screen.key("space", () => {
    const visibleSkills = getVisibleSkills();
    const skill = visibleSkills[getSelectedIndex(skillList)] ?? visibleSkills[0];
    if (!skill) {
      return;
    }

    if (selectedIds.has(skill.id)) {
      selectedIds.delete(skill.id);
    } else {
      selectedIds.add(skill.id);
    }
    render();
  });
  screen.key("t", () => {
    const targetsArr = allTargets;
    const currentSelection = new Set(selectedTargets);
    let listIndex = 0;

    const targetBox = blessed.list({
      parent: screen,
      border: "line",
      height: "50%",
      width: "40%",
      top: "center",
      left: "center",
      label: ` ${BEE_ASCII} Select Targets `,
      tags: true,
      keys: true,
      vi: true,
      mouse: true,
      shadow: true,
      style: SELECTED_LIST_STYLE,
      items: targetsArr.map((t) =>
        currentSelection.has(t)
          ? `{yellow-fg}{bold}[x]{/bold}{/yellow-fg} ${t}`
          : `[ ] ${t}`
      )
    });
    const hintBox = blessed.box({
      parent: screen,
      top: "50%",
      left: "30%",
      width: "40%",
      height: "shrink",
      tags: true,
      content: "{gray-fg}space toggle  a all  A none  enter done{/gray-fg}"
    });
    targetBox.focus();
    screen.render();

    function closeTargetSelector(): void {
      targetBox.detach();
      hintBox.detach();
      if (!currentSelection.has(primaryTarget) && currentSelection.size > 0) {
        primaryTarget = [...currentSelection][0];
      }
      selectedTargets.clear();
      for (const t of currentSelection) {
        selectedTargets.add(t);
      }
      skillList.focus();
      void refresh();
    }

    targetBox.key("space", () => {
      const selected = targetsArr[listIndex];
      if (currentSelection.has(selected)) {
        currentSelection.delete(selected);
      } else {
        currentSelection.add(selected);
      }
      targetBox.setItems(targetsArr.map((t) =>
        currentSelection.has(t)
          ? `{yellow-fg}{bold}[x]{/bold}{/yellow-fg} {bold}${t}{/bold}`
          : `[ ] ${t}`
      ));
      screen.render();
    });
    targetBox.key("a", () => {
      targetsArr.forEach((t) => currentSelection.add(t));
      targetBox.setItems(targetsArr.map((t) =>
        `{yellow-fg}{bold}[x]{/bold}{/yellow-fg} {bold}${t}{/bold}`
      ));
      screen.render();
    });
    targetBox.key("A", () => {
      currentSelection.clear();
      targetBox.setItems(targetsArr.map((t) =>
        `[ ] ${t}`
      ));
      screen.render();
    });
    targetBox.key(["enter", "escape", "C-c", "q"], () => {
      closeTargetSelector();
    });
    targetBox.on("select", (_item, index) => {
      listIndex = index;
    });
  });
  screen.key("i", () => {
    void mutate("install");
  });
  screen.key("u", () => {
    void mutate("uninstall");
  });
  screen.key("x", () => {
    void toggleArchive();
  });
  screen.key("r", () => {
    void resetCursor();
  });
  screen.key("v", () => {
    viewMode = viewMode === "list" ? "matrix" : "list";
    skillList.select(0);
    render();
  });
  screen.key("N", () => {
    detailTab = (detailTab + 1) % DETAIL_TABS.length;
    renderSelectedSkillDetail();
    screen.render();
  });
  screen.key("T", async () => {
    const idx = THEME_NAMES.indexOf(currentTheme as typeof THEME_NAMES[number]);
    const next = THEME_NAMES[(idx + 1) % THEME_NAMES.length];
    currentTheme = next;
    currentColors = getTheme(next);
    await saveTheme(platformContext.configBaseDir, next);
    render();
  });
  screen.key(["?", "C-slash"], () => {
    const helpBox = blessed.box({
      parent: screen,
      border: "line",
      height: "80%",
      width: "60%",
      top: "center",
      left: "center",
      label: ` ${BEE_ASCII} Keyboard Shortcuts `,
      tags: true,
      keys: true,
      vi: true,
      mouse: true,
      shadow: true,
      content: COMMAND_HELP,
      style: {
        bg: "black",
        fg: "white",
        border: { fg: currentColors.brandYellow }
      }
    });
    helpBox.focus();
    screen.render();

    helpBox.key(["escape", "q"], () => {
      helpBox.detach();
      screen.render();
      skillList.focus();
    });
  });
  screen.key("/", () => {
    blessed.prompt({
      parent: screen,
      border: "line",
      height: "shrink",
      width: "50%",
      top: "center",
      left: "center",
      label: " Search "
    }).input("Query", query, (_error, value) => {
      query = value ?? "";
      skillList.select(0);
      render();
      skillList.focus();
    });
  });
  screen.key("f", () => {
    const allTags = [...new Set(skills.flatMap((s) => s.tags))].sort();
    const tempFilters: FilterState = { ...filters };
    let filterStep = 0;

    const filterBox = blessed.box({
      parent: screen,
      border: "line",
      height: "shrink",
      width: "50%",
      top: "center",
      left: "center",
      label: ` ${BEE_ASCII} Filters `,
      tags: true,
      keys: true,
      shadow: true,
      style: {
        bg: "black",
        fg: "white",
        border: { fg: currentColors.brandYellow }
      },
      content: renderFilterContent()
    });
    filterBox.focus();
    screen.render();

    function renderFilterContent(): string {
      const lines: string[] = [
        `${filterStep === 0 ? "{yellow-fg}{bold}\u25B6 {/bold}{/yellow-fg}" : "  "}{bold}Install status:{/bold}`,
        `  ${tempFilters.installedStatus === "all" ? "{yellow-fg}{bold}[x]{/bold}{/yellow-fg}" : "[ ]"} all`,
        `  ${tempFilters.installedStatus === "installed" ? "{yellow-fg}{bold}[x]{/bold}{/yellow-fg}" : "[ ]"} installed only`,
        `  ${tempFilters.installedStatus === "uninstalled" ? "{yellow-fg}{bold}[x]{/bold}{/yellow-fg}" : "[ ]"} uninstalled only`,
        "",
        `${filterStep === 1 ? "{yellow-fg}{bold}\u25B6 {/bold}{/yellow-fg}" : "  "}{bold}Target:{/bold}`,
        `  ${tempFilters.filterTarget === null ? "{yellow-fg}{bold}[x]{/bold}{/yellow-fg}" : "[ ]"} any`,
        ...allTargets.map((t) =>
          `  ${tempFilters.filterTarget === t ? "{yellow-fg}{bold}[x]{/bold}{/yellow-fg}" : "[ ]"} ${t}`
        ),
        "",
        ...(allTags.length > 0
          ? [
            `${filterStep === 2 ? "{yellow-fg}{bold}\u25B6 {/bold}{/yellow-fg}" : "  "}{bold}Tag:{/bold}`,
            `  ${tempFilters.tag === null ? "{yellow-fg}{bold}[x]{/bold}{/yellow-fg}" : "[ ]"} any`,
            ...allTags.map((tag) =>
              `  ${tempFilters.tag === tag ? "{yellow-fg}{bold}[x]{/bold}{/yellow-fg}" : "[ ]"} ${tag}`
            )
          ]
          : [`{bold}Tag:{/bold}  {gray-fg}(no tags defined){/gray-fg}`]),
        "",
        "{gray-fg}\u2191\u2193 dimension  \u2190\u2192 cycle  enter done{/gray-fg}"
      ];
      return lines.join("\n");
    }

    function applyFilters(): void {
      filters = { ...tempFilters };
      filterBox.detach();
      skillList.focus();
      skillList.select(0);
      render();
    }

    function cycleFilter(direction: 1 | -1): void {
      const statusOptions: Array<FilterState["installedStatus"]> = ["all", "installed", "uninstalled"];
      const targetOptions: Array<SupportedTarget | null> = [null, ...allTargets];
      const tagOptions: Array<string | null> = [null, ...allTags];
      const statusIdx = statusOptions.indexOf(tempFilters.installedStatus);
      const targetIdx = targetOptions.indexOf(tempFilters.filterTarget);
      const tagIdx = tagOptions.indexOf(tempFilters.tag);

      if (filterStep === 0) {
        const next = (statusIdx + direction + statusOptions.length) % statusOptions.length;
        tempFilters.installedStatus = statusOptions[next];
      } else if (filterStep === 1) {
        const next = (targetIdx + direction + targetOptions.length) % targetOptions.length;
        tempFilters.filterTarget = targetOptions[next];
      } else if (filterStep === 2 && allTags.length > 0) {
        const next = (tagIdx + direction + tagOptions.length) % tagOptions.length;
        tempFilters.tag = tagOptions[next];
      }

      filterBox.setContent(renderFilterContent());
      screen.render();
    }

    filterBox.key("up", () => { filterStep = Math.max(0, filterStep - 1); filterBox.setContent(renderFilterContent()); screen.render(); });
    filterBox.key("down", () => { filterStep = Math.min(2, filterStep + 1); filterBox.setContent(renderFilterContent()); screen.render(); });
    filterBox.key("left", () => cycleFilter(-1));
    filterBox.key("right", () => cycleFilter(1));
    filterBox.key("space", () => cycleFilter(1));
    filterBox.key(["enter", "escape", "C-c", "q"], () => applyFilters());
  });
  groupList.on("select", async (_item, index) => {
    const taxonomyGroups = [...new Set(skills.map((skill) => skill.group))].sort();
    const allGroups = [
      "all",
      ...taxonomyGroups,
      ...(customGroupNames.length > 0 ? customGroupNames.map((name) => `${USER_GROUP_PREFIX}${name}`) : [])
    ];
    const selected = allGroups[index] ?? "all";

    if (selected.startsWith(USER_GROUP_PREFIX)) {
      const groupName = selected.slice(USER_GROUP_PREFIX.length);
      const userConfig = await loadUserConfig(platformContext.configBaseDir);
      const group = userConfig.groups.find((g) => g.name === groupName);

      if (!group || group.skills.length === 0) {
        activeGroup = "all";
        activeCustomGroupSkills = null;
        log(`Custom group "${groupName}" is empty or not found.`);
      } else {
        activeGroup = selected;
        activeCustomGroupSkills = group.skills;
      }
    } else {
      activeGroup = selected;
      activeCustomGroupSkills = null;
    }

    skillList.select(0);
    render();
    skillList.focus();
  });
  skillList.on("select item", () => {
    if (isRendering) {
      return;
    }

    renderSelectedSkillDetail();
    screen.render();
  });

  skillList.focus();
  await refresh();

  return new Promise((resolve) => {
    screen.on("destroy", resolve);
  });
}

async function loadSkillPreview(skill: ManagerSkillRecord): Promise<string> {
  if (skill.origin !== "owned") {
    return "";
  }

  try {
    const content = await readFile(
      join(ownedSkillsRoot, skill.id, "SKILL.md"),
      "utf8"
    );
    const lines = content.split("\n").filter((l) => !l.startsWith("---") && !l.startsWith("metadata:") && !l.startsWith("compatibility:"));
    const firstLines = lines.slice(0, 12).map((l) => l.length > 60 ? l.slice(0, 60) + "..." : l);

    return firstLines.map((l) => l || " ").join("\n");
  } catch {
    return "";
  }
}

function getRelatedSkills(
  skill: ManagerSkillRecord,
  allSkills: ManagerSkillRecord[]
): ManagerSkillRecord[] {
  const ownTags = new Set(skill.tags);

  if (ownTags.size === 0) {
    return [];
  }

  return allSkills
    .filter((s) => s.id !== skill.id && s.tags.some((t) => ownTags.has(t)))
    .sort((a, b) => {
      const aCommon = a.tags.filter((t) => ownTags.has(t)).length;
      const bCommon = b.tags.filter((t) => ownTags.has(t)).length;

      return bCommon - aCommon;
    });
}

function filterSkills(
  skills: ManagerSkillRecord[],
  group: string,
  query: string,
  activeCustomGroupSkills: string[] | null,
  filters?: FilterState,
  primaryTarget?: SupportedTarget
): ManagerSkillRecord[] {
  const normalizedQuery = query.trim().toLowerCase();

  return skills.filter((skill) => {
    let groupMatches = true;

    if (group.startsWith(USER_GROUP_PREFIX)) {
      groupMatches = activeCustomGroupSkills?.includes(skill.id) ?? false;
    } else {
      groupMatches = group === "all" || skill.group === group;
    }

    const queryMatches = !normalizedQuery || [
      skill.id,
      skill.description,
      skill.group,
      skill.subgroup,
      skill.sourceId,
      ...skill.tags,
      ...skill.customTags
    ].some((value) => value?.toLowerCase().includes(normalizedQuery));

    let filterMatches = true;
    if (filters) {
      if (filters.installedStatus === "installed" && primaryTarget) {
        filterMatches = filterMatches && skill.installedTargets.includes(primaryTarget);
      } else if (filters.installedStatus === "uninstalled" && primaryTarget) {
        filterMatches = filterMatches && !skill.installedTargets.includes(primaryTarget);
      }

      if (filters.filterTarget) {
        filterMatches = filterMatches && skill.availableTargets.includes(filters.filterTarget);
      }

      if (filters.tag) {
        filterMatches = filterMatches && skill.tags.includes(filters.tag);
      }
    }

    return groupMatches && queryMatches && filterMatches;
  });
}

function renderSkillRow(
  skill: ManagerSkillRecord,
  target: SupportedTarget,
  selectedIds: Set<string>
): string {
  const prefix = selectedIds.has(skill.id) ? "{yellow-fg}{bold}[x]{/bold}{/yellow-fg}" : "[ ]";
  const status = skill.installedTargets.includes(target)
    ? "\u25CF"
    : skill.availableTargets.includes(target)
      ? "\u25CB"
      : "-";
  const archived = skill.archived ? " {cyan-fg}(archived){/cyan-fg}" : "";
  const idText = skill.archived ? `{cyan-fg}${skill.id}{/cyan-fg}` : skill.id;

  return `${prefix} ${idText}  ${status}${archived}`;
}

function renderMatrixRow(
  skill: ManagerSkillRecord,
  targets: SupportedTarget[],
  selectedIds: Set<string>,
  maxIdLen: number
): string {
  const prefix = selectedIds.has(skill.id) ? "{yellow-fg}{bold}[x]{/bold}{/yellow-fg}" : "[ ]";
  const idText = skill.archived ? `{cyan-fg}${skill.id}{/cyan-fg}` : skill.id;
  const paddedId = skill.id.padEnd(maxIdLen);
  const displayId = skill.archived ? `{cyan-fg}${paddedId}{/cyan-fg}` : paddedId;

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
