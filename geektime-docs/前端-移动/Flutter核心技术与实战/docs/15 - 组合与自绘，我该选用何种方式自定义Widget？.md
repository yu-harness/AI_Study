你好，我是陈航。

在上一次分享中，我们认识了Flutter中最常用也最经典的布局Widget，即单子容器Container、多子容器Row/Column，以及层叠容器Stack与Positioned，也学习了这些不同容器之间的摆放子Widget的布局规则，我们可以通过它们，来实现子控件的对齐、嵌套、层叠等，它们也是构建一个界面精美的App所必须的布局概念。

在实际开发中，我们会经常遇到一些复杂的UI需求，往往无法通过使用Flutter的基本Widget，通过设置其属性参数来满足。这个时候，我们就需要针对特定的场景自定义Widget了。

在Flutter中，自定义Widget与其他平台类似：可以使用基本Widget组装成一个高级别的Widget，也可以自己在画板上根据特殊需求来画界面。

接下来，我会分别与你介绍组合和自绘这两种自定义Widget的方式。

## 组装

使用组合的方式自定义Widget，即通过我们之前介绍的布局方式，摆放项目所需要的基础Widget，并在控件内部设置这些基础Widget的样式，从而组合成一个更高级的控件。

这种方式，对外暴露的接口比较少，减少了上层使用成本，但也因此增强了控件的复用性。在Flutter中，**组合的思想始终贯穿在框架设计之中**，这也是Flutter提供了如此丰富的控件库的原因之一。

比如，在新闻类应用中，我们经常需要将新闻Icon、标题、简介与日期组合成一个单独的控件，作为一个整体去响应用户的点击事件。面对这类需求，我们可以把现有的Image、Text及各类布局，组合成一个更高级的新闻Item控件，对外暴露设置model和点击回调的属性即可。

接下来，我通过一个例子为你说明如何通过组装去自定义控件。

下图是App Store的升级项UI示意图，图里的每一项，都有应用Icon、名称、更新日期、更新简介、应用版本、应用大小以及更新/打开按钮。可以看到，这里面的UI元素还是相对较多的，现在我们希望将升级项UI封装成一个单独的控件，节省使用成本，以及后续的维护成本。

![](https://static001.geekbang.org/resource/image/01/cc/0157ffe54a9cd933795af6c8d7141ecc.png?wh=1125%2A2436)

图1 App Store 升级项UI

在分析这个升级项UI的整体结构之前，我们先定义一个数据结构UpdateItemModel来存储升级信息。在这里为了方便讨论，我把所有的属性都定义为了字符串类型，你在实际使用中可以根据需要将属性定义得更规范（比如，将appDate定义为DateTime类型）。

```
class UpdateItemModel {
  String appIcon;//App图标
  String appName;//App名称
  String appSize;//App大小
  String appDate;//App更新日期
  String appDescription;//App更新文案
  String appVersion;//App版本
  //构造函数语法糖，为属性赋值
  UpdateItemModel({this.appIcon, this.appName, this.appSize, this.appDate, this.appDescription, this.appVersion});
}
```

接下来，我以Google Map为例，和你一起分析下这个升级项UI的整体结构。

按照子Widget的摆放方向，布局方式只有水平和垂直两种，因此我们也按照这两个维度对UI结构进行拆解。

按垂直方向，我们用绿色的框把这个UI拆解为上半部分与下半部分，如图2所示。下半部分比较简单，是两个文本控件的组合；上半部分稍微复杂一点，我们先将其包装为一个水平布局的Row控件。

接下来，我们再一起看看水平方向应该如何布局。

![](https://static001.geekbang.org/resource/image/dd/21/dd6241906557f49e184a5dc16d33e521.png?wh=1318%2A736)

图2 升级项UI整体结构示意图

我们先把升级项的上半部分拆解成对应的UI元素：

- 左边的应用图标拆解为Image；
- 右边的按钮拆解为FlatButton；
- 中间部分是两个文本在垂直方向上的组合，因此拆解为Column，Column内部则是两个Text。

拆解示意图，如下所示：

![](https://static001.geekbang.org/resource/image/29/0d/29c1762d9c6271049c9149b5ab06bb0d.png?wh=976%2A598)

图3 上半部分UI结构示意图

通过与拆解前的UI对比，你就会发现还有3个问题待解决：即控件间的边距如何设置、中间部分的伸缩（截断）规则又是怎样、图片圆角怎么实现。接下来，我们分别来看看。

Image、FlatButton，以及Column这三个控件，与父容器Row之间存在一定的间距，因此我们还需要在最左边的Image与最右边的FlatButton上包装一层Padding，用以留白填充。

另一方面，考虑到需要适配不同尺寸的屏幕，中间部分的两个文本应该是变长可伸缩的，但也不能无限制地伸缩，太长了还是需要截断的，否则就会挤压到右边按钮的固定空间了。

因此，我们需要在Column的外层用Expanded控件再包装一层，让Image与FlatButton之间的空间全留给Column。不过，通常情况下这两个文本并不能完全填满中间的空间，因此我们还需要设置对齐格式，按照垂直方向上居中，水平方向上居左的方式排列。

最后一项需要注意的是，升级项UI的App Icon是圆角的，但普通的Image并不支持圆角。这时，我们可以使用ClipRRect控件来解决这个问题。ClipRRect可以将其子Widget按照圆角矩形的规则进行裁剪，所以用ClipRRect将Image包装起来，就可以实现图片圆角的功能了。

下面的代码，就是控件上半部分的关键代码：

```
Widget buildTopRow(BuildContext context) {
  return Row(//Row控件，用来水平摆放子Widget
    children: <Widget>[
      Padding(//Paddng控件，用来设置Image控件边距
        padding: EdgeInsets.all(10),//上下左右边距均为10
        child: ClipRRect(//圆角矩形裁剪控件
          borderRadius: BorderRadius.circular(8.0),//圆角半径为8
          child: Image.asset(model.appIcon, width: 80,height:80)图片控件//
        )
      ),
      Expanded(//Expanded控件，用来拉伸中间区域
        child: Column(//Column控件，用来垂直摆放子Widget
          mainAxisAlignment: MainAxisAlignment.center,//垂直方向居中对齐
          crossAxisAlignment: CrossAxisAlignment.start,//水平方向居左对齐
          children: <Widget>[
            Text(model.appName,maxLines: 1),//App名字
            Text(model.appDate,maxLines: 1),//App更新日期
          ],
        ),
      ),
      Padding(//Paddng控件，用来设置Widget间边距
        padding: EdgeInsets.fromLTRB(0,0,10,0),//右边距为10，其余均为0
        child: FlatButton(//按钮控件
          child: Text("OPEN"),
          onPressed: onPressed,//点击回调
        )
      )
  ]);
}
```

升级项UI的下半部分比较简单，是两个文本控件的组合。与上半部分的拆解类似，我们用一个Column控件将它俩装起来，如图4所示：

![](https://static001.geekbang.org/resource/image/7d/3d/7da3ec3d2068550fc20481ae3457173d.png?wh=960%2A326)

图4 下半部分UI结构示意图

与上半部分类似，这两个文本与父容器之间存在些间距，因此在Column的最外层还需要用Padding控件给包装起来，设置父容器间距。

另一方面，Column的两个文本控件间也存在间距，因此我们仍然使用Padding控件将下面的文本包装起来，单独设置这两个文本之间的间距。

同样地，通常情况下这两个文本并不能完全填满下部空间，因此我们还需要设置对齐格式，即按照水平方向上居左的方式对齐。

控件下半部分的关键代码如下所示：

```
Widget buildBottomRow(BuildContext context) {
  return Padding(//Padding控件用来设置整体边距
    padding: EdgeInsets.fromLTRB(15,0,15,0),//左边距和右边距为15
    child: Column(//Column控件用来垂直摆放子Widget
      crossAxisAlignment: CrossAxisAlignment.start,//水平方向距左对齐
      children: <Widget>[
        Text(model.appDescription),//更新文案
        Padding(//Padding控件用来设置边距
          padding: EdgeInsets.fromLTRB(0,10,0,0),//上边距为10
          child: Text("${model.appVersion} • ${model.appSize} MB")
        )
      ]
  ));
}
```

最后，我们将上下两部分控件通过Column包装起来，这次升级项UI定制就完成了：

```
class UpdatedItem extends StatelessWidget {
  final UpdatedItemModel model;//数据模型
  //构造函数语法糖，用来给model赋值
  UpdatedItem({Key key,this.model, this.onPressed}) : super(key: key);
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return Column(//用Column将上下两部分合体
        children: <Widget>[
          buildTopRow(context),//上半部分
          buildBottomRow(context)//下半部分
        ]);
  }
  Widget buildBottomRow(BuildContext context) {...}
  Widget buildTopRow(BuildContext context) {...}
}
```

试着运行一下，效果如下所示：

![](https://static001.geekbang.org/resource/image/87/66/8737980f8b42caf33b77197a7a165f66.png?wh=828%2A1792)

图5 升级项UI运行示例

搞定！

**按照从上到下、从左到右去拆解UI的布局结构，把复杂的UI分解成各个小UI元素，在以组装的方式去自定义UI中非常有用，请一定记住这样的拆解方法。**

## 自绘

Flutter提供了非常丰富的控件和布局方式，使得我们可以通过组合去构建一个新的视图。但对于一些不规则的视图，用SDK提供的现有Widget组合可能无法实现，比如饼图，k线图等，这个时候我们就需要自己用画笔去绘制了。

在原生iOS和Android开发中，我们可以继承UIView/View，在drawRect/onDraw方法里进行绘制操作。其实，在Flutter中也有类似的方案，那就是CustomPaint。

**CustomPaint是用以承接自绘控件的容器，并不负责真正的绘制**。既然是绘制，那就需要用到画布与画笔。

在Flutter中，画布是Canvas，画笔则是Paint，而画成什么样子，则由定义了绘制逻辑的CustomPainter来控制。将CustomPainter设置给容器CustomPaint的painter属性，我们就完成了一个自绘控件的封装。

对于画笔Paint，我们可以配置它的各种属性，比如颜色、样式、粗细等；而画布Canvas，则提供了各种常见的绘制方法，比如画线drawLine、画矩形drawRect、画点DrawPoint、画路径drawPath、画圆drawCircle、画圆弧drawArc等。

这样，我们就可以在CustomPainter的paint方法里，通过Canvas与Paint的配合，实现定制化的绘制逻辑。

接下来，我们看一个例子。

在下面的代码中，我们继承了CustomPainter，在定义了绘制逻辑的paint方法中，通过Canvas的drawArc方法，用6种不同颜色的画笔依次画了6个1/6圆弧，拼成了一张饼图。最后，我们使用CustomPaint容器，将painter进行封装，就完成了饼图控件Cake的定义。

```
class WheelPainter extends CustomPainter {
 // 设置画笔颜色 
  Paint getColoredPaint(Color color) {//根据颜色返回不同的画笔
    Paint paint = Paint();//生成画笔
    paint.color = color;//设置画笔颜色
    return paint;
  }

  @override
  void paint(Canvas canvas, Size size) {//绘制逻辑
    double wheelSize = min(size.width,size.height)/2;//饼图的尺寸
    double nbElem = 6;//分成6份
    double radius = (2 * pi) / nbElem;//1/6圆
    //包裹饼图这个圆形的矩形框
    Rect boundingRect = Rect.fromCircle(center: Offset(wheelSize, wheelSize), radius: wheelSize);
    // 每次画1/6个圆弧
    canvas.drawArc(boundingRect, 0, radius, true, getColoredPaint(Colors.orange));
    canvas.drawArc(boundingRect, radius, radius, true, getColoredPaint(Colors.black38));
    canvas.drawArc(boundingRect, radius * 2, radius, true, getColoredPaint(Colors.green));
    canvas.drawArc(boundingRect, radius * 3, radius, true, getColoredPaint(Colors.red));
    canvas.drawArc(boundingRect, radius * 4, radius, true, getColoredPaint(Colors.blue));
    canvas.drawArc(boundingRect, radius * 5, radius, true, getColoredPaint(Colors.pink));
  }
  // 判断是否需要重绘，这里我们简单的做下比较即可
  @override
  bool shouldRepaint(CustomPainter oldDelegate) => oldDelegate != this;
}
//将饼图包装成一个新的控件
class Cake extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return CustomPaint(
        size: Size(200, 200),
        painter: WheelPainter(),
      );
  }
}
```

试着运行一下，效果如下所示：

![](https://static001.geekbang.org/resource/image/fb/84/fb03c4222e150a29a41d53a773b94984.png?wh=828%2A1792)

图6 自绘控件示例

可以看到，使用CustomPainter进行自绘控件并不算复杂。这里，我建议你试着用画笔和画布，去实现更丰富的功能。

**在实现视觉需求上，自绘需要自己亲自处理绘制逻辑，而组合则是通过子Widget的拼接来实现绘制意图。**因此从渲染逻辑处理上，自绘方案可以进行深度的渲染定制，从而实现少数通过组合很难实现的需求（比如饼图、k线图）。不过，当视觉效果需要调整时，采用自绘的方案可能需要大量修改绘制代码，而组合方案则相对简单：只要布局拆分设计合理，可以通过更换子Widget类型来轻松搞定。

## 总结

在面对一些复杂的UI视图时，Flutter提供的单一功能类控件往往不能直接满足我们的需求。于是，我们需要自定义Widget。Flutter提供了组装与自绘两种自定义Widget的方式，来满足我们对视图的自定义需求。

以组装的方式构建UI，我们需要将目标视图分解成各个UI小元素。通常，我们可以按照从上到下、从左到右的布局顺序去对控件层次结构进行拆解，将基本视觉元素封装到Column、Row中。对于有着固定间距的视觉元素，我们可以通过Padding对其进行包装，而对于大小伸缩可变的视觉元素，我们可以通过Expanded控件让其填充父容器的空白区域。

而以自绘的方式定义控件，则需要借助于CustomPaint容器，以及最终承接真实绘制逻辑的CustomPainter。CustomPainter是绘制逻辑的封装，在其paint方法中，我们可以使用不同类型的画笔Paint，利用画布Canvas提供的不同类型的绘制图形能力，实现控件自定义绘制。

无论是组合还是自绘，在自定义UI时，有了目标视图整体印象后，我们首先需要考虑的事情应该是如何将它化繁为简，把视觉元素拆解细分，变成自己立即可以着手去实现的一个小控件，然后再思考如何将这些小控件串联起来。把大问题拆成小问题后，实现目标也逐渐清晰，落地方案就自然浮出水面了。

这其实就和我们学习新知识的过程是一样的，在对整体知识概念有了初步认知之后，也需要具备将复杂的知识化繁为简的能力：先理清楚其逻辑脉络，然后再把不懂的知识拆成小点，最后逐个攻破。

我把今天分享讲的两个例子放到了[GitHub](https://github.com/cyndibaby905/15_custom_ui_demo)上，你可以下载后在工程中实际运行，并对照着今天的知识点进行学习，体会在不同场景下，组合和自绘这两种自定义Widget的具体使用方法。

## 思考题

最后，我给你留下两道作业题吧。

- 请扩展UpdatedItem控件，使其能自动折叠过长的更新文案，并能支持点击后展开的功能。

<!--THE END-->

![](https://static001.geekbang.org/resource/image/bf/bf/bf6c18f1f391a7f9999e21fdcaeff9bf.png?wh=1125%2A1068)

- 请扩展Cake控件，使其能够根据传入的double数组（最多10个元素）中数值的大小，定义饼图的圆弧大小。

欢迎你在评论区给我留言分享你的观点，我会在下一篇文章中等待你！感谢你的收听，也欢迎你把这篇文章分享给更多的朋友一起阅读。
<div><strong>精选留言（15）</strong></div><ul>
<li><span>吴小安</span> 👍（16） 💬（1）<p>大前端的界面不是提倡尽量减少图层的数量？这样一直嵌套下去图层似乎太多，这些布局的控件是不是不算图层？不参与渲染？</p>2019-08-01</li><br/><li><span>和小胖</span> 👍（12） 💬（4）<p>关于第二道思考题目的解决方法，请老师看一下：

&#47;&#47;绘制自定义view，其中画笔 paint ，画布 canvas，而 CustomPainter 负责具体的绘制逻辑处理
class WheelPainter extends CustomPainter {
  List&lt;double&gt; _list;
  List&lt;Color&gt; _listColor;
  double _total; &#47;&#47;总份数

  WheelPainter(this._list, this._listColor);

  @override
  void paint(Canvas canvas, Size size) {
    double wheelSize = min(size.width, size.height) &#47; 2; &#47;&#47;饼图的尺寸
    &#47;&#47;用一个矩形框来包裹饼图
    Rect boundingRect = Rect.fromCircle(
        center: Offset(wheelSize, wheelSize), radius: wheelSize);
    &#47;&#47;求出数组中所有数值的和
    _total = _list.reduce((value, element) =&gt; value + element);
    print(&quot;总份额是：$_total&quot;);
    &#47;&#47;求出每一份所占的角度
    double radius = (2 * pi) &#47; _total; &#47;&#47;求出每一份的弧度
    print(&quot;总角度是${2 * pi},每份额角度是:$radius&quot;);
    &#47;&#47;循环绘制每一份扇形
    for (int i = 0; i &lt; _list.length; i++) {
      &#47;&#47; 求出初始角度
      double startRadius;
      if (i == 0) {
        startRadius = 0;
      } else {
        startRadius =
            _list.sublist(0, i).reduce((value, element) =&gt; value + element) *
                radius;
      }
      &#47;&#47;求出滑过角度，即当前份额乘以每份所占角度
      double sweepRadius = radius * _list[i];
      print(&quot;起始角度：$startRadius,划过角度：$sweepRadius&quot;);

      &#47;&#47;&#47; 绘制扇形，第一个参数是绘制矩形所在的矩形，第二个参数是起始角度，第三个参数是矩形划过的角度
      &#47;&#47;&#47; 第三个参数代表扇形是否是实心，否则就只是绘制边框是空心的，最后一个参数是画笔
      canvas.drawArc(boundingRect, startRadius, sweepRadius, true,
          getPaintByColor(_listColor[i]));
    }
  }

  &#47;&#47;根据不同的 color 来获取对应的画笔
  Paint getPaintByColor(Color color) {
    Paint paint = Paint();
    paint.color = color;
    return paint;
  }

  &#47;&#47;判断是否需要重绘
  @override
  bool shouldRepaint(CustomPainter oldDelegate) =&gt; oldDelegate != this;
}

Padding getCustomPaint() {
  return Padding(
      padding: EdgeInsets.all(10),
      child: CustomPaint(
        size: Size(200, 200), 
        painter: WheelPainter(
            List.of([1.0, 2.0, 3.0, 4.0, 20]),
            List.of([
              Colors.red,
              Colors.blue,
              Colors.green,
              Colors.amber,
              Colors.black54
            ])),
      ));
}</p>2019-09-05</li><br/><li><span>wanggw</span> 👍（5） 💬（3）<p>功能算是差不多实现了，但是还存在一个核心的问题不知道应该解决，就是我怎么获取Text展示文本的行数，我需要行数才能控制 more 按钮的显示和隐藏，否则我默认超过2行显示 more 按钮，当文本只有1行的时候，more 按钮也显示了😂。暂时还没找到解决方案。这是我写的例子：https:&#47;&#47;github.com&#47;wanggw911&#47;flutter_hello&#47;blob&#47;master&#47;lib&#47;widget&#47;Listview02.dart</p>2019-08-22</li><br/><li><span>davidzhou</span> 👍（4） 💬（2）<p>我的思路这样，先自定义一个statefulwidget，里面用过一个变量控制两个text，因为text是statelesswidget，无法动态去刷新，一个widget设置Maxlines=2，另一个不设置，more是一个floatbutton，点击事件里面实现setstate改变先前定义的变量就行了</p>2019-08-01</li><br/><li><span>獸丶</span> 👍（3） 💬（1）<p>老师，Flutter代码规范方面会讲吗，如果代码全写在一个Dart文件里，有点太冗杂了，还是说遵循SRP，一个类一个Dart文件？</p>2019-08-02</li><br/><li><span>Geek_e7jq8k</span> 👍（2） 💬（3）<p>请问下，再混合开发的场景下,module类型的对于root Widget，我们必须使用MaterialApp或者CupertinoApp二选一么？如果不使用这两个基础的widgetApp，除了不能享受封装好的Theme、封装好的Widget组件这些便利外，是否有无法实现的基础功能（比如在iOS中的右滑返回等等）？ 同时想问下目前国内很多App在安卓上的表现都不是Material风格的，同时也不完全是Cupertino风格，所以在实际应用中，主流的做法是使用 MaterialApp&#47;CupertinoApp&#47;完全自定义 这三种的哪一种呢？以及在开发过程中的是否有什么弊端呢？</p>2019-10-08</li><br/><li><span>Neil 陈荣</span> 👍（1） 💬（2）<p>老师，我想绘制一个围棋游戏的棋盘，并在上面实现落子、提子等各种操作。大致估计了一下，如果用组合的方案，算上棋子，棋盘，各种线，至少会有接近400个 widget. 这种情况下性能会有问题吗？我想知道 widget 数量一般在多少以内采用组合不会出现性能问题，这个有没有一个指导性的最佳实践？如果一上来就用自绘的方案的话，担心各种操作的交互功能不容易实现。谢谢！</p>2019-12-11</li><br/><li><span>毛哥来了</span> 👍（1） 💬（3）<p>我是用Builder(builder: (Buildcontext context){})来创建description那个Text组件，然后就可以通过context.size.height获取Text的高度，然后就能判断按钮何时展示了</p>2019-10-24</li><br/><li><span>浣熊特工队</span> 👍（1） 💬（2）<p>请问老师，more按钮那里的左右渐隐是怎么实现的啊，我用TextOverflow.fade是向下渐隐的啊</p>2019-09-03</li><br/><li><span>🌙</span> 👍（1） 💬（1）<p>如果说尽量使用stateless，但是只要需要交互都必须是stateful吧？怎么尽量来使用成stateless呢？</p>2019-08-23</li><br/><li><span>楼外楼</span> 👍（1） 💬（1）<p>哪些算是非可视容器呢？</p>2019-08-10</li><br/><li><span>Simon</span> 👍（1） 💬（2）<p>老师，Flutter其中一个游戏引擎flame，也是通过自绘的方式实现的吗？</p>2019-08-01</li><br/><li><span>Captain</span> 👍（0） 💬（1）<p>老师，pi是在哪里定义的？</p>2019-11-18</li><br/><li><span>leslee</span> 👍（0） 💬（2）<p>老师我把你的案例跑起来了, 但是我把 我把计数器那个案列的代码里面的 MaterialApp 的 themeData 的 primaryColor 的颜色改成你的 ligjtblue[800] 后他报错, 报 type color is not a subtype of type materialcolor 我看了文档确实颜色是分好几个类型,   可是为什么你的可以运行我的不可以运行........</p>2019-10-21</li><br/><li><span>离尘不离人คิดถึง</span> 👍（0） 💬（1）<p>功能都实现了，抽象了一个有状态的组件：https:&#47;&#47;github.com&#47;lichenbuliren&#47;flutter_study&#47;blob&#47;master&#47;lib&#47;components&#47;appUpdateItemCard.dart；
基本思路：
1、用 Contaner  的 decoration 绘制一个圆角白色渐变的白底；
2、抽取 UI 组件，内部维护一个 『showMore』 状态
3、描述文本组件根据 『showMore』 来动态设置 『maxLines』属性值，并且设置 『overflow』为省略号
唯一存在的小瑕疵就是我的 FlatButton  控件中的文本一直存在 padding；手动设置了 0 也不生效；因为我看该章节里面的 『more』文本应该是靠右对齐的，这里麻烦老师帮忙看下，我尝试了各种方案都没法实现</p>2019-10-20</li><br/>
</ul>