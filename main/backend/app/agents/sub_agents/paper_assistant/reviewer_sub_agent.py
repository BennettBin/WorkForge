from __future__ import annotations

from typing import Any, Callable

from .models import PaperDraft, PaperReview


class PaperAssistantReviewerSubAgent:
    def execute(
        self,
        draft: PaperDraft,
        skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]],
    ) -> PaperReview:
        issues: list[str] = []
        content = draft.markdown or ""
        outline_check = skill_execute_fn("paper_outline", {"requirement": "review_check", "parsed_text": content[:3000], "language": "auto"})
        revise_check = skill_execute_fn("paper_revision_suggestions", {"requirement": "review_check", "parsed_text": content[:3000], "language": "auto"})
        if len(content.strip()) < 120:
            issues.append("Output too short.")
        lowered = content.lower()
        if "abstract" not in lowered:
            issues.append("Missing abstract section.")
        if "revision" not in lowered:
            issues.append("Missing revision guidance.")
        if isinstance(outline_check.get("sections"), list) and len(outline_check.get("sections", [])) == 0:
            issues.append("Skill check failed: empty paper outline.")
        if isinstance(revise_check.get("checks"), list) and len(revise_check.get("checks", [])) == 0:
            issues.append("Skill check failed: empty revision checklist.")
        return PaperReview(passed=len(issues) == 0, issues=issues, normalized_markdown=content.strip() + "\n")
