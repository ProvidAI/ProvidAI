"""SQLAlchemy models for Hedera marketplace."""

from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .database import Base


class TaskStatus(str, enum.Enum):
    """Task status enum."""

    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class PaymentStatus(str, enum.Enum):
    """Payment status enum."""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Task(Base):
    """Task model."""

    __tablename__ = "tasks"

    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    created_by = Column(String)  # Agent ID
    assigned_to = Column(String, ForeignKey("agents.agent_id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result = Column(JSON, nullable=True)
    metadata = Column(JSON, nullable=True)

    # Relationships
    agent = relationship("Agent", back_populates="tasks")
    payments = relationship("Payment", back_populates="task")
    dynamic_tools = relationship("DynamicTool", back_populates="task")


class Agent(Base):
    """Agent model."""

    __tablename__ = "agents"

    agent_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    agent_type = Column(String)  # orchestrator, negotiator, executor, verifier
    description = Column(Text)
    capabilities = Column(JSON)  # List of capabilities
    hedera_account_id = Column(String, nullable=True)
    erc8004_metadata_uri = Column(String, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    metadata = Column(JSON, nullable=True)

    # Relationships
    tasks = relationship("Task", back_populates="agent")
    payments_sent = relationship(
        "Payment", foreign_keys="Payment.from_agent_id", back_populates="from_agent"
    )
    payments_received = relationship(
        "Payment", foreign_keys="Payment.to_agent_id", back_populates="to_agent"
    )


class Payment(Base):
    """Payment model."""

    __tablename__ = "payments"

    id = Column(String, primary_key=True)
    task_id = Column(String, ForeignKey("tasks.id"))
    from_agent_id = Column(String, ForeignKey("agents.agent_id"))
    to_agent_id = Column(String, ForeignKey("agents.agent_id"))
    amount = Column(Float, nullable=False)
    currency = Column(String, default="HBAR")
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_id = Column(String, nullable=True)  # Hedera transaction ID
    authorization_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=True)

    # Relationships
    task = relationship("Task", back_populates="payments")
    from_agent = relationship("Agent", foreign_keys=[from_agent_id], back_populates="payments_sent")
    to_agent = relationship(
        "Agent", foreign_keys=[to_agent_id], back_populates="payments_received"
    )


class DynamicTool(Base):
    """Dynamic tool created by executor agent."""

    __tablename__ = "dynamic_tools"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String, ForeignKey("tasks.id"))
    tool_name = Column(String, nullable=False)
    tool_description = Column(Text)
    tool_code = Column(Text, nullable=False)  # Python code
    file_path = Column(String)  # Path to generated file
    created_at = Column(DateTime, default=datetime.utcnow)
    used_count = Column(Integer, default=0)
    metadata = Column(JSON, nullable=True)

    # Relationships
    task = relationship("Task", back_populates="dynamic_tools")
