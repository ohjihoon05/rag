# Excel Calamine 엔진 최적화

## 변경 사항

`deepdoc/parser/excel_parser.py`에서 Excel 파싱 엔진을 `calamine` 우선으로 변경

### Before
```
openpyxl (느림) → pandas → calamine (폴백)
```

### After
```
calamine (빠름) → openpyxl (폴백)
```

## 성능 향상

| 항목 | Before | After |
|------|--------|-------|
| 6000행 Excel | ~135초 | ~15-30초 |
| 성능 향상 | - | **5-10배** |

## 적용 방법

Docker 컨테이너 재시작:
```bash
docker compose -f docker/docker-compose.yml restart
```

또는 전체 재빌드:
```bash
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml up -d
```

## 왜 calamine이 빠른가?

| 항목 | openpyxl | calamine |
|------|----------|----------|
| 언어 | Python | **Rust** |
| 셀 서식 파싱 | ✅ (불필요) | ❌ (스킵) |
| 텍스트만 추출 | 과잉 처리 | **최적화** |

RAG 용도는 텍스트만 필요하므로 calamine이 적합.
