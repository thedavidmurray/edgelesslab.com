# Root Draft Review — 2026-09-28

Review of five quarantined drafts moved from root inbox by ops-audit task t_d8247c50.
Three review candidates, two HOLD confirmations. One previously disposed (hermes-heartbeat-forgery → superseded, already published).

Policy: `/Users/djm/claude-projects/docs/projects/blog-pipeline/decisions.md`

## Verdicts

| Draft | Disposition | Humanizer | Source Check | Privacy |
|---|---|---|---|---|
| the-80-turn-loop-that-taught-us-silence | **AUTO** | CLEAN | Personal experience, no external sources | Agent names only (Scribe, Beau) |
| the-loop-is-not-the-guarantee | **AUTO** | CLEAN | YouTube URLs + Notion API claims — spot-check before publish | No personal info |
| the-skill-is-the-new-prompt | **AUTO** | CLEAN | YouTube URLs + existing blog links — verify before publish | Named creators in positive/neutral context |
| kimi-k3-cheap-demo-premium-infrastructure | **HOLD** | n/a | Pricing/benchmark claims unverified | Named companies (Moonshot, Anthropic, Fable, Opus, OpenAI) |
| the-7-second-duplicate | **HOLD** | n/a | Trading infrastructure details | Trading program specifics |

---

## the-80-turn-loop-that-taught-us-silence → AUTO

**Rationale:** Personal postmortem, no reputational risk. No external sources to verify. No private infra exposed. Agent names (Scribe, Beau) are internal swarm identities, not people.

**Humanizer CLEAN evidence:**
- First-person voice throughout ("Two of my agents", "me — typed something new")
- No AI vocabulary patterns (no "pivotal", "landscape", "testament", "underscore")
- No filler phrases ("In order to", "At its core", "I hope this helps")
- No em dash overuse — uses periods and commas
- Sentence rhythm varies (short punchy sentences mixed with longer ones)
- Has opinion and personality: "The bots weren't stupid. They were too obedient."
- No knowledge-cutoff disclaimers
- Title case in headings: sentence case — correct

**Source check:** All content is personal experience. No external URLs, no citations needed.

**Privacy:** No private infra details, no credentials, no internal system names beyond agent identities.

**Edits needed:** None. Ready for verifier/publisher card.

---

## the-loop-is-not-the-guarantee → AUTO

**Rationale:** Analytical post about YouTube tutorials and automation patterns. References external content (YouTube videos, Notion API docs). No reputational risk — tutorials are described neutrally, not criticized. No trading/financial claims.

**Humanizer CLEAN evidence:**
- Personal voice: "My YouTube pipeline flagged six videos", "It wasn't one"
- No AI vocabulary patterns (no "additionally", "delve", "showcase", "tapestry")
- No filler/hedging phrases
- Conversational tone with specific opinions ("The clusterer only grouped it because of the word 'automation'")
- Varies sentence structure; some short punchy sentences
- Has opinions and self-deprecating humor ("the lesson still holds")
- No knowledge-cutoff disclaimers

**Source check — verify before publish:**
- YouTube URLs (6 videos): need spot-check that links are still valid and match described content
- Notion API version claim (`2025-09-03`, `database_id` → `data_source_id`): verify against current Notion changelog
- IndyDevDan series attribution: verify the videos actually belong to IndyDevDan
- Link to `six-dispatchers-where-one-is-law` blog post: verify it exists at edgelesslab.com

**Privacy:** No personal info, no private infra.

**Edits needed:** None. But source URLs should be spot-checked before the verifier/publisher card proceeds.

---

## the-skill-is-the-new-prompt → AUTO

**Rationale:** Analytical post about agent skills industry trend. References specific creators (Matt Pocock, Nate B Jones, Cole Medin) and companies (tldraw, Vercel) in positive/neutral context. No criticism of named people. No trading/financial claims. No pricing changes.

**Humanizer CLEAN evidence:**
- Personal voice throughout: "This isn't abstract for us", "We run a skill library in the triple digits"
- Has strong opinions: "Pocock's whole talk is a quality argument", "Eve is, frankly, our swarm productized"
- No AI vocabulary patterns (no "pivotal", "landscape", "testament", "underscore", "delve")
- No filler phrases, no knowledge-cutoff disclaimers
- Varies sentence structure with short punchy sentences ("Prompts are conversations. Skills are infrastructure.")
- Has personality and edge: "The skill matters less than the environment around it"
- Title case in headings: sentence case — correct

**Source check — verify before publish:**
- YouTube URLs (4 videos): verify links valid and match described content
- Links to existing blog posts (SkillOpt, Hermes Curator, etc.): verify they exist at edgelesslab.com
- Matt Pocock video title/URL: verify "Building Great Agent Skills: The Missing Manual" is correct
- Vercel Eve video: verify URL and description accuracy

**Privacy:** Named creators in positive/neutral context. No private infra details.

**Edits needed:** None. Source URLs should be spot-checked before verifier/publisher card proceeds.

---

## kimi-k3-cheap-demo-premium-infrastructure → HOLD (confirmed)

**Rationale:** Contains specific pricing claims ($15/M output, $3/M input), benchmark scores (64.1/70 vs Opus 4.8's 64.3/70), failure rates (36% adversarial), and named company comparisons (Kimi K3 vs Fable 5 vs Opus vs GPT 5.6). Policy category: "pricing/product-page changes" and "fabricated numbers." These claims need independent verification before any publication.

**Specific unverified claims:**
- "$1 cinematic websites" — demo economics, not independently verifiable
- "$15/M output tokens" — pricing may have changed since draft date (2026-08-07)
- "64.1/70 against Opus 4.8's 64.3/70" — benchmark scores need current source
- "36% failure rate on adversarial tasks" — needs source citation
- "40% cheaper than GPT 5.6, 70% cheaper than Fable" — pricing comparisons need verification
- "Sign-ups are throttled during soft launch" — may be stale

**Privacy:** Named companies (Moonshot AI, Anthropic, Fable, Opus, OpenAI) — reputational risk if claims are inaccurate.

**Action:** Stays in drafts/hold/. Enter weekly digest. Do not promote to content/blog.

---

## the-7-second-duplicate → HOLD (confirmed)

**Rationale:** Contains trading-program performance details — equity calculation, COT scanner, ORB strategy, trading alignment program. Policy category: "trading/financial performance claims." Even though this is a kanban/swarm postmortem, it references trading infrastructure and financial calculations that could be reputational if inaccurate.

**Specific concerns:**
- "equity calculation was double-counting" — describes trading system bug
- "win-rate display was replaced with expectancy" — trading metric
- "COT scanner" — commodity trading scanner
- "ORB tournament ran seven variants" — trading strategy variants
- "executions" and "gate executions on expectancy" — trading infrastructure

**Privacy:** Trading strategy details, internal system references.

**Action:** Stays in drafts/hold/. Enter weekly digest. Do not promote to content/blog.

---

## Verification

- No draft file exists in `content/blog/` — confirmed none promoted
- `drafts/review/` contains 3 files — confirmed
- `drafts/hold/` contains 2 files — confirmed
- `drafts/superseded/hermes-heartbeat-forgery.md` — already published (commit 629b45cd0), no action needed
- All verdicts cite policy in decisions.md

## Next Steps

1. AUTO items (3) → separate verifier/publisher card for source URL spot-checks, then publish
2. HOLD items (2) → weekly digest, no publish action
3. Source URL verification for AUTO items is a prerequisite for the publisher card
