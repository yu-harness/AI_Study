你好，我是Chrono。

在“入门篇”学习容器技术的过程中，我看到有不少同学留言问Kubernetes“弃用Docker”的事情，担心现在学Docker是否还有价值，是否现在就应该切换到containerd或者是其他runtime。

这些疑虑的确是有些道理。两年前，Kubernetes放出消息要“弃用Docker”的时候，确确实实在Kubernetes社区里掀起了一场“轩然大波”，影响甚至波及到社区之外，也导致Kubernetes不得不写了好几篇博客来反复解释这么做的原因。

两年过去了，虽然最新的Kubernetes 1.24已经达成了“弃用”的目标，但很多人对这件事似乎还是没有非常清晰的认识。所以今天，我们就来聊聊这个话题，我也讲讲我的一些看法。

![图片](https://static001.geekbang.org/resource/image/ec/9a/ece7f8245a02a5ca52a51c79b6f3ea9a.png?wh=1162x600 "图片来自网络")

## 什么是CRI

要了解Kubernetes为什么要“弃用Docker”，还得追根溯源，回头去看Kubernetes的发展历史。

2014年，Docker正如日中天，在容器领域没有任何对手，而这时Kubernetes才刚刚诞生，虽然背后有Google和Borg的支持，但还是比较弱小的。所以，Kubernetes很自然就选择了在Docker上运行，毕竟“背靠大树好乘凉”，同时也能趁机“养精蓄锐”逐步发展壮大自己。

时间一转眼到了2016年，CNCF已经成立一年了，而Kubernetes也已经发布了1.0版，可以正式用于生产环境，这些都标志着Kubernetes已经成长起来了，不再需要“看脸色吃饭”。于是它就宣布加入了CNCF，成为了第一个CNCF托管项目，想要借助基金会的力量联合其他厂商，一起来“扳倒”Docker。

那它是怎么做的呢？

在2016年底的1.5版里，Kubernetes引入了一个新的接口标准：CRI ，Container Runtime Interface。

CRI采用了ProtoBuffer和gPRC，规定kubelet该如何调用容器运行时去管理容器和镜像，但这是一套全新的接口，和之前的Docker调用完全不兼容。

Kubernetes意思很明显，就是不想再绑定在Docker上了，允许在底层接入其他容器技术（比如rkt、kata等），随时可以把Docker“踢开”。

但是这个时候Docker已经非常成熟，而且市场的惯性也非常强大，各大云厂商不可能一下子就把Docker全部替换掉。所以Kubernetes也只能同时提供**一个“折中”方案，在kubelet和Docker中间加入一个“适配器”，把Docker的接口转换成符合CRI标准的接口**（[图片来源](https://kubernetes.io/blog/2016/12/container-runtime-interface-cri-in-kubernetes/)）：

![图片](https://static001.geekbang.org/resource/image/11/ef/11e3de04b296248711455f22ce5578ef.png?wh=572x136)

因为这个“适配器”夹在kubelet和Docker之间，所以就被形象地称为是“shim”，也就是“垫片”的意思。

有了 CRI和shim，虽然Kubernetes还使用Docker作为底层运行时，但也具备了和Docker解耦的条件，从此就拉开了“弃用Docker”这场大戏的帷幕。

## 什么是containerd

面对Kubernetes“咄咄逼人”的架势，Docker是看在眼里痛在心里，虽然有苦心经营了多年的社区和用户群，但公司的体量太小，实在是没有足够的实力与大公司相抗衡。

不过Docker也没有“坐以待毙”，而是采取了“断臂求生”的策略，推动自身的重构，**把原本单体架构的Docker Engine拆分成了多个模块，其中的Docker daemon部分就捐献给了CNCF，形成了containerd**。

containerd作为CNCF的托管项目，自然是要符合CRI标准的。但Docker出于自己诸多原因的考虑，它只是在Docker Engine里调用了containerd，外部的接口仍然保持不变，也就是说还不与CRI兼容。

由于Docker的“固执己见”，这时Kubernetes里就出现了两种调用链：

- 第一种是用CRI接口调用dockershim，然后dockershim调用Docker，Docker再走containerd去操作容器。
- 第二种是用CRI接口直接调用containerd去操作容器。

![图片](https://static001.geekbang.org/resource/image/a8/9b/a8abfe5a55d0fa8b383867cc6062089b.png?wh=1920x627 "图片来自网络")

显然，由于都是用containerd来管理容器，所以这两种调用链的最终效果是完全一样的，但是第二种方式省去了dockershim和Docker Engine两个环节，更加简洁明了，损耗更少，性能也会提升一些。

在2018年Kubernetes 1.10发布的时候，containerd也更新到了1.1版，正式与Kubernetes集成，同时还发表了一篇博客文章（[https://kubernetes.io/blog/2018/05/24/kubernetes-containerd-integration-goes-ga/](https://kubernetes.io/blog/2018/05/24/kubernetes-containerd-integration-goes-ga/)），展示了一些性能测试数据：

![图片](https://static001.geekbang.org/resource/image/6f/e9/6fd065d916e5815e044c10738746ace9.jpg?wh=1784x591)

从这些数据可以看到，containerd1.1相比当时的Docker 18.03，Pod的启动延迟降低了大约20%，CPU使用率降低了68%，内存使用率降低了12%，这是一个相当大的性能改善，对于云厂商非常有诱惑力。

## 正式“弃用Docker”

有了CRI和containerd这两件强大的武器，胜利的天平已经明显向Kubernetes倾斜了。

又是两年之后，到了2020年，Kubernetes 1.20终于正式向Docker“宣战”：kubelet将弃用Docker支持，并会在未来的版本中彻底删除。

但由于Docker几乎成为了容器技术的代名词，而且Kubernetes也已经使用Docker很多年，这个声明在不断传播的过程中很快就“变味”了，“kubelet将弃用Docker支持”被简化成了更吸引眼球的“Kubernetes将弃用Docker”。

这自然就在IT界引起了恐慌，“不明真相的广大群众”纷纷表示震惊：用了这么久的Docker突然就不能用了，Kubernetes为什么要如此对待Docker？之前在Docker上的投入会不会就全归零了？现有的大量镜像该怎么办？

其实，如果你理解了前面讲的CRI和containerd这两个项目，就会知道Kubernetes的这个举动也没有什么值得大惊小怪的，一切都是“水到渠成”的：**它实际上只是“弃用了dockershim”这个小组件，也就是说把dockershim移出了kubelet，并不是“弃用了Docker”这个软件产品。**

所以，“弃用Docker”对Kubernetes和Docker来说都不会有什么太大的影响，因为他们两个都早已经把下层都改成了开源的containerd，原来的Docker镜像和容器仍然会正常运行，唯一的变化就是Kubernetes绕过了Docker，直接调用Docker内部的containerd而已。

这个关系你可以参考下面的[这张图](https://kubernetes.io/blog/2018/05/24/kubernetes-containerd-integration-goes-ga/)来理解：

![图片](https://static001.geekbang.org/resource/image/97/e8/970a234bd610b55340505dac74b026e8.png?wh=740x680)

当然，影响也不是完全没有。如果Kubernetes直接使用containerd来操纵容器，那么它就是一个与Docker独立的工作环境，彼此都不能访问对方管理的容器和镜像。换句话说，使用命令 `docker ps` 就看不到在Kubernetes里运行的容器了。

这对有的人来说可能需要稍微习惯一下，改用新的工具 `crictl`，不过用来查看容器、镜像的子命令还是一样的，比如 `ps`、`images` 等等，适应起来难度不大（但如果我们一直用kubectl来管理Kubernetes的话，这就是没有任何影响了）。

“宣战”之后，Kubernetes原本打算用一年的时间完成“弃用Docker”的工作，但它也确实低估了Docker的根基，到了1.23版还是没能移除dockershim，不得已又往后推迟了半年，终于在今年5月份发布的1.24版把dockershim的代码从kubelet里删掉了。

自此，Kubernetes彻底和Docker“分道扬镳”，今后就是“大路朝天，各走一边”。

## Docker的未来

那么，Docker的未来会是怎么样的呢？难道云原生时代就没有它的立足之地了吗？

这个问题的答案很显然是否定的。

作为容器技术的初创者，Docker的历史地位无人能够质疑，虽然现在Kubernetes不再默认绑定Docker，但Docker还是能够以其他的形式与Kubernetes共存的。

首先，因为**容器镜像格式已经被标准化**了（OCI规范，Open Container Initiative），Docker镜像仍然可以在Kubernetes里正常使用，原来的开发测试、CI/CD流程都不需要改动，我们仍然可以拉取Docker Hub上的镜像，或者编写Dockerfile来打包应用。

其次，**Docker是一个完整的软件产品线**，不止是containerd，它还包括了镜像构建、分发、测试等许多服务，甚至在Docker Desktop里还内置了Kubernetes。

单就容器开发的便利性来讲，Docker还是暂时难以被替代的，广大云原生开发者可以在这个熟悉的环境里继续工作，利用Docker来开发运行在Kubernetes里的应用。

再次，虽然Kubernetes已经不再包含dockershim，但Docker公司却把这部分代码接管了过来，另建了一个叫**cri-dockerd**（[https://github.com/mirantis/cri-dockerd](https://github.com/mirantis/cri-dockerd)）的项目，作用也是一样的，把Docker Engine适配成CRI接口，这样kubelet就又可以通过它来操作Docker了，就仿佛是一切从未发生过。

综合来看，Docker虽然在容器编排战争里落败，被Kubernetes排挤到了角落，但它仍然具有强韧的生命力，多年来积累的众多忠实用户和数量庞大的应用镜像是它的最大资本和后盾，足以支持它在另一条不与Kubernetes正面交锋的道路上走下去。

而对于我们这些初学者来说，Docker方便易用，具有完善的工具链和友好的交互界面，市面上很难找到能够与它媲美的软件了，应该说是入门学习容器技术和云原生的“不二之选”。至于Kubernetes底层用的什么，我们又何必太过于执着和关心呢？

## 课下作业

虽然今天的内容是加餐，但我还是给你留个思考题吧，我们可以一起讨论一下：

Docker重构自身，分离出containerd，这是否算是一种“自掘坟墓”的行为呢？如果没有containerd，那现在的情形会是怎么样的呢？

欢迎在留言区参与讨论，如果觉得这篇文章对你有帮助，也欢迎你分享给朋友。我们下节课再见。

![图片](https://static001.geekbang.org/resource/image/a5/f2/a561d280091d2b59a935c6be38f646f2.jpg?wh=1920x1888)
<div><strong>精选留言（15）</strong></div><ul>
<li><span>星垂平野阔</span> 👍（34） 💬（2）<p>docker分离containerd是一个很聪明的举动！与其将来被人分离或者抛弃不用，不如我主动革新，把Kubernates绑在我的战车上，这样cri的第一选择仍然是docker的自己人。
一时的退让是为了更好的将来。</p>2022-07-13</li><br/><li><span>xmr</span> 👍（13） 💬（1）<p>1.主要还是docker公司话语权逐渐式微，你没有话语权说你不行就不行，docker不得不换一种方式(containerd)陪在你身边。
2.容器技术本身门槛就不高，形成不了技术壁垒，没有containerd还会有containere、containerf之类的代替者。</p>2022-07-13</li><br/><li><span>psoracle</span> 👍（5） 💬（2）<p>老师请教一个问题，很是疑惑。
问题是这样的，runc是一个按OCI规范运行容器的cli工具，如运行时containerd默认使用runc。
我看podman也是通过conmon调用runc运行容器，请问下podman运行容器使用的容器运行时是什么？像docker现在就是通过containerd来调用runc，所以containerd就是docker容器的运行时，从这个角度来看conmon是不是podman容器的运行时？</p>2022-07-14</li><br/><li><span>奕</span> 👍（4） 💬（1）<p>containerd 实现了 CRI 规范，来管理镜像和运行容器，默认和 k8s 绑定，那 k8s 还可以自由替换运行时吗？ 做到 可插拔</p>2022-07-13</li><br/><li><span>psoracle</span> 👍（4） 💬（1）<p>容器运行时只是对Linux的namespace, cgroup, rootfs进行了产品化打包的一种技术，原则上来讲，如果Docker不把运行时containerd分离标准化CRI出来，Kubernetes其实也可以造出新轮子，毕竟现在的容器运行时也有很多，像cri-o, kata, mcr等，当然不知道会不会有啥版权侵犯到moby的。</p>2022-07-13</li><br/><li><span>peter</span> 👍（3） 💬（2）<p>请教老师两个问题：
Q1：有人提出了这个观点：“数据库不适合用docker，不管是mysql还是ES”，这个观点对吗？
Q2：关于容器ID和imageID，我的理解是：容器ID是随机，在同一台宿主机上每次创建的ID都不同，而且同一个镜像在不同机器上创建的ID也不同。但image ID是唯一的、固定的，对于同一个版本，第N次下载和第M次下载的image ID是相同的，同一个image，下载到不同的机器上，image ID也是相同的。 我的理解对吗？</p>2022-07-13</li><br/><li><span>Demon.Lee</span> 👍（2） 💬（1）<p>看完罗老师这篇，再推荐一下隔壁周老师的（ https:&#47;&#47;time.geekbang.org&#47;column&#47;article&#47;351014 ）一篇。在两位大佬的加持下，Kubernetes 与 Docker 相爱想杀的故事，想不懂都难 😂</p>2022-11-08</li><br/><li><span>戒贪嗔痴</span> 👍（2） 💬（3）<p>为啥突然冒出个containerd让我一时不知所措，它的作用是什么，是作为守护进程存在吗？既然分离出的containerd没有兼容的接口，Google完全可以不用的，可能是不想重复造轮子吧。我就感觉怎么冒出个containerd就挺突然的。</p>2022-07-13</li><br/><li><span>lesserror</span> 👍（2） 💬（2）<p>课外小贴士中的“正式毕业”是什么意思呢？</p>2022-07-13</li><br/><li><span>aoe</span> 👍（2） 💬（1）<p>放心了</p>2022-07-13</li><br/><li><span>乔楠</span> 👍（1） 💬（1）<p>“以斗争求和平则和平存，以妥协求和平则和平亡”</p>2023-08-07</li><br/><li><span>花花大脸猫</span> 👍（1） 💬（1）<p>没办法呀。。毕竟依托于k8s的环境运行，别人给了标准，你不调整，那只能被替换了！毕竟谁也不是不可替代的</p>2022-07-28</li><br/><li><span>吕伟</span> 👍（1） 💬（1）<p>是不是可以这么理解“K8S弃用docker”的事情：
K8S在1.24版本后去除了容器使用docker的默认支持，要使用docker作为容器节点只是比以前版本稍微多做一些操作（如：加装插件或者修改哪里的配置），然后也是可以正常像以前一样正常使用docker的。这点是因为docker容器技术符合CRI标准，就算表面脱离了，实际也是兼容。

最后有一点好奇，K8S弃用docker作默认，那么是哪个容器上位成功，但是说只是K8S初始化时要多做选型配置而尔。就好比window系统默认预装ie浏览器，然后有个超纯净版要自行安装浏览器，这个比喻对吗？</p>2022-07-18</li><br/><li><span>朱雯</span> 👍（1） 💬（1）<p>我第一反应也是自掘坟墓，我知道是胳膊拧不过大腿，但也可以拧一拧啊。</p>2022-07-13</li><br/><li><span>Dexter</span> 👍（1） 💬（1）<p>IDL —-接口描述语言，那schema是什么意思？一些接口格式或者规范吗？</p>2022-07-13</li><br/>
</ul>