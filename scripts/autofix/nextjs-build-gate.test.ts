import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { detectIgnoreBuildErrors, fixIgnoreBuildErrors } from "./nextjs-build-gate";
import { writeFileSync, mkdirSync, rmSync, readFileSync } from "node:fs";
import { join } from "node:path";

const TEST_DIR = join(process.cwd(), "scripts/autofix/.test-tmp");

describe("nextjs-build-gate", () => {
  beforeEach(() => {
    mkdirSync(TEST_DIR, { recursive: true });
  });

  afterEach(() => {
    rmSync(TEST_DIR, { recursive: true, force: true });
  });

  describe("detectIgnoreBuildErrors", () => {
    it("returns false when config has no typescript block", () => {
      const p = join(TEST_DIR, "no-tsconfig.ts");
      writeFileSync(p, "export default {};\n");
      expect(detectIgnoreBuildErrors(p)).toBe(false);
    });

    it("returns false when ignoreBuildErrors is false", () => {
      const p = join(TEST_DIR, "safe.ts");
      writeFileSync(p, "export default { typescript: { ignoreBuildErrors: false } };\n");
      expect(detectIgnoreBuildErrors(p)).toBe(false);
    });

    it("returns true when ignoreBuildErrors is true", () => {
      const p = join(TEST_DIR, "bad.ts");
      writeFileSync(p, "export default { typescript: { ignoreBuildErrors: true } };\n");
      expect(detectIgnoreBuildErrors(p)).toBe(true);
    });
  });

  describe("fixIgnoreBuildErrors", () => {
    it("sets ignoreBuildErrors to false when it is true", () => {
      const p = join(TEST_DIR, "fix-me.ts");
      writeFileSync(p, "export default { typescript: { ignoreBuildErrors: true } };\n");
      const changed = fixIgnoreBuildErrors(p);
      expect(changed).toBe(true);
      const content = readFileSync(p, "utf-8");
      expect(content).toContain("ignoreBuildErrors: false");
      expect(content).not.toContain("ignoreBuildErrors: true");
    });

    it("adds typescript block when missing", () => {
      const p = join(TEST_DIR, "no-tsblock.ts");
      writeFileSync(p, "export default { output: \"export\" };\n");
      const changed = fixIgnoreBuildErrors(p);
      expect(changed).toBe(true);
      const content = readFileSync(p, "utf-8");
      expect(content).toContain("typescript");
      expect(content).toContain("ignoreBuildErrors: false");
    });

    it("returns false when no changes needed", () => {
      const p = join(TEST_DIR, "already-safe.ts");
      writeFileSync(p, "export default { typescript: { ignoreBuildErrors: false } };\n");
      const changed = fixIgnoreBuildErrors(p);
      expect(changed).toBe(false);
    });
  });
});
