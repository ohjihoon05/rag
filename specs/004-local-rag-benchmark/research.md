# Local RAG Benchmark Research

## Source Analysis

### Skald Blog Key Findings

**URL**: https://blog.yakkomajuri.com/blog/local-rag

#### 1. RAG Stack Components

| Component | Cloud Option | Local Option |
|-----------|--------------|--------------|
| Vector DB | - | Postgres + pgvector |
| Embeddings | Voyage AI | Sentence Transformers, bge-m3 |
| LLM | Claude | GPT-OSS 20B, llama.cpp |
| Reranker | - | Cross-encoder, bge-reranker-v2-m3 |
| Doc Parser | - | Docling |

#### 2. Performance Results

| Configuration | Score | Notes |
|---------------|-------|-------|
| Voyage + Claude | 9.45/10 | Best overall |
| Voyage + GPT-OSS 20B | 9.18/10 | Open LLM surprisingly good |
| Local Multilingual (bge-m3) | 8.63/10 | Good for diverse languages |
| Local English-only | 7.10/10 | Point queries OK, aggregation weak |

#### 3. Key Insights

1. **Embedding Quality Matters Most**: 임베딩 모델 선택이 검색 품질에 가장 큰 영향
2. **Multilingual Models Win**: 다국어 모델(bge-m3)이 단일 언어 모델보다 robust
3. **Reranking Helps**: 특히 복잡한 쿼리에서 reranking이 효과적
4. **LLM Less Critical**: 검색 품질이 좋으면 작은 LLM도 충분

### GeekNews Discussion Points

**URL**: https://news.hada.io/topic?id=24712

#### Community Insights

1. **Vector DB 필수성 논란**
   - 일부: BM25만으로도 충분할 수 있음
   - 반론: 의미론적 검색에는 벡터 필수

2. **Hybrid Search 추천**
   - 키워드(BM25) + 벡터 조합이 최적
   - RAGFlow도 이 방식 지원

3. **로컬 환경 한계**
   - GPU 없으면 임베딩 속도 느림
   - 대용량 문서에서 성능 저하

## RAGFlow vs Skald Comparison

| Feature | RAGFlow | Skald |
|---------|---------|-------|
| Vector DB | Elasticsearch | pgvector |
| Hybrid Search | Yes | Yes |
| Reranking | Optional | Optional |
| Doc Parsing | DeepDoc (자체) | Docling |
| Multi-language | Yes (bge-m3) | Yes (bge-m3) |

## Decisions

### 1. Test Approach
**Decision**: Direct Retrieval API 사용 (Chat Completions 불안정)

**Rationale**:
- Chat Completions API에 ES 벡터 저장 이슈 있음
- Direct Retrieval은 BM25 폴백으로 안정적 작동
- 검색 품질 테스트에 집중

**Alternatives Rejected**:
- Chat Completions: ES 벡터 문제로 차단됨

### 2. Embedding Model
**Decision**: bge-m3 유지

**Rationale**:
- 한국어 데이터 테스트
- Skald 벤치마크에서도 다국어 모델이 우수

### 3. Search Method Priority
**Decision**: Hybrid Search 중심 테스트

**Rationale**:
- Skald와 커뮤니티 모두 Hybrid 추천
- RAGFlow 기본 설정도 Hybrid

### 4. Evaluation Method
**Decision**: 키워드 매칭 + 수동 검토

**Rationale**:
- 자동화 가능한 기본 평가
- 복잡한 질문은 수동 검토 필요

## Technical Notes

### RAGFlow Retrieval API

```python
POST /api/v1/retrieval
{
    "dataset_ids": ["..."],
    "question": "한소희",
    "top_k": 10,
    "similarity_threshold": 0.2,
    "keywords_similarity_weight": 0.3  # 0=vector only, 1=keyword only
}
```

### Skald High TopK Strategy

Skald는 높은 TopK 값 사용:
- Vector search: top 100
- Post-reranking: top 50

→ RAGFlow에서도 top_k 증가 테스트 필요

## Open Questions

1. RAGFlow에서 reranker 설정 방법?
2. ES 벡터 저장 문제 해결 시 Chat Completions 재테스트?
3. Ollama 외 다른 임베딩 서비스 테스트?
