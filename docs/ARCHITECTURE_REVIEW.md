# AI 起名项目架构对照评估

评估日期：2026-07-01

评估目标：对照用户提出的目标架构，检查当前代码是否已经落在该架构内，并给出后续调整建议。

评估范围：

- 后端：`ainame/`
- 前端：`ainameapp/`
- 已有文档：`docs/PROJECT_PLAN.md`、`docs/BACKEND_HANDOFF.md`

## 1. 总体结论

当前项目已经具备 AI 起名平台 MVP 的主要功能闭环，但还没有完全落到目标架构中。

一句话判断：

> 当前代码是“功能闭环优先的 MVP 架构”，不是严格的“Gateway + Router + Service + Worker + Infrastructure”分层架构。

当前已经具备的能力：

- FastAPI 后端入口和路由拆分。
- 用户注册、登录、JWT 鉴权。
- Redis 保存邮箱验证码。
- SQLAlchemy async 数据访问。
- 起名记录、反馈记录、使用记录、知识库文件记录。
- LangGraph / LangChain / DeepSeek 起名工作流。
- RabbitMQ 异步处理知识库文件。
- RAG 知识库增强企业起名。
- 基础 `.com` 域名检测。

当前与目标架构的主要差距：

- 没有 Nginx / Gateway 配置。
- 没有独立 `services` 层，业务逻辑大量写在 router 中。
- 起名请求仍是同步调用 AI，没有进入 Worker 队列。
- Worker 已存在，但只用于知识库文件处理，且使用 RabbitMQ，不是目标中的 ARQ + Redis。
- 主业务数据库默认仍是 MySQL，不是目标中的 PostgreSQL。
- `order_router`、`admin_router`、`user_router` 尚未形成。
- 支付、套餐、管理员后台还未实现。

## 2. 架构对照表

| 目标层级 | 目标设计 | 当前实现 | 符合程度 | 结论 |
| --- | --- | --- | --- | --- |
| Gateway | Nginx 反向代理、HTTPS、静态缓存、限流 | 未发现 Nginx / Docker / 部署网关配置 | 未符合 | 仍是应用直连形态 |
| Routers Layer | 只接收请求、校验参数、返回响应 | 已有 `auth_router`、`name_router`、`rag_router`，但包含业务逻辑 | 部分符合 | 路由拆了，但职责过重 |
| Services Layer | `AIService`、`OrderService`、`UserService` 等业务服务 | 未发现 `services` 目录或 Service 类 | 未符合 | 服务层缺失 |
| Worker Layer | ARQ + Redis 处理 AI 慢请求和邮件任务 | 有 `rag_worker.py`，使用 RabbitMQ 处理知识库文件 | 部分符合 | Worker 思路已有，但未服务起名主流程 |
| Infrastructure Layer | PostgreSQL、Redis、DeepSeek、SQLAlchemy async | SQLAlchemy async、Redis、DeepSeek 已有；主库默认 MySQL | 部分符合 | 基础设施已有，但数据库与目标不一致 |

## 3. 当前代码结构观察

当前后端目录大致如下：

```text
ainame/
  main.py
  dependencies.py
  routers/
    auth_router.py
    name_router.py
    rag_router.py
  core/
    workflow.py
    rag_service.py
    redisconfig.py
    auth.py
    tools.py
  repository/
    user_repo.py
    name_record_repo.py
    knowledge_file_repo.py
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

这说明项目已经有一定分层意识：

- `routers`：接口入口。
- `schemas`：Pydantic 请求和响应模型。
- `models`：SQLAlchemy ORM 模型。
- `repository`：数据库访问。
- `core`：AI、鉴权、Redis、RAG、工具函数。
- `settings`：配置读取。
- `rag_worker.py`：后台消费者。

但从目标架构角度看，当前缺少最关键的 `services` 层。现在很多业务编排直接发生在 router 中。

## 4. Gateway 层评估

目标：

- Nginx 作为前端反向代理。
- HTTPS 证书卸载。
- 静态资源缓存。
- 基础防刷和限流。

当前代码情况：

- 未发现 `nginx.conf`。
- 未发现 `docker-compose.yml` 或类似部署编排。
- 未发现明确的 HTTPS、静态缓存、限流配置。
- FastAPI 在 `ainame/main.py` 中直接创建 `app = FastAPI()`。

结论：

Gateway 层当前未落地。

建议：

- 部署阶段补充 Nginx 配置。
- 将 `/api/` 转发到 FastAPI。
- 将前端静态资源交给 Nginx。
- 对注册、登录、验证码、起名提交接口做基础限流。

## 5. Routers Layer 评估

目标：

- 路由层只负责 HTTP 请求接入。
- 只做参数校验、依赖注入、返回响应。
- 不直接写业务逻辑。

当前已有路由：

- `auth_router`：注册、登录、验证码。
- `name_router`：起名、反馈、历史记录。
- `rag_router`：知识库上传、文件列表、文件详情。

当前未形成的路由：

- `user_router`：用户信息、资产/权益查询。
- `order_router`：支付、套餐购买。
- `admin_router`：管理员后台接口。

主要问题：

### 5.1 `auth_router` 包含业务逻辑

当前 `auth_router.py` 中直接完成：

- 生成邮箱验证码。
- 发送邮件。
- 写入 Redis。
- 校验验证码。
- 检查邮箱是否已注册。
- 创建用户。
- 校验密码。
- 生成 Token。

这些逻辑更适合放入 `AuthService` 或 `UserService`。

### 5.2 `name_router` 包含核心业务编排

当前 `name_router.py` 中直接完成：

- 扣减免费额度。
- 调用 AI 起名工作流。
- 创建起名记录。
- 创建使用记录。
- AI 异常时退回额度。
- 查询历史记录。
- 删除历史记录。
- 处理反馈优化。

其中扣额度、调用 AI、保存记录、失败退款这些都属于业务逻辑，应进入 `NameService` / `AIService` / `UserService`。

### 5.3 `rag_router` 包含文件存储与消息队列逻辑

当前 `rag_router.py` 中直接完成：

- 保存上传文件到本地目录。
- 创建知识库文件记录。
- 构造 RabbitMQ 消息。
- 连接 RabbitMQ 并投递任务。

这些更适合放入 `KnowledgeService` 和队列基础设施模块。

结论：

Router 层已经按接口模块拆分，但不符合“只接收请求、不做业务逻辑”的目标。当前路由层职责偏重。

## 6. Services Layer 评估

目标：

- `AIService`：封装 LangChain / LangGraph 运行逻辑。
- `OrderService`：处理订单状态流转。
- `UserService`：处理用户权益、点数扣减。
- 路由层调用服务层。

当前代码情况：

- 未发现 `ainame/services` 目录。
- 未发现 `AIService`、`OrderService`、`UserService` 类。
- AI 编排主要在 `core/workflow.py`。
- 用户额度逻辑在 `repository/user_repo.py` 和 `routers/name_router.py`。
- 起名记录写入逻辑在 `repository/name_record_repo.py` 和 `routers/name_router.py`。
- 订单系统尚未实现。

当前最接近 Service 的模块：

- `core/workflow.py`：接近 `AIService` 的底层 AI 引擎。
- `repository/user_repo.py`：包含一部分用户权益变更。
- `repository/name_record_repo.py`：包含起名记录和使用记录持久化。

但这些还不是业务服务层。

结论：

Services Layer 当前未落地。这是当前架构与目标架构之间最大的结构性差距。

建议后续拆分方向：

```text
services/
  auth_service.py
  user_service.py
  name_service.py
  ai_service.py
  knowledge_service.py
  order_service.py
```

建议职责：

- `AuthService`：验证码、注册、登录、Token。
- `UserService`：用户权益、额度扣减、额度退回、资产查询。
- `NameService`：起名任务提交、历史记录、反馈优化、结果查询。
- `AIService`：调用 LangGraph / DeepSeek，处理结构化输出。
- `KnowledgeService`：知识库文件上传、状态、重试、删除。
- `OrderService`：订单创建、支付回调、套餐权益发放。

## 7. Worker Layer 评估

目标：

- FastAPI 收到起名请求后，将任务推入 Redis 队列。
- 立即返回“任务已提交”。
- Worker 后台调用 LangChain / DeepSeek 生成名字。
- 结果写入数据库或通过 WebSocket 推送前端。
- 邮件验证码等耗时任务也可放入 Worker。
- 推荐组件：ARQ + Redis。

当前代码情况：

- 当前有 `rag_worker.py`。
- 当前 Worker 使用 RabbitMQ 和 `aio_pika`。
- 当前 Worker 只处理知识库文件解析。
- 当前起名接口 `/names/generate` 仍同步调用 `generate_naming_v2`。
- 当前验证码邮件发送仍在 HTTP 请求中直接执行。

当前已经符合目标精神的部分：

- 知识库上传接口不是同步解析文件，而是投递到队列。
- Worker 会更新 `knowledge_files` 状态。
- 文件处理状态已有 `pending -> processing -> completed / failed` 流转。

当前不符合目标的部分：

- 起名慢请求没有进入 Worker。
- 没有 ARQ。
- Redis 当前只用于验证码，不是任务 Broker。
- 没有起名任务表的 `pending/running/success/failed` 异步状态模型。
- 没有 WebSocket 推送或任务结果查询接口。

结论：

Worker 层部分落地，但只覆盖 RAG 文件处理。对核心 AI 起名慢请求来说，目前仍未落地。

建议：

- 起名生成应改为异步任务模式。
- API 提交后返回 `task_id` 或 `record_id`。
- Worker 负责执行 DeepSeek 调用。
- 前端通过轮询或 WebSocket 获取结果。
- 邮件验证码发送也可以从路由中迁移到 Worker。

## 8. Infrastructure Layer 评估

目标：

- PostgreSQL 作为主数据库。
- SQLAlchemy async ORM。
- Redis 作为验证码缓存、热点缓存和异步任务 Broker。
- LangChain / DeepSeek 作为 AI 基础设施。

当前代码情况：

### 8.1 数据库

当前 `settings/__init__.py` 中默认业务数据库为：

```text
mysql+aiomysql://root:password@localhost:3306/ainame?charset=utf8mb4
```

同时，LangGraph checkpoint 单独使用 PostgreSQL：

```text
LANGGRAPH_CHECKPOINT_DB_URI=postgresql://...
```

这说明：

- 主业务库当前默认是 MySQL。
- PostgreSQL 当前主要用于 LangGraph thread memory / checkpoint。
- 这与目标“PostgreSQL 作为主业务库”不一致。

### 8.2 SQLAlchemy async

当前已经使用：

- `create_async_engine`
- `async_sessionmaker`
- `AsyncSession`

这一点符合目标架构。

### 8.3 Redis

当前 Redis 已用于：

- 邮箱验证码存储。
- 通过 `core/redisconfig.py` 提供 FastAPI 依赖。

但 Redis 当前没有用于：

- 起名任务队列。
- ARQ Broker。
- 高频缓存。

### 8.4 AI 基础设施

当前已经使用：

- `langchain-deepseek`
- `langgraph`
- `ChatDeepSeek`
- 结构化输出 schema。
- LangGraph checkpoint。
- RAG 检索。

AI 基础设施基本具备，但建议从 `core/workflow.py` 外包一层 `AIService`，让业务层不要直接依赖底层 workflow 细节。

结论：

Infrastructure 层部分符合。主要差距是主业务库不是 PostgreSQL，以及 Redis 还没有承担任务队列角色。

## 9. 数据模型评估

当前已有核心模型：

- `User`
- `EmailCode`
- `UsageRecord`
- `NameRecord`
- `NameFeedback`
- `KnowledgeFile`

这些模型已经覆盖 MVP 核心闭环：

- 用户。
- 免费次数。
- 起名记录。
- 反馈记录。
- 使用记录。
- 知识库文件状态。

和目标架构相比，缺少：

- `Order`
- `Package`
- `PaymentCallback`
- `UserEntitlement` 或独立权益账户表。
- `NameTask` 异步任务表。
- `AdminUser` 或用户角色权限体系。

特别说明：

当前 `NameRecord.status` 默认是 `success`，更像“结果记录表”，不是完整的“任务状态表”。如果要支持异步起名，它需要扩展为：

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
```

## 10. 起名主流程现状

当前起名流程大致是：

```text
前端请求 /names/generate
  -> FastAPI router 鉴权
  -> router 扣减用户免费次数
  -> router 调用 core.workflow.generate_naming_v2
  -> DeepSeek / LangGraph 同步生成结果
  -> router 写入 name_records
  -> router 写入 usage_records
  -> 返回生成结果
```

目标架构期望流程是：

```text
前端请求 /names/generate
  -> FastAPI router 鉴权和参数校验
  -> NameService 创建任务并冻结/扣减权益
  -> 投递任务到 Redis / ARQ
  -> 立即返回 task_id
  -> Worker 执行 AI 生成
  -> 写入 name_records / name_results
  -> 前端轮询或 WebSocket 获取结果
```

差异：

- 当前是同步 AI 调用。
- 目标是异步任务提交。
- 当前失败后立即退款。
- 目标中建议使用“提交时冻结/扣减，失败后退回”的任务化权益模型。

## 11. 风险点

### P0：AI 起名同步阻塞 HTTP 请求

DeepSeek 起名可能耗时数秒到十几秒。当前 `/names/generate` 同步等待 AI 返回，会带来：

- FastAPI 请求长时间占用。
- 用户并发增加时接口容易堆积。
- AI 超时会直接影响 HTTP 链路。
- 难以做任务重试、排队和状态查询。

这是当前架构和目标架构之间最关键的风险。

### P0：Service 层缺失导致业务逻辑分散

目前 router 直接编排业务，后续订单、权益、支付、AI 任务、管理员后台接入后，路由层会越来越重。

建议优先抽出：

- `NameService`
- `UserService`
- `AIService`
- `KnowledgeService`

### P1：主业务库与目标 PostgreSQL 不一致

目标架构希望 PostgreSQL 作为主库，当前默认是 MySQL。由于已有 JSON 字段、LangGraph checkpoint、AI 结构化结果，PostgreSQL + JSONB 更适合长期演进。

迁移前需要评估：

- Alembic 迁移兼容性。
- SQLAlchemy JSON 字段差异。
- 现有 MySQL 数据迁移。
- 本地开发环境成本。

### P1：队列技术选型不统一

目标写的是 ARQ + Redis，当前知识库 Worker 用 RabbitMQ。

两条路都可以，但需要统一决策：

- 如果坚持目标架构：迁移到 ARQ + Redis。
- 如果保留 RabbitMQ：目标架构文档应改为 RabbitMQ，并让起名任务也进入 RabbitMQ。

不建议长期同时维护 RabbitMQ 和 ARQ，除非确实有不同场景的明确理由。

### P1：验证码邮件仍在请求链路内发送

当前验证码接口会直接发邮件。邮件服务慢或失败时，会影响注册体验。后续可以放入 Worker。

### P2：配置和编码问题

读取代码时发现部分中文注释和字符串显示为乱码。这通常是文件编码或终端编码问题。它不一定影响运行，但会影响维护和交接。

建议统一为 UTF-8，并确认编辑器、终端、Git 编码策略一致。

## 12. 建议的演进路线

### 第一阶段：不改变功能，先理清边界

目标：把业务逻辑从 router 搬到 service，但接口行为不变。

建议顺序：

1. 新增 `UserService`，承接额度扣减、退回、权益查询。
2. 新增 `NameService`，承接起名生成、记录保存、反馈优化。
3. 新增 `AuthService`，承接验证码、注册、登录。
4. 新增 `KnowledgeService`，承接文件保存、任务投递、状态查询。

### 第二阶段：起名任务异步化

目标：解决 AI 慢请求阻塞。

建议顺序：

1. 设计起名任务状态。
2. 提交起名接口只创建任务并返回 `task_id`。
3. Worker 调用 AI 并写入结果。
4. 增加任务查询接口。
5. 前端改为提交后轮询或 WebSocket 等待结果。

### 第三阶段：统一队列方案

目标：确定到底使用 ARQ + Redis 还是 RabbitMQ。

建议：

- 如果项目规模较小、团队希望轻量：选 ARQ + Redis。
- 如果后续任务类型多、需要更强消息队列能力：保留 RabbitMQ。
- 无论选哪个，都让起名、知识库、邮件等异步任务使用统一模式。

### 第四阶段：补商业化模块

目标：补齐目标架构中的订单、套餐、管理员后台。

建议新增：

- `order_router`
- `admin_router`
- `user_router`
- `OrderService`
- `Package` / `Order` / `PaymentCallback` / `UserEntitlement` 模型。

### 第五阶段：数据库策略确认

目标：决定是否从 MySQL 迁移到 PostgreSQL。

如果继续按目标架构走，建议主库迁移到 PostgreSQL，并使用 JSONB 保存 AI 结构化结果。

## 13. 目标架构达成度评分

| 模块 | 达成度 | 说明 |
| --- | ---: | --- |
| Gateway | 0% | 未发现 Nginx 或部署网关配置 |
| Routers | 50% | 已拆路由，但业务逻辑较重 |
| Services | 10% | 没有 service 层，只有 core/repository |
| Worker | 40% | 有 RAG Worker，但起名未异步 |
| Infrastructure | 65% | SQLAlchemy async、Redis、AI 已有；主库与队列方案不一致 |
| 数据模型 | 55% | MVP 表较完整，缺订单、任务、权益、管理员 |
| 整体 | 45% | 功能可用，但离目标分层架构还有明显距离 |

## 14. 最终结论

当前项目不是完全处在你上面定义的架构里，但已经具备向该架构演进的基础。

更准确地说：

- 当前已经有 Router、Repository、Model、Schema、Core、Worker 的雏形。
- 当前缺少严格的 Service 层。
- 当前 AI 起名主链路仍是同步请求，不符合“AI 慢请求进队列”的目标。
- 当前 Worker 思路已经在知识库文件处理中验证过，可以迁移到起名任务。
- 当前基础设施接近目标，但主业务数据库和队列选型需要统一。

优先级最高的下一步不是立刻加新功能，而是：

1. 抽出 Service 层。
2. 将起名生成异步任务化。
3. 明确 Redis/ARQ 与 RabbitMQ 的队列选型。
4. 决定主业务库是否迁移 PostgreSQL。

完成这四步后，项目会从“可用 MVP”进入更清晰、更可扩展的后端架构。
