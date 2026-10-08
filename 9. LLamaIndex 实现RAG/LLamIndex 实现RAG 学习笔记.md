# LlamaIndex 实现 RAG — 学习笔记

## 0. 一句话理解

**RAG（检索增强生成）= 先"查资料"再"回答"**。

大模型训练完就"冻结"了，不知道你私有的数据（财报、合同、内部文档）。RAG 的做法是：把文档先存进一个"知识库"，用户提问时先**从知识库里检索最相关的片段**，连同问题一起喂给大模型，让它**基于这些片段回答**——相当于给大模型配了一个随叫随到的"资料库"。

```
提问 → 检索最相关文档片段 → 片段+问题 一起给 LLM → 基于片段回答
```

好处：**不训练模型也能让它懂你的数据**，且答案可溯源、可随时更新知识库。

---

## 1. LlamaIndex 是什么

LLM 应用的数据框架，专为 RAG 设计。它帮你把「文档 → 可检索的知识库 → 问答」整条链路串起来，你只需要写几行代码。

| 模块 | 一句话作用 | 类比 |
|------|-----------|------|
| **Data connectors** | 从各种数据源加载数据 | 图书管理员把书搬进来 |
| **Data indexes** | 分块 + 向量化 + 建索引 | 给书做目录和关键词检索卡 |
| **Query Engines** | 检索 + 拼上下文 + 生成回答 | 借书 + 请专家回答 |
| **Data agents** | LLM + 工具，自动做复杂任务 | 智能助手，自己决定用什么工具 |

> LlamaIndex 是"数据框架"，不是模型。它本身不产生知识，是**组织数据 + 调模型**的那层胶水。

---

## 2. 环境安装

核心思想：**模块化安装，只装需要的**。0.10+ 把整个框架拆成很多小包，避免一把梭装个巨无霸（也减少依赖冲突）。

```bash
# 核心框架
pip install llama-index-core                                        # 索引/查询/内存/工具
pip install llama-index-readers-file llama-index-readers-web        # 数据连接器：读文件/网页

# 模型：阿里云百炼 DashScope 千问
pip install llama-index-llms-dashscope llama-index-embeddings-dashscope

# 向量库 + 检索器
pip install llama-index-vector-stores-faiss faiss-cpu                # FAISS 向量库
pip install llama-index-retrievers-bm25 rank-bm25                    # BM25 关键词检索

# 文档解析
pip install pypdf python-pptx trafilatura                            # 本地 PDF/PPT/网页
pip install llama-parse                                              # 云解析复杂 PDF
```

> 记法：**core + readers（数据）+ llms/embeddings（模型）+ vector-stores/retrievers（检索）+ 解析库**，各司其职。

---

## 3. 配置模型（Settings）

核心思想：**一次配置，全局复用**。`Settings` 是 LlamaIndex 的"全局配置中心"，在这里设好 LLM 和 Embedding，后面所有索引、检索、问答都会自动用上，不用到处重复传参。

```python
import os, getpass
if not os.getenv('DASHSCOPE_API_KEY'):
    os.environ['DASHSCOPE_API_KEY'] = getpass.getpass('输入百炼 API Key: ')
api_key = os.environ['DASHSCOPE_API_KEY']

from llama_index.core import Settings
from llama_index.llms.dashscope import DashScope
from llama_index.embeddings.dashscope import DashScopeEmbedding

Settings.llm = DashScope(
    api_key=api_key,                    # 必须显式传，DashScope 不读环境变量
    model_name='qwen-plus',             # qwen-plus/max/turbo
    temperature=0.2,                    # 低温度 → 回答更稳定严谨
    is_function_calling_model=False,    # 关函数调用 → Agent 走 ReActAgent（千问兼容更好）
)
Settings.embed_model = DashScopeEmbedding(
    api_key=api_key,
    model_name='text-embedding-v3',     # 中文向量模型
    embed_batch_size=10,                # DashScope 单次最多 10 条
)
```

**三个模型概念**：
- **LLM（生成模型）**：负责"说话"，回答你的问题（这里用千问）
- **Embedding（向量模型）**：负责"算相似度"，把文本变成数字向量（这里用 text-embedding-v3）
- **向量维度**：`text-embedding-v3` = 1024 维。**建索引/检索时维度必须一致**，否则报错

**踩过的坑**：
- DashScope 的 `api_key` 必须显式传，它**不读** `DASHSCOPE_API_KEY` 环境变量
- `embed_batch_size` 必须 ≤ 10，否则接口报 "batch size larger than 10"
- `is_function_calling_model=False`：千问走 FunctionAgent 时返回的 JSON 不干净会报错，关掉后改走 ReActAgent 更稳

---

## 4. 最小 RAG 示例

核心思想：**RAG 全流程就 4 步**——读、建、问、答。这是理解整个框架的钥匙：

```python
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex

documents = SimpleDirectoryReader('data').load_data()    # ① 读文档
index = VectorStoreIndex.from_documents(documents)       # ② 建索引（自动分块+向量化）
query_engine = index.as_query_engine(similarity_top_k=5) # ③ 查询引擎
response = query_engine.query('收盘价多少')               # ④ 提问
print(response)
```

第②步一行代码，内部其实做了三件事：**分块 → 向量化 → 建索引**。`similarity_top_k=5` 表示"检索时拿最相关的 5 个片段"。

---

## 5. 数据连接器（Data connectors）

核心思想：**不同数据源用不同"读法"**。`SimpleDirectoryReader` 按文件扩展名自动选解析器，也能自定义。

### 5.1 本地文件 + 网页

```python
from llama_index.core import SimpleDirectoryReader
from llama_index.readers.file import PyMuPDFReader          # PDF 解析（带坐标）
from llama_index.readers.web import BeautifulSoupWebReader  # 网页解析

local_loader = SimpleDirectoryReader(
    input_dir='./data',
    required_exts=['.pdf', '.docx', '.pptx', '.epub', '.md'],   # 只读这些类型
    file_extractor={'.pdf': PyMuPDFReader()},                   # 指定 PDF 用谁解析
)
local_docs = local_loader.load_data()

web_loader = BeautifulSoupWebReader()
web_docs = web_loader.load_data(urls=['https://...'])

documents = local_docs + web_docs   # 合并，后续统一处理
```

> `file_extractor` 是「扩展名 → 解析器」的映射，**想换 PDF 解析器就改这一处**，很灵活。

### 5.2 LlamaParse 云解析（复杂 PDF）

核心思想：**普通 PDF 用本地库就够了；表格、公式、扫描件用云端**。LlamaParse 是官方云服务，识别准确度高很多，但要联网 + 消耗额度。

```python
from llama_parse import LlamaParse

parser = LlamaParse(
    api_key=os.environ['LLAMA_CLOUD_API_KEY'],  # 独立于百炼的另一套 Key
    result_type='markdown',                     # 输出 Markdown，保留表格/层级
    num_workers=3,                              # 并行解析
)
file_extractor = {'.pdf': parser}               # 覆盖默认 PDF 解析器
documents_cloud = SimpleDirectoryReader('./data', file_extractor=file_extractor).load_data()
```

---

## 6. 分块（Chunking）

核心思想：**大模型一次吃不了整本书**。把长文档切成小段（chunk），检索时只取最相关的几段给模型——既省 token 又提高精度。

```python
from llama_index.core.node_parser import SentenceSplitter

splitter = SentenceSplitter(
    chunk_size=1024,      # 每块目标长度（太大丢精度，太小丢上下文）
    chunk_overlap=100,    # 相邻块重叠，防止切断关键信息
    paragraph_separator='\n\n',   # 按段落边界切，尽量不拆表格
)
nodes = splitter.get_nodes_from_documents(documents)  # 产出节点列表
```

**两个权衡**：
- `chunk_size` 太大 → 片段信息杂，检索不准
- `chunk_size` 太小 → 上下文不完整，模型理解不了
- `chunk_overlap` 重叠 → 关键句跨块时，两边都能检索到

> 版本坑：0.10.21+ 参数名是 `chunk_overlap`（旧版叫 `overlap`）。

---

## 7. 建索引（Indexing）

### 7.1 IngestionPipeline（现代做法）

核心思想：**把「清洗→分块→向量化→存库」串成流水线**。像工厂流水线，想加环节就往列表里追加（去重、抽元数据、抽标题），方便复用和管理。

```python
from llama_index.core.ingestion import IngestionPipeline

pipeline = IngestionPipeline(transformations=[
    SentenceSplitter(chunk_size=1024, chunk_overlap=100),  # ① 分块
    Settings.embed_model,                                  # ② 向量化
])
nodes_pipe = await pipeline.arun(documents=documents)      # 异步执行
```

### 7.2 FAISS 向量库

核心思想：**数据量大时，内存索引检索慢**。FAISS 是 Facebook 开源的向量检索库，专门做大规模相似度搜索，更快、可扩展。

```python
import faiss
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.vector_stores.faiss import FaissVectorStore

d = 1024  # 必须 = embedding 维度（text-embedding-v3）
faiss_index = faiss.IndexFlatL2(d)                    # L2 距离衡量相似度
vector_store = FaissVectorStore(faiss_index=faiss_index)
storage_context = StorageContext.from_defaults(vector_store=vector_store)
vector_index = VectorStoreIndex(nodes, storage_context=storage_context)
```

> `StorageContext` 告诉 LlamaIndex"向量存到 FAISS、节点信息走默认路径"。

---

## 8. 检索（Retrieval）

### 8.1 向量检索（默认）

```python
from llama_index.core.retrievers import VectorIndexRetriever

vector_retriever = VectorIndexRetriever(index=vector_index, similarity_top_k=5)
```

> 原理：把问题也向量化，在索引里找**余弦/距离最接近**的片段。

### 8.2 混合检索 + Rerank（推荐，效果好很多）

核心思想：**纯向量检索有盲区**。它擅长"意思相近"，但会漏掉"关键词精确匹配"（比如搜"安宫牛黄丸"这种专有名词）。所以：

- **向量检索**：懂语义，找"意思像的"
- **BM25 关键词检索**：懂字面，找"词出现的"
- **Rerank 精排**：把两路结果混合后再让 LLM 挑一遍，留最相关的

```
向量检索 ┐
         ├→ 融合 → Rerank 精排 → 最相关的 top-3 → 喂给 LLM
BM25    ┘
```

```python
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.core.retrievers import QueryFusionRetriever
from llama_index.core.postprocessor import LLMRerank
from llama_index.core.query_engine import RetrieverQueryEngine

bm25_retriever = BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=5)

hybrid_retriever = QueryFusionRetriever(
    [vector_retriever, bm25_retriever], similarity_top_k=5, num_queries=1,
)
reranker = LLMRerank(top_n=3, llm=Settings.llm)

query_engine = RetrieverQueryEngine.from_args(
    retriever=hybrid_retriever, node_postprocessors=[reranker],
)
response = query_engine.query('世运电路2023年同比增长率是多少？')
```

### 8.3 调试：看检索到啥

```python
retrieved_nodes = vector_retriever.retrieve('查询')
for i, node in enumerate(retrieved_nodes):
    print(node.score, node.node.text[:300])   # score 越小越相似（L2 距离）
```

> 检索效果不好时，**先看召回结果再改**：是分块太粗？还是该换检索/加 Rerank？——先看证据再下药。

---

## 9. 带记忆的聊天（Query Engines）

核心思想：**单次问答是"失忆"的**。多轮对话需要"记忆"——把历史对话存下来，每轮一起带上。

```python
from llama_index.core.memory import ChatMemoryBuffer

memory = ChatMemoryBuffer.from_defaults(token_limit=5000)  # 记忆上限，超了丢最老的
chat_engine = vector_index.as_chat_engine(
    chat_mode='context',    # 每轮先检索相关文档，再结合对话历史回答
    memory=memory,
    system_prompt='基于检索信息回答，没有就根据自身能力回答',
)
r1 = chat_engine.chat('詹姆斯是谁')
r2 = chat_engine.chat('世运电路2023年上半年营业收入多少')  # 能接上文
```

---

## 10. Agent（AgentWorkflow）

核心思想：**从"被问一句答一句"升级到"自主完成任务"**。Agent = LLM + 一组工具 + 系统提示词，模型自己决定**何时调用哪个工具**、怎么组合。

```python
from llama_index.core.agent.workflow import AgentWorkflow
from llama_index.core.tools import FunctionTool, QueryEngineTool

# 工具 1：把自定义函数包装成工具
def vector_query(query: str, page_numbers: list) -> str:
    return str(vector_index.as_query_engine(similarity_top_k=5).query(query))

vector_tool = FunctionTool.from_defaults(
    name='vector_tool',
    description='文档精确检索，回答具体数据时使用',   # 描述告诉 Agent 何时用它
    fn=vector_query,
)

# 工具 2：把查询引擎包装成工具
summary_tool = QueryEngineTool.from_defaults(
    name='summary_tool', query_engine=summary_engine,
    description='全文总结时使用',
)

# 构建 Agent
agent = AgentWorkflow.from_tools_or_functions(
    tools_or_functions=[vector_tool, summary_tool],
    llm=Settings.llm,
    system_prompt='你是 RAG 助手。需要数据调 vector_tool，需要总结调 summary_tool。',
    verbose=True,   # 打印 Agent 每步思考，方便观察
)
resp = await agent.run('总结一下兴证电子')   # Agent 自动选工具
```

**踩过的坑**：
- 0.14 版：`from_tools` 改名 **`from_tools_or_functions`**，参数也变 `tools_or_functions`
- 千问默认走 FunctionAgent 会报 JSONDecodeError → 在 cell-04 设 `is_function_calling_model=False`，Agent 改走 **ReActAgent**（用文本格式解析工具调用，兼容性好）

---

## 11. 索引持久化

核心思想：**建索引很费时费钱（解析+向量化）**。存到磁盘，下次启动直接加载，秒开。

```python
from llama_index.core import VectorStoreIndex, StorageContext, load_index_from_storage

# 保存（默认 SimpleVectorStore，纯 JSON 可加载）
index = VectorStoreIndex(nodes)
index.storage_context.persist(persist_dir='./storage')

# 加载
sc = StorageContext.from_defaults(persist_dir='./storage')
loaded = load_index_from_storage(sc)
loaded.as_query_engine().query('...')
```

**关键点**：
- 默认 SimpleVectorStore 持久化是 JSON，`load_index_from_storage` 能正确加载
- **FAISS 持久化是二进制**，不能直接 `load_index_from_storage`（会 UnicodeDecodeError），需用 `FaissVectorStore` 配套加载
- 加载时 `Settings.embed_model` 必须和保存时**维度一致**
- 大数据量生产环境，用专业向量库（PGVector / Milvus / Qdrant）

---

## 12. 常见坑速查表

| 报错 | 原因 | 解决 |
|------|------|------|
| `api_key Input should be a valid string` | 没显式传 api_key | DashScope 加 `api_key=` |
| `batch size larger than 10` | 一批发太多 | `embed_batch_size=10` |
| `No module named fitz/pymupdf` | 缺 PDF 解析库 | `pip install pymupdf` |
| `No module named llama_parse` | 缺云解析包 | `pip install llama-parse` |
| `ModuleNotFoundError: openai embedding` | Settings.embed_model 没配，fallback 到 OpenAI | 先跑 cell-04 配好 DashScope |
| `NameError: DashScope not defined` | import 段没跑 | 整体运行整个 cell，不是选中行 |
| `from_tools has no attribute` | 版本 API 改名 | 用 `from_tools_or_functions` |
| `JSONDecodeError`（Agent） | FunctionAgent 解析千问 JSON 失败 | `is_function_calling_model=False` 走 ReActAgent |
| `UnicodeDecodeError` 读 storage | FAISS 二进制被当 JSON 读 | 用默认 SimpleVectorStore 持久化 |

---

## 13. 整体回顾：RAG 全链路图

```
                ┌───────────── 离线（一次性）─────────────┐
数据源（PDF/网页/Word） ─→ SimpleDirectoryReader ─→ 分块 ─→ 向量化 ─→ 建索引（FAISS/内存）
  （Data connector）      （Chunking）           （Embedding）    （Index）
                └───────────────────────────────────────────┘
                                                          │
                ┌───────────── 在线（每次提问）────────────┐
   用户问题 ─→ 向量化 ─→ 检索（向量+BM25） ─→ Rerank ─→ 相关片段+问题 ─→ LLM(千问) ─→ 回答
                                          （混合检索）      （精排）
                └──────────────────────────────────────────┘
```

**两个阶段**：
- **离线**：把文档变成可检索的知识库（读→分块→向量化→建索引），做一次
- **在线**：每次提问都走一遍（检索→拼上下文→生成），可反复
