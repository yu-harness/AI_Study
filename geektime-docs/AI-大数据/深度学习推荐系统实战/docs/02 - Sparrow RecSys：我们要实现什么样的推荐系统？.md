你好，我是王喆。

上节课，我们明确了推荐系统要解决的基本问题，清楚了深度学习推荐系统的技术架构，这节课我们开始走进实战。

作为程序员，我相信你肯定听过，甚至可能还很认同Linux之父Linus Torvalds的那句话“Talk is cheap.Show me the code.”。我也一样，所以只讲解理论知识不是这门课的风格，我希望你通过这门课的学习，不仅能构建出一棵深度学习推荐系统的知识树，还能动手实现出一个看得见、摸得着、能操作、能修改的推荐系统。

所以今天，**你跟着我的讲解，只需要花三十分钟的时间，就能将一套完整的深度学习推荐系统，Sparrow RecSys（随着课程的进行，我们会逐渐补充新的模块），在你自己的电脑上运行起来**。这也是我们这门课最终要实现的深度学习推荐系统。

## 废话不多说，直接运行

废话不多说，我们先把Sparrow RecSys安装运行起来。因为我已经把项目相关的所有代码（代码还会随着课程进行持续更新）、数据都整理到GitHub的开源项目中，所以你不需要额外安装任何的支持软件，也不需要额外下载任何数据。

这样，整个安装过程就跟“把大象装进冰箱“一样，只需要三步，就是打开冰箱门，把大象装进去，关上冰箱门。“翻译”成咱们的过程就是，从GitHub中clone代码，在本地以maven project的形式安装，运行RecSysServer主函数启动推荐服务器。接下来，我们详细地解释一下这三个步骤。

首先，从GitHub中clone代码。这里，我直接给出了Sparrow Recsys开源项目的地址：[https://github.com/wzhe06/SparrowRecSys](https://github.com/wzhe06/SparrowRecSys)。点击之后，你需要使用`git clone https://github.com/wzhe06/SparrowRecSys.git`命令，或者从Web端下载的方式，把代码下载到本地。

然后，你可以在本地以maven project的形式安装，也就是导入项目到IDE。我推荐你使用IntelliJ IDEA为本项目的IDE。这样，我们直接使用IDEA，打开本地的Sparrow Recsys项目根目录就能导入项目。不过有一点需要注意，如果项目没有自动识别为maven project，你还需要右键点击pom.xml文件，选择将该项目设置为maven project才能进行后面的操作。

最后，运行RecSysServer。等到所有库文件自动下载完毕，项目编译完毕后，我们找到项目的主函数`com.wzhe.sparrowrecsys.online.RecSysServer`，右键点击运行。因为推荐服务器默认运行在6010端口，所以我们打开浏览器，输入`http://localhost:6010/`，就能看到整个推荐系统的前端效果了。

![](https://static001.geekbang.org/resource/image/29/e0/291a34c2e4cd379434efd2e3aed777e0.jpg?wh=1920%2A1583%3Fwh%3D1920%2A1583 "图1 Sparrow Recsys的主页")

如果通过上面的步骤，你的浏览器显示出了由多个电影列表组成的Sparrow Recsys的主页，那么恭喜你，你已经拥有了这套深度学习推荐系统。

而且我相信，你把Sparrow Recsys这只“大象”装到自己冰箱里的时间，不会超过30分钟。但第一次见面的热情过后，你会不但想知其然，还想知其所以然，那接下来我就和你说说Sparrow Recsys的来历，以及功能和架构。而且在接下来的课程中，我会以它为例来给你讲透深度学习推荐系统。

## “麻雀虽小，五脏俱全”的Sparrow Recsys

Sparrow RecSys，全称Sparrow Recommender System，中文名“**麻雀推荐系统**”，名字取自“**麻雀虽小，五脏俱全**”之意。

你第一眼见到它，可能认为它像个Demo或者玩具。虽然它不可能真正具备一个工业级深度学习推荐系统的全部功能，但我希望它是一颗能够成长为参天大树的种子，一只未来有可能大鹏展翅的雏鸟。在投入一定的精力改造、拓展之后，它甚至有可能支撑起一个规模互联网公司的推荐系统框架。这就是我设计Sparrow RecSys的初衷。我也希望你能够在实现Sparrow RecSys的过程中，快速领略深度学习推荐系统的主要模块和主流技术，并且找到乐趣、找到成就感。

那么Sparrow Recsys到底实现了哪些功能呢？它又包含了哪些深度学习推荐系统的关键技术呢？下面，我会为你一一讲解。

## Sparrow Recsys的功能有哪些

Sparrow RecSys是一个电影推荐系统，视频推荐是我最熟悉的领域，这也是我以电影推荐作为切入点的原因。像所有经典的推荐系统一样，它具备“相似推荐”“猜你喜欢”等经典的推荐功能，在页面设置上，主要由“首页”“电影详情页”和“为你推荐页”组成。

**首先，是Sparrow RecSys的首页**。

![](https://static001.geekbang.org/resource/image/29/e0/291a34c2e4cd379434efd2e3aed777e0.jpg?wh=1920%2A1583%3Fwh%3D1920%2A1583 "图2 Sparrow RecSys的首页")

Sparrow RecSys 的首页由不同类型的电影列表组成，当用户首次访问首页时，系统默认以历史用户的平均打分从高到低排序，随着当前用户不断为电影打分，系统会对首页的推荐结果进行个性化的调整，比如电影类型的排名会进行个性化调整，每个类型内部的影片也会进行个性化推荐。

**其次，是电影详情页。**

![](https://static001.geekbang.org/resource/image/b1/46/b12e82af7b561f2d657da25b04960946.jpg?wh=1920%2A1530 "图3 电影详情页")

你可以看到电影详情页除了罗列出电影的一些基本信息，最关键的部分是相似影片的推荐。相似内容推荐是几乎所有推荐系统非常重要的功能，传统的推荐系统基本依赖于基于内容（Content based）的推荐方法，而我们这门课程会更多地讲解基于深度学习Embedding的相似内容推荐方法。

**最后，是为你推荐页。**

![](https://static001.geekbang.org/resource/image/55/65/55d0f2b3395d30b9ecac47a615686765.jpg?wh=1920%2A1470 "图4 为你推荐页")

这一部分也是整个推荐系统中最重要的部分，是用户的个性化推荐页面。这个页面会根据用户的点击、评价历史进行个性化推荐。这几乎是所有推荐系统最经典和最主要的应用场景。我希望在这门课程中，你能够动手完成个性化推荐中的每个关键步骤，包括但不限于特征的处理、候选集的召回、排序层主要模型等等。

## Sparrow Recsys的数据从哪来？

知道了Sparrow RecSys的功能之后，你肯定想问，“老师，咱们的数据从哪来呀？”。既然Sparrow RecSys是一个开源项目，那么Sparrow RecSys的数据源肯定也是开源和免费的，它的数据源来自于著名的电影开源数据集[MovieLens](https://grouplens.org/datasets/movielens/)。

为了方便你调试，咱们这门课程的教学数据集对MovieLens数据集进行了精简，只留下了1000部电影。如果希望在全量数据集上进行推荐，你可以去MovieLens的官方网站下载全量数据，它一共包含了27000部电影。

MovieLens的数据集包括三部分，分别是 **movies.csv（电影基本信息数据）、ratings.csv（**用户评分数据）**和 links.csv**（外部链接数据）。下面，我就具体说说它们分别长什么样。

### 1. movies.csv（电影基本信息数据）

movies表是电影的基本信息表，它包含了电影ID（movieId）、电影名（title）、发布年份以及电影类型（genres）等基本信息。

![](https://static001.geekbang.org/resource/image/f3/7a/f3579fbb04e430d5322fcd58fb410c7a.jpeg?wh=1858%2A682 "图5 电影基本信息数据")

MovieLens 20M Dataset包含了2016年前的约13万部电影，我们课程的实验数据集从中抽取了前1000部电影。电影数据集是我们推荐的主体，其中分类、发布年份、电影名称等信息也将是推荐模型可以利用的重要特征。

### 2. ratings.csv（用户评分数据）

ratings表包含了用户ID（userId）、电影ID（movieId）、评分（rating）和时间戳（timestamp）等信息。

![](https://static001.geekbang.org/resource/image/6c/ec/6c1d79ba6f9ea7017b7b0f60d3798aec.jpeg?wh=902%2A1027 "图6 用户评分数据")

MovieLens 20M Dataset包含了2000万条评分数据，我们课程的实验数据集从中抽取了约104万条评论数据。评论数据集是之后推荐模型训练所需的训练样本来源，也是我们分析用户行为序列、电影统计型特征的原始数据。

### 3. links.csv（外部链接数据）

links表包含了电影ID（movieId）、IMDB对应电影ID（imdbId）、TMDB对应电影ID（tmdbId）等信息。其中，imdb和tmdb是全球最大的两个电影数据库。因为links表包含了MovieLens电影和这两个数据库ID之间的对应关系，所以，我们可以根据这个对应关系来抓取电影的其他相关信息，这也为我们大量拓展推荐系统特征提供了可能。

![](https://static001.geekbang.org/resource/image/95/07/951f3fb63de288774c404c215756cf07.jpeg?wh=1057%2A969 "图7 外部链接数据")

此外，MovieLens的数据集中还包含了tags.csv，它用于记录用户为电影打的标签，由于课程中暂时没有使用标签数据，我就展开说了。

## Sparrow Recsys涵盖的技术点

清楚了Sparrow Recsys的功能和数据，你肯定迫不及待地想知道Sparrow Recsys会使用哪些技术，可以实现哪些模型。

那我们直接来看下面这张Sparrow Recsys的技术架构图。你会发现，它其实就是我们用具体的技术选型，把上节课的深度学习推荐系统架构图给填上得到的。所以，Sparrow Recsys就是深度学习推荐系统架构的一个实现。

![](https://static001.geekbang.org/resource/image/8c/9e/8cee6a7eeebda9745bfbe1b6yy18c59e.jpg?wh=2395%2A2751 "图8 Sparrow Recsys的推荐系统架构")

你可以看到，它一共分为三个模块，分别是数据、模型和前端。其中每个部分都用业界推荐系统的主流技术，比如数据部分我们会用Spark，Flink进行样本和特征的处理，模型部分我们会使用TensorFlow训练深度神经网络、Wide&amp;Deep、PNN等模型。

![](https://static001.geekbang.org/resource/image/2f/02/2f89e7a0fb0f130f2ec8e75d3848f802.jpeg?wh=1920%2A987 "图9 Sparrow Recsys中的技术点")

我想啊，你在看到这么多的技术点和技术平台之后，肯定想问，我们的课程能把它们都讲完、讲透吗？这是个好问题，我也有必要在这里说清楚。从中，我们可以总结出Sparrow Recsys中具体用到的技术点。

其实推荐系统是一个应用属性很强的领域，想把推荐系统学好，我们就必须去学习各式各样相关的平台、技术，所以我们这门课的涉及面非常广。但你也不用因为要学这么多的技术而感到惊慌，因为我们没有必要去深究每个平台内部的原理、优化的方法，我们当好一个使用者就好。

举个例子你就明白了，我们处理数据需要用到Spark，但我们有必要成为Spark的专家吗？其实不用。因为即使你已经走上了工作岗位，也有平台架构部的同事能够提供Spark的很多技术支持。所以学习这门课程，我们大可抱着一个使用者，而不是开发者、维护者的心态去使用不同的技术平台。当然，如果你想成为某个细分方向的专家，比如Spark的专家、Flink的专家等等，我相信极客时间上肯定还有很不错的课程供你学习。

所以希望你能够通过Sparrow Recsys认识到主流深度学习推荐系统都使用了哪些技术，让自己有一个全面的认识，建立自己的知识广度。如果还想深入钻研某个方向，也可以由此开始，努力成为一个领域的专家。

## 小结

这堂课，我带你熟悉了我们将要实现的推荐系统Sparrow Recsys，它将是我们深度学习推荐系统这门课的落地项目和实现范例。希望有这个真实可用的推荐系统作为支撑，这门课可以同时兼顾概念讲解和代码实战，也让我们接下来的共同合作能够更好。

从开篇词到这一节课，我们从推荐系统要解决的核心问题，生发出深度学习推荐系统的技术架构，再到让技术架构实实在在地落地到Sparrow Recsys这个开源项目上。我想你已经可以感受到架构篇的学习过程，其实就是一个从抽象到具体，从形而上到形而下的过程。

那在搭建起这整门课程的框架之后，接下来我们将会一起深入到技术细节，以及深度学习的实践中，一起去体验深度学习浪潮之巅的推荐系统知识，期待继续与你同行！

## 课后思考

1. 当你把Sparrow Recsys在自己的电脑上安装运行起来之后，对照着上节课的深度学习推荐系统架构图，你能试着说出每个模块的代码属于架构图中的哪一部分吗？
2. 你觉得对于一个电影推荐系统来说，什么数据对生成用户个性化推荐结果最有帮助？

好啦，快按照这节的方法把Sparrow Recsys运行起来吧！课后的两个问题也并不困难，相信你肯定可以回答出来。今天就讲到这里了，我们下节课见！
<div><strong>精选留言（15）</strong></div><ul>
<li><span>Capricornus</span> 👍（62） 💬（12）<p>MAC OS系统
1.下载IDEA（https:&#47;&#47;www.jetbrains.com&#47;idea&#47;download&#47;#section=mac）
2.下载JDK（https:&#47;&#47;www.oracle.com&#47;java&#47;technologies&#47;javase-jdk15-downloads.html）
3.安装IDEA和JDK（JDK的路径~&#47;Library&#47;Java&#47;JavaVirtualMachines&#47;openjdk-15.0.1-1）
4.打开IDEA，打开File-&gt;Project Strucure-&gt;Project-&gt;Project JDK(我的好像会自动识别)。若没有识别（显示jdk15.1）,点击三角号，自己添加，步骤Add SDK-&gt;JDK-&gt;选择上面提到的JDK路径选择。
5.在pom.xml点击右键，设置为maven project-&gt;&#39;Reload project&#39;。耐心等待，这个很费时间。
6.然后找到SparrowRecSys&#47;src&#47;main&#47;java&#47;com&#47;SparrowRecSys&#47;online&#47;RecSysServer,右击选择&quot;Run &#39;RecSysServer.main()&#39;&quot;,程序就执行起来了.
7.浏览器中键入http:&#47;&#47;localhost:6010&#47;</p>2020-12-22</li><br/><li><span>挖掘机</span> 👍（12） 💬（6）<p>windows下搭建推荐系统的步骤
1. 使用的vscode作为IDE
2. 编译命令为mvn package assembly:single
3. 我的web root uri在源代码里总是为空，稍微改了一下，这里是为了绕过去，也请指导的高手告诉正确方法
RecSysServer.java中49行改成了绝对路径
URI webRootUri = URI.create(&quot;file:&#47;D:&#47;Work&#47;RecommendationSystem&#47;Sparrow&#47;SparrowRecSys&#47;target&#47;classes&#47;webroot&#47;&quot;);
4. 运行java -jar target\SparrowRecSys-1.0-SNAPSHOT-jar-with-dependencies.jar即刻成功</p>2020-12-21</li><br/><li><span>嘿人</span> 👍（40） 💬（1）<p>王老师您好，我学习的时候就是经常把握不好“使用者”的度，碰到什么都想扎进去研究，导致很容易陷入‘局部极小值’，请问怎么把握这个度呢？</p>2020-12-09</li><br/><li><span>浣熊当家</span> 👍（38） 💬（7）<p>因为没有项目经验，想知道git clone到本地之后，怎么运行这个Maven project呢？油管上有没有类似的demo可以看看，老师能出一下小的录屏么？万分感谢。。第一步就卡住了。。</p>2020-09-23</li><br/><li><span>Hhha爲</span> 👍（34） 💬（1）<p>老师您好，我查阅了网上的一些博客资料，大多认为协同过滤这样的传统方法应该是在召回层。，不过在您的图里是在排序（精排）层，可以问一下这样分类的理由是什么吗？谢谢！</p>2020-09-23</li><br/><li><span>pedro</span> 👍（27） 💬（2）<p>暂时没有去跑项目，先尝试回答问题二吧，对于一个电影爱好者而言，从我的角度出发，一个能够取悦我的，电影推荐系统，必须满足我在电影种类，演员，电影内容，电影质量上的需求，要说什么最有帮助，我觉得应该是用户历史浏览记录。</p>2020-09-22</li><br/><li><span>Don</span> 👍（20） 💬（2）<p>召回有优化之后，排序并不能捕捉到召回新增的特征，在排序后召回的优化点弱化很多，这种一般怎么处理？比如：召回有话增加了性别+年龄的特征，但是排序层没有用这维特征，导致根据该特征召回的内容排序后都在靠后位置没有机会曝光</p>2020-09-23</li><br/><li><span>Sam</span> 👍（15） 💬（6）<p>## 上个旧版本有些链接失效，现在补上这个新的，而且更新了步骤。
win7下 搭建 推荐系统 的步骤：
1. 第1步骤：下载IDEA。
https:&#47;&#47;www.jetbrains.com&#47;idea&#47;download&#47;#section=windows

2. 第2步骤：如何下载和配置JDK1.8（一定要JDK1.8）
https:&#47;&#47;www.cnblogs.com&#47;hejh&#47;p&#47;11276434.html

3.第3步骤：IDEA配置JDK1.8（一定要JDK1.8）
https:&#47;&#47;blog.csdn.net&#47;liluo_2951121599&#47;article&#47;details&#47;78484776

4. 第4步骤：window下安装scala步骤
https:&#47;&#47;www.cnblogs.com&#47;onlyxx&#47;p&#47;5168882.html

4.1 第4.1步骤：Scala安装问题找不到主类的（不要安装在有空格的路径）
https:&#47;&#47;blog.csdn.net&#47;weekdawn&#47;article&#47;details&#47;94625067

4.2 第4.2步骤：Scala2.11要匹配JDK1.8，否则出问题
https:&#47;&#47;blog.csdn.net&#47;yulutian&#47;article&#47;details&#47;80566728

5. 第5步骤：IDEA配置Scala
https:&#47;&#47;www.cnblogs.com&#47;starzy&#47;p&#47;10461038.html

6. 第6步骤：win7安装hadoop spark
https:&#47;&#47;www.jianshu.com&#47;p&#47;9f40fe1b6587

7. 第7步骤：安装Redis
https:&#47;&#47;www.cnblogs.com&#47;liuqingzheng&#47;p&#47;9831331.html

大功告成，如果安装过程有问题的同学，请留言，我们一起解决！~^^</p>2021-06-18</li><br/><li><span>夜雨声烦</span> 👍（15） 💬（6）<p>JAVA小白 mac os系统 安装Sparrow Recsys时的历程：
1，安装java8和scala2.11
网上有很多参考教程。
安装Java8：https:&#47;&#47;blog.csdn.net&#47;irokay&#47;article&#47;details&#47;71374426
遇到的&#47;etc&#47;profile是readonly的情况，解决方法是更改该文件的权限，增加写权限：775.https:&#47;&#47;blog.csdn.net&#47;good007boy&#47;article&#47;details&#47;88659162
安装scale：https:&#47;&#47;blog.csdn.net&#47;u012373815&#47;article&#47;details&#47;53231292
遇到的问题，在执行scala的时候出现“scala [ERROR] Failed to construct terminal; falling back to unsupported”，应该是跟iterm2起了什么冲突，解决方案：https:&#47;&#47;blog.csdn.net&#47;merrily01&#47;article&#47;details&#47;102823539
2，安装、打开IDEA
略过
3，执行文件
在pom.xml点击右键，设置为maven project-&gt;&#39;Reload project&#39;
配置SDK：在File-&gt;Project Structure-&gt;Project配置Project SDK
然后找到SparrowRecSys&#47;main&#47;java&#47;online&#47;RecSysServer,右击选择&quot;Run &#39;RecSysServer.main()&#39;&quot;,程序就执行起来了
浏览器输入http:&#47;&#47;localhost:6010&#47;，就可以看到SparrowRecSys首页</p>2020-10-09</li><br/><li><span>明月</span> 👍（12） 💬（2）<p>老师，这是需要去了解一下java吗，在校生做推荐系统还是用Python</p>2020-11-25</li><br/><li><span>何去何从</span> 👍（10） 💬（1）<p>老师您好！因为之前工作没有过推荐系统相关的项目经验，如果后期有机会面试相关岗位，能否把这个项目写到简历中当做一个项目经验呢？</p>2020-09-23</li><br/><li><span>海</span> 👍（7） 💬（2）<p>老师，马上就要秋招找工作了。时间问题只学习了python，感觉学习java体系来不及了，为了找工作想在scala系和pyspark系取舍一下。请问pyspark等用python调大数据相关技术在工业界运用广吗？</p>2020-12-29</li><br/><li><span>悠悠我心</span> 👍（7） 💬（1）<p>运行起来了，还没仔细看代码，期待</p>2020-09-24</li><br/><li><span>wolong</span> 👍（7） 💬（2）<p>大佬您好！我这边大概从事搜索、广告、推荐的工作也大概有六七年的光景，我有几个一直困扰的问题希望您能抽时间帮忙解答。
1.现在关于实时广告点击率预估，业界主流的深度学习解决方案是怎样的思路？
2.深度强化学习在推荐行业目前的应用主要瓶颈在那些点？</p>2020-09-22</li><br/><li><span>太子长琴</span> 👍（6） 💬（1）<p>用户特征，尤其是行为特征，比如点击记录，有效浏览时长，点评记录，点评结果
物品特征，主演，类型，评分</p>2020-09-25</li><br/>
</ul>