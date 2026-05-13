from dataclasses import dataclass
import json
from typing import Optional

from app.services.llm_runtime import LLMTextGenerator
from app.services.model_router import ModelDecision, ModelRouter


@dataclass
class CoordinationPlan:
    task_type: str
    stages: list[str]
    model_decisions: list[ModelDecision]
    requirement_summary: str
    needs_web_search: bool


class CoordinatorAgent:
    def __init__(self, router: ModelRouter):
        self.router = router

    _TASK_TYPES = {"ppt", "report", "wechat_post", "data_analysis", "code_doc", "paper_assistant", "generic_task", "template_generation"}
    _KEYWORD_RULES: list[tuple[str, list[str]]] = [
        ("template_generation", ["模板生成", "生成模板", "template generation", "build template", "模板构建", "模板提取"]),
        ("report", ["report", "报告", "analysis report", "汇报文档"]),
        ("wechat_post", ["公众号", "wechat", "推文", "公号"]),
        ("data_analysis", ["data", "csv", "统计", "数据分析", "回归"]),
        ("code_doc", ["readme", "api doc", "技术文档", "代码文档"]),
        ("paper_assistant", ["paper", "论文", "abstract", "投稿"]),
        ("ppt", ["ppt", "slides", "presentation", "演示", "汇报ppt", "幻灯片"]),
    ]

    def infer_task_type(self, requirement: str, user_id: Optional[str] = None) -> str:
        keyword_type = self._infer_task_type_by_keywords(requirement)
        llm_type = self._infer_task_type_by_llm(requirement, user_id=user_id, keyword_hint=keyword_type)
        if llm_type is not None:
            return llm_type
        if keyword_type is not None:
            return keyword_type
        return "generic_task"

    def _infer_task_type_by_keywords(self, requirement: str) -> Optional[str]:
        text = (requirement or "").lower()
        for task_type, keywords in self._KEYWORD_RULES:
            if any(k in text for k in keywords):
                return task_type
        return None

    def _infer_task_type_by_llm(self, requirement: str, user_id: Optional[str], keyword_hint: Optional[str]) -> Optional[str]:
        if not (requirement or "").strip() or not user_id:
            return None
        decision = self.router.pick(user_id, "planning")
        if not decision.provider_type or not decision.model_name:
            return None
        provider_cfg = self.router.repos.providers.get_default_for_user(user_id)
        api_key = (provider_cfg.api_key_encrypted or "").strip() if provider_cfg and provider_cfg.api_key_encrypted else None
        prompt = (
            "Classify the following user request into exactly one task type.\n"
            "Allowed task_type: ppt, report, wechat_post, data_analysis, code_doc, paper_assistant, generic_task, template_generation.\n"
            "Rules:\n"
            "1) If intent is unclear or not covered, return generic_task.\n"
            "2) Return strict JSON only: {\"task_type\":\"...\"}\n"
            f"Keyword-matching result: {keyword_hint if keyword_hint else 'NO_KEYWORD_MATCH'}\n"
            f"User requirement:\n{requirement.strip()[:3000]}"
        )
        try:
            content = LLMTextGenerator().generate(
                provider_type=decision.provider_type,
                base_url=decision.base_url,
                model_name=decision.model_name,
                prompt=prompt,
                api_key=api_key,
                timeout_seconds=45,
            )
        except Exception:
            return None
        try:
            payload = json.loads((content or "").strip())
        except Exception:
            return None
        task_type = str(payload.get("task_type", "")).strip()
        if task_type in self._TASK_TYPES:
            return task_type
        return None

    def infer_template_settings(self, requirement: str, user_id: Optional[str] = None) -> dict[str, str]:
        defaults: dict[str, str] = {
            "templateType": "",
            "templateName": "",
            "language": "",
            "templateIntent": "",
            "targetAudience": "",
        }
        if not (requirement or "").strip() or not user_id:
            return defaults
        decision = self.router.pick(user_id, "planning")
        if not decision.provider_type or not decision.model_name:
            return defaults
        provider_cfg = self.router.repos.providers.get_default_for_user(user_id)
        api_key = (provider_cfg.api_key_encrypted or "").strip() if provider_cfg and provider_cfg.api_key_encrypted else None
        prompt = (
            "Extract template settings from the user requirement.\n"
            "Return strict JSON only with keys:\n"
            "templateType, templateName, language, templateIntent, targetAudience.\n"
            "Constraints:\n"
            "1) templateType must be one of: ppt, wechat_post, report.\n"
            "2) language must be one of: zh-CN, en-US.\n"
            "3) If not found, return empty string for that field.\n"
            "4) Do not invent values.\n"
            f"User requirement:\n{requirement.strip()[:3000]}"
        )
        try:
            content = LLMTextGenerator().generate(
                provider_type=decision.provider_type,
                base_url=decision.base_url,
                model_name=decision.model_name,
                prompt=prompt,
                api_key=api_key,
                timeout_seconds=45,
            )
            payload = json.loads((content or "").strip())
        except Exception:
            return defaults
        template_type = str(payload.get("templateType", "")).strip()
        language = str(payload.get("language", "")).strip()
        if template_type not in {"ppt", "wechat_post", "report"}:
            template_type = ""
        if language not in {"zh-CN", "en-US"}:
            language = ""
        return {
            "templateType": template_type,
            "templateName": str(payload.get("templateName", "")).strip(),
            "language": language,
            "templateIntent": str(payload.get("templateIntent", "")).strip(),
            "targetAudience": str(payload.get("targetAudience", "")).strip(),
        }

    def plan_for_ppt(self, user_id: str, requirement: str) -> CoordinationPlan:
        return self.plan_for_task(user_id, "ppt", requirement)

    def plan_for_task(self, user_id: str, task_type: str, requirement: str) -> CoordinationPlan:
        stages = ["planning", "generation", "review", "export"]
        decisions = [self.router.pick(user_id, stage) for stage in stages]  # type: ignore[arg-type]
        summary, needs_web_search = self._understand_requirement(requirement)
        return CoordinationPlan(
            task_type=task_type,
            stages=stages,
            model_decisions=decisions,
            requirement_summary=summary,
            needs_web_search=needs_web_search,
        )

    def infer_ppt_skill(self, requirement: str) -> str:
        text = (requirement or "").lower()
        template_keywords = [
            "提取模板",
            "模板提取",
            "保存模板",
            "生成ppt模板",
            "extract template",
            "save template",
            "generate ppt template",
        ]
        if any(k in text for k in template_keywords):
            return "ppt_template_generation"
        return "ppt_generation"

    def _understand_requirement(self, requirement: str) -> tuple[str, bool]:
        text = (requirement or "").strip()
        summary = text[:200] if text else "No detailed requirement provided."
        search_keywords = ["搜索", "检索", "联网", "补充资料", "最新", "reference", "citation", "research"]
        needs_web_search = any(k.lower() in text.lower() for k in search_keywords)
        return summary, needs_web_search
