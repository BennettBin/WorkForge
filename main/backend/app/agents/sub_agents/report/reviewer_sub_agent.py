from __future__ import annotations

from typing import Any, Callable

from .models import ReportDraft, ReportReview


class ReportReviewerSubAgent:
    def execute(self, draft: ReportDraft, skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]]) -> ReportReview:
        issues: list[str] = []
        content = draft.markdown or ""
        if len(content.strip()) < 120:
            issues.append("Output too short.")
        check = skill_execute_fn("report_quality_check", {"content": content})
        missing_sections = [str(s) for s in check.get("missing_sections", [])] if isinstance(check.get("missing_sections", []), list) else []

        lowered = content.lower()
        alias_map = {
            "summary": [
                "summary", "executive summary", "abstract",
                "\u6458\u8981", "\u603b\u7ed3", "\u6982\u8ff0", "\u7efc\u8ff0", "\u603b\u89c8",
            ],
            "findings": [
                "findings", "results", "analysis",
                "\u53d1\u73b0", "\u7ed3\u679c", "\u5206\u6790\u7ed3\u8bba", "\u5173\u952e\u53d1\u73b0",
            ],
            "recommendations": [
                "recommendations", "suggestions", "actions",
                "\u5efa\u8bae", "\u6539\u8fdb\u5efa\u8bae", "\u884c\u52a8\u5efa\u8bae", "\u5bf9\u7b56", "\u4e0b\u4e00\u6b65",
            ],
        }

        for section in missing_sections:
            aliases = alias_map.get(section, [])
            if aliases and any(a in lowered or a in content for a in aliases):
                continue
            issues.append(f"Missing report section: {section}")

        return ReportReview(passed=len(issues) == 0, issues=issues, normalized_markdown=content.strip() + "\n")
