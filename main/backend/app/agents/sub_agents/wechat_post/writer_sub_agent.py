from __future__ import annotations

from typing import Any, Callable

from .models import WechatPostDraft, WechatPostPlan


class WechatPostWriterSubAgent:
    def execute(
        self,
        requirement: str,
        parsed_text: str,
        style: str,
        language: str,
        plan: WechatPostPlan,
        skill_execute_fn: Callable[[str, dict[str, Any]], dict[str, Any]],
        llm_generate_fn: Callable[[str], str] | None,
    ) -> WechatPostDraft:
        style_rules = skill_execute_fn("wechat_style_polish", {"requirement": requirement, "content": parsed_text[:2000]})
        prompt = (
            f"Task Type: wechat_post\nLanguage: {language}\nStyle: {style}\n"
            f"Requirement:\n{requirement}\n\n"
            f"Title Candidates:\n{plan.title_candidates}\n\n"
            f"Style Rules:\n{style_rules.get('style_rules', [])}\n\n"
            f"Reference:\n{parsed_text[:6000]}\n\n"
            "Write markdown with title options, abstract, body sections, closing CTA."
        )
        if callable(llm_generate_fn):
            markdown = llm_generate_fn(prompt)
        else:
            markdown = "# Wechat Post\n\n## Title Options\n- Option 1\n\n## Abstract\nFallback.\n\n## Body\nTBD.\n"
        return WechatPostDraft(markdown=markdown, section_count=markdown.count("\n## "))
