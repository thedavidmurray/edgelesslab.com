# Prompt Testing Framework

A systematic toolkit for evaluating and testing LLM prompts. Built for teams who treat prompts as production code.

**Product**: Tier 2 — Edgeless Labs LLC
**License**: MIT

---

## The Problem

Prompts break silently. You change a prompt, deploy it, and three days later someone notices the outputs degraded. No test caught it because no test existed.

This framework gives you:
- A CLI for running prompt tests against real APIs
- Pre-built test suites for accuracy, consistency, edge cases, format compliance, and safety
- An LLM-as-judge evaluator for subjective quality criteria
- Templates for A/B testing, regression testing, and benchmarking
- CI/CD integration patterns

---

## Quick Start

### Prerequisites

```bash
# Python 3.9+
pip install pyyaml anthropic openai requests

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."
# or
export OPENAI_API_KEY="sk-..."
```

### Run your first test

```bash
# Run a test suite
./framework/prompt-test.sh run test-suites/accuracy/test_spec.yaml

# Run with verbose output
./framework/prompt-test.sh run test-suites/accuracy/test_spec.yaml --verbose

# Run all suites
./framework/prompt-test.sh run-all test-suites/

# Evaluate results with LLM-as-judge
python framework/evaluate.py results/run-2026-03-12.json

# Generate HTML report
python framework/evaluate.py results/run-2026-03-12.json --report reports/output.html
```

---

## Test Spec Format

Tests are defined in YAML. A test spec looks like:

```yaml
name: "Code Generation Accuracy"
prompt_template: "prompts/code-gen.md"
model: "claude-3-5-haiku-20241022"
tests:
  - name: "fibonacci"
    input: "Write a fibonacci function in Python"
    assertions:
      - type: contains
        value: "def fibonacci"
      - type: llm_judge
        criteria: "Function correctly implements fibonacci sequence"
        threshold: 0.8
  - name: "empty input"
    input: ""
    assertions:
      - type: not_empty
      - type: contains
        value: "please provide"
        case_insensitive: true
```

See `framework/config.example.yaml` for the full schema.

---

## Directory Layout

```
prompt-testing-framework/
├── framework/
│   ├── prompt-test.sh        # CLI entry point
│   ├── evaluate.py           # LLM-as-judge evaluator
│   └── config.example.yaml  # Full config reference
│
├── test-suites/
│   ├── accuracy/             # Output matches known-good examples
│   ├── consistency/          # Stable across multiple runs
│   ├── edge-cases/           # Boundary conditions and adversarial inputs
│   ├── format-compliance/    # JSON schema, markdown structure
│   └── safety/               # Prompt injection resistance
│
├── templates/
│   ├── a-b-test.yaml         # Compare two prompt variants
│   ├── regression-test.yaml  # Catch regressions after changes
│   └── benchmark.yaml        # Measure performance metrics
│
├── guide/
│   ├── 01-why-test-prompts.md
│   ├── 02-test-anatomy.md
│   ├── 03-evaluation-methods.md
│   ├── 04-ci-integration.md
│   └── 05-metrics.md
│
└── reports/
    └── report-template.html
```

---

## Assertion Types

| Type | Description | Example |
|------|-------------|---------|
| `contains` | Output contains substring | `value: "def fibonacci"` |
| `not_contains` | Output does not contain substring | `value: "error"` |
| `exact_match` | Output equals expected exactly | `value: "yes"` |
| `fuzzy_match` | Output similar to expected (threshold 0-1) | `value: "yes", threshold: 0.9` |
| `regex` | Output matches regex pattern | `pattern: "\\d{3}-\\d{4}"` |
| `json_valid` | Output is valid JSON | — |
| `json_schema` | Output matches JSON schema | `schema: {...}` |
| `not_empty` | Output is not empty | — |
| `max_length` | Output under character limit | `value: 500` |
| `min_length` | Output over character minimum | `value: 10` |
| `llm_judge` | LLM evaluates quality | `criteria: "..."`, `threshold: 0.8` |
| `rubric` | Scored rubric evaluation | `rubric: [...]` |

---

## Supported Models

Set `model` in your test spec or via `--model` flag:

- `claude-3-5-haiku-20241022` (default, fastest)
- `claude-3-5-sonnet-20241022`
- `claude-opus-4-5`
- `gpt-4o-mini`
- `gpt-4o`

The evaluator (`evaluate.py`) uses a separate judge model, configurable via `--judge-model`.

---

## CI/CD Integration

See `guide/04-ci-integration.md` for full examples. Quick reference:

```yaml
# GitHub Actions
- name: Run prompt tests
  run: |
    ./framework/prompt-test.sh run-all test-suites/ --fail-threshold 0.9
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

Exit codes: `0` = all tests pass, `1` = failures below threshold, `2` = configuration error.

---

## License

MIT — Copyright 2026 Edgeless Labs LLC
