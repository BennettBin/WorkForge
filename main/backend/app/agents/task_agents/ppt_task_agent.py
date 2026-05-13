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
    def _direct_fallback(self, parsed_text: str, requested_pages: int, requirement: str) -> PPTTaskArtifacts:
        pages = max(3, int(requested_pages or 8))
        outline = [{"page": 1, "kind": "cover", "title": "Presentation", "bullets": [requirement[:120] or "Auto generated"]}]
        for i in range(2, pages):
            outline.append({"page": i, "kind": "content", "title": f"Section {i-1}", "bullets": [parsed_text[:120] or requirement[:120] or "Content"]})
        outline.append({"page": pages, "kind": "summary", "title": "Summary", "bullets": ["Key takeaways"]})
        slides = [{"page": row["page"], "kind": row["kind"], "title": row["title"], "bullets": row["bullets"], "speaker_notes": ""} for row in outline]
        return PPTTaskArtifacts(outline=outline, slides=slides, review_passed=True, review_issues=[])

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
        try:
            finder = skill_execute_fn(
                "find_skill",
                {"task_type": "ppt", "requirement": requirement, "preferred_skills": ["ppt_generation"]},
            )
        except Exception:
            return self._direct_fallback(parsed_text, requested_pages, requirement)
        matched = finder.get("matched_skills", []) if isinstance(finder, dict) else []
        if not matched:
            return self._direct_fallback(parsed_text, requested_pages, requirement)
        ppt_generation_skill = matched[0]
        try:
            result = skill_execute_fn(
                ppt_generation_skill,
                {
                    "parsed_text": parsed_text,
                    "requested_pages": requested_pages,
                    "requirement": requirement,
                    "retrieve_context_fn": retrieve_context_fn,
                    "knowledge_search_fn": knowledge_search_fn,
                    "llm_generate_fn": llm_generate_fn,
                    "no_source_file": no_source_file,
                },
            )
        except Exception:
            return self._direct_fallback(parsed_text, requested_pages, requirement)
        outline_items = result.get("outline", [])
        return PPTTaskArtifacts(
            outline=outline_items if isinstance(outline_items, list) else [],
            slides=result.get("slides", []) if isinstance(result.get("slides"), list) else [],
            review_passed=bool(result.get("review_passed", False)),
            review_issues=[str(x) for x in result.get("review_issues", [])] if isinstance(result.get("review_issues"), list) else [],
        )
