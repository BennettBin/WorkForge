from pathlib import Path

from app.services.skill_registry.registry import SkillRegistry
from app.services.skill_runtime.executor import SkillExecutor


def test_skill_registry_resolve_extended_task_domains():
    skill_root = Path(__file__).resolve().parents[1] / "app" / "skills"
    registry = SkillRegistry(skill_root)
    report_skills = [s.name for s in registry.resolve_for("report", "generation")]
    wechat_skills = [s.name for s in registry.resolve_for("wechat_post", "generation")]
    assert "report_outline" in report_skills
    assert "wechat_title_ideas" in wechat_skills


def test_skill_executor_supports_extended_skills():
    executor = SkillExecutor.create_default()
    out_report = executor.execute("report_outline", {"requirement": "Generate annual report"})
    out_wechat = executor.execute("wechat_title_ideas", {"requirement": "AI productivity"})
    out_data = executor.execute("data_clean_plan", {})
    out_code = executor.execute("code_readme_structure", {})
    out_paper = executor.execute("paper_outline", {})
    assert "sections" in out_report
    assert "titles" in out_wechat
    assert "steps" in out_data
    assert "sections" in out_code
    assert "sections" in out_paper
