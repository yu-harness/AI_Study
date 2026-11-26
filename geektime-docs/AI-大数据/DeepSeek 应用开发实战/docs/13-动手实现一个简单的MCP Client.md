你好，我是邢云阳。

上节课，我带你动手实现了一个 MCP Server，并使用 Roo Code 与 Claude Desktop 作为 MCP 客户端测试了功能。这节课，我们将进一步学习如何使用 MCP Python SDK 来编写一个 MCP Client，以便更加灵活地与 MCP 服务器进行通信和集成。

## MCP 通信方式

在写代码之前，我们需要先了解一下MCP 支持的两种通信方式：

- **标准输入输出**（Standard Input/Output, stdio）：客户端通过启动服务器子进程并使用标准输入（stdin）和标准输出（stdout）建立双向通信，一个服务器进程只能与启动它的客户端通信（1:1 关系）。stdio 适用于本地快速集成的场景。
- **服务器发送事件**（Server-Sent Events, SSE）：服务器作为独立进程运行，客户端和服务器代码完全解耦，支持多个客户端随时连接和断开。

这节课，我们分别了解一下这两种方式。

## Stdio 方式

首先我来实现一个简单的示例，带你体会一下 stdio 方式 MCP Client 与 MCP Server 的通信过程。

### 项目初始化

我们还是使用 uv 工具对项目进行初始化。

```python
uv init mcp-client-demo

uv add "mcp[cli]"

pip install mcp
```

初始化完成后，我们将 hello.py 删除，然后创建一个 client.py。

![图片](https://static001.geekbang.org/resource/image/23/e2/23e4dcede7589d9f026c9379a0d130e2.png?wh=468x262)

接下来，开始写代码。首先引用一下 MCP Client 的包。

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
```

### 设置服务器连接参数

之后需要编写设置服务器连接参数的代码。在使用 stdio 方式进行通信时，MCP 服务器的进程由 MCP 客户端程序负责启动。因此，我们通过 StdioServerParameters 来配置服务器进程的启动参数，包括运行 MCP 服务器的命令及其对应的参数。代码如下：

```python
# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="uv", # Executable
    args=[
        "run",
        "--with",
        "mcp[cli]",
        "--with-editable",
        "D:\\workspace\\python\\mcp-test\\achievement",
        "mcp",
        "run",
        "D:\\workspace\\python\\mcp-test\\achievement\\server.py"
    ],# Optional command line arguments
    env=None # Optional environment variables
)
```

代码非常简单，就是一个 command 加 args。这两部分填的内容，就是上节课我们配置 MCP Server 运行的配置文件时的内容。通过配置这部分内容，可以确保 MCP 客户端能够正确启动并连接到 MCP 服务器。

### 建立服务器连接

接下来，我们写一个 run 方法来建立客户端与服务器的连接。

```python
async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()
```

stdio\_client 负责启动服务器进程并建立双向通信通道，它返回用于读写数据的流对象。ClientSession 则在这些流的基础上提供高层的会话管理，包括初始化连接、维护会话状态等。代码无需深究其含义，会套路即可。

### 调用工具

接下来就是 MCP Client 的核心部分——工具的调用。工具的调用分为两个步骤，第一个步骤是列出 MCP Server 支持的工具，即 list\_tools()。第二个步骤是调用指定工具，即call\_tool(name, args)。 代码如下：

```python
async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("Tools:", tools)

            # call a tool
            score = await session.call_tool(name="get_score_by_name",arguments={"name": "张三"})
            print("score: ", score)
```

由于我们是与上一节课的 MCP Server 建立的连接，因此 call\_tool 的 name 参数填写上节课写的 get\_score\_by\_name 工具，工具的参数是一个字典类型，需要写成 {“arg1”: “value”} 的形式，此处写“张三”，表示返回张三的绩效。

最后不要忘了启动 run 函数。

```python
if __name__ == "__main__":
    import asyncio
    asyncio.run(run())
```

### 运行客户端

我们可以使用 uv 命令运行程序。

```python
uv run .\client.py
```

打印信息如下：

```python
[03/06/25 21:15:35] INFO     Processing request of type ListToolsRequest                              server.py:534
Tools: meta=None nextCursor=None tools=[Tool(name='get_score_by_name', description='根据员工的姓名获取该员工的绩效得分
分', inputSchema={'properties': {'name': {'title': 'Name', 'type': 'string'}}, 'required': ['name'], 'title': 'get_score_by_nameArguments', 'type': 'object'})]
                    INFO     Processing request of type CallToolRequest                               server.py:534 
score:  meta=None content=[TextContent(type='text', text='name: 张三 绩效评分: 85.9', annotations=None)] isError=False
```

可以看到 list\_tools 列出了我们定义的 get\_score\_by\_name 工具，而且很神奇的是我们的打印结果还包含了 inputSchema，这说明 MCP Server 自动帮我们写了 JSON 格式的参数描述。

之后我们通过 call\_tools 调用了 get\_score\_by\_name 工具，成功返回了张三的绩效。这说明我们这个手动版本的 MCP Client 与 MCP Server 成功建立了通信。

## SSE 方式

接下来我们看一下 SSE 方式，需要首先了解一下什么是 SSE。

### 什么是 SSE？

Server-Sent Events（SSE，服务器发送事件）是一种基于 HTTP 协议的技术，允许服务器向客户端**单向、实时地推送数据**。在 SSE 模式下，客户端通过创建一个 EventSource 对象与服务器建立**持久连接**，服务器则通过该连接**持续发送**数据流，而无需客户端反复发送请求。MCP Python SDK 使用了 Starlette 框架来实现 SSE。

SSE 模式下客户端通过访问 Server 的 /messages 端点发送 JSON-RPC 调用，并通过 /sse 端点获取服务器推送的 JSON-RPC 消息。

### 改造 MCP Server 代码

为了能让上节课编写的 MCP Server 代码支持 SSE，我们需要对代码进行改造。改造点主要是需要实现一个 SSE 服务器。先上代码：

```python
def create_starlette_app(mcp_server: Server, *, debug: bool = False) -> Starlette:
    """Create a Starlette application that can server the provied mcp server with SSE."""
    sse = SseServerTransport("/messages/")

    async def handle_sse(request: Request) -> None:
        async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )

    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
        ],
    )
```

该函数在最开始创建了 SseServerTransport 对象，并指定基础路径 /messages/，用于后续管理 SSE 连接和消息传递。

之后的 handle\_sse 是一个异步请求处理函数，当客户端请求建立 SSE 连接时会被调用。在该方法中利用 sse.connect\_sse 方法，传入当前请求的 scope、receive 方法和 \_send 方法，建立一个异步上下文管理器。管理器会返回两个数据流，分别是 read\_stream 用于读取客户端发送的数据以及 write\_stream 用于向客户端发送数据。

在成功建立连接后，调用 mcp\_server.run 方法，并传入读取、写入流以及由 mcp\_server.create\_initialization\_options() 生成的初始化参数。这一过程实现了 MCP 服务器与客户端之间的实时数据交互。

最后 create\_starlette\_app 方法返回一个新的 Starlette 应用实例，包括调试模式以及路由设置。

路由设置使用 Route(“/sse”, endpoint=handle\_sse) 定义 /sse 路径，当客户端访问此路径时将触发 handle\_sse 函数处理 SSE 连接。

使用 Mount(“/messages/”, app=sse.handle\_post\_message) 将 /messages/ 路径挂载到 sse.handle\_post\_message 应用上，用于处理通过 POST 请求发送的消息，实现与 SSE 长连接的消息传递功能。

这样，一个 SSE 服务就实现好了。这部分代码对于 Python 新手来说有点抽象，可以先直接照抄，使用起来，等到后面对于 Python 越来越熟练了，再去理解。

另一个改造点需要创建 MCP 服务器实例，然后通过上面定义的 create\_starlette\_app 方法创建 Starlette 应用，最后使用 uvicorn 启动 ASGI 服务器，实现实时的 SSE 数据传输。代码如下：

```python
if __name__ == "__main__":
    mcp_server = mcp._mcp_server

    parser = argparse.ArgumentParser(description='Run MCP SSE-based server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=18080, help='Port to listen on')
    args = parser.parse_args()

    # Bind SSE request handling to MCP server
    starlette_app = create_starlette_app(mcp_server, debug=True)

    uvicorn.run(starlette_app, host=args.host, port=args.port)
```

同样是先用起来，我们的重点要放在工具如何编写上，这种套路代码，都不需要研究太深。

代码完成后，可以通过 uv 命令运行起来：

```python
uv run server.py
```

效果为：

![图片](https://static001.geekbang.org/resource/image/88/07/886cd88e8de1c8f3cc53e0b3f2d58907.png?wh=939x161)

### 改造 MCP Client 代码

客户端的改造会相对简单，就是使用 sse\_client 替换 stdio\_client，并在初始化时传入 MCP Server 的 HTTP 访问地址。代码如下：

```python
async def connect_to_sse_server(server_url: str):
    """Connect to an MCP server running with SSE transport"""
    # Store the context managers so they stay alive
    async with sse_client(url=server_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # List available tools to verify connection
            print("Initialized SSE client...")
            print("Listing tools...")
            response = await session.list_tools()
            tools = response.tools
            print("\nConnected to server with tools:", [tool.name for tool in tools]) 

            # call a tool
            score = await session.call_tool(name="get_score_by_name",arguments={"name": "张三"})

            print("score: ", score)  
```

这段代码是对原来的 run 方法进行了改造，重点在于 1～6 行，其他部分保持不变。

之后在启动时传入 URL 即可。

```python
async def main():
    if len(sys.argv) < 2:
        print("Usage: uv run client.py <URL of SSE MCP server (i.e. http://localhost:8080/sse)>")
        sys.exit(1)
    
    await connect_to_sse_server(server_url=sys.argv[1])

if __name__ == "__main__":
    asyncio.run(main())
```

同样是使用 uv 命令运行程序：

```python
uv run client-sse.py http://localhost:18080/sse
```

效果为：

![图片](https://static001.geekbang.org/resource/image/8f/18/8fde0dc6b9aa0a2896d493d2b7614f18.png?wh=1366x235)

至此，SSE 方式就实现了。

## 总结

今天我们学习了 MCP Client 与 Server 之间的两种通讯方法，并使用代码实操的方式，体验了这两种方法的效果。这节课的[代码](https://github.com/xingyunyang01/Geek02/tree/main)已经放到了我的 GitHub 上。接下来我们通过一张表格，对这两种方式进行对比和总结。

![图片](https://static001.geekbang.org/resource/image/7f/a7/7fd634a9dd1832633fdd90dfe8d5b2a7.png?wh=1920x808)

这两种方式各有所长，于是开源社区便研发了一些协议转换工具，比如 [mcp-proxy](https://github.com/sparfenyuk/mcp-proxy) ，允许将 stdio 模式的服务器转换为 SSE 模式运行。例如，用户可以通过 mcp-proxy 在 Claude Desktop 中使用 stdio 服务器，而无需重新实现为 SSE 模式。

最后提醒一下，MCP 毕竟是一个刚出现了半年的新东西，虽然在社区引起了一些反响，也有很多 IDE 进行了接入，但还远远没有发展到能和 Agent 二分天下的时候。因此我为你讲解这个技术就是为了追新，让你有一个知识储备，以不变应万变。基本就学到这个程度就可以了，无需太深究，否则一旦后面 MCP 没发展起来，现在过度深究就是走弯路了。

## 思考题

你认为 Roo Code 等 IDE 用的是 Stdio 还是 SSE 方式？

欢迎你在留言区展示你的思考结果，我们一起探讨。如果你觉得这节课的内容对你有帮助的话，也欢迎你分享给其他朋友，我们下节课再见！
<div><strong>精选留言（15）</strong></div><ul>
<li><span>111</span> 👍（15） 💬（1）<p>关于思考题，我并没有用过Roo Code，所以去它官网上瞅了一眼，然后就翻到了它官方文档中的这样一章节：https:&#47;&#47;docs.roocode.com&#47;features&#47;mcp&#47;server-transports，总结来说就是：当需要访问的是本地部署的大模型资源时，建议Stdio，当需要使用托管的大模型服务时，建议使用SSE；文章结尾也导向了Roo Code中配置 STDIO 和 SSE 传输的指南链接。

关于agent和MCP按照我目前粗浅的理解下来，看一下两者的架构图就能发现，Agent是通过LLM做规划，然后通过AI应用程序按照规划做相应的工具调用；而MCP则是在AI程序外面加了一个MCP Client，然后让MCP Client调MCP Server，具体的操作发生在MCP Server上。这样做的好处是：具体的能力放到一个个的MCP 【Client - Server】对上面，AI程序成为LLM和MCP之间的协调者，新的能力可以通过MCP这套协议快速集成，而不用AI程序自身再去一个一个对接调用实现，实现了一定程度的解耦。</p>2025-03-31</li><br/><li><span>！null</span> 👍（2） 💬（1）<p>create_starlette_app这个函数没看明白。
应该是客户端调用“&#47;sse” 服务端因为Starlette设置了routes，所以会调用handle_sse？是这个意思吗？handle_sse 异步调用SseServerTransport？SseServerTransport调用&quot;&#47;messages&#47;&quot;?,进而通过Starlette的路由调用sse.handle_post_message吗？handle_post_message这个函数是干什么用的？调用之后是什么作用。
还有这个client是通过命令行调用的吧？如何让大模型调用呢？</p>2025-04-10</li><br/><li><span>笃定</span> 👍（1） 💬（1）<p>目前已经越来越多的应用和服务支持 MCP 协议了，从目前的发展情况来看。MCP 应该不会是昙花一现，发展不起来。所以有个问题想问一下老师。之后在 Agent 开发层面，是否现在这些 Agent 开发框架，例如 Langchain，或者不使用开发框架，手撸 Agent，以后的趋势，对于调用常用的服务，是否都将在 Agent 代码里直接使用 MCP Client 对接大模型，Client 对 MCP Server 发请求调工具就行，不会再自己去写 Tool 了？相当于将 Agent Tools 代码 -&gt; 替换为 MCP Client 代码？</p>2025-05-18</li><br/><li><span>笃定</span> 👍（1） 💬（1）<p>我使用的 MCP Host 插件是 Roo Code (prev. Roo Cline) 。配置好 postgres MCP 后，查看了一下主机进程，发现其进程信息如下：

(base) ➜  ~ ps -ef | grep &#39;npx&#39;
  501 18076 18053   0 Sat09AM ??         0:00.15 node &#47;Users&#47;mac&#47;.npm&#47;_npx&#47;cd1ce99963b5e8b1&#47;node_modules&#47;.bin&#47;mcp-server-postgres postgresql:&#47;&#47;postgres:postgres@127.0.0.1:5432&#47;achievement
  501 85164 85140   0 Fri04PM ??         0:00.09 node &#47;Users&#47;mac&#47;.npm&#47;_npx&#47;cd1ce99963b5e8b1&#47;node_modules&#47;.bin&#47;mcp-server-postgres postgresql:&#47;&#47;postgres:postgres@127.0.0.1:5432&#47;achievement

通过 ps 命令输出的进程号信息，发现它们并无关联，不是父子进程关系呀，我个人认为它目前使用的应该不是 Stdio 方式，应该是 SSE 方式</p>2025-05-18</li><br/><li><span>Geek_c559a0</span> 👍（1） 💬（1）<p>可以在一个StdioServerParameters 里边配置多个server吗 还是每次只能通过一个StdioServerParameters配置单个server。</p>2025-05-09</li><br/><li><span>锋芒</span> 👍（1） 💬（1）<p>请问 PyCharm market中没有Roo Code应该怎么处理呢 ？</p>2025-05-05</li><br/><li><span>轩爷</span> 👍（1） 💬（1）<p>SSE 已经被抛弃，取而代之的是Streamable HTTP</p>2025-04-27</li><br/><li><span>JoeTsai</span> 👍（1） 💬（1）<p>没懂为什么会有MCP和Agent二分天下的看法, MCP 本质上不是为了解决Agent里的tools能力而生的么? 那其实是Agent的一部分吧</p>2025-03-29</li><br/><li><span>林龍</span> 👍（1） 💬（3）<p>sse 中的server的代码是在git中的哪个目录路径下，没有找到</p>2025-03-28</li><br/><li><span>夏落de烦恼</span> 👍（1） 💬（1）<p>盲猜Sdtio😂</p>2025-03-28</li><br/><li><span>maybe</span> 👍（0） 💬（1）<p>Roo Code 等 IDE 用的是 Stdio。</p>2025-05-19</li><br/><li><span>笃定</span> 👍（0） 💬（1）<p>但是，看 postgres mcp 官方的源代码，没有看到有 sse 相关的代码呀？难道还是 Stdio 方式。。。。
https:&#47;&#47;github.com&#47;modelcontextprotocol&#47;servers&#47;blob&#47;main&#47;src&#47;postgres&#47;index.ts
</p>2025-05-18</li><br/><li><span>Lq</span> 👍（0） 💬（1）<p>执行client.py报错循环依赖了，python还在学习中，老师指导一下谢谢。  File &quot;&#47;Library&#47;Frameworks&#47;Python.framework&#47;Versions&#47;3.12&#47;lib&#47;python3.12&#47;asyncio&#47;runners.py&quot;, line 5, in &lt;module&gt;
    from mcp import ClientSession, StdioServerParameters
ImportError: cannot import name &#39;ClientSession&#39; from partially initialized module &#39;mcp&#39; (most likely due to a circular import) (&#47;Library&#47;Frameworks&#47;Python.framework&#47;Versions&#47;3.12&#47;lib&#47;python3.12&#47;site-packages&#47;mcp&#47;__init__.py)
</p>2025-05-14</li><br/><li><span>吴珊珊1</span> 👍（0） 💬（1）<p>windows mcp client stdio方式执行client.py报错

D:\workspace\python\DeepseekInAction\mcp-client-achievement\.venv\Scripts\python.exe D:\workspace\python\DeepseekInAction\mcp-client-achievement\client.py 
Tools: meta=None nextCursor=None tools=[Tool(name=&#39;get_score_by_name&#39;, description=&#39;根据员工的姓名获取该员工的绩效得分&#39;, inputSchema={&#39;properties&#39;: {&#39;name&#39;: {&#39;title&#39;: &#39;Name&#39;, &#39;type&#39;: &#39;string&#39;}}, &#39;required&#39;: [&#39;name&#39;], &#39;title&#39;: &#39;get_score_by_nameArguments&#39;, &#39;type&#39;: &#39;object&#39;})]
score:  meta=None content=[TextContent(type=&#39;text&#39;, text=&#39;name: 张三 绩效评分: 85.9&#39;, annotations=None)] isError=False
[04&#47;30&#47;25 11:31:17] INFO     Processing request of type           server.py:534
                             ListToolsRequest                                  
                    INFO     Processing request of type           server.py:534
                             CallToolRequest                                   
Exception ignored in: &lt;function BaseSubprocessTransport.__del__ at 0x0000023C43264FE0&gt;
Traceback (most recent call last):
  File &quot;D:\software\miniforge3\Lib\asyncio\base_subprocess.py&quot;, line 125, in __del__
    _warn(f&quot;unclosed transport {self!r}&quot;, ResourceWarning, source=self)
                               ^^^^^^^^
  File &quot;D:\software\miniforge3\Lib\asyncio\base_subprocess.py&quot;, line 78, in __repr__
    info.append(f&#39;stdout={stdout.pipe}&#39;)</p>2025-04-30</li><br/><li><span>完美坚持</span> 👍（0） 💬（2）<p>为什么我这边运行了uv run client.py，一点反应都没有
我是在命令行运行的，</p>2025-04-24</li><br/>
</ul>