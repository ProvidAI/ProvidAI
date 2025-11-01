"""HCS-10 coordination tools for Verifier."""

from typing import Dict, Any
from datetime import datetime

from shared.hedera import get_hedera_client
from shared.protocols import HCS10Coordinator
from shared.protocols.hcs10 import TaskMessage, MessageType


async def submit_verification_message(
    task_id: str, message_type: str, payload: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Submit a verification message to HCS-10 topic.

    Args:
        task_id: Task ID
        message_type: Message type (e.g., "task_completed", "payment_completed")
        payload: Message payload with verification details

    Returns:
        Submission status
    """
    hedera_client = get_hedera_client()
    coordinator = HCS10Coordinator(hedera_client)

    message = TaskMessage(
        message_type=MessageType(message_type),
        task_id=task_id,
        agent_id="verifier",
        timestamp=datetime.utcnow().isoformat(),
        payload=payload,
    )

    status = await coordinator.submit_task_message(message)

    return {
        "task_id": task_id,
        "message_type": message_type,
        "status": status,
        "timestamp": message.timestamp,
    }
