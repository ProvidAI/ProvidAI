"""ERC-8004 discovery tools for Negotiator."""

import os
from typing import List, Dict, Any

from shared.protocols import ERC8004Discovery, AgentMetadata


async def discover_agents_by_capability(capability: str) -> List[Dict[str, Any]]:
    """
    Discover marketplace agents by capability using ERC-8004.

    Args:
        capability: Capability to search for (e.g., "data-analysis", "image-generation", "code-review")

    Returns:
        List of discovered agents with their metadata

    Example:
        agents = await discover_agents_by_capability("data-analysis")
        # Returns: [{"agent_id": "...", "name": "...", "capabilities": [...], ...}]
    """
    # Get ERC-8004 configuration
    registry_address = os.getenv("ERC8004_REGISTRY_ADDRESS")
    rpc_url = os.getenv("ERC8004_RPC_URL", "https://testnet.hashio.io/api")

    if not registry_address:
        raise ValueError("ERC8004_REGISTRY_ADDRESS not configured")

    # Create discovery client
    discovery = ERC8004Discovery(registry_address=registry_address, rpc_url=rpc_url)

    # Discover agents
    agents = await discovery.discover_agents(capability)

    # Convert to dict format
    return [agent.to_dict() for agent in agents]


async def get_agent_details(agent_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific agent.

    Args:
        agent_id: Agent ID to lookup

    Returns:
        Agent metadata including capabilities, pricing, and reputation
    """
    registry_address = os.getenv("ERC8004_REGISTRY_ADDRESS")
    rpc_url = os.getenv("ERC8004_RPC_URL", "https://testnet.hashio.io/api")

    if not registry_address:
        raise ValueError("ERC8004_REGISTRY_ADDRESS not configured")

    discovery = ERC8004Discovery(registry_address=registry_address, rpc_url=rpc_url)

    agent = await discovery.get_agent_by_id(agent_id)

    if agent is None:
        raise ValueError(f"Agent {agent_id} not found")

    return agent.to_dict()


async def evaluate_agent_pricing(agents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate and compare pricing for multiple agents.

    Args:
        agents: List of agent metadata dictionaries

    Returns:
        Pricing analysis with recommendations

    Example:
        analysis = await evaluate_agent_pricing([agent1, agent2, agent3])
        # Returns: {
        #     "best_value": {"agent_id": "...", "score": 8.5, ...},
        #     "lowest_price": {"agent_id": "...", "price": 0.01, ...},
        #     "highest_reputation": {"agent_id": "...", "reputation": 9.2, ...}
        # }
    """
    if not agents:
        return {"error": "No agents to evaluate"}

    # Parse pricing from agents
    pricing_data = []
    for agent in agents:
        pricing = agent.get("pricing", {})
        rate = float(pricing.get("rate", "0").split()[0])  # Extract numeric value
        reputation = agent.get("reputation_score", 0.0)

        pricing_data.append(
            {
                "agent_id": agent["agent_id"],
                "name": agent["name"],
                "rate": rate,
                "reputation": reputation,
                "value_score": (reputation * 10) - rate,  # Simple value calculation
            }
        )

    # Sort by different criteria
    best_value = max(pricing_data, key=lambda x: x["value_score"])
    lowest_price = min(pricing_data, key=lambda x: x["rate"])
    highest_reputation = max(pricing_data, key=lambda x: x["reputation"])

    return {
        "total_agents": len(agents),
        "best_value": best_value,
        "lowest_price": lowest_price,
        "highest_reputation": highest_reputation,
        "all_options": pricing_data,
    }
