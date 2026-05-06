from app.prompts.agent_templates import (
    CONTENT_NOTES_SOURCE_FILE_TEMPLATE,
    CONTENT_NOTES_WEB_SEARCH_TEMPLATE,
    NO_SOURCE_FILE_SYSTEM_INSTRUCTION,
    OUTLINE_NO_SOURCE_DEFAULT_SNIPPETS,
)
from app.prompts.llm_templates import build_content_prompt, build_outline_prompt

__all__ = [
    "build_outline_prompt",
    "build_content_prompt",
    "OUTLINE_NO_SOURCE_DEFAULT_SNIPPETS",
    "CONTENT_NOTES_SOURCE_FILE_TEMPLATE",
    "CONTENT_NOTES_WEB_SEARCH_TEMPLATE",
    "NO_SOURCE_FILE_SYSTEM_INSTRUCTION",
]
