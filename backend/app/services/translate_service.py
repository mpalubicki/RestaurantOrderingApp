import os
import hashlib
from datetime import datetime, timezone
from typing import Iterable, List, Dict, Optional
from google.cloud import translate_v3 as translate
from app.extensions import mongo


def _project_id() -> str:
    pid = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GCLOUD_PROJECT")
    if not pid:
        raise RuntimeError("Missing GOOGLE_CLOUD_PROJECT environment variable.")
    return pid


def _location() -> str:
    return os.getenv("TRANSLATE_LOCATION", "global")


def _hash_key(text: str, target_language: str, source_language: Optional[str]) -> str:
    base = f"{source_language or ''}::{target_language}::{text}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _ensure_indexes() -> None:
    mongo.db.translations_cache.create_index("key", unique=True)
    mongo.db.translations_cache.create_index("created_at")


def translate_text(text: str, target_language: str, source_language: str | None = None) -> str:
    return translate_texts([text], target_language=target_language, source_language=source_language)[0]


def translate_texts(
    texts: Iterable[str],
    target_language: str,
    source_language: str | None = None,
) -> List[str]:
    _ensure_indexes()

    target_language = (target_language or "en").strip().lower()
    if target_language in ("en", "en-gb", "en-us"):
        return [t for t in texts]

    cleaned: List[str] = []
    for t in texts:
        t = (t or "").strip()
        cleaned.append(t)

    keys = [_hash_key(t, target_language, source_language) for t in cleaned]
    cached_docs = list(mongo.db.translations_cache.find({"key": {"$in": keys}}))
    cache_map: Dict[str, str] = {d["key"]: d.get("translated", "") for d in cached_docs}

    results: List[Optional[str]] = [None] * len(cleaned)
    misses: List[str] = []
    miss_indexes: List[int] = []
    miss_keys: List[str] = []

    for idx, (t, k) in enumerate(zip(cleaned, keys)):
        if not t:
            results[idx] = ""
            continue
        if k in cache_map and cache_map[k]:
            results[idx] = cache_map[k]
        else:
            misses.append(t)
            miss_indexes.append(idx)
            miss_keys.append(k)

    if misses:
        client = translate.TranslationServiceClient()
        parent = f"projects/{_project_id()}/locations/{_location()}"

        req = {
            "parent": parent,
            "contents": misses,
            "target_language_code": target_language,
        }
        if source_language:
            req["source_language_code"] = source_language

        resp = client.translate_text(request=req)
        translated_texts = [tr.translated_text for tr in resp.translations]

        now = datetime.now(timezone.utc)
        bulk = []
        for k, src, tr in zip(miss_keys, misses, translated_texts):
            bulk.append({
                "key": k,
                "source_language": source_language,
                "target_language": target_language,
                "source": src,
                "translated": tr,
                "created_at": now,
            })

        for doc in bulk:
            mongo.db.translations_cache.update_one(
                {"key": doc["key"]},
                {"$setOnInsert": doc},
                upsert=True
            )

        for idx, tr in zip(miss_indexes, translated_texts):
            results[idx] = tr

    return [r if r is not None else "" for r in results]
