import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { loadTaxonomy } from "../../src/catalog/taxonomy";

const tempDirectories: string[] = [];

afterEach(async () => {
  await Promise.allSettled(
    tempDirectories.splice(0).map((directory) =>
      rm(directory, { recursive: true, force: true })
    )
  );
});

describe("loadTaxonomy", () => {
  it("accepts skill ids that include underscores", async () => {
    const root = await mkdtemp(join(tmpdir(), "skillbird-taxonomy-"));
    tempDirectories.push(root);
    const taxonomyPath = join(root, "taxonomy.yaml");

    await writeFile(
      taxonomyPath,
      [
        "groups:",
        "  - id: design",
        "    label: Design",
        "skills:",
        "  modelscope_imagegen:",
        "    group: design",
        "    tags: [image]"
      ].join("\n"),
      "utf8"
    );

    const taxonomy = await loadTaxonomy(taxonomyPath);

    expect(taxonomy.skills.modelscope_imagegen).toMatchObject({
      group: "design",
      tags: ["image"]
    });
  });
});
