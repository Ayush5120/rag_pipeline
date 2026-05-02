import hashlib
import json
from django.core.cache import cache

CACHE_TTL = 60 * 60  # 1 hour

def make_cache_key(question: str, doc_id=None) -> str:
    """
    Generate a deterministic cache key from question + doc_id.
    
    WHY MD5?
    Cache keys must be short strings (Redis key limit = 512 bytes).
    MD5 produces a 32-char hex string regardless of question length.
    MD5 is not cryptographically secure but we don't need that here —
    we just need a consistent short key. Fast and sufficient.
    """
    payload = json.dumps(
        {'question': question.lower().strip(), 'doc_id': doc_id},
        sort_keys=True
    )
    return f"rag:query:{hashlib.md5(payload.encode()).hexdigest()}"

def get_cached_answer(question: str, doc_id=None) -> dict | None:
    key = make_cache_key(question, doc_id)
    return cache.get(key)

def set_cached_answer(question: str, doc_id, answer: dict):
    key = make_cache_key(question, doc_id)
    cache.set(key, answer, timeout=CACHE_TTL)


