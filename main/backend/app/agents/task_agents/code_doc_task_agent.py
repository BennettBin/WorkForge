from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class CodeDocTaskArtifacts:
    markdown: str
    review_passed: bool
    review_issues: list[str]
    plan_summary: str
    section_count: int


class CodeDocTaskAgent:
    def execute(
        self,
        requirement: str,
        parsed_text: str,
        style: str,
        language: str,
        skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]],
        llm_generate_fn: Optional[Callable[[str], str]] = None,
    ) -> CodeDocTaskArtifacts:
        plan = skill_execute_fn("code_doc_planner", {"requirement": requirement, "parsed_text": parsed_text, "language": language})
        draft = skill_execute_fn(
            "code_doc_writer",
            {
                "requirement": requirement,
                "parsed_text": parsed_text,
                "style": style,
                "language": language,
                "plan": plan,
                "llm_generate_fn": llm_generate_fn,
            },
        )
        review = skill_execute_fn("code_doc_reviewer", {"draft": draft})
        return CodeDocTaskArtifacts(
            markdown=str(review.get("normalized_markdown", "")).strip() + "\n",
            review_passed=bool(review.get("passed", False)),
            review_issues=[str(x) for x in review.get("issues", [])] if isinstance(review.get("issues"), list) else [],
            plan_summary=str(plan.get("summary", "code doc plan generated")),
            section_count=int(draft.get("section_count", 0) or 0),
        )

