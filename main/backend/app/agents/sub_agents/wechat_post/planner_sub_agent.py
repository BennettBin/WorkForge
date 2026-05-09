from __future__ import annotations

from typing import Any, Callable

from .models import WechatPostPlan


class WechatPostPlannerSubAgent:
    def execute(self, requirement: str, parsed_text: str, language: str, skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]]) -> WechatPostPlan:
        out = skill_execute_fn("wechat_title_ideas", {"requirement": requirement, "parsed_text": parsed_text[:4000], "language": language})
        titles = [str(x) for x in out.get("titles", [])] if isinstance(out.get("titles"), list) else []
        return WechatPostPlan(title_candidates=titles, summary=f"title_candidates={len(titles)}")
