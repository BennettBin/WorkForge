from __future__ import annotations


def run(payload: dict) -> dict:
    return {
        "summary": "code doc plan generated",
        "readme_sections": ["Project Overview", "Quick Start", "Configuration", "Architecture", "Testing", "FAQ"],
        "api_sections": ["Endpoints", "Request/Response Schema", "Error Codes", "Examples"],
    }

