"""HCS-10 coordination tools for Orchestrator."""

from typing import Dict, Any
import os

from shared.hedera import get_hedera_client
from shared.protocols import HCS10Coordinator


async def submit_coordination_message(
    task_id: str, message_type: str, payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Submit a coordination message to HCS-10 topic.

    Args:
        task_id: Task ID
        message_type: Message type (task_created, task_assigned, etc.)
        payload: Message payload

    Returns:
        Submission status
    """
    from shared.protocols.hcs10 import TaskMessage, MessageType
    from datetime import datetime

    # Get Hedera client
    hedera_client = get_hedera_client()

    # Create HCS-10 coordinator
    coordinator = HCS10Coordinator(hedera_client)

    # Create message
    message = TaskMessage(
        message_type=MessageType(message_type),
        task_id=task_id,
        agent_id="orchestrator",
        timestamp=datetime.utcnow().isoformat(),
        payload=payload,
    )

    # Submit message
    status = await coordinator.submit_task_message(message)

    return {
        "task_id": task_id,
        "message_type": message_type,
        "status": status,
        "timestamp": message.timestamp,
    }
