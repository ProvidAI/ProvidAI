#!/usr/bin/env python
"""
Debug script to test agent registration with exact fee.
"""

import os
import sys
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account
import hashlib

load_dotenv(override=True)

RPC_URL = os.getenv("HEDERA_RPC_URL", "https://testnet.hashio.io/api")
PRIVATE_KEY = os.getenv("HEDERA_PRIVATE_KEY")
CONTRACT_ADDRESS = "0xeD2a06Ba4e718Ec2b1211Ddb85546e637Df3958E"

if not PRIVATE_KEY:
    print("❌ HEDERA_PRIVATE_KEY not set")
    sys.exit(1)

print("🔧 Connecting to Hedera...")
web3 = Web3(Web3.HTTPProvider(RPC_URL))

if not web3.is_connected():
    print("❌ Failed to connect")
    sys.exit(1)

account = web3.eth.account.from_key(PRIVATE_KEY)
wallet_address = account.address

print(f"✅ Connected")
print(f"📍 Wallet: {wallet_address}")
print(f"💰 Balance: {web3.from_wei(web3.eth.get_balance(wallet_address), 'ether')} HBAR")

# The exact registration fee from contract
REGISTRATION_FEE = web3.to_wei(0.005, 'ether')
print(f"\n💰 Registration fee: {web3.from_wei(REGISTRATION_FEE, 'ether')} HBAR")
print(f"   In wei: {REGISTRATION_FEE}")

# Test with a unique domain
import time
test_domain = f"test-{int(time.time())}"

# Generate deterministic address
seed = hashlib.sha256(test_domain.encode()).hexdigest()
agent_account = Account.from_key('0x' + seed)
agent_address = agent_account.address

# Simple metadata URI
metadata_uri = f"https://example.com/metadata/{test_domain}.json"

print(f"\n🧪 Testing registration:")
print(f"   Domain: {test_domain}")
print(f"   Address: {agent_address}")
print(f"   Metadata: {metadata_uri}")

# Build minimal ABI for newAgent function
abi = [
    {
        "inputs": [
            {"internalType": "string", "name": "agentDomain", "type": "string"},
            {"internalType": "address", "name": "agentAddress", "type": "address"},
            {"internalType": "string", "name": "metadataUri", "type": "string"}
        ],
        "name": "newAgent",
        "outputs": [{"internalType": "uint256", "name": "agentId", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "REGISTRATION_FEE",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getAgentCount",
        "outputs": [{"internalType": "uint256", "name": "count", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

# Verify the fee matches
try:
    contract_fee = contract.functions.REGISTRATION_FEE().call()
    print(f"\n✓ Contract fee verified: {web3.from_wei(contract_fee, 'ether')} HBAR")
    if contract_fee != REGISTRATION_FEE:
        print(f"⚠️  Fee mismatch! Contract expects {contract_fee} wei")
        REGISTRATION_FEE = contract_fee
except Exception as e:
    print(f"⚠️  Could not verify fee: {e}")

# Get current agent count
try:
    count_before = contract.functions.getAgentCount().call()
    print(f"📊 Current agent count: {count_before}")
except Exception as e:
    print(f"⚠️  Could not get count: {e}")
    count_before = 0

print("\n📤 Sending transaction...")

try:
    # Get current nonce
    nonce = web3.eth.get_transaction_count(wallet_address)

    # Get current gas price
    gas_price = web3.eth.gas_price

    # Build transaction with exact parameters
    tx = {
        'from': wallet_address,
        'to': CONTRACT_ADDRESS,
        'nonce': nonce,
        'gas': 500000,  # High gas limit to ensure it doesn't run out
        'gasPrice': gas_price,
        'value': REGISTRATION_FEE,  # Exact fee required
        'data': contract.functions.newAgent(
            test_domain, agent_address, metadata_uri
        ).build_transaction({'from': wallet_address})['data']
    }

    print(f"   Nonce: {nonce}")
    print(f"   Gas limit: {tx['gas']}")
    print(f"   Gas price: {web3.from_wei(gas_price, 'gwei')} gwei")
    print(f"   Value: {web3.from_wei(tx['value'], 'ether')} HBAR")

    # Sign transaction
    signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)

    # Send transaction
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"\n⏳ Transaction sent: {tx_hash.hex()}")

    # Wait for receipt
    print("   Waiting for confirmation...")
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

    print(f"\n📃 Receipt:")
    print(f"   Status: {'✅ SUCCESS' if receipt['status'] == 1 else '❌ FAILED'}")
    print(f"   Gas used: {receipt['gasUsed']} / {tx['gas']}")
    print(f"   Block: {receipt['blockNumber']}")

    if receipt['status'] == 1:
        # Check new count
        try:
            count_after = contract.functions.getAgentCount().call()
            print(f"\n✅ Registration successful!")
            print(f"   Agent count: {count_before} → {count_after}")
            print(f"   New agent ID: {count_after}")
        except:
            print("\n✅ Transaction succeeded!")
    else:
        print("\n❌ Transaction failed!")
        print("   The contract reverted the transaction")

        # Try to decode revert reason
        try:
            # Get the transaction
            tx_details = web3.eth.get_transaction(tx_hash)
            # Try to call the function to get the revert reason
            web3.eth.call(tx_details, receipt['blockNumber'] - 1)
        except Exception as e:
            print(f"   Revert reason: {e}")

except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"   Type: {type(e).__name__}")

print("\n✨ Done!")