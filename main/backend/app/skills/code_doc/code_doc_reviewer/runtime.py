from __future__ import annotations


def run(payload: dict) -> dict:
    draft = payload.get("draft", {}) if isinstance(payload.get("draft"), dict) else {}
    content = str(draft.get("markdown", ""))
    issues: list[str] = []
    if len(content.strip()) < 120:
        issues.append("Output too short.")
    lowered = content.lower()
    if "quick start" not in lowered:
        issues.append("Missing quick start section.")
    if "api" not in lowered:
        issues.append("Missing API section.")
    return {"passed": len(issues) == 0, "issues": issues, "normalized_markdown": content.strip() + "\n"}

