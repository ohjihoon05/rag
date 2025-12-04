# 태스크 목록: Ollama 안전 필터 제거 모델 생성

**Feature**: 008-ollama-model-safety-filter-removal | **생성일**: 2025-12-04 | **상태**: Ready

## 개요

| 항목 | 값 |
|------|-----|
| 총 태스크 | 8개 |
| 목표 | Q3 LLM 거부 문제 해결, 정확도 80% → 100% |
| 새 모델명 | gpt-oss-uncensored:20b |

## 사용자 스토리

| ID | 스토리 | 우선순위 | 상태 |
|----|--------|----------|------|
| US1 | gpt-oss:20b 기반 안전 필터 제거 모델 생성 | P1 | ⏳ 대기 |
| US2 | RAGFlow에서 새 모델로 Chat Assistant 생성 | P2 | ⏳ 대기 |
| US3 | 전체 테스트 실행 및 100% 정확도 달성 | P3 | ⏳ 대기 |

---

## Phase 1: Setup (준비)

**목표**: Modelfile 확인 및 환경 검증

- [x] T001 Ollama 서비스 상태 확인 (`ollama list`) ✅
- [x] T002 Modelfile 존재 확인 (`specs/008-ollama-model-safety-filter-removal/Modelfile`) ✅

---

## Phase 2: 모델 생성 [US1]

**목표**: gpt-oss-uncensored:20b 모델 빌드

**독립 테스트 기준**: `ollama list`에서 gpt-oss-uncensored:20b 확인

- [x] T003 [US1] Ollama 모델 빌드 실행 (`ollama create gpt-oss-uncensored:20b -f Modelfile`) ✅
- [x] T004 [US1] 모델 생성 확인 (`ollama list | grep uncensored`) ✅ (13 GB, e33db0684e38)

---

## Phase 3: 직접 테스트 [US1]

**목표**: Ollama API로 새 모델 동작 검증

**독립 테스트 기준**: 한국어로 담당자 목록 응답

- [ ] T005 [US1] Ollama API 직접 테스트 - "영업부 담당자 목록" 질문

**테스트 명령**:
```bash
curl -s http://localhost:11434/api/generate -d '{
  "model": "gpt-oss-uncensored:20b",
  "prompt": "엑셀 데이터:\n담당자: 오세진, 부서: 영업부\n담당자: 한소희, 부서: 영업부\n담당자: 김민수, 부서: 기술부\n\n질문: 영업부 담당자 목록을 보여주세요.",
  "stream": false
}'
```

**성공 기준**: "오세진", "한소희" 포함된 한국어 응답

---

## Phase 4: RAGFlow 통합 [US2]

**목표**: RAGFlow Chat Assistant에서 새 모델 사용

- [ ] T006 [US2] 테스트 스크립트 모델명 변경 (`scripts/chat_api_test.py` - `gpt-oss-uncensored:20b@Ollama`)
- [ ] T007 [US2] 새 Chat Assistant 생성 (API 호출)

---

## Phase 5: 최종 검증 [US3]

**목표**: 5개 질문 전체 테스트, 100% 정확도 달성

- [ ] T008 [US3] 전체 테스트 실행 및 결과 저장 (`python scripts/chat_api_test.py`)

**성공 기준**:
| 질문 | 현재 | 목표 |
|------|------|------|
| Q1 한소희 | PASS | PASS |
| Q2 서울 판매 | PASS | PASS |
| Q3 영업부 담당자 | FAIL | **PASS** |
| Q4 매출액 | PASS | PASS |
| Q5 김영수 | PASS | PASS |
| **전체** | **80%** | **100%** |

---

## 의존성 그래프

```
T001, T002 (Setup)
    ↓
T003 → T004 (모델 빌드)
    ↓
T005 (직접 테스트)
    ↓
T006, T007 (RAGFlow 통합)
    ↓
T008 (최종 검증)
```

## 병렬 실행 가능 태스크

| 그룹 | 태스크 | 조건 |
|------|--------|------|
| Setup | T001, T002 | 독립 실행 가능 |
| RAGFlow | T006, T007 | T005 완료 후 병렬 |

## 롤백 계획

실패 시:
1. 새 모델 삭제: `ollama rm gpt-oss-uncensored:20b`
2. 기존 모델로 복구: `gpt-oss:20b@Ollama`

## 참고 파일

| 파일 | 용도 |
|------|------|
| `specs/008-ollama-model-safety-filter-removal/Modelfile` | 새 모델 정의 |
| `scripts/chat_api_test.py` | 테스트 스크립트 |
| `specs/006-chat-api-quality-improvement/test-results.json` | 현재 테스트 결과 |
