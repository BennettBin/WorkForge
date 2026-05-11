from __future__ import annotations


def run(payload: dict) -> dict:
    requirement = str(payload.get("requirement", "")).strip()
    return {
        "summary": f"report plan generated: {requirement[:80]}",
        "sections": [
            "Executive Summary",
            "Background",
            "Method",
            "Findings",
            "Risks and Limitations",
            "Recommendations",
            "Conclusion",
        ],
    }

