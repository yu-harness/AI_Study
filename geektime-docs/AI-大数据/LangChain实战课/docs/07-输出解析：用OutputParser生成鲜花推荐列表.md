你好，我是黄佳，欢迎来到LangChain实战课！

首先请你回忆一下[第4课](https://time.geekbang.org/column/article/700699)中我们学了什么: 为一些花和价格生成吸引人的描述，并将这些描述和原因存储到一个CSV文件中。为了实现这个目标，程序调用了OpenAI模型，并利用了结构化输出解析器，以及一些数据处理和存储的工具。

今天我要带着你深入研究一下LangChain中的输出解析器，并用一个新的解析器——Pydantic 解析器来重构第4课中的程序。这节课也是模型I/O框架的最后一讲。

![](https://static001.geekbang.org/resource/image/62/2d/6215fdd31373523a46bb02f86283522d.jpg?wh=4000x1536 "模型 I/O Pipeline")

下面先来看看LangChain中的输出解析器究竟是什么，有哪些种类。

## LangChain 中的输出解析器

语言模型输出的是文本，这是给人类阅读的。但很多时候，你可能想要获得的是程序能够处理的结构化信息。这就是输出解析器发挥作用的地方。

输出解析器是**一种专用于处理和构建语言模型响应的类**。一个基本的输出解析器类通常需要实现两个核心方法。

- get\_format\_instructions：这个方法需要返回一个字符串，用于指导如何格式化语言模型的输出，告诉它应该如何组织并构建它的回答。
- parse：这个方法接收一个字符串（也就是语言模型的输出）并将其解析为特定的数据结构或格式。这一步通常用于确保模型的输出符合我们的预期，并且能够以我们需要的形式进行后续处理。

还有一个可选的方法。

- parse\_with\_prompt：这个方法接收一个字符串（也就是语言模型的输出）和一个提示（用于生成这个输出的提示），并将其解析为特定的数据结构。这样，你可以根据原始提示来修正或重新解析模型的输出，确保输出的信息更加准确和贴合要求。

下面是一个基于上述描述的简单伪代码示例：

```plain
class OutputParser:
    def __init__(self):
        pass

    def get_format_instructions(self):
        # 返回一个字符串，指导如何格式化模型的输出
        pass

    def parse(self, model_output):
        # 解析模型的输出，转换为某种数据结构或格式
        pass

    def parse_with_prompt(self, model_output, prompt):
        # 基于原始提示解析模型的输出，转换为某种数据结构或格式
        pass
```

在LangChain中，通过实现get\_format\_instructions、parse 和 parse\_with\_prompt 这些方法，针对不同的使用场景和目标，设计了各种输出解析器。让我们来逐一认识一下。

1. 列表解析器（List Parser）：这个解析器用于处理模型生成的输出，当需要模型的输出是一个列表的时候使用。例如，如果你询问模型“列出所有鲜花的库存”，模型的回答应该是一个列表。
2. 日期时间解析器（Datetime Parser）：这个解析器用于处理日期和时间相关的输出，确保模型的输出是正确的日期或时间格式。
3. 枚举解析器（Enum Parser）：这个解析器用于处理预定义的一组值，当模型的输出应该是这组预定义值之一时使用。例如，如果你定义了一个问题的答案只能是“是”或“否”，那么枚举解析器可以确保模型的回答是这两个选项之一。
4. 结构化输出解析器（Structured Output Parser）：这个解析器用于处理复杂的、结构化的输出。如果你的应用需要模型生成具有特定结构的复杂回答（例如一份报告、一篇文章等），那么可以使用结构化输出解析器来实现。
5. Pydantic（JSON）解析器：这个解析器用于处理模型的输出，当模型的输出应该是一个符合特定格式的JSON对象时使用。它使用Pydantic库，这是一个数据验证库，可以用于构建复杂的数据模型，并确保模型的输出符合预期的数据模型。
6. 自动修复解析器（Auto-Fixing Parser）：这个解析器可以自动修复某些常见的模型输出错误。例如，如果模型的输出应该是一段文本，但是模型返回了一段包含语法或拼写错误的文本，自动修复解析器可以自动纠正这些错误。
7. 重试解析器（RetryWithErrorOutputParser）：这个解析器用于在模型的初次输出不符合预期时，尝试修复或重新生成新的输出。例如，如果模型的输出应该是一个日期，但是模型返回了一个字符串，那么重试解析器可以重新提示模型生成正确的日期格式。

上面的各种解析器中，前三种很容易理解，而结构化输出解析器你已经用过了。所以接下来我们重点讲一讲Pydantic（JSON）解析器、自动修复解析器和重试解析器。

## Pydantic（JSON）解析器实战

Pydantic (JSON) 解析器应该是最常用也是最重要的解析器，我带着你用它来重构鲜花文案生成程序。

> Pydantic 是一个 Python 数据验证和设置管理库，主要基于 Python 类型提示。尽管它不是专为 JSON 设计的，但由于 JSON 是现代 Web 应用和 API 交互中的常见数据格式，Pydantic 在处理和验证 JSON 数据时特别有用。

### 第一步：创建模型实例

先通过环境变量设置OpenAI API密钥，然后使用LangChain库创建了一个OpenAI的模型实例。这里我们仍然选择了text-davinci-003作为大语言模型。

```plain
# ------Part 1
# 设置OpenAI API密钥
import os
os.environ["OPENAI_API_KEY"] = '你的OpenAI API Key'

# 创建模型实例
from langchain import OpenAI
model = OpenAI(model_name='gpt-3.5-turbo-instruct')
```

### 第二步：定义输出数据的格式

先创建了一个空的DataFrame，用于存储从模型生成的描述。接下来，通过一个名为FlowerDescription的Pydantic BaseModel类，定义了期望的数据格式（也就是数据的结构）。

```plain
# ------Part 2
# 创建一个空的DataFrame用于存储结果
import pandas as pd
df = pd.DataFrame(columns=["flower_type", "price", "description", "reason"])

# 数据准备
flowers = ["玫瑰", "百合", "康乃馨"]
prices = ["50", "30", "20"]

# 定义我们想要接收的数据格式
from pydantic import BaseModel, Field
class FlowerDescription(BaseModel):
    flower_type: str = Field(description="鲜花的种类")
    price: int = Field(description="鲜花的价格")
    description: str = Field(description="鲜花的描述文案")
    reason: str = Field(description="为什么要这样写这个文案")
```

在这里我们用到了负责数据格式验证的Pydantic库来创建带有类型注解的类FlowerDescription，它可以自动验证输入数据，确保输入数据符合你指定的类型和其他验证条件。

Pydantic有这样几个特点。

1. 数据验证：当你向Pydantic类赋值时，它会自动进行数据验证。例如，如果你创建了一个字段需要是整数，但试图向它赋予一个字符串，Pydantic会引发异常。
2. 数据转换：Pydantic不仅进行数据验证，还可以进行数据转换。例如，如果你有一个需要整数的字段，但你提供了一个可以转换为整数的字符串，如 `"42"`，Pydantic会自动将这个字符串转换为整数42。
3. 易于使用：创建一个Pydantic类就像定义一个普通的Python类一样简单。只需要使用Python的类型注解功能，即可在类定义中指定每个字段的类型。
4. JSON支持：Pydantic类可以很容易地从JSON数据创建，并可以将类的数据转换为JSON格式。

下面，我们基于这个Pydantic数据格式类来创建LangChain的输出解析器。

### 第三步：创建输出解析器

在这一步中，我们创建输出解析器并获取输出格式指示。先使用LangChain库中的PydanticOutputParser创建了输出解析器，该解析器将用于解析模型的输出，以确保其符合FlowerDescription的格式。然后，使用解析器的get\_format\_instructions方法获取了输出格式的指示。

```plain
# ------Part 3
# 创建输出解析器
from langchain.output_parsers import PydanticOutputParser
output_parser = PydanticOutputParser(pydantic_object=FlowerDescription)

# 获取输出格式指示
format_instructions = output_parser.get_format_instructions()
# 打印提示
print("输出格式：",format_instructions)
```

程序输出如下：

```plain
输出格式： The output should be formatted as a JSON instance that conforms to the JSON schema below.

As an example, for the schema {"properties": {"foo": {"title": "Foo", "description": "a list of strings", "type": "array", "items": {"type": "string"}}}, "required": ["foo"]}}
the object {"foo": ["bar", "baz"]} is a well-formatted instance of the schema. The object {"properties": {"foo": ["bar", "baz"]}} is not well-formatted.

Here is the output schema:

{"properties": {"flower_type": {"title": "Flower Type", "description": "\u9c9c\u82b1\u7684\u79cd\u7c7b", "type": "string"}, "price": {"title": "Price", "description": "\u9c9c\u82b1\u7684\u4ef7\u683c", "type": "integer"}, "description": {"title": "Description", "description": "\u9c9c\u82b1\u7684\u63cf\u8ff0\u6587\u6848", "type": "string"}, "reason": {"title": "Reason", "description": "\u4e3a\u4ec0\u4e48\u8981\u8fd9\u6837\u5199\u8fd9\u4e2a\u6587\u6848", "type": "string"}}, "required": ["flower_type", "price", "description", "reason"]}
```

上面这个输出，这部分是通过output\_parser.get\_format\_instructions()方法生成的，这是Pydantic (JSON) 解析器的核心价值，值得你好好研究研究。同时它也算得上是一个很清晰的提示模板，能够为模型提供良好的指导，描述了模型输出应该符合的格式。（其中description中的中文被转成了UTF-8编码。）

它指示模型输出JSON Schema的形式，定义了一个有效的输出应该包含哪些字段，以及这些字段的数据类型。例如，它指定了 `"flower_type"` 字段应该是字符串类型，`"price"` 字段应该是整数类型。这个指示中还提供了一个例子，说明了什么是一个格式良好的输出。

下面，我们会把这个内容也传输到模型的提示中，**让输入模型的提示和输出解析器的要求相互吻合，前后就呼应得上**。

### 第四步：创建提示模板

我们定义了一个提示模板，该模板将用于为模型生成输入提示。模板中包含了你需要模型填充的变量（如价格和花的种类），以及之前获取的输出格式指示。

```plain
# ------Part 4
# 创建提示模板
from langchain import PromptTemplate
prompt_template = """您是一位专业的鲜花店文案撰写员。
对于售价为 {price} 元的 {flower} ，您能提供一个吸引人的简短中文描述吗？
{format_instructions}"""

# 根据模板创建提示，同时在提示中加入输出解析器的说明
prompt = PromptTemplate.from_template(prompt_template, 
       partial_variables={"format_instructions": format_instructions}) 

# 打印提示
print("提示：", prompt)
```

输出：

````plain
提示： 
input_variables=['flower', 'price'] 

output_parser=None 

partial_variables={'format_instructions': 'The output should be formatted as a JSON instance that conforms to the JSON schema below.\n\n
As an example, for the schema {
"properties": {"foo": {"title": "Foo", "description": "a list of strings", "type": "array", "items": {"type": "string"}}}, 
"required": ["foo"]}}\n
the object {"foo": ["bar", "baz"]} is a well-formatted instance of the schema. 
The object {"properties": {"foo": ["bar", "baz"]}} is not well-formatted.\n\n
Here is the output schema:\n```\n
{"properties": {
"flower_type": {"title": "Flower Type", "description": "\\u9c9c\\u82b1\\u7684\\u79cd\\u7c7b", "type": "string"}, 
"price": {"title": "Price", "description": "\\u9c9c\\u82b1\\u7684\\u4ef7\\u683c", "type": "integer"}, 
"description": {"title": "Description", "description": "\\u9c9c\\u82b1\\u7684\\u63cf\\u8ff0\\u6587\\u6848", "type": "string"}, 
"reason": {"title": "Reason", "description": "\\u4e3a\\u4ec0\\u4e48\\u8981\\u8fd9\\u6837\\u5199\\u8fd9\\u4e2a\\u6587\\u6848", "type": "string"}}, 
"required": ["flower_type", "price", "description", "reason"]}\n```'} 

template='您是一位专业的鲜花店文案撰写员。
\n对于售价为 {price} 元的 {flower} ，您能提供一个吸引人的简短中文描述吗？\n
{format_instructions}' 

template_format='f-string' 

validate_template=True
````

这就是包含了format\_instructions信息的提示模板。

1. `input_variables=['flower', 'price']`：这是一个包含你想要在模板中使用的输入变量的列表。我们在模板中使用了 `'flower'` 和 `'price'` 两个变量，后面我们会用具体的值（如玫瑰、20元）来替换这两个变量。
2. `output_parser=None`：这是你可以选择在模板中使用的一个输出解析器。在此例中，我们并没有选择在模板中使用输出解析器，而是在模型外部进行输出解析，所以这里是 `None`。
3. `partial_variables`：包含了你想要在模板中使用，但在生成模板时无法立即提供的变量。在这里，我们通过 `'format_instructions'` 传入输出格式的详细说明。
4. `template`：这是模板字符串本身。它包含了你想要模型生成的文本的结构。在此例中，模板字符串是你询问鲜花描述的问题，以及关于输出格式的说明。
5. `template_format='f-string'`：这是一个表示模板字符串格式的选项。此处是f-string格式。
6. `validate_template=True`：表示是否在创建模板时检查模板的有效性。这里选择了在创建模板时进行检查，以确保模板是有效的。

总的来说，这个提示模板是一个用于生成模型输入的工具。你可以在模板中定义需要的输入变量，以及模板字符串的格式和结构，然后使用这个模板来为每种鲜花生成一个描述。

后面，我们还要把实际的信息，循环传入提示模板，生成一个个的具体提示。下面让我们继续。

### 第五步：生成提示，传入模型并解析输出

这部分是程序的主体，我们循环来处理所有的花和它们的价格。对于每种花，都根据提示模板创建了输入，然后获取模型的输出。然后使用之前创建的解析器来解析这个输出，并将解析后的输出添加到DataFrame中。最后，你打印出了所有的结果，并且可以选择将其保存到CSV文件中。

```plain
# ------Part 5
for flower, price in zip(flowers, prices):
    # 根据提示准备模型的输入
    input = prompt.format(flower=flower, price=price)
    # 打印提示
    print("提示：", input)

    # 获取模型的输出
    output = model(input)

    # 解析模型的输出
    parsed_output = output_parser.parse(output)
    parsed_output_dict = parsed_output.dict()  # 将Pydantic格式转换为字典

    # 将解析后的输出添加到DataFrame中
    df.loc[len(df)] = parsed_output.dict()

# 打印字典
print("输出的数据：", df.to_dict(orient='records'))
```

这一步中，你使用你的模型和输入提示（由鲜花种类和价格组成）生成了一个具体鲜花的文案需求（同时带有格式描述），然后传递给大模型，也就是说，提示模板中的 flower 和 price，此时都被具体的花取代了，而且模板中的 {format\_instructions}，也被替换成了 JSON Schema 中指明的格式信息。

具体来说，输出的一个提示是这样的：

> **提示**： 您是一位专业的鲜花店文案撰写员。  
> 对于售价为 20 元的 康乃馨 ，您能提供一个吸引人的简短中文描述吗？  
>    
> The output should be formatted as a JSON instance that conforms to the JSON schema below.  
>    
> As an example, for the schema {“properties”: {“foo”: {“title”: “Foo”, “description”: “a list of strings”, “type”: “array”, “items”: {“type”: “string”}}}, “required”: \[“foo”]}}  
> the object {“foo”: \[“bar”, “baz”]} is a well-formatted instance of the schema. The object {“properties”: {“foo”: \[“bar”, “baz”]}} is not well-formatted.  
>    
> Here is the output schema:
> 
> ```
> {"properties": {"flower_type": {"title": "Flower Type", "description": "\u9c9c\u82b1\u7684\u79cd\u7c7b", "type": "string"}, "price": {"title": "Price", "description": "\u9c9c\u82b1\u7684\u4ef7\u683c", "type": "integer"}, "description": {"title": "Description", "description": "\u9c9c\u82b1\u7684\u63cf\u8ff0\u6587\u6848", "type": "string"}, "reason": {"title": "Reason", "description": "\u4e3a\u4ec0\u4e48\u8981\u8fd9\u6837\u5199\u8fd9\u4e2a\u6587\u6848", "type": "string"}}, "required": ["flower_type", "price", "description", "reason"]}
> ```

下面，程序解析模型的输出。在这一步中，你使用你之前定义的输出解析器（output\_parser）将模型的输出解析成了一个FlowerDescription的实例。FlowerDescription是你之前定义的一个Pydantic类，它包含了鲜花的类型、价格、描述以及描述的理由。

然后，将解析后的输出添加到DataFrame中。在这一步中，你将解析后的输出（即FlowerDescription实例）转换为一个字典，并将这个字典添加到你的DataFrame中。这个DataFrame是你用来存储所有鲜花描述的。

模型的最后输出如下：

```plain
输出的数据： 
[{'flower_type': 'Rose', 'price': 50, 'description': '玫瑰是最浪漫的花，它具有柔和的粉红色，有着浓浓的爱意，价格实惠，50元就可以拥有一束玫瑰。', 'reason': '玫瑰代表着爱情，是最浪漫的礼物，以实惠的价格，可以让您尽情体验爱的浪漫。'}, 
{'flower_type': '百合', 'price': 30, 'description': '这支百合，柔美的花蕾，在你的手中摇曳，仿佛在与你深情的交谈', 'reason': '营造浪漫氛围'}, 
{'flower_type': 'Carnation', 'price': 20, 'description': '艳丽缤纷的康乃馨，带给你温馨、浪漫的气氛，是最佳的礼物选择！', 'reason': '康乃馨是一种颜色鲜艳、芬芳淡雅、具有浪漫寓意的鲜花，非常适合作为礼物，而且20元的价格比较实惠。'}]
```

因此，Pydantic的优点就是容易解析，而解析之后的字典格式的列表在进行数据分析、处理和存储时非常方便。每个字典代表一条记录，它的键（ 即 `"flower_type"`、`"price"`、`"description"` 和 `"reason"`）是字段名称，对应的值是这个字段的内容。这样一来，每个字段都对应一列，每个字典就是一行，适合以DataFrame的形式来表示和处理。

## 自动修复解析器（OutputFixingParser）实战

下面咱们来看看如何使用自动修复解析器。

首先，让我们来设计一个解析时出现的错误。

```plain
# 导入所需要的库和模块
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List

# 使用Pydantic创建一个数据格式，表示花
class Flower(BaseModel):
    name: str = Field(description="name of a flower")
    colors: List[str] = Field(description="the colors of this flower")
# 定义一个用于获取某种花的颜色列表的查询
flower_query = "Generate the charaters for a random flower."

# 定义一个格式不正确的输出
misformatted = "{'name': '康乃馨', 'colors': ['粉红色','白色','红色','紫色','黄色']}"

# 创建一个用于解析输出的Pydantic解析器，此处希望解析为Flower格式
parser = PydanticOutputParser(pydantic_object=Flower)
# 使用Pydantic解析器解析不正确的输出
parser.parse(misformatted)
```

这段代码如果运行，会出现错误。

```plain
langchain.schema.output_parser.OutputParserException: Failed to parse Flower from completion {'name': '康乃馨', 'colors': ['粉红色','白色']}. Got: Expecting property name enclosed in double quotes: line 1 column 2 (char 1)
```

这个错误消息来自Python的内建JSON解析器发现我们输入的JSON格式不正确。程序尝试用PydanticOutputParser来解析JSON字符串时，Python期望属性名称被双引号包围，但在给定的JSON字符串中是单引号。

当这个错误被触发后，程序进一步引发了一个自定义异常：OutputParserException，它提供了更多关于错误的上下文。这个自定义异常的消息表示在尝试解析flower对象时遇到了问题。

刚才说了，问题在于misformatted字符串的内容：

`"{'name': '康乃馨', 'colors': ['粉红色','白色','红色','紫色','黄色']}"`

应该改为：

`'{"name": "康乃馨", "colors": ["粉红色","白色","红色","紫色","黄色"]}'`

这样，你的JSON字符串就会使用正确的双引号格式，应该可以被正确地解析。

不过，这里我并不想这样解决问题，而是尝试使用OutputFixingParser来帮助咱们自动解决类似的格式错误。

```plain
# 从langchain库导入所需的模块
from langchain.chat_models import ChatOpenAI
from langchain.output_parsers import OutputFixingParser

# 设置OpenAI API密钥
import os
os.environ["OPENAI_API_KEY"] = '你的OpenAI API Key'

# 使用OutputFixingParser创建一个新的解析器，该解析器能够纠正格式不正确的输出
new_parser = OutputFixingParser.from_llm(parser=parser, llm=ChatOpenAI())

# 使用新的解析器解析不正确的输出
result = new_parser.parse(misformatted) # 错误被自动修正
print(result) # 打印解析后的输出结果
```

用上面的新的new\_parser来代替Parser进行解析，你会发现，JSON格式的错误问题被解决了，程序不再出错。

输出如下：

```plain
name='Rose' colors=['red', 'pink', 'white']
```

这里的秘密在于，在OutputFixingParser内部，调用了原有的PydanticOutputParser，如果成功，就返回；如果失败，它会将格式错误的输出以及格式化的指令传递给大模型，并要求LLM进行相关的修复。

神奇吧，大模型不仅给我们提供知识，还随时帮助分析并解决程序出错的信息。

## 重试解析器（RetryWithErrorOutputParser）实战

OutputFixingParser不错，但它只能做简单的格式修复。如果出错的不只是格式，比如，输出根本不完整，有缺失内容，那么仅仅根据输出和格式本身，是无法修复它的。

此时，通过实现输出解析器中parse\_with\_prompt方法，LangChain提供的重试解析器可以帮助我们利用大模型的推理能力根据原始提示找回相关信息。

我们通过分析一个重试解析器的用例来理解上面的这段话。

首先还是设计一个解析过程中的错误。

```plain
# 定义一个模板字符串，这个模板将用于生成提问
template = """Based on the user question, provide an Action and Action Input for what step should be taken.
{format_instructions}
Question: {query}
Response:"""

# 定义一个Pydantic数据格式，它描述了一个"行动"类及其属性
from pydantic import BaseModel, Field
class Action(BaseModel):
    action: str = Field(description="action to take")
    action_input: str = Field(description="input to the action")

# 使用Pydantic格式Action来初始化一个输出解析器
from langchain.output_parsers import PydanticOutputParser
parser = PydanticOutputParser(pydantic_object=Action)

# 定义一个提示模板，它将用于向模型提问
from langchain.prompts import PromptTemplate
prompt = PromptTemplate(
    template="Answer the user query.\n{format_instructions}\n{query}\n",
    input_variables=["query"],
    partial_variables={"format_instructions": parser.get_format_instructions()},
)
prompt_value = prompt.format_prompt(query="What are the colors of Orchid?")

# 定义一个错误格式的字符串
bad_response = '{"action": "search"}'
parser.parse(bad_response) # 如果直接解析，它会引发一个错误
```

由于bad\_response只提供了action字段，而没有提供action\_input字段，这与Action数据格式的预期不符，所以解析会失败。

我们首先尝试用OutputFixingParser来解决这个错误。

```plain
from langchain.output_parsers import OutputFixingParser
from langchain.chat_models import ChatOpenAI
fix_parser = OutputFixingParser.from_llm(parser=parser, llm=ChatOpenAI())
parse_result = fix_parser.parse(bad_response)
print('OutputFixingParser的parse结果:',parse_result)
```

OutputFixingParser的parse结果：`action='search' action_input='query'`

我们来看看这个尝试解决了什么问题，没解决什么问题。

**解决的问题有：**

- 不完整的数据：原始的bad\_response只提供了action字段而没有action\_input字段。OutputFixingParser已经填补了这个缺失，为action\_input字段提供了值 `'query'`。

**没解决的问题有：**

- 具体性：尽管OutputFixingParser为action\_input字段提供了默认值 `'query'`，但这并不具有描述性。真正的查询是 “Orchid（兰花）的颜色是什么？”。所以，这个修复只是提供了一个通用的值，并没有真正地回答用户的问题。
- 可能的误导：`'query'` 可能被误解为一个指示，要求进一步查询某些内容，而不是作为实际的查询输入。

当然，还有更鲁棒的选择，我们最后尝试一下RetryWithErrorOutputParser这个解析器。

```plain
# 初始化RetryWithErrorOutputParser，它会尝试再次提问来得到一个正确的输出
from langchain.output_parsers import RetryWithErrorOutputParser
from langchain.llms import OpenAI
retry_parser = RetryWithErrorOutputParser.from_llm(
    parser=parser, llm=OpenAI(temperature=0)
)
parse_result = retry_parser.parse_with_prompt(bad_response, prompt_value)
print('RetryWithErrorOutputParser的parse结果:',parse_result)
```

这个解析器没有让我们失望，成功地还原了格式，甚至也根据传入的原始提示，还原了action\_input字段的内容。

RetryWithErrorOutputParser的parse结果：`action='search' action_input='colors of Orchid'`

## 总结时刻

结构化解析器和Pydantic解析器都旨在从大型语言模型中获取格式化的输出。结构化解析器更适合简单的文本响应，而Pydantic解析器则提供了对复杂数据结构和类型的支持。选择哪种解析器取决于应用的具体需求和输出的复杂性。

自动修复解析器主要适用于纠正小的格式错误，它更加“被动”，仅在原始输出出现问题时进行修复。重试解析器则可以处理更复杂的问题，包括格式错误和内容缺失。它通过重新与模型交互，使得输出更加完整和符合预期。

在选择哪种解析器时，需要考虑具体的应用场景。如果仅面临格式问题，自动修复解析器可能足够；但如果输出的完整性和准确性至关重要，那么重试解析器可能是更好的选择。

## 思考题

1. 到目前为止，我们已经使用了哪些LangChain输出解析器？请你说一说它们的用法和异同。同时也请你尝试使用其他类型的输出解析器，并把代码与大家分享。
2. 为什么大模型能够返回JSON格式的数据，输出解析器用了什么魔法让大模型做到了这一点？
3. 自动修复解析器的“修复”功能具体来说是怎样实现的？请做debug，研究一下LangChain在调用大模型之前如何设计“提示”。
4. 重试解析器的原理是什么？它主要实现了解析器类的哪个可选方法？

题目较多，可以选择性思考，期待在留言区看到你的分享。如果你觉得内容对你有帮助，也欢迎分享给有需要的朋友！最后如果你学有余力，可以进一步学习下面的延伸阅读。

## 延伸阅读

1. 工具：[Pydantic](https://docs.pydantic.dev/latest/) 是一个Python库，用于数据验证，可以确保数据符合特定的格式
2. 文档：LangChain中的各种 [Output Parsers](https://python.langchain.com/docs/modules/model_io/output_parsers/)
<div><strong>精选留言（15）</strong></div><ul>
<li><span>在路上</span> 👍（23） 💬（1）<p>从源码上看，OutputFixingParser和RetryWithErrorOutputParser的本质是相同的，都是当PydanticOutputParser.parse(input)解析失败，通过语言模型分析抛出的异常，修正input。
不同之处在于，OutputFixingParser利用input schema、input、exception来修正input，RetryWithErrorOutputParser除了利用input schema、input、exception，还利用一个额外的prompt来修正input，有了额外的prompt，自然就能够既修正input格式，又补全input内容。</p>2023-09-20</li><br/><li><span>高源</span> 👍（10） 💬（2）<p>老师有个问题请教，例如目前大模型比较多，我的理解如果满足企业内部自己使用，是需要对大模型微调吧才能完全满足定制，例如输出企业自己相关数据，文档，代码等，而不是简单把提示写好弄个差不多开源大模型上去。我的理解是需要微调吧，针对自己企业数据进行训练对模型，但这块听老师课我理解需要对模型层次熟悉才能下手进行微调吧，我自己理解目前从效果上还是gpt其它模型还是比较弱，百度说他的2.0已经超过gpt3.5，比gpt4差点，我觉得没那么快吧，另外训练模型机器硬件人员等各种因素叠加，不是说都能做好了吧，企业自己落地自己模型这块现实吗，自己做需要那些条件，例如人员要求等，谢谢</p>2023-11-01</li><br/><li><span>棟</span> 👍（1） 💬（4）<p>老师，请教一个问题，
fix_parser或retry_parser中，如果错误的输出是json格式会报如下错误：
action_input
  Field required [type=missing, input_value={&#39;action&#39;: &#39;search&#39;}, input_type=dict]
    For further information visit https:&#47;&#47;errors.pydantic.dev&#47;2.3&#47;v&#47;missing

我是将错误bad_response = &#39;{&quot;action&quot;: &quot;search&quot;}&#39;  --&gt; 更改为bad_response = &quot;{&#39;action&#39;: &#39;search&#39;}&quot;才能正常调用模型，这个要怎么修复。
知道的朋友也请指点，感谢！</p>2023-10-07</li><br/><li><span>曹胖子</span> 👍（0） 💬（1）<p>parsed_output = output_parser.parse(output.content)   会报异常， 目前我尝试打印了 output的数据类型和结构，感觉是返回的数据结构出现的变动，最终我调整为 parsed_output = output_parser.parse(output.content) 后代码可执行。</p>2024-06-03</li><br/><li><span>风隼[咖啡]</span> 👍（0） 💬（1）<p>    # parsed_output_dict = parsed_output.dict()  # 将Pydantic格式转化位字典
    # Pydantic 格式转化为字典,Pydantic V2dict 方法已经被废弃，推荐使用 model_dump 方法来代替
    parsed_output_dict = parsed_output.model_dump()</p>2023-12-15</li><br/><li><span>rick009</span> 👍（0） 💬（1）<p>老师您好，有个问题请教一下，我想要从给定的一段文本中抽离一些FAQ，然后想返回JSON数组的格式，以下是prompt：
template = &quot;&quot;&quot;你是一名知识库管理员，需将以下内容拆分成 {nums} 个问答对，确保准确无误且只从文献中获取，不得扩散。你的算法或流程应该能够准确抽取关键信息，并生成准确的问答对，以充分利用文献。
    {doc_content}
    {format_instructions}  
    &quot;&quot;&quot;
想要返回的格式为
The output should be formatted as a JSON instance that conforms to the JSON schema below.\n\nAs an example, for the schema {&quot;properties&quot;: {&quot;foo&quot;: {&quot;title&quot;: &quot;Foo&quot;, &quot;description&quot;: &quot;a list of strings&quot;, &quot;type&quot;: &quot;array&quot;, &quot;items&quot;: {&quot;type&quot;: &quot;string&quot;}}}, &quot;required&quot;: [&quot;foo&quot;]}\nthe object {&quot;foo&quot;: [&quot;bar&quot;, &quot;baz&quot;]} is a well-formatted instance of the schema. The object {&quot;properties&quot;: {&quot;foo&quot;: [&quot;bar&quot;, &quot;baz&quot;]}} is not well-formatted.\n\nHere is the output schema:\n```\n{&quot;$defs&quot;: {&quot;QA&quot;: {&quot;properties&quot;: {&quot;Q&quot;: {&quot;description&quot;: &quot;\\u95ee\\u9898&quot;, &quot;title&quot;: &quot;Q&quot;, &quot;type&quot;: &quot;string&quot;}, &quot;A&quot;: {&quot;description&quot;: &quot;\\u7b54\\u6848&quot;, &quot;title&quot;: &quot;A&quot;, &quot;type&quot;: &quot;string&quot;}}, &quot;required&quot;: [&quot;Q&quot;, &quot;A&quot;], &quot;title&quot;: &quot;QA&quot;, &quot;type&quot;: &quot;object&quot;}}, &quot;items&quot;: {&quot;$ref&quot;: &quot;#&#47;$defs&#47;QA&quot;}}\n```
class QA(BaseModel):
    Q: str = Field(description=&quot;问题&quot;)
    A: str = Field(description=&quot;答案&quot;)

class QAList(RootModel):
    root: List[QA] = Field(description=&quot;FAQ问答对列表&quot;)
但是返回的格式总是不停的在变，都无法返回希望的数据结构</p>2023-12-06</li><br/><li><span>鲸鱼</span> 👍（0） 💬（1）<p>我遇到一个问题，目前的langchain必须使用v1版本的pydantic，如果使用了v2版本抛出的异常类型不对，会导致PydanticOutputParser无法捕获正常的ValidationError异常，从而不会去请求openAI修复response。
PydanticOutputParser的具体捕获代码是这里

class PydanticOutputParser(BaseOutputParser[T]):
    &quot;&quot;&quot;Parse an output using a pydantic model.&quot;&quot;&quot;

    pydantic_object: Type[T]
    &quot;&quot;&quot;The pydantic model to parse.&quot;&quot;&quot;

    def parse(self, text: str) -&gt; T:
        try:
            # Greedy search for 1st json candidate.
            match = re.search(
                r&quot;\{.*\}&quot;, text.strip(), re.MULTILINE | re.IGNORECASE | re.DOTALL
            )
            json_str = &quot;&quot;
            if match:
                json_str = match.group()
            json_object = json.loads(json_str, strict=False)
            return self.pydantic_object.parse_obj(json_object)

        except (json.JSONDecodeError, ValidationError) as e: # 这里只能捕获v1版本的ValidationError
            name = self.pydantic_object.__name__
            msg = f&quot;Failed to parse {name} from completion {text}. Got: {e}&quot;
            raise OutputParserException(msg, llm_output=text)
</p>2023-10-25</li><br/><li><span>在路上</span> 👍（0） 💬（1）<p>佳哥好，我发现在OutputFixingParser示例中，如果做如下修改：
new_parser = OutputFixingParser.from_llm(parser=parser, llm=ChatOpenAI(temperature=0))
或者
new_parser = OutputFixingParser.from_llm(parser=parser, llm=OpenAI(temperature=0))
可以得到稳定的输出：
name=&#39;康乃馨&#39; colors=[&#39;粉红色&#39;, &#39;白色&#39;, &#39;红色&#39;, &#39;紫色&#39;, &#39;黄色&#39;]
而不是：
name=&#39;Rose&#39; colors=[&#39;red&#39;, &#39;pink&#39;, &#39;white&#39;]</p>2023-09-20</li><br/><li><span>yanyu-xin</span> 👍（1） 💬（0）<p>重试解析器（RetryWithErrorOutputParser）实战学习，修改代码如下。注意：要设置max_retries=3，增加重试次数，解析成功率会极大提高
（1）原代码：
fix_parser = OutputFixingParser.from_llm(parser=parser, llm=ChatOpenAI())
新代码：
os.environ[&quot;BAICHUAN_API_KEY&quot;] =&quot;xxx&quot; # 请替换为你的百川模型 BAICHUAN API Key
from langchain_community.llms import BaichuanLLM
# 加载百川模型
llm = BaichuanLLM()
fix_parser = OutputFixingParser.from_llm(parser=parser, llm=llm, max_retries=3) # 使用百川模型，增加重试次数:3
（2）
原代码：
from langchain.llms import OpenAI
retry_parser = RetryWithErrorOutputParser.from_llm(
    parser=parser, llm=OpenAI(temperature=0)
)
新代码：
from langchain_community.llms import BaichuanLLM
# 初始化百川智能模型
baichuan_llm = BaichuanLLM()
# 初始化RetryWithErrorOutputParser，使用百川智能模型
retry_parser = RetryWithErrorOutputParser.from_llm(
    parser=parser, llm=baichuan_llm  , max_retries=3     # 使用百川模型
)</p>2024-07-27</li><br/><li><span>yanyu-xin</span> 👍（1） 💬（0）<p>继续使用国产大模型替代OpenAI进行代码学习。
在自动修复解析器（OutputFixingParser）实战中发现，使用通义千问模型调用时出错，无法解析。但是用百川智能模型能够正确解析。
使用百川模型修正代码如下：
原代码：
new_parser = OutputFixingParser.from_llm(parser=parser, llm=ChatOpenAI())
新代码：
os.environ[&quot;BAICHUAN_API_KEY&quot;] =&quot;xxx&quot; # 请替换为你的百川模型 BAICHUAN API Key
from langchain_community.llms import BaichuanLLM
llm = BaichuanLLM()  # 加载百川模型
new_parser = OutputFixingParser.from_llm(parser=parser, llm=llm, max_retries=3) # 增加重试次数:3</p>2024-07-27</li><br/><li><span>张申傲</span> 👍（1） 💬（0）<p>第7讲打卡~
再补充一个最简单的StrOutputParser字符串解析器，它将LLM的输出结果直接解析成字符串，在客服系统、聊天机器人等场景中使用得比较多。</p>2024-07-13</li><br/><li><span>LVEli</span> 👍（0） 💬（0）<p>老师，请问这里提到的List Parser。在实际使用中：list_parser = ListOutputParser()时，会提示类似这样的报错：这是一个静态类。。。如果不能使用这个输出解析器，是否还有其他方法能使agent执行后输出的string类型结果，转换成列表呢，谢谢~~</p>2025-01-17</li><br/><li><span>勤小码</span> 👍（0） 💬（0）<p>2024&#47;8 目前使 langchain==0.2.12，运行文中示例代码会抛异常。参考官方文档发现需要修改两处导入：

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.output_parsers import RetryOutputParser

具体内容见官方How-to文档
https:&#47;&#47;python.langchain.com&#47;v0.2&#47;docs&#47;how_to&#47;output_parser_retry&#47;

langchain 目前更新比较快，各种API也不稳定，容易出现各种意想不到的问题。本示例异常原因后续再debug详细看看。
</p>2024-08-14</li><br/><li><span>核桃爸爸</span> 👍（0） 💬（0）<p>2024年7月24日，最新版本的 langchain 库无法运行成功</p>2024-07-24</li><br/><li><span>chenyang</span> 👍（0） 💬（0）<p>老师你好，
02_OutputFixParser.py 和 03_RetryParser.py 运行时，都会报
KeyError: &quot;Input to PromptTemplate is missing variables {&#39;completion&#39;}.  Expected: [&#39;completion&#39;, &#39;error&#39;, &#39;instructions&#39;] Received: [&#39;instructions&#39;, &#39;input&#39;, &#39;error&#39;]&quot;
请问是什么原因呀</p>2024-07-10</li><br/>
</ul>