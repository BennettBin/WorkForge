# WorkForge AI 核心数据模型契约（步骤 5）

版本：`v1.0`  
日期：`2026-05-04`  
依据文档：`develop_guide/product_design.md`、`develop_guide/implementation_plan.md`

## 1. Task
必填字段：
- `task_id`（唯一标识）
- `task_type`（MVP-1 取值：`ppt`）
- `user_requirement`
- `status`
- `created_at`
- `updated_at`

可选字段：
- `project_id`
- `template_id`
- `llm_provider_id`
- `model_routing_policy`
- `expires_at`

约束：
- `status` 必须属于状态机定义集合。
- `task_type` 在 MVP-1 固定为 `ppt`。

有效样例：`task_id` 非空、`task_type=ppt`、`status=created`。  
无效样例：`task_id` 为空或 `status` 非法值。

## 2. File
必填字段：
- `file_id`
- `task_id`
- `file_name`
- `file_type`
- `file_path`
- `uploaded_at`

可选字段：
- `parsed_text_path`
- `summary`
- `file_size_bytes`
- `parse_status`
- `expires_at`

约束：
- `file_type` 仅允许：`pdf/docx/doc/txt/ppt/pptx`（MVP-1）。
- `file_size_bytes` 不得超过 `50MB`。
- 单任务最多绑定 1 个源文件。

有效样例：`file_type=pdf` 且大小 <= 50MB。  
无效样例：`file_type=zip` 或大小 > 50MB。

## 3. AgentRun
必填字段：
- `run_id`
- `task_id`
- `agent_name`
- `status`
- `created_at`

可选字段：
- `input`
- `output`
- `error_message`
- `started_at`
- `finished_at`

约束：
- `status` 允许：`running/completed/failed`。
- 手动重跑必须追加新记录，不能覆盖旧记录。

有效样例：`status=running` 且 `run_id` 唯一。  
无效样例：`status=done` 或复用已存在 `run_id`。

## 4. SkillCall
必填字段：
- `skill_call_id`
- `task_id`
- `skill_name`
- `created_at`

可选字段：
- `input`
- `output`
- `token_usage`
- `duration_ms`

约束：
- `token_usage` 必须 >= 0。
- `skill_name` 不能为空字符串。

有效样例：`skill_name=outline_generation`、`token_usage=1200`。  
无效样例：`skill_name` 为空或 `token_usage=-1`。

## 5. LLMProviderConfig
必填字段：
- `provider_id`
- `user_id`
- `provider_type`
- `display_name`
- `model_name`
- `created_at`
- `updated_at`

可选字段：
- `base_url`
- `api_key_encrypted`
- `temperature`
- `max_tokens`
- `timeout_seconds`
- `streaming_enabled`
- `is_default`

约束：
- `provider_type` 允许：`openai_compatible/ollama/local_transformers/vllm/custom_http`。
- MVP-1 至少配置三类通道：在线 API、Ollama、本地 LLM。
- 默认在线通道策略：DeepSeek API。

有效样例：`provider_type=openai_compatible` 且配置了 `model_name`。  
无效样例：`provider_type=unknown_provider` 或缺少 `model_name`。

## 6. OutputFile
必填字段：
- `output_id`
- `task_id`
- `version`
- `file_type`
- `file_path`
- `created_at`

可选字段：
- `source_run_id`
- `checksum`

约束：
- `file_type` 在 MVP-1 固定为 `pptx`。
- 同一 `task_id` 下 `version` 必须递增且唯一。
- 新生成结果创建新版本，不覆盖历史版本。

有效样例：`version=2`、`file_type=pptx`。  
无效样例：重复 `version` 或 `file_type=exe`。

## 7. 验证测试结论
- 覆盖模型：Task、File、AgentRun、SkillCall、LLMProviderConfig、OutputFile（6/6）。
- 每个模型均提供了 1 个有效样例与 1 个无效样例判定规则（6/6）。
- 结论：满足步骤 5 验收标准。
