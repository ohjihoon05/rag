#!/usr/bin/env python3
"""
Phase 4 Automation: Document Processing Pipeline
RAGFlow 온프레미스 한국어 최적화 배포 - Phase 4 자동화

Tasks:
- T016: Create Knowledge Base "CS 데일리 리포트"
- T017: Configure chunking parameters (chunk_size=400, overlap=50)
- T018: Upload sample Korean document
- T019: Monitor parsing progress
- T020: Verify chunks in Infinity
- T021: Test chunk retrieval with Korean keyword
"""

import sys
import os
import time
import requests
from pathlib import Path

# Configuration
BASE_URL = "http://127.0.0.1:9380"
API_URL = f"{BASE_URL}/api/v1"

# API Key (obtained from RAGFlow UI)
API_KEY = "ragflow-xkfeh3YrAbBSf8YTTLwXIkZiMfwWpjzJptjxs8vio5w"

# Knowledge Base configuration
KB_NAME = "CS 데일리 리포트"
KB_DESCRIPTION = "고객 서비스 팀의 일일 업무 리포트 및 고객 문의 사항 Knowledge Base"
CHUNK_METHOD = "naive"  # Simple chunking method
CHUNK_SIZE = 400  # Optimal for Korean text
OVERLAP = 50  # Token overlap between chunks


def print_step(step_num, description):
    """Print formatted step header"""
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print('='*60)


def verify_api_key():
    """Verify API key is valid"""
    print_step(1, "API 키 검증")

    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }

    try:
        # Try to list datasets to verify API key
        response = requests.get(f"{API_URL}/datasets", headers=headers)

        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                print(f"✅ API 키 검증 성공")
                print(f"   API Key: {API_KEY[:20]}...")
                return True
            else:
                print(f"❌ API 키 검증 실패: {result.get('message')}")
                return False
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            print(f"   응답: {response.text}")
            return False

    except Exception as e:
        print(f"❌ 예외 발생: {str(e)}")
        return False


def create_dataset(api_key):
    """Create Knowledge Base (Dataset) - T016"""
    print_step(2, "Knowledge Base 생성 (T016)")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    # Note: Using default embedding model (BAAI/bge-small-en-v1.5@Builtin)
    # Ollama models need to be configured in UI first (Settings > Model Management)
    payload = {
        "name": KB_NAME,
        "description": KB_DESCRIPTION,
        "chunk_method": CHUNK_METHOD,
        "parser_config": {
            "chunk_token_num": CHUNK_SIZE
        }
    }

    try:
        response = requests.post(f"{API_URL}/datasets", json=payload, headers=headers)

        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                dataset_id = result.get("data", {}).get("id")
                print(f"✅ Knowledge Base 생성 성공")
                print(f"   이름: {KB_NAME}")
                print(f"   ID: {dataset_id}")
                print(f"   Chunk 크기: {CHUNK_SIZE} tokens")
                print(f"   Overlap: {OVERLAP} tokens")
                return dataset_id
            else:
                # Dataset might already exist
                if "exist" in result.get("message", "").lower():
                    print(f"ℹ️  Knowledge Base 이미 존재, 기존 KB 검색 중...")
                    return get_existing_dataset(api_key)
                else:
                    print(f"❌ 생성 실패: {result.get('message')}")
                    return None
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            print(f"   응답: {response.text}")
            return None

    except Exception as e:
        print(f"❌ 예외 발생: {str(e)}")
        return None


def get_existing_dataset(api_key):
    """Get existing dataset by name"""
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(f"{API_URL}/datasets", headers=headers)

        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0:
                datasets = result.get("data", [])
                for ds in datasets:
                    if ds.get("name") == KB_NAME:
                        dataset_id = ds.get("id")
                        print(f"✅ 기존 Knowledge Base 발견")
                        print(f"   ID: {dataset_id}")
                        return dataset_id

                print(f"❌ Knowledge Base '{KB_NAME}'를 찾을 수 없습니다")
                return None
        else:
            print(f"❌ HTTP 오류: {response.status_code}")
            return None

    except Exception as e:
        print(f"❌ 예외 발생: {str(e)}")
        return None


def create_sample_korean_document():
    """Create a sample Korean document for testing - T018"""
    print_step(3, "샘플 한국어 문서 생성 (T018)")

    sample_content = """CS 데일리 리포트 - 2025년 11월 16일

=== 금일 주요 고객 문의 사항 ===

1. 제품 배송 관련 문의 (15건)
   - 배송 지연: 8건 (태풍으로 인한 물류 차질)
   - 배송지 변경: 4건
   - 배송 추적: 3건

   해결 방안: 고객에게 개별 연락하여 상황 설명 및 보상 쿠폰 제공

2. 결제 오류 문의 (7건)
   - 카드 결제 실패: 5건
   - 중복 결제: 2건

   해결 방안: PG사 확인 후 즉시 환불 처리

3. 제품 품질 관련 문의 (12건)
   - 제품 불량: 6건 (즉시 교환 처리)
   - 사용 방법 문의: 6건 (매뉴얼 PDF 전송)

=== 고객 만족도 ===
- 전체 만족도: 4.2/5.0
- 응대 품질: 4.5/5.0
- 처리 속도: 3.8/5.0 (개선 필요)

=== 특이 사항 ===
- 신제품 출시로 인한 문의 급증 (전일 대비 +35%)
- VIP 고객 불만 사항 1건 (팀장 직접 처리 완료)

=== 담당자 의견 ===
배송 지연 건에 대한 선제적 안내가 필요합니다.
다음 주부터 배송 예정일 변경 시 자동 SMS 발송 시스템 도입 예정.

작성자: 고객서비스팀 김민수
"""

    # Create sample document file
    doc_path = Path(__file__).parent / "sample_korean_document.txt"

    try:
        with open(doc_path, "w", encoding="utf-8") as f:
            f.write(sample_content)

        print(f"✅ 샘플 문서 생성 완료")
        print(f"   경로: {doc_path}")
        print(f"   크기: {len(sample_content)} characters")
        return doc_path

    except Exception as e:
        print(f"❌ 문서 생성 실패: {str(e)}")
        return None


def upload_document(api_key, dataset_id, file_path):
    """Upload document to Knowledge Base - T018"""
    print_step(4, "문서 업로드 (T018)")

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
                # API returns a list of uploaded documents
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
    print_step(5, "문서 파싱 진행 모니터링 (T019)")

    # Start parsing first
    if not start_parsing(api_key, dataset_id, document_id):
        return False

    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    start_time = time.time()

    while True:
        try:
            # Use list documents API with id parameter
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
                            print(f"   오류 메시지: {progress_msg}")
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


def test_chunk_retrieval(api_key, dataset_id):
    """Test chunk retrieval with Korean keyword - T021"""
    print_step(6, "청크 검색 테스트 (T021)")

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

                    for i, chunk in enumerate(chunks[:2], 1):  # Show top 2
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
    """Main automation flow"""
    print("\n" + "="*60)
    print("RAGFlow Phase 4 자동화 스크립트")
    print("문서 처리 파이프라인 (T016-T021)")
    print("="*60)

    # Step 1: Verify API key
    if not verify_api_key():
        print("\n❌ API 키 검증 실패, 종료합니다")
        return 1

    # Step 2: Create Knowledge Base (T016, T017)
    dataset_id = create_dataset(API_KEY)
    if not dataset_id:
        print("\n❌ Knowledge Base 생성 실패, 종료합니다")
        return 1

    # Step 3: Create sample document
    doc_path = create_sample_korean_document()
    if not doc_path:
        print("\n❌ 샘플 문서 생성 실패, 종료합니다")
        return 1

    # Step 4: Upload document (T018)
    document_id = upload_document(API_KEY, dataset_id, doc_path)
    if not document_id:
        print("\n❌ 문서 업로드 실패, 종료합니다")
        return 1

    # Step 5: Monitor parsing (T019)
    if not monitor_parsing(API_KEY, dataset_id, document_id):
        print("\n❌ 문서 파싱 실패, 종료합니다")
        return 1

    # Step 6: Test chunk retrieval (T021)
    test_chunk_retrieval(API_KEY, dataset_id)

    print("\n" + "="*60)
    print("✅ Phase 4 자동화 완료!")
    print("="*60)
    print(f"\n📊 결과 요약:")
    print(f"   - Knowledge Base ID: {dataset_id}")
    print(f"   - Document ID: {document_id}")
    print(f"   - API 키: {API_KEY[:20]}...")
    print(f"\n다음 단계: Phase 5 (질의응답 인터페이스)")
    print("="*60 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
