"""HCS-10 Coordination Protocol implementation."""

import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from hedera import TopicId


class MessageType(str, Enum):
    """HCS-10 message types."""

    TASK_CREATED = "task_created"
    TASK_ASSIGNED = "task_assigned"
    TASK_PROGRESS = "task_progress"
    TASK_COMPLETED = "task_completed"
    TOOL_CREATED = "tool_created"
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_COMPLETED = "payment_completed"


@dataclass
class TaskMessage:
    """HCS-10 task coordination message."""

    message_type: MessageType
    task_id: str
    agent_id: str
    timestamp: str
    payload: Dict[str, Any]
    sequence_number: Optional[int] = None

    def to_json(self) -> str:
        """Serialize to JSON for HCS submission."""
        data = asdict(self)
        data["message_type"] = self.message_type.value
        return json.dumps(data)

    @classmethod
    def from_json(cls, json_str: str) -> "TaskMessage":
        """Deserialize from JSON."""
        data = json.loads(json_str)
        data["message_type"] = MessageType(data["message_type"])
        return cls(**data)


class HCS10Coordinator:
    """HCS-10 Coordination Protocol for multi-agent tasks."""

    def __init__(self, hedera_client, topic_id: Optional[TopicId] = None):
        """
        Initialize HCS-10 coordinator.

        Args:
            hedera_client: HederaClientWrapper instance
            topic_id: Optional specific topic ID
        """
        from shared.hedera.client import HederaClientWrapper

        self.hedera_client: HederaClientWrapper = hedera_client
        self.topic_id = topic_id or hedera_client.topic_id

        if self.topic_id is None:
            raise ValueError("No topic ID available. Create a topic first.")

    async def submit_task_message(self, message: TaskMessage) -> str:
        """
        Submit a task coordination message to HCS.

        Args:
            message: TaskMessage to submit

        Returns:
            Transaction status
        """
        json_message = message.to_json()
        return await self.hedera_client.submit_message(json_message, self.topic_id)

    async def create_task(self, task_id: str, agent_id: str, task_data: Dict[str, Any]) -> str:
        """Create a new task."""
        message = TaskMessage(
            message_type=MessageType.TASK_CREATED,
            task_id=task_id,
            agent_id=agent_id,
            timestamp=datetime.utcnow().isoformat(),
            payload=task_data,
        )
        return await self.submit_task_message(message)

    async def assign_task(
        self, task_id: str, from_agent: str, to_agent: str, assignment_data: Dict[str, Any]
    ) -> str:
        """Assign task to another agent."""
        message = TaskMessage(
            message_type=MessageType.TASK_ASSIGNED,
            task_id=task_id,
            agent_id=from_agent,
            timestamp=datetime.utcnow().isoformat(),
            payload={"assigned_to": to_agent, **assignment_data},
        )
        return await self.submit_task_message(message)

    async def update_progress(
        self, task_id: str, agent_id: str, progress_data: Dict[str, Any]
    ) -> str:
        """Update task progress."""
        message = TaskMessage(
            message_type=MessageType.TASK_PROGRESS,
            task_id=task_id,
            agent_id=agent_id,
            timestamp=datetime.utcnow().isoformat(),
            payload=progress_data,
        )
        return await self.submit_task_message(message)

    async def complete_task(
        self, task_id: str, agent_id: str, result_data: Dict[str, Any]
    ) -> str:
        """Mark task as completed."""
        message = TaskMessage(
            message_type=MessageType.TASK_COMPLETED,
            task_id=task_id,
            agent_id=agent_id,
            timestamp=datetime.utcnow().isoformat(),
            payload=result_data,
        )
        return await self.submit_task_message(message)

    async def notify_tool_creation(
        self, task_id: str, agent_id: str, tool_info: Dict[str, Any]
    ) -> str:
        """Notify that a dynamic tool was created."""
        message = TaskMessage(
            message_type=MessageType.TOOL_CREATED,
            task_id=task_id,
            agent_id=agent_id,
            timestamp=datetime.utcnow().isoformat(),
            payload=tool_info,
        )
        return await self.submit_task_message(message)

    async def notify_payment(
        self, task_id: str, agent_id: str, payment_data: Dict[str, Any], completed: bool = False
    ) -> str:
        """Notify payment initiation or completion."""
        message_type = (
            MessageType.PAYMENT_COMPLETED if completed else MessageType.PAYMENT_INITIATED
        )
        message = TaskMessage(
            message_type=message_type,
            task_id=task_id,
            agent_id=agent_id,
            timestamp=datetime.utcnow().isoformat(),
            payload=payment_data,
        )
        return await self.submit_task_message(message)
