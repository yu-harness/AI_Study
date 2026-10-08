from langchain_community.document_loaders import TextLoader
import os
# 基于脚本自身位置定位文件，避免「在当前目录之外运行」导致路径失效
# encoding="utf-8"：文件是 UTF-8 编码，但 Windows 中文系统默认用 GBK 打开，需显式指定
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
loader = TextLoader(os.path.join(BASE_DIR, "藜麦.txt"), encoding="utf-8")
documents = loader.load()

from langchain_text_splitters import RecursiveCharacterTextSplitter
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=128,  # 根据嵌入模型调整（如text-embedding-ada-002支持8191）
    chunk_overlap=50,
    separators=["\n\n", "\n", "。",  "！", "？","//"]  # 优化分隔符
)

texts = text_splitter.create_documents([documents[0].page_content],metadatas=[documents[0].metadata])


from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from langchain_community.vectorstores import Chroma

# # 使用本地模型路径
# model_path = "/root/autodl-tmp/AI-ModelScope/m3e-base"

# # 确保模型路径存在
# if not os.path.exists(model_path):
#     raise FileNotFoundError(f"模型路径不存在: {model_path}")

# 配置embedding模型参数
model_kwargs = {'device': 'cpu'}  # 使用CPU
encode_kwargs = {'normalize_embeddings': True}  # 标准化嵌入向量

# 创建embedding模型实例
embedding = HuggingFaceBgeEmbeddings(
    model_name="moka-ai/m3e-small",  # 使用本地路径而非HuggingFace ID
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs,
    query_instruction="为文本生成向量表示用于文本检索"  # M3E模型不需要特定指令，但保留不影响
)


# 加载数据到Chroma数据库
db = Chroma.from_documents(documents, embedding)
# similarity search
search_result = db.similarity_search("藜一般在几月播种？")
print("=== 检索结果（藜一般在几月播种？）===")
for i, doc in enumerate(search_result):
    print(f"[{i+1}] {doc.page_content[:200]}...")


from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from langchain_core.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="deepseek-v3", # 使用千帆modelbuilder上的deepseek-v3
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key="",  # 你的api-key，在这里创建：https://console.bce.baidu.com/iam/#/iam/apikey/list
    base_url="https://qianfan.baidubce.com/v2/", # 千帆modelbuilder 的base_url
    # organization="...",
    # other params...
)
retriever = db.as_retriever()
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
qa = ConversationalRetrievalChain.from_llm(llm, retriever, memory=memory)
result = qa.invoke({"question": "藜怎么防治虫害？"})
print("\n=== 问答结果 ===")
print("问题:", result.get("question"))
print("答案:", result.get("answer"))