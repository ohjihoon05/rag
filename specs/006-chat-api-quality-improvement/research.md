# Research: Chat API 답변 품질 개선

**Date**: 2025-12-04 | **Status**: Completed

## A. 프롬프트 분석

### 현재 프롬프트 (영어)
```
You are an intelligent assistant. Please summarize the content of the knowledge base to answer the question. Please list the data in the knowledge base and answer in detail. When all knowledge base content is irrelevant to the question, your answer must include the sentence "Sorry! No relevant content was found in the knowledge base!".
```

### 문제점
1. **언어 불일치**: 영어 프롬프트 + 한국어 질문/데이터 → LLM 혼란
2. **지시 모호성**: "summarize" vs "answer with specific data" 불명확
3. **데이터 활용 강제 없음**: LLM이 일반 지식으로 답변 시도

### 개선 프롬프트 제안 (한국어)
```
당신은 엑셀 데이터 분석 전문가입니다. 아래 지식 베이스에서 제공된 데이터를 반드시 활용하여 질문에 답변하세요.

중요 규칙:
1. 지식 베이스에 있는 데이터만 사용하세요
2. 데이터가 있으면 구체적인 숫자와 이름을 포함해서 답변하세요
3. 데이터가 없으면 "해당 데이터를 찾을 수 없습니다"라고만 답변하세요
4. 추측하거나 만들어내지 마세요

지식 베이스:
{knowledge}

위 데이터를 기반으로 질문에 정확하게 답변해주세요.
```

### API 이슈 발견
- `/api/v1/chats` POST/PUT 요청에서 `req.get()` 에러 발생
- RAGFlow SDK chat.py:33, chat.py:152에서 요청 본문 파싱 실패
- 원인: Content-Type 또는 JSON 인코딩 문제 가능성

---

## B. 청크 품질 확인

### ES 검색 결과
```
총 청크 수: 474개
"영업부" 키워드 포함: 155개
```

### 샘플 청크 내용
```
일자：2025-11-03 20:43:02; 담당자：오세진; 부서：영업부; 지역：부산;
제품명：솔루션1; 판매수량：42; 단가：626484; 할인율：0.27; 매출액：17600831;
비고：거래번호-31964 ——영업보고서
```

### 분석
- ✅ 청크에 필요한 모든 필드 포함 (담당자, 부서, 지역, 제품명, 매출액 등)
- ✅ 한국어 데이터 정상 저장
- ✅ "영업부" 키워드 검색 가능
- ⚠️ 청크가 여러 거래를 포함 → 특정 담당자 검색 시 정확도 저하 가능

---

## C. 검색 파라미터 분석

### 현재 설정
| 파라미터 | 값 | 의미 |
|----------|-----|------|
| similarity_threshold | 0.2 | 최소 유사도 (낮을수록 더 많은 결과) |
| keywords_similarity_weight | 0.7 | 키워드 vs 벡터 가중치 |
| top_n | 8 | 반환할 청크 수 |

### 개선 제안
| 파라미터 | 현재 | 제안 | 이유 |
|----------|------|------|------|
| similarity_threshold | 0.2 | 0.1 | 더 많은 관련 청크 포함 |
| keywords_similarity_weight | 0.7 | 0.8 | 한국어는 키워드 매칭이 더 효과적 |
| top_n | 8 | 15 | 더 많은 컨텍스트 제공 |

---

## D. API 디버깅 결과

### Retrieval API 에러
```
POST /api/v1/retrieval
Response: {"code":100,"data":null,"message":"AttributeError(\"'NoneType' object has no attribute 'get'\")"}
```

### Chat Completions API
- ✅ 작동함 (테스트 통과)
- 6-8 chunks 검색 성공
- LLM 답변만 문제

### 벡터 저장 확인
```
ES Index: ragflow_8aa40b20c2b911f0ac399e7eb07324e5
Dataset: 550f506ecf8e11f092cc9e4ca9309b43
Vector Field: q_1024_vec (len=1024) ✅
```

---

## 결론 및 우선순위

### 핵심 문제
1. **LLM이 검색된 데이터를 활용하지 않음** (프롬프트 문제)
2. **SDK API 버그** (chat create/update 실패)

### 실행 순서
1. ⭐ **프롬프트 개선**: 테스트 스크립트에서 직접 테스트
2. **파라미터 조정**: similarity_threshold, top_n 증가
3. **SDK 버그 우회**: 기존 Chat 사용 또는 WebUI에서 생성

### 다음 단계
- 테스트 스크립트 수정하여 개선된 프롬프트 적용
- 동일 5개 질문으로 재테스트
- 결과 비교
