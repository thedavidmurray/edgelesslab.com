# 03 — Evaluation Methods

The right evaluation method depends on what you're testing. Some outputs have objectively correct answers. Others require judgment. This document covers each method, when to use it, and its limitations.

---

## Exact match

```yaml
- type: exact_match
  value: "yes"
```

The output must exactly equal `value` after trimming whitespace from both ends.

**Use when:** The output should be a single, specific string — a word, a number, a classification label.

**Limitation:** Models often add explanation ("Yes, that is correct.") even when you ask for a single word. Pair with `max_length` to enforce brevity, or use `contains` instead.

---

## Contains

```yaml
- type: contains
  value: "def fibonacci"
  case_insensitive: false  # optional, default false
```

The output must contain the substring `value`.

**Use when:** The output should include a specific word, phrase, or code token, regardless of what surrounds it.

**Limitation:** Only checks presence. A response that contains the string but is otherwise nonsensical will pass. Combine with `min_length`, `not_contains`, and `llm_judge` for stronger coverage.

```yaml
# Negative check: ensure something is absent
- type: not_contains
  value: "I cannot help"
  case_insensitive: true
```

---

## Fuzzy match

```yaml
- type: fuzzy_match
  value: "The quick brown fox jumps over the lazy dog"
  threshold: 0.6  # 0.0-1.0, lower = more permissive
```

Uses character-level sequence similarity (`difflib.SequenceMatcher`). The output must have similarity above `threshold` compared to `value`.

**Use when:** The output should be semantically close to a known-good response but exact phrasing may vary.

**Limitation:** Character-level similarity doesn't capture semantic similarity. "The fox is quick and brown" and "The quick brown fox" will score higher than "A fast auburn vulpine" even though the latter is more semantically similar. For semantic comparison, use `llm_judge`.

---

## Regex

```yaml
- type: regex
  pattern: "\\d{4}-\\d{2}-\\d{2}"
  case_insensitive: false  # optional
```

The output must match the regex pattern (searched, not full-match).

**Use when:** The output should contain structured text with a predictable format — dates, phone numbers, URLs, code patterns.

**Note on escaping:** In YAML strings, use `\\d` not `\d`. The YAML parser handles one level of escaping before the regex engine handles another.

Examples:
```yaml
# ISO date
pattern: "\\d{4}-\\d{2}-\\d{2}"

# Email address
pattern: "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"

# Python function definition
pattern: "def \\w+\\(.*\\):"

# JSON key present
pattern: "\"status\":\\s*\"\\w+\""

# Starts with a markdown bullet
pattern: "^[-*]\\s+"
```

---

## JSON validation

```yaml
# Check output is valid JSON
- type: json_valid

# Check output matches a schema
- type: json_schema
  schema:
    required:
      - name
      - age
    properties:
      name:
        type: string
      age:
        type: integer
      active:
        type: boolean
```

`json_valid` checks that the output parses without error.

`json_schema` checks that required fields are present and fields have the expected types. Types supported: `string`, `number`, `integer`, `boolean`, `array`, `object`.

**Limitation:** Schema validation here is basic — it doesn't support nested schemas, enums, or format constraints. For full JSON Schema validation, install `jsonschema` and extend `evaluate.py`.

**Common pattern:** Pair `json_valid` + `json_schema` + `not_contains: "```"` to ensure you get clean JSON without markdown fences:

```yaml
assertions:
  - type: json_valid
  - type: json_schema
    schema:
      required: [id, status]
  - type: not_contains
    value: "```"
```

---

## Length constraints

```yaml
- type: not_empty         # output is not empty or whitespace-only
- type: max_length
  value: 500              # output is under 500 characters
- type: min_length
  value: 100              # output is over 100 characters
```

Length is measured in characters, not words or tokens.

**Use when:** You have strict length requirements (e.g., a classification that must be one word) or quality requirements (a substantive response should be at least N characters).

---

## LLM-as-judge

```yaml
- type: llm_judge
  criteria: |
    The function correctly implements fibonacci.
    It handles edge cases n=0 and n=1 correctly.
    The code is readable Python.
  threshold: 0.8
```

A second LLM call is made to score the output against `criteria`. The judge returns a score from 0.0 to 1.0. The assertion passes if `score >= threshold`.

The judge uses this prompt structure:
1. System prompt: "You are an impartial evaluator..."
2. User prompt: The criteria, the output to evaluate, and the original input.
3. Expected response: JSON with `score`, `reasoning`, and `passed`.

**Run with:**
```bash
python framework/evaluate.py results/run.json --judge-model claude-3-5-sonnet-20241022
```

**Use when:**
- The output must satisfy subjective quality criteria (tone, helpfulness, accuracy of reasoning)
- The output is too variable for exact or regex matching but correctness is still assessable
- You want to measure quality on a spectrum, not just pass/fail

**Choosing a judge model:**
- Use a more capable model than the one being tested when possible
- `claude-3-5-sonnet-20241022` or `gpt-4o` are good judge models
- Avoid using the same model that generated the output (self-evaluation bias)

**Writing good criteria:**
```yaml
# Too vague — judge cannot assess reliably
criteria: "The response is good."

# Better — specific, verifiable behaviors
criteria: |
  The response:
  1. Answers the user's actual question directly
  2. Does not include irrelevant information
  3. Is written at a reading level appropriate for a non-technical user
  4. Does not start with "As an AI..."
```

**Limitation:** LLM judges are not perfectly reliable. They can be inconsistent across runs and may reflect biases in the judge model. Use a consistent judge model across comparisons, and treat scores as approximate rather than exact.

---

## Rubric scoring

```yaml
- type: rubric
  threshold: 0.75
  rubric:
    - criterion: "Accuracy"
      max_score: 3
      description: "The answer is factually correct"
    - criterion: "Clarity"
      max_score: 2
      description: "The explanation is easy to understand"
    - criterion: "Conciseness"
      max_score: 1
      description: "No unnecessary padding"
```

The judge scores each rubric criterion independently, sums the scores, and normalizes to 0.0-1.0. Passes if `normalized_score >= threshold`.

**Use when:**
- You need to break down quality into independent dimensions
- You want to track which dimensions degrade after a change
- You're doing A/B testing and want to compare variants across dimensions

**Rubric design tips:**
- Keep each criterion independent (don't overlap)
- Use 1-3 as max_score per criterion; avoid large scales that are hard to interpret consistently
- 5-8 criteria is a good range; more than 10 reduces reliability
- Write criteria that a judge can score without needing context about your product

---

## Combining methods

Use multiple assertions to create defense in depth:

```yaml
assertions:
  # Cheap, fast checks first
  - type: not_empty
  - type: contains
    value: "def "
  - type: max_length
    value: 1000

  # More specific structural check
  - type: regex
    pattern: "def \\w+\\(.*\\):"

  # Subjective quality check (runs in evaluate.py, not the initial run)
  - type: llm_judge
    criteria: "The function is correct, readable, and handles edge cases."
    threshold: 0.8
```

The cheap checks catch obvious failures early without spending tokens on judge calls.

---

## Choosing a method

| Output type | Recommended method |
|-------------|-------------------|
| Single word / exact phrase | `exact_match` + `max_length` |
| Contains a specific term | `contains` |
| Matches a format pattern | `regex` |
| Valid JSON | `json_valid` + `json_schema` |
| Code that works | `contains` + `llm_judge` |
| Quality of explanation | `llm_judge` or `rubric` |
| Length constraint | `min_length` / `max_length` |
| Not empty | `not_empty` |
| Not present | `not_contains` |
