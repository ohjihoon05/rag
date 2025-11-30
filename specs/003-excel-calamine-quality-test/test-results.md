# Excel Quality Test Results

**Test Date**: 2025-11-30
**RAGFlow Version**: v0.22.0
**Embedding Model**: bge-m3@Ollama
**LLM Model**: qwen2.5:7b

## Test Summary

| Metric | Result |
|--------|--------|
| Parsing Time | ~130 seconds |
| Chunks Created | 416 |
| Korean Encoding | **PASS** |
| Direct Retrieval | **PASS** (30 chunks found) |
| Chat Completions | **FAIL** (0 chunks returned) |
| Accuracy | 0/5 (0%) |
| Hallucinations | 0/4 (Good) |

## Key Findings

### 1. Excel Parsing Performance
- **Time**: ~130 seconds for 6,000 rows
- **Engine**: openpyxl (calamine has encoding issues)
- **Chunks**: 416 HTML table chunks generated

### 2. Korean Encoding - FIXED
The chunks are stored with proper Korean encoding:
- `<caption>영업보고서</caption>` - Sales Report
- `<td>한소희</td>` - Person name (Han So-hee)
- `<th>담당자</th>` - Manager column header

### 3. Retrieval API - Working
Direct `/api/v1/retrieval` API successfully finds Korean content:
- Query: "한소희" → Found 30 matching chunks
- Semantic search working correctly

### 4. Chat Completions API - NOT WORKING
The `/api/v1/chats/{id}/completions` endpoint returns empty results:
- Reference chunks: 0
- Answer: "해당 데이터가 없습니다"
- Prompt knowledge variable: empty

**Root Cause Analysis**:
The Chat API's internal retrieval mechanism is not retrieving chunks, despite:
- Correct dataset_ids configuration
- Working direct retrieval API
- Proper embedding model settings

This appears to be a **RAGFlow bug** or misconfiguration in the chat completions pipeline.

## Test Questions

### Accuracy Tests (All Failed due to Chat API issue)
| Q# | Question | Expected | Result |
|----|----------|----------|--------|
| 1 | 한소희 담당자의 총 거래 건수 | 289건 | FAIL |
| 2 | 제품E의 총 판매수량 | 159,726 | FAIL |
| 3 | 매출액이 가장 높은 담당자 | 이영희 | FAIL |
| 4 | 어떤 부서들이 있나요 | 영업부, 인사부, 재무부 등 | FAIL |
| 5 | 서울 지역 판매 데이터 유무 | 있음 | FAIL |

### Hallucination Tests (All Passed - No false data generated)
| H# | Question | Result |
|----|----------|--------|
| 1 | 김영수 담당자 매출 (존재안함) | OK - 없다고 응답 |
| 2 | 제품Z 판매현황 (존재안함) | OK - 없다고 응답 |
| 3 | 제주도 지역 매출 (존재안함) | OK - 없다고 응답 |
| 4 | 2024년 매출 데이터 (존재안함) | OK - 없다고 응답 |

## Recommendations

1. **Excel Parsing**: Working correctly with openpyxl. Consider investigating calamine encoding issues for potential performance improvement.

2. **Chat API Debug**: Need to investigate why chat completions API doesn't retrieve chunks:
   - Check similarity threshold settings
   - Verify embedding model consistency
   - Review chat configuration in database

3. **Workaround**: Use direct retrieval API + manual LLM integration instead of chat completions.

## Files

- Test script: `scripts/calamine_quality_test.py`
- Chunk sample: `specs/003-excel-calamine-quality-test/chunk_sample.json`
- Test questions: `specs/003-excel-calamine-quality-test/test-questions.md`
