# 成员 A 后端交接文档

## 1. 当前阶段定位

本阶段只开发后端，不改前端。

成员 A 已围绕第一阶段 MVP 完成后端基础能力建设，主要包括：

- 密码规则统一
- 用户免费生成次数
- 使用记录表
- 起名记录表
- 反馈记录表
- 知识库文件表
- Alembic 迁移
- 起名历史记录
- 多轮反馈保存
- 使用次数扣减记录
- 企业知识库上传状态记录
- 企业知识库文件列表/详情接口
- RabbitMQ 消费者状态回写
- 后端依赖清单 `requirements.txt`
- 环境变量示例 `.env.example`
- 成员 A 接口测试清单 `test_member_a.http`

## 2. 已完成内容

### 2.1 密码规则统一

后端密码最小长度已调整为 6 位，与前端注册提示保持一致。

涉及文件：

- `ainame/schemas/user_schemas.py`

### 2.2 用户免费生成次数

规则已实现：

- 新用户默认 3 次免费生成机会
- 首次生成起名任务扣 1 次
- 多轮反馈不扣次数
- 次数不足时禁止新建起名任务
- 查看历史记录不扣次数
- 上传企业知识库不扣次数

涉及文件：

- `ainame/models/user.py`
- `ainame/repository/user_repo.py`
- `ainame/routers/name_router.py`
- `ainame/schemas/user_schemas.py`

数据库变化：

- `user` 表新增 `free_quota` 字段，默认值为 3

### 2.3 新增业务表

已新增模型文件：

- `ainame/models/business.py`

包含 4 张表：

- `usage_records`
- `name_records`
- `name_feedbacks`
- `knowledge_files`

### 2.4 Alembic 迁移

已创建并执行迁移。

迁移文件：

- `ainame/alembictable/versions/6f0a8d1c2b3e_add_user_free_quota.py`
- `ainame/alembictable/versions/9c2a1f7e4d8b_add_business_records_tables.py`

新环境执行：

```powershell
alembic upgrade head
```

## 3. 数据表与业务接入

### 3.1 usage_records

用途：记录每次使用额度消耗。

当前已接入：

- `/names/generate`
- `/names/get_names`

首次生成成功后，会写入：

- `user_id`
- `record_id`
- `usage_type = name_generate`
- `cost_count = 1`
- `before_quota`
- `after_quota`

### 3.2 name_records

用途：保存每次首次起名任务。

当前已接入：

- `/names/generate`
- `/names/get_names`

保存输入参数、输出结果、类别、`thread_id`。删除采用软删除：`is_deleted=True`。

### 3.3 name_feedbacks

用途：保存多轮反馈记录。

当前已接入：

- `/names/feedback`

反馈成功后会更新 `name_records.result_data`，同时写入 `name_feedbacks`。

### 3.4 knowledge_files

用途：保存企业知识库上传文件和处理状态。

当前已接入：

- `/knowledge/upload`
- `/knowledge/files`
- `/knowledge/files/{file_id}`
- `rag_worker.py`

状态流转：

```text
pending -> processing -> completed
pending -> processing -> failed
```

## 4. 后端接口说明

### 4.1 首次起名

```http
POST /names/generate
```

行为：检查并扣减免费次数，调用 AI 工作流，创建 `name_records` 和 `usage_records`。

返回新增字段：

```json
{
  "thread_id": "...",
  "record_id": 1,
  "names": []
}
```

### 4.2 多轮反馈

```http
POST /names/feedback
```

行为：不扣免费次数，只允许基于当前用户自己的 `thread_id` 继续优化，保存反馈历史并更新最新结果。

### 4.3 历史记录

```http
GET /names/records?skip=0&limit=20
GET /names/records/{record_id}
DELETE /names/records/{record_id}
```

说明：用户只能访问和删除自己的记录。详情接口返回 `feedbacks`。

### 4.4 企业知识库文件

```http
POST /knowledge/upload
GET /knowledge/files?skip=0&limit=20
GET /knowledge/files/{file_id}
```

说明：上传后返回 `knowledge_file_id` 和状态；列表/详情接口用于前端展示处理进度。

## 5. 配置与依赖

已新增：

- `ainame/requirements.txt`
- `ainame/.env.example`

`settings` 已支持环境变量读取，同时保留旧默认值以兼容本地环境。

已改为从 `settings` 读取：

- `DB_URI`
- `REDIS_URL`
- `RABBITMQ_URL`
- 邮箱配置
- `JWT_SECRET_KEY`
- `DEEPSEEK_API_KEY`

注意：项目没有自动加载 `.env` 文件。如果要直接读取 `.env`，后续可引入 `python-dotenv` 或由启动脚本注入环境变量。

## 6. 测试说明

已新增接口测试清单：

- `ainame/test_member_a.http`

覆盖：

- 首次生成
- 多轮反馈
- 历史列表
- 历史详情
- 删除历史
- 上传知识库文件
- 知识库文件列表
- 知识库文件详情

当前未新增完整 pytest 自动化测试，原因是本地环境缺少部分 AI/RAG/RabbitMQ 依赖，完整服务导入会失败。建议在依赖整理完成后补自动化接口测试。

## 7. 验证情况

已完成：

- Python 语法检查通过
- 新增仓储可导入
- 新增 schema 可导入
- Alembic 迁移已执行成功
- 数据库表和字段已确认存在

当前完整路由导入在本地环境可能因依赖缺失失败：

- `aio_pika`
- `langchain_ollama`

可通过安装 `requirements.txt` 中依赖解决。

## 8. 新增/修改文件清单

### 模型层

- `ainame/models/user.py`
- `ainame/models/business.py`
- `ainame/models/__init__.py`

### 仓储层

- `ainame/repository/user_repo.py`
- `ainame/repository/name_record_repo.py`
- `ainame/repository/knowledge_file_repo.py`

### 路由层

- `ainame/routers/name_router.py`
- `ainame/routers/rag_router.py`
- `ainame/routers/auth_router.py`

### Schema

- `ainame/schemas/user_schemas.py`
- `ainame/schemas/name_schemas.py`
- `ainame/schemas/knowledge_schemas.py`

### 配置与依赖

- `ainame/settings/__init__.py`
- `ainame/core/redisconfig.py`
- `ainame/requirements.txt`
- `ainame/.env.example`

### Worker

- `ainame/rag_worker.py`

### 测试/文档

- `ainame/test_member_a.http`
- `docs/PROJECT_PLAN.md`
- `docs/BACKEND_API_NOTES.md`
- `docs/BACKEND_HANDOFF.md`

## 9. 仍可后续增强

成员 A 第一阶段核心任务已经完成。后续如果还有时间，可增强：

- 使用记录查询接口，如 `GET /usage/records`
- 自动化 pytest 接口测试
- 自动加载 `.env`
- 更细的知识库文件删除/重建接口
- 将 RabbitMQ 队列名也放入 settings

## 10. 交接结论

按 `PROJECT_PLAN.md`，成员 A 第一阶段后端职责已经完成并补齐收尾项：

- 免费次数闭环
- 历史记录闭环
- 反馈记录闭环
- 使用记录闭环
- 知识库文件状态闭环
- RabbitMQ 状态回写
- 依赖与环境变量说明
- 手动接口测试清单

接下来可以交给成员 B 接前端页面，成员 C 继续优化 AI 工作流、RAG 和域名校验稳定性。