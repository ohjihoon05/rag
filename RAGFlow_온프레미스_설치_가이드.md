# RAGFlow 온프레미스 설치 가이드 (Ollama + 한국어 최적화)

## 📋 목차
1. [환경 분석 결과](#환경-분석-결과)
2. [선택된 구성 요소](#선택된-구성-요소)
3. [설치 전 준비사항](#설치-전-준비사항)
4. [설치 및 설정 단계](#설치-및-설정-단계)
5. [RAGFlow 실행](#ragflow-실행)
6. [Ollama 및 한국어 모델 통합](#ollama-및-한국어-모델-통합)
7. [문서 업로드 및 RAG 사용](#문서-업로드-및-rag-사용)
8. [트러블슈팅](#트러블슈팅)

---

## 환경 분석 결과

### ✅ 현재 PC 환경
- **OS**: Windows (WSL2 with Docker Desktop)
- **CPU**: 8 cores
- **RAM**: 15.54GB
- **Docker**: v28.2.2
- **Docker Compose**: v2.36.2
- **Ollama**: 실행 중 (localhost:11434)

### 설치된 Ollama 모델
- `qwen2.5:7b` - 한국어 LLM (이미 설치됨)
- `qwen2.5:0.5b` - 경량 LLM
- `nomic-embed-text:latest` - 영어 임베딩 모델
- `tifa-*` - 한국어 fine-tuned 모델 시리즈

**판정**: RAGFlow 온프레미스 실행 가능 ✅

---

## 선택된 구성 요소

### 1️⃣ 문서 저장 엔진: **Infinity** 🚀

#### 선택 이유:
- ✅ **메모리 효율**: Elasticsearch보다 30-40% 적은 메모리 사용
- ✅ **고성능**: 더 빠른 벡터 검색 속도
- ✅ **무료**: 완전 오픈소스
- ✅ **RAGFlow 최적화**: 공식 지원, 기본 Docker 설정 포함

### 2️⃣ Embedding 모델: **bge-m3**

#### 특징:
- 🌏 **다국어 지원**: 100개 이상 언어 (한국어 포함)
- 📄 **긴 문서 처리**: 최대 8192 토큰
- 🔝 **성능**: MTEB 리더보드 상위권
- 🦙 **Ollama 호환**: 직접 사용 가능
- 💪 **RAG 최적화**: 검색, 분류, 클러스터링 다목적 지원

**Ollama 설치 명령어**:
```bash
ollama pull bge-m3
```

### 3️⃣ Reranking 모델: **bge-reranker-v2-m3**

#### 특징:
- 🎯 **정확도 향상**: RAG 검색 품질 개선
- 🇰🇷 **한국어 최적화**: 18개 언어 지원 (한국어 포함)
- 🔬 **Cross-Encoder**: 더 정확한 문서 순위 결정
- 📊 **성능**: 한국어 Embedding Benchmark F1 score 0.7456

**모델 경로**:
- 기본: `BAAI/bge-reranker-v2-m3`
- 한국어 특화: `dragonkue/bge-reranker-v2-m3-ko`

### 4️⃣ LLM 모델: **qwen2.5:7b**

- ✅ **이미 설치됨**
- 한국어 성능 우수
- 회사 문서 질의응답에 적합

---

## 설치 전 준비사항

### 1. Ollama에 bge-m3 임베딩 모델 설치

```bash
ollama pull bge-m3
```

설치 확인:
```bash
ollama list
```

### 2. 환경 설정 파일 수정

#### `docker/.env` 파일 수정

현재 위치로 이동:
```bash
cd C:\Users\ohjh\ragflow
```

`.env` 파일에서 다음 항목 변경:

```bash
# 문서 저장 엔진을 Infinity로 변경
DOC_ENGINE=infinity

# 타임존 설정 (한국)
TZ=Asia/Seoul

# HuggingFace 미러 (선택사항, 다운로드 속도 개선)
HF_ENDPOINT=https://hf-mirror.com
```

---

## 설치 및 설정 단계

### Step 1: RAGFlow 클론 및 초기 설정

프로젝트는 이미 `C:\Users\ohjh\ragflow`에 있으므로 이 단계는 생략합니다.

### Step 2: `docker/.env` 파일 수정

```bash
cd docker
```

`.env` 파일 편집:
```bash
# 문서 저장 엔진
DOC_ENGINE=infinity

# 타임존
TZ=Asia/Seoul
```

### Step 3: `service_conf.yaml` 설정 준비

`docker/service_conf.yaml.template` 파일을 복사하여 `conf/service_conf.yaml` 생성:

```bash
# Windows PowerShell 또는 Git Bash에서
cp docker/service_conf.yaml.template conf/service_conf.yaml
```

`conf/service_conf.yaml` 파일에 다음 내용 추가/수정:

```yaml
user_default_llm:
  factory: 'Ollama'
  base_url: 'http://host.docker.internal:11434'  # Docker에서 호스트 Ollama 접근
  default_models:
    chat_model:
      name: 'qwen2.5:7b'
      factory: 'Ollama'
      base_url: 'http://host.docker.internal:11434'
    embedding_model:
      name: 'bge-m3'
      factory: 'Ollama'
      base_url: 'http://host.docker.internal:11434'
    rerank_model:
      name: 'bge-reranker-v2-m3'
      factory: 'HuggingFace'  # HuggingFace TEI 또는 로컬 서비스
```

**중요**: Docker 컨테이너에서 Windows 호스트의 Ollama에 접근하려면 `host.docker.internal`을 사용합니다.

---

## RAGFlow 실행

### 방법 1: Docker Compose로 전체 스택 실행 (권장)

```bash
cd docker
docker compose up -d
```

서비스 상태 확인:
```bash
docker compose ps
```

로그 확인:
```bash
docker compose logs -f ragflow-server
```

### 방법 2: 기본 서비스만 실행 후 백엔드 로컬 개발

먼저 의존 서비스 실행:
```bash
cd docker
docker compose -f docker-compose-base.yml up -d
```

그 다음 로컬에서 백엔드 실행 (개발/디버깅 시):
```bash
cd ..
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

export PYTHONPATH=$(pwd)
bash docker/launch_backend_service.sh
```

---

## Ollama 및 한국어 모델 통합

### 1. Ollama 연결 확인

RAGFlow가 실행되면 웹 브라우저에서 접속:
```
http://localhost
```

초기 계정 생성 후 로그인합니다.

### 2. LLM 모델 설정

1. **설정(Settings)** → **모델 관리(Model Management)** 메뉴로 이동
2. **LLM 모델 추가**:
   - Factory: `Ollama`
   - Base URL: `http://host.docker.internal:11434/v1` (Docker) 또는 `http://localhost:11434/v1` (로컬)
   - Model Name: `qwen2.5:7b`

### 3. Embedding 모델 설정

1. **Embedding 모델 추가**:
   - Factory: `Ollama`
   - Base URL: `http://host.docker.internal:11434/v1`
   - Model Name: `bge-m3`
   - Dimensions: `1024` (bge-m3 기본값)

### 4. Reranking 모델 설정 (선택사항)

Reranker는 별도 HuggingFace TEI 서비스를 사용하거나, RAGFlow가 자동으로 로드합니다.

별도 설정이 필요하면:
```yaml
# conf/service_conf.yaml
user_default_llm:
  default_models:
    rerank_model:
      name: 'BAAI/bge-reranker-v2-m3'
      factory: 'HuggingFace'
```

---

## 문서 업로드 및 RAG 사용

### 1. 지식베이스(Knowledge Base) 생성

1. RAGFlow 대시보드에서 **Knowledge Base** → **Create**
2. 이름 입력 (예: "회사 데일리 리포트")
3. **Parsing Method**: `DeepDoc` 또는 `General` (문서 종류에 따라)
4. **Chunking Method**: `Naive` (기본) 또는 `QA` (Q&A 형식에 적합)

### 2. 문서 업로드

1. 생성한 지식베이스 선택 → **Upload Documents**
2. CS 팀의 데일리 리포트 파일 드래그 앤 드롭 (PDF, DOCX, TXT 등)
3. 파싱 시작 - 진행 상황은 문서 목록에서 확인

### 3. 대화(Chat) 생성

1. **Chat** 메뉴 → **Create**
2. 연결할 지식베이스 선택
3. 프롬프트 설정:
   ```
   당신은 회사 문서를 기반으로 정확하게 답변하는 AI 어시스턴트입니다.
   문서에 있는 내용만 사용하여 질문에 답변하세요.
   정보가 문서에 없으면 "해당 내용은 문서에서 찾을 수 없습니다"라고 답변하세요.
   ```
4. **Temperature**: `0.1` (더 정확하고 일관된 답변)
5. **Top K**: `3-5` (검색할 문서 청크 수)

### 4. 질의응답 테스트

예시 질문:
- "지난주 고객 문의 중 가장 많았던 이슈는 무엇인가요?"
- "2025년 1월 15일 리포트 내용을 요약해주세요"
- "제품 A에 대한 불만 사항을 모두 찾아주세요"

---

## 트러블슈팅

### 1. Docker 컨테이너가 Ollama에 연결되지 않는 경우

**문제**: `connection refused` 에러

**해결방법**:
- `host.docker.internal` 대신 호스트 IP 직접 사용
- Windows에서 WSL2 IP 확인:
  ```bash
  ipconfig
  # "Ethernet adapter vEthernet (WSL)" 섹션의 IP 사용
  ```
- `service_conf.yaml`의 `base_url`을 `http://<WSL_IP>:11434`로 변경

### 2. Ollama 모델이 목록에 나타나지 않는 경우

**확인사항**:
```bash
# Ollama 실행 확인
curl http://localhost:11434/api/tags

# bge-m3 설치 확인
ollama list | grep bge-m3
```

### 3. 문서 파싱이 실패하는 경우

**가능한 원인**:
- 메모리 부족: Docker Desktop 메모리 할당 증가 (Settings → Resources → Memory: 8GB 이상)
- 파일 형식 문제: PDF 암호화 해제 또는 다른 형식으로 변환

### 4. 한국어 검색 결과가 부정확한 경우

**개선 방법**:
1. **Chunking 크기 조정**:
   - 한국어 문서는 `chunk_size: 300-500` 토큰이 적합
   - Knowledge Base 설정에서 조정
2. **Reranker 활성화**:
   - 검색 정확도를 크게 향상시킴
3. **Embedding 모델 변경**:
   - 한국어 특화 모델 테스트: `dragonkue/bge-m3-ko`

### 5. Infinity 서비스가 시작되지 않는 경우

**확인**:
```bash
docker compose logs infinity

# 재시작
docker compose restart infinity
```

### 6. 메모리 부족 문제

현재 RAM이 15.54GB이므로 여유 메모리가 제한적입니다.

**최적화 방법**:
1. **Docker 메모리 제한**:
   - `docker/.env`에서 `MEM_LIMIT=6073741824` (6GB)로 조정
2. **불필요한 서비스 중지**:
   - 개발 중이 아니라면 frontend는 빌드된 정적 파일 사용
3. **경량 LLM 사용**:
   - 필요시 `qwen2.5:0.5b` 같은 경량 모델 사용

---

## 추가 리소스

### 공식 문서
- RAGFlow: https://ragflow.io/docs/
- Ollama: https://ollama.com/
- BGE Models: https://github.com/FlagOpen/FlagEmbedding

### 유용한 명령어

```bash
# 모든 서비스 중지
cd docker
docker compose down

# 데이터 포함 완전 삭제 (주의!)
docker compose down -v

# 특정 서비스 재시작
docker compose restart ragflow-server

# 로그 실시간 확인
docker compose logs -f

# Ollama 모델 목록
ollama list

# Ollama 모델 삭제
ollama rm <model-name>
```

---

## 사용 시나리오: CS 데일리 리포트 관리

### 워크플로우

1. **매일 또는 주기적으로**:
   - CS 팀이 작성한 데일리 리포트 문서를 RAGFlow 지식베이스에 업로드
   - 자동 파싱 및 벡터화

2. **질의응답**:
   - 관리자나 팀원이 RAGFlow Chat을 통해 질문
   - "이번 주 가장 많이 발생한 이슈는?"
   - "고객 X의 문의 내역 요약"
   - "제품 Y에 대한 피드백 정리"

3. **검색 및 분석**:
   - 특정 키워드, 날짜, 제품으로 필터링
   - 문서에 있는 원문 그대로 답변
   - 잘못된 정보 생성 최소화 (Temperature 낮게 설정)

### 기대 효과

- ✅ **정확성**: 문서 기반 답변으로 환각(hallucination) 최소화
- ✅ **효율성**: 수백 개 리포트에서 즉시 정보 검색
- ✅ **확장성**: 문서 수가 증가해도 성능 유지
- ✅ **프라이버시**: 온프레미스 실행으로 데이터 외부 유출 없음

---

## 결론

이 가이드를 따라 RAGFlow를 Ollama와 함께 온프레미스 환경에서 실행하고, 한국어 문서에 최적화된 RAG 시스템을 구축할 수 있습니다.

**핵심 포인트**:
- ✅ Docker로 간편한 배포
- ✅ Ollama로 로컬 LLM 실행 (비용 절감)
- ✅ bge-m3로 한국어 임베딩 지원
- ✅ Infinity로 효율적인 벡터 저장
- ✅ CS 리포트 관리에 최적화된 설정

문제 발생 시 트러블슈팅 섹션을 참조하거나, RAGFlow 커뮤니티에 문의하세요.

**설치 완료 후 접속 URL**: http://localhost

즐거운 RAG 경험 되세요! 🚀
