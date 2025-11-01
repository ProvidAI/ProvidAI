# Smart Contracts

## ERC8004Registry.sol

Solidity smart contract implementing the ERC-8004 Agent Discovery Protocol.

### Overview

The ERC8004Registry contract enables decentralized agent discovery in the Hedera marketplace:

- **Agent Registration**: Agents register with unique IDs and metadata URIs
- **Capability Indexing**: Agents tag themselves with capabilities for discovery
- **Metadata Storage**: Agent details stored on-chain, full metadata off-chain (IPFS/HTTP)
- **Discovery**: Query agents by capability

### Key Functions

#### Registration

```solidity
function registerAgent(string memory agentId, string memory metadataURI) public
```

Register a new agent with metadata URI pointing to full agent details.

#### Discovery

```solidity
function findAgentsByCapability(string memory capability) public view returns (string[] memory)
```

Find all agents offering a specific capability.

#### Capability Indexing

```solidity
function indexCapability(string memory agentId, string memory capability) public
```

Add a capability tag to your agent for discovery.

### Deployment

#### Hedera Testnet

```bash
# Using Hardhat
npx hardhat run scripts/deploy.js --network hedera-testnet

# Using Foundry
forge create --rpc-url https://testnet.hashio.io/api \
  --private-key $PRIVATE_KEY \
  src/ERC8004Registry.sol:ERC8004Registry
```

#### Hedera Mainnet

```bash
forge create --rpc-url https://mainnet.hashio.io/api \
  --private-key $PRIVATE_KEY \
  src/ERC8004Registry.sol:ERC8004Registry
```

### Agent Metadata Format

Agent metadata should be hosted on IPFS or HTTP and follow this structure:

```json
{
  "agent_id": "data-analyzer-001",
  "name": "Sales Data Analyzer",
  "description": "Advanced sales data analysis and forecasting",
  "capabilities": [
    "data-analysis",
    "forecasting",
    "trend-detection"
  ],
  "endpoint": "https://api.example.com/analyze",
  "pricing": {
    "model": "pay-per-use",
    "rate": "0.01 HBAR"
  },
  "owner": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "verified": true,
  "reputation_score": 8.5,
  "api_spec": {
    "method": "POST",
    "parameters": [
      {
        "name": "data",
        "type": "string",
        "description": "CSV data to analyze"
      },
      {
        "name": "analysis_type",
        "type": "string",
        "description": "Type of analysis (summary, trends, forecast)"
      }
    ],
    "auth_type": "bearer"
  }
}
```

### Integration with Python Backend

The Python backend uses Web3.py to interact with this contract:

```python
from shared.protocols import ERC8004Discovery

discovery = ERC8004Discovery(
    registry_address="0x...",
    rpc_url="https://testnet.hashio.io/api"
)

# Find agents
agents = await discovery.discover_agents("data-analysis")

# Register an agent
discovery.register_agent(metadata, "ipfs://QmXx...")
```

### Security Considerations

- Only agent owners can update their metadata
- Agent IDs must be unique
- Consider implementing agent verification/reputation system
- Metadata URIs should be immutable (use IPFS) or versioned

### Events

The contract emits events for indexing and monitoring:

- `AgentRegistered(agentId, metadataURI, owner, timestamp)`
- `AgentUpdated(agentId, metadataURI, timestamp)`
- `AgentDeactivated(agentId, timestamp)`
- `CapabilityIndexed(agentId, capability)`

### Future Enhancements

- Staking mechanism for reputation
- Agent verification badges
- Dispute resolution
- Payment escrow integration
- Multi-capability search
