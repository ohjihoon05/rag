# Chat Completions API Fix - Implementation Plan

## Executive Summary

Chat Completions API가 검색 결과를 0으로 반환하는 문제를 해결하기 위한 구현 계획입니다.

## Root Cause Analysis

### Issue 1: Session ID Required (Critical)

**Location**: `api/apps/sdk/session.py:126-127`

```python
if not req.get("session_id"):
    req["question"] = ""
```

**Problem Flow**:
1. Client calls `/api/v1/chats/{id}/completions` without session_id
2. `session.py:126-127` sets `question = ""`
3. Empty question passed to `dialog_service.chat()`
4. Retrieval runs with empty query
5. No chunks found (0 results)

**Evidence**:
- Direct Retrieval API works (30 chunks) - doesn't require session_id
- Chat Completions API fails (0 chunks) - requires session_id

### Issue 2: Embedding Dimension 0 Error (Blocking)

**Error**:
```
WARNING: The dimension of query and chunk do not match: 0 vs. 0
ValueError: Found array with 0 feature(s) (shape=(1, 0))
```

**Call Stack**:
```
dialog_service.chat()
  → get_models() [line 211-233]
    → LLMBundle(dialog.tenant_id, LLMType.EMBEDDING, embedding_list[0])
  → retriever.retrieval()
    → search.py:get_vector() [line 52-60]
      → emb_mdl.encode_queries(txt) [line 53]
        → OllamaEmbed.encode_queries() [line 287-295]
          → self.client.embeddings() - FAILS SILENTLY
    → hybrid_similarity() with empty vector [line 219-227]
      → cosine_similarity([avec], bvecs) - CRASHES
```

**Root Cause**:
`OllamaEmbed.encode_queries()` at line 287-295:
```python
def encode_queries(self, text):
    # ...
    res = self.client.embeddings(prompt=text, model=self.model_name, ...)
    try:
        return np.array(res["embedding"]), 128
    except Exception as _e:
        log_exception(_e, res)
        # NO RETURN STATEMENT - returns None implicitly!
```

If Ollama API fails or returns unexpected response, the method returns `None`, causing:
- `q_vec` becomes `None` or empty
- `hybrid_similarity` receives empty vector
- `cosine_similarity` crashes with shape=(1, 0) error

## Implementation Plan

### Phase 1: Fix Session ID Requirement

**File**: `api/apps/sdk/session.py`

**Change**: Modify lines 126-127 to preserve question when no session_id

```python
# Before (line 126-127):
if not req.get("session_id"):
    req["question"] = ""

# After:
if not req.get("session_id"):
    # Create a new session for single-question mode
    # Don't clear the question - allow stateless queries
    pass  # or create temporary session
```

**Alternative Approach**: Auto-create session if not provided
```python
if not req.get("session_id"):
    # Auto-create temporary session for single queries
    session = Session.create(dialog_id=req.get("chat_id"))
    req["session_id"] = session.id
```

### Phase 2: Fix Embedding Error Handling

**File**: `rag/llm/embedding_model.py`

**Change**: Add proper error handling in `OllamaEmbed.encode_queries()`

```python
# Before (line 287-295):
def encode_queries(self, text):
    for token in OllamaEmbed._special_tokens:
        text = text.replace(token, "")
    res = self.client.embeddings(prompt=text, model=self.model_name, ...)
    try:
        return np.array(res["embedding"]), 128
    except Exception as _e:
        log_exception(_e, res)
        # Returns None - BUG!

# After:
def encode_queries(self, text):
    for token in OllamaEmbed._special_tokens:
        text = text.replace(token, "")
    try:
        res = self.client.embeddings(prompt=text, model=self.model_name, ...)
        embedding = res.get("embedding")
        if embedding is None or len(embedding) == 0:
            raise ValueError(f"Empty embedding returned for model {self.model_name}")
        return np.array(embedding), 128
    except Exception as e:
        logging.error(f"OllamaEmbed.encode_queries failed: {e}")
        raise  # Propagate error instead of returning None
```

### Phase 3: Add Defensive Checks

**File**: `rag/nlp/search.py`

**Change**: Add validation before calling hybrid_similarity

```python
# At line 121-122, after get_vector:
matchDense = self.get_vector(qst, emb_mdl, topk, req.get("similarity", 0.1))
q_vec = matchDense.embedding_data

# Add validation:
if not q_vec or len(q_vec) == 0:
    logging.error(f"Empty query vector returned for query: {qst[:50]}...")
    raise ValueError("Embedding model returned empty vector")
```

**File**: `rag/nlp/query.py`

**Change**: Add input validation in hybrid_similarity

```python
# At line 219:
def hybrid_similarity(self, avec, bvecs, atks, btkss, tkweight=0.3, vtweight=0.7):
    # Add validation
    if avec is None or len(avec) == 0:
        raise ValueError("Query vector (avec) is empty")
    if bvecs is None or len(bvecs) == 0:
        logging.warning("No chunk vectors (bvecs) provided")
        return np.array([]), [], []

    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    # ... rest of function
```

## Testing Plan

### Test 1: Session ID Behavior
```python
# Test without session_id (should now work)
response = requests.post(
    f"{BASE_URL}/api/v1/chats/{CHAT_ID}/completions",
    headers=headers,
    json={"question": "한소희"}
)
assert response.json()["data"]["answer"] != "해당 데이터가 없습니다"
```

### Test 2: Embedding Error Handling
```python
# Verify embedding errors are properly raised, not silently ignored
# Check RAGFlow logs for proper error messages instead of silent failures
```

### Test 3: Quality Test
```bash
python scripts/calamine_quality_test.py
# Expected: Accuracy >= 60%
```

## Implementation Order

1. **Fix Issue 1 (Session ID)** - Required for basic functionality
2. **Fix Issue 2 (Embedding Error)** - Required for reliability
3. **Add Defensive Checks** - Improve debugging
4. **Run Quality Tests** - Validate fixes
5. **Clean up debug logging** - Production readiness

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing session-based flows | Medium | High | Add backward compatibility check |
| Ollama connection issues masked | Low | Medium | Add explicit connection validation |
| Performance impact from extra validation | Low | Low | Validation is O(1) |

## Success Criteria

1. Chat Completions API returns chunks (> 0) without session_id
2. Embedding errors are properly raised with clear error messages
3. Quality test accuracy >= 60%
4. No regression in session-based flows

## Files to Modify

| File | Change Type | Priority |
|------|-------------|----------|
| `api/apps/sdk/session.py` | Modify session logic | P0 |
| `rag/llm/embedding_model.py` | Fix error handling | P0 |
| `rag/nlp/search.py` | Add validation | P1 |
| `rag/nlp/query.py` | Add validation | P1 |
| `scripts/calamine_quality_test.py` | Update test | P2 |
