#!/usr/bin/env python3
"""List existing Infinity tables to see what schema works"""

import requests

API_KEY = "ragflow-xkfeh3YrAbBSf8YTTLwXIkZiMfwWpjzJptjxs8vio5w"
BASE_URL = "http://127.0.0.1:9380/api/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}"
}

# List all datasets to see which ones have documents
response = requests.get(f"{BASE_URL}/datasets", headers=headers)
result = response.json()

if result.get("code") == 0:
    datasets = result.get("data", [])
    print(f"Found {len(datasets)} datasets\n")

    for ds in datasets:
        ds_id = ds.get("id")
        ds_name = ds.get("name")
        emb_model = ds.get("embedding_model")
        chunk_num = ds.get("chunk_num", 0)
        doc_amount = ds.get("document_amount", 0)

        print(f"Dataset: {ds_name}")
        print(f"  ID: {ds_id}")
        print(f"  Embedding: {emb_model}")
        print(f"  Documents: {doc_amount}")
        print(f"  Chunks: {chunk_num}")

        # If it has chunks, it has a working Infinity table
        if chunk_num > 0:
            print(f"  ✅ This dataset has a working Infinity table!")

            # Get chunk details
            chunk_response = requests.get(
                f"{BASE_URL}/datasets/{ds_id}/chunks",
                headers=headers,
                params={"page": 1, "page_size": 1}
            )

            if chunk_response.status_code == 200:
                chunk_result = chunk_response.json()
                if chunk_result.get("code") == 0:
                    chunks = chunk_result.get("data", {}).get("chunks", [])
                    if chunks:
                        print(f"  Sample chunk: {chunks[0].get('content_with_weight', '')[:100]}...")

        print()
