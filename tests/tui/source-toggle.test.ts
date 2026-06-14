import { describe, expect, it } from "vitest";
import type { UserSkillConfig } from "../../src/config/user-config";
import { sourceStateLabel, renderSourceStateRow } from "../../src/tui/source-toggle";
import { COLORS } from "../../src/tui/theme";

const baseConfig: UserSkillConfig = {
  version: 1,
  groups: [],
  archivedIds: [],
  customTags: {},
  theme: "dove",
  sourceOverrides: {},
  includedIds: [],
  excludedIds: []
};

describe("source toggle helpers", () => {
  it("labels enabled default-disabled and disabled source states", () => {
    expect(sourceStateLabel(true, undefined)).toBe("enabled");
    expect(sourceStateLabel(false, undefined)).toBe("default-disabled");
    expect(sourceStateLabel(false, true)).toBe("enabled");
    expect(sourceStateLabel(true, false)).toBe("disabled");
  });

  it("renders deterministic rows with state labels", () => {
    expect(renderSourceStateRow(
      { id: "enabled-pack", enabled: true, description: "Enabled" },
      baseConfig,
      COLORS
    )).toContain("enabled");

    expect(renderSourceStateRow(
      { id: "business-pack", enabled: false, description: "Business" },
      baseConfig,
      COLORS
    )).toContain("default-disabled");

    expect(renderSourceStateRow(
      { id: "disabled-pack", enabled: true, description: "Disabled" },
      { ...baseConfig, sourceOverrides: { "disabled-pack": false } },
      COLORS
    )).toContain("disabled");
  });
});
