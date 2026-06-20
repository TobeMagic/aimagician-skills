import { describe, expect, it } from "vitest";
import type { ManagerSkillRecord } from "../../src/manager/manager";
import type { SupportedTarget } from "../../src/model/targets";
import {
  COMMAND_HELP,
  findUnsupportedBlessedTags,
  renderMatrixLabel,
  renderMatrixRow,
  renderSkillRow,
  stripBlessedTags,
  validateBlessedTags,
  visibleWidth
} from "../../src/tui/rendering";
import { BIRD_SPLASH } from "../../src/tui/theme";

describe("tui rendering helpers", () => {
  it("uses only numeric ANSI blessed color tags with balanced markup", () => {
    const content = [COMMAND_HELP, ...BIRD_SPLASH].join("\n");

    expect(content).not.toContain("yellow-fg");
    expect(content).not.toContain("{bold}←{bold}");
    expect(validateBlessedTags(content)).toEqual({ unsupported: [], unbalanced: [] });
  });

  it("renders matrix rows with stable visible widths when tags are present", () => {
    const targets: SupportedTarget[] = ["codex", "opencode", "gemini"];
    const skills = [
      skill({ id: "short", installedTargets: ["codex"], managedTargets: ["codex"] }),
      skill({ id: "archived-long-skill", archived: true, availableTargets: ["codex", "gemini"] }),
      skill({ id: "selected", availableTargets: ["opencode", "gemini"] })
    ];
    const idWidth = Math.max(...skills.map((item) => visibleWidth(item.id)), 8);
    const rows = skills.map((item) => renderMatrixRow(item, targets, new Set(["selected"]), idWidth));
    const plainRows = rows.map(stripBlessedTags);

    expect(new Set(rows.map(visibleWidth)).size).toBe(1);
    expect(plainRows.map((row) => row.indexOf("Cx:"))).toEqual([idWidth + 6, idWidth + 6, idWidth + 6]);
    for (const row of rows) {
      expect(validateBlessedTags(row)).toEqual({ unsupported: [], unbalanced: [] });
    }
  });

  it("renders skill rows and matrix labels without leaking raw blessed tags", () => {
    const row = renderSkillRow(
      skill({ id: "aimagician-superpower", installedTargets: ["codex"], managedTargets: ["codex"] }),
      "codex",
      new Set(["aimagician-superpower"]),
      new Set(["aimagician-superpower"]),
      "super"
    );
    const label = renderMatrixLabel(["codex", "opencode"]);

    expect(stripBlessedTags(label)).toContain("Matrix Cx Oc");
    expect(findUnsupportedBlessedTags(row)).toEqual([]);
    expect(validateBlessedTags(row)).toEqual({ unsupported: [], unbalanced: [] });
    expect(stripBlessedTags(row)).toContain("aimagician-superpower");
  });
});

function skill(overrides: Partial<ManagerSkillRecord>): ManagerSkillRecord {
  return {
    id: "demo-skill",
    origin: "owned",
    group: "build",
    tags: [],
    customTags: [],
    recommendedScopes: ["global"],
    recommendedTargets: ["codex"],
    availableTargets: ["codex", "opencode", "gemini"],
    installedTargets: [],
    managedTargets: [],
    commandOnly: false,
    archived: false,
    ...overrides
  };
}
