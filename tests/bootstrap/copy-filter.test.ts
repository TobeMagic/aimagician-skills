import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { shouldCopyManagedSource } from "../../src/bootstrap/copy-filter";

describe("managed source copy filter", () => {
  it("keeps authored skill files", () => {
    expect(shouldCopyManagedSource(join("skills", "owned", "pptx-studio", "SKILL.md"))).toBe(true);
  });

  it.each([".git", ".private", ".pytest_cache", "node_modules", "__pycache__"])(
    "excludes transient %s directories at any depth",
    (directory) => {
      expect(shouldCopyManagedSource(join(directory, "artifact.bin"))).toBe(false);
      expect(
        shouldCopyManagedSource(
          join("skills", "owned", "pptx-studio", "scripts", directory, "artifact.bin")
        )
      ).toBe(false);
    }
  );

  it("does not exclude an authored directory that only resembles .pytest_cache", () => {
    expect(
      shouldCopyManagedSource(
        join("skills", "owned", "pptx-studio", "references", ".pytest_cache-guide", "README.md")
      )
    ).toBe(true);
  });

  it.each(["module.pyc", "module.PYO"])("excludes Python bytecode %s", (filename) => {
    expect(
      shouldCopyManagedSource(
        join("skills", "owned", "pptx-studio", "scripts", "window_pptx", filename)
      )
    ).toBe(false);
  });

  it("continues to exclude local external reference repositories", () => {
    expect(
      shouldCopyManagedSource(
        join("skills", "owned", "example", "references", "_external_repos", "upstream", "README.md")
      )
    ).toBe(false);
  });
});
