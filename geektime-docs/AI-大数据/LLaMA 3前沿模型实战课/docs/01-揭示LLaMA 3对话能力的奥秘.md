你好，我是Tyler。今天我们正式开始学习LLaMA 3的能力模型。

过去的一年中，大模型技术得到了广泛认可，全行业对大模型的投入也在不断增加。开源社区涌现了许多优秀的模型和框架，推动了大模型技术的普及和应用。在这一年的时间里，LLaMA 系列模型也经历了快速的发展，从 LLaMA 2 到 LLaMA 3，我们看到了性能和应用上的显著提升。

本季专栏中，我将采用“Learn by doing”的方法，通过简洁的示例，深入剖析大模型技术的本质。我们将探讨LLaMA 3的能力模型，详细解析大模型技术的各个方面，并深入到你在使用LLaMA 3过程中会遇到的各种细节。

在第一讲中，我将详细介绍LLaMA 3模型的核心能力——对话生成，并展示它在文本生成方面的强大潜力。

## 基本操作：生成内容

首先，让我们来了解一下LLaMA 3的核心能力。LLaMA 3主要依赖于Next Token Prediction（下一个词预测）机制，通过预测下一个词来生成连贯的对话。这种机制基于海量文本数据的训练，使模型能够捕捉语言的模式和规律，生成符合上下文逻辑的文本内容。

### Next Token Prediction

Next Token Prediction是大语言模型生成文本的基础。模型处理输入文本的步骤如下：

1. **标记化：**首先，大模型将输入文本分解成一系列的 token（词或子词）。例如，句子“请解释一下黑洞的形成”可能被分解为以下 token：

```plain
["请", "解释", "一", "下", "黑", "洞", "的", "形", "成"]
```

2. **文字表征：**接下来，将这些 token 转换为模型能够理解的数值形式（通常是嵌入向量）。
3. **概率预测：**大模型会根据当前的输入序列计算下一个词的概率分布。这些概率分布表示下一个词的可能性，例如：

```plain
{"黑洞": 0.1, "形成": 0.05, "是": 0.2, "由于": 0.15, ...}
```

4. **生成文本：**根据概率分布选择具体的一个词作为下一个词。选择方式可以是贪婪搜索（选择概率最大的词）、随机采样（根据概率分布随机选择）或其他搜索策略（比如Beam Search）。例如，使用贪婪搜索选择概率最大的词“是”，并将其添加到已生成的文本序列中，重复上述步骤。

```plain
[“请”, “解释”, “一”, “下”, “黑”, “洞”, “的”, “形”, “成”, “是”]。
```

因此，LLaMA 3模型的推理过程是一个循环：通过预测下一个词，将其加入到序列中，再预测下一个词来生成连贯的文本。这种循环造成了大量的模型推理算力开销，这也是为什么OpenAI等公司在API使用中根据Token计费。

接下来，我们通过一个具体的代码示例来演示LLaMA 3的文本生成过程。假设我们有一个文章开头：

> 在一个阳光明媚的早晨，Alice决定去森林里探险。她走着走着，突然发现了一条小路。

我们使用LLaMA 3来续写这段话：

```python
import torch
from modelscope import snapshot_download
from transformers import AutoModelForCausalLM, AutoTokenizer

# 下载模型
cache_dir = './llama_cache'
model_id = snapshot_download("LLM-Research/Meta-Llama-3-8B", cache_dir=cache_dir)
```

```python
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# 加载分词器和模型
cache_dir = './llama_cache'
model_path = cache_dir + '/LLM-Research/Meta-Llama-3-8B'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    device_map="auto" if torch.cuda.is_available() else None
)

# 编码输入并将其移至模型设备
input_text = "在一个阳光明媚的早晨，Alice决定去森林里探险。她走着走着，突然发现了一条小路。"
inputs = tokenizer(input_text, return_tensors="pt").to(model.device)

# 生成并解码文本
with torch.no_grad():
    outputs = model.generate(**inputs)
generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(generated_text)
```

输出结果：

> 这条小路被两旁茂密的树木掩映着，似乎通向森林深处。Alice决定沿着小路前进，想看看尽头有什么惊喜等着她。

在这个例子中，LLaMA 3 成功地续写了文章内容，我们可以看到 LLaMA 3 流畅地生成了具有创意性的内容，这个生成的过程就是刚刚提到的 Next Token Prediction 循环所形成的。

### 停止条件

你可能会问，Next Token Prediction 的方式岂不是会一直输出内容不停止？很好的问题！现在我们来聊聊LLaMA 3 **停止输出的条件**，LLaMA 3 的输出由以下几个因素控制：

- **最大长度（max\_length）：**这是最常用的控制方式之一。在初始化模型时，你可以指定一个最大长度值。当模型生成的文本长度达到该值时，它就会停止输出。

例如，如果将最大长度设置为100，那么模型生成的文本最长不会超过100个词。

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

cache_dir = './llama_cache'
model_path = cache_dir + '/LLM-Research/Meta-Llama-3-8B'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    device_map="auto" if torch.cuda.is_available() else None
)

max_length = 50
input_text = "写一首关于爱情的诗"
encoded_input = tokenizer(input_text, return_tensors="pt")
output = model.generate(encoded_input.input_ids, max_length=max_length)
print(tokenizer.decode(output[0], skip_special_tokens=True))
```

- **其他停止条件：**一些模型还支持其他停止条件。例如检测到重复的文本、低质量的文本等。

LLaMA 3 可以检测到重复的文本并将其跳过。

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

cache_dir = './llama_cache'
model_path = cache_dir + '/LLM-Research/Meta-Llama-3-8B'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    device_map="auto" if torch.cuda.is_available() else None
)

repetition_penalty = 1.2
input_text = "写一首关于爱情的诗："
encoded_input = tokenizer(input_text, return_tensors="pt")
output = model.generate(encoded_input.input_ids, repetition_penalty=repetition_penalty)
print(tokenizer.decode(output[0], skip_special_tokens=True))
```

这些停止条件确保模型生成的文本不会无限延长，可以通过设置不同的参数来控制生成过程。

## 无状态到有状态：对话能力

对话生成不仅需要理解上下文，还得保持连贯性。**因此，我们首先要解决的问题，就是大模型服务“无状态”的问题。**为了让“无状态”的LLaMA 3模型具备对话能力，我们可以将先前的“历史会话”作为当前输入的一部分。这样可以保持上下文的连贯性，使模型成为一个“有状态”的服务，从而准确地生成响应。

以下是实现这一功能的代码示例：

```python
import torch
from modelscope import snapshot_download
from transformers import AutoModelForCausalLM, AutoTokenizer

# 下载模型
cache_dir = './llama_cache'
model_id = snapshot_download("LLM-Research/Meta-Llama-3-8B-Instruct", cache_dir=cache_dir)
```

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

cache_dir = './llama_cache'
model_path = cache_dir + '/LLM-Research/Meta-Llama-3-8B-Instruct'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    device_map="auto" if torch.cuda.is_available() else None
)

# 初始化对话历史
dialogue_history = [
    "Customer: Hi, I have an issue with my order.",
    "Support: Sure, could you please provide your order number?",
    "Customer: Sure, it's #12345.",
    "Support: Thank you. Let me check the status for you.",
]

# 合并对话历史为一个字符串
dialogue_history_text = "\n".join(dialogue_history)

# 添加用户输入，模拟当前对话
user_input = "Customer: Can you please expedite the delivery?"
input_text = dialogue_history_text + "\n" + user_input

# 生成文本
input_ids = tokenizer.encode(input_text, return_tensors="pt")
outputs = model.generate(input_ids, max_length=100)
generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

print("Generated Response:", generated_text)

```

这段代码演示了如何使用 LLaMA 3 模型生成对话响应。

首先，我们定义了模型和 tokenizer，并初始化了一个简单的对话历史列表。然后，将对话历史转换为单个字符串，并添加用户的当前输入。接下来，我们使用 tokenizer 对输入进行编码，然后通过模型生成响应文本。最后，解码生成的文本并打印出来。

**这里为你带来这节课的第一个重点**，你可能会发现，上面的示例使用了基础版模型，而下面的示例使用了 Instruct 版本的模型。这是为什么呢？这是因为这两个模型的目标不一样，为了服务不同的角色，每个版本 LLaMA 3 模型在训练数据和训练方法上有所不同，针对特定对象进行了微调，比如：

- 人类用户：通过指令微调，使模型更好地理解和响应人类指令。这种微调使模型能够处理更自然的语言输入，提供更准确和相关的回答。
- 检索系统：结合检索系统的微调方法，提升模型在特定领域的信息检索能力。通过实时检索最新的外部数据，模型可以提供更加准确和时效性强的回答。
- 智能体（多步推理）：模型之间的协作与交互，通过互相微调提升整体智能水平。不同模型可以相互补充，共同完成复杂的任务，从而提高整体性能。

此外，选择不同版本的 LLaMA 3 模型还需要考虑多个维度。

- 场景数据：根据不同应用场景选择合适的指令微调数据，如语言、行业、文化等。不同领域的数据特点和需求不同，需要针对性地进行模型微调。
- 输入长度：不同版本的模型在输入长度上有所差异，我们需要根据具体应用需求选择适合的模型版本。一些应用场景可能需要处理较长的输入文本，因此选择支持较长输入的模型版本是必要的。
- 参数效率：通过微调降低模型的参数要求，例如使用更小的模型架构或优化算法。在资源有限的环境中，可以优化模型性能以满足需求。通过合理的参数配置，可以在性能和资源消耗之间找到平衡点。
- 量化程度：不同量化程度带来不同的性能提升和效果下降，需要在性能和效果之间找到平衡点。量化可以减少模型的计算和存储需求，但也可能影响生成效果，因此需要根据具体应用情况进行权衡。

这些考虑因素在选择和使用 LLaMA 3 模型时至关重要。随着后面课程的深入，我们将在示例中不断展开这些内容。

在解决了大模型的“无状态“问题之后，我们再来看另一个大模型的局限性，那就是**训练数据时效性的问题。**

## 封闭到开放：检索增强

在某些情况下，我们需要 LLaMA 3 训练后产生的最新事实。为了解决这个问题，我们可以结合检索系统，在生成过程中获取最新或特定领域的事实信息。

**为了解决 LLaMA 3 无法提供最新的事实信息的问题**，我们需要用到检索增强生成（RAG）方法。简单来说，RAG 就是结合外部知识库或 API 进行实时检索，并将检索到的内容通过提示语补充到模型的输入中。

这种方法可以显著提高生成内容的准确性和时效性。例如，在对话过程中调用外部知识库，增强回答的准确性。以下是一个常见的示例实现步骤：

1. 定义检索机制：首先，我们需要选择一个适当的外部知识库或 API，用于实时检索最新的事实信息。常见的选择包括搜索引擎 API、新闻 API、专门的行业知识库等。
2. 集成检索系统：将外部检索系统集成到 LLaMA 3 的生成流程中。当模型生成初步响应后，调用检索系统获取最新的相关信息，并将检索到的信息整合到最终的响应中。
3. 更新生成内容：利用检索到的最新信息，更新和完善模型的初步生成内容，确保回答的准确性和时效性。

相应的，以下是一个简单的代码示例，演示如何在生成过程中集成外部知识库进行实时检索和信息更新。

1. 定义检索机制：在 retrieve\_information 函数中，我们使用搜索引擎API根据给定的查询关键词检索最新的信息。
2. 集成检索系统：在 generate\_response 函数中，首先使用 LLaMA 3 生成初步响应，然后提取生成文本中的关键词，通过 retrieve\_information 函数获取相关的最新信息。
3. 更新生成内容：将检索到的信息整合到最终的响应中，生成更为准确和时效性的回答。

```python
import requests
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from googleapiclient.discovery import build

cache_dir = './llama_cache'
model_path = cache_dir + '/LLM-Research/Meta-Llama-3-8B-Instruct'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
    device_map="auto" if torch.cuda.is_available() else None
)

# Google Custom Search API配置
API_KEY = 'YOUR_GOOGLE_API_KEY'
SEARCH_ENGINE_ID = 'YOUR_SEARCH_ENGINE_ID'

# 检索相关文档的函数
def retrieve_documents(query):
    try:
        service = build("customsearch", "v1", developerKey=API_KEY)
        res = service.cse().list(q=query, cx=SEARCH_ENGINE_ID).execute()
        results = res.get('items', [])
        documents = [item["snippet"] for item in results]
        return documents
    except Exception as e:
        print(f"Error retrieving documents: {e}")
        return []

# 生成答案的函数
def generate_answer(query, documents):
    # 限制检索到的文档数量
    documents = documents[:3]
    context = "\n\n".join(documents) + "\n\nQuestion: " + query + "\nAnswer:"
    # 编码输入
    inputs = tokenizer(context, return_tensors="pt", truncation=True, max_length=2048).to(model.device)
    # 生成答案
    outputs = model.generate(**inputs, max_length=512)
    # 解码答案
    answer = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return answer

# 主函数
def main():
    query = "What is the capital of France?"
    documents = retrieve_documents(query)
    if documents:
        answer = generate_answer(query, documents)
        print("Question:", query)
        print("Answer:", answer)
    else:
        print("No documents retrieved.")

if __name__ == "__main__":
    main()

```

> Question: What is the capital of France?  
> Answer: The capital of France is Paris. It is known for its art, fashion, and culture, and is home to famous landmarks such as the Eiffel Tower and the Louvre Museum.

通过结合外部知识库或 API 进行实时检索和信息更新，我们可以有效解决 LLaMA 3 在生成过程中无法获取最新事实的问题。这种方法不仅提高了回答的准确性，还确保了内容的时效性。在后续课程中，我们将进一步探讨如何使用向量数据和混合检索及重排技术，来构建一个定制化的 RAG 引擎。

在对话生成的基础上，我们可以进一步探索多智能体架构。多智能体系统可以分担复杂任务，通过不同的智能体协同工作，提供更专业、更高效的服务。

## 单体服务到微服务：多智能体

在单步推理方面，LLaMA 3 存在一定的局限性，例如长对话和职责混乱可能会影响模型的推理性能。针对这些问题，多智能体架构提供了一些优化策略。多智能体系统（MAS）通过将多个智能体组织起来协同工作，实现复杂任务的解决。

每个智能体都有特定的角色和功能，通过相互之间的通信和协作来达成共同目标。在LLaMA 3的应用中，我们可以利用多智能体系统的以下优点：

- **拆分对话**：将单一对话拆分成多个独立的对话段，以减少对话长度对模型推理性能的影响。例如，在处理一个长篇对话时，可以将对话分成若干段，每段集中讨论一个具体问题。
- **明确职责**：当单个模型需要处理过多问题时，可以通过拆分角色来明确每个模型的职责。例如，在一个复杂的对话系统中，可以设置不同的子模型分别处理用户意图识别、对话管理和应答生成等任务。
- **角色拆分**：通过角色拆分，确保每个模型处理的内容单一而连贯，从而提升整体对话系统的性能和准确性。例如，可以设置一个专门处理技术问题的模型和一个专门处理日常对话的模型，分别负责不同类型的对话。

为了模拟一个计算机科学家（Agent A）和一个法律专家（Agent B）协作解决人工智能合规标准制定的问题，我们设计了如下复杂的任务和分工：

1. **Agent A（计算机科学家）：**负责提出技术实施的建议和技术难题的解决，熟悉人工智能技术和数据隐私。

```python
# agent_a.py
from common import create_app

app = create_app("system: 你是一个熟悉人工智能技术的计算机科学家。")

if __name__ == '__main__':
    app.run(port=5000)
```

2. **Agent B（法律专家）：**负责评估合规性、提出法律建议和法规框架，精通法律法规和数据隐私保护。

```python
# agent_b.py
from common import create_app

app = create_app("system: 你是一个熟悉法律法规的法律专家。")

if __name__ == '__main__':
    app.run(port=5001)
```

3. **Agent C（标准化专家）：**负责协调和整合建议，生成完整的技术合规方案。确保最终的合规方案完整和可实施。

```python
# agent_c.py
from flask import Flask, request, jsonify
from transformers import pipeline
from transformers import AutoTokenizer, AutoModelForCausalLM

from langchain.agents import initialize_agent, Tool, AgentType
from langchain.llms import HuggingFacePipeline
import requests
import torch

app = Flask(__name__)

cache_dir = './llama_cache'
model_path = cache_dir + '/LLM-Research/Meta-Llama-3-8B-Instruct'
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
    device_map="auto" if torch.cuda.is_available() else None,
    pad_token_id=tokenizer.eos_token_id
)

def call_expert(url, task_requirement):
    response = requests.post(url, json={"intent": task_requirement}, timeout=5)
    response.raise_for_status()
    return response.json().get("response", "Error: No response from expert")

ai_expert = lambda task: call_expert("http://localhost:5000/chat", task)
law_expert = lambda task: call_expert("http://localhost:5001/chat", task)

ai = Tool.from_function(func=ai_expert, name="ai_expert", description="当你需要人工智能专家知识时使用这个工具，输入为具体问题，返回为问题答案")
law = Tool.from_function(func=law_expert, name="law_expert", description="当你需要法律合规专家知识时使用这个工具，输入为具体问题，返回为问题答案")

tools = [ai, law]

pipe = pipeline(task="text-generation", model=model, tokenizer=tokenizer, max_new_tokens=512)
llm = HuggingFacePipeline(pipeline=pipe)

agent = initialize_agent(tools,
        llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        max_iterations = 5,
        handle_parsing_errors = True)

@app.route('/integrate', methods=['POST'])
def integrate():
    data = request.get_json()
    task = data.get('task', '')
    res = agent.run(task)
    return jsonify({'response': res})

if __name__ == '__main__':
    app.run(port=5002)
```

可以看出，在多智能体合作的时候，**各个智能体在彼此的眼中都是工具**。下面，通过 curl 命令向 [http://localhost:5002/integrate](http://localhost:5002/integrate) 发送 POST 请求，任务描述为制定人工智能合规标准，避免人工智能伤害人类。

返回结果为标准化专家（Agent C）通过协调计算机科学家（Agent A）和法律专家（Agent B）的响应生成的综合答案。

```bash
$ curl -X POST http://localhost:5002/integrate \
       -H "Content-Type: application/json" \
       -d '{"task": "制定人工智能合规标准，避免人工智能伤害人类"}'
```

在这个设计示例中，计算机科学家和法律专家在制定人工智能合规标准时进行了分工和协作。Agent A 提出技术实施的建议和解决技术难题，而 Agent B 负责评估合规性、提出法律建议和法规框架。这种分工模式能有效结合技术实施和法律法规，以确保人工智能技术的合法合规性。

最后，我们展开介绍 common.py，这个函数接收模型目录和种子记忆（seed memory）作为参数，创建并返回一个 python 服务应用。

这里有一个重点，那就是我们要给每个 Agent 一个种子记忆，也就是它的全局人设，这是智能体应用中最重要的部分，因为**如果没有一个坚固的人设，智能体在长期工作过程中一定会出现偏离**，在后面课程中我将进一步解释这句话的含义。

```python
# common.py
from flask import Flask, request, jsonify
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

def create_app(seed_memory):
    app = Flask(__name__)

    cache_dir = './llama_cache'
    model_path = cache_dir + '/LLM-Research/Meta-Llama-3-8B-Instruct'
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        model_path,
        torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
        pad_token_id=tokenizer.eos_token_id
    )

    # 定义聊天接口
    @app.route('/chat', methods=['POST'])
    def chat():
        data = request.get_json()
        intent = data.get('intent', '')

        # 构造提示词
        prompt = f"{seed_memory}\n请回答以下问题:{intent}"
        input_ids = tokenizer.encode(prompt, return_tensors="pt").to("cuda")
        outputs = model.generate(input_ids, max_length=150)
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)

        return jsonify({'response': response})

    return app
```

当然本节课的例子都是为了让你可以快速产生感性认识，这种实现方式适用于简单的示例和小规模的应用，但在生产环境中则需要进一步地学习更复杂的方案。

## 小结

好了，到这里我们来做个总结吧。在这节课中，我们介绍了 LLaMA 3 能力的几个层面。

首先是 NTP（Next Token Prediction）的基础能力。我们详细解析了其原理和实现方式，NTP通过预测下一个词来生成连贯的对话，是大语言模型生成文本的核心机制。我们展示了如何将输入文本分解为token，将其转换为嵌入形式，并通过大语言模型预测下一个词的概率分布来生成文本。我们还介绍了 LLaMA 3 和 LLaMA 3-Instruct 两个版本，并提及了LLaMA 3 的其他变体。

接着是从无状态到有状态的对话服务转变。我们讲解了如何保留对话历史信息，将无状态的LLM转化为有状态的对话服务，以确保生成的对话保持上下文的连贯性。

然后是从封闭到开放的实时信息服务，也就是我们常说的检索增强生成（RAG）技术的目标。我们介绍了如何将封闭的 LLM 转变为能够获取实时信息的开放服务。通过整合外部检索系统（例如我们使用的搜索引擎 API），模型可以在生成过程中获取最新的事实信息，以保证生成内容的准确性和时效性。

最后，我们讨论了多智能体的协作。通过多智能体的配合，我们可以解决长对话带来的推理性能和效果问题，避免职责混乱。明确分工后，各智能体可以处理不同类型的任务，从而提升整体对话系统的效率和准确性。

通过这些讲解，希望你能更深入地理解 LLaMA 3 的各项能力和应用场景，快速地掌握大模型技术的实际操作方法。

课程代码地址：[https://github.com/tylerelyt/LLaMa-in-Action](https://github.com/tylerelyt/LLaMa-in-Action)

## 课后思考

1. 使用 LLaMA 3 的不同版本对比实验，在评论区给出你的实验对比效果。
2. 使用 Ollama 和 HuggingFace LLaMA 3 进行内容生成，对比性能表现。

期待你在留言区和我交流互动。如果今天的课程对你有帮助，欢迎你把它转发出去。我们下节课见！

## 实验环境

我们将使用Ollama进行实验环境的搭建。以下是具体步骤：

你需要在以下环境中进行操作：

- macOS bash
- Linux bash
- Windows WSL bash

首先运行以下命令来启动LLaMA 3模型：

```bash
$ ollama run llama3:text
```

你会看到类似以下输出：

```python
pulling manifest
pulling cebceffdc781... 100% ▕█████████████████████████████████████████████████████████████▏ 4.7 GB
pulling 4fa551d4f938... 100% ▕█████████████████████████████████████████████████████████████▏  12 KB
pulling 0dbc577651fb... 100% ▕█████████████████████████████████████████████████████████████▏  337 B
verifying sha256 digest
writing manifest
removing any unused layers
success
>>> Send a message (/? for help)
```

可以通过以下命令测试Ollama是否正常工作：

```python
$ curl -X POST http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt":"Why is the sky blue?"
 }'
```

接下来启动open-webui：

```python
$ docker run -d -p 3000:8080 --add-host=host.docker.internal:host-gateway -v open-webui:/app/backend/data --name open-webui --restart always ghcr.io/open-webui/open-webui:main
```

你会看到类似以下输出：

```python
Unable to find image 'ghcr.io/open-webui/open-webui:main' locally
main: Pulling from open-webui/open-webui
2cc3ae149d28: Pull complete
dc57dfa1396c: Pull complete
b275de30f399: Pull complete
0ea58f563222: Pull complete
251072225b40: Pull complete
130662f3df11: Pull complete
4f4fb700ef54: Pull complete
de53a1836181: Pull complete
d28e6308a168: Pull complete
e2c345686679: Pull complete
4a9cac9db244: Pull complete
8f76aa437192: Pull complete
5e8d46269631: Pull complete
83e1a8b855bf: Pull complete
179448cc6367: Pull complete
a3c72f49a0d3: Pull complete
Digest: sha256:cecf06773cc0621dbe83c25fdeaf9c9bae33799cd7df14790a9b8ccf61b91764
Status: Downloaded newer image for ghcr.io/open-webui/open-webui:main
cbff08075458b6342eef83c36343ec04500fe899281e0f74260aa4ed64bbe374
```

之后访问 [http://localhost:3000](http://localhost:3000)，注册一个账号，就可以看到以下界面使用啦。

![图片](https://static001.geekbang.org/resource/image/3f/ce/3f345bdbb8c5d0eddef102c700ccd6ce.png?wh=1400x730)
<div><strong>精选留言（15）</strong></div><ul>
<li><span>兵戈</span> 👍（4） 💬（3）<p>Typler老师的课程代码地址：https:&#47;&#47;github.com&#47;tylerelyt&#47;llama。不过当前工程目录下缺少requirements.txt，可能会让许多跑代码的同学遇到包依赖不一致的问题，我提了一个issue：
https:&#47;&#47;github.com&#47;tylerelyt&#47;llama&#47;issues&#47;1
希望Typer老师有空补充下 :）</p>2024-10-18</li><br/><li><span>兵戈</span> 👍（3） 💬（2）<p>Tyler老师提供示例很不错，其中第一个示例，最好加上max_length参数，否则可能会一直运行停不下来，如下：
with torch.no_grad():
    outputs = model.generate(**inputs, max_length=100)</p>2024-10-17</li><br/><li><span>edward</span> 👍（3） 💬（3）<p>请问老师 实验环境需要什么样的机器配置？</p>2024-10-16</li><br/><li><span>keep move</span> 👍（1） 💬（1）<p>示例代码如何能运行起来，能否写个简要的步骤呢</p>2024-10-30</li><br/><li><span>J Sun</span> 👍（0） 💬（1）<p>模型怎么下载
</p>2024-10-18</li><br/><li><span>S！</span> 👍（0） 💬（0）<p>m2系列的mac pro运行demo一直没有输出结果，console输出如下：
import sys; print(&#39;Python %s on %s&#39; % (sys.version, sys.platform))
&#47;usr&#47;local&#47;bin&#47;python3.10 -X pycache_prefix=&#47;Users&#47;salesonlee&#47;Library&#47;Caches&#47;JetBrains&#47;PyCharm2024.1&#47;cpython-cache &#47;Applications&#47;PyCharm.app&#47;Contents&#47;plugins&#47;python&#47;helpers&#47;pydev&#47;pydevd.py --multiprocess --qt-support=auto --client 127.0.0.1 --port 57101 --file &#47;Users&#47;salesonlee&#47;IT&#47;dev_codes&#47;PythonProjects&#47;tylerelyt-llama&#47;chapter1&#47;lesson1&#47;example1.py 
Connected to pydev debugger (build 241.17890.14)
Loading checkpoint shards: 100%|██████████| 4&#47;4 [01:00&lt;00:00, 15.10s&#47;it]
Setting `pad_token_id` to `eos_token_id`:None for open-end generation.
Starting from v4.46, the `logits` model output will have the same type as the model (except at train time, where it will always be FP32)


请问是因为没有使用gpu么，是硬件配置的原因？还是其它原因？ </p>2024-11-11</li><br/><li><span>S！</span> 👍（0） 💬（0）<p>import sys; print(&#39;Python %s on %s&#39; % (sys.version, sys.platform))
&#47;usr&#47;local&#47;bin&#47;python3.10 -X pycache_prefix=&#47;Users&#47;salesonlee&#47;Library&#47;Caches&#47;JetBrains&#47;PyCharm2024.1&#47;cpython-cache &#47;Applications&#47;PyCharm.app&#47;Contents&#47;plugins&#47;python&#47;helpers&#47;pydev&#47;pydevd.py --multiprocess --qt-support=auto --client 127.0.0.1 --port 57101 --file &#47;Users&#47;salesonlee&#47;IT&#47;dev_codes&#47;PythonProjects&#47;tylerelyt-llama&#47;chapter1&#47;lesson1&#47;example1.py 
Connected to pydev debugger (build 241.17890.14)
Loading checkpoint shards: 100%|██████████| 4&#47;4 [01:00&lt;00:00, 15.10s&#47;it]
Setting `pad_token_id` to `eos_token_id`:None for open-end generation.
Starting from v4.46, the `logits` model output will have the same type as the model (except at train time, where it will always be FP32)
</p>2024-11-11</li><br/><li><span>S！</span> 👍（0） 💬（0）<p>m2系列mac pro 运行demo一直没有输出结果，console输出如下：</p>2024-11-11</li><br/><li><span>S！</span> 👍（0） 💬（0）<p>运行课程demo需要什么样的碍硬件资源？</p>2024-11-10</li><br/><li><span>S！</span> 👍（0） 💬（2）<p>Mac pro可以运行llama3么</p>2024-11-10</li><br/><li><span>keep move</span> 👍（0） 💬（0）<p>python学习那个方向 pytorch吗</p>2024-10-23</li><br/><li><span>Orson</span> 👍（0） 💬（0）<p># agent_a.py
from common import create_app

app = create_app(&quot;system: 你是一个熟悉人工智能技术的计算机科学家。&quot;)

if __name__ == &#39;__main__&#39;:
    app.run(port=5000)
请问，在用AutoDL这样的云服务的时候，app.run(port=5000）需要怎么修改。或者，agent_a、b、c和common文件需要做哪些修改？</p>2024-10-21</li><br/><li><span>Allen</span> 👍（0） 💬（0）<p>你好，请问在调用模型时with torch.no_grad():为啥后面几段里没有加？会影响性能吗？谢谢。</p>2024-10-20</li><br/><li><span>Dowen Liu</span> 👍（0） 💬（0）<p>不用python 能不能做同样的调用呢？比如直接调用接口、spring ai </p>2024-10-19</li><br/><li><span>J Sun</span> 👍（0） 💬（1）<p>模型在哪里下载</p>2024-10-18</li><br/>
</ul>