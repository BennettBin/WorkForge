from pathlib import Path

from app.services.skill_registry.registry import SkillRegistry
from app.services.skill_runtime.executor import SkillExecutor


def test_skill_registry_resolve_extended_task_domains():
    skill_root = Path(__file__).resolve().parents[1] / "app" / "skills"
    registry = SkillRegistry(skill_root)
    report_skills = [s.name for s in registry.resolve_for("report", "generation")]
    wechat_skills = [s.name for s in registry.resolve_for("wechat_post", "generation")]
    assert "report_generation" in report_skills
    assert "wechat_post_generation" in wechat_skills


def test_skill_executor_supports_extended_skills():
    executor = SkillExecutor.create_default()
    out_find = executor.execute("find_skill", {"task_type": "report", "preferred_skills": ["report_generation"]})
    out_report = executor.execute("report_generation", {"requirement": "Generate annual report", "parsed_text": "context", "style": "formal", "language": "en-US"})
    out_wechat = executor.execute("wechat_post_generation", {"requirement": "AI productivity", "parsed_text": "context", "style": "popular", "language": "zh-CN"})
    out_data = executor.execute("data_analysis", {"requirement": "analyze data", "parsed_text": "table context", "style": "academic", "language": "en-US"})
    out_code = executor.execute("code_doc_generation", {"requirement": "write readme", "parsed_text": "repo context", "style": "concise", "language": "en-US"})
    out_paper = executor.execute("paper_assistant_generation", {"requirement": "Draft abstract", "parsed_text": "sample context", "style": "academic", "language": "en-US"})
    assert out_find["has_match"] is True
    assert "report_generation" in out_find["matched_skills"]
    assert "markdown" in out_report
    assert "markdown" in out_wechat
    assert "markdown" in out_data
    assert "markdown" in out_code
    assert "markdown" in out_paper
