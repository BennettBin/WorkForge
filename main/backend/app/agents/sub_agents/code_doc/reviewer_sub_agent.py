from __future__ import annotations

from typing import Any, Callable

from .models import CodeDocDraft, CodeDocReview


class CodeDocReviewerSubAgent:
    def execute(
        self,
        draft: CodeDocDraft,
        skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]],
    ) -> CodeDocReview:
        issues: list[str] = []
        content = draft.markdown or ""
        readme_check = skill_execute_fn("code_readme_structure", {"requirement": "review_check", "parsed_text": content[:3000], "language": "auto"})
        api_check = skill_execute_fn("code_api_doc", {"requirement": "review_check", "parsed_text": content[:3000], "language": "auto"})
        if len(content.strip()) < 120:
            issues.append("Output too short.")
        lowered = content.lower()
        if "quick start" not in lowered:
            issues.append("Missing quick start section.")
        if "api" not in lowered:
            issues.append("Missing API section.")
        if isinstance(readme_check.get("sections"), list) and len(readme_check.get("sections", [])) == 0:
            issues.append("Skill check failed: empty README structure.")
        if isinstance(api_check.get("sections"), list) and len(api_check.get("sections", [])) == 0:
            issues.append("Skill check failed: empty API structure.")
        return CodeDocReview(passed=len(issues) == 0, issues=issues, normalized_markdown=content.strip() + "\n")
