#!/usr/bin/env python3
"""
CLAUDE.md Template Autoresearch — FROZEN evaluation harness.

DO NOT MODIFY THIS FILE during experiments. It:
1. Loads a CLAUDE.md template from ../claude-md/
2. Scores it on 5 dimensions using LLM-as-judge (OpenRouter Gemini)
3. Logs results to results.tsv with hard-constraint checks
4. Prints composite score for the loop runner to act on

Usage:
    python3.11 prepare.py ../claude-md/solo-dev.md
    python3.11 prepare.py ../claude-md/solo-dev.md --id my-experiment
    python3.11 prepare.py --best
"""

import os
import sys
import json
import re
import time
import argparse
from datetime import datetime, timezone
from pathlib import Path

# ─── Paths ───────────────────────────────────────────────────────────────────

AUTORESEARCH_DIR = Path(__file__).parent
RESULTS_FILE = AUTORESEARCH_DIR / "results.tsv"
EVAL_TASKS_FILE = AUTORESEARCH_DIR / "eval_tasks.json"
PROJECT_ROOT = AUTORESEARCH_DIR.parent.parent.parent  # products/ -> obsidian-claude-setup/ -> products/ -> claude-projects/

# Load .env from project root
env_path = PROJECT_ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, val = line.partition("=")
            os.environ.setdefault(key.strip(), val.strip())

# ─── Hard Constraints ────────────────────────────────────────────────────────

REQUIRED_COMMANDS = ["obsidian read", "obsidian create", "obsidian search"]

# ─── Scoring Weights ─────────────────────────────────────────────────────────

WEIGHTS = {
    "task_accuracy": 0.30,
    "completeness": 0.25,
    "clarity": 0.20,
    "conciseness": 0.15,
    "persona_fit": 0.10,
}

# ─── Judge Prompt ────────────────────────────────────────────────────────────

JUDGE_PROMPT_TEMPLATE = """You are a CLAUDE.md template quality judge. Score the template below on 5 dimensions.

The template is for a "{persona}" persona using Claude Code with an Obsidian vault.

Representative tasks this persona would ask Claude to perform:
{tasks}

Score each dimension 1-10:

1. TASK_ACCURACY (30%): Would Claude correctly execute each of the 5 representative tasks above using ONLY the instructions in this template? Consider whether commands, schemas, and patterns are present and correct.

2. COMPLETENESS (25%): Are the critical Obsidian CLI commands well-covered? Does the template include enough vault structure and frontmatter schema detail for Claude to act without asking clarifying questions?

3. CLARITY (20%): Are the instructions unambiguous? Could a developer unfamiliar with Obsidian follow them correctly on first read?

4. CONCISENESS (15%): Is the template lean? No repetition, no filler text, no unnecessary examples? Ideally under 80 lines.

5. PERSONA_FIT (10%): Does the tone, vocabulary, folder names, frontmatter fields, and example commands clearly match the target persona ("{persona}")? Would a "{persona}" feel this was written for them?

Return ONLY a JSON object with these exact keys:
{{"task_accuracy": N, "completeness": N, "clarity": N, "conciseness": N, "persona_fit": N, "notes": "1-2 sentences of specific, actionable feedback"}}

TEMPLATE TO JUDGE:
{template_content}
"""


# ─── OpenRouter Client ───────────────────────────────────────────────────────

def call_openrouter(prompt: str, model: str = "google/gemini-2.0-flash-001") -> str:
    """Call OpenRouter API and return text response."""
    import urllib.request

    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set in environment or .env")

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 400,
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/obsidian-claude-setup",
        },
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())

    return data["choices"][0]["message"]["content"]


# ─── Hard Constraint Check ───────────────────────────────────────────────────

def check_hard_constraints(template_content: str) -> tuple[bool, list[str]]:
    """
    Return (passed, missing_commands).
    All REQUIRED_COMMANDS must appear in the template text.
    """
    missing = [cmd for cmd in REQUIRED_COMMANDS if cmd not in template_content]
    return (len(missing) == 0), missing


# ─── Scoring ─────────────────────────────────────────────────────────────────

def score_template(template_path: Path) -> dict:
    """Load a template, run hard checks, call LLM judge, return scores dict."""
    template_content = template_path.read_text()
    persona = template_path.stem  # e.g. "solo-dev"

    # Hard constraints first — fail fast, no LLM call needed
    passed, missing = check_hard_constraints(template_content)
    if not passed:
        print(f"  [FAIL] Hard constraints missing: {missing}")
        return {
            "task_accuracy": 0, "completeness": 0, "clarity": 0,
            "conciseness": 0, "persona_fit": 0,
            "composite": 0.0,
            "status": "HARD_FAIL",
            "notes": f"Missing required commands: {', '.join(missing)}",
        }

    # Load eval tasks for this persona
    eval_tasks = json.loads(EVAL_TASKS_FILE.read_text())
    tasks_for_persona = eval_tasks.get(persona, eval_tasks.get("solo-dev", []))
    tasks_str = "\n".join(f"  {i+1}. {t}" for i, t in enumerate(tasks_for_persona))

    prompt = JUDGE_PROMPT_TEMPLATE.format(
        persona=persona,
        tasks=tasks_str,
        template_content=template_content,
    )

    try:
        raw = call_openrouter(prompt)
    except Exception as exc:
        print(f"  [ERROR] LLM call failed: {exc}")
        return {
            "task_accuracy": 5, "completeness": 5, "clarity": 5,
            "conciseness": 5, "persona_fit": 5,
            "composite": 5.0,
            "status": "ERROR",
            "notes": f"LLM error: {exc}",
        }

    # Parse JSON from response
    match = re.search(r'\{[^{}]+\}', raw, re.DOTALL)
    if not match:
        print(f"  [WARN] Could not parse judge response: {raw[:200]}")
        return {
            "task_accuracy": 5, "completeness": 5, "clarity": 5,
            "conciseness": 5, "persona_fit": 5,
            "composite": 5.0,
            "status": "PARSE_ERROR",
            "notes": "Judge response was not valid JSON",
        }

    scores = json.loads(match.group())

    # Clamp all dimension scores to [1, 10]
    for key in WEIGHTS:
        scores[key] = max(1, min(10, int(scores.get(key, 5))))

    # Weighted composite
    composite = round(sum(scores[k] * WEIGHTS[k] for k in WEIGHTS), 2)
    scores["composite"] = composite
    scores["status"] = "OK"
    scores.setdefault("notes", "")

    return scores


# ─── Logging ─────────────────────────────────────────────────────────────────

HEADER = (
    "timestamp\ttemplate\texperiment_id\t"
    "task_accuracy\tcompleteness\tclarity\tconciseness\tpersona_fit\t"
    "composite\tstatus\tnotes"
)


def log_result(template_name: str, experiment_id: str, scores: dict):
    """Append one TSV row to results.tsv, writing header if the file is new."""
    if not RESULTS_FILE.exists():
        RESULTS_FILE.write_text(HEADER + "\n")

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    notes = str(scores.get("notes", "")).replace("\t", " ").replace("\n", " ")

    row = "\t".join([
        timestamp,
        template_name,
        experiment_id,
        str(scores.get("task_accuracy", "?")),
        str(scores.get("completeness", "?")),
        str(scores.get("clarity", "?")),
        str(scores.get("conciseness", "?")),
        str(scores.get("persona_fit", "?")),
        str(scores.get("composite", "?")),
        str(scores.get("status", "?")),
        notes,
    ])

    with open(RESULTS_FILE, "a") as f:
        f.write(row + "\n")


# ─── Best Score Display ───────────────────────────────────────────────────────

def show_best():
    """Print best composite score per template from results.tsv."""
    if not RESULTS_FILE.exists():
        print("No results yet.")
        return

    lines = RESULTS_FILE.read_text().strip().splitlines()
    if len(lines) < 2:
        print("No results yet.")
        return

    best: dict[str, tuple[float, str]] = {}  # template -> (composite, experiment_id)
    for line in lines[1:]:
        parts = line.split("\t")
        if len(parts) < 9:
            continue
        template = parts[1]
        try:
            composite = float(parts[8])
        except ValueError:
            continue
        if template not in best or composite > best[template][0]:
            best[template] = (composite, parts[2])

    print(f"\nBest scores across {len(best)} templates ({len(lines)-1} total experiments):")
    for template, (score, exp_id) in sorted(best.items()):
        print(f"  {template:<20} {score:.2f}/10  [{exp_id}]")


# ─── Main ─────────────────────────────────────────────────────────────────────

def run(template_path: Path, experiment_id: str = None) -> dict:
    persona = template_path.stem
    if not experiment_id:
        experiment_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    print(f"\n{'='*60}")
    print(f"  Template:   {persona}")
    print(f"  Experiment: {experiment_id}")
    print(f"{'='*60}")

    start = time.time()
    scores = score_template(template_path)
    elapsed = round(time.time() - start, 1)

    log_result(persona, experiment_id, scores)

    print(f"  Composite:    {scores['composite']:.2f}/10  [{scores['status']}]")
    print(f"  task_accuracy {scores.get('task_accuracy', '?')}/10  "
          f"completeness {scores.get('completeness', '?')}/10  "
          f"clarity {scores.get('clarity', '?')}/10")
    print(f"  conciseness   {scores.get('conciseness', '?')}/10  "
          f"persona_fit {scores.get('persona_fit', '?')}/10")
    print(f"  Time:         {elapsed}s")
    if scores.get("notes"):
        print(f"  Notes:        {scores['notes']}")

    return scores


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CLAUDE.md Template Autoresearch — Scoring"
    )
    parser.add_argument("template", nargs="?", type=Path,
                        help="Path to CLAUDE.md template (e.g. ../claude-md/solo-dev.md)")
    parser.add_argument("--id", type=str, help="Custom experiment ID")
    parser.add_argument("--best", action="store_true",
                        help="Show best score per template from results.tsv")
    args = parser.parse_args()

    if args.best:
        show_best()
        sys.exit(0)

    if not args.template:
        parser.print_help()
        sys.exit(1)

    template_path = Path(args.template).resolve()
    if not template_path.exists():
        print(f"Error: template not found: {template_path}")
        sys.exit(1)

    scores = run(template_path, args.id)
    # Exit code 0 on success, 1 on hard fail or error so the loop runner can detect
    if scores.get("status") in ("HARD_FAIL", "ERROR"):
        sys.exit(1)
