---
name: report_writer
domain: report
task_types:
  - report
stages:
  - generating
runtime_handler: runtime.py:run
trigger_keywords:
  - report
  - write
---

# report_writer

Write markdown report draft from requirement and context.

