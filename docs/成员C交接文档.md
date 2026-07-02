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

## 4. 结果字段

当前已经按 category 拆 schema：

- `HumanNameSchema`
- `CompanyNameSchema`
- `PetNameSchema`
- `NameSchema` 作为前端兼容超集

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

企业名保留 `domain`、`domain_status`、`risk_level`、`risk_reason`、`score`、`score_detail`、`score_reason`。

## 5. Prompt 与评分

人名：

- 恰好 5 个候选。
- 每个名字必须包含姓氏。
- `reference` 写出处或灵感来源。
- `moral` 同时写寓意和解释。
- 评分重点：`phonology` 音韵、`meaning` 寓意、`surname_fit` 姓氏匹配。

企业名：

- 恰好 5 个候选。
- 结合行业、业务方向、目标客群、品牌调性、核心诉求。
- 如果知识库有结果，必须吸收产品特点、目标客群、核心卖点、品牌调性、禁忌词、企业规则、关键词或差异化定位。
- 禁忌词必须作为命名避讳。
- 评分重点：`brand_sense` 品牌感、`industry_fit` 行业匹配、`spreadability` 传播性、`differentiation` 差异化。

宠物/IP：

- 恰好 5 个候选。
- 名字短小、可爱、顺口，适合日常呼喊。
- 结合毛色、体型、动作、性格、习惯或 IP 设定。
- 评分重点：`cuteness` 可爱度、`imagery` 画面感、`callability` 呼喊顺口度。

## 6. 多轮反馈规则

反馈接口：

```http
POST /names/feedback
```

请求示例：

```json
{
  "thread_id": "...",
  "category": "brand",
  "feedback": "保留清新感，但名字更短一点"
}
```

当前规则：

- 反馈复用旧 `thread_id`，不会新建线程。
- 后端按 `thread_id` 查询历史记录。
- 后端把上一轮 `result_data` 格式化成 `history_names` 注入 workflow。
- Prompt 先读取上一轮候选名，不把反馈当全新任务。
- 保留用户没有否定的候选名特点。
- 只修改用户指出的问题。
- 反馈后仍然返回恰好 5 个候选名。

## 7. AI 输出异常兜底

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

## 8. RAG 与企业知识库

接口：

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
- 超长内容追加 `【内容过长已截断】`。

## 9. RabbitMQ 消费与失败重试

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

RabbitMQ 只用于知识库文件处理，不扩展到起名主流程异步化。

## 10. 成员 A 交接点

- `knowledge_files` 表字段必须存在：`status/error_message/retry_count/is_deleted/processed_at/deleted_at`。
- Alembic 版本链需要保持一致。
- RabbitMQ、MySQL、PostgreSQL、Redis、DeepSeek key 都需要在 `.env` 配好。
- `LANGGRAPH_CHECKPOINT_DB_URI` 建议指向可用 PostgreSQL。
- checkpoint 不可用时当前代码支持内存兜底，但线程记忆不会跨进程持久化。

## 11. 成员 B 交接点

前端必须保存：

- `thread_id`
- `record_id`

起名、反馈、知识库接口都需要：

```http
Authorization: Bearer <token>
```

知识库上传成功后，不要提示“学习完成”，建议提示“上传成功，后台处理中”。

知识库文件列表建议展示：

- `status`
- `error_message`
- `retry_count`
- 删除按钮
- 失败时的重试按钮

当 `retry_count >= 3` 时，前端应提示重新上传文件。

## 12. 测试清单

成员 C 相关测试：

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

说明：部分测试只做 AST/Prompt/Schema 检查，不会真实调用 DeepSeek、RabbitMQ、MySQL 或 PostgreSQL。

## 13. 已知注意事项

1. 当前起名主流程仍是同步 HTTP 请求，尚未异步化。
2. RabbitMQ 只负责知识库文件处理。
3. 企业名会触发 `.com` 域名查询，外部网络不稳定时可能影响响应时间。
4. `NameSchema` 是前端兼容超集，人名和宠物/IP 也能看到空的企业字段。
5. Windows 终端偶尔会把旧中文文档显示成乱码，优先以 UTF-8 方式读取。
