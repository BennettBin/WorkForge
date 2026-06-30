# WorkForge

一个面向本地办公与内容生产的多能力 Agent 工作台，支持任务创建、文件上传解析、PPT 生成、报告撰写、数据分析、代码文档、公众号文案、论文辅助、模板生成与可扩展 Skill 运行。

**项目状态**: 🚧 本地开发版，已具备 FastAPI 后端、React 前端、桌面启动脚本、用户/模型配置、任务运行、文件解析、RAG 索引和 PPT 模板渲染主流程

## 📋 核心特性

- **统一任务入口**: 用户输入需求并上传文件后，系统自动识别任务类型并进入对应 Agent 流程
- **任务类型识别**: 支持显式 `TaskType=`、关键词规则和 LLM 兜底识别，失败时回退到通用任务
- **多任务能力**: 覆盖 PPT、报告、公众号文案、数据分析、代码文档、论文辅助、模板生成和通用文本任务
- **文件解析与 RAG**: 上传文件后解析文本，生成本地 chunk、metadata 和向量/词法索引，后续查询复用已有索引
- **自主召回与搜索**: Agent 在生成和修订阶段会判断是否需要 RAG 召回或外部搜索补充上下文
- **PPT 模板渲染**: 支持系统模板、模板约束、slot 映射、预览图和 PPTX 导出
- **模型与 Embedding 配置**: 支持聊天模型 provider、独立 embedding provider、Ollama 兼容配置和不可用时的降级路径
- **用户与并发控制**: 提供注册登录、当前用户、活跃用户、任务并发限制和运行任务面板
- **桌面本地运行**: 提供 Tauri 配置和 PowerShell 后端启动/停止脚本，便于本机开发调试

## 🛠️ 技术栈

| 层级 | 技术 |
|---|---|
| 前端 | React 18 + TypeScript + Vite + Ant Design |
| 桌面 | Tauri 配置 + 本地启动脚本 |
| API | FastAPI + Pydantic 2 |
| 存储 | 本地 JSON Repository + runtime storage |
| 文件解析 | pypdf + python-docx + python-pptx + openpyxl |
| Agent Runtime | LangGraph + Skill Executor + Task Agent |
| LLM | OpenAI-compatible / Ollama / vLLM / 自定义 Provider |
| Embedding | 独立 Embedding Provider + sentence-transformers / Ollama / lexical fallback |
| 输出 | PPTX、Markdown、JSON、文本和模板包 |

## 📚 核心文档

当前仓库的主要说明入口：

1. **[README.md](README.md)** - 项目入口、能力概览和启动方式
2. **[backend/.env.example](.env.example)** - 后端环境变量示例
3. **[backend/app/skills](app/skills)** - Skill 定义、脚本和能力目录
4. **[backend/app/templates](app/templates)** - PPT/文本模板资源
5. **[backend/tests](tests)** - 后端任务流、模板、Provider、权限和 RAG 回归测试

## 🚀 快速开始

### 环境要求

- Python 3.10+（建议使用项目虚拟环境）
- Node.js 18+
- PowerShell（Windows 本地脚本）
- 可选：Ollama、vLLM 或其他 OpenAI-compatible 模型服务

### 后端开发

```bash
# 1. 进入后端目录
cd backend

# 2. 创建并激活虚拟环境
python -m venv .venv
.\.venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动 API
python main.py
```

后端默认提供 FastAPI 路由，包括健康检查、用户认证、任务、Skill、模型 Provider、Embedding Provider、系统信息和 WebSocket 任务事件。

### 前端开发

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动 Vite 开发服务
npm run dev

# 4. 构建前端
npm run build
```

### 桌面/本地脚本

```powershell
# 启动后端
.\desktop\scripts\start-backend.ps1

# 停止后端
.\desktop\scripts\stop-backend.ps1
```

如需启动 Tauri 开发模式：

```bash
cd frontend
npm run tauri:dev
```

## 🧭 典型任务流程

1. 用户登录并进入任务创建页。
2. 输入需求，可选上传 PDF、DOCX、PPTX、TXT、MD、Excel 等文件。
3. 前端调用任务类型识别接口，用户确认任务设置。
4. 后端创建 Task，并记录模板、语言、页数、Provider 等配置。
5. 上传文件后写入本地 storage，并登记 RAG 文档状态。
6. 解析阶段生成文本、chunk、RAG metadata 和索引。
7. 执行阶段选择 Skill、模型和模板，按需执行 RAG 召回或搜索。
8. 生成结果写入 output version，前端展示下载、预览和修订入口。

## 📁 项目结构

```text
main/
├── backend/                 # FastAPI 后端和 Agent 运行时
│   ├── app/
│   │   ├── agents/          # Coordinator、Task Agent、工具和运行时
│   │   ├── api/             # FastAPI app、路由和错误处理
│   │   ├── models/          # Pydantic Entity 和 Request/Response
│   │   ├── prompts/         # Agent 和任务 Prompt
│   │   ├── repositories/    # 本地 JSON Repository
│   │   ├── services/        # 任务、模型、Skill、RAG、导出和模板服务
│   │   ├── skills/          # 可扩展 Skill 目录
│   │   └── templates/       # PPT/文本模板资源
│   ├── tests/               # 后端测试套件
│   ├── runtime_data/        # 后端运行数据
│   ├── storage/             # 后端本地存储
│   ├── main.py              # 后端启动入口
│   └── requirements.txt     # Python 依赖
├── frontend/                # React + Vite 前端
│   ├── src/                 # 页面、组件、store 和 API 客户端
│   ├── package.json         # 前端脚本和依赖
│   └── vite.config.ts       # Vite 配置
├── desktop/                 # Tauri 配置和本地脚本
│   └── scripts/             # start/stop backend 脚本
├── docs/                    # 项目文档目录
├── logs/                    # 运行日志
├── runtime_data/            # 根级运行数据
└── README.md                # 本文件
```

## 📦 开发命令

```bash
# 后端测试
cd backend
python -m pytest -q

# 运行重点回归测试
python -m pytest tests/test_coordinator_routing.py tests/test_embedding_provider_config.py -q

# 前端开发与构建
cd frontend
npm run dev
npm run build
```

## 🔄 当前能力阶段

- **任务系统** ✅ 已接入
  - 创建、上传、解析、运行、修订、下载、版本比较和回滚
- **用户与会话** ✅ 已接入
  - 注册登录、用户隔离、活跃用户和并发任务限制
- **Provider 管理** ✅ 已接入
  - Chat Provider、Embedding Provider、默认配置和连接测试
- **Skill Runtime** ✅ 已接入
  - Skill Registry、Skill Executor、解析 Skill、生成 Skill、搜索 Skill 和模板 Skill
- **PPT 生成** ✅ 已接入
  - 大纲、逐页内容、模板 slot 映射、模板渲染和 PPTX 导出
- **模板生成与预览** ✅ 已接入
  - PPT 模板提取、模板 bundle 校验、预览图和恢复流程
- **RAG 文件索引** 🚧 本地 JSON 版持续完善
  - documents/chunks/sections/index metadata 本地持久化
  - 文件 hash 去重、索引复用、exact match 和 embedding fallback
- **桌面集成** 🚧 开发中
  - Tauri 配置与本地后端脚本已存在，完整安装包流程仍需继续完善

## 🧪 测试

项目主要测试范围：

- **API Flow**: 任务创建、上传、解析、运行、下载
- **Coordinator Routing**: 任务类型识别、显式设置和 LLM 兜底
- **Provider**: 用户隔离、默认模型、Embedding 配置和运行时路由
- **Template**: 模板 bundle、slot contract、布局 introspection 和渲染约束
- **PPT E2E**: PPT 生成、像素级回归和导出验证
- **Security/Isolation**: 用户数据隔离、并发限制和权限路径

推荐在改动后至少运行相关测试：

```bash
cd backend
python -m pytest tests/test_coordinator_routing.py tests/test_embedding_provider_config.py -q
```

涉及任务流或 PPT 生成时运行：

```bash
python -m pytest tests/test_task_api_flow.py tests/test_ppt_generation_runtime_template_constraints.py -q
```

## 🔐 隐私和安全

- ✅ 用户数据按 user_id 进行 Repository 层隔离
- ✅ 上传文件写入本地 storage/runtime_data，不应提交真实用户文件
- ✅ Provider 密钥只应存在本地配置或运行数据中
- ✅ 文件解析和 RAG 索引保留 hash、metadata 和可追踪 chunk
- ⚠️ 当前是本地 JSON 存储形态，不等价于生产数据库权限模型
- ⚠️ 外部搜索、模型调用和模板脚本执行需要按部署环境单独评估安全边界

## 📖 贡献指南

建议遵循以下原则：

1. 先补回归测试，再修改任务流或 Skill 行为
2. 保持 API Route 轻量，业务逻辑放在 service/agent/skill 中
3. 文件解析、RAG 和生成流程要能记录清晰事件
4. 不把模型权重、用户上传文件、运行缓存和密钥提交到 Git
5. 不覆盖已有未提交修改，改动保持聚焦

## 📝 许可证

内部开发项目，许可证待确认。

---

**最后更新**: 2026-06-30  
**当前维护者**: WorkForge Team
