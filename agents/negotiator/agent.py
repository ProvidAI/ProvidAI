"""Negotiator Agent implementation using Strands SDK."""

import os
from strands import Agent
from anthropic import Anthropic

from .system_prompt import NEGOTIATOR_SYSTEM_PROMPT
from .tools import (
    discover_agents_by_capability,
    get_agent_details,
    evaluate_agent_pricing,
    create_payment_request,
    authorize_payment,
    get_payment_status,
    submit_negotiation_message,
)


def create_negotiator_agent() -> Agent:
    """
    Create and configure the Negotiator agent.

    Returns:
        Configured Strands Agent instance
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("NEGOTIATOR_MODEL", "claude-3-7-sonnet-20250219")

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    client = Anthropic(api_key=api_key)

    tools = [
        discover_agents_by_capability,
        get_agent_details,
        evaluate_agent_pricing,
        create_payment_request,
        authorize_payment,
        get_payment_status,
        submit_negotiation_message,
    ]

    agent = Agent(
        client=client,
        model=model,
        system_prompt=NEGOTIATOR_SYSTEM_PROMPT,
        tools=tools,
    )

    return agent


# Example usage
async def run_negotiator_example():
    """Example of using the negotiator agent."""
    agent = create_negotiator_agent()

    request = """
    Find a data analysis agent in the marketplace.
    Evaluate their pricing and set up payment authorization for 0.5 HBAR.
    """

    result = await agent.run(request)
    print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_negotiator_example())
