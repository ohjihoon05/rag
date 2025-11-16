#!/usr/bin/env python3
import time
import requests

API_KEY = "ragflow-xkfeh3YrAbBSf8YTTLwXIkZiMfwWpjzJptjxs8vio5w"
BASE_URL = "http://localhost:9380/api/v1"
DATASET_ID = "8363e9acc2c311f0bae4129e0f398f8e"
DOCUMENT_ID = "836f4a40c2c311f0b62b129e0f398f8e"

headers = {"Authorization": f"Bearer {API_KEY}"}

for i in range(36):  # 3 minutes max
    try:
        response = requests.get(
            f"{BASE_URL}/datasets/{DATASET_ID}/documents",
            headers=headers,
            params={"id": DOCUMENT_ID}
        )

        if response.status_code == 200:
            data = response.json()["data"]["docs"][0]
            run_status = data["run"]
            progress = data["progress"]
            chunks = data["chunk_count"]
            msg = data["progress_msg"][:100] if data["progress_msg"] else "N/A"

            print(f"[{i+1:2d}] Status: {run_status:8s} | Progress: {progress:5.1f}% | Chunks: {chunks:3d} | {msg}")

            if run_status == "DONE":
                print(f"\n✅ Parsing completed! Total chunks: {chunks}")
                break
            elif run_status == "FAIL":
                print(f"\n❌ Parsing failed: {msg}")
                break
        else:
            print(f"HTTP Error: {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")

    time.sleep(5)
