"""Verifier Agent implementation using Strands SDK."""

import os
from strands import Agent
from anthropic import Anthropic

from .system_prompt import VERIFIER_SYSTEM_PROMPT
from .tools import (
    verify_task_result,
    validate_output_schema,
    check_quality_metrics,
    release_payment,
    reject_and_refund,
    submit_verification_message,
)


def create_verifier_agent() -> Agent:
    """
    Create and configure the Verifier agent.

    Returns:
        Configured Strands Agent instance
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("VERIFIER_MODEL", "claude-3-7-sonnet-20250219")

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    client = Anthropic(api_key=api_key)

    tools = [
        verify_task_result,
        validate_output_schema,
        check_quality_metrics,
        release_payment,
        reject_and_refund,
        submit_verification_message,
    ]

    agent = Agent(
        client=client,
        model=model,
        system_prompt=VERIFIER_SYSTEM_PROMPT,
        tools=tools,
    )

    return agent


# Example usage
async def run_verifier_example():
    """Example of using the verifier agent."""
    agent = create_verifier_agent()

    request = """
    Verify task task-123 with the following criteria:
    - Required fields: ["summary", "insights", "data"]
    - Quality threshold: 80
    - Max errors: 2

    If verification passes, release payment payment-456.
    """

    result = await agent.run(request)
    print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_verifier_example())
