from langgraph.graph import StateGraph, START, END
from typing import TypedDict

# Step 1: 定义 State
class SimpleState(TypedDict):
    message: str
    processed: bool

# Step 2: 定义节点函数
def greet_node(state: SimpleState) -> dict:
    """欢迎节点：生成问候语"""
    print(f"[greet_node] 收到消息: {state['message']}")
    return {"message": f"你好！{state['message']}"}

def process_node(state: SimpleState) -> dict:
    """处理节点：标记为已处理"""
    print(f"[process_node] 处理消息: {state['message']}")
    return {"processed": True}

# Step 3: 构建图
builder = StateGraph(SimpleState)

# 添加节点
builder.add_node("greet", greet_node)
builder.add_node("process", process_node)

# 添加边
builder.add_edge(START, "greet")
builder.add_edge("greet", "process")
builder.add_edge("process", END)

# Step 4: 编译图
graph = builder.compile()

# Step 5: 运行
result = graph.invoke({
    "message": "世界",
    "processed": False
})

print(f"\n最终结果: {result}")


# 可视化：流程图保存为同目录下的 png 文件
from pathlib import Path

png_path = Path(__file__).with_name("graph.png")
png_path.write_bytes(graph.get_graph().draw_mermaid_png())
print(f"\n流程图已保存到 {png_path}")

# 或者打印 Mermaid 格式
print(graph.get_graph().draw_mermaid())