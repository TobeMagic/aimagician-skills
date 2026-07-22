#!/usr/bin/env node

import { createHash } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import { basename, dirname, extname, join, resolve } from "node:path";

const API = "https://commons.wikimedia.org/w/api.php";

function usage() {
  return [
    "Usage: fetch-wikimedia-assets.mjs --query <text> [--query <text> ...] --output-dir <dir>",
    "       [--count <1-10>] [--width <320-4096>] [--manifest <path>] [--user-agent <descriptive value>]",
    "",
    "Searches Wikimedia Commons on demand and writes an asset manifest with source, author, license, URL, and SHA-256 evidence.",
    "Set WIKIMEDIA_USER_AGENT or pass --user-agent. Do not use downloaded media until its recorded license fits the project."
  ].join("\n");
}

function parseArgs(argv) {
  const options = { queries: [], count: 2, width: 1600 };
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token === "--help" || token === "-h") return { help: true };
    if (!["--query", "--output-dir", "--count", "--width", "--manifest", "--user-agent"].includes(token)) {
      throw new Error(`Unknown option: ${token}`);
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) throw new Error(`${token} requires a value`);
    index += 1;
    if (token === "--query") options.queries.push(value.trim());
    else if (token === "--count") options.count = Number(value);
    else if (token === "--width") options.width = Number(value);
    else options[token.slice(2).replace("-", "_")] = value;
  }
  if (options.queries.length === 0 || options.queries.some((query) => !query)) throw new Error("At least one non-empty --query is required");
  if (!options.output_dir) throw new Error("--output-dir is required");
  if (!Number.isInteger(options.count) || options.count < 1 || options.count > 10) throw new Error("--count must be an integer from 1 to 10");
  if (!Number.isInteger(options.width) || options.width < 320 || options.width > 4096) throw new Error("--width must be an integer from 320 to 4096");
  options.user_agent = options.user_agent ?? process.env.WIKIMEDIA_USER_AGENT;
  if (!options.user_agent || options.user_agent.length < 12 || !/[\/(@]/.test(options.user_agent)) {
    throw new Error("A descriptive --user-agent or WIKIMEDIA_USER_AGENT is required");
  }
  return options;
}

function plainText(value) {
  return String(value ?? "")
    .replace(/<[^>]*>/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&quot;/g, '"')
    .replace(/&#39;|&apos;/g, "'")
    .replace(/\s+/g, " ")
    .trim();
}

function safeSlug(value) {
  const slug = String(value).normalize("NFKD").replace(/[^A-Za-z0-9._-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 72);
  return slug || "asset";
}

function metadataValue(metadata, key) {
  return plainText(metadata?.[key]?.value);
}

function extensionFor(url, contentType) {
  const fromUrl = extname(basename(new URL(url).pathname)).toLowerCase();
  if (/^\.(png|jpe?g|webp|gif|svg|tiff?)$/.test(fromUrl)) return fromUrl === ".jpeg" ? ".jpg" : fromUrl;
  const byType = { "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif", "image/svg+xml": ".svg", "image/tiff": ".tiff" };
  return byType[contentType] ?? ".img";
}

async function requestJson(params, userAgent) {
  const url = `${API}?${new URLSearchParams(params)}`;
  const response = await fetch(url, { headers: { "user-agent": userAgent, accept: "application/json" }, signal: AbortSignal.timeout(30_000) });
  if (!response.ok) throw new Error(`Wikimedia API returned ${response.status}`);
  return response.json();
}

async function search(query, options) {
  const payload = await requestJson({
    action: "query",
    format: "json",
    formatversion: "2",
    generator: "search",
    gsrsearch: query,
    gsrnamespace: "6",
    gsrlimit: String(options.count),
    prop: "imageinfo",
    iiprop: "url|size|mime|extmetadata",
    iiurlwidth: String(options.width)
  }, options.user_agent);
  return payload.query?.pages ?? [];
}

async function download(page, query, outputDir, options) {
  const info = page.imageinfo?.[0];
  const url = info?.thumburl ?? info?.url;
  if (!url) return null;
  const response = await fetch(url, { headers: { "user-agent": options.user_agent, accept: "image/*" }, signal: AbortSignal.timeout(60_000) });
  if (!response.ok) throw new Error(`Asset download returned ${response.status}: ${url}`);
  const contentType = String(response.headers.get("content-type") ?? info.mime ?? "").split(";")[0].toLowerCase();
  if (!contentType.startsWith("image/")) throw new Error(`Refusing non-image response (${contentType || "unknown"}): ${url}`);
  const bytes = Buffer.from(await response.arrayBuffer());
  const extension = extensionFor(url, contentType);
  const filename = `${safeSlug(query)}-${page.pageid ?? safeSlug(page.title)}${extension}`;
  const outputPath = join(outputDir, filename);
  await writeFile(outputPath, bytes);
  const metadata = info.extmetadata ?? {};
  return {
    id: safeSlug(`${query}-${page.pageid ?? page.title}`),
    query,
    file: filename,
    title: plainText(page.title).replace(/^File:/, ""),
    source_page: info.descriptionurl ?? "",
    source_file: info.url ?? url,
    author: metadataValue(metadata, "Artist") || metadataValue(metadata, "Credit") || "unknown",
    license: metadataValue(metadata, "LicenseShortName") || "unknown",
    license_url: metadataValue(metadata, "LicenseUrl"),
    usage_terms: metadataValue(metadata, "UsageTerms"),
    mime: contentType,
    source_dimensions: { width: info.width ?? null, height: info.height ?? null },
    bytes: bytes.length,
    sha256: createHash("sha256").update(bytes).digest("hex")
  };
}

async function main(options) {
  const outputDir = resolve(options.output_dir);
  const manifestPath = resolve(options.manifest ?? join(outputDir, "asset-manifest.json"));
  await mkdir(outputDir, { recursive: true });
  await mkdir(dirname(manifestPath), { recursive: true });
  const assets = [];
  const failures = [];
  for (const query of options.queries) {
    try {
      const pages = await search(query, options);
      for (const page of pages.slice(0, options.count)) {
        try {
          const asset = await download(page, query, outputDir, options);
          if (asset) assets.push(asset);
        } catch (error) {
          failures.push({ query, title: plainText(page.title), error: error.message });
        }
      }
      if (pages.length === 0) failures.push({ query, error: "No matching Commons files" });
    } catch (error) {
      failures.push({ query, error: error.message });
    }
  }
  const manifest = {
    schema_version: 1,
    provider: "Wikimedia Commons",
    retrieved_at: new Date().toISOString(),
    output_dir: outputDir,
    requested_width: options.width,
    assets,
    failures,
    review_required: "Verify subject fit, attribution, license terms, and derivative-use constraints before publication."
  };
  await writeFile(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  process.stdout.write(`${JSON.stringify({ manifest: manifestPath, downloaded: assets.length, failed: failures.length }, null, 2)}\n`);
  if (assets.length === 0) process.exitCode = 1;
}

try {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) process.stdout.write(`${usage()}\n`);
  else await main(options);
} catch (error) {
  process.stderr.write(`${error.message}\n\n${usage()}\n`);
  process.exitCode = 2;
}
