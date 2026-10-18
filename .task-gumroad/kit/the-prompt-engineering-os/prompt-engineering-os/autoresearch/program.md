# Listing Autoresearch — Experiment Protocol

## What This Is

An autoresearch loop that iteratively improves the Gumroad product listing copy.
Based on Karpathy's autoresearch pattern: one mutable file + one scalar metric + fixed time budget + git-based ratcheting.

## Architecture

```
prepare.py    — FROZEN: scoring function, forbidden word filter, experiment runner
listing.md    — MUTABLE: the product listing copy (YOUR TARGET)
program.md    — THIS FILE: instructions for the autoresearch agent
results.tsv   — APPEND-ONLY: experiment log with scores
run.sh        — Loop runner (N iterations)
```

## The Experiment Loop

Each iteration:

1. **Read** `results.tsv` to see what's been tried and what scored highest
2. **Read** `listing.md` to understand the current state of the copy
3. **Propose** ONE specific change to `listing.md`
4. **Check** the change doesn't introduce any forbidden words (see below)
5. **Write** the modified `listing.md`
6. **Run** `python3.11 prepare.py --id <experiment_name>`
7. **Decide**: if composite score improved, keep the change. If not, revert `listing.md` to the previous version.

## What You Can Modify in listing.md

### High-Impact Targets (modify these first)
- **Opening hook** — The first 3 sentences are the highest-leverage copy on the page.
  - Try: leading with a specific failure mode instead of a generalization
  - Try: opening with a concrete outcome ("18 months of production Claude work, distilled")
  - Try: reordering the problem/solution framing
- **Short description** — The one-sentence card preview. It's what buyers see before clicking.
  - Try: leading with the outcome, not the contents
  - Try: making the "18 months" detail more prominent
  - Try: adding a sharper specific claim
- **"What makes this different" section** — The section that earns the price
  - Try: making each bullet more concrete and specific
  - Try: adding a specific outcome to each differentiator
  - Try: reordering bullets so the strongest claim is first
- **Pricing tier descriptions** — Where purchase decisions happen
  - Try: adding a "best for" line to each tier
  - Try: making the Professional upgrade reason more concrete
  - Try: adding a specific outcome to the Team tier

### Medium-Impact Targets
- **"Who this is for" section** — Make each persona more specific
- **Chapter descriptions** — Tighten any that are vague or sound like every other guide
- **The stats line** — "30 chapters. 100+ templates. 125 code examples. 22 reference tables."
  - Try: reordering these by what matters most to buyers
  - Try: adding "8 frameworks" or "7 anti-patterns" to the stat line
- **The refund guarantee** — Make it more specific and confident

### Low-Impact Targets
- Sentence structure within existing paragraphs
- Minor word substitutions that don't change meaning

## Forbidden Words (Hard Filter — AUTO-REJECTED)

The following words will cause the score to be set to 0 regardless of quality:
- "revolutionary"
- "game-changing"
- "next-level"
- "leverage"
- "robust"
- "comprehensive"
- "crucial"
- "transformative"
- "incredible"
- "amazing"

These come from `brand-notes.md`. Using any of them causes immediate rejection.
Check your proposed copy before writing it.

## Scoring Dimensions (for your reference)

The judge scores on 5 dimensions (each 1-10):
- **CLARITY** (25%): Is the value proposition immediately clear?
- **URGENCY** (20%): Does it create desire to buy now?
- **CREDIBILITY** (20%): Does it feel trustworthy and specific?
- **VALUE_COMMUNICATION** (20%): Is the price justified by described contents?
- **SCANNABILITY** (15%): Can a skimmer get the key points in 10 seconds?

The composite is the weighted average. Target: 7.5+

## Rules

1. **ONE change per experiment** — Isolate variables. Never change two things at once.
2. **Name experiments descriptively** — e.g., `hook_v2_outcome_first`, `short_desc_18months`, `pricing_bestfor_lines`
3. **Revert failures** — If score drops, restore `listing.md` before trying something else.
4. **Don't touch prepare.py** — The scoring function is frozen.
5. **Don't modify program.md** — These instructions are fixed.
6. **Log everything** — results.tsv is your experiment journal.
7. **Never add forbidden words** — Check before writing. Auto-rejection wastes an API call.

## Getting Started

```bash
# 1. Run baseline
python3.11 prepare.py --baseline

# 2. Start experimenting (modify listing.md, then run)
python3.11 prepare.py --id hook_v2_outcome_first

# 3. Check progress
python3.11 prepare.py --best

# 4. Run N iterations in a loop
bash run.sh 20
```

## Example Experiments to Try

1. **Hook rewrite**: Replace "Most developers treat prompting like it's guesswork" with a more specific failure scenario ("You're three days into debugging a Claude workflow that worked fine last week")
2. **Short description outcome-first**: Lead with "Stop debugging prompts you don't understand" before the contents
3. **Credibility detail**: Add "18 months" or "434 sources" to the opening section where it earns the most trust
4. **Tier naming**: Rename "Starter/Professional/Team" to names that speak to outcomes
5. **"What makes this different" specificity**: Change "Every pattern is from production use" to name a specific pattern and what it solved
6. **Guarantee strengthening**: Make the refund guarantee sound more confident ("If you read it and your prompts don't change, I want to know why")
7. **Urgency addition**: Add a specific "why now" — model updates breaking prompts, new release, or a concrete outcome they're missing today
8. **Opening problem specificity**: Replace the generic "copy examples from Reddit" with a more vivid specific failure that developers recognize
