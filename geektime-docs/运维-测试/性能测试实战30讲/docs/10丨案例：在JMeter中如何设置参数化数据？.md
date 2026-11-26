今天我们来做一个实例，看下在JMeter中，如何合理地设置参数化数据。

## 正式场景前的基准测试

在没有做业务混合场景之前，我们需要先做Benchmark测试，来确定一个登录业务能支持多少的业务量，这样就可以在业务混合场景中，根据场景中各业务的比例来确定登录的数据需要多少真实的数据。

我们继续用上一篇文章中用户登录的例子，单独测试登录业务，结果如下：

```
Java
summary +    125 in 00:00:04 =   31.0/s Avg:    28 Min:     0 Max:   869 Err:     0 (0.00%) Active: 1 Started: 1 Finished: 0
summary +   3404 in 00:00:30 =  113.2/s Avg:    31 Min:     0 Max:   361 Err:     0 (0.00%) Active: 6 Started: 6 Finished: 0
summary +   4444 in 00:00:30 =  148.4/s Avg:    57 Min:     0 Max:   623 Err:    10 (0.23%) Active: 11 Started: 11 Finished: 0
```

从上面的结果可以看到登录业务能达到的TPS是113左右，这里我们取整为100，以方便后续的计算。

## 在测试工具中配置参数

在上面的试探性测试场景中，不需要观察系统的资源，只需要根据TPS做相应的数据统计即可。

前面我们知道，在这个示例中只做了近10万条的用户数据，为了方便示例进程。

下面我们从数据库中查询可以支持登录5分钟不重复的用户数据。根据前面的公式，我们需要30000条数据。

```
Java
100x5mx60s=30000条
```

接下来连接数据库，取30000条数据，存放到文本中，如下所示：

```
Java
username,password
test00001,test00001
test00002,test00002
test00003,test00003
test00004,test00004
test00005,test00005
test00006,test00006
test00007,test00007
...................
test30000,test30000
```

## 参数化配置在JMeter中的使用说明

我们将这些用户配置到测试工具的参数当中，这里以JMeter的CSV Data Set Config功能为例。配置如下：

![](https://static001.geekbang.org/resource/image/d4/a6/d40134621469079dd7b9de6e19165ca6.png?wh=1120%2A350%3Fwh%3D1120%2A350)

在JMeter的参数化配置中，有几个技术点，在这里说明一下。

“Allow quoted data?”这里有两个选择，分别是False和True。它的含义为是否允许带引号的数据，比如说在参数化文件中有这样的数据。

```
Java
"username","password"
"test00001","test00001"
"test00002","test00002"
...................
"test30000","test30000"
```

如果有引号，这个选择必须是True。如果设置为False，那么我们在脚本中会看到如下的数据：

```
Java
username=%22test00001%22password=%22test00001%22
```

由于设置为False，JMeter将（"）转换为了%22的URL编码，很显然这个数据是错的。如果选择为True，则显示如下：

```
Java
username=test00001password=test00001
```

这里就显示对了。

除此之外，还有如下几个功能点需要说明：

- Recycle on EOF? ：这里有三个选择，False、True和Edit。前两个选择非常容易理解。False是指在没有参数的时候不循环使用；True是指在没有参数的时候循环使用。Edit是指在没有参数的时候会根据定义的内容来调用函数或变量。
- Stop thread on EOF?：这里有三个选择，False、True和Edit。含义和上面一致。
- Sharing mode : 这里有四个选择，All threads、Current thread group、Current thread、Edit。

Sharing mode的前三个选择是比较容易理解的，参数是在所有线程中生效，在当前线程组生效，还是在当前线程中生效。但这里的Edit和前两个参数中的Edit相比，有不同的含义。这里选择了Edit之后，会出现一个输入框，就是说这里并不是给引用函数和参数使用的，而是要自己明确如何执行Sharing mode。那如何来使用呢？

举例来说，假设我们有Thread Group 1-5 五个线程组，但是参数化文件只想在Thread Group 1、3、5中使用，不想在线程组2、4中使用，那么很显然前面的几个选项都达不到目的，这时我们就可以选择Edit选项，在这里输入`SharedWithThreadGroup1and3and5`。而在其他的线程组中配置其他参数化文件。

也就是说同样的一个变量名，在线程组1/3/5中取了一组数据，在线程组2/4中取了另一组数据。

以上三个参数的选项可以随意组合。于是就会得到如下表。

**需要注意的是，EOF是文件结束符的意思。在下面的解释中，为了更符合性能测试中的术语，特意解释为参数不足时。**

以上三个功能点根据参数设计得不同，会产生不同的组合，我们依次查看一下。

![](https://static001.geekbang.org/resource/image/3c/b1/3ce3106d6b079e715cce6fcbf8de72b1.png?wh=1204%2A246)

这个组合显然是矛盾的，没有参数时不让循环，还不让停止线程，这不是耍流氓吗？真实的结果是什么呢？当我们执行时就会发现，参数变成了这样：

```
username=%3CEOF%3E&password=%3CEOF%3E
```

服务端果然返回了：`{"flag":false,"errMsg":"账号不存在"}`。

![](https://static001.geekbang.org/resource/image/2e/6b/2ea13362d80579cbcc8f941e53ed696b.png?wh=1202%2A249)  
这个组合中第二个选项显然是没意义的，既然参数允许重复使用了，又怎么会发生参数不足停止线程的情况呢？

![](https://static001.geekbang.org/resource/image/e5/65/e5643ea7e5dd17bb31a715e2aa5bdf65.png?wh=1202%2A283)  
这个组合因为第一个选项为“Edit”所以变得不确定了，如果在Edit的函数或变量返回为True，则和第2种组合一样；如果返回为False，则和第1种组合一样。

![](https://static001.geekbang.org/resource/image/d4/99/d48f109b59767bd99679f4f442494899.png?wh=1203%2A253)  
这是一个完全合情合理的组合！

![](https://static001.geekbang.org/resource/image/4b/05/4be6a8f830155a6fdfdee518c9220305.png?wh=1206%2A254)

同第二个组合一样，第二个选项显然没有意义。

![](https://static001.geekbang.org/resource/image/91/0c/9107142e3f0acd73eb2f350dc698a70c.png?wh=1200%2A281)  
这个组合同样因为第一个选项为Edit，所以变得不确定了，如果在Edit的函数或变量返回为True，则和第3种组合一样；如果返回为False，则和第4种组合一样。

![](https://static001.geekbang.org/resource/image/00/e0/008693e916bf65b9cdc6586afd5fcde0.png?wh=1203%2A245)  
这个组合因为是否停止线程的不确定性会出现两种可能，有可能是第1种组合，也有可能是第4种组合。

![](https://static001.geekbang.org/resource/image/ed/57/ed552dbc050ec154ac7f4f1b4148e657.png?wh=1210%2A265)  
这个组合中是否停止线程的Edit配置没有意义，因为可循环使用参数，所以不会发生参数不足导致线程停止的情况。

![](https://static001.geekbang.org/resource/image/37/f0/37735347120d86198df67dffbaa31ff0.png?wh=1200%2A290)  
这是一个古怪的组合，具有相当的不确定性，有可能变成第1、2、4、5种组合。

下面我们再来看下其他衍生的设置组合。

![](https://static001.geekbang.org/resource/image/91/0b/9151da6424095444d56141c5e8c11b0b.jpg?wh=1757%2A4607)

## 真实场景下的JMeter参数配置和执行结果

根据以上的描述，我们先用10个用户来测试下，将Stop `thread on EOF?`改为True，将`Recycle on EOF?`改为False，其他不变。同时将线程组中配置为1个线程循环11次。这样设置的目的是为了看在数据不足时，是否可以根据规则停掉线程组。如下所示：

![](https://static001.geekbang.org/resource/image/d4/a6/d40134621469079dd7b9de6e19165ca6.png?wh=1120%2A350%3Fwh%3D1120%2A350)

线程组配置如下：

![](https://static001.geekbang.org/resource/image/d2/3f/d26aeda4baea18631966b15dd5084a3f.png?wh=519%2A110)

执行之后，我们会在日志中看到如下信息：

```
Java
2019-09-05 22:56:30,171 INFO o.a.j.t.JMeterThread: Stop Thread seen for thread Thread Group 1 1-1, reason: org.apache.jorphan.util.JMeterStopThreadException: End of file:/Users/Zee/Downloads/user10.csv detected for CSV DataSet:CSV Data Set Config configured with stopThread:true, recycle:false
```

可以看到在参数用完又不可循环使用参数的情况下，JMeter主动停止了线程。

我们延续使用上文中场景二的条件，即希望场景中每个线程的每次迭代都用不同的数据。

为了能很快地整理出实际的结果，我们只使用10条数据来模拟，条件设置如下：

```
线程组：2
线程（每线程组）：6
参数化数据：10条
```

执行完场景后，会在日志中看到如下信息：

```
Java
2019-09-07 23:24:25,585 INFO o.a.j.t.JMeterThread: Stop Thread seen for thread Thread Group 1 1-1, reason: org.apache.jorphan.util.JMeterStopThreadException: End of file:/Users/Zee/Downloads/user10.csv detected for CSV DataSet:CSV Data Set Config configured with stopThread:true, recycle:false
2019-09-07 23:24:25,452 INFO o.a.j.t.JMeterThread: Stop Thread seen for thread Thread Group 1 1-2, reason: org.apache.jorphan.util.JMeterStopThreadException: End of file:/Users/Zee/Downloads/user10.csv detected for CSV DataSet:CSV Data Set Config configured with stopThread:true, recycle:false
2019-09-07 23:24:23,406 INFO o.a.j.t.JMeterThread: Stop Thread seen for thread Thread Group 2 2-1, reason: org.apache.jorphan.util.JMeterStopThreadException: End of file:/Users/Zee/Downloads/user10.csv detected for CSV DataSet:CSV Data Set Config configured with stopThread:true, recycle:false
2019-09-07 23:24:25,517 INFO o.a.j.t.JMeterThread: Stop Thread seen for thread Thread Group 2 2-2, reason: org.apache.jorphan.util.JMeterStopThreadException: End of file:/Users/Zee/Downloads/user10.csv detected for CSV DataSet:CSV Data Set Config configured with stopThread:true, recycle:false
```

可见所有的线程都按我们的配置停止了线程，同时各线程取得参数如下表所示：

![](https://static001.geekbang.org/resource/image/6c/ab/6cd12cb6c6b0f41dec961379380beaab.png?wh=793%2A671)  
每次执行场景会有不同，不同点是线程组1有可能执行6次，而线程组2只执行4次；或者线程组1中的线程2执行次数比线程1执行次数多。但总体执行次数会是10次。

如果数据可以被线程平均分配，则每个线程的迭代次数会相同。如果数据不能被线程平均分配，则每个线程的迭代次数不会相同，但相差不会大。

## 参数化配置在LoadRunner中的使用说明

在LoadRunner中参数配置页面如下：

![](https://static001.geekbang.org/resource/image/88/a7/88659e50f65ba8cb8005aa2e82c742a7.png?wh=495%2A545)

它的取值组合如下所示：  
![](https://static001.geekbang.org/resource/image/c7/a3/c705bcf1b185248e05a0457ac0a010a3.png?wh=1206%2A676)

以上的组合中，组合7对应着上文中JMeter真实场景中每次迭代取不同数据的组合，即JMeter中的参数组合4。

## 总结

通过今天的内容，我们对性能测试中的参数化做了一次解析，在执行性能测试时，我们需要根据实际的业务场景选择不同的数据量和参数设置组合。

不同的压力工具在参数化的实现逻辑上也会不同，但是参数化必须依赖业务逻辑，而不是工具中能做到什么功能。所以在参数化之前，我们必须分析真实业务逻辑中如何使用数据，再在工具中选择相对应的组合参数的方式去实现。

这里我总结一下性能工作中参数化的逻辑，希望对你有所启发。

1. 分析业务场景；
2. 罗列出需要参数化的数据及相对应的关系；
3. 将参数化数据从数据库中取出或设计对应的生成规则；
4. 合理地将参数化数据保存在不同的文件中；
5. 在压力工具中设置相应的参数组合关系，以便实现模拟真实场景。

通过以上步骤，我们就可以合理的参数化数据，模拟出真实场景。

## 思考题

你可以思考一下下面几个问题：

1. 为什么参数化数据要符合生产环境的数据分布？
2. 为什么参数化数据要关注组合逻辑关系，而不是随意设置组合？

欢迎你在评论区写下你的思考，也欢迎把这篇文章分享给你的朋友或者同事，一起交流一下。
<div><strong>精选留言（15）</strong></div><ul>
<li><span>律飛</span> 👍（16） 💬（5）<p>JMeter 的 CSV Data Set Config 功能用来从文件中读取数据行，并将它们拆分后存储到变量中。个人理解，Recycle on EOF的优先级高于Stop thread on EOF，也就是说，需要先判断Recycle on EOF，如果是Flase，直接在文件结束时就停止了线程，根本不考虑Stop thread on EOF参数值；如果是True，就要根据Stop thread on EOF参数值来确定线程是否停止运行。在明白组合逻辑关系后，可以更高效的设置参数、更准确的达到测试目的。
各种测试工具有各种测试功能，可能其中就会存在有关联的参数配置，这也需要我们特别关注。如果查阅资料还不能清晰认识，就按老师的做法，通过对不同组合进行实验，最终弄清楚组合关系，归纳总结出优先顺序，从而在平时测试中帮助我们快速有效地找到最优的组合。</p>2020-01-07</li><br/><li><span>小昭</span> 👍（10） 💬（2）<p>今日思考题：
为什么参数化数据要符合生产环境的数据分布？
因为如果不符合生产环境的话，我们做这个性能测试就没有意义了。

为什么参数化数据要关注组合逻辑关系，而不是随意设置组合？
随意设置就会出现逻辑矛盾或者没有意义的组合。这样看上去节省了时间，其实反而浪费了时间。

今日感悟：
CSV Data Set Config这个功能之前学过，但是只是别人告诉我怎么填，我就照着填了，没有深入思考各个参数不同组合会有什么样的效果。这节课听下来，对这个功能的理解又深入了些。超值超值，感谢老师。

看了评论为了验证Recycle on EOF和Stop thread on EOF这两个参数的关系，我去JMeter里实践了一下，我的CSV文件里有7条数据，线程数我设置的8。
得出结论是：如果Recycle on EOF是Flase，Stop thread on EOF是Flase，由于线程数比文件数据多，JMeter会继续执行，但是由于没有数据，会报错，然后停止；如果Recycle on EOF是Flase，Stop thread on EOF是True，就直接停止。所以两个参数我认为需要结合起来看，虽然Recycle on EOF的优先级高一些，但也不是能起决定性作用的。


然后回过头来再看一遍文章发现其实我练习的这两种情况老师都讲了并且举了例子。我刚学完的时候是清楚的（至少自己感觉是清楚的），但是看了评论我发现还是有点懵，然后决定自己试一试。练习过之后，是真的明白了。所以真的要动手去做呀。</p>2020-03-20</li><br/><li><span>zuozewei</span> 👍（7） 💬（3）<p>第一个问题：为什么参数化数据要符合生产环境的数据分布？

在「01丨性能综述：性能测试的概念到底是什么」中已经讲过，性能模型中的业务模型是真实场景的抽象，即需要的数据通常都是从生产环境中的数据中统计来的，其关键就是「数据必须保证仿真」。
那么性能测试的时候我们需要特别注意压测流量以及相关的数据，必须保证它们的多样化和代表性，否则会导致测试结果会严重失真。
比如，当使用相同的测试数据进行重复测试时，如果压测请求不够大，那么各种缓存可能会严重影响测试结果。

第二个问题：为什么参数化数据要关注组合逻辑关系，而不是随意设置组合？

因为参数化数据要组合逻辑关系会直接影响参数化数据的分布情况，即数据是否均匀？数据是否稳定？是保否证测试时间足够长？满足测试的负载请求足够多和数据足够多样化，从而最大限度地减少或者掩盖缓存等其他因素的影响。</p>2020-01-20</li><br/><li><span>善行通</span> 👍（5） 💬（1）<p>感谢老师总结；
1、罗列出需要参数化的数据及相对应的关系；
2、将参数化数据从数据库中取出或设计对应的生成规则；
3、合理地将参数化数据保存在不同的文件中；
4、在压力工具中设置相应的参数组合关系，以便实模拟真实场景

之前做行测不太去理解：
Recycle on EOF? ：这里有三个选择，False、True 和 Edit。
Stop thread on EOF?：这里有三个选择，False、True 和 Edit。含义和上面一致。
Sharing mode : 这里有四个选择，All threads、Current thread group、Current thread、Edit。
这几个用户，经过老师这样一步一步分析，收获很大，谢谢老师分享

第一个问题：为什么参数化数据要符合生产环境的数据分布？
1、减少数据命中率；
2、减少缓存命中率；
3、符合性能压测价值,测试结果更真实；

第二个：为什么参数化数据要关注组合逻辑关系，而不是随意设置组合？
1、业务规则决定参数文件不能随便组合；
2、如果随意组合参数，会影响事务成功率；
</p>2020-01-06</li><br/><li><span>筱の简單</span> 👍（3） 💬（1）<p>1、为什么参数化数据要符合生产环境的数据分布？
因为压测本身就是服务于生产环境，为使项目满足真实用户的需要，所以做压测的宗旨都是以实际业务逻辑出发满足用户需要，所以参数化也依赖业务逻辑，故在参数化之前，需要分析真实业务逻辑中如何使用数据，再在工具中选择相对应的组合参数的方式去实现。
2、为什么参数化数据要关注组合逻辑关系，而不是随意设置组合？
因为不关注组合的逻辑关系而随意设置组合，有些组合会存在没有意义且不符合逻辑关系的情况。影响参数化设置的有效性，也侧面反映压测人员的技术专业性。</p>2020-02-22</li><br/><li><span>陈陈陈小芮</span> 👍（2） 💬（2）<p>老师您好，我是刚接触性能测试没多久，所以有点疑问想请教下：
1、tps每秒100，5分钟需要的用户数据就是5x60x100，意思就是一秒钟需要的用户数据就是100个吗？举个例子，我的线程数、循环数都设置为1，一个线程组下有13个接口请求，但其中只有login这一个请求需要用到账号密码，其余的12个都不需要，此时执行显示13个请求在3秒处理完成，tps为平均每秒4.2个请求，按上面的逻辑，也就是一秒需要4.2个用户账号密码吗，但是这就跟我原本只需要一个账号密码相悖了，所以不太理解这个所需用户数的计算
2、在之前的基础篇您有讲过，tps是指的一个完整的事物，这个事物可以自己定义，若按这个理解，那么tps就应该是一个登陆操作带来的一系列请求（用我举的例子就是包含login在内的13个请求），可是此处的tps似乎是每秒处理的请求数（3秒请求数13，每秒就是4.2左右），好像又并不是事物数，这个点也不太理解</p>2021-08-23</li><br/><li><span>兰澜</span> 👍（2） 💬（2）<p>高楼老师，听了这个课收获很多，理清了一些思路。刚刚学习性能测试，做了一些简单的项目，有一个很问题一直很困惑，做一个项目的性能测试是我们获得了项目中需要测试性能的各接口的TPS和响应时间指标，跑基准场景测试时，使用LR工具，我要如何来设置start new iteration中的第3个选项中的每间隔多长时间迭代一次的值呢，这个可以依据什么来计算呢？或者怎么设置比较合理？还有就是start vusers中的用户数，每隔多长时间启动多少个用户，这个怎么设置比较合理呢？刚踏入性能测试，不知道如何去设置跑场景时的这些参数值，不知道怎样才是合理的</p>2020-03-10</li><br/><li><span>武先生爱学习</span> 👍（2） 💬（1）<p>请问，在公司里，做性能测试用的是什么负载机，用的自己的机器还是Linux负载机呢，这一块能否介绍下？</p>2020-02-24</li><br/><li><span>小老鼠</span> 👍（2） 💬（1）<p>1，EOF处理不同对性能测试有什么影响？2，参数化用DB来获取，对性能测试结果的有无影响。</p>2020-01-10</li><br/><li><span>VintageCat</span> 👍（1） 💬（1）<p>
Java
summary +    125 in 00:00:04 =   31.0&#47;s Avg:    28 Min:     0 Max:   869 Err:     0 (0.00%) Active: 1 Started: 1 Finished: 0
summary +   3404 in 00:00:30 =  113.2&#47;s Avg:    31 Min:     0 Max:   361 Err:     0 (0.00%) Active: 6 Started: 6 Finished: 0
summary +   4444 in 00:00:30 =  148.4&#47;s Avg:    57 Min:     0 Max:   623 Err:    10 (0.23%) Active: 11 Started: 11 Finished: 0


这个登录接口的数据是怎么来的呢？我是指用什么策略执行的 ，没有很明白，看active分别是1 6 11这个是指不同的压力线程组情况下吧</p>2023-05-26</li><br/><li><span>galsangflower</span> 👍（1） 💬（1）<p>csv文件读变量会影响性能吗</p>2022-07-18</li><br/><li><span>🌻eleven</span> 👍（1） 💬（1）<p>一直没明白，选择“当前线程”是什么意思，怎么判断当前线程
</p>2022-06-09</li><br/><li><span>章鱼</span> 👍（1） 💬（1）<p>问题一：数据必须保证仿真，否则性能压测将没有意义
问题二：因为参数化数据要组合逻辑关系会直接影响参数化数据的分布情况，即数据是否均匀？数据是否稳定？是保否证测试时间足够长？满足测试的负载请求足够多和数据足够多样化，从而最大限度地减少或者掩盖缓存等其他因素的影响</p>2022-03-23</li><br/><li><span>敢不敢y-- 不敢</span> 👍（1） 💬（1）<p>我想知道这个数据是从哪里能看到的？？？？
Java
summary +    125 in 00:00:04 =   31.0&#47;s Avg:    28 Min:     0 Max:   869 Err:     0 (0.00%) Active: 1 Started: 1 Finished: 0
summary +   3404 in 00:00:30 =  113.2&#47;s Avg:    31 Min:     0 Max:   361 Err:     0 (0.00%) Active: 6 Started: 6 Finished: 0
summary +   4444 in 00:00:30 =  148.4&#47;s Avg:    57 Min:     0 Max:   623 Err:    10 (0.23%) Active: 11 Started: 11 Finished: 0</p>2022-03-20</li><br/><li><span>bolo</span> 👍（1） 💬（1）<p>1、为什么参数化数据要符合生产环境的数据分布？
个人理解因为测试用的数据要尽可能的贴近生产环境的。比如需要MQ相关的测试，我们一般通过从生产环境MQ平台查找符合条件的的消息，然后进行特定字段的修改后拿到测试环境经行测试（自己构造的话，很容易出现信息偏差，风险也较高）
另外一个例子是，我们有一个项目需要将媒体上报的设备字段落入到数据库，因为真实的用户的设备字段是不一样的，所以针对设备参数化的时候需要满足一定的位数，以及数字及字母的组合来模拟真实的线上用户。数据库层面根据设备字段又进行了数据的分库分表，如果参数化不合理（或者采用同一条数据），会导致数据分布的不够均匀，也是不符合产品需求的

2、实际操作了Jmeter里的CSV Data Set Config配置，
第1种场景：（更加贴近实际需要，循环执行的时候仅使用csv的数据。当循环次数超出时，终止执行。）
a)  Recyele on EOF 设置为 False(不再循环使用参数)
b)  Stop thread on EOF 设置为True (在参数不足时停止线程)
c)  Sharing mode设置为 All thead (所有线程)
CSV内的数据仅有6条，而线程数设置为1， 循环次数设置为8 
执行后，执行6次  成功后结束


第2种场景 循环csv的文件（循环使用参数后，不会存在参数不足的情况了。没有意义）
a)  Recyele on EOF 设置为 True(循环使用参数)
b)  Stop thread on EOF 设置为True (参数不足时，停止线程)
c)  Sharing mode设置为 All thead (所有线程)
CSV内的数据仅有6条，而线程数设置为1， 循环次数设置为8 
执行后，执行8次成功后结束


第3种场景 循环csv的文件（循环使用参数后，不会存在参数不足的情况了。没有一直）
a)  Recyele on EOF 设置为 True(循环使用参数)
b)  Stop thread on EOF 设置为False (参数不足时，不停止线程)
c)  Sharing mode设置为 All thead (所有线程)
CSV内的数据仅有6条，而线程数设置为1， 循环次数设置为8 
执行后，执行8次成功后结束


第4种场景 循环csv的文件（不符合场景，不循环使用参数，再循环次数设置的比较大的时候，肯定会存在参数不足的情况的）
a)  Recyele on EOF 设置为 False(不循环使用参数)
b)  Stop thread on EOF 设置为False (参数不足时，不停止线程)
c)  Sharing mode设置为 All thead (所有线程)
CSV内的数据仅有6条，而线程数设置为1， 循环次数设置为8 
执行后，执行8次，前6次成功，后2次失败</p>2021-02-24</li><br/>
</ul>