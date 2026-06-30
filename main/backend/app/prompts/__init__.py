from app.prompts.agent_templates import (
    CONTENT_NOTES_SOURCE_FILE_TEMPLATE,
    CONTENT_NOTES_WEB_SEARCH_TEMPLATE,
    NO_SOURCE_FILE_SYSTEM_INSTRUCTION,
    OUTLINE_NO_SOURCE_DEFAULT_SNIPPETS,
)
from app.prompts.agent_system_prompts import (
    BaseAgentSystemPrompt,
    CodeDocTaskAgentSystemPrompt,
    CoordinatorAgentSystemPrompt,
    DataAnalysisTaskAgentSystemPrompt,
    GenericTaskAgentSystemPrompt,
    PPTTaskAgentSystemPrompt,
    PaperAssistantTaskAgentSystemPrompt,
    ReportTaskAgentSystemPrompt,
    SkillDirective,
    TemplateGenerationTaskAgentSystemPrompt,
    TextTaskAgentSystemPrompt,
    WechatPostTaskAgentSystemPrompt,
)
from app.prompts.llm_templates import build_content_prompt, build_outline_prompt

__all__ = [
    "SkillDirective",
    "BaseAgentSystemPrompt",
    "CoordinatorAgentSystemPrompt",
    "TextTaskAgentSystemPrompt",
    "CodeDocTaskAgentSystemPrompt",
    "DataAnalysisTaskAgentSystemPrompt",
    "ReportTaskAgentSystemPrompt",
    "WechatPostTaskAgentSystemPrompt",
    "PaperAssistantTaskAgentSystemPrompt",
    "GenericTaskAgentSystemPrompt",
    "PPTTaskAgentSystemPrompt",
    "TemplateGenerationTaskAgentSystemPrompt",
    "build_outline_prompt",
    "build_content_prompt",
    "OUTLINE_NO_SOURCE_DEFAULT_SNIPPETS",
    "CONTENT_NOTES_SOURCE_FILE_TEMPLATE",
    "CONTENT_NOTES_WEB_SEARCH_TEMPLATE",
    "NO_SOURCE_FILE_SYSTEM_INSTRUCTION",
]
