"""x402 payment tools for Negotiator."""

import os
import uuid
from typing import Dict, Any
from decimal import Decimal

from shared.hedera import get_hedera_client
from shared.protocols import X402Payment, PaymentRequest
from shared.database import SessionLocal, Payment
from shared.database.models import PaymentStatus as DBPaymentStatus


async def create_payment_request(
    task_id: str,
    from_agent_id: str,
    to_agent_id: str,
    to_hedera_account: str,
    amount: float,
    description: str = "",
) -> Dict[str, Any]:
    """
    Create an x402 payment request.

    Args:
        task_id: Associated task ID
        from_agent_id: Paying agent ID
        to_agent_id: Receiving agent ID
        to_hedera_account: Hedera account ID of receiving agent
        amount: Payment amount in HBAR
        description: Payment description

    Returns:
        Payment request details
    """
    db = SessionLocal()
    try:
        payment_id = str(uuid.uuid4())
        from_account = os.getenv("HEDERA_ACCOUNT_ID")

        if not from_account:
            raise ValueError("HEDERA_ACCOUNT_ID not configured")

        # Create payment record
        payment = Payment(
            id=payment_id,
            task_id=task_id,
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            amount=amount,
            currency="HBAR",
            status=DBPaymentStatus.PENDING,
            metadata={"to_hedera_account": to_hedera_account, "description": description},
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        return {
            "payment_id": payment_id,
            "task_id": task_id,
            "from_agent": from_agent_id,
            "to_agent": to_agent_id,
            "amount": amount,
            "currency": "HBAR",
            "status": "pending",
            "description": description,
        }
    finally:
        db.close()


async def authorize_payment(payment_id: str) -> Dict[str, Any]:
    """
    Authorize a payment (escrow pattern).

    This marks the payment as authorized and ready for release pending verification.

    Args:
        payment_id: Payment ID to authorize

    Returns:
        Authorization details
    """
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()

        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        # Get x402 payment handler
        hedera_client = get_hedera_client()
        x402 = X402Payment(hedera_client)

        # Create payment request object
        payment_request = PaymentRequest(
            payment_id=payment_id,
            from_account=os.getenv("HEDERA_ACCOUNT_ID", ""),
            to_account=payment.metadata.get("to_hedera_account", ""),
            amount=Decimal(str(payment.amount)),
            description=payment.metadata.get("description", ""),
        )

        # Authorize (for now, just generates authorization ID)
        auth_id = await x402.authorize_payment(payment_request)

        # Update payment record
        payment.authorization_id = auth_id
        payment.status = DBPaymentStatus.AUTHORIZED

        db.commit()
        db.refresh(payment)

        return {
            "payment_id": payment_id,
            "authorization_id": auth_id,
            "status": "authorized",
            "message": "Payment authorized. Waiting for verification to release funds.",
        }
    finally:
        db.close()


async def get_payment_status(payment_id: str) -> Dict[str, Any]:
    """
    Get current payment status.

    Args:
        payment_id: Payment ID

    Returns:
        Payment status and details
    """
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()

        if not payment:
            raise ValueError(f"Payment {payment_id} not found")

        return {
            "payment_id": payment.id,
            "task_id": payment.task_id,
            "status": payment.status.value,
            "amount": payment.amount,
            "currency": payment.currency,
            "transaction_id": payment.transaction_id,
            "authorization_id": payment.authorization_id,
            "created_at": payment.created_at.isoformat(),
            "completed_at": payment.completed_at.isoformat() if payment.completed_at else None,
        }
    finally:
        db.close()
