#!/usr/bin/env python3
"""Create Knowledge Base with bge-m3 embedding and parse document"""

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

print("="*60)
print("Creating KB with bge-m3 embedding (1024-dim)")
print("="*60)

# Create KB with bge-m3
payload = {
    "name": "CS 데일리 리포트 (bge-m3)",
    "description": "고객 서비스 팀의 일일 업무 리포트 - bge-m3 embedding (1024-dim)",
    "embedding_model": "bge-m3@Ollama",
    "chunk_method": "naive",
    "parser_config": {
        "chunk_token_num": 400
    }
}

response = requests.post(f"{BASE_URL}/datasets", json=payload, headers=headers)
result = response.json()

if result.get("code") == 0:
    dataset_id = result["data"]["id"]
    print(f"KB created successfully!")
    print(f"  Name: {result['data']['name']}")
    print(f"  ID: {dataset_id}")
    print(f"  Embedding: {result['data']['embedding_model']}")
    print(f"  Dimensions: 1024")
else:
    print(f"Failed to create KB: {result.get('message')}")
    sys.exit(1)

# Upload document
print(f"\n{'='*60}")
print("Uploading Korean document")
print("="*60)

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
    document_id = upload_result["data"][0]["id"]
    print(f"Document uploaded successfully!")
    print(f"  File: {doc_path.name}")
    print(f"  Document ID: {document_id}")
else:
    print(f"Failed to upload: {upload_result.get('message')}")
    sys.exit(1)

# Start parsing
print(f"\n{'='*60}")
print("Starting document parsing")
print("="*60)

parse_response = requests.post(
    f"{BASE_URL}/datasets/{dataset_id}/chunks",
    headers=headers,
    json={"document_ids": [document_id]}
)

if parse_response.json().get("code") == 0:
    print("Parsing started...")
else:
    print(f"Failed to start parsing: {parse_response.json().get('message')}")
    sys.exit(1)

# Monitor parsing
print("\nMonitoring parsing progress...")

for i in range(36):  # 3 minutes max
    time.sleep(5)

    status_response = requests.get(
        f"{BASE_URL}/datasets/{dataset_id}/documents",
        headers={"Authorization": f"Bearer {API_KEY}"},
        params={"id": document_id}
    )

    status_result = status_response.json()
    if status_result.get("code") == 0:
        docs = status_result["data"]["docs"]
        if docs:
            doc = docs[0]
            run_status = doc["run"]
            progress = doc.get("progress", 0)
            chunk_count = doc.get("chunk_count", 0)

            print(f"[{i+1}] Status: {run_status}, Progress: {progress:.1f}%, Chunks: {chunk_count}")

            if run_status == "DONE":
                print(f"\n{'='*60}")
                print("PARSING COMPLETED!")
                print("="*60)
                print(f"  Embedding Model: bge-m3@Ollama (1024-dim)")
                print(f"  Chunks Created: {chunk_count}")
                print(f"  Time Taken: {(i+1)*5} seconds")
                print(f"  KB ID: {dataset_id}")
                print(f"  Document ID: {document_id}")
                print("="*60)

                # Save IDs for later use
                with open(Path(__file__).parent / "bge_m3_ids.txt", "w") as f:
                    f.write(f"KB_ID={dataset_id}\n")
                    f.write(f"DOC_ID={document_id}\n")
                    f.write(f"CHUNK_COUNT={chunk_count}\n")

                sys.exit(0)

            elif run_status == "FAIL":
                msg = doc.get("progress_msg", "N/A")
                print(f"\nParsing failed:")
                print(msg)
                sys.exit(1)

print("\nTimeout waiting for parsing")
sys.exit(1)
