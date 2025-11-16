#!/usr/bin/env python3
import requests
import json

API_KEY = "ragflow-xkfeh3YrAbBSf8YTTLwXIkZiMfwWpjzJptjxs8vio5w"
BASE_URL = "http://localhost:9380/api/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json; charset=utf-8"
}

payload = {
    "name": "CS 데일리 리포트 (Ollama)",
    "description": "고객 서비스 팀의 일일 업무 리포트 - Ollama nomic-embed-text 사용",
    "embedding_model": "nomic-embed-text@Ollama",
    "chunk_method": "naive",
    "parser_config": {
        "chunk_token_num": 400
    }
}

print("Creating Knowledge Base with Ollama embedding...")
response = requests.post(
    f"{BASE_URL}/datasets",
    headers=headers,
    json=payload
)

print(f"Status: {response.status_code}")
result = response.json()
print(json.dumps(result, indent=2, ensure_ascii=False))

if result.get("code") == 0:
    dataset_id = result["data"]["id"]
    print(f"\n✅ KB created: {dataset_id}")
    print(f"   Name: {result['data']['name']}")
    print(f"   Embedding: {result['data']['embedding_model']}")
else:
    print(f"\n❌ Failed: {result.get('message')}")
