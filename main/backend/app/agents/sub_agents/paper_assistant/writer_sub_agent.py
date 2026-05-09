from __future__ import annotations

from typing import Any, Callable

from .models import PaperDraft, PaperPlan


class PaperAssistantWriterSubAgent:
    def execute(
        self,
        requirement: str,
        parsed_text: str,
        style: str,
        language: str,
        plan: PaperPlan,
        skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]],
        llm_generate_fn: Callable[[str], str] | None,
    ) -> PaperDraft:
        revise_refine = skill_execute_fn("paper_revision_suggestions", {"requirement": requirement, "parsed_text": parsed_text[:3000], "language": language})
        prompt = (
            f"Task Type: paper_assistant\nLanguage: {language}\nStyle: {style}\n"
            f"Requirement:\n{requirement}\n\n"
            f"Section Plan:\n{plan.sections}\nReview Checks:\n{plan.review_checks}\n"
            f"Revision Hints:\n{revise_refine.get('checks', [])}\n\n"
            f"Reference:\n{parsed_text[:6000]}\n\n"
            "Write markdown for paper assistance: outline, abstract draft, and revision guidance."
        )
        if callable(llm_generate_fn):
            markdown = llm_generate_fn(prompt)
        else:
            markdown = "# Paper Assistant\n\n## Outline\nFallback.\n\n## Abstract Draft\nTBD.\n\n## Revision Suggestions\nTBD.\n"
        return PaperDraft(markdown=markdown, section_count=markdown.count("\n## "))
