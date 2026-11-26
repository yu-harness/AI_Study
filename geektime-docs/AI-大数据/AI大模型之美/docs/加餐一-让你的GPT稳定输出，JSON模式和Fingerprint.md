你好，我是徐文浩。

过去一年，是整个AI领域风驰电掣的一年。希望「AI大模型之美」这门课程，让你对大模型领域有了一个完整的认识。而随着AI大模型领域的进一步发展，无论是OpenAI开放的API能力，还是开源领域百花齐放的各种模型，都有了长足的进步和发展。

所以，在这新的一年里，我会对「AI大模型之美」这门课程做一个更新。一方面，是查漏补缺，修订一下已经上线的内容。因为无论是OpenAI提供的GPT，还是llama-index和LangChain这样的开源项目，在API上都发生了很大的变化。另一方面，则是提供一些更深入的内容，因为OpenAI和百花齐放的开源领域，都提供更丰富的AI能力，让我们开发AI的应用更加方便了。

## 废弃Completions接口，使用Chat Completions接口

在这个课程一开始的时候，我就以一个给跨境电商的商品写标题的例子向你展示了 GPT-3.5 模型的能力。

```python
from openai import OpenAI
import os

client = OpenAI(
  api_key=os.environ['OPENAI_API_KEY'],
)
COMPLETION_MODEL = "text-davinci-003"

prompt = """
Consideration proudct : 工厂现货PVC充气青蛙夜市地摊热卖充气玩具发光蛙儿童水上玩具

1. Compose human readale product title used on Amazon in english within 20 words.
2. Write 5 selling points for the products in Amazon.
3. Evaluate a price range for this product in U.S.

Output the result in json format with three properties called title, selling_points and price_range
"""

def get_response(prompt, model=COMPLETION_MODEL):
    completions = client.completions.create (
        model=COMPLETION_MODEL,
        prompt=prompt,
        max_tokens=512,
        n=1,
        stop=None,
        temperature=0.0,        
    )
    message = completions.choices[0].text
    return message

print(get_response(prompt)) 
```

输出结果：

```python
NotFoundError: Error code: 404 - {'error': {'message': 'The model `text-davinci-003` has been deprecated, learn more here: https://platform.openai.com/docs/deprecations', 'type': 'invalid_request_error', 'param': None, 'code': 'model_not_found'}}
```

不过如果你今天尝试运行这段代码，只会收到一个报错。这是因为OpenAI已经将这个例子里的 text-davinci-003 模型废弃了。现在如果你还是想要获得相同的返回结果，需要替换成 gpt-3.5-turbo-instruct 这个模型。

```python
NEW_MODEL = "gpt-3.5-turbo-instruct"

print(get_response(prompt, model=NEW_MODEL)) 
```

输出结果：

```python
 {
  "title": "Factory Stock PVC Inflatable Frog, Hot Selling Night Market Stall Toy with Light for Children's Water Play",
  "selling_points": [
    "Made with high quality PVC material",
    "Inflatable and easy to store",
    "Attractive design with glowing feature",
    "Perfect for water play and night markets",
    "Available in stock for immediate purchase"
  ],
  "price_range": "$15 - $25"
}
```

好在 gpt-3.5-turbo-instruct 这个模型的价格要比 text-davinci-003 低上不少，所以更换成这个新模型对用户来说还是划得来的。毕竟，你只需要修改一下模型名称，原来的代码就能继续跑起来了。

![图片](https://static001.geekbang.org/resource/image/a8/3e/a8a316694a0d7fde4d37d4459549043e.png?wh=1580x364 "在 OpenAI 的官方文档可以看到，Completions API 已经打上了 Legacy 的标记")

不过，如果你想写一些新功能和新代码，我建议你不要再使用上面的Completions API了，因为这一系列的API已经被OpenAI打上了“Legacy”的标记。而且，OpenAI也没有为 GPT-4 这个最强大模型，提供 Completions API。

如果今天你想要实现让GPT给你写文案和标题的能力，我推荐你使用Chat Completions接口，你只需要把你的指令需求替换成一个用户通过chat对话向AI发出请求的方式就可以了，非常简单。

```python
from openai import OpenAI
import os

client = OpenAI(
  api_key=os.environ['OPENAI_API_KEY'],
)
CHAT_COMPLETION_MODEL = "gpt-3.5-turbo"

prompt = """
Consideration proudct : 工厂现货PVC充气青蛙夜市地摊热卖充气玩具发光蛙儿童水上玩具

1. Compose human readale product title used on Amazon in english within 20 words.
2. Write 5 selling points for the products in Amazon.
3. Evaluate a price range for this product in U.S.

Output the result in json format with three properties called title, selling_points and price_range
"""

def get_chat_response(prompt, model=CHAT_COMPLETION_MODEL):
    messages = [
        {"role" : "system", "content" : "You are an useful AI asssitant."},
        {"role" : "user", "content": prompt}
    ]
    response = client.chat.completions.create (
        model=model,
        messages=messages,
        max_tokens=512,
        n=1,
        stop=None,
        temperature=0.7,        
    )
    message = response.choices[0].message.content
    return message

print(get_chat_response(prompt)) 
```

输出结果：

```python
{
  "title": "Factory Stock PVC Inflatable Frog Night Market Hot Selling Light-up Frog Children's Water Toy",
  "selling_points": [
    "High-quality PVC material for durability",
    "Inflatable design for easy storage and transportation",
    "Glowing feature adds fun to nighttime play",
    "Suitable for both kids and adults",
    "Perfect for water play at the pool or beach"
  ],
  "price_range": "$10 - $20"
}
```

可以看到，这个代码和我们使用 Completions API 的代码基本是一样的，我们只是做了三个小小的改动。

1. 将代码接口从 client.completions.create 更换成了 client.chat.completions.create。
2. 不再是直接提供一个prompt参数，而是需要将你的prompt封装成system和user的message。
3. 解析的返回结果的格式也有了小小的变动，拿到的是包含 role 和 content 的 message，而不是原来那样的 text。

## 使用JSON模式获得稳定输出

在这个例子中，我们让AI为我们输出一个JSON格式的回复。这也是大量AI辅助应用场景下，我们经常会提出的需求。因为一旦输出结果是JSON格式，就意味着我们可以很容易地用程序来解析返回的结果，也就不需要手工去分段复制粘贴AI返回的内容了，可以**批量且自动化地**完成相应的任务。

生成式AI（GenAI）虽然非常聪明，能够理解你提出的要求，也能给出聪明而且正确的返回结果。但是，它也有一个小小的缺点，就是**输出结果有时候并不是那么可控**。比如，我们用更加像人类对话的方式提出我们的需求，就会遇到这样的问题。

```python
prompt = """
Hi,

Could you write me a title, 5 selling points, and a price range for a product called "工厂现货PVC充气青蛙夜市地摊热卖充气玩具发光蛙儿童水上玩具" in English in json format?
"""

print(get_chat_response(prompt)) 
```

输出结果：

````python
Certainly! Here's the information you requested in JSON format:
```json
{
  "title": "Factory Stock PVC Inflatable Frog Night Market Bestseller Inflatable Toy with LED Lights for Children's Water Play",
  "sellingPoints": [
    "High-quality PVC material",
    "Inflatable and portable design",
    "Attractive LED lights for night play",
    "Suitable for water activities",
    "Popular choice at night markets"
  ],
  "priceRange": "$10 - $20"
}

Please note that the translation provided is based on the given product name, and the price range is presented as an estimate.
````

上面这段代码里，我们并没有修改任何需求的逻辑，只是把提出的要求变得更加口语化了一点。但是在输出的结果中，AI给出了一些我们并不需要的冗余信息。除了原本我们希望得到的JSON格式的内容之外，AI还在JSON的前后，给了一些模仿人类对话的介绍和贴心的建议。

然而，如果我们是通过一段程序来自动解析输出的JSON，这样的返回结果反而变得更麻烦了。当遇到这种情况的时候，要么调整我们的提示语（Prompt），然后寄希望于输出结果里只有一个干净的JSON字符串。或者，我们提供一个考虑到可能存在各种脏数据的JSON解析函数，在解析JSON之前，剔除掉前后无关的文本内容。但是这两种方法，其实都不太稳定。前者，可能需要你花费很多时间去调整Prompt，后者，则总会遇到一些你意想不到的脏数据，导致在有些场景下解析失败。

不过，OpenAI显然是已经考虑到了这个问题。毕竟，让ChatGPT的接口返回一些格式化好的数据，然后把后续流程交给代码来处理，是目前应用AI最常见的一种组合。所以，现在你可以在调用 Chat Completions 接口的时候，就指定输出 JSON 格式。一旦你指定了输出格式是JSON，对应的Chat Completions的接口返回的内容就只有JSON，你就不再需要操心微调提示语，或者兼容各种脏数据输出的情况了。你可以按照下面这样来修改你的代码。

```python
CHAT_COMPLETION_MODEL = "gpt-3.5-turbo-0125"
def get_json_response(prompt, model=CHAT_COMPLETION_MODEL):
    messages = [
        {"role" : "system", "content" : "You are an useful AI asssitant."},
        {"role" : "user", "content": prompt}
    ]
    response = client.chat.completions.create (
        model=model,
        messages=messages,
        max_tokens=512,
        n=1,
        stop=None,
        temperature=0.7, 
        response_format={ "type": "json_object" },      
    )
    message = response.choices[0].message.content
    return message

prompt = """
Hi,

Could you write me a title, 5 selling points, and a price range for a product called "工厂现货PVC充气青蛙夜市地摊热卖充气玩具发光蛙儿童水上玩具" in English in json format?

The json format should be like this:

{
    "title": "Blablabla",
    "selling_points": [
        "Blablabla",
        "Blablabla",
        "Blablabla",
        "Blablabla",
        "Blablabla"
    ],
    "price_range": "$x.00 - $y.00"
}

"""

print(get_json_response(prompt)) 
```

输出结果：

```python
{
    "title": "Factory Stock PVC Inflatable Frog Night Market Stall Hot Selling Light-Up Frog Children's Water Toy",
    "selling_points": [
        "Inflatable frog toy for children",
        "Glow in the dark feature for added fun",
        "Perfect for water play activities",
        "Ideal for night markets and stalls",
        "High-quality PVC material for durability"
    ],
    "price_range": "$10.00 - $20.00"
}
```

1. 首先，只有在使用 **gpt-4-turbo-preview** 或者 **gpt-3.5-turbo-0125** 这两个模型的时候，OpenAI的API才支持指定JSON作为输出格式。所以你要先把使用的模型换成这两个模型中的一个。
2. 然后，你只需要在Chat Completions接口中，增加一个参数，指定 response\_format={ “type”: “json\_object” } 就好了。
3. 除了这两处修改之外，为了确保输出的JSON格式和你期望的一样。我建议你在原来的Prompt的最后，再给出一个你期望的JSON格式的例子。这个小技巧有助于最终输出的JSON格式和你期望的一样，确保后续程序的解析成功。如果对比一下这里给出了JSON格式例子代码的输出结果和上面没有给例子的输出结果，你会发现，JSON中对应价格区间的字段 **price\_range** 的输出格式，一个是用了下划线 **\_** 作为单词之间的分割，而另一个则是用了驼峰格式的 **priceRange**。如果你的解析代码中，希望使用 **price\_range**，那么在原来的输出结果里是获取不到的。

## 使用seed参数和Fingerprint

无论是指定JSON作为输出的数据格式，还是进一步地提供了对应JSON格式的示例，我们都是为了确保AI模型的输出结果是稳定的。不过，虽然输出的数据格式稳定了，但是如果你反复运行几次上面的代码，你会发现它输出的内容每次都会发生变化。

```python
{
    "title": "Factory Stock PVC Inflatable Frog Night Market Stall Hot Selling Inflatable Toy Glowing Frog Children's Water Toy",
    "selling_points": [
        "Made of high-quality PVC material",
        "Unique design with glowing feature",
        "Perfect for children's water play",
        "Ideal for night market stalls",
        "Limited stock available"
    ],
    "price_range": "$15.00 - $25.00"
}
```

注：如果再次运行代码，输出的JSON内容是不同的。

但是，在有些场景下，我们不仅希望输出的格式是稳定的，我们还希望在输入内容一样的情况下，输出的结果也不要发生变化。比如，我在撰写这个课程的例子的时候，我希望提供的示例代码，每次的输出结果都是一样的。这样，方便你验证自己实验的结果。你可能会说，那是不是把 temperature 这个参数设置成0就可以了? 因为我们之前就介绍过，这个参数决定了模型生成文本时的随机性。

你不妨可以试一试，结果其实并非如此。Temperature作为一个参数，其实是决定了我们在AI大模型生成下一个Token的候选列表的时候，高概率的Token被选中的概率的分布是更大还是更小。即使Temperature设置成0，也并不意味着模型的输出是一样的。

```python
def get_fingerprint_response(prompt, seed=42, model=CHAT_COMPLETION_MODEL):
    messages = [
        {"role" : "system", "content" : "You are an useful AI asssitant."},
        {"role" : "user", "content": prompt}
    ]
    response = client.chat.completions.create (
        model=model,
        messages=messages,
        max_tokens=512,
        n=1,
        stop=None,
        seed=seed,
        temperature=0, 
        response_format={ "type": "json_object" },      
    )
    message = response.choices[0].message.content
    fingerpring = response.system_fingerprint
    return fingerpring, message

fingerprint , json_response = get_fingerprint_response(prompt,seed=1)
print(fingerprint)
print(json_response)
```

输出结果：

```python
fp_69829325d0
{
    "title": "Factory Stock PVC Inflatable Frog Night Market Stall Hot Selling Inflatable Toy Glowing Frog Children's Water Toy",
    "selling_points": [
        "Made of high-quality PVC material",
        "Unique design with glowing feature",
        "Perfect for children to play with in the water",
        "Ideal for night markets and outdoor events",
        "Easy to inflate and deflate for storage"
    ],
    "price_range": "$10.00 - $20.00"
}
```

换一个seed调一次：

```python
fingerprint , json_response = get_fingerprint_response(prompt,seed=2)
print(fingerprint)
print(json_response)
```

输出结果：

```python
fp_69829325d0
{
    "title": "Factory Stock PVC Inflatable Frog Night Market Stall Hot Selling Inflatable Toy Glowing Frog Children's Water Toy",
    "selling_points": [
        "Made of high-quality PVC material",
        "Suitable for night markets and stalls",
        "Glowing feature adds fun for children",
        "Ideal for water play",
        "Popular and in-demand product"
    ],
    "price_range": "$10.00 - $20.00"
}
```

通过这个例子可以看到，尽管temperature已经设置成了0，但是不同 seed 输出的结果还是不同的。

为了尽可能地确保每次的输出结果一样，你还需要指定一个seed参数。这个seed参数是一个随机数的种子。如果你指定了相同的seed参数，把temperature设置成0，并且确保调用模型的其他参数和提示语完全一致。那么，OpenAI的输出结果，就会**尽可能地一致。**

我们把seed设置成12345运行一次：

```python
fingerprint , json_response_1 = get_fingerprint_response(prompt,seed=12345)
print(fingerprint)
print(json_response_1)
```

输出结果：

```python
fp_69829325d0
{
    "title": "Factory Stock PVC Inflatable Frog Night Market Stall Hot Selling Inflatable Toy Glowing Frog Children's Water Toy",
    "selling_points": [
        "Made of high-quality PVC material",
        "Unique design with glowing feature",
        "Perfect for children to play with in the water",
        "Ideal for night markets and outdoor events",
        "Easy to inflate and deflate for storage"
    ],
    "price_range": "$10.00 - $20.00"
}
```

再运行一次：

```python
fingerprint , json_response_2 = get_fingerprint_response(prompt,seed=12345)
print(fingerprint)
print(json_response_2)
```

输出结果：

```python
fp_69829325d0
{
    "title": "Factory Stock PVC Inflatable Frog Night Market Stall Hot Selling Inflatable Toy Glowing Frog Children's Water Toy",
    "selling_points": [
        "Made of high-quality PVC material",
        "Unique design with glowing feature",
        "Perfect for children to play with in the water",
        "Ideal for night markets and outdoor events",
        "Easy to inflate and deflate for storage"
    ],
    "price_range": "$10.00 - $20.00"
}
```

再来对比一下输出的结果：

```python
print(json_response_1 == json_response_2)
```

输出结果一致。

```python
True
```

我在这使用了相同的提示语、模型的配置参数，在seed参数相同和不同这两种情况下，运行了程序。可以看到，即使我们已经把temperature设置成0，seed参数不同的情况下，输出结果也并不完全相同。而当我们把seed都设置成了12345之后，输出的结果就完全一致了。**不过，需要注意，OpenAI在官方文档中，也申明了即使seed一致，它也只是尽可能保障输出结果是一致的，而没有打上100%的保票。**

如果你希望通过相同的seed参数来保障输出结果是可以反复重现（Reproducible）的，我也推荐你和我一样，把输出结果中的 **system\_fingerprint** 参数单拎出来。这个参数，是针对你调用模型的各个参数组合的指纹，如果这个值在两次AI模型调用中不一样，就意味着你一定有一些参数在两次调用中是不同的。这个时候，输出的结果不一致是正常现象，并不能说明你的seed参数不一样。

## 小结

好了，这就是这一讲的主要内容，最后我们来回顾一下。这一讲主要是为了教会你如何让OpenAI的模型**稳定输出**。为了让模型的输出结果一直是一个干净的JSON文件，你需要选用 **gpt-4-turbo-preview** 或者 **gpt-3.5-turbo-0125** 这两个模型中的一个，并且在参数中设定返回结果是 JSON Mode。为了确保输出的JSON的参数和你计划的一样，你需要在提示语中给出你期望的JSON示例。

如果你不仅希望输出的格式是稳定的，连输出的内容也是可复现的，相同的输入总能得到相同的输出结果，要怎么办呢？一方面你要将 temperature 参数设置成0，另一方面在每次调用模型的时候，需要将 seed 这个随机数种子设置成相同的值。你学会了吗？

## 课后练习

除了对比输出的内容之外，我们还可以通过 embedding 计算两个输出结果之间的距离，来看它们是否是一致的。在OpenAI的Cookbook里，也有对应的[示例](https://cookbook.openai.com/examples/reproducible_outputs_with_the_seed_parameter)。你能试着使用这个方式，看看不同seed和相同seed的返回结果之间的距离是怎么样的吗？

欢迎你把你试验的成果分享到评论区，也欢迎你把这节课的内容分享给需要的朋友，我们下节课再见！
<div><strong>精选留言（3）</strong></div><ul>
<li><span>王平</span> 👍（1） 💬（1）<p>老师如果需要输出是一种自定义的数据结构，有什么好的方法吗？</p>2024-02-22</li><br/><li><span>HXL</span> 👍（0） 💬（0）<p>老师 您好 ! 最近遇到个问题 调用openai的接口 发现一直超时不知道是啥原因 ? 

&quot;cause: FetchError: request to https:&#47;&#47;api.openai.com&#47;v1&#47;chat&#47;completions failed, reason:&quot;</p>2024-04-11</li><br/><li><span>Toni</span> 👍（0） 💬（0）<p>试了一下，以期得到每次输出的结果都完全一样，这是概率模型输出的难点。
调用的参数是 temperature=0.0, seed=12345, 相同的 fingerprint。试了多次，一致性达到前4个卖点都相同已是我得到的最佳结果。

结果1:
fp_2b778c6b35
{
    &quot;title&quot;: &quot;Inflatable Frog Night Market Hot Selling Toy with LED for Kids&quot;,
    &quot;selling_points&quot;: [
        &quot;工厂现货，质量可靠&quot;,
        &quot;可充气，易携带&quot;,
        &quot;发光设计，吸引眼球&quot;,
        &quot;适合水上玩耍，增加乐趣&quot;,
        &quot;可作为地摊销售，商机多&quot;
    ],
    &quot;price_range&quot;: &quot;$10 - $20&quot;
}

结果2:
fp_2b778c6b35
{
    &quot;title&quot;: &quot;Inflatable Frog Night Market Hot Selling Toy with LED for Kids&quot;,
    &quot;selling_points&quot;: [
        &quot;工厂现货，质量可靠&quot;,
        &quot;可充气，易携带&quot;,
        &quot;发光设计，吸引眼球&quot;,
        &quot;适合水上玩耍，增加乐趣&quot;,
        &quot;可用于夜市地摊销售&quot;
    ],
    &quot;price_range&quot;: &quot;$10 - $20&quot;
}

用英文输出，一致性也无明显提高。
在本例中，提示词中要求给出相关商品的5个卖点，输出结果保持完全一致对概率模型而言并不容易，当然在本示例中也无必要，但它却提供一个很好的观察点。</p>2024-03-03</li><br/>
</ul>