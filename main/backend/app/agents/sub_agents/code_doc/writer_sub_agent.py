from __future__ import annotations

from typing import Any, Callable

from .models import CodeDocDraft, CodeDocPlan


class CodeDocWriterSubAgent:
    def execute(
        self,
        requirement: str,
        parsed_text: str,
        style: str,
        language: str,
        plan: CodeDocPlan,
        skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]],
        llm_generate_fn: Callable[[str], str] | None,
    ) -> CodeDocDraft:
        api_refine = skill_execute_fn("code_api_doc", {"requirement": requirement, "parsed_text": parsed_text[:3000], "language": language})
        prompt = (
            f"Task Type: code_doc\nLanguage: {language}\nStyle: {style}\n"
            f"Requirement:\n{requirement}\n\n"
            f"README Sections:\n{plan.readme_sections}\nAPI Sections:\n{plan.api_sections}\n"
            f"API Hints:\n{api_refine.get('sections', [])}\n\n"
            f"Reference:\n{parsed_text[:6000]}\n\n"
            "Write markdown README and technical documentation."
        )
        if callable(llm_generate_fn):
            markdown = llm_generate_fn(prompt)
        else:
            markdown = "# Code Documentation\n\n## Project Overview\nFallback.\n\n## Quick Start\nTBD.\n\n## API\nTBD.\n"
        return CodeDocDraft(markdown=markdown, section_count=markdown.count("\n## "))
