from __future__ import annotations

from typing import Any, Callable

from .models import DataAnalysisDraft, DataAnalysisReview


class DataAnalysisReviewerSubAgent:
    def execute(
        self,
        draft: DataAnalysisDraft,
        skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]],
    ) -> DataAnalysisReview:
        issues: list[str] = []
        content = draft.markdown or ""
        review_clean = skill_execute_fn("data_clean_plan", {"requirement": "review_check", "parsed_text": content[:3000], "language": "auto"})
        review_charts = skill_execute_fn("data_chart_plan", {"requirement": "review_check", "parsed_text": content[:3000], "language": "auto"})
        if len(content.strip()) < 120:
            issues.append("Output too short.")
        lowered = content.lower()
        if "clean" not in lowered and "cleaning" not in lowered:
            issues.append("Missing cleaning section.")
        if "finding" not in lowered and "conclusion" not in lowered:
            issues.append("Missing findings section.")
        if isinstance(review_clean.get("steps"), list) and len(review_clean.get("steps", [])) == 0:
            issues.append("Skill check failed: empty cleaning plan.")
        if isinstance(review_charts.get("charts"), list) and len(review_charts.get("charts", [])) == 0:
            issues.append("Skill check failed: empty chart plan.")
        return DataAnalysisReview(passed=len(issues) == 0, issues=issues, normalized_markdown=content.strip() + "\n")
