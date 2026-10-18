# 05 — Metrics

What you measure determines what you improve. This document covers the metrics available in this framework, what they mean, and how to use them for decision-making.

---

## Pass rate

The primary metric. Percentage of tests that pass all assertions.

```
pass_rate = passed_tests / total_tests
```

**In the results JSON:**
```json
"summary": {
  "total": 20,
  "passed": 18,
  "failed": 2,
  "pass_rate": 0.9
}
```

**Interpretation:**
- `1.0` — all tests pass. This is your baseline when the prompt is working correctly.
- Below baseline after a change — you introduced a regression.
- Baseline measurement requires saving results before and after changes.

**Threshold setting.** Not all tests are equally important. Consider:
- Critical path tests (primary use case): threshold 1.0
- Edge case tests: threshold 0.8-0.9
- Quality rubrics: threshold 0.75
- Safety tests: threshold 1.0

Use `--fail-threshold` to set the CI failure threshold.

---

## Assertion pass rate

Drill down to individual assertion types to understand *where* failures concentrate.

The results JSON contains per-test, per-assertion status:

```json
"assertions": [
  {"type": "contains", "status": "pass"},
  {"type": "llm_judge", "status": "fail", "score": 0.62, "reason": "score 0.62 below threshold 0.8"}
]
```

**What patterns to look for:**
- If `llm_judge` assertions fail while `contains` assertions pass, your prompt is producing syntactically correct but semantically weak output.
- If `json_valid` fails consistently, your prompt is not reliably returning JSON.
- If `max_length` fails, your prompt is producing verbose output and may need instructions to be more concise.

---

## Latency

Each test records `latency_ms` — wall time from sending the request to receiving the response.

```json
{
  "name": "fibonacci function",
  "latency_ms": 843
}
```

**Latency is primarily a function of model and output length.** It's not directly controllable via prompt engineering, but it's useful for:

**Baseline tracking.** If latency increases significantly after a prompt change, the new prompt may be producing longer outputs. Longer outputs cost more.

**Model comparison.** When running A/B tests with different models, compare latency alongside quality.

**SLA planning.** If your application has a response time SLA, aggregate latency across test runs to estimate p50/p95.

To compute latency statistics from a results file:

```python
import json, statistics

with open("results/run.json") as f:
    data = json.load(f)

latencies = [t["latency_ms"] for t in data["tests"] if t.get("latency_ms")]
print(f"p50: {statistics.median(latencies):.0f}ms")
print(f"p95: {sorted(latencies)[int(len(latencies)*0.95)]:.0f}ms")
print(f"mean: {statistics.mean(latencies):.0f}ms")
```

---

## LLM judge scores

For tests with `llm_judge` or `rubric` assertions, individual scores are stored in results:

```json
{
  "type": "llm_judge",
  "status": "pass",
  "score": 0.87,
  "reasoning": "The function correctly implements fibonacci..."
}
```

**Using scores for A/B testing.** When comparing two prompt variants, compare average judge scores, not just pass rates. A variant that scores 0.95 vs 0.85 is better even if both pass the threshold.

**Rubric dimension breakdown.** Rubric assertions store per-criterion scores:

```json
{
  "type": "rubric",
  "status": "pass",
  "score": 0.83,
  "reasoning": "[{\"criterion\": \"Clarity\", \"score\": 2, \"max_score\": 2}, ...]"
}
```

Track which rubric dimensions degrade after changes to identify which aspect of quality was affected.

---

## Cost

The framework does not currently track token counts or cost automatically. To estimate:

**Input tokens** = system prompt tokens + user message tokens (roughly: characters / 4)
**Output tokens** = output characters / 4
**Cost** = (input_tokens × input_price) + (output_tokens × output_price)

For current Anthropic pricing: https://www.anthropic.com/pricing

Rough estimates per test run (2026 pricing):
- `claude-3-5-haiku`: ~$0.001-0.003 per test
- `claude-3-5-sonnet`: ~$0.01-0.03 per test
- LLM judge call (same models): same range again

A 20-test suite with haiku costs roughly $0.02-0.06. Running it in CI on every PR for a team doing 50 PRs/month: ~$1-3/month.

---

## Consistency score

Consistency is not a single metric — it's measured by running the same test multiple times and comparing outputs.

To measure consistency:
1. Run the same test spec N times.
2. Compare pass rates across runs.
3. Compare output similarity for the same tests across runs.

A high-variance prompt may pass 90% of tests on one run and 70% on the next. This is a signal that the prompt relies on lucky phrasing rather than reliable structure.

**Practical approach:** Run your regression test suite 3 times before declaring a prompt "stable." If pass rate varies by more than 5 points across runs, investigate.

---

## Tracking metrics over time

Save all results files with timestamps. Minimal tracking:

```
results/
├── run-accuracy-20260101-143022.json
├── run-accuracy-20260215-091504.json
├── run-accuracy-20260312-102233.json
```

To compare pass rates over time:

```python
import json
from pathlib import Path

for f in sorted(Path("results").glob("run-accuracy-*.json")):
    data = json.loads(f.read_text())
    s = data["summary"]
    print(f"{data['timestamp'][:10]}  pass_rate={s['pass_rate']:.1%}  ({s['passed']}/{s['total']})")
```

Output:
```
2026-01-01  pass_rate=100.0%  (18/18)
2026-02-15  pass_rate=88.9%   (16/18)   ← regression introduced
2026-03-12  pass_rate=100.0%  (18/18)   ← fixed
```

---

## Summary: what to track

| Metric | Frequency | Purpose |
|--------|-----------|---------|
| Pass rate | Every run | Catch regressions |
| Assertion failures by type | On failure | Diagnose root cause |
| Latency (p50/p95) | Weekly | Model performance baseline |
| LLM judge scores | Per A/B test | Quality comparison |
| Rubric dimension scores | Per A/B test | Identify which quality dimension changed |
| Pass rate trend | Monthly | Track prompt health over time |
