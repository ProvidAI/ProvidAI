"""Hedera client configuration and utilities."""

import os
from typing import Optional
from dataclasses import dataclass

from hedera import (
    Client,
    AccountId,
    PrivateKey,
    TopicCreateTransaction,
    TopicMessageSubmitTransaction,
    TopicId,
)
from pydantic_settings import BaseSettings


class HederaConfig(BaseSettings):
    """Hedera configuration from environment."""

    network: str = "testnet"
    account_id: str
    private_key: str
    hcs_topic_id: Optional[str] = None

    class Config:
        env_prefix = "HEDERA_"
        case_sensitive = False


@dataclass
class HederaClientWrapper:
    """Wrapper for Hedera client with utilities."""

    client: Client
    operator_id: AccountId
    operator_key: PrivateKey
    topic_id: Optional[TopicId] = None

    async def create_topic(self, memo: str = "Agent Coordination Topic") -> TopicId:
        """Create a new HCS topic."""
        transaction = TopicCreateTransaction().set_topic_memo(memo)

        response = await transaction.execute(self.client)
        receipt = await response.get_receipt(self.client)

        if receipt.topic_id is None:
            raise ValueError("Failed to create topic")

        self.topic_id = receipt.topic_id
        return self.topic_id

    async def submit_message(self, message: str, topic_id: Optional[TopicId] = None) -> str:
        """Submit a message to HCS topic."""
        target_topic = topic_id or self.topic_id
        if target_topic is None:
            raise ValueError("No topic ID specified")

        transaction = (
            TopicMessageSubmitTransaction()
            .set_topic_id(target_topic)
            .set_message(message.encode("utf-8"))
        )

        response = await transaction.execute(self.client)
        receipt = await response.get_receipt(self.client)

        return str(receipt.status)


def get_hedera_client(config: Optional[HederaConfig] = None) -> HederaClientWrapper:
    """
    Get configured Hedera client for testnet.

    Args:
        config: Optional HederaConfig, if None will load from environment

    Returns:
        Configured HederaClientWrapper
    """
    if config is None:
        config = HederaConfig()

    # Create client for testnet or mainnet
    if config.network == "testnet":
        client = Client.for_testnet()
    elif config.network == "mainnet":
        client = Client.for_mainnet()
    else:
        raise ValueError(f"Unsupported network: {config.network}")

    # Set operator
    operator_id = AccountId.from_string(config.account_id)
    operator_key = PrivateKey.from_string(config.private_key)
    client.set_operator(operator_id, operator_key)

    # Parse topic ID if provided
    topic_id = None
    if config.hcs_topic_id:
        topic_id = TopicId.from_string(config.hcs_topic_id)

    return HederaClientWrapper(
        client=client, operator_id=operator_id, operator_key=operator_key, topic_id=topic_id
    )
