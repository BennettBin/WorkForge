from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class PPTTaskArtifacts:
    outline: list[dict]
    slides: list[dict]
    review_passed: bool
    review_issues: list[str]


class PPTTaskAgent:
    def execute(
        self,
        parsed_text: str,
        requested_pages: int,
        requirement: str,
        retrieve_context_fn: Optional[Callable[[str, int], list[str]]] = None,
        knowledge_search_fn=None,
        llm_generate_fn=None,
        no_source_file: bool = False,
        skill_execute_fn: Optional[Callable[[str, dict[str, Any]], dict[str, Any]]] = None,
    ) -> PPTTaskArtifacts:
        if skill_execute_fn is None:
            raise ValueError("skill_execute_fn is required for PPT task execution.")
        outline_payload = skill_execute_fn(
            "ppt_outline_planner",
            {
                "parsed_text": parsed_text,
                "requested_pages": requested_pages,
                "requirement": requirement,
                "retrieve_context_fn": retrieve_context_fn,
                "llm_generate_fn": llm_generate_fn,
                "no_source_file": no_source_file,
            },
        )
        outline_items = outline_payload.get("outline", [])

        knowledge_by_slide: dict[int, list[dict]] = {}
        if callable(knowledge_search_fn):
            search_budget = max(3, min(10, requested_pages - 2)) if no_source_file else 3
            for item in outline_items:
                if not isinstance(item, dict) or item.get("kind") != "content":
                    continue
                if search_budget <= 0:
                    break
                query = f"{requirement} {item.get('title', '')}"
                refs = knowledge_search_fn(query, max_results=2)
                idx = int(item.get("index", 0) or 0)
                if refs and idx > 0:
                    knowledge_by_slide[idx] = refs
                search_budget -= 1

        content_payload = skill_execute_fn(
            "ppt_content_writer",
            {
                "outline": outline_items,
                "parsed_text": parsed_text,
                "retrieve_context_fn": retrieve_context_fn,
                "external_knowledge_by_slide": knowledge_by_slide,
                "llm_generate_fn": llm_generate_fn,
                "no_source_file": no_source_file,
            },
        )
        slides = content_payload.get("slides", [])
        review_payload = skill_execute_fn("ppt_quality_reviewer", {"slides": slides, "requested_pages": requested_pages})
        return PPTTaskArtifacts(
            outline=outline_items if isinstance(outline_items, list) else [],
            slides=review_payload.get("reviewed", []) if isinstance(review_payload.get("reviewed"), list) else [],
            review_passed=bool(review_payload.get("passed", False)),
            review_issues=[str(x) for x in review_payload.get("issues", [])] if isinstance(review_payload.get("issues"), list) else [],
        )

