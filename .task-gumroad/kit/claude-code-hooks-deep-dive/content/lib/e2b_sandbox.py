#!/usr/bin/env python3
"""
e2b_sandbox.py - E2B Code Interpreter Sandbox Wrapper

Provides isolated code execution for trading agents and other Claude Code operations.

FEATURES:
- Sandboxed Python/JavaScript execution
- Automatic cleanup and timeout handling
- Integration with trading observability
- Result capture and logging

SECURITY: 2024-12-29
- All code runs in E2B's cloud sandbox (isolated from host)
- Automatic timeout prevents runaway execution
- Results sanitized before logging

USAGE:
    from e2b_sandbox import E2BSandbox, execute_code_safely

    # Quick execution
    result = execute_code_safely("print(2 + 2)")

    # With context manager
    with E2BSandbox() as sandbox:
        result = sandbox.run("import numpy as np; print(np.random.rand())")
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict

# E2B SDK
try:
    from e2b_code_interpreter import Sandbox
    E2B_AVAILABLE = True
except ImportError:
    E2B_AVAILABLE = False
    Sandbox = None

logger = logging.getLogger(__name__)

# Configuration
DEFAULT_TIMEOUT = 60  # seconds
MAX_OUTPUT_SIZE = 50000  # characters
HOOKS_DIR = Path(__file__).parent.parent
LOG_PATH = HOOKS_DIR / "sandbox.log"


@dataclass
class ExecutionResult:
    """Result of code execution in sandbox."""
    success: bool
    output: str = ""
    error: str = ""
    execution_time_ms: float = 0
    logs: List[str] = field(default_factory=list)
    artifacts: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


class E2BSandbox:
    """
    E2B Code Interpreter sandbox wrapper.

    Provides isolated execution environment for:
    - Trading strategy backtesting
    - Code validation before deployment
    - Data analysis in isolation
    - Safe experimentation
    """

    def __init__(
        self,
        timeout: int = DEFAULT_TIMEOUT,
        api_key: Optional[str] = None,
        template: str = "base"
    ):
        """
        Initialize E2B sandbox.

        Args:
            timeout: Execution timeout in seconds
            api_key: E2B API key (defaults to E2B_API_KEY env var)
            template: Sandbox template ("base", "python", "node")
        """
        if not E2B_AVAILABLE:
            raise ImportError(
                "E2B SDK not installed. Run: pip install e2b-code-interpreter"
            )

        self.timeout = timeout
        self.api_key = api_key or os.environ.get("E2B_API_KEY")
        self.template = template
        self.sandbox: Optional[Sandbox] = None
        self._start_time: Optional[datetime] = None

        if not self.api_key:
            raise ValueError(
                "E2B API key required. Set E2B_API_KEY environment variable "
                "or pass api_key parameter."
            )

    def __enter__(self) -> "E2BSandbox":
        """Context manager entry - create sandbox."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup sandbox."""
        self.stop()
        return False

    def start(self) -> bool:
        """Start the sandbox environment."""
        try:
            self._start_time = datetime.now()
            self.sandbox = Sandbox(api_key=self.api_key, timeout=self.timeout)
            logger.info(f"E2B sandbox started (template: {self.template})")
            return True
        except Exception as e:
            logger.error(f"Failed to start E2B sandbox: {e}")
            return False

    def stop(self):
        """Stop and cleanup the sandbox."""
        if self.sandbox:
            try:
                self.sandbox.kill()
                logger.info("E2B sandbox stopped")
            except Exception as e:
                logger.warning(f"Error stopping sandbox: {e}")
            finally:
                self.sandbox = None

    def run(
        self,
        code: str,
        language: str = "python",
        capture_output: bool = True
    ) -> ExecutionResult:
        """
        Execute code in the sandbox.

        Args:
            code: Code to execute
            language: Programming language ("python", "javascript")
            capture_output: Whether to capture stdout/stderr

        Returns:
            ExecutionResult with output, errors, and metadata
        """
        if not self.sandbox:
            return ExecutionResult(
                success=False,
                error="Sandbox not started. Call start() or use context manager."
            )

        start_time = datetime.now()
        logs = []
        artifacts = []

        try:
            # Execute code
            execution = self.sandbox.run_code(code)

            # Collect output
            output_parts = []
            error_parts = []

            # Process logs
            if hasattr(execution, 'logs') and execution.logs:
                for log in execution.logs:
                    if hasattr(log, 'line'):
                        logs.append(str(log.line))
                        if hasattr(log, 'stderr') and log.stderr:
                            error_parts.append(str(log.line))
                        else:
                            output_parts.append(str(log.line))

            # Process results
            if hasattr(execution, 'results') and execution.results:
                for result in execution.results:
                    if hasattr(result, 'text') and result.text:
                        output_parts.append(str(result.text))
                    if hasattr(result, 'formats') and result.formats:
                        artifacts.append({
                            "type": "result",
                            "formats": result.formats
                        })

            # Check for errors
            if hasattr(execution, 'error') and execution.error:
                error_parts.append(str(execution.error))

            output = "\n".join(output_parts)[:MAX_OUTPUT_SIZE]
            error = "\n".join(error_parts)[:MAX_OUTPUT_SIZE]

            execution_time = (datetime.now() - start_time).total_seconds() * 1000

            return ExecutionResult(
                success=not error,
                output=output,
                error=error,
                execution_time_ms=execution_time,
                logs=logs[:100],  # Limit log entries
                artifacts=artifacts[:10],  # Limit artifacts
                metadata={
                    "language": language,
                    "code_length": len(code),
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            error_msg = str(e)[:MAX_OUTPUT_SIZE]

            logger.error(f"Sandbox execution error: {error_msg}")

            return ExecutionResult(
                success=False,
                error=error_msg,
                execution_time_ms=execution_time,
                metadata={
                    "language": language,
                    "exception_type": type(e).__name__,
                    "timestamp": datetime.now().isoformat()
                }
            )

    def run_file(self, file_path: str) -> ExecutionResult:
        """Execute a file in the sandbox."""
        try:
            path = Path(file_path)
            if not path.exists():
                return ExecutionResult(
                    success=False,
                    error=f"File not found: {file_path}"
                )

            code = path.read_text()
            language = "python" if path.suffix == ".py" else "javascript"
            return self.run(code, language=language)

        except Exception as e:
            return ExecutionResult(
                success=False,
                error=f"Failed to read file: {e}"
            )

    def install_package(self, package: str) -> ExecutionResult:
        """Install a Python package in the sandbox."""
        return self.run(f"!pip install {package}")

    def upload_file(self, local_path: str, remote_path: str = "/tmp/") -> bool:
        """Upload a file to the sandbox."""
        if not self.sandbox:
            return False

        try:
            path = Path(local_path)
            content = path.read_bytes()
            self.sandbox.files.write(f"{remote_path}{path.name}", content)
            return True
        except Exception as e:
            logger.error(f"File upload failed: {e}")
            return False


def execute_code_safely(
    code: str,
    timeout: int = 30,
    language: str = "python"
) -> ExecutionResult:
    """
    Quick helper for one-off code execution.

    Args:
        code: Code to execute
        timeout: Max execution time in seconds
        language: Programming language

    Returns:
        ExecutionResult with execution details
    """
    api_key = os.environ.get("E2B_API_KEY")

    if not api_key:
        return ExecutionResult(
            success=False,
            error="E2B_API_KEY not set. Get a key at https://e2b.dev"
        )

    if not E2B_AVAILABLE:
        return ExecutionResult(
            success=False,
            error="E2B SDK not installed. Run: pip install e2b-code-interpreter"
        )

    try:
        with E2BSandbox(timeout=timeout) as sandbox:
            return sandbox.run(code, language=language)
    except Exception as e:
        return ExecutionResult(
            success=False,
            error=f"Sandbox error: {e}"
        )


def log_sandbox_event(
    event_type: str,
    code_snippet: str,
    result: ExecutionResult,
    agent: str = "unknown"
):
    """
    Log sandbox execution event for observability.

    Args:
        event_type: Type of sandbox operation
        code_snippet: First 200 chars of code
        result: ExecutionResult from execution
        agent: Agent identifier
    """
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "agent": agent,
            "code_preview": code_snippet[:200],
            "success": result.success,
            "execution_time_ms": result.execution_time_ms,
            "has_error": bool(result.error),
            "output_length": len(result.output)
        }

        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    except Exception as e:
        logger.warning(f"Failed to log sandbox event: {e}")


# Convenience functions for common patterns

def test_trading_strategy(strategy_code: str, test_data: Dict = None) -> ExecutionResult:
    """
    Test a trading strategy in isolation.

    Args:
        strategy_code: Python code implementing the strategy
        test_data: Optional test data dict

    Returns:
        ExecutionResult with strategy output
    """
    setup_code = """
import json
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

# Mock trading context
class MockPosition:
    def __init__(self, token: str, amount: float):
        self.token = token
        self.amount = amount

class MockContext:
    positions: List[MockPosition] = []
    balance: float = 10000.0

    def buy(self, token: str, amount: float):
        self.balance -= amount
        self.positions.append(MockPosition(token, amount))
        return {"status": "success", "token": token, "amount": amount}

    def sell(self, token: str, amount: float):
        self.balance += amount
        return {"status": "success", "token": token, "amount": amount}

ctx = MockContext()
"""

    data_setup = ""
    if test_data:
        data_setup = f"\ntest_data = {json.dumps(test_data)}\n"

    full_code = setup_code + data_setup + "\n" + strategy_code

    return execute_code_safely(full_code, timeout=60)


def validate_python_syntax(code: str) -> ExecutionResult:
    """
    Validate Python code syntax without executing.

    Args:
        code: Python code to validate

    Returns:
        ExecutionResult indicating if syntax is valid
    """
    validation_code = f'''
import ast

code = """{code}"""

try:
    ast.parse(code)
    print("VALID: Python syntax is correct")
except SyntaxError as e:
    print(f"INVALID: {{e}}")
'''

    return execute_code_safely(validation_code, timeout=10)


if __name__ == "__main__":
    # Test the module
    print("E2B Sandbox Module")
    print("=" * 40)

    if not os.environ.get("E2B_API_KEY"):
        print("\nE2B_API_KEY not set. Set it to test sandbox functionality.")
        print("Get a key at: https://e2b.dev")
    else:
        print("\nTesting sandbox execution...")
        result = execute_code_safely("print('Hello from E2B sandbox!')")
        print(f"Success: {result.success}")
        print(f"Output: {result.output}")
        if result.error:
            print(f"Error: {result.error}")
        print(f"Execution time: {result.execution_time_ms:.2f}ms")
