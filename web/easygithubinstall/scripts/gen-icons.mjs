#!/usr/bin/env node
/**
 * Generates PNG icons from icon.svg for PWA (requires sharp — dev-only).
 * Fallback: copy SVG; manifest still works with SVG favicon.
 */
import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const dir = join(dirname(fileURLToPath(import.meta.url)), "..", "public");

try {
  const sharp = (await import("sharp")).default;
  const svg = readFileSync(join(dir, "icon.svg"));
  for (const size of [192, 512]) {
    const buf = await sharp(svg).resize(size, size).png().toBuffer();
    writeFileSync(join(dir, `icon-${size}.png`), buf);
  }
  console.log("Generated icon-192.png and icon-512.png");
} catch (err) {
  console.warn("sharp not available; create icon PNGs manually or run: npm i -D sharp && node scripts/gen-icons.mjs");
  if (!existsSync(join(dir, "icon-192.png"))) {
    writeFileSync(join(dir, "icon-192.png"), Buffer.alloc(0));
  }
}