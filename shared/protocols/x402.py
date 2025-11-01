"""x402 Payment Protocol implementation for Hedera."""

from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from decimal import Decimal
from enum import Enum

from hedera import (
    TransferTransaction,
    Hbar,
    AccountId,
)


class PaymentStatus(str, Enum):
    """Payment status."""

    PENDING = "pending"
    AUTHORIZED = "authorized"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


@dataclass
class PaymentRequest:
    """x402 payment request."""

    payment_id: str
    from_account: str
    to_account: str
    amount: Decimal
    currency: str = "HBAR"
    description: str = ""
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["amount"] = str(self.amount)
        return data


@dataclass
class PaymentReceipt:
    """Payment receipt."""

    payment_id: str
    transaction_id: str
    status: PaymentStatus
    amount: Decimal
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None


class X402Payment:
    """x402 Payment Protocol for agent-to-agent payments."""

    def __init__(self, hedera_client):
        """
        Initialize x402 payment handler.

        Args:
            hedera_client: HederaClientWrapper instance
        """
        from shared.hedera.client import HederaClientWrapper

        self.hedera_client: HederaClientWrapper = hedera_client

    async def create_payment(self, payment_request: PaymentRequest) -> PaymentReceipt:
        """
        Create and execute a payment.

        Args:
            payment_request: Payment request details

        Returns:
            PaymentReceipt with transaction details
        """
        from datetime import datetime

        try:
            # Convert accounts
            from_account = AccountId.from_string(payment_request.from_account)
            to_account = AccountId.from_string(payment_request.to_account)

            # Convert amount to Hbar
            amount_hbar = Hbar.from_tinybars(int(payment_request.amount * 100_000_000))

            # Create transfer transaction
            transaction = (
                TransferTransaction()
                .add_hbar_transfer(from_account, amount_hbar.negated())
                .add_hbar_transfer(to_account, amount_hbar)
                .set_transaction_memo(f"x402: {payment_request.description}")
            )

            # Execute transaction
            response = await transaction.execute(self.hedera_client.client)
            receipt = await response.get_receipt(self.hedera_client.client)

            # Create payment receipt
            return PaymentReceipt(
                payment_id=payment_request.payment_id,
                transaction_id=str(response.transaction_id),
                status=PaymentStatus.COMPLETED,
                amount=payment_request.amount,
                timestamp=datetime.utcnow().isoformat(),
                metadata={
                    "receipt_status": str(receipt.status),
                    "original_request": payment_request.to_dict(),
                },
            )

        except Exception as e:
            # Return failed receipt
            return PaymentReceipt(
                payment_id=payment_request.payment_id,
                transaction_id="",
                status=PaymentStatus.FAILED,
                amount=payment_request.amount,
                timestamp=datetime.utcnow().isoformat(),
                metadata={"error": str(e)},
            )

    async def authorize_payment(self, payment_request: PaymentRequest) -> str:
        """
        Authorize a payment (escrow-like pattern).

        This is a placeholder for future escrow implementation.
        Currently returns a payment ID for tracking.
        """
        return f"auth_{payment_request.payment_id}"

    async def release_payment(self, authorization_id: str, payment_request: PaymentRequest) -> PaymentReceipt:
        """
        Release an authorized payment.

        For now, this simply executes the payment.
        Future: integrate with smart contract escrow.
        """
        return await self.create_payment(payment_request)

    def calculate_service_fee(
        self, base_amount: Decimal, rate: Decimal = Decimal("0.01")
    ) -> Decimal:
        """
        Calculate service fee for agent marketplace.

        Args:
            base_amount: Base service amount
            rate: Fee rate (default 1%)

        Returns:
            Service fee amount
        """
        return base_amount * rate
