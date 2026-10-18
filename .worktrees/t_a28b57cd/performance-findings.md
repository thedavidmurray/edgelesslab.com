# Tartanism Performance Regression — Investigation Report

## Summary
Lighthouse score dropped from ~0.86 to 0.74 on the tartanism page. Root cause: oversized JS bundle + main thread work.

## Metrics (Lighthouse 13.4.0, live site)
| Metric | Score | Value |
|---|---|---|
| Performance | 0.74 | — |
| Total Blocking Time | 0.34 | 850ms |
| LCP | 0.84 | 2.7s |
| CLS | 1.0 | 0 |
| Unused JavaScript | 0.0 | 60KB wasted |
| Speed Index | 0.99 | 2.0s |
| Interactive | 0.94 | 3.3s |

## Bundle Analysis (out/tartanism/app/assets/)
- index-3ZW5epyv.js — 352KB / 106KB transferred, 57% unused
- OldApp-jPBFSGd2.js — 173KB (legacy, lazy)
- index-CpV7C7bY.css — 40KB (critters inlines critical, lazy-loads rest)

## What Changed
1. Commit 8da20f800 (Sep 12) — last tartanism change; removed GA4 from source but deployed HTML still has it
2. index-3ZW5epyv.js hash unchanged since June — no code-splitting done
3. GA4 snippet with fake G-XXXXXXXXXX ID makes pointless network request

## Recommendations
1. Code-split main bundle (index → lazy chunks for generator/PatternDetail)
2. Remove dead GA4 snippet from HTML template
3. Dynamic import for non-critical chunks on initial load

## Files Examined
- public/tartanism/app/index.html (deployed template)
- out/tartanism/app/index.html (built output)
- tartanism/app/index.html (source)
- out/tartanism/app/assets/index-3ZW5epyv.js (352KB bundle)
- .github/workflows/deploy.yml (CI/CD pipeline)
- scripts/run-critters.mjs (postbuild critters inlining)