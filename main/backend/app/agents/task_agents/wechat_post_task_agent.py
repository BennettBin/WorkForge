from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Optional


@dataclass
class WechatPostTaskArtifacts:
    markdown: str
    review_passed: bool
    review_issues: list[str]
    plan_summary: str
    section_count: int


class WechatPostTaskAgent:
    def execute(
        self,
        requirement: str,
        parsed_text: str,
        style: str,
        language: str,
        skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]],
        llm_generate_fn: Optional[Callable[[str], str]] = None,
    ) -> WechatPostTaskArtifacts:
        plan = skill_execute_fn("wechat_post_planner", {"requirement": requirement, "parsed_text": parsed_text, "language": language})
        draft = skill_execute_fn(
            "wechat_post_writer",
            {
                "requirement": requirement,
                "parsed_text": parsed_text,
                "style": style,
                "language": language,
                "plan": plan,
                "llm_generate_fn": llm_generate_fn,
            },
        )
        review = skill_execute_fn("wechat_post_reviewer", {"draft": draft})
        return WechatPostTaskArtifacts(
            markdown=str(review.get("normalized_markdown", "")).strip() + "\n",
            review_passed=bool(review.get("passed", False)),
            review_issues=[str(x) for x in review.get("issues", [])] if isinstance(review.get("issues"), list) else [],
            plan_summary=str(plan.get("summary", "wechat_post plan generated")),
            section_count=int(draft.get("section_count", 0) or 0),
        )

