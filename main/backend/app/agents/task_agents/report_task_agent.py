from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from app.agents.task_agents.base_text_task_agent import BaseTextTaskAgent, TextTaskConfig
from app.prompts import ReportTaskAgentSystemPrompt


@dataclass
class ReportTaskArtifacts:
    markdown: str
    review_passed: bool
    review_issues: list[str]
    plan_summary: str
    section_count: int


class ReportTaskAgent(BaseTextTaskAgent):
    def __init__(self) -> None:
        super().__init__(
            prompt=ReportTaskAgentSystemPrompt(),
            config=TextTaskConfig(
                task_type="report",
                skill_name="report",
                fallback_title="Report",
                fallback_plan_summary="report plan generated",
            ),
        )

    def execute(
        self,
        requirement: str,
        parsed_text: str,
        style: str,
        language: str,
        skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]],
        llm_generate_fn: Optional[Callable[[str], str]] = None,
    ) -> ReportTaskArtifacts:
        result = self.execute_text(
            requirement=requirement,
            parsed_text=parsed_text,
            style=style,
            language=language,
            skill_execute_fn=skill_execute_fn,
            llm_generate_fn=llm_generate_fn,
        )
        return ReportTaskArtifacts(**result)
