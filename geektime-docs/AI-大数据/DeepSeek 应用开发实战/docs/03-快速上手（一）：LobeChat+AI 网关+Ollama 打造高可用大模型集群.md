你好，我是邢云阳。

学完我专门为你准备的前置课程，相信对于目前主流的 AI 开发到底是在开发什么，你已经有了一定的认知，这对于你学习后面的课程会有很大的帮助。

从这一章起，我会为你揭秘在云公司里，针对不同的用户场景，DeepSeek 模型是如何部署的。相信你在学完这一章的内容后，只要手里有服务器资源，都能够轻松复刻出同款效果来，并且还可以举一反三，搞定其他开源模型的私有化部署。

接下来的两节课，我会先介绍一种相对简单且在业界进行私有化模型的 AI 应用开发时极为常用的方案，即通过 LobeChat + 网关 + Ollama 打造高可用的部署方案。今天，我们先用 Ollama 将 DeepSeek 模型拉起来，下一节课，我们再来实现高可用集群。

## 什么是 Ollama ？

首先来了解一下 Ollama。Ollama 是一个专为在本地机器上便捷部署和运行大型语言模型（LLM）而设计的开源框架，它可以用简单的命令行快捷部署多种大模型，例如 DeepSeek、Qwen、Llama3 等等模型。

除此之外呢，Ollama 自身还会通过权重量化技术，调整模型权重，并通过分块加载与缓存机制以及 GPU/CPU 灵活调度等技术，使得模型能够降低对硬件的要求，提高资源利用率。以 DeepSeek-R1 的蒸馏模型 DeepSeek-R1-Distill-Qwen-7B 为例，最小也需要 14 G 的显存。但 Ollama 通过对模型的量化，可以显著降低对于显存的占用。

讲到这，可能会有同学还是不理解什么是量化，我举一个简单的例子做一下类比。我们在使用微信时，经常会互相发一些图片。如果我们在收到图片时不点下载原图，图片画质就不清晰（分辨率低），但图片大小可能只有几百 K，占用存储空间小；如果我们点了下载原图，图片更加清晰（分辨率高），但占用存储空间大。原版模型和量化模型之间的关系呢，大概就类似于原图和非原图之间的关系，如果为了节省显存，就需要对模型进行量化。

![](https://static001.geekbang.org/resource/image/8a/dc/8a16ec50882d2cd75be998a72bd16ddc.jpg?wh=3158x2771)

Ollama 有一个非常出色的特性，这也是众多开发者选择它的关键原因，即 Ollama 为所有支持的模型封装了统一的 API，并且兼容 OpenAI 数据格式。这一点至关重要，由于模型是由不同公司或团队训练的，每种模型原本都提供各自的开发接口。因此，Ollama 进行统一封装后，用户在使用时就变得极为便捷。

比如，我们编写 Agent 代码时，就会把标准的 OpenAI SDK 的 base\_url 参数和模型名称做出修改。同样地，如果通过 Ollama 访问 DeepSeek，只需将 base\_url 修改为 Ollama 的地址即可。后期如果需要切换到 Qwen 模型，也无需再修改 base\_url，只需更换模型名称即可。

```python
client = OpenAI(
    api_key=os.getenv("AliDeep"),  
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)
```

## Ollama 部署 DeepSeek-R1 实战

OK，讲了这么多，接下来，我们就进入到这节课的实战环节。

### 环境准备

为了节省资源，我是在联通云上开通了一台带有 2 张 T4 卡的云服务器，操作系统是 Ubuntu 22.04。T4 卡的单卡显存是 16 G，理论上至多能跑满血版的 7B 模型，但由于使用的是 Ollama 部署，因此我们可以以 32B 模型为例做演示。只要你学会了 32B 模型的部署，之后不管是部署 1.5B 还是 671B，方法都一模一样，没有任何区别。

首先使用 nvidia-smi 命令，确认 GPU 卡的驱动已经装好，可以被识别。

```json
root@aitest:~# nvidia-smi                                                                                                                                                
Sun Feb 16 13:56:24 2025                                                                                                                                                 
+-----------------------------------------------------------------------------+                                                                                          
| NVIDIA-SMI 515.76       Driver Version: 515.76       CUDA Version: 11.7     |                                                                                          
|-------------------------------+----------------------+----------------------+                                                                                          
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |                                                                                          
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |                                                                                          
|                               |                      |               MIG M. |                                                                                          
|===============================+======================+======================|                                                                                          
|   0  Tesla T4            Off  | 00000000:00:07.0 Off |                    0 |                                                                                          
| N/A   42C    P0    25W /  70W |      2MiB / 15360MiB |      0%      Default |                                                                                          
|                               |                      |                  N/A |                                                                                          
+-------------------------------+----------------------+----------------------+                                                                                          
|   1  Tesla T4            Off  | 00000000:00:08.0 Off |                    0 |                                                                                          
| N/A   43C    P0    26W /  70W |      2MiB / 15360MiB |      5%      Default |                                                                                          
|                               |                      |                  N/A |                                                                                          
+-------------------------------+----------------------+----------------------+                                                                                          
                                                                                                                                                                         
+-----------------------------------------------------------------------------+                                                                                          
| Processes:                                                                  |                                                                                          
|  GPU   GI   CI        PID   Type   Process name                  GPU Memory |                                                                                          
|        ID   ID                                                   Usage      |                                                                                          
|=============================================================================|                                                                                          
|  No running processes found                                                 |                                                                                          
+-----------------------------------------------------------------------------+ 
```

可以看到两张 T4 卡已经就绪了。

### 安装 Ollama

我们用官方推荐的 Docker 方式部署 Ollama，便于进行版本的管理与测试。

首先将 Ollama 镜像下载到本地，由于国内无法访问 DockerHub，因此大家可以使用后面命令中的代理地址访问：

```shell
docker pull docker.1ms.run/ollama/ollama:0.5.11
```

之后使用命令启动 Ollama 容器：

```shell
docker run -dp 8880:11434 --gpus device=0 --name DeepSeek-R1-1 docker.1ms.run/ollama/ollama:0.5.11
```

这条命令的意思是，首先将容器的 11434 端口映射到宿主机的 8880 端口，11434 即 Ollama 提供 API 访问的端口。–gpus device=0 表示该容器要使用 GPU 0 号卡，怎么知道 GPU 卡的编号的呢？是在前面执行 nvidia-smi 命令时知道的。

根据前面 nvidia-smi 命令的执行结果，两张 Tesla T4 的编号分别是 0 和 1。–name DeepSeek-R1-1 是给容器起一个名字，叫 abc 都可以，只要你喜欢。最后是下载下来的容器镜像的名称。

如果一切正常，启动后，就会返回容器的 ID。接着我们通过 docker ps 命令，就可以查询到容器的信息。

```shell
root@aitest:~# docker run -dp 8880:11434 --gpus device=0 --name DeepSeek-R1-1 docker.1ms.run/ollama/ollama:latest                                                        
7049f65fd9d34392c26355174f4701c1b2c5aa718cdc168d19a982f0519d7635

root@aitest:~# docker ps                                                                                                                                                 
CONTAINER ID   IMAGE                                 COMMAND               CREATED          STATUS         PORTS                                           NAMES         
7049f65fd9d3   docker.1ms.run/ollama/ollama:0.5.11   "/bin/ollama serve"   10 seconds ago   Up 9 seconds   0.0.0.0:8880->11434/tcp, [::]:8880->11434/tcp   DeepSeek-R1-1
```

这一步，经常会报如下的错误：

```shell
root@aitest:~# docker run -dp 8880:11434 --gpus device=0 --name DeepSeek-R1-1 docker.1ms.run/ollama/ollama:0.5.11
bd74646a26c6a539aa7660eb664caa585dba188720f0975701b73d87263b6cdf                                                                                                         
docker: Error response from daemon: could not select device driver "" with capabilities: [[gpu]]. 
```

这是因为服务器的 NVIDIA Container Toolkit 没有装，需要执行如下命令安装一下：

```shell
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
apt-get update
apt-get install -y nvidia-docker2
systemctl restart docker
```

安装完成后，执行 docker info 命令，确保 docker 守护进程已经正确配置 GPU 支持。命令和输出如下：

```shell
root@aitest:~# docker info | grep -i nvidia                                                                                                                              
 Runtimes: io.containerd.runc.v2 nvidia runc
```

此时再重新 docker run，就可以将 Ollama 容器拉起了。

### 部署与测试 DeepSeek-R1

Ollama 官方提供了一个可视化的模型仓库，便于我们了解 Ollama 已经支持了哪些模型，以及下载模型。仓库的地址是：[https://ollama.com/library](https://ollama.com/library)

![](https://static001.geekbang.org/resource/image/d4/ef/d47b76021768f0352110a338b1d7feef.jpg?wh=3000x1414)

点开链接后，第一个就是 DeepSeek-R1 模型，分为 1.5b 到 671b 多个版本。

![](https://static001.geekbang.org/resource/image/bd/fd/bddc98e798a0793406bc8e8a8cd6eafd.jpg?wh=3000x1858)

点进去之后可以选择模型版本以及看到模型运行命令，更新记录等。

这里我介绍两种 Ollama 拉起 DeepSeek-R1 的方案。

#### 1.在容器内下载模型和拉起*

我们需要进入到 Ollama 容器的内部，去执行模型运行命令。进入容器的命令为：

```shell
docker exec -it <你的容器名称或 ID> /bin/bash
```

然后执行模型运行命令：

```shell
ollama run deepseek-r1:32b
```

输出如下，由于本地没有模型，所以，会先在模型仓库下载模型，我们需要耐心等待模型下载完毕。

![](https://static001.geekbang.org/resource/image/ec/a4/ec17d58caa90e5cd220579af19f515a4.jpg?wh=3020x213)

下载完成后，就会加载模型，直到出现success，模型就加载好了。

![](https://static001.geekbang.org/resource/image/8e/d0/8e9ddb83284e0d68a5662c36044468d0.jpg?wh=3020x415)

直接输入对话，测试效果。例如：

![](https://static001.geekbang.org/resource/image/bb/16/bb7f9d27d03929f1b19dc658fa404216.jpg?wh=3020x1010)

可以看到，模型带有 DeepSeek-R1 标志性的 &lt;think&gt;&lt;/think&gt; 也就是深度思考，但是由于我们问的问题太简单了，模型认为不需要深度思考就能回答，因此就直接回答了。

#### 2.将模型文件挂载进容器（推荐）

我更推荐接下来的这种方法，因为下一节我们讲负载均衡方案时，需要起两个 Ollama 容器，因此用这种方式只下载一次模型文件就可以，比较方便。

执行如下命令，在服务器上安装 Ollama 工具。

```shell
curl -fsSL https://ollama.com/install.sh | sh
```

之后直接将模型下载到本地：

```shell
ollama pull deepseek-r1:32b
```

启动容器，将模型挂载进去，需要注意 Ollama 在 ubuntu 服务器上的默认是模型文件存放目录 /usr/share/ollama/.ollama/models，但是在容器中的目录是 /root/.ollama/models，挂载时要写成**服务器目录:容器目录**的格式，注意不要写反了。

```shell
docker run -dp 8880:11434 --runtime=nvidia --gpus device=0 --name DeepSeek-R1-1 -v /usr/share/ollama/.ollama/models
:/root/.ollama/models docker.1ms.run/ollama/ollama:0.5.11
```

最后查看容器中的模型是否已经运行：

```shell
root@aitest:~# docker ps                                                                                                                                                 
CONTAINER ID   IMAGE                                 COMMAND               CREATED         STATUS         PORTS                                           NAMES          
9a44f04e78f7   docker.1ms.run/ollama/ollama:0.5.11   "/bin/ollama serve"   6 minutes ago   Up 6 minutes   0.0.0.0:8880->11434/tcp, [::]:8880->11434/tcp   DeepSeek-R1-1  

root@aitest:~# docker exec -it 9a44f04e78f7 ollama list                                                                                                                  
NAME               ID              SIZE     MODIFIED                                                                                                                     
deepseek-r1:32b    38056bbcbb2d    19 GB    About an hour ago
```

### 模型为什么不思考？

在上文中，我们问 “hello”，DeepSeek 并没有思考。但是我们用官方版本的去问同样的问题，会发现，官方版的无论简单问题还是复杂问题都会思考：

![](https://static001.geekbang.org/resource/image/33/61/3373eba7cbb32a18a5373a2a6fe28761.jpg?wh=2943x1302)

这是什么原因呢？我们使用如下命令看一下 deepseek-r1:32b 的聊天模板。

```shell
ollama show --modelfile deepseek-r1:32b
```

输出如下：

![](https://static001.geekbang.org/resource/image/4b/30/4b92eb78715c32b24776620e31e3fe30.jpg?wh=3000x1053)

可以看到在 &lt;｜ Assistant｜ &gt; 后面直接就是跟的 Content，没有可以强调 &lt;think&gt; 的事情，因此就相当于把是否 think 的主动权交给大模型了。这个其实是对的，如果每一个问题无论简单与否都要思考，会劳民伤财，费时费钱。但这个事情反过来看，如果大模型的能力不能达到极致，在遇到我们想让它思考的问题时，它不思考，体验性又不好。所以这也是官方版本做了强制 think 的原因吧。

那我们如何像官方一样强制 think 呢？其实很简单，按官方教程描述，只需要加一个think标签即可。

操作步骤是这样的。首先将聊天模板保存下来：

```shell
ollama show --modelfile deepseek-r1:32b > Modelfile
```

之后，在 &lt;｜ Assistant｜ &gt; 之后加上 &lt;think&gt;\\\\n，如下图所示：

![](https://static001.geekbang.org/resource/image/a6/37/a6961ca87e89f1d029c43ebb976d4a37.jpg?wh=3020x237)

之后基于 Modelfile 创建一个新的模型：

```shell
ollama create deepseek-r1-think:32b -f ./Modelfile
```

![](https://static001.geekbang.org/resource/image/72/4f/72d9d9609143b5fc63e100d4eb11234f.jpg?wh=3020x660)

这时，再按照前面讲的将模型文件挂载进容器的启动方式，启动容器。

进入容器后，执行一下 ollama list，可以看到现在有两个模型了。

![](https://static001.geekbang.org/resource/image/07/6a/073d3f770c5c077ef709362e9a368a6a.jpg?wh=3033x520)

使用如下命令，将模型 deepseek-r1-think:32b 运行起来，然后测试：

```shell
ollama run deepseek-r1-think:32b
```

测试结果如下：

![](https://static001.geekbang.org/resource/image/84/96/8400017f6921fbfd5eaa98bb4b979c96.jpg?wh=3020x743)

再问相同的问题，模型具备了思考能力。

## API访问

最后，我们看一下，Ollama 的 API 访问。由于 Ollama 的 API 兼容了 OpenAI 的数据结构，因此测试非常简单，直接 curl 一下即可：

```shell
curl http://localhost:8880/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
    "model": "deepseek-r1-think:32b",
	"messages": [
		{"role": "user", "content": "hello"}
	]
}'
```

结果如下：

![](https://static001.geekbang.org/resource/image/a6/4e/a6e75cacd66d7eb7436496592b36994e.jpg?wh=3020x485)

## 总结

这节课，我们开启了 DeepSeek-R1 模型的私有化部署之路。事实上，在 DeepSeek 模型爆火之前，很多同学都是在使用 OpenAI，通义千问等商业模型，对于私有化模型基本没有部署经验。因此我先选择了一种相对非常容易上手的方式，来带你入门。下面我们做个总结。

Ollama 致力于让用户可以以极简的方式快速部署运行开源模型。为了减少对于显存的占用，Ollama 对模型进行了量化处理，因此我们才可以在一张 16GB 显存的 T4 卡上，体验 DeepSeek-R1:32B 模型。

除此之外，Ollama 还对各个大模型进行了统一的 API 封装，API 兼容 OpenAI 数据格式，因此用户可以直接通过访问 OpenAI 模型的方式去访问 Ollama 拉起的模型，非常方便。

最后，我们还结合 DeepSeek-R1 的一个典型特征，深度思考，进行了测试，并解决了模型遇到简单问题不思考的问题。如果你手头上有服务器，或者个人笔记本的显卡是 3090、4090 等相对不错的显卡，可以尝试按文章内容实践一遍，加深理解。

除此之外，我再扩展一点内容，在部署与测试 DeepSeek-R1 小节，我讲了用 Docker 拉起大模型的两种方式，这两种方式无一例外都需要下载模型文件。因此在实际生产中，我们不会这么做。我们会提前将模型文件下载到本地后，基于 Ollama 镜像再打一个新镜像，新镜像便包含了模型文件。这样后期使用时，直接将镜像拉起便可以使用。还有一种方法，是将模型文件放置在对象存储，使用时进行挂载，后续课程里我还会讲解这种方法。

## 思考题

我在测试 API 访问时，提示词非常短，因此返回的速度很快。如果是一个复杂一点的提示词，例如：请帮我写一段 Python 的加减法程序，就会等好长时间才能看到回复。你可以思考一下，如何能调整一下，让用户不等这么久呢？

欢迎你在留言区展示你的思考过程，我们一起探讨。如果你觉得这节课的内容对你有帮助的话，也欢迎你分享给其他朋友，我们下节课再见！
<div><strong>精选留言（15）</strong></div><ul>
<li><span>willmyc</span> 👍（17） 💬（1）<p>目前想到的：1，启用流式输出 2，限制token的生成个数 3.加缓存 4，升级硬件资源</p>2025-03-04</li><br/><li><span>一周吃三次西蓝花</span> 👍（7） 💬（1）<p>老师您好，GPU的需求规格我们知道了，那么在真正部署的时候，对于其他硬件的配置又该如何考虑？比如内存、CPU、硬盘大小等。是否有资料可以学习。</p>2025-03-04</li><br/><li><span>永不止步</span> 👍（5） 💬（1）<p>如果想让deepseek输出思考内容，也可以不用修改modelfile，只需要告诉他输出思考内容，后面的对话就有了</p>2025-04-11</li><br/><li><span>mihello</span> 👍（3） 💬（2）<p>autoDL gpu32G 跑起来了，有点曲折：
1. 由于autoDL的实例是docker容器，所以无法按照老师的docker方式运行（容器里面岂能再次运行容器！）
2. 所以只能通过官方方式安装：curl -fsSL https:&#47;&#47;ollama.com&#47;install.sh | sh
3. 安装遇到 curl 报错（v7.8）：OpenSSL Error messages: error:0A000126:SSL routines::unexpected eof while reading，需要升级curl到8.0
apt remove curl
apt purge curl
apt-get update
apt-get install -y libssl-dev autoconf libtool make
cd &#47;usr&#47;local&#47;src
wget https:&#47;&#47;curl.haxx.se&#47;download&#47;curl-8.7.1.zip
unzip curl-8.7.1.zip
cd curl-8.7.1
.&#47;buildconf
.&#47;configure --with-ssl 
make
sudo make install
sudo cp &#47;usr&#47;local&#47;bin&#47;curl &#47;usr&#47;bin&#47;curl
sudo ldconfig
curl -V

4. 然后又遇到安装下载ollama timeout（众所周知的原因），只能多试几次，然后其中一次成功下载了。run起来了。
</p>2025-03-10</li><br/><li><span>楚翔style</span> 👍（2） 💬（1）<p>老师,有个问题请教下. 模型部署到本地有什么意义吗? 能想到的就是个人知识库   现在各大厂都开放满血版dk,或者直接买满血版api不是更好吗. </p>2025-03-27</li><br/><li><span>6CYS</span> 👍（2） 💬（2）<p>老师好，请问企业级部署的话，用ollama的多还是Xinference的多？</p>2025-03-26</li><br/><li><span>完美坚持</span> 👍（2） 💬（1）<p>在AutoDL上使用Ollama部署DeepSeek：实现局域网私有化AI助手 - KeViNOne的文章 - 知乎
https:&#47;&#47;zhuanlan.zhihu.com&#47;p&#47;23213698282

这个好像可以。

</p>2025-03-08</li><br/><li><span>Geek_d8905a</span> 👍（2） 💬（1）<p>老师，我了解到deepseek官方限制：问答最大上下文长度为64k，最大输出长度为8k，如果使用ollama部署，这个限制有没有被ollama做二次限制？或者不同蒸馏型号有不同的大小限制。</p>2025-03-05</li><br/><li><span>b1a2e1u1u</span> 👍（2） 💬（1）<p>试验了一下在&lt;｜Assistant｜&gt;后加入&lt;think&gt;\\n标签强制进行思考，感觉这种方式会影响 deepseek-r1 的输出格式，思考过程不再是以开头&lt;think&gt;和结尾&lt;&#47;think&gt;标签进行闭合，而且也有几率依然会出现不思考直接给答案的情况

(base) PS C:\Users\admin&gt; ollama run deepseek-r1-think:7b
&gt;&gt;&gt; hello


&lt;&#47;think&gt;

Hello! How can I assist you today? 😊</p>2025-03-04</li><br/><li><span>kevin</span> 👍（2） 💬（1）<p>16GB 显存的 T4 卡部署32B的ds模型，大模型反应很慢吧？我部署了，体验是这样的</p>2025-03-04</li><br/><li><span>Kathy</span> 👍（1） 💬（1）<p>老师，这个可以直接在Mac 上部署吗</p>2025-04-23</li><br/><li><span>Geek_66f829</span> 👍（1） 💬（1）<p>老师你好，Ollama 通过对模型的量化，可以显著降低对于显存的占用，但是同时也会降低模型输出的质量，我这样理解对吗？</p>2025-04-13</li><br/><li><span>ifelse</span> 👍（1） 💬（1）<p>学习打卡</p>2025-04-02</li><br/><li><span>Cathon</span> 👍（1） 💬（1）<p>老师，请问生产上会用ollama部署模型吗，是不是通常都用vllm呀</p>2025-03-14</li><br/><li><span>完美坚持</span> 👍（1） 💬（1）<p>老师我在aotodl上面用ollama安装了deepseek，但是无论是7b还是32b的都特别慢，看nvidia-smi，好像没有怎么用显卡gpu（4MiB &#47;  32760MiB，36G显存只用了4m）
但是用ollama ps
NAME              ID              SIZE      PROCESSOR    UNTIL   
deepseek-r1:7b    0a8c26691023    6.0 GB    100% GPU     Forever    
这里好像又显示用了gpu

我查了半天也没弄好，这是怎么回事呀？怎么就可以让他调用gpu了呢?

我的配置如下：GPU
vGPU-32GB(32GB) * 1
CPU
12 vCPU Intel(R) Xeon(R) Platinum 8352V CPU @ 2.10GHz
内存
90GB</p>2025-03-08</li><br/>
</ul>