# Feature Specification: Chat API 답변 품질 개선

**Version**: 1.0 | **Date**: 2025-12-04 | **Status**: Active

## Problem Statement

RAGFlow Chat API에서 검색은 성공하지만(6-8 chunks 반환) LLM이 데이터를 활용하지 못하고 "죄송합니다, 확인할 수 없습니다"라고 답변하는 문제가 발생.

### 현재 테스트 결과
- **chat_api_test.py**: 3/5 통과 (60%)
- **calamine_quality_test.py**: 2/5 정확도 (40%)
- 벡터 저장: `q_1024_vec` 정상 저장 확인

### 핵심 증상
1. 검색 성공 (6-8 chunks) → LLM "데이터 없다" 답변
2. 일부 쿼리 ("영업부", "매출액") → 0 chunks 반환
3. Retrieval API 에러: `AttributeError("'NoneType' object has no attribute 'get'")`

## Technical Environment

| 항목 | 값 |
|------|-----|
| Dataset ID | `550f506ecf8e11f092cc9e4ca9309b43` |
| Document ID | `6019bdb4cf8e11f0bbea9e4ca9309b43` |
| Test File | `daily_report_sample.xlsx` (6,000 rows) |
| Chunks | 474개 파싱 완료 |
| LLM | gpt-oss:20b@Ollama |
| Embedding | bge-m3@Ollama (1024 dims) |
| Vector Field | `q_1024_vec` |
| Storage | Elasticsearch 8.x |

## Improvement Strategies

### A. 프롬프트 개선 (Priority 1)
- LLM이 제공된 컨텍스트를 "자신의 데이터"로 인식하도록 수정
- 한국어 vs 영어 프롬프트 비교 테스트
- 데이터 기반 답변 강제 지시 추가

### B. 청크 품질 확인
- ES에 저장된 실제 청크 내용 검사
- 엑셀 데이터 청크화 품질 분석
- "영업부", "매출액" 키워드 포함 청크 존재 여부 확인

### C. 검색 파라미터 조정
- `similarity_threshold`: 0.2 → 0.1 테스트
- `keywords_similarity_weight`: 0.5 → 0.8 (키워드 가중치 증가)
- `top_n`: 8 → 15 증가

### D. 직접 디버깅
- curl 명령으로 단계별 API 테스트
- Retrieval API 에러 원인 조사
- Chat Completions vs Retrieval API 차이 분석

## Success Criteria

| 메트릭 | 현재 | 목표 |
|--------|------|------|
| Point Query 정확도 | 50% | >= 80% |
| Aggregation 정확도 | 0% | >= 60% |
| List Query 정확도 | 0% | >= 60% |
| 할루시네이션 | 1건 | 0건 |
| 평균 응답 시간 | 18초 | < 15초 |

## Test Questions (daily_report_sample.xlsx 기반)

1. **Point Query**: "한소희 담당자의 총 거래 건수는 몇 건인가요?"
2. **Aggregation**: "서울 지역에서 가장 많이 판매된 제품은 무엇인가요?"
3. **List Query**: "영업부에 속한 담당자들의 이름을 알려주세요."
4. **Top Query**: "매출액이 가장 높은 거래의 상세 정보를 알려주세요."
5. **Hallucination Check**: "김영수라는 담당자가 있나요?"

## Out of Scope

- RAGFlow 코어 코드 수정
- 새로운 LLM 모델 설치
- Elasticsearch 설정 변경
