# Chat Completions API Debug Findings

**Date**: 2025-11-30
**Status**: Investigation Complete - Multiple Issues Found

## Summary

Chat completions API (`/api/v1/chats/{id}/completions`) 에서 검색 결과가 0으로 반환되는 문제를 조사했습니다.

## Discovered Issues

### Issue 1: Session ID Required (CRITICAL)

**Location**: `api/apps/sdk/session.py:126-127`

```python
if not req.get("session_id"):
    req["question"] = ""
```

**Problem**: `session_id`가 제공되지 않으면 질문이 빈 문자열로 설정됩니다.

**Impact**: 모든 검색이 빈 질문으로 실행되어 결과가 없음.

**Fix Applied**: 테스트 스크립트에서 `session_id`를 먼저 생성하도록 수정.

### Issue 2: Embedding Dimension Mismatch (BLOCKING)

**Error**:
```
The dimension of query and chunk do not match: 0 vs. 0
ValueError: Found array with 0 feature(s) (shape=(1, 0))
```

**Observed Behavior**:
- Direct retrieval API (`/api/v1/retrieval`) → Works (30 chunks found)
- Chat completions API → Fails (0 chunks, embedding error)

**Root Cause Analysis**:
- Chat completions uses `dialog_service.py` which calls `retriever.retrieval()`
- Direct retrieval uses `doc.py` which also calls `settings.retriever.retrieval()`
- Both should use the same retriever, but embeddings return 0 dimensions in chat completions

**Suspected Cause**:
- `LLMBundle` initialization difference between the two paths
- Possible caching issue with embedding model
- Tensor/array conversion problem in hybrid_similarity function

### Issue 3: Parameters vs Variables Naming (RESOLVED)

**Location**: `api/apps/sdk/chat.py:64`

```python
key_mapping = {"parameters": "variables", ...}
```

**Problem**: API uses `variables` but internal code uses `parameters`.

**Status**: Working correctly after investigation - mapping is handled properly.

## Code Changes Made

### 1. `api/db/services/dialog_service.py`

**Line 377-379** - Fixed attachments initialization:
```python
# Before:
attachments = kwargs["doc_ids"].split(",") if "doc_ids" in kwargs else []

# After:
attachments = kwargs["doc_ids"].split(",") if "doc_ids" in kwargs else None
```

**Line 432** - Fixed knowledge retrieval condition:
```python
# Before:
if attachments is not None and "knowledge" in [p["key"] for p in prompt_config["parameters"]]:

# After:
if "knowledge" in [p["key"] for p in prompt_config.get("parameters", [])]:
```

### 2. `scripts/calamine_quality_test.py`

Added `create_session()` function and modified `ask_question()` to use session_id.

## Current Test Results

| Test | Direct Retrieval API | Chat Completions API |
|------|---------------------|---------------------|
| Query: "한소희" | 30 chunks ✓ | 0 chunks ✗ |
| Embedding | Works | 0 dimensions |
| Error | None | ValueError |

## Next Steps

1. **Debug embedding model loading** in `dialog_service.py` vs `doc.py`
2. **Compare LLMBundle** initialization paths
3. **Check hybrid_similarity** function for tensor handling issues
4. **Verify Ollama connection** is consistent across both API paths

## Files Modified

- `api/db/services/dialog_service.py`
- `scripts/calamine_quality_test.py`

## Workaround

Until the embedding issue is resolved, use the direct retrieval API (`/api/v1/retrieval`) combined with manual LLM calls instead of chat completions.
