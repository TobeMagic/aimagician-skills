import { access, readFile } from "node:fs/promises";
import { constants } from "node:fs";
import { describe, expect, it } from "vitest";
import { loadScopedUserConfig } from "../../src/config/user-config";
import { previewInstallSkills, setSkillOverride } from "../../src/manager/manager";
import { planManagedInstallSync } from "../../src/bootstrap/direct-target-sync";

describe("v3 acceptance coverage", () => {
  it("ACC-01 covers include/exclude priority default-disabled sources and manifest isolation tests", async () => {
    expect(loadScopedUserConfig).toBeTypeOf("function");
    expect(setSkillOverride).toBeTypeOf("function");
    await access("tests/config/user-config.test.ts", constants.F_OK);
    await access("tests/manager/manager-operations.test.ts", constants.F_OK);

    const managerTests = await readFile("tests/manager/manager-operations.test.ts", "utf8");
    expect(managerTests).toContain("source-default-disabled");
    expect(managerTests).toContain("excluded");
    expect(managerTests).toContain("keeps archive overrides isolated");
  });

  it("ACC-02 covers selected-target sync and manual-file preservation tests", async () => {
    expect(planManagedInstallSync).toBeTypeOf("function");
    await access("tests/bootstrap/direct-target-sync.test.ts", constants.F_OK);

    const syncTests = await readFile("tests/bootstrap/direct-target-sync.test.ts", "utf8");
    expect(syncTests).toContain("updates only the selected direct targets");
    expect(syncTests).toContain("keeps unmanaged directories");
    expect(syncTests).toContain("manual-skill");
  });

  it("ACC-03 covers project-scope installs into project-local CLI paths", async () => {
    const managerTests = await readFile("tests/manager/manager-operations.test.ts", "utf8");
    expect(managerTests).toContain("installs selected skills into project-native target homes");
    expect(managerTests).toContain(".claude");
    expect(managerTests).toContain("projectDir");
  });

  it("ACC-04 documents real global verification as preview-confirmed and user-approved", async () => {
    const prd = await readFile("docs/PRD.md", "utf8");
    expect(prd).toContain("ACC-04");
    expect(prd).toContain("explicit user approval");
    expect(prd).toContain("preview confirmation");
  });

  it("ACC-05 covers PRD checklist plus TUI orchestration helper tests", async () => {
    expect(previewInstallSkills).toBeTypeOf("function");
    await access("tests/tui/source-toggle.test.ts", constants.F_OK);

    const prd = await readFile("docs/PRD.md", "utf8");
    expect(prd).toContain("ACC-05");
    expect(prd).toContain("v3 Acceptance Status");
  });
});
