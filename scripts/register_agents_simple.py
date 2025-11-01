#!/usr/bin/env python
"""
Simple agent registration script that registers agents to the IdentityRegistry.
"""

import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account
import hashlib

# Load environment variables
load_dotenv(override=True)

RPC_URL = os.getenv("HEDERA_RPC_URL", "https://testnet.hashio.io/api")
PRIVATE_KEY = os.getenv("HEDERA_PRIVATE_KEY")
CONTRACT_ADDRESS = "0xeD2a06Ba4e718Ec2b1211Ddb85546e637Df3958E"

if not PRIVATE_KEY:
    print("❌ Error: HEDERA_PRIVATE_KEY not set")
    sys.exit(1)

print("🔧 Connecting to Hedera testnet...")
web3 = Web3(Web3.HTTPProvider(RPC_URL))

if not web3.is_connected():
    print("❌ Failed to connect")
    sys.exit(1)

account = web3.eth.account.from_key(PRIVATE_KEY)
wallet_address = account.address

print(f"✅ Connected")
print(f"📍 Wallet: {wallet_address}")
print(f"💰 Balance: {web3.from_wei(web3.eth.get_balance(wallet_address), 'ether')} HBAR")

# Load contract ABI
contract_json_path = Path(__file__).parent.parent / "shared/contracts/IdentityRegistry.sol/IdentityRegistry.json"
with open(contract_json_path) as f:
    contract_data = json.load(f)
    abi = contract_data['abi']

contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

# List of research agents to register
agents = [
    "problem-framer-001",
    "literature-miner-001",
    "feasibility-analyst-001",
    "goal-planner-001",
    "knowledge-synthesizer-001",
    "hypothesis-designer-001",
    "experiment-runner-001",
    "code-generator-001",
    "insight-generator-001",
    "bias-detector-001",
    "compliance-checker-001",
    "paper-writer-001",
    "peer-reviewer-001",
    "reputation-manager-001",
    "archiver-001"
]

print(f"\n📋 Registering {len(agents)} research agents...")
print("="*60)

# Get registration fee
try:
    fee = contract.functions.REGISTRATION_FEE().call()
    print(f"💰 Registration fee per agent: {web3.from_wei(fee, 'ether')} HBAR")
except:
    fee = web3.to_wei(0.005, 'ether')
    print(f"💰 Using default fee: 0.005 HBAR per agent")

total_cost = len(agents) * float(web3.from_wei(fee, 'ether'))
print(f"💸 Total cost: {total_cost} HBAR\n")

registered = 0
failed = 0

for i, domain in enumerate(agents, 1):
    print(f"[{i}/{len(agents)}] Registering {domain}...")

    # Generate unique address for agent
    seed = hashlib.sha256(domain.encode()).hexdigest()
    agent_account = Account.from_key('0x' + seed)
    agent_address = agent_account.address

    # Metadata URI (you can change this to IPFS or actual server)
    metadata_uri = f"https://providai.io/metadata/{domain}.json"

    print(f"   Address: {agent_address[:10]}...")

    try:
        # Build and send transaction
        nonce = web3.eth.get_transaction_count(wallet_address)

        tx = contract.functions.newAgent(
            domain,
            agent_address,
            metadata_uri
        ).build_transaction({
            'from': wallet_address,
            'nonce': nonce,
            'gas': 500000,
            'gasPrice': web3.eth.gas_price,
            'value': fee
        })

        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print(f"   TX: {tx_hash.hex()[:16]}...")

        # Wait for receipt
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

        if receipt['status'] == 1:
            print(f"   ✅ Success!")
            registered += 1
        else:
            print(f"   ❌ Failed (gas used: {receipt['gasUsed']})")
            failed += 1

    except Exception as e:
        print(f"   ❌ Error: {e}")
        failed += 1

    # Small delay between transactions
    if i < len(agents):
        time.sleep(2)

print("\n" + "="*60)
print("REGISTRATION SUMMARY")
print("="*60)
print(f"✅ Successfully registered: {registered}")
print(f"❌ Failed: {failed}")

# Check final count on-chain
try:
    count = contract.functions.getAgentCount().call()
    print(f"\n📊 Total agents on-chain: {count}")
except Exception as e:
    print(f"\n⚠️ Could not get on-chain count: {e}")

print("\n✨ Done!")