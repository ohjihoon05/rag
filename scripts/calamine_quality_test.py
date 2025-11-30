#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Excel Calamine Quality Test - 성능 + 정확도 + 할루시네이션 테스트
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

# Test Questions
ACCURACY_QUESTIONS = [
    {
        "question": "한소희 담당자의 총 거래 건수는 몇 건인가요?",
        "expected_keywords": ["289", "건"],
        "description": "담당자별 거래 건수 조회"
    },
    {
        "question": "제품E의 총 판매수량은 얼마인가요?",
        "expected_keywords": ["159", "726"],
        "description": "제품별 판매수량 집계"
    },
    {
        "question": "매출액이 가장 높은 담당자는 누구인가요?",
        "expected_keywords": ["이영희"],
        "description": "매출 1위 담당자"
    },
    {
        "question": "어떤 부서들이 있나요?",
        "expected_keywords": ["영업부", "인사부", "재무부"],
        "description": "부서 목록"
    },
    {
        "question": "서울 지역의 판매 데이터가 있나요?",
        "expected_keywords": ["서울", "있"],
        "description": "지역 데이터 유무"
    }
]

HALLUCINATION_QUESTIONS = [
    {
        "question": "김영수 담당자의 매출 실적은 어떻게 되나요?",
        "forbidden_keywords": ["김영수", "매출", "원", "건"],
        "expected_behavior": "데이터 없음 응답",
        "description": "존재하지 않는 담당자"
    },
    {
        "question": "제품Z의 판매현황을 알려주세요.",
        "forbidden_keywords": ["제품Z", "판매", "수량"],
        "expected_behavior": "데이터 없음 응답",
        "description": "존재하지 않는 제품"
    },
    {
        "question": "제주도 지역의 매출은 얼마인가요?",
        "forbidden_keywords": ["제주", "원", "매출액"],
        "expected_behavior": "데이터 없음 응답",
        "description": "존재하지 않는 지역"
    },
    {
        "question": "2024년 매출 데이터를 보여주세요.",
        "forbidden_keywords": ["2024년", "매출"],
        "expected_behavior": "데이터 없음 응답",
        "description": "존재하지 않는 기간"
    }
]

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
    if data.get("code") == 0:
        return data.get("data", {})
    raise Exception(f"Failed to create dataset: {data.get('message')}")

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
    if data.get("code") == 0:
        return data.get("data", [])
    raise Exception(f"Failed to upload: {data.get('message')}")

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
        docs_data = data.get("data", {})
        if isinstance(docs_data, dict):
            docs = docs_data.get("docs", [])
        else:
            docs = docs_data
        if docs and isinstance(docs, list) and len(docs) > 0:
            return docs[0]
    return None

def wait_for_parsing(dataset_id, doc_id):
    start = time.time()
    last_progress = -1
    while True:
        doc = get_document_status(dataset_id, doc_id)
        if doc:
            status = doc.get("run", "UNKNOWN")
            progress = doc.get("progress", 0)
            elapsed = int(time.time() - start)
            if progress != last_progress:
                print(f"  -> Status: {status}, Progress: {progress:.1%} ({elapsed}s)")
                last_progress = progress
            if status == "DONE" or (status == "RUNNING" and progress >= 1.0):
                return True, elapsed
            if status == "FAIL":
                return False, elapsed
        time.sleep(5)

def retrieve_chunks(dataset_ids, question, top_k=5):
    url = f"{BASE_URL}/api/v1/retrieval"
    payload = {"dataset_ids": dataset_ids, "question": question, "top_k": top_k}
    r = requests.post(url, headers=get_headers(), json=payload)
    data = r.json()
    if data.get("code") == 0:
        return data.get("data", {}).get("chunks", [])
    return []

def create_chat_assistant(name, dataset_ids):
    """Create a chat assistant linked to datasets"""
    url = f"{BASE_URL}/api/v1/chats"
    payload = {
        "name": name,
        "dataset_ids": dataset_ids,
        "llm": {"model_name": "qwen2.5:7b", "temperature": 0.1, "max_tokens": 512},
        "prompt": {
            "empty_response": "해당 데이터가 없습니다",
            "keywords_similarity_weight": 0.7,
            "opener": "Excel 데이터에 대해 질문해주세요.",
            "prompt": "You are an intelligent assistant. Please summarize the content of the knowledge base to answer the question. Please list the data in the knowledge base and answer in detail. When all knowledge base content is irrelevant to the question, your answer must include the sentence \"해당 데이터가 없습니다\". Answers need to consider chat history.\n      Here is the knowledge base:\n      {knowledge}\n      The above is the knowledge base.",
            "refine_multiturn": False,
            "rerank_model": "",
            "show_quote": True,
            "similarity_threshold": 0.2,
            "top_n": 5,
            "variables": [{"key": "knowledge", "optional": False}]
        }
    }
    r = requests.post(url, headers=get_headers(), json=payload)
    data = r.json()
    if data.get("code") == 0:
        return data.get("data", {})
    raise Exception(f"Failed to create chat: {data.get('message')}")

def create_session(chat_id):
    """Create a session for the chat"""
    url = f"{BASE_URL}/api/v1/chats/{chat_id}/sessions"
    payload = {"name": f"test_session_{int(time.time())}"}
    r = requests.post(url, headers=get_headers(), json=payload)
    data = r.json()
    if data.get("code") == 0:
        return data.get("data", {}).get("id")
    return None

def ask_question(chat_id, question, session_id=None):
    """Ask a question to the chat assistant - requires session_id"""
    url = f"{BASE_URL}/api/v1/chats/{chat_id}/completions"
    payload = {
        "question": question,
        "stream": False
    }
    if session_id:
        payload["session_id"] = session_id
    r = requests.post(url, headers=get_headers(), json=payload)
    data = r.json()
    if data.get("code") == 0:
        return data.get("data", {}).get("answer", "")
    print(f"    [Warning] API error: {data.get('message', 'unknown')}")
    return None

def delete_chat(chat_id):
    url = f"{BASE_URL}/api/v1/chats"
    r = requests.delete(url, headers=get_headers(), json={"ids": [chat_id]})
    return r.json()

def check_accuracy(answer, expected_keywords):
    """Check if answer contains expected keywords"""
    if not answer:
        return False, 0
    answer_lower = answer.lower()
    found = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    return found >= len(expected_keywords) / 2, found / len(expected_keywords)

def check_hallucination(answer, forbidden_keywords):
    """Check if answer generates forbidden content (hallucination)"""
    if not answer:
        return False, []  # No answer = no hallucination
    answer_lower = answer.lower()
    found_forbidden = [kw for kw in forbidden_keywords if kw.lower() in answer_lower]
    # If forbidden keywords found AND answer doesn't say "없" or "모르", it's hallucination
    if found_forbidden and "없" not in answer and "모르" not in answer:
        return True, found_forbidden
    return False, []

def run_quality_test():
    print("=" * 70)
    print("EXCEL CALAMINE QUALITY TEST")
    print("=" * 70)

    dataset_id = None
    chat_id = None
    results = {
        "parsing_time": 0,
        "accuracy_tests": [],
        "hallucination_tests": [],
        "summary": {}
    }

    try:
        # 1. Create dataset with calamine settings
        print("\n[1] Creating dataset (Naive + HTML4Excel)...")
        dataset_name = f"calamine_quality_test_{int(time.time())}"
        parser_config = {"html4excel": True, "chunk_token_num": 512}
        dataset = create_dataset(dataset_name, "naive", parser_config)
        dataset_id = dataset.get("id")
        print(f"    Dataset ID: {dataset_id}")

        # 2. Upload Excel file
        print("\n[2] Uploading Excel file...")
        start_upload = time.time()
        docs = upload_document(dataset_id, EXCEL_FILE)
        doc = docs[0] if isinstance(docs, list) else docs
        doc_id = doc.get("id")
        print(f"    Document ID: {doc_id}")

        # 3. Parse document
        print("\n[3] Parsing document...")
        start_parsing(dataset_id, [doc_id])
        success, parsing_time = wait_for_parsing(dataset_id, doc_id)
        results["parsing_time"] = parsing_time

        if not success:
            print("    PARSING FAILED!")
            return results

        print(f"    Parsing completed in {parsing_time} seconds")

        # 4. Create chat assistant
        print("\n[4] Creating chat assistant...")
        chat = create_chat_assistant(f"test_chat_{int(time.time())}", [dataset_id])
        chat_id = chat.get("id")
        print(f"    Chat ID: {chat_id}")

        # 4.1 Create session (required for completions API)
        print("\n[4.1] Creating session...")
        session_id = create_session(chat_id)
        print(f"    Session ID: {session_id}")

        # 5. Accuracy Tests
        print("\n[5] Running accuracy tests...")
        print("-" * 50)
        for i, test in enumerate(ACCURACY_QUESTIONS, 1):
            print(f"\n  Q{i}: {test['question']}")
            answer = ask_question(chat_id, test["question"], session_id)
            if answer:
                print(f"  A{i}: {answer[:200]}...")
                passed, score = check_accuracy(answer, test["expected_keywords"])
                status = "PASS" if passed else "FAIL"
                print(f"  -> {status} (score: {score:.0%})")
            else:
                answer = ""
                passed, score = False, 0
                print(f"  -> FAIL (no response)")

            results["accuracy_tests"].append({
                "question": test["question"],
                "answer": answer[:500] if answer else "",
                "passed": passed,
                "score": score,
                "description": test["description"]
            })
            time.sleep(1)  # Rate limiting

        # 6. Hallucination Tests
        print("\n[6] Running hallucination tests...")
        print("-" * 50)
        for i, test in enumerate(HALLUCINATION_QUESTIONS, 1):
            print(f"\n  H{i}: {test['question']}")
            answer = ask_question(chat_id, test["question"], session_id)
            if answer:
                print(f"  A{i}: {answer[:200]}...")
                is_hallucination, forbidden_found = check_hallucination(answer, test["forbidden_keywords"])
                if is_hallucination:
                    print(f"  -> HALLUCINATION DETECTED: {forbidden_found}")
                else:
                    print(f"  -> OK (no hallucination)")
            else:
                answer = ""
                is_hallucination = False
                forbidden_found = []
                print(f"  -> OK (no response)")

            results["hallucination_tests"].append({
                "question": test["question"],
                "answer": answer[:500] if answer else "",
                "is_hallucination": is_hallucination,
                "forbidden_found": forbidden_found,
                "description": test["description"]
            })
            time.sleep(1)

        # 7. Summary
        accuracy_passed = sum(1 for t in results["accuracy_tests"] if t["passed"])
        hallucination_count = sum(1 for t in results["hallucination_tests"] if t["is_hallucination"])

        results["summary"] = {
            "parsing_time_seconds": parsing_time,
            "accuracy_score": f"{accuracy_passed}/{len(ACCURACY_QUESTIONS)}",
            "accuracy_percent": accuracy_passed / len(ACCURACY_QUESTIONS) * 100,
            "hallucination_count": hallucination_count,
            "overall_pass": accuracy_passed >= 4 and hallucination_count == 0
        }

        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"  Parsing Time: {parsing_time} seconds")
        print(f"  Accuracy: {accuracy_passed}/{len(ACCURACY_QUESTIONS)} ({results['summary']['accuracy_percent']:.0f}%)")
        print(f"  Hallucinations: {hallucination_count}")
        print(f"  Overall: {'PASS' if results['summary']['overall_pass'] else 'FAIL'}")

        return results

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return results

    finally:
        # Cleanup
        print("\n[7] Cleanup...")
        if chat_id:
            try:
                delete_chat(chat_id)
                print("    Chat deleted")
            except:
                pass
        if dataset_id:
            try:
                delete_dataset(dataset_id)
                print("    Dataset deleted")
            except:
                pass

if __name__ == "__main__":
    results = run_quality_test()

    # Save results
    output_file = r"C:\Users\ohjh\ragflow\specs\003-excel-calamine-quality-test\test-results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to: {output_file}")
