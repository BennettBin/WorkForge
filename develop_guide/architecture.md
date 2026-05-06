# WorkForge AI 当前架构与脚本说明

## 维护规则
- 任何新增、删除、重命名、职责变更的脚本/模块，都必须同步更新本文件。
- 每次更新需写明：变更时间、变更摘要、影响范围。
- 架构说明以“当前真实实现”为准，不写规划性虚构内容。

## 架构总览（当前）
- 当前仓库已完成 MVP 最小目录骨架与步骤 6-10 基础实现（位于 `main/`）。
- 核心设计目标：
  - 前端：React + TypeScript + Vite + Ant Design
  - 后端：FastAPI
  - 桌面壳：Tauri 2
  - 任务编排：Coordinator + Task Agent + Sub Agent + Task Orchestrator
  - 存储：MVP-1 使用 JSON/Excel（后续可迁移 SQLite/PostgreSQL）

## 模块与脚本职责（当前）
- `main/backend/main.py`：后端本地启动入口（读取 `settings.host/settings.port`，默认 `127.0.0.1:8080`）。
- `main/backend/requirements.txt`：后端依赖基线。
- `main/backend/app/api/`：HTTP 接口层（任务、文件、配置、结果等 API）。
- `main/backend/app/api/app.py`：FastAPI 应用装配与生命周期注入（含默认管理员初始化与前端静态页面托管，登录入口路由为 `/Login`）。
- `main/backend/app/api/errors.py`：统一错误响应与全局异常处理。
- `main/backend/app/api/routes/health.py`：健康检查接口（`GET /WorkForge`）。
- `main/backend/app/api/routes/tasks.py`：任务创建、上传、解析、运行、状态更新、下载接口。
- `main/backend/app/api/routes/auth.py`：注册、登录、用户资料和密码更新接口。
- `main/backend/app/api/routes/providers.py`：模型 Provider 配置、列表与连通性测试接口。
- `main/backend/app/api/routes/skills.py`：Skill 列表与按任务阶段解析接口。
- `main/backend/app/api/routes/ws_tasks.py`：任务进度 WebSocket 推送接口。
- `main/backend/app/agents/coordinator/`：总控 Agent 逻辑。
- `main/backend/app/agents/coordinator/coordinator_agent.py`：阶段规划与模型决策收敛。
- `main/backend/app/agents/task_agents/`：任务级 Agent（MVP-1 先支持 PPT 任务）。
- `main/backend/app/agents/task_agents/ppt_task_agent.py`：PPT 任务代理，组织子 Agent 执行。
- `main/backend/app/agents/sub_agents/`：子任务 Agent（大纲、内容、审查等）。
- `main/backend/app/agents/sub_agents/outline_agent.py`：大纲生成。
- `main/backend/app/agents/sub_agents/content_agent.py`：页内容与备注生成。
- `main/backend/app/agents/sub_agents/review_agent.py`：质量审查。
- `main/backend/app/services/file_parser/`：多格式解析与 OCR 编排。
- `main/backend/app/services/file_parser/parser.py`：文件解析器实现（pdf/docx/doc/txt/ppt/pptx + OCR fallback）。
- `main/backend/app/services/text_processing/`：文本清洗与标准化处理。
- `main/backend/app/services/text_processing/cleaner.py`：解析文本清洗实现。
- `main/backend/app/services/llm_provider/`：在线 API / Ollama / 本地 LLM Provider 适配。
- `main/backend/app/services/llm_provider/provider_service.py`：Provider 配置与测试服务。
- `main/backend/app/services/llm_provider/provider_defaults.py`：Provider 默认配置（含 Ollama 默认 chat/embedding/base_url）。
- `main/backend/app/services/llm_runtime/`：真实 LLM 文本调用运行时。
- `main/backend/app/services/llm_runtime/text_generator.py`：按 Provider 类型执行 Ollama/OpenAI-compatible/Anthropic 请求；`huggingface` provider 通过 vLLM(OpenAI-compatible) 调用本地下载模型。
- `main/backend/app/services/vector_store/`：向量索引构建与检索。
- `main/backend/app/services/vector_store/index_service.py`：本地向量索引持久化与相似检索服务。
- `main/backend/app/services/knowledge_search/`：通用知识检索与网页信息提取。
- `main/backend/app/services/knowledge_search/search_service.py`：公网检索 + 网页文本提取服务（失败可降级）。
- `main/backend/app/services/skill_runtime/`：Skill 运行时执行器。
- `main/backend/app/services/skill_runtime/executor.py`：按 Skill 名称触发真实服务代码（含 `knowledge_search` 执行绑定）。
- `main/backend/app/services/model_router/`：模型选择与路由策略。
- `main/backend/app/services/model_router/router.py`：最小路由实现（用户默认优先，系统默认 DeepSeek）。
- `main/backend/app/services/export_engine/`：PPTX 导出与版本产物写入。
- `main/backend/app/services/export_engine/pptx_exporter.py`：真实 PPTX 导出实现（python-pptx）。
- `main/backend/app/services/task_manager/`：任务状态流转与编排入口。
- `main/backend/app/services/task_manager/task_service.py`：任务服务（创建、上传、解析、文本清洗、向量索引、需求理解、主流程编排、修订与版本管理）。
- `main/backend/app/services/skill_registry/`：Skill 检索与按需加载。
- `main/backend/app/services/skill_registry/registry.py`：Skill 元数据扫描与解析服务。
- `main/backend/app/services/auth_service.py`：认证与会话服务。
- `main/backend/app/repositories/interfaces/`：数据访问抽象接口。
- `main/backend/app/repositories/interfaces/user_repository.py`：用户接口。
- `main/backend/app/repositories/interfaces/session_repository.py`：会话接口。
- `main/backend/app/repositories/interfaces/task_event_repository.py`：任务事件接口。
- `main/backend/app/repositories/json_impl/`：MVP-1 的 JSON/Excel 存储实现。
- `main/backend/app/repositories/json_impl/store.py`：并发锁 + 原子写 + 损坏恢复。
- `main/backend/app/repositories/json_impl/repositories.py`：核心仓储 JSON 实现。
- `main/backend/app/repositories/json_impl/repositories.py`：核心仓储 JSON 实现（含 users/sessions/task_events）。
- `main/backend/app/repositories/json_impl/excel_mirror.py`：Excel 快照写入。
- `main/backend/app/models/`：核心数据模型定义。
- `main/backend/app/models/requests.py`：任务相关请求参数模型。
- `main/backend/app/utils/`：公共工具函数与通用封装。
- `main/backend/app/utils/ids.py`：统一 ID 生成工具。
- `main/backend/tests/`：后端单元测试与集成测试。
- `main/backend/tests/test_json_repositories_smoke.py`：仓储创建/查询/更新/版本冒烟测试。
- `main/backend/tests/test_task_api_flow.py`：任务 API 端到端流程测试（创建/上传/解析/运行/下载）。
- `main/backend/tests/test_model_router.py`：模型路由优先级与默认策略测试。
- `main/backend/tests/test_steps_21_30.py`：步骤 21-30 集成测试（认证、Provider、Skill、WebSocket、修订、版本管理、回归样本）。
- `main/backend/tests/test_provider_matrix.py`：Provider 多渠道配置矩阵测试（保存配置 + 连接测试）。
- `main/backend/tests/test_task_api_flow.py`：任务端到端流程测试（含搜索需求触发 `knowledge_search` Skill 的断言）。
- `main/backend/runtime_data/`：历史本地运行数据目录（由旧 `main/backend/main/` 重命名而来）。
- `main/frontend/src/pages/`：页面层（Home/TaskCreate/TaskRunning/ResultPreview/ModelSettings/History/Auth；TaskRunning 含系统/用户/LLM 实时日志窗口）。
- `main/frontend/src/components/`：复用组件层（上传、进度、结果展示等）。
- `main/frontend/src/api/`：前端 API Client 封装（默认后端地址 `http://127.0.0.1:8080`）。
- `main/frontend/src/store/`：状态管理。
- `main/frontend/src/styles/`：样式资源。
- `main/frontend/src/App.tsx`：路由与顶层布局（未登录仅允许访问认证页）。
- `main/frontend/src/main.tsx`：前端启动入口与 Provider 装配。
- `main/desktop/`：Tauri 桌面壳配置与打包相关内容。
- `main/desktop/tauri.conf.json`：Tauri 联动配置。
- `main/desktop/scripts/start-backend.ps1`：后端后台启动脚本（默认端口 `8080`，自动清理失效 pid 并等待健康检查通过）。
- `main/desktop/scripts/stop-backend.ps1`：后端后台停止脚本（读取 pid 文件后停止进程并清理 pid 文件）。
- `hi.bat`：仓库根目录一键启动后端脚本（封装调用 `main/desktop/scripts/start-backend.ps1`）。
- `bye.bat`：仓库根目录一键停止后端脚本（封装调用 `main/desktop/scripts/stop-backend.ps1`）。
- `main/storage/uploads|parsed|outputs|versions/`：原始文件、解析产物、输出文件、版本文件。
- `main/docs/`：工程内文档目录。

## 变更记录
```text
时间：
变更摘要：
影响范围：
```

- 时间：2026-05-04 16:30
  变更摘要：初始化架构文档，建立“新增/修改脚本必须同步更新”的维护规则，并给出当前目标架构与模块职责占位说明。
  影响范围：`develop_guide/architecture.md`（文档治理与架构基线）。

- 时间：2026-05-04 16:48
  变更摘要：完成步骤 3 后，更新为“目录骨架已落地”状态，并补充 `main/` 下当前模块职责说明。
  影响范围：`main/` 目录结构、`develop_guide/architecture.md`。

- 时间：2026-05-04 17:07
  变更摘要：完成步骤 6-10，新增仓储接口、JSON/Excel 适配、FastAPI 基础服务、前端基础壳与 Tauri 联动配置，并同步更新脚本职责。
  影响范围：`main/backend/*`、`main/frontend/*`、`main/desktop/*`、`develop_guide/architecture.md`。

- 时间：2026-05-04 20:13
  变更摘要：完成步骤 11-14，新增任务 API、文件上传解析链路与任务主流程编排服务，并补充端到端自动化测试。
  影响范围：`main/backend/app/api/routes/tasks.py`、`main/backend/app/services/task_manager/*`、`main/backend/app/services/file_parser/parser.py`、`main/backend/tests/*`。

- 时间：2026-05-04 20:26
  变更摘要：完成步骤 15-20，落地多 Agent 分层、模型路由、真实大纲与内容生成、质量审查拦截和真实 PPTX 导出。
  影响范围：`main/backend/app/agents/*`、`main/backend/app/services/model_router/*`、`main/backend/app/services/export_engine/*`、`main/backend/app/services/task_manager/task_service.py`、`main/backend/tests/*`。

- 时间：2026-05-04 20:58
  变更摘要：完成步骤 21-30，新增认证闭环、前端端到端页面联动、WebSocket 进度推送、Provider 配置、Skill Registry、Skill 调用审计、局部修订与版本管理。
  影响范围：`main/backend/app/api/routes/*`、`main/backend/app/services/*`、`main/backend/app/repositories/*`、`main/frontend/src/pages/*`、`main/frontend/src/api/http.ts`、`main/backend/tests/test_steps_21_30.py`。

- 时间：2026-05-04 21:49
  变更摘要：统一后端端口到 8080、健康检查状态标识改为 WorkForge、前端增加登录前页面门禁，并在后端生命周期初始化默认管理员账户（admin/123456）。
  影响范围：`main/backend/app/config.py`、`main/backend/main.py`、`main/backend/app/api/app.py`、`main/backend/app/api/routes/health.py`、`main/backend/app/services/auth_service.py`、`main/frontend/src/App.tsx`、`main/frontend/src/api/http.ts`、`main/frontend/src/pages/TaskRunning/TaskRunningPage.tsx`、`main/desktop/scripts/start-backend.ps1`、`develop_guide/process.md`。

- 时间：2026-05-04 21:57
  变更摘要：清理旧前端端口配置并统一为 8080；健康检查访问入口由 `/health` 统一为 `/WorkForge`。
  影响范围：`main/backend/app/api/routes/health.py`、`main/backend/app/api/app.py`、`main/frontend/vite.config.ts`、`main/desktop/tauri.conf.json`、`develop_guide/backend_service_baseline.md`、`develop_guide/full_check_report.md`、`develop_guide/process.md`。

- 时间：2026-05-04 22:04
  变更摘要：修复 `http://127.0.0.1:8080/auth` 返回 404 问题，后端新增前端页面托管路由；修复后端停止脚本的 PID 保留变量冲突。
  影响范围：`main/backend/app/api/app.py`、`main/desktop/scripts/stop-backend.ps1`、`develop_guide/process.md`。

- 时间：2026-05-04 22:08
  变更摘要：将系统登录页路由从 `/auth` 统一改为 `/Login`，同步前端未登录跳转与后端页面托管入口。
  影响范围：`main/frontend/src/App.tsx`、`main/backend/app/api/app.py`、`develop_guide/process.md`。

- 时间：2026-05-05 16:10
  变更摘要：将 `main/backend/main/` 重命名为 `main/backend/runtime_data/`，消除与上级 `main/` 名称重复导致的歧义。
  影响范围：`main/backend/runtime_data/*`、`develop_guide/architecture.md`、`develop_guide/process.md`。

- 时间：2026-05-05 16:18
  变更摘要：增强后端启动脚本的容错能力，自动处理脏 PID 文件并在启动后执行 `/WorkForge` 健康检查，避免“PID 文件存在但服务未运行”导致无法进入页面。
  影响范围：`main/desktop/scripts/start-backend.ps1`、`develop_guide/process.md`、`develop_guide/architecture.md`。

- 时间：2026-05-05 16:30
  变更摘要：升级 Model Settings 为多 Provider 配置面板（Deepseek/OpenAI/Anthropic/Qwen/Ollama/Hugging Face/本地 LLM），新增按渠道动态必填项提示；后端扩展 Provider 类型与字段，并将系统默认模型路由改为 Ollama（qwen3:8b）。
  影响范围：`main/frontend/src/pages/ModelSettings/ModelSettingsPage.tsx`、`main/backend/app/models/{requests,entities}.py`、`main/backend/app/services/llm_provider/{provider_service,provider_defaults.py,__init__.py}`、`main/backend/app/services/model_router/router.py`、`main/backend/tests/test_model_router.py`、`develop_guide/process.md`。

- 时间：2026-05-05 16:35
  变更摘要：新增 Provider 矩阵回归测试，逐一验证 Deepseek/OpenAI/Anthropic/Qwen/Ollama/Hugging Face/本地 LLM 的保存与测试连接路径可用。
  影响范围：`main/backend/tests/test_provider_matrix.py`、`develop_guide/process.md`、`develop_guide/architecture.md`。

- 时间：2026-05-05 16:49
  变更摘要：实现通用知识检索 Skill 与网页信息提取服务，并在 PPT 生成主流程接入“文本清洗 -> 向量索引 -> 需求理解 -> 大纲 -> 按需检索知识 -> 逐页内容生成 -> 审查 -> 导出”链路。
  影响范围：`main/backend/app/services/{text_processing,vector_store,knowledge_search}/*`、`main/backend/app/skills/common/knowledge_search.skill`、`main/backend/app/agents/{coordinator,sub_agents,task_agents}/*`、`main/backend/app/services/task_manager/task_service.py`、`develop_guide/process.md`。

- 时间：2026-05-05 16:59
  变更摘要：补全 Skill 声明到执行代码的硬绑定链路：`knowledge_search.skill` 增加 `runtime_handler` 与触发关键词，`SkillExecutor` 统一执行入口由 TaskService 显式触发，并新增测试验证“用户提出搜索需求 -> 触发 Skill -> 记录 SkillCall”。
  影响范围：`main/backend/app/skills/common/knowledge_search.skill`、`main/backend/app/services/{skill_runtime,skill_registry}/*`、`main/backend/app/services/task_manager/task_service.py`、`main/backend/app/agents/task_agents/ppt_task_agent.py`、`main/backend/tests/test_task_api_flow.py`、`develop_guide/process.md`。

- 时间：2026-05-05 17:17
  变更摘要：修复“未实际调用 LLM”和“完成后找不到输出文件”问题：生成阶段接入真实 LLM runtime 调用（含失败后回退）、导出后增加文件存在性强校验，并将 `settings.data_dir` 固化为项目级 `main/storage` 绝对路径；同时修复停止脚本在 pid 不存在时的删除异常。
  影响范围：`main/backend/app/services/llm_runtime/*`、`main/backend/app/agents/sub_agents/{outline_agent,content_agent}.py`、`main/backend/app/agents/task_agents/ppt_task_agent.py`、`main/backend/app/services/task_manager/task_service.py`、`main/backend/app/config.py`、`main/desktop/scripts/stop-backend.ps1`、`develop_guide/process.md`。
- Time: 2026-05-05 17:39
  Change Summary: Hardened PPTX output retrieval and download flow. Added binary download endpoints in task routes (`/v1/tasks/{task_id}/download/latest/file`, `/v1/tasks/{task_id}/download/{version}/file`) and added legacy-to-current storage path resolution so historical outputs saved under old roots can still be located. Updated frontend ResultPreview to support one-click file download instead of path-only display.
  Impact Scope: `main/backend/app/api/routes/tasks.py`, `main/frontend/src/pages/ResultPreview/ResultPreviewPage.tsx`, `main/frontend/src/api/http.ts`.
  Notes: TaskService skill registry path was switched to absolute app path (`main/backend/app/services/task_manager/task_service.py`) to avoid cwd-dependent skill discovery failures.
- Time: 2026-05-05 18:02
  Change Summary: Implemented task-scoped vector cache lifecycle. File vectorization now happens at parse time (instead of run time), and web search results are automatically vectorized and appended into the same task cache for downstream outline/content generation and later revisions. Added manual cache clear API and frontend action.
  Impact Scope: `main/backend/app/services/task_manager/task_service.py`, `main/backend/app/services/vector_store/index_service.py`, `main/backend/app/api/routes/tasks.py`, `main/frontend/src/pages/ResultPreview/ResultPreviewPage.tsx`, `main/backend/tests/test_task_api_flow.py`.
  Notes: Vector cache is retained after task completion and can be explicitly cleared by user via `POST /v1/tasks/{task_id}/cache/clear`.
- Time: 2026-05-05 18:14
  Change Summary: Added no-source-file execution path and image placeholder rendering path for PPT generation. When task has no uploaded source file, orchestration now continues with search-driven content synthesis instead of failing. Content pipeline now emits `image_placeholders` per slide; export engine reserves a dedicated image box and prints placeholder label/source in-slide for manual user insertion.
  Impact Scope: `main/backend/app/services/task_manager/task_service.py`, `main/backend/app/agents/task_agents/ppt_task_agent.py`, `main/backend/app/agents/sub_agents/{outline_agent.py,content_agent.py,review_agent.py}`, `main/backend/app/services/export_engine/pptx_exporter.py`, `main/backend/tests/test_task_api_flow.py`.
  Notes: Placeholder layout applies to content slides that carry non-empty `image_placeholders`; cover/normal slides remain unchanged.
- Time: 2026-05-05 18:18
  Change Summary: Hardened backend stop script against pid-file race conditions.
  Impact Scope: `main/desktop/scripts/stop-backend.ps1`.
  Notes: PID removal now ignores transient file-not-found on removal to prevent false stop failures.
- Time: 2026-05-05 20:55
  Change Summary: Updated Task Create frontend flow to make source file optional.
  Impact Scope: `main/frontend/src/pages/TaskCreate/TaskCreatePage.tsx`.
  Notes: Task creation now conditionally executes upload/parse only when a file is selected; otherwise it directly triggers run for no-source-file agent flow.
- Time: 2026-05-05 20:59
  Change Summary: Added port-occupancy cleanup in backend lifecycle scripts to prevent stale process routing.
  Impact Scope: `main/desktop/scripts/start-backend.ps1`, `main/desktop/scripts/stop-backend.ps1`.
  Notes: Scripts now stop existing listener on port `8080` before launching/while stopping, ensuring requests hit the latest backend code path.
- Time: 2026-05-05 21:12
  Change Summary: Added centralized prompt registry under `main/backend/app/prompts/` and moved all active LLM/agent prompt text used by current generation flow into prompt templates.
  Impact Scope: `main/backend/app/prompts/{__init__.py,llm_templates.py,agent_templates.py,README.md}`, `main/backend/app/agents/sub_agents/{outline_agent.py,content_agent.py}`.
  Notes: Prompt comments now include caller script path and functional purpose for direct editing/auditing.
- Time: 2026-05-05 21:48
  Change Summary: Added LLM debug enforcement in task run flow. `POST /v1/tasks/{task_id}/run` now accepts `require_llm` and `llm_timeout_seconds`. When `require_llm=true`, generation is marked failed unless at least one LLM invocation succeeds. Added explicit LLM call start/success/failure events and `llm_debug` payload in run result for diagnostics.
  Impact Scope: `main/backend/app/models/requests.py`, `main/backend/app/api/routes/tasks.py`, `main/backend/app/services/task_manager/task_service.py`, `main/backend/tests/test_task_api_flow.py`.
  Notes: Default LLM timeout is runtime-configured per request/provider and currently falls back to `90s` when no provider timeout is configured (previously `12s`, before that fixed `3s`).
- Time: 2026-05-05 22:10
  Change Summary: Hardened provider-type routing and LLM invocation prechecks. `LLMTextGenerator.generate` now normalizes `provider_type` and uses explicit routing sets (Ollama/Anthropic/HuggingFace/OpenAI-compatible family) instead of implicit catch-all. `run_task` inner `llm_generate` now validates provider/model/prompt fields and normalizes base_url/api_key before invocation.
  Impact Scope: `main/backend/app/services/llm_runtime/text_generator.py`, `main/backend/app/services/task_manager/task_service.py`.
  Notes: This change prevents silent misrouting caused by provider type case/alias mismatch and surfaces invalid generation decisions earlier.
- Time: 2026-05-05 23:06
  Change Summary: Reworked vectorization runtime to support Ollama embeddings with task-scoped configurable settings and default fallback. Vector index now attempts Ollama `embedding_model` (default `qwen3-embedding:8b`) and persists vectorizer metadata into index payload. Task service now constructs vector runtime config from user default provider (Ollama base_url/embedding_model/timeout/api_key), otherwise falls back to system Ollama defaults. Added one-time Ollama-unavailable short-circuit to avoid repeated timeout penalties and preserve MVP stability via lexical fallback.
  Impact Scope: `main/backend/app/services/vector_store/index_service.py`, `main/backend/app/services/task_manager/task_service.py`, `main/backend/tests/test_task_api_flow.py`.
  Notes: Added real Ollama connectivity check in provider test API (`/api/tags`) to expose unreachable host/model-not-found diagnostics (`main/backend/app/services/llm_provider/provider_service.py`, `main/backend/tests/test_provider_matrix.py`).
- Time: 2026-05-06 00:29
  Change Summary: Unified model defaults across frontend presets and backend provider backfill: default chat model is `qwen3:8b`, default embedding model is `qwen3-embedding:8b`.
  Impact Scope: `main/frontend/src/pages/ModelSettings/ModelSettingsPage.tsx`, `main/backend/app/services/llm_provider/provider_service.py`.
  Notes: Existing saved provider records are not force-migrated; new saves/upserts use the unified defaults.
- Time: 2026-05-06 13:53
  Change Summary: Added repository-root quick commands for backend lifecycle: `hi.bat` to start backend and `bye.bat` to stop backend, both wrapping existing PowerShell scripts.
  Impact Scope: `hi.bat`, `bye.bat`, `develop_guide/architecture.md`, `develop_guide/process.md`.
  Notes: These wrappers keep operation entry simple while reusing existing health-check and pid-handling logic in PowerShell scripts.
- Time: 2026-05-06 14:22
  Change Summary: Updated `huggingface` provider call path to vLLM(OpenAI-compatible) and added TaskRunning real-time conversation panel (system/user/LLM input-output stream with hover full text and history accumulation).
  Impact Scope: `main/backend/app/services/llm_runtime/text_generator.py`, `main/backend/app/models/requests.py`, `main/backend/app/services/task_manager/task_service.py`, `main/backend/app/api/routes/ws_tasks.py`, `main/frontend/src/pages/ModelSettings/ModelSettingsPage.tsx`, `main/frontend/src/pages/TaskRunning/TaskRunningPage.tsx`, `main/backend/tests/test_{provider_matrix,llm_runtime_routing}.py`, `develop_guide/process.md`.
  Notes: WebSocket payload now includes incremental `new_skill_calls` and task snapshot for frontend live-log rendering.
- Time: 2026-05-06 14:31
  Change Summary: Moved no-source-file system instruction from frontend hardcode to backend prompt constant and applied it in task orchestration runtime when no source file is attached.
  Impact Scope: `main/backend/app/prompts/{agent_templates.py,__init__.py}`, `main/backend/app/services/task_manager/task_service.py`, `main/frontend/src/pages/TaskCreate/TaskCreatePage.tsx`, `develop_guide/process.md`.
  Notes: TaskCreate now submits raw user requirement; backend injects the instruction centrally for planning and generation.
- Time: 2026-05-06 15:19
  Change Summary: Removed unused `decisions` argument from `PPTTaskAgent.execute` and cleaned call sites in task orchestration to avoid dead parameters and confusion about LLM invocation path.
  Impact Scope: `main/backend/app/agents/task_agents/ppt_task_agent.py`, `main/backend/app/services/task_manager/task_service.py`, `develop_guide/process.md`.
  Notes: Model decisions remain consumed in `TaskService.llm_generate` closure; execution behavior unchanged.
- Time: 2026-05-06 20:15
  Change Summary: Reworked revision endpoint pipeline (`POST /v1/tasks/{task_id}/revisions`) from immediate deterministic edit to LLM-driven revision orchestration. The revision flow now: reads cached prior slide deck JSON (`*.slides.json`), targets requested page, gathers context from original requirement + parsed file text + vector retrieval + optional web search, invokes LLM for structured revised slide JSON, runs `ReviewAgent` on full deck, then exports next version PPT.
  Impact Scope: `main/backend/app/services/task_manager/task_service.py`, `main/backend/tests/test_steps_21_30.py`, `develop_guide/process.md`.
  Notes: Revision stage now emits auditable runtime traces (`llm_call_start/succeeded/failed`, `llm_text_generation`, `knowledge_search`, `failed_review`) so frontend TaskRunning/Result flows can verify LLM participation.
- Time: 2026-05-06 21:10
  Change Summary: Extended revision and export architecture in two areas: (1) `RevisionRequest.page_index` changed to optional; if missing, revision pipeline performs LLM-based slide targeting and supports multi-slide updates in one request. (2) Export engine now supports style-template application by loading a matched template from `main/backend/app/templates/ppt`, clearing template sample slides, and rendering output slides with template theme/layout defaults.
  Impact Scope: `main/backend/app/models/requests.py`, `main/backend/app/services/task_manager/task_service.py`, `main/backend/app/services/export_engine/pptx_exporter.py`, `main/frontend/src/pages/{ResultPreview,TaskCreate}/`, `main/backend/tests/test_steps_21_30.py`, `develop_guide/process.md`.
  Notes: Template matching is fuzzy by style-name normalization and token overlap; one best template is selected per export (run/revision/rollback).
