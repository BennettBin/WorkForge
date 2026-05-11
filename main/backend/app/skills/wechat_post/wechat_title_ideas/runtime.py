from __future__ import annotations


def run(payload: dict) -> dict:
    requirement = str(payload.get("requirement", "")).strip()
    prefix = requirement[:24] if requirement else "Topic"
    return {
        "titles": [
            f"{prefix}: key takeaways in one post",
            f"{prefix}: 5 things you should know",
            f"{prefix}: practical guide from basics to action",
            f"{prefix}: pitfalls and recommendations",
            f"{prefix}: latest trends and interpretation",
        ]
    }

