#!/usr/bin/env python
"""
Upload agent metadata files to Pinata (IPFS).

This script uploads all agent metadata JSON files to Pinata and returns the IPFS hashes.
You'll need to set PINATA_API_KEY and PINATA_SECRET_KEY in your .env file.
"""

import os
import sys
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Pinata API credentials
PINATA_API_KEY = os.getenv("PINATA_API_KEY")
PINATA_SECRET_KEY = os.getenv("PINATA_SECRET_KEY")

if not PINATA_API_KEY or not PINATA_SECRET_KEY:
    print("❌ Error: PINATA_API_KEY and PINATA_SECRET_KEY must be set in .env")
    print("\nTo get your Pinata keys:")
    print("1. Sign up at https://pinata.cloud")
    print("2. Go to API Keys section")
    print("3. Create a new key")
    print("4. Add to .env file:")
    print("   PINATA_API_KEY=your_api_key")
    print("   PINATA_SECRET_KEY=your_secret_key")
    sys.exit(1)

# Pinata API endpoints
PINATA_BASE_URL = "https://api.pinata.cloud"
PINATA_PIN_FILE = f"{PINATA_BASE_URL}/pinning/pinFileToIPFS"
PINATA_PIN_JSON = f"{PINATA_BASE_URL}/pinning/pinJSONToIPFS"

# Headers for Pinata API
headers = {
    "pinata_api_key": PINATA_API_KEY,
    "pinata_secret_api_key": PINATA_SECRET_KEY
}

# Metadata directory
METADATA_DIR = Path(__file__).parent.parent / "agent_metadata"

def upload_json_to_pinata(json_data, name):
    """
    Upload JSON data to Pinata.

    Args:
        json_data: Dictionary to upload
        name: Name for the pinned content

    Returns:
        IPFS hash if successful, None otherwise
    """
    try:
        # Prepare the request
        payload = {
            "pinataContent": json_data,
            "pinataOptions": {
                "cidVersion": 1
            },
            "pinataMetadata": {
                "name": name,
                "keyvalues": {
                    "type": "agent_metadata",
                    "project": "ProvidAI"
                }
            }
        }

        # Make the request
        response = requests.post(
            PINATA_PIN_JSON,
            json=payload,
            headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            return result["IpfsHash"]
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None


def upload_file_to_pinata(file_path):
    """
    Upload a file to Pinata.

    Args:
        file_path: Path to file to upload

    Returns:
        IPFS hash if successful, None otherwise
    """
    try:
        # Prepare the file
        with open(file_path, 'rb') as file:
            files = {'file': file}

            # Metadata for the pin
            metadata = {
                "name": os.path.basename(file_path),
                "keyvalues": {
                    "type": "agent_metadata",
                    "project": "ProvidAI"
                }
            }

            # Prepare the options
            options = {
                "cidVersion": "1",
                "wrapWithDirectory": "false"
            }

            # Prepare the payload
            payload = {
                'pinataMetadata': json.dumps(metadata),
                'pinataOptions': json.dumps(options)
            }

            # Make the request
            response = requests.post(
                PINATA_PIN_FILE,
                files=files,
                data=payload,
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                return result["IpfsHash"]
            else:
                print(f"   ❌ Error: {response.status_code} - {response.text}")
                return None

    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None


def main():
    """Upload all agent metadata files to Pinata."""

    print("="*80)
    print("UPLOADING AGENT METADATA TO PINATA (IPFS)")
    print("="*80)

    # Check if metadata directory exists
    if not METADATA_DIR.exists():
        print(f"❌ Metadata directory not found: {METADATA_DIR}")
        print("   Run: python -m scripts.generate_agent_metadata first")
        sys.exit(1)

    # Get all JSON files
    metadata_files = list(METADATA_DIR.glob("*.json"))

    if not metadata_files:
        print(f"❌ No metadata files found in {METADATA_DIR}")
        sys.exit(1)

    print(f"\n📁 Found {len(metadata_files)} metadata files")
    print(f"🔐 Using Pinata API Key: {PINATA_API_KEY[:8]}...")

    # Store results
    results = {}
    uploaded = 0
    failed = 0

    print("\n" + "-"*80)
    print("Starting upload...")
    print("-"*80)

    for i, file_path in enumerate(metadata_files, 1):
        filename = file_path.name
        agent_id = filename.replace('.json', '')

        print(f"\n[{i}/{len(metadata_files)}] Uploading {filename}...")

        # Load JSON data
        with open(file_path, 'r') as f:
            json_data = json.load(f)

        # Upload as JSON (more efficient than file upload)
        ipfs_hash = upload_json_to_pinata(json_data, filename)

        if ipfs_hash:
            print(f"   ✅ Success! IPFS Hash: {ipfs_hash}")
            print(f"   📍 Gateway URL: https://gateway.pinata.cloud/ipfs/{ipfs_hash}")
            print(f"   🌐 IPFS URL: ipfs://{ipfs_hash}")

            results[agent_id] = {
                "filename": filename,
                "ipfs_hash": ipfs_hash,
                "gateway_url": f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}",
                "ipfs_url": f"ipfs://{ipfs_hash}"
            }
            uploaded += 1
        else:
            print(f"   ❌ Failed to upload")
            failed += 1

    # Save results to file
    results_file = Path(__file__).parent.parent / "ipfs_metadata_urls.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print("\n" + "="*80)
    print("UPLOAD COMPLETE")
    print("="*80)
    print(f"✅ Successfully uploaded: {uploaded}")
    print(f"❌ Failed: {failed}")

    if uploaded > 0:
        print(f"\n📄 IPFS URLs saved to: {results_file}")

        # Print update script
        print("\n📝 To update agents with IPFS metadata URLs, use:")
        print("="*80)

        for agent_id, data in list(results.items())[:3]:  # Show first 3 as examples
            print(f"\nAgent: {agent_id}")
            print(f"  IPFS: ipfs://{data['ipfs_hash']}")
            print(f"  Gateway: {data['gateway_url']}")

        if len(results) > 3:
            print(f"\n... and {len(results) - 3} more agents")

        print("\n💡 Next steps:")
        print("1. Update the contract with these IPFS URLs using updateMetadata() function")
        print("2. Or re-register agents with IPFS URLs instead of HTTP URLs")
        print("3. Test retrieval via IPFS gateways")

    return results


if __name__ == "__main__":
    main()