---
name: report_outline
domain: report
version: 1.0.0
owner: backend
status: active
task_types:
  - report
stages:
  - planning
  - generating
runtime_handler: runtime.py:run
trigger_keywords:
  - report
  - executive summary
  - findings
---

# report_outline

## Metadata
- `name`: report_outline
- `domain`: report
- `task_types`: report
- `stages`: planning, generating

## Core Capability
Build a report section blueprint for downstream drafting.

## Workflow
1. Read requirement and context.
2. Produce standard report section set.
3. Return planning hints for drafting order.

## Output Requirements
- Must include section list.
- Must include at least one summary-oriented section.

## Notes
- Keep structure adaptable for technical and business reports.


