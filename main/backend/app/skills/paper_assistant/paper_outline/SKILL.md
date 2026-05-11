---
name: paper_outline
domain: paper_assistant
version: 1.0.0
owner: backend
status: active
task_types:
  - paper_assistant
stages:
  - planning
runtime_handler: runtime.py:run
trigger_keywords:
  - abstract
  - methodology
  - 论文
---

# paper_outline

## Metadata
- `name`: paper_outline
- `domain`: paper_assistant
- `task_types`: paper_assistant
- `stages`: planning

## Core Capability
Create academic-paper section skeleton for drafting assistance.

## Workflow
1. Parse academic intent and scope.
2. Return canonical paper sections.
3. Support downstream abstract/method/result writing.

## Output Requirements
- `sections` array with full paper structure.

## Notes
- Preserve academic ordering and terminology consistency.


