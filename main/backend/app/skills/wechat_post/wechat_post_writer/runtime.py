from __future__ import annotations


def run(payload: dict) -> dict:
    requirement = str(payload.get("requirement", "")).strip()
    parsed_text = str(payload.get("parsed_text", ""))
    style = str(payload.get("style", ""))
    language = str(payload.get("language", ""))
    plan = payload.get("plan", {}) if isinstance(payload.get("plan"), dict) else {}
    llm_generate_fn = payload.get("llm_generate_fn")
    prompt = (
        f"Task Type: wechat_post\nLanguage: {language}\nStyle: {style}\n"
        f"Requirement:\n{requirement}\n\n"
        f"Title Candidates:\n{plan.get('title_candidates', [])}\n\n"
        f"Reference:\n{parsed_text[:6000]}\n\n"
        "Write markdown with title options, abstract, body sections, closing CTA."
    )
    if callable(llm_generate_fn):
        markdown = llm_generate_fn(prompt)
    else:
        markdown = "# Wechat Post\n\n## Title Options\n- Option 1\n\n## Abstract\nFallback.\n\n## Body\nTBD.\n"
    return {"markdown": markdown, "section_count": markdown.count("\n## ")}

