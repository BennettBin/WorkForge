from __future__ import annotations

from typing import Any, Callable

from .models import CodeDocPlan


class CodeDocPlannerSubAgent:
    def execute(
        self,
        requirement: str,
        parsed_text: str,
        language: str,
        skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]],
    ) -> CodeDocPlan:
        readme = skill_execute_fn("code_readme_structure", {"requirement": requirement, "parsed_text": parsed_text[:4000], "language": language})
        api = skill_execute_fn("code_api_doc", {"requirement": requirement, "parsed_text": parsed_text[:4000], "language": language})
        readme_sections = [str(x) for x in readme.get("sections", [])] if isinstance(readme.get("sections"), list) else []
        api_sections = [str(x) for x in api.get("sections", [])] if isinstance(api.get("sections"), list) else []
        return CodeDocPlan(summary="code doc plan generated", readme_sections=readme_sections, api_sections=api_sections)
