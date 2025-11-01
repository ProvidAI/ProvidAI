"""Agent-to-agent (A2A) payment messaging helpers."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Iterable, Optional, Union

A2A_PAYMENT_PROTOCOL_URI = "a2a://x402-payment/1.0"

DecimalLike = Union[Decimal, str, float, int]


def _now_iso() -> str:
    """Return the current UTC timestamp in ISO format."""

    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    """Generate a unique message identifier."""

    return str(uuid.uuid4())


def _serialize_amount(amount: DecimalLike) -> str:
    """Convert an amount into a canonical decimal string."""

    decimal_amount = amount if isinstance(amount, Decimal) else Decimal(str(amount))
    # Normalize without scientific notation while preserving fractional precision.
    return format(decimal_amount, "f")


def new_thread_id(task_id: str, payment_id: str) -> str:
    """Create a stable A2A thread identifier for a task/payment pair."""

    return f"a2a:{task_id}:{payment_id}"


@dataclass
class A2AMessage:
    """Canonical representation of an A2A message envelope."""

    id: str
    type: str
    from_agent: str
    to_agent: str
    thid: str
    timestamp: str
    body: Dict[str, Any]
    protocol: str = A2A_PAYMENT_PROTOCOL_URI

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serialisable dict representation."""

        return {
            "id": self.id,
            "protocol": self.protocol,
            "type": self.type,
            "from": self.from_agent,
            "to": self.to_agent,
            "thid": self.thid,
            "timestamp": self.timestamp,
            "body": self.body,
        }


def build_payment_proposal_message(
    *,
    payment_id: str,
    task_id: str,
    amount: DecimalLike,
    currency: str,
    from_agent: str,
    to_agent: str,
    verifier_addresses: Iterable[str],
    approvals_required: int,
    marketplace_fee_bps: int,
    verifier_fee_bps: int,
    thread_id: Optional[str] = None,
) -> A2AMessage:
    """Create an A2A payment proposal message."""

    thid = thread_id or new_thread_id(task_id, payment_id)
    body = {
        "payment_id": payment_id,
        "task_id": task_id,
        "amount": _serialize_amount(amount),
        "currency": currency,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "verifier_addresses": list(verifier_addresses),
        "approvals_required": approvals_required,
        "marketplace_fee_bps": marketplace_fee_bps,
        "verifier_fee_bps": verifier_fee_bps,
    }

    return A2AMessage(
        id=_new_id(),
        type="payment/proposal",
        from_agent=from_agent,
        to_agent=to_agent,
        thid=thid,
        timestamp=_now_iso(),
        body=body,
    )


def build_payment_authorized_message(
    *,
    payment_id: str,
    task_id: str,
    amount: DecimalLike,
    currency: str,
    from_agent: str,
    to_agent: str,
    transaction_id: str,
    thread_id: str,
) -> A2AMessage:
    """Create an A2A message signalling that escrow funding succeeded."""

    body = {
        "payment_id": payment_id,
        "task_id": task_id,
        "amount": _serialize_amount(amount),
        "currency": currency,
        "transaction_id": transaction_id,
        "status": "authorized",
    }

    return A2AMessage(
        id=_new_id(),
        type="payment/authorized",
        from_agent=from_agent,
        to_agent=to_agent,
        thid=thread_id,
        timestamp=_now_iso(),
        body=body,
    )


def build_payment_release_message(
    *,
    payment_id: str,
    task_id: str,
    amount: DecimalLike,
    currency: str,
    from_agent: str,
    to_agent: str,
    transaction_id: str,
    status: str,
    verification_notes: Optional[str],
    thread_id: str,
) -> A2AMessage:
    """Create an A2A message for successful payment release."""

    body = {
        "payment_id": payment_id,
        "task_id": task_id,
        "amount": _serialize_amount(amount),
        "currency": currency,
        "transaction_id": transaction_id,
        "status": status,
    }
    if verification_notes:
        body["verification_notes"] = verification_notes

    return A2AMessage(
        id=_new_id(),
        type="payment/released",
        from_agent=from_agent,
        to_agent=to_agent,
        thid=thread_id,
        timestamp=_now_iso(),
        body=body,
    )


def build_payment_refund_message(
    *,
    payment_id: str,
    task_id: str,
    amount: DecimalLike,
    currency: str,
    from_agent: str,
    to_agent: str,
    transaction_id: Optional[str],
    status: str,
    rejection_reason: str,
    thread_id: str,
) -> A2AMessage:
    """Create an A2A message for a rejected/refunded payment."""

    body: Dict[str, Any] = {
        "payment_id": payment_id,
        "task_id": task_id,
        "amount": _serialize_amount(amount),
        "currency": currency,
        "status": status,
        "rejection_reason": rejection_reason,
    }
    if transaction_id:
        body["transaction_id"] = transaction_id

    return A2AMessage(
        id=_new_id(),
        type="payment/refunded",
        from_agent=from_agent,
        to_agent=to_agent,
        thid=thread_id,
        timestamp=_now_iso(),
        body=body,
    )
