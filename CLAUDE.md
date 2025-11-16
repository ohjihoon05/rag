# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RAGFlow is an open-source RAG (Retrieval-Augmented Generation) engine based on deep document understanding. It's a full-stack application with:
- Python backend (Flask-based API server + async task executors)
- React/TypeScript frontend (built with UmiJS framework)
- Microservices architecture with Docker deployment
- Multiple data stores (MySQL, Elasticsearch/Infinity, Redis, MinIO)

## Architecture

### Backend (`/api/`)
- **Main Server**: `api/ragflow_server.py` - Flask application entry point that starts the HTTP API server
- **Task Executor**: `rag/svr/task_executor.py` - Async worker processes for document parsing and RAG operations
- **Apps**: Modular Flask blueprints in `api/apps/` registered in `api/apps/__init__.py`:
  - `kb_app.py` - Knowledge base (dataset) management
  - `dialog_app.py` - Chat/conversation handling
  - `document_app.py` - Document processing and parsing
  - `canvas_app.py` - Agent workflow canvas (visual programming)
  - `file_app.py` - File upload/download/management
  - `chunk_app.py` - Document chunk CRUD operations
  - `llm_app.py` - LLM model configuration
  - `user_app.py` / `tenant_app.py` - User and tenant management
- **Services**: Business logic layer in `api/db/services/` (e.g., `knowledgebase_service.py`, `document_service.py`)
- **Models**: Database ORM models in `api/db/db_models.py` using Peewee
- **Launch Script**: `docker/launch_backend_service.sh` starts WS task executors + main server with retry logic

### Core Processing (`/rag/`)
- **Document Processing**: `deepdoc/` - Multi-format parsing (PDF, DOCX, PPT, Excel, images, etc.)
  - `deepdoc/parser/` - Format-specific parsers (pdf_parser.py, docx_parser.py, etc.)
  - `deepdoc/vision/` - OCR, layout recognition, table structure detection
  - Supports multiple parsing methods: DeepDoc (default), MinerU, Docling
- **LLM Integration**: `rag/llm/` - Unified abstractions for 20+ LLM providers
  - `chat_model.py` - Chat/completion interface
  - `embedding_model.py` - Text embedding interface
  - `rerank_model.py` - Reranking interface
- **RAG Pipeline**: `rag/flow/` - Document chunking and processing
  - `parser/` - Text extraction and preprocessing
  - `splitter/` - Chunking strategies
  - `tokenizer/` - Token counting
- **Graph RAG**: `graphrag/` - Knowledge graph construction and querying
  - `general/` - Full GraphRAG implementation (entity extraction, community detection)
  - `light/` - Lightweight GraphRAG variant

### Agent System (`/agent/`)
- **Component Architecture**: Modular workflow components in `agent/component/`
  - `llm.py` - LLM invocation component
  - `begin.py` - Entry point component
  - `retrieval.py` - RAG retrieval component (uses agent/tools/retrieval.py)
  - `categorize.py`, `switch.py` - Conditional routing
  - `iteration.py` - Loop constructs
  - `webhook.py` - HTTP webhook calls
- **Tools**: External API integrations in `agent/tools/`
  - `tavily.py`, `duckduckgo.py`, `google.py` - Web search
  - `wikipedia.py`, `arxiv.py`, `pubmed.py` - Knowledge bases
  - `exesql.py` - SQL execution
  - `code_exec.py` - Python code sandbox execution
  - `retrieval.py` - RAG retrieval tool (used by retrieval component)
- **Canvas**: Visual workflow editor (`agent/canvas.py`) for building agent pipelines

### Frontend (`/web/`)
- **Framework**: UmiJS (React meta-framework) with file-based routing in `src/routes.ts`
- **UI Components**: Ant Design + shadcn/ui (Radix UI primitives)
- **State Management**: Zustand stores in `src/stores/`
- **Styling**: Tailwind CSS with custom configuration
- **Dev Server**: Runs on port 9222 by default, proxies API calls to backend (see `.umirc.ts`)

## Common Development Commands

### Backend Development

#### Setup
```bash
# Install uv package manager
pipx install uv pre-commit

# Clone and install dependencies
git clone https://github.com/infiniflow/ragflow.git
cd ragflow/
uv sync --python 3.10 --all-extras  # Install Python packages
uv run download_deps.py             # Download models and resources
pre-commit install                  # Setup pre-commit hooks
```

#### Start dependent services (required before running backend)
```bash
# Add host entries (Linux/Mac)
sudo sh -c 'echo "127.0.0.1 es01 infinity mysql minio redis sandbox-executor-manager" >> /etc/hosts'

# Start MySQL, Elasticsearch/Infinity, Redis, MinIO
docker compose -f docker/docker-compose-base.yml up -d

# Check services are healthy
docker compose -f docker/docker-compose-base.yml ps
```

#### Run backend locally
```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Set Python path
export PYTHONPATH=$(pwd)  # Linux/Mac
# set PYTHONPATH=%cd%     # Windows CMD

# Optional: Use HuggingFace mirror if needed
export HF_ENDPOINT=https://hf-mirror.com

# Start backend (launches task executors + API server)
bash docker/launch_backend_service.sh

# Alternative: Run API server only (for debugging)
python api/ragflow_server.py

# Alternative: Run single task executor
python rag/svr/task_executor.py 0
```

#### Stop backend
```bash
pkill -f "ragflow_server.py|task_executor.py"
```

#### Testing
```bash
# Run all tests
uv run pytest

# Run specific test markers (p1 = high priority)
uv run pytest -m p1
uv run pytest -m "p1 or p2"

# Run specific test file
uv run pytest test/testcases/test_http_api/test_kb_app/test_create_kb.py

# Run with coverage
uv run pytest --cov=api --cov=rag --cov-report=html
```

#### Code Quality
```bash
# Linting (auto-fix issues)
ruff check --fix

# Format code
ruff format

# Check only (CI mode)
ruff check
ruff format --check

# Pre-commit hooks will run ruff automatically on git commit
```

### Frontend Development

#### Setup and Run
```bash
cd web

# Install dependencies
npm install

# Development server (http://localhost:9222)
npm run dev

# Production build
npm run build

# Preview production build
npm run preview
```

#### Code Quality
```bash
# ESLint (check only)
npm run lint

# Run tests
npm run test

# Run tests with coverage
npm run test -- --coverage

# Format code (Prettier)
npm run prettier:write  # if configured
```

#### Frontend proxies backend API
The dev server (`.umirc.ts`) proxies these paths to the backend:
- `/api` → `http://127.0.0.1:9380` (main API server)
- `/api/v1/admin` → `http://127.0.0.1:9381` (admin API, if running)

### Docker Development

#### Full Stack with Docker
```bash
cd docker

# Start all services (uses docker-compose.yml)
docker compose up -d

# Check logs
docker logs -f ragflow-server  # API server logs
docker compose logs -f         # All service logs

# Restart specific service
docker compose restart ragflow-server

# Stop all services
docker compose down

# Stop and remove volumes (clears all data)
docker compose down -v
```

#### Build Docker Image
```bash
# Build from source
docker build --platform linux/amd64 -f Dockerfile -t infiniflow/ragflow:nightly .

# Build with specific tag
docker build --platform linux/amd64 -f Dockerfile -t ragflow:local .
```

## Key Configuration Files

### Backend Configuration
- **`docker/.env`**: Docker environment variables (ports, passwords, image tags)
- **`docker/service_conf.yaml.template`**: Service configuration template (populated at runtime with env vars)
  - Database connections (MySQL, Elasticsearch/Infinity, Redis)
  - Storage configuration (MinIO, S3, OSS)
  - LLM default settings
- **`pyproject.toml`**: Python dependencies, package metadata, tool configurations (ruff, pytest)
- **`.pre-commit-config.yaml`**: Pre-commit hooks (ruff linting/formatting, yaml/json checks)

### Frontend Configuration
- **`web/package.json`**: NPM dependencies and scripts
- **`web/.umirc.ts`**: UmiJS configuration (routes, proxy, build settings)
- **`web/tailwind.config.js`**: Tailwind CSS configuration
- **`web/tsconfig.json`**: TypeScript compiler options

## Testing Strategy

### Python Tests (`test/`)
- **Markers**: Use pytest markers for priority-based test execution
  - `@pytest.mark.p1` - High priority / critical path tests
  - `@pytest.mark.p2` - Medium priority tests
  - `@pytest.mark.p3` - Low priority / edge case tests
- **Structure**:
  - `test/testcases/test_http_api/` - HTTP API endpoint tests
  - `test/testcases/test_sdk_api/` - Python SDK tests
  - `test/testcases/test_web_api/` - Web interface tests
  - `test/unit_test/` - Unit tests for utilities and helpers
- **Running Tests**: `uv run pytest -m p1` for quick validation

### Frontend Tests (`web/`)
- **Framework**: Jest + React Testing Library
- **Run**: `npm run test` or `npm run test -- --coverage`

## Database Engines

RAGFlow supports two document storage engines:

### Elasticsearch (Default)
- Default configuration in `docker/.env`: `DOC_ENGINE=elasticsearch`
- Stores document chunks and vectors
- Version: 8.11.3 (configurable via `STACK_VERSION`)

### Infinity (Alternative)
- Set `DOC_ENGINE=infinity` in `docker/.env`
- High-performance alternative to Elasticsearch
- **Important**: Switching engines requires data migration
  ```bash
  docker compose -f docker/docker-compose.yml down -v  # Clears data!
  # Edit docker/.env: DOC_ENGINE=infinity
  docker compose -f docker/docker-compose.yml up -d
  ```

## Architecture Patterns

### Task Execution Flow
1. User uploads document via API (`file_app.py`)
2. Document metadata saved to MySQL (`document_service.py`)
3. Task queued in Redis for async processing
4. Task executor picks up task (`task_executor.py`)
5. Document parsed using appropriate parser (`deepdoc/parser/`)
6. Text chunked using selected strategy (`rag/flow/splitter/`)
7. Chunks embedded and stored in Elasticsearch/Infinity
8. Progress updated in MySQL, visible in UI

### Agent Workflow Execution
1. User builds workflow in canvas UI (`canvas_app.py`)
2. Workflow saved as JSON (nodes + edges)
3. Execution starts from "begin" component (`agent/component/begin.py`)
4. Components execute in topological order based on edges
5. Each component processes inputs, calls tools if needed
6. Output passed to next component via edges
7. Results streamed back to UI via Server-Sent Events (SSE)

### LLM Provider Abstraction
- All LLM providers implement common interfaces in `rag/llm/`
- Factory pattern in `chat_model.py`, `embedding_model.py`, `rerank_model.py`
- Add new provider: Create class in respective module, register in factory
- Configuration in `service_conf.yaml` under `user_default_llm`

## Development Environment Requirements

- **Python**: 3.10, 3.11, or 3.12 (3.13 not supported yet)
- **Node.js**: >=18.20.4
- **Docker**: >=24.0.0
- **Docker Compose**: >=v2.26.1
- **uv**: Latest version (Python package manager)
- **System**: 16GB+ RAM, 50GB+ disk space
- **Optional**: jemalloc (for memory optimization)

## Default Credentials

When running with Docker defaults:
- **MinIO**: Username `rag_flow` / Password from `docker/.env` (MINIO_PASSWORD)
- **MySQL**: Username `rag_flow` / Password from `docker/.env` (MYSQL_PASSWORD)
- **Elasticsearch**: Username `elastic` / Password from `docker/.env` (ELASTIC_PASSWORD)
- **RAGFlow Admin**: Create account on first login at `http://localhost/` (or configured SVR_HTTP_PORT)
