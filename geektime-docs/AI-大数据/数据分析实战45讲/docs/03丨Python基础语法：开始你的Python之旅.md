上一节课我跟你分享了数据挖掘的最佳学习路径，相信你对接下来的学习已经心中有数了。今天我们继续预习课，我会用三篇文章，分别对Python的基础语法、NumPy和Pandas进行讲解，带你快速入门Python语言。如果你已经有Python基础了，那先恭喜你已经掌握了这门简洁而高效的语言，这几节课你可以跳过，或者也可以当作复习，自己查漏补缺，你还可以在留言区分享自己的Python学习和使用心得。

好了，你现在心中是不是有个问题，要学好数据分析，一定要掌握Python吗？

我的答案是，想学好数据分析，你最好掌握Python语言。为什么这么说呢？

首先，在一份关于开发语言的调查中，使用过Python的开发者，80%都会把Python作为自己的主要语言。Python已经成为发展最快的主流编程语言，从众多开发语言中脱颖而出，深受开发者喜爱。其次，在数据分析领域中，使用Python的开发者是最多的，远超其他语言之和。最后，Python语言简洁，有大量的第三方库，功能强大，能解决数据分析的大部分问题，这一点我下面具体来说。

Python语言最大的优点是简洁，它虽然是C语言写的，但是摒弃了C语言的指针，这就让代码非常简洁明了。同样的一行Python代码，甚至相当于5行Java代码。我们读Python代码就像是读英文一样直观，这就能让程序员更好地专注在问题解决上，而不是在语言本身。

当然除了Python自身的特点，Python还有强大的开发者工具。在数据科学领域，Python有许多非常著名的工具库：比如科学计算工具NumPy和Pandas库，深度学习工具Keras和TensorFlow，以及机器学习工具Scikit-learn，使用率都非常高。

总之，如果你想在数据分析、机器学习等数据科学领域有所作为，那么掌握一项语言，尤其是Python语言的使用是非常有必要的，尤其是我们刚提到的这些工具，熟练掌握它们会让你事半功倍。

## 安装及IDE环境

了解了为什么要学Python，接下来就带你快速开始你的第一个Python程序，所以我们先来了解下如何安装和搭建IDE环境。

**Python的版本选择**

Python主要有两个版本： 2.7.x和3.x。两个版本之间存在一些差异，但并不大，它们语法不一样的地方不到10%。

另一个事实就是：大部分Python库都同时支持Python 2.7.x和3.x版本。虽然官方称Python2.7只维护到2020年，但是我想告诉你的是：千万不要忽视Python2.7，它的寿命远不止到2020年，而且这两年Python2.7还是占据着Python版本的统治地位。一份调查显示：在2017年的商业项目中2.7版本依然是主流，占到了63.7%，即使这两年Python3.x版本使用的增速较快，但实际上Python3.x在2008年就已经有了。

那么你可能会问：这两个版本该如何选择呢？

版本选择的标准就是看你的项目是否会依赖于Python2.7的包，如果有依赖的就只能使用Python2.7，否则你可以用Python 3.x开始全新的项目。

**Python IDE推荐**

确定了版本问题后，怎么选择Python IDE呢？有众多优秀的选择，这里推荐几款。

**1. PyCharm**

这是一个跨平台的Python开发工具，可以帮助用户在使用Python时提升效率，比如：调试、语法高亮、代码跳转、自动完成、智能提示等。

**2. Sublime Text**

SublimeText是个著名的编辑器，Sublime Text3基本上可以1秒即启动，反应速度很快。同时它对Python的支持也很到位，具有代码高亮、语法提示、自动完成等功能。

**3. Vim**

Vim是一个简洁、高效的工具，速度很快，可以做任何事，从来不崩溃。不过Vim相比于Sublime Text上手有一定难度，配置起来有些麻烦。

**4. Eclipse+PyDev**

习惯使用Java的人一定对Eclipse这个IDE不陌生，那么使用Eclipse+PyDev插件会是一个很好的选择，这样熟悉Eclipse的开发者可以轻易上手。

如果上面这些IDE你之前都没有怎么用过，那么推荐你使用Sublime Text，上手简单，反应速度快。

## Python基础语法

环境配置好后，我们就来快速学习几个Python必会的基础语法。我假设你是Python零基础，但已经有一些其他编程语言的基础。下面我们一一来看。

**输入与输出**

```
name = raw_input("What's your name?")
sum = 100+100
print ('hello,%s' %name)
print ('sum = %d' %sum)
```

raw\_input是Python2.7的输入函数，在python3.x里可以直接使用input，赋值给变量name，print 是输出函数，%name代表变量的数值，因为是字符串类型，所以在前面用的 %s作为代替。

这是运行结果：

```
What's your name?cy
hello,cy
sum = 200
```

**判断语句：if … else …**

```
if score>= 90:
       print 'Excellent'
else:
       if score < 60:
           print 'Fail'
       else:
           print 'Good Job'
```

if … else … 是经典的判断语句，需要注意的是在if expression后面有个冒号，同样在else后面也存在冒号。

另外需要注意的是，Python不像其他语言一样使用{}或者begin…end来分隔代码块，而是采用代码缩进和冒号的方式来区分代码之间的层次关系。所以**代码缩进在Python中是一种语法**，如果代码缩进不统一，比如有的是tab有的是空格，会怎样呢？会产生错误或者异常。相同层次的代码一定要采用相同层次的缩进。

**循环语句：for … in**

```
sum = 0
for number in range(11):
    sum = sum + number
print sum
```

运行结果：

```
55
```

for循环是一种迭代循环机制，迭代即重复相同的逻辑操作。如果规定循环的次数，我们可以使用range函数，它在for循环中比较常用。range(11)代表从0到10，不包括11，也相当于range(0,11)，range里面还可以增加步长，比如range(1,11,2)代表的是\[1,3,5,7,9]。

**循环语句: while**

```
sum = 0
number = 1
while number < 11:
       sum = sum + number
       number = number + 1
print sum
```

运行结果：

```
55
```

1到10的求和也可以用while循环来写，这里while控制了循环的次数。while循环是条件循环，在while循环中对于变量的计算方式更加灵活。因此while循环适合循环次数不确定的循环，而for循环的条件相对确定，适合固定次数的循环。

**数据类型：列表、元组、字典、集合**

**列表：\[]**

```
lists = ['a','b','c']
lists.append('d')
print lists
print len(lists)
lists.insert(0,'mm')
lists.pop()
print lists
```

运行结果：

```
['a', 'b', 'c', 'd']
4
['mm', 'a', 'b', 'c']
```

列表是Python中常用的数据结构，相当于数组，具有增删改查的功能，我们可以使用len()函数获得lists中元素的个数；使用append()在尾部添加元素，使用insert()在列表中插入元素，使用pop()删除尾部的元素。

**元组 (tuple)**

```
tuples = ('tupleA','tupleB')
print tuples[0]
```

运行结果：

```
tupleA
```

元组tuple和list非常类似，但是tuple一旦初始化就不能修改。因为不能修改所以没有append(), insert() 这样的方法，可以像访问数组一样进行访问，比如tuples\[0]，但不能赋值。

**字典 {dictionary}**

```
# -*- coding: utf-8 -*
#定义一个dictionary
score = {'guanyu':95,'zhangfei':96}
#添加一个元素
score['zhaoyun'] = 98
print score
#删除一个元素
score.pop('zhangfei')
#查看key是否存在
print 'guanyu' in score
#查看一个key对应的值
print score.get('guanyu')
print score.get('yase',99)
```

运行结果：

```
{'guanyu': 95, 'zhaoyun': 98, 'zhangfei': 96}
True
95
99
```

字典其实就是{key, value}，多次对同一个key放入value，后面的值会把前面的值冲掉，同样字典也有增删改查。增加字典的元素相当于赋值，比如score\[‘zhaoyun’] = 98，删除一个元素使用pop，查询使用get，如果查询的值不存在，我们也可以给一个默认值，比如score.get(‘yase’,99)。

**集合：set**

```
s = set(['a', 'b', 'c'])
s.add('d')
s.remove('b')
print s
print 'c' in s
```

运行结果：

```
set(['a', 'c', 'd'])
True
```

集合set和字典dictory类似，不过它只是key的集合，不存储value。同样可以增删查，增加使用add，删除使用remove，查询看某个元素是否在这个集合里，使用in。

**注释：#**

注释在python中使用#，如果注释中有中文，一般会在代码前添加# -*- coding: utf-8 -*。

如果是多行注释，使用三个单引号，或者三个双引号，比如：

```
# -*- coding: utf-8 -*
'''
这是多行注释，用三个单引号
这是多行注释，用三个单引号 
这是多行注释，用三个单引号
'''
```

**引用模块/包：import**

```
# 导入一个模块
import model_name
# 导入多个模块
import module_name1,module_name2
# 导入包中指定模块 
from package_name import moudule_name
# 导入包中所有模块 
from package_name import *
```

Python语言中import的使用很简单，直接使用import module\_name语句导入即可。这里import的本质是什么呢？import的本质是路径搜索。import引用可以是模块module，或者包package。

针对module，实际上是引用一个.py文件。而针对package，可以采用from … import …的方式，这里实际上是从一个目录中引用模块，这时目录结构中必须带有一个\_\_init\_\_.py文件。

**函数：def**

```
def addone(score):
   return score + 1
print addone(99)
```

运行结果：

```
100
```

函数代码块以def关键词开头，后接函数标识符名称和圆括号，在圆括号里是传进来的参数，然后通过return进行函数结果得反馈。

**A+B Problem**

上面的讲的这些基础语法，我们可以用sumlime text编辑器运行Python代码。另外，告诉你一个相当高效的方法，你可以充分利用一个刷题进阶的网址：[https://pintia.cn/problem-sets/91827364500/exam/problems/type/7](https://pintia.cn/problem-sets/91827364500/exam/problems/type/7)，这是一个OnlineJudge。

什么是OnlineJudge呢？它实际上是一个在线答题系统，做题后你可以在后台提交代码，然后OnlineJudge会告诉你运行的结果，如果结果正确就反馈：Accepted，如果错误就反馈：Wrong Answer。

不要小看这样的题目，也会存在编译错误、内存溢出、运行超时等等情况。所以题目对编码的质量要求还是挺高的。下面我就给你讲讲这道A+B的题目，你可以自己做练习，然后在后台提交答案。

**题目：A+B**

输入格式：有一系列的整数对A和B，以空格分开。

输出格式：对于每个整数对A和B，需要给出A和B的和。

输入输出样例：

```
INPUT
1 5
OUTPUT
6
```

针对这道题，我给出了下面的答案：

```
while True:
       try:
              line = raw_input()
              a = line.split()
              print int(a[0]) + int(a[1])
       except:
              break
```

当然每个人可以有不同的解法，官方也有Python的答案，这里给你介绍这个OnlineJudge是因为：

1. 可以在线得到反馈，提交代码后，系统会告诉你对错。而且你能看到每道题的正确率，和大家提交后反馈的状态；
2. 有社区论坛可以进行交流学习；
3. 对算法和数据结构的提升大有好处，当然对数据挖掘算法的灵活运用和整个编程基础的提升都会有很大的帮助。

## 总结

现在我们知道，Python毫无疑问是数据分析中最主流的语言。今天我们学习了这么多Python的基础语法，你是不是体会到了它的简洁。如果你有其他编程语言基础，相信你会非常容易地转换成Python语法的。那到此，Python我们也就算入门了。有没有什么方法可以在此基础上快速提升Python编程水平呢？给你分享下我的想法。

在日常工作中，我们解决的问题都不属于高难度的问题，大部分人做的都是开发工作而非科研项目。所以我们要提升的主要是**熟练度**，而通往熟练度的唯一路径就是练习、练习、再练习！

如果你是第一次使用Python，不用担心，最好的方式就是直接做题。把我上面的例子都跑一遍，自己在做题中体会。

如果你想提升自己的编程基础，尤其是算法和数据结构相关的能力，因为这个在后面的开发中都会用到。那么ACM Online Judge是非常好的选择，勇敢地打开这扇大门，把它当作你进阶的好工具。

你可以从Accepted比率高的题目入手，你做对的题目数越多，你的排名也会越来越往前，这意味着你的编程能力，包括算法和数据结构的能力都有了提升。另外这种在社区中跟大家一起学习，还能排名，就像游戏一样，让学习更有趣味，从此不再孤独。

![](https://static001.geekbang.org/resource/image/b9/9c/b93956302991443d440684d86d16199c.jpg?wh=1142%2A1986)

我在文章中多次强调练习的作用，这样可以增加你对数据分析相关内容的熟练度。所以我给你出了两道练习题，你可以思考下如何来做，欢迎把答案放到评论下面，我也会和你一起在评论区进行讨论。

1. 如果我想在Python中引用scikit-learn库该如何引用？
2. 求1+3+5+7+…+99的求和，用Python该如何写？

欢迎你把今天的内容分享给身边的朋友，和他一起掌握Python这门功能强大的语言。
<div><strong>精选留言（15）</strong></div><ul>
<li><span>米可哲</span> 👍（36） 💬（3）<p>online judge 会不会要求太高，一般水平的人刷leetcode就足够了吧？？</p>2018-12-30</li><br/><li><span>Hyperuniverse</span> 👍（139） 💬（3）<p>刷题网站:
1、LeetCode
2、Kaggel
3、老师推荐的Online Judge

Python入门：就看这本足够了——《Python编程：从入门到实践》

IDE：pycharm（写爬虫）、jupyter notebook+spyder3（数据分析主要IDE）、Sublime Text 3（牛逼的编辑器）

数据库：PGsql（挺好用的）、Mysql（开源，主流）

py版本：毫不犹豫选择py3（应为2020年py2停止维护了）

提升：没啥好说的，就是“干”，多写多练自然有感觉了，对，当你写多了代码，你看问题的层次也将不一样。所以，对自己狠心一点，不要一直在入门徘徊。
</p>2018-12-20</li><br/><li><span>●</span> 👍（95） 💬（3）<p>Q1:不是python内置库
采用命令行安装库pip install scikit-learn
引用库 import scikit-learn
Q2:
方法一：sum函数
print(sum(range(1,100,2)))
方法二：if迭代
a = 0
for i in range(1,100,2):
	a += i 
print(a)
方法三：while循环
i = 1
b = 0
while i &lt; 100:
	if i % 2 != 0 :
		b += i
	i +=1
print(b)</p>2018-12-20</li><br/><li><span>小熊猫</span> 👍（47） 💬（3）<p>1. pycharm、sublime、jupyter都用过，个人认为Pycharm适合比较大一点的项目，平时自己开发一些小脚本什么的可以用sublime，比较简洁方便，目前一直在用Jupyter，比较适合做数据分析，显示图表之类的，可视化、一行代码一个结果都很方便，今天的课程已经用Jupyter全部写了一遍。
2. 求和：sum(range(1, 100, 2))
sum(iterable, start)，sum的输入是iterable对象，比如list、tuple、set等
range()的返回值就是一个iterable对象，可以直接作为sum的输入参数
3. 前面有位同学一直出现 ‘int’ object is not iterable.的错误，我今天用Jupyter也碰到了，应该是前面老师的例子中用了sum做变量，后面求和这道题再用sum()做函数，所以出错了， 重启下Jupyter就行了，或者用魔法命令%reset清除变量应该也可以。
4. 吐槽下极客时间里不能回复其他人的留言，只有老师才能，这个功能需要完善下
</p>2018-12-21</li><br/><li><span>每天晒白牙</span> 👍（20） 💬（2）<p>第一道题：
import scikie-learn

第二道题：
方法一：用for循环
sum=0
for number in range(1,100,2):
     sum = sum + number
print sum
方法二：用while
sum =0
number = 1
while number &lt; 100:
        sum = sum + number
        number = number +2
print sum</p>2018-12-20</li><br/><li><span>拉我吃</span> 👍（19） 💬（1）<p>p1.
要先安装库
pip install -U scikit-learn

代码里写
import sklearn

p2. 
代码 sum(range(1, 99, 2)) 直接求和
print(sum(range(1, 99, 2))) 打印出来
</p>2018-12-20</li><br/><li><span>Miracle</span> 👍（12） 💬（2）<p>sklearn库是机器学习领域好用到哭的一个库，数据清洗，各种机器学习算法都给写好了，我们可以直接使用，学习sklearn感觉最好的方式就是通过官方文档学习：https:&#47;&#47;scikit-learn.org&#47;stable&#47;，但是在这之前最好先跟着教程过一遍sklearn，至少知道什么问题应该用什么算法等，然后再通过查阅文档进行补充。 使用的时候也很简单，pip install安装，然后import sklearn 或者 from sklearn import 模块等。  关于学习Python，我觉得可以找一个简单的教程（B站上好多）跟一遍，掌握基础的语法和使用，然后就是刷题或者项目中提高代码编程能力，在这个途中遇到不懂得可以查阅Python的官方文档进行知识补充。 我觉得官方文档是最好的学习方式。</p>2020-01-23</li><br/><li><span>大萌</span> 👍（10） 💬（1）<p>1、安装完成后 import sklearn
2、
（1）采用for循环
sum = 0
for i in range(1,100,2):
    sum+=i
print(sum)
（2）采用递归方法
def sum(x):
	if x&gt;99:
		return 0
	num = sum(x+2)
	return x+num
print(sum(1))
平常编程会用jupyter notebook，也可以推荐一下</p>2018-12-21</li><br/><li><span>夜路破晓</span> 👍（9） 💬（3）<p>实话说，这篇读起来“有点卡”，应该是没有编程基础的缘故。晚上下班回来鼓捣半天，最后给笔记本装了Anaconda，但是类似“Python中%的含义”就让我百度了半小时才搞懂。
逻辑不难懂，甚至看完这篇觉得貌似入门Python并不难，关键是想自己写出来就得花点功夫、在搞懂的基础上多做练习了。
买了从零学Python的视频课，也找到了《Python：从入门到实践》电子书，打算这周末先研究下再回来看。</p>2018-12-21</li><br/><li><span>虎皮青椒</span> 👍（6） 💬（1）<p>1.如果我想在Python中引用scikit-learn库该如何引用？
1）scikit-learn安装
	Python中安装scikit-learn之前需要以下先决条件：
	- Python(&gt;= 2.6 or &gt;= 3.3)
	- NumPy (&gt;= 1.6.1)
	- SciPy (&gt;= 0.9)
	1.1）安装numpy
		sudo pip install numpy
	1.2）安装安装scipy
		需要先安装matplotlib、ipython、ipython-notebook、pandas、sympy
		sudo apt-get install python-matplotlib ipython ipython-notebook
		sudo apt-get install python-pandas python-sympy python-nose
		sudo pip install scipy
	1.3）安装scikit-learn
		sudo pip install -U scikit-learn
	1.4）测试
		查看pip安装是否有sklearn这一项
		pip list | grep sklearn		
2）导入scikit-learn库
	from sklearn import *
	
2.求1+3+5+7+…+99的求和，用Python该如何写？
sum = 0
for number in range(1, 100, 2):
	sum += number
print(&quot;1 + 3 + 5 + 7 + … + 99的求和为%d&quot; % sum)</p>2019-04-16</li><br/><li><span>小林子</span> 👍（4） 💬（1）<p>第一题：
import sklearn

第二题：
sum([i for i in range(1,99,2)])</p>2018-12-20</li><br/><li><span>CHEN</span> 👍（3） 💬（1）<p>print(sum([i for i in range(1,100,2)]))</p>2020-07-08</li><br/><li><span>鱼鱼鱼培填</span> 👍（3） 💬（1）<p>看错题目了，第二题应该是：
sum = 0
for i in range(1, 100, 2):
	sum += i
print(sum)</p>2018-12-20</li><br/><li><span>nsyao</span> 👍（2） 💬（2）<p>关于ide选择部分，建议老师改一下。其实sunlime不合适新手，反而是anaconda套件更合适，spyder或jupyter对新手都很友好</p>2020-10-22</li><br/><li><span>土豆</span> 👍（2） 💬（1）<p>正好疫情在家封闭期间读完了 learning python英文版本，这本书虽然比较厚，1500页，但是是我读过的最好的python入门服务。所以我算是pyrhon入门了，回头再刷刷老师推荐的oj题目</p>2020-04-12</li><br/>
</ul>