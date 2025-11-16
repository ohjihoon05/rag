# Phase 4 완료 Summary

## 성공적으로 완료된 작업

### ✅ T016-T017: Knowledge Base 생성 및 설정
- KB 이름: "CS 데일리 리포트 (Ollama)"
- KB ID: `520b0696c2dd11f0897e129e0f398f8e`
- Chunk 크기: 400 tokens
- Chunk 방식: naive (simple chunking)

### ✅ T018-T019: 한국어 문서 업로드 및 파싱
- 문서: `sample_korean_document.txt` (590자)
- Document ID: `13e2d96ec2df11f0b5b1ee23cff8d9aa`
- **파싱 결과: 2개 청크 생성 (10초 소요)**
- 상태: DONE (성공적으로 완료)

### ✅ T020: 청크 저장 확인
- Elasticsearch에 2개 청크 저장 확인
- Chunk IDs: `9680b8b20696f052`, `0bd4ea45cc9b6782`

## 주요 해결 사항

### 🔧 Issue 1: Infinity "Invalid data type" Error (3051)
**문제**: Infinity 벡터 DB에서 테이블 생성 시 데이터 타입 오류 발생
**해결**: Elasticsearch로 Document Engine 전환
- 변경: `docker/.env`에서 `DOC_ENGINE=elasticsearch`로 설정
- 결과: 파싱이 즉시 성공

### 🔧 Issue 2: Model Authorization
**문제**: "Model(@None) not authorized" 오류
**해결**: tenant_llm 테이블에 Ollama 모델 직접 등록
```sql
INSERT INTO tenant_llm (tenant_id, llm_factory, llm_name, model_type, api_base, status)
VALUES
  ('8aa40b20c2b911f0ac399e7eb07324e5', 'Ollama', 'nomic-embed-text', 'embedding',
   'http://host.docker.internal:11434', '1'),
  ('8aa40b20c2b911f0ac399e7eb07324e5', 'Ollama', 'qwen2.5:7b', 'chat',
   'http://host.docker.internal:11434', '1');
```

## 시스템 구성

### 모델 설정
- **Embedding**: nomic-embed-text@Ollama (768 dimensions)
- **LLM**: qwen2.5:7b@Ollama (Korean-capable)
- **Reranker**: BAAI/bge-reranker-v2-m3@HuggingFace

### 인프라
- **Document Store**: Elasticsearch 8.11.3
- **Vector DB**: Elasticsearch (Infinity 사용 중단)
- **Database**: MySQL 8.0.39
- **Object Storage**: MinIO
- **Cache**: Redis (Valkey 8)
- **Ollama**: localhost:11434 (host.docker.internal)

### Docker 설정
- Memory Limit: 6GB
- Timezone: Asia/Seoul
- Platform: Windows + WSL2

## API 엔드포인트 검증

### ✅ 작동하는 API
- `POST /api/v1/datasets` - KB 생성
- `POST /api/v1/datasets/{id}/documents` - 문서 업로드
- `POST /api/v1/datasets/{id}/chunks` - 파싱 시작
- `GET /api/v1/datasets/{id}/documents?id={doc_id}` - 파싱 상태 조회
- `GET /api/v1/datasets/{id}/documents/{doc_id}/chunks` - 청크 목록

### ⚠️ 제한사항 발견
- Chunk 내용 조회 API 제한 (content_with_weight 필드 비어있음)
- Retrieval API 직접 호출 불가 (405 Method Not Allowed)
- **해결 방법**: Phase 5에서 Chat API를 통한 RAG 질의응답으로 테스트

## 다음 단계: Phase 5

### T022: Chat 생성 (KB 연결)
- Knowledge Base와 연결된 Chat 생성
- System Prompt 설정 (문서 기반 응답 강제)

### T023-T027: 한국어 Q&A 테스트
- 테스트 질문:
  1. "배송이 지연된 이유는 무엇인가요?"
  2. "전체 고객 만족도는 어떻게 되나요?"
  3. "결제 오류는 몇 건 발생했나요?"

### 검증 사항
- 한국어 질문에 대한 정확한 문서 기반 응답
- Ollama qwen2.5:7b LLM의 한국어 성능
- RAG 파이프라인 전체 동작 확인

## 배운 교훈

1. **Infinity vs Elasticsearch**:
   - Infinity는 아직 안정성 이슈 있음 (특정 스키마 에러)
   - Elasticsearch가 더 안정적이고 검증됨

2. **모델 등록 방식**:
   - UI를 통한 등록이 정석이지만, DB 직접 등록도 작동함
   - `tenant_llm` 테이블 구조 이해 필요

3. **API 설계**:
   - SDK API endpoints와 UI용 endpoints가 다를 수 있음
   - Retrieval은 Chat API를 통해 사용하도록 설계됨

4. **한국어 처리**:
   - nomic-embed-text가 한국어를 지원함 (multilingual)
   - Chunk 파싱이 성공적으로 완료됨
   - 실제 Q&A 품질은 Phase 5에서 확인 필요
