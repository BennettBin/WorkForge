from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.knowledge_search import KnowledgeSearchService


class SkillExecutionError(Exception):
    pass


@dataclass
class SkillExecutor:
    knowledge_search: KnowledgeSearchService

    @classmethod
    def create_default(cls) -> "SkillExecutor":
        return cls(knowledge_search=KnowledgeSearchService())

    def execute(self, skill_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        name = (skill_name or "").strip().lower()
        if name == "knowledge_search":
            query = str(payload.get("query", "")).strip()
            max_results_raw = payload.get("max_results", 2)
            try:
                max_results = int(max_results_raw)
            except Exception:
                max_results = 2
            items = self.knowledge_search.search_and_extract(query, max_results=max(1, min(5, max_results)))
            return {"items": items}
        raise SkillExecutionError(f"Unsupported skill execution: {skill_name}")
