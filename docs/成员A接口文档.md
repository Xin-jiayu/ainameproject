# 成员 A 后端接口文档

更新时间：2026-07-01

## 1. 基础说明

后端基础地址示例：

```text
http://127.0.0.1:8000
```

除注册、登录、发送验证码外，业务接口都需要登录态：

```http
Authorization: Bearer <access_token>
```

注意：

- `Bearer` 后面必须有一个空格
- token 不要加引号
- 修改 `JWT_SECRET_KEY` 后，旧 token 会失效，需要重新登录
- 如果返回 `Token格式非法或损坏`，优先检查请求头格式和 token 是否过期/失效

## 2. 认证接口

### 2.1 发送邮箱验证码

```http
GET /auth/code?email=<email>
```

示例：

```http
GET http://127.0.0.1:8000/auth/code?email=test@example.com
```

成功返回：

```json
{
  "message": "验证码发送成功"
}
```

### 2.2 注册

```http
POST /auth/register
Content-Type: application/json
```

请求示例：

```json
{
  "email": "test@example.com",
  "username": "test",
  "password": "123456",
  "confirm_password": "123456",
  "code": "1234"
}
```

成功返回：

```json
{
  "message": "注册成功"
}
```

### 2.3 登录

```http
POST /auth/login
Content-Type: application/json
```

请求示例：

```json
{
  "email": "test@example.com",
  "password": "123456"
}
```

成功返回：

```json
{
  "user": {
    "id": 1,
    "email": "test@example.com",
    "username": "test",
    "free_quota": 3
  },
  "token": "xxxxx.yyyyy.zzzzz"
}
```

后续接口使用：

```http
Authorization: Bearer xxxxx.yyyyy.zzzzz
```

## 3. 起名主流程接口

### 3.1 首次起名

```http
POST /names/generate
Content-Type: application/json
Authorization: Bearer <access_token>
```

说明：

- 创建新的起名任务
- 成功后扣减 1 次免费次数
- 写入 `name_records`
- 写入 `usage_records`
- 写入 `name_candidates`
- 返回 `thread_id` 和 `record_id`

企业名请求示例：

```json
{
  "category": "企业名",
  "surname": "",
  "gender": "不限",
  "length": "四个字以内",
  "other": "一家做环保新材料的初创公司，希望名字有科技感、可信赖",
  "exclude": ["康", "旧"]
}
```

人名请求示例：

```json
{
  "category": "人名",
  "surname": "林",
  "gender": "女",
  "length": "两个字",
  "other": "希望温柔、有书卷气，适合宝宝起名",
  "exclude": ["萍"]
}
```

宠物名请求示例：

```json
{
  "category": "宠物名",
  "surname": "",
  "gender": "不限",
  "length": "两个字",
  "other": "一只活泼的白色小狗，亲人、爱撒娇",
  "exclude": []
}
```

成功返回示例：

```json
{
  "thread_id": "9be1fd1d-9937-4534-8e7b-ea37f6d2a633",
  "record_id": 12,
  "names": [
    {
      "name": "青岚材科",
      "reference": "青岚取清新自然之意，材科体现新材料科技属性",
      "moral": "寓意企业以绿色材料连接科技与自然",
      "domain": "qinglancai.com",
      "domain_status": "未注册"
    }
  ]
}
```

常见错误：

```json
{
  "detail": "免费生成次数已用完，暂时无法新建起名任务"
}
```

### 3.2 兼容版首次起名

```http
POST /names/get_names
Content-Type: application/json
Authorization: Bearer <access_token>
```

说明：

- 老接口兼容保留
- 同样会扣减免费次数
- 同样会保存起名记录和候选名

建议新前端优先使用：

```http
POST /names/generate
```

### 3.3 多轮反馈优化

```http
POST /names/feedback
Content-Type: application/json
Authorization: Bearer <access_token>
```

说明：

- 基于已有 `thread_id` 继续优化
- 不扣减免费次数
- 写入 `name_feedbacks`
- 更新 `name_records.result_data`
- 刷新该记录下的 `name_candidates`

请求示例：

```json
{
  "thread_id": "9be1fd1d-9937-4534-8e7b-ea37f6d2a633",
  "category": "企业名",
  "feedback": "保留清新、绿色的感觉，但名字再短一点，更适合传播。"
}
```

成功返回示例：

```json
{
  "thread_id": "9be1fd1d-9937-4534-8e7b-ea37f6d2a633",
  "record_id": 12,
  "names": [
    {
      "name": "青岚",
      "reference": "延续上一轮青岚材科中的核心意象",
      "moral": "表达清洁、自然、向上的品牌气质",
      "domain": "qinglan.com",
      "domain_status": "已注册"
    }
  ]
}
```

## 4. 起名历史接口

### 4.1 历史列表

```http
GET /names/records?skip=0&limit=20
Authorization: Bearer <access_token>
```

返回示例：

```json
[
  {
    "id": 12,
    "category": "企业名",
    "title": "青岚材科",
    "thread_id": "9be1fd1d-9937-4534-8e7b-ea37f6d2a633",
    "status": "success",
    "created_at": "2026-07-01T10:00:00",
    "updated_at": "2026-07-01T10:00:00"
  }
]
```

### 4.2 历史详情

```http
GET /names/records/{record_id}
Authorization: Bearer <access_token>
```

说明：

- 只能查看当前用户自己的记录
- 返回输入参数、结果、反馈历史

### 4.3 删除历史记录

```http
DELETE /names/records/{record_id}
Authorization: Bearer <access_token>
```

说明：

- 软删除
- 设置 `is_deleted = true`

成功返回：

```json
{
  "message": "删除成功"
}
```

## 5. 企业知识库接口

### 5.1 上传知识库文件

```http
POST /knowledge/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
```

表单字段：

```text
file
```

curl 示例：

```bash
curl -X POST "http://127.0.0.1:8000/knowledge/upload" \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@./company_rules.txt"
```

成功返回：

```json
{
  "result": "success",
  "knowledge_file_id": 3,
  "status": "pending",
  "message": "文件上传成功，后台正在构建知识库"
}
```

### 5.2 知识库文件列表

```http
GET /knowledge/files?skip=0&limit=20
Authorization: Bearer <access_token>
```

说明：

- 只返回当前用户自己的文件
- 默认过滤软删除文件

### 5.3 知识库文件详情

```http
GET /knowledge/files/{file_id}
Authorization: Bearer <access_token>
```

返回字段包含：

- `id`
- `filename`
- `file_path`
- `file_type`
- `file_size`
- `status`
- `error_message`
- `retry_count`
- `is_deleted`
- `processed_at`
- `deleted_at`
- `created_at`
- `updated_at`

状态说明：

- `pending`：等待处理
- `processing`：正在处理
- `completed`：处理完成
- `failed`：处理失败
- `deleted`：已软删除

### 5.4 删除知识库文件

```http
DELETE /knowledge/files/{file_id}
Authorization: Bearer <access_token>
```

说明：

- 软删除
- 设置 `is_deleted = true`
- 设置 `status = deleted`
- 写入 `deleted_at`

### 5.5 重试知识库文件处理

```http
POST /knowledge/files/{file_id}/retry
Authorization: Bearer <access_token>
```

说明：

- 只有 `failed` 状态可重试
- 重试后状态改为 `pending`
- 清空 `error_message`
- `retry_count + 1`
- 重新投递 RabbitMQ

## 6. 第二阶段候选名字接口

接口前缀：

```http
/phase2
```

### 6.1 查询候选名字

```http
GET /phase2/records/{record_id}/candidates
Authorization: Bearer <access_token>
```

返回示例：

```json
[
  {
    "id": 1,
    "record_id": 12,
    "name": "青岚材科",
    "reference": "青岚取清新自然之意",
    "moral": "寓意绿色材料连接科技与自然",
    "reason": "适合环保新材料品牌",
    "domain": "qinglancai.com",
    "domain_status": "未注册",
    "score": 88,
    "is_selected": false,
    "is_favorite": false,
    "created_at": "2026-07-01T10:00:00"
  }
]
```

### 6.2 收藏候选名

```http
POST /phase2/candidates/{candidate_id}/favorite
Authorization: Bearer <access_token>
```

### 6.3 取消收藏候选名

```http
DELETE /phase2/candidates/{candidate_id}/favorite
Authorization: Bearer <access_token>
```

### 6.4 选中候选名

```http
POST /phase2/candidates/{candidate_id}/select
Authorization: Bearer <access_token>
```

说明：

- 同一条起名记录下，只保留一个 `is_selected = true`

### 6.5 更新候选名评分

```http
PATCH /phase2/candidates/{candidate_id}/score
Authorization: Bearer <access_token>
Content-Type: application/json
```

请求示例：

```json
{
  "score": 92
}
```

## 7. 第二阶段域名矩阵接口

### 7.1 生成域名校验结果

```http
POST /phase2/records/{record_id}/domain-checks
Authorization: Bearer <access_token>
```

默认生成：

- `.com`
- `.cn`
- `.ai`

说明：

- `.com` 使用当前 whois 检查逻辑
- `.cn` / `.ai` 当前为 mock
- 重复生成会先清理旧结果，再写入新结果

### 7.2 查询域名校验结果

```http
GET /phase2/records/{record_id}/domain-checks
Authorization: Bearer <access_token>
```

返回示例：

```json
[
  {
    "id": 1,
    "record_id": 12,
    "candidate_id": 1,
    "domain": "qinglancai.com",
    "suffix": "com",
    "check_status": "未注册",
    "raw_result": {
      "provider": "whois"
    },
    "checked_at": "2026-07-01T10:00:00"
  }
]
```

## 8. 第二阶段商标风险接口

### 8.1 生成商标风险结果

```http
POST /phase2/records/{record_id}/trademark-checks
Authorization: Bearer <access_token>
```

说明：

- 当前为 mock
- `provider = mock`
- 风险等级：`low` / `medium` / `high`
- 重复生成会先清理旧结果，再写入新结果

### 8.2 查询商标风险结果

```http
GET /phase2/records/{record_id}/trademark-checks
Authorization: Bearer <access_token>
```

返回示例：

```json
[
  {
    "id": 1,
    "record_id": 12,
    "candidate_id": 1,
    "name": "青岚材科",
    "category_code": "35",
    "risk_level": "low",
    "matched_items": {
      "mock": true,
      "matches": []
    },
    "provider": "mock",
    "checked_at": "2026-07-01T10:00:00"
  }
]
```

## 9. 第二阶段社媒风险接口

### 9.1 生成社媒风险结果

```http
POST /phase2/records/{record_id}/social-checks
Authorization: Bearer <access_token>
```

当前支持平台：

- `wechat`
- `douyin`
- `xiaohongshu`
- `weibo`

说明：

- 当前为 mock
- 重复生成会先清理旧结果，再写入新结果

### 9.2 查询社媒风险结果

```http
GET /phase2/records/{record_id}/social-checks
Authorization: Bearer <access_token>
```

返回示例：

```json
[
  {
    "id": 1,
    "record_id": 12,
    "candidate_id": 1,
    "platform": "wechat",
    "name": "青岚材科",
    "risk_level": "medium",
    "matched_accounts": {
      "mock": true,
      "accounts": [
        {
          "name": "青岚材科",
          "platform": "wechat"
        }
      ]
    },
    "checked_at": "2026-07-01T10:00:00"
  }
]
```

## 10. 第二阶段订单与权益接口

### 10.1 创建订单草稿

```http
POST /phase2/orders
Authorization: Bearer <access_token>
Content-Type: application/json
```

请求示例：

```json
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

成功返回：

```json
{
  "id": 1,
  "user_id": 1,
  "order_no": "NO202607011900001234abcd",
  "product_type": "quota",
  "amount": 9.9,
  "pay_status": "pending",
  "business_id": null,
  "quota_delta": 10,
  "before_quota": null,
  "after_quota": null,
  "extra_data": {
    "package_name": "10次生成包"
  },
  "created_at": "2026-07-01T10:00:00",
  "paid_at": null
}
```

### 10.2 查询订单列表

```http
GET /phase2/orders?skip=0&limit=20
Authorization: Bearer <access_token>
```

### 10.3 查询订单详情

```http
GET /phase2/orders/{order_id}
Authorization: Bearer <access_token>
```

### 10.4 模拟支付成功

```http
POST /phase2/orders/{order_id}/mock-pay
Authorization: Bearer <access_token>
```

说明：

- 当前为 mock 支付
- 支付成功后 `pay_status = paid`
- 写入 `paid_at`
- 写入 `before_quota`
- 写入 `after_quota`
- 用户 `free_quota` 增加 `quota_delta`
- 重复调用不会重复增加次数

## 11. 运维与统计接口

### 11.1 基础调用统计

```http
GET /ops/metrics
```

返回内容包括：

- 总请求数
- 总错误数
- 平均耗时
- 最大耗时
- 按路由统计的调用次数
- 按路由统计的错误数
- 按路由统计的状态码分布

说明：

- 当前为进程内统计
- 服务重启后统计会清零

## 12. 推荐联调顺序

1. 登录获取 token
2. 调用 `/names/generate`
3. 获取 `record_id`
4. 调用 `/phase2/records/{record_id}/candidates`
5. 测试候选名收藏、选中、评分
6. 调用域名矩阵生成和查询接口
7. 调用商标风险生成和查询接口
8. 调用社媒风险生成和查询接口
9. 创建订单草稿
10. 模拟支付成功
11. 检查用户次数是否增加
12. 查询 `/ops/metrics` 查看接口统计

## 13. 当前 mock 能力边界

以下能力当前是模拟能力：

- `.cn` 域名校验
- `.ai` 域名校验
- 商标风险查询
- 社媒重名风险查询
- 支付

前端展示或演示时需要说明：

- 风险结果仅用于产品流程演示
- 不代表真实法律、商标或平台注册可用性结论

## 14. 常见错误

### 14.1 Token 格式非法或损坏

返回：

```json
{
  "detail": "Token格式非法或损坏"
}
```

处理：

- 检查是否使用 `Authorization: Bearer <token>`
- 检查 token 是否带引号
- 重新登录获取新 token
- 确认后端 `JWT_SECRET_KEY` 没有在登录后发生变化

### 14.2 免费次数不足

返回：

```json
{
  "detail": "免费生成次数已用完，暂时无法新建起名任务"
}
```

处理：

- 使用订单模拟支付增加次数
- 或在数据库中为测试用户补充 `free_quota`

### 14.3 记录或候选名不存在

可能原因：

- `record_id` / `candidate_id` 错误
- 记录不属于当前登录用户
- 记录已被软删除

## 15. 相关文件

主要后端文件：

- `ainame/routers/auth_router.py`
- `ainame/routers/name_router.py`
- `ainame/routers/rag_router.py`
- `ainame/routers/phase_two_router.py`
- `ainame/routers/ops_router.py`
- `ainame/repository/name_record_repo.py`
- `ainame/repository/knowledge_file_repo.py`
- `ainame/repository/phase_two_repo.py`
- `ainame/models/business.py`
- `ainame/schemas/name_schemas.py`
- `ainame/schemas/knowledge_schemas.py`
- `ainame/core/observability.py`
- `ainame/settings/__init__.py`
