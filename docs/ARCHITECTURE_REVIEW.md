# AI 起名项目架构对照评估

评估日期：2026-07-02

评估目标：对照用户提出的目标架构，复核当前代码是否已经落在该架构内，并更新上一版架构评估结论。

评估范围：

- 后端：`ainame/`
- 前端：`ainameapp/`
- 部署配置：`ainame/nginx.conf`、`ainame/docker-compose.yml`、`ainame/Dockerfile`
- 已有文档：`docs/项目规划文档.md`、`docs/成员A第二阶段后端交接文档.md`、`docs/管理员端用户管理后端交接文档.md`

## 1. 总体结论

当前项目已经从“第一阶段 MVP 功能闭环”推进到“第二阶段能力部分落地”的状态。相比上一版评估，代码中已经新增了 Gateway 配置、管理员接口、运营指标接口、第二阶段候选名/校验/订单相关模型和接口。

但从用户提出的目标架构来看，当前仍不是严格的五层架构。

一句话判断：

> 当前代码已经具备 Gateway、Routers、Repository、Model、Worker、Infrastructure 的雏形，并补齐了部分第二阶段业务表；但核心 Service 层仍缺失，AI 起名主链路仍是同步请求，Worker 层尚未承接 AI 慢任务。

当前已经具备的能力：

- Nginx 反向代理配置和 Docker Compose 编排。
- FastAPI 路由拆分，包括 `auth_router`、`name_router`、`rag_router`、`admin_router`、`ops_router`、`phase_two_router`。
- 用户注册、登录、JWT 鉴权。
- 管理员用户管理能力。
- Redis 保存邮箱验证码。
- SQLAlchemy async 数据访问。
- 起名记录、反馈记录、使用记录、知识库文件记录。
- 候选名表、域名校验表、商标校验表、社媒校验表、订单表。
- LangGraph / LangChain / DeepSeek 起名工作流。
- RabbitMQ 异步处理知识库文件。
- RAG 知识库增强企业起名。
- 基础请求日志与指标接口。

当前仍与目标架构有差距的部分：

- Gateway 有基础反代，但还没有 HTTPS、静态资源缓存和限流。
- 已新增独立 `services` 层，核心业务入口开始从 router 下沉到 service。
- 起名请求已新增异步提交接口，任务进入 RabbitMQ；同步 `/names/generate` 暂时保留用于兼容。
- Worker 层统一选型为 RabbitMQ，当前覆盖知识库、起名、邮件三类任务。
- 主业务数据库默认仍是 MySQL，不是目标中的 PostgreSQL。
- 订单能力已经有基础表和模拟支付接口，但还不是独立 `order_router` + `OrderService`。
- 用户资产/权益查询没有形成独立 `user_router`。

## 2. 架构对照表

| 目标层级 | 目标设计 | 当前实现 | 符合程度 | 结论 |
| --- | --- | --- | --- | --- |
| Gateway | Nginx 反向代理、HTTPS、静态缓存、限流 | 已有 `nginx.conf` 和 `docker-compose.yml`，Nginx 反代到 `web:8000` | 部分符合 | 基础反代已落地，HTTPS/缓存/限流未落地 |
| Routers Layer | 只接收请求、参数校验、返回响应 | 路由模块明显增多，但 router 仍直接编排业务 | 部分符合 | 模块拆分进步明显，职责仍偏重 |
| Services Layer | `AIService`、`OrderService`、`UserService` 等业务服务 | 已有 `ainame/services`，包含起名、用户、知识库、订单、校验、AI、邮件服务 | 部分符合 | Service 层已落地，后续继续收敛边界 |
| Worker Layer | RabbitMQ 处理 AI 慢请求、知识库、邮件任务 | 已有 `rag_worker.py`、`name_worker.py`、`email_worker.py` | 基本符合 | 队列选型已统一为 RabbitMQ |
| Infrastructure Layer | PostgreSQL、Redis、RabbitMQ、DeepSeek、SQLAlchemy async | SQLAlchemy async、Redis、DeepSeek、RabbitMQ、MySQL、PostgreSQL checkpoint 都存在 | 部分符合 | 基础设施丰富，主库仍与 PostgreSQL 目标不一致 |

## 3. 当前代码结构观察

当前后端目录已经比上一版更完整：

```text
ainame/
  main.py
  dependencies.py
  nginx.conf
  docker-compose.yml
  Dockerfile
  routers/
    auth_router.py
    name_router.py
    rag_router.py
    admin_router.py
    ops_router.py
    phase_two_router.py
  core/
    workflow.py
    rag_service.py
    redisconfig.py
    auth.py
    tools.py
    observability.py
  repository/
    user_repo.py
    name_record_repo.py
    knowledge_file_repo.py
    phase_two_repo.py
  models/
    user.py
    business.py
  schemas/
    user_schemas.py
    name_schemas.py
    knowledge_schemas.py
  settings/
    __init__.py
  rag_worker.py
```

说明：

- `routers` 已覆盖认证、起名、知识库、管理员、运营指标、第二阶段业务。
- `repository` 已覆盖用户、起名记录、知识库、第二阶段业务表。
- `models.business` 已包含候选名、校验、订单等第二阶段模型。
- `core.observability` 已接入请求日志和 metrics 快照。
- 仍未看到 `services` 层。

## 4. Gateway 层评估

目标：

- Nginx 作为最前端反向代理。
- HTTPS 证书卸载。
- 静态资源缓存。
- 基础防刷限流。

当前代码情况：

- 已存在 `ainame/nginx.conf`。
- 已存在 `ainame/docker-compose.yml`。
- Docker Compose 中包含 `web`、`db`、`postgres_db`、`redis`、`nginx` 服务。
- Nginx 监听 `80`，并通过 upstream 转发到 `web:8000`。

已符合：

- 有 Nginx 反向代理。
- 有容器编排基础。

未符合：

- 未看到 `listen 443 ssl`。
- 未看到 HTTPS 证书配置。
- 未看到 `limit_req` 或类似限流配置。
- 未看到静态资源缓存规则。
- 当前 Nginx 配置将 `/` 全部反代给 FastAPI，没有区分静态资源和 API。

结论：

Gateway 层已经从“未落地”提升到“基础反代已落地”，但仍不是完整 Gateway。

建议：

- 增加 HTTPS 配置。
- 增加登录、注册、验证码、起名提交接口的限流。
- 如果前端走静态部署，让 Nginx 承担前端静态资源缓存。
- 根据部署环境抽出 `server_name`，不要固定虚拟机 IP。

## 5. Routers Layer 评估

目标：

- 路由层只负责 HTTP 请求接入。
- 只做参数校验、依赖注入、返回响应。
- 不直接写业务逻辑。

当前已有路由：

- `auth_router`：注册、登录、验证码。
- `name_router`：起名、反馈、历史记录。
- `rag_router`：知识库上传、文件列表、删除、重试。
- `admin_router`：管理员用户管理。
- `ops_router`：运行指标。
- `phase_two_router`：候选名、域名校验、商标校验、社媒校验、订单。

相比上一版的进步：

- `admin_router` 已落地。
- 订单相关接口已通过 `/phase2/orders` 落地。
- 知识库文件删除和失败重试已补齐。
- 候选名收藏、选中、评分、校验矩阵接口已补齐。
- 运营指标接口已补齐。

仍存在的问题：

### 5.1 Router 仍承担业务编排

`name_router.py` 中仍直接完成：

- 扣减免费额度。
- 调用 `core.workflow.generate_naming_v2`。
- 创建起名记录。
- 创建候选名。
- 创建使用记录。
- AI 异常后退回额度。
- 反馈后替换候选名。

这些更适合进入 `NameService`、`UserService`、`AIService`。

### 5.2 `phase_two_router` 混合了业务规则和基础设施调用

`phase_two_router.py` 中直接完成：

- 候选名收藏、选中、评分。
- 多后缀域名校验。
- 商标和社媒模拟校验。
- 订单创建、查询、模拟支付。

这些更适合拆入：

- `CandidateService`
- `ValidationService`
- `OrderService`

### 5.3 `rag_router` 仍直接连接 RabbitMQ

`rag_router.py` 中仍直接完成：

- 保存上传文件。
- 创建知识库文件记录。
- 构造 RabbitMQ 消息。
- 连接 RabbitMQ 并投递任务。
- 判断重试次数。

这些更适合进入 `KnowledgeService` 和队列客户端模块。

结论：

Router 层模块划分已经明显进步，但仍未达到“只接入 HTTP，不做业务逻辑”的目标。

## 6. Services Layer 评估

目标：

- `AIService`：封装 LangChain / LangGraph 运行逻辑。
- `OrderService`：处理订单状态流转。
- `UserService`：处理用户权益、消耗点数扣减。
- 路由层调用服务层。

当前代码情况：

- `Test-Path ainame/services` 返回 `False`。
- 未发现 `AIService`、`OrderService`、`UserService` 等类。
- AI 编排仍主要在 `core/workflow.py`。
- 权益扣减仍在 `repository/user_repo.py` 和 `routers/name_router.py` 之间完成。
- 订单状态流转在 `repository/phase_two_repo.py` 中完成。

当前最接近 Service 的模块：

- `core/workflow.py`：底层 AI 工作流。
- `repository/phase_two_repo.py`：第二阶段业务持久化和部分业务规则。
- `repository/user_repo.py`：用户、额度、管理员相关数据库操作和部分规则。
- `repository/knowledge_file_repo.py`：知识库文件状态流转。

问题：

- Repository 层承担了部分业务服务职责。
- Router 层承担了部分业务编排职责。
- 缺少清晰的事务边界和业务用例入口。
- 后续真实支付、真实商标接口、真实社媒接口接入后，router/repository 会继续膨胀。

结论：

Services Layer 仍未落地。这依然是当前代码与目标架构之间最大的结构差距。

建议后续拆分：

```text
services/
  auth_service.py
  user_service.py
  name_service.py
  ai_service.py
  knowledge_service.py
  validation_service.py
  order_service.py
  admin_service.py
```

## 7. Worker Layer 评估

目标：

- FastAPI 收到起名请求后，只把任务推送到 RabbitMQ 队列。
- 立即返回“任务已提交”。
- Worker 调用 LangChain / DeepSeek 生成名字。
- 结果存入数据库或通过 WebSocket 推送给前端。
- 邮件验证码等耗时任务也可以放入 Worker。
- 目标组件统一为 RabbitMQ。

当前代码情况：

- 有 `rag_worker.py`、`name_worker.py`、`email_worker.py`。
- Worker 使用 `aio_pika` 和 RabbitMQ。
- `rag_worker.py` 处理知识库文件解析。
- `name_worker.py` 处理 AI 起名慢任务。
- `email_worker.py` 处理验证码邮件等邮件发送任务。
- `/names/tasks` 已提供异步任务提交接口。
- `/names/tasks/{task_id}` 已提供前端轮询查询接口。

已符合：

- 知识库文件解析已异步化。
- 知识库状态已有 `pending / processing / completed / failed`。
- 知识库失败重试已有接口。

未符合：

- 同步 `/names/generate` 仍保留，前端需逐步迁移到异步接口。
- Redis 仍主要用于验证码，不作为任务 Broker。
- WebSocket 推送暂未实现，目前采用轮询查询接口。

结论：

Worker 层有真实落地，但只覆盖 RAG 文件处理。对目标中最关键的“AI 慢请求异步化”仍未达成。

建议：

- 队列选型已统一为 RabbitMQ。
- 起名任务、知识库任务、邮件任务均进入 RabbitMQ。
- 不再引入第二套队列体系，避免任务分散。

## 8. Infrastructure Layer 评估

目标：

- PostgreSQL 作为主数据库。
- SQLAlchemy async ORM。
- Redis 用作验证码、缓存和异步任务 Broker。
- LangChain / DeepSeek 作为 AI 基础设施。

当前代码情况：

### 8.1 数据库

`settings/__init__.py` 中默认业务数据库仍是：

```text
mysql+aiomysql://root:password@localhost:3306/ainame?charset=utf8mb4
```

同时：

- Docker Compose 中有 MySQL。
- Docker Compose 中也有 PostgreSQL。
- PostgreSQL 当前主要用于 LangGraph checkpoint。
- 测试文档中也明确区分 MySQL 业务库和 PostgreSQL memory DB。

结论：

主业务数据库仍不是目标中的 PostgreSQL。PostgreSQL 已引入，但主要承担 LangGraph 记忆/checkpoint。

### 8.2 SQLAlchemy async

当前已经使用：

- `create_async_engine`
- `async_sessionmaker`
- `AsyncSession`

这一点符合目标。

### 8.3 Redis

当前 Redis 已用于：

- 邮箱验证码。
- 作为容器服务存在。

但 Redis 未用于：

- 任务 Broker，当前统一由 RabbitMQ 承担。
- 起名任务队列。
- 高频数据缓存。

### 8.4 AI 基础设施

当前已经具备：

- `langchain-deepseek`
- `langgraph`
- `langgraph-checkpoint-postgres`
- `ChatDeepSeek`
- 结构化输出 schema。
- RAG 检索。
- 域名工具。

AI 基础设施较完整，但建议外包 `AIService`，不要让业务路由直接依赖 `core.workflow`。

### 8.5 可观测性

新增了：

- `core.observability`
- `request_logging_middleware`
- `/ops/metrics`

这是架构上的正向补充。

结论：

Infrastructure 层比上一版更完整。队列选型已经统一为 RabbitMQ；当前主要不一致点是主业务库仍不是 PostgreSQL。

## 9. 数据模型评估

当前已有核心模型：

- `User`
- `EmailCode`
- `UsageRecord`
- `NameRecord`
- `NameFeedback`
- `KnowledgeFile`
- `NameCandidate`
- `DomainCheck`
- `TrademarkCheck`
- `SocialNameCheck`
- `Order`

相比上一版，已经补齐：

- 候选名字表。
- 多后缀域名校验表。
- 商标风险表。
- 社媒重名表。
- 订单表。
- 管理员标记和冻结标记。
- 知识库文件重试、软删除、处理时间字段。

仍缺少或不完整：

- 独立套餐表 `Package`。
- 独立权益账户表 `UserEntitlement`。
- 支付回调表 `PaymentCallback`。
- 独立起名任务表 `NameTask`。
- 起名结果推送/任务查询模型。
- 真实支付渠道状态流转。

特别说明：

当前 `NameRecord.status` 仍默认是 `success`，更像“结果记录表”，不是完整异步任务表。若要支持 AI 起名异步化，建议新增或改造为：

```text
pending
running
success
failed
cancelled
```

并保存：

```text
request_payload
result_data
error_message
retry_count
started_at
finished_at
worker_id
```

## 10. 起名主流程现状

当前起名流程仍然是同步模式：

```text
前端请求 /names/generate
  -> FastAPI router 鉴权
  -> router 扣减用户免费次数
  -> router 调用 core.workflow.generate_naming_v2
  -> DeepSeek / LangGraph 同步生成结果
  -> router 写入 name_records
  -> router 写入 name_candidates
  -> router 写入 usage_records
  -> 返回生成结果
```

目标架构期望流程：

```text
前端请求 /names/generate
  -> Router 参数校验
  -> NameService 检查并冻结/扣减权益
  -> 创建 name_task，状态 pending
  -> 投递任务到 RabbitMQ
  -> 立即返回 task_id
  -> Worker 执行 AI 生成
  -> 写入 name_records / name_candidates
  -> 任务状态改为 success / failed
  -> 前端轮询或 WebSocket 获取结果
```

核心差异仍然是：

- 当前同步等待 AI。
- 目标异步提交任务。
- 当前没有 `task_id` 查询链路。

## 11. 订单与商业化基础评估

当前已经有：

- `Order` 模型。
- `/phase2/orders` 创建订单。
- `/phase2/orders` 查询订单列表。
- `/phase2/orders/{order_id}` 查询详情。
- `/phase2/orders/{order_id}/mock-pay` 模拟支付。
- 支付后增加用户 `free_quota`。

这说明“订单基础”已经落地。

但与目标 `order_router + OrderService` 相比，仍有差距：

- 订单接口挂在 `phase_two_router` 下，不是独立 `order_router`。
- 订单状态流转在 repository 中完成，不是 `OrderService`。
- 没有真实支付回调。
- 没有套餐表。
- 没有支付回调幂等处理。
- 没有权益账户流水的完整模型。

结论：

订单能力是“第二阶段模拟订单基础”，不是完整支付/套餐系统。

## 12. 管理员后台评估

当前已经有：

- `User.is_admin`
- `User.is_frozen`
- `get_admin_user`
- `admin_router`
- `/admin/users` 用户列表。
- 修改用户、冻结、重置密码、删除用户。
- 前端 `ainameapp/pages/admin/` 页面。

这说明管理员后台基础能力已落地。

仍可增强：

- 管理员操作审计日志。
- 更细粒度 RBAC 权限。
- 管理员与普通用户角色拆表。
- 删除用户的业务影响校验。

结论：

`admin_router` 已形成，上一版“管理员后台未形成”的结论已过期。

## 13. 风险点

### P0：AI 起名同步阻塞 HTTP 请求

这是当前最高优先级架构风险。DeepSeek 起名可能耗时数秒到十几秒，当前 `/names/generate` 会同步等待 AI 返回。

风险：

- HTTP 请求长时间占用。
- 并发升高时接口堆积。
- AI 超时直接影响用户请求。
- 难以做排队、重试、取消、状态查询。

### P0：Service 层缺失

Router 和 Repository 已经承载了大量业务逻辑。第二阶段功能越多，这个问题越明显。

建议优先抽出：

- `NameService`
- `UserService`
- `AIService`
- `KnowledgeService`
- `OrderService`
- `ValidationService`

### P1：队列运行保障

目标已经统一为 RabbitMQ + aio-pika。

后续重点不是选型，而是运行保障：

- RabbitMQ 服务要纳入部署编排和健康检查。
- `rag_worker.py`、`name_worker.py`、`email_worker.py` 要随应用一起启动。
- 需要补充失败重试、死信队列或人工补偿策略。

### P1：主业务库与目标 PostgreSQL 不一致

当前主业务库仍默认 MySQL。项目已经大量使用 JSON 字段，长期看 PostgreSQL + JSONB 更贴合目标架构。

但是否迁移需要权衡：

- 现有迁移脚本兼容性。
- 当前团队熟悉程度。
- 部署成本。
- 历史数据迁移。

### P1：支付能力仍是模拟

当前订单有 mock pay，但没有真实支付回调和幂等处理。接真实支付前必须设计：

- 支付渠道订单号。
- 回调验签。
- 幂等表或幂等约束。
- 订单状态机。
- 权益发放事务。

### P2：编码显示问题

读取部分中文注释和字符串时仍出现乱码。可能是终端编码或文件编码不一致。建议统一 UTF-8。

## 14. 建议演进路线

### 第一阶段：先抽 Service，不改变接口

目标：行为不变，边界变清晰。

建议顺序：

1. `NameService`：承接起名、反馈、候选名保存、使用记录。
2. `UserService`：承接额度扣减、退款、冻结判断、权益查询。
3. `KnowledgeService`：承接上传、删除、重试、投递队列。
4. `OrderService`：承接订单创建、模拟支付、后续真实支付。
5. `ValidationService`：承接域名、商标、社媒校验。
6. `AIService`：承接 `core.workflow` 的业务封装。

### 第二阶段：AI 起名异步化

目标：解决慢请求阻塞。

建议顺序：

1. 设计 `name_tasks` 或扩展 `name_records.status`。
2. 提交接口只创建任务并返回 `task_id`。
3. Worker 调用 DeepSeek / LangGraph。
4. 写入 `name_records` 和 `name_candidates`。
5. 增加任务查询接口。
6. 前端轮询或 WebSocket 等待结果。

### 第三阶段：完善 RabbitMQ Worker 体系

目标：在统一 RabbitMQ 选型下，提高异步任务可靠性。

建议：

- 为 `rag_document_queue`、`name_generation_queue`、`email_queue` 制定重试策略。
- 增加 Worker 健康检查和启动文档。
- 为失败任务增加后台查询、重试或人工补偿入口。
- 后续如需优先级队列或死信队列，继续基于 RabbitMQ 扩展。

### 第四阶段：完善商业化和管理员能力

建议补齐：

- 独立 `order_router`。
- `Package` 表。
- `PaymentCallback` 表。
- 用户权益账户或权益流水。
- 管理员操作审计。
- 订单状态机。

### 第五阶段：确认数据库策略

如果继续坚持目标架构，建议规划 MySQL 到 PostgreSQL 的迁移。

如果短期保留 MySQL，则建议更新目标架构文档，将 PostgreSQL 定位为 LangGraph checkpoint / memory DB，而不是主业务库。

## 15. 目标架构达成度评分

| 模块 | 达成度 | 上一版 | 说明 |
| --- | ---: | ---: | --- |
| Gateway | 45% | 0% | 已有 Nginx 和 Compose，但无 HTTPS/限流/静态缓存 |
| Routers | 70% | 50% | 路由模块更完整，但仍承担业务逻辑 |
| Services | 10% | 10% | 仍无 service 层 |
| Worker | 45% | 40% | 知识库 Worker 增强，但 AI 起名仍未异步 |
| Infrastructure | 70% | 65% | 配置、日志、Compose 更完整，但主库和队列目标不一致 |
| 数据模型 | 78% | 55% | 已补候选名、校验、订单、管理员字段 |
| 管理后台 | 65% | 0% | 管理员用户管理已落地 |
| 商业化基础 | 45% | 10% | 有订单和 mock pay，但无真实支付/套餐 |
| 整体 | 60% | 45% | 第二阶段能力明显增加，但核心分层仍未完成 |

## 16. 最终结论

当前项目比上一版更接近目标架构，但还不能说已经完全处在目标架构里。

已经明显改善的部分：

- Gateway 基础配置已出现。
- 管理员后台接口已落地。
- 订单基础和模拟支付已落地。
- 第二阶段候选名、域名、商标、社媒校验表和接口已落地。
- 知识库文件管理和重试能力增强。
- 可观测性开始接入。

仍最需要优先处理的部分：

1. 抽出 Service 层。
2. 将 AI 起名从同步请求改成异步任务。
3. 完善 RabbitMQ Worker 的部署、监控和失败补偿。
4. 决定主业务库是否迁移 PostgreSQL，或调整目标架构。
5. 将订单从 mock pay 演进到真实支付状态机和权益发放模型。

当前更准确的阶段判断：

> 项目已经不再只是第一阶段 MVP，而是进入了第二阶段功能扩展期；但架构仍是“Router + Repository + Core”的功能型结构，尚未完成“Router + Service + Infrastructure + Worker”的清晰分层。
