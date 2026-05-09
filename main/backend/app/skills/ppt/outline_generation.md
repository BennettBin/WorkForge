---
name: outline_generation
domain: ppt
version: 1.0.0
owner: backend
status: active
task_types:
  - ppt
stages:
  - generating
tags:
  - outline
  - slide-plan
  - structure
depends_on:
  - base_prompt
---

# outline_generation

## Metadata
- `name`: outline_generation
- `domain`: ppt
- `task_types`: ppt
- `stages`: generating
- `depends_on`: base_prompt

## Core Capability
Generate page-level PPT outline (cover/content/summary) with coherent topic flow.

## Workflow
1. Read requirement and parsed source summary.
2. Allocate page structure and section sequence.
3. Output per-slide title, bullets, and notes hints.

## Output Requirements
- Page count matches requested count.
- Includes cover and summary slide.
- Each content slide has non-empty bullets.

## Notes
- Keep slide text density readable.
- Prefer traceable facts from source context.

