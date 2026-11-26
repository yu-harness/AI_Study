你好，我是大圣。

在上一讲中，我带你了解了Vuex这个数据管理框架的使用方法，以及Vue 3中数据管理框架的来源、实战细节和相关的原理。

其实项目中除了数据管理，路由系统也是非常核心的模块。所以在这一讲中，我会先带你了解一下前端开发方式的演变，让你明白前端路由因何而来，之后再讲解前端路由的实现原理。最后，我会再带你手写一个vue-router，并在这个过程中为你补充相关的实战要点，让你对如何用好vue-router有一个直观体验。

## 前后端开发模式的演变

在jQuery时代，对于大部分Web项目而言，前端都是不能控制路由的，而是需要依赖后端项目的路由系统。通常，前端项目也会部署在后端项目的模板里，整个项目执行的示意图如下：

![图片](https://static001.geekbang.org/resource/image/26/2b/26ddd952f1f7d6dc3193af5be57e202b.jpg?wh=1569x462)

jQuery那个时代的前端工程师，都要学会在后端的模板，比如JSP，Smatry等里面写一些代码。但是在这个时代，前端工程师并不需要了解路由的概念。对于每次的页面跳转，都由后端开发人员来负责重新渲染模板。

前端依赖后端，并且前端不需要负责路由的这种开发方式，有很多的优点，比如开发速度会很快、后端也可以承担部分前端任务等，所以到现在还有很多公司的内部管理系统是这样的架构。当然，这种开发方式也有很多缺点，比如前后端项目无法分离、页面跳转由于需要重新刷新整个页面、等待时间较长等等，所以也会让交互体验下降。

为了提高页面的交互体验，很多前端工程师做了不同的尝试。在这个过程中，前端的开发模式发生了变化，项目的结构也发生了变化。下图所示的，是在目前的前端开发中，用户访问页面后代码执行的过程。

![图片](https://static001.geekbang.org/resource/image/26/ec/2657d4eb129568d3c5b766e40eef60ec.jpg?wh=1920x435)

从上面的示意图中，我们可以看到：用户访问路由后，无论是什么URL地址，都直接渲染一个前端的入口文件index.html，然后就会在index.html文件中加载JS和CSS。之后，JavaScript获取当前的页面地址，以及当前路由匹配的组件，再去动态渲染当前页面即可。用户在页面上进行点击操作时，也不需要刷新页面，而是直接通过JS重新计算出匹配的路由渲染即可。

在前后两个示意图中，绿色的部分表示的就是前端负责的内容。而在后面这个架构下，前端获得了路由的控制权，在JavaScript中控制路由系统。也因此，页面跳转的时候就不需要刷新页面，网页的浏览体验也得到了提高。**这种所有路由都渲染一个前端入口文件的方式，是单页面应用程序（SPA，single page application）应用的雏形。**

通过JavaScript动态控制数据去提高用户体验的方式并不新奇，Ajax让数据的获取不需要刷新页面，SPA应用让路由跳转也不需要刷新页面。这种开发的模式在jQuery时代就出来了，浏览器路由的变化可以通过pushState来操作，这种纯前端开发应用的方式，以前称之为Pjax （pushState+ Ajax）。之后，这种开发模式在MVVM框架的时代大放异彩，现在大部分使用Vue/React/Angular的应用都是这种架构。

SPA应用相比于模板的开发方式，对前端更加友好，比如：前端对项目的控制权更大了、交互体验也更加丝滑，更重要的是，前端项目终于可以独立出来单独部署了。

## 前端路由的实现原理

在讲完前端路由的执行逻辑之后，我们深入探索一下前端控制路由的实现原理。

现在，通过URL区分路由的机制上，有两种实现方式，一种是hash模式，通过URL中#后面的内容做区分，我们称之为hash-router；另外一个方式就是history模式，在这种方式下，路由看起来和正常的URL完全一致。

这两个不同的原理，在vue-router中对应两个函数，分别是createWebHashHistory和createWebHistory。

![图片](https://static001.geekbang.org/resource/image/d0/d3/d07894f8b9df7c1afed10b730f8276d3.jpg?wh=1546x561)

### hash 模式

单页应用在页面交互、页面跳转上都是无刷新的，这极大地提高了用户访问网页的体验。**为了实现单页应用，前端路由的需求也变得重要了起来。**

类似于服务端路由，前端路由实现起来其实也很简单，就是匹配不同的 URL 路径，进行解析，然后动态地渲染出区域 HTML 内容。但是这样存在一个问题，就是 URL 每次变化的时候，都会造成页面的刷新。解决这一问题的思路便是在改变 URL 的情况下，保证页面的不刷新。

在 2014 年之前，大家是通过 hash 来实现前端路由，URL hash 中的 # 就是类似于下面代码中的这种 # ：

```plain
http://www.xxx.com/#/login
```

之后，在进行页面跳转的操作时，hash 值的变化并不会导致浏览器页面的刷新，只是会触发hashchange事件。在下面的代码中，通过对hashchange事件的监听，我们就可以在fn函数内部进行动态地页面切换。

```javascript
window.addEventListener('hashchange',fn)
```

### history 模式

2014年之后，因为HTML5标准发布，浏览器多了两个API：pushState 和 replaceState。通过这两个 API ，我们可以改变 URL 地址，并且浏览器不会向后端发送请求，我们就能用另外一种方式实现前端路由\*\*。

在下面的代码中，我们监听了popstate事件，可以监听到通过pushState修改路由的变化。并且在fn函数中，我们实现了页面的更新操作。

```plain
window.addEventListener('popstate', fn)
```

## 手写迷你vue-router

明白了前端路由实现原理还不够，接下来我们一起写代码直观感受一下。这里我们准备设计一个使用hash模式的迷你vue-router。

现在，我们在src/router目录下新建一个grouter文件夹，并且在grouter文件夹内部新建index.js。有了[上一讲](https://time.geekbang.org/column/article/439588)手写Vuex的基础，我们就可以在index.js中写入下面的代码。

在代码中，我们首先实现了用Router类去管理路由，并且，我们使用createWebHashHistory来返回hash模式相关的监听代码，以及返回当前URL和监听hashchange事件的方法；然后，我们通过Router类的install方法注册了Router的实例，并对外暴露createRouter方法去创建Router实例；最后，我们还暴露了useRouter方法，去获取路由实例。

```javascript
import {ref,inject} from 'vue'
const ROUTER_KEY = '__router__'

function createRouter(options){
    return new Router(options)
}

function useRouter(){
    return inject(ROUTER_KEY)
}
function createWebHashHistory(){
    function bindEvents(fn){
        window.addEventListener('hashchange',fn)
    }
    return {
        bindEvents,
        url:window.location.hash.slice(1) || '/'
    }
}
class Router{
    constructor(options){
        this.history = options.history
        this.routes = options.routes
        this.current = ref(this.history.url)

        this.history.bindEvents(()=>{
            this.current.value = window.location.hash.slice(1)
        })
    }
    install(app){
        app.provide(ROUTER_KEY,this)
    }
}

export {createRouter,createWebHashHistory,useRouter}
```

有了上面这段代码，我们回到src/router/index.js中，可以看到下面代码的使用方式，我们使用createWebHashHistory作为history参数，使用routes作为页面的参数传递给createRouter函数。

```javascript
import {
    createRouter,
    createWebHashHistory,
} from './grouter/index'
const router = createRouter({
  history: createWebHashHistory(),
  routes
})
```

下一步，我们需要注册两个内置组件router-view和router-link。在createRouter创建的Router实例上，current返回当前的路由地址，并且使用ref包裹成响应式的数据。router-view组件的功能，就是current发生变化的时候，去匹配current地址对应的组件，然后动态渲染到router-view就可以了。

我们在src/router/grouter下新建RouterView.vue，写出下面的代码。在代码中，我们首先使用useRouter获取当前路由的实例；然后通过当前的路由，也就是router.current.value的值，在用户路由配置route中计算出匹配的组件；最后通过计算属性返回comp变量，在template内部使用component组件动态渲染。

```xml
<template>
    <component :is="comp"></component>
</template>
<script setup>

import {computed } from 'vue'
import { useRouter } from '../grouter/index'

let router = useRouter()

const comp = computed(()=>{
    const route = router.routes.find(
        (route) => route.path === router.current.value
    )
    return route?route.component : null
})
</script>
```

在上面的代码中，我们的目的是介绍vue-router的大致原理。之后，在课程的源码篇中，我们会在《前端路由原理：vue-router 源码剖析》这一讲完善这个函数的路由匹配逻辑，并让这个函数支持正则匹配。

有了RouterView组件后，我们再来实现router-link组件。我们在grouter下面新建文件RouterILink.vue，并写入下面的代码。代码中的template依然是渲染一个a标签，只是把a标签的href属性前面加了个一个#， 就实现了hash的修改。

```xml
<template>
    <a :href="'#'+props.to">
        <slot />
    </a>
</template>

<script setup>
import {defineProps} from 'vue'
let props = defineProps({
    to:{type:String,required:true}
})

</script>
```

然后，回到grouter/index.js中，我们注册router-link和router-view这两个组件, 这样hash模式的迷你vue-router就算实现了。这里我演示了支持hash模式迷你vue-router，那你不妨进一步思考一下，history模式又该如何实现。

```javascript
import {ref,inject} from 'vue'
import RouterLink from './RouterLink.vue'
import RouterView from './RouterView.vue'
class Router{
    ....
    install(app){
        app.provide(ROUTER_KEY,this)
        app.component("router-link",RouterLink)
        app.component("router-view",RouterView)
    }
}
```

**实际上，vue-router还需要处理很多额外的任务，比如路由懒加载、路由的正则匹配等等**。在今天了解了vue-router原理之后，等到课程最后一部分剖析vue-router源码的那一讲时，你就可以真正感受到“玩具版”的router和实战开发中的router的区别。

## vue-router实战要点

了解了vue-router的原理后，我们再来介绍一下vue-router在实战中的几个常见功能。

首先是在**路由匹配的语法**上，vue-router支持动态路由。例如我们有一个用户页面，这个页面使用的是User组件，但是每个用户的信息都不一样，需要给每一个用户配置单独的路由入口，这时就可以按下面代码中的样式来配置路由。

在下面的代码中，冒号开头的id就是路由的动态部分，会同时匹配/user/dasheng和/user/geektime， 这一部分的详细内容你可以参考[官方文档的路由匹配语法部分](https://next.router.vuejs.org/zh/guide/essentials/route-matching-syntax.html)。

```javascript
const routes = [
  { path: '/users/:id', component: User },
]
```

然后是在实战中，对于有些页面来说，只有管理员才可以访问，普通用户访问时，会提示没有权限。这时就需要用到vue-router的**导航守卫功能**了，也就是在访问路由页面之前进行权限认证，这样可以做到对页面的控制，也就是只允许某些用户可以访问。

此外，在项目庞大之后，如果首屏加载文件太大，那么就可能会影响到性能。这个时候，我们可以使用vue-router的**动态导入功能**，把不常用的路由组件单独打包，当访问到这个路由的时候再进行加载，这也是vue项目中常见的优化方式。

关于vue-router实战中的种种优化和注意点，在课程后续的15-19讲，也就是实战痛点中，我会借助实战场景，挨个给你讲解。

## 总结

好，这一讲的主要内容就讲完了，我们来总结一下今天学到的内容。首先，我们回顾了前后端开发模式的演变，也即前端项目经历的从最初的嵌入到后端内部发布，再到现在的前后端分离的过程，而这一过程也见证了前端SPA应用的发展。

然后，我们讲到了前端路由实现的两种方式，也即通过监听不同的浏览器事件，来实现hash模式和history模式。之后，根据这个原理，我们手写了一个迷你的vue-router，通过createRouter创建路由实例，并在app.use函数内部执行router-link和router-view组件的注册，最后在router-view组件内部动态的渲染组件。

在这一讲的最后，我还给你简单说明了一下vue-router实战中常见的一些痛点。vue-router进一步实战的内容，比如权限认证、页面懒加载等功能，在课程后面的15-19讲中还会详细展开。相信今天这一讲结束后，你一定对vue-router有了更加新的理解。

## 思考题

最后给你留个思考题，今天我们只用了大概60行代码，就实现了hash模式的迷你vue-router，那你还可以思考一下，支持history模式的迷你vue-router又该如何实现呢？

欢迎在留言区分享你的答案，也欢迎你把这一讲分享给你的朋友们，我们下一讲见！
<div><strong>精选留言（15）</strong></div><ul>
<li><span>ll</span> 👍（50） 💬（5）<p>本节又是收获满满，巩固加回顾了关于前端路由的整体知识结构，有一下几点：

1. 什么是路由
   所谓 router 是干什么的？是指 route 的，这里中文翻译的是 “路”。何为“路由”，可能是“路由哪里 
   来&quot;；这里的“路”，广义上来说是“资源”，可以是“页面”，也可以是 json 音视频等等。

   如果把路由具象化，它是这么个东西；你告诉它一串神秘的代码（地址，url等），它给你“宝贵的资
   源”，它就是个“指路的”。

   路由是“天然”存在的，因为我们所有在网上的行为本质都是向“某个地方”要“某些资源”

 2. 前后端路由的区别的补充
    传统方式与SPA“页面跳转”的问题涉及一个核心的问题，是“导航流程”，具体可以参考，李兵老师 
    《浏览器工作原理与实践》中导航流程一节。

    导航流程简单说，就是浏览器地址栏输入地址后，到浏览器准备渲染页面前这个阶段。开始流程的 
    一个标志，就是浏览器标签页标题左边开始转圈圈。

    传统的开发模式写出的页面，在每一次请求网络资源的过程，理论上都有这个流程。这可能就是两者 
    之间性能差异所在

    而 SPA 开发模式，网络资源用 XMLHttpRequest 调用，页面部分用JS“模拟”页面刷新。这里JS模拟部
    分就是现在所学 vue-router 的工作。

 3. 关于路由实现
    总结下，时间以2014年，HTML5标准作为分野，分两个部分
    – API：location.hash；Event：hashchange
    – API：history.pushState，history.replaceState；Event：popstate

    这个就是前端路由的实现核心，如果对具体API感兴趣，可以参考《Javascript 高级程序设计》第4
    版，12章，关于 BOM 的描述。

    大致意思是 hash 的改变不触发页面 reloads；pushState，replaceState 改变 history 也不触发
    reloads。浏览器的这种行为，是根据 HTML5 这个标准实现的

    然后，第一个API支持了路由的 hash 模式，在这之前 hash 的应用 &lt;a id=&quot;xxx&quot;&gt; 在页面中的定位，
    第二个API支持了路由的 history 模式，但这个需要后端配合调整下后端路由；为什么，试着将要跳 
    转的地址复制到浏览器地址栏，然后按回车，分析下页面渲染的过程，大概就清楚了。</p>2021-11-10</li><br/><li><span>Kevin</span> 👍（7） 💬（4）<p>关于webHashHistory,和webHistory 我这里有一个实践要注意的点，不知是否正确。
就是是否需要服务器这个角色参与。
whh，完全是在浏览器中完成的路由行为。
wh 可能是要有服务器参与的 
这一点，在最近的项目中，将vue项目打包直接放到Android assert目录下时，使用两种路由一个404, 一个正常，后续改成了whh了

请大佬，解惑。</p>2021-11-10</li><br/><li><span>Geek_4578dc</span> 👍（3） 💬（1）<p>大圣 实战代码仓库地址 能发一下吗</p>2021-11-11</li><br/><li><span>balabla</span> 👍（2） 💬（1）<p>大圣老师，看完之后，仍有几个问题，求翻牌+1
1.能说下vue-router3.x到vue-router4.x有什么需要重点关注的地方嘛
2.vue-router3.x和vue-router4.x 从底层实现原理上，是否有变化
3.代码里current 的响应式用的 ref 和用vue.util.definereactive 效果一样嘛</p>2021-11-17</li><br/><li><span>Jerry.L</span> 👍（1） 💬（1）<p>大圣老师，我跟你一样的代码，为什么在命令行提示：[@vue&#47;compiler-sfc] `defineProps` is a compiler macro and no longer needs to be imported.然后在浏览器控制台又提示：Uncaught SyntaxError: The requested module &#39;&#47;src&#47;router&#47;grouter&#47;index.js&#39; does not provide an export named &#39;default&#39;。</p>2022-01-12</li><br/><li><span>Aaron</span> 👍（1） 💬（1）<p>老师好，调用 pushState replaceState 并不会触发 popstate 事件，监听通常需要 hack 这两个 api。
https:&#47;&#47;developer.mozilla.org&#47;en-US&#47;docs&#47;Web&#47;API&#47;PopStateEvent#:~:text=Note%3A%20Just%20calling%20history.pushState()%20or%20history.replaceState()%20won%27t%20trigger%20a%20popstate%20event.</p>2021-12-06</li><br/><li><span>风一样</span> 👍（1） 💬（3）<p>老师请问Router对象的install，是在哪里用呢？在源码中没有看到，还有install函数的参数，是什么对象呢？</p>2021-11-23</li><br/><li><span>香橙派来的</span> 👍（1） 💬（1）<p>有了 RouterView 组件后，我们再来实现 router-link 组件。我们在 grouter 下面新建文件 RouterILnk.vue，并写入下面的代码。代码中的 template 依然是渲染一个 a 标签，只是把 a 标签的 href 属性前面加了个一个 #， 就实现了 hash 的修改。

老师，这一段中的 “新建文件RouterILnk.vue ” 与下文的注册 “import RouterLink from &#39;.&#47;RouterLink.vue&#39; ”的文件名字对不上，应该是打错了，会找不到资源</p>2021-11-17</li><br/><li><span>@</span> 👍（1） 💬（1）<p>
&lt;template&gt;
    &lt;a :href=&quot;&#39;#&#39;+props.to&quot;&gt;
        &lt;slot &#47;&gt;
    &lt;&#47;a&gt;
&lt;&#47;template&gt;

&lt;script setup&gt;
let props = defineProps({
    to:{type:String,required:true}
})

&lt;&#47;script&gt;

这里是否需要引入下defineProps，大段代码部分能否内部写点注释
建议老师跟着文章里的代码打一遍，看看能不能跑通
代码上 有些马虎  是否是从课件里粘出来的时候整漏了</p>2021-11-11</li><br/><li><span>关关君</span> 👍（1） 💬（4）<p>很早啊就知道History这个API了但是没用过也用不上，但今天用History写路由的时候，看了API才发现使用history.pushState()方法的时候不会触发 popstate 这个事件，只有当浏览器操作行为的时候才会触发，就比如back forward。
所以在实现的时候调用完pushState之后我手动修改的current.value 的值才成功了。</p>2021-11-11</li><br/><li><span>海阔天空</span> 👍（1） 💬（2）<p>现在一般都用history路由了吧，history路由与html5的配合更好，能充分利用html5的特性，比如html5中监听滚动条的状态等，history都可以监听</p>2021-11-11</li><br/><li><span>拼搏、进取</span> 👍（1） 💬（1）<p>const comp = computed(()=&gt;{
    const route = router.routes[0].children.find(
        (route) =&gt; route.path === router.current.value    )

    return route?route.component : null
})
大圣老师， router.routes[0].children，这里报错了。我改成outer.routes.find()......</p>2021-11-10</li><br/><li><span>一线蓝光</span> 👍（1） 💬（2）<p>在计算匹配的组件时，我们直接取得 children 匹配即可。这里我使用children匹配不上，直接使用router.routes进行的匹配， 麻烦问下是什么原因呢</p>2021-11-10</li><br/><li><span>Devo Zou</span> 👍（0） 💬（1）<p>function createWebHistory() {
  function bindEvents(fn) {
    window.addEventListener(&quot;popstate&quot;, fn);
  }
  return {
    bindEvents,
    url: window.location.pathname || &quot;&#47;&quot;,
  };
}

另外再把RouterLink里面的a标签href的 &#39;#&#39; 去掉就可以实现history 模式了。不知道这样实现对不对[捂脸]
</p>2021-11-26</li><br/><li><span>bugu</span> 👍（0） 💬（1）<p>本期bug题解：https:&#47;&#47;github.com&#47;HaoChunYang&#47;vue3-class&#47;blob&#47;main&#47;todo-list&#47;src&#47;router&#47;hrouter&#47;RouterView.vue
哈哈</p>2021-11-11</li><br/>
</ul>