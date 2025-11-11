# MASTER BACKLOG - AI-LAWYER SYSTEM AUDIT FIXES

## CRITICAL ISSUES (Sprint 1 - 3-5 days)

### C-01 | Critical | Утечка секретов в коде / секреты в репо
**Files**: `backend/app/core/config.py`, `backend/app/api/notifications.py`, any hardcoded keys  
**Reproduction**: `rg -n "SECRET_KEY|VAPID|API_KEY|OPENAI"`  
**Fix Summary**: Remove all hardcoded secrets, use os.getenv, add .env.example, connect Secret Manager in prod. Add pre-commit hook, CI-scan.  
**Patch**:
```python
# config.py
from pydantic import BaseSettings
class Settings(BaseSettings):
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    VAPID_PUBLIC_KEY: str = Field(None, env="VAPID_PUBLIC_KEY")
    VAPID_PRIVATE_KEY: str = Field(None, env="VAPID_PRIVATE_KEY")
    class Config:
        env_file = ".env"
settings = Settings()
```
**Commands**: 
```bash
rg -n "your-vapid|SECRET_KEY\s*=" || true
python -c "from app.core.config import settings; print('ok')"
```
**Test**: Static scan passes; no secret strings in `git ls-files -z | xargs -0 rg -n 'PRIVATE|SECRET|API_KEY'`  
**Estimate**: 8h (4h dev + 4h CI)  
**Sprint**: 1

### C-02 | Critical | Нет валидации входных эмбеддингов
**Files**: `backend/app/services/vector_store_service.py` (add_document)  
**Reproduction**: Send document with empty/abnormal embedding → index corrupted  
**Fix Summary**: Validate shape/dtype/NaN/inf and embedding length before add. Return 4xx and log.  
**Patch**:
```python
def _validate_embedding(emb):
    import numpy as np
    if emb is None: raise ValueError("embedding is None")
    arr = np.asarray(emb, dtype=float)
    if arr.ndim != 1: raise ValueError("invalid embedding dim")
    if np.isnan(arr).any() or np.isinf(arr).any(): raise ValueError("bad embedding")
    return arr.tolist()
# usage:
emb = _validate_embedding(data["embedding"])
collection.add(ids=[id], embeddings=[emb], documents=[doc], metadatas=[meta])
```
**Test**: Unit test sending bad embeddings → assert 400 and no change in collection count  
**Estimate**: 3h  
**Sprint**: 1

### C-03 | Critical | SQL/Query injection via metadata filters
**Files**: `backend/app/services/vector_store_service.py` (where filters usage)  
**Reproduction**: Craft metadata with `"$or": {"__sql":"..."}` and pass to where= → observe behavior  
**Fix Summary**: Sanitize metadata before saving and when building filter queries. Allow only predefined keys and types.  
**Patch**:
```python
ALLOWED_METADATA_KEYS = {"source","article","valid_from","valid_to","edition"}
def sanitize_metadata(m):
    return {k: v for k,v in m.items() if k in ALLOWED_METADATA_KEYS}
meta = sanitize_metadata(meta)
```
**Test**: Fuzz metadata inputs in tests; assert no exception and queries treated safely  
**Estimate**: 4h  
**Sprint**: 1

### C-04 | Critical | Небезопасное хеширование паролей
**Files**: `backend/app/core/security.py`, auth modules  
**Reproduction**: Check hashing algorithm configuration (bcrypt rounds)  
**Fix Summary**: Use passlib with bcrypt/argon2; ensure salted hashes, no custom weak salt  
**Patch**:
```python
from passlib.context import CryptContext
pwd_ctx = CryptContext(schemes=["argon2","bcrypt"], deprecated="auto")
def hash_password(password): return pwd_ctx.hash(password)
def verify_password(plain, hashed): return pwd_ctx.verify(plain, hashed)
```
**Test**: Migrate sample weak hashes and verify validation; auth unit tests  
**Estimate**: 4h  
**Sprint**: 1

### C-05 | Critical | Отсутствует HTTPS enforcement в продакшене
**Files**: deployment scripts / reverse proxy / env  
**Reproduction**: Spin up prod env, check https availability  
**Fix Summary**: Enforce HSTS, redirect HTTP→HTTPS, ensure certs (Let's Encrypt)  
**Test**: Verify HTTPS redirect and security headers  
**Estimate**: 6h (ops)  
**Sprint**: 1

## HIGH ISSUES (Sprint 1 → Sprint 2)

### H-01 | High | Неправильная схема чанкинга юридических текстов
**Files**: `backend/app/core/rag_system.py`, `simple_expert_rag.py`  
**Reproduction**: Load law with "статья X ч.1" and run split_document — verify breaks in middle of reference  
**Fix Summary**: Chunk by legal structure: split by article headers → parts → paragraphs → sentences  
**Patch**:
```python
def split_legal(text, max_tokens=500, overlap_tokens=75):
    articles = re.split(r'(Статья\s+\d+\.?)', text, flags=re.I)
    # reconstruct per-article blocks, then split by paragraphs & sentences
    ...
```
**Test**: Run check_chunk_id_collisions.py, golden retrieval; assert chunk boundaries at article/part markers  
**Estimate**: 2d dev + 0.5d testing  
**Sprint**: 2

### H-02 | High | BM25 + Vector объединение — заменить на RRF
**Files**: `backend/app/services/enhanced_rag_service.py`  
**Fix Summary**: Compute ranks for both lists, use RRF merging by ranks, then rerank top-K  
**Patch**:
```python
def rrf(emb_ids, bm25_ids, k=60):
    ranks_emb = {id: i+1 for i,id in enumerate(emb_ids)}
    ranks_bm25 = {id: i+1 for i,id in enumerate(bm25_ids)}
    all_ids = set(emb_ids)|set(bm25_ids)
    scores = {doc: 1/(k+ranks_emb.get(doc,1e6)) + 1/(k+ranks_bm25.get(doc,1e6)) for doc in all_ids}
    return sorted(scores.items(), key=lambda x:x[1], reverse=True)
```
**Test**: Golden_retrieval_test: compare hit@5 before/after; expect increase  
**Estimate**: 1d dev + 0.5d testing  
**Sprint**: 2

### H-03 | High | Chunk ID коллизии при перезаписи документов
**Files**: `core/rag_system.py`  
**Fix Summary**: Include doc fingerprint (md5 of first N chars or ingestion timestamp + edition)  
**Patch**:
```python
doc_sig = hashlib.md5((metadata.source + (metadata.edition or "") + text[:2000]).encode()).hexdigest()[:8]
parent_doc_id = f"{metadata.source}:{metadata.edition or 'v0'}:{doc_sig}"
chunk_id = f"{parent_doc_id}:chunk:{chunk_index}:{hashlib.md5(chunk_content.encode()).hexdigest()[:8]}"
```
**Test**: Run check_chunk_id_collisions.py on historic uploads  
**Estimate**: 4h  
**Sprint**: 1

### H-04 | High | Проблемы с фильтрацией по датам
**Files**: `vector_store_service.py` / search filters  
**Fix Summary**: Store ISO8601 dates consistently; use proper date comparisons  
**Patch**:
```python
where = {
  "$and":[
    {"valid_from":{"$lte": situation_date.isoformat()}},
    {"$or":[{"valid_to":{"$gte": situation_date.isoformat()}}, {"valid_to":{"$eq": None}}]}
  ]
}
```
**Test**: Unit tests with older/newer doc metadata; golden tests with historical dates  
**Estimate**: 6h  
**Sprint**: 2

### H-05 | High | Хардкод VAPID ключей
**Files**: `backend/app/api/notifications.py`  
**Fix Summary**: Move to env, add rotation docs. Use settings.VAPID_*  
**Test**: Ensure push notifications still sign  
**Estimate**: 2h  
**Sprint**: 1

### H-06 | High | Отсутствие валидации входных данных (XSS/SQL)
**Files**: controllers/api endpoints  
**Fix Summary**: Ensure all endpoints use Pydantic models, strict types; sanitize strings  
**Test**: Run security_test.py, bandit, fuzz fields  
**Estimate**: 2d  
**Sprint**: 1-2

### H-07 | High | LoRA target modules неполные
**Files**: `lora_training_service.py`  
**Fix Summary**: Include all attention projection matrices in target_modules  
**Estimate**: 2h  
**Sprint**: 2

### H-08 | High | Readiness probe не отражает реальное состояние
**Files**: `main.py`  
**Fix Summary**: /ready should check app.state.ready for all components  
**Estimate**: 2h  
**Sprint**: 2

### H-09 | High | Rate limiting отсутствует для ML endpoints
**Files**: middleware/rate_limit  
**Fix Summary**: Implement per-user rate limiting for inference endpoints  
**Estimate**: 1d  
**Sprint**: 2

### H-10 | High | Embeddings caching недостаточный
**Files**: `embeddings_service.py`  
**Fix Summary**: Increase cache size or use Redis with TTL  
**Estimate**: 4h  
**Sprint**: 2

## MEDIUM ISSUES (Sprint 2 → Sprint 3)

### M-01 | Medium | LoRA hyperparams: max_seq_length слишком маленький
**Files**: `lora_training_service.py`  
**Fix**: Set max_seq_length >= 2048, packing=True, correct target_modules  
**Test**: Train small job, check loss decrease and evaluation on golden set  
**Estimate**: 2d  
**Sprint**: 2

### M-02 | Medium | Rate limiting for ML endpoints missing
**Files**: middleware/rate_limit / main.py  
**Fix**: Implement token-bucket per user/api key + global GPU queue  
**Test**: k6 scripts, assert 429 returned for excessive requests  
**Estimate**: 1d  
**Sprint**: 2

### M-03 | Medium | Embeddings caching insufficient
**Fix**: Use Redis LRU cache for embeddings with TTL, or increase local cache  
**Estimate**: 1d  
**Sprint**: 3

### M-04 | Medium | Missing readiness gating for critical endpoints
**Files**: main.py  
**Fix**: Require Depends(require_components("saiga")) for inference endpoints  
**Estimate**: 4h  
**Sprint**: 2

## LOW ISSUES (Sprint 3)

### L-01 | Low | Docstrings & code comments
**Fix**: Add for public functions (assignable per module)  
**Estimate**: 1d  
**Sprint**: 3

### L-02 | Low | Remove print() from prod code
**Fix**: Replace with logger  
**Estimate**: 2h  
**Sprint**: 3

### L-03 | Low | Remove hardcoded paths
**Fix**: Use LOG_DIR from env  
**Estimate**: 2h  
**Sprint**: 3

### L-04 | Low | Add unit tests where missing
**Fix**: Increase test coverage  
**Estimate**: 2d  
**Sprint**: 3

## SPRINT PLAN

### Sprint 1 (3–5 дней) — Blocker & Critical
- C-01, C-02, C-03, C-04, C-05 (security + secrets + hashing + https)
- H-03 (chunk id collisions)
- H-05 (VAPID)
- **Deliverables**: Clean repo (no secrets), secure auth, HTTPS enforced, no chunk collisions
- **Owners**: backend lead / devops / security

### Sprint 2 (1–2 недели) — Core infra & RAG
- H-01 (legal chunking), H-02 (RRF), H-04 (date filters), M-04 (readiness), M-01 (LoRA hyperparams)
- **Deliverables**: High quality retrieval, correct chunking, readiness gating, LoRA configs for legal text

### Sprint 3 (1 неделя) — Performance & Ops
- M-02 (rate limiting), M-03 (embeddings caching), load tests/optimizations
- **Deliverables**: Prometheus Grafana dashboards, alerts

### Sprint 4 (ongoing) — Tests & docs
- Tests & docs, canary rollout, A/B, continuous security scans

## ACCEPTANCE CRITERIA (Release Gating)

To mark **READY_FOR_PRODUCTION**:
- [ ] All Critical and High issues closed
- [ ] CI passes: ruff, pytest, bandit, pip-audit  
- [ ] Golden retrieval hit@5 ≥ 0.95 on staging
- [ ] p95 latency targets met on staging load test
- [ ] Prometheus metrics and alerts configured
- [ ] Secrets removed from repo, secret manager configured
- [ ] Canary run and rollback tested