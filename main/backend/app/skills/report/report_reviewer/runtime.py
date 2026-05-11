from __future__ import annotations


def run(payload: dict) -> dict:
    draft = payload.get("draft", {}) if isinstance(payload.get("draft"), dict) else {}
    content = str(draft.get("markdown", ""))
    issues: list[str] = []
    if len(content.strip()) < 120:
        issues.append("Output too short.")
    lowered = content.lower()
    if "summary" not in lowered and "摘要" not in content:
        issues.append("Missing report section: summary")
    if "finding" not in lowered and "结果" not in content and "发现" not in content:
        issues.append("Missing report section: findings")
    if "recommendation" not in lowered and "建议" not in content:
        issues.append("Missing report section: recommendations")
    return {"passed": len(issues) == 0, "issues": issues, "normalized_markdown": content.strip() + "\n"}

