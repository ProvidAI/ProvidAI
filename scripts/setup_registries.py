#!/usr/bin/env python
"""
Set up the Reputation and Validation registries on the Identity Registry contract.
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3

# Load environment variables
load_dotenv(override=True)

RPC_URL = os.getenv("HEDERA_RPC_URL", "https://testnet.hashio.io/api")
PRIVATE_KEY = os.getenv("HEDERA_PRIVATE_KEY")

# Registry addresses from user
IDENTITY_REGISTRY = "0xeD2a06Ba4e718Ec2b1211Ddb85546e637Df3958E"
REPUTATION_REGISTRY = "0xe8ED6183f45C573FDeDf17d2D53baC875C7653E3"
VALIDATION_REGISTRY = "0x2d2B9147B0Db7820aEA50C5FCC1a6FB0eAaB6d9b"

if not PRIVATE_KEY:
    print("❌ Error: HEDERA_PRIVATE_KEY not set in .env file")
    sys.exit(1)

print("🔧 Connecting to Hedera testnet...")
web3 = Web3(Web3.HTTPProvider(RPC_URL))

if not web3.is_connected():
    print("❌ Failed to connect to Hedera")
    sys.exit(1)

print(f"✅ Connected to Hedera testnet")

# Setup account
account = web3.eth.account.from_key(PRIVATE_KEY)
wallet_address = account.address
print(f"📍 Wallet address: {wallet_address}")

balance = web3.eth.get_balance(wallet_address)
balance_hbar = web3.from_wei(balance, 'ether')
print(f"💰 Balance: {balance_hbar} HBAR")

# Load contract ABI
contract_json_path = Path(__file__).parent.parent / "shared/contracts/IdentityRegistry.sol/IdentityRegistry.json"

if not contract_json_path.exists():
    print(f"\n❌ Contract JSON not found at: {contract_json_path}")
    sys.exit(1)

with open(contract_json_path) as f:
    contract_data = json.load(f)
    abi = contract_data['abi']

# Create contract instance
print(f"\n🔧 Loading Identity Registry contract...")
identity_registry = web3.eth.contract(address=IDENTITY_REGISTRY, abi=abi)
print(f"✅ Contract loaded at: {IDENTITY_REGISTRY}")

# Check current registries
print("\n📊 Current Registry Configuration:")
try:
    current_reputation = identity_registry.functions.reputationRegistry().call()
    print(f"  Reputation Registry: {current_reputation}")
except Exception as e:
    print(f"  Reputation Registry: Not set or error ({e})")
    current_reputation = "0x0000000000000000000000000000000000000000"

try:
    current_validation = identity_registry.functions.validationRegistry().call()
    print(f"  Validation Registry: {current_validation}")
except Exception as e:
    print(f"  Validation Registry: Not set or error ({e})")
    current_validation = "0x0000000000000000000000000000000000000000"

# Set Reputation Registry if needed
if current_reputation == "0x0000000000000000000000000000000000000000":
    print(f"\n🔧 Setting Reputation Registry to: {REPUTATION_REGISTRY}")

    try:
        tx = identity_registry.functions.setReputationRegistry(REPUTATION_REGISTRY).build_transaction({
            "from": wallet_address,
            "nonce": web3.eth.get_transaction_count(wallet_address),
            "gas": 100000,
            "gasPrice": web3.eth.gas_price,
        })

        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print(f"   ⏳ TX: {tx_hash.hex()}")
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        if receipt['status'] == 1:
            print(f"   ✅ Reputation Registry set successfully!")
        else:
            print(f"   ❌ Transaction failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
else:
    print(f"✅ Reputation Registry already set")

# Set Validation Registry if needed
if current_validation == "0x0000000000000000000000000000000000000000":
    print(f"\n🔧 Setting Validation Registry to: {VALIDATION_REGISTRY}")

    try:
        tx = identity_registry.functions.setValidationRegistry(VALIDATION_REGISTRY).build_transaction({
            "from": wallet_address,
            "nonce": web3.eth.get_transaction_count(wallet_address),
            "gas": 100000,
            "gasPrice": web3.eth.gas_price,
        })

        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print(f"   ⏳ TX: {tx_hash.hex()}")
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)

        if receipt['status'] == 1:
            print(f"   ✅ Validation Registry set successfully!")
        else:
            print(f"   ❌ Transaction failed")
    except Exception as e:
        print(f"   ❌ Error: {e}")
else:
    print(f"✅ Validation Registry already set")

print("\n✅ Registry setup complete!")