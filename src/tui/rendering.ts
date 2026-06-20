import type { ManagerSkillRecord } from "../manager/manager";
import type { SupportedTarget } from "../model/targets";
import {
  AVAILABLE_GLYPH,
  BIRD_ASCII,
  BROKEN_GLYPH,
  INSTALLED_GLYPH,
  PALETTE,
  UNAVAILABLE_GLYPH,
  formatMatrixCell,
  targetShortLabel
} from "./theme";

const BLESSED_TAG_RE = /\{\/?[^{}]+\}/g;
const ANSI_RE = /\x1b\[[0-9;?]*[ -/]*[@-~]/g;
const SIMPLE_TAGS = new Set(["bold", "center", "dim", "underline"]);
const CELL_WIDTH = 4;

function colorTag(value: string): string {
  return `{${value}-fg}`;
}

function closeColorTag(value: string): string {
  return `{/${value}-fg}`;
}

function colorText(value: string, color: string): string {
  return `${colorTag(color)}${value}${closeColorTag(color)}`;
}

function keyText(value: string): string {
  return `${colorTag(PALETTE.amber)}{bold}${value}{/bold}${closeColorTag(PALETTE.amber)}`;
}

export const COMMAND_HELP = [
  `{bold}${colorText("Skillbird Keyboard Shortcuts", PALETTE.amber)}{/bold}`,
  "",
  "{bold}Navigate{/bold}",
  `  ${keyText("←")}/${keyText("→")} ........... switch panel (Categories/Skills/Details)`,
  `  ${keyText("↑")}/${keyText("↓")} ........... navigate list / scroll detail`,
  `  ${keyText("/")} ................. search skills`,
  `  ${keyText("v")} ................. toggle list/matrix view`,
  `  ${keyText("s")} ................. toggle scope (global/project)`,
  `  ${keyText("a")} ................. toggle archived visibility`,
  "",
  "{bold}Select{/bold}",
  `  ${keyText("space")} ............. multi-select (tags or skills)`,
  `  ${keyText("A")} ................. select all tags`,
  `  ${keyText("Shift+A")} .......... deselect all tags`,
  `  ${keyText("Enter")} ............. view skill detail in Details`,
  `  ${keyText("t")} ................. open target multi-select`,
  `  ${keyText("N")} ................. cycle detail tab (Matrix/README/Related)`,
  "",
  "{bold}Actions{/bold}",
  `  ${keyText("i")} ................. install (scope -> target -> install)`,
  `  ${keyText("u")} ................ uninstall selected`,
  `  ${keyText("x")} ................ archive / unarchive`,
  `  ${keyText("r")} ................ repair broken skills`,
  `  ${keyText("p")} ................. preview sync`,
  `  ${keyText("I")} ................. include selected`,
  `  ${keyText("X")} ................. exclude selected`,
  `  ${keyText("d")} ................. reset include/exclude`,
  `  ${keyText("T")} ................ cycle theme (dove/monokai/nord)`,
  `  ${keyText("S")} ................ manage external sources`,
  "",
  "{bold}Manage{/bold}",
  `  ${keyText("c")} ................ create custom group`,
  `  ${keyText("E")} ................ edit custom group`,
  `  ${keyText("D")} ................ delete custom group`,
  "",
  "{bold}System{/bold}",
  `  ${keyText("?")} ................ show this help`,
  `  ${keyText("q")} ................ quit`,
  "",
  "{center}{dim}Press ESC to close{/dim}{/center}"
].join("\n");

export function stripBlessedTags(value: string): string {
  return value.replace(BLESSED_TAG_RE, "");
}

export function stripAnsi(value: string): string {
  return value.replace(ANSI_RE, "");
}

export function visibleWidth(value: string): number {
  let width = 0;
  for (const char of stripAnsi(stripBlessedTags(value))) {
    width += charWidth(char.codePointAt(0) ?? 0);
  }
  return width;
}

export function padVisible(value: string, width: number): string {
  const missing = width - visibleWidth(value);
  return missing > 0 ? `${value}${" ".repeat(missing)}` : value;
}

export function findUnsupportedBlessedTags(value: string): string[] {
  const unsupported = new Set<string>();
  for (const match of value.matchAll(BLESSED_TAG_RE)) {
    const raw = match[0].slice(1, -1);
    const tag = raw.startsWith("/") ? raw.slice(1) : raw;
    if (!isSupportedTag(tag)) {
      unsupported.add(match[0]);
    }
  }
  return [...unsupported].sort();
}

export function findUnbalancedBlessedTags(value: string): string[] {
  const stack: string[] = [];
  const issues: string[] = [];

  for (const match of value.matchAll(BLESSED_TAG_RE)) {
    const raw = match[0].slice(1, -1);
    const closing = raw.startsWith("/");
    const tag = closing ? raw.slice(1) : raw;

    if (!isSupportedTag(tag)) {
      continue;
    }

    if (!closing) {
      stack.push(tag);
      continue;
    }

    const previous = stack.pop();
    if (previous !== tag) {
      issues.push(match[0]);
      if (previous) {
        stack.push(previous);
      }
    }
  }

  return [...issues, ...stack.map((tag) => `{${tag}}`)];
}

export function validateBlessedTags(value: string): { unsupported: string[]; unbalanced: string[] } {
  return {
    unsupported: findUnsupportedBlessedTags(value),
    unbalanced: findUnbalancedBlessedTags(value)
  };
}

export function highlightText(text: string, query: string): string {
  if (!query || !text.toLowerCase().includes(query.toLowerCase())) return text;
  const idx = text.toLowerCase().indexOf(query.toLowerCase());
  const match = text.slice(idx, idx + query.length);
  return `${text.slice(0, idx)}${colorText(match, PALETTE.amber)}${text.slice(idx + query.length)}`;
}

export function renderSkillRow(
  skill: ManagerSkillRecord,
  target: SupportedTarget,
  selectedIds: Set<string>,
  brokenIds?: Set<string>,
  query?: string
): string {
  const prefix = selectedIds.has(skill.id)
    ? `${colorTag(PALETTE.amber)}{bold}✚{/bold}${closeColorTag(PALETTE.amber)}`
    : colorText("✟", PALETTE.ghostWhite);
  const status = skill.installedTargets.includes(target)
    ? colorText(INSTALLED_GLYPH, PALETTE.pollen)
    : skill.availableTargets.includes(target)
      ? colorText(AVAILABLE_GLYPH, PALETTE.ghostWhite)
      : colorText(UNAVAILABLE_GLYPH, PALETTE.dimGray);
  const archived = skill.archived ? ` ${colorText("(archived)", PALETTE.dimGray)}` : "";
  const broken = brokenIds?.has(skill.id) ? ` ${colorText(BROKEN_GLYPH, PALETTE.stinger)}` : "";
  const idDisplay = query ? highlightText(skill.id, query) : skill.id;
  const idText = skill.archived ? colorText(idDisplay, PALETTE.dimGray) : idDisplay;

  return `${prefix} ${idText}  ${status}${broken}${archived}`;
}

export function renderMatrixLabel(targets: SupportedTarget[]): string {
  const labels = targets.map((target) => targetShortLabel(target)).join(" ");
  return ` ${BIRD_ASCII} Matrix ${labels} `;
}

export function renderMatrixRow(
  skill: ManagerSkillRecord,
  targets: SupportedTarget[],
  selectedIds: Set<string>,
  maxIdLen: number
): string {
  const prefix = selectedIds.has(skill.id)
    ? `${colorTag(PALETTE.amber)}{bold}[x]{/bold}${closeColorTag(PALETTE.amber)}`
    : "[ ]";
  const idValue = padVisible(skill.id, maxIdLen);
  const displayId = skill.archived ? colorText(idValue, PALETTE.dimGray) : idValue;
  const cells = targets.map((target) => renderMatrixCell(skill, target)).join(" ");

  return `${prefix} ${displayId}  ${cells}`;
}

function renderMatrixCell(skill: ManagerSkillRecord, target: SupportedTarget): string {
  const available = skill.availableTargets.includes(target);
  const installed = skill.installedTargets.includes(target);
  const managed = skill.managedTargets.includes(target);
  const glyph = formatMatrixCell(available, installed, managed);
  const color = !available ? PALETTE.dimGray : installed ? PALETTE.pollen : PALETTE.ghostWhite;
  return padVisible(`${targetShortLabel(target)}:${colorText(glyph, color)}`, CELL_WIDTH);
}

function isSupportedTag(tag: string): boolean {
  return SIMPLE_TAGS.has(tag) || /^[0-9]+-(?:fg|bg)$/.test(tag);
}

function charWidth(codePoint: number): number {
  if (
    codePoint === 0 ||
    (codePoint >= 0x0300 && codePoint <= 0x036f) ||
    (codePoint >= 0xfe00 && codePoint <= 0xfe0f)
  ) {
    return 0;
  }
  if (
    codePoint >= 0x1100 &&
    (codePoint <= 0x115f ||
      codePoint === 0x2329 ||
      codePoint === 0x232a ||
      (codePoint >= 0x2e80 && codePoint <= 0xa4cf && codePoint !== 0x303f) ||
      (codePoint >= 0xac00 && codePoint <= 0xd7a3) ||
      (codePoint >= 0xf900 && codePoint <= 0xfaff) ||
      (codePoint >= 0xfe10 && codePoint <= 0xfe19) ||
      (codePoint >= 0xfe30 && codePoint <= 0xfe6f) ||
      (codePoint >= 0xff00 && codePoint <= 0xff60) ||
      (codePoint >= 0xffe0 && codePoint <= 0xffe6))
  ) {
    return 2;
  }
  return 1;
}
