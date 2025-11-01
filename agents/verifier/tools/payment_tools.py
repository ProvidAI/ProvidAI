"""Payment release tools for Verifier agent."""

import os
from typing import Dict, Any
from datetime import datetime
from decimal import Decimal

from shared.hedera import get_hedera_client
from shared.protocols import X402Payment, PaymentRequest
from shared.database import SessionLocal, Payment
from shared.database.models import PaymentStatus as DBPaymentStatus


async def release_payment(payment_id: str, verification_notes: str = "") -> Dict[str, Any]:
    """
    Release an authorized payment after successful verification.

    Args:
        payment_id: Payment ID to release
        verification_notes: Optional notes about verification

    Returns:
        Payment release result
    """
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()

        if not payment:
            return {"success": False, "error": f"Payment {payment_id} not found"}

        if payment.status != DBPaymentStatus.AUTHORIZED:
            return {
                "success": False,
                "error": f"Payment not authorized. Current status: {payment.status.value}",
            }

        # Get x402 payment handler
        hedera_client = get_hedera_client()
        x402 = X402Payment(hedera_client)

        # Create payment request
        payment_request = PaymentRequest(
            payment_id=payment_id,
            from_account=os.getenv("HEDERA_ACCOUNT_ID", ""),
            to_account=payment.metadata.get("to_hedera_account", ""),
            amount=Decimal(str(payment.amount)),
            description=payment.metadata.get("description", ""),
        )

        # Release payment
        receipt = await x402.release_payment(payment.authorization_id, payment_request)

        # Update payment record
        payment.status = DBPaymentStatus(receipt.status.value)
        payment.transaction_id = receipt.transaction_id
        payment.completed_at = datetime.utcnow()

        if payment.metadata is None:
            payment.metadata = {}
        payment.metadata["verification_notes"] = verification_notes
        payment.metadata["receipt"] = {
            "transaction_id": receipt.transaction_id,
            "timestamp": receipt.timestamp,
        }

        db.commit()
        db.refresh(payment)

        return {
            "success": True,
            "payment_id": payment_id,
            "transaction_id": receipt.transaction_id,
            "status": payment.status.value,
            "amount": payment.amount,
            "currency": payment.currency,
            "message": "Payment released successfully",
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to release payment: {str(e)}",
        }
    finally:
        db.close()


async def reject_and_refund(
    payment_id: str, rejection_reason: str
) -> Dict[str, Any]:
    """
    Reject task results and mark payment for refund.

    Args:
        payment_id: Payment ID
        rejection_reason: Reason for rejection

    Returns:
        Rejection result
    """
    db = SessionLocal()
    try:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()

        if not payment:
            return {"success": False, "error": f"Payment {payment_id} not found"}

        # Mark payment as refunded
        payment.status = DBPaymentStatus.REFUNDED

        if payment.metadata is None:
            payment.metadata = {}
        payment.metadata["rejection_reason"] = rejection_reason
        payment.metadata["rejected_at"] = datetime.utcnow().isoformat()

        db.commit()
        db.refresh(payment)

        return {
            "success": True,
            "payment_id": payment_id,
            "status": "refunded",
            "rejection_reason": rejection_reason,
            "message": "Payment marked for refund due to failed verification",
        }

    finally:
        db.close()
