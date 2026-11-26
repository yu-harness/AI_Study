你好，我是郑晔！

上一讲，我们抛开了 LangChain，基于 OpenAI Python 程序库实现了一个 Agent，主要是为了让你更好地理解 Agent 的运作机理。其中最核心的部分就是一个循环，不断地执行各种动作，直到判断运行的结果是停下来。

现在，你已经知道了 Agent 是怎样运作的，这一讲，我们再回来看看如何用 LangChain 实现一个 Agent，相信有了之前的铺垫，这一讲的代码就比较容易理解了。

## 基于LangChain实现的Agent

从实现的功能上讲，我们这一讲要实现的功能和上一讲是完全相同的，只不过我们采用了 LangChain 的基础设施，代码如下所示：

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

@tool
def calculate(what: str) -> float:
    """Runs a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary"""
    return eval(what)

@tool
def ask_fruit_unit_price(fruit: str) -> str:
    """Asks the user for the price of a fruit"""
    if fruit.casefold() == "apple":
        return "Apple unit price is 10/kg"
    elif fruit.casefold() == "banana":
        return "Banana unit price is 6/kg"
    else:
        return "{} unit price is 20/kg".format(fruit)


prompt = PromptTemplate.from_template('''Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}''')

tools = [calculate, ask_fruit_unit_price]
model = ChatOpenAI(model="gpt-4o-mini")
agent = create_react_agent(model, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
result = agent_executor.invoke({
    "input": "What is the total price of 3 kg of apple and 2 kg of banana?"
})
print(result)
```

## 工具

这一讲的代码与上一讲实现了完全相同的功能，主要是我们把上一讲的两个动作函数几乎原封不动地搬了过来。

```python
@tool
def calculate(what: str) -> float:
    """Runs a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary"""
    return eval(what)

@tool
def ask_fruit_unit_price(fruit: str) -> str:
    """Asks the user for the price of a fruit"""
    if fruit.casefold() == "apple":
        return "Apple unit price is 10/kg"
    elif fruit.casefold() == "banana":
        return "Banana unit price is 6/kg"
    else:
        return "{} unit price is 20/kg".format(fruit)
```

之所以要说几乎，是我们给这两个函数添加了一点东西。首先，`@tool` 是一个装饰器，它让我们把一个函数变成了一个工具（tool）。

工具在 LangChain 里是一个重要的概念，它和我们说的 Agent 系统架构中的工具概念是可以对应上的，工具主要负责执行查询，或是完成一个一个的动作。

Agent 在执行过程中，会获取工具的信息，传给大模型。这些信息主要就是一个工具的名称、描述和参数，这样大模型就知道该在什么情况下怎样调用这个工具了。`@tool` 可以提取函数名变成工具名，提取参数变成工具的参数，还有一点就是，它可以提取函数的 Docstring 作为工具的描述。这样一来，calculate 就从一个普通的函数变成了一个工具。

```python
@tool
def calculate(what: str) -> float:
    """Runs a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary"""
    return eval(what)

print(calculate.name)
print(calculate.description)
print(calculate.args)
```

## 提示词

接下来就是提示词，这里我们没有把上一讲的提示词直接搬过来，而是采用了一个[更通用的提示词](https://smith.langchain.com/hub/hwchase17/react)：

```python
prompt = PromptTemplate.from_template('''Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought:{agent_scratchpad}''')
```

如果你还记得，我们在学习[提示工程](https://time.geekbang.org/column/article/822235)的那一讲的时候，已经见过这个提示词模板了，再结合上一讲介绍过的提示词，对于这里的思考（Thought）、行动（Action）和观察（Observation），你肯定不陌生了。

作为一个模板，这里面有几个空是留给我们的，最主要的就是 `tools` 和 `tool_names` 两个变量，这就是工具的信息。`tool_names` 很简单，就是工具的名称。

`tools` 是工具格式化成一个字符串。比如，在缺省的实现中， `calculate` 就会格式化成下面这个样子，可以看到它包括了工具的基本属性都拼装了进去。

```plain
calculate(what: str) -> float - Runs a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary
```

`input` 也比较好理解，就是我们的输入。 `agent_scratchpad` 是在 Agent 的执行过程中，存放中间过程的，你可以把它理解成我们上一讲的聊天历史部分。

## 组装 Agent

有了工具，有了提示词，现在我们可以组装 Agent 了：

```python
tools = [calculate, ask_fruit_unit_price]
model = ChatOpenAI(model="gpt-4o-mini")
agent = create_react_agent(model, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
```

我们调用 `create_react_agent` 创建了一个基于 ReAct 的 Agent。前面说过，ReAct 的Agent 能够正常运行，需要提示词与代码配合起来使用。我前面给出的提示词就是要与 `create_react_agent` 函数配合在一起使用的。

`create_react_agent` 完成的工作就是基于这段提示词的执行过程进行处理，比如，解析返回内容中的动作（Action）与动作输入（Action Input），还有前面说的 `agent_scratchpad` 的处理过程，也是在这个函数中组装进去的。

站在软件设计的角度看，二者结合如此紧密，却被分开了，等于破坏了封装。实际上，二者之前确实是合在一起的，就是一个 `create_react_agent` 函数。现在将二者分开，是为了给使用者一个调整提示词的机会。

与之前几个基于 LangChain 的应用最大的不同在于，我们这个 Agent 的实现并没有组装成一个链。正如我们前面所说，Agent 的核心是一个循环，这其实是一个流程，而之前的应用从头到尾都是一个“链”式过程。所以，这里用到了 AgentExecutor。

即便不看它的实现，你应该也能知道，其核心实现就是一个循环：判断是不是该结束，不是的话，继续下一步，向大模型发送消息，是的话，跳出循环。

现在，我们已经组装好了所有的代码，接下来就是执行这个 Agent 了：

```python
result = agent_executor.invoke({
    "input": "What is the total price of 3 kg of apple and 2 kg of banana?"
})
print(result)
```

一次的执行结果输出如下：

```plain
> Entering new AgentExecutor chain...

To find the total price of 3 kg of apples and 2 kg of bananas, I need to know the unit prices of both fruits. I will first ask for the price of apples and then for the price of bananas.

Action: ask_fruit_unit_price  
Action Input: "apple"  
Apple unit price is 10/kg

Now that I have the unit price of apples, I need to ask for the unit price of bananas.

Action: ask_fruit_unit_price  
Action Input: "banana"  
Banana unit price is 6/kg

Now that I have the unit prices of both fruits (10/kg for apples and 6/kg for bananas), I can calculate the total price for 3 kg of apples and 2 kg of bananas.

Action: calculate  
Action Input: "3 * 10 + 2 * 6"  42

I now know the final answer
Final Answer: The total price of 3 kg of apples and 2 kg of bananas is 42.

> Finished chain.
{'input': 'What is the total price of 3 kg of apple and 2 kg of banana?', 'output': 'The total price of 3 kg of apples and 2 kg of bananas is 42.'}
```

因为在 AgentExecutor 初始化的时候，我打开了 `verbose` 这个开关，所以，这里我们看到 Agent 内部的执行过程。我们可以看到，其过程几乎与我们上一讲的过程是一样的，先查看苹果和香蕉的单价，然后，计算总和。最终，把计算结果返回给我们。

## 工具（Tool）和工具包（Toolkit）

在前面的实现中，为了兼容上一讲的内容，我们自定义了自己的工具实现。实际上， LangChain 社区已经为我们提供了[大量的工具](https://python.langchain.com/docs/integrations/tools/)，让我们可以很方便地集成各种东西。在很多情况下，这些工具我们只要直接拿过来用就好，下面是一个例子：

```python
shell_tool = ShellTool()

tools = [shell_tool]
model = ChatOpenAI(model="gpt-4o-mini")
agent = create_react_agent(model, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
result = agent_executor.invoke({
    "input": "Create a file named 'test.txt' and write 'Hello, World!' to it."
})
```

在这个例子里，我们创建了一个可以执行自然语言命令的命令行工具。为了支持命令行的执行，我们引入了 ShellTool，它是一个命令行工具。所有的工具实际上都是 Tool 这个接口的实现，ShellTool 也是实现这个接口。前面的动作函数就是通过 `@tool` 这个装饰器生成了一个实现 Tool 接口的对象。

对程序员来说，命令行的行为大家都不陌生，下面就是这个 Agent 的一次执行结果，我让它创建了一个名为 test.txt 的文件，然后，在其中写入“Hello, World!”。

```plain
I need to create a file named 'test.txt' and then write the text 'Hello, World!' into it. I'll do this using shell commands in the terminal. 

Action: terminal  
Action Input: echo 'Hello, World!' > test.txt  

Executing command:
 echo 'Hello, World!' > test.txt

The file 'test.txt' has been created with the content 'Hello, World!'. 

Final Answer: A file named 'test.txt' has been created with the content 'Hello, World!'.
```

除了工具，LangChain 还有一个 Toolkit 的概念，它的作用是把相关的一些工具集成在一起。举个例子，Github 提供了一大堆的能力，比如查询 Issue、创建 Pull Request 等等。如果一个一个列出来就会很多，所以，就有了一个 Github Toolkit 把它们放在了一起。下面是一个示例：

```plain
github = GitHubAPIWrapper()
toolkit = GitHubToolkit.from_github_api_wrapper(github)

tools = toolkit.get_tools()
agent = create_react_agent(model, tools, prompt)
...
```

当然，为了这段代码能够执行，你需要找到相关的配置：

```bash
export GITHUB_APP_ID="your-app-id"
export GITHUB_APP_PRIVATE_KEY="path-to-private-key"
export GITHUB_REPOSITORY="your-github-repository"
```

正是有了工具和工具包的概念，Agent 能做的事情就会无限放大。如果我们做的是比较通用的事情，很多时候，就是在已有的工具和工具包中进行选择。不过，我之所以把如何编写一个工具放在前头，是因为大多数情况下，我们需要编写自己的工具，无论是访问私有的数据，还是内部的接口。所以，学习编写工具几乎是一件必须要学会的事。不过，这种代码就进入到我们熟悉的范围了，对大部分程序员而言，应该不是太大的问题。

现在你已经了解了采用 LangChain 构建 Agent 的基本方法。虽然我们这里只介绍了基于 ReAct 构建的 Agent，但实际上，LangChain 里提供了大量的各种创建 Agent 的方法，比如创建基于 SQL 的 Agent、基于 JSON 的 Agent 等等，我们可以根据需要进行选择。

## 总结时刻

这一讲，我们使用 LangChain 重新构建了上一讲的 Agent。有了上一讲的基础，这一讲的代码理解起来应该非常容易。

与构建其它类型应用不同的地方是，构建 Agent 不是构建一条“链”，所以，需要用一个 AgentExecutor 去执行 Agent，其本质是一个循环，一直执行到大模型认为已经找到了答案。

与 Agent 配合的概念中，工具（Tool）和工具包（Toolkit）是非常重要的。开发一个 Agent，很多时候就是在开发工具和集成工具：

- 工具负责与模型交互，其输入由模型产生，输出会回传给模型。
- 工具包是一组相关的工具。

如果今天的内容你只能记住一件事，那请记住，**编写基于 LangChain 的 Agent，关键点是学会工具。**

## 练习题

LangChain 社区提供了大量的工具，你可以找一个自己感兴趣的，用它来改造这一讲的代码，实现一个新的 Agent。欢迎在留言区分享你的改造心得。

欢迎你在留言区和我交流互动，如果这一讲对你有帮助，别忘了分享给身边更多朋友。
<div><strong>精选留言（3）</strong></div><ul>
<li><span>风</span> 👍（0） 💬（1）<p>AI是自动识别需要调用哪个tool以及需要传入什么作为参数？</p>2025-02-18</li><br/><li><span>grok</span> 👍（6） 💬（1）<p>我用的grok2，本节代码跑不通。需要清理输入。改动如下：
```
def clean_tool_input(func):
    &quot;&quot;&quot;装饰器：清理传递给工具函数的输入&quot;&quot;&quot;
    @wraps(func)  # 这会保留原始函数的元数据，包括 docstring
    def wrapper(input_str: str, *args, **kwargs):
        # 清理输入，只取第一行并去除空白字符
        cleaned_input = input_str.split(&#39;\n&#39;)[0].strip()
        return func(cleaned_input, *args, **kwargs)
    return wrapper

@tool
@clean_tool_input
def calculate(what: str) -&gt; float:
    &quot;&quot;&quot;Runs a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary&quot;&quot;&quot;
    return eval(what)

@tool
@clean_tool_input
def ask_fruit_unit_price(fruit: str) -&gt; str:
    &quot;&quot;&quot;Asks the user for the price of a fruit&quot;&quot;&quot;
    if fruit.casefold() == &quot;apple&quot;:
        return &quot;Apple unit price is 10&#47;kg&quot;
    elif fruit.casefold() == &quot;banana&quot;:
        return &quot;Banana unit price is 6&#47;kg&quot;
    else:
        return &quot;{} unit price is 20&#47;kg&quot;.format(fruit)
```

完整代码在此：https:&#47;&#47;github.com&#47;groklab&#47;misc&#47;blob&#47;main&#47;geektime-llm-zhengye-column&#47;lec14.ipynb</p>2024-12-02</li><br/><li><span>张申傲</span> 👍（4） 💬（0）<p>第14讲打卡~
LangChain 内置了大量开箱即用的工具，可以参考：https:&#47;&#47;python.langchain.com&#47;docs&#47;integrations&#47;tools&#47;</p>2025-01-24</li><br/>
</ul>