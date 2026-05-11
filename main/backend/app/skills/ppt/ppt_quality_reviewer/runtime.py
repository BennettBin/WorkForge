from __future__ import annotations


def run(payload: dict) -> dict:
    slides = payload.get("slides", [])
    requested_pages = int(payload.get("requested_pages", 0) or 0)
    issues: list[str] = []
    if not isinstance(slides, list):
        slides = []
    if requested_pages > 0 and len(slides) != requested_pages:
        issues.append(f"Page count mismatch: expected {requested_pages}, actual {len(slides)}")
    if not slides:
        issues.append("No slides generated")
        return {"passed": False, "issues": issues, "reviewed": slides}
    if str(slides[0].get("kind", "")) != "cover":
        issues.append("Missing cover slide")
    if str(slides[-1].get("kind", "")) != "summary":
        issues.append("Missing summary slide")
    for slide in slides:
        idx = int(slide.get("index", 0) or 0)
        title = str(slide.get("title", ""))
        bullets = slide.get("bullets", []) if isinstance(slide.get("bullets"), list) else []
        placeholders = slide.get("image_placeholders", []) if isinstance(slide.get("image_placeholders"), list) else []
        if not title.strip():
            issues.append(f"Slide {idx} missing title")
        if str(slide.get("kind", "")) == "content" and len(bullets) == 0:
            issues.append(f"Slide {idx} has empty content")
        if sum(len(str(b)) for b in bullets) > 900:
            issues.append(f"Slide {idx} has too much text")
        for ph in placeholders:
            if isinstance(ph, dict):
                if not str(ph.get("label", "")).strip():
                    issues.append(f"Slide {idx} has invalid image placeholder label")
                if not str(ph.get("source", "")).strip():
                    issues.append(f"Slide {idx} has invalid image placeholder source")
    return {"passed": len(issues) == 0, "issues": issues, "reviewed": slides}

