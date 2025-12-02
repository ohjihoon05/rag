#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAGFlow Single Excel Test Script - Test one chunking method at a time
"""

import os
import sys
import time
import json
import requests

# Configuration
API_KEY = "ragflow-xkfeh3YrAbBSf8YTTLwXIkZiMfwWpjzJptjxs8vio5w"
BASE_URL = "http://localhost"
EXCEL_FILE = r"C:\Users\ohjh\ragflow\daily_report_sample.xlsx"

def get_headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

def get_upload_headers():
    return {"Authorization": f"Bearer {API_KEY}"}

def create_dataset(name, chunk_method, parser_config):
    url = f"{BASE_URL}/api/v1/datasets"
    payload = {"name": name, "chunk_method": chunk_method, "parser_config": parser_config}
    r = requests.post(url, headers=get_headers(), json=payload)
    data = r.json()
    print(f"Create dataset response: {data}")
    if data.get("code") == 0:
        return data.get("data", {})
    raise Exception(f"Failed: {data.get('message')}")

def delete_dataset(dataset_id):
    url = f"{BASE_URL}/api/v1/datasets"
    r = requests.delete(url, headers=get_headers(), json={"ids": [dataset_id]})
    return r.json()

def upload_document(dataset_id, file_path):
    url = f"{BASE_URL}/api/v1/datasets/{dataset_id}/documents"
    with open(file_path, "rb") as f:
        files = {"file": (os.path.basename(file_path), f)}
        r = requests.post(url, headers=get_upload_headers(), files=files)
    data = r.json()
    print(f"Upload response: {data}")
    if data.get("code") == 0:
        return data.get("data", [])
    raise Exception(f"Failed: {data.get('message')}")

def start_parsing(dataset_id, document_ids):
    url = f"{BASE_URL}/api/v1/datasets/{dataset_id}/chunks"
    payload = {"document_ids": document_ids}
    r = requests.post(url, headers=get_headers(), json=payload)
    return r.json()

def get_document_status(dataset_id, doc_id):
    url = f"{BASE_URL}/api/v1/datasets/{dataset_id}/documents"
    r = requests.get(url, headers=get_headers(), params={"id": doc_id})
    data = r.json()
    if data.get("code") == 0:
        # API returns {"data": {"docs": [...], "total": N}}
        docs_data = data.get("data", {})
        if isinstance(docs_data, dict):
            docs = docs_data.get("docs", [])
        else:
            docs = docs_data
        if docs and isinstance(docs, list) and len(docs) > 0:
            return docs[0]
    return None

def list_chunks(dataset_id, document_id, limit=10):
    url = f"{BASE_URL}/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks"
    r = requests.get(url, headers=get_headers(), params={"page": 1, "page_size": limit})
    data = r.json()
    print(f"    list_chunks raw response: {str(data)[:500]}")
    if data.get("code") == 0:
        # API may return {"data": {"chunks": [...], "total": N}} or {"data": [...]}
        result = data.get("data", [])
        if isinstance(result, dict):
            return result.get("chunks", [])
        return result
    return []

def retrieve_chunks(dataset_ids, question, top_k=3):
    url = f"{BASE_URL}/api/v1/retrieval"
    payload = {"dataset_ids": dataset_ids, "question": question, "top_k": top_k}
    r = requests.post(url, headers=get_headers(), json=payload)
    data = r.json()
    if data.get("code") == 0:
        return data.get("data", {}).get("chunks", [])
    return []

def get_total_chunks(dataset_id, doc_id):
    """Get total chunk count"""
    url = f"{BASE_URL}/api/v1/datasets/{dataset_id}/documents/{doc_id}/chunks"
    r = requests.get(url, headers=get_headers(), params={"page": 1, "page_size": 1})
    data = r.json()
    # Try getting total from top-level or nested in data
    if data.get("code") == 0:
        result = data.get("data", {})
        if isinstance(result, dict):
            return result.get("total", 0)
    return data.get("total", 0)

def wait_for_parsing(dataset_id, doc_id, timeout=None):
    start = time.time()
    last_progress = -1
    while True:
        doc = get_document_status(dataset_id, doc_id)
        if doc:
            status = doc.get("run", "UNKNOWN")
            progress = doc.get("progress", 0)
            elapsed = int(time.time() - start)
            # Only print when progress changes
            if progress != last_progress:
                print(f"  -> Status: {status}, Progress: {progress:.1%} ({elapsed}s)")
                last_progress = progress
            if status == "DONE" or (status == "RUNNING" and progress >= 1.0):
                return True, doc
            if status == "FAIL":
                return False, doc
        time.sleep(5)

def run_test(test_name, chunk_method, parser_config, cleanup=True):
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"Method: {chunk_method}")
    print(f"Config: {json.dumps(parser_config, ensure_ascii=False)}")
    print(f"{'='*60}")

    dataset_name = f"test_{chunk_method}_{int(time.time())}"
    dataset_id = None

    try:
        # 1. Create dataset
        print("\n[1] Creating dataset...")
        dataset = create_dataset(dataset_name, chunk_method, parser_config)
        dataset_id = dataset.get("id")
        print(f"    ID: {dataset_id}")

        # 2. Upload file
        print("\n[2] Uploading Excel file...")
        docs = upload_document(dataset_id, EXCEL_FILE)
        doc = docs[0] if isinstance(docs, list) else docs
        doc_id = doc.get("id")
        print(f"    Doc ID: {doc_id}")

        # 3. Start parsing
        print("\n[3] Starting parsing...")
        result = start_parsing(dataset_id, [doc_id])
        print(f"    Result: {result}")

        # 4. Wait for completion
        print("\n[4] Waiting for parsing (unlimited)...")
        success, parsed_doc = wait_for_parsing(dataset_id, doc_id)

        if not success:
            print("    FAILED or TIMEOUT")
            return {"test": test_name, "status": "FAIL", "chunk_count": 0}

        # 5. Get chunk info
        print("\n[5] Getting chunks...")
        chunk_count = get_total_chunks(dataset_id, doc_id)
        chunks = list_chunks(dataset_id, doc_id, limit=3)
        print(f"    Total chunks: {chunk_count}")

        if chunks:
            print("\n    Sample chunks:")
            for i, c in enumerate(chunks[:2]):
                content = c.get("content", "")[:100]
                print(f"    [{i+1}] {content}...")

        # 6. Test retrieval
        print("\n[6] Testing retrieval...")
        questions = ["제품B 판매수량", "한소희 매출액"]
        for q in questions:
            results = retrieve_chunks([dataset_id], q)
            print(f"    Q: {q}")
            if results:
                similarity = results[0].get("similarity", 0)
                content = results[0].get("content", "")[:80]
                print(f"       -> Sim: {similarity:.3f}, Content: {content}...")
            else:
                print(f"       -> No results")

        return {
            "test": test_name,
            "status": "OK",
            "chunk_count": chunk_count,
            "method": chunk_method,
            "config": parser_config
        }

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"test": test_name, "status": "ERROR", "error": str(e)}

    finally:
        if dataset_id and cleanup:
            print("\n[7] Cleanup...")
            try:
                delete_dataset(dataset_id)
                print("    Dataset deleted")
            except:
                pass
        elif dataset_id:
            print(f"\n[7] Skipping cleanup. Dataset ID: {dataset_id}")

if __name__ == "__main__":
    # Get test number from command line
    test_num = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    tests = [
        ("Test 1: Table (Default)", "table", {"chunk_token_num": 512}),
        ("Test 2: Naive (Default)", "naive", {"html4excel": False, "chunk_token_num": 512}),
        ("Test 3: Naive + HTML4Excel", "naive", {"html4excel": True, "chunk_token_num": 512}),
        ("Test 4: Table + Korean Opt", "table", {"chunk_token_num": 320}),
        ("Test 5: Naive + HTML + Korean", "naive", {"html4excel": True, "chunk_token_num": 320}),
    ]

    # Check for --no-cleanup flag
    cleanup = "--no-cleanup" not in sys.argv

    if 1 <= test_num <= len(tests):
        name, method, config = tests[test_num - 1]
        result = run_test(name, method, config, cleanup=cleanup)
        print(f"\n{'='*60}")
        print(f"RESULT: {json.dumps(result, ensure_ascii=False, indent=2)}")
    else:
        print(f"Usage: python {sys.argv[0]} <test_number 1-5> [--no-cleanup]")
