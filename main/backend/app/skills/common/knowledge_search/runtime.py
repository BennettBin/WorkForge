from __future__ import annotations

from app.services.knowledge_search import KnowledgeSearchService


def run(payload: dict) -> dict:
    query = str(payload.get("query", "")).strip()
    try:
        max_results = int(payload.get("max_results", 2))
    except Exception:
        max_results = 2
    service = KnowledgeSearchService()
    items = service.search_and_extract(query, max_results=max(1, min(5, max_results)))
    return {"items": items}

