#!/usr/bin/env python3
"""Verify chunks using correct API endpoints"""

import requests
import json

API_KEY = "ragflow-xkfeh3YrAbBSf8YTTLwXIkZiMfwWpjzJptjxs8vio5w"
BASE_URL = "http://127.0.0.1:9380/api/v1"
DATASET_ID = "520b0696c2dd11f0897e129e0f398f8e"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Try to list chunks
print("=" * 60)
print("Listing chunks from Knowledge Base")
print("=" * 60)

response = requests.get(
    f"{BASE_URL}/datasets/{DATASET_ID}/chunks",
    headers=headers,
    params={"page": 1, "page_size": 10}
)

print(f"Status: {response.status_code}")
result = response.json()
print(json.dumps(result, indent=2, ensure_ascii=False))

if result.get("code") == 0:
    chunks = result.get("data", {}).get("chunks", [])
    print(f"\n✅ Found {len(chunks)} chunks")

    for i, chunk in enumerate(chunks, 1):
        print(f"\n[Chunk {i}]")
        print(f"ID: {chunk.get('id')}")
        print(f"Content: {chunk.get('content_with_weight', '')[:200]}...")
        print(f"Doc ID: {chunk.get('doc_id')}")

# Test retrieval
print("\n" + "=" * 60)
print("Testing chunk retrieval with Korean keywords")
print("=" * 60)

test_queries = [
    "배송 지연",
    "고객 만족도",
    "결제 오류"
]

for query in test_queries:
    print(f"\n🔍 검색어: '{query}'")

    payload = {
        "question": query,
        "top_k": 3
    }

    response = requests.post(
        f"{BASE_URL}/datasets/{DATASET_ID}/retrieval",
        headers=headers,
        json=payload
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2, ensure_ascii=False)[:500])
    else:
        print(f"Error: {response.text[:200]}")
