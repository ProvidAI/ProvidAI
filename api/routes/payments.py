"""Payment management routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from shared.database import get_db, Payment
from shared.database.models import PaymentStatus

router = APIRouter()


class PaymentResponse(BaseModel):
    """Payment response."""

    id: str
    task_id: str
    from_agent_id: str
    to_agent_id: str
    amount: float
    currency: str
    status: str
    transaction_id: Optional[str]

    class Config:
        from_attributes = True


class CreatePaymentRequest(BaseModel):
    """Create payment request."""

    task_id: str
    from_agent_id: str
    to_agent_id: str
    to_hedera_account: str
    amount: float
    description: str = ""


class ReleasePaymentRequest(BaseModel):
    """Release payment request."""

    verification_notes: str = ""


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: str, db: Session = Depends(get_db)):
    """Get payment by ID."""
    payment = db.query(Payment).filter(Payment.id == payment_id).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    return PaymentResponse(
        id=payment.id,
        task_id=payment.task_id,
        from_agent_id=payment.from_agent_id,
        to_agent_id=payment.to_agent_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status.value,
        transaction_id=payment.transaction_id,
    )


@router.get("/", response_model=List[PaymentResponse])
async def list_payments(
    task_id: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)
):
    """List payments with optional filtering."""
    query = db.query(Payment)

    if task_id:
        query = query.filter(Payment.task_id == task_id)

    if status:
        query = query.filter(Payment.status == PaymentStatus(status))

    payments = query.order_by(Payment.created_at.desc()).all()

    return [
        PaymentResponse(
            id=payment.id,
            task_id=payment.task_id,
            from_agent_id=payment.from_agent_id,
            to_agent_id=payment.to_agent_id,
            amount=payment.amount,
            currency=payment.currency,
            status=payment.status.value,
            transaction_id=payment.transaction_id,
        )
        for payment in payments
    ]


@router.post("/", response_model=PaymentResponse)
async def create_payment(request: CreatePaymentRequest):
    """Create a new payment."""
    from agents.negotiator import create_negotiator_agent

    agent = create_negotiator_agent()

    prompt = f"""
    Create a payment request:
    Task ID: {request.task_id}
    From: {request.from_agent_id}
    To: {request.to_agent_id} (Hedera account: {request.to_hedera_account})
    Amount: {request.amount} HBAR
    Description: {request.description}
    """

    result = await agent.run(prompt)

    return {"message": "Payment request created", "result": result}


@router.post("/{payment_id}/release")
async def release_payment(payment_id: str, request: ReleasePaymentRequest):
    """Release an authorized payment."""
    from agents.verifier import create_verifier_agent

    agent = create_verifier_agent()

    prompt = f"""
    Release payment: {payment_id}
    Verification notes: {request.verification_notes}
    """

    result = await agent.run(prompt)

    return {"message": "Payment release initiated", "result": result}
