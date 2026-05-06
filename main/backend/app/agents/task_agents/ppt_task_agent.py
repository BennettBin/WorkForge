from dataclasses import dataclass

from app.agents.sub_agents import ContentAgent, OutlineAgent, ReviewAgent


@dataclass
class PPTTaskArtifacts:
    outline: list[dict]
    slides: list[dict]
    review_passed: bool
    review_issues: list[str]


class PPTTaskAgent:
    def __init__(self):
        self.outline_agent = OutlineAgent()
        self.content_agent = ContentAgent()
        self.review_agent = ReviewAgent()

    def execute(
        self,
        parsed_text: str,
        requested_pages: int,
        requirement: str,
        retrieve_context_fn=None,
        knowledge_search_fn=None,
        llm_generate_fn=None,
        no_source_file: bool = False,
    ) -> PPTTaskArtifacts:
        outline_items = self.outline_agent.generate(
            parsed_text,
            requested_pages,
            requirement,
            retrieve_context_fn=retrieve_context_fn,
            llm_generate_fn=llm_generate_fn,
            no_source_file=no_source_file,
        )

        knowledge_by_slide: dict[int, list[dict]] = {}
        if callable(knowledge_search_fn):
            search_budget = max(3, min(10, requested_pages - 2)) if no_source_file else 3
            for item in outline_items:
                if item.kind != "content":
                    continue
                if search_budget <= 0:
                    break
                query = f"{requirement} {item.title}"
                refs = knowledge_search_fn(query, max_results=2)
                if refs:
                    knowledge_by_slide[item.index] = refs
                search_budget -= 1

        content_items = self.content_agent.generate(
            outline_items,
            parsed_text,
            retrieve_context_fn=retrieve_context_fn,
            external_knowledge_by_slide=knowledge_by_slide,
            llm_generate_fn=llm_generate_fn,
            no_source_file=no_source_file,
        )
        review = self.review_agent.review(content_items, requested_pages)

        return PPTTaskArtifacts(
            outline=[
                {
                    "index": i.index,
                    "kind": i.kind,
                    "title": i.title,
                    "goals": i.goals,
                }
                for i in outline_items
            ],
            slides=[
                {
                    "index": c.index,
                    "kind": c.kind,
                    "title": c.title,
                    "bullets": c.bullets,
                    "notes": c.notes,
                    "image_placeholders": c.image_placeholders,
                }
                for c in review.reviewed
            ],
            review_passed=review.passed,
            review_issues=review.issues,
        )
