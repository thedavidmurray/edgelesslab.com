# 01 — Why Test Prompts

## The silent regression problem

You iterate on a prompt, ship it, and it works. Three weeks later, a report comes in: the output quality has degraded. Nobody changed the prompt — but the model provider shipped a silent update, or the input distribution shifted, or someone made a "minor wording change" that turned out to matter.

You have no baseline. You have no test. You can't reproduce when it stopped working.

This is the silent regression problem. It happens because most teams treat prompts as configuration rather than code.

---

## Why prompts break

Prompts fail for reasons that differ from traditional software bugs:

**Model updates.** Providers update models without announcing it. A prompt tuned for one model version may produce worse output on a successor. You need tests that catch this.

**Input distribution shift.** Your prompt was developed on the clean, well-formed inputs in your examples. Real users send edge cases, unicode, empty inputs, and half-formed sentences. Tests surface what your prompt does with those.

**Incremental drift.** Small wording changes accumulate. Each change seems safe in isolation. The combined effect is a prompt that barely resembles the original intent. Tests give you a regression line.

**Context window pressure.** As you add system prompt content — instructions, examples, constraints — older instructions get pushed toward the end and lose attention weight. Tests detect when additions degrade earlier behaviors.

**Adversarial inputs.** If your prompt is exposed to untrusted user input, injection attacks are a real concern. Tests verify that your prompt resists them.

---

## What testing buys you

**Confidence to iterate.** When you have a passing test suite, you can change your prompt and know within minutes whether you broke anything. Without tests, every change is a gamble.

**A regression baseline.** Save test results before any change. Compare after. A drop in pass rate is an objective signal, not a gut feeling.

**Documentation of intent.** A test suite is a specification. It says: "this prompt should produce output containing X, formatted as Y, handling edge case Z." That's more useful than a comment in a doc.

**Faster debugging.** When something breaks, your test suite narrows the cause. Which test failed? What input triggered it? What did the output contain? The failure report is the starting point for the investigation.

**CI/CD enforcement.** Tests that run in CI prevent broken prompts from reaching production. The pipeline fails if the pass rate drops below threshold.

---

## What this framework provides

**A CLI tool** (`prompt-test.sh`) that reads YAML test specs and runs them against real API calls. No mock responses. Real model output.

**Pre-built test suites** for accuracy, consistency, edge cases, format compliance, and safety.

**An LLM-as-judge evaluator** (`evaluate.py`) for subjective quality criteria that can't be checked with simple string matching.

**Templates** for A/B testing, regression testing, and benchmarking.

**HTML reports** that show pass rates, latency, and assertion details in a scannable format.

---

## When not to use this framework

**During initial prompt development.** When you're still figuring out what the prompt should do, don't write tests yet. Write tests once you have a working version worth protecting.

**For one-off manual prompts.** If you're using a prompt once, testing overhead isn't worth it. Tests pay off when prompts are used repeatedly in production.

**As a substitute for human evaluation.** LLM-as-judge is useful but imperfect. For high-stakes outputs, use this framework to filter obvious failures, then add human review for borderline cases.

---

## Next steps

- Read `02-test-anatomy.md` to understand how a test is structured.
- Run an example test: `./framework/prompt-test.sh run test-suites/accuracy/test_spec.yaml --dry-run`
- Look at `framework/config.example.yaml` for the full YAML reference.
