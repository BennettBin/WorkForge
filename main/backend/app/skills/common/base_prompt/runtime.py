from __future__ import annotations


def run(payload: dict) -> dict:
    requirement = str(payload.get("requirement", "")).strip()
    return {
        "goal": requirement[:240],
        "constraints": ["Use structured output", "Keep claims traceable", "Do not leak secrets"],
        "acceptance_checklist": ["Has clear structure", "Matches user requirement", "Language/style constraints respected"],
    }

