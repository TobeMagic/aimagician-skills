import { describe, expect, it } from "vitest";
import { shouldCopyManagedSource } from "../../src/bootstrap/copy-filter";

describe("shouldCopyManagedSource", () => {
  it("never installs an owned skill private library", () => {
    expect(shouldCopyManagedSource("/repo/skills/owned/pptx-studio/.private/sources/gaojie/example.pptx")).toBe(false);
  });

  it("keeps the public PPTX Studio runtime", () => {
    expect(shouldCopyManagedSource("/repo/skills/owned/pptx-studio/scripts/pptx_studio/physical_adapter.py")).toBe(true);
  });
});
