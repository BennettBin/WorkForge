from __future__ import annotations


def run(payload: dict) -> dict:
    return {
        "summary": "data analysis plan generated",
        "clean_steps": ["Schema scan", "Missing-value strategy", "Type normalization", "Outlier handling", "Validation checks"],
        "chart_plan": ["Trend line chart", "Category bar chart", "Distribution histogram"],
    }

