---
name: code_readme_structure
domain: code_doc
version: 1.0.0
owner: backend
status: active
task_types:
  - code_doc
stages:
  - planning
runtime_handler: runtime.py:run
trigger_keywords:
  - readme
  - quick start
  - 文档结构
---

# code_readme_structure

## Metadata
- `name`: code_readme_structure
- `domain`: code_doc
- `task_types`: code_doc
- `stages`: planning

## Core Capability
Generate README section scaffolding for software documentation tasks.

## Workflow
1. Parse project intent.
2. Return ordered README sections.
3. Highlight setup and architecture coverage.

## Output Requirements
- `sections` array with practical doc headings.

## Notes
- Keep structure usable for both small scripts and medium services.


