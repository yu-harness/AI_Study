你好，我是大圣。

前面我们用了四讲，学习了Vue在浏览器中是如何执行的，你可以参考上一讲结尾的Vue执行全景图来回顾一下。在Vue中，组件都是以虚拟DOM的形式存在，加载完毕之后注册effect函数。这样组件内部的数据变化之后，用Vue的响应式机制做到了通知组件更新，内部则使用patch函数实现了虚拟DOM的更新，中间我们也学习了位运算、最长递增子序列等算法。

这时候你肯定还有一个疑问，那就是虚拟DOM是从哪来的？我们明明写的是template和JSX，这也是吃透Vue源码最后一个难点：Vue中的Compiler。

下图就是Vue核心模块依赖关系图，reactivity和runtime我们已经剖析完毕，迷你版本的代码你可以在[GitHub](https://github.com/shengxinjing/weiyouyi)中看到。今天开始我将用三讲的内容，给你详细讲解一下Vue在编译的过程中做了什么。

![图片](https://static001.geekbang.org/resource/image/59/15/59f10ba0b6a6ed5fb956ca05016fde15.jpg?wh=1888x982)

编译原理也属于计算机中的一个重要学科，Vue的compiler是在Vue场景下的实现，目的就是实现template到render函数的转变。

我们第一步需要先掌握编译原理的基本概念。Vue官方提供了模板编译的[在线演示](https://vue-next-template-explorer.netlify.app/#%7B%22src%22%3A%22%3Cdiv%20id%3D%5C%22app%5C%22%3E%5Cn%20%20%20%20%3Cdiv%20%40click%3D%5C%22%28%29%3D%3Econsole.log%28xx%29%5C%22%20%3Aid%3D%5C%22name%5C%22%3E%7B%7Bname%7D%7D%3C%2Fdiv%3E%5Cn%20%20%20%20%3Ch1%20%3Aname%3D%5C%22title%5C%22%3E%E7%8E%A9%E8%BD%ACvue3%3C%2Fh1%3E%5Cn%20%20%20%20%3Cp%20%3E%E7%BC%96%E8%AF%91%E5%8E%9F%E7%90%86%3C%2Fp%3E%5Cn%3C%2Fdiv%3E%5Cn%22%2C%22ssr%22%3Afalse%2C%22options%22%3A%7B%22mode%22%3A%22module%22%2C%22filename%22%3A%22Foo.vue%22%2C%22prefixIdentifiers%22%3Afalse%2C%22hoistStatic%22%3Atrue%2C%22cacheHandlers%22%3Atrue%2C%22scopeId%22%3Anull%2C%22inline%22%3Afalse%2C%22ssrCssVars%22%3A%22%7B%20color%20%7D%22%2C%22compatConfig%22%3A%7B%22MODE%22%3A3%7D%2C%22whitespace%22%3A%22condense%22%2C%22bindingMetadata%22%3A%7B%22TestComponent%22%3A%22setup-const%22%2C%22setupRef%22%3A%22setup-ref%22%2C%22setupConst%22%3A%22setup-const%22%2C%22setupLet%22%3A%22setup-let%22%2C%22setupMaybeRef%22%3A%22setup-maybe-ref%22%2C%22setupProp%22%3A%22props%22%2C%22vMySetupDir%22%3A%22setup-const%22%7D%2C%22optimizeBindings%22%3Afalse%7D%7D)。下图左侧代码是我们写的template，右侧代码就是compiler模块解成的render函数，我们今天的任务就是能够实现一个迷你的compiler。

![图片](https://static001.geekbang.org/resource/image/33/23/3326bd4f65d0714c4920e6d37e1be923.png?wh=1920x608)

## 整体流程

上述转化的过程可以分为下面的示意图几步来实现。

首先，代码会被解析成一个对象，这个对象有点像虚拟DOM的概念，用来描述template的代码关系，这个对象就是抽象语法树（简称AST，后面我们细讲）。然后通过transform模块对代码进行优化，比如识别Vue中的语法，静态标记、最后通过generate模块生成最终的render函数。

![图片](https://static001.geekbang.org/resource/image/9a/6d/9aaa7b24f6b9ff0cef5f70151ddd926d.jpg?wh=1920x1747)

理清了流程，我们动手完成具体代码实现。用下面的代码就能实现上述的流程图里的内容。其中parse函数负责生成抽象语法树AST，transform函数负责语义转换，generate函数负责最终的代码生成。

```javascript

function compiler(template) {
  const ast = parse(template);
  transform(ast)
  const code = generate(ast)
  return code
}

let template = `<div id="app">
  <div @click="()=>console.log(xx)" :id="name">{{name}}</div>
  <h1 :name="title">玩转vue3</h1>
  <p >编译原理</p>
</div>
`

const renderFunction = compiler(template)
console.log(renderFunction)
```

我们先来看下parse函数如何实现。template转成render函数是两种语法的转换，这种代码转换的需求其实计算机的世界中非常常见。比如我们常用的Babel，就是把ES6的语法转成低版本浏览器可以执行的代码。

## tokenizer的迷你实现

首先，我们要对template进行词法分析，把模板中的&lt;div&gt;, @click, {{}}等语法识别出来，转换成一个个的token。你可以理解为把template的语法进行了分类，这一步我们叫tokenizer。

下面的代码就是tokenizer的迷你实现。我们使用tokens数组存储解析的结果，然后对模板字符串进行循环，在template中，&lt; &gt; / 和空格都是关键的分隔符，如果碰见&lt;字符，我们需要判断下一个字符的状态。如果是字符串我们就标记tagstart；如果是/，我们就知道是结束标签，标记为tagend，最终通过push方法把分割之后的token存储在数组tokens中返回。

```javascript
function tokenizer(input) {
  let tokens = []
  let type = ''
  let val = ''
  // 粗暴循环
  for (let i = 0; i < input.length; i++) {
    let ch = input[i]
    if (ch === '<') {
      push()
      if (input[i + 1] === '/') {
        type = 'tagend'
      } else {
        type = 'tagstart'
      }
    } if (ch === '>') {
      if(input[i-1]=='='){
        //箭头函数
      }else{
        push()
        type = "text"
        continue
      }
    } else if (/[\s]/.test(ch)) { // 碰见空格截断一下
      push()
      type = 'props'
      continue
    }
    val += ch
  }
  return tokens

  function push() {
    if (val) {
      if (type === "tagstart") val = val.slice(1) // <div => div
      if (type === "tagend") val = val.slice(2)   //  </div  => div
      tokens.push({
        type,
        val
      })
      val = ''
    }
  }
}
```

实现了上面的代码，我们就得到了解析之后的token数组。

## 生成抽象语法树

下面的数组中，我们分别用tagstart、props tagend和text标记，用它们标记了全部内容。然后下一步我们需要把这个数组按照标签的嵌套关系转换成树形结构，这样才能完整地描述template标签的关系。

```javascript
[
  { type: 'tagstart', val: 'div' },
  { type: 'props', val: 'id="app"' },
  { type: 'tagstart', val: 'div' },
  { type: 'props', val: '@click="()=console.log(xx)"' },
  { type: 'props', val: ':id="name"' },
  { type: 'text', val: '{{name}}' },
  { type: 'tagend', val: 'div' },
  { type: 'tagstart', val: 'h1' },
  { type: 'props', val: ':name="title"' },
  { type: 'text', val: '玩转vue3' },
  { type: 'tagend', val: 'h1' },
  { type: 'tagstart', val: 'p' },
  { type: 'text', val: '编译原理' },
  { type: 'tagend', val: 'p' },
  { type: 'tagend', val: 'div' }
```

然后我们分析token数组，看看它是如何转化成一个体现语法规则的树形结构的。  
就像我们用虚拟DOM描述页面DOM结构一样，我们使用树形结构描述template的语法，这个树我们称之为抽象语法树，简称AST。

下面的代码中我们用parse函数实现AST的解析。过程是这样的，首先我们使用一个AST对象作为根节点。然后通过walk函数遍历整个tokens数组，根据token的类型不同，生成不同的node对象。最后根据tagend的状态来决定walk的递归逻辑，最终实现了整棵树的构建。

```javascript
function parse(template) {
  const tokens = tokenizer(template)
  let cur = 0
  let ast = {
    type: 'root',
    props:[],
    children: []
  }
  while (cur < tokens.length) {
    ast.children.push(walk())
  }
  return ast

  function walk() {
    let token = tokens[cur]
    if (token.type == 'tagstart') {
      let node = {
        type: 'element',
        tag: token.val,
        props: [],
        children: []
      }
      token = tokens[++cur]
      while (token.type !== 'tagend') {
        if (token.type == 'props') {
          node.props.push(walk())
        } else {
          node.children.push(walk())
        }
        token = tokens[cur]
      }
      cur++
      return node
    }
    if (token.type === 'tagend') {
      cur++
      // return token
    }
    if (token.type == "text") {
      cur++
      return token
    }
    if (token.type === "props") {
      cur++
      const [key, val] = token.val.replace('=','~').split('~')
      return {
        key,
        val
      }
    }
  }
}
```

上面的代码会生成抽象语法树AST，这个树的结构如下面代码所示，通过type和children描述整个template的结构。

```javascript
{
  "type": "root",
  "props": [],
  "children": [
    {
      "type": "element",
      "tag": "div",
      "props": [
        {
          "key": "id",
          "val": "\"app\""
        }
      ],
      "children": [
        {
          "type": "element",
          "tag": "div",
          "props": [
            {
              "key": "@click",
              "val": "\"()"
            },
            {
              "key": ":id",
              "val": "\"name\""
            }
          ],
          "children": [
            {
              "type": "text",
              "val": "{{name}}"
            }
          ]
        },
        {
          "type": "element",
          "tag": "h1",
          "props": [
            {
              "key": ":name",
              "val": "\"title\""
            }
          ],
          "children": [
            {
              "type": "text",
              "val": "玩转vue3"
            }
          ]
        },
        {
          "type": "element",
          "tag": "p",
          "props": [],
          "children": [
            {
              "type": "text",
              "val": "编译原理"
            }
          ]
        }
      ]
    }
  ]
}
```

## 语义分析和优化

有了抽象语法树之后，我们还要进行语义的分析和优化，也就是说，我们要在这个阶段理解语句要做的事。咱们结合例子来理解会更容易。

在template这个场景下，两个大括号包裹的字符串就是变量，@click就是事件监听。

下面的代码中我们使用transform函数实现这个功能，这一步主要是理解template中Vue的语法，并且为最后生成的代码做准备。我们使用context对象存储AST所需要的上下文，如果我们用到了变量{{}}，就需要引入toDisplayString函数，上下文中的helpers存储的就是我们用到的工具函数。

```javascript
function transform(ast) {
  // 优化一下ast
  let context = {
    // import { toDisplayString , createVNode , openBlock , createBlock } from "vue"
    helpers:new Set(['openBlock','createVnode']), // 用到的工具函数 
  }
  traverse(ast, context)
  ast.helpers = context.helpers
}
```

然后我们使用traverse函数递归整个AST，去优化AST的结构，并且在这一步实现简单的静态标记。

当节点标记为element的时候，我们递归调用整个AST，内部挨个遍历AST所有的属性，我们默认使用ast.flag标记节点的动态状态。如果属性是@开头的，我们就认为它是Vue中的事件绑定，使用arg.flag|= PatchFlags.EVENT 标记当前节点的事件是动态的，需要计算diff，这部分位运算的知识点我们在上一讲已经学习过了。

然后冒号开头的就是动态的属性传递，并且把class和style标记了不同的flag。如果都没有命中的话，就使用static:true，标记当前节点位是静态节点。

```javascript
function traverse(ast, context){
  switch(ast.type){
    case "root":
      context.helpers.add('createBlock')
      // log(ast)
    case "element":
      ast.children.forEach(node=>{
        traverse(node,context)
      })
      ast.flag = 0
      ast.props = ast.props.map(prop=>{
        const {key,val} = prop
        if(key[0]=='@'){
          ast.flag |= PatchFlags.EVENT // 标记event需要更新
          return {
            key:'on'+key[1].toUpperCase()+key.slice(2),
            val
          }
        }
        if(key[0]==':'){
          const k = key.slice(1)
          if(k=="class"){
            ast.flag |= PatchFlags.CLASS // 标记class需要更新

          }else if(k=='style'){
            ast.flag |= PatchFlags.STYLE // 标记style需要更新
          }else{
            ast.flag |= PatchFlags.PROPS // 标记props需要更新
          }
          return{
            key:key.slice(1),
            val
          }
        }
        if(key.startsWith('v-')){
          // pass such as v-model 
        }
        //标记static是true 静态节点
        return {...prop,static:true} 
      })
      break
    case "text":
      // trnsformText
      let re = /\{\{(.*)\}\}/g
      if(re.test(ast.val)){
        //有{{
          ast.flag |= PatchFlags.TEXT // 标记props需要更新
          context.helpers.add('toDisplayString')
          ast.val = ast.val.replace(/\{\{(.*)\}\}/g,function(s0,s1){
            return s1
          })
      }else{
        ast.static = true
      }
  }
}  

```

经过上面的代码标记优化之后，项目在数据更新之后，浏览器计算虚拟dom diff运算的时候，就会执行类似下面的代码逻辑。

**我们通过在compiler阶段的标记，让template产出的虚拟DOM有了更精确的状态，可以越过大部分的虚拟DOM的diff计算，极大提高Vue的运行时效率，这个思想我们日常开发中也可以借鉴学习。**

```javascript
if(vnode.static){
  return 
}
if(vnode.flag & patchFlag.CLASS){
  遍历class 计算diff  
}else if(vnode.flag & patchFlag.STYLE){
  计算style的diff
}else if(vnode.flag & patchFlag.TEXT){
  计算文本的diff
}
```

接下来，我们基于优化之后的AST生成目标代码，也就是generate函数要做的事：遍历整个AST，拼接成最后要执行的函数字符串。

下面的代码中，我们首先把helpers拼接成import语句，并且使用walk函数遍历整个AST，在遍历的过程中收集helper集合的依赖。最后，在createVnode的最后一个参数带上ast.flag进行状态的标记。

```javascript
function generate(ast) {
  const {helpers} = ast 

  let code = `
import {${[...helpers].map(v=>v+' as _'+v).join(',')}} from 'vue'\n
export function render(_ctx, _cache, $props){
  return(_openBlock(), ${ast.children.map(node=>walk(node))})}`

  function walk(node){
    switch(node.type){
      case 'element':
        let {flag} = node // 编译的标记
        let props = '{'+node.props.reduce((ret,p)=>{
          if(flag.props){
            //动态属性
            ret.push(p.key +':_ctx.'+p.val.replace(/['"]/g,'') )
          }else{
            ret.push(p.key +':'+p.val )
          }

          return ret
        },[]).join(',')+'}'
        return `_createVnode("${node.tag}",${props}),[
          ${node.children.map(n=>walk(n))}
        ],${JSON.stringify(flag)}`
        break
      case 'text':
        if(node.static){
          return '"'+node.val+'"'
        }else{
          return `_toDisplayString(_ctx.${node.val})`
        }
        break
    }
  }
  return code
}
```

## 最终实现效果

最后我们执行一下代码，看下效果输出的代码。可以看到，它已经和Vue输出的代码很接近了，到此为止，我们也实现了一个非常迷你的Vue compiler，这个产出的render函数最终会和组件的setup函数一起组成运行时的组件对象。

```javascript
function compiler(template) {
  const ast = parse(template);
  transform(ast)

  const code = generate(ast)
  return code
}

let template = `<div id="app">
  <div @click="()=>console.log(xx)" :id="name">{{name}}</div>
  <h1 :name="title">玩转vue3</h1>
  <p >编译原理</p>
</div>
`

const renderFunction = compiler(template)
console.log(renderFunction)

// 下面是输出结果
import { openBlock as _openBlock, createVnode as _createVnode, createBlock as _createBlock, toDisplayString as _toDisplayString } from 'vue'

export function render(_ctx, _cache, $props) {
  return (_openBlock(), _createVnode("div", { id: "app" }), [
    _createVnode("div", { onClick: "()=>console.log(xx)", id: "name" }), [
      _toDisplayString(_ctx.name)
    ], 24, _createVnode("h1", { name: "title" }), [
      "玩转vue3"
    ], 8, _createVnode("p", {}), [
      "编译原理"
    ], 0
  ], 0)
}

```

## 总结

我们总结一下今天所学的内容。今天，我带你手写了一个非常迷你的Vue compiler，这也是我们学习框架源码的时候一个比较正确的思路：在去看实际的源码之前，先通过迷你版本的实现，熟悉整个Vue compiler工作的主体流程。

![图片](https://static001.geekbang.org/resource/image/ce/0d/ce5d04ae043d4247b4yy03e91353620d.jpg?wh=1920x453)

通过这个迷你的compiler，我们学习了编译原理的入门知识：包括parser的实现、AST是什么，AST的语义化优化和代码生成generate模块，这给我们下一讲弄清楚Vue的compiler的核心逻辑打下了良好的理论基础。

我想提醒你注意一个优化方法，我们实现的迷你compiler也实现了属性的静态标记，通过在编译期间的标记方式，让虚拟DOM在运行时有更多的状态，从而能够精确地控制更新。这种编译时的优化也能够对我们项目开发有很多指引作用，我会在剖析完Vue的compiler之后，在第34讲那里跟你分享一下实战中如何使用编译优化的思想。

## 思考题

最后留一个思考题吧，Vue的compiler输出的代码会有几个hoisted开头的变量，这几个变量有什么用处呢？欢迎在评论区分享你的答案，也欢迎你把这一讲分享给你的同事和朋友们，我们下一讲再见！
<div><strong>精选留言（6）</strong></div><ul>
<li><span>神瘦</span> 👍（0） 💬（1）<p>“tokenizer 的迷你实现”这个地方“把模板中的”这几个字后面一大段空白呢，你们那边能看到吗？检查下呢</p>2022-01-30</li><br/><li><span>openbilibili</span> 👍（0） 💬（1）<p>template中的p标签 不能有空格 不然解析不了</p>2022-01-06</li><br/><li><span>斜月浮云</span> 👍（0） 💬（2）<p>hoisted开头的变量用于静态节点提升，说白了就是在整个生命周期中只需要进行一次创建，有效节省不必要的性能开销。

话说最后的generate代码明显不对啊，createVnode的后括号阔歪了哦~🙂</p>2022-01-03</li><br/><li><span>陈坚泓</span> 👍（0） 💬（0）<p>const [key, val] = token.val.replace(&#39;=&#39;,&#39;~&#39;).split(&#39;~&#39;)  
是不是可以写成
const [key, val] = token.val.split(&#39;=&#39;)  

备注里 &#47;&#47; trnsformText    估计是拼错了 </p>2022-05-20</li><br/><li><span>Blueberry</span> 👍（0） 💬（0）<p>template语法需要经过这么一系列的编译，那h函数呢，是经过什么变成了最后的render语法?</p>2022-04-12</li><br/><li><span>名字好长的大林</span> 👍（0） 💬（1）<p>PatchFlags 这个变量没有给？？</p>2022-02-04</li><br/>
</ul>