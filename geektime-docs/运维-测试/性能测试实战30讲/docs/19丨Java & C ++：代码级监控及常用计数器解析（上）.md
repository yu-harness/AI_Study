在性能测试分析中，有一部分人存在着一个思路上的误解，那就是一开始就一头扎进代码里，折腾代码性能。这是我非常反对的一种做法。

事实上，要想这么做，有一个前提，那就是架构中的其他组件都经过了千锤百炼，出现问题的可能性极低。

实际上，我凭着十几年的经验来看，大部分时候，代码出现严重性能瓶颈的情况还真是不多。再加上现在成熟的框架那么多，程序员们很多情况下只写业务实现。在这种情况下，代码出现性能瓶颈的可能性就更低了。

但我们今天终归要说代码级的监控及常用的计数器。如何去评估一个业务系统的代码性能呢？在我看来，分析的思路是下面这个样子的。

![](https://static001.geekbang.org/resource/image/ee/e3/eebce7bd7cab91685baf4a9a526be9e3.jpg?wh=1542%2A1112)

从上图可以看到，分析的时候有两个关键点：执行时间和执行空间。我相信很多人都清楚，我们要很快找到执行时间耗在哪一段和空间耗在哪里。

现在我们来实际操作一下，看如何判断。

## Java类应用查找方法执行时间

首先你得选择一个合适的监控工具。Java方法类的监控工具有很多，这里我选择JDK里自带的jvisualvm。

顺便说一下，我的Java版本号是这个：

```
(base) GaoLouMac:~ Zee$ java -version
java version "1.8.0_111"
Java(TM) SE Runtime Environment (build 1.8.0_111-b14)
Java HotSpot(TM) 64-Bit Server VM (build 25.111-b14, mixed mode)
```

打开应用服务器上的JMX之后，连上jvisualvm，你会看到这样的视图。

![](https://static001.geekbang.org/resource/image/76/36/76e17407985e427e832c0de988cc8f36.png?wh=1254%2A727)

这里再啰嗦一下我们的目标，这时我们要找到消耗CPU的方法，所以要先点`Sampler - CPU`，你可以看到如下视图。

![](https://static001.geekbang.org/resource/image/d3/63/d3a21195b1b8bcb1838df3d7ec76ef63.png?wh=1420%2A751)

从上图可以看到方法执行的累积时间，分别为自用时间百分比、自用时间、自用时间中消耗CPU的时间、总时间、总时间中消耗CPU的时间、样本数。

从这些数据中就可以看到方法的执行效率了。

但是，这里面Method这么多，我怎么知道哪个跟我的方法执行时间有关呢？比如说上面这个应用中，最消耗CPU的是JDBC的一个方法fill。这合理吗？

先来看一下我的脚本。

![](https://static001.geekbang.org/resource/image/ad/b8/ad1e7b5f712dcbb7e7b35af084f01db8.png?wh=223%2A275)

从结构上你就能看出来，我做了登录，然后就做了创建的动作，接着就退出了。

这几个操作和数据库都有交互。拿create这个步骤来说，它的脚本非常直接，就是一个POST接口。

![](https://static001.geekbang.org/resource/image/7d/dd/7dadcb5071e391a7c97f9ae91e00c9dd.png?wh=991%2A337)

还记得前面我们怎么说查看后端的运行逻辑的吗？后端接收这个POST的代码如下：

```
    @RequestMapping("/save")
    @ResponseBody
    public Object save(Blog blog, HttpSession session){
        try{
            Long id = blog.getId();
            if(id==null){
                User user = (User)session.getAttribute("user");
                blog.setAuthor(user.getName());
                blog.setUserId(user.getId());
                blog.setCreateTime(new Date());
                blog.setLastModifyTime(new Date());
                blogWriteService.create(blog);
            }else {
                blog.setLastModifyTime(new Date());
                blogWriteService.update(blog);
            }
        }catch (Exception e){
            throw new JsonResponseException(e.getMessage());
        }
        return true;
    }
```

这段代码的功能就是讲前端内容接收过来放到实体中，然后通过create方法写到数据库中。那么create是怎么实现的呢？

```
    public void  create(Blog blog) {
        mapper.insert(blog);
        BlogStatistics blogStatistics = new BlogStatistics(blog.getId());
        blogStatisticsMapper.insert(blogStatistics);
```

它就是一个mapper.insert，显然这个create是我们自己实现的代码，里面其实没有什么逻辑。而ReadAheadInputStream.fill是create中的MyBatis调用的JDBC中的方法。 从压力工具到数据库的调用逻辑就是：

![](https://static001.geekbang.org/resource/image/e2/a6/e23bec9dd1d7712ff541c86479433ba6.jpg?wh=1424%2A606)

而我们看到的最耗时的方法是最后一个，也就是fill。实际上，我们应该关心的是save接口到底怎么样。我们来过滤下看看。

![](https://static001.geekbang.org/resource/image/53/af/535a53ffb59aa005830e5f30159c2faf.png?wh=1431%2A131)

从save的结果上来看，它本身并没有耗什么时间，都是后面的调用在消耗时间。

我们再来看看cerate。

![](https://static001.geekbang.org/resource/image/36/b6/36e52d8b3f346aa6b66ece606aa6e6b6.png?wh=1286%2A385)

它本身也没消耗什么时间。

顺着逻辑图，我们再接着看MyBatis中的insert方法。

![](https://static001.geekbang.org/resource/image/c7/8a/c780aa816eb132eea8acc0bb06cc0e8a.png?wh=1291%2A131)

就这样一层层找下去，最后肯定就找到了fill这个方法了。但是你怎么知道整个调用逻辑中有哪些层级呢？你说我可以看源码。当然不是不可以。但要是没有源码呢？做性能分析的人经常没有源码呀。

这个时候，我们就要来看栈了。这里我打印了一个调用栈，我们来看下这个逻辑。

```
"http-nio-8080-exec-1" - Thread t@42
   java.lang.Thread.State: RUNNABLE
	...............
	at com.mysql.jdbc.util.ReadAheadInputStream.fill(ReadAheadInputStream.java:100)
    ...............
    ...............
    at com.sun.proxy.$Proxy87.create(Unknown Source)
	...............
	at com.blog.controller.BackBlogController.save(BackBlogController.java:85)
	...............
	at java.lang.Thread.run(Thread.java:745)


   Locked ownable synchronizers:
	- locked <4b6968c3> (a java.util.concurrent.ThreadPoolExecutor$Worker)
```

我把其他的都给清掉了，我们只看最简单的栈逻辑，其中UnknownSource的部分是因为反射实现的insert没有把源码反编译出来。

其实这个栈有117行，我怕你看晕。

从这一层一层的关系中，我们就可以知道调用逻辑了。知道调用逻辑的方法有很多，看源码也行，看编译后运行的代码也行，关键在于知道谁调了谁，这样就行了。

我这个还算是清晰的调用逻辑，要是代码调用关系再复杂一些，分分钟有想死有没有？

不过比较好的是，像jvisualvm这样的工具给我们提供了很多便利。这时可能有人会跳起来了，为什么不用Arthas、BTrace之类的工具呢？如果你喜欢的话，可以把Athas弄上，像下面这样。

```
[arthas@1]$ trace com.blog.controller.BackBlogController save
Press Q or Ctrl+C to abort.
Affect(class-cnt:2 , method-cnt:2) cost in 320 ms.
`---ts=2020-01-06 10:38:37;thread_name=http-nio-8080-exec-2;id=2b;is_daemon=true;priority=5;TCCL=org.apache.catalina.loader.ParallelWebappClassLoader@4f2895f8
    `---[29.048684ms] com.blog.controller.BackBlogController$$EnhancerBySpringCGLIB$$586fe45c:save()
        `---[28.914387ms] org.springframework.cglib.proxy.MethodInterceptor:intercept() #0
            `---[27.897315ms] com.blog.controller.BackBlogController:save()
                ...............
                `---[24.192784ms] com.blog.service.BlogWriteService:create() #85
```

这也能看出来creat是消耗了时间的。如果你接着跟踪create方法。如下所示：

```
[arthas@1]$ trace com.blog.service.BlogWriteService create //这一行是arthas中跟踪class中的某个具体方法的语句。
Press Q or Ctrl+C to abort.
Affect(class-cnt:2 , method-cnt:2) cost in 199 ms. //被跟踪方法的处理次数和时长
`---ts=2020-01-06 10:41:51;thread_name=http-nio-8080-exec-4;id=2f;is_daemon=true;priority=5;TCCL=org.apache.catalina.loader.ParallelWebappClassLoader@4f2895f8
    `---[6.939189ms] com.sun.proxy.$Proxy87:create()
`---ts=2020-01-06 10:41:51;thread_name=http-nio-8080-exec-10;id=38;is_daemon=true;priority=5;TCCL=org.apache.catalina.loader.ParallelWebappClassLoader@4f2895f8
        `---[4.144799ms] com.blog.service.BlogWriteServiceImpl:create()  //写接口中create方法耗时
            +---[2.131934ms] tk.mybatis.mapper.common.Mapper:insert() #24   //mybatis中insert方法耗时
                ...............
            `---[1.95441ms] com.blog.mapper.BlogStatisticsMapper:insert() #26 //insert方法调用了上面的create方法耗时
```

要是接着往下跟踪，就可以看到反射这一块了。

```
[arthas@1]$ trace tk.mybatis.mapper.common.Mapper insert
Press Q or Ctrl+C to abort.
Affect(class-cnt:5 , method-cnt:5) cost in 397 ms.
`---ts=2020-01-06 10:44:01;thread_name=http-nio-8080-exec-5;id=33;is_daemon=true;priority=5;TCCL=org.apache.catalina.loader.ParallelWebappClassLoader@4f2895f8
    `---[3.800107ms] com.sun.proxy.$Proxy80:insert()
```

类似的，你还可以玩JDK自带的工具jdb，它也可以直接attach到一个进程上，调试能力也是不弱的。

在我看来，这些工具、手段都是为了实现从`响应时间长<->代码行`的分析过程。思路是最重要的。

另外也要说一下，现在有的APM工具也可以实现这样的功能，但是呢，我并不建议一开始就上这么细致的工具，因为不管APM产品吹得有多牛逼，它都是要消耗10%左右的CPU的。并且，你觉得直接在生产上装一个APM工具的agent到业务系统中是合理的吗？如果是自己实现的metrics方法，输出性能数据尚可接受，如果是别人的这类工具，还是算了。

在大部分时候，我都不建议在生产上用APM工具。万一生产上真的有极端的情况，需要看细致的性能问题，再临时attach上去，也可以做到。何必为了可能出现的问题而长时间地消耗资源呢。

## 总结

大部分时间里，性能测试和分析都在和时间打交道，而在时间的拆分逻辑中，我们在前面也提到过思路，如何一步步把时间拆解到应用当中，那就是**分段**。

当拆解到应用当中之后，就是抓函数方法的执行时间了。这是保证我们从前到后分析逻辑的关键一环，请你注意，是关键一环，而不是最初的一环。

通过这篇文章我想告诉你，在大部分的开发语言中，都有手段直接将方法的执行时间消耗抓出来，你可能现在还不知道是什么方法，没关系，因为跟踪的手段有很多，你可以临时去学习如何操作。

我只要在你的脑子里种下这样的一种印象，那就是，有办法抓到函数方法的执行时间消耗在哪里！

## 思考题

最后给你留两道思考题吧。我为什么不建议在生产环境中一开始就上APM类工具来抓取方法的执行时间呢？你有什么方法可以抓取到Java语言中的方法执行时间？如果你擅长其他语言，也可以描述其他语言中的方法执行时间抓取工具。

欢迎你在评论区写下你的思考，也欢迎把这篇文章分享给你的朋友或者同事，一起交流一下。
<div><strong>精选留言（15）</strong></div><ul>
<li><span>嘟嘟爱学习</span> 👍（11） 💬（2）<p>我觉得某些生产环境还是可以直接上APM的：
1. 能接受10%性能损耗的，比如原来耗时1秒，上了变成1.1秒其实感觉不明显；原来高峰期CPU使用率30%，上了变成40%也还在可接受范围内；
2. APM的成功失败不影响业务的运行，就是即使APM挂了，业务也还能正常运行；
3. 在docker+k8且又有大量虚机大量服务的情况下，上APM也是一个方案，不然当出现问题时要在那么多服务里面把问题定位到，用jmx这类监控很容易措手不及和慌手慌脚。
4. 现在好些公司没有专职性能测试，好些系统没有经过性能测试就上线的，此时APM是开发和运维人员的一个救命稻草了，这种公司我相信很多。</p>2020-02-08</li><br/><li><span>aoe</span> 👍（8） 💬（1）<p>在我知识范围内Java最强的监控工具是Oracle 开发的 JMC，没有之一。前Oracle首席工程师在 极客时间的《Java核心技术面试精讲》专栏 | 第26讲 | 如何监控和诊断JVM堆内和堆外内存使用？ 文中提到：“我这里特别推荐Java Mission Control（JMC），这是一个非常强大的工具，不仅仅能够使用JMX进行普通的管理、监控任务，还可以配合Java Flight Recorder（JFR）技术，以非常低的开销，收集和分析 JVM 底层的 Profiling 和事件等信息。目前， Oracle 已经将其开源，如果你有兴趣请可以查看 OpenJDK 的Mission Control项目。”</p>2020-10-14</li><br/><li><span>凌空飞起的剪刀腿</span> 👍（4） 💬（1）<p>使用strace 跟踪进程流程</p>2020-04-03</li><br/><li><span>alley</span> 👍（2） 💬（1）<p>perftop 可以查看CPU热点函数</p>2021-02-16</li><br/><li><span>娜娜</span> 👍（1） 💬（1）<p>请问老师C++、C的怎么监控</p>2022-07-28</li><br/><li><span>Geek_6a9aeb</span> 👍（1） 💬（1）<p>老师，为啥说代码造成瓶颈不多呢，高并发带来java线程死锁的情况 是很常见的代码问题吧</p>2021-01-12</li><br/><li><span>老街头的猫🐱。</span> 👍（1） 💬（1）<p>高老师，这个第一个调用栈是用什么命令打出来的，根据什么关键字？在 jvisualvm中没看到进程ID呀？</p>2020-10-19</li><br/><li><span>月亮和六便士</span> 👍（1） 💬（1）<p>高老师：1. 打调用栈的时候，怎么保证打印出来的正好是自己写的方法的调用栈，而不是一堆没用的调用栈，我连续打几次都不是自己写的方法的调用栈，这时候我觉得一定有什么技巧，而我不知道。2，interrunpts --&gt; softirqs 怎么对应，我知道interrunpts 逻辑终端号是 45，中断设备是网卡，在softirqs中没有找到45这个号，里面只有网卡设备模块。准备把老师的专栏，手抄一遍，然后练习一遍，然后再理解一遍</p>2020-04-08</li><br/><li><span>顺利</span> 👍（1） 💬（1）<p>分段拆分时间如何做呢老师，没找到前面的相应内容。有什么工具吗？</p>2020-02-27</li><br/><li><span>蜡笔小新爱看书</span> 👍（0） 💬（1）<p>打开应用服务器上的 JMX 之后，连上 jvisualvm，你会看到这样的视图。

这个具体是怎么操作？能说明一下吗？</p>2023-07-17</li><br/><li><span>蔚来懿</span> 👍（0） 💬（1）<p>老师，学到这一节了，为啥我还是不知道，响应时间长，怎么定位到代码这一层了，前面系统层的如何定位（操作系统、进程、线程耗时，这块在怎么得出时间呢？），么有看到在哪里可以分析出来的？</p>2021-01-16</li><br/><li><span>蔡森冉</span> 👍（0） 💬（1）<p>降到agent我记得在华为云控制台要监控服务器就是安装了这个东西的</p>2020-03-23</li><br/><li><span>目标就是这么明确</span> 👍（0） 💬（1）<p>清晰</p>2020-03-20</li><br/><li><span>董飞</span> 👍（0） 💬（1）<p>越来越看不懂了，老师，推荐下这方面的资料。</p>2020-03-18</li><br/><li><span>Hulk</span> 👍（2） 💬（0）<p>Arthas</p>2020-02-27</li><br/>
</ul>