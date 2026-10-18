#!/usr/bin/env python3
"""
skill-activation.py - ESSENTIAL Hook for UserPromptSubmit
Analyzes user prompts and suggests relevant skills based on context.
Follows IndyDevDan's progressive disclosure pattern.

SECURITY HARDENED: 2024-12-23
- Removed dynamic sys.path manipulation
- Added config integrity verification
- Input validation on all JSON fields
"""

import json
import os
import sys
import re
import hashlib
import importlib.util
from pathlib import Path

# Configuration - use environment variable with fallback
PROJECT_DIR = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).parent.parent.parent))
HOOKS_DIR = Path(__file__).parent
SKILL_RULES_PATH = Path(__file__).parent.parent / "skill-rules.json"
SKILLS_DIR = Path(__file__).parent.parent / "skills"

# Integrity hash for skill-rules.json (update when config changes legitimately)
# Generate with: python3 -c "import hashlib; print(hashlib.sha256(open('.claude/skill-rules.json').read().encode()).hexdigest())"
EXPECTED_CONFIG_HASH = "55056e66d54a9e5c82cd86f320fb95f965a05dacfc0c379a39817e18488808af"

def load_skill_matcher():
    """Safely load SkillMatcher from explicit path without sys.path manipulation."""
    matcher_path = HOOKS_DIR / "lib" / "skill_matcher.py"

    if not matcher_path.exists():
        return None, None

    # Verify the file is within our hooks directory (prevent symlink attacks)
    try:
        resolved = matcher_path.resolve()
        if not str(resolved).startswith(str(HOOKS_DIR.resolve())):
            return None, None
    except (OSError, ValueError):
        return None, None

    try:
        spec = importlib.util.spec_from_file_location("skill_matcher", matcher_path)
        if spec is None or spec.loader is None:
            return None, None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Return both new YAML-based matcher and legacy wrapper
        return getattr(module, "SkillMatcher", None), getattr(module, "LegacySkillMatcher", None)
    except Exception:
        return None, None

SkillMatcher, LegacySkillMatcher = load_skill_matcher()

def verify_config_integrity(content: str) -> bool:
    """Verify skill-rules.json hasn't been tampered with."""
    if EXPECTED_CONFIG_HASH is None:
        return True  # Integrity checking disabled
    actual_hash = hashlib.sha256(content.encode()).hexdigest()
    return actual_hash == EXPECTED_CONFIG_HASH

def load_skill_rules():
    """Load skill rules from configuration file with integrity verification."""
    default_rules = {"skills": [], "global_rules": {"suggest_skills": True}}

    if not SKILL_RULES_PATH.exists():
        return default_rules

    # Verify path is within expected directory (prevent symlink attacks)
    try:
        resolved = SKILL_RULES_PATH.resolve()
        expected_parent = Path(__file__).parent.parent.resolve()
        if not str(resolved).startswith(str(expected_parent)):
            return default_rules
    except (OSError, ValueError):
        return default_rules

    try:
        with open(SKILL_RULES_PATH) as f:
            content = f.read()

        # Verify integrity if hash is configured
        if not verify_config_integrity(content):
            # Config tampered - fail closed
            return default_rules

        return json.loads(content)
    except (json.JSONDecodeError, OSError):
        return default_rules

def analyze_prompt(prompt: str, rules: dict) -> list:
    """Analyze prompt and return matching skills."""
    matches = []
    prompt_lower = prompt.lower()

    for skill in rules.get("skills", []):
        trigger = skill.get("trigger", "")

        # Check keyword triggers
        if trigger.startswith("keyword:"):
            keywords = trigger[8:].split("|")
            if any(kw in prompt_lower for kw in keywords):
                matches.append({
                    "name": skill["name"],
                    "commands": skill.get("commands", []),
                    "auto_activate": skill.get("auto_activate", False),
                    "reason": f"Matched keywords: {', '.join(k for k in keywords if k in prompt_lower)}"
                })

        # Check session start triggers
        elif trigger == "session_start":
            # Detect if this looks like a session start
            session_indicators = ["hello", "hi", "start", "begin", "let's", "help me"]
            if any(ind in prompt_lower for ind in session_indicators) and len(prompt) < 100:
                matches.append({
                    "name": skill["name"],
                    "commands": skill.get("commands", []),
                    "auto_activate": skill.get("auto_activate", False),
                    "reason": "Session start detected"
                })

    return matches

def format_suggestions(matches: list) -> str:
    """
    Format skill suggestions for display.
    Lightweight one-line format: "Relevant skills: /skill1 (desc), /skill2 (desc)"
    """
    if not matches:
        return ""

    # Create concise skill hints
    hints = []
    for match in matches:
        name = match.get('name', '')
        # Extract first few words from description
        desc = match.get('description', '')
        if desc:
            # Get first sentence or first 5 words
            desc_short = desc.split('.')[0] if '.' in desc else desc
            words = desc_short.split()[:5]
            desc_hint = ' '.join(words)
            if len(desc.split()) > 5:
                desc_hint += '...'
        else:
            desc_hint = match.get('reason', 'relevant skill')

        hints.append(f"/{name} ({desc_hint})")

    if not hints:
        return ""

    # Single line suggestion
    return f"\nRelevant skills: {', '.join(hints)}"

def validate_input(hook_input: dict) -> dict:
    """Validate and sanitize hook input."""
    validated = {}

    # Extract and validate prompt - must be string, reasonable length
    prompt = hook_input.get("prompt", "")
    if not isinstance(prompt, str):
        prompt = ""
    # Limit prompt length to prevent DoS
    prompt = prompt[:10000]
    validated["prompt"] = prompt

    # Fallback fields
    if not prompt:
        content = hook_input.get("content", hook_input.get("message", ""))
        if isinstance(content, str):
            validated["prompt"] = content[:10000]

    return validated

def main():
    """Main hook entry point."""
    # Read hook input from stdin with size limit
    try:
        raw_input = sys.stdin.read(100000)  # 100KB max
        hook_input = json.loads(raw_input)
        if not isinstance(hook_input, dict):
            hook_input = {}
    except (json.JSONDecodeError, ValueError):
        hook_input = {}

    # Validate and sanitize input
    validated = validate_input(hook_input)
    prompt = validated.get("prompt", "")

    # Load rules and analyze
    rules = load_skill_rules()

    # Prefer the compatibility matcher because it merges YAML discovery with
    # explicit keyword rules such as source-grounded NotebookLM routing.
    matches = []
    if LegacySkillMatcher:
        try:
            legacy_matcher = LegacySkillMatcher(rules, SKILLS_DIR)
            matches = legacy_matcher.match(prompt)
        except Exception:
            if SkillMatcher:
                try:
                    yaml_matcher = SkillMatcher(SKILLS_DIR)
                    matches = yaml_matcher.match_skills(prompt, top_n=3, min_score=0.3)
                except Exception:
                    matches = analyze_prompt(prompt, rules)
            else:
                matches = analyze_prompt(prompt, rules)
    elif SkillMatcher:
        try:
            yaml_matcher = SkillMatcher(SKILLS_DIR)
            matches = yaml_matcher.match_skills(prompt, top_n=3, min_score=0.3)
        except Exception:
            matches = analyze_prompt(prompt, rules)
    else:
        matches = analyze_prompt(prompt, rules)

    # Build response with correct schema
    # Claude Code expects: continue (bool), decision (approve|block), not "decision": "continue"
    # For UserPromptSubmit, we can add additionalContext
    response = {
        "continue": True
    }

    # Add suggestions as additionalContext if any matches and suggestions enabled
    if matches and rules.get("global_rules", {}).get("suggest_skills", True):
        suggestions = format_suggestions(matches)
        if suggestions:
            response["hookSpecificOutput"] = {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": suggestions
            }

    # Output JSON response for Claude Code
    print(json.dumps(response))

if __name__ == "__main__":
    main()
