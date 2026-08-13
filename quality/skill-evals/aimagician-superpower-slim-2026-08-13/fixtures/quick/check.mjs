import { readFile } from "node:fs/promises";

const readme = await readFile(new URL("./README.md", import.meta.url), "utf8");
if (!readme.includes("installs owned skills")) {
  throw new Error("README must use the corrected verb 'installs'.");
}
if (readme.includes("installes")) {
  throw new Error("README still contains the typo.");
}
console.log("quick-fixture: PASS");
