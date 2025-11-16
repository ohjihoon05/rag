# Implementation Plan: RAGFlow 온프레미스 한국어 최적화 배포

**Branch**: `001-ragflow-korean-optimization` | **Date**: 2025-11-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-ragflow-korean-optimization/spec.md`

## Summary

RAGFlow 온프레미스 배포를 Ollama 기반 로컬 LLM과 한국어 최적화 모델(bge-m3 임베딩, bge-reranker-v2-m3 리랭킹, qwen2.5:7b LLM)로 구성하여 CS 팀의 데일리 리포트 문서 검색 및 질의응답 시스템을 구축합니다. Docker Compose 기반 전체 스택(RAGFlow, MySQL, Infinity, Redis, MinIO)을 배포하며, 메모리 제약(15.54GB RAM) 환경에서 최적화된 설정을 적용합니다.

## Technical Context

**Language/Version**: Python 3.11 (RAGFlow backend), Node.js 18.20.4 (RAGFlow frontend), Bash (Docker entrypoint scripts)
**Primary Dependencies**:
- Backend: Flask, Peewee ORM, RAGFlow v0.22.0, transformers, FlagEmbedding
- Frontend: React, UmiJS, Ant Design, Tailwind CSS
- Infrastructure: Docker Compose v2.36.2, Ollama (host), MySQL 8.0, Redis 7.0, MinIO
**Storage**:
- MySQL 8.0 (메타데이터: 사용자, Knowledge Base, 문서, 청크 정보)
- Infinity (벡터 데이터베이스: 문서 임베딩 및 검색)
- MinIO (객체 저장: 업로드된 문서 파일)
- Redis 7.0 (태스크 큐: 비동기 문서 파싱 작업)
**Testing**: pytest (Python backend unit/integration tests), Jest (React frontend tests)
**Target Platform**:
- Development: Windows 10/11 + WSL2 + Docker Desktop
- Runtime: Docker containers (Linux-based) communicating via internal network
- Ollama: Windows host (localhost:11434), accessed from containers via host.docker.internal
**Project Type**: Web application (Python Flask backend + React frontend)
**Performance Goals**:
- 질의 응답 < 5초 (Top K=3 검색 기준)
- 문서 파싱 속도 > 10페이지/분
- 동시 사용자 5-10명 지원
**Constraints**:
- 메모리 제약: 총 RAM 15.54GB (Docker 서비스 + Ollama + OS 포함)
- 메모리 할당 전략: Infinity 6GB, MySQL 2GB, Redis 1GB, RAGFlow 3GB, 여유 3-4GB
- 네트워크: Docker → Ollama 연결 필수 (host.docker.internal:11434)
- 문서 형식: PDF, DOCX, TXT, Excel, PPT 지원 (DeepDoc 파서)
**Scale/Scope**:
- 문서 수: 1,000+ 문서 (지속적 증가)
- Knowledge Base: 5-10개 (팀별, 주제별)
- 벡터 데이터: 50GB까지 확장 가능
- 사용자: 5-10명 동시 사용

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Status**: ✅ PASS (Constitution template not customized, using default gates)

Since the project constitution is still using the template format and not yet customized for this specific project, we proceed with standard best practices gates:

### Standard Gates Applied

1. **Deployment Simplicity**: ✅ PASS
   - Single command deployment: `docker compose up -d`
   - All services containerized with Docker Compose
   - Configuration via `.env` and `service_conf.yaml`

2. **Documentation**: ✅ PASS
   - Comprehensive installation guide created: `RAGFlow_온프레미스_설치_가이드.md`
   - Troubleshooting section included
   - Use case scenarios documented

3. **Testing Strategy**: ⚠️ ADVISORY
   - Manual testing planned for Phase 4
   - Automated tests not in scope for initial deployment
   - Future recommendation: Add integration tests for Ollama connectivity

4. **Security & Privacy**: ✅ PASS
   - On-premise deployment ensures data privacy
   - No external API calls (except optional HuggingFace model downloads)
   - Docker internal network isolation

5. **Resource Optimization**: ✅ PASS
   - Infinity chosen over Elasticsearch (30-40% less memory)
   - Memory limits configured in Docker Compose
   - CPU-only mode (no GPU requirement)

**Post-Design Re-check**: Will verify after Phase 1 completion

## Project Structure

### Documentation (this feature)

```text
specs/001-ragflow-korean-optimization/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── ollama-api.yaml      # Ollama API contract (external)
│   ├── ragflow-kb-api.yaml  # RAGFlow Knowledge Base API
│   └── ragflow-chat-api.yaml # RAGFlow Chat API
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Existing RAGFlow project structure (not modified)
ragflow/
├── api/                     # Flask backend
│   ├── apps/                # API blueprints (kb_app, dialog_app, document_app, etc.)
│   ├── db/                  # Database models and services
│   └── ragflow_server.py    # Main Flask application
│
├── rag/                     # Core RAG pipeline
│   ├── llm/                 # LLM provider abstractions (chat_model, embedding_model, rerank_model)
│   ├── flow/                # Document processing (parser, splitter, tokenizer)
│   ├── svr/                 # Task executor (async workers)
│   └── deepdoc/             # Document parsers (PDF, DOCX, Excel, etc.)
│
├── web/                     # React frontend (UmiJS framework)
│   ├── src/
│   │   ├── components/      # UI components
│   │   ├── pages/           # Page components (file-based routing)
│   │   └── stores/          # Zustand state management
│   ├── .umirc.ts            # UmiJS configuration
│   └── package.json         # Frontend dependencies
│
├── docker/                  # Docker deployment files
│   ├── docker-compose.yml           # Main compose file
│   ├── docker-compose-base.yml      # Base services (MySQL, Redis, etc.)
│   ├── .env                         # Environment variables (CUSTOMIZED)
│   ├── service_conf.yaml.template   # Service config template
│   └── launch_backend_service.sh    # Backend entrypoint script
│
├── conf/                    # Runtime configuration
│   └── service_conf.yaml    # Service config (CREATED from template)
│
├── specs/                   # SpecKit documentation (THIS FEATURE)
│   └── 001-ragflow-korean-optimization/
│       ├── plan.md
│       ├── spec.md
│       ├── research.md      # To be created
│       ├── data-model.md    # To be created
│       ├── quickstart.md    # To be created
│       └── contracts/       # To be created
│
├── test/                    # Existing test suite (not modified)
│   ├── testcases/
│   └── unit_test/
│
├── pyproject.toml           # Python dependencies (uv)
└── RAGFlow_온프레미스_설치_가이드.md  # Installation guide (CREATED)
```

**Structure Decision**:
This is an existing web application project with established backend (Python/Flask) and frontend (React/UmiJS) structure. Our implementation focuses on **configuration and deployment** rather than code changes. We customize Docker environment files (`.env`, `service_conf.yaml`) and create comprehensive documentation in the `specs/main/` directory. No modifications to existing source code are planned.

## Complexity Tracking

> **No violations detected** - all Constitution Check gates passed or are advisory only.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | N/A |

---

## Phase 0: Research & Technology Validation

**Objective**: Resolve all NEEDS CLARIFICATION items from Technical Context and validate technology choices.

### Research Tasks

1. **Ollama API Integration Patterns**
   - Research: How to connect Docker containers to host-based Ollama service
   - Question: `host.docker.internal` vs direct IP addressing on Windows WSL2
   - Deliverable: Best practices for Docker → Host Ollama communication

2. **Korean Language Model Performance**
   - Research: bge-m3 vs alternatives for Korean text embedding
   - Benchmark: Korean Embedding Benchmark scores, MTEB multilingual leaderboard
   - Deliverable: Validation of bge-m3 as optimal choice

3. **Infinity vs Elasticsearch for Korean Text**
   - Research: Infinity vector database performance with multilingual embeddings
   - Comparison: Memory usage, query speed, Korean language support
   - Deliverable: Confirmation of Infinity as memory-efficient choice

4. **Memory Optimization Strategies**
   - Research: Docker memory limits and allocation strategies for 15.54GB total RAM
   - Question: Optimal memory allocation per service (Infinity, MySQL, Redis, RAGFlow)
   - Deliverable: Memory allocation plan

5. **Reranking Model Integration**
   - Research: bge-reranker-v2-m3 integration methods in RAGFlow
   - Question: HuggingFace TEI vs direct model loading
   - Deliverable: Reranker setup instructions

**Output**: `research.md` with all findings and decisions documented

---

## Phase 1: Design & Contracts

**Prerequisites**: `research.md` complete

### Design Tasks

1. **Data Model Design**
   - Extract entities: Knowledge Base, Document, Chunk, Chat, User
   - Define relationships: KB → Documents → Chunks, Chat → KB
   - Document storage strategy: MySQL (metadata), Infinity (vectors), MinIO (files)
   - **Output**: `data-model.md`

2. **API Contracts**
   - Ollama API contract: `/v1/chat/completions`, `/v1/embeddings` endpoints
   - RAGFlow Knowledge Base API: Create KB, Upload Document, List Documents
   - RAGFlow Chat API: Create Chat, Send Message, Get Response
   - **Output**: `contracts/ollama-api.yaml`, `contracts/ragflow-kb-api.yaml`, `contracts/ragflow-chat-api.yaml`

3. **Quickstart Guide**
   - Step-by-step deployment instructions
   - Configuration examples
   - First document upload walkthrough
   - **Output**: `quickstart.md`

4. **Agent Context Update**
   - Run: `.specify/scripts/powershell/update-agent-context.ps1 -AgentType claude`
   - Add technologies: Ollama, bge-m3, Infinity, RAGFlow
   - Preserve existing manual additions

**Outputs**: data-model.md, contracts/*, quickstart.md, updated agent context

---

## Phase 2: Task Breakdown

**Note**: This phase is executed by `/speckit.tasks` command, NOT by `/speckit.plan`.

Tasks will be generated based on the design artifacts from Phase 1 and will include:
- Docker environment configuration
- Ollama model download and setup
- RAGFlow service deployment
- Model integration and testing
- Documentation and user training

**Command to execute**: `/speckit.tasks`

---

## Next Steps

1. ✅ **Complete**: Feature specification created (`spec.md`)
2. ✅ **Complete**: Implementation plan initialized (this file)
3. **TODO**: Execute Phase 0 research tasks → generate `research.md`
4. **TODO**: Execute Phase 1 design tasks → generate `data-model.md`, `contracts/`, `quickstart.md`
5. **TODO**: Update agent context with new technologies
6. **TODO**: Re-evaluate Constitution Check after design
7. **TODO**: Run `/speckit.tasks` to generate task breakdown

---

**Execution Status**: Phase 0 (Research) - Ready to Begin
**Blockers**: None
**Dependencies**: Ollama must remain running on host (localhost:11434)
