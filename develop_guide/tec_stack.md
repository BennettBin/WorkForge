# WorkForge AI 技术栈推荐（面向独立应用 + MVP 迭代）

## 结论（推荐主栈）

基于你的产品设计和后续演进诉求，建议采用：

- **桌面壳**：`Tauri 2`（打包成 Windows/macOS/Linux 安装包）
- **前端**：`React + TypeScript + Vite + Ant Design`
- **后端**：`Python + FastAPI`
- **任务编排**：以你文档中的 `Harness + 多 Agent 分层` 为核心，外加统一 `Task Orchestrator`
- **本地存储（MVP）**：`JSON + Excel`（通过 Repository 抽象隔离）
- **后续数据库迁移**：无缝替换为 `SQLite/PostgreSQL`（保持接口不变）
- **文件处理与导出**：`python-pptx / python-docx / pandas / openpyxl / pypdf`
- **通信方式**：`HTTP + WebSocket（任务进度流）`

---

## 1. 为什么这套栈最适合你的 3 个要求

### 1) 逐功能开发、保持可扩展

- FastAPI + 分层架构（api / services / agents / repositories）天然适合按模块逐步增加能力。
- React 前端可按页面和功能卡片拆分（PPT、报告、数据分析等）独立迭代。
- 多 Agent、Skill Registry、Model Router 都可以以插件化接口增加，不破坏既有功能。

### 2) 先用 JSON/Excel，后续可切数据库

- 关键点不是“先不用数据库”，而是**先定义数据访问接口**：
  - `TaskRepository`
  - `FileRepository`
  - `ProviderConfigRepository`
  - `OutputVersionRepository`
- MVP 实现 `Json/ExcelRepository`；后续新增 `SqlRepository` 即可迁移，无需重写业务逻辑。

### 3) 先做 MVP，再改前后端

- Tauri + React + FastAPI 的边界清晰，后续重做 UI 或替换后端框架都可控。
- MVP 可先实现单任务闭环（PDF/DOCX -> PPTX），再逐步叠加 Agent 可视化、模型配置、Skill Registry、修改闭环。

---

## 2. 推荐架构（可落地）

```text
Desktop (Tauri)
  ├─ Frontend (React)
  │   ├─ TaskCreate / TaskRunning / ResultPreview / ModelSettings / History
  │   └─ API Client + State Store
  └─ Local Backend (FastAPI)
      ├─ API Layer
      ├─ Application Layer (Task Orchestrator / ModelRouter / SkillRegistry)
      ├─ Domain Layer (Task/AgentRun/OutputVersion 等模型)
      ├─ Infrastructure Layer (JSON/Excel Repos, File Parser, Export Engine)
      └─ Storage (uploads/parsed/outputs/versions)
```

---

## 3. 数据层设计（先 JSON/Excel，后数据库）

建议从第一天就固定接口：

- `repositories/interfaces/*.py`：只定义抽象接口
- `repositories/json_impl/*.py`：MVP 实现
- `repositories/sql_impl/*.py`：后续迁移实现

并统一数据模型（Pydantic）：

- `Task`
- `AgentRun`
- `SkillCall`
- `LLMProviderConfig`
- `OutputFile`

这样可以确保后面换 SQLite/PostgreSQL 时，API 层和 Agent 层几乎不动。

---

## 4. MVP 迭代建议（与你文档一致）

1. **MVP-1**：PDF/DOCX -> PPTX 闭环（上传、解析、生成、导出、下载）
2. **MVP-2**：任务执行可视化（阶段、进度、Agent 时间线）
3. **MVP-3**：LLM Provider 配置层（OpenAI-compatible + Ollama + Custom Base URL）
4. **MVP-4**：Skill Registry（按需加载）
5. **MVP-5**：局部修改 + 版本管理
6. **MVP-6**：扩展任务类型（报告、公众号、数据分析、代码文档、论文辅助）

---

## 5. 独立应用安装包方案

- 使用 `Tauri bundler` 输出：
  - Windows：`.msi`
  - macOS：`.dmg`
  - Linux：`.AppImage` / `.deb`
- Python 后端作为本地 sidecar 进程随安装包分发。
- 首版建议先稳定 Windows 打包链路，再扩展多平台。

---

## 6. 版本建议（起步）

- Node.js `20 LTS`
- Python `3.11`（兼容性和生态稳定）
- FastAPI `0.11x+`
- React `18+`
- TypeScript `5+`
- Tauri `2.x`

---

## 7. 一句话执行建议

先按“**Tauri + React 前端 + FastAPI 后端 + Repository 抽象**”搭框架，把 `MVP-1` 跑通；后续每加一个功能模块，只增加 Agent/Skill/Template/Repo 实现，不改核心骨架。
