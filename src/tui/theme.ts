// ── Brand ──────────────────────────────────────────────────────────────
export const BEE_ASCII = "\u{1F41D}";

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

// ── PRD §2.2: Splash Screen (Braille Bee Art) ─────────────────────────
export const BEE_SPLASH = [
  "",
  "       {amber}\u2808\u2808\u2800\u2808\u2808\u2800\u2808\u2808{/amber}",
  "      {amber}\u2808\u2808\u2808\u2808\u2808\u2808\u2808\u2808\u2808\u2808\u2808{/amber}",
  "     {amber}\u2808\u2808\u2808\u2808\u2838\u2838\u2808\u2808\u2838\u2838\u2808\u2808\u2808\u2808{/amber}",
  "      {amber}\u2808\u2808\u2808\u2808\u2808\u2808\u2808\u2808\u2808\u2808\u2808{/amber}",
  "       {amber}\u2808\u2808\u2808\u2808\u2800\u2808\u2808\u2808\u2808{/amber}",
  "         {amber}\u2808\u2808\u2808\u2808\u2808\u2808\u2808\u2808{/amber}",
  "          {dimGray}\u2808\u2808\u2808\u2808\u2808\u2808\u2808{/dimGray}",
  "",
  "    {bold}{amber} S K I L L B E E {/amber}{/bold}",
  "    {dimGray}\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500{/dimGray}",
  "    {ghostWhite}Personal Skill Manager{/ghostWhite}",
  "    {ghostWhite}for AI CLI Tools{/ghostWhite}",
  "",
  "    {dimGray}v1.1.0  \u2022  github.com/TobeMagic/aimagician-skills{/dimGray}",
  ""
];

// ── PRD §2.3: Hive Layout Select Indicators ────────────────────────────
export const SELECT_GLYPH = "\u25B6";   // ▶  amber — selected item
export const UNSELECT_GLYPH = "\u25E6"; // ◦  ghost white — unselected
export const GROUP_CUSTOM_PREFIX = "\u25CE"; // ◎ — custom group marker

// ── Status Glyphs ──────────────────────────────────────────────────────
export const INSTALLED_GLYPH = "\u2714";   // ✔  pollen green
export const AVAILABLE_GLYPH = "\u25E6";   // ◦  ghost white
export const UNAVAILABLE_GLYPH = "\u2014"; // —  dim gray
export const BROKEN_GLYPH = "\u{1F494}";   // 💔 stinger red

// ── Theme System ───────────────────────────────────────────────────────
export const THEME_NAMES = ["bee", "monokai", "nord"] as const;
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
  bee: {
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
  return themes[name as ThemeName] ?? themes.bee;
}

export const COLORS: ThemeColors = themes.bee;

export const SELECTED_LIST_STYLE = {
  selected: {
    bg: COLORS.selectedBg,
    fg: COLORS.selectedFg,
    bold: true
  },
  item: {
    fg: PALETTE.ghostWhite
  }
};

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
