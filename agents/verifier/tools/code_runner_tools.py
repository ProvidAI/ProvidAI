"""Code execution tools for Verifier agent."""

import subprocess
import tempfile
import os
from typing import Dict, Any, Optional
from pathlib import Path


async def run_verification_code(
    code: str,
    language: str = "python",
    timeout: int = 30,
    test_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run verification code to test task outputs.

    This allows the Verifier to write and execute code to validate results,
    perform statistical analysis, or run automated tests.

    Args:
        code: Code to execute
        language: Programming language (python, javascript, bash)
        timeout: Execution timeout in seconds
        test_data: Optional test data to make available to the code

    Returns:
        Execution results

    Example:
        # Verify data quality with Python code
        result = await run_verification_code(
            code='''
import json
import sys

data = json.loads(sys.argv[1])
completeness = len([x for x in data if x]) / len(data) * 100
print(f"Completeness: {completeness}%")
sys.exit(0 if completeness >= 95 else 1)
            ''',
            language="python",
            test_data={"results": [1, 2, 3, None, 5]}
        )
    """
    try:
        if language == "python":
            return await _run_python_code(code, timeout, test_data)
        elif language == "javascript":
            return await _run_javascript_code(code, timeout, test_data)
        elif language == "bash":
            return await _run_bash_code(code, timeout)
        else:
            return {
                "success": False,
                "error": f"Unsupported language: {language}",
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Code execution error: {str(e)}",
        }


async def _run_python_code(
    code: str, timeout: int, test_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute Python code."""
    import json

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        temp_file = f.name

    try:
        # Prepare arguments
        args = ["python", temp_file]
        if test_data:
            args.append(json.dumps(test_data))

        # Execute
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
        }
    finally:
        os.unlink(temp_file)


async def _run_javascript_code(
    code: str, timeout: int, test_data: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """Execute JavaScript code using Node.js."""
    import json

    with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
        if test_data:
            # Inject test data
            f.write(f"const testData = {json.dumps(test_data)};\n")
        f.write(code)
        temp_file = f.name

    try:
        result = subprocess.run(
            ["node", temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
        }
    finally:
        os.unlink(temp_file)


async def _run_bash_code(code: str, timeout: int) -> Dict[str, Any]:
    """Execute Bash code."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        f.write(code)
        temp_file = f.name

    try:
        # Make executable
        os.chmod(temp_file, 0o755)

        result = subprocess.run(
            ["bash", temp_file],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
        }
    finally:
        os.unlink(temp_file)


async def run_unit_tests(
    task_id: str,
    test_code: str,
    language: str = "python",
) -> Dict[str, Any]:
    """
    Run unit tests against task results.

    Args:
        task_id: Task ID to test
        test_code: Test code (pytest, jest, etc.)
        language: Test framework language

    Returns:
        Test results

    Example:
        result = await run_unit_tests(
            task_id="task-123",
            test_code='''
import pytest
from task_results import get_result

def test_completeness():
    result = get_result("task-123")
    assert "summary" in result
    assert "data" in result

def test_data_quality():
    result = get_result("task-123")
    assert len(result["data"]) > 0
            ''',
            language="python"
        )
    """
    from shared.database import SessionLocal, Task

    db = SessionLocal()
    try:
        # Get task results
        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {"success": False, "error": f"Task {task_id} not found"}

        result_data = task.result or {}

        # Create temporary test file with task results
        if language == "python":
            with tempfile.TemporaryDirectory() as tmpdir:
                # Write result data
                result_file = Path(tmpdir) / "task_results.py"
                result_file.write_text(f"""
import json

_result = {repr(result_data)}

def get_result(task_id):
    return _result
""")

                # Write test file
                test_file = Path(tmpdir) / "test_task.py"
                test_file.write_text(test_code)

                # Run pytest
                result = subprocess.run(
                    ["pytest", str(test_file), "-v"],
                    capture_output=True,
                    text=True,
                    cwd=tmpdir,
                    timeout=60,
                )

                return {
                    "success": result.returncode == 0,
                    "output": result.stdout,
                    "errors": result.stderr,
                    "passed": result.returncode == 0,
                }
        else:
            return {"success": False, "error": f"Unsupported language: {language}"}

    finally:
        db.close()


async def validate_code_output(
    expected_output: str,
    actual_output: str,
    comparison_type: str = "exact",
) -> Dict[str, Any]:
    """
    Validate code output against expected results.

    Args:
        expected_output: Expected output
        actual_output: Actual output from task
        comparison_type: Comparison method (exact, contains, regex, json)

    Returns:
        Validation result
    """
    import re
    import json

    try:
        if comparison_type == "exact":
            matches = expected_output.strip() == actual_output.strip()
        elif comparison_type == "contains":
            matches = expected_output in actual_output
        elif comparison_type == "regex":
            matches = re.search(expected_output, actual_output) is not None
        elif comparison_type == "json":
            # Compare as JSON objects
            expected_json = json.loads(expected_output)
            actual_json = json.loads(actual_output)
            matches = expected_json == actual_json
        else:
            return {
                "success": False,
                "error": f"Unknown comparison type: {comparison_type}",
            }

        return {
            "success": True,
            "matches": matches,
            "comparison_type": comparison_type,
            "message": "Output matches expected" if matches else "Output does not match",
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Validation error: {str(e)}",
        }
