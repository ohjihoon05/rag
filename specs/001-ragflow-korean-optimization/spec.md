# Feature Specification: RAGFlow 온프레미스 한국어 최적화 배포

**Version**: 1.0
**Date**: 2025-11-16
**Status**: Planning

## Overview

RAGFlow 온프레미스 배포를 Ollama 기반 로컬 LLM과 한국어 최적화 모델로 구성하여 CS 팀의 데일리 리포트 문서 검색 및 질의응답 시스템 구축

## Problem Statement

### Current Situation
- CS 팀이 매일 작성하는 데일리 리포트가 축적됨
- 문서 수가 계속 증가하여 수동 검색과 정보 찾기가 어려움
- 특정 고객 문의, 제품별 이슈, 시기별 트렌드 파악이 비효율적
- 외부 API 사용 시 비용 및 데이터 보안 문제

### Desired Outcome
- 온프레미스 환경에서 RAGFlow 실행
- Ollama 기반 로컬 LLM으로 비용 절감 및 데이터 보안 확보
- 한국어 문서에 최적화된 임베딩 및 검색 성능
- CS 리포트 업로드 시 자동 파싱 및 벡터화
- 자연어 질문으로 정확한 문서 기반 답변 제공

## Functional Requirements

### FR1: 온프레미스 배포 환경 구성
**Priority**: P0 (Critical)

- Docker Compose 기반 전체 스택 배포
- 다음 서비스 포함:
  - RAGFlow 메인 서버 (Flask API)
  - Task Executor (문서 파싱 워커)
  - MySQL (메타데이터 저장)
  - Infinity (벡터 데이터베이스)
  - Redis (큐 관리)
  - MinIO (파일 저장)
- 로컬 호스트의 Ollama 연결 (localhost:11434)
- 메모리 제약 환경 최적화 (15.54GB RAM)

**Acceptance Criteria**:
- `docker compose up -d` 명령으로 모든 서비스 실행 성공
- 모든 컨테이너가 healthy 상태 유지
- `http://localhost`에서 RAGFlow 웹 UI 접속 가능
- Ollama 연결 확인 (모델 목록 조회 가능)

### FR2: 한국어 최적화 모델 통합
**Priority**: P0 (Critical)

- **LLM**: qwen2.5:7b (이미 설치됨)
- **Embedding**: bge-m3 (다국어, 한국어 우수)
- **Reranking**: bge-reranker-v2-m3 (한국어 최적화)
- Ollama API를 통한 LLM 및 Embedding 모델 접근
- HuggingFace 기반 Reranking 모델 통합

**Acceptance Criteria**:
- RAGFlow 설정에서 Ollama 모델 선택 가능
- bge-m3 임베딩 모델로 한국어 문서 벡터화 성공
- Reranker 활성화 시 검색 정확도 향상 확인
- 한국어 질문에 대한 정확한 답변 생성

### FR3: 문서 업로드 및 파싱
**Priority**: P0 (Critical)

- Knowledge Base 생성 기능
- 다양한 문서 형식 지원 (PDF, DOCX, TXT, Excel, PPT)
- 자동 파싱 및 청킹 (DeepDoc 또는 General 파서)
- 한국어 문서에 적합한 청킹 크기 설정 (300-500 토큰)
- 파싱 진행 상황 모니터링

**Acceptance Criteria**:
- CS 데일리 리포트 PDF/DOCX 업로드 성공
- 파싱 완료 후 문서 청크가 Infinity에 저장
- 문서 내용 검색 시 관련 청크 반환
- 업로드 실패 시 에러 메시지 표시

### FR4: 질의응답 인터페이스
**Priority**: P0 (Critical)

- Chat 생성 및 Knowledge Base 연결
- 자연어 한국어 질문 입력
- 문서 기반 정확한 답변 생성
- 문서에 없는 내용은 명시적으로 "찾을 수 없음" 응답
- Temperature, Top K 등 파라미터 조정 가능

**Acceptance Criteria**:
- "지난주 고객 문의 중 가장 많았던 이슈는?" 같은 질문에 답변
- 답변이 실제 문서 내용과 일치
- 환각(hallucination) 최소화 (Temperature 0.1 설정)
- 검색된 문서 출처 표시

### FR5: 설정 및 관리 도구
**Priority**: P1 (High)

- `.env` 파일을 통한 환경 변수 관리
- `service_conf.yaml` 기반 서비스 설정
- Ollama 모델 관리 (추가, 삭제, 전환)
- Docker 서비스 상태 모니터링
- 로그 확인 및 트러블슈팅 도구

**Acceptance Criteria**:
- `.env` 수정 후 재시작으로 설정 반영
- Ollama 모델 추가/삭제 시 RAGFlow에서 즉시 사용 가능
- `docker compose logs` 명령으로 에러 진단 가능
- 메모리/CPU 사용량 모니터링 가능

## Non-Functional Requirements

### NFR1: Performance
- 문서 파싱 속도: 평균 10페이지/분 이상
- 질의 응답 속도: 5초 이내 (Top K=3 기준)
- 동시 사용자: 5-10명 지원
- 메모리 사용: 총 12GB 이하 (Docker + Ollama 포함)

### NFR2: Scalability
- 문서 수: 1,000개 이상 지원
- Knowledge Base: 여러 개 생성 가능 (팀별, 주제별 분리)
- 벡터 데이터베이스 크기: 50GB까지 확장 가능

### NFR3: Reliability
- 서비스 가동률: 95% 이상
- 자동 재시작: 서비스 크래시 시 자동 복구
- 데이터 백업: MySQL 및 MinIO 데이터 백업 지원

### NFR4: Security & Privacy
- 온프레미스 실행: 데이터 외부 전송 없음
- 사용자 인증: RAGFlow 내장 인증 시스템
- 네트워크 격리: Docker 내부 네트워크 사용
- 문서 접근 제어: Knowledge Base별 권한 관리 (향후)

### NFR5: Usability
- 웹 기반 UI: 별도 설치 불필요
- 한국어 UI 지원
- 직관적인 문서 업로드 (드래그 앤 드롭)
- 명확한 에러 메시지 및 가이드

## Technical Constraints

### TC1: Hardware
- RAM: 15.54GB (제한적, 최적화 필요)
- CPU: 8 cores (충분)
- Storage: 50GB+ 여유 공간 권장
- GPU: 선택사항 (CPU 모드로 실행 가능)

### TC2: Software
- OS: Windows 10/11 + WSL2
- Docker Desktop: v24.0.0+
- Docker Compose: v2.26.1+
- Ollama: 최신 버전
- Python: 3.10/3.11 (백엔드, Docker 내부)
- Node.js: 18.20.4+ (프론트엔드, Docker 내부)

### TC3: Network
- Ollama: localhost:11434 접근 필요
- RAGFlow 웹 UI: localhost:80 (HTTP)
- Docker 내부 통신: host.docker.internal 사용

### TC4: Integration
- Ollama API: `/v1/chat/completions`, `/v1/embeddings` 엔드포인트
- HuggingFace: Reranking 모델 로드 (선택적)
- Docker Compose profiles: infinity, cpu 프로필 사용

## Use Cases

### UC1: 일일 리포트 업로드 및 검색
**Actor**: CS 팀원

**Flow**:
1. RAGFlow 웹 UI 로그인
2. "CS 데일리 리포트" Knowledge Base 선택
3. 오늘 작성한 리포트 PDF 파일 업로드
4. 파싱 완료 대기 (진행률 표시)
5. Chat에서 "오늘 가장 많은 문의 유형은?" 질문
6. 업로드한 문서 기반 답변 확인

### UC2: 과거 데이터 분석
**Actor**: 팀 리더

**Flow**:
1. RAGFlow Chat 접속
2. "2025년 1월 15일부터 1월 20일까지 제품 A 관련 이슈 요약해줘" 질문
3. 관련 문서들에서 정보 추출 및 요약 제공
4. 출처 문서 확인 (어느 리포트에서 가져왔는지)

### UC3: 특정 고객 문의 이력 조회
**Actor**: 고객 지원 담당자

**Flow**:
1. Chat에서 "고객 X의 지난 3개월 문의 내역 정리해줘" 요청
2. 해당 고객 관련 문서 청크 검색
3. 시간순으로 정리된 문의 내역 답변
4. 추가 질문: "가장 빈번한 문제는 뭐야?"

### UC4: 모델 성능 튜닝
**Actor**: 시스템 관리자

**Flow**:
1. Ollama에서 새 한국어 모델 다운로드 (`ollama pull new-model`)
2. `service_conf.yaml` 수정하여 새 모델 지정
3. Docker 재시작 (`docker compose restart ragflow-server`)
4. 테스트 질문으로 답변 품질 비교
5. 더 좋은 모델로 최종 선택

## Out of Scope

다음 항목들은 현재 범위에 포함되지 않음:

- GPU 가속 (향후 옵션)
- 다중 사용자 권한 관리 (현재는 기본 인증만)
- 자동 보고서 생성
- 외부 API 통합 (Slack, Teams 등)
- 실시간 협업 기능
- 모바일 앱

## Success Metrics

- 문서 검색 정확도: 80%+ (관련 문서 상위 3개에 포함)
- 답변 정확도: 85%+ (실제 문서 내용 반영)
- 시스템 가동 시간: 95%+
- 평균 응답 시간: < 5초
- 사용자 만족도: 4/5 이상
- 메모리 사용: < 12GB (피크 시간 기준)

## Dependencies

### External Dependencies
- Ollama (localhost:11434)
- Docker Desktop
- HuggingFace (모델 다운로드, 선택적)

### Internal Dependencies
- RAGFlow v0.22.0+ (현재 설치된 버전)
- bge-m3 모델 (Ollama에서 다운로드)
- qwen2.5:7b 모델 (이미 설치됨)

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| 메모리 부족 (15.54GB RAM) | High | Medium | Infinity 사용, 메모리 제한 설정, 경량 모델 옵션 |
| Ollama 연결 실패 (Docker) | High | Low | host.docker.internal 사용, IP 직접 지정 옵션 |
| 한국어 검색 정확도 부족 | Medium | Medium | bge-m3 사용, Reranker 활성화, 청킹 최적화 |
| 문서 파싱 실패 (암호화 PDF 등) | Low | Low | 에러 메시지, 대체 형식 안내 |
| Infinity 서비스 불안정 | Medium | Low | Elasticsearch 폴백 옵션 제공 |

## Timeline

**Phase 1: Environment Setup** (Day 1)
- Docker 환경 구성
- Ollama 모델 다운로드
- 설정 파일 수정

**Phase 2: Deployment** (Day 2)
- Docker Compose 실행
- 서비스 상태 확인
- Ollama 연결 테스트

**Phase 3: Model Integration** (Day 3)
- bge-m3 임베딩 설정
- Reranker 통합
- 모델 성능 테스트

**Phase 4: Testing & Optimization** (Day 4-5)
- 샘플 문서 업로드
- 질의응답 테스트
- 메모리/성능 최적화
- 트러블슈팅 가이드 작성

## References

- RAGFlow Documentation: https://ragflow.io/docs/
- Ollama Documentation: https://ollama.com/
- BGE Models: https://github.com/FlagOpen/FlagEmbedding
- Installation Guide: `RAGFlow_온프레미스_설치_가이드.md`
