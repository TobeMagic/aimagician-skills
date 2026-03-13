import { z } from "zod";
import { assetKinds, catalogSections, type CatalogSection } from "../model/assets";
import {
  capabilityKinds,
  capabilityStatuses,
  supportedTargets
} from "../model/targets";
import type {
  CatalogFileInput,
  CatalogSourceInput
} from "./source-types";

const slugSchema = z.string().regex(/^[a-z0-9]+(?:-[a-z0-9]+)*$/);

const capabilitySupportSchema = z
  .object({
    support: z.enum(capabilityStatuses),
    reason: z.string().min(1).optional()
  })
  .strict();

const capabilityMapSchema = z.partialRecord(
  z.enum(capabilityKinds),
  capabilitySupportSchema
);

const targetCapabilitiesSchema = z.partialRecord(
  z.enum(supportedTargets),
  capabilityMapSchema
);

export const targetSelectionSchema = z
  .object({
    include: z.array(z.enum(supportedTargets)).min(1).optional(),
    exclude: z.array(z.enum(supportedTargets)).min(1).optional(),
    capabilities: targetCapabilitiesSchema.optional()
  })
  .strict()
  .superRefine((selection, context) => {
    const include = new Set(selection.include ?? []);
    const exclude = new Set(selection.exclude ?? []);

    for (const target of include) {
      if (exclude.has(target)) {
        context.addIssue({
          code: z.ZodIssueCode.custom,
          message: `Target "${target}" cannot be both included and excluded`
        });
      }
    }
  });

function createAssetSchema(section: CatalogSection) {
  const expectedKind = section === "skills" ? "skill" : "plugin";

  return z
    .object({
      id: slugSchema,
      kind: z.literal(expectedKind),
      path: z.string().min(1).optional(),
      description: z.string().min(1).optional(),
      targets: targetSelectionSchema.optional()
    })
    .strict();
}

function createBaseSourceSchema(section: CatalogSection) {
  return z
    .object({
      id: slugSchema,
      enabled: z.boolean().default(true),
      description: z.string().min(1).optional(),
      version: z.string().min(1).optional(),
      targets: targetSelectionSchema.optional(),
      assets: z.array(createAssetSchema(section)).min(1)
    })
    .strict();
}

function createGithubSourceSchema(section: CatalogSection) {
  return createBaseSourceSchema(section).extend({
    type: z.literal("github"),
    github: z
      .object({
        repo: z.string().regex(/^[^/\s]+\/[^/\s]+$/),
        ref: z.string().min(1).optional(),
        path: z.string().min(1).optional()
      })
      .strict()
  });
}

function createCommandSourceSchema(section: CatalogSection) {
  return createBaseSourceSchema(section).extend({
    type: z.literal("command"),
    command: z
      .object({
        run: z.string().min(1),
        shell: z.string().min(1).optional(),
        cwd: z.string().min(1).optional()
      })
      .strict()
  });
}

export function createCatalogFileSchema(section: CatalogSection) {
  if (!catalogSections.includes(section)) {
    throw new Error(`Unsupported catalog section: ${section}`);
  }

  return z
    .object({
      sources: z.array(
        z.discriminatedUnion("type", [
          createGithubSourceSchema(section),
          createCommandSourceSchema(section)
        ])
      )
    })
    .strict();
}

export function parseCatalogFile(
  section: CatalogSection,
  input: unknown
): CatalogFileInput {
  return createCatalogFileSchema(section).parse(input);
}

export function isCatalogSourceInput(value: unknown): value is CatalogSourceInput {
  return z
    .object({
      id: slugSchema,
      type: z.enum(["github", "command"] as const),
      assets: z.array(
        z.object({
          id: slugSchema,
          kind: z.enum(assetKinds)
        })
      )
    })
    .safeParse(value).success;
}
