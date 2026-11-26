你好，我是winter。

在前面几篇文章中，我们已经了解了关于执行上下文、作用域、闭包之间的关系。

今天，我们则要说一说更为细节的部分：语句。

语句是任何编程语言的基础结构，与JavaScript对象一样，JavaScript语句同样具有“看起来很像其它语言，但是其实一点都不一样”的特点。

我们比较常见的语句包括变量声明、表达式、条件、循环等，这些都是大家非常熟悉的东西，对于它们的行为，我在这里就不赘述了。

为了了解JavaScript语句有哪些特别之处，首先我们要看一个不太常见的例子，我会通过这个例子，来向你介绍JavaScript语句执行机制涉及的一种基础类型：Completion类型。

## Completion类型

我们来看一个例子。在函数foo中，使用了一组try语句。我们可以先来做一个小实验，在try中有return语句，finally中的内容还会执行吗？我们来看一段代码。

```
function foo(){
  try{
    return 0;
  } catch(err) {

  } finally {
    console.log("a")
  }
}

console.log(foo());
```

通过实际试验，我们可以看到，finally确实执行了，而且return语句也生效了，foo()返回了结果0。

虽然return执行了，但是函数并没有立即返回，又执行了finally里面的内容，这样的行为违背了很多人的直觉。

如果在这个例子中，我们在finally中加入return语句，会发生什么呢？

```
function foo(){
  try{
    return 0;
  } catch(err) {

  } finally {
    return 1;
  }
}

console.log(foo());
```

通过实际执行，我们看到，finally中的return “覆盖”了try中的return。在一个函数中执行了两次return，这已经超出了很多人的常识，也是其它语言中不会出现的一种行为。

面对如此怪异的行为，我们当然可以把它作为一个孤立的知识去记忆，但是实际上，这背后有一套机制在运作。

这一机制的基础正是JavaScript语句执行的完成状态，我们用一个标准类型来表示：Completion Record（我在类型一节提到过，Completion Record用于描述异常、跳出等语句执行过程）。

Completion Record 表示一个语句执行完之后的结果，它有三个字段：

- \[\[type]] 表示完成的类型，有break continue return throw和normal几种类型；
- \[\[value]] 表示语句的返回值，如果语句没有，则是empty；
- \[\[target]] 表示语句的目标，通常是一个JavaScript标签（标签在后文会有介绍）。

JavaScript正是依靠语句的 Completion Record类型，方才可以在语句的复杂嵌套结构中，实现各种控制。接下来我们要来了解一下JavaScript使用Completion Record类型，控制语句执行的过程。

首先我们来看看语句有几种分类。

![](https://static001.geekbang.org/resource/image/98/d5/98ce53be306344c018cddd6c083392d5.jpg?wh=555%2A872)

## 普通的语句

在JavaScript中，我们把不带控制能力的语句称为普通语句。普通语句有下面几种。

- 声明类语句
  
  - var声明
  - const声明
  - let声明
  - 函数声明
  - 类声明
- 表达式语句
- 空语句
- debugger语句

这些语句在执行时，从前到后顺次执行（我们这里先忽略var和函数声明的预处理机制），没有任何分支或者重复执行逻辑。

普通语句执行后，会得到 \[\[type]] 为 normal 的 Completion Record，JavaScript引擎遇到这样的Completion Record，会继续执行下一条语句。

这些语句中，只有表达式语句会产生 \[\[value]]，当然，从引擎控制的角度，这个value并没有什么用处。

如果你经常使用Chrome自带的调试工具，可以知道，输入一个表达式，在控制台可以得到结果，但是在前面加上var，就变成了undefined。

![](https://static001.geekbang.org/resource/image/a3/67/a35801b1b82654d17e413e51b340d767.png?wh=376%2A237)

Chrome控制台显示的正是语句的Completion Record的\[\[value]]。

## 语句块

介绍完了普通语句，我们再来介绍一个比较特殊的语句：语句块。

语句块就是拿大括号括起来的一组语句，它是一种语句的复合结构，可以嵌套。

语句块本身并不复杂，我们需要注意的是语句块内部的语句的Completion Record的\[\[type]] 如果不为 normal，会打断语句块后续的语句执行。

比如我们考虑，一个\[\[type]]为return的语句，出现在一个语句块中的情况。

从语句的这个type中，我们大概可以猜到它由哪些特定语句产生，我们就来说说最开始的例子中的 return。

return语句可能产生return或者throw类型的Completion Record。我们来看一个例子。

先给出一个内部为普通语句的语句块：

```
{
  var i = 1; // normal, empty, empty
  i ++; // normal, 1, empty
  console.log(i) //normal, undefined, empty
} // normal, undefined, empty
```

在每一行的注释中，我给出了语句的Completion Record。

我们看到，在一个block中，如果每一个语句都是normal类型，那么它会顺次执行。接下来我们加入return试试看。

```
{
  var i = 1; // normal, empty, empty
  return i; // return, 1, empty
  i ++; 
  console.log(i)
} // return, 1, empty
```

但是假如我们在block中插入了一条return语句，产生了一个非normal记录，那么整个block会成为非normal。这个结构就保证了非normal的完成类型可以穿透复杂的语句嵌套结构，产生控制效果。

接下来我们就具体讲讲控制类语句。

## 控制型语句

控制型语句带有 if、switch关键字，它们会对不同类型的Completion Record产生反应。

控制类语句分成两部分，一类是对其内部造成影响，如if、switch、while/for、try。

另一类是对外部造成影响如break、continue、return、throw，这两类语句的配合，会产生控制代码执行顺序和执行逻辑的效果，这也是我们编程的主要工作。

一般来说， for/while - break/continue 和 try - throw 这样比较符合逻辑的组合，是大家比较熟悉的，但是，实际上，我们需要控制语句跟break 、continue 、return 、throw四种类型与控制语句两两组合产生的效果。

![](https://static001.geekbang.org/resource/image/77/d3/7760027d7ee09bdc8ec140efa9caf1d3.png?wh=840%2A463)

通过这个表，我们不难发现知识的盲点，也就是我们最初的的case中的try和return的组合了。

因为finally中的内容必须保证执行，所以 try/catch执行完毕，即使得到的结果是非normal型的完成记录，也必须要执行finally。

而当finally执行也得到了非normal记录，则会使finally中的记录作为整个try结构的结果。

## 带标签的语句

前文我重点讲了type在语句控制中的作用，接下来我们重点来讲一下最后一个字段：target，这涉及了JavaScript中的一个语法，带标签的语句。

实际上，任何JavaScript语句是可以加标签的，在语句前加冒号即可：

```
    firstStatement: var i = 1;
```

大部分时候，这个东西类似于注释，没有任何用处。唯一有作用的时候是：与完成记录类型中的target相配合，用于跳出多层循环。

```
    outer: while(true) {
      inner: while(true) {
          break outer;
      }
    }
    console.log("finished")
```

break/continue 语句如果后跟了关键字，会产生带target的完成记录。一旦完成记录带了target，那么只有拥有对应label的循环语句会消费它。

## 结语

我们以Completion Record类型为线索，为你讲解了JavaScript语句执行的原理。

因为JavaScript语句存在着嵌套关系，所以执行过程实际上主要在一个树形结构上进行， 树形结构的每一个节点执行后产生Completion Record，根据语句的结构和Completion Record，JavaScript实现了各种分支和跳出逻辑。

你遇到哪些语句中的执行的实际效果，是跟你想象的有所出入呢，你可以给我留言，我们一起讨论。
<div><strong>精选留言（15）</strong></div><ul>
<li><span>csᵏᵒᵖ</span> 👍（7） 💬（2）<p>winter老师，特殊处理就是指后面的 “因为 finally 中的内容必须保证执行，所以 try&#47;catch 执行完毕，即使得到的结果是非 normal 型的完成记录，也必须要执行 finally“ 吗</p>2019-10-26</li><br/><li><span>小say</span> 👍（6） 💬（1）<p>老师你好，前面说[[value]]如果没有返回值就是empty但是为什么在Chrome调试器下显示的是undefined？
后文中语句块中
{
  var i = 1; &#47;&#47; normal, empty, empty
  i ++; &#47;&#47; normal, 1, empty
  console.log(i) &#47;&#47;normal, undefined, empty
} &#47;&#47; normal, undefined, empty
其中 var i = 1; 为什么[[value]]会是empty？console.log(i)的[[value]]为什么是undefined？所以到底什么时候是empty什么时候是undefined？</p>2019-09-17</li><br/><li><span>Smallfly</span> 👍（2） 💬（1）<p>winter 老师，有什么工具能查看 JS 引擎的运行时的特殊类型么？</p>2019-10-17</li><br/><li><span>Puru</span> 👍（1） 💬（2）<p>Python 也是先执行finally后执行return</p>2019-06-25</li><br/><li><span>尤璐洁</span> 👍（0） 💬（1）<p>winter老师，这些个私有属性的值执行时的值是如何得出的，是靠分析，还是说有某种方式可以看到验证呢？</p>2019-10-23</li><br/><li><span>东</span> 👍（0） 💬（3）<p>void function() {
	if(true){
		console.log(1)
		break
		console.log(2)
	}
}()
在if中用break、continue会报错VM506:4 Uncaught SyntaxError: Illegal break statement，而不是穿透，为什么和表格举出的不一致呢</p>2019-07-09</li><br/><li><span>热爱减肥的胖子</span> 👍（0） 💬（1）<p>请问，上图上那个“特殊处理”怎么理解？</p>2019-06-26</li><br/><li><span>有铭</span> 👍（98） 💬（8）<p>很感兴趣这些高级特性的知识老师是从哪里学到的，我翻过js高级编程那本书都没讲到过这些</p>2019-03-02</li><br/><li><span>周小成</span> 👍（88） 💬（3）<p>穿透和消费，报错应该是连贯的，“穿透”就是指不在当前这一层处理，向外逐层寻找可以“消费”的那一层，直到最后都没找到就报错，比如：function里面有while, while里面有switch, switch里面又有continue，按图表来看，switch-continue应该是穿透，向上层寻找消费，碰到while-contine,那就是消费，再如switch里面是return, switch-return穿透，向上层whlie-return穿透，最后function-return是消费。</p>2019-03-12</li><br/><li><span>Rushan-Chen</span> 👍（59） 💬（13）<p>请问老师，表格中的“穿透”和“消费”是什么意思？</p>2019-03-02</li><br/><li><span>AICC</span> 👍（46） 💬（0）<p>3楼你好，我的理解是，消费指对应的代码被有效的执行了，穿透指对应代码被跳过了，也就是对应控制的语句体被有效执行比如try catch,当try中出现了throw,能被有效捕获进而执行catch，这在我理解就是try被消费执行了，而当catch中还有throw时，由于catch不具备处理throw的能力，于是catch被中断跳出，也就是作者所说的穿透，希望能帮到你</p>2019-03-02</li><br/><li><span>加利率的钟摆</span> 👍（33） 💬（4）<p>```javascript
function test(){
  if(true){
    console.log(&quot;111&quot;);
    break;
  }
  if(true){
    console.log(&quot;222&quot;);
  }
}

test(); &#47;&#47; SyntaxError: Illegal break statement
```

我们可以这么分析：

1. if 和 break 相遇，break 穿透至 function
2. function 和 break 相遇，报错

```javascript
function test() {
  var a = 0;
  switch (a) {
    case 0:
      if (true) {
        console.log(&quot;111&quot;);
        break;
      }
  }

  if (true) {
    console.log(&quot;222&quot;);
  }
}

test();
&#47;&#47; 111
&#47;&#47; 222
```

我们可以这么分析：

1. if 和 break 相遇，break 穿透至 switch
2. swicth 和 break 相遇，消费掉 break
3. 接着执行之后的代码</p>2019-04-17</li><br/><li><span>火云邪神0007</span> 👍（16） 💬（0）<p>老师在前面讲过，穿透就是去上一层的作用域或者控制语句找可以消费break，continue的执行环境，消费就是在这一层就执行了这个break或者continue</p>2019-03-04</li><br/><li><span>Dream.</span> 👍（15） 💬（1）<p>第一次看见『消费』与『穿透』这样的描述。

这两个词的来源自哪里呢？

结合表格中的控制语句组合使用得到的结果来看，我的理解是

『消费』是控制语句里的内容执行完毕。
『穿透』是控制语句里的内容没能执行完，被中止了。
</p>2019-03-03</li><br/><li><span>夜空中最亮的星</span> 👍（10） 💬（0）<p>老师，我昨天成功的把您的课推销出去了一份，哈哈😄高兴</p>2019-03-02</li><br/>
</ul>