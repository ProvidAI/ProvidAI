// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title ERC8004Registry
 * @dev Agent discovery and registration following ERC-8004 standard
 *
 * This contract allows agents to register their metadata and capabilities,
 * enabling discovery by potential clients.
 */
contract ERC8004Registry {
    struct AgentRegistration {
        string agentId;
        string metadataURI;  // IPFS or HTTP URI to agent metadata
        address owner;
        uint256 registeredAt;
        bool active;
    }

    // Mapping from agent ID to registration
    mapping(string => AgentRegistration) public agents;

    // Mapping from capability to list of agent IDs
    mapping(string => string[]) public capabilityIndex;

    // List of all registered agent IDs
    string[] public allAgentIds;

    // Events
    event AgentRegistered(
        string indexed agentId,
        string metadataURI,
        address indexed owner,
        uint256 timestamp
    );

    event AgentUpdated(
        string indexed agentId,
        string metadataURI,
        uint256 timestamp
    );

    event AgentDeactivated(
        string indexed agentId,
        uint256 timestamp
    );

    event CapabilityIndexed(
        string indexed agentId,
        string capability
    );

    /**
     * @dev Register a new agent
     * @param agentId Unique agent identifier
     * @param metadataURI URI pointing to agent metadata (IPFS, HTTP, etc.)
     */
    function registerAgent(
        string memory agentId,
        string memory metadataURI
    ) public {
        require(bytes(agentId).length > 0, "Agent ID cannot be empty");
        require(bytes(metadataURI).length > 0, "Metadata URI cannot be empty");
        require(agents[agentId].owner == address(0), "Agent already registered");

        agents[agentId] = AgentRegistration({
            agentId: agentId,
            metadataURI: metadataURI,
            owner: msg.sender,
            registeredAt: block.timestamp,
            active: true
        });

        allAgentIds.push(agentId);

        emit AgentRegistered(agentId, metadataURI, msg.sender, block.timestamp);
    }

    /**
     * @dev Update agent metadata URI
     * @param agentId Agent identifier
     * @param metadataURI New metadata URI
     */
    function updateAgent(
        string memory agentId,
        string memory metadataURI
    ) public {
        require(agents[agentId].owner == msg.sender, "Not agent owner");
        require(agents[agentId].active, "Agent not active");

        agents[agentId].metadataURI = metadataURI;

        emit AgentUpdated(agentId, metadataURI, block.timestamp);
    }

    /**
     * @dev Deactivate an agent
     * @param agentId Agent identifier
     */
    function deactivateAgent(string memory agentId) public {
        require(agents[agentId].owner == msg.sender, "Not agent owner");
        require(agents[agentId].active, "Agent already inactive");

        agents[agentId].active = false;

        emit AgentDeactivated(agentId, block.timestamp);
    }

    /**
     * @dev Index agent capability for discovery
     * @param agentId Agent identifier
     * @param capability Capability string (e.g., "data-analysis", "image-generation")
     */
    function indexCapability(
        string memory agentId,
        string memory capability
    ) public {
        require(agents[agentId].owner == msg.sender, "Not agent owner");
        require(agents[agentId].active, "Agent not active");

        capabilityIndex[capability].push(agentId);

        emit CapabilityIndexed(agentId, capability);
    }

    /**
     * @dev Get agent metadata URI
     * @param agentId Agent identifier
     * @return Metadata URI
     */
    function getAgent(string memory agentId) public view returns (string memory) {
        require(agents[agentId].active, "Agent not found or inactive");
        return agents[agentId].metadataURI;
    }

    /**
     * @dev Find agents by capability
     * @param capability Capability to search for
     * @return Array of agent IDs with the capability
     */
    function findAgentsByCapability(
        string memory capability
    ) public view returns (string[] memory) {
        return capabilityIndex[capability];
    }

    /**
     * @dev Get total number of registered agents
     * @return Number of agents
     */
    function getTotalAgents() public view returns (uint256) {
        return allAgentIds.length;
    }

    /**
     * @dev Get all agent IDs (paginated)
     * @param offset Starting index
     * @param limit Maximum number of results
     * @return Array of agent IDs
     */
    function getAllAgents(
        uint256 offset,
        uint256 limit
    ) public view returns (string[] memory) {
        require(offset < allAgentIds.length, "Offset out of bounds");

        uint256 end = offset + limit;
        if (end > allAgentIds.length) {
            end = allAgentIds.length;
        }

        string[] memory result = new string[](end - offset);
        for (uint256 i = offset; i < end; i++) {
            result[i - offset] = allAgentIds[i];
        }

        return result;
    }

    /**
     * @dev Get agent registration details
     * @param agentId Agent identifier
     * @return Agent registration struct
     */
    function getAgentDetails(
        string memory agentId
    ) public view returns (AgentRegistration memory) {
        return agents[agentId];
    }
}
