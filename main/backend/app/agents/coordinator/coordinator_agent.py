from dataclasses import dataclass

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

    def plan_for_ppt(self, user_id: str, requirement: str) -> CoordinationPlan:
        stages = ["planning", "generation", "review", "export"]
        decisions = [self.router.pick(user_id, stage) for stage in stages]  # type: ignore[arg-type]
        summary, needs_web_search = self._understand_requirement(requirement)
        return CoordinationPlan(
            task_type="ppt",
            stages=stages,
            model_decisions=decisions,
            requirement_summary=summary,
            needs_web_search=needs_web_search,
        )

    def _understand_requirement(self, requirement: str) -> tuple[str, bool]:
        text = (requirement or "").strip()
        summary = text[:200] if text else "未提供详细需求，按通用学术汇报生成。"
        search_keywords = ["搜索", "检索", "联网", "补充资料", "最新", "reference", "citation", "research"]
        needs_web_search = any(k.lower() in text.lower() for k in search_keywords)
        return summary, needs_web_search
