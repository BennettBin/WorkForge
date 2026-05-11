---
name: paper_revision_suggestions
domain: paper_assistant
version: 1.0.0
owner: backend
status: active
task_types:
  - paper_assistant
stages:
  - reviewing
runtime_handler: runtime.py:run
trigger_keywords:
  - revise
  - reviewer
  - 学术润色
---

# paper_revision_suggestions

## Metadata
- `name`: paper_revision_suggestions
- `domain`: paper_assistant
- `task_types`: paper_assistant
- `stages`: reviewing

## Core Capability
Provide review-oriented checks for paper polishing and revision.

## Workflow
1. Inspect draft structure and claims.
2. Return high-value revision checks.
3. Feed reviewer sub-agent for final decision.

## Output Requirements
- `checks` array with concrete revision axes.

## Notes
- This skill does not replace formal citation verification.


