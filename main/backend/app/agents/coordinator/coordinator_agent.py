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

    def infer_task_type(self, requirement: str) -> str:
        text = (requirement or "").lower()
        if any(k in text for k in ["report", "报告", "analysis report", "汇报文档"]):
            return "report"
        if any(k in text for k in ["公众号", "wechat", "推文", "公号"]):
            return "wechat_post"
        if any(k in text for k in ["data", "csv", "统计", "数据分析", "回归"]):
            return "data_analysis"
        if any(k in text for k in ["readme", "api doc", "技术文档", "代码文档"]):
            return "code_doc"
        if any(k in text for k in ["paper", "论文", "abstract", "投稿"]):
            return "paper_assistant"
        return "ppt"

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

    def _understand_requirement(self, requirement: str) -> tuple[str, bool]:
        text = (requirement or "").strip()
        summary = text[:200] if text else "No detailed requirement provided."
        search_keywords = ["搜索", "检索", "联网", "补充资料", "最新", "reference", "citation", "research"]
        needs_web_search = any(k.lower() in text.lower() for k in search_keywords)
        return summary, needs_web_search
