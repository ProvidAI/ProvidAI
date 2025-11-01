"""Orchestrator Agent implementation using Strands SDK."""

import os

from anthropic import Anthropic
from strands import Agent

from .system_prompt import ORCHESTRATOR_SYSTEM_PROMPT
from .tools import (
    create_task,
    create_todo_list,
    executor_agent,
    get_task,
    negotiator_agent,
    update_task_status,
    update_todo_item,
    verifier_agent,
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
        negotiator_agent,
        executor_agent,
        verifier_agent,
    ]

    # Create agent with Strands SDK
    agent = Agent(
        client=client,
        model=model,
        system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
        tools=tools,
    )

    return agent
