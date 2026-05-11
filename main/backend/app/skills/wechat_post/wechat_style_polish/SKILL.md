---
name: wechat_style_polish
domain: wechat_post
version: 1.0.0
owner: backend
status: active
task_types:
  - wechat_post
stages:
  - generating
  - reviewing
runtime_handler: runtime.py:run
trigger_keywords:
  - 风格
  - 润色
  - readability
---

# wechat_style_polish

## Metadata
- `name`: wechat_style_polish
- `domain`: wechat_post
- `task_types`: wechat_post
- `stages`: generating, reviewing

## Core Capability
Provide readability and tone constraints for WeChat-style writing.

## Workflow
1. Return style-rule checklist.
2. Apply checklist during draft/review loops.

## Output Requirements
- `style_rules` array with concrete writing constraints.

## Notes
- Emphasize short paragraphs and clear section transitions.


