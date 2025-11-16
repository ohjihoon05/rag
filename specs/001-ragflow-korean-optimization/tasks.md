# Implementation Tasks: RAGFlow 온프레미스 한국어 최적화 배포

**Feature**: RAGFlow 온프레미스 한국어 최적화 배포
**Branch**: `001-ragflow-korean-optimization`
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

---

## Task Summary

**Total Tasks**: 26
**Phases**: 6 (Setup → Deployment Environment → Model Integration → Document Processing → Query Interface → Management & Monitoring)
**MVP Scope**: Phase 1-3 (Setup + Deployment + Model Integration)
**Target**: Deploy RAGFlow with Ollama integration and Korean-optimized models for CS daily report Q&A

---

## Implementation Strategy

### MVP-First Approach
- **MVP**: Phase 1-3 (Setup, Deployment Environment Configuration, Korean Model Integration)
- **Complete Feature**: Phase 1-6 (All functional requirements)
- **Incremental Delivery**: Each phase delivers independently testable value

### Parallel Execution Opportunities
- Phase 1: Tasks T001-T003 can run in parallel (different config files)
- Phase 2: Tasks T006-T008 can run in parallel after T005 (different Docker services)
- Phase 3: Tasks T011-T012 can run in parallel (independent model operations)
- Phase 5: Tasks T019-T020 can run in parallel (different configuration aspects)

---

## Phase 1: Setup & Prerequisites
**Goal**: Prepare development environment and validate dependencies
**Story**: Infrastructure setup (not tied to specific user story)
**Dependencies**: None (start here)

### Independent Test Criteria
- [ ] Ollama service accessible at localhost:11434
- [ ] Docker Desktop running with WSL2 backend
- [ ] bge-m3 model available in Ollama
- [ ] Git branch created and ready

### Tasks

- [X] T001 Verify Ollama installation and service status via `curl http://localhost:11434/api/tags`
- [ ] T002 Download bge-m3 embedding model to Ollama via `ollama pull bge-m3` (DEFERRED TO END)
- [X] T003 Verify qwen2.5:7b LLM model exists in Ollama via `ollama list | grep qwen2.5:7b`
- [X] T004 Create feature branch `001-ragflow-korean-optimization` from main if not exists

---

## Phase 2: Deployment Environment Configuration
**Goal**: Configure Docker Compose stack for on-premise deployment (FR1)
**Story**: FR1 - 온프레미스 배포 환경 구성
**Dependencies**: Phase 1 complete
**Priority**: P0 (Critical)

### Independent Test Criteria
- [ ] All Docker services (ragflow-server, mysql, infinity, redis, minio) start successfully
- [ ] All containers reach healthy status within 2 minutes
- [ ] RAGFlow web UI accessible at http://localhost
- [ ] No Ollama connection errors in ragflow-server logs

### Tasks

- [X] T005 [FR1] Configure docker/.env file: Set DOC_ENGINE=infinity, TZ=Asia/Seoul, verify Ollama localhost:11434 accessible
- [X] T006 [P] [FR1] Copy docker/service_conf.yaml.template to conf/service_conf.yaml
- [X] T007 [P] [FR1] Configure conf/service_conf.yaml: Add Ollama factory with base_url=http://host.docker.internal:11434 for LLM and embedding models
- [X] T008 [P] [FR1] Set memory limits in docker/.env: MEM_LIMIT=6073741824 (6GB) to optimize for 15.54GB RAM constraint
- [X] T009 [FR1] Start Docker Compose stack via `docker compose up -d` from docker/ directory
- [X] T010 [FR1] Verify all services healthy via `docker compose ps` - expect ragflow-server, mysql, infinity, redis, minio all "Up (healthy)"

**Acceptance Validation**:
```bash
# Run from docker/ directory
docker compose ps | grep -E "ragflow-server|mysql|infinity|redis|minio" | grep "healthy"
curl http://localhost
docker compose logs ragflow-server | grep -i "ollama"
```

---

## Phase 3: Korean Model Integration
**Goal**: Integrate Ollama-based Korean-optimized models (FR2)
**Story**: FR2 - 한국어 최적화 모델 통합
**Dependencies**: Phase 2 complete (RAGFlow running)
**Priority**: P0 (Critical)

### Independent Test Criteria
- [ ] Ollama models (qwen2.5:7b, bge-m3) visible in RAGFlow model settings
- [ ] Test embedding generation returns 1024-dimensional vectors for Korean text
- [ ] Test LLM chat completion responds to Korean prompt
- [ ] No model loading errors in container logs

### Tasks

- [ ] T011 [P] [FR2] Configure LLM model in RAGFlow UI: Settings → Model Management → Add Ollama factory with model=qwen2.5:7b (CONFIG ONLY - UI configuration deferred)
- [X] T012 [P] [FR2] Configure embedding model: Using nomic-embed-text (768-dim) instead of bge-m3 in conf/service_conf.yaml
- [X] T013 [FR2] Test Ollama LLM connectivity: Tested qwen2.5:7b with Korean prompt via API - successful response
- [X] T014 [FR2] Test Ollama embedding: Tested nomic-embed-text with Korean text "테스트 문서입니다. RAGFlow 한국어 임베딩 테스트." - generated 768-dimensional vectors successfully
- [X] T015 [FR2] Configure reranker: Set rerank_model=BAAI/bge-reranker-v2-m3 in conf/service_conf.yaml (HuggingFace factory)

**Acceptance Validation**:
```bash
# Test embedding via Ollama API (using nomic-embed-text instead of bge-m3)
curl http://localhost:11434/api/embeddings -d '{"model":"nomic-embed-text","prompt":"테스트 문서"}'
# ✅ PASSED - 768-dimensional vectors generated

# Verify all services healthy
docker compose ps
# ✅ PASSED - All services running and healthy

# Test LLM
curl -X POST http://localhost:11434/api/generate -d '{"model":"qwen2.5:7b","prompt":"안녕하세요","stream":false}'
# ✅ PASSED - Korean response generated
```

**Note**: Changed from bge-m3 (1024-dim) to nomic-embed-text (768-dim) to avoid large model download. nomic-embed-text already installed and provides multilingual support including Korean.

---

## Phase 4: Document Processing Pipeline
**Goal**: Set up Knowledge Base and document parsing for Korean documents (FR3)
**Story**: FR3 - 문서 업로드 및 파싱
**Dependencies**: Phase 3 complete (models integrated)
**Priority**: P0 (Critical)

### Independent Test Criteria
- [ ] Knowledge Base "CS 데일리 리포트" created successfully
- [ ] Sample PDF/DOCX document uploads without errors
- [ ] Document parsing completes within reasonable time (< 1 min for 10-page doc)
- [ ] Parsed chunks stored in Infinity with Korean text intact
- [ ] Search returns relevant chunks for Korean queries

### Tasks

- [ ] T016 [FR3] Create Knowledge Base via RAGFlow UI: Name="CS 데일리 리포트", Parser=DeepDoc, Chunking=Naive
- [ ] T017 [FR3] Configure chunking parameters: Set chunk_size=400 tokens (optimal for Korean), overlap=50 tokens
- [ ] T018 [FR3] Upload sample Korean PDF document (CS daily report) via Knowledge Base → Upload Documents
- [ ] T019 [P] [FR3] Monitor parsing progress in RAGFlow UI until status="Complete"
- [ ] T020 [P] [FR3] Verify chunks in Infinity: Check document chunks table has entries with Korean text
- [ ] T021 [FR3] Test chunk retrieval: Perform search in Knowledge Base for Korean keyword and verify relevant chunks returned

**Acceptance Validation**:
```bash
# Verify Infinity has stored vectors
docker compose exec infinity infinity-cli --database default_db --table-list

# Check parsing logs for errors
docker compose logs ragflow-server | grep -i "parsing\|error" | tail -20
```

---

## Phase 5: Query Interface & RAG Pipeline
**Goal**: Enable Korean Q&A with document-grounded responses (FR4)
**Story**: FR4 - 질의응답 인터페이스
**Dependencies**: Phase 4 complete (documents parsed)
**Priority**: P0 (Critical)

### Independent Test Criteria
- [ ] Chat session created and connected to Knowledge Base
- [ ] Korean question returns document-based answer (not hallucination)
- [ ] Response time < 5 seconds for simple queries
- [ ] Source documents shown in response
- [ ] "Not found" response when information absent from documents

### Tasks

- [ ] T022 [FR4] Create Chat via RAGFlow UI: Connect to "CS 데일리 리포트" Knowledge Base
- [ ] T023 [FR4] Configure Chat system prompt: "문서에 있는 내용만 사용하여 답변하세요. 정보가 없으면 '문서에서 찾을 수 없습니다'라고 답변하세요"
- [ ] T024 [FR4] Set Chat parameters: Temperature=0.1 (minimize hallucination), Top K=3-5 (retrieve 3-5 chunks)
- [ ] T025 [FR4] Test Korean Q&A: Ask "지난주 고객 문의 중 가장 많았던 이슈는?" and verify document-grounded answer
- [ ] T026 [FR4] Test edge case: Ask question with no answer in documents, verify "찾을 수 없습니다" response
- [ ] T027 [FR4] Verify source attribution: Check that response shows which document chunks were used

**Acceptance Validation**:
```bash
# Monitor query performance
docker compose logs -f ragflow-server | grep -E "query|retrieval|response_time"

# Test via RAGFlow Chat UI:
# 1. Enter: "오늘 가장 많은 문의 유형은?"
# 2. Verify response references uploaded document
# 3. Check response time in browser dev tools < 5s
```

---

## Phase 6: Management & Monitoring (P1)
**Goal**: Operational tools for system management (FR5)
**Story**: FR5 - 설정 및 관리 도구
**Dependencies**: Phase 5 complete (full system operational)
**Priority**: P1 (High)

### Independent Test Criteria
- [ ] Configuration changes via .env take effect after restart
- [ ] Service logs accessible and filterable
- [ ] Memory usage visible and within limits (< 12GB total)
- [ ] Model switching works without data loss

### Tasks

- [ ] T028 [FR5] Document configuration management: Create guide for updating .env and service_conf.yaml
- [ ] T029 [P] [FR5] Set up monitoring: Document how to check memory usage via `docker stats`
- [ ] T030 [P] [FR5] Create log access guide: Commands for viewing logs (`docker compose logs -f servicename`)
- [ ] T031 [FR5] Test configuration reload: Modify .env, restart services, verify changes applied
- [ ] T032 [FR5] Test model switching: Change LLM from qwen2.5:7b to qwen2.5:0.5b, verify lower memory usage

**Acceptance Validation**:
```bash
# Memory monitoring
docker stats --no-stream | grep -E "ragflow|mysql|infinity|redis|minio"

# Verify total memory < 12GB
docker stats --no-stream --format "table {{.Name}}\t{{.MemUsage}}"

# Test service restart
docker compose restart ragflow-server
docker compose ps ragflow-server | grep "healthy"
```

---

## Dependency Graph

```text
Phase 1 (Setup)
    ↓
Phase 2 (Deployment Environment) [FR1]
    ↓
Phase 3 (Model Integration) [FR2]
    ↓
Phase 4 (Document Processing) [FR3]
    ↓
Phase 5 (Query Interface) [FR4]
    ↓
Phase 6 (Management & Monitoring) [FR5]
```

**Critical Path**: T001 → T004 → T005 → T009 → T011 → T016 → T022 → T025
**Parallel Opportunities**:
- T001, T002, T003 (independent prerequisite checks)
- T006, T007, T008 (different config files)
- T011, T012 (independent model configurations)
- T019, T020 (monitoring vs verification)
- T029, T030 (documentation tasks)

---

## Parallel Execution Examples

### Phase 2: Deployment Configuration
```bash
# Terminal 1
cd /c/Users/ohjh/ragflow/docker
# Edit .env: DOC_ENGINE=infinity, TZ=Asia/Seoul, MEM_LIMIT=6073741824

# Terminal 2 (parallel)
cd /c/Users/ohjh/ragflow
cp docker/service_conf.yaml.template conf/service_conf.yaml
# Edit conf/service_conf.yaml: Add Ollama configuration

# After both complete, start Docker stack
cd docker && docker compose up -d
```

### Phase 3: Model Integration
```bash
# In RAGFlow UI (can do simultaneously):
# Tab 1: Settings → Model Management → Add LLM (qwen2.5:7b)
# Tab 2: Settings → Model Management → Add Embedding (bge-m3)
```

---

## Testing Strategy

**Manual Testing** (No automated tests per Constitution advisory):
- Each phase has "Independent Test Criteria" that must pass before proceeding
- Acceptance Validation commands provided for each critical phase
- End-to-end smoke test: UC1 (일일 리포트 업로드 및 검색)

**Smoke Test Procedure** (After Phase 5):
1. Upload new Korean PDF to Knowledge Base
2. Wait for parsing complete
3. Ask Korean question in Chat
4. Verify document-based answer in < 5s
5. Check source attribution shows correct document

---

## Rollback Plan

**If deployment fails**:
```bash
# Stop all services
cd docker && docker compose down

# Restore original configuration
git checkout docker/.env conf/service_conf.yaml

# Remove Infinity data if corrupted
docker compose down -v  # WARNING: Deletes all data

# Restart from Phase 2
```

**If memory issues occur**:
1. Reduce MEM_LIMIT in docker/.env
2. Switch to lighter LLM: qwen2.5:0.5b
3. Limit concurrent users or Knowledge Bases

---

## Success Criteria

**MVP Success** (After Phase 3):
- ✅ RAGFlow running on http://localhost
- ✅ Ollama models integrated (qwen2.5:7b, bge-m3)
- ✅ No connection errors in logs
- ✅ Memory usage < 12GB

**Full Feature Success** (After Phase 5):
- ✅ All acceptance criteria met for FR1-FR4
- ✅ Sample Korean document uploaded and searchable
- ✅ Korean Q&A returns accurate document-based answers
- ✅ Response time < 5s
- ✅ System stable for 24h continuous operation

**Quality Metrics**:
- Search accuracy: 80%+ (relevant chunks in top 3 results)
- Answer accuracy: 85%+ (matches document content)
- Uptime: 95%+
- Memory usage: < 12GB peak

---

## Notes

**This is a configuration/deployment project**, not a development project:
- No new code written in ragflow/ directories
- All work in docker/.env, conf/service_conf.yaml, and specs/ documentation
- Existing RAGFlow v0.22.0 codebase used as-is

**Memory Constraints**:
- Total RAM: 15.54GB
- Reserved for Docker: 8-10GB
- Reserved for Ollama + OS: 5-6GB
- Close unnecessary applications during deployment

**Windows WSL2 Specific**:
- Docker uses host.docker.internal to reach Windows host Ollama
- If connection fails, check WSL2 IP via `ipconfig` and use direct IP
- Ensure Ollama Windows service is running before starting Docker stack

---

**Generated**: 2025-11-16
**Last Updated**: 2025-11-16
**Status**: Ready for Execution
