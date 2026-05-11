from __future__ import annotations


def run(payload: dict) -> dict:
    requirement = str(payload.get("requirement", "")).strip()
    parsed_text = str(payload.get("parsed_text", ""))
    style = str(payload.get("style", ""))
    language = str(payload.get("language", ""))
    plan = payload.get("plan", {}) if isinstance(payload.get("plan"), dict) else {}
    llm_generate_fn = payload.get("llm_generate_fn")
    prompt = (
        f"Task Type: data_analysis\nLanguage: {language}\nStyle: {style}\nRequirement:\n{requirement}\n\n"
        f"Clean Steps:\n{plan.get('clean_steps', [])}\nChart Plan:\n{plan.get('chart_plan', [])}\n\n"
        f"Reference:\n{parsed_text[:6000]}\n\nWrite markdown including assumptions, cleaning, findings and chart recommendations."
    )
    if callable(llm_generate_fn):
        markdown = llm_generate_fn(prompt)
    else:
        markdown = "# Data Analysis\n\n## Assumptions\nFallback.\n\n## Cleaning\nTBD.\n\n## Findings\nTBD.\n"
    return {"markdown": markdown, "section_count": markdown.count("\n## ")}

