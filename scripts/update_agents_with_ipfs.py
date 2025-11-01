#!/usr/bin/env python
"""
Update registered agents with IPFS metadata URLs.
"""

import os
import sys
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from web3 import Web3
from eth_account import Account

# Load environment variables
load_dotenv(override=True)

RPC_URL = os.getenv("HEDERA_RPC_URL", "https://testnet.hashio.io/api")
PRIVATE_KEY = os.getenv("HEDERA_PRIVATE_KEY")
CONTRACT_ADDRESS = "0x1F26e1Fa2DE63B9bd993BDb2214fB793031A2E89"  # New contract

if not PRIVATE_KEY:
    print("❌ Error: HEDERA_PRIVATE_KEY not set")
    sys.exit(1)

# Load IPFS URLs
ipfs_urls_path = Path(__file__).parent.parent / "ipfs_metadata_urls.json"
if not ipfs_urls_path.exists():
    print("❌ Error: ipfs_metadata_urls.json not found")
    print("   Run: python scripts/upload_metadata_to_pinata.py first")
    sys.exit(1)

with open(ipfs_urls_path) as f:
    ipfs_data = json.load(f)

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

print(f"\n📋 Updating {len(ipfs_data)} agents with IPFS metadata...")
print("="*60)

updated = 0
failed = 0
skipped = 0

for agent_domain, data in ipfs_data.items():
    print(f"\nUpdating {agent_domain}...")

    # Get agent info to find agent ID
    try:
        agent_info = contract.functions.resolveByDomain(agent_domain).call()
        agent_id = agent_info[0]
        current_uri = agent_info[3]

        print(f"   Agent ID: {agent_id}")
        print(f"   Current URI: {current_uri[:50]}...")

        # Check if already using IPFS
        if current_uri.startswith("ipfs://"):
            print(f"   ⚠️  Already using IPFS")
            skipped += 1
            continue

    except Exception as e:
        print(f"   ❌ Agent not found: {e}")
        failed += 1
        continue

    # Update with IPFS URL
    ipfs_uri = data['ipfs_url']  # Use ipfs:// protocol
    print(f"   New URI: {ipfs_uri}")

    try:
        # Build and send transaction
        nonce = web3.eth.get_transaction_count(wallet_address)

        tx = contract.functions.updateMetadata(
            agent_id,
            ipfs_uri
        ).build_transaction({
            'from': wallet_address,
            'nonce': nonce,
            'gas': 200000,
            'gasPrice': web3.eth.gas_price
        })

        signed_tx = web3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

        print(f"   TX: {tx_hash.hex()[:16]}...")

        # Wait for receipt
        receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

        if receipt['status'] == 1:
            print(f"   ✅ Success!")
            updated += 1
        else:
            print(f"   ❌ Failed (gas used: {receipt['gasUsed']})")
            failed += 1

    except Exception as e:
        print(f"   ❌ Error: {e}")
        failed += 1

    # Small delay between transactions
    time.sleep(2)

print("\n" + "="*60)
print("UPDATE SUMMARY")
print("="*60)
print(f"✅ Successfully updated: {updated}")
print(f"⚠️  Already using IPFS: {skipped}")
print(f"❌ Failed: {failed}")

# Verify a few agents
if updated > 0:
    print(f"\n🔍 Verifying updates...")
    for agent_domain in list(ipfs_data.keys())[:3]:
        try:
            agent_info = contract.functions.resolveByDomain(agent_domain).call()
            print(f"   {agent_domain}: {agent_info[3][:60]}...")
        except:
            pass

print("\n✨ Done!")
print("\n📝 Next steps:")
print("1. Test agent discovery with IPFS metadata")
print("2. Verify IPFS gateway access works")
print("3. Consider pinning to additional IPFS nodes for redundancy")