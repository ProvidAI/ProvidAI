# Dynamic Tools Directory

This directory contains **runtime-generated tools** created by the Executor agent.

## Purpose

The Executor agent uses **meta-tooling** to dynamically create custom Python tools for integrating with marketplace agents discovered via ERC-8004.

## How It Works

1. **Discovery**: Negotiator discovers an agent via ERC-8004
2. **Tool Generation**: Executor receives agent metadata and creates a Python tool
3. **Tool Loading**: Executor uses `load_tool` to load the generated Python module
4. **Execution**: The tool is called like any other Strands SDK tool

## Example Generated Tool

```python
# File: analyze_sales_data.py

async def analyze_sales_data(data: str, analysis_type: str, api_key: str = None) -> dict:
    """
    Call the discovered sales data analyzer agent.

    Args:
        data: CSV sales data
        analysis_type: Type of analysis (summary, trends, forecast)
        api_key: Optional API key for authentication

    Returns:
        Analysis results
    """
    import httpx

    endpoint = "https://sales-analyzer.example.com/api/analyze"

    async with httpx.AsyncClient() as client:
        response = await client.post(
            endpoint,
            json={"data": data, "type": analysis_type},
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {}
        )
        response.raise_for_status()
        return response.json()
```

## Tool Lifecycle

1. **Creation**: `create_dynamic_tool()` generates Python code
2. **Storage**: Tool saved to this directory + database record
3. **Loading**: `load_and_execute_tool()` imports and executes
4. **Tracking**: Usage count and metadata stored in database
5. **Cleanup**: Tools can be archived or deleted after task completion

## Template Structure

All generated tools follow this structure:

- **Imports**: Required libraries (httpx, json, etc.)
- **Function Signature**: Async function with typed parameters
- **Docstring**: Comprehensive documentation
- **Error Handling**: Try/except with structured error returns
- **API Call**: HTTP request to discovered agent
- **Response**: Structured return dictionary

## Security Notes

- Tools are generated from trusted ERC-8004 metadata
- API keys handled securely via parameters
- All tools run in the same process context
- Consider sandboxing for untrusted agents

## Files

- `__init__.py`: Package marker
- `README.md`: This file
- `*.py`: Dynamically generated tool modules
