---
name: data_excel_cate_word_report
domain: data_analysis
version: 1.0.0
owner: backend
status: active
task_types:
  - data_analysis
stages:
  - exporting
runtime_handler: app.services.skill_runtime.executor:SkillExecutor.execute(data_excel_cate_word_report)
trigger_keywords:
  - excel
  - xlsx
  - cate
  - bar chart
  - word
---

# data_excel_cate_word_report

## Metadata
- `name`: data_excel_cate_word_report
- `domain`: data_analysis
- `task_types`: data_analysis
- `stages`: exporting

## Core Capability
For Excel datasets, compute distribution of column `cate`, generate academic-style bar chart, and export chart + analysis into a Word report.

## Workflow
1. Read uploaded Excel (`xlsx/xls`) and locate `cate` column.
2. Count category frequencies and sort by frequency.
3. Render bar chart image.
4. Build Word report with summary, table, figure, and analysis text.

## Output Requirements
- Return `report_path` and `chart_path`.
- Return `cate_column`, `category_count`, `total_rows`.
- If chart backend is unavailable, keep Word export and include fallback note.

## Notes
- This skill is intended for structured tabular tasks, not generic text analysis.
- If `cate` column is missing, raise explicit error for upstream fallback handling.
