# 04 — CI/CD Integration

Running prompt tests in CI catches regressions before they reach production. This document covers integration patterns for GitHub Actions, GitLab CI, and shell-based pipelines, plus strategies for managing API costs and test execution time.

---

## Core pattern

The simplest CI integration:

1. Store your API key as a CI secret.
2. Run your test suite on pull requests.
3. Fail the pipeline if pass rate drops below threshold.

```bash
./framework/prompt-test.sh run-all test-suites/ --fail-threshold 0.9
```

Exit codes:
- `0` — all tests pass
- `1` — failures below threshold
- `2` — configuration error (missing spec file, invalid YAML, missing API key)

---

## GitHub Actions

### Basic setup

```yaml
# .github/workflows/prompt-tests.yml
name: Prompt Tests

on:
  pull_request:
    paths:
      - 'prompts/**'
      - 'test-suites/**'
      - 'framework/**'
  push:
    branches:
      - main

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install pyyaml

      - name: Make CLI executable
        run: chmod +x framework/prompt-test.sh

      - name: Run prompt tests
        run: |
          ./framework/prompt-test.sh run-all test-suites/ \
            --fail-threshold 0.9 \
            --output results/ci-run.json
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          PTF_RESULTS_DIR: results

      - name: Evaluate LLM judge assertions
        if: always()
        run: |
          python framework/evaluate.py results/ci-run.json \
            --report results/report.html
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

      - name: Upload test report
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: prompt-test-report
          path: results/
          retention-days: 30
```

### Path-filtered triggers

Run only affected test suites when prompt files change:

```yaml
on:
  pull_request:
    paths:
      - 'prompts/support-*.md'  # Only run when support prompts change

jobs:
  test-support:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: pip install pyyaml
      - name: Run support tests
        run: ./framework/prompt-test.sh run test-suites/accuracy/test_spec.yaml
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Scheduled benchmark runs

Run benchmarks weekly on a schedule rather than every PR:

```yaml
on:
  schedule:
    - cron: '0 8 * * 1'  # Every Monday at 8am UTC

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: pip install pyyaml
      - name: Run benchmark
        run: |
          DATE=$(date +%Y%m%d)
          ./framework/prompt-test.sh run templates/benchmark.yaml \
            --output "results/benchmark-${DATE}.json"
          python framework/evaluate.py "results/benchmark-${DATE}.json" \
            --report "results/benchmark-${DATE}.html"
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      - name: Upload benchmark results
        uses: actions/upload-artifact@v4
        with:
          name: benchmark-${{ github.run_number }}
          path: results/
```

---

## GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - test

prompt-tests:
  stage: test
  image: python:3.11-slim
  before_script:
    - pip install pyyaml
    - chmod +x framework/prompt-test.sh
  script:
    - |
      ./framework/prompt-test.sh run-all test-suites/ \
        --fail-threshold 0.9 \
        --output results/ci-run.json
    - |
      python framework/evaluate.py results/ci-run.json \
        --report results/report.html
  artifacts:
    when: always
    paths:
      - results/
    expire_in: 30 days
  only:
    changes:
      - prompts/**/*
      - test-suites/**/*
```

---

## Managing costs

Prompt tests make real API calls. Cost scales with test count, model choice, and frequency.

**Use cheap models for CI.** `claude-3-5-haiku-20241022` costs ~10x less than `claude-3-5-sonnet-20241022` and is appropriate for most CI assertions.

```yaml
# In test_spec.yaml, use haiku for CI
model: "claude-3-5-haiku-20241022"
```

**Separate fast and slow test suites.** Run cheap tests on every PR. Reserve expensive tests (rubrics, many judge calls) for merge to main or nightly runs.

```bash
# On PR: run fast tests only
./framework/prompt-test.sh run test-suites/accuracy/test_spec.yaml
./framework/prompt-test.sh run test-suites/format-compliance/test_spec.yaml

# On merge to main: run everything including LLM judge
./framework/prompt-test.sh run-all test-suites/
python framework/evaluate.py results/latest.json
```

**Limit test count per suite.** Keep CI-facing test specs focused: 10-20 tests per suite. Save comprehensive testing for pre-release.

**Cache results for unchanged prompts.** If no prompt file changed, skip the test run entirely using path filters.

---

## Managing test execution time

**Typical times per test:**
- Simple assertion (contains, regex): 1-4 seconds (dominated by API latency)
- LLM judge call: 3-10 seconds
- 20 tests + 10 judge calls: ~2-5 minutes

**Parallelization.** The CLI runs tests sequentially to avoid rate limit issues. For parallel execution, split your test spec into multiple files and run them in parallel CI jobs.

```yaml
# GitHub Actions matrix for parallel suites
jobs:
  test:
    strategy:
      matrix:
        suite: [accuracy, consistency, edge-cases, format-compliance]
    steps:
      - run: ./framework/prompt-test.sh run test-suites/${{ matrix.suite }}/test_spec.yaml
```

**Timeout handling.** Set per-request timeouts to avoid hung CI jobs:

```bash
./framework/prompt-test.sh run test-suites/accuracy/test_spec.yaml --timeout 20
```

---

## Storing results

Results JSON files are small (typically < 100KB). Options:

**Git artifact.** Store in CI artifacts with a retention window. Good for debugging recent failures.

**Object storage.** For long-term trend analysis, push results to S3, GCS, or similar after each run:

```bash
# After the test run
aws s3 cp results/ci-run.json \
  s3://your-bucket/prompt-test-results/$(date +%Y/%m/%d)/run-${CI_RUN_ID}.json
```

**PR comments.** Post a summary to the PR on failure:

```yaml
- name: Comment on PR
  if: failure()
  uses: actions/github-script@v7
  with:
    script: |
      const results = require('./results/ci-run.json')
      const { passed, failed, pass_rate } = results.summary
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: `**Prompt Tests Failed**\n\nPassed: ${passed} | Failed: ${failed} | Rate: ${(pass_rate*100).toFixed(1)}%`
      })
```

---

## Pre-commit hook

Run a fast smoke test before every commit:

```bash
# .git/hooks/pre-commit
#!/usr/bin/env bash
if git diff --cached --name-only | grep -q "^prompts/"; then
    echo "Prompt files changed — running smoke tests..."
    ./framework/prompt-test.sh run test-suites/accuracy/test_spec.yaml \
        --fail-threshold 1.0 \
        --timeout 15
fi
```

```bash
chmod +x .git/hooks/pre-commit
```

This only runs if prompt files are staged. Fast tests (accuracy, format-compliance) are appropriate here. Skip slow tests (safety, LLM judge) in pre-commit.
