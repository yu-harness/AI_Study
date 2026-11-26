你好，我是徐文浩。

在去年的课程里，我们就说过，像GPT这样的大语言模型，其实并不是全知全能的。无论是简单的算术题，还是想要获取实时的外部信息，如果直接让GPT给出答案，往往会得到错误的结果。

对于这类问题，一个常见的解决方案就是**把大语言模型和自己撰写的程序代码结合起来**。让程序代码解决获取外部的实时信息和精确的数学计算问题，让大语言模型解决语言理解和内容生成问题。然后通过大语言模型的逻辑推理能力，把两者结合起来，通过对用户输入内容的理解，去调用不同的程序代码，最终完成用户的需求。

在前面第14～17课里，我们就介绍过如何使用 Langchain 这个开源框架来做到这一点。而正因为这种方式非常有效，OpenAI 直接在后续的模型里内置了这个能力，也就是我们今天要介绍的 Function Call。

## 通过 Function Call 来计算数学题

### 定义工具方便 Function Call 的调用

我们先通过一个最简单的四则运算的例子，看看怎么使用ChatGPT 的 **Function Call** 的能力。想让 ChatGPT 能够使用“按计算器”的方式，就需要先定义一些“按计算器”的 Function。

```python
import json
def add(x, y):
    return json.dumps({"result" : x + y})

def subtract(x, y):
    return json.dumps({"result" : x - y})

def multiply(x, y):
    return json.dumps({"result" : x * y})

def divide(x, y):
    if y == 0:
        return "Error! Division by zero."
    return json.dumps({"result" : x / y})

def get_tools_definition(function_name, description):
    return {
            "type": "function",
            "function": {
                "name": function_name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "x": {
                            "type": "number",
                            "description": "The first number",
                        },
                        "y": {
                            "type": "number",
                            "description": "the second number",
                        },
                    },
                    "required": ["x", "y"],
                },
            },
        }

tools = [
    get_tools_definition("add", "add x to y"),
    get_tools_definition("subtract", "subtract y from x"),
    get_tools_definition("multiply", "x multiply y"),
    get_tools_definition("divide", "x divide y"),
]

```

定义可以被 Function Call 调用的 Function 的代码  
这里的Python 函数代码非常简单，我们定义了简单的四个加减乘除的函数。不过，为了让 ChatGPT 这样的 AI 能够调用这些代码，这些函数的返回值需要做一下特殊处理。我们不能直接返回对应的计算结果，而是需要把返回结果，以一个 json 字符串的形式包装起来。所以在这里，我们通过 json.dumps 返回了以 result 作为 key，计算结果作为 value 的 字典（dict），进行了序列化之后的字符串。

除此之外，为了让 ChatGPT 理解每个函数是干什么的，我们还需要为这些函数定义一下它们的描述。在这里，加减乘除四个函数的描述除了\*\*函数名称（name）**和**描述（description）\*\*不同之外，其他都是一样的。所以我定义了一个 **get\_tools\_definition** 函数，来为这四个函数定义对应的描述信息。

一个可以给 ChatGPT 调用的 Function Call 的描述信息，是一个 Python 的dict。里面通过键值对的方式提供一些参数。

1. 必选的 **type** 参数，值必须是 **function**，来告诉 ChatGPT 这是一个 function call 的工具。
2. 必选的 **function** 参数，内部也是一个 dict，通过下面的这些参数来描述这个 function 是干什么的，以及如何调用：

<!--THE END-->

- **name** 定义了 function 对应的名称，后续在 ChatGPT 返回的结果里，就会根据这个名称来告诉我们应该调用哪一个 function。
- **description** 描述了 function 能干什么事情，ChatGPT 并不会去读取你定义的 Python 函数代码。所以你需要在 description 里清楚地描述出你这个 function 是用来干什么事情的。
- **parameters** 定义了这个函数能够支持的输入参数，里面是一个 JSON Schema 对象。在这里，我们定义了 **x** 和 **y** 这两个参数，并且描述了他们的类型是 number。然后通过 **required** 这个属性，定义了在函数的输入里 **x** 和 **y** 这两个参数都是必须的。

### 通过 ChatGPT 来选择调用的 Function Call

在有了 **get\_tools\_definition** 函数之后，我们在 **tools** 这个数组，一口气定义了加减乘除的四个函数。有了这个tools 数组，我们就可以沿用之前的 ChatGPT 的 API，来组合 AI 和 Python函数，实现算术运算了。

```python
from openai import OpenAI
import json

client = OpenAI()

messages = [{"role": "user", "content": "What does 1024 + 10086 equal to?"}]
response = client.chat.completions.create(
    model="gpt-3.5-turbo-0125",
    messages=messages,
    tools=tools,
    tool_choice="auto",  # auto is default, but we'll be explicit
)

```

这里调用的 ChatGPT 的代码和之前基本一样，一个小小的区别在于，我们传入了 **tools** 和 **tools\_choice** 这两个参数。其中，**tools** 参数用的就是我们刚刚定义好的 tools 数组，而 **tools\_choice** 参数则是设置成了 **“auto”**，也就是告诉 ChatGPT，它应该自动决策应该使用哪一个函数。在这里，我们发送给 ChatGPT 的问题是 “What does 1024 + 10086 equal to?”，我们期望它会调用加法来进行对应地计算。

```python
response_message = response.choices[0].message
print(response_message.content)
```

输出结果：

```python
None
```

调用了 ChatGPT 之后，我们可以像往常一样，把对应的消息结果给打印出来。你可以看到，这个时候返回的输出结果是 None，而不是一个我们可以阅读的答案。不过这一点，其实是在意料之内的，因为我们通过 tools 和 tools\_choice 这两个参数，告诉了 ChatGPT 我们想要使用 Function Call 功能，所以我们希望 ChatGPT 并不是返回一个文本消息给我们，而是告诉我们应该调用哪一个 function，以及调用这个 function 的参数是什么。而这些信息，我们可以从 response 的 tool\_calls 字段中拿到。

```python
tool_calls = response_message.tool_calls
available_functions = {
    "add": add,
    "subtract": subtract,
    "multiply": multiply,
    "divide": divide,
}

for tool_call in tool_calls:
    function_name = tool_call.function.name
    tool_call_id = tool_call.id
    function_to_call = available_functions[function_name]
    function_args = json.loads(tool_call.function.arguments)
    function_response = function_to_call(
        x=function_args.get("x"),
        y=function_args.get("y"),
    )
    print(function_response)
    //从 tool_calls 中拿到需要调用的函数以及参数，并且实际调用对应的函数
```

输出结果：

```python
{"result": 11110}
```

可以看到，返回的结果就是 1024 + 10086 的计算结果。

我们实际拿到的 tool\_calls 是一个列表，里面可能会有多个 function 对象，我们可以依次获取并调用这些 function。function的 name 参数就对应着我们之前在定义 tool 的过程中的 name 参数，function 的 arguments 参数就对应着我们之前定义 tool 过程中的 parameters 参数。通过利用 name 名称对应的函数，调用对应的参数名称，我们就能获取到函数执行的结果。

### 获取自然语言回答的问题答案

不过，我们还是希望 ChatGPT 能够通过一个自然语言来告诉我们答案。因为很多时候，Function Call 调用的函数，只是一个中间结果，而不是我们想要的最终答案。

```python
messages.append(response_message)
messages.append(
    {
        "tool_call_id": tool_call_id,
        "role": "tool",
        "name": function_name,
        "content": str(function_response),
    }
)  

final_response = client.chat.completions.create(
    model="gpt-3.5-turbo-0125",
    messages=messages,
)
print(final_response.choices[0].message.content)
```

输出结果：

```python
1024 + 10086 = 11110
```

可以看到，返回的输出结果是整个算术式，而不是孤零零的一个数字。

所以，我们需要再给到 ChatGPT 更多的上下文（Context），让它理解我们是通过调用 Function Call 选择了一个函数进行调用，并且拿到了函数的调用结果，然后请它给我们一个最终的答案。

首先，我们要把刚才第一次 ChatGPT 调用的返回结果添加到 messages 里，让 ChatGPT 知道这时它返回给我们选择要调用的Function Call 是什么。也就是刚刚那段代码中的第一行内容。

```python
messages.append(response_message)
```

其次，我们还要将 Function Call 的调用结果，也封装成一条消息，加入到 messages 中。在这条消息里面，我们需要告诉 ChatGPT，它的 tool\_call\_id 就是刚才它要求调用的 function call的 id，对应的 role 就是 “tool”，而 name 就是 function\_name。

最后，我们把这个包含了 ChatGPT 选择的 function call，以及 function call 的返回结果的 messages 再次发送给 ChatGPT，就能拿到一个自然语言表达的结果，而不是一个 function call 给到的一个孤零零的数字。比如，在这里最终的输出结果就是这样一个算术式子：

```python
1024 + 10086 = 11110
```

### 需要注意函数调用的描述

Function Call 的功能非常强大且实用，不过要注意。ChatGPT 其实并不知道我们撰写的 Python 函数代码是怎么实现的。比如，我们可以看一看，如果在减法的描述里，把 x 和 y 的关系写反，会怎么样。

我们先把前面整个 Function Call 的过程封装成一个函数。

```python
def chat_using_function_call(content, tools = tools, available_functions = available_functions, client = client):    messages = [{"role": "user", "content": content}]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    response_message = response.choices[0].message
    messages.append(response_message)    
    tool_calls = response_message.tool_calls
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_to_call = available_functions[function_name]
        function_args = json.loads(tool_call.function.arguments)
        function_response = function_to_call(
            x=function_args.get("x"),
            y=function_args.get("y"),
        )
        messages.append(
            {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            }
            )
    final_response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=messages,
    )
    print(final_response.choices[0].message.content)
```

然后调用 Function Call 来进行减法计算。

```python
chat_using_function_call("What does 10086 - 1024 equal to?")
```

输出结果：

```python
10086 - 1024 equals to 9062.
```

我们先把之前的的 Function Call 的调用链路封装成一个函数，这样后面我们要测试不同的function 的 description 的时候会比较方便。可以看到，在这个时候，我们询问 ChatGPT 一个减法问题的时候，获得的答案仍然是正确的。

接下来，我们来修改一下减法 function 的描述，我们的subtract 函数实现里写的是 x - y，但是在描述中，我们把它改成 y - x。

```python
tools = [
    get_tools_definition("add", "add x to y"),
    get_tools_definition("subtract", "y - x"),
    get_tools_definition("multiply", "x multiply y"),
    get_tools_definition("divide", "x divide y"),
]
chat_using_function_call("What does 10086 - 1024 equal to?", tools = tools)
```

输出结果：

```python
10086 - 1024 equals -9062.
```

可以看到，这个时候 ChatGPT 给到的减法的答案就错了。它按照我们的描述更换了输入的 x 和 y 这两个参数的顺序，导致减法的结果变成了一个负数。**所以想要让 function call 获得一个准确而有效的结果，对function 的准确描述和命名就非常重要了。**

## 通过 Function Call 来连接外部资料库

在刚刚的例子里，我们提出的问题，直接通过一次 Function Call 就得到了答案。但是很多时候，我们询问的问题更加复杂，API 只是帮助我们获取了信息，最终还需要 ChatGPT 去分析这个答案才会拿到最终的结果。

### 尝试 SerpAPI

比如说，市场上有很多搜索相关的 API，能够帮助我们拿到商品的相关信息，我就经常使用 SerpAPI 来快速搭建一些原型。

首先，你还是需要安装 serpapi 和 google-search-results 这两个 python 库。

```python
%pip install serpapi
%pip install google-search-results
```

然后我们去 serapi.com 注册一个账号，就能获得一个 API\_KEY，可以进行 100 次免费的搜索API 的调用。

我们先来试一试这个搜索 API。

```python
API_KEY = "YOUR_API_KEY"

from serpapi import GoogleSearch
params = {
  "engine": "google_shopping",
  "q": "Macbook M3",
  "api_key": API_KEY
}
search = GoogleSearch(params)
results = search.get_dict()
shopping_results = results["shopping_results"]

import json
pretty_json = json.dumps(shopping_results, indent=4)
print(pretty_json)
```

输出结果：

```python
[
    {
        "position": 1,
        "title": "Apple 14\" MacBook Pro (M3, Space Gray) with Apple M3 8-Core Chip 8GB Unified RAM ...",
        "link": "https://www.bhphotovideo.com/c/product/1793630-REG/apple_mtl73ll_a_14_macbook_pro_with.html?kw=APMTL73LLA&ap=y&smp=y&BI=E6540&srsltid=AfmBOopxJGtKB93QRtNQIcVcZ6ExpmkCUFj_tri2hicX0iQ02Jwvegnii78",
        "product_link": "https://www.google.com/shopping/product/1?gl=us&prds=pid:10805795665197980642",
        "product_id": "10805795665197980642",
        "serpapi_product_api": "https://serpapi.com/search.json?device=desktop&engine=google_product&gl=us&google_domain=google.com&hl=en&product_id=10805795665197980642",
        "source": "B&H Photo-Video-Audio",
        "price": "$1,449.00",
        ……
        ……
        ...
        "store_rating": 4.4,
        "store_reviews": 1400
    }
]
```

可以看到，我们通过一个简单的关键词，就能搜索到里面的商品名称、价格等购物信息。

### 将 SerpAPI 封装成 Function Call

有了这个搜索函数的能力，我们就可以把它封装成 function call，供我们后续通过 ChatGPT 来调用。

我们先封装 search\_product 的代码。

```python
def search_product(product_keywords):

    params = {
    "engine": "google_shopping",
    "q": product_keywords,
    "api_key": API_KEY
    }
    search = GoogleSearch(params)
    results = search.get_dict()
    shopping_results = results["shopping_results"][0]
    return json.dumps(shopping_results)

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_product",
            "description": "search for a product on google shopping, get information like name, price, description etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "product_keywords": {
                        "type": "string",
                        "description": "Name or key words of the product to search",
                    },
                },
                "required": ["product_keywords"],
            },
        }
    },
]
```

然后根据新的参数和函数，封装Function Call 的过程。

```python
available_functions = {
    "search_product": search_product,
}

def chat_using_function_call(content, tools = tools, available_functions = available_functions, client = client):
    messages = [{"role": "user", "content": content}]
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    response_message = response.choices[0].message
    messages.append(response_message)    
    tool_calls = response_message.tool_calls
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_to_call = available_functions[function_name]
        function_args = json.loads(tool_call.function.arguments)
        function_response = function_to_call(
            product_keywords=function_args.get("product_keywords"),
        )
        print("function " + function_name + ", with arguments " + str(function_args) + " called")
        messages.append(
            {
                "tool_call_id": tool_call.id,
                "role": "tool",
                "name": function_name,
                "content": function_response,
            }
            )
    final_response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        messages=messages,
    )
    print(final_response.choices[0].message.content)
 
```

这里的代码和前面加减乘除的代码基本一样，我们只是修改了对应的函数 name、description、parameters 这些配置参数。并且在 Function Call 的调用链路中，通过 print 函数，打印出了什么样的 function 被调用了。

有了这样的封装，我们就可以来问问 ChatGPT，最新的 Macbook M3 的价格了。

```python
chat_using_function_call("What is the price of Macbook M3?", tools = tools)
```

输出结果：

```python
function search_product, with arguments {'product_keywords': 'Macbook M3'} called
The price of the Apple 14" MacBook Pro with M3 8-Core Chip and 8GB Unified RAM is $1,449.00. You can find more details on the product [here](https://www.bhphotovideo.com/c/product/1793630-REG/apple_mtl73ll_a_14_macbook_pro_with.html?kw=APMTL73LLA&ap=y&smp=y&BI=E6540&srsltid=AfmBOopxJGtKB93QRtNQIcVcZ6ExpmkCUFj_tri2hicX0iQ02Jwvegnii78).
```

可以看到，在输出结果中 ChatGPT 先通过我们封装好的 search\_product 函数，搜索了搜索引擎中的购物信息。在最终的返回结果中，也给出了详细的Macbook M3 的配置、价格，乃至购买链接。

而且我们不仅可以查看单个商品的信息，还能利用 Function Call 的能力，比较两个不同商品的价格信息。比如，我们可以让 ChatGPT 帮助我们比较 Macbook M3 和 Macbook M2 的商品价格。

```python
chat_using_function_call("Could you help me to compare the price of Macbook M3 and Macbook M2?", tools = tools)
```

输出结果：

```python
function search_product, with arguments {'product_keywords': 'Macbook M3'} called
function search_product, with arguments {'product_keywords': 'Macbook M2'} called
The price of the Macbook M3 (Apple 14" MacBook Pro with M3 8-Core Chip 8GB Unified RAM) is $1,449.00. You can find more details about it [here](https://www.bhphotovideo.com/c/product/1793630-REG/apple_mtl73ll_a_14_macbook_pro_with.html?kw=APMTL73LLA&ap=y&smp=y&BI=E6540&srsltid=AfmBOopxJGtKB93QRtNQIcVcZ6ExpmkCUFj_tri2hicX0iQ02Jwvegnii78).
The price of the Macbook M2 (MacBook Air 15-Inch, M2 8GB RAM 256GB SSD) is $999.00. More details can be found [here](https://www.bestbuy.com/site/apple-macbook-air-15-laptop-m2-chip-8gb-memory-256gb-ssd-midnight/6534606.p?skuId=6534606&utm_source=feed).
Therefore, the Macbook M3 is priced higher than the Macbook M2.
```

可以看到，在输出的结果中，ChatGPT 的 Function Call 被调用了两次，分别查询了 Macbook M3 和 Macbook M2 的商品信息。并且，它并不是直接拿其中的任何一个返回结果给我们一个答案，而是真的比较了两个商品的价格，并告诉我们新款的 M3 的价格要高于旧款的 M2。

这也是 Function Call 功能的强大之处，它可以通过多个 Function Call 调用，并且配合 ChatGPT 自身的理解能力和推理能力，给出一个复杂问题的答案。

## 小结

好了，这一讲到这里就结束了。这一讲我为你介绍了 OpenAI 的 ChatGPT 的相关接口提供的 Function Call 能力。和之前我们介绍过的 Langchain 类似， Function Call 可以让 AI 选择外部的程序函数来调用，解决 ChatGPT 这样的语言模型并不擅长进行数学运算，也缺少有时效性的外部数据信息的问题。

并且ChatGPT 一次请求中，可能会让你调用多个外部函数，这样我们就可以组合不同的 Function Call 的调用结果，解决更加复杂的问题。

## 思考题

在这一讲的代码实现中，我们在获得 Function Call 的调用结果后，并不会根据拿到的返回结果，再次调用 Function Call。你想一想，我们在什么场景下会产生这样的“连环调用”Function Call 的需求呢？如果有的话，你能尝试撰写代码实现这样的通用功能吗？

欢迎你把你的代码实现分享再评论区，也欢迎你把这节课的内容分享给其他朋友，我们下节课再见！
<div><strong>精选留言（4）</strong></div><ul>
<li><span>Toni</span> 👍（3） 💬（0）<p>谢谢徐文浩老师的加餐，并在思考题里提出“连环调用”Function Call的问题。

让AI解决一个比较复杂的工作流程，包括自动规划分割子任务，自动生成子任务调动的排序，执行各个子任务并将结果汇总保存最终反馈给用户，可以考虑使用plan-and-excute框架，参考: https:&#47;&#47;blog.langchain.dev&#47;planning-agents&#47;</p>2024-08-08</li><br/><li><span>longslee</span> 👍（1） 💬（0）<p>思考题：是不是递归场景呀？以前编码时需要程序员设定边界和退出条件，现在把要求提给 ChatGPT 让它去调用。当然它会不会产生递归的调用，我也不清楚哈哈，猜测。</p>2024-07-10</li><br/><li><span>twintel</span> 👍（0） 💬（0）<p>这个是不是可以用来解决最近比较火的9.8和9.11比大小的问题</p>2024-07-19</li><br/><li><span>Geek_aecc52</span> 👍（0） 💬（0）<p>良心作者呀，又加餐了</p>2024-06-13</li><br/>
</ul>