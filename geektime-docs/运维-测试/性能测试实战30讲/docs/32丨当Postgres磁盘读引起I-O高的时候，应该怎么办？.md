在性能分析的人眼里，性能瓶颈就是性能瓶颈。无论这个性能瓶颈出现在代码层、操作系统层、数据库层还是其他层，最终的目的只有一个结果：解决掉！

有人可能会觉得这种说法过于霸道。

事实上，我要强调的性能分析能力，是一套分析逻辑。在这一套分析逻辑中，不管是操作系统、代码还是数据库等，所涉及到的都只是基础知识。如果一个人都掌握这些内容，那确实不现实，但如果是对一个性能团队的要求，我觉得一点也不高。

在性能测试和性能分析的项目中，没有压力发起，就不会有性能瓶颈，也就谈不上性能分析了。所以每个问题的前提，都是要有压力。

但不是所有的压力场景都合理，再加上即使压力场景不合理，也能压出性能瓶颈，这就会产生一种错觉：似乎一个错误的压力场景也是有效的。

我是在介入一个项目时，首先会看场景是否有效。如果无效，我就不会下手去调了，因为即使优化好了，可能也给不出生产环境应该如何配置的结论，那工作就白做了。

所以要先调场景。

我经常会把一个性能测试项目里的工作分成两大阶段：

### 整理阶段

在这个阶段中，要把之前项目中做错的内容纠正过来。不止有技术里的纠正，还有从上到下沟通上的纠正。

### 调优阶段

这才真是干活的阶段。

在这个案例中，同样，我还是要表达一个分析的思路。

## 案例问题描述

这是一个性能从业人员问的问题：为什么这个应用的update用了这么长时间呢？他还给了我一个截图：

![](https://static001.geekbang.org/resource/image/fe/ac/fe83f42fd8b130b561e2a8f79c7cabac.png?wh=1569%2A507)

从这个图中可以看到时间在100毫秒左右。根据我的经验，一个SQL执行100ms，对实时业务来说，确实有点长了。

但是这个时间是长还是短，还不能下结论。要是业务需要必须写成这种耗时的SQL呢？

接着他又给我发了TPS图。如下所示：

![](https://static001.geekbang.org/resource/image/ee/24/ee0ec6e2a7038611ccb30d7b5bf66824.png?wh=1435%2A737)

这个TPS图确实……有点乱！还记得前面我对TPS的描述吧，在一个场景中，TPS是要有阶梯的。

如果你在递增的TPS场景中发现了问题，然后为了找到这个问题，用同样的TPS级别快速加起来压力，这种方式也是可以的。只是这个结果不做为测试报告，而是应该记录到调优报告当中。

而现在我们看到的这个TPS趋势，那真是哪哪都挨不上呀。如此混乱的TPS，那必然是性能有问题。

他还告诉了我两个信息。

1. 有100万条参数化数据；
2. GC正常，dump文件也没有死锁的问题。

这两个信息应该说只能是信息，并不能起到什么作用。另外，我也不知道他说的“GC正常”是怎么个正常法，只能相信他说的。

以上就是基本的信息了。

## 分析过程

照旧，先画个架构图出来看看。

每次做性能分析的时候，我几乎都会先干这个事情。只有看了这个图，我心里才踏实。才能明确知道要面对的系统范围有多大；才能在一个地方出问题的时候，去考虑是不是由其他地方引起的；才能跟着问题找到一条条的分析路径……

下面是一张简单的架构图，从下面这张架构图中可以看到，这不是个复杂的应用，是个非常典型的微服务结构，只是数据库用了PostgreSQL而已。

![](https://static001.geekbang.org/resource/image/21/3d/21e32cd936482c970abb2ef02007563d.jpg?wh=1069%2A423)

由于这个问题反馈的是从服务集群日志中看到的update慢，所以后面的分析肯定是直接对着数据库去了。

这里要提醒一句，我们看到什么现象，就跟着现象去分析。这是非常正规的思路吧。但就是有一些人，明明看着数据库有问题，非要瞪着眼睛跟应用服务器较劲。

前不久就有一个人问了我一个性能问题，说是在压力过程中，发现数据库CPU用完了，应用服务器的CPU还有余量，于是加了两个数据库CPU。但是加完之后，发现数据库CPU使用率没有用上去，反而应用服务器的CPU用完了。我一听，觉得挺合理的呀，为什么他在纠结应用服务器用完了呢？于是我就告诉他，别纠结这个，先看时间耗在哪里。结果发现应用的时间都耗在读取数据库上了，只是数据库硬件好了一些而已。

因为这是个在数据库上的问题，所以我直接查了数据库的资源。

![](https://static001.geekbang.org/resource/image/dc/78/dcacb613ed1d09dfa56d500c10307e78.png?wh=1059%2A378)

查看vmstat，从这个结果来看，系统资源确实没用上。不过，请注意，这个bi挺高，能达到30万以上。那这个值说明了什么呢？我们来算一算。

bi是指每秒读磁盘的块数。所以要先看一下，一块有多大。

```
[root@7dgroup1 ~]# tune2fs -l /dev/vda1 | grep "Block size"
Block size:               4096
[root@7dgroup1 ~]#
```

那计算下来大约就是：

$(300000\*4096)/1024/1024=1172M$

1172M的读取，显然这个值是不低的。

接下来查看I/O。再执行下iostat看看。

![](https://static001.geekbang.org/resource/image/59/74/59600c6b74472e8d8e3e9c785bb22674.png?wh=1590%2A537)

从这个结果来看，%util已经达到了95%左右，同时看rkB/s那一列，在300M左右。

接着在master上面的执行iotop。

![](https://static001.geekbang.org/resource/image/8b/5a/8b4e86cc2835768bc7477e09a36c3a5a.png?wh=1503%2A711)

我发现Walsender Postgres进程达到了56.07%的使用率，也就是说它的读在300M左右。但是写的并不多，从图上看只有5.77M/s。

结合上面几个图，我们后面的优化方向就是：**降低读取，提高写入**。

到这里，我们就得说道说道了。这个Walsender Postgres进程是干吗的呢？

我根据理解，画了一个Walsender的逻辑图：

![](https://static001.geekbang.org/resource/image/a2/3b/a250bc12f25ded65ea6287912891dd3b.jpg?wh=1463%2A440)

从这个图中就可以看得出来，Walsender和Walreceiver实现了PostgreSQL的Master和Slave之间的流式复制。Walsender取归档目录中的内容（敲黑板了呀！），通过网络发送给Walreceiver，Walreceiver接收之后在slave上还原和master数据库一样的数据。

而现在读取这么高，那我们就把读取降下来。

先查看一下几个关键参数：

![](https://static001.geekbang.org/resource/image/e3/bf/e3313d522881096d711e77503e0454bf.png?wh=625%2A138)

![](https://static001.geekbang.org/resource/image/93/b1/93441006fdb611b1b07beec5566129b1.png?wh=400%2A125)

这两个参数对PostgreSQL非常重要。checkpoint\_completion\_target这个值表示这次checkpoint完成的时间占到下一次checkpoint之间的时间的百分比。

这样说似乎不太好理解。画图说明一下：

![](https://static001.geekbang.org/resource/image/e9/30/e9fccc9914c54e17e75d1c44baeb9b30.jpg?wh=466%2A116)

在这个图中300s就是checkpoint\_timeout，即两次checkpoint之间的时间长度。这时若将checkpoint\_completion\_target设置为0.1，那就是说CheckPoint1完成时间的目标就是在30s以内。

在这样的配置之下，你就会知道checkpoint\_completion\_target设置得越短，集中写的内容就越多，I/O峰值就会高；checkpoint\_completion\_target设置得越长，写入就不会那么集中。也就是说checkpoint\_completion\_target设置得长，会让写I/O有缓解。

在我们这个案例中，写并没有多少。所以这个不是什么问题。

但是读取的I/O那么大，又是流式传输的，那就是会不断地读文件，为了保证有足够的数据可以流式输出，这里我把shared\_buffers增加，以便减轻本地I/O的的压力。

来看一下优化动作：

```
checkpoint_completion_target = 0.1
checkpoint_timeout = 30min
shared_buffers = 20G
min_wal_size = 1GB
max_wal_size = 4GB
```

其中的max\_wal\_size和min\_wal\_size官方含义如下所示。

max\_wal\_size (integer)：

> Maximum size to let the WAL grow to between automatic WAL checkpoints. This is a soft limit; WAL size can exceed max\_wal\_size under special circumstances, like under heavy load, a failing archive\_command, or a high wal\_keep\_segments setting. The default is 1 GB. Increasing this parameter can increase the amount of time needed for crash recovery. This parameter can only be set in the postgresql.conf file or on the server command line.

min\_wal\_size (integer)：

> As long as WAL disk usage stays below this setting, old WAL files are always recycled for future use at a checkpoint, rather than removed. This can be used to ensure that enough WAL space is reserved to handle spikes in WAL usage, for example when running large batch jobs. The default is 80 MB. This parameter can only be set in the postgresql.conf file or on the server command line.

请注意，上面的shared\_buffers是有点过大的，不过我们先验证结果再说。

## 优化结果

再看iostat：

![](https://static001.geekbang.org/resource/image/23/45/23ab209aedc2282eee042f0c4b941645.png?wh=1370%2A737)

看起来持续的读降低了不少。效果是有的，方向没错。再来看看TPS：  
![](https://static001.geekbang.org/resource/image/f1/bc/f12e8ba227c6a66e0dfb9d60794c46bc.png?wh=1490%2A637)

看这里TPS确实稳定了很多，效果也比较明显。

这也就达到我们优化的目标了。就像在前面文章中所说的，在优化的过程中，当你碰到TPS非常不规则时，请记住，一定要先把TPS调稳定，不要指望在一个混乱的TPS曲线下做优化，那将使你无的放矢。

## 问题又来了？

在解决了上一个问题之后，没过多久，另一个问题又抛到我面前了，这是另一个接口，因为是在同一个项目上，所以对问问题的人来说，疑惑还是数据库有问题。

来看一下TPS：

![](https://static001.geekbang.org/resource/image/dc/97/dcd93f0218e4311de099404bba562297.png?wh=1589%2A562)

这个问题很明显，那就是后面的成功事务数怎么能达到8000以上？如果让你蒙的话，你觉得会是什么原因呢？

在这里，告诉你我对TPS趋势的判断逻辑，那就是**TPS不能出现意外的趋势。**

什么叫意外的趋势？就是当在运行一个场景之前就已经考虑到了这个TPS趋势应该是个什么样子（做尝试的场景除外），当拿到运行的结果之后，TPS趋势要和预期一致。

如果没有预期，就不具有分析TPS的能力了，最多也就是压出曲线，但不会懂曲线的含义。

像上面的这处TPS图，显然就出现意外了，并且是如此大的意外。前面只有1300左右的TPS，后面怎么可能跑到8000以上，还全是对的呢？

所以我看到这个图之后，就问了一下：是不是没加断言？

然后他查了一下，果然没有加断言。于是重跑场景。得到如下结果：

![](https://static001.geekbang.org/resource/image/bc/a0/bc81f1c069d430d56786dd44e9e28ba0.png?wh=1458%2A644)  
从这个图上可以看到，加了断言之后，错误的事务都正常暴露出来了。像这种后台处理了异常并返回了信息的时候，前端会收到正常的HTTP Code，所以才会出现这样的问题。

这也是为什么通常我们都要加断言来判断业务是否正常。

## 总结

在性能分析的道路上，我们会遇到各种杂七杂八的问题。很多时候，我们都期待着性能测试中的分析像破案一样，并且最好可以破一个惊天地泣鬼神的大案，以扬名四海。

然而分析到了根本原因之后，你会发现优化的部分是如此简单。

其实对于PostgreSQL数据库来说，像buffer、log、replication等内容，都是非常重要的分析点，在做项目之前，我建议先把这样的参数给收拾一遍，不要让参数配置成为性能问题，否则得不偿失。

## 思考题

最后问你两个问题吧。为什么加大buffer可以减少磁盘I/O的压力？为什么说TPS趋势要在预期之内？

欢迎你在评论区写下你的思考，我会和你一起交流。也欢迎把这篇文章分享给你的朋友或者同事，一起交流一下。
<div><strong>精选留言（15）</strong></div><ul>
<li><span>罗辑思维</span> 👍（13） 💬（3）<p>分享下自己学习体会：
为什么缓存可以加速I&#47;O的访问速度？
老师说的缓存应该有两个：操作系统的缓存和PostgreSQL的缓存。它俩作用都是为了把经常访问的数据（也就是热点数据），提前读入到内存中。这样，下次访问时就可以直接从内存读取数据，而不需要经过硬盘，从而加速I&#47;O 的访问速度。

因为没接触过PostgreSQL,在做思考题时找了些资料，下面是延伸的学习。
PostgreSQL缓存跟操作系统的缓存有啥联系？

1.在访问数据时，数据会先加载到操作系统缓存，然后再加载到shared_buffers，这个加载过程可能是一些查询，也可以使用pg_prewarm预热缓存。
2.当然也可能同时存在操作系统和shared_buffers两份一样的缓存（双缓存）。
3.查找到的时候会先在shared_buffers查找是否有缓存，如果没有再到操作系统缓存查找，最后再从磁盘获取。
4.操作系统缓存使用简单的LRU（移除最近最久未使用的缓存），而PostgreSQL采用的优化的时钟扫描，即缓存使用频率高的会被保存，低的被移除。

PostgreSQL缓存读顺序share_buffers -&gt; 操作系统缓存 -&gt; 硬盘。那么也可能是操作系统缓存不足，而不定是share_buffers。通过文章中vmstat命令看到cache有260G，free值也很稳定，所以应该检查PostgreSQL的缓存。（老师执行vmstat是不是埋了个伏笔）。

参考资料
https:&#47;&#47;www.cnblogs.com&#47;zhangfx01&#47;p&#47;postgresql_shared_buffer.html
https:&#47;&#47;blog.csdn.net&#47;kwame211&#47;article&#47;details&#47;78665999</p>2020-03-05</li><br/><li><span>Geek_7cf52a</span> 👍（3） 💬（1）<p>bi 是指每秒读磁盘的块数。所以要先看一下，一块有多大。

[root@7dgroup1 ~]# tune2fs -l &#47;dev&#47;vda1 | grep &quot;Block size&quot;
Block size: 4096
[root@7dgroup1 ~]#

(300000∗1024)&#47;1024&#47;1024≈293M

=====================================================
=====================================================
上面为原文
这里指的是块。但是老师这样算也错了吧，一块是4096byte,那300000块的大小应该是300000*4096&#47;1024&#47;1024=1172M</p>2020-07-09</li><br/><li><span>jy</span> 👍（2） 💬（5）<p>bi 是指每秒读磁盘的块数。所以要先看一下，一块有多大。

[root@7dgroup1 ~]# tune2fs -l &#47;dev&#47;vda1 | grep &quot;Block size&quot;
Block size:               4096
[root@7dgroup1 ~]#

(300000∗1024)&#47;1024&#47;1024≈293M

=====================================================
=====================================================
上面为原文

问题一：
老师，这里是不是有问题？
bi表示从块设备读入数据的总量（即读磁盘）（kb&#47;s），而不是每秒读磁盘的块数
其实，这样算就可以了：300000&#47;1024≈293M


问题二：查询Block size的目的是？我看这个4096和iostat图中r&#47;s列的值差不多，
而r&#47;s表示每秒完成读IO设备的次数</p>2020-05-20</li><br/><li><span>月亮和六便士</span> 👍（2） 💬（1）<p>老师假如一条SQL语句执行100毫秒，我们一般觉得需要去优化SQL语句，但是也可能是等到磁盘读取消耗了大部分时间，我们如何区分这种情况？</p>2020-04-25</li><br/><li><span>rainbowzhouj</span> 👍（2） 💬（1）<p>CPU的处理速度与磁盘的处理速度不同，Buffer能起到协调和缓冲的作用，增加Buffer增加了缓冲的空间，故磁盘I&#47;O的压力就会减少。</p>2020-04-05</li><br/><li><span>Geek_6a9aeb</span> 👍（1） 💬（1）<p>原文:这个 bi 挺高，能达到 30 万以上。那这个值说明了什么呢？我们来算一算。
bi 是指每秒读磁盘的块数。 
-------------------------------------------
老师这里，30万是指有30万块数，还是30万kb的数据， 如果是kb那没有必要查一块是多大的呀？</p>2021-02-03</li><br/><li><span>。。。</span> 👍（1） 💬（1）<p>继续打卡</p>2020-03-12</li><br/><li><span>qtracer</span> 👍（0） 💬（1）<p>（1）为什么加大 buffer 可以减少磁盘 I&#47;O 的压力？
buffer可以缓存和合并来自文件系统的写请求，当积累足够多刷盘的时候，可以顺序写，提高写效率。
（2）为什么说 TPS 趋势要在预期之内？
TPS趋势不在预期内，无法准确判断瓶颈在什么时候出现的，不利于进一步分析。</p>2024-03-20</li><br/><li><span>坚持半途而废</span> 👍（0） 💬（1）<p>一块是4096个字节，读每秒到了300000次
为啥是：
（300000*1024）&#47;1024&#47;1024？
不应该是：
（300000*4096）&#47;1024？</p>2021-11-05</li><br/><li><span>坚持半途而废</span> 👍（0） 💬（1）<p>确实没有看明白，怎么等于300M的</p>2021-11-05</li><br/><li><span>Geek_6a9aeb</span> 👍（0） 💬（1）<p>老师，看了一下午太困惑了，后面一下子就写到优化的动作，看 shared_buffers 最后一下子是20g, 没看到调优前这些值是多大的？ 难道调优前是特别小吗？</p>2021-02-03</li><br/><li><span>David.cui</span> 👍（0） 💬（1）<p>老师，我遇到一个国产数据库的的压测场景。数据库+Loadrunner。loadrunner录制好了脚本，通过增加用户数来增加压力。刚开始通过增加用户把数据库的CPU压满了，TPS还可以。
后来数据库做了一个调优，TPS一下就高出来很多，但是CPU再也上不去了，基本上就维持在30-40%左右。我怀疑是数据库测使用了类似于结果集缓存的技术，只是给Loadrunner返回结果，至于结果的准确性就无从知道了。但是怎么去确认呢？</p>2020-12-07</li><br/><li><span>rainbowzhouj</span> 👍（0） 💬（1）<p>第一个问题，为什么加大 Buffer 可以减少磁盘 I&#47;O 的压力？
</p>2020-04-05</li><br/><li><span>rainbowzhouj</span> 👍（0） 💬（1）<p>高老师，您好，以下是我对两个问题的思考：

第二个问题，为什么说 TPS 趋势要在预期之内？
此问题类比测试人员设计测试用例，每条用例你要知道它对应的预期结果是什么。若执行后，预期结果与实际结果一致，那么就通过；反之，异常则需要提Bug，分析定位问题的原因，然后解决。</p>2020-04-05</li><br/><li><span>你比昨天快乐🌻</span> 👍（0） 💬（1）<p>酣畅淋漓，看完了，有种跃跃欲试的感觉，难道是幻想，哈哈</p>2020-03-24</li><br/>
</ul>