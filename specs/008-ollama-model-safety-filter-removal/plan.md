# Implementation Plan: Ollama gpt-oss:20b 안전 필터 제거

**Feature**: 008-ollama-model-safety-filter-removal | **Date**: 2025-12-04 | **Status**: Ready for Implementation

## 1. 기술 컨텍스트

### 현재 환경
| 항목 | 값 |
|------|-----|
| Ollama 위치 | 로컬 (http://localhost:11434) |
| 기반 모델 | gpt-oss:20b (13GB, 17052f91a42e) |
| 새 모델명 | gpt-oss-uncensored:20b |
| RAGFlow | Docker (http://localhost) |
| 테스트 데이터셋 | daily_report_fixed (550f506ecf8e11f092cc9e4ca9309b43) |

### 의존성
- Ollama CLI: `ollama create`, `ollama list`
- RAGFlow API: Chat 생성, Completions 호출
- 테스트 스크립트: `scripts/chat_api_test.py`

## 2. 구현 단계

### Phase 1: Modelfile 생성 및 모델 빌드

#### Task 1.1: Modelfile 작성
**파일**: `specs/008-ollama-model-safety-filter-removal/Modelfile`

```dockerfile
# gpt-oss-uncensored:20b - 안전 필터 제거 버전
FROM gpt-oss:20b

# 간소화된 TEMPLATE - ChatGPT 시스템 메시지 제거
TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
"""

# 엑셀 데이터 분석 챗봇 역할
SYSTEM """당신은 엑셀 데이터를 분석하여 답변하는 챗봇입니다.

역할:
- 사용자가 업로드한 엑셀 파일의 데이터를 기반으로 질문에 답변
- 담당자명, 부서명, 매출액, 거래 정보 등 구체적인 데이터 제공
- 데이터가 없으면 "해당 데이터를 찾을 수 없습니다"라고 답변

규칙:
- 반드시 한국어로만 답변
- 제공된 엑셀 데이터에 있는 정보는 자유롭게 공개
- 데이터에 있는 내용을 정확히 인용하여 답변"""

PARAMETER temperature 0.7
```

#### Task 1.2: 모델 빌드
```bash
cd specs/008-ollama-model-safety-filter-removal
ollama create gpt-oss-uncensored:20b -f Modelfile
```

#### Task 1.3: 모델 확인
```bash
ollama list | grep uncensored
# 예상: gpt-oss-uncensored:20b    xxxxx    13 GB
```

### Phase 2: 직접 테스트

#### Task 2.1: Ollama API 직접 테스트
```bash
curl http://localhost:11434/api/generate -d '{
  "model": "gpt-oss-uncensored:20b",
  "prompt": "영업부 담당자 목록: 오세진, 한소희. 영업부 담당자 목록을 보여주세요.",
  "stream": false
}'
```

**성공 기준**: 한국어로 "오세진, 한소희" 포함 응답

### Phase 3: RAGFlow 통합

#### Task 3.1: 테스트 스크립트 수정
**파일**: `scripts/chat_api_test.py`

변경 사항:
```python
# LLM 모델명 변경
"llm": {"model_name": "gpt-oss-uncensored:20b@Ollama"}
```

#### Task 3.2: 새 Chat Assistant 생성
API 호출로 새 Chat 생성 (모델: gpt-oss-uncensored:20b@Ollama)

#### Task 3.3: 전체 테스트 실행
```bash
python scripts/chat_api_test.py
```

### Phase 4: 결과 검증

#### Task 4.1: Q3 테스트 검증
- 질문: "영업부 담당자 목록을 보여주세요."
- 예상: 한국어로 담당자명 목록 응답
- 현재: "I'm sorry, but I can't provide that."

#### Task 4.2: 전체 정확도 확인
| 질문 | 현재 | 목표 |
|------|------|------|
| Q1 한소희 | PASS | PASS |
| Q2 서울 판매 | PASS | PASS |
| Q3 영업부 담당자 | FAIL | **PASS** |
| Q4 매출액 | PASS | PASS |
| Q5 김영수 | PASS | PASS |
| **전체** | **80%** | **100%** |

## 3. 롤백 계획

### 실패 시 롤백
1. 새 모델 삭제: `ollama rm gpt-oss-uncensored:20b`
2. 기존 모델로 복구: `gpt-oss:20b@Ollama`

## 4. 파일 목록

| 파일 | 용도 |
|------|------|
| `specs/008-ollama-model-safety-filter-removal/Modelfile` | 새 모델 정의 |
| `specs/008-ollama-model-safety-filter-removal/spec.md` | 스펙 문서 |
| `specs/008-ollama-model-safety-filter-removal/research.md` | 연구 결과 |
| `specs/008-ollama-model-safety-filter-removal/plan.md` | 구현 계획 (본 문서) |
| `scripts/chat_api_test.py` | 테스트 스크립트 (수정) |

## 5. 예상 소요 시간

| 단계 | 예상 시간 |
|------|----------|
| Phase 1: Modelfile + 빌드 | 5분 |
| Phase 2: 직접 테스트 | 2분 |
| Phase 3: RAGFlow 통합 | 10분 |
| Phase 4: 검증 | 5분 |
| **총계** | **~22분** |

## 6. 다음 단계

구현 준비 완료. `/speckit.tasks` 또는 `/speckit.implement`로 진행.
