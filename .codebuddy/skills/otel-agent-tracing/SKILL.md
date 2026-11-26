---
name: otel-agent-tracing
description: 给本地 agent harness 接 OpenTelemetry 追踪的完整流程：找事件单一出口、Tracer 接口加 Noop 默认、GenAI 语义约定映射、确定性 trace id、Jaeger 原生二进制与 Langfuse 自托管两种后端、截图取证。用户要给 agent 系统加追踪、可观测性、接 Langfuse/Jaeger/OTel 时使用。
---

# 给 agent harness 接 OpenTelemetry 追踪

## 适用场景

本地 agent 系统（有主循环、工具调用、事件流）要加外部追踪，产出 trace / span / thread 三层并留 UI 截图证据。

## 流程

1. **找事件单一出口**。成熟的 harness 一般有一个 emit_trace / append_event 之类的收口函数（tether 是 `runtime.py` 的 `emit_trace()`）。挂点只加在这里，转发同一个 payload，原有工件（trace.jsonl 等）一个字不动。不要满代码埋点。

2. **Tracer 接口 + Noop 默认**。新建 `tracing.py`：`NoopTracer`（默认，零开销，全部旧测试不动）、`OtelTracer`、`tracer_from_env()` 读 `TETHER_TRACING` 决定后端。SDK import 放在 `OtelTracer.__init__` 里，默认路径不加载依赖。collector 连不上要在启动时就地报错（socket 探测端口），不允许追踪静默丢失。

3. **三层映射**（这是面试核心，先说清楚再写代码）：
   - trace = 一次 run，trace id 用 run_id 的 sha256 前 16 字节派生（OTel 接受 int trace_id，经 `SpanContext` + `NonRecordingSpan` + `set_span_in_context` 注入），保证本地工件和远端 trace 一一对应。
   - span = run 内单次动作。模型调用：`gen_ai.operation.name=chat`、`gen_ai.request.model`、`gen_ai.usage.input_tokens/output_tokens`；工具调用：`gen_ai.operation.name=execute_tool`、`gen_ai.tool.name`、`gen_ai.tool.call.arguments/result`。语义约定在 `opentelemetry.semconv._incubating.attributes.gen_ai_attributes`。
   - thread = session id，打 `session.id` 属性（`session_attributes.SESSION_ID`），**每个 span 都要带**（Langfuse 的 session 聚合只统计带这个属性的行），后端按标签过滤即得同会话全部 trace。
   - span 时间直接用事件的 created_at（ISO 转纳秒）和 duration_ms，OTel 的 `start_span(start_time=)`、`end(end_time=)` 都支持，时间线和本地工件严格一致。
   - 要兼容 Langfuse 就无条件加 `langfuse.observation.type`（根 agent、模型 generation、工具 tool）：Langfuse 按它渲染类型，Jaeger 当普通属性，一份数据两个后端通用。

4. **usage 断层要补**。provider 的 completion metadata 如果没有提取 usage（Anthropic 兼容路径常见），在客户端里补 `input_tokens/output_tokens/total_tokens/stop_reason`，否则 generation span 上没有 token 数。

5. **后端二选一，共用同一份事件流**：
   - **Jaeger 原生二进制**（Windows 无 Docker 时唯一选择）：GitHub release 下 `jaeger-<ver>-windows-amd64.zip`（网络不通走 ghproxy.net），解压即得 collector + UI 一体化 exe，UI 在 16686，OTLP HTTP 在 4318，内存存储重启清空。
   - **Langfuse 自托管**（Docker 引擎可用时）：官方 compose 起 web/worker/postgres/clickhouse/minio/redis 六件套，`LANGFUSE_INIT_*` 环境变量自动建组织/项目/用户/API key。镜像用 daocloud 镜像站拉（`m.daocloud.io/docker.io/<repo>:<tag>`）后 `docker tag` 回 compose 期望名；本机直连 Docker Hub 会超时。端点 `http://localhost:3000/api/public/otel/v1/traces`，请求头两个都要：`Authorization: Basic base64(pk:sk)`、`x-langfuse-ingestion-version: 4`（缺后者数据延迟十几分钟才可见）。UI 在 3000。

6. **本机端点绕过环境代理**。沙箱或公司环境的 `HTTP_PROXY` 会拦截本机 OTLP 流量（现象：导出器报 Exceeded 30 redirects）。指向 localhost / 127.0.0.1 的导出器用 `requests.Session(trust_env=False)`，远端端点保持默认。这个函数提成模块级（`_make_otlp_exporter`）才能直接测。

7. **演示脚本**。同一 session 连跑多个 run（thread 层证据），合成模式（FakeModelClient 类）不耗 API 额度；再跑一次真实模型拿真实 token 数。

8. **验证顺序**：先 API 后截图。
   - Jaeger：`GET http://localhost:16686/api/traces?service=<name>` 核对 span 树、tags 参数 `tags={"session.id":"..."}` 核对 thread 过滤、sha256 核对 trace id 派生关系。
   - Langfuse：v4 实例是 events_only 模式，v1 的 `GET /api/public/traces`、`/api/public/sessions` 已下线，用 `GET /api/public/v2/observations?sessionId=<id>&fields=core,basic,usage` 按 traceId/sessionId 过滤后自行分组，行里 type 列就是 AGENT/GENERATION/TOOL。

9. **截图**：Jaeger 三张（trace 列表、单条时间线、session.id 过滤）。Langfuse 四张（Tracing 列表、单条 trace 树含 token 汇总、Sessions 列表、session 详情会话视图——thread 层的原生形态）。用 agent-browser：open → wait --load networkidle → screenshot，最后必须 close；SPA 页面 networkidle 卡就降级 load。

10. **文档收尾**：设计文档写清三层映射和挂点（一句话能说清「事件流第二个接收方」），README 加特性行和截图，面试话术在「可观测性是行业方向」处补实证。

## 坑

- OTel 属性不接受 None：拍平嵌套 metadata 时跳过 None 键，否则刷一堆 Invalid type 警告。
- 生成 observation 的生命周期：model_requested 打开 generation、model_parsed 关闭；run 异常结束时要把没关的 generation 先关掉，否则留永远不结束的 span。
- `python -m tether.cli` 只加载模块不执行 main（cli.py 末尾没有 main 调用），静默退出零输出；用包的 `__main__` 入口（`python -m tether`）。
- Jaeger API 的过滤参数名是 `tags`（JSON），写 `tag` 会静默返回空。
- Langfuse 请求头的 base64 值尾部有 `==` 填充，解析 key=value 时只能按第一个等号切分。
- agent-browser 的 daemon 异常被杀后登录态丢失，重新 open 会回登录页，重新登录即可，不需要 close 重来。
