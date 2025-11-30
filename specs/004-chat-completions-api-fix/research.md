# Chat Completions API Debug Research

**Date**: 2025-11-30
**Status**: Investigation Complete

## Summary

Chat Completions API (`/api/v1/chats/{id}/completions`)에서 검색 결과가 0으로 반환되는 문제를 조사했습니다.

## Test Environment

| Component | Value |
|-----------|-------|
| Dataset | `test_nohtml_1764510007` |
| Chunks | 474 |
| Embedding Model | `bge-m3@Ollama` |
| Test File | `daily_report_sample.xlsx` (6000 rows, Korean) |
| Test Query | "한소희" (담당자 이름) |

## Comparison Test Results

| API | Endpoint | Result |
|-----|----------|--------|
| Direct Retrieval | `/api/v1/retrieval` | ✅ 30 chunks found |
| Chat Completions | `/api/v1/chats/{id}/completions` | ❌ 0 chunks (error) |

## Issue 1: Session ID Required

### Discovery

**Location**: `api/apps/sdk/session.py:126-127`

```python
if not req.get("session_id"):
    req["question"] = ""
```

### Code Flow Analysis

```
Client Request (no session_id)
    ↓
session.py:126-127: req["question"] = ""
    ↓
dialog_service.chat(): empty question
    ↓
retriever.retrieval(): search with ""
    ↓
Result: 0 chunks
```

### Verification

Added debug logging to trace the issue:
```python
# dialog_service.py에 추가한 디버그 로그
logging.info(f"[DEBUG] questions: {questions}")
```

Output showed:
```
[DEBUG] questions: ['']  # Empty string!
```

After adding session_id to test:
```
[DEBUG] questions: ['한소희']  # Correct question
```

## Issue 2: Embedding Dimension 0 Error

### Error Message

```
WARNING: The dimension of query and chunk do not match: 0 vs. 0
ValueError: Found array with 0 feature(s) (shape=(1, 0)) while a minimum of 1 is required by check_pairwise_arrays.
```

### Call Stack Analysis

```
api/apps/sdk/session.py
  → @session_bp.post("completions")
    → DialogService.chat(dialog, messages, **req)

api/db/services/dialog_service.py
  → def chat(dialog, messages, *, regenerate=False, **kwargs)
    → get_models(dialog)  [line 211-233]
      → embd_mdl = LLMBundle(dialog.tenant_id, LLMType.EMBEDDING, embedding_list[0])
    → retriever.retrieval(questions, embd_mdl, ...)  [line 445]

rag/nlp/search.py
  → def retrieval(question, embd_mdl, ...)  [line 358]
    → sres = self.search(req, ...)  [line 387]
      → def search(req, ...)  [line 73]
        → matchDense = self.get_vector(qst, emb_mdl, ...)  [line 121]
          → qv, _ = emb_mdl.encode_queries(txt)  [line 53]
            → OllamaEmbed.encode_queries()  # FAILS HERE

rag/nlp/query.py
  → hybrid_similarity(avec, bvecs, ...)  [line 219]
    → cosine_similarity([avec], bvecs)  [line 223]
      # CRASH: avec has 0 dimensions
```

### Root Cause

**File**: `rag/llm/embedding_model.py:287-295`

```python
class OllamaEmbed(Base):
    def encode_queries(self, text):
        for token in OllamaEmbed._special_tokens:
            text = text.replace(token, "")
        res = self.client.embeddings(prompt=text, model=self.model_name, ...)
        try:
            return np.array(res["embedding"]), 128
        except Exception as _e:
            log_exception(_e, res)
            # BUG: No return statement - returns None implicitly!
```

When Ollama API fails or returns unexpected response:
1. Exception is caught
2. Exception is logged
3. Function returns `None` (implicit)
4. `q_vec` becomes `None` or empty
5. `hybrid_similarity` crashes

### LLMBundle Initialization Comparison

| Path | Location | Code |
|------|----------|------|
| Direct Retrieval | `doc.py:1457` | `LLMBundle(kb.tenant_id, LLMType.EMBEDDING, llm_name=kb.embd_id)` |
| Chat Completions | `dialog_service.py:219` | `LLMBundle(dialog.tenant_id, LLMType.EMBEDDING, embedding_list[0])` |

Both use `LLMBundle` but:
- Direct retrieval uses `llm_name=kb.embd_id` (keyword argument)
- Chat completions uses positional argument `embedding_list[0]`

### LLM4Tenant Initialization

**File**: `api/db/services/tenant_llm_service.py:247-252`

```python
class LLM4Tenant:
    def __init__(self, tenant_id, llm_type, llm_name=None, lang="Chinese", **kwargs):
        self.tenant_id = tenant_id
        self.llm_type = llm_type
        self.llm_name = llm_name
        self.mdl = TenantLLMService.model_instance(tenant_id, llm_type, llm_name, lang=lang, **kwargs)
```

### model_instance Method

**File**: `api/db/services/tenant_llm_service.py:131-138`

```python
@classmethod
@DB.connection_context()
def model_instance(cls, tenant_id, llm_type, llm_name=None, lang="Chinese", **kwargs):
    model_config = TenantLLMService.get_model_config(tenant_id, llm_type, llm_name)
    kwargs.update({"provider": model_config["llm_factory"]})
    if llm_type == LLMType.EMBEDDING.value:
        if model_config["llm_factory"] not in EmbeddingModel:
            return None  # Returns None if factory not found!
        return EmbeddingModel[model_config["llm_factory"]](
            model_config["api_key"],
            model_config["llm_name"],
            base_url=model_config["api_base"]
        )
```

## Key Findings

### 1. Session Requirement
- Without `session_id`, the question is cleared to empty string
- This is intentional design for session-based conversation
- But breaks single-query use cases

### 2. Silent Error Handling
- `OllamaEmbed.encode_queries()` silently returns None on failure
- No error propagation to caller
- Makes debugging difficult

### 3. No Input Validation
- `hybrid_similarity()` doesn't validate input vectors
- Crashes with cryptic sklearn error instead of clear message

## Recommended Fixes

### Fix 1: Session Handling
```python
# api/apps/sdk/session.py:126-127
if not req.get("session_id"):
    # Option A: Allow stateless queries
    pass  # Don't clear question

    # Option B: Auto-create session
    # session = create_temporary_session(...)
    # req["session_id"] = session.id
```

### Fix 2: Error Handling
```python
# rag/llm/embedding_model.py:287-295
def encode_queries(self, text):
    try:
        res = self.client.embeddings(prompt=text, model=self.model_name, ...)
        embedding = res.get("embedding")
        if not embedding:
            raise ValueError(f"Empty embedding from {self.model_name}")
        return np.array(embedding), 128
    except Exception as e:
        logging.error(f"encode_queries failed: {e}")
        raise  # Propagate error
```

### Fix 3: Input Validation
```python
# rag/nlp/query.py:219
def hybrid_similarity(self, avec, bvecs, ...):
    if avec is None or len(avec) == 0:
        raise ValueError("Empty query vector")
    # ... rest of function
```

## Files Investigated

| File | Lines | Purpose |
|------|-------|---------|
| `api/apps/sdk/session.py` | 126-127 | Session requirement |
| `api/db/services/dialog_service.py` | 211-233, 445 | get_models, retrieval call |
| `api/db/services/tenant_llm_service.py` | 131-138, 247-252 | model_instance, LLM4Tenant |
| `api/db/services/llm_service.py` | 71-119 | LLMBundle class |
| `rag/llm/embedding_model.py` | 262-295 | OllamaEmbed class |
| `rag/nlp/search.py` | 52-60, 121-122 | get_vector, search |
| `rag/nlp/query.py` | 219-227 | hybrid_similarity |

## Test Scripts Created

- `scripts/calamine_quality_test.py` - Modified to use session_id
- Added `create_session()` function for session management

## Debug Logging Added

```python
# dialog_service.py
logging.info(f"[DEBUG] questions: {questions}")
logging.info(f"[DEBUG] attachments: {attachments}")
```

## Conclusion

Two distinct issues prevent Chat Completions API from working:

1. **Session ID Required** (CRITICAL): Without session_id, question is cleared
2. **Embedding Error Handling** (BLOCKING): Silent failures in OllamaEmbed

Both issues need to be fixed for the API to function correctly.
