你好，我是徐文浩。

有不少人在使用OpenAI提供的GPT系列模型的时候，都反馈效果并不好。这些反馈中有一大类问题，是回答不了一些简单的问题。比如当我们用中文问AI一些事实性的问题，AI很容易胡编乱造。而当你问它最近发生的新闻事件的时候，它就干脆告诉你它不知道21年之后的事情。

本来呢，我写到这里就可以了。不过到了3月24日，OpenAI推出了ChatGPT Plugins这个功能，可以让ChatGPT通过插件的形式链接外部的第三方应用。我自己也还在排队等waiting list，所以暂时也无法体验。不过，即使有了第三方应用，我们也不能确保自己想要知道的信息正好被其他人提供了。而且，有些信息和问题我们只想提供给自己公司的内部使用，并不想开放给所有人。这个时候，我们既希望能够利用OpenAI的大语言模型的能力，但是又需要这些能力仅仅在我们自己指定的数据上。那么这一讲，就是为了解决这个问题的。

## 大型语言模型的不足之处

我们先来尝试问ChatGPT一个人尽皆知的常识，“鲁迅先生去日本学习医学的老师是谁”，结果它给出的答案是鲁迅的好友，内山书店的老板内山完造，而不是大家都学习过的藤野先生。

![图片](https://static001.geekbang.org/resource/image/89/64/891fc431e1cd46b1d45f60fe79c2e964.png?wh=704x264)

之所以会出现这样的情况，和大模型的原理以及它使用训练的数据集是有关的。大语言模型的原理，就是利用训练样本里面出现的文本的前后关系，通过前面的文本对接下来出现的文本进行概率预测。如果类似的前后文本出现得越多，那么这个概率在训练过程里会收敛到少数正确答案上，回答就准确。如果这样的文本很少，那么训练过程里就会有一定的随机性，对应的答案就容易似是而非。而在GPT-3的模型里，虽然整体的训练语料很多，但是中文语料很少。只有不到1%的语料是中文的，所以如果问很多中文相关的知识性或者常识性问题，它的回答往往就很扯。

当然，你可以说我们有一个解决办法，就是多找一些高质量的中文语料训练一个新的模型。或者，对于我们想让AI能够回答出来的问题，找一些数据。然后利用OpenAI提供的“微调”（Fine-tune）接口，在原来的基础上训练一个新模型出来。

![图片](https://static001.geekbang.org/resource/image/47/9c/47e11ff6d1534e8f53ea8da3ae5bcb9c.png?wh=700x217 "如果你问一下新闻类的信息，ChatGPT通常会拒绝回答")

这样当然是可以的，就是成本有点高。对于上面那个例子来说，只是缺少一些文本数据，还好说。如果是时效性要求比较强的资讯类的信息，就很难这么做。比如，我们想让AI告诉我们前一天足球赛的比分，我们不太可能每隔几个小时就单独训练或者微调一下模型，那样干的成本太高了。

## Bing的解法——先搜索，后提示

不过对这个领域比较关注的朋友可能就要问了。之前微软不是在Bing这个搜索引擎里，加上了ChatGPT的问答功能吗？效果似乎也还不错，那Bing是怎么做到的呢，是因为他们用了更加厉害的语言模型吗？

虽然我并没有什么内幕消息，不了解Bing是怎么做的。但是如果是我的话，会用这样一个解决办法——那就是先搜索，后提示（Prompt）。

1. 我们先通过搜索的方式，找到和询问的问题最相关的语料。这个搜索过程中，我们既可以用传统的基于关键词搜索的技术，也可以用[第 9 讲](http://time.geekbang.org/column/article/644795)我们刚刚介绍过的使用Embedding的相似度进行语义搜索的技术。
2. 然后，我们将和问题语义最接近的前几条内容，作为提示语的一部分给到AI。然后请AI参考这些内容，再来回答这个问题。

![图片](https://static001.geekbang.org/resource/image/c8/f2/c8f7888bdfc3438934e784beayybeef2.png?wh=686x438)

我在这里，也给了你一个例子的截图。当我们把《藤野先生》里的两个段落给到AI，然后请AI根据这两个段落，回答原来那个问题，就会得到正确的答案，你也可以去看一看。

这也是利用大语言模型的一个常见模式。因为大语言模型其实内含了两种能力。

第一种，是海量的语料中，本身已经包含了的知识信息。比如，我们前面问AI鱼香肉丝的做法，它能回答上来就是因为语料里已经有了充足的相关知识。我们一般称之为“世界知识”。

第二种，是根据你输入的内容，理解和推理的能力。这个能力，不需要训练语料里有一样的内容。而是大语言模型本身有“思维能力”，能够进行阅读理解。这个过程里，“知识”不是模型本身提供的，而是我们找出来，临时提供给模型的。如果不提供这个上下文，再问一次模型相同的问题，它还是答不上来的。

## 通过llama\_index封装“第二大脑”

我给上面这种先搜索、后提示的方式，取了一个名字，叫做AI的“第二大脑”模式。因为这个方法，需要提前把你希望AI能够回答的知识，建立一个外部的索引，这个索引就好像AI的“第二个大脑”。每次向AI提问的时候，它都会先去查询一下这个第二大脑里面的资料，找到相关资料之后，再通过自己的思维能力来回答问题。

实际上，你现在在网上看到的很多读论文、读书回答问题的应用，都是通过这个模式来实现的。那么，现在我们就来自己实现一下这个“第二大脑”模式。

不过，我们不必从0开始写代码。因为这个模式实在太过常用了，所以有人为它写了一个开源Python包，叫做llama-index。那么我们这里，可以直接利用这个软件包，用几行代码来试一试，它能不能回答上鲁迅先生写的《藤野先生》相关的问题。

llama-index还没有人做好Conda下的包，所以即使在Conda下还是要通过pip来安装。

```python
pip install llama-index
pip install langchain
```

我把从网上找到的《藤野先生》这篇文章变成了一个txt文件，放在了 data/mr\_fujino 这个目录下。我们的代码也非常简单，一共没有几行。

```python
import openai, os
from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader

openai.api_key = os.environ.get("OPENAI_API_KEY")

documents = SimpleDirectoryReader('./data/mr_fujino').load_data()
index = GPTSimpleVectorIndex.from_documents(documents)

index.save_to_disk('index_mr_fujino.json')
```

输出结果：

```python
INFO:llama_index.token_counter.token_counter:> [build_index_from_nodes] Total LLM token usage: 0 tokens
INFO:llama_index.token_counter.token_counter:> [build_index_from_nodes] Total embedding token usage: 6763 tokens
```

注：日志中会打印出来我们通过Embedding消耗了多少个Token。

首先，我们通过一个叫做SimpleDirectoryReader的数据加载器，将整个./data/mr\_fujino 的目录给加载进来。这里面的每一个文件，都会被当成是一篇文档。

然后，我们将所有的文档交给了 GPTSimpleVectorIndex 构建索引。顾名思义，它会把文档分段转换成一个个向量，然后存储成一个索引。

最后，我们会把对应的索引存下来，存储的结果就是一个json文件。后面，我们就可以用这个索引来进行相应的问答。

```python
index = GPTVectorStoreIndex.load_from_disk('index_mr_fujino.json')
response = index.query("鲁迅先生在日本学习医学的老师是谁？")
print(response)
```

要进行问答也没有几行代码，我们通过 GPTSimpleVectorIndex 的 load\_from\_disk 函数，可以把刚才生成的索引加载到内存里面来。然后对着Index索引调用Query函数，就能够获得问题的答案。可以看到，通过外部的索引，我们可以正确地获得问题的答案。

```python
INFO:llama_index.token_counter.token_counter:> [query] Total LLM token usage: 2984 tokens
INFO:llama_index.token_counter.token_counter:> [query] Total embedding token usage: 34 tokens

鲁迅先生在日本学习医学的老师是藤野严九郎先生。
```

这么一看，似乎问题特别简单，三行代码就搞定了。别着急，我们再看看别的问题它是不是也能答上来？这次我们来试着问问鲁迅先生是在哪里学习医学的。

```python
response = index.query("鲁迅先生去哪里学的医学？")
print(response)
```

输出结果：

```python
> Got node text: 藤野先生
东京也无非是这样。上野的樱花烂熳的时节，望去确也像绯红的轻云，但花下也缺不了成群结队的“清国留学生”的速成班，头顶上盘着大辫子，顶得学生制帽的顶上高高耸起，形成一座富士山。也有解散辫子，盘得平的，除下帽来，油光可鉴，宛如小姑娘的发髻一般，还要将脖子扭几扭。实在标致极了。
中国留学生会馆的门房里有几本书买，有时还值得去一转；倘在上午，里面的几间洋房里倒也还可以坐坐的。但到傍晚，有...

INFO:llama_index.token_counter.token_counter:> [query] Total LLM token usage: 2969 tokens
INFO:llama_index.token_counter.token_counter:> [query] Total embedding token usage: 26 tokens

鲁迅先生去仙台的医学专门学校学习医学。
```

它仍然正确回答了问题。那么，我们搜索到的内容，在这个过程里面是如何提交给OpenAI的呢？我们就来看看下面的这段代码就知道了。

```python
from llama_index import QuestionAnswerPrompt
query_str = "鲁迅先生去哪里学的医学？"
DEFAULT_TEXT_QA_PROMPT_TMPL = (
    "Context information is below. \n"
    "---------------------\n"
    "{context_str}"
    "\n---------------------\n"
    "Given the context information and not prior knowledge, "
    "answer the question: {query_str}\n"
)
QA_PROMPT = QuestionAnswerPrompt(DEFAULT_TEXT_QA_PROMPT_TMPL)

response = index.query(query_str, text_qa_template=QA_PROMPT)
print(response)
```

这段代码里，我们定义了一个QA\_PROMPT的对象，并且为它设计了一个模版。

1. 这个模版的开头，我们告诉AI，我们为AI提供了一些上下文信息（Context information）。
2. 模版里面支持两个变量，一个叫做 context\_str，另一个叫做query\_str。context\_str 的地方，在实际调用的时候，会被通过Embedding相似度找出来的内容填入。而 query\_str 则是会被我们实际提的问题替换掉。
3. 实际提问的时候，我们告诉AI，只考虑上下文信息，而不要根据自己已经有的先验知识（prior knowledge）来回答问题。

我们就是这样，把搜索找到的相关内容以及问题，组合到一起变成一段提示语，让AI能够按照我们的要求来回答问题。那我们再问一次AI，看看答案是不是没有变。

输出结果：

```python
鲁迅先生去仙台的医学专门学校学习医学。
```

这一次AI还是正确地回答出了鲁迅先生是去仙台的医学专门学校学习的。我们再试一试，问一些不相干的问题，会得到什么答案，比如我们问问红楼梦里林黛玉和贾宝玉的关系。

```python
QA_PROMPT_TMPL = (
    "下面的“我”指的是鲁迅先生 \n"
    "---------------------\n"
    "{context_str}"
    "\n---------------------\n"
    "根据这些信息，请回答问题: {query_str}\n"
    "如果您不知道的话，请回答不知道\n"
)
QA_PROMPT = QuestionAnswerPrompt(QA_PROMPT_TMPL)

response = index.query("请问林黛玉和贾宝玉是什么关系？", text_qa_template=QA_PROMPT)

print(response)
```

输出结果：

```python
不知道
```

可以看到，AI的确按照我们的指令回答不知道，而不是胡答一气。

## 通过llama\_index对于文章进行小结

还有一个常见的使用llama-index这样“第二大脑”的Python库的应用场景，就是生成文章的摘要。在前面教你如何进行文本聚类的时候，我们已经看到了可以通过合适的提示语（Prompt）做到这一点。不过，如果要总结一篇论文、甚至是一本书，每次最多只能支持4096个Token的API就不太够用了。

要解决这个问题也并不困难，我们只要进行分段小结，再对总结出来的内容再做一次小结就可以了。我们可以把一篇文章，乃至一本书，构建成一个树状的索引。每一个树里面的节点，就是它的子树下内容的摘要。最后，在整棵树的根节点，得到的就是整篇文章或者整本书的总结了。

![图片](https://static001.geekbang.org/resource/image/49/42/49489cc171aee72855930aaf68112b42.jpg?wh=1820x1350 "通过将文本分片建立树状结构的索引来完成全文的总结")

事实上，llama-index本身就内置了这样的功能。下面我们就来看看要实现这个功能，我们的代码应该怎么写。

首先，我们先来安装一下 spaCy 这个Python库，并且下载一下对应的中文分词分句需要的模型。

```python
pip install spacy
python -m spacy download zh_core_web_sm
```

接下来的代码很简单，我们选用了GPTListIndex这个llama-index里最简单的索引结构。不过我们针对自身需求做了两点优化。

首先，在索引里面，我们指定了一个 LLMPredictor，让我们向OpenAI发起请求的时候，都使用ChatGPT的模型。因为这个模型比较快，也比较便宜。llama-index默认使用的模型是text-davinci-003，价格比gpt-3.5-turbo要贵上十倍。在我们前面只是简单进行几轮对话的时候，这个价格差异还不明显。而如果你要把几十本书都灌进去，那成本上就会差上不少了。我们在这里，设置了模型输出的内容都在1024个Token以内，这样可以确保我们的小结不会太长，不会把一大段不相关的内容都合并到一起去。

其次，我们定义了使用 SpacyTextSplitter来进行中文文本的分割。llama-index默认的设置对于中文的支持和效果都不太好。不过好在它可以让你自定义使用的文本分割方式。我们选用的文章是中文的，里面的标点符号也都是中文的，所以我们就用了中文的语言模型。我们也限制了分割出来的文本段，最长不要超过2048个Token，这些参数都可以根据你实际用来处理的文章内容和属性自己设置。

```python
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import SpacyTextSplitter
from llama_index import GPTListIndex, LLMPredictor, ServiceContext
from llama_index.node_parser import SimpleNodeParser

# define LLM
llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo", max_tokens=1024))

text_splitter = SpacyTextSplitter(pipeline="zh_core_web_sm", chunk_size = 2048)
parser = SimpleNodeParser(text_splitter=text_splitter)
documents = SimpleDirectoryReader('./data/mr_fujino').load_data()
nodes = parser.get_nodes_from_documents(documents)

service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)

list_index = GPTListIndex(nodes=nodes, service_context=service_context)
```

输出结果：

```python
WARNING:llama_index.llm_predictor.base:Unknown max input size for gpt-3.5-turbo, using defaults.
INFO:llama_index.token_counter.token_counter:> [build_index_from_nodes] Total LLM token usage: 0 tokens
INFO:llama_index.token_counter.token_counter:> [build_index_from_nodes] Total embedding token usage: 0 tokens
```

GPTListIndex在构建索引的时候，并不会创建Embedding，所以索引创建的时候很快，也不消耗Token数量。它只是根据你设置的索引结构和分割方式，建立了一个List的索引。

接着，我们就可以让AI帮我们去小结这篇文章了。同样的，提示语本身很重要，所以我们还是强调了文章内容是鲁迅先生以“我”这个第一人称写的。因为我们想要的是按照树状结构进行文章的小结，所以我们设定了一个参数，叫做 response\_mode = “tree\_summarize”。这个参数，就会按照上面我们所说的树状结构把整个文章总结出来。

实际上，它就是将每一段文本分片，都通过query内的提示语小结。再对多个小结里的内容，再次通过query里的提示语继续小结。

```python
response = list_index.query("下面鲁迅先生以第一人称‘我’写的内容，请你用中文总结一下:", response_mode="tree_summarize")
print(response)
```

输出结果：

```python
INFO:llama_index.indices.common_tree.base:> Building index from nodes: 2 chunks
INFO:llama_index.token_counter.token_counter:> [query] Total LLM token usage: 9787 tokens
INFO:llama_index.token_counter.token_counter:> [query] Total embedding token usage: 0 tokens
鲁迅先生回忆了自己在日本学医期间的经历，描述了自己在解剖实习中的经历，以及与教授藤野先生的交往。他还提到了一些不愉快的事情，比如遭到同学的诽谤和歧视，以及看到中国人被枪毙时的感受。最后，他告诉藤野先生自己将不再学医，而是想学生物学。他想起了一个人，这个人是他的老师，他对鲁迅很热心，给他很多鼓励和教诲。鲁迅现在只有他的照片，但是每次看到他的照片，都会让他感到勇气和良心发现。
```

可以看到，我们只用了几行代码就完成了整个文章的小结，返回的结果整体上来说也还算不错。

## 引入多模态，让llamd-index能够识别小票

llama\_index不光能索引文本，很多书里面还有图片、插画这样的信息。llama\_index一样可以索引起来，供你查询，这也就是所谓的多模态能力。当然，这个能力其实是通过一些多模态的模型，把文本和图片能够联系到一起做到的。在整个课程的第三部分，我们也会专门来看看这些图像的多模态模型是怎么样的。

这里我们就来看一个llama\_index[官方样例库](https://github.com/jerryjliu/llama_index/blob/main/examples/multimodal/Multimodal.ipynb)里面给到的例子，也就是把吃饭的小票都拍下来。然后询问哪天吃了什么，花了多少钱。

```python
from llama_index import SimpleDirectoryReader, GPTVectorStoreIndex
from llama_index.readers.file.base import DEFAULT_FILE_EXTRACTOR, ImageParser
from llama_index.response.notebook_utils import display_response, display_image
from llama_index.indices.query.query_transform.base import ImageOutputQueryTransform

image_parser = ImageParser(keep_image=True, parse_text=True)
file_extractor = DEFAULT_FILE_EXTRACTOR
file_extractor.update(
{
    ".jpg": image_parser,
    ".png": image_parser,
    ".jpeg": image_parser,
})

# NOTE: we add filename as metadata for all documents
filename_fn = lambda filename: {'file_name': filename}

receipt_reader = SimpleDirectoryReader(
    input_dir='./data/receipts', 
    file_extractor=file_extractor, 
    file_metadata=filename_fn,
)
receipt_documents = receipt_reader.load_data()
```

要能够索引图片，我们引入了ImageParser这个类，这个类背后，其实是一个基于OCR扫描的模型 [Donut](https://huggingface.co/naver-clova-ix/donut-base-finetuned-cord-v2)。它通过一个视觉的Encoder和一个文本的Decoder，这样任何一个图片能够变成一个一段文本，然后我们再通过OpenAI的Embedding把这段文本变成了一个向量。

我们仍然只需要使用简单的SimpleDirectoryReader，我们通过指定FileExtractor，会把对应的图片通过ImageParser解析成为文本，并最终成为向量来用于检索。

然后，我们仍然只需要向我们的索引用自然语言提问，就能找到对应的图片了。在提问的时候，我们专门制定了一个ImageOutputQueryTransform，主要是为了在输出结果的时候，能够在图片外加上 `<img>` 的标签方便在Notebook里面显示。

```python
receipts_index = GPTVectorStoreIndex.from_documents(receipt_documents)
receipts_response = receipts_index.query(
    'When was the last time I went to McDonald\'s and how much did I spend. \
    Also show me the receipt from my visit.',
    query_transform=ImageOutputQueryTransform(width=400)
)

display_response(receipts_response)
```

输出结果：

```python
INFO:llama_index.token_counter.token_counter:> [query] Total LLM token usage: 1004 tokens
INFO:llama_index.token_counter.token_counter:> [query] Total embedding token usage: 30 tokens

Final Response: The last time you went to McDonald's was on 03/10/2018 at 07:39:12 PM and you spent $26.15. Here is the receipt from your visit:
```

![图片](https://static001.geekbang.org/resource/image/18/08/181747bf1e95664b3929db6ec4a46b08.jpg?wh=750x1000)

可以看到，答案中不仅显示出了对应的图片，也给出了正确的答案，这也要归功于OpenAI对于任意文本强大的处理能力。

我们可以单独解析一下图片，看看对应的文本内容是什么。

```python
output_image = image_parser.parse_file('./data/receipts/1100-receipt.jpg')
print(output_image.text)
```

输出结果：

```plain
<s_menu><s_nm> Story</s_nm><s_num> 16725 Stony Platin Rd</s_nm><s_num> Store#:</s_nm><s_num> 3659</s_num><s_price> 700-418-8362</s_price><sep/><s_nm> Welcome to all day breakfast dormist O Md Donald's</s_nm><s_num> 192</s_num><s_price> 192</s_price><sep/><s_nm> QTY ITEM</s_nm><s_num> OTAL</s_num><s_unitprice> 03/10/2018</s_unitprice><s_cnt> 1</s_cnt><s_price> 07:39:12 PM</s_price><sep/><s_nm> Delivery</s_nm><s_cnt> 1</s_cnt><s_price> 0.00</s_price><sep/><s_nm> 10 McNuggets EVM</s_nm><s_cnt> 1</s_cnt><s_price> 10.29</s_price><sep/><s_nm> Barbeque Sauce</s_nm><s_cnt> 1</s_cnt><s_price> 1</s_price><sep/><s_nm> Barbeque Sauce</s_nm><s_num> 1</s_cnt><s_price> 0.40</s_price><sep/><s_nm> L Coke</s_nm><s_cnt> 1</s_cnt><s_price> 0.40</s_price><sep/><s_nm> M French Fries</s_nm><s_cnt> 1</s_cnt><s_price> 3.99</s_price><sep/><s_nm> HM GrChS S-Fry Yog</s_nm><s_cnt> 1</s_cnt><sep/><s_nm> Smoonya</s_nm><s_cnt> 1</s_cnt><sep/><s_nm> HM Apple Juice</s_nm><s_cnt> 1</s_cnt><s_price> 2.89</s_price><sep/><s_nm> Cookies</s_nm><s_cnt> 6</s_cnt><s_price> 2.89</s_price><sep/><s_nm> Choc Chip Cookie</s_nm><s_cnt> 6</s_cnt><s_price> 1.19</s_price><sep/><s_nm> Baked Apple Pie</s_nm><s_cnt> 1</s_cnt><s_price> 3.29</s_price><sep/><s_nm> French Fries</s_nm><s_cnt> 1</s_cnt><s_price> 2.99</s_price><sep/><s_nm> Iced Tea</s_nm><s_cnt> 1</s_cnt><s_price> 2.99</s_price></s_menu><s_sub_total><s_subtotal_price> 25.04</s_subtotal_price><s_tax_price> 1.11</s_tax_price></s_sub_total><s_total><s_total_price> 26.15</s_total_price><s_changeprice> 0.00</s_changeprice><s_creditcardprice> 26.15</s_creditcardprice></s_total>



```

可以看到，对应的就是OCR后的文本结果，里面的确有对应我们去的店铺的名字和时间，以及消费的金额。

围绕OpenAI以及整个大语言模型的生态还在快速发展中，所以llama-index这个库也在快速迭代。我自己在使用的过程中，也遇到各种各样的小Bug。对于中文的支持也有各种各样的小缺陷。不过，作为开源项目，它已经有一个很不错的生态了，特别是提供了大量的DataConnector，既包括PDF、ePub这样的电子书格式，也包括YouTube、Notion、MongoDB这样外部的数据源、API接入的数据，或者是本地数据库的数据。你可以在 [llamahub.ai](https://llamahub.ai/) 看到社区开发出来的读取各种不同数据源格式的DataConnector。

![图片](https://static001.geekbang.org/resource/image/d1/91/d19d1dd9888785c85bbc3ac5aec08191.png?wh=1237x1029)

## 小结

好了，相信经过这一讲，你已经能够上手使用llama-index这个Python包了。通过它，你可以快速将外部的资料库变成索引，并且通过它提供的query接口快速向文档提问，也能够通过将文本分片，并通过树状的方式管理索引并进行小结。

llama-index还有很多其他功能，这个Python库仍然在发展过程中，不过已经非常值得拿来使用，加速你开发大语言模型类的相关应用了。相关的文档，可以在[官网](https://gpt-index.readthedocs.io/en/latest/)看到。对应的代码也是开源的，遇到问题也可以直接去[源代码](https://github.com/jerryjliu/gpt_index)里一探究竟。

llama-index其实给出了一种使用大语言模型的设计模式，我称之为“第二大脑”模式。通过先将外部的资料库索引，然后每次提问的时候，先从资料库里通过搜索找到有相关性的材料，然后再通过AI的语义理解能力让AI基于搜索到的结果来回答问题。

![图片](https://static001.geekbang.org/resource/image/e4/6c/e4ae3fbeaa82d82e317dfcef40679f6c.jpg?wh=1896x1292)

其中，前两步的索引和搜索，我们可以使用OpenAI的Embedding接口，也可以使用其它的大语言模型的Embedding，或者传统的文本搜索技术。只有最后一步的问答，往往才必须使用OpenAI的接口。我们不仅可以索引文本信息，也可以通过其他的模型来把图片变成文本进行索引，实现所谓的多模态功能。

希望通过今天的这几个例子，你也能开始建立起自己的“第二大脑”资料库，能够将自己的数据集交给AI进行索引，获得一个专属于你自己的AI。

## 课后练习

1. llama-index的生态，不仅支持各种各样的DataConnector去加载数据，后端也支持各种形式的索引，比如在语义搜索里面我们介绍过的 Faiss、Pinecone、Weaviate 它都是支持的。除了这些之外，你能看看 llama-index 还有哪些形式的索引吗？除了进行问答和文章概括之外，你觉得这个库还能帮助我们做什么事情？
2. 现在有很多应用，在你把文档上传之后，还会给你一系列的提示，告诉你可以向对应的书或者论文问什么问题。比如 [SCISPACE](https://scispace.com/)，你能想想这些问题是怎么来的吗？

期待能在评论区看到你的分享，也欢迎你把这节课分享给感兴趣的朋友，我们下一讲再见。

## 推荐阅读

llama-index的功能非常强大，并且源代码里也专门提供了示例部分。你可以去看一下它的官方文档以及示例，了解它可以用来干什么。

1. 官方文档：[https://gpt-index.readthedocs.io/en/latest/](https://gpt-index.readthedocs.io/en/latest/)
2. 源码以及示例：[https://github.com/jerryjliu/llama\_index](https://github.com/jerryjliu/llama_index)
<div><strong>精选留言（15）</strong></div><ul>
<li><span>Owen</span> 👍（7） 💬（0）<p>截止到目前，最新能运行的代码

&#39;&#39;&#39;
归纳总结文章内容
&#39;&#39;&#39;
from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import SpacyTextSplitter
from llama_index.core import SummaryIndex, ServiceContext, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter

documents = SimpleDirectoryReader(input_dir=&quot;data&quot;).load_data() # 只能填写文件夹，不能具体到文件

service_context = ServiceContext.from_defaults(
    llm=ChatOpenAI(temperature=0, model_name=&quot;gpt-3.5-turbo&quot;, max_tokens=1000, n=1),
    node_parser=SentenceSplitter(chunk_size=512, chunk_overlap=20),
)

index = SummaryIndex.from_documents(documents = documents, service_context = service_context)
query_engine = index.as_query_engine()
response = query_engine.query(&quot;用中文总结这个故事&quot;)

print(response)</p>2024-03-01</li><br/><li><span>Penguin Shi</span> 👍（7） 💬（0）<p>《藤野先生》输出摘要的代码，因为代码更新，有bug，参考https:&#47;&#47;gpt-index.readthedocs.io&#47;en&#47;latest&#47;guides&#47;primer&#47;usage_pattern.html更新代码如下：

from langchain.chat_models import ChatOpenAI
from langchain.text_splitter import SpacyTextSplitter
from llama_index import ListIndex, LLMPredictor, ServiceContext
from llama_index import (
    VectorStoreIndex,
    get_response_synthesizer,
)
from llama_index.retrievers import VectorIndexRetriever
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.node_parser import SimpleNodeParser

# define LLM
llm_predictor = LLMPredictor(llm=ChatOpenAI(temperature=0, model_name=&quot;gpt-3.5-turbo&quot;, max_tokens=1024))

text_splitter = SpacyTextSplitter(pipeline=&quot;zh_core_web_sm&quot;, chunk_size = 2048)
parser = SimpleNodeParser(text_splitter=text_splitter)
documents = SimpleDirectoryReader(&#39;.&#47;data&#47;mr_fujino&#39;).load_data()

index = ListIndex.from_documents(documents)
retriever = index.as_retriever()

query_engine = RetrieverQueryEngine.from_args(retriever, response_mode=&#39;tree_summarize&#39;)
response = query_engine.query(&quot;下面鲁迅先生以第一人称‘我’写的内容，请你用中文总结一下:&quot;)

print(response)

另目前文档中，&quot;我把从网上找到的《藤野先生》这篇文章变成了一个 txt 文件，放在了 data&#47;mr_fujino 这个目录下。我们的代码也非常简单，一共没有几行。&quot;此文字下方代码的，第7行，index = GPTSimpleVectorIndex.from_documents(documents)中，“GPTSimpleVectorIndex”还未改成“GPTVectorStoreIndex” ；第9行，更改为index.storage_context.persist(&#39;index_mr_fujino&#39;)。
请更改，方便后续同学学习并运行代码。</p>2023-07-09</li><br/><li><span>Wise</span> 👍（20） 💬（5）<p>在llama_index V0.6.1 版本中，没有GPTSimpleVectorIndex 类了
import openai, os
from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader
os.environ[&quot;OPENAI_API_KEY&quot;] = &#39;&#39;
# 加载 documents
documents = SimpleDirectoryReader(&#39;.&#47;data&#47;mr_fujino&#39;).load_data()
index = GPTVectorStoreIndex.from_documents(documents)
index.storage_context.persist(&#39;index_mr_fujino&#39;)

# 从磁盘重新加载：
from llama_index import StorageContext, load_index_from_storage
# rebuild storage context
storage_context = StorageContext.from_defaults(persist_dir=&quot;.&#47;index_mr_fujino&quot;)
# load index
index = load_index_from_storage(storage_context)
query_engine = index.as_query_engine()
response = query_engine.query(&quot;鲁迅先生在日本学习医学的老师是谁？&quot;)
print(response)

参考官方文档连接：https:&#47;&#47;gpt-index.readthedocs.io&#47;en&#47;latest&#47;getting_started&#47;starter_example.html</p>2023-05-07</li><br/><li><span>hello</span> 👍（15） 💬（4）<p>想请教下老师，我们喂的语料，会被其他人看到使用吗？</p>2023-04-06</li><br/><li><span>daz2yy</span> 👍（11） 💬（1）<p>老师，请问下一个问题，我把它用作 QA 系统的时候有个问题，原本 QA 就有标准的回答模版，里面包括有文档地址、操作步骤等；如果让 GPT 根据这个模版来回答问题，他会自由发挥，会漏掉一部分内容；想拥有 AI 自由对话的能力，又想有固定的回答模版这个怎么能较好的兼顾呢？</p>2023-04-04</li><br/><li><span>Terry</span> 👍（8） 💬（1）<p>老师，请教一下langchain我理解也是一个LLM应用框架，它的功能和版本也更新很快。它和llama_index的区分是什么？在LLM应用开发上，我们一般怎么选择会比较好？</p>2023-04-25</li><br/><li><span>马听</span> 👍（8） 💬（3）<p>分享一个加载MySQL数据的例子：
from llama_index import GPTSimpleVectorIndex,download_loader

DatabaseReader = download_loader(&#39;DatabaseReader&#39;)

reader = DatabaseReader(
    scheme = &quot;mysql&quot;, # Database Scheme
    host = &quot;localhost&quot;, # Database Host
    port = &quot;3306&quot;, # Database Port
    user = &quot;martin&quot;, # Database User
    password = &quot;xxxxxx&quot;, # Database Password
    dbname = &quot;martin&quot;, # Database Name
)

query = f&quot;&quot;&quot;
select * from student_info
&quot;&quot;&quot;

documents = reader.load_data(query=query)
print(documents)</p>2023-04-12</li><br/><li><span>Oxygen Au 昕</span> 👍（6） 💬（1）<p>
response = list_index.query(&quot;下面鲁迅先生以第一人称‘我’写的内容，请你用中文总结一下:&quot;, response_mode=&quot;tree_summarize&quot;)
print(response)


上面这段代码报错，AttributeError: &#39;GPTListIndex&#39; object has no attribute &#39;query&#39; ， 我用的是llama-index 0.6.1

下面是正确的代码
query_engine = list_index.as_query_engine(response_mode=&quot;tree_summarize&quot;)
response = query_engine.query(&quot;下面鲁迅先生以第一人称‘我’写的内容，请你用中文总结一下:&quot;)
print(response)

结果： 鲁迅先生在日本学习医学时遇到了藤野严九郎教授，他很有学问，对学生也很关心，甚至帮助鲁迅修改讲义。但鲁迅当时不够用功，有时也很任性。在学习中，他遇到了一些困难和不愉快的事情，最终决定离开医学去学习生物学。离开前，藤野先生送给他一张照片，并希望他能保持联系。鲁迅很久没有和任何人通信，但想起了这位热心的老师，他的照片挂在鲁迅的房间里，每当他疲倦时看到照片就会感到勇气和良心发现。</p>2023-05-09</li><br/><li><span>黄智荣</span> 👍（2） 💬（1）<p>现在有很多应用，在你把文档上传之后，还会给你一系列的提示，告诉你可以向对应的书或者论文问什么问题。
------ 可以根据索引的文本，让chatgpt 设计几个提问的问题</p>2023-05-16</li><br/><li><span>勇.Max</span> 👍（2） 💬（3）<p>上面from llama_index import GPTSimpleVectorIndex会报错，因为现在已经改成了GPTVectorStoreIndex。
from llama_index import GPTVectorStoreIndex &#47;&#47;老师看到后可以更新下
</p>2023-05-08</li><br/><li><span>Viola</span> 👍（2） 💬（2）<p> 有同学遇到吗？
type object &#39;GPTSimpleVectorIndex&#39; has no attribute &#39;from_documents&#39;</p>2023-04-05</li><br/><li><span>hawk</span> 👍（2） 💬（3）<p>这些预选的问题，应该也是通过组合特定的提示语，和段落摘要，扔给GPT得到的吧？</p>2023-04-04</li><br/><li><span>牛味浓龙魏流</span> 👍（1） 💬（2）<p>所以llama_index跟chatGPT没什么关系是吗。。还是说这个包本身也在跟openAI打交道，看代码看不出来</p>2023-05-15</li><br/><li><span>东临沧海</span> 👍（1） 💬（1）<p>建议老师安装的库文件标明一下版本号，遇到这样问题好几次了，每次都要浪费大量时间。
llama_index版本都到v0.6.5，更新太快了</p>2023-05-11</li><br/><li><span>snow</span> 👍（1） 💬（2）<p>想请教下老师，为什么我在调用query 的时候，提示说BaseQueryEngine.query() got an unexpected keyword argument &#39;response_mode&#39; ？  发现当定义 list_index = GPTListIndex(nodes=nodes, service_context=service_context)， 没法直接调用list_index.query() ,而需要  list_index.as_query_engine().query() 这样子调用。 </p>2023-05-09</li><br/>
</ul>