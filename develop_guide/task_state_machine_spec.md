# WorkForge AI 统一任务状态机规范（步骤 4）

版本：`v1.0`  
日期：`2026-05-04`  
依据文档：`develop_guide/product_design.md`、`develop_guide/implementation_plan.md`

## 1. 状态集合

正常状态：
- `created`
- `file_uploaded`
- `file_parsed`
- `planning`
- `skill_selecting`
- `model_selecting`
- `generating`
- `reviewing`
- `exporting`
- `completed`

失败状态：
- `failed_file_parse`
- `failed_generation`
- `failed_model_connection`
- `failed_model_authentication`
- `failed_model_context_length`
- `failed_export`
- `failed_review`

修订状态：
- `revision_requested`
- `revision_planning`
- `revision_generating`
- `revision_reviewing`
- `revision_completed`

## 2. 允许的状态迁移

主流程迁移：
- `created -> file_uploaded`
- `file_uploaded -> file_parsed`
- `file_parsed -> planning`
- `planning -> skill_selecting`
- `skill_selecting -> model_selecting`
- `model_selecting -> generating`
- `generating -> reviewing`
- `reviewing -> exporting`
- `exporting -> completed`

失败迁移：
- `file_uploaded -> failed_file_parse`
- `model_selecting -> failed_model_connection`
- `model_selecting -> failed_model_authentication`
- `generating -> failed_generation`
- `generating -> failed_model_context_length`
- `reviewing -> failed_review`
- `exporting -> failed_export`

修订迁移：
- `completed -> revision_requested`
- `revision_requested -> revision_planning`
- `revision_planning -> revision_generating`
- `revision_generating -> revision_reviewing`
- `revision_reviewing -> revision_completed`

重跑迁移（MVP-1）：
- 任意 `failed_* -> planning`（手动重跑）
- `revision_completed -> completed`（修订结果成为新可交付版本）

## 3. 状态机约束
- 未经 `file_uploaded` 禁止进入 `file_parsed`。
- 未经 `reviewing` 禁止进入 `exporting`。
- `completed` 后才允许进入 `revision_requested`。
- 所有失败状态必须记录失败原因与可追踪标识。

## 4. 验证测试（3 条典型流程走查）

成功流程：
- `created -> file_uploaded -> file_parsed -> planning -> skill_selecting -> model_selecting -> generating -> reviewing -> exporting -> completed`
- 结果：闭环成立。

失败流程（解析失败）：
- `created -> file_uploaded -> failed_file_parse -> planning`
- 结果：失败可回收并可重跑，闭环成立。

修订流程：
- `completed -> revision_requested -> revision_planning -> revision_generating -> revision_reviewing -> revision_completed -> completed`
- 结果：修订闭环成立。

结论：
- 3 条典型流程均能在状态机中闭环，满足步骤 4 验收要求。
