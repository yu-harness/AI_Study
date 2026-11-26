今天我来带你进行K-Means的学习。K-Means是一种非监督学习，解决的是聚类问题。K代表的是K类，Means代表的是中心，你可以理解这个算法的本质是确定K类的中心点，当你找到了这些中心点，也就完成了聚类。

那么请你和我思考以下三个问题：

- 如何确定K类的中心点？
- 如何将其他点划分到K类中？
- 如何区分K-Means与KNN？

如果理解了上面这3个问题，那么对K-Means的原理掌握得也就差不多了。

先请你和我思考一个场景，假设我有20支亚洲足球队，想要将它们按照成绩划分成3个等级，可以怎样划分？

## K-Means的工作原理

对亚洲足球队的水平，你可能也有自己的判断。比如一流的亚洲球队有谁？你可能会说伊朗或韩国。二流的亚洲球队呢？你可能说是中国。三流的亚洲球队呢？你可能会说越南。

其实这些都是靠我们的经验来划分的，那么伊朗、中国、越南可以说是三个等级的典型代表，也就是我们每个类的中心点。

所以回过头来，如何确定K类的中心点？一开始我们是可以随机指派的，当你确认了中心点后，就可以按照距离将其他足球队划分到不同的类别中。

这也就是K-Means的中心思想，就是这么简单直接。你可能会问：如果一开始，选择一流球队是中国，二流球队是伊朗，三流球队是韩国，中心点选择错了怎么办？其实不用担心，K-Means有自我纠正机制，在不断的迭代过程中，会纠正中心点。中心点在整个迭代过程中，并不是唯一的，只是你需要一个初始值，一般算法会随机设置初始的中心点。

好了，那我来把K-Means的工作原理给你总结下：

1. 选取K个点作为初始的类中心点，这些点一般都是从数据集中随机抽取的；
2. 将每个点分配到最近的类中心点，这样就形成了K个类，然后重新计算每个类的中心点；
3. 重复第二步，直到类不发生变化，或者你也可以设置最大迭代次数，这样即使类中心点发生变化，但是只要达到最大迭代次数就会结束。

## 如何给亚洲球队做聚类

对于机器来说需要数据才能判断类中心点，所以我整理了2015-2019年亚洲球队的排名，如下表所示。

我来说明一下数据概况。

其中2019年国际足联的世界排名，2015年亚洲杯排名均为实际排名。2018年世界杯中，很多球队没有进入到决赛圈，所以只有进入到决赛圈的球队才有实际的排名。如果是亚洲区预选赛12强的球队，排名会设置为40。如果没有进入亚洲区预选赛12强，球队排名会设置为50。

![](https://static001.geekbang.org/resource/image/d8/4a/d8ac2a98aa728d64f919bac088ed574a.png?wh=784%2A794)  
针对上面的排名，我们首先需要做的是数据规范化。你可以把这些值划分到\[0,1]或者按照均值为0，方差为1的正态分布进行规范化。具体数据规范化的步骤可以看下13篇，也就是[数据变换](https://time.geekbang.org/column/article/77059)那一篇。

我先把数值都规范化到\[0,1]的空间中，得到了以下的数值表：

![](https://static001.geekbang.org/resource/image/a7/17/a722eeab035fb13751a6dc5c0530ed17.png?wh=726%2A789)  
如果我们随机选取中国、日本、韩国为三个类的中心点，我们就需要看下这些球队到中心点的距离。

距离有多种计算的方式，有关距离的计算我在KNN算法中也讲到过：

- 欧氏距离
- 曼哈顿距离
- 切比雪夫距离
- 余弦距离

欧氏距离是最常用的距离计算方式，这里我选择欧氏距离作为距离的标准，计算每个队伍分别到中国、日本、韩国的距离，然后根据距离远近来划分。我们看到大部分的队，会和中国队聚类到一起。这里我整理了距离的计算过程，比如中国和中国的欧氏距离为0，中国和日本的欧式距离为0.732003。如果按照中国、日本、韩国为3个分类的中心点，欧氏距离的计算结果如下表所示：

![](https://static001.geekbang.org/resource/image/b6/e9/b603ccdb93420c8455aea7278efaece9.png?wh=616%2A828)  
然后我们再重新计算这三个类的中心点，如何计算呢？最简单的方式就是取平均值，然后根据新的中心点按照距离远近重新分配球队的分类，再根据球队的分类更新中心点的位置。计算过程这里不展开，最后一直迭代（重复上述的计算过程：计算中心点和划分分类）到分类不再发生变化，可以得到以下的分类结果：

![](https://static001.geekbang.org/resource/image/12/98/12c6039884ee99742fbbebf198425998.png?wh=865%2A919)  
所以我们能看出来第一梯队有日本、韩国、伊朗、沙特、澳洲；第二梯队有中国、伊拉克、阿联酋、乌兹别克斯坦；第三梯队有卡塔尔、泰国、越南、阿曼、巴林、朝鲜、印尼、叙利亚、约旦、科威特和巴勒斯坦。

## 如何使用sklearn中的K-Means算法

sklearn是Python的机器学习工具库，如果从功能上来划分，sklearn可以实现分类、聚类、回归、降维、模型选择和预处理等功能。这里我们使用的是sklearn的聚类函数库，因此需要引用工具包，具体代码如下：

```
from sklearn.cluster import KMeans
```

当然K-Means只是sklearn.cluster中的一个聚类库，实际上包括K-Means在内，sklearn.cluster一共提供了9种聚类方法，比如Mean-shift，DBSCAN，Spectral clustering（谱聚类）等。这些聚类方法的原理和K-Means不同，这里不做介绍。

我们看下K-Means如何创建：

```
KMeans(n_clusters=8, init='k-means++', n_init=10, max_iter=300, tol=0.0001, precompute_distances='auto', verbose=0, random_state=None, copy_x=True, n_jobs=1, algorithm='auto')
```

我们能看到在K-Means类创建的过程中，有一些主要的参数：

- **n\_clusters**: 即K值，一般需要多试一些K值来保证更好的聚类效果。你可以随机设置一些K值，然后选择聚类效果最好的作为最终的K值；
- **max\_iter**： 最大迭代次数，如果聚类很难收敛的话，设置最大迭代次数可以让我们及时得到反馈结果，否则程序运行时间会非常长；
- **n\_init**：初始化中心点的运算次数，默认是10。程序是否能快速收敛和中心点的选择关系非常大，所以在中心点选择上多花一些时间，来争取整体时间上的快速收敛还是非常值得的。由于每一次中心点都是随机生成的，这样得到的结果就有好有坏，非常不确定，所以要运行n\_init次, 取其中最好的作为初始的中心点。如果K值比较大的时候，你可以适当增大n\_init这个值；
- **init：** 即初始值选择的方式，默认是采用优化过的k-means++方式，你也可以自己指定中心点，或者采用random完全随机的方式。自己设置中心点一般是对于个性化的数据进行设置，很少采用。random的方式则是完全随机的方式，一般推荐采用优化过的k-means++方式；
- **algorithm**：k-means的实现算法，有“auto” “full”“elkan”三种。一般来说建议直接用默认的"auto"。简单说下这三个取值的区别，如果你选择"full"采用的是传统的K-Means算法，“auto”会根据数据的特点自动选择是选择“full”还是“elkan”。我们一般选择默认的取值，即“auto” 。

在创建好K-Means类之后，就可以使用它的方法，最常用的是fit和predict这个两个函数。你可以单独使用fit函数和predict函数，也可以合并使用fit\_predict函数。其中fit(data)可以对data数据进行k-Means聚类。 predict(data)可以针对data中的每个样本，计算最近的类。

现在我们要完整地跑一遍20支亚洲球队的聚类问题。我把数据上传到了[GitHub](https://github.com/cystanford/kmeans)上，你可以自行下载。

```
# coding: utf-8
from sklearn.cluster import KMeans
from sklearn import preprocessing
import pandas as pd
import numpy as np
# 输入数据
data = pd.read_csv('data.csv', encoding='gbk')
train_x = data[["2019年国际排名","2018世界杯","2015亚洲杯"]]
df = pd.DataFrame(train_x)
kmeans = KMeans(n_clusters=3)
# 规范化到[0,1]空间
min_max_scaler=preprocessing.MinMaxScaler()
train_x=min_max_scaler.fit_transform(train_x)
# kmeans算法
kmeans.fit(train_x)
predict_y = kmeans.predict(train_x)
# 合并聚类结果，插入到原数据中
result = pd.concat((data,pd.DataFrame(predict_y)),axis=1)
result.rename({0:u'聚类'},axis=1,inplace=True)
print(result)
```

运行结果：

```
国家  2019年国际排名  2018世界杯  2015亚洲杯  聚类
0       中国         73       40        7   2
1       日本         60       15        5   0
2       韩国         61       19        2   0
3       伊朗         34       18        6   0
4       沙特         67       26       10   0
5      伊拉克         91       40        4   2
6      卡塔尔        101       40       13   1
7      阿联酋         81       40        6   2
8   乌兹别克斯坦         88       40        8   2
9       泰国        122       40       17   1
10      越南        102       50       17   1
11      阿曼         87       50       12   1
12      巴林        116       50       11   1
13      朝鲜        110       50       14   1
14      印尼        164       50       17   1
15      澳洲         40       30        1   0
16     叙利亚         76       40       17   1
17      约旦        118       50        9   1
18     科威特        160       50       15   1
19    巴勒斯坦         96       50       16   1
```

## 总结

今天我给你讲了K-Means算法原理，我们再来看下开篇我给你提的三个问题。

如何确定K类的中心点？其中包括了初始的设置，以及中间迭代过程中中心点的计算。在初始设置中，会进行n\_init次的选择，然后选择初始中心点效果最好的为初始值。在每次分类更新后，你都需要重新确认每一类的中心点，一般采用均值的方式进行确认。

如何将其他点划分到K类中？这里实际上是关于距离的定义，我们知道距离有多种定义的方式，在K-Means和KNN中，我们都可以采用欧氏距离、曼哈顿距离、切比雪夫距离、余弦距离等。对于点的划分，就看它离哪个类的中心点的距离最近，就属于哪一类。

如何区分K-Means和KNN这两种算法呢？刚学过K-Means和KNN算法的同学应该能知道两者的区别，但往往过了一段时间，就容易混淆。所以我们可以从三个维度来区分K-Means和KNN这两个算法：

- 首先，这两个算法解决数据挖掘的两类问题。K-Means是聚类算法，KNN是分类算法。
- 这两个算法分别是两种不同的学习方式。K-Means是非监督学习，也就是不需要事先给出分类标签，而KNN是有监督学习，需要我们给出训练数据的分类标识。
- 最后，K值的含义不同。K-Means中的K值代表K类。KNN中的K值代表K个最接近的邻居。

![](https://static001.geekbang.org/resource/image/eb/c5/eb60546c6a3d9bc6a1538049c26723c5.png?wh=864%2A588)  
那么学完了今天的内容后，你能说一下K-Means的算法原理吗？如果我们把上面的20支亚洲球队用K-Means划分成5类，在规范化数据的时候采用标准化的方式（即均值为0，方差为1），该如何编写程序呢？运行的结果又是如何？

欢迎你在评论区与我分享你的答案，也欢迎点击“请朋友读”，把这篇文章分享给你的朋友或者同事。
<div><strong>精选留言（15）</strong></div><ul>
<li><span>third</span> 👍（35） 💬（2）<p>两者的区别的比喻是，
Kmeans开班，选老大，风水轮流转，直到选出最佳中心老大
Knn小弟加队伍，离那个班相对近，就是那个班的

一群人的有些人想要聚在一起
首先大家民主（无监督学习）随机选K个老大（随机选择K个中心点）
谁跟谁近，就是那个队伍的人（计算距离，距离近的聚合到一块）
随着时间的推移，老大的位置在变化（根据算法，重新计算中心点）
直到选出真正的中心老大（重复，直到准确率最高）

Knn
一个人想要找到自己的队伍
首先听从神的旨意（有监督学习），随机最近的几个邻居
看看距离远不远（根据算法，计算距离）
近的就是一个班的了（属于哪个分类多，就是哪一类）

#输入数据
#数据探索
import pandas as pd
data=pd.read_csv(&quot;.&#47;26&#47;data.csv&quot;,encoding=&#39;gbk&#39;)
# print(data)数据符合完整合一，数据质量较高

#提取数据
train_x=data[[&quot;2019年国际排名&quot;,&quot;2018世界杯&quot;,&quot;2015亚洲杯&quot;]]

#数据规范化
from sklearn import preprocessing
ss=preprocessing.StandardScaler()
train_ss_x=ss.fit_transform(train_x)

#对数据进行拟合并预测
from sklearn.cluster import KMeans
kmeans=KMeans(n_clusters=5)
kmeans.fit(train_ss_x)
pre=kmeans.predict(train_ss_x)

#数据对比
train_x=pd.DataFrame(train_x)
result=pd.concat((data,pd.DataFrame(pre)),axis=1)

result.rename({0:u&#39;聚类&#39;},axis=1,inplace=True)
print(result)</p>2019-02-19</li><br/><li><span>Lee</span> 👍（9） 💬（1）<p># coding: utf-8
from sklearn.cluster import KMeans
from sklearn import preprocessing
import pandas as pd
import numpy as np
# 输入数据
data = pd.read_csv(r&#39;F:\Python\notebook\K-Means\kmeans-master\data.csv&#39;, encoding = &#39;gbk&#39;)
data.head()
train_x = data[[&quot;2019年国际排名&quot;,&quot;2018世界杯&quot;,&quot;2015亚洲杯&quot;]]
df = pd.DataFrame(train_x)
kmeans = KMeans(n_clusters=5)
# 规范化
min_max_scaler=preprocessing.StandardScaler()
train_x=min_max_scaler.fit_transform(train_x)
# kmeans 算法
kmeans.fit(train_x)
predict_y = kmeans.predict(train_x)
# 合并聚类结果，插入到原数据中
result = pd.concat((data,pd.DataFrame(predict_y)),axis=1)
result.rename({0:u&#39;聚类&#39;},axis=1,inplace=True)
print(result)

       国家  2019年国际排名  2018世界杯  2015亚洲杯  聚类
0       中国         73       40        7   0
1       日本         60       15        5   3
2       韩国         61       19        2   3
3       伊朗         34       18        6   3
4       沙特         67       26       10   0
5      伊拉克         91       40        4   0
6      卡塔尔        101       40       13   4
7      阿联酋         81       40        6   0
8   乌兹别克斯坦         88       40        8   0
9       泰国        122       40       17   4
10      越南        102       50       17   4
11      阿曼         87       50       12   2
12      巴林        116       50       11   2
13      朝鲜        110       50       14   2
14      印尼        164       50       17   1
15      澳洲         40       30        1   3
16     叙利亚         76       40       17   4
17      约旦        118       50        9   2
18     科威特        160       50       15   1
19    巴勒斯坦         96       50       16   4</p>2019-02-14</li><br/><li><span>白夜</span> 👍（10） 💬（3）<p>然后我们再重新计算这三个类的中心点，如何计算呢？最简单的方式就是取平均值，然后根据新的中心点按照距离远近重新分配球队的分类，再根据球队的分类更新中心点的位置。计算过程这里不展开，最后一直迭代（重复上述的计算过程：计算中心点和划分分类）到分类不再发生变化。

老师，这段可以再解释一下吗？没计算过程不太理解</p>2019-02-15</li><br/><li><span>乃鱼同学</span> 👍（7） 💬（1）<p>K-Means 是聚类算法：经常做坏事的人 ，就是坏人。
KNN 是分类算法：坏人经常做坏事。
我对孩子就是这么说的。</p>2019-10-08</li><br/><li><span>听妈妈的话</span> 👍（4） 💬（3）<p>代码里的第八行应该去掉列名里的空格：
train_x = data[[&#39;2019年国际排名&#39;,&#39;2018世界杯&#39;,&#39;2015亚洲杯&#39;]]
Z-score标准化的代码：train_x=preprocessing.scale(train_x)

国家	2019年国际排名	2018世界杯	2015亚洲杯	聚类
0	中国	73	40	7	3
1	日本	60	15	5	1
2	韩国	61	19	2	1
3	伊朗	34	18	6	1
4	沙特	67	26	10	1
5	伊拉克	91	40	4	3
6	卡塔尔	101	40	13	0
7	阿联酋	81	40	6	3
8	乌兹别克斯坦	88	40	8	3
9	泰国	122	40	17	4
10	越南	102	50	17	4
11	阿曼	87	50	12	0
12	巴林	116	50	11	0
13	朝鲜	110	50	14	0
14	印尼	164	50	17	2
15	澳洲	40	30	1	1
16	叙利亚	76	40	17	4
17	约旦	118	50	9	0
18	科威特	160	50	15	2
19	巴勒斯坦	96	50	16	4</p>2019-03-22</li><br/><li><span>iamtalent123</span> 👍（4） 💬（2）<p>老师，请问为什么要对train_x转化为datadframe格式呢？df=pd.DataFrame(train_x)，df有什么用呢？</p>2019-03-05</li><br/><li><span>juixv3937</span> 👍（2） 💬（2）<p>为什么,你们的代码,运行出来跟我的结果都不一样</p>2019-08-11</li><br/><li><span>周飞</span> 👍（2） 💬（1）<p>k-means的算法原理就是：
1.选择几个初始的中心点。
2.计算每个点到各个中心点的距离，然后把每个点划分到距离最近的中心点所在的类。
3.更新中心点的值。对于每个类，计算类中所有数据的平均值，把平均值作为新的中心点。
4.重复 2 和4 步骤，直到每个类中的数据不再变化，或者到达指定的迭代步数。</p>2019-04-14</li><br/><li><span>FORWARD―MOUNT</span> 👍（2） 💬（2）<p>如何调整聚类中心没听懂</p>2019-02-18</li><br/><li><span>Jack</span> 👍（1） 💬（1）<p>老师，对于K-Means算法，我们如何评估模型的好坏，常用的评价指标都有哪些呢？</p>2020-07-20</li><br/><li><span>Yafei</span> 👍（1） 💬（1）<p>这也就是 K-Means 的中心思想，就是这么简单直接。你可能会问：如果一开始，选择一流球队是中国，二流球队是伊朗，三流球队是韩国，中心点选择错了怎么办？其实不用担心，K-Means 有自我纠正机制，在不断的迭代过程中，会纠正中心点。中心点在整个迭代过程中，并不是唯一的，只是你需要一个初始值，一般算法会随机设置初始的中心点。
老师，这段是否表述有误，如果你一开始就给中国一流球队的标签，在计算所有点到中国距离的平均距离过程中，分类点会收敛到这类标签的中心点，但是标签还是一流球队，并不会改变，变化的仅是分类点。因此，对于聚类，我们只是将所有样本点归到一个类别下，具体类别的标签应该是我们自己来标记的。如理解不对，还望指正！</p>2019-07-01</li><br/><li><span>JingZ</span> 👍（1） 💬（2）<p>import numpy as np 这行代码不需要吧~感觉没用到</p>2019-02-26</li><br/><li><span>非同凡想</span> 👍（0） 💬（1）<p>交作业了
import pandas as pd
from sklearn.preprocessing import MinMaxScaler,StandardScaler
from sklearn.cluster import KMeans

data  = pd.read_csv(&#39;~&#47;Documents&#47;kmeans&#47;data.csv&#39;,encoding=&#39;gbk&#39;)

print(data.info())
print(data.head())

features = data.columns[1:]

train_x = data[features]

# scaler = MinMaxScaler()
scaler = StandardScaler()
train_x = scaler.fit_transform(train_x)

model = KMeans(n_clusters=5)

clusters = model.fit_predict(train_x)
data[&#39;聚类&#39;] = clusters
print(data)

       国家  2019年国际排名  2018世界杯  2015亚洲杯  聚类
0       中国         73       40        7   2
1       日本         60       15        5   1
2       韩国         61       19        2   1
3       伊朗         34       18        6   1
4       沙特         67       26       10   1
5      伊拉克         91       40        4   2
6      卡塔尔        101       40       13   0
7      阿联酋         81       40        6   2
8   乌兹别克斯坦         88       40        8   2
9       泰国        122       40       17   4
10      越南        102       50       17   4
11      阿曼         87       50       12   0
12      巴林        116       50       11   0
13      朝鲜        110       50       14   0
14      印尼        164       50       17   3
15      澳洲         40       30        1   1
16     叙利亚         76       40       17   4
17      约旦        118       50        9   0
18     科威特        160       50       15   3
19    巴勒斯坦         96       50       16   4</p>2020-11-23</li><br/><li><span>Geek_c9fa4e</span> 👍（0） 💬（1）<p>K-Means的算法原理：就是通过初始化一个类别，通过计算出它们直接的距离，来区别属于哪一个类。</p>2020-04-28</li><br/><li><span>鱼非子</span> 👍（0） 💬（1）<p>        国家  2019年国际排名  2018世界杯  2015亚洲杯  聚类
0       中国         73       40        7   3
1       日本         60       15        5   1
2       韩国         61       19        2   1
3       伊朗         34       18        6   1
4       沙特         67       26       10   3
5      伊拉克         91       40        4   3
6      卡塔尔        101       40       13   0
7      阿联酋         81       40        6   3
8   乌兹别克斯坦         88       40        8   3
9       泰国        122       40       17   0
10      越南        102       50       17   0
11      阿曼         87       50       12   2
12      巴林        116       50       11   2
13      朝鲜        110       50       14   2
14      印尼        164       50       17   4
15      澳洲         40       30        1   1
16     叙利亚         76       40       17   0
17      约旦        118       50        9   2
18     科威特        160       50       15   4
19    巴勒斯坦         96       50       16   0
</p>2020-03-04</li><br/>
</ul>