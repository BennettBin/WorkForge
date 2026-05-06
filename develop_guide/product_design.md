# WorkForge AI 产品设计文档

> 项目定位：基于 Harness 框架的多 Agent 智能办公生产系统

---

## 1. 项目背景

在办公、科研、内容创作、数据分析和代码开发等场景中，用户经常需要完成以下任务：

- 根据 PDF / Word / PPT / Excel 等文件制作汇报材料；
- 根据参考资料撰写报告、论文草稿、公众号推文；
- 根据数据文件完成清洗、分析、绘图和结论总结；
- 根据项目代码生成 README、技术文档、前端页面或重构建议；
- 根据已有文档继续修改、润色、扩展或转换格式。

传统的大模型对话系统虽然可以生成文本，但存在几个明显问题：

1. **缺少稳定的任务流程**：用户提出复杂需求后，模型容易直接生成结果，缺少规划、拆解、检查和修改闭环。
2. **上下文使用效率低**：如果一次性加载所有模板、规则和 Skill，会浪费大量 token。
3. **输出质量不可控**：生成结果缺少明确的验收标准和审查机制。
4. **难以交付最终文件**：普通聊天系统往往只返回文本，不能稳定生成 PPTX、DOCX、PDF、图表、代码等最终文件。
5. **修改体验差**：用户不满意时，系统常常重新生成，而不是在已有结果上局部修改。

因此，本项目希望构建一个以最终办公成果交付为目标的智能系统：用户只需要上传参考文件并描述需求，系统即可自动选择任务流程、调用对应 Skill、组织多个 Agent 协作，并最终生成可下载、可修改、可版本管理的文件。

---

## 2. 产品名称

### 2.1 推荐名称

**WorkForge AI**

中文名称可暂定为：**智能办公工坊**。

### 2.2 名称含义

- **Work**：面向真实工作场景，包括办公、科研、数据分析、内容创作和代码开发。
- **Forge**：表示“锻造、打磨、生成高质量成果”。
- **AI**：表示系统由大模型、多 Agent 和 Skill 调用机制驱动。

### 2.3 其他候选名称

| 名称 | 特点 |
|---|---|
| OfficePilot | 强调办公任务自动驾驶 |
| DocuFlow AI | 强调文档生成流程 |
| TaskCraft AI | 强调任务拆解与结果打磨 |
| SkillOffice | 强调 Skill 动态调用 |
| AgentDesk | 强调多 Agent 办公系统 |
| HarnessOffice | 突出 Harness 框架 |
| 灵工坊 | 中文产品感较强 |

最终建议：

> **WorkForge AI：基于多 Agent 协作的智能办公内容生成平台**

---

## 3. 产品定位

WorkForge AI 是一个面向办公、科研、内容创作、数据分析和代码开发场景的多 Agent 智能生产平台。

用户只需上传参考文件并描述目标任务，系统即可自动完成：

1. 需求理解；
2. 任务类型识别；
3. 文件解析；
4. 模板选择；
5. Skill 按需调用；
6. 多 Agent 协作生成；
7. 质量审查；
8. 文件导出；
9. 用户反馈后的局部修改；
10. 版本管理。

系统的目标不是简单聊天，而是完成从用户需求到最终办公文件交付的完整工作流。

---

## 4. 项目目标

本项目的目标是开发一个 **多功能办公助手**，基于 Harness 框架，利用严格的任务约束机制，使 Agent 能够更快、更好、更节省 token 地完成复杂办公任务。

系统应具备以下核心能力：

1. 拥有多个 Skills，并能够根据任务需求动态调用对应 Skill，而不是一次性读取所有 Skill。
2. 支持多个 Agent 协同完成复杂任务。
3. 每个任务由一个 Task Agent 负责统筹。
4. Task Agent 下设多个 Sub Agents，分别负责任务中的不同部分。
5. Task Agent 负责与 Sub Agents 讨论、汇总和最终检阅。
6. 只有 Task Agent 审查通过后，子任务结果才可以进入最终输出。
7. 系统能够进行自我反馈、自我修改和质量检查。
8. 用户不满意时，系统应在已有结果基础上进行局部修改，而不是完全重新生成。
9. 大模型接口应支持用户自行配置，兼容云端 API、本地大模型、Ollama 以及后续扩展的多种 LLM 调用方式。

---

## 5. 目标用户

### 5.1 学生 / 研究生 / 科研人员

主要需求：

- 读论文；
- 做 journal club PPT；
- 写论文草稿；
- 写文献综述；
- 写 figure legend；
- 写实验报告；
- 根据数据画学术图表；
- 生成 response to reviewers 草稿。

### 5.2 企业办公人员

主要需求：

- 写项目报告；
- 写商业分析报告；
- 制作汇报 PPT；
- 生成会议纪要；
- 写年度总结；
- 写客户方案；
- 整理调研资料。

### 5.3 自媒体 / 内容创作者

主要需求：

- 写公众号推文；
- 将论文或报告转成科普文章；
- 生成标题；
- 生成摘要；
- 生成配图建议；
- 生成小红书 / 知乎 / LinkedIn 风格内容。

### 5.4 数据分析用户

主要需求：

- 上传 Excel / CSV；
- 自动清洗数据；
- 分组统计；
- 回归分析；
- 按学术论文要求画图；
- 生成分析报告；
- 输出可复现代码。

### 5.5 程序员 / 项目开发者

主要需求：

- 分析项目结构；
- 重构代码；
- 生成前端页面；
- 生成后端接口；
- 写 README；
- 写技术文档；
- 写 Skill 文档；
- 生成测试代码。

---

## 6. 核心功能概览

WorkForge AI 第一阶段重点支持以下任务：

1. 做 PPT；
2. 写报告；
3. 写论文相关内容；
4. 写公众号推文；
5. 写代码完成数据处理和数据分析；
6. 按学术论文要求绘图；
7. 生成 README 和技术文档；
8. 根据用户反馈修改已有输出。

---

## 7. 核心功能模块设计

## 7.1 PPT 生成模块

### 7.1.1 用户输入

- 参考文件，例如 PDF、DOCX、PPTX、TXT；
- PPT 主题；
- 页数要求；
- 受众类型；
- 汇报场景；
- 语言要求；
- 风格要求；
- 是否需要图表；
- 是否需要 speaker notes；
- 是否需要参考文献页。

### 7.1.2 系统输出

- `.pptx` 文件；
- PPT 大纲；
- 每页标题；
- 每页正文；
- 图表或示意图建议；
- speaker notes；
- 可选 PDF 版本。

### 7.1.3 支持场景

- 根据论文生成 journal club PPT；
- 根据项目材料生成进展汇报 PPT；
- 根据商业资料生成路演 PPT；
- 根据技术文档生成教学 PPT；
- 根据报告生成总结型 PPT。

### 7.1.4 可选模板

- 学术汇报模板；
- 商务汇报模板；
- 项目进展模板；
- 极简图文模板；
- 科技风模板；
- 教学课件模板。

---

## 7.2 报告生成模块

### 7.2.1 用户输入

- 报告主题；
- 参考文件；
- 报告类型；
- 字数要求；
- 章节要求；
- 语气要求；
- 是否需要摘要；
- 是否需要图表；
- 是否需要引用。

### 7.2.2 系统输出

- `.docx` 文件；
- `.pdf` 文件；
- Markdown 版本；
- 报告大纲；
- Executive summary；
- 图表和表格。

### 7.2.3 支持报告类型

- 项目报告；
- 调研报告；
- 技术报告；
- 实验报告；
- 商业分析报告；
- 数据分析报告；
- 周报 / 月报 / 年终总结。

---

## 7.3 论文辅助模块

### 7.3.1 产品边界

该模块定位为 **论文写作辅助**，而不是完全替代用户写论文。

### 7.3.2 功能范围

- 论文大纲生成；
- Introduction 草稿；
- Results 描述；
- Discussion 逻辑优化；
- Figure legend 生成；
- Abstract 生成；
- Cover letter 生成；
- Response to reviewers 生成；
- 语言润色；
- 参考文献格式整理；
- 根据目标期刊调整语气。

### 7.3.3 系统输出

- `.docx` 文件；
- Markdown 文本；
- 分 section 的可编辑内容；
- 修改建议；
- 审稿回复草稿。

---

## 7.4 公众号推文生成模块

### 7.4.1 用户输入

- 主题；
- 参考文件；
- 目标读者；
- 平台类型；
- 字数要求；
- 风格要求；
- 是否需要标题候选；
- 是否需要配图建议。

### 7.4.2 系统输出

- 推文正文；
- 标题候选；
- 摘要；
- 小标题；
- 金句；
- 封面图 prompt；
- 配图建议；
- 结尾互动语。

### 7.4.3 可选风格

- 科普风；
- 商业分析风；
- 个人成长风；
- 学术转科普风；
- 新闻评论风；
- 干货教程风。

---

## 7.5 数据处理与分析模块

### 7.5.1 用户输入

- Excel / CSV 文件；
- 分析目标；
- 分组变量；
- 时间变量；
- 指标变量；
- 统计方法要求；
- 绘图风格要求；
- 输出格式要求。

### 7.5.2 系统输出

- 清洗后的数据文件；
- Python 分析代码；
- 图表文件；
- 数据分析报告；
- 可复现 notebook 或 `.py` 文件。

### 7.5.3 功能范围

- 缺失值处理；
- 异常值处理；
- 数据格式转换；
- 分组均值计算；
- 描述性统计；
- 回归分析；
- 时间序列分析；
- 柱状图；
- 折线图；
- 箱线图；
- 显著性标注；
- 学术论文风格图表；
- 自动生成图注。

---

## 7.6 代码辅助模块

### 7.6.1 用户输入

- 项目文件；
- 代码片段；
- 错误信息；
- 功能需求；
- 重构目标；
- 前端或后端开发要求。

### 7.6.2 系统输出

- 修改建议；
- 新代码文件；
- README；
- 技术文档；
- 项目结构调整方案；
- 前端页面代码；
- API 接口设计；
- 单元测试。

### 7.6.3 功能范围

- 代码解释；
- 代码重构；
- bug 修复；
- 项目结构优化；
- 前后端接口设计；
- 单元测试生成；
- README 生成；
- Skill 文档生成。

---

## 8. 产品使用路径

## 8.1 路径一：自然语言直接生成

适合熟悉系统的用户。

### 示例

用户输入：

> 请根据这个 PDF 生成一个 15 页的学术汇报 PPT，风格简洁，包含演讲稿。

系统自动识别：

- 任务类型：PPT 生成；
- 输入文件：PDF；
- 输出格式：PPTX；
- 页数：15；
- 风格：学术简洁；
- 附加要求：speaker notes。

执行流程：

```text
解析 PDF → 生成大纲 → 生成每页内容 → 设计页面布局 → 质量审查 → 导出 PPTX
```

---

## 8.2 路径二：功能入口式生成

适合普通用户。

前端提供功能卡片：

- 做 PPT；
- 写报告；
- 写论文；
- 写公众号；
- 数据分析；
- 写代码 / 改代码。

用户点击某一功能后进入表单页面。

以“做 PPT”为例，表单字段包括：

- 上传文件；
- 输入主题；
- 选择模板；
- 选择页数；
- 选择语言；
- 选择风格；
- 是否需要演讲稿；
- 是否需要图表；
- 点击生成。

---

## 8.3 路径三：模板驱动生成

适合高频任务。

用户先选择模板，例如：

- 学术论文汇报 PPT；
- 年终总结报告；
- 数据分析报告；
- 公众号科普文；
- GitHub README；
- 技术文档。

然后系统根据模板要求引导用户填写必要信息。

---

## 8.4 路径四：已有文件修改

适合用户已经有初稿或系统已经生成过文件的情况。

流程：

```text
用户上传已有 PPT / DOCX / Markdown
  ↓
系统解析已有内容
  ↓
用户提出修改要求
  ↓
系统定位需要修改的部分
  ↓
只修改对应页面 / 段落 / 图表
  ↓
重新导出文件
```

示例修改需求：

- 把第 3 页内容变得更简洁；
- 把这个报告改成更正式的语气；
- 把图 2 改成论文风格；
- 把这个 README 改成 GitHub 高赞项目风格；
- 把第 6 页重新写；
- 增加一个总结页。

---

## 8.5 路径五：交互式逐步生成

适合复杂任务，例如论文、报告、重要 PPT。

流程：

```text
第一步：系统生成大纲
第二步：用户确认或修改大纲
第三步：系统生成正文
第四步：用户修改风格或内容
第五步：系统导出最终文件
```

优点：

- 质量更高；
- 用户可控性更强；
- 适合高价值任务；
- 能减少一次性生成导致的结构错误。

---

## 9. 系统总体架构

WorkForge AI 采用分层式多 Agent 架构：

```text
用户输入
  ↓
Coordinator Agent
  ↓
Task Router
  ↓
LLM Provider Router
  ↓
Task Agent
  ↓
Sub Agents
  ↓
Skill Registry
  ↓
Template Library
  ↓
Quality Review
  ↓
Export Engine
  ↓
最终文件
```

---

## 9.5 大模型接口与 LLM Provider 配置层

为了满足不同用户、不同部署环境和不同成本控制需求，WorkForge AI 不应绑定某一个固定大模型服务，而应提供统一的 **LLM Provider 配置层**。用户可以在前端或配置文件中自行选择模型调用方式，例如云端 API、本地大模型、Ollama 或自定义兼容接口。

### 9.5.1 设计目标

LLM Provider 配置层需要实现以下目标：

1. **多 Provider 接入**：支持 OpenAI-compatible API、本地模型服务、Ollama、vLLM、LM Studio、Transformers 本地推理等方式。
2. **统一调用接口**：上层 Agent 不直接依赖具体模型厂商，而是通过统一的 `LLMClient` 或 `ModelProvider` 调用。
3. **用户可配置**：用户可以在前端页面填写 API Key、Base URL、模型名称、温度、最大 token 等参数。
4. **任务级模型选择**：不同任务可使用不同模型，例如大纲规划用高质量模型，格式转换用低成本模型，本地隐私任务用本地模型。
5. **成本与隐私可控**：用户可根据预算、隐私要求、速度要求选择云端或本地模型。
6. **可扩展**：后续可以继续增加 Anthropic、Gemini、DeepSeek、Qwen、Moonshot、智谱、阿里云百炼、火山方舟等 Provider。

### 9.5.2 支持的 LLM 调用方式

| 调用方式 | 典型场景 | 关键配置 | 说明 |
|---|---|---|---|
| OpenAI-compatible API | 使用 OpenAI、DeepSeek、Qwen、Moonshot 等兼容接口 | API Key、Base URL、Model Name | 最适合作为第一版统一接口 |
| Ollama | 本地运行 Llama、Qwen、DeepSeek-R1 Distill 等模型 | Ollama Host、Model Name | 适合本地开发和隐私场景 |
| 本地 Transformers | 直接用 Hugging Face Transformers 加载模型 | Model Path、Device、Precision | 灵活但工程复杂度较高 |
| vLLM | 本地或服务器高性能推理 | Endpoint、Model Name | 适合生产环境部署开源模型 |
| LM Studio | 桌面本地模型 API | Local Server URL、Model Name | 适合非工程用户本地调用 |
| 自定义 HTTP Provider | 用户已有内部模型服务 | Endpoint、Headers、Payload Schema | 适合企业内部部署 |

第一版建议优先支持：

1. OpenAI-compatible API；
2. Ollama；
3. 自定义 Base URL。

这样既能覆盖云端 API，也能覆盖本地大模型调用。

### 9.5.3 前端配置入口

前端应增加一个 **模型配置页面 / Model Settings 页面**，允许用户配置默认模型和任务模型。

配置项包括：

- Provider 类型：OpenAI-compatible API / Ollama / Local / Custom；
- API Key；
- Base URL；
- Model Name；
- Temperature；
- Max Tokens；
- Timeout；
- 是否启用流式输出；
- 是否作为默认模型；
- 连接测试按钮；
- 当前模型可用状态。

示例交互路径：

```text
用户进入 Settings
  ↓
选择 Provider：Ollama
  ↓
填写 Host：http://localhost:11434
  ↓
选择模型：qwen2.5:7b / llama3.1:8b / deepseek-r1:7b
  ↓
点击 Test Connection
  ↓
保存为默认模型
```

对于 API 模型：

```text
用户进入 Settings
  ↓
选择 Provider：OpenAI-compatible API
  ↓
填写 Base URL、API Key、Model Name
  ↓
点击 Test Connection
  ↓
保存配置
```

### 9.5.4 任务级模型路由

系统不应只允许一个全局模型，而应支持任务级别或阶段级别的模型选择。

| 阶段 | 推荐模型类型 | 原因 |
|---|---|---|
| 需求理解 | 高质量通用模型 | 需要准确理解用户意图 |
| 文件摘要 | 长上下文模型或本地模型 | 需要处理大量文本 |
| PPT 大纲 | 高质量推理模型 | 需要结构规划能力 |
| 普通文本扩写 | 成本较低模型 | 任务难度较低 |
| 数据分析代码生成 | 代码能力强的模型 | 需要 Python / R / SQL 能力 |
| 最终审查 | 高质量模型 | 需要发现逻辑和格式问题 |

可以设计一个 `ModelRouter`：

```text
Task Type + Stage + User Preference
  ↓
ModelRouter
  ↓
选择合适 Provider 和 Model
  ↓
LLMClient 调用
```

### 9.5.5 后端抽象设计

后端应提供统一抽象，避免 Agent 直接调用具体模型 API。

```python
class BaseLLMProvider:
    def chat(self, messages, **kwargs):
        raise NotImplementedError

    def stream_chat(self, messages, **kwargs):
        raise NotImplementedError

    def test_connection(self):
        raise NotImplementedError
```

具体实现：

```text
OpenAICompatibleProvider
OllamaProvider
LocalTransformersProvider
VLLMProvider
CustomHTTPProvider
```

Agent 调用时只依赖统一接口：

```python
llm = model_router.get_model(task_type="ppt", stage="outline")
result = llm.chat(messages, temperature=0.3)
```

### 9.5.6 安全与密钥管理

由于用户需要自行配置 API Key，系统必须考虑密钥安全。

建议：

1. API Key 不应明文显示在前端。
2. 后端数据库中应加密保存 API Key。
3. 前端只显示脱敏后的 Key，例如 `sk-****abcd`。
4. 支持用户删除或更新模型配置。
5. 本地部署版本可以允许 `.env` 文件配置。
6. SaaS 版本应区分用户级配置和系统级默认配置。
7. 任务日志中不得记录完整 API Key。

### 9.5.7 配置优先级

建议模型配置按以下优先级生效：

```text
任务级指定模型
  > 用户默认模型
  > 项目默认模型
  > 系统默认模型
```

### 9.5.8 异常处理

模型调用失败时，系统应提供可理解的错误提示。常见错误包括：

- API Key 无效；
- Base URL 无法访问；
- 模型名称不存在；
- Ollama 服务未启动；
- 本地模型显存不足；
- 请求超时；
- 上下文长度超限；
- 速率限制；
- 余额不足。

系统应支持自动重试、切换备用模型、提示用户修改配置，并保留当前任务进度，避免任务完全丢失。

### 9.5.9 推荐配置策略

| 任务 | 默认策略 |
|---|---|
| PPT / 报告 / 论文大纲 | 优先使用高质量 API 模型 |
| 文件摘要和粗略改写 | 可使用本地 Ollama 模型 |
| 数据分析代码 | 使用代码能力较强的模型 |
| 最终质量审查 | 使用高质量 API 模型 |
| 隐私文件处理 | 优先推荐本地模型 |

这可以体现系统的灵活性：既支持高质量云端模型，也支持用户本地模型。

---

## 10. Agent 协作机制

## 10.1 第一层：Coordinator Agent

Coordinator Agent 是系统总控 Agent。

职责：

- 理解用户需求；
- 判断任务类型；
- 管理上传文件；
- 调用 Task Router；
- 分配任务给对应 Task Agent；
- 控制 token 使用；
- 判断是否需要追问用户；
- 管理最终输出；
- 管理用户反馈和修改请求。

---

## 10.2 第二层：Task Agent

每类任务都有一个 Task Agent。

可包括：

- PPT Agent；
- Report Agent；
- Paper Agent；
- WeChat Article Agent；
- Data Analysis Agent；
- Code Agent。

职责：

- 制定任务计划；
- 选择模板；
- 选择 Skills；
- 拆分子任务；
- 调用 Sub Agents；
- 汇总结果；
- 做质量检查；
- 判断是否可以进入最终输出。

---

## 10.3 第三层：Sub Agents

Sub Agent 只负责明确的局部任务。

### PPT 任务中的 Sub Agents

- Outline Agent：负责 PPT 大纲；
- Content Agent：负责每页内容；
- Design Agent：负责视觉布局；
- Chart Agent：负责图表；
- Speaker Notes Agent：负责演讲稿；
- Review Agent：负责质量检查；
- Export Agent：负责生成 PPTX。

### 报告任务中的 Sub Agents

- Structure Agent；
- Summary Agent；
- Section Writing Agent；
- Table Agent；
- Formatting Agent；
- Review Agent；
- Export Agent。

### 数据分析任务中的 Sub Agents

- Data Loading Agent；
- Data Cleaning Agent；
- Statistics Agent；
- Plot Agent；
- Interpretation Agent；
- Code Review Agent；
- Export Agent。

---

## 11. 标准任务执行流程

所有任务应尽量遵循统一流程：

```text
用户输入
  ↓
需求解析
  ↓
任务类型识别
  ↓
文件解析
  ↓
模板选择
  ↓
任务拆解
  ↓
Skill 检索与调用
  ↓
Sub Agents 执行
  ↓
Task Agent 汇总
  ↓
质量审查
  ↓
生成最终文件
  ↓
用户反馈
  ↓
局部修改
  ↓
重新导出
```

---

## 12. Skill 体系设计

## 12.1 Skill 的核心原则

系统不应一次性把所有 Skill 内容读入上下文，而应根据任务类型和当前阶段动态调用相关 Skill。

每个 Skill 都应该是一个独立文件，并包含明确的使用条件、输入、流程、输出和质量标准。

---

## 12.2 Skill 文件标准结构

每个 Skill 建议采用以下 Markdown 格式：

```markdown
# Skill Name

## Purpose
这个 Skill 解决什么问题。

## When to Use
什么时候调用这个 Skill。

## Inputs
需要什么输入。

## Workflow
执行步骤。

## Output
输出格式。

## Quality Checklist
输出前检查标准。

## Common Failure Cases
常见错误。

## Revision Strategy
用户不满意时如何修改。
```

---

## 12.3 通用基础 Skills

| Skill | 作用 |
|---|---|
| File Understanding Skill | 解析用户上传文件，提取结构、主题和关键信息 |
| Requirement Clarification Skill | 将用户自然语言需求整理成明确任务规格 |
| Outline Planning Skill | 为 PPT、报告、论文、推文生成大纲 |
| Style Control Skill | 控制语气、格式、受众和表达风格 |
| Quality Review Skill | 最终输出前做质量检查 |
| Citation / Reference Skill | 处理参考文献、来源引用和文献格式 |
| Revision Skill | 根据用户反馈在已有结果上修改 |
| Export Skill | 将内容导出为目标文件格式 |

---

## 12.4 PPT 相关 Skills

| Skill | 作用 |
|---|---|
| PPT Outline Skill | 生成页级别 PPT 结构 |
| Slide Content Skill | 把大纲转成每页内容 |
| Slide Design Skill | 决定页面布局、图文比例和视觉风格 |
| Speaker Notes Skill | 生成每页演讲稿 |
| Chart Suggestion Skill | 根据内容建议图表或示意图 |
| PPT Export Skill | 导出 `.pptx` 文件 |
| Slide Review Skill | 检查每页是否过密、逻辑是否连贯 |

---

## 12.5 报告相关 Skills

| Skill | 作用 |
|---|---|
| Report Structure Skill | 生成报告章节结构 |
| Executive Summary Skill | 生成摘要和核心结论 |
| Long-form Writing Skill | 生成正式报告正文 |
| Table Generation Skill | 生成报告表格 |
| Report Formatting Skill | 控制标题层级、编号和图表说明 |
| DOCX Export Skill | 导出 Word 文件 |
| Report Review Skill | 检查完整性、正式性和结构逻辑 |

---

## 12.6 论文相关 Skills

| Skill | 作用 |
|---|---|
| Paper Outline Skill | 设计论文结构 |
| Literature Summary Skill | 总结文献 |
| Introduction Writing Skill | 写 Introduction |
| Results Writing Skill | 根据数据或图表写 Results |
| Discussion Writing Skill | 写 Discussion |
| Figure Legend Skill | 写 figure legends |
| Abstract Skill | 写摘要 |
| Journal Style Skill | 根据目标期刊调整风格 |
| Reviewer Response Skill | 写审稿回复 |

---

## 12.7 公众号推文相关 Skills

| Skill | 作用 |
|---|---|
| Article Angle Skill | 确定文章切入角度 |
| Title Generation Skill | 生成标题 |
| Popularization Skill | 把复杂内容转成通俗表达 |
| Social Media Style Skill | 控制公众号、小红书、知乎、LinkedIn 等平台风格 |
| Hook Writing Skill | 写开头吸引读者 |
| CTA Skill | 生成结尾引导语 |
| Cover Image Prompt Skill | 生成封面图 prompt |

---

## 12.8 数据分析相关 Skills

| Skill | 作用 |
|---|---|
| Data Cleaning Skill | 清洗数据 |
| Statistical Analysis Skill | 做统计分析 |
| Academic Plot Skill | 按论文风格画图 |
| Regression Analysis Skill | 做回归 |
| Time Series Analysis Skill | 处理时间序列 |
| Excel Processing Skill | 读写 Excel |
| Python Code Generation Skill | 生成可运行 Python 脚本 |
| Data Report Skill | 把分析结果写成报告 |

---

## 12.9 代码开发相关 Skills

| Skill | 作用 |
|---|---|
| Project Structure Analysis Skill | 分析项目结构 |
| Refactor Planning Skill | 给出重构方案 |
| Frontend Generation Skill | 生成前端代码 |
| Backend API Skill | 设计后端接口 |
| README Generation Skill | 生成 README |
| Technical Documentation Skill | 生成技术文档 |
| Test Generation Skill | 生成测试代码 |
| Debugging Skill | 定位 bug |

---

## 13. 模板体系设计

每种任务都应该有多个模板，模板可以由用户选择，也可以由系统根据任务自动推荐。

### 13.1 PPT 模板

```text
templates/
  ppt/
    academic_presentation.yaml
    business_report.yaml
    project_progress.yaml
    teaching_slides.yaml
    minimalist_slides.yaml
```

### 13.2 报告模板

```text
templates/
  report/
    technical_report.yaml
    business_analysis_report.yaml
    data_analysis_report.yaml
    research_report.yaml
    annual_summary.yaml
```

### 13.3 公众号模板

```text
templates/
  article/
    wechat_popular_science.yaml
    wechat_business_analysis.yaml
    zhihu_deep_analysis.yaml
    xiaohongshu_note.yaml
```

### 13.4 代码文档模板

```text
templates/
  code/
    github_readme.yaml
    technical_documentation.yaml
    api_documentation.yaml
    skill_documentation.yaml
```

---

## 14. 文件上传与解析模块

### 14.1 支持文件类型

- PDF；
- DOCX；
- PPTX；
- TXT；
- Markdown；
- CSV；
- XLSX；
- Python 文件；
- 项目压缩包。

### 14.2 解析内容

- 文本；
- 表格；
- 标题结构；
- 图片说明；
- 代码结构；
- 元数据；
- 文档摘要；
- 可检索 chunks。

### 14.3 文件元数据

系统应保留：

- 文件 ID；
- 文件名；
- 文件类型；
- 文件大小；
- 上传时间；
- 解析状态；
- 文件摘要；
- 解析文本路径；
- 原始文件路径。

---

## 15. 输出质量标准

## 15.1 通用输出标准

任何任务输出前都必须检查：

1. 是否满足用户明确要求；
2. 是否使用了用户上传的参考文件；
3. 是否存在明显事实错误；
4. 是否结构完整；
5. 是否格式正确；
6. 是否有空段落、重复内容或乱码；
7. 是否符合指定语言；
8. 是否符合指定风格；
9. 是否生成了用户要求的文件格式；
10. 文件是否可以被下载和正常打开。

---

## 15.2 PPT 输出标准

检查项：

- 页数是否符合要求；
- 每页是否有明确标题；
- 每页内容是否过密；
- 逻辑顺序是否自然；
- 是否有封面和总结页；
- 图表是否清晰；
- 字体和布局是否统一；
- 是否需要 speaker notes；
- 是否符合模板风格；
- PPTX 是否可正常打开。

---

## 15.3 报告输出标准

检查项：

- 是否有标题；
- 是否有摘要或 executive summary；
- 是否有清晰章节；
- 是否有结论；
- 是否语气正式；
- 是否图表编号正确；
- 是否引用来源；
- 是否格式统一；
- DOCX / PDF 是否可正常打开。

---

## 15.4 论文输出标准

检查项：

- 是否符合学术写作逻辑；
- 是否区分 Introduction / Results / Discussion；
- 是否避免过度夸大；
- 是否术语一致；
- 是否保留科学不确定性；
- figure legend 是否清楚；
- 是否符合目标期刊风格；
- 引用格式是否一致。

---

## 15.5 公众号输出标准

检查项：

- 标题是否有吸引力；
- 开头是否有 hook；
- 内容是否通俗；
- 小标题是否清晰；
- 是否适合目标读者；
- 是否避免过度学术化；
- 结尾是否有总结或互动；
- 是否有配图建议。

---

## 15.6 数据分析输出标准

检查项：

- 数据是否成功读取；
- 缺失值是否处理；
- 分组是否正确；
- 指标计算是否正确；
- 图表是否符合学术风格；
- 坐标轴是否清楚；
- 图例是否清楚；
- 统计方法是否说明；
- 代码是否可复现；
- 输出文件是否完整。

---

## 15.7 代码输出标准

检查项：

- 是否满足需求；
- 是否可以运行；
- 是否有必要注释；
- 是否符合项目结构；
- 是否没有明显语法错误；
- 是否避免硬编码；
- 是否有错误处理；
- 是否有 README 或使用说明；
- 是否说明运行命令。

---

## 16. 用户不满意时的修改流程

用户不满意时，系统应基于已有结果修改，而不是完全重新生成。

---

## 16.1 修改请求分类

### 16.1.1 内容修改

示例：

- 这部分写得太浅；
- 第 3 页补充机制图；
- 报告里加入更多数据分析。

### 16.1.2 风格修改

示例：

- 更正式一点；
- 更像学术论文；
- 更适合公众号读者。

### 16.1.3 结构修改

示例：

- 把第二部分提前；
- 增加一个背景章节；
- PPT 从 10 页扩展到 15 页。

### 16.1.4 格式修改

示例：

- 改成 Word；
- 图表改成黑白风格；
- 标题编号改成 1.1 / 1.2。

### 16.1.5 错误修正

示例：

- 这里理解错了；
- 这个数据不对；
- 引用不准确。

---

## 16.2 修改流程

```text
用户提出修改意见
  ↓
系统识别修改类型
  ↓
定位需要修改的内容区域
  ↓
判断是否需要重新调用 Skill
  ↓
局部修改
  ↓
Task Agent 审查
  ↓
重新导出文件
  ↓
保存新版本
```

---

## 16.3 版本管理

每次生成或修改都保存一个版本。

示例：

```text
Version 1: 初始生成
Version 2: 修改第 3 页
Version 3: 改成更商务风格
Version 4: 增加图表
```

用户可以：

- 查看历史版本；
- 对比版本差异；
- 回退到旧版本；
- 下载任意版本。

---

## 17. 前端页面设计

## 17.1 首页

首页包含：

- 产品名称；
- 一句话介绍；
- 文件上传入口；
- 自然语言输入框；
- 功能入口卡片；
- 最近任务记录。

核心交互：

```text
上传文件 + 输入需求 + 点击生成
```

---

## 17.2 任务创建页

包含：

- 任务类型选择；
- 文件上传区；
- 模板选择区；
- 参数设置区；
- 自然语言补充要求；
- 开始生成按钮。

### PPT 参数示例

- 页数；
- 风格；
- 语言；
- 是否需要演讲稿；
- 是否需要图表。

### 报告参数示例

- 字数；
- 格式；
- 语气；
- 是否需要目录；
- 是否需要引用。

### 数据分析参数示例

- 分组变量；
- 时间变量；
- 指标变量；
- 图表类型；
- 输出格式。

---

## 17.3 任务执行页

这是产品体验的关键页面。

需要动态展示：

- 当前执行阶段；
- 当前 Agent；
- 当前 Agent 输出；
- 任务进度；
- 已完成子任务；
- 可展开的中间结果；
- 错误信息；
- 重新执行按钮。

### 进度展示示例

```text
任务进度：
[√] 文件解析完成
[√] 大纲生成完成
[进行中] 正在生成第 4-6 页内容
[等待中] 最终审查
[等待中] 文件导出
```

### Agent 时间线示例

```text
Coordinator Agent:
已识别任务类型：PPT 生成

PPT Agent:
已选择模板：学术汇报模板

Outline Agent:
已生成 12 页大纲

Content Agent:
正在生成每页内容

Review Agent:
发现第 5 页信息过密，已建议拆分
```

---

## 17.4 结果预览页

包含：

- 最终文件下载；
- 内容预览；
- 修改输入框；
- 修改历史；
- 重新导出按钮。

示例：

```text
生成结果：
- 下载 PPTX
- 下载 PDF
- 查看大纲
- 查看演讲稿

修改：
“请把整体风格改得更商务一点”
“请减少文字，增加图示”
“请把第 6 页重新写”
```

---

## 17.5 模型配置页

模型配置页用于让用户自行配置大模型调用方式。

页面应包含：

- Provider 类型选择；
- API Key 输入框；
- Base URL 输入框；
- Model Name 输入框或下拉选择；
- Temperature、Max Tokens、Timeout 等高级参数；
- 是否启用流式输出；
- Test Connection 按钮；
- 保存为默认模型按钮；
- 当前配置状态提示；
- 删除配置按钮。

建议支持多个模型配置，并允许用户设置：

- 默认模型；
- PPT 任务默认模型；
- 报告任务默认模型；
- 数据分析任务默认模型；
- 本地隐私任务默认模型。

---

## 17.6 历史任务页

保存用户历史任务：

- 任务名称；
- 任务类型；
- 创建时间；
- 使用文件；
- 输出文件；
- 任务状态；
- 继续修改按钮。

---

## 18. 后端核心数据结构建议

## 18.1 User

```json
{
  "user_id": "string",
  "username": "string",
  "created_at": "datetime"
}
```

---

## 18.2 Project

```json
{
  "project_id": "string",
  "user_id": "string",
  "project_name": "string",
  "description": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 18.3 Task

```json
{
  "task_id": "string",
  "project_id": "string",
  "task_type": "ppt/report/paper/wechat/data/code",
  "user_requirement": "string",
  "status": "pending/running/reviewing/completed/failed",
  "template_id": "string",
  "llm_provider_id": "string",
  "model_routing_policy": "string",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 18.4 File

```json
{
  "file_id": "string",
  "task_id": "string",
  "file_name": "string",
  "file_type": "pdf/docx/pptx/csv/xlsx/txt",
  "file_path": "string",
  "parsed_text_path": "string",
  "summary": "string",
  "uploaded_at": "datetime"
}
```

---

## 18.5 AgentRun

```json
{
  "run_id": "string",
  "task_id": "string",
  "agent_name": "string",
  "status": "running/completed/failed",
  "input": "string",
  "output": "string",
  "created_at": "datetime"
}
```

---

## 18.6 SkillCall

```json
{
  "skill_call_id": "string",
  "task_id": "string",
  "skill_name": "string",
  "input": "string",
  "output": "string",
  "token_usage": "number",
  "created_at": "datetime"
}
```

---

## 18.7 LLMProviderConfig

```json
{
  "provider_id": "string",
  "user_id": "string",
  "provider_type": "openai_compatible/ollama/local_transformers/vllm/custom_http",
  "display_name": "string",
  "base_url": "string",
  "api_key_encrypted": "string",
  "model_name": "string",
  "temperature": "number",
  "max_tokens": "number",
  "timeout_seconds": "number",
  "streaming_enabled": "boolean",
  "is_default": "boolean",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

## 18.8 ModelRoutingRule

```json
{
  "rule_id": "string",
  "user_id": "string",
  "task_type": "ppt/report/paper/wechat/data/code/all",
  "stage": "planning/summarization/generation/review/export/all",
  "provider_id": "string",
  "priority": "number",
  "enabled": "boolean"
}
```

---

## 18.9 OutputFile

```json
{
  "output_id": "string",
  "task_id": "string",
  "version": "number",
  "file_type": "pptx/docx/pdf/md/py/png",
  "file_path": "string",
  "created_at": "datetime"
}
```

---

## 19. 任务状态机设计

### 19.1 正常任务状态

```text
created
  ↓
file_uploaded
  ↓
file_parsed
  ↓
planning
  ↓
skill_selecting
  ↓
model_selecting
  ↓
generating
  ↓
reviewing
  ↓
exporting
  ↓
completed
```

---

## 19.2 失败状态

```text
failed_file_parse
failed_generation
failed_model_connection
failed_model_authentication
failed_model_context_length
failed_export
failed_review
```

---

## 19.3 修改状态

```text
revision_requested
  ↓
revision_planning
  ↓
revision_generating
  ↓
revision_reviewing
  ↓
revision_completed
```

---

## 20. 产品核心亮点

## 20.1 按需调用 Skill，节省 token

系统不会一次性读取所有 Skill，而是根据任务类型和当前阶段动态检索并加载相关 Skill。

## 20.2 多 Agent 协作

任务不是由单个 Agent 直接生成，而是由 Coordinator Agent、Task Agent 和 Sub Agents 分层协作完成。

## 20.3 有质量审查机制

生成结果必须经过 Quality Review，只有通过检查后才允许导出。

## 20.4 支持局部修改

用户不满意时，系统会定位需要修改的部分，在已有结果上修改，而不是重新生成全部内容。

## 20.5 面向最终文件交付

系统最终输出的不只是文本，而是 PPTX、DOCX、PDF、Markdown、Python 代码、图表等真实文件。

## 20.6 支持复杂办公场景

系统覆盖 PPT、报告、论文辅助、公众号推文、数据分析、代码开发等多个高频场景。

## 20.7 支持用户自定义大模型接口

系统不绑定单一模型服务，用户可以自行配置云端 API、本地大模型、Ollama 或自定义兼容接口。这样既可以满足高质量生成场景，也可以满足隐私保护、成本控制和本地开发需求。

---

## 21. MVP 开发计划

## 21.1 MVP 1：单任务闭环

优先实现一个核心任务：

> 根据上传 PDF / DOCX 生成 PPTX

功能包括：

- 文件上传；
- 文件解析；
- 用户输入需求；
- PPT 大纲生成；
- PPT 内容生成；
- PPTX 导出；
- 文件下载。

目标：证明系统可以从用户输入到最终文件交付跑通完整链路。

---

## 21.2 MVP 2：加入 Agent 执行可视化

新增功能：

- 当前 Agent 状态；
- 任务进度条；
- 中间结果展示；
- 日志流式输出；
- 错误提示。

目标：提升用户对系统执行过程的感知。

---

## 21.3 MVP 3：加入 LLM Provider 配置层

新增功能：

- 支持 OpenAI-compatible API 配置；
- 支持 Ollama 本地模型配置；
- 支持自定义 Base URL；
- 支持 Test Connection；
- 支持默认模型保存；
- 后端统一封装 LLM Provider 接口；
- Agent 调用模型时通过 ModelRouter 获取模型。

目标：让用户能够根据自己的环境和预算自由选择大模型调用方式。

---

## 21.4 MVP 4：加入 Skill Registry

新增功能：

- Skill 文件管理；
- 根据任务检索 Skill；
- 只加载相关 Skill；
- 记录 Skill 调用历史。

目标：验证“按需调用 Skill 节省 token”的核心设计。

---

## 21.5 MVP 5：加入修改闭环

新增功能：

- 用户对结果提出修改意见；
- 系统定位修改位置；
- 生成新版本；
- 支持历史版本下载。

目标：实现真实办公系统所需的迭代能力。

---

## 21.6 MVP 6：扩展任务类型

依次加入：

1. 报告生成；
2. 公众号推文；
3. 数据分析；
4. 代码文档生成；
5. 论文辅助写作。

---

## 22. 推荐项目目录结构

```text
workforge-ai/
  backend/
    app/
      api/
      agents/
        coordinator/
        task_agents/
        sub_agents/
      skills/
        common/
        ppt/
        report/
        paper/
        article/
        data_analysis/
        code/
      templates/
        ppt/
        report/
        article/
        code/
      services/
        file_parser/
        llm_provider/
        model_router/
        export_engine/
        task_manager/
        skill_registry/
      models/
      utils/
    tests/
    main.py

  frontend/
    src/
      pages/
        Home/
        TaskCreate/
        TaskRunning/
        ResultPreview/
        ModelSettings/
        History/
      components/
        FileUploader/
        TaskCard/
        AgentTimeline/
        ProgressPanel/
        ResultViewer/
      api/
      store/
      styles/
    package.json

  storage/
    uploads/
    parsed/
    outputs/
    versions/

  docs/
    product_design.md
    api_design.md
    skill_design.md
    mvp_plan.md

  README.md
```

---

## 23. 典型使用案例

## 23.1 Case 1：论文转 PPT

用户输入：

> 请根据这篇 PDF 论文生成一个 15 页 journal club PPT，适合研究生组会汇报，要求包含背景、方法、主要结果、创新点和讨论问题。

系统输出：

- 15 页 PPTX；
- 每页 speaker notes；
- 3 个讨论问题；
- 一页总结。

---

## 23.2 Case 2：Excel 数据分析

用户输入：

> 请根据这个 Excel，按照 HIGH 和 LOW 两组分别计算 ROS 和 ROA 的均值，并画出随时间变化的折线图，要求符合学术论文风格。

系统输出：

- 清洗后的 Excel；
- Python 分析代码；
- 折线图 PNG；
- 数据分析报告 DOCX。

---

## 23.3 Case 3：项目 README 生成

用户输入：

> 请根据这个项目代码，生成一个 GitHub 高赞项目风格的 README。

系统输出：

- README.md；
- 项目简介；
- 安装方法；
- 使用示例；
- 项目结构；
- API 文档；
- Roadmap。

---

## 23.4 Case 4：报告转公众号

用户输入：

> 请把这个技术报告改写成一篇适合公众号发布的科普推文，语气通俗，标题要有吸引力。

系统输出：

- 推文正文；
- 5 个标题；
- 摘要；
- 配图建议；
- 封面图 prompt。

---

## 24. 需要进一步明确的问题

后续正式开发前，需要继续明确以下问题：

1. 第一版 MVP 是否只聚焦 PDF / DOCX 到 PPTX？
2. 用户是否需要登录系统？
3. 文件是否长期保存？
4. 是否支持用户删除历史文件？
5. Agent 的中间输出展示到什么粒度？
6. 是否允许用户查看完整执行日志？
7. 模板是否允许用户自定义？
8. Skill 是否允许用户自定义或上传？
9. 输出文件是否需要支持在线预览？
10. 是否需要任务队列和异步执行？
11. 是否需要接入数据库保存任务历史？
12. 是否需要支持多人协作？
13. 第一版支持哪些 LLM Provider？
14. API Key 是只保存在本地，还是加密保存到数据库？
15. 是否允许同一个任务不同阶段使用不同模型？
16. 是否需要支持模型调用成本统计？

---

## 25. 当前阶段最优先事项

建议当前阶段优先完成以下内容：

1. 确定产品名称和定位；
2. 固定第一版 MVP 功能范围；
3. 明确第一个任务类型的完整工作流；
4. 设计 Skill 文件格式；
5. 设计 Task Agent 和 Sub Agent 的职责；
6. 搭建前后端项目结构；
7. 实现 LLM Provider 配置层，至少支持 OpenAI-compatible API 和 Ollama；
8. 实现文件上传和解析；
9. 实现第一个任务的生成和导出；
9. 实现前端任务执行状态展示；
10. 实现用户反馈后的局部修改。

---

## 26. 项目最终描述

WorkForge AI 是一个基于 Harness 框架的多 Agent 智能办公生产系统。

它通过任务路由、模板选择、Skill 按需调用、多 Agent 协作、质量审查和版本化修改机制，将用户上传的参考文件和自然语言需求转化为可交付的办公成果，包括 PPT、报告、论文辅助文本、公众号推文、数据分析图表和代码文档。

系统的目标不是简单聊天，而是完成从需求理解到最终文件生成的完整工作流。

