from __future__ import annotations


# Called by: main/backend/app/agents/sub_agents/outline_agent.py
# Purpose: Default section seeds when no source file is uploaded.
OUTLINE_NO_SOURCE_DEFAULT_SNIPPETS = [
    "Background and motivation",
    "Core concepts",
    "Current evidence",
    "Method and approach",
    "Key findings",
    "Risks and limitations",
    "Action plan",
]


# Called by: main/backend/app/agents/sub_agents/content_agent.py
# Purpose: Notes template when content is generated from uploaded files.
CONTENT_NOTES_SOURCE_FILE_TEMPLATE = "Slide {index} speaking notes: {title}. Source-file aligned content."


# Called by: main/backend/app/agents/sub_agents/content_agent.py
# Purpose: Notes template when no source file is provided.
CONTENT_NOTES_WEB_SEARCH_TEMPLATE = "Slide {index} speaking notes: {title}. No source file. Content is organized via search and synthesis."


# Called by: main/backend/app/services/task_manager/task_service.py
# Purpose: Backend-side system instruction for no-source-file task mode.
NO_SOURCE_FILE_SYSTEM_INSTRUCTION = (
    "【系统附加指令】当前未上传参考文件。请先自行检索相关资料并总结，"
    "再基于检索结果完成回答与PPT制作。"
)
