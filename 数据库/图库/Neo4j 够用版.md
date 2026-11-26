---
title: "Neo4j 够用版"
topic: "数据库"
type: note
date: 2026-11-15
---

# Neo4j 够用版：只看这个项目用到的部分

不用系统学图数据库。这个项目里 Neo4j 只承担一件事：**存一批市场叙事文本，按关键词全文检索，按租户过滤**。掌握下面四件事就够了。

## 一、四个概念

| 概念               | 是什么                                | 类比       |
| ---------------- | ---------------------------------- | -------- |
| Node（节点）         | 一条实体，可带任意属性                        | 表格里的一行   |
| Property（属性）     | 节点上的键值对，如 `narrative_id`、`content` | 列        |
| Relationship（关系） | 两个节点之间的有向边，也带属性和类型                 | 外键，但能带属性 |
| Label（标签）        | 节点的类别，如 `:MarketNarrative`         | 表名       |
|                  |                                    |          |

一句话：**节点像行，标签像表名，关系像能存属性的外键**。这个项目只用了节点 + 属性 + 全文索引，没有用到多层关系遍历。

## 二、Cypher 是什么

**Neo4j 的查询语言，地位等同 MySQL 的 SQL。** 区别在于它不写表连接，而是**把图的形状直接画出来**：

```cypher
(节点)-[:关系]->(节点)
```

小括号是点，方括号是边，箭头是方向，冒号后面是类型——这就是全部符号。你画成什么样，数据库就去找什么样的子图，所以官方叫它「pattern matching」（模式匹配）。

三个最基本的形状：

| 想查什么 | Cypher 怎么写 |
| --- | --- |
| 所有节点 | `MATCH (n) RETURN n` |
| 指定类型 | `MATCH (n:MarketNarrative) RETURN n` |
| 两个节点有某关系 | `MATCH (a)-[:IMPACTS]->(b) RETURN a, b` |

它和 SQL 的对应关系：

| SQL | Cypher |
| --- | --- |
| `FROM t` | `MATCH (n:Label)` |
| `WHERE` | `WHERE` |
| `SELECT` | `RETURN` |
| `INSERT` | `CREATE` / `MERGE` |
| `UPDATE` | `SET` |
| `DELETE` | `DELETE` |
| `JOIN` | 不用写，直接画 `-[:X]->` |

一句话：**SQL 描述"从哪张表取哪些列"，Cypher 描述"找什么形状的子图"。**

## 三、Cypher 五条语法就够


```cypher
// 1. 建节点（括号是节点，花括号是属性）
CREATE (:MarketNarrative {
  narrative_id: "n_001",
  content: "美联储加息预期升温，成长股承压",
  importance: 0.8,
  tenant_id: "global",
  updated_at: "2026-01-01T00:00:00Z"
});

// 2. 查询（MATCH 找，WHERE 过滤，RETURN 返回）
MATCH (n:MarketNarrative)
WHERE n.tenant_id = "global"
RETURN n.content, n.importance
ORDER BY n.importance DESC
LIMIT 5;

// 3. 改属性
MATCH (n:MarketNarrative {narrative_id: "n_001"})
SET n.importance = 0.9;

// 4. 建关系（可选，这个项目没用到）
MATCH (a:MarketNarrative {narrative_id: "n_001"}), (b:MarketNarrative {narrative_id: "n_002"})
CREATE (a)-[:RELATES_TO {weight: 0.7}]->(b);

// 5. 全文索引：先建索引，再查
CREATE FULLTEXT INDEX narrative_ft IF NOT EXISTS
FOR (n:MarketNarrative) ON EACH [n.content, n.summary, n.name];
```

对照 SQL 记：`MATCH` ≈ `FROM`，`WHERE` 一样，`RETURN` ≈ `SELECT`，`SET` ≈ `UPDATE`，`CREATE` ≈ `INSERT`。区别是「关系」用 `-->` 画出来，而不是 join。

## 四、项目里那条查询逐行读

```cypher
CALL db.index.fulltext.queryNodes($index_name, $search_query, {limit: $limit})
YIELD node, score
WHERE coalesce(node.tenant_id, 'global') IN ['global', $tenant_id]
RETURN coalesce(node.narrative_id, elementId(node)) AS narrative_id,
       coalesce(node.content, node.summary, node.name) AS content,
       coalesce(node.importance, 0.5) AS importance,
       coalesce(node.source, node.url) AS source,
       coalesce(node.updated_at, node.created_at) AS updated_at,
       score
ORDER BY score DESC
LIMIT $limit
```

| 行 | 在干什么 |
| --- | --- |
| `CALL db.index.fulltext.queryNodes(...)` | 用全文索引查关键词，返回命中的节点和相关度 `score` |
| `YIELD node, score` | 把索引给的两个结果接出来 |
| `WHERE coalesce(tenant_id,'global') IN ['global', $tenant_id]` | 只看公共叙事 + 自己的；`coalesce` 是「为空就用默认值」 |
| `RETURN ... AS ...` | 统一字段名；`coalesce` 链表示「有这个字段就用，没有就试下一个」 |
| `ORDER BY score DESC` | 最相关的排前面 |
| `LIMIT $limit` | 截断 |

三个设计点值得记：

- **`coalesce` 到处用**，因为历史数据结构不一致（有的叫 `content`、有的叫 `summary`、`name`）。这是「不改数据、在查询层兼容」的做法。
- **没有向量检索**：全文索引靠关键词命中，说「加息」搜不到只写了「紧缩」的叙事。要语义检索必须另配向量库（这个项目里向量库是另一个 Milvus）。
- **`score` 直接当权重用**：上层把它塞进 `decay_weight`，参与和向量结果的统一排序。

## 五、本地十分钟跑通

```bash
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/test1234 neo4j:5
```

浏览器打开 `http://localhost:7474`，用户名 `neo4j`、密码 `test1234`，直接在输入框执行上面的 Cypher 即可。Python 侧只需：

```python
from neo4j import GraphDatabase
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "test1234"))
with driver.session(database="neo4j") as s:
    for row in s.run("MATCH (n:MarketNarrative) RETURN n.content LIMIT 3"):
        print(row["n.content"])
```

## 六、什么时候才需要真正学它

只有当你要做**多跳关系推理**（“这只股票 → 属于哪个行业 → 该行业受哪个政策影响”）时，图数据库的价值才显现：关系是数据本身，`MATCH (a)-[:X]->(b)-[:Y]->(c)` 一次走完，SQL 要写多层 join。

这个项目没到这一步——它把 Neo4j 当「带全文索引的文本表」用。所以按上面四节学到能读懂那条 Cypher，就够应对代码阅读和面试提问了。

## 七、本机已部署的实例（2026-11-15）

已用 Docker 起好，容器名 `neo4j`，镜像 `neo4j:5`，端口映射 7474（浏览器）与 7687（Bolt）。

| 项 | 值 |
| --- | --- |
| 浏览器 | http://localhost:7474 |
| 用户名 / 密码 | `neo4j` / `test1234` |
| Bolt 地址 | `bolt://localhost:7687` |
| 数据卷 | 未挂载（删除容器即丢数据） |

常用命令：

```bash
docker start neo4j          # 开机后启动
docker stop neo4j
docker logs -f neo4j        # 看出错
docker exec -it neo4j cypher-shell -u neo4j -p test1234   # 命令行进库
```

已建的索引与样例数据：

```cypher
CREATE FULLTEXT INDEX narrative_ft IF NOT EXISTS
FOR (n:MarketNarrative) ON EACH [n.content, n.summary, n.name];
```

实测查询（`cypher-shell` 里跑过）：

```cypher
CALL db.index.fulltext.queryNodes('narrative_ft', '加息')
YIELD node, score
RETURN node.content AS content, round(score, 3) AS score
ORDER BY score DESC LIMIT 5;
```

返回：

```text
"美联储加息预期升温，成长股承压", 0.379
"国内降息落地，地产链回暖", 0.087
```

注意第二行：它只含一个「息」字也被召回，说明**默认分析器对中文是按字切分的**，噪音很大。要按词匹配得换 CJK 分析器：

```cypher
CREATE FULLTEXT INDEX narrative_ft_cjk IF NOT EXISTS
FOR (n:MarketNarrative) ON EACH [n.content]
OPTIONS { indexConfig: { `fulltext.analyzer`: 'cjk' } };
```

这也解释了项目里的检索为什么必须再叠一层 reranker——全文分数本身不够精确。

## 八、登录后怎么用（Query 界面）

你看到的这个界面就是 **Neo4j Browser**：上面一条黑色输入框，下面回显结果。

### 三步上手

1. **点顶部输入行**，粘贴 Cypher，按 `Ctrl+Enter`（或点右侧 ▶）执行。
2. 结果默认是**节点图**（圆圈 + 连线），点左侧结果里的表格图标可以切成行列表格。
3. 左侧 `Queries` 栏会记住跑过的语句，点一下就能再次执行。

### 现在就能跑的四条

```cypher
// ① 看库里有什么（我刚灌的两条）
MATCH (n:MarketNarrative) RETURN n LIMIT 25;

// ② 只看内容，表格视图更清楚
MATCH (n:MarketNarrative)
RETURN n.narrative_id AS id, n.content AS content, n.importance AS importance;

// ③ 全文检索，验证索引能用
CALL db.index.fulltext.queryNodes('narrative_ft', '加息')
YIELD node, score RETURN node.content, round(score, 3) AS score
ORDER BY score DESC;

// ④ 看有哪些索引
SHOW INDEXES;
```

第 ① 条跑完，画面中间会出现两个圆圈各带标签 `MarketNarrative`，点圆圈能在右侧看到属性面板——这就是「节点 + 属性」的直观样子。

![[Pasted image 20261115211138.png|543]]

![[Pasted image 20261115211202.png|1033]]
### 几条命令行小指令

| 指令 | 作用 |
| --- | --- |
| `:help` | 内置帮助 |
| `:clear` | 清屏 |
| `:history` | 历史语句 |
| `:sysinfo` | 看内存与版本 |
| `:play movies` | 官方新手教程（会自带一份电影数据） |

### 写数据的标准姿势

```cypher
// 建：MERGE 是「有就复用、没有才建」，比 CREATE 安全（重复执行不会造重复节点）
MERGE (n:MarketNarrative {narrative_id: 'n_003'})
SET n.content = '人民币汇率走强，出口链承压',
    n.importance = 0.7,
    n.tenant_id = 'global',
    n.updated_at = datetime();

// 删
MATCH (n:MarketNarrative {narrative_id: 'n_003'}) DELETE n;

// 改
MATCH (n:MarketNarrative {narrative_id: 'n_001'}) SET n.importance = 0.9 RETURN n;
```

### 两个注意

- **别拿默认库当实验场乱删**：现在只有 2 个节点，随便玩；真接项目数据后，删除前先 `MATCH ... RETURN` 确认命中范围。
- **中文检索按字切分**：`'加息'` 会把只含「息」的句子也召回（实测分数 0.087），做项目要换 `cjk` 分析器（见上一节）。

## 九、这个项目为什么要用它（以及用偏了哪里）

### 它实际承担的活

记忆召回是两路并行：

| 路子          | 存什么                               | 怎么查     | 解决什么               |
| ----------- | --------------------------------- | ------- | ------------------ |
| 向量库（Milvus） | **每个用户自己的**偏好、约束                  | 语义相似度   | “他说过不买 ST” 这类个人记忆  |
| 图库（Neo4j）   | **公共的**市场叙事（`tenant_id='global'`） | 关键词全文检索 | “加息”“衰退”这类**术语命中** |


两个理由让它非图库不可（至少当初是这么想的）：

1. **公共数据只存一份**。宏观叙事对所有用户都一样，塞进每个人的向量库等于复制 N 份；放图库用 `tenant_id IN ['global', 我]` 一次查完。
2. **补语义检索的漏**。用户问「加息对成长股的影响」，向量库可能召回「紧缩预期压制估值」——语义近但词不对；而全文索引能稳稳命中带「加息」的叙事。两路合并再 rerank，召回更全。

### 但代码里只用了它 20% 的能力

现在只用节点 + 属性 + 全文索引，**一条关系都没建**。等于把一个图数据库当成「带全文索引的文本表」用——这种需求用 Postgres 的 `tsvector` 或 Elasticsearch 也能做，不一定非要 Neo4j。

真正属于图数据库的场景，是**关系本身携带信息、需要多跳遍历**：

```cypher
// 建模示例：股票 → 行业 → 受哪个政策影响
(:Stock {ticker:'AAPL'})-[:BELONGS_TO]->(:Industry {name:'消费电子'})
(:Policy {name:'美国关税'})-[:IMPACTS {severity:0.8}]->(:Industry {name:'消费电子'})
(:Event {name:'加息'})-[:PRESSURES]->(:Sector {name:'成长股'})
```

有了这些边，一次查询就能回答「我持仓的 AAPL，最近受哪些政策影响、影响强度多大」：

```cypher
MATCH (s:Stock {ticker:'AAPL'})-[:BELONGS_TO]->(i:Industry)<-[r:IMPACTS]-(p:Policy)
RETURN p.name, r.severity ORDER BY r.severity DESC;
```

这在关系型库里要 join 三张表；在代码里则要写三次检索再手工拼——图库一行走完。

### 三种数据的对比（记住这张表就不迷）

| 数据形态       | 选什么           | 例子              |
| ---------- | ------------- | --------------- |
| 键值/事务/审计   | 关系库（Postgres） | 用户、任务、事件流       |
| 语义相似检索     | 向量库（Milvus）   | 用户偏好、长文本片段      |
| **多跳关系推理** | **图库（Neo4j）** | 资产—行业—政策—事件的传导链 |

判断标准一句话：**如果「关系」本身就是你要查的东西，用图库；如果只是要按关键词找文本，用全文索引就够了。**

### 所以对你的项目意味着什么

- 现在这层能工作，但属于「能用图库，但不是非图库不可」。
- 想让它有价值，得往「关系」上走：把叙事和资产/行业连起来，做传导路径检索；面试时这也是一个能主动讲的改进点——「当前实现只用了全文检索，下一步会把叙事挂到行业节点上做多跳召回」。


## 十、教程与资源

| 资源 | 链接 | 用途 |
| --- | --- | --- |
| 本地内置教程 | 浏览器里执行 `:play movies` | 20 分钟建立图直觉，最快 |
| Getting Started | https://neo4j.com/docs/getting-started/ | 安装 + 第一个图 |
| Cypher 手册 | https://neo4j.com/docs/cypher-manual/current/ | 语法字典 |
| Cypher 速查表 | https://neo4j.com/docs/cypher-cheat-sheet/ | 一页 PDF |
| GraphAcademy | https://graphacademy.neo4j.com/ | 免费课，`Cypher Fundamentals` 约 2 小时 |
| Sandbox | https://sandbox.neo4j.com/ | 云端免费实例 |
| 中文镜像 | https://neo4j.ac.cn/ | 官方文档中文版 |

建议路径：`:play movies` → GraphAcademy 的 Cypher 基础 → 回来看本文第三章那条查询。集群、备份、GDS 算法库可以先跳过。

## 十一、面试会问什么

图库这块，被问到的概率不高，但一旦问到，基本集中在下面六个问题。

### 1. 什么时候该用图数据库，什么时候不该

**一句话**：当「关系本身是查询目标、且需要多跳」时才用。

- 该用：资产→行业→政策→事件的传导链、社交关系、权限继承链、知识图谱。
- 不该用：只是按 id 查、按关键词搜、做统计报表——关系库或 ES 更省事。

补充一句能加分的：关系库做多跳是 `JOIN`，深度一加执行计划就爆炸（笛卡尔积风险）；Neo4j 用**索引邻接**，每个节点直接持有相邻边的指针，跳数是常数级开销。

### 2. 你们项目里为什么用它、存了什么

**照实说**：存公共的市场叙事（`tenant_id='global'`），用全文索引按关键词召回，和用户私有的向量记忆合并后重排。

**主动补一句短板**（面试官很吃这套）：「目前只用了全文检索，一条关系都没建，其实用 ES 也能替代；下一步会把叙事挂到行业节点上做多跳传导。」

### 3. Cypher 和 SQL 有什么本质区别

|      | SQL       | Cypher                         |
| ---- | --------- | ------------------------------ |
| 思维   | 表 + join  | 画模式                            |
| 多跳   | 每层一个 join | `(a)-[:X]->(b)-[:Y]->(c)` 一条写完 |
| 变长路径 | 难         | `[:X*1..3]` 直接表达               |
| 弱项   | 深层递归      | 大范围聚合、跨表统计                     |


### 4. 索引有哪几种、不建会怎样

- **唯一约束**：`CREATE CONSTRAINT ... REQUIRE n.id IS UNIQUE`，兼做索引。
- **范围索引**：等值/范围查询用，最常见。
- **全文索引**：`db.index.fulltext.queryNodes`，分词后按相关度打分。
- **向量索引**：5.11+ 支持，能直接做相似度检索（和 Milvus 竞争）。

不建索引 → 查询退化成**全图扫描**，节点一多就慢到不可用。这也是很多人「图库用着比 MySQL 还慢」的真实原因。

### 5. 图库的坑在哪

1. **超级节点**：一个节点连了几百万条边（如“热门股”），遍历时爆炸。
2. **不适合大范围聚合**：`COUNT`/`SUM` 全图统计比列存慢得多。
3. **写放大**：每条边都要维护双向指针，写入比关系库重。
4. **跨库无事务**：和关系库、向量库之间只能靠应用层补偿——这正是本项目 `_store_preference_memory` 里 `try/except + 回滚` 的原因。

### 6. 建模题：什么时候把「关系」升级成「节点」

判断标准：**这条关系需要被别人引用、或者自己带一堆属性时，就升级成节点。**

```cypher
// 简单关系：只表示“属于”
(:Stock)-[:BELONGS_TO]->(:Industry)

// 升级成节点：这笔持仓本身有成本、数量、时间，还要被别的东西引用
(:Portfolio)-[:HOLDS {shares: 100, cost: 180}]->(:Stock)      // 关系带属性版
(:Holding {shares: 100, cost: 180})-[:OF]->(:Stock)           // 升级成节点版
```

第二种更好，因为 `Holding` 之后可能要挂交易记录、分红流水。

### 答题策略

面试官问图库，多半只是想确认你**知道它适合什么、不适合什么**，不是考你写复杂 Cypher。所以别背语法，把第 1 条和第 5 条讲清楚就够了；能主动说出「我们项目其实用浅了」，比硬夸技术选型更加分。
