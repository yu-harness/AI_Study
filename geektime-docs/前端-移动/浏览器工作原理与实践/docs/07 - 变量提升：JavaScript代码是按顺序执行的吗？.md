讲解完宏观视角下的浏览器后，从这篇文章开始，我们就进入下一个新的模块了，这里我会对JavaScript执行原理做深入介绍。

今天在该模块的第一篇文章，我们主要讲解**执行上下文**相关的内容。那为什么先讲执行上下文呢？它这么重要吗？可以这么说，**只有理解了JavaScrip的执行上下文，你才能更好地理解JavaScript语言本身**，比如变量提升、作用域和闭包等。不仅如此，理解执行上下文和调用栈的概念还能助你成为一名更合格的前端开发者。

不过由于我们专栏不是专门讲JavaScript语言的，所以我并不会对JavaScript语法本身做过多介绍。本文主要是从JavaScript的顺序执行讲起，然后**一步步带你了解JavaScript是怎么运行的**。

接下来咱们先看段代码，你觉得下面这段代码输出的结果是什么？

```
showName()
console.log(myname)
var myname = '极客时间'
function showName() {
    console.log('函数showName被执行');
}
```

使用过JavaScript开发的程序员应该都知道，JavaScript是按顺序执行的。若按照这个逻辑来理解的话，那么：

- 当执行到第1行的时候，由于函数showName还没有定义，所以执行应该会报错；
- 同样执行第2行的时候，由于变量myname也未定义，所以同样也会报错。

然而实际执行结果却并非如此， 如下图：

![](https://static001.geekbang.org/resource/image/fb/03/fbafaba4ad7092cbee011a8a02e38903.png?wh=722%2A414)

在声明之前使用函数和变量的执行结果

第1行输出“函数showName被执行”，第2行输出“undefined”，这和前面想象中的顺序执行有点不一样啊！

通过上面的执行结果，你应该已经知道了函数或者变量可以在定义之前使用，那如果使用没有定义的变量或者函数，JavaScript代码还能继续执行吗？为了验证这点，我们可以删除第3行变量myname的定义，如下所示：

```
showName()
console.log(myname)
function showName() {
    console.log('函数showName被执行');
}
```

然后再次执行这段代码时，JavaScript引擎就会报错，结果如下：

![](https://static001.geekbang.org/resource/image/a5/c2/a5262e2ca891ea114dfaf1e37f9ca4c2.png?wh=1142%2A73)

使用了未定义的变量——执行报错

从上面两段代码的执行结果来看，我们可以得出如下三个结论。

1. 在执行过程中，若使用了未声明的变量，那么JavaScript执行会报错。
2. 在一个变量定义之前使用它，不会出错，但是该变量的值会为undefined，而不是定义时的值。
3. 在一个函数定义之前使用它，不会出错，且函数能正确执行。

第一个结论很好理解，因为变量没有定义，这样在执行JavaScript代码时，就找不到该变量，所以JavaScript会抛出错误。

但是对于第二个和第三个结论，就挺让人费解的：

- 变量和函数为什么能在其定义之前使用？这似乎表明JavaScript代码并不是一行一行执行的。
- 同样的方式，变量和函数的处理结果为什么不一样？比如上面的执行结果，提前使用的showName函数能打印出来完整结果，但是提前使用的myname变量值却是undefined，而不是定义时使用的“极客时间”这个值。

## 变量提升（Hoisting）

要解释这两个问题，你就需要先了解下什么是变量提升。

不过在介绍变量提升之前，我们先通过下面这段代码，来看看什么是JavaScript中的**声明**和**赋值**。

```
var myname = '极客时间'
```

这段代码你可以把它看成是两行代码组成的：

```
var myname    //声明部分
myname = '极客时间'  //赋值部分
```

如下图所示：

![](https://static001.geekbang.org/resource/image/ec/3c/ec882f2d9deec26ce168b409f274533c.png?wh=1142%2A439)

如何理解\`var myname = '极客时间'\`

上面是**变量**的声明和赋值，那接下来我们再来看看**函数**的声明和赋值，结合下面这段代码：

```
function foo(){
  console.log('foo')
}

var bar = function(){
  console.log('bar')
}
```

第一个函数foo是一个完整的函数声明，也就是说没有涉及到赋值操作；第二个函数是先声明变量bar，再把`function(){console.log('bar')}`赋值给bar。为了直观理解，你可以参考下图：

![](https://static001.geekbang.org/resource/image/61/77/611c09ab995b9b608d9c0db193266777.png?wh=1142%2A648)

函数的声明和赋值

好了，理解了声明和赋值操作，那接下来我们就可以聊聊什么是变量提升了。

**所谓的变量提升，是指在JavaScript代码执行过程中，JavaScript引擎把变量的声明部分和函数的声明部分提升到代码开头的“行为”。变量被提升后，会给变量设置默认值，这个默认值就是我们熟悉的undefined。**

下面我们来模拟下实现：

```
/*
* 变量提升部分
*/
// 把变量 myname提升到开头，
// 同时给myname赋值为undefined
var myname = undefined
// 把函数showName提升到开头
function showName() {
    console.log('showName被调用');
}

/*
* 可执行代码部分
*/
showName()
console.log(myname)
// 去掉var声明部分，保留赋值语句
myname = '极客时间'
```

为了模拟变量提升的效果，我们对代码做了以下调整，如下图：

![](https://static001.geekbang.org/resource/image/ce/d5/cefe564dbff729e735a834fd9e3bd0d5.png?wh=1142%2A528)

模拟变量提升示意图

从图中可以看出，对原来的代码主要做了两处调整：

- 第一处是把声明的部分都提升到了代码开头，如变量myname和函数showName，并给变量设置默认值undefined；
- 第二处是移除原本声明的变量和函数，如`var myname = '极客时间'`的语句，移除了var声明，整个移除showName的函数声明。

通过这两步，就可以实现变量提升的效果。你也可以执行这段模拟变量提升的代码，其输出结果和第一段代码应该是完全一样的。

通过这段模拟的变量提升代码，相信你已经明白了可以在定义之前使用变量或者函数的原因——**函数和变量在执行之前都提升到了代码开头**。

## JavaScript代码的执行流程

从概念的字面意义上来看，“变量提升”意味着变量和函数的声明会在物理层面移动到代码的最前面，正如我们所模拟的那样。但，这并不准确。**实际上变量和函数声明在代码里的位置是不会改变的，而且是在编译阶段被JavaScript引擎放入内存中**。对，你没听错，一段JavaScript代码在执行之前需要被JavaScript引擎编译，**编译**完成之后，才会进入**执行**阶段。大致流程你可以参考下图：

![](https://static001.geekbang.org/resource/image/64/1e/649c6e3b5509ffd40e13ce9c91b3d91e.png?wh=1142%2A203)

JavaScript的执行流程图

### 1. 编译阶段

那么编译阶段和变量提升存在什么关系呢？

为了搞清楚这个问题，我们还是回过头来看上面那段模拟变量提升的代码，为了方便介绍，可以把这段代码分成两部分。

**第一部分：变量提升部分的代码。**

```
var myname = undefined
function showName() {
    console.log('函数showName被执行');
}
```

**第二部分：执行部分的代码。**

```
showName()
console.log(myname)
myname = '极客时间'
```

下面我们就可以把JavaScript的执行流程细化，如下图所示：

![](https://static001.geekbang.org/resource/image/06/13/0655d18ec347a95dfbf843969a921a13.png?wh=1142%2A634)

JavaScript执行流程细化图

从上图可以看出，输入一段代码，经过编译后，会生成两部分内容：**执行上下文（Execution context）和可执行代码**。

**执行上下文是JavaScript执行一段代码时的运行环境**，比如调用一个函数，就会进入这个函数的执行上下文，确定该函数在执行期间用到的诸如this、变量、对象以及函数等。

关于执行上下文的细节，我会在下一篇文章《08 | 调用栈：为什么JavaScript代码会出现栈溢出？》做详细介绍，现在你只需要知道，在执行上下文中存在一个**变量环境的对象**（Viriable Environment），该对象中保存了变量提升的内容，比如上面代码中的变量myname和函数showName，都保存在该对象中。

你可以简单地把变量环境对象看成是如下结构：

```
VariableEnvironment:
     myname -> undefined, 
     showName ->function : {console.log(myname)
```

了解完变量环境对象的结构后，接下来，我们再结合下面这段代码来分析下是如何生成变量环境对象的。

```
showName()
console.log(myname)
var myname = '极客时间'
function showName() {
    console.log('函数showName被执行');
}
```

我们可以一行一行来分析上述代码：

- 第1行和第2行，由于这两行代码不是声明操作，所以JavaScript引擎不会做任何处理；
- 第3行，由于这行是经过var声明的，因此JavaScript引擎将在环境对象中创建一个名为myname的属性，并使用undefined对其初始化；
- 第4行，JavaScript引擎发现了一个通过function定义的函数，所以它将函数定义存储到堆(HEAP）中，并在环境对象中创建一个showName的属性，然后将该属性值指向堆中函数的位置（不了解堆也没关系，JavaScript的执行堆和执行栈我会在后续文章中介绍）。

这样就生成了变量环境对象。接下来JavaScript引擎会把声明以外的代码编译为字节码，至于字节码的细节，我也会在后面文章中做详细介绍，你可以类比如下的模拟代码：

```
showName()
console.log(myname)
myname = '极客时间'
```

好了，现在有了执行上下文和可执行代码了，那么接下来就到了执行阶段了。

### 2. 执行阶段

JavaScript引擎开始执行“可执行代码”，按照顺序一行一行地执行。下面我们就来一行一行分析下这个执行过程：

- 当执行到showName函数时，JavaScript引擎便开始在变量环境对象中查找该函数，由于变量环境对象中存在该函数的引用，所以JavaScript引擎便开始执行该函数，并输出“函数showName被执行”结果。
- 接下来打印“myname”信息，JavaScript引擎继续在变量环境对象中查找该对象，由于变量环境存在myname变量，并且其值为undefined，所以这时候就输出undefined。
- 接下来执行第3行，把“极客时间”赋给myname变量，赋值后变量环境中的myname属性值改变为“极客时间”，变量环境如下所示：

```
VariableEnvironment:
     myname -> "极客时间", 
     showName ->function : {console.log(myname)
```

好了，以上就是一段代码的编译和执行流程。实际上，编译阶段和执行阶段都是非常复杂的，包括了词法分析、语法解析、代码优化、代码生成等，这些内容我会在《14 | 编译器和解释器：V8是如何执行一段JavaScript代码的？》那节详细介绍，在本篇文章中你只需要知道JavaScript代码经过编译生成了什么内容就可以了。

## 代码中出现相同的变量或者函数怎么办？

现在你已经知道了，在执行一段JavaScript代码之前，会编译代码，并将代码中的函数和变量保存到执行上下文的变量环境中，那么如果代码中出现了重名的函数或者变量，JavaScript引擎会如何处理？

我们先看下面这样一段代码：

```
function showName() {
    console.log('极客邦');
}
showName();
function showName() {
    console.log('极客时间');
}
showName(); 
```

在上面代码中，我们先定义了一个showName的函数，该函数打印出来“极客邦”；然后调用showName，并定义了一个showName函数，这个showName函数打印出来的是“极客时间”；最后接着继续调用showName。那么你能分析出来这两次调用打印出来的值是什么吗？

我们来分析下其完整执行流程：

- **首先是编译阶段**。遇到了第一个showName函数，会将该函数体存放到变量环境中。接下来是第二个showName函数，继续存放至变量环境中，但是变量环境中已经存在一个showName函数了，此时，**第二个showName函数会将第一个showName函数覆盖掉**。这样变量环境中就只存在第二个showName函数了。
- **接下来是执行阶段**。先执行第一个showName函数，但由于是从变量环境中查找showName函数，而变量环境中只保存了第二个showName函数，所以最终调用的是第二个函数，打印的内容是“极客时间”。第二次执行showName函数也是走同样的流程，所以输出的结果也是“极客时间”。

综上所述，**一段代码如果定义了两个相同名字的函数，那么最终生效的是最后一个函数**。

## 总结

好了，今天就到这里，下面我来简单总结下今天的主要内容：

- JavaScript代码执行过程中，需要先做**变量提升**，而之所以需要实现变量提升，是因为JavaScript代码在执行之前需要先**编译**。
- 在**编译阶段**，变量和函数会被存放到**变量环境**中，变量的默认值会被设置为undefined；在代码**执行阶段**，JavaScript引擎会从变量环境中去查找自定义的变量和函数。
- 如果在编译阶段，存在两个相同的函数，那么最终存放在变量环境中的是最后定义的那个，这是因为后定义的会覆盖掉之前定义的。

以上就是今天所讲的主要内容，当然，学习这些内容并不是让你掌握一些JavaScript小技巧，其主要目的是让你清楚JavaScript的执行机制：**先编译，再执行**。

如果你了解了JavaScript执行流程，那么在编写代码时，你就能避开一些陷阱；在分析代码过程中，也能通过分析JavaScript的执行过程来定位问题。

## 思考时间

最后，看下面这段代码：

```
showName()
var showName = function() {
    console.log(2)
}
function showName() {
    console.log(1)
}
```

你能按照JavaScript的执行流程，来分析最终输出结果吗？

欢迎在留言区与我分享你的想法，也欢迎你在留言区记录你的思考过程。感谢阅读，如果你觉得这篇文章对你有帮助的话，也欢迎把它分享给更多的朋友。
<div><strong>精选留言（15）</strong></div><ul>
<li><span>mfist</span> 👍（204） 💬（11）<p>输出1

编译阶段:
var showName
function showName(){console.log(1)}

执行阶段:
showName()&#47;&#47;输出1
showName=function(){console.log(2)}
&#47;&#47;如果后面再有showName执行的话，就输出2因为这时候函数引用已经变了</p>2019-08-20</li><br/><li><span>lane</span> 👍（147） 💬（10）<p>老师，head头部引入的js文件，也是先编译的吗？</p>2019-08-20</li><br/><li><span>爱吃锅巴的沐泡</span> 👍（106） 💬（6）<p>答案：1

编译阶段:
var showName = undefined
function showName() {console.log(1)}

执行阶段:
showName()        &#47;&#47;输出1
showName = function() {console.log(2)}

分析：首先遇到声明的变量showName，并在变量环境中存一个showName属性，赋值为undefined; 又遇到声明的函数，也存一个showName的属性，但是发现之前有这个属性了，就将其覆盖掉，并指向堆中的声明的这个函数地址。所以在执行阶段调用showName()会输出1;执行showName = function() {console.log(2)}这句话是把堆中的另一个函数地址赋值给了showName属性，也就改变了其属性值，所以如果再调用showName()，那个会输出2. 这是不是体现了函数是对象，函数名是指针。

疑问：如果同名的变量和函数名，变量环境中是分别保存还是如何处理的？

</p>2019-08-20</li><br/><li><span>he</span> 👍（81） 💬（10）<p>函数提升要比变量提升的优先级要高一些，且不会被变量声明覆盖，但是会被变量赋值之后覆盖。</p>2019-08-21</li><br/><li><span>shezhenbiao</span> 👍（62） 💬（6）<p>老师好，请教您一个问题。
debugger;
(function(){
    console.log(g)
    if(true){
        console.log(&#39;hello world&#39;);
        function g(){ return true; }
    }
})();
这个函数步进调试时，发现打印g时值是undefined而不是提示not defined，说明if中g函数确实是提升了，但是为何不是g()而是undefined？然后走完function g(){ return true; }这一步后 console.log(g)中的g才变为g()。这里条件声明函数的变量提升有点搞不明白。</p>2019-08-25</li><br/><li><span>William</span> 👍（40） 💬（11）<p>老师，如果把两个函数调换个儿。那么先声明function，然后把 showName 赋值 undefined，undefined不会覆盖函数声明。这是为什么？

console.log(showName.toString())
function showName() {
    console.log(1)
}
var showName = function() {
  console.log(2)
}

打印的是函数体，而非undefined，证明 undefined 不会覆盖函数声明！！</p>2019-08-21</li><br/><li><span>林展翔</span> 👍（29） 💬（1）<p>老师，可以请教下吗，在编译完成之后是单单生成了字节码，再到执行过程中变成对应平台的机器码？ 还是编译过程已经生成了对应平台的机器码， 执行阶段就直接去执行相应的机器码？</p>2019-08-20</li><br/><li><span>Geek_East</span> 👍（25） 💬（3）<p>lexical scope发生在编译阶段，会产生变量提升的效果；
JavaScript的Dynamic Scope发生在执行阶段，会产生this binding, prototype chaining search的过程；
变量提升只提升声明(left hand）不提升赋值(right hand)
function的声明主要有: function declaration, function expression
其中function declaration会将方法体也提升，而function expression同变量提升一样，只会提升声明；
变量提升在有let或者const的block中会出现Temporal Dead Zone Error, 效果好似没有提升；
另外要注意block内部的var变量能够穿透block提升到global scope.

更多JS请了解：
https:&#47;&#47;geekeast.github.io&#47;jsscope.html</p>2019-11-28</li><br/><li><span>林高鸿</span> 👍（25） 💬（1）<p>老师，ES6 后不用 var，所以可否理解 Hoisting 为“权宜之计&#47;设计失误”呢？</p>2019-08-20</li><br/><li><span>YBB</span> 👍（23） 💬（4）<p>老师我想问下，一段javascript代码进入编译阶段是会对函数体内的代码也进行编译，还是只是将函数体的代码存储在堆，在执行中遇到该函数再去编译？</p>2019-08-26</li><br/><li><span>趁你还年轻233</span> 👍（13） 💬（3）<p>var showName;
function showName() {
    console.log(1)
}
showName();
showName = function() {
    console.log(2)
};

这样声明没有问题，可以正常输出1。

为什么下面的代码会报错呢：Uncaught TypeError: showName is not a function

var showName = undefined;
function showName() {
    console.log(1)
}
showName();
showName = function() {
    console.log(2)
};</p>2019-11-11</li><br/><li><span>林展翔</span> 👍（7） 💬（4）<p>x = 10 + 20;
console.log(x);
若对 x 未进行定义, 直接赋值, 可以输出
若按照课程理解并假设
编译阶段会有一个
x = undefine
但是
console.log(x);
x = 10 + 20;
console.log(x);
会出现报错  x is not defined
在这个地方 我的理解有什么问题吗 还是说 原来就没有 x = undefine 操作, 只是在 x = 10 + 20; 给 x 赋值了一下.</p>2019-08-20</li><br/><li><span>杨陆伟</span> 👍（3） 💬（3）<p>showName()
function showName(){
    console.log(1)
}
var showName=function(){
    console.log(2)
}
showName()

第二个showName打印为2，为什么这个showName找的是变量而不是函数，或者此时变量环境中已经没有了showName函数，只有showName变量？谢谢</p>2019-08-20</li><br/><li><span>Lester</span> 👍（2） 💬（1）<p>如果变量和函数同名，那么在编译阶段，变量的声明会被忽略，执行的时候还是后面的是什么就是什么，而不会因为同名，就一定是函数。</p>2019-11-13</li><br/><li><span>子非鱼</span> 👍（2） 💬（1）<p>老师我有个问题，正常情况domcontentloaded事件是在浏览器下载并解析完html才触发，如果有内嵌外部js文件，也要等到js加载并执行完才触发。但如果页面是被二次访问并且html和引入的外部js都命中了缓存，则是否也要等到js被完全执行才触发呢？</p>2019-08-22</li><br/>
</ul>