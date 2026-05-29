export const BEE_ASCII = "\u{1F41D}";

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
}

const themes: Record<ThemeName, ThemeColors> = {
  bee: {
    brandYellow: "yellow",
    brandBlack: "black",
    installed: "green",
    uninstalled: "white",
    archived: "gray",
    archivedFg: "cyan",
    selectedBg: "blue",
    selectedFg: "white",
    error: "red",
    accent: "yellow",
    muted: "gray",
    headerBorder: "yellow",
    panelBorder: "yellow"
  },
  monokai: {
    brandYellow: "orange",
    brandBlack: "black",
    installed: "green",
    uninstalled: "white",
    archived: "gray",
    archivedFg: "magenta",
    selectedBg: "magenta",
    selectedFg: "white",
    error: "red",
    accent: "orange",
    muted: "gray",
    headerBorder: "orange",
    panelBorder: "orange"
  },
  nord: {
    brandYellow: "cyan",
    brandBlack: "black",
    installed: "green",
    uninstalled: "white",
    archived: "gray",
    archivedFg: "blue",
    selectedBg: "blue",
    selectedFg: "white",
    error: "red",
    accent: "cyan",
    muted: "gray",
    headerBorder: "cyan",
    panelBorder: "cyan"
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
    fg: "white"
  }
};

export function targetShortLabel(target: string): string {
  const labels: Record<string, string> = {
    codex: "Cx",
    claude: "Cd",
    opencode: "Oc",
    gemini: "Gm",
    hermes: "Hm",
    cursor: "Cr",
    copilot: "Cp"
  };
  return labels[target] ?? target.slice(0, 2);
}

export function formatMatrixCell(
  isAvailable: boolean,
  isInstalled: boolean,
  _isManaged: boolean
): string {
  if (!isAvailable) return " -";
  if (isInstalled) return "\u25CF";
  return "\u25CB";
}
