from __future__ import annotations

from typing import Any, Callable

from .models import ReportDraft, ReportPlan


class ReportWriterSubAgent:
    def execute(
        self,
        requirement: str,
        parsed_text: str,
        style: str,
        language: str,
        plan: ReportPlan,
        skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]],
        llm_generate_fn: Callable[[str], str] | None,
    ) -> ReportDraft:
        _ = skill_execute_fn("report_outline", {"requirement": requirement, "parsed_text": parsed_text[:3000], "language": language})
        prompt = (
            f"Task Type: report\nLanguage: {language}\nStyle: {style}\n"
            f"Requirement:\n{requirement}\n\n"
            f"Planned Sections:\n{plan.sections}\n\n"
            f"Reference:\n{parsed_text[:6000]}\n\n"
            "Write markdown report with headings, summary, findings, recommendations."
        )
        if callable(llm_generate_fn):
            markdown = llm_generate_fn(prompt)
        else:
            markdown = "# Report\n\n## Summary\nFallback draft.\n\n## Findings\nTBD.\n\n## Recommendations\nTBD.\n"
        return ReportDraft(markdown=markdown, section_count=markdown.count("\n## "))
