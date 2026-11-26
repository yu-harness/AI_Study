"""运维与数据准备脚本集合，不参与线上问答链路。

每个脚本都是独立的命令行入口，用 `python -m finagent.scripts.<name>` 执行：

- init_db                    本地建库建表，走代码里的 init_schema
- apply_migrations           生产环境按文件名顺序执行 infra/migrations 下的 SQL 与 Cypher
- import_portfolio           导入租户范围内的组合持仓快照
- sync_market_data           从行情接口同步实时报价与历史价格到源表
- sync_sec_rag               抓取 SEC 财报片段，灌进检索源表
- check_production_readiness 上线前检查配置与依赖，返回非 0 表示不该发版
- run_api                    启动生产 API
- run_local_preview_api      启动本地预览 API，用内存实现顶替 Milvus / Neo4j / 行情网关

约定：脚本只做一次性或周期性的数据准备与运维动作，不写业务逻辑；
业务逻辑一律在 packages/ 下，脚本只负责组装 settings、调用 store 或 orchestrator。
"""


