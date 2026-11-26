你好，我是郑晔！

上一讲，我们已经从概念上了解了 Agent。你现在知道 Agent 其实也是一个软件系统，只不过，因为有了大模型的加持，它有了一个可以做“自主”推理的大脑，完成很多“智能”的工作。

这一讲，我们来实现一个 Agent。不同于之前借助 LangChain，这次我们会用更底层的方式实现一个 Agent，帮助你更好地理解 Agent 的运作原理。

我们构建这个 Agent 会基于 ReAct 来实现，我们在 [04 讲](https://time.geekbang.org/column/article/822235)介绍过，ReAct 表示 Reasoning + Acting，也就是推理和行动。采用这个模式，要经历思考（Thought）、行动（Action）、观察（Observation）三个阶段。

大模型会先思考要做什么，决定采用怎样的行动，然后在环境中执行这个行动，返回一个观察结果。有了这个观察结果，大模型就会重复思考的过程，再次考虑要做什么，采用怎样的行动，这个过程会持续到大模型决定这个过程结束为止。

我们的实现代码参考了 Simon Willison 的一篇[文章](https://til.simonwillison.net/llms/python-react-pattern)，这篇文章介绍了如何用 Python 实现 ReAct 模式。

## 基础的聊天机器人

我们先来实现一个基础的聊天机器人：

```python
from openai import OpenAI

DEFAULT_MODEL = "gpt-4o-mini"
client = OpenAI()

class Agent:
    def __init__(self, system=""):
        self.system = system
        self.messages = []
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def invoke(self, message):
        self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result

    def execute(self):
        completion = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=self.messages,
            temperature=0
        )
        return completion.choices[0].message.content
```

我们采用了直接的 OpenAI Python 库实现：

- 初始化的时候，我们可以传入系统提示词给这个 Agent 做一些初始的设定。 `messages` 是我们维护的历史消息列表，如果设定了系统提示词，就把它加到历史消息里。
- `invoke` 是主要的对外接口。调用之前，我们把消息存放到历史消息里，等到调用大模型之后，再把应答存放到历史消息里。
- `execute` 处理了请求大模型的过程，模型和消息都比较好理解。`temperature` 的值是 0，因为这里用到的是大模型的推理过程，所以，我们希望确定性强一些。另外，这里我们使用了同步处理，因为我们这里是把大模型当作推理引擎，需要等待所有的内容回来。

有了前面的基础，这段代码应该比较容易理解，但我们也能看到这段代码存在的问题，比如历史消息会无限膨胀。所以，它只是一段示例代码，不能用在生产里。

## ReAct 提示词

要创建一个基于 ReAct 的 Agent，关键是要有一个特定的提示词。下面是我们这个例子里的提示词：

```python
prompt = """
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.

Your available actions are:

calculate:
e.g. calculate: 4 * 7 / 3
Runs a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary

ask_fruit_unit_price:
e.g. ask_fruit_unit_price: apple
Asks the user for the price of a fruit

Example session:

Question: What is the unit price of apple?
Thought: I need to ask the user for the price of an apple to provide the unit price. 
Action: ask_fruit_unit_price: apple
PAUSE

You will be called again with this:

Observation: Apple unit price is 10/kg

You then output:

Answer: The unit price of apple is 10 per kg.
""".strip()
```

这段提示词分成了三个部分，ReAct 描述、可用的动作和示例。

ReAct 描述，给大模型解释了ReAct 的三个阶段：思考（Thought）、行动（Action）、观察（Observation）。这里还多了一个暂停（Pause），其主要的目的就是停下来，这时执行流程就回到我们这里，执行相应的动作。当动作执行完毕，再把控制权返回给大模型。

```plain
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you - then return PAUSE.
Observation will be the result of running those actions.
```

可用的动作，告诉大模型在思考的时候可以结合哪些动作来完成工作。为了简化，我们这里只设计了两个动作，一个是计算，根据一个算式得到一个结果；另一个是询问水果价格。这样，大模型思考的结果就可以是让我们执行一个具体的动作。

```plain
Your available actions are:

calculate:
e.g. calculate: 4 * 7 / 3
Runs a calculation and returns the number - uses Python so be sure to use floating point syntax if necessary

ask_fruit_unit_price:
e.g. ask_fruit_unit_price: apple
Asks the user for the price of a fruit
```

最后是一个示例，展现了一个完整的思考过程。从问题开始，大模型给出了怎样的思考，做出了哪些动作，然后将观察结果返回给大模型，最终大模型给出了输出。这里给出的示例，是为了供大模型更好地参考，还记得我们在提示工程中讲过的少样本提示吗？这个提示词就是 ReAct 和少样本提示的结合。

```plain
Example session:

Question: What is the unit price of apple?
Thought: I need to ask the user for the price of an apple to provide the unit price. 
Action: ask_fruit_unit_price: apple
PAUSE

You will be called again with this:

Observation: Apple unit price is 10/kg

You then output:

Answer: The unit price of apple is 10 per kg.
```

## 动作

在提示词里，我们给出了可用的动作，这是我们要实现的代码。大模型会告诉我们要做什么动作，但具体怎样做是我们的事情。下面是两个动作的实现：

```python
def calculate(what):
    return eval(what)


def ask_fruit_unit_price(fruit):
    if fruit.casefold() == "apple":
        return "Apple unit price is 10/kg"
    elif fruit.casefold() == "banana":
        return "Banana unit price is 6/kg"
    else:
        return "{} unit price is 20/kg".format(fruit)
```

`calculate` 采用了 Python 本身的 eval 机制实现，而 `ask_fruit_unit_price` 则实现了不同水果价格。如你所见，这两个函数都很简单，但它们怎样实现并不重要，重点是我们有了一个接口去实现自己的机制，我们可以调用一些外部 API 去查询也好，去执行一个操作也罢，这样，Agent 就能跳出大模型本身的限制了。所以，**动作代码是我们发挥想象力的重要一环。**

## 组合起来

我们要实现 Agent 的基础组件都有了，接下来，我们就把它们组合到一起。

```python
action_re = re.compile(r'^Action: (\w+): (.*)$')

known_actions = {
    "calculate": calculate,
    "ask_fruit_unit_price": ask_fruit_unit_price
}

def query(question, max_turns=5):
    i = 0
    agent = Agent(prompt)
    next_prompt = question
    while i < max_turns:
        i += 1
        result = agent.invoke(next_prompt)
        print(result)
        actions = [action_re.match(a) for a in result.split('\n') if action_re.match(a)]
        if actions:
            # There is an action to run
            action, action_input = actions[0].groups()
            if action not in known_actions:
                raise Exception("Unknown action: {}: {}".format(action, action_input))
            print(" -- running {} {}".format(action, action_input))
            observation = known_actions[action](action_input)
            print("Observation:", observation)
            next_prompt = "Observation: {}".format(observation)
        else:
            return
```

这里我们实现了一个 `query` 函数，其核心是一个循环。每次循环我们都会询问大模型，起始的提示词就是用户的问题。每次询问的结果，我们会先从里面分析出要执行的动作，这里采用了正则表达式直接匹配文本：

```python
action_re = re.compile(r'^Action: (\w+): (.*)$')

actions = [action_re.match(a) for a in result.split('\n') if action_re.match(a)]
```

如果存在要执行的动作，我们就来执行这个动作。在结果中拆分出动作及其输出，然后，去执行：

```python
action, action_input = actions[0].groups()
observation = known_actions[action](action_input)
```

最后，再把执行的结果作为观察结果，发送给大模型进行下一轮的询问：

```python
next_prompt = "Observation: {}".format(observation)
```

万事俱备，我们来执行一下。我们问一个问题：3 千克苹果和 2 千克香蕉一共多少钱？

```python
query("What is the total price of 3kg of apple and 2kg of banana?")
```

Agent 输出的结果如下：

```plain
Thought: To find the total price, I need to know the price per kilogram of both apples and bananas. I will ask for the price of each fruit. 

Action: ask_fruit_unit_price: apple
PAUSE
 -- running ask_fruit_unit_price apple
Observation: Apple unit price is 10/kg
Thought: Now that I have the price for apples, I need to ask for the price of bananas to calculate the total price for 1 kg of apples and 2 kg of bananas.

Action: ask_fruit_unit_price: banana
PAUSE
 -- running ask_fruit_unit_price banana
Observation: Banana unit price is 6/kg
Thought: I now have the prices for both fruits. The price of apples is 10/kg and the price of bananas is 6/kg. I can calculate the total price for 1 kg of apples and 2 kg of bananas.

Action: calculate: 1 * 10 + 2 * 6
PAUSE
 -- running calculate 1 * 10 + 2 * 6
Observation: 22
Answer: The total price of 1 kg of apples and 2 kg of bananas is 22.
```

我们看一下输出的过程：

- 第一步的思考是要计算总价，那么就需要先知道单价。所以，第一个动作是询问苹果的价格。
- 我们执行 `ask_fruit_unit_price` 这个动作，其参数是 apple。我们得到苹果单价之后，再把它作为观察结果，发送给大模型。
- 第二步的思考是，已知苹果价格，要计算总价还要得到香蕉价格。
- 我们执行 `ask_fruit_unit_price` 这个动作，其参数是 banana，同样，把单价作为观察结果返回给大模型。
- 第三步的思考是，两个单价都有了，就可以计算总价了，调用 `calculate` 这个动作，参数是一个表达式：1 * 10 + 2 * 6。
- 我们执行这个计算，得到结果是 22，把它返回给大模型。
- 最后的思考是，已经得到答案，无需继续执行了，把结果返回回来。

经过四轮的询问，我们最终得到了一个答案。可以看到在这个过程中，我们完全没有参与，都是大模型自己思考该干什么，然后执行相应的动作，这就是很多人所说的“自主”（Autonomous）。

当然，这是一个比较简单的问题，如果问题复杂，可能轮数会大幅度增加，极端情况下，甚至会出现无法收敛的情况，也就是一轮一轮地不断问下去，这会造成极大的成本消耗。所以，在设计 Agent 的时候会限制最大询问次数， `query` 函数的 `max_turns` 参数就是做这个限制的。

好了，到这里，你应该对如何实现一个 Agent 有了一个初步的了解。上面的代码对于任何一个程序员来说都可以轻松理解。我们的重点是了解在这个过程中，代码是如何与大模型配合的，比如，我们之所以能找到执行的动作及其参数，是因为我们给大模型的提示词里对输出提了要求。再比如，大模型之所以能够不断地思考，是因为我们把聊天历史传给了大模型，让它对当前的上下文有了理解。

希望你可以花时间慢慢体会大模型与代码之间的这些互动。虽然这个例子很简单，但它很适合作为我们理解大模型编程的基础。

有了这个简单的例子作为基础，当我们再去看更复杂的 Agent 时，就更能理解背后的运作机制，而不致于迷失其中了。

## 总结时刻

这一讲，我们抛开了 LangChain，用更底层的方式实现了一个基于 ReAct 框架的 Agent。我们看到了如何编写一个 ReAct 提示词，让大模型通过思考（Thought）、行动（Action）、观察（Observation）来完成更多的工作。

在我们这个例子里，规划是通过 ReAct 提示词完成的，记忆是通过聊天历史实现的，而动作则是通过一个一个的函数实现的。

如果今天的内容你只能记住一件事，那请记住，**Agent 的执行过程本质上就是一个循环，由大模型引导着一次次地做着各种动作，以达成我们的目标**。

## 练习题

尝试修改我提供的例子，给它增加一些动作，让这个 Agent 实现更多的能力。欢迎在留言区分享你的改造心得。
<div><strong>精选留言（5）</strong></div><ul>
<li><span>hellotong</span> 👍（1） 💬（1）<p>深入浅出👍</p>2024-11-29</li><br/><li><span>kergee</span> 👍（0） 💬（1）<p>和 Function Calling 的区别呢？</p>2025-02-15</li><br/><li><span>grok</span> 👍（3） 💬（0）<p>挺好玩的：
```
query(&quot;三公斤苹果和两公斤香蕉的总价？&quot;)
---
Thought: To calculate the total price of three kilograms of apples and two kilograms of bananas, I first need to know the unit price of each fruit.

Action: ask_fruit_unit_price: apple
PAUSE
 -- running ask_fruit_unit_price apple
Observation: Apple unit price is 10&#47;kg
Thought: Now that I have the price of apples, I need to ask for the price of bananas to proceed with the calculation.

Action: ask_fruit_unit_price: banana
PAUSE
 -- running ask_fruit_unit_price banana
Observation: Banana unit price is 6&#47;kg
Thought: I now have the unit prices for both apples and bananas. I can calculate the total price by multiplying the quantity of each fruit by its unit price and then summing these amounts.

Action: calculate: 3 * 10 + 2 * 6
PAUSE
 -- running calculate 3 * 10 + 2 * 6
Observation: 42
Answer: 三公斤苹果和两公斤香蕉的总价是42元。
```

本节代码在此：https:&#47;&#47;github.com&#47;groklab&#47;misc&#47;blob&#47;main&#47;geektime-llm-zhengye-column&#47;lec13.ipynb</p>2024-12-01</li><br/><li><span>张申傲</span> 👍（1） 💬（0）<p>第13讲打卡~</p>2025-01-24</li><br/><li><span>willmyc</span> 👍（1） 💬（0）<p>老师，您好有几个问题 1.query(&quot;What is the total price of 3kg of apple and 2kg of banana?&quot;)这个prompt和输出的不匹配 2.re.compile 需要导入包，import re 3.为了方便理解，老师后续的代码是否可以增加一点注释，谢谢您！</p>2024-11-29</li><br/>
</ul>