# Chat Completions API Fix

## Overview

RAGFlow의 Chat Completions API (`/api/v1/chats/{id}/completions`)에서 검색 결과가 0으로 반환되는 문제를 해결합니다.

## Problem Statement

### 현상
- Direct Retrieval API (`/api/v1/retrieval`) → **정상 작동** (30 chunks 반환)
- Chat Completions API (`/api/v1/chats/{id}/completions`) → **실패** (0 chunks, embedding 오류)

### 오류 메시지
```
WARNING: The dimension of query and chunk do not match: 0 vs. 0
ValueError: Found array with 0 feature(s) (shape=(1, 0)) while a minimum of 1 is required by check_pairwise_arrays.
```

## Root Cause Analysis

### Issue 1: Session ID Required (CRITICAL)

**위치**: `api/apps/sdk/session.py:126-127`

```python
if not req.get("session_id"):
    req["question"] = ""
```

**문제**: `session_id`가 제공되지 않으면 질문이 빈 문자열로 설정됩니다.

**영향**: 모든 검색이 빈 질문으로 실행되어 결과가 없음.

### Issue 2: Embedding Dimension 0 Error (BLOCKING)

**위치**: `api/db/services/dialog_service.py` → `retriever.retrieval()` 호출

**현상**:
- `dialog_service.py`에서 `LLMBundle` 초기화 후 embedding 호출 시 0 차원 반환
- `doc.py`의 direct retrieval에서는 동일한 `LLMBundle` 사용 시 정상 작동

**추정 원인**:
1. `LLMBundle` 인스턴스 초기화 차이
2. embedding 모델 캐싱 문제
3. `hybrid_similarity` 함수의 tensor 처리 문제

## Functional Requirements

### FR-1: Session ID 없이도 질문 처리
- `session_id` 없이 completions 호출 시에도 `question` 파라미터 유지
- 기존 동작(세션 기반 대화)과 새로운 동작(단일 질문) 모두 지원

### FR-2: Embedding 정상 작동
- Chat completions에서 embedding이 올바른 차원으로 생성되어야 함
- Direct retrieval API와 동일한 검색 결과 반환

### FR-3: 테스트 검증
- 수정 후 품질 테스트(calamine_quality_test.py) 통과
- Accuracy 테스트 최소 60% 이상

## Non-Functional Requirements

### NFR-1: 하위 호환성
- 기존 session_id 기반 API 호출은 그대로 작동
- 기존 클라이언트 코드 변경 불필요

### NFR-2: 성능
- 검색 응답 시간 5초 이내

## Affected Files

- `api/apps/sdk/session.py` - session_id 필수 로직
- `api/db/services/dialog_service.py` - embedding 및 retrieval 로직
- `rag/nlp/query.py` - hybrid_similarity 함수
- `api/db/services/llm_service.py` - LLMBundle 클래스

## Success Criteria

1. `session_id` 없이 completions API 호출 가능
2. Chat completions에서 embedding 정상 생성 (dimension > 0)
3. 검색 결과 반환 (chunks > 0)
4. 품질 테스트 통과 (accuracy >= 60%)

## Test Data

- Dataset: `test_nohtml_1764510007` (474 chunks, bge-m3@Ollama embedding)
- Test file: `daily_report_sample.xlsx` (6000 rows, Korean)
- Query: "한소희" (담당자 이름)
