from __future__ import annotations


def run(payload: dict) -> dict:
    draft = payload.get("draft", {}) if isinstance(payload.get("draft"), dict) else {}
    markdown = str(draft.get("markdown", ""))
    issues: list[str] = []
    if len(markdown.strip()) < 120:
        issues.append("Output too short.")
    if "##" not in markdown:
        issues.append("Missing section structure.")
    return {"passed": len(issues) == 0, "issues": issues, "normalized_markdown": markdown.strip() + "\n"}

