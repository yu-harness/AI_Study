你好，我是邢云阳。

上节课，我们学习了DeepSeek如何开通与使用，不知道你是不是已经尝试了它的官方对话模式呢？

不过经常使用 AI 的同学可能会发现，即便 DeepSeek 这样大模型里的佼佼者，也不是万能的。有很多内容其实它是回答不了的。特别是一些垂直领域的知识或实时性比较高的知识。比如我们想做一个天气问答助手，直接调用大模型是不行的：

![](https://static001.geekbang.org/resource/image/42/af/4280f7f75c58fa83888ca0a138c56baf.jpg?wh=4971x1142)

这时我们就需要想办法让大模型具备与外界进行交互的能力。比如大模型要是能调用高德天气的 API 获取实时天气，就可以解决问题。基于此，行业龙头 OpenAI 为我们提供了解决方案，那就是 Function Calling 机制。该机制可以让大模型审时度势地调用由人类提供的外部工具，从而解决上述问题。

我在《AI 重塑云原生应用开发实战》课程的[第一讲](https://time.geekbang.org/column/article/833574?utm_campaign=geektime_search&utm_content=geektime_search&utm_medium=geektime_search&utm_source=geektime_search&utm_term=geektime_search)详细讲解过 Function Calling 机制，想了解的同学可以点击链接进行查看，由于那一门课程的编程语言是 Go，因此我也提供了一个 Python 的示例放到了我的 [GitHub](https://github.com/xingyunyang01/Geek02) 上。

Function Calling 对于不熟悉 AI 的同学来说，可能还稍微陌生一些。但 Agent，也就是智能体这个词，大家绝对是耳熟能详的。其实呢，Agent 也是类似 Function Calling 一样，能让大模型和外部进行交互的一种思想，今天这节课，我们就来了解其本质。

## 什么是 Agent？

第一次看到这个词的同学，可能以为是类似 Nginx 的代理，但其实不是。 Agent 简单来说不是一个技术，而是一种 AI 设计模式，一种让大模型变得更聪明的套路。就像我们写传统代码时，会有很多设计模式一样，这些设计模式，就不算是技术，而是纯粹为了让代码写得更高效的套路。

在《雍正王朝》这部史诗级著作中，康熙帝经常会说，“你以为朕处置你，仅仅是因为你处事操切？”。啥叫处事操切？翻译成白话就是，你做事太着急了，为啥不多思考计划一下再行动，并且考虑如何把手下的人用起来呢？

大模型是根据人脑的原理设计的，因此也会犯处事操切的毛病。在 2023 年，曾经有一条封神的提示词，“请一步步的思考”，被无数人拿来炫技。这条提示词的专业名词叫“思维链（CoT）”，算是 Agent 思想的前身，这是因为当时人们还没想好大模型如何与外界实现交互。

后来一篇名叫《ReAct: Synergizing Reasoning and Acting in Language Models》论文的出现，开启了后续 Agent 思想的百家争鸣。

## 什么是 ReAct

ReAct 包含了 Reason 与 Act 两个部分。可以理解为就是**思维链+外部工具调用**。

ReAct 思想会让大模型把大问题拆分成小问题，一步步地解决，每一步都会尝试调用外部工具来解决问题，并且还会根据工具的反馈结果，思考工具调用是否出了问题。如果判断出问题了，大模型会尝试重新调用工具。这样经过一系列的工具调用后，最终完成目标。

那什么是工具调用出问题呢？可以这么理解，比如我问你 1+1 =?，你告诉我 3。我会认为没问题。但如果我问你，你不理我，或者说，你问错人了，那我会尝试重新再问一遍。

ReAct 由于简单好理解，一条提示词就可以搞定，实际用起来效果还不错，因此在项目中很常用。当然除此之外，还有很多更复杂的 Agent 设计模式。我在《AI 重塑云原生应用开发实战》的[第三讲](https://time.geekbang.org/column/article/834219?utm_campaign=geektime_search&utm_content=geektime_search&utm_medium=geektime_search&utm_source=geektime_search&utm_term=geektime_search)挑重点讲过几种常见的，你如果感兴趣可以点击链接查看。

接下来，我们来到手写代码的环节。首先是环境准备。

## 环境准备

- 运行环境：Windows/Linux
- python版本：3.11
- LLM：官方的 deepseek-chat \\ 阿里云百炼平台提供的 deepseek-v3
- SDK：openai 1.63.2

DeepSeek-V3 模型，在官方提供的商业版本（[https://platform.deepseek.com/](https://platform.deepseek.com/)）中叫做 deepseek-chat。但受制于算力不足的约束，官方版本的服务不大稳定，有时会出现无法调用或者崩溃的情况。因此可以在（[阿里云百炼平台](https://www.aliyun.com/product/bailian?spm=5176.29956983.nav-v2-dropdown-menu-1.460.11051b9eQWJDch)）也开一个账户，使用阿里云私有化部署的 DeepSeek-V3。

怎么开通充值，我就不演示了，如果有不会的同学可以在留言区留言，我单独讲解。

## ReAct Prompt 模板

要为大模型赋予 ReAct 能力，使其变成 Agent，我们需要在向大模型提问时，使用 ReAct Prompt，从而让大模型在思考如何解决提问时，能使用 ReAct 思想。

这里给你推荐一个特别好用的网站 [LangChain Hub](https://smith.langchain.com/hub)。

![](https://static001.geekbang.org/resource/image/5f/56/5f9518eb90962bc58664262fb5c5b256.jpg?wh=4000x1864)

LangChain 大家一定不陌生，是目前社区最火的 AI 应用开发脚手架。而 LangChain Hub 则是 LangChain 搭建的一个 prompt 仓库。仓库中包含了丰富的 prompt，且具备分类。用户可以非常方便地查找想要的 prompt。

例如，我们在搜索框输入 react，可以看到有多条 ReAct Prompt。也可以在右侧点击分类进行过滤。

![](https://static001.geekbang.org/resource/image/5f/52/5f18a479476066cbf188cc677ffe0552.jpg?wh=4000x1971)

在这里我推荐一个 LangChain 官方的 ReAct Prompt，链接是 [LangSmith (langchain.com)](https://smith.langchain.com/hub/langchain-ai/react-agent-template)，我们贴出来分析一下其原理。

````plain
{instructions}

TOOLS:
------

You have access to the following tools:

{tools}

To use a tool, please use the following format:

```
Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
```

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

```
Thought: Do I need to use a tool? No
Final Answer: [your response here]
```

Begin!

Previous conversation history:
{chat_history}

New input: {input}
{agent_scratchpad}
````

这段 prompt 开头的 {instructions} 其实是为大模型设置人设。之后告诉大模型，使用 {tools} 中定义的工具。因此在 {tools} 里，应该填入工具的描述。工具的描述我们会在下文中，为大家介绍如何编写。

模板接下来要求大模型按照规定的格式思考和回答问题，这就是在教大模型如何推理和规划，大模型在有了推理和规划能力后就变成了 Agent。

![](https://static001.geekbang.org/resource/image/70/f1/703e31e0b345edd32cd226772yya94f1.jpg?wh=2093x1120)

因为 Agent 会将问题拆分成多个子问题，之后一个个的解决，因此从 Thought 到 Observation 的过程会执行 N 次，直到大模型认为得到了最终的答案。

于是便有了第二个 Thought：大模型认为得到了最终的答案。Final Answer就表示最终的答案。

该模板还支持在 {chat\_history} 中填入历史对话，方便大模型理解上下文。最后还有一个 {agent\_scratchpad}，这是一个 Agent 剪贴板，用于记录 Agent 的思考过程，可以不填，不影响整个 Agent 执行过程。

到此，整个 ReAct Prompt 模板就分析完了。我们初步可以看出，ReAct 的执行过程是一个与人类交互的过程。在 Action 和 Action Input 中，大模型会告诉人类需要执行什么工具、以及工具的入参是什么，而具体的工具执行，需要由人类完成。

人类完成后，将工具执行结果填入到Observation，反馈给大模型，直到大模型得到 Final Answer。

整个过程中，人类需要从Action、Action Input 以及 Final Answer 中使用正则或字符串的方式取值。因此该模板是一个 StringPromptTemplate 类型的 prompt 模板。除此之外，ReAct 模板还有 JSON 类型的，我会在今后的课程再展开讲解。

## Agent 核心代码

接下来我们就用一个查询股票收盘价的案例，使用 Agent 的方式实现一遍。

### ReAct 模板

模板就使用上文中讲述的 ReAct prompt 模板。但是我略微做了修改。我将 Observation 那句拿了出来，并改成了：

```plain
Then wait for Human will response to you the result of action by use Observation.
```

之后还加了一句内容。

```plain
... (this Thought/Action/Action Input/Observation can repeat N times)
```

这是因为我们是通过提示词来赋能大模型 Agent 能力的，因此提示词的质量会影响大模型的输出，有时大模型会过于自作聪明，将本该由人类回复的 Observation 替人类杜撰一个答案后回复。因此我做了修改。

当然上文提到的 Langchain Hub 上还有很多优秀的提示词，大家也可以测试。我之前从 Dify 的源码中扒到过它的提示词，实测效果不错。

### 工具定义

工具定义分为工具描述（prompt）定义与实际工具调用函数的定义两个部分。

前面我们学习了工具是 prompt 的一部分，Agent 能否准确地命中工具，很大程度上取决于我们对于工具的描述写得好不好。

工具描述的定义方法，按照 Function Calling 的定义，分成工具名称、工具描述以及工具参数描述三个部分。以下是股票工具描述的参考代码：

```python
tools = [
    {
        "name": "get_closing_price",
        "description": "使用该工具获取指定股票的收盘价",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "股票名称",
                }
            },
            "required": ["name"]
        },
    },
]
```

描述是提供给大模型做阅读理解的。但真正执行工具的是人类。因此我们还需要定义真正的工具执行函数。

```python
def get_closing_price(name):
    if name == "青岛啤酒":
        return "67.92"
    elif name == "贵州茅台":
        return "1488.21"
    else:
        return "未搜到该股票"
```

### 注入模板

当用户开始提问时，代码需要将 instructions 、tools、tool\_names、input 都注入进模板，将模板替换用户原始的 prompt，发送给大模型。

参考代码如下：

```python
instructions = "你是一个股票助手，可以回答股票相关的问题"

query = "青岛啤酒和贵州茅台的收盘价哪个贵？"

prompt = REACT_PROMPT.format(instructions=instructions,tools=tools,tool_names="get_closing_price",input=query)

messages = [{"role": "user", "content": prompt}]
```

### Agent 多轮对话核心逻辑

前文讲过，Agent 处理问题会将大问题拆分成一个个的小问题，分别选择相应的工具去解决问题。因此作为实际工具调用者的我们，就需要配合大模型完成多轮工具的调用，直到大模型反馈 Final Answer，因此这是一个多轮对话的模式。

我们可以用死循环来实现多轮对话，死循环的结束条件是检测到大模型输出 Final Answer。参考代码如下：

```python
while True:
    response = send_messages(messages)
    response_text = response.choices[0].message.content

    print("大模型的回复：")
    print(response_text)

    final_answer_match = re.search(r'Final Answer:\s*(.*)', response_text)
    if final_answer_match:
        final_answer = final_answer_match.group(1)
        print("最终答案:", final_answer)
        break

    messages.append(response.choices[0].message)

    action_match = re.search(r'Action:\s*(\w+)', response_text)
    action_input_match = re.search(r'Action Input:\s*({.*?}|".*?")', response_text, re.DOTALL)

    if action_match and action_input_match:
        tool_name = action_match.group(1)
        params = json.loads(action_input_match.group(1))

        if tool_name == "get_closing_price":
            observation = get_closing_price(params['name'])
            print("人类的回复：Observation:", observation)
            messages.append({"role": "user", "content": f"Observation: {observation}"})
```

当大模型选择了工具时，会返回 Action 以及 Action Input，返回的示例如下：

```plain
Action: get_closing_price
Action Input: {"name": "青岛啤酒"}
```

反之，当大模型认为得到最终答案时，会返回 Final Answer，示例如下：

```plain
Thought: Do I need to use a tool? No
Final Answer: 贵州茅台的收盘价为1488.21元，青岛啤酒的收盘价为67.92元，因此贵州茅台的收盘价比青岛啤酒
贵。
```

因此在代码中，我使用了正则表达式的方式，从这三个字段后面，将内容截取出来。

之后调用相应的函数完成股票收盘价的获取。

计算完成后，将答案添加到Observation 后，再将历史对话+Observation 发送给大模型。

由于我是问了两只股票的价格，因此大模型会调用两次工具。全部的大模型和人类交互的对话如下，大家可以结合对话再理解一下。

````python
大模型的回复：
```
Thought: Do I need to use a tool? Yes
Action: get_closing_price
Action Input: {"name": "青岛啤酒"}
```

人类的回复：Observation: 67.92

大模型的回复：
```
Thought: Do I need to use a tool? Yes
Action: get_closing_price
Action Input: {"name": "贵州茅台"}
```

人类的回复：Observation: 1488.21

大模型的回复：
```
Thought: Do I need to use a tool? No
Final Answer: 贵州茅台的收盘价为1488.21元，青岛啤酒的收盘价为67.92元，因此贵州茅台的收盘价比青岛啤酒
贵。
```

最终答案: 贵州茅台的收盘价为1488.21元，青岛啤酒的收盘价为67.92元，因此贵州茅台的收盘价比青岛啤酒贵。
````

## 总结

在这节课中，我们深入探讨了如何使用 ReAct 推理方案构建 Agent，并通过 Python 语言代码 0 框架手写了一个简单的 Agent，展示了其工作原理。从 ReAct Prompt 模板的设计原理以及使用，到工具的定义，再到 Agent 多轮对话的实现，我们一步步揭开了 ReAct 模型驱动下的智能推理过程。

我一直认为做 AI 应用开发，写好了 prompt，就至少成功了一半。我们通过对 ReAct Prompt 模板的学习，以及对于大模型与人类之间交互的对话的直观体验，相信可以让你更加深刻地理解 ReAct 的原理。

除此之外，我们还介绍了 LangChain Hub的使用，通过 LangChain Hub，我们可以发掘出大量优秀的 Prompt 模板，让我们的 AI 应用开发之路走得更加轻松。

在了解了 ReAct 思路之后，我们还掌握了如何编写 Agent。这节课的代码已公开在了 GitHub上，地址为：[https://github.com/xingyunyang01/Geek02](https://github.com/xingyunyang01/Geek02)。希望你自己尝试一下复现这节课的代码效果，并自由地扩展工具，进一步加深对ReAct Agent 实现逻辑的理解。

理解了 Agent 的本质，会为我们后续做实战项目打下坚实的基础，让我们继续加油吧。

## 思考题

你认为 Agent 是对 Function Calling 的平替还是升级版？为什么？

欢迎你在留言区展示你的思考，我们一起来讨论。如果你觉得这节课的内容对你有帮助的话，也欢迎你分享给其他朋友，我们下节课再见！
<div><strong>精选留言（15）</strong></div><ul>
<li><span>最后的风之子</span> 👍（13） 💬（3）<p>作者官方补充说明：由于r1自带思维链，与Agent产生了冲突，所以Agent不能使用r1等慢速思考模型，而是要使用v3等老老实实执行命令，没有自己想法的模型；r1适合做的是单项的任务。比如用r1做一个生成财报的工具，然后让v3做Agent去调用该工具</p>2025-03-03</li><br/><li><span>xzy</span> 👍（17） 💬（1）<p>不太理解老师说的Agent是一种设计模式，我理解的Agent是这样子的：

大模型中的Agent概念指的是一种基于大模型（如大语言模型）的自动化实体，它具备感知、决策、行动和学习的能力。Agent可以被视为大模型的上层应用，负责将大模型的智能转化为具体的行动和结果。

Agent的核心特征
感知环境：Agent通过传感器或其他方式感知周围的环境，这个环境可以是虚拟的，也可以是物理的13。

自主决策：Agent能够根据感知到的信息自主做出决定15。

执行行动：Agent通过执行器或效应器采取行动以实现目标13。

学习和优化：Agent可以通过学习和获取知识来提高其性能，并根据结果进行自我优化16。

Agent的组成和功能
Agent通常由以下组成部分构成：

LLM（大模型）：作为Agent的核心大脑，提供智能和决策能力24。

记忆：帮助Agent记住过去的经验和知识，分为短期记忆和长期记忆24。

规划：Agent根据目标和环境进行任务分解和路径规划24。

工具使用：Agent利用各种工具来执行任务，例如API、搜索引擎等24。

Agent的应用
Agent在多个领域发挥着重要作用，例如：

RPA（机器人流程自动化）：Agent可以理解人类意图并操作软件以实现自动化1。

任务规划：Agent能够根据提示词和知识库进行决策和规划4。

总之，Agent是大模型的重要应用形式，它通过感知、决策、行动和学习来实现智能化和自动化。</p>2025-03-03</li><br/><li><span>Toni</span> 👍（13） 💬（1）<p>大语言模型(LLM)自从大力出奇迹后就不断带给人们惊喜。大算力，大数据，大参量使得LLM的表现越来越惊艳，借助 Embedding 的力量使得像情感判断之类的事件都可以在零训练基础上轻松实现。问LLM 个问题，它就会滔滔不绝地回答个没完没了，有的没的顺着之前预训练时的喜好(QKV)一顿输出，屡屡出现从人类的角度看是幻觉的现象而不查，原因是知道的太多了，不吐不快。

为了提高 LLM 回答的准确性，人类技高一筹，用微调给大模型上手段，用各种提示词Prompt给大模型设人设，用外挂特定数据库给LLM立规矩，十八般武艺全用上就是为了LLM 为我所用，依靠LLM 强大的语言理解能力，人类为不同的问题设计了不同的工具(Tools)以扩展LLM的能力如实时访问互联网，调用数学计算的专用工具。

沿着Prompt这条路，提示词越写越成熟，应对各种问题的模块都可以信手拈来，还发展出引导大模型工作流的思维链，将Prompt的各个流程串联起来演变出各式各样的智能体Agent，目的只有一个让Prompt 简单化易写易用，降低大模型的使用门槛。

在这样的需求背景下，DeepSeek-r1横空出世，在其优质大模型DeepSeek-v3基础上训练模型让它自己学习如何有效构建思维链，完成了卓越的思维链预训练，实现了大模型思维链的零启动。

期待本课程中有关DeepSeek 应用开发示例，体会新模型的优异便捷。

个人的一点想法分享。</p>2025-03-06</li><br/><li><span>张申傲</span> 👍（8） 💬（2）<p>Agent是Function Calling的升级版。

Agent的本质是一个由LLM驱动的智能系统，内部包含了多个子模块，包括Planning、Memory、Tools和Execution等等，而Function Calling只是Agent诸多能力中的一项。

此外，按照OpenAI对于Function Calling或Tool Calling的原始定义，它的作用仅仅是按照规范化的格式生成函数调用参数，而实际的调用还是需要我们自己的应用来执行，相较之下，Agent则是把整个流程都给封装好了。</p>2025-03-04</li><br/><li><span>软件产品经理韩安美</span> 👍（4） 💬（1）<p>不懂代码的产品经理怎么能结合模型做应用呢？老师课程也顾及一下吧</p>2025-03-07</li><br/><li><span>zhihai.tu</span> 👍（3） 💬（1）<p>应该是升级吧，Function calling 只是 Agents的一项能力，要实现 Agents，还需要大模型+规划+上下文等等。</p>2025-03-04</li><br/><li><span>黄国华</span> 👍（2） 💬（1）<p>老师，最近manus很火，您觉得它是如何处理prompt，也就是怎么将用户意图转换为准确的prompt的</p>2025-03-07</li><br/><li><span>完美坚持</span> 👍（2） 💬（3）<p>“不管是FC还是Agent，大模型都只能选择工具，真正执行工具的永远是人类写的程序。Agent与FC相比，主要是在于如何让大模型思考的过程是我们自己可控的，而不是像FC一样，完全让大模型自己判断”

这个让大模型思考的过程是我们自己可控的，这里我们使用提示词实现的吗？</p>2025-03-05</li><br/><li><span>神宫寺的鲸</span> 👍（2） 💬（4）<p>妈呀没懂，这些代码是放在python运行还是直接丢给deep seek
</p>2025-03-03</li><br/><li><span>Grack</span> 👍（2） 💬（3）<p>老师，您讲的Agent“是一种AI设计模式，一种让大模型变得更聪明的套路”，这里我有些疑惑，我之前学习其他资料，OpenAI对Agent的定义是具有Memory,Planning,Tools和Action能力的&quot;智能系统&quot;。我理解Agent是一个小到deepseek chat对话框的prompt引导的结果，大到未来课程的一个作业帮，可以当作一个Agent，大概可以理解为传统的自动化应用+大模型的大脑后的一个系统。如果说Agent是一个设计模式，那么这个设计模式应该包含什么、怎么解释呢？ 请老师答疑解惑，谢谢！</p>2025-03-03</li><br/><li><span>jogholy</span> 👍（1） 💬（1）<p>反复看了function calling和react，感觉还是一回事。为什么呢？不都是告诉大模型有什么工具可以用，然后大模型根据问题选择工具，然后调用工具再回复给大模型最后拿到答案吗？</p>2025-04-18</li><br/><li><span>Geek_36aa63</span> 👍（1） 💬（1）<p>请教老师一个问题，如果tool的参数不止一个，需要多个参数。怎么通过多轮对话引导用户补全参数呢？应该怎么写prompt</p>2025-04-15</li><br/><li><span>西钾钾</span> 👍（1） 💬（1）<p>老师，有没有一个分析阅读开源代码比较好的模型？或者是否可以通过其他的方式通过 AI 手段来理解分析开源代码呢？</p>2025-03-07</li><br/><li><span>Apple_968715</span> 👍（1） 💬（1）<p>更新太慢，半夜放毒</p>2025-03-04</li><br/><li><span>燕伟晴</span> 👍（0） 💬（1）<p>“到此，整个 ReAct Prompt 模板就分析完了。我们初步可以看出，ReAct 的执行过程是一个与人类交互的过程。在 Action 和 Action Input 中，大模型会告诉人类需要执行什么工具、以及工具的入参是什么，而具体的工具执行，需要由人类完成。”

老师这段用的词为人类，prompt里用的词也是Human，为什么选择人类这个词，而不是程序、函数之类的呢</p>2025-05-14</li><br/>
</ul>