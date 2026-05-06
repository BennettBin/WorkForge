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
