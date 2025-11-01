"""Execution utilities for Executor agent."""

import subprocess
from typing import Dict, Any


async def execute_shell_command(command: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Execute a shell command.

    Args:
        command: Shell command to execute
        timeout: Timeout in seconds

    Returns:
        Command execution result
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
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
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Command timed out after {timeout} seconds",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


async def get_tool_template(template_type: str = "basic") -> Dict[str, Any]:
    """
    Get a template for creating dynamic tools.

    Args:
        template_type: Type of template (basic, authenticated, streaming)

    Returns:
        Tool template code and documentation
    """
    templates = {
        "basic": '''
async def {tool_name}(input_data: str) -> Dict[str, Any]:
    """
    Basic tool template.

    Args:
        input_data: Input data

    Returns:
        Result dictionary
    """
    import httpx

    endpoint = "{endpoint_url}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            endpoint,
            json={"data": input_data}
        )
        response.raise_for_status()
        return response.json()
''',
        "authenticated": '''
async def {tool_name}(input_data: str, api_key: str) -> Dict[str, Any]:
    """
    Authenticated tool template.

    Args:
        input_data: Input data
        api_key: API authentication key

    Returns:
        Result dictionary
    """
    import httpx

    endpoint = "{endpoint_url}"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            endpoint,
            json={"data": input_data},
            headers={"Authorization": f"Bearer {api_key}"}
        )
        response.raise_for_status()
        return response.json()
''',
        "streaming": '''
async def {tool_name}(input_data: str) -> Dict[str, Any]:
    """
    Streaming tool template.

    Args:
        input_data: Input data

    Returns:
        Streamed results
    """
    import httpx

    endpoint = "{endpoint_url}"
    results = []

    async with httpx.AsyncClient() as client:
        async with client.stream("POST", endpoint, json={"data": input_data}) as response:
            response.raise_for_status()
            async for chunk in response.aiter_text():
                results.append(chunk)

    return {"chunks": results}
''',
    }

    template = templates.get(template_type, templates["basic"])

    return {
        "template_type": template_type,
        "template_code": template,
        "usage": "Replace {tool_name} and {endpoint_url} with actual values",
    }
