---
name: data_clean_plan
domain: data_analysis
version: 1.0.0
owner: backend
status: active
task_types:
  - data_analysis
stages:
  - planning
runtime_handler: runtime.py:run
trigger_keywords:
  - clean
  - missing value
  - 数据清洗
---

# data_clean_plan

## Metadata
- `name`: data_clean_plan
- `domain`: data_analysis
- `task_types`: data_analysis
- `stages`: planning

## Core Capability
Return a deterministic data-cleaning checklist for analysis workflows.

## Workflow
1. Inspect requirement.
2. Output cleaning step sequence.
3. Provide validation hints.

## Output Requirements
- `steps` array.
- Steps must cover missing data and type normalization.

## Notes
- Keep workflow explainable and auditable.


