# -*- coding: utf-8 -*-
# 强制 stdout/stderr 用 UTF-8 输出，避免 Windows 终端 GBK 编码导致 print 中文崩溃
import sys
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ("utf-8", "utf8"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
"""
RAG 完整流程（修复版）
=====================
流程：加载文档 → 切分 → 向量化 → 存储向量库 → 检索 → LLM 问答

相对原版 rag.py 的修复：
1. 【关键】Chroma 存储改用切分后的 texts，而不是未切分的原始 documents
2. 删除未使用的导入（PromptTemplate、Chat prompt 类等）
3. 切分分隔符补充中文逗号「，」，长句切分更均匀
4. API Key 用环境变量读取（DASHSCOPE_API_KEY），避免明文泄露
5. 适配 langchain 1.x：legacy 链从 langchain_classic 导入
6. TextLoader 显式指定 encoding="utf-8"，避免 Windows GBK 解码中文报错
7. 脚本顶部强制 stdout 用 UTF-8，避免终端 print 中文崩溃
"""

# ============ 第 1 步：加载文档 ============
import os
from langchain_community.document_loaders import TextLoader

# 基于脚本自身位置定位文件，而不是当前工作目录，避免「在哪运行」导致路径失效
# encoding="utf-8"：文件是 UTF-8 编码，但 Windows 中文系统默认用 GBK 打开，需显式指定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
loader = TextLoader(os.path.join(BASE_DIR, "藜麦.txt"), encoding="utf-8")
documents = loader.load()
print(f"已加载 {len(documents)} 篇文档，全文长度：{len(documents[0].page_content)} 字")

# ============ 第 2 步：文本切分 ============
# chunk_size 对中文按字符数计算，128 字 ≈ 一个小段落
# chunk_overlap 让相邻片段有重叠，避免语义在边界被切断
from langchain_text_splitters import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=128,        # 根据嵌入模型调整（如 text-embedding-ada-002 支持 8191）
    chunk_overlap=50,      # 相邻片段重叠 50 字
    separators=["\n\n", "\n", "。", "！", "？", "，", "//"]  # 优化分隔符，补充中文逗号
)

texts = text_splitter.create_documents(
    [documents[0].page_content], metadatas=[documents[0].metadata]
)
print(f"切分为 {len(texts)} 个片段")

# ============ 第 3 步：配置 Embedding 模型 ============
from langchain_community.embeddings import HuggingFaceBgeEmbeddings

# 使用本地模型路径（若在本机，可取消注释并改成本机路径）
# model_path = "/root/autodl-tmp/AI-ModelScope/m3e-base"
# if not os.path.exists(model_path):
#     raise FileNotFoundError(f"模型路径不存在: {model_path}")

model_kwargs = {'device': 'cpu'}                     # 使用 CPU
encode_kwargs = {'normalize_embeddings': True}       # 标准化嵌入向量

embedding = HuggingFaceBgeEmbeddings(
    model_name="moka-ai/m3e-small",   # m3e 模型较小，适合学习场景
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs,
    query_instruction="为文本生成向量表示用于文本检索"
)

# ============ 第 4 步：存入向量库（修复点） ============
# 原代码误用了未切分的 documents，这里改用切分好的 texts
# —— 切分是 RAG 的灵魂，检索命中与否取决于片段粒度
from langchain_community.vectorstores import Chroma

db = Chroma.from_documents(texts, embedding)

# ============ 第 5 步：相似度检索 ============
search_result = db.similarity_search("藜一般在几月播种？")
print("\n=== 检索结果（藜一般在几月播种？）===")
for i, doc in enumerate(search_result):
    print(f"[{i+1}] {doc.page_content[:200]}...")

# ============ 第 6 步：检索增强问答 ============
# langchain 1.x 把 legacy 链（ConversationalRetrievalChain / ConversationBufferMemory）
# 迁到了独立的 langchain_classic 包，故从 langchain_classic 导入
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI

# API Key 从环境变量读取（你已配置 DASHSCOPE_API_KEY），避免明文泄露
api_key = os.getenv("DASHSCOPE_API_KEY")

llm = ChatOpenAI(
    model="qwen-plus",            # 通义千问，可选 qwen-max / qwen-turbo
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1/",  # DashScope OpenAI 兼容接口
)

retriever = db.as_retriever()
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
qa = ConversationalRetrievalChain.from_llm(llm, retriever, memory=memory)

result = qa.invoke({"question": "藜怎么防治虫害？"})
print("\n=== 问答结果 ===")
print("问题:", result.get("question"))
print("答案:", result.get("answer"))
