import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    ".next-backup-autoresearch/**",
    "_next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    // Standalone apps and committed build output (minified bundles, generated
    // pages). Linting these buries real src/ errors under ~1,200 noise hits.
    ".standalone-stash/**",
    "pen-plotter/**",
    "tartanism/**",
    "total-serialism/**",
    "flow-viz/**",
    "lab/**",
    "blog/**",
    "products/**",
    "projects/**",
    "knowledge/**",
    "about/**",
    "privacy/**",
    "terms/**",
    "404/**",
    "_not-found/**",
    "docs/**",
    "public/**",
  ]),
]);

export default eslintConfig;
