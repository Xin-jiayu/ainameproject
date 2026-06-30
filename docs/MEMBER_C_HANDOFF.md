# 成员 C 交接文档

## 1. 当前职责范围

成员 C 负责 AI 工作流、RAG 知识库接入、Prompt 质量优化、起名分类路由、反馈记忆链路和基础校验逻辑。

不归成员 C 主责的内容：

- 用户表、额度字段、业务记录表等数据库结构
- Alembic 迁移维护
- 登录注册、JWT 鉴权、免费次数扣减
- 前端页面布局和交互体验

这些内容分别由成员 A 后端/数据库、成员 B 前端继续维护。

## 2. 本轮完成内容

### 2.1 三类起名路由确认

文件：

- `ainame/core/workflow.py`

当前路由关系：

```text
人名   -> human_naming_node
企业名 -> company_naming_node
宠物名 -> pet_naming_node
```

已处理点：

- 工作流节点名称和路由返回值已经对齐。
- 未知 `category` 会抛出明确错误，不再静默失败。
- 原先结束边里企业节点未正确结束的问题已经修正。

未知分类错误示例：

```text
未知起名分类: '游戏角色'，允许值: 人名、企业名、宠物名
```

### 2.2 thread_id 记忆逻辑确认

文件：

- `ainame/core/workflow.py`
- `ainame/routers/name_router.py`

当前规则：

- `/names/generate` 首次生成时创建新的 `thread_id`
- `thread_id` 会传入 LangGraph config：

```python
{"configurable": {"thread_id": thread_id}}
```

- `/names/feedback` 复用前端传来的旧 `thread_id`
- 反馈接口会先按 `thread_id` 查历史记录，查不到则返回 404
- 反馈不会新建 `thread_id`

成员 B 前端必须保存首次生成返回的 `thread_id`，后续反馈原样传回。

### 2.3 人名 Prompt 优化

目标：更稳定输出 5 个名字，包含出处、寓意、解释。

当前要求：

- 恰好 5 个候选
- 每个名字必须包含姓氏
- `reference` 写出处或灵感来源
- `moral` 同时写寓意和解释
- 人名场景不需要域名：
  - `domain = ""`
  - `domain_status = "不适用"`

### 2.4 企业名 Prompt 优化

目标：结合行业、品牌调性、知识库内容，生成更像商业品牌的名字。

当前要求：

- 恰好 5 个候选
- 结合行业、业务方向、目标客群、品牌调性或核心诉求
- 主动吸收用户知识库里的产品特征、企业规则、品牌禁忌、关键词和差异化卖点
- 名字要像真实商业品牌，而不是说明词、技术参数或口号
- `reference` 说明创意来源
- `moral` 说明品牌寓意和商业解释
- `domain` 生成简短 `.com` 域名建议
- `domain_status` 先填“正在查询...”，后端再统一覆盖

### 2.5 宠物/IP Prompt 优化

目标：更可爱、更好记、更有画面感。

当前要求：

- 恰好 5 个候选
- 名字可爱、顺口、容易呼唤
- 优先 1-3 个字
- 可使用叠音、昵称感、小名感、拟声感、轻微反差萌
- 结合毛色、体型、动作、性格、习惯或 IP 设定
- 每个名字都要让人联想到具体画面
- 宠物/IP 场景不需要域名：
  - `domain = ""`
  - `domain_status = "不适用"`

## 3. RAG 与企业知识库说明

相关文件：

- `ainame/routers/rag_router.py`
- `ainame/core/rag_service.py`
- `ainame/rag_worker.py`
- `ainame/core/workflow.py`

当前流程：

1. 前端调用 `/knowledge/upload` 上传 TXT/PDF。
2. 后端保存文件并创建 `knowledge_files` 记录，初始状态为 `pending`。
3. 后端投递 RabbitMQ 任务。
4. `rag_worker.py` 消费任务并构建用户专属知识库。
5. 企业起名时，`company_naming_node` 使用 `user_id + other` 检索知识库内容。
6. 检索结果进入企业名 Prompt。

成员 A 注意：

- RabbitMQ 必须启动。
- `knowledge_files` 表必须存在。
- 上传接口字段名固定为 `file`。
- 成功上传不代表知识库已经构建完成，只代表任务已入队。

成员 B 注意：

- 上传成功后不要提示“学习完成”，建议提示“上传成功，后台处理中”。
- 企业名生成前，如果刚上传文件，可能需要等待 worker 完成处理。

## 4. 和成员 A 的交接重点

### 4.1 数据库和迁移归属

以下属于成员 A 范围：

- `user.free_quota`
- `usage_records`
- `name_records`
- `name_feedbacks`
- `knowledge_files`
- Alembic 版本链
- `alembic_version` 表维护

本地联调时遇到过的问题：

```text
Unknown column 'user.free_quota' in 'field list'
```

原因：代码模型已经有 `free_quota`，但 MySQL 表结构未升级。

当前本地数据库状态已经执行到：

```text
9c2a1f7e4d8b
```

并已存在：

```text
user
email_code
name_records
name_feedbacks
usage_records
knowledge_files
```

说明：这些表后续需要保留，当前不要回退。

### 4.2 后端接口依赖

AI 工作流依赖：

- `DEEPSEEK_API_KEY`
- PostgreSQL LangGraph checkpointer，当前代码里 `DB_URI = postgresql://postgres:123456@localhost:5432/ainame`
- MySQL 业务库，用于用户、历史、额度、知识库文件记录
- RabbitMQ，用于知识库异步任务
- Redis，用于验证码

注意：当前 workflow 内部的 LangGraph 记忆库连接写死为 PostgreSQL 地址，和业务库 `settings.DB_URI` 不是同一个配置。成员 A 后续可以考虑把它也迁到 `.env`。

## 5. 和成员 B 的交接重点

### 5.1 请求地址

当前前端请求地址应为：

```js
const BASE_URL = "http://127.0.0.1:8000";
```

之前发现过写死局域网地址导致接口打不通：

```js
http://192.168.1.91:8000
```

本机联调时应使用 `127.0.0.1:8000` 或 `localhost:8000`。

### 5.2 登录和 token

`/names/generate`、`/names/feedback`、`/knowledge/upload` 都需要：

```http
Authorization: Bearer <token>
```

如果后端日志出现：

```text
POST /names/generate 401 Unauthorized
```

优先检查：

- 是否先登录
- token 是否保存到 `uni` storage
- 请求头是否携带 `Authorization`

### 5.3 前端必须使用的响应字段

首次生成响应：

```json
{
  "thread_id": "...",
  "record_id": 1,
  "names": []
}
```

反馈响应：

```json
{
  "thread_id": "...",
  "record_id": 1,
  "names": []
}
```

`names` 中每项字段：

```json
{
  "name": "",
  "reference": "",
  "moral": "",
  "domain": "",
  "domain_status": ""
}
```

前端展示建议：

- 人名：展示 `name`、`reference`、`moral`；隐藏空 `domain`
- 企业名：展示 `domain` 和 `domain_status`
- 宠物/IP：展示 `name`、`reference`、`moral`；隐藏空 `domain`

## 6. 测试说明

新增静态/轻量测试：

- `ainame/tests/test_workflow_routing.py`
- `ainame/tests/test_thread_memory.py`
- `ainame/tests/test_human_prompt.py`
- `ainame/tests/test_company_prompt.py`
- `ainame/tests/test_pet_prompt.py`

这些测试不会调用 DeepSeek、MySQL、PostgreSQL、RabbitMQ，主要用于锁定：

- 三类 category 路由
- 未知 category 明确报错
- 首次生成新建 `thread_id`
- 反馈复用旧 `thread_id`
- 三类 Prompt 的关键约束

运行方式：

```powershell
cd D:\python\ainameproject
conda run -n fastapi-env python -m unittest .\ainame\tests\test_pet_prompt.py .\ainame\tests\test_company_prompt.py .\ainame\tests\test_human_prompt.py .\ainame\tests\test_workflow_routing.py .\ainame\tests\test_thread_memory.py
```

最近一次结果：

```text
Ran 10 tests ... OK
```

## 7. 当前已知注意事项

1. `settings` 已支持自动加载 `ainame/.env`。
2. `requirements.txt` 已加入 `python-dotenv`。
3. `docs/MEMBER_B_API_EXAMPLES.md` 已整理接口请求和响应样例。
4. 部分旧文档在 Windows 终端里显示乱码，但文件本身按项目现状继续保留。
5. `/names/get_names` 是旧接口，会生成 `legacy-*` 记录，不是推荐的记忆链路。建议成员 B 使用 `/names/generate`。
6. 企业名会执行 `.com` 域名查询，网络或 whois 服务不稳定时可能拖慢响应。

## 8. 后续建议

给成员 A：

- 将 workflow 里的 PostgreSQL checkpoint `DB_URI` 改为从 `.env` 读取。
- 明确 MySQL 与 PostgreSQL 的职责边界。
- 检查 Alembic 版本链，避免再出现数据库记录了不存在 revision 的情况。
- 给 `/names/generate` 增加更友好的异常处理，避免 AI/RAG 外部依赖失败时直接 500。

给成员 B：

- 启动时如果没有 token，建议自动跳转登录页。
- 企业知识库上传成功后，文案改为“上传成功，后台处理中”。
- 反馈按钮点击前确认 `thread_id` 存在，否则提示用户先生成一次。
- 按 `docs/MEMBER_B_API_EXAMPLES.md` 联调三条主接口。

给成员 C：

- 后续可以继续优化反馈场景 Prompt，让人名和宠物名也能更好利用历史结果。
- 企业名 RAG 可以加入知识库为空时的降级提示。
- 结构化输出可考虑按不同 category 拆 schema，避免人名/宠物名也被迫带 `domain` 字段。
