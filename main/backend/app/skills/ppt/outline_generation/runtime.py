from __future__ import annotations


def run(payload: dict) -> dict:
    requested_pages = int(payload.get("requested_pages", 10) or 10)
    return {"requested_pages": max(1, requested_pages), "note": "PPT outline generation is handled by PPT sub-agents."}

