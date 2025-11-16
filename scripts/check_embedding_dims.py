#!/usr/bin/env python3
"""Check embedding dimensions from Ollama"""

import requests

response = requests.post(
    "http://localhost:11434/api/embeddings",
    json={"model": "nomic-embed-text", "prompt": "test"}
)

data = response.json()
dims = len(data["embedding"])
print(f"Vector dimensions: {dims}")
