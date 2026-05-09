from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.services.data_analysis_tools import ExcelCateDistributionTool
from app.services.knowledge_search import KnowledgeSearchService


class SkillExecutionError(Exception):
    pass


@dataclass
class SkillExecutor:
    knowledge_search: KnowledgeSearchService
    excel_report_tool: ExcelCateDistributionTool

    @classmethod
    def create_default(cls) -> "SkillExecutor":
        return cls(
            knowledge_search=KnowledgeSearchService(),
            excel_report_tool=ExcelCateDistributionTool(),
        )

    def execute(self, skill_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        name = (skill_name or "").strip().lower()
        if name == "knowledge_search":
            query = str(payload.get("query", "")).strip()
            max_results_raw = payload.get("max_results", 2)
            try:
                max_results = int(max_results_raw)
            except Exception:
                max_results = 2
            items = self.knowledge_search.search_and_extract(query, max_results=max(1, min(5, max_results)))
            return {"items": items}
        if name == "report_outline":
            requirement = str(payload.get("requirement", "")).strip()
            return {
                "sections": [
                    "Executive Summary",
                    "Background",
                    "Method",
                    "Findings",
                    "Risks and Limitations",
                    "Recommendations",
                    "Conclusion",
                ],
                "hint": f"Report should stay aligned with requirement: {requirement[:120]}",
            }
        if name == "report_quality_check":
            content = str(payload.get("content", ""))
            lowered = content.lower()
            section_aliases = {
                "summary": [
                    "summary",
                    "executive summary",
                    "abstract",
                    "\u6458\u8981",
                    "\u603b\u7ed3",
                    "\u6982\u8ff0",
                    "\u7efc\u8ff0",
                    "\u603b\u89c8",
                ],
                "findings": [
                    "findings",
                    "results",
                    "analysis",
                    "\u53d1\u73b0",
                    "\u7ed3\u679c",
                    "\u5206\u6790\u7ed3\u8bba",
                    "\u5173\u952e\u53d1\u73b0",
                ],
                "recommendations": [
                    "recommendations",
                    "suggestions",
                    "actions",
                    "\u5efa\u8bae",
                    "\u6539\u8fdb\u5efa\u8bae",
                    "\u884c\u52a8\u5efa\u8bae",
                    "\u5bf9\u7b56",
                    "\u4e0b\u4e00\u6b65",
                ],
            }
            missing: list[str] = []
            for section, aliases in section_aliases.items():
                if not any(alias in lowered or alias in content for alias in aliases):
                    missing.append(section)
            return {"missing_sections": missing, "passed": len(missing) == 0}
        if name == "wechat_title_ideas":
            requirement = str(payload.get("requirement", "")).strip()
            prefix = requirement[:24] if requirement else "Topic"
            return {
                "titles": [
                    f"{prefix}: key takeaways in one post",
                    f"{prefix}: 5 things you should know",
                    f"{prefix}: practical guide from basics to action",
                    f"{prefix}: pitfalls and recommendations",
                    f"{prefix}: latest trends and interpretation",
                ]
            }
        if name == "wechat_style_polish":
            return {"style_rules": ["Short paragraphs", "Conversational tone", "Strong heading transitions", "Actionable closing"]}
        if name == "data_clean_plan":
            return {"steps": ["Schema scan", "Missing-value strategy", "Type normalization", "Outlier handling", "Validation checks"]}
        if name == "data_chart_plan":
            return {"charts": ["Trend line chart", "Category bar chart", "Distribution histogram"], "notes": "Select charts based on variable types."}
        if name == "data_excel_cate_word_report":
            excel_path = str(payload.get("excel_path", "")).strip()
            report_docx_path = str(payload.get("report_docx_path", "")).strip()
            chart_png_path = str(payload.get("chart_png_path", "")).strip()
            requirement = str(payload.get("requirement", "")).strip()
            llm_markdown = str(payload.get("llm_markdown", ""))
            language = str(payload.get("language", "zh-CN") or "zh-CN")
            if not excel_path or not report_docx_path or not chart_png_path:
                raise SkillExecutionError("data_excel_cate_word_report requires excel_path/report_docx_path/chart_png_path.")
            result = self.excel_report_tool.generate_report(
                excel_path=excel_path,
                report_docx_path=report_docx_path,
                chart_png_path=chart_png_path,
                requirement=requirement,
                llm_markdown=llm_markdown,
                language=language,
            )
            return {
                "report_path": result.report_path,
                "chart_path": result.chart_path,
                "cate_column": result.cate_column,
                "category_count": len(result.categories),
                "total_rows": result.total_rows,
            }
        if name == "code_readme_structure":
            return {"sections": ["Project Overview", "Quick Start", "Configuration", "Architecture", "Testing", "FAQ"]}
        if name == "code_api_doc":
            return {"sections": ["Endpoints", "Request/Response Schema", "Error Codes", "Examples"]}
        if name == "paper_outline":
            return {"sections": ["Title", "Abstract", "Introduction", "Methods", "Results", "Discussion", "Conclusion", "References"]}
        if name == "paper_revision_suggestions":
            return {"checks": ["Claim-evidence alignment", "Terminology consistency", "Academic tone", "Citation completeness"]}
        raise SkillExecutionError(f"Unsupported skill execution: {skill_name}")
