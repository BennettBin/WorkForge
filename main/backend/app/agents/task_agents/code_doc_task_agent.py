from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from app.agents.sub_agents.code_doc import (
    CodeDocPlannerSubAgent,
    CodeDocReviewerSubAgent,
    CodeDocWriterSubAgent,
)


@dataclass
class CodeDocTaskArtifacts:
    markdown: str
    review_passed: bool
    review_issues: list[str]
    plan_summary: str
    section_count: int


class CodeDocTaskAgent:
    def __init__(self):
        self.planner = CodeDocPlannerSubAgent()
        self.writer = CodeDocWriterSubAgent()
        self.reviewer = CodeDocReviewerSubAgent()

    def execute(
        self,
        requirement: str,
        parsed_text: str,
        style: str,
        language: str,
        skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]],
        llm_generate_fn: Optional[Callable[[str], str]] = None,
    ) -> CodeDocTaskArtifacts:
        plan = self.planner.execute(requirement, parsed_text, language, skill_execute_fn)
        draft = self.writer.execute(requirement, parsed_text, style, language, plan, skill_execute_fn, llm_generate_fn)
        review = self.reviewer.execute(draft, skill_execute_fn)
        return CodeDocTaskArtifacts(
            markdown=review.normalized_markdown,
            review_passed=review.passed,
            review_issues=review.issues,
            plan_summary=plan.summary,
            section_count=draft.section_count,
        )
