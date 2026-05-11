from __future__ import annotations


def run(payload: dict) -> dict:
    requirement = str(payload.get("requirement", "")).strip()
    parsed_text = str(payload.get("parsed_text", ""))
    style = str(payload.get("style", ""))
    language = str(payload.get("language", ""))
    plan = payload.get("plan", {}) if isinstance(payload.get("plan"), dict) else {}
    llm_generate_fn = payload.get("llm_generate_fn")
    prompt = (
        f"Task Type: paper_assistant\nLanguage: {language}\nStyle: {style}\nRequirement:\n{requirement}\n\n"
        f"Section Plan:\n{plan.get('sections', [])}\nReview Checks:\n{plan.get('review_checks', [])}\n\n"
        f"Reference:\n{parsed_text[:6000]}\n\nWrite markdown for paper assistance: outline, abstract draft, revision guidance."
    )
    if callable(llm_generate_fn):
        markdown = llm_generate_fn(prompt)
    else:
        markdown = "# Paper Assistant\n\n## Outline\nFallback.\n\n## Abstract Draft\nTBD.\n\n## Revision Suggestions\nTBD.\n"
    return {"markdown": markdown, "section_count": markdown.count("\n## ")}

