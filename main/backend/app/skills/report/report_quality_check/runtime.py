from __future__ import annotations


def run(payload: dict) -> dict:
    content = str(payload.get("content", ""))
    lowered = content.lower()
    section_aliases = {
        "summary": ["summary", "executive summary", "abstract", "摘要", "总结", "概述", "综述", "总览"],
        "findings": ["findings", "results", "analysis", "发现", "结果", "分析结论", "关键发现"],
        "recommendations": ["recommendations", "suggestions", "actions", "建议", "改进建议", "行动建议", "对策", "下一步"],
    }
    missing: list[str] = []
    for section, aliases in section_aliases.items():
        if not any(alias in lowered or alias in content for alias in aliases):
            missing.append(section)
    return {"missing_sections": missing, "passed": len(missing) == 0}

