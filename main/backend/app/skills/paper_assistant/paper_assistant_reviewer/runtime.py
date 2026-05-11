from __future__ import annotations


def run(payload: dict) -> dict:
    draft = payload.get("draft", {}) if isinstance(payload.get("draft"), dict) else {}
    content = str(draft.get("markdown", ""))
    issues: list[str] = []
    if len(content.strip()) < 120:
        issues.append("Output too short.")
    lowered = content.lower()
    if "abstract" not in lowered:
        issues.append("Missing abstract section.")
    if "revision" not in lowered:
        issues.append("Missing revision guidance.")
    return {"passed": len(issues) == 0, "issues": issues, "normalized_markdown": content.strip() + "\n"}

