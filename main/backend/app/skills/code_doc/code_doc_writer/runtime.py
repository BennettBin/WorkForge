from __future__ import annotations


def run(payload: dict) -> dict:
    requirement = str(payload.get("requirement", "")).strip()
    parsed_text = str(payload.get("parsed_text", ""))
    style = str(payload.get("style", ""))
    language = str(payload.get("language", ""))
    plan = payload.get("plan", {}) if isinstance(payload.get("plan"), dict) else {}
    llm_generate_fn = payload.get("llm_generate_fn")
    prompt = (
        f"Task Type: code_doc\nLanguage: {language}\nStyle: {style}\nRequirement:\n{requirement}\n\n"
        f"README Sections:\n{plan.get('readme_sections', [])}\nAPI Sections:\n{plan.get('api_sections', [])}\n\n"
        f"Reference:\n{parsed_text[:6000]}\n\nWrite markdown README and technical documentation."
    )
    if callable(llm_generate_fn):
        markdown = llm_generate_fn(prompt)
    else:
        markdown = "# Code Documentation\n\n## Project Overview\nFallback.\n\n## Quick Start\nTBD.\n\n## API\nTBD.\n"
    return {"markdown": markdown, "section_count": markdown.count("\n## ")}

