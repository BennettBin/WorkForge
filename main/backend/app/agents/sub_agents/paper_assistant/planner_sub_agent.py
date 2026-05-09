from __future__ import annotations

from typing import Any, Callable

from .models import PaperPlan


class PaperAssistantPlannerSubAgent:
    def execute(
        self,
        requirement: str,
        parsed_text: str,
        language: str,
        skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]],
    ) -> PaperPlan:
        outline = skill_execute_fn("paper_outline", {"requirement": requirement, "parsed_text": parsed_text[:4000], "language": language})
        review = skill_execute_fn("paper_revision_suggestions", {"requirement": requirement, "parsed_text": parsed_text[:4000], "language": language})
        sections = [str(x) for x in outline.get("sections", [])] if isinstance(outline.get("sections"), list) else []
        checks = [str(x) for x in review.get("checks", [])] if isinstance(review.get("checks"), list) else []
        return PaperPlan(summary="paper plan generated", sections=sections, review_checks=checks)
