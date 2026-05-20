# WorkForge AI Current Architecture

## Maintenance Rules
- Update this file whenever major service/module boundaries change.
- Keep entries factual and scoped to what is implemented now.

## Core Runtime Modules
- `main/backend/app/api/routes/tasks.py`: task APIs, template list APIs, run/revise/rollback/download flow.
- `main/backend/app/services/task_manager/task_service.py`: core task orchestration, template bundle resolution, PPT generation execution path.
- `main/backend/app/services/template_bundle/validator.py`: fixed PPT template bundle contract validator.
- `main/backend/app/services/export_engine/template_script_runner.py`: script runtime loader/executor for `render_from_template.py`.
- `main/backend/app/services/export_engine/pptx_exporter.py`: compatibility PPT exporter path (currently fallback only when script render feature flag is disabled).
- `main/backend/app/templates/ppt/system_default/rebuild_template_ppt.py`: utility script for byte-level 1:1 template PPT rebuild and optional embedded asset extraction.
- `main/backend/app/templates/ppt/system_default/extract_ppt_elements.py`: generic extractor that unpacks full PPTX package and emits `_manifest.json` plus textbox placeholder mapping.
- `main/backend/app/templates/ppt/system_default/build_ppt_from_extracted.py`: function-based builder that reconstructs PPTX from extracted elements and replaces all slide textbox texts by parameter keys.
- `main/backend/app/skills/template_generation/runtime.py`: template-generation runtime; for PPT input it extracts full package elements into `template_elements/` and emits a parameterized rebuild function script `build_ppt_from_extracted.py` inside each template folder.
- `main/backend/app/agents/task_agents/template_generation_task_agent.py`: template-generation orchestration now routes PPT template generation through `template_generation` skill runtime payload.
- `main/frontend/src/pages/TaskCreate/TaskCreatePage.tsx`: task creation form, template selection UI and defaults.

## PPT Template Script Runtime Chain (Current)
1. Task creation binds `template_choice` to task requirement (`TemplateChoice=<name>`).
2. If `template_choice` is missing for PPT generation, backend defaults to `system_default`.
3. Backend validates template bundle at `app/templates/ppt/<template_choice>/`.
4. During PPT export nodes (run/revise/rollback), `TaskService` calls `_render_ppt_with_template(...)`.
5. `_render_ppt_with_template(...)` loads:
   - `template.pptx`
   - `template.meta.json`
   - `template.rules.json`
   - `render_from_template.py`
6. `TemplateScriptRunner.render(...)` invokes template script entrypoint:
   `render(payload, output_path, template_path, meta, rules)`.
7. Output PPTX path is registered as version artifact.

## Template Selection/Listing Policy
- API `/v1/tasks/ppt/templates` returns valid bundles by default.
- Invalid bundles are hidden unless `include_invalid=true`.
- Frontend TaskCreate uses `system_default` as initial template choice and requires template selection for PPT tasks.

## Change Log
- 2026-05-18 10:12: Added `rebuild_template_ppt.py` under `system_default` for exact PPT template duplication and optional extraction of `ppt/media` + `ppt/theme` assets.
- 2026-05-18 10:32: Added `extract_ppt_elements.py` (generic extraction) and `build_ppt_from_extracted.py` (parameterized rebuild function) for template package round-trip with customizable textbox texts.
- 2026-05-18 11:33: Migrated PPT extraction/rebuild generation logic into `skills/template_generation` and switched `TemplateGenerationTaskAgent` PPT path to `template_generation` skill.
