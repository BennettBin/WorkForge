from __future__ import annotations

from typing import Any, Callable

from .models import ReportPlan


class ReportPlannerSubAgent:
    def execute(self, requirement: str, parsed_text: str, language: str, skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]]) -> ReportPlan:
        out = skill_execute_fn("report_outline", {"requirement": requirement, "parsed_text": parsed_text[:4000], "language": language})
        sections = [str(x) for x in out.get("sections", [])] if isinstance(out.get("sections"), list) else []
        return ReportPlan(summary=out.get("hint", "report plan generated"), sections=sections)
