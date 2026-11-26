"""演示 LangGraph 的 State + reducer：谁追加、谁累加、谁覆盖。"""

import operator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages


class State(TypedDict):
    messages: Annotated[list, add_messages]   # 追加：新消息接到末尾
    retry: Annotated[int, operator.add]       # 累加：返回值加到旧值上
    user_id: str                              # 覆盖：后写的盖掉先写的


def node_a(state: State) -> dict:
    print("进入 a，当前 retry =", state["retry"])
    return {
        "messages": [{"role": "user", "content": "你好，我是 A"}],
        "retry": 1,
        "user_id": "u_a",
    }


def node_b(state: State) -> dict:
    print("进入 b，拿到 a 写的 user_id =", state["user_id"])
    return {
        "messages": [{"role": "assistant", "content": "收到，我是 B"}],
        "retry": 2,
        "user_id": "u_b",
    }


graph = StateGraph(State)
graph.add_node("a", node_a)
graph.add_node("b", node_b)
graph.add_edge(START, "a")
graph.add_edge("a", "b")
graph.add_edge("b", END)
app = graph.compile()

result = app.invoke({"messages": [], "retry": 0, "user_id": ""})

print("\n--- 结果 ---")
print("messages 条数:", len(result["messages"]))
for m in result["messages"]:
    print("  ", type(m).__name__, m.content)
print("retry   :", result["retry"], "（0 + 1 + 2）")
print("user_id :", result["user_id"], "（被 b 覆盖）")
