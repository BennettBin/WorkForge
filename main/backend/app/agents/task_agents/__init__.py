from .code_doc_task_agent import CodeDocTaskAgent, CodeDocTaskArtifacts
from .data_analysis_task_agent import DataAnalysisTaskAgent, DataAnalysisTaskArtifacts
from .generic_task_agent import GenericTaskAgent, GenericTaskArtifacts
from .paper_assistant_task_agent import PaperAssistantTaskAgent, PaperAssistantTaskArtifacts
from .ppt_task_agent import PPTTaskAgent, PPTTaskArtifacts
from .report_task_agent import ReportTaskAgent, ReportTaskArtifacts
from .template_generation_task_agent import TemplateGenerationTaskAgent, TemplateGenerationArtifacts
from .wechat_post_task_agent import WechatPostTaskAgent, WechatPostTaskArtifacts

__all__ = [
    "PPTTaskAgent",
    "PPTTaskArtifacts",
    "ReportTaskAgent",
    "ReportTaskArtifacts",
    "WechatPostTaskAgent",
    "WechatPostTaskArtifacts",
    "DataAnalysisTaskAgent",
    "DataAnalysisTaskArtifacts",
    "GenericTaskAgent",
    "GenericTaskArtifacts",
    "CodeDocTaskAgent",
    "CodeDocTaskArtifacts",
    "PaperAssistantTaskAgent",
    "PaperAssistantTaskArtifacts",
    "TemplateGenerationTaskAgent",
    "TemplateGenerationArtifacts",
]
