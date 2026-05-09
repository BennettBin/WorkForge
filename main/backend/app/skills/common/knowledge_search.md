---
name: knowledge_search
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
  - generating
tags:
  - search
  - web
  - retrieval
runtime_handler: app.services.knowledge_search.search_service:KnowledgeSearchService.search_and_extract
trigger_keywords:
  - 搜索
  - 检索
  - 联网
  - 补充资料
  - 最新
  - reference
  - citation
  - research
---

# knowledge_search

## Metadata
- `name`: knowledge_search
- `domain`: common
- `task_types`: ppt, report, wechat_post, data_analysis, code_doc, paper_assistant
- `stages`: planning, generating
- `status`: active

## Core Capability
Perform web retrieval and extract compact evidence snippets for generation and revision.

## Workflow
1. Build search query from requirement and topic.
2. Fetch results and extract page text snippets.
3. Return structured references.

## Output Requirements
- `items[]` with `title`, `url`, `snippet`, optional `content`.
- Empty list on no result; no malformed entries.

## Notes
- Network failure should degrade gracefully.
- Avoid blocking the full task pipeline when search is unavailable.

