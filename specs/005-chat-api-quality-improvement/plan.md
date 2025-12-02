# Implementation Plan: Chat API 답변 품질 개선

**Branch**: `main` | **Date**: 2025-12-03 | **Spec**: [spec.md](spec.md)

## Summary

RAGFlow Chat API의 답변 품질을 개선하기 위한 4가지 전략(A/B/C/D) 실행 계획

## Technical Context

- **Language**: Python 3.11
- **RAGFlow Version**: Latest (docker-ragflow-gpu-1)
- **LLM**: qwen2.5:7b@Ollama
- **Embedding**: bge-m3@Ollama (1024 dims)
- **Storage**: Elasticsearch 8.x
- **Test Data**: daily_report_sample.xlsx (6,000 rows, 474 chunks)

## Implementation Tasks

### Task 1: 프롬프트 개선 테스트 (Strategy A)

**Goal**: 한국어 프롬프트로 LLM이 검색된 데이터를 활용하도록 유도

**Changes**:
1. `calamine_quality_test.py`의 `create_chat_assistant()` 수정
2. 프롬프트를 한국어로 변경
3. 데이터 활용 강제 지시 추가

**Test**:
```bash
python scripts/calamine_quality_test.py
```

**Expected**: 정확도 40% → 70%+

---

### Task 2: 검색 파라미터 조정 (Strategy C)

**Goal**: 더 많은 관련 청크를 LLM에 제공

**Changes**:
| 파라미터 | 현재 | 변경 |
|----------|------|------|
| similarity_threshold | 0.2 | 0.1 |
| keywords_similarity_weight | 0.7 | 0.8 |
| top_n | 5-8 | 15 |

**Test**:
- 동일 5개 질문으로 테스트
- 반환되는 chunks 수 비교

---

### Task 3: 테스트 스크립트 통합

**Goal**: 단일 스크립트로 A/B/C/D 전략 비교 테스트

**New Script**: `scripts/chat_quality_improvement_test.py`

**Features**:
- 다양한 프롬프트 설정 테스트
- 파라미터 조합 테스트
- 결과 비교 리포트 생성

---

### Task 4: 결과 분석 및 최적 설정 도출

**Goal**: 최적의 프롬프트 + 파라미터 조합 결정

**Deliverables**:
- 테스트 결과 JSON
- 최적 설정 문서화
- 권장 사항 정리

## Success Criteria

| 메트릭 | Baseline | Target |
|--------|----------|--------|
| Point Query | 50% | >= 80% |
| Aggregation | 0% | >= 60% |
| List Query | 0% | >= 60% |
| Hallucination | 1건 | 0건 |
| Response Time | 18s | < 15s |

## File Changes

```
scripts/
├── calamine_quality_test.py  # Modify: prompt improvement
├── chat_api_test.py          # Modify: parameter tuning
└── chat_quality_improvement_test.py  # New: combined test

specs/005-chat-api-quality-improvement/
├── spec.md      # Created
├── research.md  # Created
├── plan.md      # This file
└── test-results.json  # Generated after test
```

## Notes

- SDK API `/api/v1/chats` POST/PUT에 버그 있음 (요청 본문 파싱 실패)
- 우회 방법: 테스트 스크립트에서 직접 Chat 생성 후 completions 호출
- 또는 WebUI에서 Chat 생성 후 ID 사용
