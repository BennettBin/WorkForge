# Repository Guidelines

## Project Structure & Module Organization

This repository is currently documentation-first. Root files include `WorkForge_AI_Product_Design.md` for product requirements, `tec_stack.md` for the proposed stack, `LICENSE`, and `.gitignore`. The `main/` directory exists as the future application root.

Use the documented architecture when adding code:

- `main/frontend/`: React + TypeScript + Vite UI, components, pages, API clients, and assets.
- `main/backend/`: Python + FastAPI service with `api/`, `services/`, `agents/`, `repositories/`, and domain models.
- `main/desktop/`: Tauri configuration and packaging code.
- `tests/`: backend tests and broader integration tests.
- `main/frontend/src/assets/`: frontend images, templates, and static resources.

## Build, Test, and Development Commands

No runnable scaffold is committed yet. Once created, keep these commands documented and working:

- `npm install`: install frontend dependencies from `main/frontend/`.
- `npm run dev`: start the Vite development server.
- `python -m venv .venv`: create the local Python environment.
- `pip install -r requirements.txt`: install backend dependencies.
- `uvicorn main.backend.api.app:app --reload`: run the FastAPI backend locally.
- `npm run tauri dev`: run the desktop app in development mode.
- `pytest`: run backend tests.

## Coding Style & Naming Conventions

Use Python 3.11+ with 4-space indentation, `snake_case` modules and functions, and `PascalCase` classes or Pydantic models. Use TypeScript for frontend code with `PascalCase` React components and `camelCase` variables. Keep repository interfaces explicit, for example `TaskRepository`, `JsonTaskRepository`, and `SqlTaskRepository`.

## Testing Guidelines

Use `pytest` for backend tests. Name Python test files `test_*.py` and place them under `tests/` or the matching backend package. Frontend tests should use the eventual Vite-compatible runner and `*.test.ts` or `*.test.tsx` naming. Prioritize orchestration, repositories, file parsing, and export generation.

## Commit & Pull Request Guidelines

Recent commits use short subjects such as `design file` plus merge commits. Prefer clear imperative messages going forward, such as `Add backend repository interfaces`.

Pull requests should include a summary, linked issue or task, test results, and screenshots or recordings for UI changes. Document any new configuration, environment variables, or migration steps.

## Security & Configuration Tips

Do not commit `.env`, credentials, datasets, generated outputs, checkpoints, or virtual environments. `.gitignore` already excludes these paths; document required variable names without secret values.

## Attentions

Before writing any code, you must read `develop_guide/architecture.md` in its entirety; furthermore, `develop_guide/architecture.md` must be updated upon the completion of any major feature or project milestone, and whenever script/module architecture changes.
Before writing any code, you must read `develop_guide/product_design.md` in its entirety.
During development, after every completed implementation step, you must append a new record to `develop_guide/process.md` including completion time and completed content.
Whenever adding/updating/removing scripts, modules, or major service boundaries, you must update `develop_guide/architecture.md` to reflect current architecture and the purpose of each script/module.

### Skill Runtime Enforcement (Mandatory)

For every new or updated Skill, agents must implement an executable runtime chain, not only a documentation description.

Minimum required contract for each Skill:
- `Skill file` must include:
  - clear trigger conditions/keywords
  - runtime binding target (handler path or executor mapping)
  - expected input/output schema
- `Skill registry` must expose the runtime binding metadata so orchestrators can resolve it.
- `Skill executor/runtime` must map the Skill name to a real callable service/tool implementation.
- `Task orchestration` must explicitly trigger the Skill when trigger conditions are met.
- `Auditability` is required: each Skill trigger must leave traceable execution records (for example `SkillCall`).
- `Fallback` is required: if tool/network execution fails, the workflow must degrade safely without silent failure.

Validation requirement before completion:
- Add or update automated tests proving:
  1) trigger conditions can activate the Skill,
  2) activation executes the bound tool/service path,
  3) execution results are persisted in trace logs/audit records.
