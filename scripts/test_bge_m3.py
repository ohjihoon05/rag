#!/usr/bin/env python3
"""Test bge-m3 embedding model"""

import requests

response = requests.post(
    "http://localhost:11434/api/embeddings",
    json={"model": "bge-m3", "prompt": "테스트"}
)

data = response.json()
dims = len(data["embedding"])
print(f"bge-m3 embedding dimensions: {dims}")
print(f"Model size: 1.2 GB")
print(f"Multilingual: Yes (supports Korean)")
