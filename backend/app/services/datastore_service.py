from __future__ import annotations
from typing import Any
from google.cloud import datastore


def _client() -> datastore.Client:
    return datastore.Client()


def _entity_to_dict(e: datastore.Entity) -> dict[str, Any]:
    d = dict(e)
    d["_key"] = e.key.name or e.key.id
    return d


def list_order_confirmations(limit: int = 50) -> list[dict[str, Any]]:
    limit = max(1, min(int(limit), 200))

    client = _client()
    q = client.query(kind="order_confirmations")
    q.order = ["-received_at"]

    results: list[dict[str, Any]] = []
    for e in q.fetch(limit=limit):
        results.append(_entity_to_dict(e))
    return results


def get_order_confirmation(order_id: str) -> dict[str, Any] | None:
    client = _client()
    key = client.key("order_confirmations", str(order_id))
    e = client.get(key)
    if not e:
        return None
    return _entity_to_dict(e)


def delete_order_confirmation(order_id: str) -> bool:
    client = _client()
    key = client.key("order_confirmations", str(order_id))
    if not client.get(key):
        return False
    client.delete(key)
    return True
