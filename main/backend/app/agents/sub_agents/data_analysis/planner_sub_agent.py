from __future__ import annotations

from typing import Any, Callable

from .models import DataAnalysisPlan


class DataAnalysisPlannerSubAgent:
    def execute(
        self,
        requirement: str,
        parsed_text: str,
        language: str,
        skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]],
    ) -> DataAnalysisPlan:
        clean = skill_execute_fn("data_clean_plan", {"requirement": requirement, "parsed_text": parsed_text[:4000], "language": language})
        chart = skill_execute_fn("data_chart_plan", {"requirement": requirement, "parsed_text": parsed_text[:4000], "language": language})
        clean_steps = [str(x) for x in clean.get("steps", [])] if isinstance(clean.get("steps"), list) else []
        charts = [str(x) for x in chart.get("charts", [])] if isinstance(chart.get("charts"), list) else []
        return DataAnalysisPlan(summary="data analysis plan generated", clean_steps=clean_steps, chart_plan=charts)
