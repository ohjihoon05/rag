#!/usr/bin/env python3
"""Debug KB configuration to see what's wrong"""

import requests
import json

API_KEY = "ragflow-xkfeh3YrAbBSf8YTTLwXIkZiMfwWpjzJptjxs8vio5w"
BASE_URL = "http://127.0.0.1:9380/api/v1"
DATASET_ID = "520b0696c2dd11f0897e129e0f398f8e"

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

# Get KB details
print("=== Knowledge Base Details ===")
response = requests.get(f"{BASE_URL}/datasets/{DATASET_ID}", headers=headers)
print(f"Status: {response.status_code}")
result = response.json()
print(json.dumps(result, indent=2, ensure_ascii=False))

# Get KB info
print("\n=== Knowledge Base Info ===")
response = requests.get(f"{BASE_URL}/datasets/{DATASET_ID}/info", headers=headers)
print(f"Status: {response.status_code}")
result = response.json()
print(json.dumps(result, indent=2, ensure_ascii=False))

# List all datasets
print("\n=== All Datasets ===")
response = requests.get(f"{BASE_URL}/datasets", headers=headers)
result = response.json()
if result.get("code") == 0:
    datasets = result.get("data", [])
    for ds in datasets:
        print(f"\nID: {ds.get('id')}")
        print(f"Name: {ds.get('name')}")
        print(f"Embedding: {ds.get('embedding_model')}")
        print(f"Chunk method: {ds.get('chunk_method')}")
        print(f"Parser config: {ds.get('parser_config')}")
