#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAGFlow Excel Optimization Test Script
Tests different chunking methods for Korean daily report Excel files
Uses direct API calls instead of SDK
"""

import os
import sys
import time
import json
import requests
from pathlib import Path

# Configuration
API_KEY = "ragflow-xkfeh3YrAbBSf8YTTLwXIkZiMfwWpjzJptjxs8vio5w"
BASE_URL = "http://localhost"
EXCEL_FILE = r"C:\Users\ohjh\ragflow\daily_report_sample.xlsx"

# Headers for API calls
def get_headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

def get_upload_headers():
    return {
        "Authorization": f"Bearer {API_KEY}"
    }

# Test questions for evaluation
TEST_QUESTIONS = [
    "제품B의 총 판매수량은?",
    "한소희 담당자의 매출액은?",
    "운영부 할인율은?"
]

def create_dataset(name, chunk_method, parser_config):
    """Create a new dataset"""
    url = f"{BASE_URL}/api/v1/datasets"
    payload = {
        "name": name,
        "chunk_method": chunk_method,
        "parser_config": parser_config
    }
    response = requests.post(url, headers=get_headers(), json=payload)
    data = response.json()
    if data.get("code") == 0:
        return data.get("data", {})
    else:
        raise Exception(f"Failed to create dataset: {data.get('message')}")

def delete_dataset(dataset_id):
    """Delete a dataset"""
    url = f"{BASE_URL}/api/v1/datasets"
    payload = {"ids": [dataset_id]}
    response = requests.delete(url, headers=get_headers(), json=payload)
    return response.json()

def upload_document(dataset_id, file_path):
    """Upload a document to a dataset"""
    url = f"{BASE_URL}/api/v1/datasets/{dataset_id}/documents"
    files = {
        "file": (os.path.basename(file_path), open(file_path, "rb"))
    }
    response = requests.post(url, headers=get_upload_headers(), files=files)
    data = response.json()
    if data.get("code") == 0:
        return data.get("data", [])
    else:
        raise Exception(f"Failed to upload document: {data.get('message')}")

def start_parsing(dataset_id, document_ids):
    """Start parsing documents"""
    url = f"{BASE_URL}/api/v1/datasets/{dataset_id}/chunks"
    payload = {
        "document_ids": document_ids
    }
    response = requests.post(url, headers=get_headers(), json=payload)
    return response.json()

def get_document_status(dataset_id, doc_id):
    """Get document parsing status"""
    url = f"{BASE_URL}/api/v1/datasets/{dataset_id}/documents"
    params = {"id": doc_id}
    response = requests.get(url, headers=get_headers(), params=params)
    data = response.json()
    if data.get("code") == 0:
        docs = data.get("data", [])
        if docs and isinstance(docs, list) and len(docs) > 0:
            return docs[0]
        elif docs and isinstance(docs, dict):
            return docs
    return None

def list_chunks(dataset_id, document_id):
    """List chunks for a document"""
    url = f"{BASE_URL}/api/v1/datasets/{dataset_id}/documents/{document_id}/chunks"
    params = {"page": 1, "page_size": 100}
    response = requests.get(url, headers=get_headers(), params=params)
    data = response.json()
    if data.get("code") == 0:
        return data.get("data", [])
    return []

def retrieve_chunks(dataset_ids, question, top_k=3):
    """Retrieve chunks based on question"""
    url = f"{BASE_URL}/api/v1/retrieval"
    payload = {
        "dataset_ids": dataset_ids,
        "question": question,
        "top_k": top_k
    }
    response = requests.post(url, headers=get_headers(), json=payload)
    data = response.json()
    if data.get("code") == 0:
        return data.get("data", {}).get("chunks", [])
    return []

def wait_for_parsing(dataset_id, doc_id, timeout=300):
    """Wait for document parsing to complete"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        doc = get_document_status(dataset_id, doc_id)
        if doc:
            status = doc.get("run", "")
            progress = doc.get("progress", 0)
            progress_msg = doc.get("progress_msg", "")
            print(f"  Status: {status}, Progress: {progress:.1%}, Msg: {progress_msg[:50]}")

            if status == "DONE" or (status == "RUNNING" and progress >= 1.0):
                return True, doc
            elif status == "FAIL":
                return False, doc

        time.sleep(5)

    return False, None

def test_chunking_method(test_name, chunk_method, parser_config, questions):
    """Test a specific chunking configuration"""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"Chunk Method: {chunk_method}")
    print(f"Parser Config: {json.dumps(parser_config, ensure_ascii=False)}")
    print(f"{'='*60}")

    dataset_name = f"excel_test_{chunk_method}_{int(time.time())}"
    dataset_id = None

    try:
        # Create dataset
        print(f"\n1. Creating dataset: {dataset_name}")
        dataset = create_dataset(dataset_name, chunk_method, parser_config)
        dataset_id = dataset.get("id")
        print(f"   Dataset ID: {dataset_id}")

        # Upload Excel file
        print(f"\n2. Uploading Excel file...")
        docs = upload_document(dataset_id, EXCEL_FILE)
        if not docs:
            print("   ERROR: Document upload failed")
            return None

        doc = docs[0] if isinstance(docs, list) else docs
        doc_id = doc.get("id")
        print(f"   Document ID: {doc_id}")

        # Start parsing
        print(f"\n3. Starting document parsing...")
        parse_result = start_parsing(dataset_id, [doc_id])
        print(f"   Parse request: {parse_result}")

        # Wait for parsing
        print(f"\n4. Waiting for parsing completion...")
        success, parsed_doc = wait_for_parsing(dataset_id, doc_id)

        if not success:
            print("   ERROR: Parsing failed or timed out")
            if parsed_doc:
                print(f"   Message: {parsed_doc.get('progress_msg', 'Unknown')}")
            return None

        # Get chunk count
        print(f"\n5. Getting chunks...")
        chunks = list_chunks(dataset_id, doc_id)
        chunk_count = len(chunks) if chunks else 0
        print(f"   Total chunks created: {chunk_count}")

        # Sample chunks
        if chunks and len(chunks) > 0:
            print(f"\n   Sample chunk (first):")
            content = chunks[0].get("content", "")[:200]
            print(f"   {content}...")

        # Run retrieval tests
        print(f"\n6. Running retrieval tests...")
        results = {}
        for i, question in enumerate(questions, 1):
            print(f"\n   Q{i}: {question}")
            retrieval_results = retrieve_chunks([dataset_id], question)

            if retrieval_results:
                print(f"   Found {len(retrieval_results)} results")
                if len(retrieval_results) > 0:
                    top_result = retrieval_results[0]
                    content = top_result.get("content", "")[:150]
                    similarity = top_result.get("similarity", 0)
                    print(f"   Similarity: {similarity:.3f}")
                    print(f"   Content: {content}...")
                results[question] = {
                    "count": len(retrieval_results),
                    "has_results": True,
                    "top_similarity": retrieval_results[0].get("similarity", 0) if retrieval_results else 0
                }
            else:
                print(f"   No results found")
                results[question] = {
                    "count": 0,
                    "has_results": False,
                    "top_similarity": 0
                }

        # Calculate metrics
        success_count = sum(1 for r in results.values() if r["has_results"])
        success_rate = success_count / len(questions) * 100
        avg_similarity = sum(r.get("top_similarity", 0) for r in results.values()) / len(questions)

        print(f"\n7. Test Summary:")
        print(f"   Chunk count: {chunk_count}")
        print(f"   Retrieval success rate: {success_rate:.1f}% ({success_count}/{len(questions)})")
        print(f"   Average top similarity: {avg_similarity:.3f}")

        return {
            "test_name": test_name,
            "chunk_method": chunk_method,
            "parser_config": parser_config,
            "dataset_id": dataset_id,
            "chunk_count": chunk_count,
            "retrieval_results": results,
            "success_rate": success_rate,
            "avg_similarity": avg_similarity
        }

    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        # Cleanup
        if dataset_id:
            print(f"\n8. Cleaning up dataset...")
            try:
                delete_dataset(dataset_id)
                print(f"   Dataset deleted")
            except Exception as e:
                print(f"   Cleanup error: {e}")

def main():
    print("RAGFlow Excel Optimization Test")
    print("=" * 60)
    print(f"Excel File: {EXCEL_FILE}")
    print(f"API URL: {BASE_URL}")

    # Check file exists
    if not os.path.exists(EXCEL_FILE):
        print(f"ERROR: Excel file not found: {EXCEL_FILE}")
        return

    # Test configurations
    tests = [
        # Test 1: Table chunking (recommended for structured data)
        {
            "name": "Test 1: Table Chunking (Default)",
            "chunk_method": "table",
            "parser_config": {
                "chunk_token_num": 512
            }
        },
        # Test 2: Naive chunking without html4excel
        {
            "name": "Test 2: Naive Chunking (Default)",
            "chunk_method": "naive",
            "parser_config": {
                "html4excel": False,
                "chunk_token_num": 512
            }
        },
        # Test 3: Naive chunking with html4excel
        {
            "name": "Test 3: Naive + HTML4Excel",
            "chunk_method": "naive",
            "parser_config": {
                "html4excel": True,
                "chunk_token_num": 512
            }
        },
        # Test 4: Table chunking with Korean-optimized token count
        {
            "name": "Test 4: Table + Korean Token Opt",
            "chunk_method": "table",
            "parser_config": {
                "chunk_token_num": 320
            }
        },
        # Test 5: Naive + html4excel with Korean optimization
        {
            "name": "Test 5: Naive + HTML + Korean Opt",
            "chunk_method": "naive",
            "parser_config": {
                "html4excel": True,
                "chunk_token_num": 320
            }
        }
    ]

    # Run tests
    all_results = []
    for test_config in tests:
        result = test_chunking_method(
            test_config["name"],
            test_config["chunk_method"],
            test_config["parser_config"],
            TEST_QUESTIONS
        )
        if result:
            all_results.append(result)

        # Brief pause between tests
        time.sleep(3)

    # Summary
    print("\n" + "=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)

    if all_results:
        print(f"\n{'Test Name':<35} {'Chunks':>8} {'Success':>10} {'Similarity':>12}")
        print("-" * 70)
        for result in all_results:
            print(f"{result['test_name']:<35} {result['chunk_count']:>8} {result['success_rate']:>9.1f}% {result['avg_similarity']:>11.3f}")

        # Find best configuration
        best = max(all_results, key=lambda x: (x['success_rate'], x['avg_similarity']))
        print(f"\n{'='*60}")
        print(f"RECOMMENDED CONFIGURATION")
        print(f"{'='*60}")
        print(f"Test: {best['test_name']}")
        print(f"Chunk Method: {best['chunk_method']}")
        print(f"Parser Config: {json.dumps(best['parser_config'], ensure_ascii=False, indent=2)}")
        print(f"Success Rate: {best['success_rate']:.1f}%")
        print(f"Avg Similarity: {best['avg_similarity']:.3f}")
    else:
        print("No successful tests completed")

if __name__ == "__main__":
    main()
