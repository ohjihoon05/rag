#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Chat API Quality Test
daily_report_sample.xlsx 데이터를 이용한 질문-응답 품질 테스트
"""

import time
import json
import requests
from datetime import datetime

# Configuration
API_KEY = "ragflow-xkfeh3YrAbBSf8YTTLwXIkZiMfwWpjzJptjxs8vio5w"
BASE_URL = "http://localhost"
CHAT_ID = "2bfca06ccf7211f0bc1a0eb8c55eee50"  # test_debug_1764674970

# 5개 테스트 질문 (daily_report_sample.xlsx 기반)
TEST_QUESTIONS = [
    {
        "question": "한소희 담당자의 총 거래 건수는 몇 건인가요?",
        "expected_keywords": ["한소희", "거래", "건수"],
        "expected_answer_hint": "한소희 담당자 관련 데이터",
        "type": "point_query"
    },
    {
        "question": "서울 지역에서 가장 많이 판매된 제품은 무엇인가요?",
        "expected_keywords": ["서울", "제품", "판매"],
        "expected_answer_hint": "서울 지역 판매 데이터",
        "type": "aggregation"
    },
    {
        "question": "영업부에 속한 담당자들의 이름을 알려주세요.",
        "expected_keywords": ["영업부", "담당자"],
        "expected_answer_hint": "영업부 담당자 목록",
        "type": "list_query"
    },
    {
        "question": "매출액이 가장 높은 거래의 상세 정보를 알려주세요.",
        "expected_keywords": ["매출액", "높은", "거래"],
        "expected_answer_hint": "최고 매출 거래 정보",
        "type": "top_query"
    },
    {
        "question": "김영수라는 담당자가 있나요?",
        "expected_keywords": ["김영수", "담당자"],
        "expected_answer_hint": "존재하지 않는 데이터 처리",
        "type": "hallucination_check"
    },
]


def get_headers():
    return {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }


def create_session(chat_id):
    """Create a new chat session"""
    url = f"{BASE_URL}/api/v1/chats/{chat_id}/sessions"
    payload = {"name": f"test_session_{int(time.time())}"}

    r = requests.post(url, headers=get_headers(), json=payload)
    data = r.json()
    if data.get("code") == 0:
        return data.get("data", {}).get("id")
    print(f"Session creation failed: {data}")
    return None


def ask_question(chat_id, session_id, question):
    """Send a question and get streaming response"""
    url = f"{BASE_URL}/api/v1/chats/{chat_id}/completions"
    payload = {
        "question": question,
        "session_id": session_id,
        "stream": False  # Non-streaming for easier parsing
    }

    start_time = time.time()
    r = requests.post(url, headers=get_headers(), json=payload)
    elapsed = time.time() - start_time

    data = r.json()
    if data.get("code") == 0:
        answer_data = data.get("data", {})
        answer = answer_data.get("answer", "")
        references = answer_data.get("reference", {}).get("chunks", [])
        return {
            "answer": answer,
            "references": len(references),
            "elapsed": elapsed,
            "success": True
        }
    return {
        "answer": f"Error: {data.get('message', 'Unknown error')}",
        "references": 0,
        "elapsed": elapsed,
        "success": False
    }


def evaluate_response(question_info, response):
    """Evaluate the quality of the response"""
    answer = response.get("answer", "").lower()

    # Check keyword coverage
    keywords_found = 0
    for kw in question_info["expected_keywords"]:
        if kw.lower() in answer:
            keywords_found += 1
    keyword_coverage = keywords_found / len(question_info["expected_keywords"]) if question_info["expected_keywords"] else 0

    # Check for hallucination indicators
    hallucination_indicators = ["죄송합니다", "찾을 수 없습니다", "없습니다", "not found", "sorry"]
    is_negative_response = any(ind in answer.lower() for ind in hallucination_indicators)

    # For hallucination check questions, a negative response is good
    if question_info["type"] == "hallucination_check":
        quality_score = 1.0 if is_negative_response else 0.5
    else:
        # For other questions, we want positive responses with good keyword coverage
        quality_score = keyword_coverage * 0.7 + (0.3 if response["references"] > 0 else 0)

    return {
        "keyword_coverage": keyword_coverage,
        "has_references": response["references"] > 0,
        "is_negative": is_negative_response,
        "quality_score": quality_score
    }


def run_test():
    print("=" * 70)
    print("CHAT API QUALITY TEST")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Create session
    print("\n[1] Creating chat session...")
    session_id = create_session(CHAT_ID)
    if not session_id:
        print("Failed to create session!")
        return
    print(f"Session created: {session_id}")

    # Run tests
    print("\n[2] Running 5 Question Tests...")
    print("-" * 70)

    results = []
    total_score = 0

    for i, q in enumerate(TEST_QUESTIONS, 1):
        print(f"\nQ{i}: {q['question']}")
        print(f"    Type: {q['type']}")

        response = ask_question(CHAT_ID, session_id, q["question"])
        evaluation = evaluate_response(q, response)

        # Print response summary
        answer_preview = response["answer"][:200] + "..." if len(response["answer"]) > 200 else response["answer"]
        print(f"    Answer: {answer_preview}")
        print(f"    References: {response['references']} chunks")
        print(f"    Time: {response['elapsed']:.2f}s")
        print(f"    Keyword Coverage: {evaluation['keyword_coverage']:.0%}")
        print(f"    Quality Score: {evaluation['quality_score']:.0%}")

        status = "PASS" if evaluation['quality_score'] >= 0.5 else "FAIL"
        print(f"    Status: {status}")

        results.append({
            "question": q["question"],
            "type": q["type"],
            "response": response,
            "evaluation": evaluation,
            "status": status
        })
        total_score += evaluation['quality_score']

        time.sleep(1)  # Rate limiting

    # Summary
    avg_score = total_score / len(TEST_QUESTIONS)
    pass_count = sum(1 for r in results if r["status"] == "PASS")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Questions: {len(TEST_QUESTIONS)}")
    print(f"Passed: {pass_count}/{len(TEST_QUESTIONS)}")
    print(f"Average Quality Score: {avg_score:.0%}")
    print(f"Average Response Time: {sum(r['response']['elapsed'] for r in results)/len(results):.2f}s")

    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "chat_id": CHAT_ID,
        "session_id": session_id,
        "results": results,
        "summary": {
            "total": len(TEST_QUESTIONS),
            "passed": pass_count,
            "average_score": avg_score
        }
    }

    output_file = r"C:\Users\ohjh\ragflow\specs\004-local-rag-benchmark\chat-api-results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2, default=str)
    print(f"\nResults saved to: {output_file}")

    return results


if __name__ == "__main__":
    run_test()
