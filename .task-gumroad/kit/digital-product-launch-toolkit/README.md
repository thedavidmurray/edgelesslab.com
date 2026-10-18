# Digital Product Launch Toolkit

The repeatable system for building, pricing, listing, and launching digital products. Templates, checklists, and scripts from shipping 17 products on Gumroad.

## What's Inside

- **guide.md / guide.pdf** -- 11-chapter guide (7,800+ words) covering the product pipeline, validation scorecard, 6-tier content system, packaging, Gumroad listing optimization, pricing strategy with real per-tier examples, wave-based launch sequencing, the content flywheel, common mistakes, the full shipped catalog with lessons per product, and scaling to 50 products. Includes 4 mermaid diagrams (pipeline, validation decision tree, wave launch sequence, content flywheel).
- **templates/** -- Product brief template, listing copy template
- **checklists/** -- Pre-build, pre-package, and launch day checklists
- **scripts/** -- URL verification script (run it before flipping any website flag)
- **Appendix C** -- the 17-product Edgeless Labs catalog as a ground-truth index
- **Appendix D** -- one fully filled-in product brief (CLAUDE.md Template Pack) showing the template in real, not abstract, form

## What Makes This Different From Free Resources

There is a lot of free launch advice online -- Justin Jackson, Daniel Vassallo, Indie Hackers retros, Gumroad's own blog. Three things make this toolkit different:

1. **The validation scorecard is weighted, not flat.** Problem Clarity and Credential are each 3x, which fails ideas where the author has no lived experience -- the dominant failure mode of first-time creators.
2. **Wave launches require a narrative thread.** Free advice says "launch multiple products." This toolkit enforces the rule that each wave shares a single story hook that doubles as the launch post.
3. **Quality gates run between stages, not just at the end.** Most launch checklists are one pre-publish checklist. This system gates every stage transition (validation to build, build to package, package to list), so mistakes are caught in place instead of at 11pm on launch day.

## Quick Start

1. Read Chapter 2 (Validation) and fill out `templates/product-brief.md` for your product idea
2. If validation score >= 36, proceed to build
3. Follow `checklists/pre-build.md` before starting content
4. Write your guide following the tier system in Chapter 3
5. Use `checklists/pre-package.md` before creating your ZIP
6. Write listing copy using `templates/listing-copy.md`
7. Run through `checklists/launch-day.md` on launch day
8. Verify URL with `scripts/verify-url.sh` before updating your website

## Prerequisites

- A Gumroad account (free to create)
- Content to sell (code, templates, guides)
- `curl` for URL verification (pre-installed on macOS/Linux)

## File Structure

```
launch-toolkit/
  guide.md                        -- Full 10-chapter guide
  guide.pdf                       -- PDF version
  templates/
    product-brief.md              -- Validation + brief template
    listing-copy.md               -- Gumroad listing template
  checklists/
    pre-build.md                  -- Before creating content
    pre-package.md                -- Before creating ZIP
    launch-day.md                 -- Launch day verification
  scripts/
    verify-url.sh                 -- URL liveness checker
  README.md
  CHANGELOG.md
```

## Version

1.0.0 -- Initial release, April 2026
