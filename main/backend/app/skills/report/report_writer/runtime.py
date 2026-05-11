from __future__ import annotations


def run(payload: dict) -> dict:
    requirement = str(payload.get("requirement", "")).strip()
    parsed_text = str(payload.get("parsed_text", ""))
    style = str(payload.get("style", ""))
    language = str(payload.get("language", ""))
    plan = payload.get("plan", {}) if isinstance(payload.get("plan"), dict) else {}
    sections = plan.get("sections", []) if isinstance(plan.get("sections"), list) else []
    llm_generate_fn = payload.get("llm_generate_fn")
    prompt = (
        f"Task Type: report\nLanguage: {language}\nStyle: {style}\n"
        f"Requirement:\n{requirement}\n\nPlanned Sections:\n{sections}\n\n"
        f"Reference:\n{parsed_text[:6000]}\n\n"
        "Write markdown report with headings, summary, findings, recommendations."
    )
    if callable(llm_generate_fn):
        markdown = llm_generate_fn(prompt)
    else:
        markdown = "# Report\n\n## Summary\nFallback draft.\n\n## Findings\nTBD.\n\n## Recommendations\nTBD.\n"
    return {"markdown": markdown, "section_count": markdown.count("\n## ")}

