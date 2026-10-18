#!/usr/bin/env node
"use strict";

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";

// ── Types ────────────────────────────────────────────────────

type NextConfig = {
  typescript?: { ignoreBuildErrors?: boolean };
  [key: string]: unknown;
};

// ── Detection ────────────────────────────────────────────────

function loadConfig(path: string): NextConfig | null {
  if (!existsSync(path)) return null;
  try {
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const raw = require(path);
    return (raw.default ?? raw) as NextConfig;
  } catch {
    return null;
  }
}

export function detectIgnoreBuildErrors(configPath: string): boolean {
  const cfg = loadConfig(configPath);
  if (!cfg) return false;
  return cfg.typescript?.ignoreBuildErrors === true;
}

// ── Fix ──────────────────────────────────────────────────

export function fixIgnoreBuildErrors(configPath: string): boolean {
  const content = readFileSync(configPath, "utf-8");

  // Case 1: `typescript: { ignoreBuildErrors: true }` → set to false
  if (/\bignoreBuildErrors\s*:\s*true\b/.test(content)) {
    const fixed = content.replace(
      /(\bignoreBuildErrors\s*:\s*)true\b/,
      "$1false",
    );
    writeFileSync(configPath, fixed, "utf-8");
    return true;
  }

  // Case 2: no typescript block at all → add it
  if (!/\btypescript\s*:/.test(content)) {
    const insertAfter = content.lastIndexOf("};");
    if (insertAfter !== -1) {
      const before = content.slice(0, insertAfter);
      const after = content.slice(insertAfter);
      const fixed =
        before +
        ",\n  typescript: { ignoreBuildErrors: false }" +
        after;
      writeFileSync(configPath, fixed, "utf-8");
      return true;
    }
  }

  return false;
}

// ── CLI ──────────────────────────────────────────────────

function main() {
  const args = process.argv.slice(2);
  const mode = args[0] ?? "check";
  const configFile = args[1] ?? join(process.cwd(), "next.config.ts");

  if (mode === "fix") {
    const changed = fixIgnoreBuildErrors(configFile);
    if (changed) {
      console.log(`Fixed ignoreBuildErrors in ${configFile}`);
    } else {
      console.log(`No changes needed for ${configFile}`);
    }
    process.exit(changed ? 0 : 1);
  } else {
    // check mode
    const bad = detectIgnoreBuildErrors(configFile);
    if (bad) {
      console.error(`FAIL: ${configFile} has ignoreBuildErrors: true`);
      process.exit(1);
    }
    console.log(`OK: ${configFile} — ignoreBuildErrors is not enabled`);
    process.exit(0);
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
