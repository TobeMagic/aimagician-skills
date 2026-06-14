// ── Brand ──────────────────────────────────────────────────────────────
export const BIRD_ASCII = "\u{1F54A}\uFE0F";

// ── PRD §2.1: ANSI 256 Color Palette ──────────────────────────────────
// 琥珀黄 Amber #FFD700 | 炭黑 Carbon #2C2C2C | 花粉绿 Pollen Green #00CD00
// 蜂刺红 Stinger Red #D70000 | 幽灵白 Ghost White #E4E4E4 | 深灰 Dim Gray #585858

export const PALETTE = {
  amber:      "214",   // #FFD700 — brand main
  carbon:     "235",   // #2C2C2C — background
  pollen:     "202",   // #00CD00 approx → 202 for visibility on dark bg
  stinger:    "160",   // #D70000 — error / warning
  ghostWhite: "252",   // #E4E4E4 — secondary text
  dimGray:    "240",   // #585858 — borders / archived
  carbonDark: "233",   // #1a1a1a — deeper bg
  amberLight: "228",   // #fff8a0 — light amber for bg highlights
} as const;

// ── Splash Screen ──────────────────────────────────────────────────────
// NOTE: blessed tag syntax requires {XXX-fg} where XXX is ANSI 256 color number
export const BIRD_SPLASH = [
  "",
  `        {${PALETTE.amber}-fg}      /\\{/${PALETTE.amber}-fg}`,
  `        {${PALETTE.amber}-fg}  ___/  \\___{/${PALETTE.amber}-fg}`,
  `        {${PALETTE.amber}-fg}<___      _>{/${PALETTE.amber}-fg}`,
  `        {${PALETTE.amber}-fg}    /  /\\ \\{/${PALETTE.amber}-fg}`,
  `        {${PALETTE.amber}-fg}   /__/  \\_\\{/${PALETTE.amber}-fg}`,
  `        {${PALETTE.dimGray}-fg}      v{/${PALETTE.dimGray}-fg}`,
  "",
  `    {bold}{${PALETTE.amber}-fg} S K I L L B I R D {/${PALETTE.amber}-fg}{/bold}`,
  `    {${PALETTE.dimGray}-fg}\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500{/${PALETTE.dimGray}-fg}`,
  `    {${PALETTE.ghostWhite}-fg}Personal Skill Manager{/${PALETTE.ghostWhite}-fg}`,
  `    {${PALETTE.ghostWhite}-fg}for AI CLI Tools{/${PALETTE.ghostWhite}-fg}`,
  "",
  `    {${PALETTE.dimGray}-fg}v1.1.1  \u2022  aimagician_superpower{/${PALETTE.dimGray}-fg}`,
  ""
];

// ── Select Indicators ──────────────────────────────────────────────────
export const SELECT_GLYPH = "\u25B6";   // ▶  amber — selected item
export const UNSELECT_GLYPH = "\u25E6"; // ◦  ghost white — unselected
export const GROUP_CUSTOM_PREFIX = "\u25CE"; // ◎ — custom group marker

// ── Status Glyphs ──────────────────────────────────────────────────────
export const INSTALLED_GLYPH = "\u2714";   // ✔  pollen green
export const AVAILABLE_GLYPH = "\u25E6";   // ◦  ghost white
export const UNAVAILABLE_GLYPH = "\u2014"; // —  dim gray
export const BROKEN_GLYPH = "\u{1F494}";   // 💔 stinger red

// ── Theme System ───────────────────────────────────────────────────────
export const THEME_NAMES = ["dove", "monokai", "nord"] as const;
export type ThemeName = (typeof THEME_NAMES)[number];

export interface ThemeColors {
  brandYellow: string;
  brandBlack: string;
  installed: string;
  uninstalled: string;
  archived: string;
  archivedFg: string;
  selectedBg: string;
  selectedFg: string;
  error: string;
  accent: string;
  muted: string;
  headerBorder: string;
  panelBorder: string;
  headerBg: string;
  guideBarBg: string;
}

const themes: Record<ThemeName, ThemeColors> = {
  dove: {
    brandYellow:    PALETTE.amber,
    brandBlack:     PALETTE.carbon,
    installed:      PALETTE.pollen,
    uninstalled:    PALETTE.ghostWhite,
    archived:       PALETTE.dimGray,
    archivedFg:     "79",
    selectedBg:     PALETTE.amber,
    selectedFg:     PALETTE.carbonDark,
    error:          PALETTE.stinger,
    accent:         PALETTE.amber,
    muted:          PALETTE.dimGray,
    headerBorder:   PALETTE.amber,
    panelBorder:    PALETTE.dimGray,
    headerBg:       PALETTE.carbon,
    guideBarBg:     PALETTE.carbonDark,
  },
  monokai: {
    brandYellow:    "208",
    brandBlack:     "234",
    installed:      "114",
    uninstalled:    "252",
    archived:       "240",
    archivedFg:     "139",
    selectedBg:     "141",
    selectedFg:     "255",
    error:          "196",
    accent:         "208",
    muted:          "240",
    headerBorder:   "208",
    panelBorder:    "238",
    headerBg:       "234",
    guideBarBg:     "233",
  },
  nord: {
    brandYellow:    "109",
    brandBlack:     "235",
    installed:      "114",
    uninstalled:    "252",
    archived:       "240",
    archivedFg:     "103",
    selectedBg:     "75",
    selectedFg:     "255",
    error:          "203",
    accent:         "109",
    muted:          "240",
    headerBorder:   "109",
    panelBorder:    "238",
    headerBg:       "235",
    guideBarBg:     "234",
  }
};

export function getTheme(name: string): ThemeColors {
  return themes[name as ThemeName] ?? themes.dove;
}

export const COLORS: ThemeColors = themes.dove;

export function getSelectedListStyle(colors: ThemeColors): { selected: { bg: string; fg: string; bold: boolean }; item: { fg: string } } {
  return {
    selected: {
      bg: colors.selectedBg,
      fg: colors.selectedFg,
      bold: true
    },
    item: {
      fg: colors.uninstalled
    }
  };
}

// ── Helpers ────────────────────────────────────────────────────────────
export function targetShortLabel(target: string): string {
  const labels: Record<string, string> = {
    codex: "Cx", claude: "Cd", opencode: "Oc",
    gemini: "Gm", hermes: "Hm", cursor: "Cr", copilot: "Cp"
  };
  return labels[target] ?? target.slice(0, 2);
}

export function formatMatrixCell(
  isAvailable: boolean,
  isInstalled: boolean,
  _isManaged: boolean
): string {
  if (!isAvailable) return UNAVAILABLE_GLYPH;
  if (isInstalled) return INSTALLED_GLYPH;
  return AVAILABLE_GLYPH;
}
