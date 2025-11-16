#!/usr/bin/env python3
"""Test with builtin embedding model to isolate the issue"""

import sys
import time
import requests
from pathlib import Path

API_KEY = "ragflow-xkfeh3YrAbBSf8YTTLwXIkZiMfwWpjzJptjxs8vio5w"
BASE_URL = "http://127.0.0.1:9380/api/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Create KB with builtin embedding (no embedding_model specified = default)
print("Creating KB with builtin embedding...")
payload = {
    "name": "Test Builtin Embedding",
    "description": "Test KB with default BAAI/bge-small-en-v1.5 embedding",
    "chunk_method": "naive",
    "parser_config": {
        "chunk_token_num": 400
    }
}

response = requests.post(f"{BASE_URL}/datasets", json=payload, headers=headers)
result = response.json()

if result.get("code") == 0:
    dataset_id = result.get("data", {}).get("id")
    print(f"✅ KB created: {dataset_id}")
    print(f"   Embedding: {result.get('data', {}).get('embedding_model')}")

    # Upload sample document
    print("\nUploading document...")
    doc_path = Path(__file__).parent / "sample_korean_document.txt"

    with open(doc_path, "rb") as f:
        files = {"file": (doc_path.name, f, "text/plain")}
        upload_response = requests.post(
            f"{BASE_URL}/datasets/{dataset_id}/documents",
            headers={"Authorization": f"Bearer {API_KEY}"},
            files=files
        )

    upload_result = upload_response.json()
    if upload_result.get("code") == 0:
        document_id = upload_result.get("data", [])[0].get("id")
        print(f"✅ Document uploaded: {document_id}")

        # Start parsing
        print("\nStarting parsing...")
        parse_response = requests.post(
            f"{BASE_URL}/datasets/{dataset_id}/chunks",
            headers=headers,
            json={"document_ids": [document_id]}
        )

        if parse_response.json().get("code") == 0:
            print("✅ Parsing started")

            # Monitor for 60 seconds
            for i in range(12):
                time.sleep(5)
                status_response = requests.get(
                    f"{BASE_URL}/datasets/{dataset_id}/documents",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    params={"id": document_id}
                )

                status_result = status_response.json()
                if status_result.get("code") == 0:
                    docs = status_result.get("data", {}).get("docs", [])
                    if docs:
                        doc = docs[0]
                        run_status = doc.get("run")
                        progress = doc.get("progress", 0)
                        chunk_count = doc.get("chunk_count", 0)

                        print(f"[{i+1}] Status: {run_status}, Progress: {progress:.1f}%, Chunks: {chunk_count}")

                        if run_status == "DONE":
                            print(f"\n✅ SUCCESS! Builtin embedding works!")
                            print(f"   Chunks created: {chunk_count}")
                            sys.exit(0)
                        elif run_status == "FAIL":
                            msg = doc.get("progress_msg", "N/A")
                            print(f"\n❌ Parsing failed:")
                            print(f"{msg}")
                            sys.exit(1)

            print("\n⏱️ Timeout waiting for parsing")
        else:
            print(f"❌ Parse start failed: {parse_response.json().get('message')}")
    else:
        print(f"❌ Upload failed: {upload_result.get('message')}")
else:
    print(f"❌ KB creation failed: {result.get('message')}")
