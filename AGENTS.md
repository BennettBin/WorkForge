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
