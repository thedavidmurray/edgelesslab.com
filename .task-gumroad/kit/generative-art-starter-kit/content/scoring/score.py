#!/usr/bin/env python3
"""
AI Scoring Script for Generative Art
Uses vision-capable LLMs to score SVG/PNG outputs.

Usage:
    python score.py output/flow.png
    python score.py output/*.png --provider gemini

Requires: API key for your chosen provider set as environment variable.
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path

SCORING_PROMPT = """Score this generative art piece for pen plotter output.

Rate each dimension 1-10:
1. Composition (balance, space usage, focal point)
2. Complexity (appropriate detail level -- not too sparse, not too chaotic)
3. Coherence (visual logic -- does the piece "make sense"?)
4. Ink Coverage (estimate percentage, target 10-80%)
5. Plottability (clean strokes, no tiny detail that plotters can't render)
6. Uniqueness (does this look different from typical generative art?)

Respond ONLY as JSON:
{
  "composition": 7,
  "complexity": 8,
  "coherence": 6,
  "ink_coverage_pct": 45,
  "plottability": 9,
  "uniqueness": 5,
  "overall": 7.2,
  "notes": "One sentence assessment"
}"""


def score_with_gemini(image_path: str) -> dict:
    """Score using Google Gemini Vision."""
    import urllib.request

    api_key = os.environ.get("GOOGLE_GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("Set GOOGLE_GEMINI_API_KEY environment variable")

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    mime = "image/png" if image_path.endswith(".png") else "image/svg+xml"

    payload = {
        "contents": [{
            "parts": [
                {"text": SCORING_PROMPT},
                {"inline_data": {"mime_type": mime, "data": image_data}},
            ]
        }]
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())

    text = result["candidates"][0]["content"]["parts"][0]["text"]
    # Extract JSON from response
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(text)


def score_with_openai(image_path: str) -> dict:
    """Score using OpenAI GPT-4o Vision."""
    import urllib.request

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ValueError("Set OPENAI_API_KEY environment variable")

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    mime = "image/png" if image_path.endswith(".png") else "image/svg+xml"

    payload = {
        "model": "gpt-4o-mini",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": SCORING_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{image_data}"}},
            ],
        }],
        "max_tokens": 500,
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode(),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())

    text = result["choices"][0]["message"]["content"]
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(text)


PROVIDERS = {
    "gemini": score_with_gemini,
    "openai": score_with_openai,
}


def main():
    parser = argparse.ArgumentParser(description="AI Art Scoring")
    parser.add_argument("images", nargs="+", help="Image files to score")
    parser.add_argument("--provider", choices=PROVIDERS.keys(), default="gemini")
    parser.add_argument("--output", type=str, default=None, help="Save results as JSON")
    args = parser.parse_args()

    scorer = PROVIDERS[args.provider]
    results = []

    for image_path in args.images:
        if not Path(image_path).exists():
            print(f"Skipping {image_path}: file not found", file=sys.stderr)
            continue

        print(f"Scoring {image_path}...", file=sys.stderr)
        try:
            score = scorer(image_path)
            score["file"] = image_path
            results.append(score)

            overall = score.get("overall", "?")
            notes = score.get("notes", "")
            print(f"  Score: {overall}/10 -- {notes}")
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)

    if args.output and results:
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        print(f"\nSaved {len(results)} scores to {args.output}", file=sys.stderr)

    if results:
        avg = sum(r.get("overall", 0) for r in results) / len(results)
        print(f"\nAverage score: {avg:.1f}/10 across {len(results)} pieces")


if __name__ == "__main__":
    main()
