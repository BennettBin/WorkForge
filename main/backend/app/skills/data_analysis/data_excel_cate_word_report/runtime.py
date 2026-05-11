from __future__ import annotations

from app.services.data_analysis_tools import ExcelCateDistributionTool


def run(payload: dict) -> dict:
    excel_path = str(payload.get("excel_path", "")).strip()
    report_docx_path = str(payload.get("report_docx_path", "")).strip()
    chart_png_path = str(payload.get("chart_png_path", "")).strip()
    requirement = str(payload.get("requirement", "")).strip()
    llm_markdown = str(payload.get("llm_markdown", ""))
    language = str(payload.get("language", "zh-CN") or "zh-CN")
    target_column = str(payload.get("target_column", "cate") or "cate").strip()
    if not excel_path or not report_docx_path or not chart_png_path:
        raise ValueError("data_excel_cate_word_report requires excel_path/report_docx_path/chart_png_path.")
    tool = ExcelCateDistributionTool()
    result = tool.generate_report(
        excel_path=excel_path,
        report_docx_path=report_docx_path,
        chart_png_path=chart_png_path,
        requirement=requirement,
        llm_markdown=llm_markdown,
        language=language,
        target_column=target_column,
    )
    return {
        "report_path": result.report_path,
        "chart_path": result.chart_path,
        "cate_column": result.cate_column,
        "category_count": len(result.categories),
        "total_rows": result.total_rows,
    }
