import blessed = require("blessed");
import { loadUserConfig, saveUserConfig, type UserSkillConfig } from "../config/user-config";
import { BIRD_ASCII, PALETTE } from "./theme";
import type { ThemeColors } from "./theme";
import type { CatalogSourceRecord } from "../catalog/source-types";

export type SourceStateLabel = "enabled" | "default-disabled" | "disabled";

export interface SourceToggleOptions {
  configBaseDir: string;
  currentColors: ThemeColors;
  sources: CatalogSourceRecord[];
  userConfig: UserSkillConfig;
  onToggle: (sourceId: string, enabled: boolean) => void;
}

export function sourceStateLabel(
  sourceEnabled: boolean,
  override: boolean | undefined
): SourceStateLabel {
  if (override === false) {
    return "disabled";
  }
  if (override === true || sourceEnabled) {
    return "enabled";
  }
  return "default-disabled";
}

export function renderSourceStateRow(
  source: Pick<CatalogSourceRecord, "id" | "enabled" | "description">,
  userConfig: UserSkillConfig,
  currentColors: ThemeColors
): string {
  const override = userConfig.sourceOverrides[source.id];
  const state = sourceStateLabel(source.enabled, override);
  const glyph = state === "enabled" ? "✔" : state === "default-disabled" ? "◦" : "✖";
  const color = state === "enabled" ? currentColors.brandYellow : state === "default-disabled" ? PALETTE.ghostWhite : PALETTE.dimGray;

  return `{${color}-fg}${glyph} ${source.id}{/${color}-fg}  {${PALETTE.dimGray}-fg}${state}{/${PALETTE.dimGray}-fg}  {${PALETTE.dimGray}-fg}${source.description ?? ""}{/${PALETTE.dimGray}-fg}`;
}

export function showSourceToggle(
  screen: blessed.Widgets.Screen,
  options: SourceToggleOptions
): void {
  const { configBaseDir, currentColors, sources, userConfig, onToggle } = options;
  const overrides = { ...userConfig.sourceOverrides };
  const localConfig = { ...userConfig, sourceOverrides: overrides };
  const items = sources.map((source) => renderSourceStateRow(source, localConfig, currentColors));

  const sourceBox = blessed.list({
    parent: screen,
    label: ` ${BIRD_ASCII} External Sources `,
    border: "line",
    height: "shrink",
    width: "60%",
    top: "center",
    left: "center",
    tags: true,
    keys: true,
    vi: true,
    mouse: true,
    shadow: true,
    style: {
      border: { fg: currentColors.brandYellow },
      bg: PALETTE.carbon,
      fg: PALETTE.ghostWhite
    },
    items
  });

  const hintBox = blessed.box({
    parent: screen,
    top: "center",
    left: "30%",
    width: "40%",
    height: "shrink",
    tags: true,
    content: `{${PALETTE.dimGray}-fg}space cycle  enter save  esc cancel{/${PALETTE.dimGray}-fg}`
  });

  sourceBox.focus();
  screen.render();

  function getSelectedIndex(): number {
    return (sourceBox as blessed.Widgets.ListElement & { selected?: number }).selected ?? 0;
  }

  sourceBox.key("space", () => {
    const idx = getSelectedIndex();
    const source = sources[idx];
    if (source) {
      const state = sourceStateLabel(source.enabled, overrides[source.id]);
      if (state === "enabled") {
        if (source.enabled) {
          overrides[source.id] = false;
        } else {
          delete overrides[source.id];
        }
      } else if (state === "default-disabled") {
        overrides[source.id] = true;
      } else {
        if (source.enabled) {
          delete overrides[source.id];
        } else {
          overrides[source.id] = true;
        }
      }
      localConfig.sourceOverrides = overrides;
      items[idx] = renderSourceStateRow(source, localConfig, currentColors);
      sourceBox.setItems([...items]);
      screen.render();
    }
  });

  sourceBox.key(["enter"], async () => {
    sourceBox.detach();
    hintBox.detach();

    const config = await loadUserConfig(configBaseDir);
    config.sourceOverrides = overrides;
    await saveUserConfig(configBaseDir, config);

    for (const source of sources) {
      const override = overrides[source.id];
      const isEnabled = override !== undefined ? override : source.enabled;
      const wasEnabled = source.enabled;
      if (isEnabled !== wasEnabled) {
        onToggle(source.id, isEnabled);
      }
    }

    screen.render();
  });

  sourceBox.key(["escape", "q"], () => {
    sourceBox.detach();
    hintBox.detach();
    screen.render();
  });
}
