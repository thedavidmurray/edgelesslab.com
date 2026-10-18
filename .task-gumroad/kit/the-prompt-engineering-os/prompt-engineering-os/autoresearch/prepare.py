#!/usr/bin/env python3.11
"""
Listing Autoresearch — FROZEN evaluation harness.

DO NOT MODIFY THIS FILE during experiments. It:
1. Loads the current listing from listing.md
2. Scores it on 5 dimensions via LLM-as-judge (OpenRouter)
3. Hard-filters forbidden brand words (score = 0 if found)
4. Logs results to results.tsv with git-ratchet semantics

Usage:
    python3.11 prepare.py              # Run one evaluation
    python3.11 prepare.py --baseline   # Record baseline score
    python3.11 prepare.py --best       # Show best score so far
    python3.11 prepare.py --id <name>  # Run with custom experiment ID
"""

import os
import re
import sys
import json
import time
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path

AUTORESEARCH_DIR = Path(__file__).parent
LISTING_FILE = AUTORESEARCH_DIR / "listing.md"
RESULTS_FILE = AUTORESEARCH_DIR / "results.tsv"

# Load .env from project root
PROJECT_ROOT = AUTORESEARCH_DIR.parent.parent.parent
_env_path = PROJECT_ROOT / ".env"
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
if not OPENROUTER_API_KEY:
    print("ERROR: OPENROUTER_API_KEY not found in environment or .env")
    sys.exit(1)

# ─── Forbidden words (from brand-notes.md) ───────────────────────────────────

FORBIDDEN_WORDS = [
    "revolutionary",
    "game-changing",
    "next-level",
    "leverage",
    "robust",
    "comprehensive",
    "crucial",
    "transformative",
    "incredible",
    "amazing",
]


def check_forbidden(listing_text: str) -> list[str]:
    """Return list of forbidden words found in the listing (case-insensitive)."""
    text_lower = listing_text.lower()
    found = []
    for word in FORBIDDEN_WORDS:
        if word in text_lower:
            found.append(word)
    return found


# ─── LLM-as-Judge Scoring ────────────────────────────────────────────────────

JUDGE_PROMPT = """You are a conversion copywriting expert evaluating a product listing for a technical digital product.

Score this listing on 5 dimensions. Each dimension is scored 1-10.

DIMENSIONS:

1. CLARITY (1-10): Is the value proposition immediately clear from the first 3 sentences? Would a developer landing on this page in 5 seconds know exactly what they are buying and why it matters?

2. URGENCY (1-10): Does the listing create genuine desire to buy now rather than later? Are there specific reasons — concrete outcomes, scarcity, or a tight "why now" — that push toward immediate purchase?

3. CREDIBILITY (1-10): Does the listing feel trustworthy and specific? Are claims backed by numbers, production context, or specifics rather than adjectives? Does it avoid hype language?

4. VALUE_COMMUNICATION (1-10): Is the price ($29/$59/$99) clearly justified by the described contents? Can the reader immediately see what they get at each tier and why the upgrade is worth it?

5. SCANNABILITY (1-10): Can a skimmer extract the core offer, who it's for, and what's included in under 10 seconds? Is the structure helping or getting in the way?

Return ONLY a JSON object with these exact keys (no markdown, no explanation):
{{"clarity": N, "urgency": N, "credibility": N, "value_communication": N, "scannability": N, "notes": "1-2 sentences of the single most important improvement needed"}}

LISTING TO EVALUATE:
{listing}
"""

WEIGHTS = {
    "clarity": 0.25,
    "urgency": 0.20,
    "credibility": 0.20,
    "value_communication": 0.20,
    "scannability": 0.15,
}


def score_listing(listing_text: str) -> dict:
    """Score the listing using LLM-as-judge via OpenRouter. Returns scores dict."""
    import urllib.request

    truncated = listing_text[:6000]
    prompt = JUDGE_PROMPT.format(listing=truncated)

    payload = json.dumps({
        "model": "google/gemini-2.0-flash-001",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400,
        "temperature": 0,
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/edgeless-ai",
            "X-Title": "listing-autoresearch",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        text = data["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        print(f"Judge API call failed: {exc}")
        return _default_scores(f"API error: {exc}")

    # Parse JSON from response (tolerate markdown fences)
    match = re.search(r"\{[^}]+\}", text, re.DOTALL)
    if not match:
        print(f"Could not parse judge response: {text[:200]}")
        return _default_scores("parse error")

    try:
        scores = json.loads(match.group())
    except json.JSONDecodeError as exc:
        print(f"JSON decode error: {exc} — raw: {text[:200]}")
        return _default_scores("json decode error")

    # Validate and clamp each dimension
    for key in WEIGHTS:
        if key not in scores:
            scores[key] = 5
        scores[key] = max(1, min(10, int(scores[key])))

    scores["composite"] = round(
        sum(scores[k] * WEIGHTS[k] for k in WEIGHTS), 2
    )
    scores.setdefault("notes", "")
    return scores


def _default_scores(reason: str) -> dict:
    base = {k: 5 for k in WEIGHTS}
    base["composite"] = 5.0
    base["notes"] = reason
    return base


# ─── Experiment Runner ───────────────────────────────────────────────────────

def run_experiment(experiment_id: str = None) -> dict:
    """Load listing.md, check forbidden words, score, log, return scores."""
    if not LISTING_FILE.exists():
        print(f"ERROR: {LISTING_FILE} not found")
        sys.exit(1)

    listing_text = LISTING_FILE.read_text()

    if not experiment_id:
        experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"\n{'='*60}")
    print(f"  Experiment: {experiment_id}")
    print(f"  Listing: {len(listing_text)} chars")
    print(f"{'='*60}\n")

    # Hard filter: forbidden words
    found_forbidden = check_forbidden(listing_text)
    if found_forbidden:
        scores = _default_scores(f"FORBIDDEN WORDS: {', '.join(found_forbidden)}")
        scores["composite"] = 0.0
        scores["status"] = "REJECTED"
        for k in WEIGHTS:
            scores[k] = 0
        scores["experiment_id"] = experiment_id
        scores["timestamp"] = datetime.now(timezone.utc).isoformat()
        log_result(scores)
        print(f"  REJECTED — forbidden words found: {', '.join(found_forbidden)}")
        return scores

    start_time = time.time()
    scores = score_listing(listing_text)
    scores["elapsed"] = round(time.time() - start_time, 1)
    scores["experiment_id"] = experiment_id
    scores["timestamp"] = datetime.now(timezone.utc).isoformat()
    scores["status"] = "OK"

    log_result(scores)

    print(f"  Composite:          {scores['composite']}/10")
    print(f"  Clarity (25%):      {scores.get('clarity', '?')}/10")
    print(f"  Urgency (20%):      {scores.get('urgency', '?')}/10")
    print(f"  Credibility (20%):  {scores.get('credibility', '?')}/10")
    print(f"  Value comm. (20%):  {scores.get('value_communication', '?')}/10")
    print(f"  Scannability (15%): {scores.get('scannability', '?')}/10")
    print(f"  Time:               {scores['elapsed']}s")
    if scores.get("notes"):
        print(f"  Notes: {scores['notes']}")

    # Git commit to track this experiment
    _git_commit(experiment_id, scores["composite"])

    return scores


def _git_commit(experiment_id: str, composite: float):
    """Commit listing.md + results.tsv to track this experiment."""
    try:
        repo_root = PROJECT_ROOT
        subprocess.run(
            ["git", "add",
             str(LISTING_FILE.relative_to(repo_root)),
             str(RESULTS_FILE.relative_to(repo_root))],
            cwd=repo_root, capture_output=True, check=False,
        )
        subprocess.run(
            ["git", "commit", "-m",
             f"autoresearch: {experiment_id} score={composite}"],
            cwd=repo_root, capture_output=True, check=False,
        )
    except Exception:
        pass  # Git commit is best-effort


def log_result(scores: dict):
    """Append experiment result as a TSV line."""
    header = (
        "timestamp\texperiment_id\tclarity\turgency\tcredibility"
        "\tvalue_communication\tscannability\tcomposite\tstatus\tnotes"
    )

    if not RESULTS_FILE.exists():
        RESULTS_FILE.write_text(header + "\n")

    line = "\t".join([
        str(scores.get("timestamp", "?")),
        str(scores.get("experiment_id", "?")),
        str(scores.get("clarity", "?")),
        str(scores.get("urgency", "?")),
        str(scores.get("credibility", "?")),
        str(scores.get("value_communication", "?")),
        str(scores.get("scannability", "?")),
        str(scores.get("composite", "?")),
        str(scores.get("status", "OK")),
        str(scores.get("notes", "")).replace("\t", " ").replace("\n", " "),
    ])

    with open(RESULTS_FILE, "a") as f:
        f.write(line + "\n")


def show_best():
    """Print the best-scoring experiment from results.tsv."""
    if not RESULTS_FILE.exists():
        print("No results yet.")
        return

    lines = RESULTS_FILE.read_text().strip().split("\n")
    if len(lines) < 2:
        print("No results yet.")
        return

    best_score = -1.0
    best_parts = None
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) < 8:
            continue
        try:
            composite = float(parts[7])
            if composite > best_score:
                best_score = composite
                best_parts = parts
        except ValueError:
            continue

    if best_parts:
        print(f"\nBest experiment: {best_parts[1]}")
        print(f"  Composite:         {best_parts[7]}/10")
        print(f"  Clarity:           {best_parts[2]}")
        print(f"  Urgency:           {best_parts[3]}")
        print(f"  Credibility:       {best_parts[4]}")
        print(f"  Value comm.:       {best_parts[5]}")
        print(f"  Scannability:      {best_parts[6]}")
        if len(best_parts) > 9:
            print(f"  Notes: {best_parts[9]}")
    print(f"\nTotal experiments: {len(lines) - 1}")


# ─── Main ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Listing Autoresearch — Evaluation Harness"
    )
    parser.add_argument(
        "--baseline", action="store_true",
        help="Run and record as baseline experiment"
    )
    parser.add_argument(
        "--best", action="store_true",
        help="Show best score so far"
    )
    parser.add_argument(
        "--id", type=str, dest="experiment_id",
        help="Custom experiment ID (default: timestamp)"
    )
    args = parser.parse_args()

    if args.best:
        show_best()
    elif args.baseline:
        run_experiment("baseline")
    else:
        run_experiment(args.experiment_id)
