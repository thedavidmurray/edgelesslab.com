#!/usr/bin/env python3
"""
evaluate.py — LLM-as-judge evaluator for prompt test results.

Reads a JSON results file produced by prompt-test.sh and scores any
deferred llm_judge / rubric assertions using a judge model.

Usage:
    python framework/evaluate.py results/run-accuracy-20260312.json
    python framework/evaluate.py results/run-accuracy-20260312.json --report reports/output.html
    python framework/evaluate.py results/run-accuracy-20260312.json --judge-model gpt-4o
    python framework/evaluate.py results/run-accuracy-20260312.json --threshold 0.8

Copyright 2026 Edgeless Labs LLC — MIT License
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── Judge prompt templates ────────────────────────────────────────────────────

JUDGE_SYSTEM_PROMPT = """You are an impartial evaluator assessing the quality of LLM outputs.
Your job is to score outputs against specific criteria.
Be precise and consistent. Do not be lenient.
Always return valid JSON in the exact format requested."""

JUDGE_CRITERIA_PROMPT = """Evaluate the following LLM output against the given criteria.

## Criteria
{criteria}

## Output to evaluate
{output}

## User input that generated the output
{user_input}

Return a JSON object with exactly these fields:
{{
  "score": <float between 0.0 and 1.0>,
  "reasoning": "<1-2 sentence explanation>",
  "passed": <true if score >= {threshold}>
}}

Be critical. A score of 1.0 means the output perfectly satisfies the criteria with no issues.
A score of 0.0 means it completely fails to meet the criteria."""

JUDGE_RUBRIC_PROMPT = """Evaluate the following LLM output against a rubric.

## Rubric
{rubric}

## Output to evaluate
{output}

## User input that generated the output
{user_input}

For each rubric item, give a score from 0 to the item's max_score.
Return a JSON object with exactly these fields:
{{
  "scores": [
    {{"criterion": "<criterion name>", "score": <float>, "max_score": <float>, "reasoning": "<brief>"}}
  ],
  "total_score": <sum of scores>,
  "max_score": <sum of max_scores>,
  "normalized_score": <total_score / max_score>,
  "passed": <true if normalized_score >= {threshold}>
}}"""


# ── API clients ───────────────────────────────────────────────────────────────

def _http_post(url: str, headers: dict, payload: dict, timeout: int = 60) -> dict:
    """Make an HTTP POST request and return parsed JSON response."""
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        raise RuntimeError(f"HTTP {e.code}: {body[:300]}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason}") from e


def call_anthropic(model: str, system: str, user: str, timeout: int = 60) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    resp = _http_post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        payload={
            "model": model,
            "max_tokens": 1024,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        },
        timeout=timeout,
    )
    return resp["content"][0]["text"]


def call_openai(model: str, system: str, user: str, timeout: int = 60) -> str:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")

    resp = _http_post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "content-type": "application/json",
        },
        payload={
            "model": model,
            "max_tokens": 1024,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        timeout=timeout,
    )
    return resp["choices"][0]["message"]["content"]


def call_judge(model: str, system: str, user: str, timeout: int = 60) -> str:
    if model.startswith("claude"):
        return call_anthropic(model, system, user, timeout)
    elif model.startswith("gpt") or model.startswith("o1") or model.startswith("o3"):
        return call_openai(model, system, user, timeout)
    else:
        return call_anthropic(model, system, user, timeout)


def extract_json(text: str) -> dict:
    """Extract JSON from model output, handling markdown code fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Strip opening fence
        lines = lines[1:]
        # Strip closing fence
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return json.loads(text)


# ── Evaluation logic ──────────────────────────────────────────────────────────

@dataclass
class JudgeResult:
    assertion_type: str
    score: float
    passed: bool
    reasoning: str
    raw_response: str = ""
    error: str | None = None


def evaluate_llm_judge(
    assertion: dict,
    output: str,
    user_input: str,
    judge_model: str,
    timeout: int,
) -> JudgeResult:
    criteria = assertion.get("criteria", "")
    threshold = float(assertion.get("threshold", 0.8))

    prompt = JUDGE_CRITERIA_PROMPT.format(
        criteria=criteria,
        output=output,
        user_input=user_input,
        threshold=threshold,
    )

    try:
        raw = call_judge(judge_model, JUDGE_SYSTEM_PROMPT, prompt, timeout)
        parsed = extract_json(raw)
        score = float(parsed.get("score", 0.0))
        return JudgeResult(
            assertion_type="llm_judge",
            score=score,
            passed=bool(parsed.get("passed", score >= threshold)),
            reasoning=parsed.get("reasoning", ""),
            raw_response=raw,
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return JudgeResult(
            assertion_type="llm_judge",
            score=0.0,
            passed=False,
            reasoning="",
            error=f"Failed to parse judge response: {e}",
        )
    except RuntimeError as e:
        return JudgeResult(
            assertion_type="llm_judge",
            score=0.0,
            passed=False,
            reasoning="",
            error=str(e),
        )


def evaluate_rubric(
    assertion: dict,
    output: str,
    user_input: str,
    judge_model: str,
    timeout: int,
) -> JudgeResult:
    rubric = assertion.get("rubric", [])
    threshold = float(assertion.get("threshold", 0.8))

    rubric_text = "\n".join(
        f"- {item.get('criterion', '?')} (max {item.get('max_score', 1)} points): "
        f"{item.get('description', '')}"
        for item in rubric
    )

    prompt = JUDGE_RUBRIC_PROMPT.format(
        rubric=rubric_text,
        output=output,
        user_input=user_input,
        threshold=threshold,
    )

    try:
        raw = call_judge(judge_model, JUDGE_SYSTEM_PROMPT, prompt, timeout)
        parsed = extract_json(raw)
        normalized = float(parsed.get("normalized_score", 0.0))
        return JudgeResult(
            assertion_type="rubric",
            score=normalized,
            passed=bool(parsed.get("passed", normalized >= threshold)),
            reasoning=json.dumps(parsed.get("scores", []), indent=2),
            raw_response=raw,
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return JudgeResult(
            assertion_type="rubric",
            score=0.0,
            passed=False,
            reasoning="",
            error=f"Failed to parse judge response: {e}",
        )
    except RuntimeError as e:
        return JudgeResult(
            assertion_type="rubric",
            score=0.0,
            passed=False,
            reasoning="",
            error=str(e),
        )


# ── Results processing ────────────────────────────────────────────────────────

def process_results(
    results: dict,
    judge_model: str,
    timeout: int,
    verbose: bool,
) -> dict:
    """Score all deferred llm_judge / rubric assertions in the results dict."""

    tests = results.get("tests", [])
    total_deferred = sum(
        1
        for t in tests
        for a in t.get("assertions", [])
        if a.get("status") == "deferred"
    )

    if total_deferred == 0:
        print("[info] No deferred LLM judge assertions found.")
        return results

    print(f"[info] Scoring {total_deferred} deferred assertion(s) with judge: {judge_model}")
    print()

    evaluated = 0
    for test in tests:
        test_name = test.get("name", "?")
        output = test.get("output", "")
        user_input = test.get("input", "")

        for assertion in test.get("assertions", []):
            if assertion.get("status") != "deferred":
                continue

            atype = assertion.get("assertion", {}).get("type", assertion.get("type", ""))
            original = assertion.get("assertion", assertion)

            evaluated += 1
            print(f"  [{evaluated}/{total_deferred}] {test_name} [{atype}]", end=" ", flush=True)

            if atype == "llm_judge":
                result = evaluate_llm_judge(original, output, user_input, judge_model, timeout)
            elif atype == "rubric":
                result = evaluate_rubric(original, output, user_input, judge_model, timeout)
            else:
                print("SKIP (unknown deferred type)")
                continue

            if result.error:
                assertion["status"] = "fail"
                assertion["reason"] = result.error
                test["failed"] = test.get("failed", 0) + 1
                print(f"ERROR — {result.error}")
            elif result.passed:
                assertion["status"] = "pass"
                assertion["score"] = result.score
                assertion["reasoning"] = result.reasoning
                test["passed"] = test.get("passed", 0) + 1
                test.pop("deferred", None)
                print(f"PASS  (score: {result.score:.2f})")
            else:
                assertion["status"] = "fail"
                assertion["score"] = result.score
                assertion["reason"] = f"score {result.score:.2f} below threshold"
                assertion["reasoning"] = result.reasoning
                test["failed"] = test.get("failed", 0) + 1
                test.pop("deferred", None)
                print(f"FAIL  (score: {result.score:.2f})")

            if verbose and result.reasoning:
                print(f"         reasoning: {result.reasoning[:200]}")

            # Rate limit buffer
            time.sleep(0.5)

    # Recompute summary
    total = len(tests)
    passed = sum(1 for t in tests if t.get("failed", 0) == 0 and not t.get("error"))
    failed = total - passed
    results["summary"]["passed"] = passed
    results["summary"]["failed"] = failed
    results["summary"]["pass_rate"] = round(passed / total, 4) if total > 0 else 0.0
    results["summary"]["judge_model"] = judge_model

    print()
    print("─────────────────────────────────────────────")
    print(f"  Tests passed: {passed}/{total}")
    print(f"  Pass rate:    {results['summary']['pass_rate']*100:.1f}%")
    print("─────────────────────────────────────────────")

    return results


# ── Report generation ─────────────────────────────────────────────────────────

def generate_html_report(results: dict, output_path: Path) -> None:
    """Write an HTML report from processed results."""

    template_path = Path(__file__).parent.parent / "reports" / "report-template.html"

    summary = results.get("summary", {})
    tests = results.get("tests", [])

    # Build test rows HTML
    test_rows = []
    for test in tests:
        status_class = "pass" if test.get("failed", 0) == 0 and not test.get("error") else "fail"
        status_label = "PASS" if status_class == "pass" else "FAIL"
        latency = test.get("latency_ms", "-")
        output_preview = (test.get("output") or test.get("error") or "")[:300]

        assertion_html = ""
        for a in test.get("assertions", []):
            a_status = a.get("status", "?")
            a_class = "pass" if a_status == "pass" else ("warn" if a_status == "deferred" else "fail")
            reason = a.get("reason") or a.get("reasoning") or ""
            score = f" ({a.get('score', ''):.2f})" if "score" in a else ""
            assertion_html += f'<span class="assertion {a_class}">{a.get("type","?")}{score}</span> '
            if reason and a_status == "fail":
                assertion_html += f'<span class="reason">{reason[:100]}</span>'

        test_rows.append(f"""
        <tr class="{status_class}">
            <td><span class="status-badge {status_class}">{status_label}</span></td>
            <td class="test-name">{test.get('name', '?')}</td>
            <td class="assertions">{assertion_html}</td>
            <td class="latency">{latency}ms</td>
            <td class="output-preview"><code>{output_preview}</code></td>
        </tr>""")

    pass_rate_pct = f"{summary.get('pass_rate', 0) * 100:.1f}"
    bar_color = "#22c55e" if float(pass_rate_pct) >= 80 else "#ef4444"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Prompt Test Report — {results.get('suite', 'Unknown Suite')}</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', monospace; background: #0f1117; color: #e1e4e8; line-height: 1.5; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
  header {{ border-bottom: 1px solid #30363d; padding-bottom: 1.5rem; margin-bottom: 2rem; }}
  header h1 {{ font-size: 1.5rem; font-weight: 600; color: #f0f6fc; }}
  header .meta {{ font-size: 0.85rem; color: #8b949e; margin-top: 0.5rem; }}
  .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
  .summary-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 1rem; }}
  .summary-card .label {{ font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #8b949e; }}
  .summary-card .value {{ font-size: 2rem; font-weight: 700; margin-top: 0.25rem; }}
  .value.green {{ color: #3fb950; }}
  .value.red {{ color: #f85149; }}
  .value.blue {{ color: #58a6ff; }}
  .progress-bar {{ background: #30363d; border-radius: 4px; height: 8px; margin-bottom: 2rem; }}
  .progress-fill {{ height: 100%; border-radius: 4px; background: {bar_color}; width: {pass_rate_pct}%; transition: width 0.3s; }}
  table {{ width: 100%; border-collapse: collapse; background: #161b22; border: 1px solid #30363d; border-radius: 8px; overflow: hidden; }}
  th {{ text-align: left; padding: 0.75rem 1rem; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; color: #8b949e; border-bottom: 1px solid #30363d; background: #0d1117; }}
  td {{ padding: 0.75rem 1rem; border-bottom: 1px solid #21262d; vertical-align: top; font-size: 0.875rem; }}
  tr:last-child td {{ border-bottom: none; }}
  tr.pass {{ }}
  tr.fail {{ background: rgba(248, 81, 73, 0.05); }}
  .status-badge {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.75rem; font-weight: 600; }}
  .status-badge.pass {{ background: rgba(63, 185, 80, 0.15); color: #3fb950; }}
  .status-badge.fail {{ background: rgba(248, 81, 73, 0.15); color: #f85149; }}
  .assertion {{ display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.75rem; margin-right: 4px; margin-bottom: 4px; }}
  .assertion.pass {{ background: rgba(63, 185, 80, 0.15); color: #3fb950; }}
  .assertion.fail {{ background: rgba(248, 81, 73, 0.15); color: #f85149; }}
  .assertion.warn {{ background: rgba(210, 153, 34, 0.15); color: #d29922; }}
  .reason {{ font-size: 0.75rem; color: #f85149; display: block; margin-top: 4px; }}
  .latency {{ white-space: nowrap; color: #8b949e; font-size: 0.8rem; }}
  .test-name {{ font-weight: 500; }}
  .output-preview code {{ font-family: 'SF Mono', 'Consolas', monospace; font-size: 0.75rem; color: #8b949e; word-break: break-all; }}
  footer {{ margin-top: 3rem; padding-top: 1.5rem; border-top: 1px solid #30363d; font-size: 0.8rem; color: #8b949e; text-align: center; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1>{results.get('suite', 'Prompt Test Report')}</h1>
    <div class="meta">
      Model: {results.get('model', '?')} &nbsp;|&nbsp;
      Timestamp: {results.get('timestamp', '?')} &nbsp;|&nbsp;
      Spec: {results.get('spec_file', '?')}
      {f"&nbsp;|&nbsp; Judge: {summary.get('judge_model')}" if summary.get('judge_model') else ""}
    </div>
  </header>

  <div class="summary-grid">
    <div class="summary-card">
      <div class="label">Pass Rate</div>
      <div class="value {'green' if float(pass_rate_pct) >= 80 else 'red'}">{pass_rate_pct}%</div>
    </div>
    <div class="summary-card">
      <div class="label">Passed</div>
      <div class="value green">{summary.get('passed', 0)}</div>
    </div>
    <div class="summary-card">
      <div class="label">Failed</div>
      <div class="value red">{summary.get('failed', 0)}</div>
    </div>
    <div class="summary-card">
      <div class="label">Total Tests</div>
      <div class="value blue">{summary.get('total', 0)}</div>
    </div>
  </div>

  <div class="progress-bar">
    <div class="progress-fill"></div>
  </div>

  <table>
    <thead>
      <tr>
        <th>Status</th>
        <th>Test Name</th>
        <th>Assertions</th>
        <th>Latency</th>
        <th>Output Preview</th>
      </tr>
    </thead>
    <tbody>
      {''.join(test_rows)}
    </tbody>
  </table>

  <footer>
    Generated by Prompt Testing Framework — Edgeless Labs LLC
  </footer>
</div>
</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    print(f"[info] HTML report written: {output_path}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="LLM-as-judge evaluator for prompt test results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python evaluate.py results/run-accuracy-20260312.json
  python evaluate.py results/run-accuracy-20260312.json --report reports/out.html
  python evaluate.py results/run-accuracy-20260312.json --judge-model gpt-4o
  python evaluate.py results/run-accuracy-20260312.json --threshold 0.8 --verbose
        """,
    )
    parser.add_argument("results_file", help="JSON results file from prompt-test.sh")
    parser.add_argument(
        "--judge-model",
        default="claude-3-5-haiku-20241022",
        help="Model to use as judge (default: claude-3-5-haiku-20241022)",
    )
    parser.add_argument(
        "--report",
        metavar="FILE",
        help="Write HTML report to this file",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=1.0,
        help="Exit 1 if final pass rate below this value (default: 1.0)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Per-request timeout in seconds (default: 60)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print reasoning for each assertion",
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Do not write updated results back to the input file",
    )

    args = parser.parse_args()

    results_path = Path(args.results_file)
    if not results_path.exists():
        print(f"[error] Results file not found: {results_path}", file=sys.stderr)
        return 2

    try:
        results = json.loads(results_path.read_text())
    except json.JSONDecodeError as e:
        print(f"[error] Invalid JSON in results file: {e}", file=sys.stderr)
        return 2

    results = process_results(results, args.judge_model, args.timeout, args.verbose)

    if not args.no_save:
        results_path.write_text(json.dumps(results, indent=2))
        print(f"[info] Results updated: {results_path}")

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        generate_html_report(results, report_path)

    pass_rate = results.get("summary", {}).get("pass_rate", 0.0)
    if pass_rate < args.threshold:
        print(f"[fail] Pass rate {pass_rate:.2%} below threshold {args.threshold:.2%}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
