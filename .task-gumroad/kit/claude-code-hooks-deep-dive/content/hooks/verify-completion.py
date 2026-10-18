#!/usr/bin/env python3
"""
Verify Completion Hook

Evidence-first completion verification hook for autonomous agent workflows.
This script provides a definitive PASS/FAIL verdict for tasks.

The system defaults to FAIL. A PASS verdict is only issued when:
  1. All required checks pass (tests, linting, file existence, etc.)
  2. Any declared evidence artifacts are present and linked in the output.

Usage:
    # Verify Python project completion
    python verify-completion.py --type python

    # Verify specific task completion
    python verify-completion.py --type task-92

    # Verify with explicit evidence artifacts
    python verify-completion.py --type task-92 --evidence type=test_output,file_path=/tmp/test-output.txt

    # Verify with custom config
    python verify-completion.py --config /path/to/criteria.yaml --type python

    # Show detailed output
    python verify-completion.py --type python --verbose

Exit Codes:
    0 - PASS: All required checks passed (verdict proven)
    1 - FAIL: One or more required checks failed (verdict not proven)
    2 - ERROR: Configuration or runtime error

Evidence Types (--evidence type=<TYPE>,...):
    test_output      Command output proving tests pass
    screenshot       Image file proving UI state
    health_check     Service/endpoint health result
    metric_value     Numeric metric (coverage %, latency, etc.)
    diff             Before/after diff for config changes
    file_content     File content proof (word count, lines, etc.)
    command_output   Arbitrary command output captured as evidence

Integration with Meta-Loop/Ralph:
    The binary exit code allows autonomous loops to make definitive decisions:
    - Exit 0: Task is done (PASS), move to next task
    - Exit 1: Task not done (FAIL), continue working or report failure
    - Exit 2: System error, escalate to human

Example in prompt:
    Complete this task. When done, run:
        python .claude/hooks/verify-completion.py --type python

    Only report <promise>COMPLETE</promise> if verification exits 0 (PASS).
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add src to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.kernel.completion_verifier import CompletionVerifier  # noqa: E402


def _parse_evidence_arg(raw: str) -> Dict[str, Any]:
    """
    Parse a single --evidence argument into a dict.

    Accepts two formats:
      key=value,key=value,...   e.g.  type=test_output,file_path=/tmp/out.txt
      JSON string               e.g.  '{"type":"screenshot","file_path":"/tmp/ui.png"}'
    """
    raw = raw.strip()
    if raw.startswith('{'):
        return json.loads(raw)

    result: Dict[str, Any] = {}
    for part in raw.split(','):
        if '=' in part:
            k, v = part.split('=', 1)
            result[k.strip()] = v.strip()
    return result


def main():
    """Main entry point for verification hook."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Evidence-first completion verification for autonomous agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        '--config',
        default='.claude/completion-criteria.yaml',
        help='Path to completion criteria YAML file (default: .claude/completion-criteria.yaml)',
    )

    parser.add_argument(
        '--type',
        default='general',
        help='Project type to verify: python, typescript, go, rust, general, task-XX (default: general)',
    )

    parser.add_argument(
        '--cwd',
        default='.',
        help='Working directory for command execution (default: current directory)',
    )

    parser.add_argument(
        '--include-optional',
        action='store_true',
        help='Include optional checks in verification (warnings only, do not fail)',
    )

    parser.add_argument(
        '--evidence',
        action='append',
        dest='evidence',
        metavar='KEY=VALUE,...',
        help=(
            'Add an evidence artifact (repeatable). '
            'Format: type=<evidence_type>,file_path=<path> '
            'or type=<evidence_type>,command=<cmd> '
            'or type=<evidence_type>,note=<text>. '
            'Evidence types: test_output, screenshot, health_check, '
            'metric_value, diff, file_content, command_output.'
        ),
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Show detailed output including passed checks',
    )

    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Minimal output (PASS/FAIL only)',
    )

    args = parser.parse_args()

    # Resolve paths
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = Path.cwd() / config_path

    cwd = Path(args.cwd)
    if not cwd.is_absolute():
        cwd = Path.cwd() / cwd

    # Parse evidence arguments
    extra_evidence: Optional[List[Dict[str, Any]]] = None
    if args.evidence:
        extra_evidence = [_parse_evidence_arg(ev) for ev in args.evidence]

    try:
        # Load verifier
        verifier = CompletionVerifier.from_yaml(str(config_path))

        # Run verification (verdict defaults to FAIL inside verify())
        result = verifier.verify(
            project_type=args.type,
            cwd=str(cwd),
            include_optional=args.include_optional,
            extra_evidence=extra_evidence,
        )

        # Output results
        if args.quiet:
            # Minimal output for scripts — PASS/FAIL
            print(result.verdict())
        elif args.verbose:
            # Detailed output
            print(f"\n{'='*60}")
            print(f"Verification: {args.type}")
            print(f"{'='*60}\n")
            print(str(result))

            if result.warnings:
                print(f"\n{'='*60}")
                print("Warnings (Optional Checks):")
                print(f"{'='*60}")
                for warning in result.warnings:
                    print(f"  WARNING: {warning}")
        else:
            # Standard output
            if result.is_complete:
                print(f"PASS: {result.checks_passed}/{result.checks_run} required checks passed")
                if result.evidence_links:
                    print("Evidence:")
                    for link in result.evidence_links:
                        print(f"  - {link}")
            else:
                print(str(result))

                if result.warnings:
                    print(f"\nWarnings: {len(result.warnings)} optional check(s) failed")

        # Exit with appropriate code: 0=PASS, 1=FAIL, 2=ERROR
        sys.exit(0 if result.is_complete else 1)

    except FileNotFoundError as e:
        print(f"ERROR: Configuration file not found: {e}", file=sys.stderr)
        print(f"\nSearched for: {config_path}", file=sys.stderr)
        print(f"Current directory: {Path.cwd()}", file=sys.stderr)
        sys.exit(2)

    except KeyError as e:
        print(f"ERROR: Unknown project type: {args.type}", file=sys.stderr)
        print(f"\nAvailable types in config: {e}", file=sys.stderr)
        sys.exit(2)

    except Exception as e:
        print(f"ERROR: Verification failed: {e}", file=sys.stderr)

        if args.verbose:
            import traceback
            traceback.print_exc()

        sys.exit(2)


if __name__ == '__main__':
    main()
