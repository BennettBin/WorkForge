from __future__ import annotations

from typing import Any, Callable

from .models import DataAnalysisDraft, DataAnalysisPlan


class DataAnalysisWriterSubAgent:
    def execute(
        self,
        requirement: str,
        parsed_text: str,
        style: str,
        language: str,
        plan: DataAnalysisPlan,
        skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]],
        llm_generate_fn: Callable[[str], str] | None,
    ) -> DataAnalysisDraft:
        chart_refine = skill_execute_fn("data_chart_plan", {"requirement": requirement, "parsed_text": parsed_text[:3000], "language": language})
        prompt = (
            f"Task Type: data_analysis\nLanguage: {language}\nStyle: {style}\n"
            f"Requirement:\n{requirement}\n\n"
            f"Clean Steps:\n{plan.clean_steps}\nChart Plan:\n{plan.chart_plan}\n"
            f"Chart Hints:\n{chart_refine.get('charts', [])}\n\n"
            f"Reference:\n{parsed_text[:6000]}\n\n"
            "Write markdown including assumptions, cleaning, analysis findings, and chart recommendations."
        )
        if callable(llm_generate_fn):
            markdown = llm_generate_fn(prompt)
        else:
            markdown = "# Data Analysis\n\n## Assumptions\nFallback.\n\n## Cleaning\nTBD.\n\n## Findings\nTBD.\n"
        return DataAnalysisDraft(markdown=markdown, section_count=markdown.count("\n## "))
