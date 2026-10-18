"""
skill_matcher.py - Lightweight skill discovery via YAML frontmatter parsing
Scans skill.md files, parses YAML frontmatter, provides keyword matching.
"""

import re
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class SkillInfo:
    """Represents a skill with its metadata."""
    name: str
    description: str
    file_path: str

    def match_score(self, query: str) -> float:
        """Calculate relevance score for a search query."""
        query_lower = query.lower()
        name_lower = self.name.lower()
        description_lower = self.description.lower()
        score = 0.0

        # Exact name match - highest score
        if name_lower == query_lower:
            return 1.0

        # Name contains full query
        if query_lower in name_lower:
            score += 0.7

        # Query contains skill name (e.g., "changelog" in query, skill is "changelog-generator")
        name_words = name_lower.replace('-', ' ').split()
        query_words = query_lower.split()

        # Check if any name word is in query
        for name_word in name_words:
            if len(name_word) < 3:
                continue
            if name_word in query_lower:
                score += 0.4  # Significant boost for name word match

        # Check query words against description
        matched_words = 0
        for word in query_words:
            if len(word) < 3:  # Skip very short words
                continue
            if word in description_lower:
                matched_words += 1

        if matched_words > 0:
            # Give more weight if multiple words match
            word_score = min(0.5, matched_words * 0.15)
            score += word_score

        return min(score, 1.0)  # Cap at 1.0


class SkillMatcher:
    """
    Lightweight skill matcher using YAML frontmatter from skill.md files.

    Usage:
        matcher = SkillMatcher(skills_dir)
        matches = matcher.match_skills("create changelog")
    """

    def __init__(self, skills_dir: Path):
        """
        Initialize skill matcher.

        Args:
            skills_dir: Path to .claude/skills directory
        """
        self.skills_dir = Path(skills_dir)
        self._skills_cache: Optional[List[SkillInfo]] = None

    def _parse_yaml_frontmatter(self, content: str) -> Optional[Dict[str, str]]:
        """
        Parse YAML frontmatter from markdown content.

        Args:
            content: Raw markdown content

        Returns:
            Dict with 'name' and 'description', or None if no frontmatter
        """
        # Match YAML frontmatter: starts with ---, ends with ---
        match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
        if not match:
            return None

        yaml_content = match.group(1)
        result = {}

        # Simple YAML parsing (name: value pairs)
        for line in yaml_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Match "key: value" pattern
            key_match = re.match(r'(\w+):\s*(.+)', line)
            if key_match:
                key, value = key_match.groups()
                result[key] = value.strip()

        return result if 'name' in result and 'description' in result else None

    def _scan_skills(self) -> List[SkillInfo]:
        """
        Scan all skill.md files and extract metadata.

        Returns:
            List of SkillInfo objects
        """
        skills = []

        if not self.skills_dir.exists():
            return skills

        # Find all skill.md files
        for skill_file in self.skills_dir.glob("*/skill.md"):
            try:
                content = skill_file.read_text(encoding='utf-8')
                frontmatter = self._parse_yaml_frontmatter(content)

                if frontmatter:
                    skills.append(SkillInfo(
                        name=frontmatter['name'],
                        description=frontmatter['description'],
                        file_path=str(skill_file)
                    ))
            except (OSError, UnicodeDecodeError):
                # Skip files that can't be read
                continue

        return skills

    def get_skills(self, force_refresh: bool = False) -> List[SkillInfo]:
        """
        Get all skills, using cache if available.

        Args:
            force_refresh: If True, bypass cache and re-scan

        Returns:
            List of SkillInfo objects
        """
        if self._skills_cache is None or force_refresh:
            self._skills_cache = self._scan_skills()
        return self._skills_cache

    def match_skills(self, user_input: str, top_n: int = 3, min_score: float = 0.3) -> List[Dict[str, any]]:
        """
        Match user input against available skills.

        Args:
            user_input: User's prompt or query
            top_n: Maximum number of matches to return
            min_score: Minimum score threshold (0.0 to 1.0)

        Returns:
            List of dicts with 'name', 'description', 'score', sorted by score
        """
        skills = self.get_skills()

        # Calculate scores for all skills
        scored_skills = []
        for skill in skills:
            score = skill.match_score(user_input)
            if score >= min_score:
                scored_skills.append({
                    'name': skill.name,
                    'description': skill.description,
                    'score': score
                })

        # Sort by score (descending) and return top N
        scored_skills.sort(key=lambda x: x['score'], reverse=True)
        return scored_skills[:top_n]

    def get_skill_by_name(self, name: str) -> Optional[SkillInfo]:
        """
        Get a specific skill by name.

        Args:
            name: Skill name to find

        Returns:
            SkillInfo if found, None otherwise
        """
        skills = self.get_skills()
        for skill in skills:
            if skill.name == name:
                return skill
        return None


# Backwards compatibility with old SkillMatcher interface
class LegacySkillMatcher:
    """
    Compatibility wrapper for old skill-rules.json based matcher.
    Delegates to new YAML-based matcher when possible.
    """

    def __init__(self, rules: dict, skills_dir: Path):
        """
        Initialize with rules and skills directory.

        Args:
            rules: Loaded skill-rules.json content (for backwards compatibility)
            skills_dir: Path to skills directory
        """
        self.rules = rules
        self.skills_dir = Path(skills_dir)
        self.yaml_matcher = SkillMatcher(skills_dir)
        self.skills = rules.get("skills", [])
        self.global_rules = rules.get("global_rules", {})

        # Compile keyword patterns for efficiency
        self._compile_patterns()

    def _compile_patterns(self):
        """Pre-compile regex patterns for keyword matching."""
        self.patterns = {}

        for skill in self.skills:
            trigger = skill.get("trigger", "")

            if trigger.startswith("keyword:"):
                # Convert pipe-separated keywords to regex
                keywords = trigger[8:].split("|")
                pattern = "|".join(re.escape(k) for k in keywords)
                self.patterns[skill["name"]] = re.compile(pattern, re.IGNORECASE)

    def match(self, prompt: str) -> List[Dict[str, any]]:
        """
        Match a prompt using both old and new matching strategies.

        Args:
            prompt: User's input prompt

        Returns:
            List of matched skills with metadata
        """
        # First try YAML-based matching
        yaml_matches = self.yaml_matcher.match_skills(prompt, top_n=5, min_score=0.2)

        # Then add legacy rule-based matches
        legacy_matches = []
        prompt_lower = prompt.lower()

        for skill in self.skills:
            match_result = self._check_skill_match(skill, prompt, prompt_lower)
            if match_result:
                legacy_matches.append(match_result)

        # Merge results, preferring YAML matches
        all_names = {m['name'] for m in yaml_matches}
        for legacy in legacy_matches:
            if legacy['name'] not in all_names:
                # Add legacy match with converted format
                yaml_matches.append({
                    'name': legacy['name'],
                    'description': legacy.get('description', ''),
                    'score': 0.5 if legacy.get('auto_activate') else 0.3
                })

        # Sort by score
        yaml_matches.sort(key=lambda x: x['score'], reverse=True)
        return yaml_matches[:3]

    def _check_skill_match(self, skill: dict, prompt: str, prompt_lower: str) -> Optional[Dict[str, any]]:
        """Check if a single skill matches the prompt (legacy logic)."""
        name = skill["name"]
        trigger = skill.get("trigger", "")

        # Check compiled pattern if exists
        if name in self.patterns:
            pattern = self.patterns[name]
            match = pattern.search(prompt_lower)
            if match:
                return self._build_match_result(skill, f"Matched keyword: {match.group()}")

        # Check session start trigger
        if trigger == "session_start":
            if self._is_session_start(prompt_lower):
                return self._build_match_result(skill, "Session start detected")

        return None

    def _is_session_start(self, prompt_lower: str) -> bool:
        """Detect if prompt looks like a session start."""
        session_indicators = [
            "hello", "hi", "hey", "start", "begin",
            "let's", "help me", "good morning", "good afternoon"
        ]

        if len(prompt_lower) < 100:
            return any(ind in prompt_lower for ind in session_indicators)

        return False

    def _build_match_result(self, skill: dict, reason: str) -> Dict[str, any]:
        """Build a standardized match result."""
        return {
            "name": skill["name"],
            "commands": skill.get("commands", []),
            "auto_activate": skill.get("auto_activate", False),
            "reason": reason,
            "description": skill.get("description", ""),
            "priority": skill.get("priority", 5)
        }
