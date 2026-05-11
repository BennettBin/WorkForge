from __future__ import annotations


def run(payload: dict) -> dict:
    requirement = str(payload.get("requirement", "")).strip()
    return {
        "sections": [
            "Executive Summary",
            "Background",
            "Method",
            "Findings",
            "Risks and Limitations",
            "Recommendations",
            "Conclusion",
        ],
        "hint": f"Report should stay aligned with requirement: {requirement[:120]}",
    }

