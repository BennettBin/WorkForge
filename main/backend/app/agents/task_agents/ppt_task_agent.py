from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional

from app.agents.runtime import LangGraphAgentRunner, LangGraphModelConfig
from app.agents.tools import execute_ppt_skill_tool
from app.agents.tools.ppt_tools import execute_ppt_skill_impl
from app.prompts import PPTTaskAgentSystemPrompt


@dataclass
class PPTTaskArtifacts:
    outline: list[dict]
    slides: list[dict]
    review_passed: bool
    review_issues: list[str]


class PPTTaskAgent:
    def __init__(self) -> None:
        self.prompt = PPTTaskAgentSystemPrompt()
        self.runner = LangGraphAgentRunner(
            model=LangGraphModelConfig(provider_type="openai_compatible", model_name="gpt-4o-mini"),
            system_prompt=self.prompt.render(),
            tools=[execute_ppt_skill_tool],
        )

    def execute(
        self,
        parsed_text: str,
        requested_pages: int,
        requirement: str,
        retrieve_context_fn: Optional[Callable[[str, int], list[str]]] = None,
        knowledge_search_fn=None,
        llm_generate_fn=None,
        event_emit_fn: Optional[Callable[[str, str], None]] = None,
        no_source_file: bool = False,
        template_constraints: Optional[dict[str, Any]] = None,
        skill_execute_fn: Optional[Callable[[str, dict[str, Any]], dict[str, Any]]] = None,
    ) -> PPTTaskArtifacts:
        if skill_execute_fn is None:
            raise ValueError("skill_execute_fn is required for PPT task execution.")
        self.runner.bootstrap_agent(safe=True)
        result = execute_ppt_skill_impl(
            skill_execute_fn=skill_execute_fn,
            parsed_text=parsed_text,
            requested_pages=requested_pages,
            requirement=requirement,
            retrieve_context_fn=retrieve_context_fn,
            knowledge_search_fn=knowledge_search_fn,
            llm_generate_fn=llm_generate_fn,
            event_emit_fn=event_emit_fn,
            no_source_file=no_source_file,
            template_constraints=template_constraints,
        )
        slides = result.get("slides", []) if isinstance(result.get("slides"), list) else []
        outline_items = result.get("outline", [])
        return PPTTaskArtifacts(
            outline=outline_items if isinstance(outline_items, list) else [],
            slides=slides,
            review_passed=bool(result.get("review_passed", False)),
            review_issues=[str(x) for x in result.get("review_issues", [])] if isinstance(result.get("review_issues"), list) else [],
        )
