# Local RAG Benchmark Test

## Overview

Skald 블로그의 Local RAG 벤치마크 방법론을 참고하여 RAGFlow의 RAG 성능을 테스트합니다.

**참고 자료**:
- [Skald Blog - Local RAG](https://blog.yakkomajuri.com/blog/local-rag)
- [GeekNews 토론](https://news.hada.io/topic?id=24712)

## Objective

RAGFlow의 다양한 검색 방식 및 모델 조합별 성능을 측정하고 비교합니다.

## Test Configurations

### 1. Embedding Models

| 모델 | 특징 | 용도 |
|------|------|------|
| bge-m3 (현재 설정) | 다국어 지원, 1024 dim | 한국어 테스트 기본 |
| all-MiniLM-L6-v2 | 영어 최적화, 빠름 | 영어 비교 테스트 |

### 2. Search Methods

| 방식 | 설명 | RAGFlow 설정 |
|------|------|--------------|
| Vector Only | 벡터 유사도 검색만 | similarity_threshold 높게 |
| Keyword Only (BM25) | 키워드 검색만 | keywords_similarity_weight: 1.0 |
| Hybrid | 벡터 + 키워드 조합 | keywords_similarity_weight: 0.3~0.7 |

### 3. Reranking

| 옵션 | 모델 |
|------|------|
| No Rerank | - |
| With Rerank | bge-reranker-v2-m3 |

### 4. LLM Models

| 모델 | 용도 |
|------|------|
| qwen2.5:7b (현재) | 기본 테스트 |
| llama3.2:3b | 경량 비교 |

## Test Dataset

**파일**: `daily_report_sample.xlsx`
- 6,000 rows 한국어 영업 데이터
- 컬럼: 날짜, 담당자, 부서, 지역, 제품, 판매수량, 매출액

## Test Questions

### Type 1: Point Query (단일 정보 조회)
> 특정 데이터 포인트를 찾는 질문

1. "한소희 담당자의 총 거래 건수는?" → 289건
2. "제품E의 총 판매수량은?" → 159,726
3. "서울 지역의 판매 데이터가 있나요?" → 있음

### Type 2: Aggregation Query (집계 질문)
> 여러 데이터를 종합해야 하는 질문

4. "매출액이 가장 높은 담당자는?" → 이영희
5. "어떤 부서들이 있나요?" → 영업부, 인사부, 재무부 등

### Type 3: Hallucination Check (환각 테스트)
> 존재하지 않는 데이터에 대한 질문

6. "김영수 담당자 매출은?" → 데이터 없음
7. "제품Z 판매현황은?" → 데이터 없음
8. "제주도 지역 매출은?" → 데이터 없음

## Evaluation Metrics

### 1. Accuracy Score
- 정답 키워드 포함 여부
- 5점 척도 (0-불일치, 5-완전일치)

### 2. Hallucination Rate
- 거짓 데이터 생성 비율
- 목표: 0%

### 3. Retrieval Quality
- Top-K chunks 관련성
- Reference chunks 수

### 4. Response Time
- 검색 시간
- 전체 응답 시간

## Success Criteria

| 메트릭 | 목표 |
|--------|------|
| Point Query 정확도 | >= 80% |
| Aggregation Query 정확도 | >= 60% |
| Hallucination Rate | 0% |
| 평균 응답 시간 | < 10초 |

## Skald 벤치마크 결과 참고

| 설정 | 점수 |
|------|------|
| Cloud (Voyage + Claude) | 9.45/10 |
| Hybrid (Voyage + GPT-OSS) | 9.18/10 |
| Local 다국어 | 8.63/10 |
| Local 영어 전용 | 7.10/10 |

## Dependencies

- RAGFlow 서버 실행 중
- Ollama 모델: bge-m3, qwen2.5:7b
- 테스트 데이터셋 업로드 완료
