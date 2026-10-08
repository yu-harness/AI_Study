# 消息队列 · 大模型应用与 Agent 场景资料

> 承接 [[消息队列-03-价值与选型]]。本篇收录的是"大模型推理与工具调用耗时较长"这个特定场景下的文章与文档。
>
> 每条资料标注它对应哪一条诉求：① 异步解耦，避免用户同步等待 ② 重试、延迟执行、优先级调度、执行容错 ③ 分布式组件通信与微服务架构。

---

## 一、场景总论：大模型应用为什么需要消息队列

### 1. Apache RocketMQ 面向 AI 演进：LiteTopic 支撑百万级多 Agent 会话协作

链接：[Apache RocketMQ 面向 AI 演进：LiteTopic 支撑百万级多 Agent 会话协作](https://rocketmq-learning.com/learning/explore/rocketmq-ai-litetopic-multi-agent/)

阿里云 RocketMQ 团队的技术分享整理稿，是这批资料里信息密度最高的一篇。它先说明 AI 应用在三个维度上的变化（通道拓扑由运行期决定、单次任务从毫秒级变成分钟级、GPU 算力成本占主导），再逐条给出传统事件驱动模型不适配的地方：积压增长的速度完全不同、一条消息对应一次会话导致队头阻塞、中间结果丢失会重复消耗算力。之后介绍 LiteTopic 的设计（Parent Topic + 按会话动态创建与回收的 LiteTopic、RocksDB 承载消费队列索引、Ready Set 替代全量轮询、Suspend(N) 非阻塞调速），最后给出两个生产案例：编程智能体 Qoder Cloud Agents 用两个 Parent Topic 做双向异步通信、用 Checkpoint 承载进度；百炼推理网关用按 user + model 建立的漏桶阵列做限流，把限流维度从单一维度扩到数千个维度。

对应问题：①②③ 全覆盖。里面"消息系统负责有序可靠传递事件，进度以 Checkpoint 为权威来源"这条边界，是回答"Agent 任务执行容错"最容易被追问的点。

### 2. RocketMQ for AI：企业级 AI 应用集成的异步通信方案（阿里云官方解决方案文档）

链接：[RocketMQ for AI 企业级 AI 应用异步通信方案](https://help.aliyun.com/zh/document_detail/2990216.html)

官方解决方案页面，篇幅不长但把三个适用方向讲清楚了：模型调用耗时引起的同步阻塞、Multi-Agent 之间与工作流节点的长耗时调度、长连接会话状态的连续性。同时列出 LiteTopic 的四项能力（百万量级通道、自动创建与删除、每个消费者可订阅万级通道、通道内有序）和两个可以动手部署的体验场景。适合作为动手实验的入口，页面上有部署时长与费用预估。

对应问题：①②③。

### 3. GenAI Integration Patterns & Asynchronous Workflows（AI Engineering Handbook）

链接：[GenAI Integration Patterns & Asynchronous Workflows](https://handbook.exemplar.dev/ai_engineer/integration_patterns)

把生成式 AI 的集成方式归成四种拓扑：同步网关、异步任务队列、事件驱动流式、离线批量；再用一张矩阵对比连接生命周期、超时韧性、系统复杂度、用户体验与最大并发规模。矩阵里有一句话很关键：同步网关的超时韧性"差"，异步任务队列"极好"。后半部分是完整的可运行示例，FastAPI 做网关、Celery 做任务编排、Redis 同时充当 broker 与状态后端，含任务超时、指数退避重试、任务状态查询接口的完整代码，末尾补充了用 Webhook 回调替代客户端轮询的做法，以及回调需要带 HMAC 签名。

对应问题：①③。四种拓扑的对比可以直接用来回答"什么时候该异步、什么时候该流式"。

### 4. How to Use Background Jobs in AI Apps for Long Tasks

链接：[How to Use Background Jobs in AI Apps for Long Tasks](https://sagnikbhattacharya.com/blog/background-jobs-ai-apps)

给出一个可以直接背下来的判定标准：三秒以内直接同步返回，三到十秒考虑流式响应，超过十秒使用后台任务。之后讲任务载荷要自包含（worker 不需要回头调用主应用取数据）、进度要写进共享状态供客户端查询、结果要随任务一起持久化以便随时取回，以及不同失败原因要不同处理（触发限流要退避重试，内容策略违规不该重试，网络错误限制次数重试）。末尾列出三个常见错误做法：为长任务阻塞 HTTP 请求、worker 里不设超时、重试内容策略违规。

对应问题：①②。

---

## 二、RocketMQ 机制文档（官方中文）

### 5. 事务消息

链接：[RocketMQ 事务消息](https://rocketmq.apache.org/zh/docs/featureBehavior/04transactionmessage/)

两阶段提交：半事务消息（此时对消费者不可见）→ 生产者执行本地事务 → 提交或回滚 → 服务端长时间未收到确认时发起消息回查。文档同时给了使用限制（事务消息只能发到 MessageType 为 Transaction 的主题、事务超时后默认回滚、只保证最终一致性）和完整 Java 示例。

对应问题：②③。Agent 场景里"工具已经执行但结果没写回"就属于这一类不一致，事务消息与回查机制是对应答案。

### 6. 定时 / 延时消息

链接：[RocketMQ 定时 / 延时消息](https://rocketmq.apache.org/zh/docs/featureBehavior/02delaymessage/)

定时与延时消息机制相同，服务端在指定时刻才把消息投递给消费者。要点：定时时间填的是毫秒级 Unix 时间戳而不是延时时长；最大定时时长默认 24 小时；精度为秒级；把大量消息设成同一时刻会造成分发延迟。典型场景是分布式定时调度与任务超时处理（订单未支付超时关闭就是标准例子）。

对应问题：②。这是"延迟执行"直接对应的官方说明。

### 7. 消费重试

链接：[RocketMQ 消费重试](https://rocketmq.apache.org/zh/docs/featureBehavior/10consumerretrypolicy)

PushConsumer 的状态机是"已就绪 → 处理中 → 待重试 → 提交 / DLQ"，无序消息的重试间隔是阶梯式的（10 秒、30 秒、1 分钟、2 分钟……逐级拉长，超过 16 次后固定为 2 小时），SimpleConsumer 则用不可见时间（InvisibleDuration）控制重试间隔，并可以在消费过程中通过接口延长。文档明确点出两类错误用法：用消费失败做条件分支、用消费失败做限流；正确做法是触发限流时延迟获取消息。

对应问题：②。这段"错误用法"的提醒在面试里比机制本身更容易加印象分。

---

## 三、RabbitMQ：延迟、优先级、DLQ（Dead Letter Queue）

### 8. Dead Letter Exchanges（官方文档）

链接：[RabbitMQ Dead Letter Exchanges](https://www.rabbitmq.com/docs/dlx)

浏览器里出现"Dead Letter Exchange"的说法就来自这里。消息进入 DLX 的四种触发条件：被拒绝且不重新入队、消息 TTL 到期、队列超过长度上限、消息重投次数超过 quorum 队列的 delivery-limit。文档还说明 DLX 本身就是一个普通交换机，建议用 policy 配置而不是写死 `x-arguments`（写死的参数不重新部署应用无法修改），以及要注意的两件事：默认重投不带 publisher confirm，目标队列不可用时消息会丢失；消息头会记录 `x-death`，可以用它查看每次进入 DLX 的原因与次数。

对应问题：②。这是"执行容错"链路里最后一环的官方说明。

### 9. Priority Support in Queues（官方文档）

链接：[RabbitMQ Priority Support in Queues](https://www.rabbitmq.com/priority.html)

RabbitMQ 的优先级队列实现。经典队列支持 0–255，但官方强烈建议只用个位数级别（每个优先级都要维护一个子队列，占用内存、磁盘与 CPU）；quorum 队列从 4.3 起支持固定 32 级（0–31），不需要额外参数。文档里两个坑值得记住：一是消费者设置了 prefetch 之后，高优先级消息可能要等低优先级消息处理完才能投递，因为预取额度已经被占满；二是经典队列里消息只有到达队首才会判定 TTL 到期。文档开头还给出更简单的替代做法：分成 high / medium / low 三个独立队列，通常比一个优先级队列更好推理，并发度也更高。

对应问题：②。"高优先级任务要等低优先级任务"这个反直觉现象是很好的面试素材。

### 10. RabbitMQ Delayed Messages

链接：[RabbitMQ Delayed Messages](https://rabbitgui.com/blog/rabbitmq-delayed-messages)

RabbitMQ 本身没有延迟投递能力，这篇把两种实现方式讲全了。方式一是 `rabbitmq_delayed_message_exchange` 插件，声明类型为 `x-delayed-message` 的交换机，发送时用 `x-delay` 头指定毫秒数；限制是延迟消息存在单节点的 Mnesia 表里、不做集群复制、该节点故障会丢消息。方式二是 TTL 加 DLQ：把消息发到一个没有消费者的"暂存队列"，到期后经 DLX 路由到真正的业务队列；要注意 RabbitMQ 只从队首判定过期，所以不同延时长度需要建立多个延时队列（文章给出 5 秒 / 30 秒 / 60 秒三个队列的做法，正好对应指数退避重试）。

对应问题：②。"延迟执行"在 RabbitMQ 上的完整答案。

---

## 四、Redis Streams

### 11. Redis Streams 数据类型文档

链接：[Redis Streams 数据类型文档](https://redis.io/docs/latest/develop/data-types/streams/)

概念总入口。讲清条目 ID 的格式（毫秒时间戳 + 序号，时间回拨时仍保持递增）、三种读取模式（范围查询、实时监听、消费组）、消费组相关命令（XGROUP CREATE、XREADGROUP、XACK、XPENDING、XCLAIM、XAUTOCLAIM、XINFO）、内存管理（MAXLEN 与 XTRIM 的近似裁剪 `~`）以及各命令的复杂度。其中"PEL（Pending Entries List）记录已投递未确认的消息"和 XAUTOCLAIM 是消费组可靠性的基础。

对应问题：③。

### 12. How to build a Redis-backed job queue for background workers（Redis 官方教程）

链接：[Redis 官方教程：Build a Redis-backed job queue for background workers](https://redis.io/tutorials/redis-backed-job-queue-for-background-workers)

一份完整的动手教程，仓库地址在文中（`redis-developer/redis-backed-job-queue-for-background-workers`）。它用一个五种键的模型把任务队列搭起来：Stream 做队列、JSON 存完整任务记录、Set 做状态索引（让按状态查询保持 O(1)）、第二个 Stream 做 DLQ、消费组做多 worker 协作。流程写得很具体：XREADGROUP 认领、处理成功 XACK、失败则计数并把同一个 job id 重新 XADD 入队、超过 maxAttempts 写入 DLQ。还讲了优雅停机（监听 SIGTERM/SIGINT，处理完当前任务再退出，未确认消息留在 PEL 可被重新认领）和如何用 curl 观察重试与进入 DLQ 的全过程。

对应问题：①②。想亲手"看到"重试与 DLQ 是怎么发生的，这篇最直接。

### 13. Streams Consumer Group Patterns

链接：[Streams Consumer Group Patterns](https://redis.antirez.com/fundamental/streams-consumer-patterns.html)

把 Redis Streams 上生产会遇到的问题逐条列出，都是官方文档不会强调的内容。启动恢复的两阶段模式：只用 `>` 读取会让崩溃前未确认的消息永久滞留在 PEL，正确做法是先用 ID `0` 清空自己的 PEL，再切到 `>` 读新消息。用 XAUTOCLAIM 做自动认领，配合每个消费者里的 janitor 协程实现去中心化的工作接管。毒丸消息（反复让消费者崩溃的坏消息）的处理方式是查 XPENDING 的投递次数，超过阈值就转入 DLQ。内存管理上指出 ACK 之后用 XDEL 删除会造成基数树碎片，应该用 XTRIM 近似裁剪。另外还讲了阻塞读取耗尽连接池的问题（所有连接都被 BLOCK 占住）和两个延迟指标的区别：入口延迟看 last-delivered-id，处理延迟看 PEL 大小。

对应问题：②③。这篇是"Redis Streams 做队列会有哪些坑"的答案来源。

---

## 五、Agent 侧的工程实践

### 14. AI Agent Deployment 实战：任务队列、状态持久化、模型路由与高并发部署（稀土掘金）

链接：[AI Agent Deployment 实战：任务队列、状态持久化、模型路由与高并发部署](https://juejin.cn/post/7676620373446869044)

中文，覆盖面广。核心是给出一个完整的部署拓扑：客户端（WebSocket / SSE）→ API 网关（限流、租户隔离）→ 任务调度接口（只做校验、生成 task_id、返回 202）→ 消息队列 → Worker 集群 → 工具网关与模型路由，状态存 Postgres Checkpoint。几个值得单独记的做法：按耗时与风险把 Worker 分成实时组、批处理组、沙箱组，避免长任务榨干短任务的计算槽位；用 Checkpoint 持久化图状态实现断点自愈，避免故障后从第一步重跑并重复执行不可逆的写入操作；对 Prompt、模型、工具 Schema 做三元组版本管理与灰度发布；把单任务的 Token 累计消耗做成硬性熔断阈值。末尾列了三个典型报错场景（同步连接池耗尽导致 504、幻觉重试循环导致账单失控、工具沙箱越权），每个都有现象、归因与解决方式。

对应问题：①②③。文中"为什么 Worker 要分组"和"Token 熔断"这两点在面试里区分度较高。

### 15. AI Agent Tool Calling Architecture: Production System Design

链接：[AI Agent Tool Calling Architecture](https://markaicode.com/architecture/ai-agent-tool-calling-architecture)

专门讲 Agent 工具调用怎么用队列隔离。架构为：编排器（唯一允许调用模型的组件）→ 事件队列（Redis Streams + 消费组，至少一次投递）→ 每个工具一个独立的无状态执行器部署 → 容错层（熔断器 + 有上限的重试）→ 结果聚合。文章很实在，开头就说明代价：队列额外引入序列化与网络开销、多出消费者组拓扑、跨组件排障需要分布式追踪，并发会话少于十来个时同步单体更简单。还给出失败模式对照表（工具调用挂起、队列积压、参数格式错误、执行器反复重启、工具被重复执行、编排器状态丢失）与伸缩信号（哪个指标对应扩容哪一层）。有两个容易记错的点文中专门纠正：一是队列位置在编排器与执行器之间，熔断器包在执行器调用外部工具的那一跳，不包队列跳；二是缺 Redis 持久化配置会在重启时丢掉在途状态、用 XREAD 而不是 XREADGROUP 会在重启后产生重复投递、不设 XTRIM 会让流无限增长。

对应问题：①②③。

### 16. Celery MCP Architecture: Production Patterns for AI Tools

链接：[Celery MCP Architecture](https://markaicode.com/architecture/celery-mcp-architecture)

把每一次 MCP 工具调用派发成 Celery 任务，Web 应用立即返回任务 ID，broker 排队，worker 池执行后把结果写入客户端可轮询的后端。讲清 Redis 与 RabbitMQ 作为 broker 的取舍（Redis 最容易搭建，但单线程处理命令、不开持久化时 broker 重启会丢任务；RabbitMQ 搭建成本更高但提供持久化与镜像队列）。代码示例里有三个关键配置：`soft_time_limit`、`time_limit`、`result_expires`，以及用一个带 `on_failure` 的自定义任务基类把失败路由到 DLQ。失败模式表里有一条很典型：broker 与结果后端共用同一个 Redis 实例时，这个实例通常最先饱和，把它们分到不同实例是最便宜的容量提升。

对应问题：①②③。

### 17. AI Agent Queue Architecture: How to Keep Production Workflows From Piling Up

链接：[AI Agent Queue Architecture](https://iamstackwell.com/posts/ai-agent-queue-architecture)

思路清楚的一篇。它把"队列架构"定义成工作如何被接受、存储、排序、分配、重试、延迟、升级与安全地失败，然后给出五个最要紧的做法：入口与执行分离（触发路径只做校验、盖幂等键、建任务记录并入队）、有意识地分配优先级、重试要有规则（可恢复错误退避重试，永久性错误不重试）、并发限制保护成本与一致性、以及一条真正的 DLQ 路径。DLQ 那段值得细看：文章认为一个合格的 DLQ 条目要保存原始载荷、任务类型、重试历史、失败原因、时间戳、关联实体 ID 与建议的下一步动作，并且要能检查、重放、取消、升级。末尾列出一组应该监控的指标：队列深度、最老任务年龄、处理延迟、重试率、DLQ 率、按类型的成功率、每个完成任务的花费、高风险动作的人工通过率。

对应问题：②③。"DLQ 不是垃圾桶而是控制点"这个说法，以及那组监控指标，都是可以直接用的答题素材。

---

## 六、MCP 长耗时工具（工具调用耗时超过一次请求能等的边界）

### 18. How to build long-running MCP tools on Azure Functions

链接：[How to build long-running MCP tools on Azure Functions](https://devblogs.microsoft.com/azure-sdk/long-running-mcp-tools-azure-functions/)

从实际问题切入：MCP 工具是请求 / 响应式的，而各客户端自己设的工具调用超时通常在 30–60 秒，超时后客户端判定调用失败，但底层工作可能还在跑。文章介绍 MCP 在 2026-07-28 版本引入的 Tasks 扩展：服务端可以返回一个异步任务句柄而不是最终结果，客户端用 `tasks/get` 轮询状态、`tasks/update` 在任务进入 input_required 时回传输入、`tasks/cancel` 取消进行中的任务；任务状态包括 working、input_required、completed、failed、cancelled。在扩展尚未被客户端与 SDK 广泛支持之前，文中用 Durable Functions 给出过渡做法：`start_mining` 在预算时间内返回结果，否则返回 workflow_id；`get_mining_result` 按 workflow_id 查询状态。文中也点出这种轮询方式仍然依赖模型正确记住并传递 workflow_id，模型编造 ID 就会查到错误实例，因此查询接口对不存在的 ID 返回 not_found 而不做猜测。

对应问题：②③。"工作耗时不该等于调用耗时"这条原则，是解释为什么工具调用也需要异步与任务状态的直接依据。

### 19. MCP Deep Dive, Part 9: When the Tool Takes Minutes — Streaming and Long-Running Tools Over MCP

链接：[MCP Deep Dive, Part 9: When the Tool Takes Minutes](https://prepstack.co.in/blog/mcp-deep-dive-part-9-streaming)

同一主题的详解版，给出按时长选择机制的分档：一秒以内同步返回，一到三十秒发进度通知并流式输出部分结果，超过三十秒入队并返回 jobId。六种做法逐个配代码说明：用 `notifications/progress` 报告进度（长工具显示"第 4/10 页"而不是一直转圈）、通过 Streamable HTTP 加 SSE 流式返回部分结果、入队后返回句柄（`create_report` 在 p95 约 90 毫秒内返回，耗时的渲染放到队列后异步执行）、把 MCP 的取消通知映射为 CancellationToken 并一路传递到最底层工作、给长连接设置保活心跳（否则空闲代理会回收连接，agent 永远等一个已经断掉的 socket）、以及把进度流给用户、把结构化结果给模型两条通道分开（把每个进度事件都灌进模型上下文只是让它花更多 token 且推理更差）。末尾有一份检查清单与七个常见陷阱。

对应问题：①③。

### 20. The 2026-07-28 MCP Specification Release Candidate（MCP 官方博客）

链接：[The 2026-07-28 MCP Specification Release Candidate](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/)

上文提到的 Tasks 扩展就来自这个版本。这一版把协议改成了无状态：`initialize` / `initialized` 握手与 `Mcp-Session-Id` 会话都被移除，协议版本、客户端信息与能力改为随每次请求放在 `_meta` 里传递，任何请求都能落到任意一个服务实例上，因此部署不再需要会话粘滞与共享会话存储。状态改由应用自己管理，典型做法是工具返回一个显式的句柄（如 `basket_id`），由模型在后续调用中当作普通参数传回。服务端需要中途向客户端索要输入时，不再依靠一直挂着的 SSE 流，而是返回 `input_required` 结果（带 `inputRequests` 与 `requestState`），客户端收集答复后带着 `inputResponses` 重新发起原调用。Tasks 扩展的任务生命周期由 `tasks/get`、`tasks/update`、`tasks/cancel` 驱动，任务是否以任务形式执行由服务端决定，`tasks/list` 因无法在有会话的前提下安全限定范围而被移除。此外还要求 `Mcp-Method` 与 `Mcp-Name` 头以便网关按操作类型路由、给列表结果加上 `ttlMs` 与 `cacheScope`、在 `_meta` 里固定 W3C Trace Context 的键名。

对应问题：①③。要解释"MCP 工具调用为什么能做异步与断点续传"，这一版规范是根上的依据。

---

## 七、官方文档里值得一并收藏的入口

| 主题 | 链接 |
|---|---|
| RocketMQ 全部特性文档（事务、延时、顺序、重试、存储与清理，以及 5.5 的 LiteTopic） | [rocketmq.apache.org/zh/docs](https://rocketmq.apache.org/zh/docs/) |
| RabbitMQ 官方文档目录（TTL、max-length、quorum 队列、consumer prefetch） | [www.rabbitmq.com/docs](https://www.rabbitmq.com/docs) |
| Redis 命令参考，XREADGROUP 的 PEL、CLAIM、NOACK 与 ID 取值含义 | [redis.io XREADGROUP](https://redis.io/docs/latest/commands/xreadgroup/) |
