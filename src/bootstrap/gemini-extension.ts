import { cp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { basename, join } from "node:path";

export interface MaterializeGeminiExtensionOptions {
  assetId: string;
  sourceDir: string;
  workspaceRoot: string;
}

export async function materializeGeminiExtension(
  options: MaterializeGeminiExtensionOptions
): Promise<string> {
  const extensionRoot = join(
    options.workspaceRoot,
    "generated",
    "gemini",
    options.assetId
  );
  const bundledSkillDir = join(extensionRoot, "skills", options.assetId);
  const originalSkill = await readFile(join(options.sourceDir, "SKILL.md"), "utf8");

  await rm(extensionRoot, { recursive: true, force: true });
  await mkdir(join(extensionRoot, "skills"), { recursive: true });
  await cp(options.sourceDir, bundledSkillDir, {
    recursive: true,
    force: true,
    filter: (source) => basename(source) !== ".git"
  });
  await writeFile(
    join(extensionRoot, "GEMINI.md"),
    createGeminiContext(options.assetId, originalSkill),
    "utf8"
  );
  await writeFile(
    join(extensionRoot, "gemini-extension.json"),
    JSON.stringify(
      {
        name: options.assetId,
        version: "1.0.0",
        contextFileName: "GEMINI.md"
      },
      null,
      2
    ),
    "utf8"
  );

  return extensionRoot;
}

function createGeminiContext(assetId: string, skillMarkdown: string): string {
  return [
    `# ${assetId}`,
    "",
    `This Gemini extension bundles the repository-managed skill \`${assetId}\`.`,
    `The original skill directory is included at \`skills/${assetId}/\`.`,
    "",
    "---",
    "",
    skillMarkdown.trim(),
    ""
  ].join("\n");
}
