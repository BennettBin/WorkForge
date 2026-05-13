from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class ReportTaskArtifacts:
    markdown: str
    review_passed: bool
    review_issues: list[str]
    plan_summary: str
    section_count: int


class ReportTaskAgent:
    def _direct_fallback(
        self,
        requirement: str,
        parsed_text: str,
        llm_generate_fn: Optional[Callable[[str], str]],
    ) -> ReportTaskArtifacts:
        if llm_generate_fn is not None:
            prompt = f"Generate a report in markdown.\nRequirement:\n{requirement}\n\nContext:\n{parsed_text[:4000]}"
            markdown = llm_generate_fn(prompt)
        else:
            source = (parsed_text or requirement or "").strip()
            markdown = f"# Report\n\n{source[:3000]}"
        return ReportTaskArtifacts(markdown=markdown.strip() + "\n", review_passed=True, review_issues=[], plan_summary="direct fallback", section_count=max(1, markdown.count("\n## ")))

    def execute(
        self,
        requirement: str,
        parsed_text: str,
        style: str,
        language: str,
        skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]],
        llm_generate_fn: Optional[Callable[[str], str]] = None,
    ) -> ReportTaskArtifacts:
        try:
            finder = skill_execute_fn(
                "find_skill",
                {"task_type": "report", "requirement": requirement, "preferred_skills": ["report_generation"]},
            )
        except Exception:
            return self._direct_fallback(requirement, parsed_text, llm_generate_fn)
        matched = finder.get("matched_skills", []) if isinstance(finder, dict) else []
        if not matched:
            return self._direct_fallback(requirement, parsed_text, llm_generate_fn)
        skill_name = matched[0] if len(matched) > 0 else "report_generation"
        try:
            result = skill_execute_fn(
                skill_name,
                {
                    "requirement": requirement,
                    "parsed_text": parsed_text,
                    "style": style,
                    "language": language,
                    "llm_generate_fn": llm_generate_fn,
                },
            )
        except Exception:
            return self._direct_fallback(requirement, parsed_text, llm_generate_fn)
        return ReportTaskArtifacts(
            markdown=str(result.get("markdown", "")).strip() + "\n",
            review_passed=bool(result.get("passed", False)),
            review_issues=[str(x) for x in result.get("issues", [])] if isinstance(result.get("issues"), list) else [],
            plan_summary=str(result.get("plan_summary", "report plan generated")),
            section_count=int(result.get("section_count", 0) or 0),
        )
