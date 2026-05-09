from __future__ import annotations

from typing import Any, Callable

from .models import WechatPostDraft, WechatPostReview


class WechatPostReviewerSubAgent:
    def execute(self, draft: WechatPostDraft, skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]]) -> WechatPostReview:
        issues: list[str] = []
        if len((draft.markdown or "").strip()) < 120:
            issues.append("Output too short.")
        if "##" not in draft.markdown:
            issues.append("Missing section structure.")
        style = skill_execute_fn("wechat_style_polish", {"content": draft.markdown})
        if not style.get("style_rules"):
            issues.append("Style rules missing.")
        return WechatPostReview(passed=len(issues) == 0, issues=issues, normalized_markdown=(draft.markdown or "").strip() + "\n")
