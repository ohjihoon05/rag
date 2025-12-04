# 009 Implementation Plan: 한글 키워드 검색 개선

## 문제 요약

**현상**: Q3 "영업부 담당자 목록" 질문에서 0 chunks 반환

**원인 분석 결과**:
1. ❌ ES 필드 매핑 문제 아님 - `content_ltks`는 검색 가능
2. ❌ Analyzer 문제 아님 - "영업부" 검색 시 2080건 매칭
3. ⚠️ **Vector Search 정확도 문제** - "영업부" 검색해도 다른 부서가 먼저 나옴
4. ⚠️ **Keyword Weight 문제** - vector 검색 결과가 keyword 검색을 override

## 검증된 사실

```python
# Retrieval API (threshold=0.0)
"영업부 담당자 목록" → 30 chunks 반환 ✅

# Chat API (threshold=0.1)
"영업부 담당자 목록" → 0 chunks 반환 ❌

# 차이점: Chat에서 threshold 필터링으로 제거됨
```

## 해결 전략

### Strategy A: Chat 파라미터 조정 (권장) ⭐
- `similarity_threshold`: 0.1 → 0.05
- `keywords_similarity_weight`: 0.2 → 0.5 (키워드 검색 비중 증가)

**장점**: 코드 변경 없음, 즉시 적용 가능
**단점**: 다른 질문에 영향 줄 수 있음

### Strategy B: 질문별 threshold 동적 조정
- 한글 키워드가 포함된 질문에 대해 threshold 낮춤
- RAGFlow 코드 수정 필요

### Strategy C: Hybrid Search 튜닝
- Vector weight vs Keyword weight 비율 조정
- dataset 레벨 설정 변경

## 구현 계획

### Phase 1: Strategy A 적용 및 테스트

#### T001: Chat 파라미터 수정
기존 Chat `d3a044d8d10f11f08f095aef2b223530` 업데이트:
```json
{
  "prompt": {
    "similarity_threshold": 0.05,
    "keywords_similarity_weight": 0.5,
    "top_n": 15
  }
}
```

#### T002: 테스트 스크립트 수정
`scripts/chat_api_test.py` 파라미터 업데이트

#### T003: 전체 테스트 실행
목표: Q3 PASS 달성

### Phase 2: 결과 검증

#### T004: 부작용 확인
- Q1-Q5 전체 테스트
- 새 파라미터가 다른 질문에 악영향 없는지 확인

#### T005: 최적 파라미터 탐색
- threshold: 0.05, 0.03, 0.01 테스트
- keyword_weight: 0.5, 0.6, 0.7 테스트

## 성공 기준

| 메트릭 | 현재 | 목표 |
|--------|------|------|
| Q3 References | 0 | >= 5 |
| Q3 Status | FAIL | PASS |
| 전체 정확도 | 80% (4/5) | 100% (5/5) |
| 다른 질문 영향 | N/A | 부작용 없음 |

## 테스트 명령어

```bash
# 파라미터 테스트
python scripts/chat_api_test.py

# Retrieval API 직접 테스트
curl -X POST http://localhost/api/v1/retrieval \
  -H "Authorization: Bearer ragflow-..." \
  -d '{"question": "영업부", "dataset_ids": ["550f..."], "similarity_threshold": 0.05}'
```

## 롤백 계획

실패 시 원래 파라미터로 복원:
- `similarity_threshold`: 0.1
- `keywords_similarity_weight`: 0.2
