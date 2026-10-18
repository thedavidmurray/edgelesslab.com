# edgelesslab.com — TypeScript Typecheck Baseline Benchmark

**Date:** 2026-09-29
**Machine:** Apple M2, 8 cores, 25769803776 bytes RAM (~24.6 GB), macOS 26.5.2 (Build 25F84)
**Node:** v26.10.0
**npm:** 11.19.1
**TypeScript (project):** 5.9.3 (from node_modules)
**npx tsc resolves to:** /Users/djm/.local/bin/npx → local node_modules/.bin/tsc → 5.9.3
**Commit:** b6a505ec8fa321fe87bdc4dbb6bc7d71483db31e — "test(analytics): add cookieless pageview coverage"
**Branch:** main
**Repo:** /Users/djm/claude-projects/edgelesslab.com
**tsconfig:** incremental=true, strict=true, module=bundler, jsx=react-jsx

## Command

```
npx tsc --noEmit -p .
```

Note: the repo's `check:design-system` script also runs `tsc --noEmit --incremental false` but includes extra design-system checks — this benchmark isolates pure typecheck only.

## Results

### Cold runs (cleared .tsbuildinfo + tsc cache before each run)

| Run | Time (s) |
|-----|----------|
| 1   | 2.774    |
| 2   | 2.265    |
| 3   | 2.572    |
| 4   | 2.658    |
| 5   | 2.282    |
| **mean** | **2.510** |
| **min**  | **2.265** |
| **max**  | **2.774** |

### Warm runs (incremental cache preserved)

| Run | Time (s) |
|-----|----------|
| 1   | 2.303    |
| 2   | 2.518    |
| 3   | 2.489    |
| 4   | 2.328    |
| 5   | 2.607    |
| **mean** | **2.449** |
| **min**  | **2.303** |
| **max**  | **2.607** |

### extendedDiagnostics (one warm run)

```
Files:                        1323
Lines of Library:            53142
Lines of Definitions:       300356
Lines of TypeScript:         38878
Lines of JavaScript:             0
Identifiers:                380965
Symbols:                    232097
Memory used:               333074K
I/O Read time:               0.11s
Parse time:                  0.85s
Bind time:                   0.58s
Total time:                  1.90s
```

### TypeScript 7 native preview (tsgo) — informational only, beta

```
npx -p @typescript/native-preview tsgo --noEmit -p .
```
Result: real 1.223s / user 1.570s / sys 0.469s (single run, not averaged)
Same TS5097 error as tsc 5.9.3 — pre-existing, unrelated to benchmark.

## Reproduction

```bash
cd /Users/djm/claude-projects/edgelesslab.com
git checkout main && git reset --hard b6a505ec8fa321fe87bdc4dbb6bc7d71483db31e
rm -f .tsbuildinfo
npx tsc --noEmit -p .
```

For warm runs, run the command twice — the second run benefits from incremental cache.

## Notes

- All 10 runs (5 cold + 5 warm) exited rc=1 with the same TS5097 error on `scripts/autofix/nextjs-build-gate.test.ts(2,63)` — this is a pre-existing project issue, not a benchmark artifact. It does not affect timing validity since tsc continues processing after reporting it.
- hyperfine not installed; used Python `time.perf_counter()` wall timing.
- /usr/bin/time on macOS does not support `-v` flag; used Python timing instead.
- No package.json or lockfile changes were made.