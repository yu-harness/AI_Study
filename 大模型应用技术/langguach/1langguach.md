---
title: "1langguach"
topic: "大模型应用技术"
type: note
date: 2026-11-13
---

# LangGraph 入门教程

一句话：**LangGraph 把 Agent 写成一幅流程图，节点是干活的函数，边决定下一步去哪，所有节点共用一张状态表。**

跟普通 LLM 调用链的区别：链是直线，走完就结束；图可以分叉、可以回头、可以停下来等人。

## 一、三个核心概念

- **State（状态）**：一张贯穿着整幅图的共享表，谁都能读、谁都能写。
- **Node（节点）**：一个普通函数，收状态、干活、返回自己改了哪几块。
- **Edge（边）**：规定下一步去哪，可以写死，也可以按状态临时判断。

打个比方：State 是传送带上的托盘，Node 是工位，Edge 是传送带的方向。

![[Pasted image 20261113141043.png|656]]

## 二、第一个图：最小可运行

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    text: str

def hello(state: State) -> dict:
    return {"text": state["text"] + "，你好"}

def bye(state: State) -> dict:
    return {"text": state["text"] + "，再见"}

builder = StateGraph(State)      # 1. 声明状态类型
builder.add_node("hello", hello) # 2. 注册节点：名字 + 函数
builder.add_node("bye", bye)
builder.add_edge(START, "hello") # 3. 连边
builder.add_edge("hello", "bye")
builder.add_edge("bye", END)

app = builder.compile()          # 4. 编译成可执行图
print(app.invoke({"text": "开始"}))
# {'text': '开始，你好，再见'}
```

四步记住就行：**建图 → 加节点 → 连边 → 编译**。编译之后图就定死了，不能再加节点。

## 三、State 状态管理

### 3.1 状态就是一张表

每个节点拿到的都是**同一份 State**，不是各自的副本。节点返回的不是完整状态，而是「我改了哪几块」的补丁，框架负责合并。

```python
def node(state: State) -> dict:
    return {"text": "新值"}      # 只更新 text，其他字段原样保留
```

### 3.2 字段即通道，reducer 决定怎么合并

State 的每个字段在内部对应一个通道（channel）。写入怎么落地，由这个字段的 reducer 决定：

- **不写 reducer**：覆盖，后写的赢。
- **写 reducer**：按规则合并，比如追加、累加。

```python
from typing import Annotated
import operator
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]   # 追加
    retry: Annotated[int, operator.add]       # 累加
    user_id: str                             # 覆盖
```

三种形态对照：

| 写法 | 合并行为 | 典型用途 |
| --- | --- | --- |
| `field: str` | 直接覆盖 | 当前状态、开关、结论 |
| `Annotated[list, add_messages]` | 追加到末尾 | 多轮对话消息 |
| `Annotated[int, operator.add]` | 旧值 + 新值 | 计数、重试次数、token |

![[Pasted image 20261113141256.png|700]]

配套示例脚本：`state_demo.py`，跑一下能看到「两条消息、retry 累加到 3、user_id 被后者覆盖」。

### 3.3 两个容易踩的坑

- 多个节点往同一个列表字段写，却没配 reducer → 前面的内容被覆盖，消息会丢。
- 节点里直接改 `state["x"] = ...` 不算数，框架只认返回值。虽然 Python 对象能改，但在并发分支或恢复快照时不可靠。

### 3.4 设计建议

- 字段尽量扁平，别套深层字典，reducer 只作用在顶层。
- 按用途分组：输入、中间结果、最终产出、账本（token、耗时）分开。
- 大对象存 id 或引用，别把整份文档塞进状态。

## 四、节点与边

### 4.1 节点的规矩

- 就是一个函数，参数是 State，返回值必须是 dict。
- 可以返回空 dict，表示不改任何字段。
- 可以抛异常，异常会让整个 `invoke` 失败。
- 节点内部做耗时操作没关系，但别写死循环。

### 4.2 四种边

- **普通边**：`add_edge("a", "b")`，写死。
- **条件边**：`add_conditional_edges`，由一个函数现场决定。
- **起始边**：`START → 第一个节点`。
- **结束边**：`某节点 → END`。

### 4.3 条件边怎么写

```python
def route(state: State) -> str:
    if len(state["messages"]) > 5:
        return "summarize"
    return "chat"

builder.add_conditional_edges(
    "router",              # 从哪个节点出发
    route,                 # 判断函数，返回字符串
    {"summarize": "summarize", "chat": "chat"},  # 返回值 → 真实节点
)
```

判断函数的返回值必须能在映射表里找到，表的值才是真正要去的节点。少写一个 key，运行时直接报错。

## 五、循环：让图自己转圈

条件边指回自己，就是循环。必须**给出口**，否则会跑到超限：

```python
class State(TypedDict):
    count: int

def work(state: State) -> dict:
    print("第", state["count"] + 1, "轮")
    return {"count": state["count"] + 1}

def should_continue(state: State) -> str:
    return "work" if state["count"] < 3 else END

builder = StateGraph(State)
builder.add_node("work", work)
builder.add_edge(START, "work")
builder.add_conditional_edges("work", should_continue, {"work": "work", END: END})
app = builder.compile()

app.invoke({"count": 0})   # 打印三轮后结束
```

LangGraph 有默认的**递归上限（25 步）**，防止写出停不下来的图。

## 六、持久化：让图记住上一轮

编译时挂一个 checkpointer，同一个 `thread_id` 的历史就能接上：

```python
from langgraph.checkpoint.memory import InMemorySaver

app = builder.compile(checkpointer=InMemorySaver())
config = {"configurable": {"thread_id": "user-001"}}

app.invoke({"messages": [("user", "我叫小明")]}, config)
app.invoke({"messages": [("user", "我叫什么？")]}, config)   # 能接上上文

snapshot = app.get_state(config)      # 看当前状态
print(snapshot.values)
```

要点：

- 不传 `thread_id` 会直接报错，因为不知道该存到哪个线程。
- `InMemorySaver` 只存在内存，进程结束就没了；生产换 `SqliteSaver` 或 `PostgresSaver`。
- 每个 super-step 结束都会存一份快照，这是断点续跑、人工介入、时间旅行的基础。

## 七、流式输出

一次性 `invoke` 要等全跑完，想看过程就用 `stream`：

```python
for chunk in app.stream({"messages": [("user", "你好")]}, config, stream_mode="updates"):
    print(chunk)
```

三种常用模式：

- `values`：每步吐完整状态，最直观，也最占带宽。
- `updates`：每步只吐这个节点改了什么，最省。
- `messages`：逐 token 吐模型输出，做打字机效果用它。

## 八、人工介入：中途停下来等人

```python
from langgraph.types import interrupt, Command

def ask_human(state: State) -> dict:
    answer = interrupt("是否继续执行？")   # 这里会暂停
    return {"text": f"用户回答：{answer}"}

# 第一次调用会停在 interrupt
app.invoke({"text": ""}, config)
# 用户确认后，从断点继续
app.invoke(Command(resume="继续"), config)
```

**前提是必须挂 checkpointer**，否则暂停之后状态就没了，没法恢复。

## 九、接真实模型：DeepSeek

`.env` 已经配好，填上 key 就能跑：

```python
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()
llm = ChatOpenAI(
    model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url=os.getenv("DEEPSEEK_BASE_URL"),
    temperature=0,
)

def chat(state: MessagesState) -> dict:
    return {"messages": [llm.invoke(state["messages"])]}

builder = StateGraph(MessagesState)     # 内置状态，只有一个 messages 字段
builder.add_node("chat", chat)
builder.add_edge(START, "chat")
builder.add_edge("chat", END)
app = builder.compile(checkpointer=InMemorySaver())

config = {"configurable": {"thread_id": "demo"}}
print(app.invoke({"messages": [("user", "用一句话解释什么是 ETF")]}, config)["messages"][-1].content)
```

`MessagesState` 是官方给的最小状态，等价于 `{"messages": Annotated[list, add_messages]}`，省得自己写。

## 十、常见坑

- 编译后再 `add_node`，无效，必须重新建图。
- 节点返回 `None` 会报错，至少返回 `{}`。
- 条件边映射表少 key，运行时 `KeyError`。
- 忘了 `thread_id`，持久化直接失败。
- `langgraph` 包里没有 `__version__`，要查版本用 `importlib.metadata.version("langgraph")`。
- `langchain-openai` 版本比 `langchain` 旧时，可能出现 `langchain_core` 不兼容，报错再单独升级。

## 十一、和 FinAgent 本项目的对应关系

- 项目里的 `AgentState` 就是这里的 State，只是字段多得多。
- `_build_chat_graph` 就是「建图」那四步，节点十一个。
- `_next_route_node` 就是条件边的判断函数，返回下一站的名字。
- `run_chat` 里的 `chat_graph.stream(..., stream_mode="updates")` 就是第七节的流式，再包一层 SSE 给前端。
- 项目把快照存进数据库而不是 `InMemorySaver`，所以能做到 `/v1/tasks/{task_id}/resume`。
