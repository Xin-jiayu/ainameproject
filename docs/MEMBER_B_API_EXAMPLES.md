# 成员 B 接口调用示例

基础地址示例：`http://127.0.0.1:8000`

所有接口都需要登录态：

```http
Authorization: Bearer <access_token>
```

## 1. 首次起名

`POST /names/generate`

说明：创建一个新的起名任务。成功后会扣 1 次免费额度，写入起名记录，并返回新的 `thread_id`。后续反馈必须复用这个 `thread_id`。

### 请求示例：企业名

```http
POST http://127.0.0.1:8000/names/generate
Accept: application/json
Content-Type: application/json
Authorization: Bearer <access_token>
```

```json
{
  "category": "企业名",
  "surname": "",
  "gender": "不限",
  "length": "四个字以内",
  "other": "一家做环保新材料的初创公司，希望名字有科技感、可信赖",
  "exclude": ["废", "旧"]
}
```

### 请求示例：人名

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

### 请求示例：宠物名

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

### 成功响应示例

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

### 常见错误

```json
{
  "detail": "免费生成次数已用完，暂时无法新建起名任务"
}
```

说明：HTTP 状态码 `403`。

```json
{
  "detail": "未知起名分类: '游戏角色'，允许值: 人名、企业名、宠物名"
}
```

说明：前端传了不支持的 `category`。

## 2. 多轮反馈优化

`POST /names/feedback`

说明：基于已有 `thread_id` 继续优化，不扣免费额度。接口会读取旧记录并复用原来的 LangGraph 记忆。

### 请求示例

```http
POST http://127.0.0.1:8000/names/feedback
Accept: application/json
Content-Type: application/json
Authorization: Bearer <access_token>
```

```json
{
  "thread_id": "9be1fd1d-9937-4534-8e7b-ea37f6d2a633",
  "category": "企业名",
  "feedback": "我喜欢上一轮的“青岚材科”。请保留清新、绿色的感觉，但名字再短一点，更适合品牌传播。"
}
```

`category` 可传，也可不传；不传时后端会使用该 `thread_id` 对应记录里的 `category`。

### 成功响应示例

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

### 常见错误

```json
{
  "detail": "起名记录不存在，无法继续优化"
}
```

说明：HTTP 状态码 `404`。通常是 `thread_id` 错误、记录已删除，或该记录不属于当前登录用户。

## 3. 企业知识库上传

`POST /knowledge/upload`

说明：上传企业专属参考文件。当前参数名固定为 `file`，请求类型为 `multipart/form-data`。上传成功后会把解析任务投递到 RabbitMQ，后台异步构建知识库。

### 请求示例：curl

```bash
curl -X POST "http://127.0.0.1:8000/knowledge/upload" \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@./company_rules.txt"
```

### 请求示例：HTTP 文件

```http
POST http://127.0.0.1:8000/knowledge/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data; boundary=WebAppBoundary

--WebAppBoundary
Content-Disposition: form-data; name="file"; filename="company_rules.txt"
Content-Type: text/plain

< ./company_rules.txt
--WebAppBoundary--
```

### 成功响应示例

```json
{
  "result": "success",
  "knowledge_file_id": 3,
  "status": "pending",
  "message": "文件 company_rules.txt 上传成功！后台正在为您构建专属知识库，请稍候测试起名功能。"
}
```

### 常见错误

```json
{
  "detail": "Not authenticated"
}
```

说明：缺少或传错 `Authorization`。

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "file"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

说明：表单字段名不是 `file`，或没有真正上传文件。

## 字段约定

`/names/generate` 请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `category` | string | 是 | 仅支持 `人名`、`企业名`、`宠物名` |
| `surname` | string | 人名必填 | 人名起名时必须传姓氏 |
| `gender` | string | 否 | `不限`、`男`、`女` |
| `length` | string | 否 | 名字长度要求 |
| `other` | string | 否 | 业务需求、性格特征、风格偏好等 |
| `exclude` | string[] | 否 | 避讳字列表 |

`/names/feedback` 请求字段：

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `thread_id` | string | 是 | 首次起名返回的 `thread_id` |
| `category` | string | 否 | 不传时使用历史记录的分类 |
| `feedback` | string | 是 | 本轮修改意见 |
