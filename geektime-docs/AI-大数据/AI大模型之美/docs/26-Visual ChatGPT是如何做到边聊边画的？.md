你好，我是徐文浩。

过去三讲里，我们分别体验了CLIP、Stable Diffusion和ControlNet这三个模型。我们用这些模型来识别图片的内容，或者通过输入一段文本指令来画图。这些模型都是所谓的多模态模型，能够把图片和文本信息联系在一起。

不过，如果我们不仅仅是要随便找几个关键词画两张画玩个票，而是要在实际的工作环境里生成能用的图片，那么现在的体验还是远远不够的。对于画出来的图我们总有各种各样的修改和编辑的需求。比如，我们总是会遇到各个团队的人对着设计师的图指手画脚地提出各种各样的意见：“能不能把小狗移到图片的右边？”“能不能把背景从草地改成森林？”“我想要一个色彩斑斓的黑。”等等。

所以，**理想中的AI画画的功能，最好还能配上一个听得懂人话的AI，能够根据我们这些外行的指手画脚来修改生成的图片。**针对这个需求，我们就来介绍一下微软开源的Visual ChatGPT。

和之前我们自己写代码不同，这一讲我们一起来读一读 [Visual ChatGPT](https://github.com/microsoft/TaskMatrix) 这个开源项目的代码，看看它是如何做到能让我们聊着天就把图片给修改完了的。

## 体验 Visual ChatGPT

我们先来体验一下Visual ChatGPT的效果是怎么样的。这一次，Colab里的GPU也不够我们用了。Visual ChatGPT要加载很多个不同的图片相关的模型，这些模型加起来的显存得有40GB以上。

好在，微软通过HuggingFace的Space功能提供了一个[免费的 Space](https://huggingface.co/spaces/microsoft/visual_chatgpt)，让你可以直接体验Visual ChatGPT的功能。不过，考虑到用的人很多，使用的过程中你的请求会被排队处理，往往要等待很长时间才能完成一条指令。所以，我建议你花个几美元的小钱，部署一个自己的Visual ChatGPT的Space来体验一下它的功能。

![图片](https://static001.geekbang.org/resource/image/36/d0/3636e392e72ff192301f90668b09d6d0.png?wh=1020x1204 "微软在 HuggingFace 的 Space 里提供了一个可以免费体验的 Visual ChatGPT")

你可以点击微软提供的Space底部的Duplicate Space，部署一个完全一样的Visual ChatGPT Space到自己的账号下，这样你就不用和其他人排队等着了。

![图片](https://static001.geekbang.org/resource/image/07/90/0759e98e7d596a4b1ecd9da7e96eab90.png?wh=1258x545)

因为我们复制的是原先的Space，所以对应的硬件配置也是和微软免费提供的一样。通过一块46G显存的A10显卡，我们可以直接装载所有用到的模型。不过，使用A10显卡的Space是有成本的，一个小时就要花去你3.15美元。所以在复制Space的时候，有两个参数你需要注意。

- 第一个是Sleep time settings，我建议你设置成5分钟。这样，一旦5分钟没有人使用这个Space，它就会进入休眠状态。而HuggingFace在休眠状态下就不会收取你任何费用。只是下一次你要使用这个Space的时候，会重新启动整个Space，需要一点点时间。
- 另一个是Space的Visibility，我建议你选择Private。这样，这个Space只有你能看到。不然的话，就算你设置了自动休眠，也免不了有人看到你的Space上来试一试。如果不断有人来使用你的Space的话，它会一直在线运行，而你就是那个付账单的人。

在复制的Space部署完成之后，你就可以先来试一下Visual ChatGPT了。首先你需要在右上角输入你的OpenAI的API Key，并按下回车键。这样，整个窗口的下方就会出现可以输入文本的聊天窗口。你可以选择自由输入你想要画的内容，也可以在下面的Examples里选择预设好的一些指令。

![图片](https://static001.geekbang.org/resource/image/06/e1/063369368ccbdce8d2591d5851d967e1.png?wh=1005x1048 "输入 API KEY 之后一定要按下回车，否则下面的对话输入框无法出现")

我们可以分别试一下Examples里面给出的指令。

1. 我们先让Visual ChatGPT画一幅小猫在花园里奔跑的图片。

<!--THE END-->

![图片](https://static001.geekbang.org/resource/image/66/a5/661088917d40bf99836184c20d9828a5.png?wh=1011x519)

2. 然后再把画面里的小猫换成小狗。

<!--THE END-->

![图片](https://static001.geekbang.org/resource/image/cc/16/cc1985b4cc9d0d10bdc6fcea253af716.png?wh=1013x523)

3. 接着去掉画面中的小狗。

<!--THE END-->

![图片](https://static001.geekbang.org/resource/image/33/68/33d3b56b982bee56613fbcf3e8dffa68.png?wh=1024x523)

4. 再把图片风格换成水彩画。

<!--THE END-->

![图片](https://static001.geekbang.org/resource/image/e4/aa/e47a2c7695566ae9de6f876b5b9e54aa.png?wh=1017x515)

5. 最后我们让Visual ChatGPT描述一下图片的内容。

![图片](https://static001.geekbang.org/resource/image/75/70/756feb6e6f3c6e5858a99e880d5cdc70.png?wh=1016x528)

可以看到，Visual ChatGPT很好地完成了我们的每一条指令。而这样的交互体验大大提升了我们用AI画画的实际体验。比如，上一讲里我们通过Canny算法获取了“戴珍珠耳环的少女”画像的轮廓，然后通过ControlNet绘制了同样姿势的其他明星的头像。原本这个过程我们是通过一系列的代码来实现的，现在我们完全可以用Visual ChatGPT，通过一系列的对话向AI下达指令来实现。

首先，我们通过Upload按钮把“戴珍珠耳环的少女”图片上传上去。

![图片](https://static001.geekbang.org/resource/image/97/47/97b3e527347f353aaf12a34456934c47.png?wh=1015x615)

接着，我们在对话框里输入文本 “Generate the canny edge of the image”，Visual ChatGPT就会把上传图片的边缘提取出来，并且生成一张新的图片。

![图片](https://static001.geekbang.org/resource/image/63/61/6323d1b16737c4d0bde69c8a6c94c561.png?wh=1028x617)

最后，我们在对话框里输入 “Generate a real color Taylor Swift photo from this canny image”，Visual ChatGPT就会基于上面边缘检测的轮廓图生成一个新的人像图。

![图片](https://static001.geekbang.org/resource/image/64/29/64e7cac2d8db67cc36540498byyb2729.png?wh=1026x619)

这样，我们不需要撰写任何代码，通过一个聊天窗口就能完成对图片的编辑和修改工作。

## Visual ChatGPT的原理与实现

Visual ChatGPT的效果非常神奇，但是其实内部原理却非常简单。Visual ChatGPT解决问题的办法就是使用[第 17 讲](https://time.geekbang.org/column/article/648461)我们介绍过的LangChain的ReAct Agent模式，它做了这样几件事情。

1. 它把各种各样图像处理的视觉基础模型（Visual Foundation Model）都封装成了一个个Tool。
2. 然后，将这些Tool都交给了一个conversation-react-description类型的Agent。每次你输入文本的时候，其实就是和这个Agent在交流。Agent接收到你的文本，就要判断自己应该使用哪一个Tool，还有应该从输入的内容里提取什么参数给到这个Tool。这些输入参数中既包括需要修改哪一个图片，也包括使用什么样的提示语。这里的Agent背后使用的就是ChatGPT。
3. 最后，Agent会实际去调用这个Tool，生成一张新的图片返回给你。

那接下来，我们就进入Visual ChatGPT的代码，来看一下具体的代码是怎么做的。Visual ChatGPT的源代码只有一个文件 [visual\_chatgpt.py](https://github.com/microsoft/TaskMatrix/blob/main/visual_chatgpt.py)。整个文件从头到尾可以分成四个部分。

1. 一系列预先定义好的ChatGPT的Prompt，以及一些会被调用的辅助函数。
2. 一系列视觉模型的Class，每一个Class都代表了一个或者多个图片处理的工具。
3. 一个叫做ConversationBot的Class，实际封装了通过对话调用各种视觉模型工具的流程。
4. 实际从命令行启动整个应用的入口，其实就是对ConverationBot提供了一个Gradio应用的封装。

### Visual ChatGPT的调用入口

对于源码，我们可以倒过来从下往上看，从Visual ChatGPT的启动入口来学习代码。对应的启动代码其实很简单，就是干了两件事情。

1. 从命令行加载了load参数，并且把对应的字符串解析成一个 `load_dict`，然后通过 `load_dict` 创建了ConversationBot。

```python
if __name__ == '__main__':
    if not os.path.exists("checkpoints"):
        os.mkdir("checkpoints")
    parser = argparse.ArgumentParser()
    parser.add_argument('--load', type=str, default="ImageCaptioning_cuda:0,Text2Image_cuda:0")
    args = parser.parse_args()
    load_dict = {e.split('_')[0].strip(): e.split('_')[1].strip() for e in args.load.split(',')}
    bot = ConversationBot(load_dict=load_dict)
    ……
```

2. 然后将整个ConversationBot做成了一个有界面的Gradio应用。

```python
……
    with gr.Blocks(css="#chatbot .overflow-y-auto{height:500px}") as demo:
        lang = gr.Radio(choices = ['Chinese','English'], value=None, label='Language')
        chatbot = gr.Chatbot(elem_id="chatbot", label="Visual ChatGPT")
        state = gr.State([])
        with gr.Row(visible=False) as input_raws:
            with gr.Column(scale=0.7):
                txt = gr.Textbox(show_label=False, placeholder="Enter text and press enter, or upload an image").style(
                    container=False)
            with gr.Column(scale=0.15, min_width=0):
                clear = gr.Button("Clear")
            with gr.Column(scale=0.15, min_width=0):
                btn = gr.UploadButton(label="🖼️",file_types=["image"])

        lang.change(bot.init_agent, [lang], [input_raws, lang, txt, clear])
        txt.submit(bot.run_text, [txt, state], [chatbot, state])
        txt.submit(lambda: "", None, txt)
        btn.upload(bot.run_image, [btn, state, txt, lang], [chatbot, state, txt])
        clear.click(bot.memory.clear)
        clear.click(lambda: [], None, chatbot)
        clear.click(lambda: [], None, state)
    demo.launch(server_name="0.0.0.0", server_port=7860)
```

我们看一下load参数，其实就是指定了不同的工具类应该使用CPU还是GPU，以及对应的模型应该加载到哪一个GPU上。

```python
python visual_chatgpt.py --load "Text2Box_cuda:0,Segmenting_cuda:0,
    Inpainting_cuda:0,ImageCaptioning_cuda:0,
    Text2Image_cuda:1,Image2Canny_cpu,CannyText2Image_cuda:1,
    Image2Depth_cpu,DepthText2Image_cuda:1,VisualQuestionAnswering_cuda:2,
    InstructPix2Pix_cuda:2,Image2Scribble_cpu,ScribbleText2Image_cuda:2,
    SegText2Image_cuda:2,Image2Pose_cpu,PoseText2Image_cuda:2,
    Image2Hed_cpu,HedText2Image_cuda:3,Image2Normal_cpu,
    NormalText2Image_cuda:3,Image2Line_cpu,LineText2Image_cuda:3"
```

### ConversationBot，一个Langchain Agnet

接下来我们再来看看控制Visual ChatGPT的核心运转流程的ConversationBot是什么样的。ConversationBot里面包含了四个函数，分别是 `__init__` 的构造函数、`init_agent` 函数、`run_text` 和 `run_image` 函数。

- `__init__` 的构造函数用来加载使用的各个视觉基础模型（Visual Foundation Model）。
- `init_agent` 函数构造了一个LangChain的conversation-react-description类型的Agent，用来实际处理整个AI对话过程。
- `run_text` 处理用户的文本输入。
- `run_image` 处理用户的图片输入。

#### `__init__` 构造函数

我们先来看看 `__init__` 这个构造函数。

```python
def __init__(self, load_dict):
        # load_dict = {'VisualQuestionAnswering':'cuda:0', 'ImageCaptioning':'cuda:1',...}
        print(f"Initializing VisualChatGPT, load_dict={load_dict}")
        if 'ImageCaptioning' not in load_dict:
            raise ValueError("You have to load ImageCaptioning as a basic function for VisualChatGPT")

        self.models = {}
        # Load Basic Foundation Models
        for class_name, device in load_dict.items():
            self.models[class_name] = globals()[class_name](device=device)

        # Load Template Foundation Models
        for class_name, module in globals().items():
            if getattr(module, 'template_model', False):
                template_required_names = {k for k in inspect.signature(module.__init__).parameters.keys() if k!='self'}
                loaded_names = set([type(e).__name__ for e in self.models.values()])
                if template_required_names.issubset(loaded_names):
                    self.models[class_name] = globals()[class_name](
                        **{name: self.models[name] for name in template_required_names})
        
        print(f"All the Available Functions: {self.models}")

……
```

代码其实很简单，首先就是将前面从命令行读入的 `load_dict` 里面的每一个Class都实例化，后面我们会看到，在实例化的过程中，这些Class都会把各种预训练好的模型加载到CPU或者GPU里面来。

这其中有一个情况需要注意，有些模型Class在我们这里叫做**template\_model，其实就是能够组合多个模型组合，来解决一个单一的任务。**这些Class不是通过命令行传入的参数名称来加载的，而是去判断这个Class需要的其他模型是否都已经加载了，如果都加载了，那么这个Class自然可以用，不需要额外占用显存或者内存。否则的话，这个Class就不会被加载。

接下来就是遍历所有的这些Class，找到里面以inference开头的函数。每一个函数都会被当作是一个LangChain里面的Tool，放到当前实例的Tools数组中去。

然后就创建了Agent需要的LLM和Memory，**如果你想要用GPT-4来管理对话过程以取得更好的效果，你就可以在这里用GPT-4替换掉LLM来做到这一点**。

```python
……
        self.tools = []
        for instance in self.models.values():
            for e in dir(instance):
                if e.startswith('inference'):
                    func = getattr(instance, e)
                    self.tools.append(Tool(name=func.name, description=func.description, func=func))
        self.llm = OpenAI(temperature=0)
        self.memory = ConversationBufferMemory(memory_key="chat_history", output_key='output')
```

#### `init_agent` 函数

接下来的 `init_agent` 函数就特别简单了，它其实就是利用上面我们加载的Tools、Memory 以及 LLM 创建了一个 conversational-react-description类型的Agent。这个Agent我们在[第 17 讲](https://time.geekbang.org/column/article/648461)其实已经介绍过了一遍。

不过，这里我们通过 `agent_kwargs` 为这个Agent专门定制了对应的提示语。这部分提示语我们晚一点再介绍。这里，对于中文和英文Visual ChatGPT只是通过简单的 `if...else` 提供了一组不同的提示语而已。

```python
    def init_agent(self, lang):
        self.memory.clear() #clear previous history
        if lang=='English':
            PREFIX, FORMAT_INSTRUCTIONS, SUFFIX = VISUAL_CHATGPT_PREFIX, VISUAL_CHATGPT_FORMAT_INSTRUCTIONS, VISUAL_CHATGPT_SUFFIX
            place = "Enter text and press enter, or upload an image"
            label_clear = "Clear"
        else:
            PREFIX, FORMAT_INSTRUCTIONS, SUFFIX = VISUAL_CHATGPT_PREFIX_CN, VISUAL_CHATGPT_FORMAT_INSTRUCTIONS_CN, VISUAL_CHATGPT_SUFFIX_CN
            place = "输入文字并回车，或者上传图片"
            label_clear = "清除"
        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent="conversational-react-description",
            verbose=True,
            memory=self.memory,
            return_intermediate_steps=True,
            agent_kwargs={'prefix': PREFIX, 'format_instructions': FORMAT_INSTRUCTIONS,
                          'suffix': SUFFIX}, )
        return gr.update(visible = True), gr.update(visible = False), gr.update(placeholder=place), gr.update(value=label_clear)
```

#### `run_text` 和 `run_image` 函数

实际处理对话的 `run_text` 和 `run_image` 函数也非常简单。`run_text` 函数就是先确保Memory不要超出我们设置的上下文长度的限制。然后直接调用Agent来应对用户输入的文本。并且对于输出的结果，它只是做了一些文件名上的字符串显示的处理而已。

```python
    def run_text(self, text, state):
        self.agent.memory.buffer = cut_dialogue_history(self.agent.memory.buffer, keep_last_n_words=500)
        res = self.agent({"input": text.strip()})
        res['output'] = res['output'].replace("\\", "/")
        response = re.sub('(image/[-\w]*.png)', lambda m: f'![](file={m.group(0)})*{m.group(0)}*', res['output'])
        state = state + [(text, response)]
        print(f"\nProcessed run_text, Input text: {text}\nCurrent state: {state}\n"
              f"Current Memory: {self.agent.memory.buffer}")
        return state, state
```

而 `run_image` 函数，则是把用户上传的图片转换成完全相同的尺寸和格式。此外，它还会使用ImageCaptioning这个模型拿到图片的描述。最后，模型将图片名称和描述等信息也作为一轮对话拼接到Agent的memory里面去。

```python

    def run_image(self, image, state, txt, lang):
        image_filename = os.path.join('image', f"{str(uuid.uuid4())[:8]}.png")
        print("======>Auto Resize Image...")
        img = Image.open(image.name)
        width, height = img.size
        ratio = min(512 / width, 512 / height)
        width_new, height_new = (round(width * ratio), round(height * ratio))
        width_new = int(np.round(width_new / 64.0)) * 64
        height_new = int(np.round(height_new / 64.0)) * 64
        img = img.resize((width_new, height_new))
        img = img.convert('RGB')
        img.save(image_filename, "PNG")
        print(f"Resize image form {width}x{height} to {width_new}x{height_new}")
        description = self.models['ImageCaptioning'].inference(image_filename)
        if lang == 'Chinese':
            Human_prompt = f'\nHuman: 提供一张名为 {image_filename}的图片。它的描述是: {description}。 这些信息帮助你理解这个图像，但是你应该使用工具来完成下面的任务，而不是直接从我的描述中想象。 如果你明白了, 说 \"收到\". \n'
            AI_prompt = "收到。  "
        else:
            Human_prompt = f'\nHuman: provide a figure named {image_filename}. The description is: {description}. This information helps you to understand this image, but you should use tools to finish following tasks, rather than directly imagine from my description. If you understand, say \"Received\". \n'
            AI_prompt = "Received.  "
        self.agent.memory.buffer = self.agent.memory.buffer + Human_prompt + 'AI: ' + AI_prompt
        state = state + [(f"![](file={image_filename})*{image_filename}*", AI_prompt)]
        print(f"\nProcessed run_image, Input image: {image_filename}\nCurrent state: {state}\n"
              f"Current Memory: {self.agent.memory.buffer}")
        return state, state, f'{txt} {image_filename} '

```

### Visual Foundation Model，实际处理图片的工具

看完了ConversationBot，我们就知道其实我们向Visual ChatGPT输入的各种文本指令，都会变成对某一个视觉基础模型（Visual Foundation Model）的调用。那么，我们就挑一两个视觉基础模型，来看看具体里面是如何调用的。

我们还是拿之前我们比较熟悉的通过Canny算法进行边缘检测的CannyText2Image来演示好了。在这个Class的构造函数里，我们还是通过Diffusers的Pipeline加载了Stable Diffusion和ControlNet的模型。这样，后面我们就可以用这个Pipeline来对图片进行处理了。

另外，在构造函数的最后，它还设置了一系列正面和负面的提示语内容。负面的提示语用于排除低质量的照片，而正面的提示语则会和用户输入的提示语拼接到一起，用来生成图片。

```python
class CannyText2Image:
    def __init__(self, device):
        print(f"Initializing CannyText2Image to {device}")
        self.torch_dtype = torch.float16 if 'cuda' in device else torch.float32
        self.controlnet = ControlNetModel.from_pretrained("fusing/stable-diffusion-v1-5-controlnet-canny",
                                                          torch_dtype=self.torch_dtype)
        self.pipe = StableDiffusionControlNetPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5", controlnet=self.controlnet, safety_checker=None,
            torch_dtype=self.torch_dtype)
        self.pipe.scheduler = UniPCMultistepScheduler.from_config(self.pipe.scheduler.config)
        self.pipe.to(device)
        self.seed = -1
        self.a_prompt = 'best quality, extremely detailed'
        self.n_prompt = 'longbody, lowres, bad anatomy, bad hands, missing fingers, extra digit, ' \
                            'fewer digits, cropped, worst quality, low quality'
```

除了构造函数，这个Class还有一个inference函数。这个函数通过Prompts这个decorator定义了name和description属性，这些属性也是我们实际加载Tools的时候使用的参数。Agent就会根据这些描述判断用户输入的文本是否应该使用当前这个工具。比如这里 CannyText2Image的description里，就告诉你用户一般会通过“generate a real image of a object or something from this canny image” 这样的指令来调用当前的工具。

而对应的inference函数的内容，就是简单地根据输入的文本调用模型来处理图片。不过要注意，这里作为输入的Inputs文本，并不是用户原始输入的内容。而是通过ConversationBot的Agent，经过“思考”之后拿到的Action Inputs。这个Inputs里面，既会包含需要处理的图片路径，也会包含对应的Prompts。

```python
    @prompts(name="Generate Image Condition On Canny Image",
             description="useful when you want to generate a new real image from both the user description and a canny image."
                         " like: generate a real image of a object or something from this canny image,"
                         " or generate a new real image of a object or something from this edge image. "
                         "The input to this tool should be a comma separated string of two, "
                         "representing the image_path and the user description. ")
    def inference(self, inputs):
        image_path, instruct_text = inputs.split(",")[0], ','.join(inputs.split(',')[1:])
        image = Image.open(image_path)
        self.seed = random.randint(0, 65535)
        seed_everything(self.seed)
        prompt = f'{instruct_text}, {self.a_prompt}'
        image = self.pipe(prompt, image, num_inference_steps=20, eta=0.0, negative_prompt=self.n_prompt,
                          guidance_scale=9.0).images[0]
        updated_image_path = get_new_image_name(image_path, func_name="canny2image")
        image.save(updated_image_path)
        print(f"\nProcessed CannyText2Image, Input Canny: {image_path}, Input Text: {instruct_text}, "
              f"Output Text: {updated_image_path}")
        return updated_image_path
```

当然，不是所有模型Class的inference函数都这么简单。有些Class，特别是我们前面介绍过的template\_model的Class，它的inference函数会复杂一些，需要多次调用多个模型组合来完成任务。比如InfinityOutPainting这个Class，就需要不断循环调用VisualQuestionAnswering和ImageCaption来获取图片的描述，然后通过Inpainting来补全图片中没有画出来的部分，最终实现把图片无限扩大，补全扩大出来的部分背景的能力。

### 复盘Prompt，理解Task Matrix机制

我们刚才说过，每个Class模型拿到的inputs输入都是模型“思考”之后根据用户输入提取出来的Action Inputs。这一点，其实还是要归功于ChatGPT强大的逻辑推理能力。我们只要回到代码的开头，看一下对应的Prompts其实就能知道Visual ChatGPT是怎么做到的了。实际上，每次用户输入的内容，都是通过VISUAL\_CHATGPT\_PREFIX、VISUAL\_CHATGPT\_FORMAT\_INSTRUCTIONS和VISUAL\_CHATGPT\_SUFFIX这三段Prompts拼接而成的。

而AI的思考过程，其实就是VISUAL\_CHATGPT\_FORMAT\_INSTRUCTIONS这一小段。

```python
VISUAL_CHATGPT_FORMAT_INSTRUCTIONS = """To use a tool, please use the following format:

Thought: Do I need to use a tool? Yes
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action

When you have a response to say to the Human, or if you do not need to use a tool, you MUST use the format:

Thought: Do I need to use a tool? No
{ai_prefix}: [your response here]

"""
```

这个其实就是我在[第 17 讲](https://time.geekbang.org/column/article/648461)里给你看过的MRKL的提示语模版。AI通过Thought、Action、Action Input 和 Observation 这样的四轮循环，完成一次Tools的判定与调用。并且，每次给到Agent的输入里，都可以包含多个迭代的Action和Action Input，调用多次模型Class来解决问题。

## 小结

看完这个代码之后，相信你完全有能力修改代码满足自己的需求了。如果有一天出现了一个更好用的视觉基础模型，你完全可以把这个新的模型Class加入到Visual ChatGPT中。你只需要通过 `__init__` 函数加载模型，然后定义好它对应的提示语以及inference函数，就能让Visual ChatGPT支持一种新的图片编辑和绘制功能了。

![](https://static001.geekbang.org/resource/image/a8/f8/a8073d98yy964983cc03c35deb0a42f8.png?wh=2284x1560 "来自 Visual ChatGPT 论文中的图 1")

回顾整个Visual ChatGPT的代码，其实并不复杂。它就是将[第 17 讲](https://time.geekbang.org/column/article/648461)我们介绍过的LangChain的Agent，和过去3讲我们介绍的各种视觉大模型组合起来，通过ChatGPT的语言和逻辑推理能力处理用户输入，通过LangChain的Agent机制来调度推理过程和工具的使用，通过视觉大模型实际来处理图片以及理解图片的内容。

这样的机制其实不仅可以用来处理图片，也可以用在其他机器学习的模型里，比如语音、视频，甚至你还可以利用它再去调用别的大语言模型。而这个机制，后来也被微软进一步扩展到Task Matrix这个概念里。Visual ChatGPT的代码库的名称今天也被改成了Task Matrix，也就是“任务矩阵”的意思。

## 思考题

最后，按照惯例还是给你留一道思考题。

Stable Diffusion的提示语是不支持中文的，但是Visual ChatGPT支持你通过中文输入你对图片的绘制和修改要求。你觉得它目前的实现有没有什么问题？如果我们想要让它不只支持中文和英文，也能支持德文、法文、西班牙文等各个语种，我们可以怎么做？欢迎你把思考后的结果分享到评论区，我们一起讨论，也欢迎你把这一讲分享给需要的朋友，我们下一讲再见！

## 推荐阅读

在Visual ChatGPT之后，微软更进一步将这个概念扩展成为Task Matrix，也对应发表了一篇[论文](https://arxiv.org/abs/2303.16434)。你有兴趣的话，可以去阅读一下。
<div><strong>精选留言（7）</strong></div><ul>
<li><span>Toni</span> 👍（11） 💬（1）<p>人工智能的快速发展带来各类相关模型的数量爆炸性增长，选择的多样性使得应用者总能挑选出几样趁手的工具，但同时也带来了一大痛点，哪个模型是最好的呢? Visual ChatGPT 的核心板块&quot;任务矩阵&quot;(Task Matrix)就是想为客户自动选出适合解决任务的模型。诚如论文的作者指出的&quot;TaskMatrix.AI 可以理解这些 API 并学习新的 API，然后根据用户说明推荐合适的API。作者举例中的用对话的形式帮助用户生成 PPT, 并根据要求不断修改，展示了 TaskMatrix.AI 方便之处，过程流畅，但实际上这里隐含了一个前提，即用户的问题非常明确，比如: &quot;对于每家公司，让我们创建一张幻灯片来介绍它的创始人、位置、使命、产品、子公司&quot; (Fig.6, 7)，在这样的情况下，TaskMatrix.AI 能给出准确的反应; 还有 Fig.3 的绘图任务，Fig.9 的智能家居场景也是如此。

ChatGPT3.5 以后的版本 AI 能够表现出很强的&quot;推理能力&quot;，这一能力本质是将自然语言中的&#39;字&#39;，&#39;语义&#39;，&#39;句子&#39;，&#39;位置&#39;，&#39;段落&#39; 等，经过大量的监督的无监督的&quot;阅读学习&quot;，在映射的高维空间中不断调整优化所形成的不断&quot;进化&quot;的模型，然后根据人们给出的问题或曰提示，&quot;猜出&quot;或称&quot;推断出&quot;后面的意思。通常情况下 AI有亮丽的表现，虽然不免夸夸其谈。但这带来 AI 另一大痛点，它不能对不清楚的问题进行反问。比如在用户提出这样的问题时:&quot;你知道如何从头开始写一篇文章并提供给我一个解决方案大纲？ 我有几篇论文的截止日期。 我只有题目以及每个的一些要点。 最好在其中包含图像。&quot;(Fig.4) TaskMatrix.AI 并没有提问&quot;你的题目是什么?&quot;，而是直接开聊。

AI 日新月异，各种模型为应对使用痛点而生，期待。

老师已先人一步用上ChatGPT4，它有反问或帮助用户捋清问题思路的能力了吗?</p>2023-05-10</li><br/><li><span>王永旺</span> 👍（3） 💬（1）<p>Semantic Kernel 老师有了解么，能不能也介绍一下这个项目？
</p>2023-05-10</li><br/><li><span>yu</span> 👍（2） 💬（1）<p>剛看完先留言：先讓他判斷用戶的語言，然後翻譯成英文處理。</p>2023-05-16</li><br/><li><span>金</span> 👍（1） 💬（1）<p>有编辑音频的chatgpt吗？最近ai孙燕姿很火，效果也不错，但是跟本人唱的还是差一些东西，旋律比较平，有办法调教吗？</p>2023-05-10</li><br/><li><span>peter</span> 👍（0） 💬（1）<p>请教老师：网站想提供几首歌，是否有合适的软件能实现？即用软件唱歌，声音随便，用人声或机器自己产生的声音都可以。不仅仅限于chatGPT；如果chatGPT没有该功能，是否有其他软件能实现？</p>2023-05-10</li><br/><li><span>极客用户</span> 👍（0） 💬（0）<p>思考题答案：加一层能进行语种翻译的大模型就可以了</p>2024-12-01</li><br/><li><span>张开元</span> 👍（0） 💬（0）<p>Visual ChatGPT的计算量和效果怎么样能平衡？</p>2023-09-15</li><br/>
</ul>