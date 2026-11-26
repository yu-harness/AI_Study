你好，我是winter。

我们在前面的HTML部分的课程中，已经学习了语义标签。这些标签涵盖了我们日常开发用到的多数标签，也是我们编写代码时最常用的一批标签。

但是我们今天要讲的标签，重要性丝毫不弱于语义类标签，这就是页面元信息类标签。

我们可以先来了解一下什么是元信息类标签。所谓元信息，是指描述自身的信息，元信息类标签，就是HTML用于描述文档自身的一类标签，它们通常出现在head标签中，一般都不会在页面被显示出来（与此相对，其它标签，如语义类标签，描述的是业务）。

元信息多数情况下是给浏览器、搜索引擎等机器阅读的，有时候这些信息会在页面之外显示给用户，有时候则不会。

元信息类标签数量不多，我在这里就逐一为你介绍一下。

## head标签

首先我们先来了解一下head标签，head标签本身并不携带任何信息，它主要是作为盛放其它语义类标签的容器使用。

head标签规定了自身必须是html标签中的第一个标签，它的内容必须包含一个title，并且最多只能包含一个base。如果文档作为iframe，或者有其他方式指定了文档标题时，可以允许不包含title标签。

## title标签

title标签表示文档的标题，从字面上就非常容易理解。这里我就讲讲需要注意的地方。

你还记得吗，我们的语义类标签中也有一组表示标题的标签：h1-h6。

heading 和 title 两个英文单词意义区分十分微妙，在中文中更是找不到对应的词汇来区分。但是实际使用中，两者确实有一定区别。

在HTML标准中，特意讨论了这个问题。我们思考一下，假设有一个介绍蜜蜂跳舞求偶仪式的科普页面，我们试着把以下两个文字分别对应到title和h1。

- 蜜蜂求偶仪式舞蹈
- 舞蹈

在听/看正确答案前，你不妨先想想，自己的答案是什么呢？为什么？

好了，思考之后，我们来看看正确答案。正确答案是“蜜蜂求偶仪式舞蹈”放入title，“舞蹈”放入h1。

我来讲一讲为什么要这样放呢？这主要是考虑到title作为元信息，可能会被用在浏览器收藏夹、微信推送卡片、微博等各种场景，这时侯往往是上下文缺失的，所以title应该是完整地概括整个网页内容的。

而h1则仅仅用于页面展示，它可以默认具有上下文，并且有链接辅助，所以可以简写，即便无法概括全文，也不会有很大的影响。

## base标签

base标签实际上是个历史遗留标签。它的作用是给页面上所有的URL相对地址提供一个基础。

base标签最多只有一个，它改变全局的链接地址，它是一个非常危险的标签，容易造成跟JavaScript的配合问题，所以在实际开发中，我比较建议你使用JavaScript来代替base标签。

## meta标签

meta标签是一组键值对，它是一种通用的元信息表示标签。

在head中可以出现任意多个meta标签。一般的meta标签由name和content两个属性来定义。name表示元信息的名，content则用于表示元信息的值。

它基本用法是下面这样的，你也可以自己动手尝试一下：

```
  <meta name=application-name content="lsForums">
```

这个标签表示页面所在的web-application，名为IsForums。

这里的name是一种比较自由的约定，HTTP标准规定了一些name作为大家使用的共识，也鼓励大家发明自己的name来使用。

除了基本用法，meta标签还有一些变体，主要用于简化书写方式或者声明自动化行为。下面我就挑几种重点的内容来分别讲解一下。

### 具有charset属性的meta

从HTML5开始，为了简化写法，meta标签新增了charset属性。添加了charset属性的meta标签无需再有name和content。

```
  <meta charset="UTF-8" >
```

charset型meta标签非常关键，它描述了HTML文档自身的编码形式。因此，我建议这个标签放在head的第一个。

```
<html>
<head>
<meta charset="UTF-8">
……
```

这样，浏览器读到这个标签之前，处理的所有字符都是ASCII字符，众所周知，ASCII字符是UTF-8和绝大多数字符编码的子集，所以，在读到meta之前，浏览器把文档理解多数编码格式都不会出错，这样可以最大限度地保证不出现乱码。

一般情况下，HTTP服务端会通过http头来指定正确的编码方式，但是有些特殊的情况如使用file协议打开一个HTML文件，则没有http头，这种时候，charset meta就非常重要了。

## 具有http-equiv属性的meta

具有http-equiv属性的meta标签，表示执行一个命令，这样的meta标签可以不需要name属性了。

例如，下面一段代码，相当于添加了content-type这个http头，并且指定了http编码方式。

```
<meta http-equiv="content-type" content="text/html; charset=UTF-8">
```

除了content-type，还有以下几种命令：

- content-language 指定内容的语言；
- default-style 指定默认样式表；
- refresh 刷新；
- set-cookie 模拟http头set-cookie，设置cookie；
- x-ua-compatible 模拟http头x-ua-compatible，声明ua兼容性；
- content-security-policy 模拟http头content-security-policy，声明内容安全策略。

### name为viewport的meta

实际上，meta标签可以被自由定义，只要写入和读取的双方约定好name和content的格式就可以了。

我们来介绍一个meta类型，它没有在HTML标准中定义，却是移动端开发的事实标准：它就是name为viewport的meta。

这类meta的name属性为viewport，它的content是一个复杂结构，是用逗号分隔的键值对，键值对的格式是key=value。

例如：

```
<meta name="viewport" content="width=500, initial-scale=1">
```

这里只指定了两个属性，宽度和缩放，实际上viewport能控制的更多，它能表示的全部属性如下：

- width：页面宽度，可以取值具体的数字，也可以是device-width，表示跟设备宽度相等。
- height：页面高度，可以取值具体的数字，也可以是device-height，表示跟设备高度相等。
- initial-scale：初始缩放比例。
- minimum-scale：最小缩放比例。
- maximum-scale：最大缩放比例。
- user-scalable：是否允许用户缩放。

对于已经做好了移动端适配的网页，应该把用户缩放功能禁止掉，宽度设为设备宽度，一个标准的meta如下：

```
<meta name="viewport" content="width=device-width,initial-scale=1,minimum-scale=1,maximum-scale=1,user-scalable=no">
```

## 其它预定义的meta

在HTML标准中，还定义了一批meta标签的name，可以视为一种有约定的meta，我在这里列出来，你可以简单了解一下。

application-name：如果页面是Web application，用这个标签表示应用名称。

- author: 页面作者。
- description：页面描述，这个属性可能被用于搜索引擎或者其它场合。
- generator: 生成页面所使用的工具，主要用于可视化编辑器，如果是手写HTML的网页，不需要加这个meta。
- keywords: 页面关键字，对于SEO场景非常关键。
- referrer: 跳转策略，是一种安全考量。
- theme-color: 页面风格颜色，实际并不会影响页面，但是浏览器可能据此调整页面之外的UI（如窗口边框或者tab的颜色）。

## 结语

在本课，我们又学习了一批标签，它们是文档用于描述自身的元信息类标签。一些元信息标签可以产生实际的行为，掌握它们对于我们编写代码是必须的。

另一些元信息仅仅是对页面的描述，掌握它们可以使我们编写的页面跟各种浏览器、搜索引擎等结合地更好。

主要包括下面这些内容。

- head：元信息的容器。
- title：文档标题。
- base：页面的基准URL。
- meta: 元信息通用标签。

我们还展开介绍了几种重要的meta标签，charset表示页面编码，http-equiv表示命令，还介绍了一些有约定的meta名称。

最后，给你留一个问题，你还见过哪些meta标签的用法？欢迎留言告诉我。
<div><strong>精选留言（15）</strong></div><ul>
<li><span>火云邪神0007</span> 👍（203） 💬（6）<p>老师，我家的猫不让我给他剪指甲，怎么办？</p>2019-02-23</li><br/><li><span>AICC</span> 👍（158） 💬（1）<p>&lt;meta http-equiv=&quot;X-UA-Compatible&quot; content=&quot;IE=edge,chrome=1&quot;&gt;
&lt;!-- 默认使用最新浏览器 --&gt;
&lt;meta http-equiv=&quot;Cache-Control&quot; content=&quot;no-siteapp&quot;&gt;
&lt;!-- 不被网页(加速)转码 --&gt;
&lt;meta name=&quot;robots&quot; content=&quot;index,follow&quot;&gt;
&lt;!-- 搜索引擎抓取 --&gt;
&lt;meta name=&quot;renderer&quot; content=&quot;webkit&quot;&gt;
&lt;meta name=&quot;viewport&quot; content=&quot;width=device-width, initial-scale=1, maximum-scale=1, minimum-scale=1, user-scalable=no, minimal-ui&quot;&gt;
&lt;meta name=&quot;apple-mobile-web-app-capable&quot; content=&quot;yes&quot;&gt;
&lt;!-- 删除苹果默认的工具栏和菜单栏 --&gt;
&lt;meta name=&quot;apple-mobile-web-app-status-bar-style&quot; content=&quot;black-translucent&quot;&gt;
&lt;!-- 设置苹果工具栏颜色 --&gt;</p>2019-02-21</li><br/><li><span>CC</span> 👍（38） 💬（2）<p>阅读完今天的文章，才感觉自己其实不懂 meta，之前对 meta 的细节缺少分类和整理。感谢老师。

回到老师的问题，我平时还见过以下三种（组）标签：

1. Open Graph 的标签组，包括 title, type, URL, site_name, description 和 image，是为 Facebook 分享提供信息；

2. Twitter 的标签组，包括 card, title, description 和 image，是为 Twitter 分享提供信息；

3. msapplication 的标签组，包括 TileColor 和 TileImage，是为 Windows 8 以及以上系统识别 favicons 用的。
</p>2019-02-21</li><br/><li><span>MarlboroKay</span> 👍（8） 💬（1）<p>meta基本用法：
  &lt;meta name=application-name content=&quot;lsForums&quot;&gt;
name = application-name 是不是少了 “”
name = &quot;applicaiton-name&quot; ?</p>2019-02-21</li><br/><li><span>靠人品去赢</span> 👍（5） 💬（1）<p>突然想问一下，老是本尊是不是一个猫奴啊，感觉很喜欢那猫举例子做封面什么的。</p>2019-02-21</li><br/><li><span>有铭</span> 👍（4） 💬（1）<p>我是说为什么viewport在html标准里找不到，一直很疑惑是从哪里蹦出来的，搞了半天原来不是html标准是行业约定</p>2019-02-23</li><br/><li><span>阿成</span> 👍（2） 💬（1）<p>常见的还有
format-detection 禁止 iPhone 的自动识别
</p>2019-02-21</li><br/><li><span>丘丘</span> 👍（11） 💬（2）<p>上面评论中的
&lt;meta name=&quot;apple-mobile-web-app-capable&quot; content=&quot;yes&quot;&gt;
&lt;!-- 删除苹果默认的工具栏和菜单栏 --&gt;
&lt;meta name=&quot;apple-mobile-web-app-status-bar-style&quot; content=&quot;black-translucent&quot;&gt;
&lt;!-- 设置苹果工具栏颜色 --&gt;
这两条，我试着似乎没有效果。
keywords这个属性，理论上对seo有作用，但是我随便进行了搜索，打开排名第一页的几个网站，都没有这么属性，是不是现在这种简单的seo打法已经被放弃了呢？</p>2019-03-24</li><br/><li><span>LiH</span> 👍（10） 💬（1）<p>&lt;meta name=&quot;format-detection&quot; content=&quot;telephone=no&quot;&gt;
&lt;meta name=&quot;format-detection&quot; content=&quot;date=no&quot;&gt;
&lt;meta name=&quot;format-detection&quot; content=&quot;address=no&quot;&gt;
&lt;meta name=&quot;format-detection&quot; content=&quot;email=no&quot;&gt;
关闭iOS上的内容识别</p>2019-03-01</li><br/><li><span>码屁</span> 👍（5） 💬（0）<p>@丘丘 你难道忘了 竞价排名[滑稽]</p>2019-05-15</li><br/><li><span>Alen</span> 👍（5） 💬（0）<p>http:&#47;&#47;www.alenqi.site&#47;2018&#47;03&#47;04&#47;complete-tags&#47; 之前总结的</p>2019-05-08</li><br/><li><span>Geek_fc1551</span> 👍（2） 💬（0）<p> &lt;meta name=&quot;apple-mobile-web-app-status-bar-style&quot; content=&quot;black-translucent&quot; &#47;&gt; 
  &lt;!-- 添加到主屏后的标题 --&gt; 
  &lt;meta name=&quot;apple-mobile-web-app-title&quot; content=&quot;标题&quot; &#47;&gt; 
  &lt;!-- 忽略数字自动识别为电话号码 --&gt; 
  &lt;meta content=&quot;telephone=no&quot; name=&quot;format-detection&quot; &#47;&gt; 
  &lt;!-- 忽略识别邮箱 --&gt; 
  &lt;meta content=&quot;email=no&quot; name=&quot;format-detection&quot; &#47;&gt; 
  &lt;meta name=&quot;apple-itunes-app&quot; content=&quot;app-id=myAppStoreID, 
affiliate-data=myAffiliateData, app-argument=myURL&quot; &#47;&gt; </p>2019-12-04</li><br/><li><span>July</span> 👍（2） 💬（0）<p>老师好，keywords 现在对seo还有用吗？</p>2019-02-28</li><br/><li><span>老纪程序</span> 👍（1） 💬（0）<p>style script  link  平时还看到有这几个</p>2021-12-03</li><br/><li><span>渴望做梦</span> 👍（1） 💬（0）<p>&lt;meta name=&quot;renderer&quot; content=&quot;webkit|ie-comp|ie-stand&quot;&gt;
对于多核浏览器，控制浏览器以哪种类型内核来显示，好像是 360 浏览器首先主导的</p>2019-07-08</li><br/>
</ul>