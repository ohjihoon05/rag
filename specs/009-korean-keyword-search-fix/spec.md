# 009: ES 한글 키워드 검색 실패 수정

## 문제 정의

### 현상
- Q3 "영업부 담당자 목록을 보여주세요" 질문에서 0 chunks 반환
- 데이터에 "영업부"가 존재함에도 ES match 쿼리로 검색 실패
- 결과: "해당 데이터를 찾을 수 없습니다"

### 근본 원인
ES의 기본 analyzer가 한글을 제대로 tokenize하지 못함:
- 데이터: `부서：영업부` 존재 확인됨
- ES `match` 쿼리: `{"match": {"content_with_weight": "영업부"}}` → 0건
- 한글 복합어가 token으로 분리되지 않아 keyword 매칭 실패

### 영향 범위
- RAGFlow hybrid search (vector + keyword) 중 keyword 검색 실패
- 특정 한글 키워드 포함 질문들의 retrieval 품질 저하

## 환경 정보

| 항목 | 값 |
|------|-----|
| ES Version | 8.11.3 |
| Dataset ID | 550f506ecf8e11f092cc9e4ca9309b43 |
| Document | daily_report_sample.xlsx (474 chunks) |
| Index Pattern | ragflow_* |

## 기술적 분석

### 현재 ES 인덱스 상태
```json
// content_with_weight 필드 샘플
"일자：2025-11-03; 담당자：오세진; 부서：영업부; 지역：부산..."
```

### 검색 실패 재현
```bash
# 0건 반환
curl -X GET "localhost:1200/ragflow_*/_search" -d '{"query":{"match":{"content_with_weight":"영업부"}}}'

# 474건 반환 (match_all)
curl -X GET "localhost:1200/ragflow_*/_search" -d '{"query":{"match_all":{}}}'
```

### 가능한 원인
1. **Standard Analyzer**: 한글을 character 단위로만 분리
2. **ICU Analyzer 미설치**: 한글 형태소 분석 플러그인 없음
3. **Nori Analyzer 미설치**: ES 공식 한글 분석기 없음

## 해결 전략

### Strategy A: Nori Analyzer 적용 (권장)
- ES 공식 한글 형태소 분석기
- 플러그인 설치 후 인덱스 재생성 필요
- 복잡도: 중 | 영향: 인덱스 재구축 필요

### Strategy B: N-gram Analyzer 사용
- 한글을 2-3 character n-gram으로 분리
- 플러그인 불필요, 설정만으로 가능
- 복잡도: 하 | 영향: 검색 정밀도 저하 가능

### Strategy C: RAGFlow 코드 수정
- keyword search 로직에서 한글 전처리 추가
- 형태소 분석 라이브러리 (konlpy 등) 사용
- 복잡도: 중 | 영향: 코드 변경 필요

### Strategy D: Vector Search Only
- keyword_similarity_weight를 0으로 설정
- vector 검색만 사용
- 복잡도: 하 | 영향: 검색 품질 변화

## 성공 기준

| 메트릭 | 현재 | 목표 |
|--------|------|------|
| Q3 "영업부 담당자" | FAIL (0 chunks) | PASS (>0 chunks) |
| 한글 키워드 검색 | 실패 | 성공 |
| 전체 테스트 정확도 | 80% (4/5) | 100% (5/5) |

## 테스트 방법

```bash
# ES 한글 검색 테스트
python -c "
import requests
r = requests.get('http://localhost:1200/ragflow_*/_search',
    auth=('elastic', 'infini_rag_flow'),
    json={'query': {'match': {'content_with_weight': '영업부'}}, 'size': 5})
print(f'영업부 검색: {r.json()[\"hits\"][\"total\"][\"value\"]}건')
"

# RAGFlow Chat API 테스트
python scripts/chat_api_test.py
```

## 참고 자료
- [ES Nori Plugin](https://www.elastic.co/guide/en/elasticsearch/plugins/current/analysis-nori.html)
- [RAGFlow ES Configuration](docker/service_conf.yaml.template)
- [008 Spec - 모델 안전 필터 제거](../008-ollama-model-safety-filter-removal/)
