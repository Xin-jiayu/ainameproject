# 成员 A 第二阶段后端交接文档

更新时间：2026-07-01

## 1. 当前结论

成员 A 第二阶段的核心后端开发已经基本完成，当前重点从“开发功能”转为“启动验证、接口联调、接口文档补充和缺陷修复”。

本阶段已经围绕 `项目规划文档.md` 中的第二阶段目标，完成了以下方向：

- 第二阶段数据库表落地
- 知识库文件管理接口完善
- 敏感配置迁移到环境变量
- 关键接口日志、错误追踪和基础调用统计
- 候选名字结构化保存
- 候选名字收藏、选中、评分接口
- 域名矩阵接口
- 商标风险模拟接口
- 社媒风险模拟接口
- 订单与权益基础接口

## 2. 运行环境说明

本项目后端依赖 `fastapi-env` 虚拟环境。

后续验证、启动、安装依赖都应使用该虚拟环境，不要直接使用系统 Python。

常用命令示例：

```powershell
.\fastapi-env\Scripts\python.exe -m pip check
.\fastapi-env\Scripts\python.exe -m compileall .\ainame
```

后端启动建议在 `ainame` 目录执行：

```powershell
..\fastapi-env\Scripts\python.exe -m uvicorn main:app --reload
```

如果在项目根目录执行，需要按实际模块路径调整启动命令。

## 3. 已完成的数据表和迁移

### 3.1 第一阶段核心表

第一阶段已完成：

- `usage_records`
- `name_records`
- `name_feedbacks`
- `knowledge_files`
- `user.free_quota`

### 3.2 第二阶段新增表

第二阶段已完成：

- `name_candidates`
- `domain_checks`
- `trademark_checks`
- `social_name_checks`
- `orders`

### 3.3 knowledge_files 增强字段

`knowledge_files` 已补充：

- `retry_count`
- `is_deleted`
- `processed_at`
- `deleted_at`

### 3.4 Alembic 迁移

已执行到最新迁移：

```text
c4f8a2d1e9b0
```

新环境执行：

```powershell
alembic upgrade head
```

## 4. 已完成的后端能力

### 4.1 知识库文件管理

已完成接口：

- `GET /knowledge/files`
- `GET /knowledge/files/{file_id}`
- `DELETE /knowledge/files/{file_id}`
- `POST /knowledge/files/{file_id}/retry`

行为说明：

- 列表和详情默认过滤软删除文件
- 删除为软删除，不直接删除物理文件
- 失败文件可重试，重试时状态改为 `pending`
- 重试会重新投递 RabbitMQ 任务
- 消费者更新状态时，如果文件已经删除，不会再把它改回 `completed`

涉及文件：

- `ainame/routers/rag_router.py`
- `ainame/repository/knowledge_file_repo.py`
- `ainame/schemas/knowledge_schemas.py`

### 4.2 敏感配置迁移

已将敏感配置统一迁移到环境变量 / `ainame/.env`：

- `DB_URI`
- `POSTGRES_MEMORY_DB_URI`
- `REDIS_URL`
- `RABBITMQ_URL`
- `MAIL_USERNAME`
- `MAIL_PASSWORD`
- `MAIL_FROM`
- `JWT_SECRET_KEY`
- `DEEPSEEK_API_KEY`

涉及文件：

- `ainame/settings/__init__.py`
- `ainame/.env.example`
- `ainame/core/nametools.py`
- `ainame/core/workflow.py`
- `ainame/init_pg_memory.py`
- `ainame/core/mailtools.py`
- `ainame/redisdemo.py`

注意：

- `ainame/.env` 是本地文件，已被 `.gitignore` 忽略
- 修改 `JWT_SECRET_KEY` 后，旧 token 会全部失效，需要重新登录

### 4.3 接口日志、错误追踪和调用统计

已新增请求级观测能力：

- 每个请求生成或透传 `X-Request-ID`
- 记录 method、path、status、latency
- 未捕获异常记录堆栈
- 慢请求根据 `REQUEST_SLOW_MS` 打 warning
- 提供进程内基础统计

新增接口：

- `GET /ops/metrics`

涉及文件：

- `ainame/core/observability.py`
- `ainame/routers/ops_router.py`
- `ainame/main.py`
- `ainame/.env.example`

配置项：

```env
LOG_LEVEL=INFO
REQUEST_SLOW_MS=1000
```

### 4.4 候选名字接入

已将 AI 生成结果写入 `name_candidates`：

- `/names/generate` 成功后写入候选名字
- `/names/get_names` 成功后写入候选名字
- `/names/feedback` 成功后刷新该记录下的候选名字

候选名字支持字段：

- `name`
- `reference`
- `moral`
- `reason`
- `domain`
- `domain_status`
- `score`
- `is_selected`
- `is_favorite`

涉及文件：

- `ainame/routers/name_router.py`
- `ainame/repository/phase_two_repo.py`
- `ainame/schemas/name_schemas.py`

### 4.5 第二阶段 phase2 接口

新增路由文件：

- `ainame/routers/phase_two_router.py`

已挂载到：

- `ainame/main.py`

接口前缀：

```http
/phase2
```

## 5. 第二阶段接口清单

所有 `/phase2` 接口都需要登录态：

```http
Authorization: Bearer <access_token>
```

### 5.1 候选名字接口

查询某条记录下的候选名字：

```http
GET /phase2/records/{record_id}/candidates
```

收藏候选名：

```http
POST /phase2/candidates/{candidate_id}/favorite
```

取消收藏：

```http
DELETE /phase2/candidates/{candidate_id}/favorite
```

选中候选名：

```http
POST /phase2/candidates/{candidate_id}/select
```

更新候选名评分：

```http
PATCH /phase2/candidates/{candidate_id}/score
Content-Type: application/json

{
  "score": 88
}
```

### 5.2 域名矩阵接口

生成并保存域名校验结果：

```http
POST /phase2/records/{record_id}/domain-checks
```

默认校验：

- `.com`
- `.cn`
- `.ai`

读取已保存域名校验结果：

```http
GET /phase2/records/{record_id}/domain-checks
```

当前能力边界：

- `.com` 使用现有 whois 查询
- `.cn` 和 `.ai` 当前为 mock 结果

### 5.3 商标风险接口

生成并保存商标风险结果：

```http
POST /phase2/records/{record_id}/trademark-checks
```

读取已保存商标风险结果：

```http
GET /phase2/records/{record_id}/trademark-checks
```

当前能力边界：

- 当前为 mock 风险结果
- 不接真实商标第三方接口
- 默认 `provider = mock`

### 5.4 社媒风险接口

生成并保存社媒重名风险结果：

```http
POST /phase2/records/{record_id}/social-checks
```

读取已保存社媒风险结果：

```http
GET /phase2/records/{record_id}/social-checks
```

当前支持平台：

- `wechat`
- `douyin`
- `xiaohongshu`
- `weibo`

当前能力边界：

- 当前为 mock 风险结果
- 不做真实社媒爬取或批量查询

### 5.5 订单与权益接口

创建订单草稿：

```http
POST /phase2/orders
Content-Type: application/json

{
  "product_type": "quota",
  "amount": 9.9,
  "quota_delta": 10,
  "business_id": null,
  "extra_data": {
    "package_name": "10次生成包"
  }
}
```

查询订单列表：

```http
GET /phase2/orders?skip=0&limit=20
```

查询订单详情：

```http
GET /phase2/orders/{order_id}
```

模拟支付成功：

```http
POST /phase2/orders/{order_id}/mock-pay
```

模拟支付成功后：

- `orders.pay_status` 改为 `paid`
- `orders.paid_at` 写入支付时间
- `orders.before_quota` 写入支付前次数
- `orders.after_quota` 写入支付后次数
- `user.free_quota` 增加 `quota_delta`

当前能力边界：

- 当前是模拟支付
- 不接真实支付渠道

## 6. 重要联调注意事项

### 6.1 Token 格式

调用需要登录的接口时必须使用：

```http
Authorization: Bearer <token>
```

常见错误：

- 少了 `Bearer`
- `Bearer` 后没有空格
- token 带了引号
- 使用了旧 token
- 修改 `JWT_SECRET_KEY` 后没有重新登录

如果返回：

```json
{
  "detail": "Token格式非法或损坏"
}
```

优先重新登录获取新 token。

### 6.2 fastapi-env

依赖检查和服务启动要使用 `fastapi-env`，不要使用系统 Python。

### 6.3 mock 能力说明

当前第二阶段中以下能力是 mock：

- `.cn` 域名校验
- `.ai` 域名校验
- 商标风险
- 社媒风险
- 支付

需要在前端展示或演示说明中避免误导为真实第三方查询。

### 6.4 重复生成处理

当前实现中：

- 重复生成域名校验会先清理旧结果，再写入新结果
- 重复生成商标风险会先清理旧结果，再写入新结果
- 重复生成社媒风险会先清理旧结果，再写入新结果
- 重复支付已支付订单不会重复增加次数

## 7. 建议联调顺序

### 7.1 基础登录链路

1. 注册或使用已有账号
2. 登录获取 token
3. 确认请求头格式：

```http
Authorization: Bearer <token>
```

### 7.2 起名和候选名链路

1. 调用 `POST /names/generate`
2. 获取 `record_id`
3. 调用 `GET /phase2/records/{record_id}/candidates`
4. 确认候选名已经写入 `name_candidates`
5. 测试收藏、取消收藏、选中、评分接口

### 7.3 校验矩阵链路

1. 调用 `POST /phase2/records/{record_id}/domain-checks`
2. 调用 `GET /phase2/records/{record_id}/domain-checks`
3. 调用 `POST /phase2/records/{record_id}/trademark-checks`
4. 调用 `GET /phase2/records/{record_id}/trademark-checks`
5. 调用 `POST /phase2/records/{record_id}/social-checks`
6. 调用 `GET /phase2/records/{record_id}/social-checks`

### 7.4 知识库管理链路

1. 上传知识库文件
2. 查询文件列表
3. 查询文件详情
4. 如果处理失败，调用重试接口
5. 测试软删除

### 7.5 订单权益链路

1. 创建订单草稿
2. 查询订单列表和详情
3. 模拟支付
4. 确认用户 `free_quota` 增加
5. 重复调用模拟支付，确认不会重复加次数

## 8. 已修改或新增的主要文件

### 模型与迁移

- `ainame/models/business.py`
- `ainame/alembictable/versions/b7d2e9f4a6c1_add_phase_two_business_tables.py`
- `ainame/alembictable/versions/c4f8a2d1e9b0_add_social_name_checks.py`

### 仓储层

- `ainame/repository/knowledge_file_repo.py`
- `ainame/repository/phase_two_repo.py`
- `ainame/repository/name_record_repo.py`

### 路由层

- `ainame/routers/rag_router.py`
- `ainame/routers/name_router.py`
- `ainame/routers/phase_two_router.py`
- `ainame/routers/ops_router.py`

### Schema

- `ainame/schemas/knowledge_schemas.py`
- `ainame/schemas/name_schemas.py`

### 配置与工具

- `ainame/settings/__init__.py`
- `ainame/.env.example`
- `ainame/core/observability.py`
- `ainame/core/mailtools.py`
- `ainame/core/nametools.py`
- `ainame/core/workflow.py`
- `ainame/init_pg_memory.py`
- `ainame/redisdemo.py`

### 应用入口

- `ainame/main.py`

## 9. 当前剩余工作

成员 A 当前剩余工作主要是收尾，不是大功能开发。

### 必做

- 使用 `fastapi-env` 启动后端
- 跑完整第二阶段接口联调
- 将 `/phase2` 接口补充到成员 B 前端接口文档
- 根据联调结果修复 bug
- 明确 mock 能力边界，避免演示时误解

### 可选增强

- 给 `/phase2` 接口补 `.http` 测试文件
- 给订单增加更多产品类型枚举约束
- 给风险结果增加综合评分汇总接口
- 将接口调用统计从内存迁移到数据库或日志系统
- 将 `.cn`、`.ai`、商标、社媒逐步替换为真实服务商接口

## 10. 交接结论

成员 A 第二阶段后端主线已经打通：

- 数据表已具备
- 迁移已完成
- 核心接口已实现
- 候选名、校验矩阵、知识库管理、订单权益和配置安全都已有基础闭环

下一步建议优先做 `fastapi-env` 环境下的完整启动和接口联调，然后把接口说明交给成员 B 接前端页面。
