---
name: report_quality_check
domain: report
version: 1.0.0
owner: backend
status: active
task_types:
  - report
stages:
  - reviewing
runtime_handler: app.services.skill_runtime.executor:SkillExecutor.execute(report_quality_check)
trigger_keywords:
  - quality
  - review
  - recommendations
---

# report_quality_check

## Metadata
- `name`: report_quality_check
- `domain`: report
- `task_types`: report
- `stages`: reviewing

## Core Capability
Validate report completeness for key narrative sections.

## Workflow
1. Scan markdown content.
2. Check mandatory sections.
3. Return pass/fail and missing section names.

## Output Requirements
- `passed` boolean.
- `missing_sections` array.

## Notes
- This check is structural, not factual truth validation.


