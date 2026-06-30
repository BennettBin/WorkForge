from pathlib import Path

from app.services.skill_registry.registry import SkillRegistry
from app.services.skill_runtime.executor import SkillExecutor


def test_skill_registry_resolve_returns_all_public_skills():
    skill_root = Path(__file__).resolve().parents[1] / "app" / "skills"
    registry = SkillRegistry(skill_root)
    report_skills = [s.name for s in registry.resolve_for("report", "generation")]
    generic_skills = [s.name for s in registry.resolve_for("generic_task", "generation")]
    assert "report" in report_skills
    assert "wechat_post" in report_skills
    assert "ppt_generation" in generic_skills
    assert "report" in generic_skills


def test_skill_executor_supports_extended_skills():
    executor = SkillExecutor.create_default()
    out_find = executor.execute("find_skill", {"task_type": "report", "preferred_skills": ["report"]})
    out_report = executor.execute("report", {"requirement": "Generate annual report", "parsed_text": "context", "style": "formal", "language": "en-US"})
    out_wechat = executor.execute("wechat_post", {"requirement": "AI productivity", "parsed_text": "context", "style": "popular", "language": "zh-CN"})
    out_data = executor.execute("data_analysis", {"requirement": "analyze data", "parsed_text": "table context", "style": "academic", "language": "en-US"})
    out_code = executor.execute("code_doc", {"requirement": "write readme", "parsed_text": "repo context", "style": "concise", "language": "en-US"})
    out_paper = executor.execute("paper_assistant", {"requirement": "Draft abstract", "parsed_text": "sample context", "style": "academic", "language": "en-US"})
    assert "has_match" in out_find
    assert "matched_skills" in out_find
    assert isinstance(out_find["matched_skills"], list)
    assert "markdown" in out_report
    assert "markdown" in out_wechat
    assert "markdown" in out_data
    assert "markdown" in out_code
    assert "markdown" in out_paper
