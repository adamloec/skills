#!/usr/bin/env node
/**
 * Color guard — fails if source reintroduces hardcoded, non-theme-aware colors.
 *
 * Light/dark theming works only if every surface reads from the design system's
 * semantic tokens (bg-card, text-muted-foreground, border-border, bg-primary, …).
 * A baked hex, a fixed dark neutral, a white-alpha overlay, or a `dark:` variant
 * silently breaks one of the two themes. This script is the backstop; CI runs it.
 *
 * It scans className-shaped patterns only, so it does NOT flag legitimate JS
 * color data (e.g. category-accent hex maps, brand SVG stroke attributes,
 * `text-white` on a saturated button, or `bg-black/70` modal scrims).
 *
 * Usage:  node scripts/check-colors.mjs
 * Escape hatch (rare, justified): append `// color-guard-ignore` to the line.
 */

import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, relative } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = join(fileURLToPath(new URL(".", import.meta.url)), "..");
const SRC = join(ROOT, "src");

const RULES = [
  {
    // bg-[#111], text-[#abc123], border-[#fff]/50 — arbitrary hex utility
    re: /-\[#[0-9A-Fa-f]{3,8}\]/,
    msg: "arbitrary hex color utility — use a semantic token (bg-card, text-foreground, …)",
  },
  {
    // dark:bg-*, dark:hover:* — the app themes via the `.light` class, so Tailwind's
    // `dark:` variant tracks the OS (prefers-color-scheme), not the app theme.
    re: /\bdark:[a-z[-]/,
    msg: "`dark:` variant — tokens carry the theme here; `dark:` tracks the OS, not the toggle",
  },
  {
    // bg-neutral-900, bg-zinc-950 — a surface baked to one shade instead of a token
    re: /\bbg-(?:neutral|zinc|gray|slate|stone)-(?:700|800|900|950)\b/,
    msg: "fixed dark neutral surface — use bg-card / bg-muted / bg-secondary",
  },
  {
    // solid bg-black (not the allowed bg-black/NN scrim)
    re: /\bbg-black(?![/\w])/,
    msg: "solid bg-black — use a token; only bg-black/NN scrims are allowed",
  },
  {
    // bg-white/5, border-white/[0.06] — a white-alpha overlay tuned for dark
    re: /\b(?:bg|border|ring|from|via|to)-white\/(?:\[|\d)/,
    msg: "white-alpha overlay — use bg-accent / border-border (text-white on saturated is fine)",
  },
];

/** @type {{file:string,line:number,text:string,msg:string}[]} */
const violations = [];

function walk(dir) {
  for (const entry of readdirSync(dir)) {
    const p = join(dir, entry);
    const s = statSync(p);
    if (s.isDirectory()) {
      if (entry === "node_modules" || entry === ".next") continue;
      walk(p);
    } else if (/\.(tsx?|jsx?)$/.test(entry)) {
      scan(p);
    }
  }
}

function scan(file) {
  const lines = readFileSync(file, "utf8").split("\n");
  lines.forEach((text, i) => {
    if (text.includes("color-guard-ignore")) return;
    for (const rule of RULES) {
      if (rule.re.test(text)) {
        violations.push({ file: relative(ROOT, file), line: i + 1, text: text.trim(), msg: rule.msg });
      }
    }
  });
}

walk(SRC);

if (violations.length === 0) {
  console.log("✓ color guard: no hardcoded colors found");
  process.exit(0);
}

console.error(`✗ color guard: ${violations.length} hardcoded color(s) found\n`);
for (const v of violations) {
  console.error(`  ${v.file}:${v.line}`);
  console.error(`    ${v.msg}`);
  console.error(`    → ${v.text.length > 100 ? v.text.slice(0, 100) + "…" : v.text}\n`);
}
process.exit(1);
