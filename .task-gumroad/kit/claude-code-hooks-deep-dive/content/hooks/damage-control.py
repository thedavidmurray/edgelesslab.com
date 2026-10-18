#!/usr/bin/env python3
"""
Damage Control PreToolUse Hook
Blocks dangerous commands and protects critical paths BEFORE execution.

Exit codes:
  0 - Allow the tool execution
  2 - Block the tool execution (returns error message to Claude)

Based on IndyDevDan's damage control patterns.
"""

import sys
import json
import re
import os
from pathlib import Path

# Load patterns from YAML (inline parser to avoid dependency)
def load_patterns():
    """Load patterns from patterns.yaml without pyyaml dependency."""
    patterns_path = Path(__file__).parent / 'patterns.yaml'

    if not patterns_path.exists():
        return None

    content = patterns_path.read_text()

    # Simple YAML parsing for our specific structure
    patterns = {
        'dangerous_commands': {'bash': {'block_patterns': []}},
        'paths': {'zero_access': [], 'read_only': [], 'no_delete': []},
        'allowlist': []
    }

    current_section = None
    current_subsection = None

    for line in content.split('\n'):
        stripped = line.strip()

        # Skip comments and empty lines
        if not stripped or stripped.startswith('#'):
            continue

        # Detect sections
        if stripped == 'dangerous_commands:':
            current_section = 'dangerous_commands'
            current_subsection = None
        elif stripped == 'paths:':
            current_section = 'paths'
            current_subsection = None
        elif stripped == 'allowlist:':
            current_section = 'allowlist'
            current_subsection = None
        elif stripped == 'bash:' and current_section == 'dangerous_commands':
            current_subsection = 'bash'
        elif stripped == 'block_patterns:':
            current_subsection = 'block_patterns'
        elif stripped == 'zero_access:':
            current_subsection = 'zero_access'
        elif stripped == 'read_only:':
            current_subsection = 'read_only'
        elif stripped == 'no_delete:':
            current_subsection = 'no_delete'
        elif stripped.startswith("- '") or stripped.startswith('- "'):
            # Extract pattern value
            match = re.match(r"-\s*['\"](.+?)['\"]", stripped)
            if match:
                value = match.group(1)

                if current_section == 'dangerous_commands' and current_subsection == 'block_patterns':
                    patterns['dangerous_commands']['bash']['block_patterns'].append(value)
                elif current_section == 'paths':
                    if current_subsection in patterns['paths']:
                        patterns['paths'][current_subsection].append(value)
                elif current_section == 'allowlist':
                    patterns['allowlist'].append(value)

    return patterns


def is_allowlisted(path, patterns):
    """Check if path is in allowlist."""
    for allowed in patterns.get('allowlist', []):
        if allowed in path:
            return True
    return False


def check_bash_command(command, patterns):
    """Check if bash command matches any dangerous pattern."""
    block_patterns = patterns.get('dangerous_commands', {}).get('bash', {}).get('block_patterns', [])

    for pattern in block_patterns:
        try:
            if re.search(pattern, command, re.IGNORECASE):
                return f"BLOCKED: Dangerous command pattern detected: '{pattern}'\nCommand: {command[:100]}..."
        except re.error:
            # Invalid regex, skip
            continue

    return None


def check_path_protection(path, tool_name, patterns):
    """Check if path violates any protection rules."""

    # Expand home directory
    if path.startswith('~'):
        path = os.path.expanduser(path)

    # Check allowlist first
    if is_allowlisted(path, patterns):
        return None

    path_rules = patterns.get('paths', {})

    # Zero access - block all operations
    for protected in path_rules.get('zero_access', []):
        if protected in path:
            return f"BLOCKED: Path '{path}' is protected (zero_access)\nPattern matched: '{protected}'"

    # Read only - block Write and Edit
    if tool_name in ['Write', 'Edit']:
        for protected in path_rules.get('read_only', []):
            if protected in path:
                return f"BLOCKED: Path '{path}' is read-only\nPattern matched: '{protected}'"

    # No delete - would need to check for delete operations
    # (handled separately for rm commands in bash)

    return None


def check_delete_protection(command, patterns):
    """Check if rm/delete command targets protected no_delete paths."""
    # Only check rm commands
    if not re.search(r'\brm\b', command):
        return None

    no_delete = patterns.get('paths', {}).get('no_delete', [])

    for protected in no_delete:
        # Check if protected path appears in rm command
        if protected in command:
            # Check if it's in allowlist
            if is_allowlisted(protected, patterns):
                continue
            return f"BLOCKED: Cannot delete protected path\nPath: '{protected}' is in no_delete protection"

    return None


def main():
    """Main hook entry point."""
    try:
        # Read hook input from stdin
        hook_input = sys.stdin.read()
        hook_data = json.loads(hook_input)

        tool_name = hook_data.get('tool_name', '')
        tool_input = hook_data.get('tool_input', {})

        # Load patterns
        patterns = load_patterns()
        if not patterns:
            # No patterns file, allow everything
            sys.exit(0)

        block_reason = None

        # Check Bash commands
        if tool_name == 'Bash':
            command = tool_input.get('command', '')

            # Check dangerous command patterns
            block_reason = check_bash_command(command, patterns)

            # Check delete protection if not already blocked
            if not block_reason:
                block_reason = check_delete_protection(command, patterns)

        # Check Write/Edit path protection
        elif tool_name in ['Write', 'Edit']:
            file_path = tool_input.get('file_path', '')
            block_reason = check_path_protection(file_path, tool_name, patterns)

        # Check Read for zero_access paths
        elif tool_name == 'Read':
            file_path = tool_input.get('file_path', '')
            # Only check zero_access for Read
            path_rules = patterns.get('paths', {})
            for protected in path_rules.get('zero_access', []):
                if protected in file_path and not is_allowlisted(file_path, patterns):
                    block_reason = f"BLOCKED: Path '{file_path}' is protected (zero_access)\nPattern matched: '{protected}'"
                    break

        if block_reason:
            print(block_reason, file=sys.stderr)
            sys.exit(2)  # Block execution

        sys.exit(0)  # Allow execution

    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse hook input: {e}", file=sys.stderr)
        sys.exit(0)  # Allow on parse error (fail open for safety)
    except Exception as e:
        print(f"ERROR: Damage control hook failed: {e}", file=sys.stderr)
        sys.exit(0)  # Allow on error (fail open)


if __name__ == '__main__':
    main()
