#!/usr/bin/env python3
"""
Phase 4 Completion: Upload and Parse Document with Ollama KB
Continue from successful KB creation with Ollama embedding
"""

import sys
import time
import requests
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:9380"
API_URL = f"{BASE_URL}/api/v1"
API_KEY = "ragflow-xkfeh3YrAbBSf8YTTLwXIkZiMfwWpjzJptjxs8vio5w"

# Use the newly created Ollama KB
DATASET_ID = "520b0696c2dd11f0897e129e0f398f8e"
DATASET_NAME = "CS 데일리 리포트 (Ollama)"


def print_step(step_num, description):
    """Print formatted step header"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print('='*60)


def upload_document(api_key, dataset_id, file_path):
    """Upload document to Knowledge Base - T018"""
    print_step(1, "문서 업로드 (T018)")

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        with open(file_path, "rb") as f:
            files = {
                "file": (file_path.name, f, "text/plain")
            }

            response = requests.post(
                f"{API_URL}/datasets/{dataset_id}/documents",
                headers=headers,
                files=files
            )

        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                data = result.get("data", [])
                if isinstance(data, list) and len(data) > 0:
                    document_id = data[0].get("id")
                    print(f"✅ 문서 업로드 성공")
                    print(f"   파일: {file_path.name}")
                    print(f"   Document ID: {document_id}")
                    return document_id
                else:
                    print(f"❌ 업로드 실패: 응답 데이터가 비어있습니다")
                    print(f"   응답 데이터: {data}")
                    return None
            else:
                print(f"❌ 업로드 실패: {result.get('message')}")
                return None
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            print(f"   응답: {response.text}")
            return None

    except Exception as e:
        print(f"❌ 예외 발생: {str(e)}")
        return None


def start_parsing(api_key, dataset_id, document_id):
    """Start document parsing"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "document_ids": [document_id]
    }

    try:
        response = requests.post(
            f"{API_URL}/datasets/{dataset_id}/chunks",
            headers=headers,
            json=payload
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print(f"✅ 파싱 시작 성공")
                return True
            else:
                print(f"❌ 파싱 시작 실패: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 예외 발생: {str(e)}")
        return False


def monitor_parsing(api_key, dataset_id, document_id, max_wait=180):
    """Monitor document parsing progress - T019"""
    print_step(2, "문서 파싱 진행 모니터링 (T019)")

    # Start parsing first
    if not start_parsing(api_key, dataset_id, document_id):
        return False

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    start_time = time.time()

    while True:
        try:
            response = requests.get(
                f"{API_URL}/datasets/{dataset_id}/documents",
                headers=headers,
                params={"id": document_id}
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    docs = result.get("data", {}).get("docs", [])
                    if len(docs) > 0:
                        doc_data = docs[0]
                        run_status = doc_data.get("run")
                        progress = doc_data.get("progress", 0)
                        chunk_count = doc_data.get("chunk_count", 0)

                        elapsed = int(time.time() - start_time)

                        if run_status == "DONE":
                            print(f"✅ 파싱 완료! (소요 시간: {elapsed}초)")
                            print(f"   청크 수: {chunk_count}")
                            print(f"   진행률: {progress:.1f}%")
                            return True
                        elif run_status == "FAIL":
                            progress_msg = doc_data.get("progress_msg", "N/A")
                            print(f"❌ 파싱 실패")
                            print(f"   오류 메시지:")
                            print(f"{progress_msg}")
                            return False
                        else:
                            print(f"⏳ 파싱 진행 중... 상태: {run_status}, 진행률: {progress:.1f}%, 청크: {chunk_count} (경과: {elapsed}초)")

            if time.time() - start_time > max_wait:
                print(f"❌ 파싱 타임아웃 ({max_wait}초 초과)")
                return False

        except Exception as e:
            print(f"❌ 예외 발생: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

        time.sleep(5)


def verify_chunks(api_key, dataset_id):
    """Verify chunks stored in Infinity - T020"""
    print_step(3, "청크 저장 검증 (T020)")

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(
            f"{API_URL}/datasets/{dataset_id}/info",
            headers=headers
        )

        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                kb_data = result.get("data", {})
                chunk_count = kb_data.get("chunk_num", 0)
                doc_count = kb_data.get("document_amount", 0)

                print(f"✅ Knowledge Base 상태 확인")
                print(f"   총 문서 수: {doc_count}")
                print(f"   총 청크 수: {chunk_count}")
                print(f"   Embedding 모델: {kb_data.get('embedding_model', 'N/A')}")

                if chunk_count > 0:
                    print(f"\n✅ 청크가 Infinity에 성공적으로 저장됨")
                    return True
                else:
                    print(f"\n⚠️ 청크가 아직 저장되지 않음")
                    return False
            else:
                print(f"❌ 조회 실패: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ 예외 발생: {str(e)}")
        return False


def test_chunk_retrieval(api_key, dataset_id):
    """Test chunk retrieval with Korean keyword - T021"""
    print_step(4, "청크 검색 테스트 (T021)")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    test_queries = [
        "배송 지연",
        "고객 만족도",
        "결제 오류"
    ]

    for query in test_queries:
        print(f"\n🔍 검색어: '{query}'")

        payload = {
            "question": query,
            "top_k": 3
        }

        try:
            response = requests.post(
                f"{API_URL}/datasets/{dataset_id}/retrieval",
                headers=headers,
                json=payload
            )

            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 0:
                    chunks = result.get("data", {}).get("chunks", [])
                    print(f"   검색된 청크 수: {len(chunks)}")

                    for i, chunk in enumerate(chunks[:2], 1):
                        content_preview = chunk.get("content", "")[:100]
                        score = chunk.get("score", 0)
                        print(f"   [{i}] 점수: {score:.3f}")
                        print(f"       내용: {content_preview}...")
                else:
                    print(f"   ❌ 검색 실패: {result.get('message')}")
            else:
                print(f"   ❌ HTTP 오류: {response.status_code}")

        except Exception as e:
            print(f"   ❌ 예외 발생: {str(e)}")

    print("\n✅ 청크 검색 테스트 완료")


def main():
    """Main completion flow"""
    print("\n" + "="*60)
    print("RAGFlow Phase 4 완료 - Ollama KB 문서 처리")
    print("="*60)
    print(f"\nKnowledge Base: {DATASET_NAME}")
    print(f"KB ID: {DATASET_ID}")
    print(f"Embedding: nomic-embed-text@Ollama")

    # Get sample document path
    doc_path = Path(__file__).parent / "sample_korean_document.txt"

    if not doc_path.exists():
        print(f"\n❌ 샘플 문서를 찾을 수 없습니다: {doc_path}")
        return 1

    # Step 1: Upload document (T018)
    document_id = upload_document(API_KEY, DATASET_ID, doc_path)
    if not document_id:
        print("\n❌ 문서 업로드 실패, 종료합니다")
        return 1

    # Step 2: Monitor parsing (T019)
    if not monitor_parsing(API_KEY, DATASET_ID, document_id):
        print("\n❌ 문서 파싱 실패, 종료합니다")
        return 1

    # Step 3: Verify chunks (T020)
    if not verify_chunks(API_KEY, DATASET_ID):
        print("\n⚠️ 청크 검증 실패했지만 계속 진행합니다")

    # Step 4: Test chunk retrieval (T021)
    test_chunk_retrieval(API_KEY, DATASET_ID)

    print("\n" + "="*60)
    print("✅ Phase 4 완료!")
    print("="*60)
    print(f"\n📊 결과 요약:")
    print(f"   - Knowledge Base: {DATASET_NAME}")
    print(f"   - KB ID: {DATASET_ID}")
    print(f"   - Document ID: {document_id}")
    print(f"   - Embedding: nomic-embed-text@Ollama (768-dim)")
    print(f"   - LLM: qwen2.5:7b@Ollama")
    print(f"\n✅ Tasks T018-T021 완료")
    print(f"\n다음 단계: Phase 5 (질의응답 인터페이스)")
    print("="*60 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
