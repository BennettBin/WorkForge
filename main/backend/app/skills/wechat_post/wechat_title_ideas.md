---
name: wechat_title_ideas
domain: wechat_post
version: 1.0.0
owner: backend
status: active
task_types:
  - wechat_post
stages:
  - planning
runtime_handler: app.services.skill_runtime.executor:SkillExecutor.execute(wechat_title_ideas)
trigger_keywords:
  - 公众号
  - 标题
  - wechat
---

# wechat_title_ideas

## Metadata
- `name`: wechat_title_ideas
- `domain`: wechat_post
- `task_types`: wechat_post
- `stages`: planning

## Core Capability
Generate multiple title candidates for WeChat content.

## Workflow
1. Read topic and audience intent.
2. Produce diverse title styles.
3. Return candidate list for writer selection.

## Output Requirements
- `titles` array with >= 5 candidates.
- Titles should be concise and readable.

## Notes
- Avoid exaggerated or misleading clickbait.


