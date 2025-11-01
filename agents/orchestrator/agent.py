"""Orchestrator Agent implementation using Strands SDK."""

import os
from strands import Agent
from anthropic import Anthropic

from .system_prompt import ORCHESTRATOR_SYSTEM_PROMPT
from .tools import (
    create_task,
    update_task_status,
    get_task,
    create_todo_list,
    update_todo_item,
    submit_coordination_message,
)


def create_orchestrator_agent() -> Agent:
    """
    Create and configure the Orchestrator agent.

    Returns:
        Configured Strands Agent instance
    """
    # Get API key and model from environment
    api_key = os.getenv("ANTHROPIC_API_KEY")
    model = os.getenv("ORCHESTRATOR_MODEL", "claude-3-7-sonnet-20250219")

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not set")

    # Create Anthropic client
    client = Anthropic(api_key=api_key)

    # Define tools for the orchestrator
    tools = [
        create_task,
        update_task_status,
        get_task,
        create_todo_list,
        update_todo_item,
        submit_coordination_message,
    ]

    # Create agent with Strands SDK
    agent = Agent(
        client=client,
        model=model,
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        tools=tools,
    )

    return agent


# Example usage
async def run_orchestrator_example():
    """Example of using the orchestrator agent."""
    agent = create_orchestrator_agent()

    # Example request
    request = """
    I need to analyze sales data from our marketplace.
    Please find an agent that can perform data analysis,
    integrate with it, and generate a report.
    """

    # Run the agent
    result = await agent.run(request)
    print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(run_orchestrator_example())
