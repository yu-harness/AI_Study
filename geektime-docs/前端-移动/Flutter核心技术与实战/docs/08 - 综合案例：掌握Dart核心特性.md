你好，我是陈航。

在前两篇文章中，我首先与你一起学习了Dart程序的基本结构和语法，认识了Dart语言世界的基本构成要素，也就是类型系统，以及它们是怎么表示信息的。然后，我带你学习了Dart面向对象设计的基本思路，知道了函数、类与运算符这些其他编程语言中常见的概念，在Dart中的差异及典型用法，理解了Dart是怎么处理信息的。

可以看到，Dart吸纳了其他编程语言的优点，在关于如何表达以及处理信息上，既简单又简洁，而且又不失强大。俗话说，纸上得来终觉浅，绝知此事要躬行。那么今天，我就用一个综合案例，把前面学习的关于Dart的零散知识串起来，希望你可以动手试验一下这个案例，借此掌握如何用Dart编程。

有了前面学习的知识点，再加上今天的综合案例练习，我认为你已经掌握了Dart最常用的80%的特性，可以在基本没有语言障碍的情况下去使用Flutter了。至于剩下的那20%的特性，因为使用较少，所以我不会在本专栏做重点讲解。如果你对这部分内容感兴趣的话，可以访问[官方文档](https://dart.dev/tutorials)去做进一步了解。

此外，关于Dart中的异步和并发，我会在后面的第23篇文章“单线程模型怎么保证UI运行流畅？”中进行深入介绍。

## 案例介绍

今天，我选择的案例是，先用Dart写一段购物车程序，但先不使用Dart独有的特性。然后，我们再以这段程序为起点，逐步加入Dart语言特性，将其改造为一个符合Dart设计思想的程序。你可以在这个改造过程中，进一步体会到Dart的魅力所在。

首先，我们来看看在不使用任何Dart语法特性的情况下，一个有着基本功能的购物车程序长什么样子。

```
//定义商品Item类
class Item {
  double price;
  String name;
  Item(name, price) {
    this.name = name;
    this.price = price;
  }
}

//定义购物车类
class ShoppingCart {
  String name;
  DateTime date;
  String code;
  List<Item> bookings;

  price() {
    double sum = 0.0;
    for(var i in bookings) {
      sum += i.price;
    }
    return sum;
  }

  ShoppingCart(name, code) {
    this.name = name;
    this.code = code;
    this.date = DateTime.now();
  }

  getInfo() {
    return '购物车信息:' +
          '\n-----------------------------' +
          '\n用户名: ' + name+ 
          '\n优惠码: ' + code + 
          '\n总价: ' + price().toString() +
          '\n日期: ' + date.toString() +
          '\n-----------------------------';
  }
}

void main() {
  ShoppingCart sc = ShoppingCart('张三', '123456');
  sc.bookings = [Item('苹果',10.0), Item('鸭梨',20.0)];
  print(sc.getInfo());
}
```

在这段程序中，我定义了商品Item类，以及购物车ShoppingCart类。它们分别包含了一个初始化构造方法，将main函数传入的参数信息赋值给对象内部属性。而购物车的基本信息，则通过ShoppingCart类中的getInfo方法输出。在这个方法中，我采用字符串拼接的方式，将各类信息进行格式化组合后，返回给调用者。

运行这段程序，不出意外，购物车对象sc包括的用户名、优惠码、总价与日期在内的基本信息都会被打印到命令行中。

```
购物车信息:
-----------------------------
用户名: 张三
优惠码: 123456
总价: 30.0
日期: 2019-06-01 17:17:57.004645
-----------------------------
```

这段程序的功能非常简单：我们初始化了一个购物车对象，然后给购物车对象进行加购操作，最后打印出基本信息。可以看到，在不使用Dart语法任何特性的情况下，这段代码与Java、C++甚至JavaScript没有明显的语法差异。

在关于如何表达以及处理信息上，Dart保持了既简单又简洁的风格。那接下来，**我们就先从表达信息入手，看看Dart是如何优化这段代码的。**

## 类抽象改造

我们先来看看Item类与ShoppingCart类的初始化部分。它们在构造函数中的初始化工作，仅仅是将main函数传入的参数进行属性赋值。

在其他编程语言中，在构造函数的函数体内，将初始化参数赋值给实例变量的方式非常常见。而在Dart里，我们可以利用语法糖以及初始化列表，来简化这样的赋值过程，从而直接省去构造函数的函数体：

```
class Item {
  double price;
  String name;
  Item(this.name, this.price);
}

class ShoppingCart {
  String name;
  DateTime date;
  String code;
  List<Item> bookings;
  price() {...}
  //删掉了构造函数函数体
  ShoppingCart(this.name, this.code) : date = DateTime.now();
...
}
```

这一下就省去了7行代码！通过这次改造，我们有两个新的发现：

- 首先，Item类与ShoppingCart类中都有一个name属性，在Item中表示商品名称，在ShoppingCart中则表示用户名；
- 然后，Item类中有一个price属性，ShoppingCart中有一个price方法，它们都表示当前的价格。

考虑到name属性与price属性（方法）的名称与类型完全一致，在信息表达上的作用也几乎一致，因此我可以在这两个类的基础上，再抽象出一个新的基类Meta，用于存放price属性与name属性。

同时，考虑到在ShoppingCart类中，price属性仅用做计算购物车中商品的价格（而不是像Item类那样用于数据存取），因此在继承了Meta类后，我改写了ShoppingCart类中price属性的get方法：

```
class Meta {
  double price;
  String name;
  Meta(this.name, this.price);
}
class Item extends Meta{
  Item(name, price) : super(name, price);
}

class ShoppingCart extends Meta{
  DateTime date;
  String code;
  List<Item> bookings;
  
  double get price {...}
  ShoppingCart(name, this.code) : date = DateTime.now(),super(name,0);
  getInfo() {...}
}
```

通过这次类抽象改造，程序中各个类的依赖关系变得更加清晰了。不过，目前这段程序中还有两个冗长的方法显得格格不入，即ShoppingCart类中计算价格的price属性get方法，以及提供购物车基本信息的getInfo方法。接下来，我们分别来改造这两个方法。

## 方法改造

我们先看看price属性的get方法：

```
double get price {
  double sum = 0.0;
  for(var i in bookings) {
    sum += i.price;
  }
  return sum;
} 
```

在这个方法里，我采用了其他语言常见的求和算法，依次遍历bookings列表中的Item对象，累积相加求和。

而在Dart中，这样的求和运算我们只需重载Item类的“+”运算符，并通过对列表对象进行归纳合并操作即可实现（你可以想象成，把购物车中的所有商品都合并成了一个商品套餐对象）。

另外，由于函数体只有一行，所以我们可以使用Dart的箭头函数来进一步简化实现函数：

```
class Item extends Meta{
  ...
  //重载了+运算符，合并商品为套餐商品
  Item operator+(Item item) => Item(name + item.name, price + item.price); 
}

class ShoppingCart extends Meta{
  ...
  //把迭代求和改写为归纳合并
  double get price => bookings.reduce((value, element) => value + element).price;
  ...
  getInfo() {...}
}
```

可以看到，这段代码又简洁了很多！接下来，我们再看看getInfo方法如何优化。

在getInfo方法中，我们将ShoppingCart类的基本信息通过字符串拼接的方式，进行格式化组合，这在其他编程语言中非常常见。而在Dart中，我们可以通过对字符串插入变量或表达式，并使用多行字符串声明的方式，来完全抛弃不优雅的字符串拼接，实现字符串格式化组合。

```
getInfo () => '''
购物车信息:
-----------------------------
  用户名: $name
  优惠码: $code
  总价: $price
  Date: $date
-----------------------------
''';
```

在去掉了多余的字符串转义和拼接代码后，getInfo方法看着就清晰多了。

在优化完了ShoppingCart类与Item类的内部实现后，我们再来看看main函数，从调用方的角度去分析程序还能在哪些方面做优化。

## 对象初始化方式的优化

在main函数中，我们使用

```
ShoppingCart sc = ShoppingCart('张三', '123456') ;
```

初始化了一个使用‘123456’优惠码、名为‘张三’的用户所使用的购物车对象。而这段初始化方法的调用，我们可以从两个方面优化：

- 首先，在对ShoppingCart的构造函数进行了大量简写后，我们希望能够提供给调用者更明确的初始化方法调用方式，让调用者以“参数名:参数键值对”的方式指定调用参数，让调用者明确传递的初始化参数的意义。在Dart中，这样的需求，我们在声明函数时，可以通过给参数增加{}实现。
- 其次，对一个购物车对象来说，一定会有一个有用户名，但不一定有优惠码的用户。因此，对于购物车对象的初始化，我们还需要提供一个不含优惠码的初始化方法，并且需要确定多个初始化方法与父类的初始化方法之间的正确调用顺序。

按照这样的思路，我们开始对ShoppingCart进行改造。

需要注意的是，由于优惠码可以为空，我们还需要对getInfo方法进行兼容处理。在这里，我用到了a??b运算符，这个运算符能够大量简化在其他语言中三元表达式(a != null)? a : b的写法：

```
class ShoppingCart extends Meta{
  ...
  //默认初始化方法，转发到withCode里
  ShoppingCart({name}) : this.withCode(name:name, code:null);
  //withCode初始化方法，使用语法糖和初始化列表进行赋值，并调用父类初始化方法
  ShoppingCart.withCode({name, this.code}) : date = DateTime.now(), super(name,0);

  //??运算符表示为code不为null，则用原值，否则使用默认值"没有"
  getInfo () => '''
购物车信息:
-----------------------------
  用户名: $name
  优惠码: ${code??"没有"}
  总价: $price
  Date: $date
-----------------------------
''';
}

void main() {
  ShoppingCart sc = ShoppingCart.withCode(name:'张三', code:'123456');
  sc.bookings = [Item('苹果',10.0), Item('鸭梨',20.0)];
  print(sc.getInfo());

  ShoppingCart sc2 = ShoppingCart(name:'李四');
  sc2.bookings = [Item('香蕉',15.0), Item('西瓜',40.0)];
  print(sc2.getInfo());
}
```

运行这段程序，张三和李四的购物车信息都会被打印到命令行中：

```
购物车信息:
-----------------------------
  用户名: 张三
  优惠码: 123456
  总价: 30.0
  Date: 2019-06-01 19:59:30.443817
-----------------------------

购物车信息:
-----------------------------
  用户名: 李四
  优惠码: 没有
  总价: 55.0
  Date: 2019-06-01 19:59:30.451747
-----------------------------
```

关于购物车信息的打印，我们是通过在main函数中获取到购物车对象的信息后，使用全局的print函数打印的，我们希望把打印信息的行为封装到ShoppingCart类中。而对于打印信息的行为而言，这是一个非常通用的功能，不止ShoppingCart类需要，Item对象也可能需要。

因此，我们需要把打印信息的能力单独封装成一个单独的类PrintHelper。但，ShoppingCart类本身已经继承自Meta类，考虑到Dart并不支持多继承，我们怎样才能实现PrintHelper类的复用呢？

这就用到了我在上一篇文章中提到的“混入”（Mixin），相信你还记得只要在使用时加上with关键字即可。

我们来试着增加PrintHelper类，并调整ShoppingCart的声明：

```
abstract class PrintHelper {
  printInfo() => print(getInfo());
  getInfo();
}

class ShoppingCart extends Meta with PrintHelper{
...
}
```

经过Mixin的改造，我们终于把所有购物车的行为都封装到ShoppingCart内部了。而对于调用方而言，还可以使用级联运算符“..”，在同一个对象上连续调用多个函数以及访问成员变量。使用级联操作符可以避免创建临时变量，让代码看起来更流畅：

```
void main() {
  ShoppingCart.withCode(name:'张三', code:'123456')
  ..bookings = [Item('苹果',10.0), Item('鸭梨',20.0)]
  ..printInfo();

  ShoppingCart(name:'李四')
  ..bookings = [Item('香蕉',15.0), Item('西瓜',40.0)]
  ..printInfo();
}
```

很好！通过Dart独有的语法特性，我们终于把这段购物车代码改造成了简洁、直接而又强大的Dart风格程序。

## 总结

这就是今天分享的全部内容了。在今天，我们以一个与Java、C++甚至JavaScript没有明显语法差异的购物车雏形为起步，逐步将它改造成了一个符合Dart设计思想的程序。

首先，我们使用构造函数语法糖及初始化列表，简化了成员变量的赋值过程。然后，我们重载了“+”运算符，并采用归纳合并的方式实现了价格计算，并且使用多行字符串和内嵌表达式的方式，省去了无谓的字符串拼接。最后，我们重新梳理了类之间的继承关系，通过mixin、多构造函数，可选命名参数等手段，优化了对象初始化调用方式。

下面是今天购物车综合案例的完整代码，希望你在IDE中多多练习，体会这次的改造过程，从而对Dart那些使代码变得更简洁、直接而强大的关键语法特性产生更深刻的印象。同时，改造前后的代码，你也可以在GitHub的[Dart\_Sample](https://github.com/cyndibaby905/08_Dart_Sample)中找到：

```
class Meta {
  double price;
  String name;
  //成员变量初始化语法糖
  Meta(this.name, this.price);
}

class Item extends Meta{
  Item(name, price) : super(name, price);
  //重载+运算符，将商品对象合并为套餐商品
  Item operator+(Item item) => Item(name + item.name, price + item.price); 
}

abstract class PrintHelper {
  printInfo() => print(getInfo());
  getInfo();
}

//with表示以非继承的方式复用了另一个类的成员变量及函数
class ShoppingCart extends Meta with PrintHelper{
  DateTime date;
  String code;
  List<Item> bookings;
  //以归纳合并方式求和
  double get price => bookings.reduce((value, element) => value + element).price;
  //默认初始化函数，转发至withCode函数
  ShoppingCart({name}) : this.withCode(name:name, code:null);
  //withCode初始化方法，使用语法糖和初始化列表进行赋值，并调用父类初始化方法
  ShoppingCart.withCode({name, this.code}) : date = DateTime.now(), super(name,0);

  //??运算符表示为code不为null，则用原值，否则使用默认值"没有"
  @override
  getInfo() => '''
购物车信息:
-----------------------------
  用户名: $name
  优惠码: ${code??"没有"}
  总价: $price
  Date: $date
-----------------------------
''';
}

void main() {
  ShoppingCart.withCode(name:'张三', code:'123456')
  ..bookings = [Item('苹果',10.0), Item('鸭梨',20.0)]
  ..printInfo();

  ShoppingCart(name:'李四')
  ..bookings = [Item('香蕉',15.0), Item('西瓜',40.0)]
  ..printInfo();
}
```

## 思考题

请你扩展购物车程序的实现，使得我们的购物车可以支持：

1. 商品数量属性；
2. 购物车信息增加商品列表信息（包括商品名称，数量及单价）输出，实现小票的基本功能。

欢迎你在评论区给我留言分享你的观点，我会在下一篇文章中等待你！感谢你的收听，也欢迎你把这篇文章分享给更多的朋友一起阅读。
<div><strong>精选留言（15）</strong></div><ul>
<li><span>relax</span> 👍（4） 💬（3）<p>能不能所有的示例代码放到一个git下面</p>2019-08-14</li><br/><li><span>Ω</span> 👍（36） 💬（3）<p>Item operator+(Item item) =&gt; I...
double get price =&gt; bookings...

这个改造+号的代码还是无法看懂
</p>2019-07-16</li><br/><li><span>bytecode</span> 👍（13） 💬（1）<p>double get price() {
  double sum = 0.0;
  for(var i in bookings) {
    sum += i.price;
  }
  return sum;
} 

文中这里的price()是多了括号()，要去掉()</p>2019-07-16</li><br/><li><span>jia58960</span> 👍（10） 💬（2）<p>大概能看懂并实现代码，但构造函数中的属性什么时候用this.属性，什么时候不用this，希望老师能回答下。</p>2019-07-24</li><br/><li><span>灰灰</span> 👍（5） 💬（2）<p>abstract class PrintHelper {
  printInfo() =&gt; print(getInfo());
  getInfo();
}

class Meta {
  double price;
  String name;
  Meta(this.name, this.price);
}

&#47;&#47; 定义商品Item类
class Item extends Meta {
  int count;
  Item(name, price, this.count): super(name, price);
  Item operator+(Item item) =&gt; Item(name + item.name, price * count + (item.price * item.count), 1);
}

&#47;&#47;定义购物车类
class ShoppingCart extends Meta with PrintHelper {
  DateTime date;
  String code;
  List&lt;Item&gt; bookings;

  double get price =&gt; bookings.reduce((value, element) =&gt; (value + element)).price;
&#47;&#47;  ShoppingCart(name, this.code): date = DateTime.now(), super(name,0);
  ShoppingCart({name}): this.withCode(name: name, code: null);
  ShoppingCart.withCode({name, this.code}): date = DateTime.now(), super(name, 0);
  getInfo () =&gt; &#39;&#39;&#39;
     购物车信息:
     
     ----------------
     商品名    单价    数量    总价
     ----------------
     ${bookings.map((item) =&gt; &#39;${item.name}  ${item.price}  ${item.count}  ${item.price * item.count}&#39;).join(&#39;\n     &#39;)}
     
     ================
     用户名： $name
     优惠码： ${code ?? &quot;没有&quot;}
     总价： $price
     日期： $date
  &#39;&#39;&#39;;
}

void main() {
  ShoppingCart.withCode(name: &#39;张三&#39;, code: &#39;123456&#39;)
  ..bookings = [Item(&#39;苹果&#39;, 10.0, 3), Item(&#39;鸭梨&#39;, 20.0, 1)]
  ..printInfo();

  ShoppingCart(name: &#39;李四&#39;)
  ..bookings = [Item(&#39;香蕉&#39;, 2.4, 2), Item(&#39;芒果&#39;, 6.8, 4)]
  ..printInfo();
}</p>2019-07-27</li><br/><li><span>Uncle.Wang</span> 👍（3） 💬（1）<p>class Meta {
  double price;
  String name;
  &#47;&#47; 成员变量初始化语法糖
  Meta(this.name, this.price);
}

abstract class PrintHelper {
  printInfo() =&gt; print(getInfo());
  getInfo();
}

class Item extends Meta with PrintHelper {
  int count;
  Item(name, price, {int count = 1}): super(name, price) {
    this.count = count;
  }
  &#47;&#47; 重载 + 运算符，将商品对象合并为套餐商品
  Item operator+(Item item) =&gt; Item(name + item.name, price + item.price); 
    @override
  getInfo() =&gt; &#39;&#39;&#39;
    商品名: $name
    单价: $price
    数量: $count
    ---------------
&#39;&#39;&#39;;
}

&#47;&#47;with 表示以非继承的方式复用了另一个类的成员变量及函数
class ShoppingCart extends Meta with PrintHelper{
  DateTime date;
  String code;
  List&lt;Item&gt; bookings;
  &#47;&#47; 以归纳合并方式求和
  double get price =&gt; bookings.reduce((value, element) =&gt; value + element).price;
  &#47;&#47; 默认初始化函数，转发至 withCode 函数
  ShoppingCart({name}) : this.withCode(name:name, code:null);
  &#47;&#47;withCode 初始化方法，使用语法糖和初始化列表进行赋值，并调用父类初始化方法
  ShoppingCart.withCode({name, this.code}) : date = DateTime.now(), super(name,0);

  getBookingInfo() {
    String str = &quot;&quot;;
    for (Item item in bookings) {
      str += item.getInfo();
    }
    return str;
  }

  &#47;&#47;?? 运算符表示为 code 不为 null，则用原值，否则使用默认值 &quot; 没有 &quot;
  @override
  getInfo() =&gt; &#39;&#39;&#39;
购物车信息:
-----------------------------
  用户名: $name
  优惠码: ${code??&quot; 没有 &quot;}
  总价: $price
  Date: $date
  商品列表：
    ---------------
${ getBookingInfo() }
-----------------------------
&#39;&#39;&#39;;
}

void main() {
  ShoppingCart.withCode(name:&#39;张三&#39;, code:&#39;123456&#39;)
  ..bookings = [Item(&#39;苹果&#39;,10.0, count: 10), Item(&#39;鸭梨&#39;,20.0, count: 5)]
  ..printInfo();

  ShoppingCart(name:&#39;李四&#39;)
  ..bookings = [Item(&#39;香蕉&#39;,15.0), Item(&#39;西瓜&#39;,40.0)]
  ..printInfo();
}
</p>2019-08-20</li><br/><li><span>江宁彭于晏</span> 👍（3） 💬（1）<p>class Meta {
  double price;
  String name;
  &#47;&#47; 成员变量初始化语法糖
  Meta(this.name, this.price);
}

class Item extends Meta{
  Item(name, price) : super(name, price);
  &#47;&#47; 重载 + 运算符，将商品对象合并为套餐商品
  Item operator+(Item item) =&gt; Item(name + item.name, price + item.price); 
}

class Items {
  Item item;
  double num;
  Items(this.item, this.num);
  double get totalPrice =&gt; item.price * num; 
}

abstract class PrintHelper {
  printInfo() =&gt; print(getInfo());
  getInfo();
}

&#47;&#47;with 表示以非继承的方式复用了另一个类的成员变量及函数
class ShoppingCart extends Meta with PrintHelper{
  DateTime date;
  String code;
  List&lt;Items&gt; bookings;
  &#47;&#47; 以归纳合并方式求和
  double get shopPrice {
     double result = 0.0;
     bookings.forEach((element) =&gt; result+=element.totalPrice);
     return result;
  }

  &#47;&#47; 默认初始化函数，转发至 withCode 函数
  ShoppingCart({name}) : this.withCode(name:name, code:null);
  &#47;&#47;withCode 初始化方法，使用语法糖和初始化列表进行赋值，并调用父类初始化方法
  ShoppingCart.withCode({name, this.code}) : date = DateTime.now(), super(name,0);

  &#47;&#47;?? 运算符表示为 code 不为 null，则用原值，否则使用默认值 &quot; 没有 &quot;
  @override
  String getInfo() {
  String bookingsResult = &#39;商品明细: \n&#39;;
  bookings.forEach((item) =&gt; bookingsResult += &#39;  商品名称：${item.item.name}  单价：${item.item.price} 数量 ：${item.num}  总价：${item.totalPrice}\n&#39;);

  return &#39;&#39;&#39;
购物车信息:
-----------------------------
  用户名: $name
  优惠码: ${code??&quot; 没有 &quot;}
  $bookingsResult
  总价: $shopPrice
  Date: $date
-----------------------------
&#39;&#39;&#39;;
  }
}

void main() {
  ShoppingCart.withCode(name:&#39;张三&#39;, code:&#39;123456&#39;)
  ..bookings = [Items(Item(&#39;苹果&#39;,10.0),5.0), Items(Item(&#39;鸭梨&#39;,20.0),10.0)]
  ..printInfo();

  ShoppingCart(name:&#39;李四&#39;)
  ..bookings = [Items(Item(&#39;香蕉&#39;,15.0),10.0), Items(Item(&#39;西瓜&#39;,40.0),1.0)]
  ..printInfo();
}
</p>2019-07-19</li><br/><li><span>Carlo</span> 👍（1） 💬（1）<p>看到一段代码：
firebaseService.login().then(
                        (value) {
                          print(value.toJson());
                        },
                        onError: (err) {
                          print(err);
                        },
                      );

请问这个onError是怎么回事啊。为什么会被执行呢？  这是dart特有的语法么？
我所知道的一般sync function的语法是

thisFunction()
    .catch(console.error)
    .then(() =&gt; console.log(&#39;We do cleanup here&#39;));</p>2019-10-15</li><br/><li><span>和小胖</span> 👍（1） 💬（1）<p>老师您的第二个题目，我理解是要做每一种商品的分类，但是我还是用了以前语言的思路来做了。麻烦老师，看看是否正确。

关键代码如下：
&#47;&#47;定义购物车类
class ShoppingCar extends Meta with PrintHelper {
  DateTime date; &#47;&#47;购物日期
  String code; &#47;&#47;优惠券
  List&lt;Item&gt; _bookings; &#47;&#47;定义私有属性
  num count; &#47;&#47;商品数量

  &#47;&#47;求出总价
  double get price =&gt;
      books.reduce((value, element) =&gt; value + element).price;

  List&lt;Item&gt; get books =&gt; _bookings;

  &#47;&#47;给bookings定义set方法
  set book(List&lt;Item&gt; bookings) {
    this._bookings = bookings;
    this.count = bookings.length;
  }

  &#47;&#47;获取分类产品信息
  String getGoodsInfo() {
    StringBuffer temp = new StringBuffer();
    Map map = new Map&lt;String, List&lt;Item&gt;&gt;();
    books.forEach((item) {
      if (!map.containsKey(item.name)) {
        List list = new List&lt;Item&gt;();
        list.add(item);
        map[item.name] = list;
      } else {
        (map[item.name] as List&lt;Item&gt;).add(item);
      }
    });
    map.forEach((k, v) {
      temp.write(&quot;商品名称：$k,该种商品数量：${(v as List).length},该种商品单价：${(v as List&lt;Item&gt;)[0].price}元\n&quot;);
      print(&quot;$k,$v&quot;);
    });
    return temp.toString();
  }

  &#47;&#47;这种表达式赋值还是挺方便的
  ShoppingCar.withCode({name, this.code}): this.date = DateTime.now(),super(name, 0.0);

  ShoppingCar({name}) : this.withCode(name: name, code: null);

  @override
  getInfo() {
    return &#39;&#39;&#39;
      购物车信息：
      ----------------------
      用户名：$name
      优惠码：${code ?? &quot;没有优惠券啊&quot;}
      商品总量：$count
      总价：$price  
      日期：$date
      ${getGoodsInfo()}
      ----------------------
  &#39;&#39;&#39;;
  }
}

运行后信息如下：购物车信息：
      ----------------------
      用户名：小李
      优惠码：没有优惠券啊
      商品总量：3
      总价：29.0  
      日期：2019-08-14 22:01:24.437085
      商品名称：苹果,该种商品数量：2,该种商品单价：10.0元
      商品名称：梨,该种商品数量：1,该种商品单价：9.0元
      ----------------------</p>2019-08-14</li><br/><li><span>刘荣清</span> 👍（1） 💬（1）<p>在vs code已经安装dart、code runner插件，本地也安装完dart SDK，然后通过vs code运行dart 提示：dart : 无法将“dart”项识别为 cmdlet、函数...
但在cmd 控制板中就可以正常运行，这是为咋啊，vs code需要额外配置咋吗</p>2019-08-03</li><br/><li><span>加温后的啤酒</span> 👍（0） 💬（1）<p>直接通过mixin关键字定义PrintHelper也比较简单：
mixin  PrintHelper {
  void printInfo() =&gt; print(getInfo());
  String getInfo();
}

</p>2019-12-23</li><br/><li><span>庆</span> 👍（0） 💬（1）<p>
class Meta {
  double price;
  String name;
  &#47;&#47;成员变量初始化语法糖
  Meta(this.name, this.price);
}

class Item extends Meta{
  Item(name, price) : super(name, price);
  &#47;&#47;重载+运算符，将商品对象合并为套餐商品
  Item operator+(Item item) =&gt; Item(name + item.name, price + item.price); 
}

abstract class PrintHelper {
  printInfo() =&gt; print(getInfo());
  getInfo();
}

&#47;&#47;with表示以非继承的方式复用了另一个类的成员变量及函数
class ShoppingCart extends Meta with PrintHelper{
  DateTime date;
  String code;
  List&lt;Item&gt; bookings;
  &#47;&#47;以归纳合并方式求和
  double get price =&gt; bookings.reduce((value, element) =&gt; value + element).price;
  &#47;&#47;默认初始化函数，转发至withCode函数
  ShoppingCart({name}) : this.withCode(name:name, code:null);
  &#47;&#47;withCode初始化方法，使用语法糖和初始化列表进行赋值，并调用父类初始化方法
  ShoppingCart.withCode({name, this.code}) : date = DateTime.now(), super(name,0);

  &#47;&#47;??运算符表示为code不为null，则用原值，否则使用默认值&quot;没有&quot;
  @override
  getInfo() =&gt; &#39;&#39;&#39;
购物车信息:
-----------------------------
  用户名: $name
  优惠码: ${code??&quot;没有&quot;}
  总价: $price
  Date: $date
  物品数量: ${bookings.length}
&#39;&#39;&#39;;

printDetails(){
   bookings.forEach((item){
     print(&quot;物品 &quot;+item.name + &quot; 价格 ${item.price}&quot;);
   });

   print(&quot;-----------------------------&quot;);

}

}

void main() {
  ShoppingCart.withCode(name:&#39;张三&#39;, code:&#39;123456&#39;)
  ..bookings = [Item(&#39;苹果&#39;,10.0), Item(&#39;鸭梨&#39;,20.0)]
  ..printInfo()
  ..printDetails();

  ShoppingCart(name:&#39;李四&#39;)
  ..bookings = [Item(&#39;香蕉&#39;,15.0), Item(&#39;西瓜&#39;,40.0)]
  ..printInfo()
  ..printDetails();
}</p>2019-12-23</li><br/><li><span>DERUWE</span> 👍（0） 💬（1）<p>使用了这个Item operator+(Item item) =&gt; Item(name + item.name, price + item.price);最后的bookings就变为长度为1的吗</p>2019-12-09</li><br/><li><span>icer</span> 👍（0） 💬（1）<p>class Meta {
  double price;
  String name;
  Meta(this.name,this.price);
}

class Item2 extends Meta {
  int num;
  Item2(String name, double price,{this.num=1}) :super(name, price);
  Item2 operator + (Item2 item) =&gt; Item2(name + item.name,price * num + item.price * item.num);
}

abstract class printHelper {
  printInfo() =&gt; print(getInfo());
  getInfo();
}

class ShoppingCart2 extends Meta with printHelper {
  DateTime date;
  String code;
  List&lt;Item2&gt; bookings;

  ShoppingCart2({name}) : this.withCode(name:name,code:null);
  ShoppingCart2.withCode({name,this.code}) : date = DateTime.now(),super(name, 0);

  double get price =&gt; bookings.reduce((value,element) =&gt; value + element).price;

  String get cardInfo {
    String str = &quot;&quot;;
    bookings.forEach((v) =&gt;
    str +=&#39;${v.name} ----- ${v.num}\n&#39;);
    return str;
  }

  getInfo() {
    return
          &quot;&quot;&quot;
        购物车信息:
        -----------------------------
        用户名: $name
        优惠码: ${code??&quot;没有&quot;}
        $cardInfo
        总价:   $price
        日期:   $date
        -----------------------------
        &quot;&quot;&quot;;
  }
</p>2019-11-19</li><br/><li><span>入夜、渐微凉</span> 👍（0） 💬（1）<p>在一个道友的回答上稍加改动，加了一个商品总数和购物车为空的情况，老师帮忙看看有没有可以优化的地方。
class Meta {
  double price;
  String name;
  String info;
  &#47;&#47;成员变量初始化语法糖
  Meta(this.name, this.price);
}
class Item extends Meta {
  int count;
  Item(name, price, {int count = 1}) : super(name, price) {
    this.count = count;
    this.info = &#39;&#39;&#39;
 商品名: $name
   单价: $price
   数量: $count
   ---------------
  &#39;&#39;&#39;;
  }
  
  Item operator +(Item item) =&gt;
      Item(name + item.name, price + item.price, count: count + item.count);
}

abstract class PrintHelper {
  printInfo() =&gt; print(getInfo());
  getInfo();
}

&#47;&#47;with表示以非继承的方式复用了另一个类的成员变量及函数
class ShoppingCart extends Meta with PrintHelper {
  DateTime date;
  String code;
  List&lt;Item&gt; bookings;
  &#47;&#47;以归纳合并方式求和
  double get price =&gt;bookings != null ?
      bookings.reduce((value, element) =&gt; value + element).price : 0.00;
  int get count =&gt; bookings != null ? bookings.reduce((value, element) =&gt; value + element).count : 0;
  &#47;&#47;默认初始化函数，转发至withCode函数
  ShoppingCart({name, List&lt;Item&gt; bookings})
      : this.withCode(name: name, code: null, bookings: bookings);
  &#47;&#47;withCode初始化方法，使用语法糖和初始化列表进行赋值，并调用父类初始化方法
  ShoppingCart.withCode({name, this.code, this.bookings})
      : date = DateTime.now(),
        super(name, 0) {
        if (bookings != null) {
            String str = &quot;&quot;;
            for (Item item in bookings) {
              str += item.info;
            }
            info = str;
        }
  }

  &#47;&#47;??运算符表示为code不为null，则用原值，否则使用默认值&quot;没有&quot;
  @override
  getInfo() =&gt; &#39;&#39;&#39;
购物车信息:
-----------------------------
  用户名: $name
  优惠码: ${code ?? &quot;没有&quot;}
  商品总数: $count
  总价: $price
  Date: $date
  商品列表: 
  ${info ?? &quot;购物车为空&quot;}
-----------------------------
&#39;&#39;&#39;;
}

void main() {
  ShoppingCart.withCode(
      name: &#39;张三&#39;,
      code: &#39;123456&#39;,
      bookings: [Item(&#39;苹果&#39;, 10.0, count: 1), Item(&#39;鸭梨&#39;, 20.0, count: 2)])
    ..printInfo();

  ShoppingCart(
      name: &#39;李四&#39;, bookings: [Item(&#39;香蕉&#39;, 15.0), Item(&#39;西瓜&#39;, 40.0, count: 4)])
    ..printInfo();

  ShoppingCart(name: &#39;王五&#39;)..printInfo();
}</p>2019-11-07</li><br/>
</ul>