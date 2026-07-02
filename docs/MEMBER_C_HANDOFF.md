# 成员 C 交接文档

更新时间：2026-07-02

## 1. 职责范围

成员 C 负责 AI 工作流、三类起名 Prompt、结构化输出、反馈记忆、企业 RAG 知识库接入、RabbitMQ 知识库文件消费流程，以及这些能力的轻量测试。

不属于成员 C 主责：

- 用户、额度、订单、管理员等业务表和权限体系。
- Alembic 版本链维护。
- 前端页面交互和样式。
- 起名主流程异步化。当前只对知识库文件处理使用 RabbitMQ。

## 2. 核心代码位置

- `ainame/core/workflow.py`：LangGraph 起名工作流、三类 Prompt、反馈规则、AI 输出兜底。
- `ainame/schemas/name_schemas.py`：三类起名结果 schema、评分字段、风险字段。
- `ainame/core/rag_service.py`：企业知识库检索、降级文案、检索内容截断。
- `ainame/routers/name_router.py`：起名、反馈、历史记录接口。
- `ainame/routers/rag_router.py`：知识库上传、列表、详情、删除、失败重试接口。
- `ainame/rag_worker.py`：RabbitMQ 消费者，负责异步解析知识库文件。
- `ainame/repository/knowledge_file_repo.py`：知识库文件状态、失败原因、重试次数更新。

## 3. 三类起名工作流

当前路由：

```text
人名   -> human_naming_node
企业名 -> company_naming_node
宠物名 -> pet_naming_node
```

未知 `category` 会抛明确错误。

前端可传：

```text
person -> 人名
brand  -> 企业名
pet    -> 宠物名
```

推荐入口：

```http
POST /names/generate
POST /names/feedback
```

旧入口 `/names/get_names` 仍存在，但会生成 `legacy-*` 线程记录，不是推荐记忆链路。

## 4. 结果 schema 与字段

当前已经按 category 拆 schema：

- `HumanNameSchema`
- `CompanyNameSchema`
- `PetNameSchema`
- `NameSchema` 作为前端兼容超集。

前端仍可统一读取：

```json
{
  "name": "",
  "reference": "",
  "moral": "",
  "domain": null,
  "domain_status": null,
  "score": 88,
  "score_detail": {},
  "score_reason": "",
  "risk_level": null,
  "risk_reason": null
}
```

人名和宠物/IP 不强制 `domain`，后端会清空非企业名场景的 `domain/domain_status/risk_*`。

企业名保留：

- `domain`
- `domain_status`
- `risk_level`
- `risk_reason`
- `score`
- `score_detail`
- `score_reason`

## 5. 评分规则

所有候选名都有：

- `score`：综合分，0-100。
- `score_detail`：可解释维度。
- `score_reason`：评分理由。

兼容字段：

- `brand_sense`
- `memorability`
- `differentiation`
- `fit`
- `spreadability`

人名额外字段：

- `phonology`：音韵。
- `meaning`：寓意。
- `surname_fit`：姓氏匹配。

企业名额外字段：

- `industry_fit`：行业匹配。

宠物/IP 额外字段：

- `cuteness`：可爱度。
- `imagery`：画面感。
- `callability`：呼喊顺口度。

## 6. Prompt 当前规则

### 6.1 人名

- 恰好 5 个候选。
- 每个名字必须包含姓氏。
- `reference` 写出处或灵感来源。
- `moral` 同时写寓意和解释。
- 评分重点：音韵、寓意、姓氏匹配。
- 不需要真实域名。

### 6.2 企业名

- 恰好 5 个候选。
- 结合行业、业务方向、目标客群、品牌调性、核心诉求。
- 企业知识库如果有结果，必须吸收产品特点、目标客群、核心卖点、品牌调性、禁忌词、企业规则、关键词或差异化定位。
- 如果资料中出现禁用、避免、不要、禁忌等表达，必须作为命名避讳。
- `reference` 要体现行业、产品特点、品牌调性、知识库要点或商业定位。
- `moral` 要解释价值感、传播感、差异化，以及如何避开禁忌词或负面联想。
- 评分重点：品牌感、行业匹配、传播性、差异化。
- 企业名会生成 `.com` 域名建议，后端随后查询并覆盖 `domain_status`。

### 6.3 宠物/IP

- 恰好 5 个候选。
- 名字短小、可爱、顺口，适合日常呼喊。
- 结合毛色、体型、动作、性格、习惯或 IP 设定。
- 每个名字要有具体画面感。
- 评分重点：可爱度、画面感、呼喊顺口度。
- 不需要真实域名。

## 7. 多轮反馈规则

反馈接口：

```http
POST /names/feedback
```

请求必须带：

```json
{
  "thread_id": "...",
  "category": "brand",
  "feedback": "保留清新感，但名字更短一点"
}
```

当前规则：

- 反馈复用旧 `thread_id`，不会新建线程。
- 后端会按 `thread_id` 查询历史记录。
- 后端会把上一轮 `result_data` 格式化成 `history_names` 注入 workflow。
- Prompt 要求先读取上一轮候选名，不把反馈当全新任务。
- 保留用户没有否定的候选名特点。
- 只修改用户指出的问题。
- 人名、企业名、宠物/IP 三类都必须参考上一轮历史结果。
- 反馈后仍然返回恰好 5 个候选名。

## 8. AI 输出异常兜底

位置：`ainame/core/workflow.py`

当前规则：

- 结构化输出无效时进入 JSON fallback。
- JSON fallback 最多重试 3 次。
- 每次重试 Prompt 都追加“只返回 JSON”。
- AI 返回空列表时触发 fallback。
- 数量多于 5 个时截断。
- 数量少于 5 个时补齐。
- 字段缺失时补默认值。
- JSON 仍不可解析时抛 `NameGenerationError`。
- 路由捕获 `NameGenerationError`，返回 502，避免直接 500。

## 9. RAG 与企业知识库

相关接口：

```http
POST /knowledge/upload
GET /knowledge/files
GET /knowledge/files/{file_id}
DELETE /knowledge/files/{file_id}
POST /knowledge/files/{file_id}/retry
```

上传流程：

1. 前端上传 TXT/PDF，字段名固定为 `file`。
2. 后端保存文件。
3. 创建 `knowledge_files` 记录，初始状态 `pending`。
4. 投递 RabbitMQ 队列 `rag_document_queue`。
5. `rag_worker.py` 消费任务。
6. Worker 调用 `process_and_stor_file(file_path, user_id)` 写入当前用户专属 Chroma collection。

知识库 collection 名：

```text
user_{user_id}_docs
```

企业名检索时只检索当前用户自己的知识库。

RAG 降级文案：

- 未上传知识库：`用户尚未上传企业知识库，请根据用户当前输入和行业常识完成命名。`
- 已上传但无相关结果：`用户已上传企业知识库，但本次未检索到相关内容，请根据用户当前输入和行业常识完成命名。`
- 检索异常：`知识库检索服务暂时不可用，请根据用户当前输入和行业常识完成命名。`

检索内容长度限制：

- 单条文档最多 900 字符。
- 总上下文最多 1800 字符。
- 超长内容会追加 `【内容过长已截断】`。

## 10. RabbitMQ 消费与失败重试

相关文件：

- `ainame/routers/rag_router.py`
- `ainame/rag_worker.py`
- `ainame/repository/knowledge_file_repo.py`

状态流转：

```text
pending -> processing -> completed
pending -> processing -> failed
failed  -> pending -> processing -> completed / failed
```

失败时：

- `status = failed`
- `error_message = str(e)`
- `updated_at` 更新

重试入口：

```http
POST /knowledge/files/{file_id}/retry
```

当前重试规则：

- 只有 `failed` 状态可以重试。
- `processing` 状态返回 409。
- 本地文件不存在时返回 400。
- 最大重试次数为 3。
- 达到 3 次后返回：`文件处理失败次数已达到上限，请重新上传文件`。
- 未达到上限时：
  - `status -> pending`
  - `error_message -> None`
  - `retry_count + 1`
  - `processed_at -> None`
  - 重新投递 RabbitMQ。

注意：这套 RabbitMQ 机制只用于知识库文件处理，不扩展到起名主流程异步化。

## 11. 成员 A 交接点

成员 A 主要关注：

- `knowledge_files` 表字段必须存在：`status/error_message/retry_count/is_deleted/processed_at/deleted_at`。
- Alembic 版本链需要保持一致。
- RabbitMQ、MySQL、PostgreSQL、Redis、DeepSeek key 都需要在 `.env` 配好。
- `LANGGRAPH_CHECKPOINT_DB_URI` 建议指向可用 PostgreSQL。
- 如果 checkpoint 不可用，当前代码支持内存兜底，但线程记忆不会跨进程持久化。

## 12. 成员 B 交接点

前端必须保存：

- `thread_id`
- `record_id`

起名和反馈接口都需要：

```http
Authorization: Bearer <token>
```

知识库上传成功后，不要提示“学习完成”，建议提示：

```text
上传成功，后台处理中
```

知识库文件列表建议展示：

- `status`
- `error_message`
- `retry_count`
- 删除按钮
- 失败时的重试按钮

当 `retry_count >= 3` 时，前端应提示重新上传文件。

## 13. 测试清单

当前成员 C 相关测试：

- `ainame/tests/test_workflow_routing.py`
- `ainame/tests/test_thread_memory.py`
- `ainame/tests/test_human_prompt.py`
- `ainame/tests/test_company_prompt.py`
- `ainame/tests/test_pet_prompt.py`
- `ainame/tests/test_feedback_prompt_flow.py`
- `ainame/tests/test_structured_output_contract.py`
- `ainame/tests/test_workflow_llm_fallback.py`
- `ainame/tests/test_rag_service_fallback.py`
- `ainame/tests/test_knowledge_retry_policy.py`
- `ainame/tests/test_checkpoint_settings.py`

常用回归命令：

```powershell
cd D:\python
$env:PYTHONIOENCODING='utf-8'
$env:DB_URI='sqlite+aiosqlite:///./test.db'
$env:MAIL_USERNAME='test@example.com'
$env:MAIL_PASSWORD='test'
$env:JWT_SECRET_KEY='test-secret'
$env:RABBITMQ_URL='amqp://guest:guest@localhost:5672/'
$env:REDIS_URL='redis://localhost:6379/0'
$env:DEEPSEEK_API_KEY='test-key'
$env:POSTGRES_MEMORY_DB_URI='postgresql://postgres:postgres@localhost:5432/test'
conda run --no-capture-output -n fastapi-env python -m pytest `
  ainameproject\ainame\tests\test_workflow_llm_fallback.py `
  ainameproject\ainame\tests\test_thread_memory.py `
  ainameproject\ainame\tests\test_structured_output_contract.py `
  ainameproject\ainame\tests\test_feedback_prompt_flow.py `
  ainameproject\ainame\tests\test_rag_service_fallback.py `
  ainameproject\ainame\tests\test_company_prompt.py `
  ainameproject\ainame\tests\test_human_prompt.py `
  ainameproject\ainame\tests\test_pet_prompt.py `
  ainameproject\ainame\tests\test_knowledge_retry_policy.py
```

说明：部分测试只做 AST/Prompt/Schema 检查，不会真实调用 DeepSeek、RabbitMQ、MySQL 或 PostgreSQL。

## 14. 已知注意事项

1. 当前起名主流程仍是同步 HTTP 请求，尚未异步化。
2. RabbitMQ 只负责知识库文件处理。
3. 企业名会触发 `.com` 域名查询，外部网络不稳定时可能影响响应时间。
4. `NameSchema` 是前端兼容超集，人名和宠物/IP 也能看到空的企业字段。
5. `docs/成员C交接文档.md` 与本文件应保持内容同步。
6. Windows 终端偶尔会把旧中文文档显示成乱码，优先以 UTF-8 方式读取。

## 15. 后续建议

- 继续补充真实端到端联调记录，尤其是 RabbitMQ worker 启动和知识库上传。
- 如果起名响应时间成为瓶颈，再单独设计起名任务异步化，不要混入当前知识库 RabbitMQ 流程。
- 可为 RAG 文件处理增加更细的失败分类，例如文件格式错误、解析失败、Embedding 服务不可用、Chroma 写入失败。
- 可为企业名风险字段接入真实商标/社媒校验结果，而不是只保留初步风险说明。
