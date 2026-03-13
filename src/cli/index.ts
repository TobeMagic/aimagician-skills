#!/usr/bin/env node

import {
  ownedSkillsRoot,
  pluginsCatalogRoot,
  repositoryRoot,
  skillsCatalogRoot
} from "../shared/paths";

function main(): void {
  console.log("AImagician Skills scaffold is ready.");
  console.log(
    JSON.stringify(
      {
        repositoryRoot,
        ownedSkillsRoot,
        skillsCatalogRoot,
        pluginsCatalogRoot
      },
      null,
      2
    )
  );
}

main();
