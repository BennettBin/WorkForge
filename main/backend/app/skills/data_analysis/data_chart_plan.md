---
name: data_chart_plan
domain: data_analysis
version: 1.0.0
owner: backend
status: active
task_types:
  - data_analysis
stages:
  - generating
runtime_handler: app.services.skill_runtime.executor:SkillExecutor.execute(data_chart_plan)
trigger_keywords:
  - chart
  - plot
  - 图表
---

# data_chart_plan

## Metadata
- `name`: data_chart_plan
- `domain`: data_analysis
- `task_types`: data_analysis
- `stages`: generating

## Core Capability
Suggest chart candidates and narrative mapping for analysis outputs.

## Workflow
1. Infer likely variable types.
2. Propose chart families.
3. Return concise chart usage notes.

## Output Requirements
- `charts` array.
- Optional `notes` for chart-selection rationale.

## Notes
- Recommendations must stay generic unless concrete schema is available.


