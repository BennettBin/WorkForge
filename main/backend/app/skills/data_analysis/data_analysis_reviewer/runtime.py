from __future__ import annotations


def run(payload: dict) -> dict:
    draft = payload.get("draft", {}) if isinstance(payload.get("draft"), dict) else {}
    content = str(draft.get("markdown", ""))
    issues: list[str] = []
    if len(content.strip()) < 120:
        issues.append("Output too short.")
    lowered = content.lower()
    if "clean" not in lowered and "cleaning" not in lowered:
        issues.append("Missing cleaning section.")
    if "finding" not in lowered and "conclusion" not in lowered:
        issues.append("Missing findings section.")
    return {"passed": len(issues) == 0, "issues": issues, "normalized_markdown": content.strip() + "\n"}

