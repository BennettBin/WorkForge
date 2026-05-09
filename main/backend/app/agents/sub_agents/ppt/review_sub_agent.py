from dataclasses import dataclass

from app.agents.sub_agents.ppt.content_sub_agent import SlideContentItem


@dataclass
class ReviewResult:
    passed: bool
    issues: list[str]
    reviewed: list[SlideContentItem]


class ReviewAgent:
    def review(self, slides: list[SlideContentItem], requested_pages: int) -> ReviewResult:
        issues: list[str] = []
        if len(slides) != requested_pages:
            issues.append(f"Page count mismatch: expected {requested_pages}, actual {len(slides)}")

        if not slides:
            issues.append("No slides generated")
            return ReviewResult(False, issues, slides)

        if slides[0].kind != "cover":
            issues.append("Missing cover slide")
        if slides[-1].kind != "summary":
            issues.append("Missing summary slide")

        for slide in slides:
            if not slide.title.strip():
                issues.append(f"Slide {slide.index} missing title")
            if slide.kind == "content" and len(slide.bullets) == 0:
                issues.append(f"Slide {slide.index} has empty content")
            if sum(len(b) for b in slide.bullets) > 900:
                issues.append(f"Slide {slide.index} has too much text")
            for ph in slide.image_placeholders:
                if not str(ph.get("label", "")).strip():
                    issues.append(f"Slide {slide.index} has invalid image placeholder label")
                if not str(ph.get("source", "")).strip():
                    issues.append(f"Slide {slide.index} has invalid image placeholder source")

        return ReviewResult(passed=len(issues) == 0, issues=issues, reviewed=slides)
