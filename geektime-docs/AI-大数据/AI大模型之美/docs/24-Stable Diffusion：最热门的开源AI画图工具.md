你好，我是徐文浩。

[上一讲](https://time.geekbang.org/column/article/653489)，我们一起体验了CLIP这个多模态的模型。在这个模型里，我们已经能够把一段文本和对应的图片关联起来了。看到文本和图片的关联，想必你也能联想到过去半年非常火热的“文生图”（Text-To-Image）的应用浪潮了。相比于在大语言模型里OpenAI的一枝独秀。文生图领域就属于百花齐放了，OpenAI陆续发表了DALL-E和 [DALL-E 2](https://labs.openai.com/)，Google也不甘示弱地发表了 [Imagen](https://imagen.research.google/)，而市场上实际被用得最多、反馈最好的用户端产品是 [Midjourney](https://midjourney.com/home/)。

不过，在整个技术社区里，最流行的产品则是Stable Diffusion。因为它是一个完全开源的产品，我们不仅可以调用Stable Diffusion内置的模型来生成图片，还能够下载社区里其他人训练好的模型来生成图片。我们不仅可以通过文本来生成图片，还能通过图片来生成图片，通过文本来编辑图片。

那么今天这一讲，我们就来看看如何使用Stable Diffusion，做到上面这些事情。

## 使用Stable Diffusion生成图片

### 文生图

可能你还没怎么体验过文生图的应用，那我们先用几行最简单的代码体验一下。在这一讲里，我建议一定要用Colab或者其他的GPU环境，因为用CPU来执行的话，速度会慢到让人无法接受。

安装依赖包：

```python
%pip install diffusers accelerate transformers
```

代码：

```python
from diffusers import DiffusionPipeline
pipeline = DiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
pipeline.to("cuda")
image = pipeline("a photograph of an astronaut riding a horse").images[0]
image
```

输出结果：  
![图片](https://static001.geekbang.org/resource/image/72/57/7217f995c7fd7143ef6807d8e0dfc057.png?wh=512x512)

代码非常简单，只有寥寥几行。这里，我们使用了Huggingface的Diffusers库，通过DiffusionPipeline加载了RunwayML的stable-diffusion-v1-5的模型。然后，指定了这个Pipeline使用CUDA也就是利用GPU来进行计算。最后向这个Pipeline输入了一段文本，通过这段文本我们就生成了一张图片。

这里，我们画的是在Stable Diffusion里非常经典的一张“宇航员在太空骑马”的图片。之所以画这么一张图片，是为了证明我们并不是通过“搜索”的方式找到一张已经存在的图片。比如，上一讲里我们介绍过CLIP模型，其实就可以完成从文本到图片的搜索功能。而Stable Diffusion，是真的让AI“画”出来一张新的图片。毕竟，以前宇航员也从来没有在太空骑过马，也不可能有人拍下过这样的照片。

### Stable Diffusion的基本原理

Stable Diffusion生成的图片效果的确不错，相信你也很好奇这个事情的原理是什么。其实，Stable Diffusion背后不是单独的一个模型，而是由多个模型组合而成的。整个Stable Diffusion文生图的过程是由这样三个核心模块组成的。

- 第一个模块是一个Text-Encoder，把我们输入的文本变成一个向量。实际使用的就是我们上一讲介绍的CLIP模型。因为CLIP模型学习的是文本和图像之间的关系，所以得到的这个向量既理解了文本的含义，又能和图片的信息关联起来。
- 第二个是Generation模块，顾名思义是一个图片信息生成模块。这里也有一个机器学习模型，叫做UNet，还有一个调度器（Scheduler），用来一步步地去除噪声。这个模块的工作流程是先往前面的用CLIP模型推理出来的向量里添加很多噪声，再通过UNet+Scheduler逐渐去除噪声，最后拿到了一个新的张量。这个张量可以认为是一个尺寸上缩小了的图片信息向量，里面隐含了我们要生成的图片信息。
- 最后一个模块，则是Decoder或者叫做解码器。背后也是一个机器学习的模型，叫做VAE。它会根据第二步的返回结果把这个图像信息还原成最终的图片。

这个过程，你可以结合Stable Diffusion相关论文里的一张模型架构图来看。

![图片](https://static001.geekbang.org/resource/image/4c/cb/4ca19441686120b9c28c8d5ba11baacb.png?wh=598x310)

这样听起来可能有点太理论了，那我们还是看看具体的代码和图片生成的过程吧，这样就比较容易理解图片是怎么生成的了。

我们先把DiffusionPipeline打印出来，看看它内部是由哪些部分组成的。

```python
pipeline
```

输出结果：

```python
StableDiffusionPipeline {
  "_class_name": "StableDiffusionPipeline",
  "_diffusers_version": "0.15.1",
  "feature_extractor": [
    "transformers",
    "CLIPFeatureExtractor"
  ],
  "requires_safety_checker": true,
  "safety_checker": [
    "stable_diffusion",
    "StableDiffusionSafetyChecker"
  ],
  "scheduler": [
    "diffusers",
    "PNDMScheduler"
  ],
  "text_encoder": [
    "transformers",
    "CLIPTextModel"
  ],
  "tokenizer": [
    "transformers",
    "CLIPTokenizer"
  ],
  "unet": [
    "diffusers",
    "UNet2DConditionModel"
  ],
  "vae": [
    "diffusers",
    "AutoencoderKL"
  ]
}
```

这个对象里面有3部分。

1. Tokenizer和Text\_Encoder，就是我们上面说的把文本变成向量的Text Encoder。可以看到我们这里用的模型就是上一讲的CLIP模型。
2. UNet和Scheduler，就是对文本向量以及输入的噪声进行噪声去除的组件，也就是Generation模块。这里用的是UNet2DConditionModel模型，还把PNDMScheduler用作了去除噪声的调度器。
3. VAE，也就是解码器（Decoder），这里用的是AutoencoderKL，它会根据上面生成的图片信息最后还原出一张高分辨率的图片。

剩下的feature\_extractor，可以用来提取图像特征，如果我们不想文生图，想要图生图，它就会被用来把我们输入的图片的特征提取成为向量。而safety\_checker则是用来检查生成内容，避免生成具有冒犯性的图片。

接下来，我们就自己来组合一下这些模型，来把整个图片生成的过程给演示出来。首先，我们把上面Stable Diffusion 1.5需要的模型组件都加载出来。

```python
from transformers import CLIPTextModel, CLIPTokenizer
from diffusers import AutoencoderKL, UNet2DConditionModel, PNDMScheduler

vae = AutoencoderKL.from_pretrained("runwayml/stable-diffusion-v1-5", subfolder="vae")
tokenizer = CLIPTokenizer.from_pretrained("openai/clip-vit-large-patch14")
text_encoder = CLIPTextModel.from_pretrained("openai/clip-vit-large-patch14")
unet = UNet2DConditionModel.from_pretrained("runwayml/stable-diffusion-v1-5", subfolder="unet")
scheduler = PNDMScheduler.from_pretrained("runwayml/stable-diffusion-v1-5", subfolder="scheduler")

torch_device = "cuda"
vae.to(torch_device)
text_encoder.to(torch_device)
unet.to(torch_device)
```

**注意，对应的CLIPTokenizer和CLIPTextModel的名字并不是stable-diffusion-v1-5，如果使用Diffusers库的Pipeline的话，可以从模型里面对应模块的 [config.json](https://huggingface.co/runwayml/stable-diffusion-v1-5/blob/main/text_encoder/config.json) 读取到它们。**

然后，我们把接下来生成图片的参数初始化一下，包括文本、对应的图片分辨率，以及一系列模型中需要使用的超参数。

```python
import torch

prompt = ["a photograph of an astronaut riding a horse"]
height = 512  # default height of Stable Diffusion
width = 512  # default width of Stable Diffusion
num_inference_steps = 25  # Number of denoising steps
guidance_scale = 7.5  # Scale for classifier-free guidance
generator = torch.manual_seed(42)  # Seed generator to create the inital latent noise
batch_size = len(prompt)
```

然后，我们把对应的输入文本变成一个向量，然后再根据一个空字符串生成一个“无条件”的向量，最后把两个向量拼接在一起。我们实际生成图片的过程，就是逐渐从这个无条件的向量向输入文本表示的向量靠拢的过程。

```python
text_input = tokenizer(
    prompt, padding="max_length", max_length=tokenizer.model_max_length, truncation=True, return_tensors="pt"
)

with torch.no_grad():
    text_embeddings = text_encoder(text_input.input_ids.to(torch_device))[0]

max_length = text_input.input_ids.shape[-1]
uncond_input = tokenizer([""] * batch_size, padding="max_length", max_length=max_length, return_tensors="pt")
uncond_embeddings = text_encoder(uncond_input.input_ids.to(torch_device))[0]

text_embeddings = torch.cat([uncond_embeddings, text_embeddings])
```

然后，我们可以先生成一系列随机噪声。

```python
latents = torch.randn(
    (batch_size, unet.in_channels, height // 8, width // 8),
    generator=generator,
)
latents = latents.to(torch_device)

latents = latents * scheduler.init_noise_sigma
```

接下来就是生成图片的代码了，我们先定义两个函数，它们会分别显示Generation模块生成出来的图片信息，以及Decoder模块还原出来的最终图片。

```python
import PIL
import torch
import numpy as np
from PIL import Image
from IPython.display import display

def display_denoised_sample(sample, i):
    image_processed = sample.cpu().permute(0, 2, 3, 1)
    image_processed = (image_processed + 1.0) * 127.5
    image_processed = image_processed.numpy().astype(np.uint8)

    image_pil = PIL.Image.fromarray(image_processed[0])
    display(f"Denoised Sample @ Step {i}")
    display(image_pil)
    return image_pil

def display_decoded_image(latents, i):
  # scale and decode the image latents with vae
  latents = 1 / 0.18215 * latents
  with torch.no_grad():
    image = vae.decode(latents).sample
    image = (image / 2 + 0.5).clamp(0, 1)
    image = image.detach().cpu().permute(0, 2, 3, 1).numpy()
    images = (image * 255).round().astype("uint8")
    pil_images = [Image.fromarray(image) for image in images]
    display(f"Decoded Image @ step {i}")
    display(pil_images[0])
    return pil_images[0]
```

最后，我们通过Diffusion算法一步一步来生成图片就好了。我们根据前面指定的参数，循环了25步，每一步都通过Scheduler和UNet来进行图片去噪声的操作。并且每5步都把对应去噪后的图片信息，以及解码后还原的图片显示出来。

```python
from tqdm.auto import tqdm

scheduler.set_timesteps(num_inference_steps)

denoised_images = []
decoded_images = []
for i, t in enumerate(tqdm(scheduler.timesteps)):
    # expand the latents if we are doing classifier-free guidance to avoid doing two forward passes.
    latent_model_input = torch.cat([latents] * 2)

    latent_model_input = scheduler.scale_model_input(latent_model_input, timestep=t)

    # predict the noise residual
    with torch.no_grad():
        noise_pred = unet(latent_model_input, t, encoder_hidden_states=text_embeddings).sample

    # perform guidance
    noise_pred_uncond, noise_pred_text = noise_pred.chunk(2)
    noise_pred = noise_pred_uncond + guidance_scale * (noise_pred_text - noise_pred_uncond)

    # compute the previous noisy sample x_t -> x_t-1
    latents = scheduler.step(noise_pred, t, latents).prev_sample
    if i % 5 == 0:
      denoised_image = display_denoised_sample(latents, i)
      decoded_image = display_decoded_image(latents, i)
      denoised_images.append(denoised_image)
      decoded_images.append(decoded_image)
```

输出结果：

```plain
Denoised Sample @ Step 0
```

![图片](https://static001.geekbang.org/resource/image/e8/77/e8fa98c88172482a84f3dbfeb0ecdf77.png?wh=64x64)

```plain
Decoded Image @ step 0
```

![图片](https://static001.geekbang.org/resource/image/e2/b9/e2ef3c2972d3b73a3c93976ce19a6fb9.png?wh=512x512)

```plain
Denoised Sample @ Step 5
```

![图片](https://static001.geekbang.org/resource/image/7e/c1/7e385e61f741f470c490c39d41b0c3c1.png?wh=64x64)

```plain
Decoded Image @ step 5
```

![图片](https://static001.geekbang.org/resource/image/b8/dd/b81cb29b003412c80519c7b9f01baedd.png?wh=512x512)

```plain
Denoised Sample @ Step 10
```

![图片](https://static001.geekbang.org/resource/image/fd/06/fd262baafbb52271b0d906d00a167c06.png?wh=64x64)

```plain
Decoded Image @ step 10
```

![图片](https://static001.geekbang.org/resource/image/a6/22/a6be734e2813e80b8bd8b936c0741a22.png?wh=512x512)

```plain
Denoised Sample @ Step 15
```

![图片](https://static001.geekbang.org/resource/image/04/8c/04e1da57c913da86b83a6e30ddc1338c.png?wh=64x64)

```plain
Decoded Image @ step 15
```

![图片](https://static001.geekbang.org/resource/image/88/88/888d083873245d5b08780f52d8990788.png?wh=512x512)

```plain
Denoised Sample @ Step 20
```

![图片](https://static001.geekbang.org/resource/image/8a/b3/8a8ee2751036cfe7yy6e2c0d70104bb3.png?wh=64x64)

```plain
Decoded Image @ step 20
```

![图片](https://static001.geekbang.org/resource/image/8f/f7/8f094d4deacec42876201388c2ab24f7.png?wh=512x512)

```plain
Denoised Sample @ Step 25
```

![图片](https://static001.geekbang.org/resource/image/6a/a3/6a4c08550f36f249ac495e4f966a90a3.png?wh=64x64)

```plain
Decoded Image @ step 25
```

![图片](https://static001.geekbang.org/resource/image/e3/37/e3de66377a02e3db266ced384de8b337.png?wh=512x512)

运行完程序，你就可以看到我们的图片是如何一步步从完全的噪点还原成一张图片的了。而且你仔细观察，还可以看到Generation生成的图像信息，类似于Decoder还原出来的图像信息的轮廓。这是因为U-Net其实是一个图片语义分割的模型。

而如果我们打印一下生成的图片的维度，你也可以看到，Generation生成的图像信息分辨率只有64x64，而我们还原出来的图片分辨率是512x512。

```plain
print(latents.shape)
latents = 1 / 0.18215 * latents
with torch.no_grad():
    image = vae.decode(latents).sample
    print(image.shape)
```

输出结果：

```plain
torch.Size([1, 4, 64, 64])
torch.Size([1, 3, 512, 512])
```

### 图生图

相信你已经理解了这个Stable Diffusion生成图片的过程，以及过程里每个模块的工作了。那你应该比较容易理解如何通过Stable Diffusion实现图生图了，我们下面就来具体看一看。

当然，这一次我们就不用自己一步步调用各个模块来实现图生图了。我们可以直接使用Diffusers库里自带的Pipeline。

```plain
import torch
from PIL import Image
from io import BytesIO

from diffusers import StableDiffusionImg2ImgPipeline

device = "cuda"
model_id_or_path = "runwayml/stable-diffusion-v1-5"
pipe = StableDiffusionImg2ImgPipeline.from_pretrained(model_id_or_path, torch_dtype=torch.float16)
pipe = pipe.to(device)

image_file = "./data/sketch-mountains-input.jpg"

init_image = Image.open(image_file).convert("RGB")
init_image = init_image.resize((768, 512))

prompt = "A fantasy landscape, trending on artstation"

images = pipe(prompt=prompt, image=init_image, strength=0.75, guidance_scale=7.5).images

display(init_image)
display(images[0])
```

输出结果：  
![图片](https://static001.geekbang.org/resource/image/d2/2c/d262d17cb96yyd721eeca30c70e40c2c.png?wh=768x512)

![图片](https://static001.geekbang.org/resource/image/71/e4/712c084e85b258ceeb2ca64c8d043fe4.png?wh=768x512)

对应的代码也非常简单，我们把Pipeline换成了StableDiffusionImg2ImgPipeline，此外除了输入一段文本之外，我们还提供了一张草稿图。然后，你可以看到对应生成的图片的轮廓，就类似于我们提供的草稿图。而图片的内容风格，则是按照我们文本提示语的内容生成的。

StableDiffusionImg2ImgPipeline的生成过程，其实和我们之前拆解的一步步生成图片的过程是相同的。**唯一的一个区别是，我们其实不是从一个完全随机的噪声开始的，而是把对应的草稿图，通过VAE的编码器，变成图像生成信息，又在上面加了随机的噪声。**所以，去除噪音的过程中，对应的草稿图的轮廓就会逐步出现了。而在一步步生成图片的过程中，内容又会向我们给出的提示语的内容来学习。

而如果我们换一下提示语，就能更改生成的具体内容。比如我们想换成宫崎骏的风格，并且希望后面高耸的不是山，而是城堡，出现的图片还是相同的轮廓，但是用不同的内容。我在下面给出了一个代码示例，你可以自己看一看。

```plain
prompt = "ghibli style, a fantasy landscape with castles"
images = pipe(prompt=prompt, image=init_image, strength=0.75, guidance_scale=7.5).images

display(init_image)
display(images[0])
```

输出结果：  
![图片](https://static001.geekbang.org/resource/image/bb/ff/bb7a09c91feda214ee71a57d3ab479ff.png?wh=768x512)

![图片](https://static001.geekbang.org/resource/image/b8/de/b8c0054e8abc08a5657f8a6f9c6afede.png?wh=768x512)

### 更多使用方法

理解了Stable Diffusion的基本框架，你可以试一试更多相关的Pipeline的用法。比如，除了引导内容生成的提示语，我们还可以设置一个负面的提示语（negative prompt），也就是排除一些内容。

```plain
prompt = "ghibli style, a fantasy landscape with castles"
negative_prompt = "river"
images = pipe(prompt=prompt, negative_prompt=negative_prompt, image=init_image, strength=0.75, guidance_scale=7.5).images

display(images[0])
```

输出结果：  
![图片](https://static001.geekbang.org/resource/image/2b/1c/2b9ce1b91e306d256fc29dc13d68d51c.png?wh=768x512)

可以看到，我们希望在图片里面尽量排除“River”。而新生成的图片，右边就没有了任何类似于河流的内容，而中间蓝色的部分也更像一个排水渠而不是自然的河流。负面提示语并不会改变模型的结构。它其实就是把原先的“无条件”向量，替换成了负面提示语的向量。这样，模型就尽可能从负面的提示语文本内容中向我们正面的提示语文本内容学习，也就是尽量远离负面提示语的内容。

同样，我们还可以通过Stable Diffusion来提升图片的分辨率，只不过需要一个单独的模型。这个模型就是专门在一个高低分辨率的图片组合上训练出来的。对应的UNet和VAE的模型是和原始的Stable Diffusion不一样的。

```plain
from diffusers import StableDiffusionUpscalePipeline

# load model and scheduler
model_id = "stabilityai/stable-diffusion-x4-upscaler"
pipeline = StableDiffusionUpscalePipeline.from_pretrained(
    model_id, revision="fp16", torch_dtype=torch.float16
)
pipeline = pipeline.to("cuda")

# let's download an  image
low_res_img_file = "./data/low_res_cat.png"
low_res_img = Image.open(low_res_img_file).convert("RGB")
low_res_img = low_res_img.resize((128, 128))

prompt = "a white cat"

upscaled_image = pipeline(prompt=prompt, image=low_res_img).images[0]

low_res_img_resized = low_res_img.resize((512, 512))

display(low_res_img_resized)
display(upscaled_image)
```

输出结果：  
![图片](https://static001.geekbang.org/resource/image/f4/c4/f47e50c28203eb7a0d8f7667f69023c4.png?wh=512x512)

![图片](https://static001.geekbang.org/resource/image/2b/b6/2be70a657f415b11489afa86639faeb6.png?wh=512x512)

如果我们打印一下pipeline，对应的模型的组件还是相同的。

```plain
pipeline
```

输出结果：

```plain
StableDiffusionUpscalePipeline {
  "_class_name": "StableDiffusionUpscalePipeline",
  "_diffusers_version": "0.15.1",
  "low_res_scheduler": [
    "diffusers",
    "DDPMScheduler"
  ],
  "max_noise_level": 350,
  "scheduler": [
    "diffusers",
    "DDIMScheduler"
  ],
  "text_encoder": [
    "transformers",
    "CLIPTextModel"
  ],
  "tokenizer": [
    "transformers",
    "CLIPTokenizer"
  ],
  "unet": [
    "diffusers",
    "UNet2DConditionModel"
  ],
  "vae": [
    "diffusers",
    "AutoencoderKL"
  ]
}
```

但是如果你去看对应模型的配置文件，可以看到 [VAE](https://huggingface.co/stabilityai/stable-diffusion-x4-upscaler/blob/main/vae/config.json) 和 [UNet](https://huggingface.co/stabilityai/stable-diffusion-x4-upscaler/blob/main/unet/config.json) 里使用的模型都是不一样的。

## 使用社区里的其他模型

在这个过程中，你可以看到Stable Diffusion并不是指某一个特定的模型，而是指一类模型结构。因为Stable Diffusion是完全开源的，所以你大可以利用自己的数据去训练一个属于自己的模型。事实上，市面上开源训练出来的Stable Diffusion的模型非常多，也已经有了像 [CIVITAI](https://civitai.com/) 这样的分享Stable Diffusion模型的平台。

![图片](https://static001.geekbang.org/resource/image/a1/4d/a119771cc79yyf74d283a195c663c04d.png?wh=1240x1213 "CIVITAI 里有用户们自己训练的各种风格的模型")

我们可以去CIVITAI的网站，找到我们喜欢的模型。比如我们专门找一个二次元的模型 [counterfeit-V2.5](https://civitai.com/models/4468/counterfeit-v25)。在对应的模型页面，我们可以看到它直接就包含了Huggingface里面的模型。

![图片](https://static001.geekbang.org/resource/image/2c/15/2cd2d729e7ac70e0f829c319d85a1715.png?wh=1240x730)

所以我们就可以直接通过Diffuers库来调用这个模型。

```plain
pipeline.to("cuda")

prompt = "((masterpiece,best quality)),1girl, solo, animal ears, rabbit, barefoot, knees up, dress, sitting, rabbit ears, short sleeves, looking at viewer, grass, short hair, smile, white hair, puffy sleeves, outdoors, puffy short sleeves, bangs, on ground, full body, animal, white dress, sunlight, brown eyes, dappled sunlight, day, depth of field"
negative_prompt = "EasyNegative, extra fingers,fewer fingers,"
image = pipeline(prompt=prompt, negative_prompt=negative_prompt).images[0]
image
```

输出结果：

![图片](https://static001.geekbang.org/resource/image/03/50/03041115b93c8d53ed71fd2ff7fcf750.png?wh=512x512)

当然，不是所有CIVITAI里的模型都在Huggingface上提供了自己的模型版本。默认CIVITAI的模型，往往只是提供了一个模型权重文件。你可以使用现在最流行的 [Stable-Diffusion-Web-UI 应用](https://github.com/AUTOMATIC1111/stable-diffusion-webui)来使用这个模型权重文件。你可以把Web-UI在本地部署起来，它会提供一个图形界面让你不用写代码就可以直接调整各种参数来生成图片。

![图片](https://static001.geekbang.org/resource/image/61/1d/616244d69ed59bb3e8935ec7fbfba91d.png?wh=1236x966 "来自 stable-diffusion-web-ui 的图形界面")

[CIVITAI 的 Wiki](https://github.com/civitai/civitai/wiki) 里面也详细提供了在Stable-Diffusion-Web-UI里面使用模型的步骤，你可以照着这个步骤多拿几个模型试试看。

## 小结

好了，这就是今天的主要内容，最后我们一起来回顾一下。

这一讲，我带着你体验了一下Stable Diffusion这个图片生成的开源模型。我们不仅通过Diffusers这个封装好的Python库，体验了文生图、图生图、提升图片分辨率等一系列应用，也深入到Stable Diffusion的模型内部，理解了整个模型的结构，还看到我们是如何一步步从一张全是噪点的图片，逐渐去除噪声变成一张可用的图片的。

在体验了基础的模型之后，我们也一起尝试了一下其他爱好者自己生成的模型。这也是下一讲我们要介绍的重点内容。我们会了解到如何通过 LoRa 这样的算法进行模型微调，以及如何通过ControlNet让我们生成的图片更加可控。

## 思考题

最后，按照惯例还是给你留一道思考题。除了今天给你演示的这些应用之外，HuggingFace还提供了很多实战场景。比如，你就可以通过 [StableDiffusionInpaintPipeline](https://huggingface.co/docs/diffusers/using-diffusers/inpaint)，用一个遮照图片和一段提示语来修改图片画面中的某一部分元素。

你可以照着[官方文档](https://huggingface.co/docs/diffusers/using-diffusers/inpaint)，体验一下这个功能，研究一下源代码，想想这个功能是如何通过Stable Diffusion的模型结构实现的。欢迎你把你体验之后的感受以及思考后的结果分享在评论区，也欢迎你把这一讲分享给感兴趣的朋友，我们下一讲再见！

## 推荐阅读

这一讲里，我们只是简单介绍了一下Stable Diffusion的模型结构。其实，无论是DALL-E 2还是Imagen，采用的图片生成方式都是和Stable Diffusion类似的。如果你想要深入了解一下这些模型的结构，可以去看一下B站里面“跟李沐学AI”里面对于 [DALL-E 2 论文的讲解](https://www.bilibili.com/video/BV17r4y1u77B/?spm_id_from=333.999.0.0)。
<div><strong>精选留言（15）</strong></div><ul>
<li><span>东方奇骥</span> 👍（9） 💬（3）<p>老师，为什么要加了噪声，再去除噪声？</p>2023-05-05</li><br/><li><span>peter</span> 👍（2） 💬（5）<p>请教老师几个问题：
Q1：stable Diffusion采用的CLIP是自身的吗？还是调用chatGPT？
Q2：先加噪声，再去掉，有什么意义？吃一口再吐一口，有意思吗？
“先往前面的用 CLIP 模型推理出来的向量里添加很多噪声，再通过 UNet+Scheduler 逐渐去除噪声，最后拿到了一个新的张量”。
Q3：本课的代码是在本机上运行的吗？我的笔记本上是普通配置，能运行并生成图吗？（或者，图的生成是调用了某个服务器？）
Q4：可以对图片进行加工吗？ 比如在一个照片的头上加一个帽子。</p>2023-05-06</li><br/><li><span>一叶</span> 👍（0） 💬（2）<p>老师 如何 手动把模型下载,然后再上传到服务器 ? 我服务器本地liunx的,发现下载很慢..... DiffusionPipeline.from_pretrained</p>2023-05-10</li><br/><li><span>厚积薄发</span> 👍（0） 💬（2）<p>CUDA out of memory. Tried to allocate 20.00 MiB (GPU 0; 14.75 GiB total capacity; 13.46 GiB 
already allocated; 10.81 MiB free; 13.46 GiB reserved in total by PyTorch) If reserved memory is &gt;&gt; allocated 
memory try setting max_split_size_mb to avoid fragmentation.  See documentation for Memory Management and 
PYTORCH_CUDA_ALLOC_CONF   老师，colab gpu不够了，默认的16g不够，是不是需要购买更大的gpu</p>2023-05-08</li><br/><li><span>Oli张帆</span> 👍（0） 💬（2）<p>请教一下老师，结合您之前讲的HuggingFace，我可以通过HuggingFace，免费调用Stable Diffusion的接口，来产生大量的图片。那这整个流程中需要的大量算力，是谁来买单的呢？</p>2023-05-06</li><br/><li><span>Toni</span> 👍（0） 💬（10）<p>1. 使用 GPU 无疑会加快图像的生成，但实在没有办法使用 GPU 时，就用 CPU，只要将下面代码中的 &quot;cuda&quot; 改成 &quot;cpu&quot; 即可，慢比没有强。

pipeline.to(&quot;cuda&quot;) =&gt; pipeline.to(&quot;cpu&quot;) 
---------------------
from diffusers import DiffusionPipeline
pipeline = DiffusionPipeline.from_pretrained(&quot;runwayml&#47;stable-diffusion-v1-5&quot;)
pipeline.to(&quot;cpu&quot;)

image = pipeline(&quot;Sports car, road, rural areas, blue sky, white clouds, endless grassland in the background&quot;).images[0]
image

--------------
生成上面的图在 cpu 条件下约10分钟。

2. 描述图像的 prompt 如果太长会报错， 比如
Token indices sequence length is longer than the specified maximum sequence length for this model (161 &gt; 77). 

程序会继续运行，但输出结果是黑板。
Potential NSFW content was detected in one or more images. A black image will be returned instead. Try again with a different prompt and&#47;or seed.

prompt 中的 Token 数超过限定时，要停止运行，以节省时间。</p>2023-05-05</li><br/><li><span>Jack</span> 👍（0） 💬（2）<p>第一次运行“a photograph of an astronaut riding a horse”，只有马，没有宇航员，多运行几次就有了，不过图片没有老师的好看</p>2023-05-05</li><br/><li><span>Jacob.C</span> 👍（0） 💬（3）<p>老师可以讲一下，colab 上，跑这个太空人骑马要运行耗时多久吗？</p>2023-05-05</li><br/><li><span>Geek_7ee455</span> 👍（0） 💬（4）<p>老师,在mac上能自己部署一套stable diffusion吗</p>2023-05-05</li><br/><li><span>莹</span> 👍（2） 💬（0）<p>直接新建一个colab notebook后默认不是用的GPU，运行代码出错了&quot;RuntimeError: Found no NVIDIA driver on your system. Please check that you have an NVIDIA GPU and installed a driver from http:&#47;&#47;www.nvidia.com&#47;Download&#47;index.aspx&quot;

遇到同样错误的小伙伴记得在Runtime菜单里选择Change runtime type，选择GPU, T4。我遇到了在运行也不成功的情况，这时可以再在Runtime菜单里选择Restart runtime或者Restart and run all。这样，我遇到的错误就解决了。</p>2023-06-02</li><br/><li><span>piboye</span> 👍（1） 💬（0）<p>李沐的课程太好了</p>2023-05-05</li><br/><li><span>Amark</span> 👍（0） 💬（0）<p>为啥有的图片跟文字不符，文字描述有啥要求吗</p>2024-02-01</li><br/><li><span>小理想。</span> 👍（0） 💬（2）<p>大家没遇到huggingface完全访问不了的情况吗？</p>2023-11-17</li><br/><li><span>昵称C</span> 👍（0） 💬（0）<p>思考题有做出来的吗？老师有答案吗？
</p>2023-07-25</li><br/><li><span>和某欢</span> 👍（0） 💬（0）<p>老师，colab如何引入Counterfeit-V3.0 这个模型呢？示例代码没看懂，运行的时候报 NameError: name &#39;pipeline&#39; is not defined.</p>2023-06-18</li><br/>
</ul>