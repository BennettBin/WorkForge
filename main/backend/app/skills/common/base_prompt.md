---
name: base_prompt
domain: common
version: 1.0.0
owner: backend
status: active
task_types:
  - ppt
  - report
  - wechat_post
  - data_analysis
  - code_doc
  - paper_assistant
stages:
  - planning
  - skill_selecting
  - generating
tags:
  - prompt
  - guardrails
  - structure
---

# base_prompt

## Metadata
- `name`: base_prompt
- `domain`: common
- `task_types`: ppt (shared conceptual guardrail for all tasks)
- `stages`: planning, skill_selecting, generating
- `status`: active

## Core Capability
Provide a normalized prompt frame and guardrails so downstream agents keep output format and quality checks consistent.

## Workflow
1. Parse requirement and constraints.
2. Normalize task goal and acceptance checks.
3. Return reusable prompt scaffold.

## Output Requirements
- Must contain normalized goal.
- Must contain constraints.
- Must contain acceptance checklist.

## Notes
- Do not include secrets or internal paths in output.
- If requirement is ambiguous, produce explicit clarifying assumptions.

