from dataclasses import dataclass
from difflib import SequenceMatcher
import json
import logging
import re
from typing import Optional

from app.agents.tools import infer_task_type_by_keywords_tool, understand_requirement_tool
from app.prompts import CoordinatorAgentSystemPrompt
from app.services.llm_runtime import LLMTextGenerator
from app.services.model_router import ModelDecision, ModelRouter

logger = logging.getLogger(__name__)


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
        self.prompt = CoordinatorAgentSystemPrompt()

    _TASK_TYPES = {"ppt", "report", "wechat_post", "data_analysis", "code_doc", "paper_assistant", "generic_task", "template_generation"}
    _KEYWORD_RULES: list[tuple[str, list[str]]] = [
        ("template_generation", ["template generation", "build template", "extract template", "\u6a21\u677f\u751f\u6210", "\u751f\u6210\u6a21\u677f", "\u6a21\u677f\u63d0\u53d6", "\u521b\u5efa\u6a21\u677f"]),
        ("wechat_post", ["wechat", "wechat post", "\u516c\u4f17\u53f7", "\u63a8\u6587", "\u516c\u53f7", "\u5c0f\u7ea2\u4e66"]),
        ("data_analysis", ["data analysis", "csv", "excel", "xlsx", "\u6570\u636e\u5206\u6790", "\u7edf\u8ba1", "\u56de\u5f52", "\u8868\u683c\u5206\u6790"]),
        ("code_doc", ["readme", "api doc", "code doc", "\u6280\u672f\u6587\u6863", "\u4ee3\u7801\u6587\u6863", "\u63a5\u53e3\u6587\u6863"]),
        ("paper_assistant", ["paper", "abstract", "thesis", "\u8bba\u6587", "\u6458\u8981", "\u6295\u7a3f", "\u5b66\u672f"]),
        ("ppt", ["ppt", "powerpoint", "slides", "presentation", "\u6f14\u793a", "\u6c47\u62a5ppt", "\u5e7b\u706f\u7247", "\u6f14\u793a\u6587\u7a3f"]),
        ("report", ["report", "analysis report", "\u62a5\u544a", "\u5206\u6790\u62a5\u544a", "\u6c47\u62a5\u6587\u6863", "\u6587\u6863"]),
    ]

    def infer_task_type(self, requirement: str, user_id: Optional[str] = None) -> str:
        explicit_type = self._extract_explicit_task_type(requirement)
        if explicit_type is not None:
            return explicit_type
        keyword_type = self._infer_task_type_by_keywords(requirement)
        if keyword_type is not None:
            return keyword_type
        llm_type = self._infer_task_type_by_llm(requirement, user_id=user_id, keyword_hint=keyword_type)
        if llm_type is not None:
            return llm_type
        return "generic_task"

    def _infer_task_type_by_keywords(self, requirement: str) -> Optional[str]:
        text = self._normalize_match_text(requirement)
        if not text:
            return None
        tokens = [
            self._normalize_match_text(token)
            for token in re.findall(r"[A-Za-z0-9\u4e00-\u9fff]+", requirement or "")
        ]
        if ("template" in text or "\u6a21\u677f" in text) and any(k in text for k in ["ppt", "powerpoint", "\u5e7b\u706f\u7247", "\u6f14\u793a\u6587\u7a3f"]):
            return "template_generation"
        best_type: Optional[str] = None
        best_score = 0.0
        for task_type, keywords in self._KEYWORD_RULES:
            for keyword in keywords:
                key = self._normalize_match_text(keyword)
                if not key:
                    continue
                if key in text:
                    return task_type
                comparable_tokens = [
                    token
                    for token in tokens
                    if len(token) >= 5 and len(key) >= 5 and abs(len(token) - len(key)) <= 3
                ]
                score = max(
                    [SequenceMatcher(None, text, key).ratio()]
                    + [
                        SequenceMatcher(None, token, key).ratio()
                        for token in comparable_tokens
                    ]
                )
                if score > best_score:
                    best_type = task_type
                    best_score = score
        if best_type is not None and best_score >= 0.72:
            return best_type
        return None

    @staticmethod
    def _normalize_match_text(text: str) -> str:
        return re.sub(r"[\s_\-]+", "", (text or "").strip().lower())

    def _extract_explicit_task_type(self, requirement: str) -> Optional[str]:
        for line in (requirement or "").splitlines():
            match = re.match(r"\s*TaskType\s*=\s*([A-Za-z0-9_\-]+)\s*$", line, flags=re.IGNORECASE)
            if not match:
                continue
            task_type = match.group(1).strip().lower().replace("-", "_")
            if task_type in self._TASK_TYPES:
                return task_type
        return None

    def _infer_task_type_by_llm(self, requirement: str, user_id: Optional[str], keyword_hint: Optional[str]) -> Optional[str]:
        if not (requirement or "").strip() or not user_id:
            return None
        user_prompt = (
            "Classify the following user request into exactly one task type.\n"
            "Allowed task_type: ppt, report, wechat_post, data_analysis, code_doc, paper_assistant, generic_task, template_generation.\n"
            "Rules:\n"
            "1) Use the keyword/fuzzy candidate as the first-pass result, then verify it against the full user requirement.\n"
            "2) If the candidate conflicts with the requirement, choose the requirement.\n"
            "3) If intent is unclear or not covered, return generic_task.\n"
            "4) Return strict JSON only: {\"task_type\":\"...\"}\n"
            f"Keyword/fuzzy candidate: {keyword_hint if keyword_hint else 'NO_KEYWORD_MATCH'}\n"
            f"User requirement:\n{requirement.strip()[:3000]}"
        )
        try:
            decision = self.router.pick(user_id, "planning")
            if not decision.provider_type or not decision.model_name:
                return None
            provider_cfg = self.router.repos.providers.get_default_for_user(user_id)
            api_key = (provider_cfg.api_key_encrypted or "").strip() if provider_cfg and provider_cfg.api_key_encrypted else None
            text = LLMTextGenerator().generate(
                provider_type=decision.provider_type,
                base_url=decision.base_url,
                model_name=decision.model_name,
                prompt=user_prompt,
                api_key=api_key,
                timeout_seconds=45,
                use_agent=False,
            )
            payload = self._parse_json_object(text)
        except Exception as exc:
            logger.info("Task type LLM fallback failed; using deterministic fallback. reason=%s", exc)
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
        user_prompt = (
            "You are filling a template generation settings form.\n"
            "Read the user requirement and return strict JSON only. Do not include markdown.\n"
            "Required JSON keys:\n"
            "{"
            "\"templateType\":\"ppt|wechat_post|report\","
            "\"templateName\":\"concise_snake_case_name\","
            "\"language\":\"zh-CN|en-US\","
            "\"templateIntent\":\"short concrete intent\","
            "\"targetAudience\":\"short concrete audience\""
            "}\n"
            "Constraints:\n"
            "1) templateType must be one of: ppt, wechat_post, report.\n"
            "2) language must be one of: zh-CN, en-US.\n"
            "3) If templateType is not named, infer it from uploaded file metadata or file format hints when available.\n"
            "4) If templateName is missing, generate a concise snake_case name from the requirement or file name.\n"
            "5) Fill every key with a non-empty value inferred from the requirement.\n"
            "6) Do not use generic values such as 'general audience' when the requirement contains an audience.\n"
            "7) templateIntent and targetAudience should preserve the user's concrete meaning and language.\n"
            "Example: requirement='科研开题答辩PPT模板，面向研究生导师' -> "
            "{\"templateType\":\"ppt\",\"templateName\":\"research_proposal_defense\","
            "\"language\":\"zh-CN\",\"templateIntent\":\"科研开题答辩\","
            "\"targetAudience\":\"研究生导师\"}\n"
            f"User requirement:\n{requirement.strip()[:3000]}"
        )
        try:
            text = LLMTextGenerator().generate(
                provider_type=decision.provider_type,
                base_url=decision.base_url,
                model_name=decision.model_name,
                prompt=user_prompt,
                api_key=api_key,
                timeout_seconds=45,
                use_agent=False,
            )
            payload = self._parse_json_object(text)
        except Exception:
            logger.exception("Template settings inference failed")
            return defaults
        template_type = str(payload.get("templateType", "")).strip()
        language = str(payload.get("language", "")).strip()
        if template_type not in {"ppt", "wechat_post", "report"}:
            template_type = ""
        if language not in {"zh-CN", "en-US"}:
            language = ""
        settings = {
            "templateType": template_type,
            "templateName": str(payload.get("templateName", "")).strip(),
            "language": language,
            "templateIntent": str(payload.get("templateIntent", "")).strip(),
            "targetAudience": str(payload.get("targetAudience", "")).strip(),
        }
        return self._refine_template_settings(settings, requirement)

    @staticmethod
    def _parse_json_object(text: str) -> dict:
        raw = (text or "").strip()
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
        left = raw.find("{")
        right = raw.rfind("}")
        if left >= 0 and right > left:
            parsed = json.loads(raw[left : right + 1])
            if isinstance(parsed, dict):
                return parsed
        raise ValueError("LLM output is not a JSON object.")

    @classmethod
    def _refine_template_settings(cls, settings: dict[str, str], requirement: str) -> dict[str, str]:
        text = (requirement or "").strip()
        if not text:
            return settings
        intent = cls._extract_template_intent(text)
        audience = cls._extract_target_audience(text)

        if intent and cls._is_blank_or_generic(settings.get("templateIntent", "")):
            settings["templateIntent"] = intent
        if audience and cls._is_blank_or_generic(settings.get("targetAudience", "")):
            settings["targetAudience"] = audience
        if not settings.get("templateName", "").strip() or cls._is_blank_or_generic(settings.get("templateName", "")):
            base = intent or text[:24]
            settings["templateName"] = cls._to_snake_case_name(base)
        if not settings.get("templateType", "").strip():
            lowered = text.lower()
            settings["templateType"] = "ppt" if ("ppt" in lowered or "powerpoint" in lowered or "幻灯片" in text or "演示" in text) else "report"
        if not settings.get("language", "").strip():
            settings["language"] = "zh-CN" if re.search(r"[\u4e00-\u9fff]", text) else "en-US"
        return settings

    @staticmethod
    def _is_blank_or_generic(value: str) -> bool:
        normalized = (value or "").strip().lower().replace("_", " ")
        return normalized in {
            "",
            "unknown",
            "unknown template",
            "ppt",
            "general",
            "general audience",
            "general presentation",
            "ordinary audience",
            "common audience",
            "user",
            "users",
            "ppt template",
            "presentation template",
            "一般",
            "一般演示",
            "一般观众",
            "普通观众",
            "用户",
            "通用",
            "ppt模板",
            "演示文稿",
            "未指定",
            "未说明",
        }

    @staticmethod
    def _extract_template_intent(text: str) -> str:
        patterns = [
            r"用于([^，。,.；;]{2,40}?)(?:的|，|。|,|；|;)",
            r"用来([^，。,.；;]{2,40}?)(?:的|，|。|,|；|;)",
            r"生成一个?([^，。,.；;]{2,40}?)(?:模板|PPT|ppt)",
            r"create (?:a |an )?([^,.]{2,60}?)(?: template| presentation| slides)",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value:
                    return value
        return ""

    @staticmethod
    def _extract_target_audience(text: str) -> str:
        patterns = [
            r"面向([^，。,.；;]{2,40})",
            r"给([^，。,.；;]{2,40})",
            r"受众(?:是|为|:|：)?([^，。,.；;]{2,40})",
            r"target audience(?: is|:)? ([^,.]{2,60})",
            r"for ([^,.]{2,60})",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                value = match.group(1).strip()
                if value:
                    return value
        return ""

    @staticmethod
    def _to_snake_case_name(value: str) -> str:
        mapping = [
            ("科研", "research"),
            ("开题", "proposal"),
            ("答辩", "defense"),
            ("模板", "template"),
            ("演示", "presentation"),
            ("汇报", "report"),
            ("技术", "tech"),
            ("商业", "business"),
        ]
        name = value
        for src, dst in mapping:
            name = name.replace(src, f" {dst} ")
        name = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()
        if not name:
            name = "generated_template"
        if not name[0].isalpha():
            name = f"template_{name}"
        return name[:41]

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
