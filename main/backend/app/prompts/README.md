# Prompt Registry

This directory centralizes prompt text used by LLM calls and agent instruction templates.

## Files

- `llm_templates.py`
  - `build_outline_prompt(...)`
    - Called by: `main/backend/app/agents/sub_agents/outline_agent.py`
    - Purpose: Prompt for generating PPT outline JSON.
  - `build_content_prompt(...)`
    - Called by: `main/backend/app/agents/sub_agents/content_agent.py`
    - Purpose: Prompt for generating per-slide content JSON (including image placeholders).

- `agent_templates.py`
  - `OUTLINE_NO_SOURCE_DEFAULT_SNIPPETS`
    - Called by: `main/backend/app/agents/sub_agents/outline_agent.py`
    - Purpose: Seed sections when no source file is uploaded.
  - `CONTENT_NOTES_SOURCE_FILE_TEMPLATE`
    - Called by: `main/backend/app/agents/sub_agents/content_agent.py`
    - Purpose: Notes wording for source-file path.
  - `CONTENT_NOTES_WEB_SEARCH_TEMPLATE`
    - Called by: `main/backend/app/agents/sub_agents/content_agent.py`
    - Purpose: Notes wording for no-source-file search path.

## Notes

- Skill Markdown files under `main/backend/app/skills/` are still the runtime skill definitions and are not moved.
- Update prompt text here first, then run backend tests to verify behavior.
