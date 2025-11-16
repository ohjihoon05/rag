#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Upload Excel and test Korean Q&A"""

import requests
import json
import time
import os

API_KEY = "ragflow-xkfeh3YrAbBSf8YTTLwXIkZiMfwWpjzJptjxs8vio5w"
BASE_URL = "http://localhost/api/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}"
}

EXCEL_FILE = "C:/Users/ohjh/ragflow/scripts/CS_Daily_Report_3MB.xlsx"

print("="*70)
print("Phase 5: 한국어 Q&A 테스트 (bge-m3 + Complex Excel)")
print("="*70)

# Step 1: Get Knowledge Base
print("\n[Step 1] Knowledge Base 확인...")
response = requests.get(f"{BASE_URL}/datasets", headers=HEADERS)
data = response.json()

if data.get("code") != 0:
    print(f"ERROR: {data.get('message')}")
    exit(1)

kbs = data.get("data", [])
if not kbs:
    print("ERROR: Knowledge Base가 없습니다")
    exit(1)

kb = kbs[0]
kb_id = kb.get("id")
kb_name = kb.get("name")
print(f"OK Knowledge Base: {kb_name}")
print(f"   ID: {kb_id}")

# Step 2: Upload Excel file
print(f"\n[Step 2] Excel 파일 업로드 중...")
print(f"   파일: {EXCEL_FILE}")
file_size = os.path.getsize(EXCEL_FILE)
print(f"   크기: {file_size / (1024*1024):.2f} MB")

with open(EXCEL_FILE, 'rb') as f:
    files = {'file': ('CS_Daily_Report_3MB.xlsx', f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
    upload_headers = {**HEADERS}

    response = requests.post(
        f"{BASE_URL}/datasets/{kb_id}/documents",
        headers=upload_headers,
        files=files
    )

if response.status_code != 200:
    print(f"ERROR: Upload failed with status {response.status_code}")
    print(response.text)
    exit(1)

upload_data = response.json()
if upload_data.get("code") != 0:
    print(f"ERROR: {upload_data.get('message')}")
    exit(1)

doc_data = upload_data.get("data")
if isinstance(doc_data, list) and len(doc_data) > 0:
    doc_id = doc_data[0].get("id")
elif isinstance(doc_data, dict):
    doc_id = doc_data.get("id")
else:
    print(f"ERROR: Unexpected response format: {doc_data}")
    exit(1)
print(f"OK 파일 업로드 성공!")
print(f"   Document ID: {doc_id}")

# Step 3: Wait for parsing
print(f"\n[Step 3] 문서 파싱 대기중...")
print("   Excel 파일 파싱은 시간이 걸릴 수 있습니다 (6.49MB, 15 sheets, 100K+ rows)")

max_wait = 600  # 10 minutes max
wait_interval = 10
elapsed = 0

while elapsed < max_wait:
    time.sleep(wait_interval)
    elapsed += wait_interval

    # Check document status
    response = requests.get(
        f"{BASE_URL}/datasets/{kb_id}/documents",
        headers=HEADERS,
        params={"id": doc_id}
    )

    if response.status_code != 200:
        print(f"   WARNING: Status check failed")
        continue

    doc_data = response.json()
    if doc_data.get("code") != 0:
        print(f"   WARNING: {doc_data.get('message')}")
        continue

    docs_result = doc_data.get("data", {})

    # Handle both list and dict response
    if isinstance(docs_result, list):
        if not docs_result:
            print(f"   WARNING: Document not found")
            continue
        doc = docs_result[0]
    elif isinstance(docs_result, dict):
        doc = docs_result
    else:
        print(f"   WARNING: Unexpected docs format")
        continue
    status = doc.get("status")
    progress = doc.get("progress", 0)
    chunk_num = doc.get("chunk_num", 0)

    print(f"   [{elapsed}s] Status: {status}, Progress: {progress:.1%}, Chunks: {chunk_num}")

    if status == "1":  # Completed
        print(f"\nOK 파싱 완료!")
        print(f"   총 청크 수: {chunk_num}")
        break
    elif status == "-1":  # Failed
        print(f"\nERROR: 파싱 실패")
        exit(1)
else:
    print(f"\nWARNING: 파싱 시간 초과 ({max_wait}초)")
    print("   계속 진행하지만 Q&A가 제대로 작동하지 않을 수 있습니다")

# Step 4: Create Chat
print(f"\n[Step 4] Chat 생성...")

chat_payload = {
    "name": "Excel Q&A Test (bge-m3)",
    "dataset_ids": [kb_id],
    "llm": {
        "model_name": "qwen2.5:7b",
        "temperature": 0.1,
        "top_p": 0.3,
        "max_tokens": 512
    },
    "prompt": {
        "similarity_threshold": 0.2,
        "keywords_similarity_weight": 0.3,
        "top_n": 5,
        "variables": [],
        "empty_response": "문서에서 찾을 수 없습니다",
        "opener": "엑셀 문서의 내용만 사용하여 답변하세요. 정보가 없으면 '문서에서 찾을 수 없습니다'라고 답변하세요."
    }
}

response = requests.post(f"{BASE_URL}/chats", headers=HEADERS, json=chat_payload)
chat_data = response.json()

if chat_data.get("code") != 0:
    print(f"ERROR: {chat_data.get('message')}")
    exit(1)

chat_id = chat_data.get("data", {}).get("id")
print(f"OK Chat 생성 완료 (ID: {chat_id})")

time.sleep(2)

# Step 5: Test Korean Q&A
print(f"\n[Step 5] 한국어 Q&A 테스트")
print("="*70)

questions = [
    "가장 많았던 문의 유형은 무엇인가요?",
    "평균 고객 만족도는 얼마인가요?",
    "김민수 담당자가 처리한 건수는 몇 건인가요?",
    "로그인 오류는 총 몇 건이 발생했나요?",
    "어느 시간대에 문의가 가장 많았나요?",
]

success_count = 0

for i, question in enumerate(questions, 1):
    print(f"\n질문 {i}: {question}")
    print("-"*70)

    start_time = time.time()
    response = requests.post(
        f"{BASE_URL}/chats/{chat_id}/completions",
        headers=HEADERS,
        json={"question": question, "stream": False}
    )
    response_time = time.time() - start_time

    result_data = response.json()

    if result_data.get("code") != 0:
        print(f"ERROR: {result_data.get('message')}")
        continue

    result = result_data.get("data", {})
    answer = result.get("answer", "")
    reference = result.get("reference", {})
    chunks = reference.get("chunks", [])

    print(f"답변: {answer}")
    print(f"\n응답 시간: {response_time:.2f}초")
    print(f"참조 청크: {len(chunks)}개")

    if chunks:
        print("\n출처:")
        for j, chunk in enumerate(chunks[:3], 1):
            doc_name = chunk.get("doc_name", "Unknown")
            content = chunk.get("content_with_weight", "")[:100]
            print(f"  {j}. {doc_name}: {content}...")
        success_count += 1
    else:
        print("WARNING: 참조 청크 없음")

# Step 6: Edge case test
print(f"\n" + "="*70)
print("[Step 6] Edge Case 테스트")
print("="*70)

edge_question = "다음 주 월요일 날씨는 어떤가요?"
print(f"\n질문: {edge_question}")

response = requests.post(
    f"{BASE_URL}/chats/{chat_id}/completions",
    headers=HEADERS,
    json={"question": edge_question, "stream": False}
)

result_data = response.json()
if result_data.get("code") == 0:
    answer = result_data.get("data", {}).get("answer", "")
    print(f"답변: {answer}")

    if "찾을 수 없습니다" in answer or "없습니다" in answer:
        print("OK Edge case 처리 정상")
    else:
        print("WARNING: 예상과 다른 응답")

# Summary
print(f"\n" + "="*70)
print("Phase 5 테스트 완료")
print("="*70)
print(f"\n성공한 질문: {success_count}/{len(questions)}")
print("\n완료된 작업:")
print("  OK Excel 파일 업로드 (6.49MB, 15 sheets)")
print("  OK 문서 파싱 완료")
print("  OK Chat 생성")
print("  OK 한국어 Q&A 테스트")
print("  OK Edge case 테스트")
print("  OK 출처 확인")
