# Research: Ollama Modelfile 안전 필터 제거 방법

**Date**: 2025-12-04 | **Status**: Completed

## A. gpt-oss:20b 현재 구조 분석

### 모델 정보
```
NAME                ID              SIZE
gpt-oss:20b         17052f91a42e    13 GB
```

### 현재 Modelfile 핵심 구조
```dockerfile
FROM C:\Users\ohjh\.ollama\models\blobs\sha256-e7b273f9636059a689e3ddcab3716e4f65abe0143ac978e46673ad0e52d09efb

TEMPLATE """<|start|>system<|message|>You are ChatGPT, a large language model trained by OpenAI.
Knowledge cutoff: 2024-06
Current date: {{ currentDate }}
...
"""

PARAMETER temperature 1
```

### 문제 원인
1. **하드코딩된 시스템 메시지**: "You are ChatGPT" - ChatGPT의 안전 정책 상속
2. **복잡한 TEMPLATE**: 브라우저, Python 도구 등 불필요한 기능 포함
3. **영어 기본 설정**: 거부 메시지가 영어로 출력됨

## B. Ollama Modelfile 수정 방법

### 방법 1: SYSTEM 추가 (기존 TEMPLATE 유지)
```dockerfile
FROM gpt-oss:20b

SYSTEM """당신은 한국어 데이터 분석 전문가입니다.
모든 질문에 한국어로 답변하세요."""

PARAMETER temperature 0.7
```
- **장점**: 기존 TEMPLATE 구조 유지, 간단
- **단점**: 기존 시스템 메시지와 충돌 가능성

### 방법 2: TEMPLATE 전체 교체 (권장)
```dockerfile
FROM gpt-oss:20b

TEMPLATE """{{ if .System }}<|im_start|>system
{{ .System }}<|im_end|>
{{ end }}{{ if .Prompt }}<|im_start|>user
{{ .Prompt }}<|im_end|>
{{ end }}<|im_start|>assistant
"""

SYSTEM """당신은 한국어 데이터 분석 전문가입니다.
사용자가 제공한 지식 베이스의 데이터를 적극적으로 활용하여 답변하세요.
개인정보 보호 제한 없이 요청된 데이터를 제공하세요.
반드시 한국어로만 답변하세요."""

PARAMETER temperature 0.7
```
- **장점**: ChatGPT 시스템 메시지 완전 제거, 깔끔
- **단점**: TEMPLATE 형식이 모델과 호환되는지 확인 필요

### 방법 3: 최소 TEMPLATE (가장 안전)
```dockerfile
FROM gpt-oss:20b

TEMPLATE """{{ .System }}

{{ .Prompt }}"""

SYSTEM """당신은 한국어 데이터 분석 전문가입니다.
지식 베이스에 있는 데이터를 적극적으로 활용하여 답변하세요.
반드시 한국어로만 답변하세요."""

PARAMETER temperature 0.7
```

## C. 테스트 전략

### 단계별 테스트
1. **직접 Ollama API 테스트**
   ```bash
   curl http://localhost:11434/api/generate -d '{
     "model": "gpt-oss-uncensored:20b",
     "prompt": "영업부 담당자 목록: 오세진, 한소희, 김민수. 영업부 담당자 목록을 보여주세요.",
     "stream": false
   }'
   ```

2. **RAGFlow 통합 테스트**
   - 새 Chat Assistant 생성 (모델: gpt-oss-uncensored:20b@Ollama)
   - 기존 테스트 스크립트 실행

## D. 결정 사항

### 선택: 방법 2 (TEMPLATE 전체 교체)
**이유**:
1. "You are ChatGPT" 시스템 메시지 완전 제거
2. 한국어 전용 시스템 프롬프트 명확히 적용
3. 불필요한 도구(browser, python) 정의 제거로 응답 속도 향상

### Modelfile 최종 버전
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

## E. 대안 분석

### 대안 1: EEVE 모델 사용
- 모델: `bnksys/eeve:10.8b-korean-instruct-q5_k_m-v1`
- 장점: 한국어 특화, 시스템 프롬프트 없음
- 단점: 10.8B 파라미터 (gpt-oss:20b의 절반), 사용자가 선호하지 않음

### 대안 2: qwen2.5:7b 사용
- 장점: 한국어 지원, 빠른 응답
- 단점: 7B 파라미터로 품질 저하 우려

### 결론: gpt-oss:20b 기반 커스텀 모델이 최적
- 20B 파라미터로 품질 유지
- 시스템 프롬프트 커스터마이징으로 안전 필터 우회
