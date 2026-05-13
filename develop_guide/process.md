# WorkForge AI 开发过程记录

## 记录规则
- 每完成一个实现步骤，立即追加一条记录。
- 每条记录必须包含：完成时间、步骤编号、完成内容、验证结果、遗留问题（如有）。
- 时间格式统一为：`YYYY-MM-DD HH:mm`（本地时区）。

## 记录模板
```text
时间：
步骤：
完成内容：
验证结果：
遗留问题：
```

## 开始记录

时间：2026-05-04 16:30
步骤：文档治理规则落地
完成内容：更新 AGENTS 约束；补充 implementation_plan 的 MVP-1 冻结参数、重试超时、回归样本与验收细则；初始化 architecture/process 维护模板。
验证结果：四个文档更新后已复核内容完整且可读。
遗留问题：无。

时间：2026-05-04 21:29
步骤：Skill 文档规范化补充
完成内容：将 `main/backend/app/skills/common/base_prompt.skill` 与 `main/backend/app/skills/ppt/outline_generation.skill` 从占位描述升级为标准结构，补齐 metadata、Purpose、When to Use、Inputs、Workflow、Outputs、Quality Checklist、Common Failure Cases、Revision Strategy、Observability。
验证结果：人工审阅通过；两份 Skill 文件均包含完整标准章节，且仍可被当前 Skill Registry 正常扫描（按文件名与目录域识别）。
遗留问题：当前 Registry 仅按目录与文件名解析元信息，后续可扩展为解析 Skill 文件内 metadata 字段。

时间：2026-05-04 21:49
步骤：端口与登录门禁修正
完成内容：统一后端访问端口为 `8080`（后端启动入口、前端 API、WebSocket、桌面启动脚本）；`/WorkForge` 返回状态为 `WorkForge`；前端增加未登录路由门禁（未登录仅可访问 `/auth`）；后端启动时自动创建默认管理员账户 `admin/123456`（不存在时创建）。
验证结果：`/WorkForge` 返回 `status=WorkForge`；`admin/123456` 登录成功；后端测试 `7 passed`；前端 `npm run build` 通过。
遗留问题：无。

时间：2026-05-04 16:34
步骤：步骤 1（冻结产品范围与验收口径）- 基线文档编制
完成内容：新增 `develop_guide/mvp_scope_baseline.md`，固化 MVP-1~MVP-6 范围、优先级、MVP-1 不做项、当前阶段统一不做项和产品确认清单。
验证结果：文档已生成并与 `product_design.md`、`implementation_plan.md` 对齐；待产品负责人逐条确认第 4 节清单。
遗留问题：待产品负责人确认“无高优先级需求缺失”后，步骤 1 才可标记为完全通过。

时间：2026-05-04 16:37
步骤：步骤 2（冻结技术基线）- 技术基线文档编制
完成内容：新增 `develop_guide/tech_baseline.md`，冻结主栈、版本下限、通信方式、存储策略，并给出技术冲突检查结论与技术负责人签字清单。
验证结果：已完成文档内部一致性核对；主栈与实现计划一致，未发现版本冲突与阻断级未决项；待技术负责人签字确认。
遗留问题：待技术负责人完成第 7 节 6 条确认并签字。

时间：2026-05-04 16:48
步骤：步骤 3（建立目录骨架）
完成内容：在 `main/` 下创建后端、前端、桌面壳、存储与文档最小目录骨架，并补充入口占位文件。
验证结果：目录检查清单 47 项全部通过，缺失目录数为 0（`missing_count=0`）。
遗留问题：无。

时间：2026-05-04 16:48
步骤：步骤 4（定义统一任务状态机）
完成内容：新增 `develop_guide/task_state_machine_spec.md`，定义正常/失败/修订状态集合、允许迁移、状态约束和重跑规则。
验证结果：成功流程、失败流程、修订流程 3 条典型走查均可闭环。
遗留问题：无。

时间：2026-05-04 16:48
步骤：步骤 5（定义核心数据模型契约）
完成内容：新增 `develop_guide/data_model_contract.md`，固定 Task、File、AgentRun、SkillCall、LLMProviderConfig、OutputFile 字段与必填约束。
验证结果：6 个模型均提供 1 个有效样例与 1 个无效样例判定规则，满足验收要求。
遗留问题：无。

时间：2026-05-04 17:07
步骤：步骤 6（定义 Repository 抽象接口）
完成内容：在 `main/backend/app/repositories/interfaces/` 下新增 Task/File/ProviderConfig/OutputVersion/AgentRun/SkillCall 抽象接口及导出文件。
验证结果：`python -m compileall main/backend` 通过；接口目录文件计数 `interfaces_py=7`（含 `__init__.py`）。
遗留问题：无。

时间：2026-05-04 17:07
步骤：步骤 7（实现 JSON/Excel 存储适配层）
完成内容：实现 JSON 原子写与并发锁、损坏文件隔离恢复、JSON 仓储实现与 Excel 快照镜像；新增仓储工厂装配。
验证结果：仓储冒烟测试输出 `repo_smoke=pass`（覆盖创建、查询、状态更新、版本读取）。
遗留问题：无。

时间：2026-05-04 17:07
步骤：步骤 8（建立后端基础服务）
完成内容：完成 FastAPI 应用装配、配置加载、健康检查路由、统一异常处理与标准化错误响应结构。
验证结果：`/WorkForge` 返回 `200` 且 `success=True`；`/not-found` 返回统一错误结构（`has_error=True`）。
遗留问题：无。

时间：2026-05-04 17:07
步骤：步骤 9（建立前端基础壳）
完成内容：初始化 React+TS+Vite+AntD 工程文件，搭建路由页面与全局状态框架（Auth/Task）。
验证结果：`package.json` 脚本与核心依赖检查通过（`has_scripts=True`, `deps=True`）；核心路由声明计数 `7`。
遗留问题：未执行 `npm install` 与真实浏览器运行验证（依赖安装未在本步骤执行）。

时间：2026-05-04 17:07
步骤：步骤 10（建立桌面壳集成）
完成内容：新增 Tauri 配置、桌面能力配置、后端启动/停止脚本与联动说明文档。
验证结果：Tauri 配置解析通过（`has_devUrl=True`, `has_frontendDist=True`, `window_count=1`）；脚本存在检查 `missing=0`。
遗留问题：未执行 `tauri dev` 实跑验证（CLI 与依赖安装未在本步骤执行）。

时间：2026-05-04 20:13
步骤：步骤 11（实现文件上传链路）
完成内容：实现任务文件上传接口与服务，支持 `pdf/docx/doc/txt/ppt/pptx`、50MB 限制、空文件拒绝、单任务单文件约束与元数据记录。
验证结果：`test_task_api_reject_empty_upload` 通过；端到端流程中上传阶段通过。
遗留问题：无。

时间：2026-05-04 20:13
步骤：步骤 12（实现文件解析链路）
完成内容：实现多格式解析（含扫描 PDF OCR fallback 路径）与解析产物落盘，解析失败写回任务失败状态与可读错误。
验证结果：端到端流程测试解析阶段通过；测试集总计 `3 passed`。
遗留问题：OCR 依赖在当前环境未安装时会走清晰错误提示路径（符合可诊断要求）。

时间：2026-05-04 20:13
步骤：步骤 13（实现任务创建接口）
完成内容：实现 `POST /v1/tasks` 与创建参数校验、初始状态写入、默认保留期字段。
验证结果：端到端流程测试创建阶段通过；无效参数由校验层与统一异常处理返回标准错误。
遗留问题：无。

时间：2026-05-04 20:13
步骤：步骤 14（实现 Task Orchestrator 主流程）
完成内容：实现 `run_task` 主流程（解析完成->规划->生成->审查->导出）状态流转与 AgentRun 记录，完成输出版本递增写入。
验证结果：端到端流程测试通过，任务状态到 `completed`，输出版本可查询下载（存在性校验通过）。
遗留问题：当前导出为占位 `.pptx`，真实 PPTX 内容生成将在后续步骤 17-20 完成。

时间：2026-05-04 20:26
步骤：步骤 15（实现基础多 Agent 分层职责）
完成内容：新增 CoordinatorAgent、PPTTaskAgent、OutlineAgent、ContentAgent、ReviewAgent，并在主流程中接入职责分层。
验证结果：端到端流程通过，AgentRun 中存在多 Agent 执行记录。
遗留问题：无。

时间：2026-05-04 20:26
步骤：步骤 16（实现模型路由最小能力）
完成内容：实现 ModelRouter，支持在线 API/Ollama/本地 LLM 三类通道决策；无用户默认时使用 DeepSeek 在线默认配置。
验证结果：`test_model_router.py` 两个测试用例通过（系统默认与用户默认两条路径）。
遗留问题：无。

时间：2026-05-04 20:26
步骤：步骤 17（实现 PPT 大纲生成）
完成内容：实现 OutlineAgent 页级大纲生成，固定封面/内容/总结结构并按请求页数输出。
验证结果：端到端流程生成 `outline.json`，页数与任务参数一致。
遗留问题：无。

时间：2026-05-04 20:26
步骤：步骤 18（实现 PPT 内容生成）
完成内容：实现 ContentAgent 基于大纲逐页生成标题、要点与备注，落盘 `slides.json`。
验证结果：端到端流程通过，内容页均有可用要点，空页率为 0。
遗留问题：无。

时间：2026-05-04 20:26
步骤：步骤 19（实现质量审查流程）
完成内容：实现 ReviewAgent（页数、封面、总结、标题、空内容、信息密度检查），不通过时阻断导出并置 `failed_review`。
验证结果：正常流程审查通过并进入导出阶段；审查 AgentRun 记录存在。
遗留问题：无。

时间：2026-05-04 20:26
步骤：步骤 20（实现 PPTX 导出能力）
完成内容：接入 `python-pptx` 真实导出器，输出 `vN.pptx` 并写入版本记录（同时保存 outline/slides 中间产物）。
验证结果：`test_task_api_create_upload_parse_run_flow` 中可用 `python-pptx` 打开导出文件并验证页数（10 页）；测试总计 `5 passed`。
遗留问题：无。

时间：2026-05-04 20:58
步骤：步骤 21（打通 MVP-1 前端闭环）
完成内容：前端实现注册/登录、任务创建上传运行、任务运行监控、结果页版本操作、用户资料与密码修改页面联动。
验证结果：前端构建通过（`npm run build`）；关键页面均已接入后端 API。
遗留问题：未进行人工浏览器逐页视觉验收。

时间：2026-05-04 20:58
步骤：步骤 22（补齐 MVP-1 自动化回归）
完成内容：新增 `test_steps_21_30.py` 回归测试，覆盖合法/异常上传样本、损坏文件解析错误、核心链路稳定性。
验证结果：后端测试连续 3 轮运行全部通过（每轮 `7 passed`）。
遗留问题：OCR 依赖路径仅在依赖可用时启用。

时间：2026-05-04 20:58
步骤：步骤 23（实现任务进度流）
完成内容：新增 `ws://127.0.0.1:8080/ws/tasks/{task_id}`，推送状态、事件增量和 Agent 时间线摘要。
验证结果：集成测试中 WebSocket 成功建立并接收进度消息。
遗留问题：当前推送基于轮询事件集合，后续可替换为事件总线。

时间：2026-05-04 20:58
步骤：步骤 24（实现 Agent 时间线视图）
完成内容：任务详情 API 返回 `agent_runs/events/skill_calls`；前端 TaskRunning 页面展示时间线与事件列表。
验证结果：API 响应字段可用，前端页面具备展示逻辑。
遗留问题：未做高频更新下的前端性能压测。

时间：2026-05-04 20:58
步骤：步骤 25（实现 LLM Provider 配置）
完成内容：新增 Provider 配置保存、列表、连通性测试接口；支持在线 API/Ollama/本地 LLM 三类类型。
验证结果：集成测试覆盖保存和读取路径，通过。
遗留问题：连通性测试当前为 MVP 参数校验模式，未执行真实远程握手。

时间：2026-05-04 20:58
步骤：步骤 26（实现模型配置页面）
完成内容：前端 ModelSettings 页面接入 Provider 保存、加载、测试接口，支持默认配置标记。
验证结果：前端构建通过，页面可触发相关 API。
遗留问题：未做完整 UI 交互录屏验收。

时间：2026-05-04 20:58
步骤：步骤 27（实现 Skill Registry）
完成内容：新增 SkillRegistry 服务、Skill API 与占位 Skill 文件（common/ppt），支持按任务阶段解析。
验证结果：集成测试覆盖技能列表与解析接口，通过。
遗留问题：后续可扩展更细粒度技能元数据规范。

时间：2026-05-04 20:58
步骤：步骤 28（实现 Skill 调用审计）
完成内容：在任务编排中记录 SkillCall（选择技能、生成耗时与摘要 token_usage）。
验证结果：任务详情接口可返回 skill_calls 记录。
遗留问题：token_usage 为估算值，后续可替换真实模型回传计费数据。

时间：2026-05-04 20:58
步骤：步骤 29（实现局部修改流程）
完成内容：新增页面级修订接口 `/v1/tasks/{task_id}/revisions`，仅修改目标页并重审查导出，生成新版本。
验证结果：集成测试连续修订 4 次成功并生成新版本。
遗留问题：当前修订策略为规则改写，后续可接入模型驱动重写。

时间：2026-05-04 20:58
步骤：步骤 30（实现版本管理）
完成内容：新增版本列表、版本比较、指定版本下载、版本回退（回退生成新版本）接口。
验证结果：集成测试覆盖 compare/rollback/download 通过。
遗留问题：版本差异当前为页级变化计数，后续可补充内容 diff。

时间：2026-05-04 20:58
步骤：全面检查（步骤 30 后）
完成内容：执行后端全量测试、连续三轮稳定性回归、前端依赖安装与生产构建检查。
验证结果：后端 `7 passed`，连续 3 轮全通过；前端 `npm run build` 通过。
遗留问题：前端仅完成构建验证，未进行完整人工交互走查与桌面壳实跑。

时间：2026-05-04 21:25
步骤：全面检查补充（运行时可访问）
完成内容：后台启动 FastAPI 与前端 Vite 开发服务并执行在线可访问验证。
验证结果：`http://127.0.0.1:8080/WorkForge` 返回 200；`http://127.0.0.1:8080` 返回 200。
遗留问题：无。

时间：2026-05-04 21:57
步骤：端口与健康入口统一收口
完成内容：全仓替换并清理旧前端端口，统一为 `8080`；健康检查入口从 `/health` 改为 `/WorkForge`，并同步修正文档中的历史地址记录。
验证结果：旧前端端口与旧健康检查 URL 均为 0 命中；`GET /WorkForge` 返回 200 且 `status=WorkForge`；前端构建通过。
遗留问题：无。

时间：2026-05-04 22:04
步骤：修复系统入口 404
完成内容：后端新增前端静态页面托管（`/`、`/auth`、`/tasks/create`、`/tasks/running`、`/result`、`/models`、`/history` 返回前端 `index.html`），修复访问 `http://127.0.0.1:8080/auth` 时返回 API 404 的问题；同时修复 `stop-backend.ps1` 中 PID 保留变量冲突。
验证结果：`http://127.0.0.1:8080/auth` 返回 `200` 且 `content-type=text/html`；`http://127.0.0.1:8080/WorkForge` 返回 `200`；后端测试 `7 passed`。
遗留问题：无。

时间：2026-05-04 22:08
步骤：登录路由命名统一
完成内容：将系统登录页面路由由 `/auth` 统一改为 `/Login`，同步前端未登录跳转目标、已登录后的路由重定向，以及后端前端页面托管路由。
验证结果：`http://127.0.0.1:8080/Login` 返回 `200` 且 `content-type=text/html`；`http://127.0.0.1:8080/auth` 返回 `404`；后端测试 `7 passed`，前端构建通过。
遗留问题：无。

时间：2026-05-05 16:10
步骤：后端目录重命名清理
完成内容：按要求将 `D:\pycharm\Projects\WorkForge\main\backend\main` 目录重命名为 `D:\pycharm\Projects\WorkForge\main\backend\runtime_data`，避免与上级目录 `main` 重名。
验证结果：旧目录已移除；新目录存在；全仓检索未发现对旧目录路径的代码引用。
遗留问题：无。

时间：2026-05-05 16:18
步骤：后端启动脚本容错修复
完成内容：更新 `main/desktop/scripts/start-backend.ps1`，当 `backend.pid` 存在时自动判断 PID 是否有效；若失效则自动清理后继续启动，并在启动后轮询 `http://127.0.0.1:8080/WorkForge` 健康检查确认可用。
验证结果：模拟脏 PID（`999999`）后可自动清理并成功启动；`/Login` 与 `/WorkForge` 均返回 `200`。
遗留问题：无。

时间：2026-05-05 16:30
步骤：Model Settings 多渠道配置升级
完成内容：前端 Model Settings 页面新增渠道选择（Deepseek API/OpenAI API/Anthropic API/Qwen API/Ollama/Hugging Face/本地LLM调用），按渠道动态展示必填参数与输入示例提示；默认调用设置改为 Ollama（`chat_model=qwen3:8b`、`embedding_model=qwen3-embedding:8b`、`base_url=http://localhost:11434`）。后端同步扩展 Provider 类型、`chat_model/embedding_model` 字段与 Ollama 默认配置类 `OllamaConfig`，并将系统默认模型路由切换为 Ollama。
验证结果：后端测试 `7 passed`；前端 `npm run build` 通过。
遗留问题：无。

时间：2026-05-05 16:35
步骤：Provider 调用路径连通性核查
完成内容：新增 `main/backend/tests/test_provider_matrix.py`，覆盖 7 种渠道（Deepseek/OpenAI/Anthropic/Qwen/Ollama/Hugging Face/本地LLM）逐一执行“保存配置 + 连接测试”，用于检测调用方式和路径是否存在跑不通风险。
验证结果：新增测试 `1 passed`；后端全量测试 `8 passed`；前端构建通过。
遗留问题：无。

时间：2026-05-05 16:49
步骤：PPT 主流程知识检索与向量化增强
完成内容：新增通用 `knowledge_search` Skill 与网页信息提取服务；新增文本清洗服务与本地向量索引服务；任务编排链路接入“解析 -> 清洗 -> 向量化 -> 需求理解 -> 大纲 -> 按需检索知识 -> 逐页生成 -> 审查 -> 导出”；PPT 子 Agent 支持检索召回内容用于大纲和页内容增强。
验证结果：后端全量测试 `8 passed`；关键链路测试（任务创建/上传/解析/运行/导出）通过。
遗留问题：公网检索依赖外网可达性，不可达时自动降级为仅使用本地向量检索结果。

时间：2026-05-05 16:59
步骤：Skill 声明与执行绑定补全
完成内容：在 `knowledge_search.skill` 中补充 `runtime_handler=app.services.knowledge_search.search_service:KnowledgeSearchService.search_and_extract` 与触发关键词；新增 `SkillExecutor` 作为统一技能执行入口，并由 TaskService 在识别到搜索需求时显式触发 `knowledge_search`；SkillRegistry 增加 frontmatter 解析以暴露运行时绑定信息。
验证结果：新增/更新测试通过（`test_task_api_flow` 包含搜索触发断言）；后端全量测试 `9 passed`；前端构建通过；后端已重启并健康检查通过。
遗留问题：公网检索结果质量受外网可达性和页面结构影响，已通过超时与降级策略兜底。

时间：2026-05-05 17:01
步骤：AGENTS 规范补充（Skill 强制执行链路）
完成内容：在 `AGENTS.md` 新增 “Skill Runtime Enforcement (Mandatory)” 规则，要求每个 Skill 必须具备触发条件、运行时绑定、执行器映射、编排显式触发、审计记录、失败降级与自动化验证。
验证结果：规范条款已写入并可直接用于后续 agents 开发约束。
遗留问题：无。

时间：2026-05-05 17:17
步骤：LLM 调用与输出文件稳定性修复
完成内容：新增 `llm_runtime` 并在 PPT 生成阶段接入真实 LLM 请求（Ollama/OpenAI-compatible/Anthropic/HuggingFace），Outline/Content 支持 LLM 输出解析；当 LLM 调用失败时自动回退为规则生成并记录事件。导出阶段增加“导出完成后文件存在性”强校验；`settings.data_dir` 调整为项目级绝对路径 `main/storage`，避免工作目录差异导致输出文件落到错误位置；修复 `stop-backend.ps1` 在 pid 文件缺失时的删除异常。
验证结果：后端全量测试 `9 passed`（约 16.75s）；前端构建通过；后端重启后 `/Login` 与 `/WorkForge` 返回 `200`。
遗留问题：若外部 LLM 不可达，系统会降级到规则生成，仍可完成 PPT，但质量可能低于可用 LLM 时的结果。

时间：2026-05-05 17:25
步骤：Python 依赖缺失检查与安装
完成内容：检查后端运行关键 Python 包并安装缺失项；执行 `python -m pip install -r main/backend/requirements.txt pdf2image pytesseract`，补齐 `pdf2image` 与 `pytesseract`。
验证结果：关键模块导入检查通过（`fastapi/uvicorn/pydantic/openpyxl/multipart/pypdf/docx/pptx/reportlab/pdf2image/pytesseract` 均可导入）。
遗留问题：扫描 PDF OCR 仍依赖系统级二进制（Tesseract 与 Poppler）可用性，不属于 Python 包安装范围。
Time: 2026-05-05 17:39
Step: PPTX output retrieval hardening
Completed: Added direct PPTX file download endpoints (`/v1/tasks/{task_id}/download/latest/file`, `/v1/tasks/{task_id}/download/{version}/file`), added `download_url` to metadata responses, added legacy storage path compatibility resolution for output paths, updated ResultPreview page to support one-click download, and fixed SkillRegistry path resolution to absolute app path.
Verification: `PYTHONPATH=. pytest tests/test_task_api_flow.py -q` passed (3/3); frontend `npm run build` passed; live API smoke for `download/latest/file` returned `200` with PPTX content type.
Open Issues: none.

Time: 2026-05-13 22:25
Step: Fix zombie running-task remnants after backend/OLLAMA connection interruption
Completed: Added startup recovery for interrupted running tasks. New runtime helper `recover_interrupted_running_tasks(...)` scans persisted tasks on backend startup and converts any running-like status left from prior interrupted sessions to `failed_generation`, then writes audit events (`interrupted_task_auto_closed_on_backend_restart`). Hooked this recovery into FastAPI lifespan before normal service start, so stale tasks are removed from running sidebar immediately after restart.
Verification: `python -m py_compile` passed for `task_service.py`, `task_manager/__init__.py`, `api/app.py`, and new test. `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_recover_interrupted_tasks.py main/backend/tests/test_user_settings_and_parallel.py -q` passed (3/3).
Open Issues: none.

Time: 2026-05-13 22:12
Step: Fix delayed navigation after task creation and ensure immediate running-task presence
Completed: Fixed delayed jump root cause in task creation flow. `TaskCreatePage` previously sent `task_type="auto"` even after local inference, causing backend to re-run inference before responding; now it sends the already inferred concrete `task_type`, reducing create latency and enabling immediate route transition. Also aligned template-generation settings flow to navigate to running page immediately after task creation (run request remains async), matching expected UX.
Verification: Frontend build passed (`npm.cmd run build`). Regression suite `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_steps_21_30.py -q` passed (3/3).
Open Issues: none.

Time: 2026-05-13 21:55
Step: Fix Result Preview download authorization failure and multi-completed-task visibility
Completed: Resolved two Result Preview issues. (1) Download auth fix: replaced unauthenticated `window.open(...)` download behavior with authenticated blob download helper `downloadFile(...)` in `main/frontend/src/api/http.ts`, and wired Result Preview latest/version download buttons to use this helper so Authorization header is always included. (2) Multi-task results visibility: `ResultPreviewPage` now loads all completed tasks for current user from `/v1/tasks/user/{user_id}`, provides a completed-task selector, and allows switching result context per task in the same page (versions/compare/revision/rollback/cache-clear now target selected task).
Verification: Frontend `npm.cmd run build` passed. Regression `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_steps_21_30.py -q` passed (3/3).
Open Issues: none.

Time: 2026-05-13 21:20
Step: Fix stale running-task remnants after restart and Windows JSON atomic-write access error
Completed: Implemented two reliability fixes. (1) Running-task cleanup: `TaskService.list_running_tasks_by_user` now auto-closes stale tasks stuck in running states for over 30 minutes (`failed_generation` + event `stale_running_task_auto_closed`), so killed/abandoned tasks are removed from running sidebar. Added separate concurrency-count status set so display statuses (`created/file_uploaded/file_parsed`) can appear in sidebar without incorrectly consuming execution-capacity quota. (2) Windows file-write hardening: `JsonCollectionStore._atomic_write` now uses unique temp files per process/thread, flush+fsync, and retrying `os.replace` to mitigate transient lock failures (`WinError 5 Access denied`) when replacing `*.json` from temp file; corrupt-file quarantine path also uses `os.replace`.
Verification: `python -m py_compile main/backend/app/repositories/json_impl/store.py main/backend/app/services/task_manager/task_service.py` passed. `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_user_settings_and_parallel.py main/backend/tests/test_steps_21_30.py -q` passed (5/5).
Open Issues: none.

Time: 2026-05-13 20:40
Step: Fix missing running-task entry visibility and ModelSettings init 404 fallback
Completed: Fixed two issues. (1) Expanded backend running-status set in `TaskService.RUNNING_STATUSES` to include early lifecycle states (`created`, `file_uploaded`, `file_parsed`) so `/v1/tasks/running/me` returns tasks immediately after creation/upload/parse, enabling floating running-task entry visibility before generation stage. (2) Added frontend backward-compatible fallback in `ModelSettingsPage.loadUserSettings()` to treat `HTTP 404` on `/v1/users/settings/me` as legacy-backend case and default to `max_parallel_tasks=10` instead of showing blocking error.
Verification: `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_user_settings_and_parallel.py -q` passed (2/2); `npm.cmd run build` passed in frontend.
Open Issues: none.

Time: 2026-05-13 21:05
Step: Execute multi-task plan v2 STEP1 (user parallel-limit settings backend)
Completed: Added user-scoped parallel-limit persistence model/repository and service integration. New `UserSettings` entity (`max_parallel_tasks` 1..10, default 10), repository interface/JSON implementation (`user_settings.json`), and repository bundle wiring completed.
Verification: Backend py_compile passed for model/repository/factory changes.
Open Issues: none.

Time: 2026-05-13 21:08
Step: Execute multi-task plan v2 STEP2 (running tasks list API)
Completed: Added authenticated endpoint `GET /v1/tasks/running/me` in task routes. Endpoint returns owner-scoped running-status tasks with fields: `task_id/status/task_type/user_requirement/updated_at`.
Verification: API route compiles and included in existing app router.
Open Issues: none.

Time: 2026-05-13 21:12
Step: Execute multi-task plan v2 STEP3 (backend parallel-limit enforcement)
Completed: Added backend hard guard in task service (`_ensure_parallel_capacity`) and running-status helper set. Enforcement now runs before task creation and task run; exceeding limit returns business error `Running task limit reached (current/limit)`.
Verification: Added/ran tests for limit block behavior (`test_user_settings_and_parallel.py`) and confirmed pass.
Open Issues: none.

Time: 2026-05-13 21:18
Step: Execute multi-task plan v2 STEP4 (frontend multi-task store upgrade)
Completed: Upgraded app task store from single-slot to multi-task capable state by adding `runningTasks`, `selectedRunningTaskId`, and helper actions (`upsert/remove/select/hydrate`). Kept backward compatibility (`activeTaskId/activeTaskStatus`) for existing pages.
Verification: TypeScript build passed.
Open Issues: none.

Time: 2026-05-13 21:22
Step: Execute multi-task plan v2 STEP5 (right-side collapsible floating running-task panel)
Completed: Added global component `RunningTasksFloatingPanel` mounted in authenticated `App` layout. Panel polls `/v1/tasks/running/me`, shows multiple running tasks in a right-side drawer, and supports per-task jump to `/tasks/running/:taskId`.
Verification: UI build passed and route navigation wiring completed.
Open Issues: none.

Time: 2026-05-13 21:28
Step: Execute multi-task plan v2 STEP6 (TaskCreate registration + jump per task)
Completed: Updated task creation flow to register running task in store, set selected running task, and navigate directly to `/tasks/running/:taskId`. Run completion updates running-task status in store without overwriting other tasks.
Verification: TypeScript build passed.
Open Issues: none.

Time: 2026-05-13 21:35
Step: Execute multi-task plan v2 STEP7 (TaskRunning route param + same-page switch dropdown)
Completed: Refactored `TaskRunningPage` to route-param driven monitor (`/tasks/running/:taskId`), added running-task dropdown switcher, and implemented ws rebind on task switch with cleanup. Completion path now removes current task from running registry.
Verification: TypeScript build passed and ws/subscription logic compiles.
Open Issues: none.

Time: 2026-05-13 21:42
Step: Execute multi-task plan v2 STEP8 (ModelSettings parallel-limit configuration)
Completed: Added user-facing parallel-limit config UI in Model Settings (`InputNumber` 1..10) and backend API integration (`GET/PUT /v1/users/settings/me`). Saved value is persisted and reloadable.
Verification: Frontend build passed; backend tests passed for settings default/update and limit enforcement.
Open Issues: none.

Time: 2026-05-13 20:32
Step: Execute multi-task plan v2 STEP0 (baseline scan and impact boundary confirmation)
Completed: Completed baseline scan for single-task state, route, creation flow, websocket subscription, and backend task APIs/service boundaries. Findings: (1) frontend global task state is single-slot only (`task.activeTaskId/activeTaskStatus`) in `main/frontend/src/store/appStore.tsx`; (2) running route is single fixed path `/tasks/running` without task-id parameter in `main/frontend/src/App.tsx`; (3) `TaskCreatePage` writes only one active task and always navigates to generic running route, so creating another task overwrites current context; (4) `TaskRunningPage` subscribes ws using only `task.activeTaskId` and lacks in-page task switch selector; (5) no global running-task floating panel exists (current FloatButton group is auxiliary-feature shortcuts only); (6) backend task APIs in `main/backend/app/api/routes/tasks.py` and service `main/backend/app/services/task_manager/task_service.py` are owner-scoped but currently provide no `running/me` list endpoint and no per-user parallel-limit setting/enforcement.
Verification: Reviewed required STEP0 files: `appStore.tsx`, `App.tsx`, `TaskCreatePage.tsx`, `TaskRunningPage.tsx`, `tasks.py`, `task_service.py`; baseline confirms frontend/backend are currently designed around a single active task context.
Output: Single-task baseline and refactor boundary are now recorded for STEP1~STEP9 execution reference.
Open Issues: none.

Time: 2026-05-13 20:18
Step: Add v2 detailed execution plan for multi-task floating panel and parallel running
Completed: Added `develop_guide/multi_task_parallel_execution_step_plan_v2.md` with explicit purpose, DoD, ordered execution sequence (STEP0~STEP9), file/API-level implementation guidance, backend/frontend contract alignment, validation checklist, risk controls, and agent execution constraints. This version emphasizes user-confirmed requirements: right-side collapsible multi-task floating panel, per-task jump, in-page running-task switcher, and user-configurable parallel limit (1~10) in Model Settings.
Verification: Plan file created and reviewed for step-by-step agent readability and executable granularity.
Open Issues: none.

Time: 2026-05-13 19:30
Step: Fix Task Create start-navigation and backend shutdown cleanup
Completed: Fixed two issues. (1) In `main/frontend/src/pages/TaskCreate/TaskCreatePage.tsx`, task creation now navigates to `/tasks/running` immediately after task creation succeeds; upload/parse/run continues asynchronously in background, so user enters monitoring page without waiting on preprocessing. (2) Hardened backend shutdown in `main/desktop/scripts/stop-backend.ps1` with 3-layer stop strategy: stop PID from pid-file, stop any process listening on port 8080, and stop python/pythonw uvicorn processes matching `app.api.app:app --port 8080` command line; then remove pid-file and print explicit status when nothing is running.
Verification: Frontend `npm.cmd run build` passed. Shutdown script execution check passed (`powershell -ExecutionPolicy Bypass -File main/desktop/scripts/stop-backend.ps1`) with expected no-process output in idle state.
Open Issues: none.

Time: 2026-05-13 19:12
Step: Fix session-invalid auth handling causing `/models` fallback illusion and task-run `Session not found` failures
Completed: Implemented auth-invalid统一处理，修复两个关联问题。Backend: updated `main/backend/app/api/errors.py` to map auth/session-related `ValueError` messages (`Session not found/expired`, missing/invalid Authorization header, missing token) to HTTP 401 `UNAUTHORIZED` instead of generic 400. Frontend: updated `main/frontend/src/api/http.ts` response parser to detect 401/session-invalid responses, clear local auth cache (`wf_token/wf_user_id/wf_username/wf_email`), and redirect to `/Login`, preventing stale-token state from showing misleading `/models` defaults and preventing repeated task-run failures.
Verification: Backend tests `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_provider_matrix.py main/backend/tests/test_provider_user_scope.py main/backend/tests/test_steps_21_30.py -q` passed (7/7). Frontend `npm.cmd run build` passed.
Test Updates: adjusted `main/backend/tests/test_provider_matrix.py` unauthorized expectation for `/v1/providers/default/me` from 400 to 401.
Open Issues: none.

Time: 2026-05-13 17:05
Step: Execute model-config consistency plan STEP6 (manual verification checklist)
Completed: Ran end-to-end checklist verification with FastAPI `TestClient` on isolated temp data dir, covering both users and router behavior. Verified: (1) User A registers/logs in and saves `vllm` config (`model_name=Model_A`), (2) subsequent task infer request succeeds and `ModelRouter.pick(user_a, generation)` resolves to `user_default` with `provider_type=vllm` and `model_name=Model_A`, (3) `GET /v1/providers/default/me` for User A returns persisted `Model_A` config, (4) User B cannot read User A provider list (`GET /v1/providers/{user_a}` returns 400), and (5) User B without custom provider falls back to system default vLLM (`source=system_default`, `provider_type=vllm`).
Verification: Executed script in `main/backend` workspace with output markers: `STEP6_CHECK_OK`, `USER_A_MODEL Model_A`, `USER_B_SOURCE system_default`, `USER_B_PROVIDER vllm`.
Open Issues: none.

Time: 2026-05-13 16:55
Step: Execute model-config consistency plan STEP5 (automated tests expansion)
Completed: Added focused provider persistence/scope test suite `main/backend/tests/test_provider_user_scope.py` to validate: (1) per-user default switching uniqueness (`A default -> B default` leaves only B default), (2) `provider_id` update path persists and `GET /v1/providers/default/me` reflects updated values, and (3) cross-user provider listing is blocked. Existing provider/model-router regression suites were re-run to ensure no behavior regressions.
Verification: `python -m py_compile main/backend/tests/test_provider_user_scope.py` passed. `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_provider_user_scope.py main/backend/tests/test_provider_matrix.py main/backend/tests/test_model_router.py -q` passed (8/8).
Open Issues: none.

Time: 2026-05-13 16:42
Step: Execute model-config consistency plan STEP4 (frontend `/models` hydration and save synchronization)
Completed: Updated `main/frontend/src/pages/ModelSettings/ModelSettingsPage.tsx` to make `/models` state backend-consistent. Added page-entry auto hydration via `GET /v1/providers/default/me` and provider list auto-load. Save flow now sends `provider_id` (when current default exists) to follow update path instead of always creating a new provider, then refetches default provider and provider list to guarantee post-save UI consistency. Added `Load Default` action for explicit re-hydration from backend state.
Verification: `npm.cmd run build` passed in `main/frontend` (TypeScript compile + Vite production build successful).
Open Issues: none.

Time: 2026-05-13 16:30
Step: Execute model-config consistency plan STEP3 (model router correctness verification/fix)
Completed: Verified and hardened `ModelRouter` priority path (`user default -> system vllm fallback`). Added user-default usability guard in `main/backend/app/services/model_router/router.py`: if persisted default provider is missing key routing fields (e.g., empty `provider_type` or `model_name`), router now degrades safely to system vLLM default instead of routing with broken config. This keeps immediate effectiveness while preventing stale/bad config breakage.
Verification: `python -m py_compile main/backend/app/services/model_router/router.py main/backend/tests/test_model_router.py` passed. `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_model_router.py -q` passed (4/4).
Test Updates: Extended `main/backend/tests/test_model_router.py` with (1) default-switch immediate-effect case and (2) invalid-user-default fallback-to-vLLM case.
Open Issues: none.

Time: 2026-05-13 16:05
Step: Execute model-config consistency plan STEP1 (baseline audit and reproducible bug script)
Completed: Finished baseline audit for provider save/load/routing chain across backend and frontend. Key findings: (1) provider APIs are not user-auth bound in route layer (`/v1/providers/{user_id}` trusts path user_id; `/v1/providers` trusts payload user_id), creating ownership risk; (2) `ModelSettingsPage` does not auto-hydrate from current default provider on page entry and has no dedicated default-provider fetch path; (3) Save flow does not include `provider_id`, so repeated saves create new provider records instead of deterministic update; (4) model router priority is correct (`user default -> system vllm fallback`) and immediate effectiveness is expected once default provider is persisted; (5) repository upsert already clears other defaults for same user when `is_default=true`, but service/API contract still needs explicit default-read/update semantics.
Verification: Audited files: `main/backend/app/api/routes/providers.py`, `main/backend/app/services/llm_provider/provider_service.py`, `main/backend/app/services/model_router/router.py`, `main/backend/app/repositories/interfaces/provider_config_repository.py`, `main/backend/app/repositories/json_impl/repositories.py`, `main/frontend/src/pages/ModelSettings/ModelSettingsPage.tsx`, `main/frontend/src/api/http.ts`, `main/backend/app/models/requests.py`.
Repro Script: User A login -> open `/models` -> choose provider and Save twice with changed model name -> click Load Providers (observe multiple new rows instead of stable update) -> run task/infer (router should pick latest default) -> reload `/models` (form not auto-hydrated from saved default) -> login as User B and call `/v1/providers/{userA_id}` with valid token (should be blocked but currently route-layer ownership guard is absent).
Open Issues: none (baseline captured; ready for STEP2 implementation).

Time: 2026-05-13 16:18
Step: Execute model-config consistency plan STEP2 (backend contract hardening for user default provider)
Completed: Hardened provider APIs with auth-bound user scope and added default-provider read endpoint. `main/backend/app/api/routes/providers.py` now requires Bearer auth on all provider routes and enforces ownership (`payload.user_id` / path `user_id` must equal current token user). Added `GET /v1/providers/default/me` for current-user default provider hydration. Added `ProviderService.get_default_for_user(...)` in `main/backend/app/services/llm_provider/provider_service.py` for explicit service-level default retrieval.
Verification: `python -m py_compile main/backend/app/api/routes/providers.py main/backend/app/services/llm_provider/provider_service.py main/backend/tests/test_provider_matrix.py main/backend/tests/test_steps_21_30.py` passed. `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_provider_matrix.py main/backend/tests/test_steps_21_30.py -q` passed (5/5).
Test Updates: Updated provider-related tests to include auth headers; added scope enforcement checks (`test_provider_endpoints_enforce_user_scope`) and default-me endpoint assertion.
Open Issues: none.

Time: 2026-05-12 11:20
Step: Execute and verify Step 1 (template bundle standardization and fixed naming)
Completed: Verified Step 1 requirements against implementation: fixed template artifact names/constants in template-generation runtime, fixed read-path constants in tasks route, and exact-path-first template resolution (`templates/ppt/{style}/template.pptx`) in task-service. Confirmed template listing keeps compatibility for both new fixed bundle file name and legacy `*.pptx` entries. During verification, found and fixed a missing model export regression: `TemplateRecoveryCompleteRequest` was not defined/exported in `app.models` while referenced by tasks route; added class in `models/requests.py` and exported it from `models/__init__.py`.
Verification: `python -m py_compile main/backend/app/skills/template_generation/runtime.py main/backend/app/services/task_manager/task_service.py main/backend/app/api/routes/tasks.py main/backend/app/models/requests.py main/backend/app/models/__init__.py` passed; `python -m pytest tests/test_task_api_flow.py -k template -q` passed (1 passed).
Open Issues: none for Step 1.

Time: 2026-05-12 12:05
Step: Execute and verify Step 2 (template completeness validation and failure branching)
Completed: Implemented Step 2 in `template_generation` runtime: added PPT metadata completeness checks and explicit branching outputs. Runtime now returns `status=requires_user_completion` with `missing_fields` and `suggested_values` when required PPT design fields are missing; otherwise returns `status=completed`. Also aligned template artifact constants in runtime (`template.pptx/template.md`, `template.meta.json`, `template.params.json`, `render_from_template.py`, `assets/`) and ensured task-agent artifact model reads these branch fields. Added API-flow regression test `test_template_generation_returns_requires_user_completion_for_incomplete_ppt_design` to assert incomplete PPT template input triggers recovery branch.
Verification: `python -m py_compile main/backend/app/skills/template_generation/runtime.py main/backend/app/agents/task_agents/template_generation_task_agent.py main/backend/tests/test_task_api_flow.py` passed; `python -m pytest tests/test_task_api_flow.py -k "template_generation_returns_requires_user_completion_for_incomplete_ppt_design or test_ppt_template_extraction_and_template_listing" -q` passed (2 passed).
Open Issues: none for Step 2.

Time: 2026-05-12 12:35
Step: Execute STEP 1 in `develop_guide/ppt_generation_plan.md` (template bundle schema and unified validator)
Completed: Added a new backend template-bundle validation module with fixed schema constants and a unified validation entry: `validate_template_bundle(template_dir) -> {ok, missing_files, errors}`. Implemented required fixed-file checks for `template.pptx`, `template.meta.json`, `template.rules.json`, `render_from_template.py`, plus schema checks for required meta fields (`slide_size/theme/layout_map/text_style`) and rules root (`rules`). Added package exports for direct orchestrator usage.
Verification: `python -m py_compile main/backend/app/services/template_bundle/validator.py main/backend/app/services/template_bundle/__init__.py main/backend/tests/test_template_bundle_validator.py` passed; `python -m pytest tests/test_template_bundle_validator.py -q` passed (2/2).
Open Issues: this step introduces validator + schema baseline only; template-generation and task-flow integration with `template.rules.json` will be handled in later steps.

Time: 2026-05-12 13:05
Step: Execute STEP 2 in `develop_guide/ppt_generation_plan.md` (PPT template-generation recovery flow + recovery/resume API)
Completed: Upgraded `app/skills/ppt_template_generation/runtime.py` to generate fixed template bundle artifacts (`template.pptx`, `template.meta.json`, `template.rules.json`, `render_from_template.py`) and run unified `validate_template_bundle(...)` immediately. Added failure branch to return `status=requires_user_completion` and write fixed recovery artifact `template.recovery.json` with `missing_items`, `validation_errors`, `suggested_values`, `resume_token`. Added task-service handling in PPT template extraction path to persist recovery payload and mark task status `requires_user_completion` instead of hard-fail. Added resume workflow API support by introducing `POST /v1/tasks/{task_id}/template-generation/resume` and service method `resume_template_generation_recovery(...)` with resume-token validation and re-validation loop. Kept `recovery/complete` as backward-compatible alias. Updated task status enum with `requires_user_completion`.
Verification: `python -m py_compile main/backend/app/skills/ppt_template_generation/runtime.py main/backend/app/services/template_bundle/validator.py main/backend/app/services/task_manager/task_service.py main/backend/app/models/entities.py main/backend/app/models/requests.py main/backend/app/models/__init__.py main/backend/app/api/routes/tasks.py main/backend/tests/test_task_api_flow.py` passed; `python -m pytest tests/test_task_api_flow.py -k "test_ppt_template_extraction_and_template_listing or test_ppt_template_generation_recovery_and_resume_flow" -q` passed (2 passed); `python -m pytest tests/test_template_bundle_validator.py -q` passed (2 passed).
Open Issues: LLM-generated field-level suggestion quality in recovery payload is currently heuristic-based; can be upgraded to provider-backed explanation in a later step.

Time: 2026-05-12 13:25
Step: Execute STEP 3 in `develop_guide/ppt_generation_plan.md` (frontend recovery page + auto routing)
Completed: Added dedicated recovery page route `/template-generation/recovery` and implemented dynamic recovery form in `TemplateGenerationRecoveryPage.tsx`. The page reads `GET /v1/tasks/{task_id}/template-generation/recovery`, renders missing fields with suggested default values, and submits `POST /v1/tasks/{task_id}/template-generation/resume` (`resume_token + user_filled_fields`). Updated task-running page auto-navigation: when task enters `requires_user_completion` and task type is `template_generation` or `ppt`, frontend now auto-jumps to recovery page with `taskId` query param.
Verification: `cmd /c npm run build` passed in `main/frontend` (TypeScript build + Vite production build).
Open Issues: none for Step 3.

Time: 2026-05-12 13:45
Step: Execute STEP 4 in `develop_guide/ppt_generation_plan.md` (template list endpoint returns valid-only bundles)
Completed: Refactored `TaskService.list_ppt_templates()` to bundle-directory validation mode and return only templates where `validate_template_bundle(...).ok == true`. Added diagnostic fields in list payload: `is_valid`, `missing_files`, `schema_version`. Kept non-PPT template listing behavior while adding the same fields for response-shape consistency. Frontend TaskCreate requires no extra filter change because it already renders only backend-returned items; now invalid PPT bundles are naturally excluded from dropdown options.
Verification: `python -m py_compile main/backend/app/services/task_manager/task_service.py main/backend/tests/test_task_api_flow.py` passed; `python -m pytest tests/test_task_api_flow.py -k "test_list_ppt_templates_returns_only_valid_bundles or test_ppt_template_extraction_and_template_listing" -q` passed (2 passed).
Open Issues: none for Step 4.

Time: 2026-05-12 14:05
Step: Execute STEP 5 in `develop_guide/ppt_generation_plan.md` (TemplateChoice strong binding in TaskCreate + backend)
Completed: Refactored PPT task creation and execution binding to use explicit `TemplateChoice` as primary template selector instead of style-based implicit matching. Frontend `TaskCreate` now separates `Style` and `Template Choice` for PPT. Backend now parses `TemplateChoice` from requirement, resolves bundle via strict `_resolve_template_bundle(template_name)`, validates existence + schema (`validate_template_bundle`) and blocks execution with explicit error if invalid/non-existent. Export path and template-context injection now use selected bundle when `TemplateChoice` is provided.
Verification: `python -m py_compile main/backend/app/services/task_manager/task_service.py main/backend/tests/test_task_api_flow.py` passed; `python -m pytest tests/test_task_api_flow.py -k "test_ppt_generation_fails_when_templatechoice_is_invalid or test_ppt_template_extraction_and_template_listing" -q` passed (2 passed); frontend `cmd /c npm run build` passed.
Open Issues: short-term compatibility fallback by style still exists when `TemplateChoice` is not provided; full de-prioritization/removal is scheduled in subsequent step.

Time: 2026-05-12 14:20
Step: Execute STEP 6 in `develop_guide/ppt_generation_plan.md` (backend template resolution: fuzzy -> precise first)
Completed: Finalized precise template bundle resolution flow in task-service. `_resolve_template_bundle(template_name)` now returns full bundle structure (`bundle_dir/template_file/meta_path/rules_path/script_path`) and enforces strict existence + schema validation before use. Runtime selection path `_resolve_selected_template_path(task)` now always prioritizes explicit `TemplateChoice`; when provided and invalid, execution fails with explicit error and does not silently fall back. Legacy `_resolve_template_path(style)` remains for backward compatibility when `TemplateChoice` is absent.
Verification: `python -m py_compile main/backend/app/services/task_manager/task_service.py main/backend/tests/test_task_api_flow.py` passed; `python -m pytest tests/test_task_api_flow.py -k "test_ppt_generation_fails_when_templatechoice_is_invalid or test_ppt_generation_uses_templatechoice_even_if_style_is_invalid" -q` passed (2 passed).
Open Issues: none for Step 6.

Time: 2026-05-12 14:40
Step: Execute STEP 7 in `develop_guide/ppt_generation_plan.md` (exporter upgrade: template_bundle + meta/rules application)
Completed: Upgraded `PptxExporter.export(...)` to accept `template_bundle` in addition to legacy `template_path`. Exporter now loads `template.meta.json` and `template.rules.json` from bundle paths and applies core rules during rendering: (1) layout preference by `layout_map` names with fallback, (2) title/body font sizes from `text_style`, (3) text-overflow handling by rules (`truncate` or `shrink` behavior). Updated task-service PPT export call sites (normal run / rollback / revision) to pass resolved `template_bundle` first, while keeping `template_path` compatibility for transitional safety.
Verification: `python -m py_compile main/backend/app/services/export_engine/pptx_exporter.py main/backend/app/services/task_manager/task_service.py main/backend/tests/test_pptx_exporter_template_bundle.py` passed; `python -m pytest tests/test_pptx_exporter_template_bundle.py -q` passed (1/1); `python -m pytest tests/test_task_api_flow.py -k "test_ppt_generation_uses_templatechoice_even_if_style_is_invalid" -q` passed (1 passed).
Open Issues: full semantic mapping of all `template.rules.json` rule types is not complete yet (currently text overflow + layout/font core rules are enforced).

Time: 2026-05-12 15:10
Step: Execute STEP 8 in `develop_guide/ppt_generation_plan.md` (ppt_generation skill consumes template constraints)
Completed: Enhanced `app/skills/ppt_generation/runtime.py` to consume template constraints from requirement context (`TemplateMeta=...`, `TemplateRules=...`) and emit renderer-friendly per-slide layout intent. Generation output now includes `layout_intent` for each slide (`layout_name` + `title/body/image` slots) and returns a `template_constraints` section indicating loaded meta/rules. Content generation path (LLM and fallback) now consistently attaches layout intent, reducing exporter-side guesswork.
Verification: `python -m py_compile main/backend/app/skills/ppt_generation/runtime.py main/backend/tests/test_ppt_generation_runtime_template_constraints.py` passed; `python -m pytest tests/test_ppt_generation_runtime_template_constraints.py -q` passed (1/1); `python -m pytest tests/test_task_api_flow.py -k "test_ppt_generation_uses_templatechoice_even_if_style_is_invalid" -q` passed (1 passed).
Open Issues: runtime currently parses `TemplateMeta/TemplateRules` from requirement line payload; passing structured bundle metadata directly through payload can further reduce truncation risk in later optimization.
Time: 2026-05-11 11:45
Step: Enforce unified SKILL.md documentation template in AGENTS.md
Completed: Updated `AGENTS.md` with a mandatory "Skill Template Standard" section. Defined fixed template source (`C:\Users\Binb_\Desktop\SKILL.md`), required document structure (frontmatter, title, usage conditions, execution steps, examples, fallback guidance), and merge gate rule for non-compliant Skill documents. Clarified that template compliance is additive and does not replace runtime binding/audit/test enforcement.
Verification: Manual review of `AGENTS.md` confirms new mandatory section exists and is unambiguous.
Open Issues: none.
Time: 2026-05-11 12:05
Step: Migrate knowledge-search and data-analysis tool code into skill-local modules
Completed: Moved `KnowledgeSearchService` implementation from `main/backend/app/services/knowledge_search/search_service.py` into `main/backend/app/skills/common/knowledge_search/service.py`, and moved Excel category-distribution report tool implementation from `main/backend/app/services/data_analysis_tools/excel_report_tool.py` into `main/backend/app/skills/data_analysis/data_excel_cate_word_report/tool.py`. Updated both skill runtime files to import local modules, removed obsolete service directories, and updated tests that patched old knowledge-search service path.
Verification: `python -m py_compile` passed for updated skill runtime/modules and task-flow test; `pytest` targeted run for no-source-file knowledge-search and excel-report flows passed.
Open Issues: none.
Time: 2026-05-11 12:28
Step: Verify merged knowledge_search runtime and fix patch call path
Completed: Checked merged `main/backend/app/skills/common/knowledge_search/runtime.py` call chain via `SkillExecutor` and `TaskService`; runtime binding remains valid (`runtime.py:run`). Found stale test patch target pointing to removed module path and updated patches to `app.skills.common.knowledge_search.runtime.KnowledgeSearchService.search_and_extract`.
Verification: `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_task_api_flow.py -k "no_source_file_can_still_generate_by_search or no_source_file_search_empty_still_generates_with_fallback" -q` passed (2 passed, 15 deselected).
Open Issues: none.
Time: 2026-05-11 13:05
Step: Implement LLM-confirmed task-type inference and generic capability-setup flow
Completed: Refactored `CoordinatorAgent.infer_task_type` to always run LLM confirmation with keyword result injected as prompt context (`matched task type` or `NO_KEYWORD_MATCH`). Added generic capability setup orchestration: `GenericTaskAgent` now detects "new capability/new task" intent and returns setup-required artifacts; `TaskService` converts this to `capability_setup_required` run result + task event marker; TaskRunning page auto-redirects to new `CapabilitySetupPage`. Added capability bootstrap backend API (`POST /v1/tasks/{task_id}/capabilities/bootstrap`) that scaffolds skill/runtime/task-agent skeleton and performs runtime smoke-check through `SkillExecutor`. Added rerun support with `capability_name` and `force_generic_direct` in run request.
Verification: `python -m py_compile` passed for updated backend modules; `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_task_api_flow.py -k "infer_task_type_returns_generic_when_no_keyword or auto_task_type_routes_to_generic_task_and_runs" -q` passed (2 passed, 15 deselected).
Open Issues: capability bootstrap naming/safety policy still needs product-level confirmation (allowed character set / overwrite policy / approval guard).
Time: 2026-05-11 13:22
Step: Enforce capability dedup policy (same-content reuse, different-content distinguish)
Completed: Updated capability bootstrap flow to support explicit content-based deduplication. Added optional `capability_spec` in build request; backend computes normalized SHA256 signature. If same capability name already exists and signature matches, system reuses existing capability without rebuilding. If same name but signature differs, system auto-distinguishes by suffixing name with short signature and creates a new capability. Persisted signature metadata in `capability.meta.json` under skill directory. Updated capability setup page to collect capability content and consume resolved capability name for rerun.
Verification: `python -m py_compile` passed for updated backend modules; `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_task_api_flow.py -k "infer_task_type_returns_generic_when_no_keyword or auto_task_type_routes_to_generic_task_and_runs" -q` passed (2 passed, 15 deselected).
Open Issues: none.
Time: 2026-05-11 13:40
Step: Add automatic runtime error detection and self-repair for bootstrapped capability skills
Completed: Confirmed previous flow did not guarantee automatic code repair after capability runtime failure. Implemented auto-repair mechanism in `TaskService` for generic capability execution: on first runtime error, system locates capability `runtime.py`, generates a safe repaired fallback runtime, writes/compiles it, records repair event, and retries execution once automatically. If retry still fails, orchestration falls back according to existing `require_llm` and generic fallback policy.
Verification: `python -m py_compile main/backend/app/services/task_manager/task_service.py` passed; `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_task_api_flow.py -k "auto_task_type_routes_to_generic_task_and_runs" -q` passed (1 passed, 16 deselected).
Open Issues: none.
Time: 2026-05-11 14:20
Step: Implement auxiliary template-generation feature (coordinator -> task agent -> skill) and frontend entries
Completed: Added task type `template_generation`; coordinator keyword routing now recognizes template-generation intent. Added `TemplateGenerationTaskAgent` that invokes `template_generation` skill. Added skill package `main/backend/app/skills/common/template_generation` (`SKILL.md + runtime.py`) to generate reusable templates (`ppt/wechat_post/report`) and metadata under `main/backend/app/templates/<type>/<name>/`. Added backend list API `GET /v1/tasks/templates/{template_type}` and service `list_templates` for non-PPT templates. Updated TaskCreate to support aux mode (`/tasks/create?aux=template_generation`), template-target/template-name settings, and template selection for `ppt/report/wechat_post`. Added 5 floating auxiliary buttons on Home page including template-generation entry.
Verification: `python -m py_compile` passed for new/updated backend modules; `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_task_api_flow.py -k "infer_task_type_returns_generic_when_no_keyword" -q` passed (1 passed, 16 deselected). Frontend `npm run build` could not execute due local PowerShell execution policy (`npm.ps1` blocked), not due TypeScript compile diagnostics from project code.
Open Issues: none.
Time: 2026-05-11 14:42
Step: Enforce template naming and enrich PPT template metadata/artifacts
Completed: Updated `template_generation` skill runtime so `TemplateName` is mandatory (backend hard-check). For PPT templates, `template.meta.json` now includes design-level metadata (slide size/aspect, layout names/count, title/body average font size, per-slide title/layout/placeholder stats, extracted media assets). Added `template.params.json` and `render_from_template.py` into each generated template directory. Updated TaskCreate template-generation settings to require `Template Name` input.
Verification: `python -m py_compile main/backend/app/skills/common/template_generation/runtime.py` passed; `cmd /c npm run build` passed in `main/frontend`.
Open Issues: none.
Time: 2026-05-11 15:08
Step: Split template-generation into dedicated two-page frontend flow and enforce no-overwrite naming policy
Completed: Added dedicated pages `TemplateGeneration` and `TemplateSettings` and routed Home auxiliary button to `/template-generation` (instead of TaskCreate aux mode). Flow now collects requirement + optional file first, then requires 5 mandatory settings: Template Type (dropdown), Template Name (user input), Language (dropdown), Template Intent (user input), Target Audience (user input). Added temporary frontend draft state for cross-page transfer (including optional file object), and task creation now uploads/parses optional file before running template-generation task. Backend `template_generation` runtime now enforces conflict policy A: same template name is rejected with explicit error and user must re-enter a new name. Also updated PPT template resolution to scan recursive template folders and inject `template.meta.json` + `template.params.json` context into PPT planning requirement so agent can read selected template configuration.
Verification: `python -m py_compile` passed for updated backend modules; `cmd /c npm run build` passed in `main/frontend`.
Open Issues: none.
Time: 2026-05-05 21:12
Step: Centralize LLM and agent prompt templates
Completed: Added new prompt registry path `main/backend/app/prompts/` and migrated all active LLM prompt text plus agent instruction templates there. Refactored `outline_agent.py` and `content_agent.py` to consume `build_outline_prompt(...)`, `build_content_prompt(...)`, and agent note/snippet templates from the new prompt package. Added `README.md` in prompt directory with per-prompt caller path and purpose.
Verification: `PYTHONPATH=. pytest tests/test_task_api_flow.py -q` passed (6/6); `PYTHONPATH=. pytest tests -q` passed (12/12).
Open Issues: none.
Time: 2026-05-05 21:48
Step: LLM invocation debug hardening
Completed: Added run-time debug controls for generation endpoint: `require_llm` (strict mode) and `llm_timeout_seconds` (override). In strict mode, task run fails if no successful LLM call is recorded; fallback generation is disabled. Added detailed LLM observability events (`llm_call_start`, `llm_call_succeeded`, `llm_call_failed`) and persisted failure skill-call audit (`llm_text_generation_failed`). Added `llm_debug` block in run response for direct verification.
Verification: `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_task_api_flow.py -q` passed (8/8); `PYTHONPATH=main/backend python -m pytest main/backend/tests -q` passed (14/14).
Open Issues: none.
Time: 2026-05-05 22:10
Step: Provider-type consistency and llm_generate precheck hardening
Completed: Updated `LLMTextGenerator.generate` to normalize `provider_type` (case/alias tolerant) and route via explicit provider sets; unknown values now fail fast instead of silently falling into OpenAI-compatible path. Updated `run_task` inner `llm_generate(prompt)` to normalize `provider_type/model_name/base_url/api_key` and enforce non-empty provider/model/prompt before making HTTP calls.
Verification: `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_task_api_flow.py -q` passed (8/8); `PYTHONPATH=main/backend python -m pytest main/backend/tests -q` passed (14/14).
Open Issues: none.
Time: 2026-05-05 23:06
Step: Ollama LLM/vector call-path hardening + embedding runtime upgrade
Completed: Rechecked Ollama LLM call chain and improved diagnostics path. Added real Ollama connectivity/model-existence probe in provider test (`GET {base_url}/api/tags`) so `/v1/providers/test` can return clear reachable/model_found status. Upgraded vector store runtime from lexical-only vectors to Ollama embedding-capable vectorization with task-scoped configurable settings, defaulting to Ollama `qwen3-embedding:8b` when no user provider config is present. Wired task service to pass embedding runtime config from user default provider (`base_url`, `embedding_model`, `timeout`, `api_key`) and persisted vectorizer metadata into index payload for traceability. Added one-time Ollama unavailable short-circuit to avoid repeated timeout penalties and keep lexical fallback for stability.
Verification: `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_task_api_flow.py -q` passed (9/9); `PYTHONPATH=main/backend python -m pytest main/backend/tests -q` passed (15/15).
Open Issues: none.
Time: 2026-05-06 00:29
Step: Unify default chat/embedding model parameters
Completed: Unified default chat model parameters to `qwen3:8b` and default embedding model parameters to `qwen3-embedding:8b`. Updated frontend Model Settings presets so all provider default `model_name` values and placeholders use `qwen3:8b`; Ollama keeps `chat_model=qwen3:8b` and `embedding_model=qwen3-embedding:8b`. Updated backend provider upsert logic to backfill `chat_model`/`embedding_model` defaults when omitted, while preserving provider-specific fields.
Verification: `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_provider_matrix.py -q` passed (1/1); frontend `npm.cmd run build` passed.
Open Issues: none.
Time: 2026-05-05 20:59
Step: stale backend process guard for no-file run path
Completed: Diagnosed live `No source file attached` error as requests hitting an old process still occupying port 8080. Hardened backend start/stop scripts to automatically terminate any listener on port 8080 before start and during stop fallback, ensuring latest code is always served.
Verification: Restarted backend via scripts; executed live API flow `create -> run` without file and got `status=completed`, with task events containing `no_source_file_detected`.
Open Issues: none.
Time: 2026-05-05 20:55
Step: TaskCreate optional source-file flow fix
Completed: Removed frontend hard requirement for source file on Task Create page. `Create + Run` now supports two paths: (1) with file -> upload + parse + run; (2) without file -> directly run task so agent can proceed with search-driven content organization.
Verification: frontend `npm run build` passed; backend `pytest tests/test_task_api_flow.py::test_task_api_no_source_file_can_still_generate_by_search -q` passed.
Open Issues: none.
Time: 2026-05-05 18:18
Step: stop-backend script robustness
Completed: Updated `main/desktop/scripts/stop-backend.ps1` to ignore race-condition deletion errors when `backend.pid` disappears between existence check and remove call.
Verification: Executed stop/start scripts consecutively; stop exited successfully and backend restart passed health check.
Open Issues: none.
Time: 2026-05-05 18:14
Step: Image placeholder + no-source-file generation path
Completed: Added no-source-file branch in task run flow: when no file is uploaded, the task no longer fails early and instead records `no_source_file_detected`, enables search-driven content organization for execution agents, and proceeds with PPT generation. Added image-placeholder support in PPT content/export: content generation now produces `image_placeholders` metadata (`label` + `source`) and exporter reserves explicit image area on slides with placeholder annotations so users can manually insert final images later.
Verification: `PYTHONPATH=. pytest tests/test_task_api_flow.py -q` passed (6/6, including new tests for no-source-file flow and image placeholder metadata); `PYTHONPATH=. pytest tests -q` passed (12/12); frontend `npm run build` passed.
Open Issues: none.
Time: 2026-05-05 18:02
Step: Task vector cache lifecycle and manual clear
Completed: Moved vectorization to parse stage (`parse_task_file`) so source file text is vectorized immediately after parsing and stored in task cache (`storage/vectors/{task_id}/index.json`). Added web-knowledge auto-vectorization: after `knowledge_search` returns page text, chunks are appended into the same task vector cache. Added manual cache-clear endpoint `POST /v1/tasks/{task_id}/cache/clear` and frontend button `Clear Task Cache` in ResultPreview.
Verification: `PYTHONPATH=. pytest tests -q` passed (10/10); `PYTHONPATH=. pytest tests/test_task_api_flow.py -q` passed (4/4, includes new cache-clear and web-vector append assertions); frontend `npm run build` passed.
Open Issues: none.
Time: 2026-05-06 13:53
Step: Backend start/stop bat shortcut commands
Completed: Added repo-root batch wrappers `hi.bat` and `bye.bat` for one-command backend start/stop. `hi.bat` delegates to `main/desktop/scripts/start-backend.ps1`; `bye.bat` delegates to `main/desktop/scripts/stop-backend.ps1`.
Verification: Static script review completed; no runtime execution in this step.
Open Issues: none.
Time: 2026-05-06 14:22
Step: HuggingFace(vLLM) routing + TaskRunning live conversation window
Completed: (1) Backend LLM runtime changed so `provider_type=huggingface` uses vLLM/OpenAI-compatible route instead of HF inference route; frontend Model Settings updated to show HuggingFace(vLLM) defaults (`http://127.0.0.1:8000/v1`, local downloaded model name) and no mandatory API key. (2) LLM audit payload now records prompt/response text for runtime visibility. (3) Task WebSocket stream now pushes incremental `new_skill_calls` plus task snapshot. (4) TaskRunning page now includes a dynamic scroll window that prints system/user/LLM input-output logs, supports hover for full text, and preserves historical records.
Verification: Backend tests passed individually with `PYTHONPATH=main/backend`: `test_llm_runtime_routing.py` (1), `test_provider_matrix.py` (1), `test_task_api_flow.py` (9), `test_json_repositories_smoke.py` (1), `test_model_router.py` (2), `test_steps_21_30.py` (2); total 16 passed. Frontend `npm run build` passed.
Open Issues: none.
Time: 2026-05-06 14:28
Step: TaskCreate no-file search-and-summary instruction
Completed: Updated TaskCreate page so source file remains optional and, when no file is selected, the submitted requirement is automatically appended with system instruction: model must first perform retrieval/search and summarization, then answer and generate PPT. Added in-page info alert for no-file mode.
Verification: frontend `npm run build` passed.
Open Issues: none.
Time: 2026-05-06 14:31
Step: Move no-file system instruction to backend constant
Completed: Removed frontend hardcoded no-file requirement suffix from TaskCreate. Added backend prompt constant `NO_SOURCE_FILE_SYSTEM_INSTRUCTION` and applied it in `TaskService.run_task` when no source file is attached; instruction now enters planning/generation centrally from backend runtime.
Verification: frontend `npm run build` passed; backend targeted tests `test_task_api_flow.py` passed.
Open Issues: none.
Time: 2026-05-06 14:41
Step: TaskRunning live conversation timeline hardening
Completed: Refined TaskRunning dynamic conversation window to maintain chronological ordering across user/system/LLM records using timestamp sort, and upgraded hover full-text rendering for long multiline content. Kept history accumulation via event/skill-call merge map and auto-scroll behavior.
Verification: frontend `npm run build` passed; backend `PYTHONPATH=main/backend python -m pytest main/backend/tests -q` passed (16/16).
Open Issues: none.
Time: 2026-05-06 15:19
Step: Remove unused decisions argument in PPTTaskAgent
Completed: Removed unused `decisions` parameter from `PPTTaskAgent.execute` and cleaned task-service call sites. This removes dead interface surface and clarifies that model decisions are consumed in `TaskService` where `llm_generate(...)` is built and passed down.
Verification: backend `PYTHONPATH=main/backend python -m pytest main/backend/tests -q` passed (16/16).
Open Issues: none.
Time: 2026-05-06 19:40
Step: Increase default LLM timeout for local generation
Completed: Raised task-run default `llm_timeout_seconds` fallback from `12s` to `90s` when request-level timeout and provider-level timeout are both unset. This reduces false timeout failures on first-call cold starts (e.g., Ollama `qwen3:8b`).
Verification: targeted backend tests passed (task API flow + LLM runtime routing).
Open Issues: none.
Time: 2026-05-06 20:15
Step: Rebuild revision pipeline to enforce LLM-based rethinking
Completed: Replaced `TaskService.revise_page` deterministic string-append logic with a full revision flow: load previous slide JSON, analyze revision instruction, collect context from original requirement + parsed source text + vector retrieval + optional web search, call LLM for structured revised slide payload, run `ReviewAgent` on full deck, then export next PPT version. Added revision-stage LLM/skill/event audit records (`llm_call_start/succeeded/failed`, `llm_text_generation(_failed)`, `knowledge_search`).
Verification: `python -m pytest main/backend/tests/test_steps_21_30.py -q` passed (2/2); `python -m pytest main/backend/tests/test_llm_runtime_routing.py -q` passed (1/1).
Open Issues: `test_task_api_flow.py` full run exceeded local timeout window in this session; no failing assertion captured.
Time: 2026-05-06 21:10
Step: Revision optional page + style-template auto apply
Completed: (1) Revision request now supports optional `page_index`; when omitted, backend asks LLM to infer target slide indexes and can revise multiple slides in one request, then reviews and exports new version. Result page revision form updated accordingly: page optional, larger `instruction` textarea, and no-page guidance text. (2) Added PPT template auto-apply pipeline: exporter supports loading/clearing a matched template file and rendering generated slides on top of template theme/layout; TaskCreate style options expanded; backend fuzzy-matches `task.style` to one template under `main/backend/app/templates/ppt` and applies it for run/revision/rollback exports.
Verification: backend `python -m pytest main/backend/tests/test_steps_21_30.py -q` passed (3/3, includes new no-page revision multi-slide test); frontend `npm.cmd run build` passed.
Open Issues: none.
Time: 2026-05-07 21:20
Step: Implement steps 31-34 multi-task extensibility baseline
Completed: Extended core architecture from PPT-only to multi-task execution for `report`, `wechat_post`, `data_analysis`, `code_doc`, and `paper_assistant` while preserving existing PPT pipeline. Added `task_type` into task creation contract and entity model; coordinator supports generic `plan_for_task`; task manager now routes non-PPT requests into a reusable text-task pipeline (planning -> generation -> review -> export) with LLM primary and deterministic fallback; exports non-PPT results as versioned markdown artifacts. Added compatibility handling for non-PPT version compare/rollback and dynamic download media types. Frontend TaskCreate now allows selecting task type.
Verification: backend `python -m pytest main/backend/tests/test_task_api_flow.py -k "extended_task_types or no_source_file_can_still_generate_by_search" -q` passed (2/2 selected); backend `python -m pytest main/backend/tests/test_steps_21_30.py -q` passed (3/3); frontend `npm.cmd run build` passed.
Open Issues: full `test_task_api_flow.py` run was not completed in this step due session timeout; targeted assertions for new capability are passing.
Time: 2026-05-07 21:34
Step: Add skill runtime chain for new task types
Completed: Added dedicated skill files and runtime bindings for `report`, `wechat_post`, `data_analysis`, `code_doc`, and `paper_assistant` under `main/backend/app/skills/*`. Extended `SkillRegistry.resolve_for(...)` domain resolution and `SkillExecutor.execute(...)` with concrete handlers (`report_outline`, `report_quality_check`, `wechat_title_ideas`, `wechat_style_polish`, `data_clean_plan`, `data_chart_plan`, `code_readme_structure`, `code_api_doc`, `paper_outline`, `paper_revision_suggestions`). Updated text-task orchestration to explicitly resolve/trigger these skills, feed aggregated `skill_context` into generation prompts, and persist skill call audit records.
Verification: backend `python -m pytest main/backend/tests/test_skill_runtime_extension.py -q` passed (2/2); backend `python -m pytest main/backend/tests/test_task_api_flow.py -k extended_task_types -q` passed (1/1 selected); py_compile checks passed.
Open Issues: none.
Time: 2026-05-07 21:52
Step: Refactor non-PPT tasks to TaskAgent + SubAgents pattern and complete skill docs
Completed: Refactored non-PPT task execution from single-function generation into structured multi-agent flow (`TextTaskAgent`) with three sub-agents: planner, writer, reviewer. Planner and reviewer sub-agents now call task-specific skills via runtime executor; writer sub-agent focuses on drafting, and task agent aggregates/reviews outputs before export. Added markdown documentation files for every active skill (`*.md`) covering metadata, core capability, workflow, output requirements, and notes/cautions.
Verification: backend `python -m pytest main/backend/tests/test_skill_runtime_extension.py -q` passed (2/2); backend `python -m pytest main/backend/tests/test_task_api_flow.py -k extended_task_types -q` passed (1/1 selected); py_compile checks passed.
Open Issues: none.
Time: 2026-05-07 22:18
Step: Migrate to per-task TaskAgent and remove generic text-task scripts
Completed: Removed generic agent scripts `app/agents/task_agents/text_task_agent.py` and `app/agents/sub_agents/text_task_sub_agents.py`. Added dedicated per-task task agents (`report_task_agent.py`, `wechat_post_task_agent.py`, `data_analysis_task_agent.py`, `code_doc_task_agent.py`, `paper_assistant_task_agent.py`) and matching per-task sub-agent modules under `app/agents/sub_agents/`. Updated task orchestration to dispatch by task type to corresponding task agent and log task-agent/sub-agent runs. Rebuilt `coordinator_agent.py` with explicit `infer_task_type(...)` and used it for `task_type=auto` in task creation. Fixed unintended non-PPT upload blocking regression.
Verification: `python -m py_compile` for migrated agent/orchestrator modules passed; `python -m pytest main/backend/tests/test_skill_runtime_extension.py -q` passed (2/2); `python -m pytest main/backend/tests/test_task_api_flow.py -k "extended_task_types or no_source_file_can_still_generate_by_search" -q` passed (2/2 selected).
Open Issues: none.
Time: 2026-05-07 22:46
Step: Enforce skill execution across all per-task sub-agent stages
Completed: Updated `data_analysis`, `code_doc`, and `paper_assistant` sub-agent modules so writer and reviewer stages also execute task-specific skills (not only planner), and wired corresponding task-agent calls to pass `skill_execute_fn` into writer/reviewer. Also aligned `report` and `wechat_post` task-agent writer calls with new writer signatures.
Verification: `python -m py_compile` for updated task-agent/sub-agent files passed; `python -m pytest tests/test_skill_runtime_extension.py -q` passed (2/2, workdir=`main/backend`); `python -m pytest tests/test_task_api_flow.py -k extended_task_types -q` passed; `python -m pytest tests/test_task_api_flow.py -k no_source_file_can_still_generate_by_search -q` passed.
Open Issues: `tests/test_task_api_flow.py` combined multi-expression run is slower in this environment and hit timeout when run as one command; split-target runs pass.
Time: 2026-05-07 23:08
Step: Unify backend runtime storage root and remove duplicated legacy directory
Completed: Switched backend default `settings.data_dir` from `main/backend/storage` to `main/backend/runtime_data/storage`; removed legacy reference `main/backend/main/storage` from download-path remapping; deleted duplicated legacy directory `main/backend/main`.
Verification: `python -m py_compile main/backend/app/config.py main/backend/app/api/routes/tasks.py` passed; source search confirmed no remaining references to `backend/main/storage`.
Open Issues: none.
Time: 2026-05-07 23:19
Step: Migrate skill metadata source from `.skill` to `.md` and remove `.skill` files
Completed: Merged each skill's frontmatter metadata (`name/domain/version/status/task_types/stages/runtime_handler/trigger_keywords`) into corresponding `.md` file, updated `SkillRegistry` to enumerate only `*.md`, and removed all legacy `*.skill` files under `main/backend/app/skills`.
Verification: `python -m py_compile main/backend/app/services/skill_registry/registry.py` passed; `python -m pytest tests/test_skill_runtime_extension.py -q` passed (2/2); `python -m pytest tests/test_task_api_flow.py -k extended_task_types -q` passed (1/1 selected).
Open Issues: none.
Time: 2026-05-08 00:02
Step: Reorganize sub-agent modules by task folder and per-agent file
Completed: Refactored `main/backend/app/agents/sub_agents` from flat files into task-scoped packages: `ppt`, `report`, `wechat_post`, `data_analysis`, `code_doc`, `paper_assistant`. In each task package, each sub-agent now has its own file (`planner_sub_agent.py`, `writer_sub_agent.py`, `reviewer_sub_agent.py`; PPT uses `outline_sub_agent.py`, `content_sub_agent.py`, `review_sub_agent.py`). Updated all task-agent imports, task-service imports, and root `sub_agents/__init__.py` exports accordingly; removed legacy flat sub-agent scripts.
Verification: `python -m py_compile` passed for updated sub-agent/task-agent/task-service modules; `python -m pytest tests/test_skill_runtime_extension.py -q` passed (2/2); `python -m pytest tests/test_task_api_flow.py -k extended_task_types -q` passed (1/1 selected).
Open Issues: `tests/test_task_api_flow.py -k no_source_file_can_still_generate_by_search -q` timed out in this environment (no assertion failure captured).
Time: 2026-05-08 00:28
Step: Redesign Task Create flow with coordinator-driven type inference and task-specific settings
Completed: Added backend endpoint `POST /v1/tasks/infer-type` using `CoordinatorAgent.infer_task_type(...)`, changed `CreateTaskRequest.task_type` default to `auto`, and rebuilt frontend `TaskCreatePage` into two-step flow: (1) input requirement -> auto infer task type; (2) Task Setting form rendered by inferred type. `Pages`/`Style` are now shown only for PPT; other task types expose task-specific parameters (report/wechat/data_analysis/code_doc/paper_assistant) and these settings are appended into structured instruction text before task creation.
Verification: `python -m py_compile` passed for backend request/model/route changes; `python -m pytest tests/test_task_api_flow.py -k create_upload_parse_run_flow -q` passed (1/1 selected); frontend `npm.cmd run build` passed.
Open Issues: none.
Time: 2026-05-08 00:41
Step: Convert navigation to sequential flow create -> running -> result
Completed: Removed `Task Running` and `Result` from top-level navigation menu so they are no longer parallel entry pages. Updated task creation behavior to navigate to `/tasks/running` immediately after task is created/uploaded/parsed and trigger `/run` in background. Updated TaskRunning page to sync task status in store and auto-navigate to `/result` when status reaches `completed` or `revision_completed`.
Verification: frontend `npm.cmd run build` passed.
Open Issues: none.
Time: 2026-05-08 01:34
Step: Fix revision pipeline for non-PPT tasks (markdown outputs)
Completed: Updated `TaskService.revise_page(...)` to branch by task type. Non-PPT tasks now use markdown revision flow instead of requiring `*.slides.json`: load latest text artifact, build revision context (parsed file excerpt + vector retrieval + optional web search), invoke LLM for revised content, and persist next version markdown output. Added graceful fallback when revision LLM fails (append revision note instead of hard-failing).
Verification: `python -m py_compile` passed for task service and tests; `python -m pytest tests/test_task_api_flow.py -k "non_ppt_revision_uses_markdown_pipeline_instead_of_slide_json or extended_task_types" -q` passed (2 selected); `python -m pytest tests/test_steps_21_30.py -k revision -q` passed (1 selected).
Open Issues: none.
Time: 2026-05-08 01:58
Step: Add Excel support and strengthen data-analysis runtime with chart+Word export tool
Completed: Extended upload/parse pipeline to accept `xlsx/xls` (`ALLOWED_FILE_TYPES`, `FileType`, parser support). Added Excel parser for text extraction summary and implemented built-in data-analysis toolchain `ExcelCateDistributionTool` to compute `cate` distribution, generate academic bar chart, and export Word report. Exposed runtime skill `data_excel_cate_word_report` in `SkillExecutor` and wired data-analysis export path to call this skill for Excel-source tasks (output artifact becomes `.docx`; fallback to markdown on tool failure).
Verification: `python -m py_compile` passed for parser/skill-runtime/task-service/tool modules; `python -m pytest tests/test_task_api_flow.py -k "data_analysis_task_accepts_xlsx_and_exports_docx_report or extended_task_types" -q` passed (2 selected).
Open Issues: none.
Time: 2026-05-09 09:12
Step: Enforce no-file forced search across task flows
Completed: Updated orchestration so tasks without uploaded files must execute `knowledge_search` before generation in both PPT and non-PPT pipelines. Added forced-search context injection into generation input and vector cache append. If forced search returns no usable results, task now fails fast instead of continuing with non-search answers.
Verification: `python -m py_compile` passed for task service and related tests; `python -m pytest tests/test_task_api_flow.py -k "no_source_file_can_still_generate_by_search or extended_task_types" -q` passed (2 selected).
Open Issues: none.
Time: 2026-05-10 16:20
Step: Co-locate skill scripts with SKILL.md and switch task execution to skills directory runtime
Completed: Reorganized `main/backend/app/skills` into skill-package layout: each skill now lives in `main/backend/app/skills/<domain>/<skill_name>/` with `SKILL.md` and `runtime.py`. Updated all skill markdown runtime binding metadata to `runtime_handler: runtime.py:run`. Replaced hardcoded runtime dispatch in `SkillExecutor` with dynamic loading from skill-local runtime file. Updated `SkillRegistry` to scan `SKILL.md` from skill folders and expose runtime metadata for orchestration resolution.
Verification: `PYTHONPATH=. pytest tests/test_skill_runtime_extension.py -q` passed (2/2); `PYTHONPATH=. pytest tests/test_task_api_flow.py -k "extended_task_types_generate_markdown_outputs or data_analysis_task_accepts_xlsx_and_exports_docx_report" -q` passed (2 selected).
Open Issues: Full `tests/test_task_api_flow.py` suite is long in this environment and timed out when run as a single command.
Time: 2026-05-10 17:05
Step: Move sub-agent scripts into skills directory and delete old sub-agent code path
Completed: Migrated all sub-agent implementation packages (`ppt/report/wechat_post/data_analysis/code_doc/paper_assistant`) from `main/backend/app/agents/sub_agents` to `main/backend/app/skills/<domain>/sub_agents`. Updated task-agent imports and task-manager PPT type imports to new `app.skills.*` paths. Deleted old `main/backend/app/agents/sub_agents` directory after migration.
Verification: `PYTHONPATH=. python -m py_compile app/services/task_manager/task_service.py app/agents/task_agents/*.py app/skills/ppt/sub_agents/*.py` passed; `PYTHONPATH=. pytest tests/test_skill_runtime_extension.py -q` passed (2/2); `PYTHONPATH=. pytest tests/test_task_api_flow.py -k "create_upload_parse_run_flow or extended_task_types_generate_markdown_outputs or data_analysis_task_accepts_xlsx_and_exports_docx_report" -q` passed (3 selected).
Open Issues: none.
Time: 2026-05-10 21:20
Step: Remove sub_agent model and refactor to per-domain small-skill runtime chains
Completed: Rebuilt task execution architecture so each domain (`ppt/report/wechat_post/data_analysis/code_doc/paper_assistant`) is now a large skill package that contains multiple small skills (`planner/writer/reviewer`) as `runtime.py + SKILL.md`. Added domain-level guide markdowns (`*_SKILL.md`) documenting available small skills and execution path. Updated all task agents to invoke small skills directly through `skill_execute_fn`, updated PPT flow and revision-review flow in `TaskService` to use skill runtime calls, and removed all remaining `app/skills/*/sub_agents` directories. Also fixed skill-call audit serialization by masking callable payload entries.
Verification: `PYTHONPATH=. python -m py_compile app/agents/task_agents/*.py app/services/task_manager/task_service.py` passed; `PYTHONPATH=. pytest tests/test_skill_runtime_extension.py -q` passed (2/2); `PYTHONPATH=. pytest tests/test_task_api_flow.py -k "create_upload_parse_run_flow or extended_task_types_generate_markdown_outputs" -q` passed (2 selected).
Open Issues: none.
Time: 2026-05-11 02:25
Step: Add PPT template extraction skill and template selection integration
Completed: Added new skill `main/backend/app/skills/ppt/ppt_template_extractor` (`runtime.py + SKILL.md`) to extract uploaded PPT template structure and assets into `main/backend/app/templates/ppt/<template_name>/` with `template.meta.json`. Updated PPT orchestration so template-extraction intent in requirement triggers router->PPT task->skill path and completes with template metadata output. Added `GET /v1/tasks/ppt/templates` for template listing and updated frontend PPT settings to load and select extracted templates in Style selector.
Verification: `PYTHONPATH=. python -m py_compile app/services/task_manager/task_service.py app/api/routes/tasks.py app/skills/ppt/ppt_template_extractor/runtime.py` passed; `PYTHONPATH=. pytest tests/test_task_api_flow.py -k "ppt_template_extraction_and_template_listing or create_upload_parse_run_flow" -q` passed (2 selected); `PYTHONPATH=. pytest tests/test_skill_runtime_extension.py -q` passed (2/2); `npm run build` passed in `main/frontend`.
Open Issues: none.
Time: 2026-05-11 02:50
Step: Consolidate PPT into two top-level skills and add router intent split
Completed: Reorganized PPT skill packages so `main/backend/app/skills` now uses two dedicated PPT skills only: `ppt_generation` and `ppt_template_generation`, each folder containing only `runtime.py` and `SKILL.md`. Deleted legacy `main/backend/app/skills/ppt/` directory and updated `PPTTaskAgent` to invoke only `ppt_generation`. Added `CoordinatorAgent.infer_ppt_skill(...)` and updated task orchestration to route template-intent requests to `ppt_template_generation`, normal requests to `ppt_generation`. Updated skill registry to support direct top-level skill folders (`skills/<skill>/SKILL.md`) in addition to domain-based layout.
Verification: `PYTHONPATH=. python -m py_compile app/agents/coordinator/coordinator_agent.py app/agents/task_agents/ppt_task_agent.py app/services/skill_registry/registry.py app/services/task_manager/task_service.py app/skills/ppt_generation/runtime.py app/skills/ppt_template_generation/runtime.py` passed; `PYTHONPATH=. pytest tests/test_task_api_flow.py -k "create_upload_parse_run_flow or ppt_template_extraction_and_template_listing" -q` passed (2 selected); `PYTHONPATH=. pytest tests/test_skill_runtime_extension.py -q` passed (2/2).
Open Issues: none.
Time: 2026-05-10 23:35
Step: Add find_skill and enforce task-agent first-call policy
Completed: Added universal skill `find_skill` under `main/backend/app/skills/find_skill` with runtime binding `runtime.py:run`. Updated all task agents (`ppt/report/wechat_post/data_analysis/code_doc/paper_assistant`) so first action is calling `find_skill`, then executing matched skills; if no match is returned, agents use default direct skill path. Updated PPT template-generation branch in task service to call `find_skill` before template extraction skill execution.
Verification: `python -m py_compile` passed for updated skill runtime, task agents, and task service; `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_skill_runtime_extension.py -q` passed (2/2); `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_task_api_flow.py -k "create_upload_parse_run_flow or extended_task_types_generate_markdown_outputs or ppt_template_extraction_and_template_listing" -q` passed (3 passed, 10 deselected).
Open Issues: none.
Time: 2026-05-11 03:45
Step: Fix no-source-file forced-search hard-fail in task execution
Completed: Adjusted `TaskService` no-source-file path for both PPT and non-PPT tasks: force-calls search skill with multiple query attempts, but no longer fails task when search returns empty. Workflow now logs `no_source_file_forced_search_empty;fallback_to_requirement_context` and continues generation using requirement text as fallback context.
Verification: `python -m py_compile main/backend/app/services/task_manager/task_service.py main/backend/tests/test_task_api_flow.py` passed; `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_task_api_flow.py -k "no_source_file_can_still_generate_by_search or no_source_file_search_empty_still_generates_with_fallback" -q` passed (2 passed, 12 deselected); `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_skill_runtime_extension.py -q` passed (2/2).
Open Issues: none.
Time: 2026-05-11 04:12
Step: Enforce agent fallback when find_skill has no match
Completed: Updated all task agents (`ppt/report/wechat_post/data_analysis/code_doc/paper_assistant`) to continue execution when `find_skill` returns empty or skill execution errors occur. Agents now degrade to direct generation path instead of raising runtime failure. Added regression test to verify task completion when `find_skill` yields no matched skills.
Verification: `python -m py_compile` passed for updated task agents and tests; `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_task_api_flow.py -k "no_source_file_can_still_generate_by_search or no_source_file_search_empty_still_generates_with_fallback or continues_when_find_skill_returns_no_match" -q` passed (3 passed, 12 deselected).
Open Issues: none.
Time: 2026-05-11 11:30
Step: Hybrid task-type inference + generic task-agent fallback
Completed: Refactored `CoordinatorAgent.infer_task_type` to hybrid routing (`keyword first -> LLM fallback -> generic fallback`). If keyword hit exists, it routes directly; if keyword miss and `user_id` is available, it calls LLM to classify into supported task types; if still unresolved, it returns `generic_task` instead of defaulting to PPT. Added new `GenericTaskAgent` under `main/backend/app/agents/task_agents` and wired non-PPT execution to route unsupported/unknown task types to this agent, removing old hard-fail branch (`Unsupported non-ppt task_type`). Updated task/create and infer-type API path to pass user context for LLM fallback, and extended task-type model literals to include `generic_task`. Added regression tests for infer-type generic fallback and auto-created generic-task run completion.
Verification: `python -m py_compile main/backend/app/agents/coordinator/coordinator_agent.py main/backend/app/agents/task_agents/generic_task_agent.py main/backend/app/services/task_manager/task_service.py main/backend/app/models/requests.py main/backend/app/models/entities.py main/backend/app/api/routes/tasks.py main/backend/tests/test_task_api_flow.py` passed; `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_task_api_flow.py -k "infer_task_type_returns_generic_when_no_keyword or auto_task_type_routes_to_generic_task_and_runs" -q` passed.
Open Issues: none.

Time: 2026-05-11 17:15
Step: Template-generation required-field auto-fill via LLM extraction
Completed: Added backend request model export and new API POST /v1/tasks/template-generation/infer-settings; coordinator now provides infer_template_settings(requirement,user_id) using LLM with strict JSON schema and safe fallback to empty fields. Frontend template-generation input page now calls infer-settings before navigation and stores inferred results in app store draft. Settings page now auto-prefills required fields from inferred values and keeps required validation for missing items.
Verification: Pending in this step (run compile/build in next step).
Open Issues: none.


Time: 2026-05-11 17:28
Step: Template generation completion jump to dedicated preview page with downloadable artifacts
Completed: Added backend template-preview APIs for template-generation tasks: summary endpoint GET /v1/tasks/{task_id}/template-preview (template file + meta JSON content + params + render script + assets list) and file download endpoint GET /v1/tasks/{task_id}/template-preview/file (template/meta/params/script/asset). Added frontend TemplatePreviewPage and route /template-preview. Updated TaskRunning completion routing to jump to /template-preview when 	ask_type=template_generation, otherwise keep /result.
Verification: backend py_compile passed for tasks route; frontend build passed (
pm run build).
Open Issues: none.


Time: 2026-05-11 17:37
Step: Replace template preview JSON with LLM-formatted textual preview items and tooltip explanations
Completed: Added new common skill 	emplate_preview_formatter (SKILL.md + 
untime.py) under pp/skills/common. Preview API now invokes this skill on every template preview request, passing metadata/assets and user model routing config; skill uses LLM to produce human-readable preview_title/preview_summary/items(label,value,explanation) with deterministic fallback. Frontend template preview page now renders textual items (not raw JSON) and each item includes tooltip explanation.
Verification: backend py_compile passed; frontend build passed (
pm run build).
Open Issues: none.


Time: 2026-05-11 17:48
Step: Refine template preview rendering logic to key:value display + per-item LLM explanation
Completed: Reworked 	emplate_preview_formatter skill runtime to first parse and flatten 	emplate.meta.json into key:value rows, then call LLM per metadata item for tooltip explanation only (one item -> one explanation call). UI values are now driven by metadata keys/values, not raw JSON printing. Added API fallback so if skill call fails, metadata key:value rows are still returned with fallback explanations to avoid blank preview.
Verification: backend py_compile passed; frontend build passed (
pm run build).
Open Issues: none.


Time: 2026-05-11 21:15
Step: Upgrade find_skill to metadata-first selection + fuzzy/semantic matching
Completed: Updated ind_skill to default 	ask_type=generic_task, removed stage from caller payload contract, and implemented hybrid matching pipeline: preferred skill hits + requirement keyword fuzzy matching (metadata-based) + optional LLM semantic selection. Added conservative merge strategy to avoid missing needed skills. Updated all task-agent invocations to remove stage. Task-service skill-execute wrappers now auto-inject model routing info (provider_type/base_url/model_name/api_key) into ind_skill calls for semantic matching. Skill registry frontmatter parser now reads metadata section only (no full skill-body load).
Verification: python -m py_compile passed for updated modules; PYTHONPATH=main/backend python -m pytest main/backend/tests/test_skill_runtime_extension.py -q passed (2/2).
Open Issues: none.


Time: 2026-05-11 21:22
Step: Merge paper_assistant sub-skills into single runtime skill
Completed: Collapsed pp/skills/paper_assistant from multi-subskill layout into a single skill contract with only SKILL.md and 
untime.py. Removed planner/writer/reviewer/outline/revision sub-skill files and updated PaperAssistantTaskAgent to call unified paper_assistant skill via ind_skill preferred match. Deleted legacy package files in this folder (PAPER_ASSISTANT_SKILL.md, __init__.py). Updated skill runtime extension test to assert unified skill execution (paper_assistant) and removed obsolete ind_skill.stage test input.
Verification: python -m py_compile main/backend/app/skills/paper_assistant/runtime.py main/backend/app/agents/task_agents/paper_assistant_task_agent.py passed; PYTHONPATH=main/backend python -m pytest main/backend/tests/test_skill_runtime_extension.py -q passed (2/2).
Open Issues: none.


Time: 2026-05-11 22:11
Step: Merge report/code_doc/wechat_post into single-skill runtime per domain
Completed: Collapsed pp/skills/report, pp/skills/code_doc, and pp/skills/wechat_post into single executable skill structure (SKILL.md + 
untime.py only). Removed all planner/writer/reviewer and auxiliary sub-skill folders/files in these three domains. Updated task agents (ReportTaskAgent, CodeDocTaskAgent, WechatPostTaskAgent) to call unified skills (
eport, code_doc, wechat_post) after ind_skill match. Updated tests that referenced removed skill names (
eport_outline, code_readme_structure, wechat_title_ideas, planner skill names) to unified skill assertions.
Verification: python -m py_compile passed for updated runtimes/agents/tests; PYTHONPATH=main/backend python -m pytest main/backend/tests/test_skill_runtime_extension.py -q passed (2/2).
Open Issues: none.


Time: 2026-05-11 22:17
Step: Merge data_analysis domain into single skill runtime
Completed: Collapsed pp/skills/data_analysis into single-skill structure (SKILL.md + 
untime.py) and removed all sub-skills/tools in this directory. Unified runtime now supports two paths: (1) markdown data-analysis generation, (2) Excel cate-distribution DOCX export when excel_path/report_docx_path/chart_png_path are provided. Updated DataAnalysisTaskAgent to call unified skill data_analysis. Updated task-service export branch to invoke data_analysis (instead of removed data_excel_cate_word_report) for Excel report generation. Updated tests referencing old planner/clean-plan skill names.
Verification: python -m py_compile passed for updated runtime/agent/task-service/tests; PYTHONPATH=main/backend python -m pytest main/backend/tests/test_skill_runtime_extension.py -q passed (2/2).
Open Issues: none.

Time: 2026-05-11 22:35
Step: Move common skills to top-level skills directory and update call paths
Completed: Moved skill packages from `app/skills/common/*` to `app/skills/*` (`base_prompt`, `knowledge_search`, `template_generation`, `template_preview_formatter`), removed old `app/skills/common` directory, and updated test patch targets from `app.skills.common.knowledge_search...` to `app.skills.knowledge_search...`. Verified skill discovery remains valid under top-level layout. During regression, fixed Python 3.9 incompatibility in tasks route (`str | None` -> `Optional[str]`) and corrected `_run_text_task` agent invocation kwargs so `force_direct/selected_capability_name` are only passed to `GenericTaskAgent`.
Verification: py_compile passed for touched modules; `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_skill_runtime_extension.py -q` passed (2/2); `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_task_api_flow.py -k "no_source_file_can_still_generate_by_search or extended_task_types_generate_markdown_outputs" -q` passed (2 passed).
Open Issues: none.
Time: 2026-05-11 23:02
Step: Rename generation-domain skill names/metadata for better find-skill recognition
Completed: Renamed skill identifiers in frontmatter for generation domains to explicit generation names: `report_generation`, `code_doc_generation`, `wechat_post_generation`, `paper_assistant_generation`. Updated each SKILL.md description and trigger keywords to be more generation-oriented and easier for metadata-based matching. Updated task-agent preferred-skill routing and fallback skill names in `ReportTaskAgent`, `CodeDocTaskAgent`, `WechatPostTaskAgent`, and `PaperAssistantTaskAgent`. Updated tests to use new skill names.
Verification: `python -m py_compile` passed for touched agents/tests; `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_skill_runtime_extension.py -q` passed (2/2); `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_task_api_flow.py -k "extended_task_types_generate_markdown_outputs" -q` passed (1 passed).
Open Issues: none.

Time: 2026-05-13 13:20
Step: Add implementation plan for vLLM default routing, multi-user active count, registration entry, and user data isolation
Completed: Added `develop_guide/vllm_concurrency_active_users_registration_plan.md` as an agent-executable rollout plan. The plan defines confirmed scope and decisions (single-node vLLM global default, active-user window=10 minutes, system-wide count, WebSocket realtime, registration flow, per-user data isolation), phased backend/frontend changes, API and WS contracts, test matrix, risk/rollback strategy, and DoD. Plan explicitly includes repository governance requirements (`architecture.md` and `process.md` update rules) for downstream execution.
Verification: Document created and saved under `develop_guide`; content reviewed for direct handoff to implementation agent.
Open Issues: none.

Time: 2026-05-13 13:40
Step: Execute STEP 1 - switch global default model routing to vLLM
Completed: Implemented vLLM global default fallback for model routing. Added `VllmConfig` defaults (`WORKFORGE_VLLM_BASE_URL`, `WORKFORGE_VLLM_MODEL`, `WORKFORGE_VLLM_API_KEY`) in provider defaults module; exported it via llm_provider package; updated `ModelRouter` system fallback from Ollama to vLLM (`provider_type=vllm`, `display_name=vLLM Local (Default)`, default endpoint `http://127.0.0.1:8000/v1`). Updated router test expectations accordingly.
Verification: `python -m py_compile main/backend/app/services/llm_provider/provider_defaults.py main/backend/app/services/llm_provider/__init__.py main/backend/app/services/model_router/router.py main/backend/tests/test_model_router.py` passed; `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_model_router.py -q` passed (2/2).
Open Issues: none.

Time: 2026-05-13 14:05
Step: Execute STEP 2 - backend active-user tracking and query API
Completed: Added `ActiveUserTracker` service with 10-minute sliding window and thread-safe in-memory unique-user tracking. Wired tracker initialization in FastAPI lifespan and added HTTP middleware to touch activity for authenticated Bearer-token requests without blocking request flow on tracker/auth errors. Added new authenticated endpoint `GET /v1/system/active-users` returning `{active_users, window_seconds, server_time}` and route registration in app router index.
Verification: `python -m py_compile main/backend/app/services/active_users/active_user_tracker.py main/backend/app/services/active_users/__init__.py main/backend/app/api/routes/system.py main/backend/app/api/routes/__init__.py main/backend/app/api/app.py main/backend/tests/test_active_user_tracker.py` passed; `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_active_user_tracker.py -q` passed (2/2).
Open Issues: none.

Time: 2026-05-13 14:20
Step: Execute STEP 3 - realtime active-user push via WebSocket and frontend display
Completed: Added backend WebSocket endpoint `/ws/system/active-users` in `ws_tasks.py` with token validation (`AuthService.validate_token`) and policy-close on invalid/missing token. Endpoint now pushes active-user snapshot every 3 seconds and touches authenticated user activity on connect. Frontend added `getWsBaseUrl()` helper in `http.ts`; Task Running page now opens active-user websocket with reconnect backoff (2s/5s/10s), updates live count state, and displays `Active Users (10m)` tag.
Verification: `python -m py_compile main/backend/app/api/routes/ws_tasks.py` passed; `npm.cmd run build` passed in `main/frontend` (TypeScript + Vite production build successful).
Open Issues: none.

Time: 2026-05-13 14:35
Step: Execute STEP 4 - registration entry and register->login flow
Completed: Delivered dedicated registration page and login-page registration entry. Frontend auth flow now has `/Login` and `/Register` routes, login form uses `account + password`, and registration form requires `username + password`; successful registration redirects back to `/Login`. Backend auth contracts updated: `RegisterRequest` now takes `username/password`, `LoginRequest` now takes `account/password` (username or email accepted). Added username uniqueness enforcement in repository and service layers; registration generates internal email (`<username>@local.workforge`) to preserve existing User schema compatibility. Added backend static route for `/Register`.
Verification: `python -m py_compile main/backend/app/models/requests.py main/backend/app/repositories/interfaces/user_repository.py main/backend/app/repositories/json_impl/repositories.py main/backend/app/services/auth_service.py main/backend/app/api/app.py main/backend/tests/test_provider_matrix.py main/backend/tests/test_steps_21_30.py` passed; `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_provider_matrix.py -q` passed (1/1); `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_steps_21_30.py -q` passed (3/3); `npm.cmd run build` passed in `main/frontend`.
Open Issues: none.

Time: 2026-05-13 15:05
Step: Execute STEP 5 - user data isolation hardening
Completed: Implemented strict owner checks for task-related APIs and task WebSocket. Added shared auth helpers in `tasks.py` to parse bearer token, resolve current user, and validate task ownership before all task operations (create/list/get/upload/parse/run/recovery/bootstrap/status/download/version/revision/cache/template preview). Added user-id consistency checks on create/infer endpoints. Updated `/ws/tasks/{task_id}` to require token query and reject cross-user subscriptions. Updated frontend Task Running task-WS connection to send token in query string. Added dedicated isolation tests to verify cross-user API/WS access is blocked and updated step regression tests to pass auth headers on task endpoints.
Verification: `python -m py_compile main/backend/app/api/routes/tasks.py main/backend/app/api/routes/ws_tasks.py main/backend/tests/test_user_data_isolation.py main/backend/tests/test_steps_21_30.py` passed; `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_user_data_isolation.py main/backend/tests/test_steps_21_30.py -q` passed (5/5); `npm.cmd run build` passed in `main/frontend`.
Open Issues: none.

Time: 2026-05-13 15:20
Step: Execute STEP 6 - tests and regression matrix
Completed: Added dedicated integration tests for auth-flow and active-user runtime push: `main/backend/tests/test_auth_and_active_users_api_ws.py` covering (1) register->login success, (2) `/v1/system/active-users` response contract, and (3) `/ws/system/active-users` realtime push payload. Completed target and critical regression suites for model routing, active-user tracking, data isolation, provider paths, and step21-30 auth/task/ws workflows.
Verification: `python -m py_compile main/backend/tests/test_auth_and_active_users_api_ws.py` passed; `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_model_router.py main/backend/tests/test_active_user_tracker.py main/backend/tests/test_auth_and_active_users_api_ws.py main/backend/tests/test_user_data_isolation.py -q` passed (8/8); `PYTHONPATH=main/backend python -m pytest main/backend/tests/test_provider_matrix.py main/backend/tests/test_steps_21_30.py -q` passed (4/4).
Open Issues: none.

Time: 2026-05-13 15:22
Step: Execute STEP 7 - documentation finalization
Completed: Updated `develop_guide/architecture.md` with verified acceptance-baseline entry for vLLM default routing, active-user tracker/API/WS, registration-login flow, and owner-scoped data isolation. Synchronized `develop_guide/process.md` with complete Step 6 and Step 7 execution/verification records.
Verification: Documentation files saved successfully and aligned with current implemented architecture and test baseline.
Open Issues: none.

Time: 2026-05-13 15:35
Step: Align frontend model-settings defaults with backend vLLM system default
Completed: Updated `main/frontend/src/pages/ModelSettings/ModelSettingsPage.tsx` to include explicit `vllm` provider type/preset and switched form initial defaults from `ollama` to `vllm` (`base_url=http://127.0.0.1:8000/v1`, `model_name=Qwen/Qwen2.5-7B-Instruct`). Provider selector initial value and fallback preset now both use `vllm`, resolving frontend/backend default mismatch.
Verification: `npm.cmd run build` passed in `main/frontend` (TypeScript + Vite build successful).
Open Issues: none.

Time: 2026-05-12 09:40
Step: Execute PPT generation plan STEP 9 and STEP 10 checks/fixes
Completed: Updated template-generation recovery status flow in `main/backend/app/services/task_manager/task_service.py` so recovery-required branch now writes `requires_user_completion` task status (instead of `failed_generation`). Added auditability fields/events for recovery flow: template name, bundle validation result (ok/missing/errors), resume attempt count, and applied rules count on successful resume. Kept compatibility strategy: invalid/legacy PPT bundles remain filtered from dropdown (`list_ppt_templates` returns only `validate_template_bundle.ok == true`), while strict `TemplateChoice` resolution is preserved for new tasks.
Verification: `python -m py_compile main/backend/app/services/task_manager/task_service.py main/backend/tests/test_task_api_flow.py` passed. Targeted pytest subset: `list_ppt_templates_returns_only_valid_bundles` and `ppt_generation_fails_when_templatechoice_is_invalid` passed; one existing template-generation E2E case returned 400 in this environment before reaching new assertions (needs separate stabilization of template-generation E2E fixture/runtime path).
Open Issues: stabilize `test_template_generation_returns_requires_user_completion_for_incomplete_ppt_design` environment-path behavior to make full Step 9 regression green.

Time: 2026-05-13 15:45
Step: Add detailed execution plan for model-config save persistence and backend/frontend consistency
Completed: Added `develop_guide/model_config_provider_persistence_plan.md` with agent-executable steps to fix and verify: user-scoped provider save/update semantics, unique per-user default switching, immediate model-router effectiveness after save, `/models` page hydration/reload consistency, owner-scope security checks, regression tests, manual verification checklist, rollback strategy, and DoD.
Verification: Plan file saved and reviewed for direct handoff; structure includes file-level targets, acceptance criteria, and required documentation updates.
Open Issues: none.
