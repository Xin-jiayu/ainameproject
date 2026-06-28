# 后端接口与运行说明

## 1. 起名接口

### 1.1 首次起名

`POST /names/generate`

说明：创建一个新的起名任务，成功后扣 1 次免费额度，并写入 `name_records` 与 `usage_records`。

成功返回包含：

```json
{
  "thread_id": "...",
  "record_id": 1,
  "names": []
}
```

错误：

- `403`：免费生成次数已用完，暂时无法新建起名任务

### 1.2 多轮反馈

`POST /names/feedback`

说明：基于已有 `thread_id` 继续优化，不扣免费额度。成功后更新 `name_records.result_data`，并写入 `name_feedbacks`。

错误：

- `404`：起名记录不存在，无法继续优化

### 1.3 历史列表

`GET /names/records?skip=0&limit=20`

说明：只返回当前登录用户自己的未删除记录。

### 1.4 历史详情

`GET /names/records/{record_id}`

说明：返回当前记录详情，并包含该记录的反馈历史 `feedbacks`。

### 1.5 删除历史记录

`DELETE /names/records/{record_id}`

说明：软删除当前用户自己的记录，设置 `is_deleted=True`。

## 2. 企业知识库接口

### 2.1 上传文件

`POST /knowledge/upload`

说明：上传文件后创建 `knowledge_files` 记录，初始状态为 `pending`，并投递 RabbitMQ 任务。

成功返回：

```json
{
  "result": "success",
  "knowledge_file_id": 1,
  "status": "pending",
  "message": "文件 xxx 上传成功！后台正在为您构建专属知识库，请稍候测试起名功能。"
}
```

### 2.2 知识库文件列表

`GET /knowledge/files?skip=0&limit=20`

说明：返回当前用户上传过的知识库文件，按更新时间倒序排序。

### 2.3 知识库文件详情

`GET /knowledge/files/{file_id}`

说明：只能查看当前用户自己的文件状态。

状态说明：

- `pending`：已上传，等待队列处理
- `processing`：消费者正在处理
- `completed`：知识库构建完成
- `failed`：处理失败，错误写入 `error_message`

## 3. 数据库迁移

新环境需要在后端目录执行：

```powershell
alembic upgrade head
```

当前最新版本：

```text
9c2a1f7e4d8b
```

## 4. 配置与依赖

已新增：

- `requirements.txt`
- `.env.example`

`settings` 已支持从环境变量读取：

- `DB_URI`
- `REDIS_URL`
- `RABBITMQ_URL`
- `MAIL_*`
- `JWT_SECRET_KEY`
- `DEEPSEEK_API_KEY`

项目目前不会自动加载 `.env` 文件；如果要自动加载，后续可以加 `python-dotenv`。

## 5. 接口测试清单

已新增：

- `test_member_a.http`

用于手动验证成员 A 第一阶段后端主链路。