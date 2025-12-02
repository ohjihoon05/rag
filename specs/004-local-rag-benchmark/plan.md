# Implementation Plan: Local RAG Benchmark

**Branch**: `main` | **Date**: 2025-12-02 | **Spec**: [spec.md](spec.md)

## Summary

Skald 블로그의 Local RAG 벤치마크 방법론을 참고하여 RAGFlow의 검색 품질을 테스트합니다.
Direct Retrieval API를 사용하여 다양한 검색 설정의 성능을 비교합니다.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: requests, RAGFlow API
**Storage**: Elasticsearch (RAGFlow 내장)
**Testing**: pytest (optional), 수동 실행
**Target Platform**: Windows + Docker
**Performance Goals**: 응답 시간 < 10초, 정확도 >= 60%
**Constraints**: ES 벡터 저장 이슈로 Chat Completions 사용 불가

## Test Strategy

### Phase 1: Direct Retrieval 테스트

Chat Completions 대신 Direct Retrieval API로 검색 품질 테스트:

```python
POST /api/v1/retrieval
{
    "dataset_ids": ["..."],
    "question": "한소희",
    "top_k": 30,
    "similarity_threshold": 0.2,
    "keywords_similarity_weight": 0.3
}
```

### Phase 2: 파라미터 변경 테스트

| Test Case | keywords_similarity_weight | top_k |
|-----------|---------------------------|-------|
| Vector Heavy | 0.1 | 30 |
| Balanced | 0.5 | 30 |
| Keyword Heavy | 0.9 | 30 |
| High TopK | 0.5 | 100 |

### Phase 3: 결과 분석

- 검색된 chunks 품질 평가
- 정답 포함 여부 확인
- 응답 시간 측정

## Project Structure

```text
specs/004-local-rag-benchmark/
├── spec.md              # 테스트 명세
├── research.md          # 기술 조사 결과
├── plan.md              # 이 파일
└── test-results.json    # 테스트 결과 (실행 후 생성)

scripts/
└── local_rag_benchmark.py  # 벤치마크 스크립트
```

## Implementation Tasks

### Task 1: 벤치마크 스크립트 작성

기존 `calamine_quality_test.py` 기반으로 수정:
- Direct Retrieval API 중심
- 파라미터 변경 테스트 추가
- 결과 JSON 저장

### Task 2: 테스트 실행

1. 기존 데이터셋 확인 또는 새로 생성
2. 각 파라미터 조합별 테스트
3. 결과 수집

### Task 3: 결과 분석

- Skald 결과와 비교
- 최적 파라미터 도출
- 개선 방향 제안

## Success Criteria

| 메트릭 | 목표 |
|--------|------|
| Point Query 정확도 | >= 80% |
| Chunk 검색 성공률 | >= 90% |
| 평균 검색 시간 | < 5초 |

## Notes

- Chat Completions API는 ES 벡터 문제로 사용 불가
- Direct Retrieval은 BM25 폴백으로 작동 중
- 벡터 검색 정상화 후 재테스트 필요
