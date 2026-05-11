---
name: code_api_doc
domain: code_doc
version: 1.0.0
owner: backend
status: active
task_types:
  - code_doc
stages:
  - generating
runtime_handler: runtime.py:run
trigger_keywords:
  - api
  - endpoint
  - 接口文档
---

# code_api_doc

## Metadata
- `name`: code_api_doc
- `domain`: code_doc
- `task_types`: code_doc
- `stages`: generating

## Core Capability
Provide API documentation section planning and field expectations.

## Workflow
1. Define endpoint-documentation skeleton.
2. Return schema/example/error-code headings.
3. Feed drafting and review sub-agents.

## Output Requirements
- `sections` array including request/response and error docs.

## Notes
- This skill provides structure hints; endpoint truth still depends on input context.


