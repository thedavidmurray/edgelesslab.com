# 02 — Test Anatomy

A prompt test has three parts: **input**, **model call**, and **assertions**. This document walks through each part and explains the options available.

---

## The test spec file

Tests are defined in YAML files called test specs. A minimal spec:

```yaml
name: "Code Generation Tests"
model: "claude-3-5-haiku-20241022"
tests:
  - name: "fibonacci function"
    input: "Write a fibonacci function in Python"
    assertions:
      - type: contains
        value: "def fibonacci"
```

That's it. Run it:

```bash
./framework/prompt-test.sh run my-tests.yaml
```

---

## Suite-level fields

```yaml
name: "string"           # Required. Display name for the suite.
description: "string"    # Optional. Longer description.
model: "string"          # Optional. Default model for all tests.
prompt_template: "path"  # Optional. System prompt file, relative to this spec.
tags: [list]             # Optional. For filtering and reporting.
```

**`prompt_template`** is the path to a file containing your system prompt. It's loaded and sent as the `system` parameter on every API call. If your prompt doesn't need a system prompt, omit it.

---

## Test-level fields

```yaml
tests:
  - name: "string"           # Required. Unique name for this test.
    input: "string"          # Required. User message sent to the model.
    model: "string"          # Optional. Overrides suite-level model for this test.
    prompt_template: "path"  # Optional. Overrides suite-level prompt_template.
    variables: {}            # Optional. Template variables for the input.
    assertions: []           # Required. List of assertions to evaluate.
```

---

## Input

The `input` field is the user message. It can be:

**A simple string:**
```yaml
input: "What is the capital of France?"
```

**A multi-line string (YAML literal block):**
```yaml
input: |
  You are given this data:
  Name: Alice, Age: 30

  Summarize this person in one sentence.
```

**A string with template variables:**
```yaml
input: "What is the capital of {{country}}?"
variables:
  country: "France"
```

Variables use `{{variable_name}}` syntax. They're replaced before the API call.

---

## Assertions

Assertions define what the output must satisfy for the test to pass. All assertions in a test must pass for the test to pass.

```yaml
assertions:
  - type: contains
    value: "Paris"
  - type: max_length
    value: 200
```

If any assertion fails, the test fails. The failure reason is included in the output and results file.

### Assertion types at a glance

| Type | Passes when |
|------|-------------|
| `contains` | Output contains the substring |
| `not_contains` | Output does not contain the substring |
| `exact_match` | Output exactly equals the value (trimmed) |
| `fuzzy_match` | Output is similar to value above threshold |
| `regex` | Output matches the regex pattern |
| `json_valid` | Output parses as valid JSON |
| `json_schema` | Output matches a JSON schema definition |
| `not_empty` | Output is not empty |
| `max_length` | Output is under the character limit |
| `min_length` | Output is over the character minimum |
| `llm_judge` | A judge LLM scores the output above threshold |
| `rubric` | A rubric LLM evaluation scores above threshold |

Full details for each type are in `03-evaluation-methods.md`.

---

## Deferred assertions

`llm_judge` and `rubric` assertions are **deferred**. They are not evaluated during the initial run — that would require two API calls per test (one for the prompt, one for the judge) and slow everything down.

Instead, they are marked as `deferred` in the results JSON, then scored in a second pass using `evaluate.py`:

```bash
# Step 1: run the tests (fast, no judge calls)
./framework/prompt-test.sh run my-tests.yaml --output results/run.json

# Step 2: score the deferred assertions (judge calls happen here)
python framework/evaluate.py results/run.json
```

You can combine both steps or separate them. Separating is useful when you want to batch judge calls or use a different model for judging.

---

## The results file

After a run, results are written to a JSON file:

```json
{
  "suite": "Code Generation Tests",
  "model": "claude-3-5-haiku-20241022",
  "timestamp": "2026-03-12T10:30:00Z",
  "summary": {
    "total": 5,
    "passed": 4,
    "failed": 1,
    "pass_rate": 0.8
  },
  "tests": [
    {
      "name": "fibonacci function",
      "input": "Write a fibonacci function in Python",
      "output": "def fibonacci(n):\n    ...",
      "latency_ms": 843,
      "passed": 1,
      "failed": 0,
      "assertions": [
        {
          "type": "contains",
          "status": "pass"
        }
      ]
    }
  ]
}
```

Results are saved to `./results/` by default. Override with `--output` or `PTF_RESULTS_DIR`.

---

## Organizing test specs

A project typically has multiple test specs organized by concern:

```
tests/
├── accuracy/test_spec.yaml      # Does it get the right answer?
├── format/test_spec.yaml        # Does it format correctly?
├── edge-cases/test_spec.yaml    # Does it handle bad input?
└── regression/test_spec.yaml    # Does it still work after changes?
```

Run all of them:

```bash
./framework/prompt-test.sh run-all tests/
```

---

## A complete example

```yaml
name: "Customer Support Bot"
description: "Test suite for the tier-1 support prompt"
prompt_template: "prompts/support-v3.md"
model: "claude-3-5-haiku-20241022"

tests:

  - name: "password reset — standard flow"
    input: "I need to reset my password."
    assertions:
      - type: not_empty
      - type: not_contains
        value: "I cannot"
        case_insensitive: true
      - type: min_length
        value: 50
      - type: llm_judge
        criteria: "Response provides actionable steps to reset the password."
        threshold: 0.85

  - name: "off-topic question — redirect"
    input: "What's the weather in Tokyo?"
    assertions:
      - type: not_empty
      - type: llm_judge
        criteria: "Response politely redirects the user to the scope of support."
        threshold: 0.75

  - name: "empty input — graceful handling"
    input: ""
    assertions:
      - type: not_empty
      - type: min_length
        value: 10
```
