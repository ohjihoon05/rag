#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Retrieval API Direct Test
RAGFlow Retrieval API를 직접 호출하여 검색 동작 확인

목적: Chat API 우회하여 검색 로직 문제 파악
"""

import requests
import json

# Configuration
API_KEY = "ragflow-xkfeh3YrAbBSf8YTTLwXIkZiMfwWpjzJptjxs8vio5w"
BASE_URL = "http://localhost"
DATASET_ID = "550f506ecf8e11f092cc9e4ca9309b43"

def get_headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

def test_retrieval(question, similarity_threshold=0.0, top_n=20, keywords_weight=0.5):
    """Retrieval API 직접 테스트"""
    url = f"{BASE_URL}/api/v1/retrieval"

    payload = {
        "question": question,
        "dataset_ids": [DATASET_ID],
        "similarity_threshold": similarity_threshold,
        "keywords_similarity_weight": keywords_weight,
        "top_n": top_n
    }

    print(f"\n{'='*60}")
    print(f"Question: {question}")
    print(f"Parameters: threshold={similarity_threshold}, weight={keywords_weight}, top_n={top_n}")
    print("-"*60)

    try:
        r = requests.post(url, headers=get_headers(), json=payload)
        data = r.json()

        if data.get("code") == 0:
            chunks = data.get("data", {}).get("chunks", [])
            print(f"SUCCESS: {len(chunks)} chunks returned")

            if chunks:
                for i, chunk in enumerate(chunks[:3], 1):
                    content = chunk.get("content", "")[:200]
                    score = chunk.get("similarity", 0)
                    print(f"\n  Chunk {i} (score: {score:.4f}):")
                    # Safe print for Windows
                    safe_content = content.encode('ascii', 'replace').decode('ascii')
                    print(f"    {safe_content}...")
            return len(chunks)
        else:
            print(f"ERROR: {data.get('message', 'Unknown error')}")
            print(f"Full response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return -1
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return -1

def test_chat_search(chat_id, question):
    """Chat Completions API로 검색 테스트 (reference 확인)"""
    # Create session
    session_url = f"{BASE_URL}/api/v1/chats/{chat_id}/sessions"
    r = requests.post(session_url, headers=get_headers(), json={"name": "retrieval_test"})
    data = r.json()

    if data.get("code") != 0:
        print(f"Session creation failed: {data}")
        return -1

    session_id = data.get("data", {}).get("id")

    # Ask question
    url = f"{BASE_URL}/api/v1/chats/{chat_id}/completions"
    payload = {
        "question": question,
        "session_id": session_id,
        "stream": False
    }

    print(f"\n{'='*60}")
    print(f"Chat Completions Test: {question}")
    print("-"*60)

    r = requests.post(url, headers=get_headers(), json=payload)
    data = r.json()

    if data.get("code") == 0:
        answer_data = data.get("data", {})
        reference = answer_data.get("reference", {})
        chunks = reference.get("chunks", [])

        print(f"Chunks returned: {len(chunks)}")

        if chunks:
            for i, chunk in enumerate(chunks[:3], 1):
                content = chunk.get("content", "")[:150]
                safe_content = content.encode('ascii', 'replace').decode('ascii')
                print(f"  Chunk {i}: {safe_content}...")

        # Print answer preview
        answer = answer_data.get("answer", "")[:200]
        safe_answer = answer.encode('ascii', 'replace').decode('ascii')
        print(f"\nAnswer: {safe_answer}...")

        return len(chunks)
    else:
        print(f"ERROR: {data.get('message')}")
        return -1

def main():
    print("="*70)
    print("RETRIEVAL API DIRECT TEST")
    print("="*70)

    # Test questions
    questions = [
        ("영업부", "Simple keyword"),
        ("매출액", "Simple keyword"),
        ("영업부에 속한 담당자", "Natural language"),
        ("매출액이 가장 높은 거래", "Natural language"),
        ("부서가 영업부인 데이터", "Explicit structure"),
    ]

    print("\n[1] Retrieval API Direct Test")
    print("="*70)

    for question, desc in questions:
        # Test with different parameters
        test_retrieval(question, similarity_threshold=0.0, top_n=20, keywords_weight=1.0)

    print("\n\n[2] Chat Completions API Test (for comparison)")
    print("="*70)

    chat_id = "d3a044d8d10f11f08f095aef2b223530"

    for question, desc in questions[:2]:  # Test first two
        test_chat_search(chat_id, question)

    print("\n\n[3] Summary")
    print("="*70)
    print("If Retrieval API returns chunks but Chat API doesn't,")
    print("the issue is in Chat's search configuration, not the index.")

if __name__ == "__main__":
    main()
