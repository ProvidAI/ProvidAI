"""Negotiator Agent implementation using Strands SDK."""

import os
from strands import Agent
from anthropic import Anthropic

from .system_prompt import NEGOTIATOR_SYSTEM_PROMPT
from .tools import (
    search_agents_by_domain,
    search_agents_by_address,
    find_top_agents,
    get_agent_details_by_id,
    create_payment_request,
    authorize_payment,
    get_payment_status,
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
        search_agents_by_domain,
        search_agents_by_address,
        find_top_agents,
        get_agent_details_by_id,
        create_payment_request,
        authorize_payment,
        get_payment_status,
    ]

    agent = Agent(
        client=client,
        model=model,
        system_prompt=NEGOTIATOR_SYSTEM_PROMPT,
        tools=tools,
    )

    return agent
