/**
 * Tests for the secret-sanitization regex set in src/index.ts.
 *
 * Run with: npx vitest run
 *
 * NOTE: index.ts has a top-level `process.exit(1)` if EXTERNAL_API_KEY is
 * unset. We set it before importing so the module loads cleanly.
 */
import { describe, expect, it, beforeAll } from "vitest";

let SECRET_PATTERNS: RegExp[];
let sanitizeError: (e: unknown) => string;

beforeAll(async () => {
  process.env.EXTERNAL_API_KEY ||= "test-key-for-tests-only";
  const mod = await import("../src/index.ts");
  SECRET_PATTERNS = mod.SECRET_PATTERNS;
  sanitizeError = mod.sanitizeError;
});

function sanitize(input: string): string {
  let out = input;
  for (const p of SECRET_PATTERNS) out = out.replace(p, "[REDACTED]");
  return out;
}

describe("secret sanitization", () => {
  it("redacts OpenAI sk- keys", () => {
    const msg = "Auth failed with sk-abcdefghij1234567890XYZ";
    expect(sanitize(msg)).not.toContain("sk-abcdefghij");
  });

  it("redacts Bearer tokens", () => {
    const msg = "Authorization: Bearer abc.def.ghi";
    expect(sanitize(msg)).not.toContain("Bearer abc");
  });

  it("redacts api_key= form", () => {
    const msg = "url?api_key=supersecret123";
    expect(sanitize(msg)).not.toContain("supersecret123");
  });

  it("redacts GitHub PATs", () => {
    const msg = "token ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    expect(sanitize(msg)).not.toContain("ghp_aaaa");
  });

  it("redacts AWS access key IDs", () => {
    const msg = "AWS key AKIAIOSFODNN7EXAMPLE found";
    expect(sanitize(msg)).not.toContain("AKIAIOSFODNN7EXAMPLE");
  });

  it("redacts JWT tokens (eyJ... header.payload.signature)", () => {
    const jwt =
      "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4ifQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c";
    const msg = `Token: ${jwt}`;
    expect(sanitize(msg)).not.toContain(jwt);
    expect(sanitize(msg)).toContain("[REDACTED]");
  });

  it("sanitizeError handles Error instances", () => {
    const err = new Error("call failed: sk-abcdefghij1234567890XYZ");
    const out = sanitizeError(err);
    expect(out).not.toContain("sk-abcdefghij");
  });

  it("sanitizeError handles non-Error values", () => {
    const out = sanitizeError("plain string with ghp_aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa");
    expect(out).not.toContain("ghp_aaaa");
  });
});
