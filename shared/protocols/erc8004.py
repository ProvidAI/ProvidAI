"""ERC-8004 Agent Discovery Protocol implementation."""

import json
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
from web3 import Web3
from eth_account import Account
import httpx


@dataclass
class AgentMetadata:
    """Agent metadata following ERC-8004 standard."""

    agent_id: str
    name: str
    description: str
    capabilities: List[str]
    endpoint: str
    pricing: Dict[str, Any]  # e.g., {"model": "pay-per-use", "rate": "0.01 HBAR"}
    owner: str
    verified: bool = False
    reputation_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentMetadata":
        """Create from dictionary."""
        return cls(**data)


class ERC8004Discovery:
    """ERC-8004 Agent Discovery and Registration."""

    def __init__(self, registry_address: str, rpc_url: str, private_key: Optional[str] = None):
        """
        Initialize ERC-8004 discovery client.

        Args:
            registry_address: Address of the ERC-8004 registry contract
            rpc_url: RPC endpoint URL
            private_key: Optional private key for transactions
        """
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.registry_address = Web3.to_checksum_address(registry_address)

        if private_key:
            self.account = Account.from_key(private_key)
        else:
            self.account = None

        # ERC-8004 Registry ABI (simplified)
        self.registry_abi = [
            {
                "inputs": [
                    {"name": "agentId", "type": "string"},
                    {"name": "metadataURI", "type": "string"},
                ],
                "name": "registerAgent",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function",
            },
            {
                "inputs": [{"name": "agentId", "type": "string"}],
                "name": "getAgent",
                "outputs": [{"name": "metadataURI", "type": "string"}],
                "stateMutability": "view",
                "type": "function",
            },
            {
                "inputs": [{"name": "capability", "type": "string"}],
                "name": "findAgentsByCapability",
                "outputs": [{"name": "agentIds", "type": "string[]"}],
                "stateMutability": "view",
                "type": "function",
            },
        ]

        self.contract = self.w3.eth.contract(
            address=self.registry_address, abi=self.registry_abi
        )

    async def discover_agents(self, capability: str) -> List[AgentMetadata]:
        """
        Discover agents by capability.

        Args:
            capability: Capability to search for (e.g., "data-analysis", "image-generation")

        Returns:
            List of agent metadata matching the capability
        """
        try:
            # Call contract to get agent IDs
            agent_ids = self.contract.functions.findAgentsByCapability(capability).call()

            # Fetch metadata for each agent
            agents = []
            async with httpx.AsyncClient() as client:
                for agent_id in agent_ids:
                    metadata = await self._fetch_agent_metadata(agent_id, client)
                    if metadata:
                        agents.append(metadata)

            return agents
        except Exception as e:
            print(f"Error discovering agents: {e}")
            return []

    async def _fetch_agent_metadata(
        self, agent_id: str, client: httpx.AsyncClient
    ) -> Optional[AgentMetadata]:
        """Fetch agent metadata from contract and resolve URI."""
        try:
            # Get metadata URI from contract
            metadata_uri = self.contract.functions.getAgent(agent_id).call()

            if not metadata_uri:
                return None

            # Fetch metadata from URI (IPFS, HTTP, etc.)
            if metadata_uri.startswith("ipfs://"):
                # Convert IPFS URI to HTTP gateway
                metadata_uri = metadata_uri.replace("ipfs://", "https://ipfs.io/ipfs/")

            response = await client.get(metadata_uri, timeout=10.0)
            response.raise_for_status()

            metadata_dict = response.json()
            return AgentMetadata.from_dict(metadata_dict)

        except Exception as e:
            print(f"Error fetching metadata for {agent_id}: {e}")
            return None

    def register_agent(self, metadata: AgentMetadata, metadata_uri: str) -> str:
        """
        Register an agent in the ERC-8004 registry.

        Args:
            metadata: Agent metadata
            metadata_uri: URI where metadata is hosted (IPFS, HTTP, etc.)

        Returns:
            Transaction hash
        """
        if not self.account:
            raise ValueError("Private key required for registration")

        # Build transaction
        transaction = self.contract.functions.registerAgent(
            metadata.agent_id, metadata_uri
        ).build_transaction(
            {
                "from": self.account.address,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "gas": 200000,
                "gasPrice": self.w3.eth.gas_price,
            }
        )

        # Sign and send
        signed_txn = self.account.sign_transaction(transaction)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)

        return tx_hash.hex()

    async def get_agent_by_id(self, agent_id: str) -> Optional[AgentMetadata]:
        """Get agent metadata by ID."""
        async with httpx.AsyncClient() as client:
            return await self._fetch_agent_metadata(agent_id, client)
