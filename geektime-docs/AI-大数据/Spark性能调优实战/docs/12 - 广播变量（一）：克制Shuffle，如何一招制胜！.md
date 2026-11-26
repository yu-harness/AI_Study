你好，我是吴磊。

在数据分析领域，数据关联（Joins）是Shuffle操作的高发区，二者如影随从。可以说，有Joins的地方，就有Shuffle。

我们说过，面对Shuffle，开发者应当“能省则省、能拖则拖”。我们已经讲过了怎么拖，拖指的就是，把应用中会引入Shuffle的操作尽可能地往后面的计算步骤去拖。那具体该怎么省呢？

在数据关联场景中，广播变量就可以轻而易举地省去Shuffle。所以今天这一讲，我们就先说一说广播变量的含义和作用，再说一说它是如何帮助开发者省去Shuffle操作的。

## 如何理解广播变量？

接下来，咱们借助一个小例子，来讲一讲广播变量的含义与作用。这个例子和Word Count有关，它可以说是分布式编程里的Hello world了，Word Count就是用来统计文件中全部单词的，你肯定已经非常熟悉了，所以，我们例子中的需求增加了一点难度，我们要对指定列表中给定的单词计数。

```
val dict = List(“spark”, “tune”)
val words = spark.sparkContext.textFile(“~/words.csv”)
val keywords = words.filter(word => dict.contains(word))
keywords.map((_, 1)).reduceByKey(_ + _).collect
```

按照这个需求，同学小A实现了如上的代码，一共有4行，我们逐一来看。第1行在Driver端给定待查单词列表dict；第2行以textFile API读取分布式文件，内容包含一列，存储的是常见的单词；第3行用列表dict中的单词过滤分布式文件内容，只保留dict中给定的单词；第4行调用reduceByKey对单词进行累加计数。

![](https://static001.geekbang.org/resource/image/ba/39/ba45d47a910ccb92861b1fd153b36839.jpg?wh=3540%2A1482 "数据结构dict随着Task一起分发到Executors")

学习过调度系统之后，我们知道，第一行代码定义的dict列表连带后面的3行代码会一同打包到Task里面去。这个时候，Task就像是一架架小飞机，携带着这些“行李”，飞往集群中不同的Executors。对于这些“行李”来说，代码的“负重”较轻，可以忽略不计，而数据的负重占了大头，成了最主要的负担。

你可能会说：“也还好吧，dict列表又不大，也没什么要紧的”。但是，如果我们假设这个例子中的并行度是10000，那么，Driver端需要通过网络分发总共10000份dict拷贝。这个时候，集群内所有的Executors需要消耗大量内存来存储这10000份的拷贝，对宝贵的网络和内存资源来说，这已经是一笔不小的浪费了。更何况，如果换做一个更大的数据结构，Task分发所引入的网络与内存开销会更可怕。

换句话说，统计计数的业务逻辑还没有开始执行，Spark就已经消耗了大量的网络和存储资源，这简直不可理喻。因此，我们需要对示例中的代码进行优化，从而跳出这样的窘境。

但是，在着手优化之前，我们不妨先来想一想，现有的问题是什么，我们要达到的目的是什么。结合刚刚的分析，我们不难发现，**Word Count的核心痛点在于，数据结构的分发和存储受制于并行，并且是以Task为粒度的，因此往往频次过高。痛点明确了，调优的目的也就清晰了，我们需要降低数据结构分发的频次**。

要达到这个目的，我们首先想到的就是降低并行度。不过，牵一发而动全身，并行度一旦调整，其他与CPU、内存有关的配置项都要跟着适配，这难免把调优变复杂了。实际上，要降低数据结构的分发频次，我们还可以考虑广播变量。

**广播变量是一种分发机制，它一次性封装目标数据结构，以Executors为粒度去做数据分发。**换句话说，在广播变量的工作机制下，数据分发的频次等同于集群中的Executors个数。通常来说，集群中的Executors数量都远远小于Task数量，相差两到三个数量级是常有的事。那么，对于第一版的Word Count实现，如果我们使用广播变量的话，会有哪些变化呢？

代码的改动很简单，主要有两个改动：第一个改动是用broadcast封装dict列表，第二个改动是在访问dict列表的地方改用broadcast.value替代。

```
val dict = List(“spark”, “tune”)
val bc = spark.sparkContext.broadcast(dict)
val words = spark.sparkContext.textFile(“~/words.csv”)
val keywords = words.filter(word => bc.value.contains(word))
keywords.map((_, 1)).reduceByKey(_ + _).collect
```

你可能会说：“这个改动看上去也没什么呀！”别着急，我们先来分析一下，改动之后的代码在运行时都有哪些变化。

**在广播变量的运行机制下，封装成广播变量的数据，由Driver端以Executors为粒度分发，每一个Executors接收到广播变量之后，将其交给BlockManager管理**。由于广播变量携带的数据已经通过专门的途径存储到BlockManager中，因此分发到Executors的Task不需要再携带同样的数据。

这个时候，你可以把广播变量想象成一架架专用货机，专门为Task这些小飞机运送“大件行李”。Driver与每一个Executors之间都开通一条这样的专用货机航线，统一运载负重较大的“数据行李”。有了专用货机来帮忙，Task小飞机只需要携带那些负重较轻的代码就好了。等这些Task小飞机在Executors着陆，它们就可以到Executors的公用仓库BlockManager里去提取它们的“大件行李”。

![](https://static001.geekbang.org/resource/image/2c/f7/2cfe084a106a01bf14a63466fa2146f7.jpg?wh=3729%2A1314 "用广播变量封装dict列表")

总之，在广播变量的机制下，dict列表数据需要分发和存储的次数锐减。我们假设集群中有20个Executors，不过任务并行度还是10000，那么，Driver需要通过网络分发的dict列表拷贝就会由原来的10000份减少到20份。同理，集群范围内所有Executors需要存储的dict拷贝，也由原来的10000份，减少至20份。这个时候，引入广播变量后的开销只是原来Task分发的1/500！

## 广播分布式数据集

那在刚刚的示例代码中，广播变量封装的是Driver端创建的普通变量：字符串列表。除此之外，**广播变量也可以封装分布式数据集**。

我们来看这样一个例子。在电子商务领域中，开发者往往用事实表来存储交易类数据，用维度表来存储像物品、用户这样的描述性数据。事实表的特点是规模庞大，数据体量随着业务的发展不断地快速增长。维度表的规模要比事实表小很多，数据体量的变化也相对稳定。

假设用户维度数据以Parquet文件格式存储在HDFS文件系统中，业务部门需要我们读取用户数据并创建广播变量以备后用，我们该怎么做呢？很简单，几行代码就可以搞定！

```
val userFile: String = “hdfs://ip:port/rootDir/userData”
val df: DataFrame = spark.read.parquet(userFile)
val bc_df: Broadcast[DataFrame] = spark.sparkContext.broadcast(df)
```

首先，我们用Parquet API读取HDFS分布式数据文件生成DataFrame，然后用broadcast封装DataFrame。从代码上来看，这种实现方式和封装普通变量没有太大差别，它们都调用了broadcast API，只是传入的参数不同。

但如果不从开发的视角来看，转而去观察运行时广播变量的创建过程的话，我们就会发现，分布式数据集与普通变量之间的差异非常显著。

从普通变量创建广播变量，由于数据源就在Driver端，因此，只需要Driver把数据分发到各个Executors，再让Executors把数据缓存到BlockManager就好了。

但是，从分布式数据集创建广播变量就要复杂多了，具体的过程如下图所示。

![](https://static001.geekbang.org/resource/image/8a/6c/8ac91a174803b97966289ff51938106c.jpg?wh=3954%2A1614 "从分布式数据集创建广播变量的过程")

与普通变量相比，分布式数据集的数据源不在Driver端，而是来自所有的Executors。Executors中的每个分布式任务负责生产全量数据集的一部分，也就是图中不同的数据分区。因此，步骤1就是**Driver从所有的Executors拉取这些数据分区，然后在本地构建全量数据。**步骤2与从普通变量创建广播变量的过程类似。 **Driver把汇总好的全量数据分发给各个Executors，Executors将接收到的全量数据缓存到存储系统的BlockManager中**。

不难发现，相比从普通变量创建广播变量，从分布式数据集创建广播变量的网络开销更大。原因主要有二：一是，前者比后者多了一步网络通信；二是，前者的数据体量通常比后者大很多。

## 如何用广播变量克制Shuffle？

你可能会问：“Driver从Executors拉取DataFrame的数据分片，揉成一份全量数据，然后再广播出去，抛开网络开销不说，来来回回得费这么大劲，图啥呢？”这是一个好问题，因为以广播变量的形式缓存分布式数据集，正是克制Shuffle杀手锏。

### Shuffle Joins

为什么这么说呢？我还是拿电子商务场景举例。有了用户的数据之后，为了分析不同用户的购物习惯，业务部门要求我们对交易表和用户表进行数据关联。这样的数据关联需求在数据分析领域还是相当普遍的。

```
val transactionsDF: DataFrame = _
val userDF: DataFrame = _
transactionsDF.join(userDF, Seq(“userID”), “inner”)
```

因为需求非常明确，同学小A立即调用Parquet数据源API，读取分布式文件，创建交易表和用户表的DataFrame，然后调用DataFrame的Join方法，以userID作为Join keys，用内关联（Inner Join）的方式完成了两表的数据关联。

在分布式环境中，交易表和用户表想要以userID为Join keys进行关联，就必须要确保一个前提：交易记录和与之对应的用户信息在同一个Executors内。也就是说，如果用户黄小乙的购物信息都存储在Executor 0，而个人属性信息缓存在Executor 2，那么，在分布式环境中，这两种信息必须要凑到同一个进程里才能实现关联计算。

在不进行任何调优的情况下，Spark默认采用Shuffle Join的方式来做到这一点。Shuffle Join的过程主要有两步。

**第一步就是对参与关联的左右表分别进行Shuffle**，Shuffle的分区规则是先对Join keys计算哈希值，再把哈希值对分区数取模。由于左右表的分区数是一致的，因此Shuffle过后，一定能够保证userID相同的交易记录和用户数据坐落在同一个Executors内。

![](https://static001.geekbang.org/resource/image/b1/28/b1b2a574eb7ef33e2315f547ecdc0328.jpg?wh=5124%2A1599 "Shuffle Join中左右表的数据分发")

Shuffle完成之后，**第二步就是在同一个Executors内，Reduce task就可以对userID一致的记录进行关联操作**。但是，由于交易表是事实表，数据体量异常庞大，对TB级别的数据进行Shuffle，想想都觉得可怕！因此，上面对两个DataFrame直接关联的代码，还有很大的调优空间。我们该怎么做呢？话句话说，对于分布式环境中的数据关联来说，要想确保交易记录和与之对应的用户信息在同一个Executors中，我们有没有其他办法呢？

### 克制Shuffle的方式

还记得之前业务部门要求我们把用户表封装为广播变量，以备后用吗？现在它终于派上用场了！

```
import org.apache.spark.sql.functions.broadcast
 
val transactionsDF: DataFrame = _
val userDF: DataFrame = _
 
val bcUserDF = broadcast(userDF)
transactionsDF.join(bcUserDF, Seq(“userID”), “inner”)

```

Driver从所有Executors收集userDF所属的所有数据分片，在本地汇总用户数据，然后给每一个Executors都发送一份全量数据的拷贝。既然每个Executors都有userDF的**全量数据**，这个时候，交易表的数据分区待在原地、保持不动，就可以轻松地关联到一致的用户数据。如此一来，我们不需要对数据体量巨大的交易表进行Shuffle，同样可以在分布式环境中，完成两张表的数据关联。

![](https://static001.geekbang.org/resource/image/b3/2a/b3c5ab392c2303bf7923488623b4022a.jpg?wh=5094%2A1695 "Broadcast Join将小表广播，避免大表Shuffle ")

利用广播变量，我们成功地避免了海量数据在集群内的存储、分发，节省了原本由Shuffle引入的磁盘和网络开销，大幅提升运行时执行性能。当然，采用广播变量优化也是有成本的，毕竟广播变量的创建和分发，也是会带来网络开销的。但是，相比大表的全网分发，小表的网络开销几乎可以忽略不计。这种小投入、大产出，用极小的成本去博取高额的性能收益，真可以说是“四两拨千斤”！

## 小结

在数据关联场景中，广播变量是克制Shuffle的杀手锏。掌握了它，我们就能以极小的成本，获得高额的性能收益。关键是我们要掌握两种创建广播变量的方式。

第一种，从普通变量创建广播变量。在广播变量的运行机制下，普通变量存储的数据封装成广播变量，由Driver端以Executors为粒度进行分发，每一个Executors接收到广播变量之后，将其交由BlockManager管理。

第二种，从分布式数据集创建广播变量，这就要比第一种方式复杂一些了。第一步，Driver需要从所有的Executors拉取数据分片，然后在本地构建全量数据；第二步，Driver把汇总好的全量数据分发给各个Executors，Executors再将接收到的全量数据缓存到存储系统的BlockManager中。

结合这两种方式，我们在做数据关联的时候，把Shuffle Joins转换为Broadcast Joins，就可以用小表广播来代替大表的全网分发，真正做到克制Shuffle。

## 每日一练

1. Spark广播机制现有的实现方式是存在隐患的，在数据量较大的情况下，Driver可能会成为瓶颈，你能想到更好的方式来重新实现Spark的广播机制吗？（提示：[SPARK-17556](https://issues.apache.org/jira/browse/SPARK-17556)）
2. 在什么情况下，不适合把Shuffle Joins转换为Broadcast Joins？

期待在留言区看到你的思考和答案，我们下一讲见！
<div><strong>精选留言（15）</strong></div><ul>
<li><span>Sansi</span> 👍（22） 💬（4）<p>1. 改成由driver获取到数据分布，然后通知各个executor之间进行拉取，这样可以利用多个executor网络，避免只有driver组装以后再一个一个发送效率过低

2.当两个需要join的数据集都很大时，使用broadcast join需要将一个很大的数据集进行网络分发多次，已经远超出了shuffle join需要传输的数据</p>2021-04-09</li><br/><li><span>Geek_d794f8</span> 👍（21） 💬（3）<p>磊哥，为什么我测试了广播rdd不行：
我写了个demo，广播rdd是报错的，代码如下：
    val userFile: String =&quot;spark-basic&#47;File&#47;csv_data.csv&quot;
    val df: DataFrame = spark.read.csv(userFile)
    val rdd = spark.sparkContext.textFile(&quot;userFile&quot;)
    val bc_df: Broadcast[RDD[String]] = spark.sparkContext.broadcast(rdd)
    bc_df.value.collect().foreach(println)

报错如下：Exception in thread &quot;main&quot; java.lang.IllegalArgumentException: requirement failed: Can not directly broadcast RDDs; instead, call collect() and broadcast the result.

然后看了一下源码：SparkContext中的broadcast方法：

def broadcast[T: ClassTag](value: T): Broadcast[T] = {
    assertNotStopped()
    require(!classOf[RDD[_]].isAssignableFrom(classTag[T].runtimeClass),
      &quot;Can not directly broadcast RDDs; instead, call collect() and broadcast the result.&quot;)
    val bc = env.broadcastManager.newBroadcast[T](value, isLocal)
    val callSite = getCallSite
    logInfo(&quot;Created broadcast &quot; + bc.id + &quot; from &quot; + callSite.shortForm)
    cleaner.foreach(_.registerBroadcastForCleanup(bc))
    bc
  }

第4行的代码显示的Can not directly broadcast RDDs
是不是我哪里不太对？</p>2021-05-12</li><br/><li><span>Jack</span> 👍（6） 💬（8）<p>老师，对于第1题，看了下spark的源码，目前Broadcast只有一个实现类TorrentBroadcast，看代码的注释，这个类通过使用类似Bit-torrent协议的方法解决了Driver成为瓶颈的问题。目前Spark还会存在广播变量的数据太大造成Driver成为瓶颈的问题吗？

&#47;**
 * A BitTorrent-like implementation of [[org.apache.spark.broadcast.Broadcast]].
 *
 * The mechanism is as follows:
 *
 * The driver divides the serialized object into small chunks and
 * stores those chunks in the BlockManager of the driver.
 *
 * On each executor, the executor first attempts to fetch the object from its BlockManager. If
 * it does not exist, it then uses remote fetches to fetch the small chunks from the driver and&#47;or
 * other executors if available. Once it gets the chunks, it puts the chunks in its own
 * BlockManager, ready for other executors to fetch from.
 *
 * This prevents the driver from being the bottleneck in sending out multiple copies of the
 * broadcast data (one per executor).
 *
 * When initialized, TorrentBroadcast objects read SparkEnv.get.conf.
 *
 * @param obj object to broadcast
 * @param id A unique identifier for the broadcast variable.
 *&#47;
private[spark] class TorrentBroadcast[T: ClassTag](obj: T, id: Long)
  extends Broadcast[T](id) with Logging with Serializable {
</p>2021-04-09</li><br/><li><span>冯杰</span> 👍（5） 💬（1）<p>老师你好，关于broacast join，遇到了一个特别的问题请教一下。
1、Fact(订单) 和 DIM(门店) 关联。  其中门店表量级为 3w(条数) * 10个(字段)，采用Parquet存储在Hive上，大小1M左右。
2、运行参数，并行度 = 200，Executor = 50，CPU核数 = 2，内存&#47;Executor = 6G，Drvier内存=2G。 PS：没有特别配置Broadcast 相关参数
3、执行时，有两个疑问点，不得其解
    a）Spark UI 显示，并没有执行BHJ，反而执行了 hash sort merge join。   照理，如此小的数据，应该走前者
    b）Spark UI 显示，走hash sort merge join后，shuffle阶段的内存计算大小为4MB，sort阶段的内存计算大小为6G。    为何sort完后，为膨胀的如此厉害。

</p>2021-06-10</li><br/><li><span>Geek_d794f8</span> 👍（5） 💬（1）<p>老师有两个问题请教一下：
1.文中提到两个表join，两个表数据量相差很大呀，为什么他们的的分区数是一致的，而且分区数不是根据hadoop的切片规则去划分的吗？
2.广播join不是默认开启的吗，好像小表默认10M；还需像文中代码val bcUserDF = broadcast(userDF)这样声明吗？
希望得到您的指导，多谢！</p>2021-04-10</li><br/><li><span>斯盖丸</span> 👍（4） 💬（5）<p>老师我生产中为啥从没有遇到过10000并行度那么大的stage，可能我公司比较小吧，集群最多才100多个核，多数时才几百个任务，最多时也才2000多个任务。这健康吗？</p>2021-05-05</li><br/><li><span>斯盖丸</span> 👍（2） 💬（1）<p>原来小表和大表join是节省了大表的shuffle，不然大表只能根据join的列在所有机器上重新分布一遍，现在懂了</p>2021-04-09</li><br/><li><span>狗哭</span> 👍（1） 💬（3）<p>select * from
(select id from table1) a -- 结果很大
left join
(select id from table2) b -- 结果很小
on t1.id = t2.id;
老师请教下，这种情况b表会广播吗？如果不会怎么处理能让其广播出去呢</p>2021-10-21</li><br/><li><span>陌生的心酸</span> 👍（0） 💬（2）<p>1&gt;.当数据量比较大，对数据进行广播后，同时还要接受各个Executor的中间结果上报，状态管理，导致网络繁忙，继而会发生分发任务到Executor产生失败

2&gt; 两个大表【超过广播变量的阈值参数设置】进行join，数据需要分发多次，效率不佳</p>2022-02-21</li><br/><li><span>子兮</span> 👍（0） 💬（1）<p>老师您好，在整个应用资源较为紧张，数据量较大的情况下：spark core计算过程中，生成一个较大的RDD , 它被引用一次，但我还是对它persist(disk)，我在用完并且动作算子后，立刻对它进行了释放unpersist，这样操作是否能加快spark 对这个rdd 的清理，加快内存的释放，缓解内存压力？如果是persist(memory and disk)，用完并且在动作算子后立即释放unpersist，是否能缓解内存压力？如果不persist，用完并且在动作算子后立即释放unpersist，是否能缓解内存压力？ 文字有些长，希望没给老师造成困扰，谢谢老师</p>2021-11-10</li><br/><li><span>子兮</span> 👍（0） 💬（1）<p>1 老师，您好，spark core计算过程中，需要频繁的使用broadCast 操作， 这样累计几次后driver 端内存会很有压力，怎样设置参数或者手动清除之前用来broadCast 的数据？谢谢老师
2 老师这个课程的微信交流群怎么添加呢？期待加入学习

</p>2021-11-10</li><br/><li><span>子兮</span> 👍（0） 💬（1）<p>老师, 课程里您讲了内连接左右左右两表的连接过程，您能否再讲一下左外连接leftoutjoin 的呢？对shuffle过程不太清晰，谢谢老师</p>2021-11-02</li><br/><li><span>zhongmin</span> 👍（0） 💬（1）<p>吴老师，问个问题，在广播分布式变量的时候，如果变量的内容发生改变，是怎么去做变量的同步和更新呢？</p>2021-09-06</li><br/><li><span>wow_xiaodi</span> 👍（0） 💬（1）<p>老师对于这节有一些问题：
(1)executor对于待回传driver端的广播数据集是先存在内存还是落地硬盘呢？
(2)由executor来处理分片再回传，可能分片需要进行一定的计算再由driver汇总广播，那么如果是无需计算的原始分片呢，driver可否亲自操刀读取所有原始分片直接汇总再分发呢，感觉这样可以节省网络开销？</p>2021-08-01</li><br/><li><span>xuchuan</span> 👍（0） 💬（1）<p>2.多个大表join应该就没法用广播解决，这个延伸一个问题，以电商为例，即席查询应该还要有数仓吧，这不是spark的主要覆盖范畴。</p>2021-05-18</li><br/>
</ul>