你好，我是陈磊。

课程到现在，我们已经一起从接口测试思维的训练，走到了接口测试技术的训练，随着学习的不断深入，你应该也有了一个自己的测试框架，虽然这个框架可能还很简陋。但是任何事情不管多晚开始，都好于从未开始，因此学到现在，你已经迈出了接口测试以及其测试技术的第一步。

做任何事情，从零到一都需要莫大的勇气和坚定的决心，在这个过程中，你要将自己挪出舒适区，进入一个陌生的领域，这确实很难。但如果你和我一起走到了这一节课，那么我要恭喜你，你已经完成了接口测试从零到一的转变，后续从一到无穷大，你只需要随着时间去积累经验就可以了。

如果把接口测试比喻成要炒一盘菜的话，那么我在之前的全部课程中，重点都是在讲解如何完成接口测试，也就是教你如何炒菜。我也教过你如何解决接口测试的需求，为你提供了解决问题的能力和手段，这也就是在帮你建造一个设备齐全的厨房，帮你一起完成接口测试任务 。

有了精致的厨房后，我也告诉了你要怎么制作顶级的厨具，也就是接口测试的技术方法和实践方式。这些厨具既有锅碗瓢盆，也有刀勺铲叉，这里的锅碗瓢盆就是你的测试框架，刀勺铲叉就是你使用框架完成的测试脚本，这其中既包含了单接口的测试脚本，也包含了业务逻辑多接口测试脚本。

那么如果想炒菜你还需要准备什么呢？毫无疑问那就是菜，所谓“巧妇难为无米之炊”，即使你有高超的手艺，有世界顶级的厨具，但如果没有做菜的原材料，那也没办法把菜做出来，就算是世界顶级大厨，也无法完成这样的任务。

今天我就顺着这个思路，和你讲讲菜的准备，也就是接口测试的数据准备工作。

## 测试数据的好处：打造自动化测试框架

随着你不断封装自己的测试框架，你的框架就始终处于等米下锅这样一种的状态，而米就是测试数据。我在之前的课程中，都是将测试数据直接写在代码里，赋值给一个变量，然后通过接口测试逻辑来完成测试。

说到这，我还是把我们之前用过的”战场“这个系统拿出来，看一看它“选择武器”这个接口测试脚本（你可以回到[04](https://time.geekbang.org/column/article/195483)中查看），虽然你现在对怎么撰写、怎么封装类似的接口脚本都已经烂熟于心，但我们还是先看一下它的代码段：

```
# uri_login存储战场的选择武器
uri_selectEq = '/selectEq'
# 武器编号变量存储用户名参数
equipmentid = '10003'
# 拼凑body的参数
payload = 'equipmentid=' + equipmentid
response_selectEq = comm.post(uri_selectEq,params=payload)
print('Response内容：' + response_selectEq.text)
```

这就是你通过自己的Common类改造后的测试框架，但是现在，它还不能是算是一个完美的框架，为什么呢？

这是因为，你现在的参数都是直接通过equipmentid变量赋值的，在做测试的时候，你还需要不断修改这个参数的赋值，才能完成接口的入参测试，这不是一种自动化的测试思路。

因此，你需要将数据封装，通过一种更好的方式，将数据存储到一种数据存储文件中，这样代码就可以自行查找对应的参数，然后调取测试框架执行测试流程，接着再通过自动比对返回预期，检验测试结果是否正确。

这样做有两个好处。

1. 无人值守，节省时间和精力。我们将所有的参数都存储到外部存储文件中，测试框架就可以自行选择第一个参数进行测试，在完成第一个测试之后，它也就可以自行选择下一个参数，整个执行过程是不需要人参与的。否则的话，我们每复制一组参数，就要执行一次脚本，然后再人工替换一次参数，再执行一次脚本，这个过程耗时费力，而且又是一个纯人工控制的没什么技术含量的活动。
2. 自动检测返回值，提高测试效率。如果你用上面的代码段完成接口测试，就要每执行一次，人工去观察一次，看接口的返回是不是和预期一致，人工来做这些事情，不只非常耗费时间，效率也很低下。但是通过代码完成一些关键匹配却很容易，这可以大大提高测试效率，快速完成交付。

怎么样，看到这些好处，你是不是也想马上给你的框架加上数据处理的部分了呢？

## 如何选取测试数据

现在我们就马上开始动手，为你的框架加上参数类。

首先，你先要定义一种参数的存储格式。那么我想问你的是，要是让你选择把数据储存在一个文件中，你会选择什么格式的文件呢？

我相信你肯定和我的选择一样，用Excel。因为目前来看，Excel是在设计测试用例方面使用最多的一个工具，那么我们也就可以用Excel作为自己的参数存储文件。

但在动手之前，你也应该想到，你的参数文件类型不会是一成不变的Excel，未来你也有可能使用其他格式的参数文件，因此在一开始你还要考虑到参数类的扩展性，这样你就不用每多了一种参数文件存储格式，就写一个参数类，来完成参数的选取和调用了。

那么如何选取和调用参数呢？你可以看看我设计的参数类：

```
import json
import xlrd
class Param(object):
  def __init__(self,paramConf='{}'):
    self.paramConf = json.loads(paramConf)
  def paramRowsCount(self):
    pass
  def paramColsCount(self):
    pass
  def paramHeader(self):
    pass
  def paramAllline(self):
    pass
  def paramAlllineDict(self):
    pass


class XLS(Param):
  '''
  xls基本格式(如果要把xls中存储的数字按照文本读出来的话,纯数字前要加上英文单引号:
  
  第一行是参数的注释,就是每一行参数是什么
  
  第二行是参数名,参数名和对应模块的po页面的变量名一致
  
  第3~N行是参数
  
  最后一列是预期默认头Exp
  '''
  def __init__(self, paramConf):
    '''
    :param paramConf: xls 文件位置(绝对路径)
    '''
    self.paramConf = paramConf
    self.paramfile = self.paramConf['file']
    self.data = xlrd.open_workbook(self.paramfile)
    self.getParamSheet(self.paramConf['sheet'])
  def getParamSheet(self,nsheets):
    '''
    设定参数所处的sheet
    :param nsheets: 参数在第几个sheet中
    :return:
    '''
    self.paramsheet = self.data.sheets()[nsheets]
  def getOneline(self,nRow):
    '''
    返回一行数据
    :param nRow: 行数
    :return: 一行数据 []
    '''
    return self.paramsheet.row_values(nRow)
  def getOneCol(self,nCol):
    '''
    返回一列
    :param nCol: 列数
    :return: 一列数据 []
    '''
    return self.paramsheet.col_values(nCol)
  def paramRowsCount(self):
    '''
    获取参数文件行数
    :return: 参数行数 int
    '''
    return self.paramsheet.nrows
  def paramColsCount(self):
    '''
    获取参数文件列数(参数个数)
    :return: 参数文件列数(参数个数) int
    '''
    return self.paramsheet.ncols
  def paramHeader(self):
    '''
    获取参数名称
    :return: 参数名称[]
    '''
    return self.getOneline(1)
  def paramAlllineDict(self):
    '''
    获取全部参数
    :return: {{}},其中dict的key值是header的值
    '''
    nCountRows = self.paramRowsCount()
    nCountCols = self.paramColsCount()
    ParamAllListDict = {}
    iRowStep = 2
    iColStep = 0
    ParamHeader= self.paramHeader()
    while iRowStep < nCountRows:
    ParamOneLinelist=self.getOneline(iRowStep)
    ParamOnelineDict = {}
    while iColStep<nCountCols:
    ParamOnelineDict[ParamHeader[iColStep]]=ParamOneLinelist[iColStep]
    iColStep=iColStep+1
    iColStep=0
    ParamAllListDict[iRowStep-2]=ParamOnelineDict
    iRowStep=iRowStep+1
    return ParamAllListDict
  def paramAllline(self):
    '''
    获取全部参数
    :return: 全部参数[[]]
    '''
    nCountRows= self.paramRowsCount()
    paramall = []
    iRowStep =2
    while iRowStep<nCountRows:
    paramall.append(self.getOneline(iRowStep))
    iRowStep=iRowStep+1
    return paramall
  def __getParamCell(self,numberRow,numberCol):
    return self.paramsheet.cell_value(numberRow,numberCol)
class ParamFactory(object):
  def chooseParam(self,type,paramConf):
    map_ = {
    'xls': XLS(paramConf)
    }
    return map_[type
```

上面这个代码看着很多，但你不需要完全看得懂，你只需要知道它解决问题的思路和方法就可以了，**思路就是通过统一抽象，建立一个公共处理数据的方式。**你可以设计和使用简单工厂类的设计模式，这样如果多一种参数存储类型，再添加一个对应的处理类就可以了，这很便于你做快速扩展，也可以一劳永逸地提供统一数据的处理模式。

如果你的技术栈和我不一样，那么你只需要搜索一下你自己技术栈所对应的简单工厂类设计模式，然后照猫画虎地把上面的逻辑实现一下就可以了。接下来，你就可以把这次测试的全部参数都存到Excel里面了，具体内容如下图所示：

![](https://static001.geekbang.org/resource/image/93/5c/93da46d5d04c57a87f0cb6fe38583d5c.jpg?wh=1142%2A294)

通过上面的参数类你可以看出，在这个Excel文件中，第一行是给人读取的每一列参数的注释，而所有的Excel都是从第二行开始读取的，第二行是参数名和固定的表示预期结果的exp。现在，我们使用ParamFactory类，再配合上面的这个Excel，就可以完成”战场“系统“选择武器”接口的改造了，如下面这段代码所示：

```
#引入Common、ParamFactory类
from common import Common
from param import ParamFactory
import os
# uri_login存储战场的选择武器
uri_selectEq = '/selectEq'
comm = Common('http://127.0.0.1:12356',api_type='http')
# 武器编号变量存储武器编号，并且验证返回时是否有参数设计预期结果
# 获取当前路径绝对值
curPath = os.path.abspath('.')
# 定义存储参数的excel文件路径
searchparamfile = curPath+'/equipmentid_param.xls'
# 调用参数类完成参数读取，返回是一个字典，包含全部的excel数据除去excel的第一行表头说明
searchparam_dict = ParamFactory().chooseParam('xls',{'file':searchparamfile,'sheet':0}).paramAlllineDict()
i=0
while i<len(searchparam_dict):
  # 读取通过参数类获取的第i行的参数
  payload = 'equipmentid=' + searchparam_dict[i]['equipmentid']
  # 读取通过参数类获取的第i行的预期
  exp=searchparam_dict[i]['exp']
  # 进行接口测试
  response_selectEq = comm.post(uri_selectEq,params=payload)
  # 打印返回结果
  print('Response内容：' + response_selectEq.text)
  # 读取下一行excel中的数据
  i=i+1
```

这样再执行你的测试脚本，你就可以看到数据文件中的三条数据，已经都会顺序的自动执行了。那么后续如果将它付诸于你自己的技术栈，以及自己的测试驱动框架比如Python的[unittest](https://docs.python.org/zh-cn/3/library/unittest.html)、Java的[Junit](https://junit.org/junit5/)等，你就可以通过断言完成预期结果的自动验证了。

## 总结

今天我们接口测试数据准备的内容就到这里了，在接口测试的工作中，作为“巧妇”的测试工程师，还是需要参数这个“米”来下锅的，虽然我们之前课程中的代码涉及到参数的处理，但是都很简单粗暴，一点也不适合自动化的处理方式，因此今天，我带你完成了参数类的封装。

有的时候，我们也把参数类叫做参数池，这也就是说参数是存放在一个池子中，那我们准备好的池子就是Excel。我相信未来你也会不断扩展自己参数池的种类，这有可能是由于测试接口的特殊需求，也有可能是由于团队技术栈的要求。因此，我们封装参数池是通过简单工厂设计模式来实现的，如果你的代码基础并不好，那么你可以不用搞清楚简单工厂设计模式是什么，只需要知道如何模拟上述代码，再进行扩展就可以了。

一个好用的测试框架既要有很好的可用性，也要有很好的扩展性设计，这样我们的私有接口测试武器仓库就会变成可以不断扩展的、保持统一使用方法的武器仓库，这样才能让你或者你的团队在面对各种各样的测试任务时，既可以快速适应不同接口测试的需求，又不需要增加学习的成本。

## 思考题

今天我们一起学习了参数类的设计，并且将它应用到”战场“系统的接口测试脚本中，后续我又告诉你为了能够完成代码的自动验证，你需要引入一些测试驱动框架，那么，你的技术栈是什么？你在你的框架中选取的测试驱动框架又是什么呢？你能将之前”战场“系统的全流程测试脚本通过参数类完成改造吗？我期待看到你的测试脚本。

我是陈磊，欢迎你在留言区留言分享你的观点，如果这篇文章让你有新的启发，也欢迎你把文章分享给你的朋友，我们一起沟通探讨。
<div><strong>精选留言（15）</strong></div><ul>
<li><span>孙瑜</span> 👍（15） 💬（5）<p>明天就按老师说的去实践下，过年宅家机缘开始学测试自动化，在现在公司刚一年目前测试大家都是辅以工具的纯手工测试，想提升一下团队测试效率和质量。调研后选了python进行学习，测试框架选了pytest，学了已有三周，目前根据公司业务已经把requests、selenium、ymal、db三方库做了封装组合，已开始实际进行api和web自动话测试。数据驱动目前只是用了一些pytest的参数化装饰器或者写sql去数据库随机抓一些id当参数，明天就去试试放在execl来驱动，这周在弄PO分层，本来看视频自学写的都挤一起，然后还有log输出 自动截图 邮件 allure报告等基础功能，还考虑后续把执行结果或其他一些信息持久化存到数据库，并集成到公司jenkins上，因为公司都是web项目appuim还没学，但有几个公众号的webview项目，还不知道怎么弄，先把主要几个系统自动化都覆盖，并把框架再多完善完善，后续还想学下Django把框架web化一些，让其他不懂擅长开发的同事们操作更方便，所以execl也是大家比较擅长使用的。目前其实还没想得明明白白的是，怎么能让不会开发的测试同事在不编写代码的前提下，也能按照自己的测试经验编写能被自动化框架执行的测试用例、测试数据和断言，提升整个团队的效率，还请老师给予指导（因为我目前设计 数据断言可以数据驱动&#47;自动，用例还是根据业务然后自己写py方法调用封装好的接口或者页面PO方法，不会写代码就用不起来，难道让他们写文字版，我来翻译成代码，感觉不灵活，参与感也不强）</p>2020-02-18</li><br/><li><span>nothingc_lj</span> 👍（10） 💬（1）<p>接触了httprunner manager这个接口自动化框架平台感觉不错，是通过数据库来存储测试用例数据</p>2020-02-18</li><br/><li><span>彦鋆</span> 👍（8） 💬（3）<p>老师，您好，看了您的文章，感觉茅塞顿开。我之前自己有写过前端的测试框架，利用po模式+selenium+unittest完成的；看了您的前几章，
我也初步写了自己的第一个接口自动化测试框架。利用自己的技术栈用分层处理的方式（有点借鉴PO模式）+unittest+excel存储数据实现了自己的接口自动化。
我的excel设计是这样的，每个sheet页的名称是接口的名称(比如battle中的index、login)，sheet页中的数据就是当前接口的所有测试用例，第一行是参数说明，
主要设计有用例名称、方法、url、参数、预期结果；util层封装了操作excel的一些方法；handle层封装一条用例需要的参数；business层对handle层获取的参数作一些处理；
common层就是对get&#47;post&#47;put方法的封装，case层主要所有的用例（test_接口名称.py），每个用例py文件实现每个sheet页中的所有用例；
report层存放利用HTMLTestRunner生成的报告；最后利用jenkins完成自动化构建并发送邮件通知。 请老师指点一下我这个简单框架，目前还没有运用到工作中，谢谢。</p>2020-02-23</li><br/><li><span>hello zero</span> 👍（6） 💬（3）<p> 老师，请教个数据准备的问题，如果需要测试的是支付，那么是不是需要提前准备好订单数据，那订单数据本身可能又需要用户和商品数据，用户数据可能又需要地址数据，商品有可能需要品类和规格数据等等。这种情况下，是先构建最基础的数据比如地址数据并同时进行测试但是不删除数据一直留给支付测试使用，等支付使用完后再进行删除；还是每次测试支付的时候都使用一组选好的一直留在那里的数据进行测试呢。也就是如何构建闭环的长流程的可以重复执行的测试数据呢？</p>2020-02-19</li><br/><li><span>梅子</span> 👍（3） 💬（1）<p>请问老师一个接口测试设计的问题，如果一个接口入参和出参数据值都比较多，入参的话需要每个参数都按照范围类型等进行测试吗？出参的话每个参数值都要进行校验吗？</p>2020-09-10</li><br/><li><span>null</span> 👍（2） 💬（1）<p>陈老师，建议例子打包一个项目，读者debug阅读代码比较深刻。从页面复制代码到本地运行，格式错了运行不起来。
</p>2020-02-20</li><br/><li><span>派森</span> 👍（2） 💬（2）<p>还是感觉yaml更加清晰，编写过程中格式问题也比较少</p>2020-02-20</li><br/><li><span>aoe</span> 👍（2） 💬（1）<p>作为一个Java程序员，我希望自己的测试框架可以实现以下功能：
1. 发现Bug后立即报错，终止后续测试：快速失败机制，节省后续测试时间，可以立即进去修改阶段；
2. 跑完全部测试用例，统计出所有Bug：适合多少提交后、自身粗心大意的程序员，及时知道增加的工作量，合理分配时间</p>2020-02-18</li><br/><li><span>钱</span> 👍（1） 💬（3）<p>哈哈，为什么不把数据存储数据库中？然后搞个测试数据管理系统，增删改查导入导出可视化分析不好玩嘛？
看完总结就是，为了加快速度，一定要善用工具，没有工具就自己造工具，怎么造就需要学习一下编程技术啦！这是耗时耗力，但收益最大的一部分。</p>2020-02-26</li><br/><li><span>罗春南_Nancy</span> 👍（1） 💬（1）<p>执行获取参数并访问选择装备的接口时，脚本是一直在执行状态的，但是没有返回任何结果</p>2020-02-24</li><br/><li><span>、Attention</span> 👍（1） 💬（7）<p>老师你好，获取全部参数的方法是不是有点问题？？ 我一直执行不出来 。</p>2020-02-17</li><br/><li><span>ZeroIce</span> 👍（1） 💬（1）<p>个人觉得：Jenkins + postman不错</p>2020-02-17</li><br/><li><span>捷后愚生</span> 👍（0） 💬（1）<p>本文总结

参数化的好处：
利用无人值守时间，节省时间和精力
自动校验返回值，提高效率

解决问题的思路和方法很重要，知识分为四种：你知道你知道、你知道你不知道、你不知道自己不知道、你不知道自己知道，当你意识到要做excel文件参数化时，但是不知道具体代码怎么实现，我想直接在百度搜索“python excel文件参数化”，可以找到很多答案，最怕是你没有这个思路。</p>2020-11-28</li><br/><li><span>Edward</span> 👍（0） 💬（1）<p>每个参数的类型比较难处理</p>2020-06-11</li><br/><li><span>liya</span> 👍（0） 💬（2）<p>现在我们的自动化项目遇到一个尴尬问题，因为有些接口验证服务 比较复杂， 接口返回太简单， 所以 需要用另外一个接口来辅助校验， 比如 注册接口 注册一个用户成功后， 会用登录接口来辅助校验，大部分的接口都会有 其它接口来辅助验证， 这样项目做大后，  很不好维护， 老师有没有什么建议？或者你们平时都是怎么验证接口逻辑正常的？</p>2020-05-13</li><br/>
</ul>