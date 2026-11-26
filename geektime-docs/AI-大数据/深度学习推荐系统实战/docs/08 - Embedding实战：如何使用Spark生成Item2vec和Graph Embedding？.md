你好，我是王喆。

前面两节课，我们一起学习了从Item2vec到Graph Embedding的几种经典Embedding方法。在打好了理论基础之后，这节课就让我们从理论走向实践，看看到底**如何基于Spark训练得到物品的Embedding向量**。

通过特征工程部分的实践，我想你已经对Spark这个分布式计算平台有了初步的认识。其实除了一些基本的特征处理方法，在Spark的机器学习包Spark MLlib中，还包含了大量成熟的机器学习模型，这其中就包括我们讲过的Word2vec模型。基于此，这节课我们会在Spark平台上，完成**Item2vec和基于Deep Walk的Graph Embedding**的训练。

对其他机器学习平台有所了解的同学可能会问，TensorFlow、PyTorch都有很强大的深度学习工具包，我们能不能利用这些平台进行Embedding训练呢？当然是可以的，我们也会在之后的课程中介绍TensorFlow并用它实现很多深度学习推荐模型。

但是Spark作为一个原生的分布式计算平台，在处理大数据方面还是比TensorFlow等深度学习平台更具有优势，而且业界的很多公司仍然在使用Spark训练一些结构比较简单的机器学习模型，再加上我们已经用Spark进行了特征工程的处理，所以，这节课我们继续使用Spark来完成Embedding的实践。

首先，我们来看看怎么完成Item2vec的训练。

## Item2vec：序列数据的处理

我们知道，Item2vec是基于自然语言处理模型Word2vec提出的，所以Item2vec要处理的是类似文本句子、观影序列之类的序列数据。那在真正开始Item2vec的训练之前，我们还要先为它准备好训练用的序列数据。在MovieLens数据集中，有一张叫rating（评分）的数据表，里面包含了用户对看过电影的评分和评分的时间。既然时间和评分历史都有了，我们要用的观影序列自然就可以通过处理rating表得到啦。

![](https://static001.geekbang.org/resource/image/36/c0/36a2cafdf3858b18a72e4ee8d8202fc0.jpeg?wh=808%2A1080 "图1 movieLens数据集中的rating评分表")

不过，在使用观影序列编码之前，我们还要再明确两个问题。一是MovieLens这个rating表本质上只是一个评分的表，不是真正的“观影序列”。但对用户来说，当然只有看过这部电影才能够评价它，所以，我们几乎可以把评分序列当作是观影序列。二是我们是应该把所有电影都放到序列中，还是只放那些打分比较高的呢？

这里，我是建议对评分做一个过滤，只放用户打分比较高的电影。为什么这么做呢？我们要思考一下Item2vec这个模型本质上是要学习什么。我们是希望Item2vec能够学习到物品之间的近似性。既然这样，我们当然是希望评分好的电影靠近一些，评分差的电影和评分好的电影不要在序列中结对出现。

好，那到这里我们明确了样本处理的思路，就是对一个用户来说，我们先过滤掉他评分低的电影，再把他评论过的电影按照时间戳排序。这样，我们就得到了一个用户的观影序列，所有用户的观影序列就组成了Item2vec的训练样本集。

那这个过程究竟该怎么在Spark上实现呢？其实很简单，我们只需要明白这5个关键步骤就可以实现了：

1. 读取ratings原始数据到Spark平台；
2. 用where语句过滤评分低的评分记录；
3. 用groupBy userId操作聚合每个用户的评分记录，DataFrame中每条记录是一个用户的评分序列；
4. 定义一个自定义操作sortUdf，用它实现每个用户的评分记录按照时间戳进行排序；
5. 把每个用户的评分记录处理成一个字符串的形式，供后续训练过程使用。

具体的实现过程，我还是建议你来参考我下面给出的代码，重要的地方我也都加上了注释，方便你来理解。

```
def processItemSequence(sparkSession: SparkSession): RDD[Seq[String]] ={
  //设定rating数据的路径并用spark载入数据
  val ratingsResourcesPath = this.getClass.getResource("/webroot/sampledata/ratings.csv")
  val ratingSamples = sparkSession.read.format("csv").option("header", "true").load(ratingsResourcesPath.getPath)


  //实现一个用户定义的操作函数(UDF)，用于之后的排序
  val sortUdf: UserDefinedFunction = udf((rows: Seq[Row]) => {
    rows.map { case Row(movieId: String, timestamp: String) => (movieId, timestamp) }
      .sortBy { case (movieId, timestamp) => timestamp }
      .map { case (movieId, timestamp) => movieId }
  })


  //把原始的rating数据处理成序列数据
  val userSeq = ratingSamples
    .where(col("rating") >= 3.5)  //过滤掉评分在3.5一下的评分记录
    .groupBy("userId")            //按照用户id分组
    .agg(sortUdf(collect_list(struct("movieId", "timestamp"))) as "movieIds")     //每个用户生成一个序列并用刚才定义好的udf函数按照timestamp排序
    .withColumn("movieIdStr", array_join(col("movieIds"), " "))
                //把所有id连接成一个String，方便后续word2vec模型处理


  //把序列数据筛选出来，丢掉其他过程数据
  userSeq.select("movieIdStr").rdd.map(r => r.getAs[String]("movieIdStr").split(" ").toSeq)
```

通过这段代码生成用户的评分序列样本中，每条样本的形式非常简单，它就是电影ID组成的序列，比如下面就是ID为11888用户的观影序列：

```
296 380 344 588 593 231 595 318 480 110 253 288 47 364 377 589 410 597 539 39 160 266 350 553 337 186 736 44 158 551 293 780 353 368 858

```

## Item2vec：模型训练

训练数据准备好了，就该进入我们这堂课的重头戏，模型训练了。手写Item2vec的整个训练过程肯定是一件让人比较“崩溃”的事情，好在Spark MLlib已经为我们准备好了方便调用的Word2vec模型接口。我先把训练的代码贴在下面，然后再带你一步步分析每一行代码是在做什么。

```
def trainItem2vec(samples : RDD[Seq[String]]): Unit ={
    //设置模型参数
    val word2vec = new Word2Vec()
    .setVectorSize(10)
    .setWindowSize(5)
    .setNumIterations(10)


  //训练模型
  val model = word2vec.fit(samples)


  //训练结束，用模型查找与item"592"最相似的20个item
  val synonyms = model.findSynonyms("592", 20)
  for((synonym, cosineSimilarity) <- synonyms) {
    println(s"$synonym $cosineSimilarity")
  }
 
  //保存模型
  val embFolderPath = this.getClass.getResource("/webroot/sampledata/")
  val file = new File(embFolderPath.getPath + "embedding.txt")
  val bw = new BufferedWriter(new FileWriter(file))
  var id = 0
  //用model.getVectors获取所有Embedding向量
  for (movieId <- model.getVectors.keys){
    id+=1
    bw.write( movieId + ":" + model.getVectors(movieId).mkString(" ") + "\n")
  }
  bw.close()
```

从上面的代码中我们可以看出，Spark的Word2vec模型训练过程非常简单，只需要四五行代码就可以完成。接下来，我就按照从上到下的顺序，依次给你解析其中3个关键的步骤。

首先是创建Word2vec模型并设定模型参数。我们要清楚Word2vec模型的关键参数有3个，分别是setVectorSize、setWindowSize和setNumIterations。其中，setVectorSize用于设定生成的Embedding向量的维度，setWindowSize用于设定在序列数据上采样的滑动窗口大小，setNumIterations用于设定训练时的迭代次数。这些超参数的具体选择就要根据实际的训练效果来做调整了。

其次，模型的训练过程非常简单，就是调用模型的fit接口。训练完成后，模型会返回一个包含了所有模型参数的对象。

最后一步就是提取和保存Embedding向量，我们可以从最后的几行代码中看到，调用getVectors接口就可以提取出某个电影ID对应的Embedding向量，之后就可以把它们保存到文件或者其他数据库中，供其他模块使用了。

在模型训练完成后，我们再来验证一下训练的结果是不是合理。我在代码中求取了ID为592电影的相似电影。这部电影叫Batman蝙蝠侠，我把通过Item2vec得到相似电影放到了下面，你可以从直观上判断一下这个结果是不是合理。

![](https://static001.geekbang.org/resource/image/3a/10/3abdb9b411615487031bf03c07bf5010.jpeg?wh=1920%2A1080 "图2 通过Item2vec方法找出的电影Batman的相似电影")

当然，因为Sparrow Recsys在演示过程中仅使用了1000部电影和部分用户评论集，所以，我们得出的结果不一定非常准确，如果你有兴趣优化这个结果，可以去movieLens下载全部样本进行重新训练。

## Graph Embedding：数据准备

到这里，我相信你已经熟悉了Item2vec方法的实现。接下来，我们再来说说基于随机游走的Graph Embedding方法，看看如何利用Spark来实现它。这里，我们选择Deep Walk方法进行实现。

![](https://static001.geekbang.org/resource/image/1f/ed/1f28172c62e1b5991644cf62453fd0ed.jpeg?wh=1920%2A691 "图3 Deep Walk的算法流程")

在Deep Walk方法中，我们需要准备的最关键数据是物品之间的转移概率矩阵。图3是Deep Walk的算法流程图，转移概率矩阵表达了图3(b)中的物品关系图，它定义了随机游走过程中，从物品A到物品B的跳转概率。所以，我们先来看一下如何利用Spark生成这个转移概率矩阵。

```
//samples 输入的观影序列样本集
def graphEmb(samples : RDD[Seq[String]], sparkSession: SparkSession): Unit ={
  //通过flatMap操作把观影序列打碎成一个个影片对
  val pairSamples = samples.flatMap[String]( sample => {
    var pairSeq = Seq[String]()
    var previousItem:String = null
    sample.foreach((element:String) => {
      if(previousItem != null){
        pairSeq = pairSeq :+ (previousItem + ":" + element)
      }
      previousItem = element
    })
    pairSeq
  })
  //统计影片对的数量
  val pairCount = pairSamples.countByValue()
  //转移概率矩阵的双层Map数据结构
  val transferMatrix = scala.collection.mutable.Map[String, scala.collection.mutable.Map[String, Long]]()
  val itemCount = scala.collection.mutable.Map[String, Long]()


  //求取转移概率矩阵
  pairCount.foreach( pair => {
    val pairItems = pair._1.split(":")
    val count = pair._2
    lognumber = lognumber + 1
    println(lognumber, pair._1)


    if (pairItems.length == 2){
      val item1 = pairItems.apply(0)
      val item2 = pairItems.apply(1)
      if(!transferMatrix.contains(pairItems.apply(0))){
        transferMatrix(item1) = scala.collection.mutable.Map[String, Long]()
      }


      transferMatrix(item1)(item2) = count
      itemCount(item1) = itemCount.getOrElse[Long](item1, 0) + count
    }
  

```

生成转移概率矩阵的函数输入是在训练Item2vec时处理好的观影序列数据。输出的是转移概率矩阵，由于转移概率矩阵比较稀疏，因此我没有采用比较浪费内存的二维数组的方法，而是采用了一个双层Map的结构去实现它。比如说，我们要得到物品A到物品B的转移概率，那么transferMatrix(itemA)(itemB)就是这一转移概率。

在求取转移概率矩阵的过程中，我先利用Spark的flatMap操作把观影序列“打碎”成一个个影片对，再利用countByValue操作统计这些影片对的数量，最后根据这些影片对的数量求取每两个影片之间的转移概率。

在获得了物品之间的转移概率矩阵之后，我们就可以进入图3(c)的步骤，进行随机游走采样了。

## Graph Embedding：随机游走采样过程

随机游走采样的过程是利用转移概率矩阵生成新的序列样本的过程。这怎么理解呢？首先，我们要根据物品出现次数的分布随机选择一个起始物品，之后就进入随机游走的过程。在每次游走时，我们根据转移概率矩阵查找到两个物品之间的转移概率，然后根据这个概率进行跳转。比如当前的物品是A，从转移概率矩阵中查找到A可能跳转到物品B或物品C，转移概率分别是0.4和0.6，那么我们就按照这个概率来随机游走到B或C，依次进行下去，直到样本的长度达到了我们的要求。

根据上面随机游走的过程，我用Scala进行了实现，你可以参考下面的代码，在关键的位置我也给出了注释：

```
//随机游走采样函数
//transferMatrix 转移概率矩阵
//itemCount 物品出现次数的分布
def randomWalk(transferMatrix : scala.collection.mutable.Map[String, scala.collection.mutable.Map[String, Long]], itemCount : scala.collection.mutable.Map[String, Long]): Seq[Seq[String]] ={
  //样本的数量
  val sampleCount = 20000
  //每个样本的长度
  val sampleLength = 10
  val samples = scala.collection.mutable.ListBuffer[Seq[String]]()
  
  //物品出现的总次数
  var itemTotalCount:Long = 0
  for ((k,v) <- itemCount) itemTotalCount += v


  //随机游走sampleCount次，生成sampleCount个序列样本
  for( w <- 1 to sampleCount) {
    samples.append(oneRandomWalk(transferMatrix, itemCount, itemTotalCount, sampleLength))
  }


  Seq(samples.toList : _*)
}


//通过随机游走产生一个样本的过程
//transferMatrix 转移概率矩阵
//itemCount 物品出现次数的分布
//itemTotalCount 物品出现总次数
//sampleLength 每个样本的长度
def oneRandomWalk(transferMatrix : scala.collection.mutable.Map[String, scala.collection.mutable.Map[String, Long]], itemCount : scala.collection.mutable.Map[String, Long], itemTotalCount:Long, sampleLength:Int): Seq[String] ={
  val sample = scala.collection.mutable.ListBuffer[String]()


  //决定起始点
  val randomDouble = Random.nextDouble()
  var firstElement = ""
  var culCount:Long = 0
  //根据物品出现的概率，随机决定起始点
  breakable { for ((item, count) <- itemCount) {
    culCount += count
    if (culCount >= randomDouble * itemTotalCount){
      firstElement = item
      break
    }
  }}


  sample.append(firstElement)
  var curElement = firstElement
  //通过随机游走产生长度为sampleLength的样本
  breakable { for( w <- 1 until sampleLength) {
    if (!itemCount.contains(curElement) || !transferMatrix.contains(curElement)){
      break
    }
    //从curElement到下一个跳的转移概率向量
    val probDistribution = transferMatrix(curElement)
    val curCount = itemCount(curElement)
    val randomDouble = Random.nextDouble()
    var culCount:Long = 0
    //根据转移概率向量随机决定下一跳的物品
    breakable { for ((item, count) <- probDistribution) {
      culCount += count
      if (culCount >= randomDouble * curCount){
        curElement = item
        break
      }
    }}
    sample.append(curElement)
  }}
  Seq(sample.toList : _

```

通过随机游走产生了我们训练所需的sampleCount个样本之后，下面的过程就和Item2vec的过程完全一致了，就是把这些训练样本输入到Word2vec模型中，完成最终Graph Embedding的生成。你也可以通过同样的方法去验证一下通过Graph Embedding方法生成的Embedding的效果。

## 小结

这节课，我们运用Spark实现了经典的Embedding方法Item2vec和Deep Walk。它们的理论知识你应该已经在前两节课的学习中掌握了，这里我就总结一下实践中应该注意的几个要点。

关于Item2vec的Spark实现，你应该注意的是训练Word2vec模型的几个参数VectorSize、WindowSize、NumIterations等，知道它们各自的作用。它们分别是用来设置Embedding向量的维度，在序列数据上采样的滑动窗口大小，以及训练时的迭代次数。

而在Deep Walk的实现中，我们应该着重理解的是，生成物品间的转移概率矩阵的方法，以及通过随机游走生成训练样本过程。

最后，我还是把这节课的重点知识总结在了一张表格中，希望能帮助你进一步巩固。

![](https://static001.geekbang.org/resource/image/02/a7/02860ed1170d9376a65737df1294faa7.jpeg?wh=1920%2A847)

这里，我还想再多说几句。这节课，我们终于看到了深度学习模型的产出，我们用Embedding方法计算出了相似电影！对于我们学习这门课来说，它完全可以看作是一个里程碑式的进步。接下来，我希望你能总结实战中的经验，跟我继续同行，一起迎接未来更多的挑战！

## 课后思考

上节课，我们在讲Graph Embedding的时候，还介绍了Node2vec方法。你能尝试在Deep Walk代码的基础上实现Node2vec吗？这其中，我们应该着重改变哪部分的代码呢？

欢迎把你的思考和答案写在留言区，如果你掌握了Embedding的实战方法，也不妨把它分享给你的朋友吧，我们下节课见！
<div><strong>精选留言（15）</strong></div><ul>
<li><span>你笑起来真好看</span> 👍（30） 💬（5）<p>transitionMatrixAndItemDis 在生成中这样定义的话，会不会造成dirver端oom？</p>2020-10-20</li><br/><li><span>fsc2016</span> 👍（27） 💬（3）<p>老师，筛选出来的高分电影有900多部，随机游走出来的序列embdding后，只有500多部，这应该和序列数量，序列长度有关，比如序列数量不够，导致没有覆盖到全部高分电影。实际工作中，像序列数量，序列长度是不是要经过筛选，来保证所有item都会被embdding？</p>2020-10-31</li><br/><li><span>Huntley</span> 👍（12） 💬（1）<p>想请教下老师，user embedding 也可以用相同的方法获得吗？如何构建用户关系图呢？是不是看过同一部电影的两个用户之间由一条无向边进行连接？和item embedding相比，有什么区别或注意事项吗？</p>2020-10-19</li><br/><li><span>浣熊当家</span> 👍（10） 💬（3）<p>老师请教下，我对item2vec和Graph Embedding的联系理解是否正确：
1. 联系：item2vec和Graph Embedding 都是为了下一步的相关性矩阵，而一段物品序列
2. 不同： item2vec使用同一用户历史时间序列下的滑动窗口， 而Graph embedding在同一用户的时间序列之上，还应用了不同用户，同一物品之间的图联系，所以说graph embedding可以生成更全面的物品与物品的连接。

所以是否可理解为graph embedding比item2vec的复杂，更完善？业界更流行的是不是想deep walk这种graph embedding的算法？</p>2020-10-20</li><br/><li><span>白夜</span> 👍（9） 💬（2）<p>老师，randomWalk这部在60核的机器上跑的很慢，，慢到无语，可以优化下吗，transitionMatrixAndItemDis._1与_2的size都是300000</p>2020-10-29</li><br/><li><span>tuomasiii</span> 👍（6） 💬（1）<p>想问一下在item2vec和graph embedding里面ttl都设置成了24小时，也就是说24小时候后这些embedding就会从redis里面evict掉吗？

还有就是如果有new user和new item我们都是需要train from scratch吗？还是说可以增量训练？</p>2021-01-05</li><br/><li><span>聪聪呀</span> 👍（6） 💬（2）<p>老师，我最近在研究使用graph embedding ，根据网上的git 代码跑了item2vec，EGES代码，我的推荐场景是视频推荐，同样的训练数据，我发现item2vec 推荐效果较好，但我发现EGES推荐效果不好（只用了ID，没有加其他特征）推荐结果相似度很低。所以想请教您，您觉得可能是什么原因引起的呢，您有没有EGES的demo </p>2020-10-21</li><br/><li><span>W</span> 👍（5） 💬（2）<p>老师你好，不知道我是不是哪里理解错了T_T，新手入门。我的问题是：评分低于3.5的电影被过滤了，相当于电影库里没有低于3.5分的电影，那么也就不会有对应低于3.5分的电影的embedding向量，为什么BatMan的推荐结果里还有低于3.5分的推荐结果呢？</p>2021-06-29</li><br/><li><span>Geek_ee4f14</span> 👍（5） 💬（1）<p>再请问下老师，游走的时候起始点没有做去重，会不会导致某些爆款成为起始点的概率更高，也不容易游走到冷门物品呀？</p>2021-01-25</li><br/><li><span>梁栋💝</span> 👍（5） 💬（1）<p>综上，随机游走因为需要完整转移概率矩阵的原因，受限于转移概率矩阵规模能否容纳到内存中。</p>2021-01-06</li><br/><li><span>王发庆</span> 👍（5） 💬（1）<p>老师，您好，请教您一个问题，在生成Embedding的时候我们都是全量生成的，在生产环境下我们能增量的去生成新节点的Embedding么？</p>2020-10-22</li><br/><li><span>花花花木兰</span> 👍（4） 💬（1）<p>老师，对于非序列数据用spark的word2vec模型是不是不合适？非序列数据用什么方法训练比较好？例如生鲜配送的场景，用户一次会购买很多菜，这些菜在一个订单中是没有先后时序的。</p>2020-12-21</li><br/><li><span>WiFeng</span> 👍（4） 💬（3）<p>你们执行都没有问题吗？

&#47;Users&#47;leeco&#47;github&#47;wzhe06&#47;SparrowRecSys&#47;src&#47;main&#47;java&#47;com&#47;wzhe&#47;sparrowrecsys&#47;offline&#47;spark&#47;embedding&#47;Embedding.scala:34:43
No TypeTag available for scala.collection.Seq[String]
    val sortUdf: UserDefinedFunction = udf((rows: Seq[Row]) =&gt; {</p>2020-10-26</li><br/><li><span>tuomasiii</span> 👍（3） 💬（1）<p>想请问下老师如果新的user&#47;item加入，embedding matrix形状变大。如果每天都end2end train from scratch，是不是太expensive了？
如果是手动扩容embedding再initialize with昨日的checkpoint继续训练新的user-item interactions，然后时间久一点再train from scratch，行得通吗？
</p>2021-02-23</li><br/><li><span>Capricornus</span> 👍（3） 💬（2）<p>userSeq.select(&quot;movieIdStr&quot;).rdd.map(r =&gt; r.getAs[String](&quot;movieIdStr&quot;).split(&quot; &quot;).toSeq)
老师这里为什么需要转陈Seq，而不使用Array？
    val sortUdf: UserDefinedFunction = udf((rows: Seq[Row]) =&gt; {
      rows.map { case Row(movieId: String, timestamp: String) =&gt; (movieId, timestamp) }
        .sortBy { case (movieId, timestamp) =&gt; timestamp }
        .map { case (movieId, timestamp) =&gt; movieId }
    })
老师这里case的作用是什么？不太能理解。</p>2021-01-24</li><br/>
</ul>