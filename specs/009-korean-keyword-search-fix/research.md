# 009 Research: ES 한글 키워드 검색 분석

## 조사 결과

### 1. ES 인덱스 필드 매핑

| 필드 | Type | Index | 용도 |
|------|------|-------|------|
| `content_with_weight` | text | **false** | 저장용 (검색 불가) |
| `content_ltks` | text | **true** | **전문 검색용** |
| `content_sm_ltks` | text | true | 요약 검색용 |
| `부서_tks` | text | true | 구조화 필드 |
| `담당자_tks` | text | true | 구조화 필드 |

### 2. 검색 테스트 결과

```python
# 검색 가능한 필드
"부서_tks" → "영업부" = 1631건 ✅
"담당자_tks" → "한소희" = 1531건 ✅
"content_ltks" → "영업부" = 2080건 ✅

# 검색 불가 필드 (index=false)
"content_with_weight" → "영업부" = 0건 ❌
```

### 3. RAGFlow 검색 로직 분석

**파일**: `rag/nlp/search.py`

```python
# Line 91: 검색 대상 필드
["docnm_kwd", "content_ltks", "kb_id", "img_id", "title_tks", ...]

# Line 291: 기본 검색 필드
cfield="content_ltks"
```

**결론**: RAGFlow는 `content_ltks` 필드를 사용하여 검색하며, 이 필드는 index=True로 검색 가능함.

### 4. Q3 실패 원인 재분석

Q3 "영업부 담당자 목록을 보여주세요" 테스트 결과:
- References: 0 chunks
- Response: "해당 데이터를 찾을 수 없습니다"

**가설들**:

#### A. similarity_threshold 문제
- 현재 threshold: 0.1
- "영업부 담당자"와 청크 내용의 유사도가 0.1 미만일 수 있음

#### B. Vector Search 실패
- bge-m3 임베딩이 "영업부 담당자"를 잘 표현하지 못함
- Hybrid search에서 vector weight가 높아 keyword 검색 결과가 무시됨

#### C. KB_ID 필터링 문제
- Chat에 연결된 dataset_id와 실제 검색 대상이 불일치
- 검색 시 kb_id 필터가 잘못 적용됨

### 5. 추가 검증 필요

```bash
# 1. similarity_threshold=0으로 테스트
# 2. vector search만 테스트
# 3. keyword search만 테스트
# 4. RAGFlow 검색 로그 확인
```

## 결론

### 원인
**ES 필드 매핑 문제가 아님** - `content_ltks`는 검색 가능하고 "영업부"가 2080건 매칭됨.

**실제 원인 후보**:
1. Hybrid search의 similarity_threshold 필터링
2. Vector search 단계에서 관련 청크를 찾지 못함
3. Dataset/KB_ID 필터링 문제

### 다음 단계
1. RAGFlow 검색 API 직접 호출하여 중간 결과 확인
2. similarity_threshold=0으로 테스트
3. 검색 로그 분석

## 대안 분석

| 전략 | 복잡도 | 위험도 | 효과 |
|------|--------|--------|------|
| A: threshold 조정 | 하 | 하 | 중 |
| B: keyword_weight 조정 | 하 | 하 | 중 |
| C: 검색 로직 디버깅 | 중 | 하 | 높음 |
| D: Vector-only 검색 | 하 | 중 | 미확인 |
