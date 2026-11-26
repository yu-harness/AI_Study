你好，我是winter，今天我们来学习一下CSS的渲染相关的属性。

我们在布局篇讲到，CSS的一些属性决定了盒的位置，那么今天我讲到的属性就决定了盒如何被渲染。

按照惯例，还是先从简单得讲起，首先我们来讲讲颜色。

## 颜色的原理

首先我们来讲讲颜色，最常见的颜色相关的属性就是 `color` 和 `background-color`。

这两个属性没什么好讲的，它们分别表示文字颜色和背景颜色，我们这里重点讲讲颜色值。

### RGB颜色

我们在计算机中，最常见的颜色表示法是RGB颜色，**它符合光谱三原色理论：红、绿、蓝三种颜色的光可以构成所有的颜色。**

![](https://static001.geekbang.org/resource/image/7f/a1/7f5bf39cbe44e36758683a674f9fcfa1.png?wh=1268%2A1268)

为什么是这三种颜色呢？这跟人类的视神经系统相关，人类的视觉神经分别有对红、绿、蓝三种颜色敏感的类型。

顺便提一下，人类对红色的感觉最为敏感，所以危险信号提示一般会选择红色；而红绿色盲的人，就是红和绿两种神经缺失一种。其它的动物视觉跟人可能不太一样，比如皮皮虾拥有16种视锥细胞，所以我猜它们看到的世界一定特别精彩。

现代计算机中多用 0 - 255 的数字表示每一种颜色，这正好占据了一个字节，每一个颜色就占据三个字节。

这个数字远远超过了人体的分辨能力，因此，上世纪90年代刚推出这样的颜色系统的时候，它被称作真彩色。早年间还有更节约空间，但是精度更低的16色、256色、8位色和16位色表示法。

红绿蓝三种颜色的光混合起来就是白光，没有光就是黑暗，所以在RGB表示法中，三色数值最大表示白色，三色数值为0表示黑色。

### CMYK颜色

如果你上过小学美术课，应该听过“红黄蓝”三原色的说法，这好像跟我们说的不太一样。实际上是这样的，颜料显示颜色的原理是它吸收了所有别的颜色的光，只反射一种颜色，所以颜料三原色其实是红、绿、蓝的补色，也就是：品红、黄、青。因为它们跟红、黄、蓝相近，所以有了这样的说法。

![](https://static001.geekbang.org/resource/image/15/1b/15fefe9f80ec8e1f7bd9ecd223feb61b.png?wh=1272%2A1272)

在印刷行业，使用的就是这样的三原色（品红、黄、青）来调配油墨，这种颜色的表示法叫做CMYK，它用一个四元组来表示颜色。

你一定会好奇，为什么它比三原色多了一种，其实答案并不复杂，在印刷行业中，黑色颜料价格最低，而品红、黄、青颜料价格较贵，如果要用三原色调配黑色，经济上是不划算的，所以印刷时会单独指定黑色。

对CMYK颜色表示法来说，同一种颜色会有多种表示方案，但是我们参考印刷行业的习惯，会尽量优先使用黑色。

### HSL颜色

好了，讲了这么多，其实还没有涉及今天的主角：HSL颜色。接下来我们就讲一讲。

我们刚才讲的颜色是从人类的视觉原理建模，应该说是十分科学了。但是，人类对颜色的认识却并非来自自己的神经系统，当我们把阳光散射，可以得到七色光：红橙黄绿蓝靛紫，实际上，阳光接近白光，它包含了各种颜色的光，它散射之后，应该是个基本连续的。这说明对人的感知来说，颜色远远大于红、绿、蓝。

因此，HSL这样的颜色模型被设计出来了，它用一个值来表示人类认知中的颜色，我们用专业的术语叫做色相（H）。加上颜色的纯度（S）和明度（L），就构成了一种颜色的表示。

![](https://static001.geekbang.org/resource/image/a3/ce/a3016a6ff178870d6dba23f807b0dfce.png?wh=500%2A395)

在这里，我需要特别推荐HSL颜色，因为它是一种语义化的颜色。当我们对一张图片改变色相时，人们感知到的是“图片的颜色变了”。这里先容我卖个关子，具体的例子待我们讲完了渐变再看。

### 其它颜色

接下来我们讲一讲RGBA，RGBA是代表Red（红色）、Green（绿色）、Blue（蓝色）和Alpha的色彩空间。RGBA颜色被用来表示带透明度的颜色，实际上，Alpha通道类似一种颜色值的保留字。在CSS中，Alpha通道被用于透明度，所以我们的颜色表示被称作 RGBA，而不是RGBO（Opacity）。

为了方便使用，CSS还规定了名称型的颜色，它内置了大量（140种）的颜色名称。不过这里我要挑出两个颜色来讲一讲：金（gold）和银（silver）。

如果你使用过这两个颜色，你会发现，金（gold）和银（silver）的视觉表现跟我们想象中的金色和银色相差甚远。与其被叫做金色和银色，它们看起来更像是难看的暗黄色和浅灰色。

为什么会这样呢？在人类天然的色彩认知中，实际上混杂了很多其它因素，金色和银色不仅仅是一种颜色，它还意味着一定的镜面反光程度，在同样的光照条件下，金属会呈现出更亮的色彩，这并非是用一个色值可以描述的，这就引出了我们接下来要讲的渐变。

## 渐变

在CSS中，`background-image`这样的属性，可以设为渐变。CSS中支持两种渐变，一种是线性渐变，一种是放射性渐变，我们先了解一下它们的基本用法：

线性渐变的写法是：

```
linear-gradient(direction, color-stop1, color-stop2, ...);
```

这里的direction可以是方向，也可以是具体的角度。例如：

- to bottom
- to top
- to left
- to right
- to bottom left
- to bottom right
- to top left
- to top right
- 120deg
- 3.14rad

以上这些都是合理的方向取值。

color-stop是一个颜色和一个区段，例如：

- rgba(255,0,0,0)
- orange
- yellow 10%
- green 20%
- lime 28px

我们组合一下，产生一个“真正的金色”的背景：

```HTML
<style>
#grad1 {
    height: 200px;
    background: linear-gradient(45deg, gold 10%, yellow 50%, gold 90%); 
}
</style>
<div id="grad1"></div>
```

放射性渐变需要一个中心点和若干个颜色：

```
radial-gradient(shape size at position, start-color, ..., last-color);
```

当我们应用的每一种颜色都是HSL颜色时，就产生了一些非常有趣的效果，比如，我们可以通过变量来调整一个按钮的风格：

```HTML
<style>
.button {
    display: inline-block;
    outline: none;
    cursor: pointer;
    text-align: center;
    text-decoration: none;
    font: 14px/100% Arial, Helvetica, sans-serif;
    padding: .5em 2em .55em;
    text-shadow: 0 1px 1px rgba(0,0,0,.3);
    border-radius: .5em;
    box-shadow: 0 1px 2px rgba(0,0,0,.2);
    color: white;
    border: solid 1px ;
}

</style>
<div class="button orange">123</div>

```

```JavaScript
var btn = document.querySelector(".button");
var h = 25;
setInterval(function(){
  h ++;
  h = h % 360;
  btn.style.borderColor=`hsl(${h}, 95%, 45%)`
  btn.style.background=`linear-gradient(to bottom,  hsl(${h},95%,54.1%),  hsl(${h},95%,84.1%))`
},100);
```

## 形状

CSS中的很多属性还会产生形状，比如我们常见的属性：

- border
- box-shadow
- border-radius

这些产生形状的属性非常有趣，我们也能看到很多利用它们来产生的CSS黑魔法。然而，这里我有一个相反的建议，我们仅仅把它们用于基本的用途，把border用于边框、把阴影用于阴影，把圆角用于圆角，所有其它的场景，都有一个更好的替代品：datauri+svg。

## 总结

今天我们介绍了CSS中渲染相关的属性：颜色和形状。

我们重点介绍了CSS的颜色系统，从颜色基本原理讲解了RGB颜色、CMYK颜色和HSV颜色，我们还讲解了Alpha通道。

接下来我们又讲了颜色的一个重要应用：渐变，我们可以把渐变看作是一个更复杂的颜色，它非常实用，能够用渐变绘制很多的图像。

最后我们讲解了形状相关的属性，以及SVG应用的一个小技巧。

### 思考题

![](https://static001.geekbang.org/resource/image/0f/ac/0f6f4cc6d564df9986e0108cb8a427ac.jpg?wh=1920%2A1440)

折衷鹦鹉是一种可爱的鸟类，但是雄性折衷鹦鹉居然是跟雌性颜色不一样！你能用JavaScript和canvas，把这只雄性折衷鹦鹉变成跟雌性一样可爱的红色吗？
<div><strong>精选留言（14）</strong></div><ul>
<li><span>阿成</span> 👍（35） 💬（7）<p>怎么说呢，要想完美的转换... 好难... 仅靠单像素颜色来识别出鹦鹉的轮廓还是不太可行... 
也许把周围像素的颜色考虑进去是个办法... 不过这图挺大的...

&lt;!DOCTYPE html&gt;
&lt;html lang=&quot;en&quot;&gt;
&lt;head&gt;
  &lt;meta charset=&quot;UTF-8&quot;&gt;
  &lt;title&gt;Document&lt;&#47;title&gt;
  &lt;style type=&quot;text&#47;css&quot;&gt;
    .bird {
      width: 400px;
      height: calc(1440 * 400 &#47; 1920 * 1px);
    }
    canvas.bird {
      background: #ccc;
    }
  &lt;&#47;style&gt;
&lt;&#47;head&gt;
&lt;body&gt;
  &lt;img id=&quot;img&quot; class=&quot;bird&quot; src=&quot;.&#47;bird.jpg&quot;&gt;
  &lt;canvas id=&quot;canvas&quot; width=&quot;1920&quot; height=&quot;1440&quot; class=&quot;bird&quot;&gt;&lt;&#47;canvas&gt;

  &lt;script type=&quot;text&#47;javascript&quot;&gt;
    let canvas = document.getElementById(&#39;canvas&#39;)
    let ctx = canvas.getContext(&#39;2d&#39;)
    let img = document.getElementById(&#39;img&#39;)
    img.addEventListener(&#39;load&#39;, () =&gt; {
      ctx.drawImage(img, 0, 0)

      let imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
      let data = imageData.data

      for (let i = 0; i &lt; data.length; i += 4) {
        if (isBird(data, i, canvas.width, canvas.height)) {
          ;[data[i], data[i + 1]] = [data[i + 1] * 1.2, data[i]]
        }
      }

      ctx.putImageData(imageData, 0, 0)
    })

    function isBird (data, i, width, height) {
      let r = data[i]
      let g = data[i + 1]
      let b = data[i + 2]

      let [h, s, l] = rgb2hsl(r, g, b)
      return h &lt; 200 &amp;&amp; h &gt; 80 &amp;&amp; s &gt; 0.23 &amp;&amp; l &lt; 0.84
    }

    function rgb2hsl (r, g, b) {
      let r1 = r &#47; 255
      let g1 = g &#47; 255
      let b1 = b &#47; 255

      let min = Math.min(r1, g1, b1)
      let max = Math.max(r1, g1, b1)

      let l = (min + max) &#47; 2
      let s
      let h

      if (l &lt; 0.5) {
        s = (max - min) &#47; (max + min)
      } else {
        s = (max - min) &#47; (2 - max - min)
      }

      if (max === r1) {
        h = (r1 - b1) &#47; (max - min)
      } else if (max === g1) {
        h = 2 + (b1 - r1) &#47; (max - min)
      } else if (max === b1) {
        h = 4 + (r1 - g1) &#47; (max - min)
      }

      h *= 60

      while (h &lt; 0) {
        h += 360
      }

      return [h, s, l]
    }
  &lt;&#47;script&gt;
&lt;&#47;body&gt;
&lt;&#47;html&gt;
</p>2019-04-28</li><br/><li><span>Peter</span> 👍（24） 💬（2）<p>一步到位：filter: hue-rotate(240deg);
根据HSL色环，绿色在120deg的位置，要变成红色，把色相顺时针旋转240deg或者逆时针120deg即可。</p>2020-06-30</li><br/><li><span>GGFGG</span> 👍（8） 💬（0）<p>CMYK，为什么有K，一方面是成本，另一方面是因为自然界的CMY不能合成纯黑的颜色，所以需要纯黑</p>2019-07-21</li><br/><li><span>sugar</span> 👍（7） 💬（2）<p>我来给个答案吧，乍一看 感觉需要用到很多cv领域的技术，模式识别判定轮廓，然后根据色值不同进行greenToRed转译。后来想了一下，这明明是前端的课程嘛，按cv的解决方案，难道还要把opencv编译到wasm里？转念一想，其实css滤镜就能做这事儿，试了试 几行css代码能做的事 在opencv要引一大堆库 改一大堆参数了</p>2019-11-11</li><br/><li><span>Geek_8rfqh9</span> 👍（2） 💬（0）<p>&lt;!DOCTYPE html&gt;
&lt;html&gt;
  &lt;head&gt;
    &lt;title&gt;鹦鹉变成红色&lt;&#47;title&gt;
    &lt;script&gt;
    	function loadImg() {
           let img = new Image
           img.src = &quot;yingwu.jpg&quot;
           
           img.onload = function () {
           	  drawCanvas(img)
           }
    	}

    	function drawCanvas(img) {
          let canvas = document.getElementById(&#39;canvas&#39;)
          canvas.width = img.width
          canvas.height = img.height
          let context = canvas.getContext(&#39;2d&#39;)

          context.drawImage(img, 0, 0);
          
         &#47;&#47;context.clearRect(200,432, 1110, 670);
          let sectionImg = context.getImageData(200, 432, 1110, 75	0);
          let imgData = sectionImg.data;

          for(let i =1; i &lt; imgData.length;i += 4) {
          	  if (imgData[i-1] &lt; imgData[i]) {
                 let temp = imgData[i-1]
                 imgData[i - 1] = imgData[i]
                 imgData[i] = temp
          	  }
          	
          }

          context.putImageData(sectionImg, 200, 432); &#47;&#47; 复制代码

    	}
    	document.addEventListener(&#39;DOMContentLoaded&#39;, function(){
          loadImg()
    	})
    	
    &lt;&#47;script&gt;
  &lt;&#47;head&gt;
  &lt;body&gt;
    &lt;canvas id=&quot;canvas&quot;&gt;&lt;&#47;canvas&gt;
  &lt;&#47;body&gt;
&lt;&#47;html&gt;</p>2020-03-01</li><br/><li><span>一路向北</span> 👍（2） 💬（4）<p>老师在末尾提到了border、box-shadow、border-radius可以产生一些CSS黑魔法，而不是只定义边框、阴影和圆角，这里我很想知道，除了基本用途，他们可以产生什么样的黑魔法呢？有没有一些推荐的资料呢？</p>2020-01-03</li><br/><li><span>猫总</span> 👍（1） 💬（0）<p>原本实现控制RGB范围来手动抠图，不过在使用的时候发现并不直观，调整起来很随缘，回看了一遍课程才发现重点是HSL调色，改进之后还是能比较精准（主要是直观）的把鹦鹉给单独替换颜色了</p>2019-07-12</li><br/><li><span>Geek_0bb537</span> 👍（1） 💬（0）<p>winter老师给我讲一下那个presentational attributes 看不懂</p>2019-04-28</li><br/><li><span>Izayoizuki</span> 👍（1） 💬（0）<p>HSL感觉还是绘画游戏原画之类用得多，编程领域反而挺少，无论h5游戏还是客户端游戏理解一般都是rgb&#47;rgba</p>2019-04-28</li><br/><li><span>Aaaaaaaaaaayou</span> 👍（1） 💬（0）<p>canvas可以得到每个像素的rgb分量，是不是把蓝色和红色的值换一下就可以了？</p>2019-04-28</li><br/><li><span>你好，阳光</span> 👍（0） 💬（0）<p>老师，datauri+svg产生形状能举个例子吗？</p>2021-05-07</li><br/><li><span>Corazon</span> 👍（0） 💬（0）<p>&lt;!DOCTYPE html&gt;
&lt;html lang=&quot;en&quot;&gt;

&lt;head&gt;
    &lt;meta charset=&quot;UTF-8&quot;&gt;
    &lt;meta name=&quot;viewport&quot; content=&quot;width=device-width, initial-scale=1.0&quot;&gt;
    &lt;title&gt;text&lt;&#47;title&gt;
    &lt;style&gt;
        &#47;* #canvas {
            width: 200px;
            height: 100px;
        } *&#47;
    &lt;&#47;style&gt;
&lt;&#47;head&gt;

&lt;body&gt;
    &lt;canvas id=&quot;canvas&quot; width=&quot;400&quot; height=&quot;400&quot;&gt;&lt;&#47;canvas&gt;
    &lt;button onclick=&quot;changeColor()&quot;&gt;Change Color&lt;&#47;button&gt;
    &lt;script&gt;
        let canvas = document.getElementById(&quot;canvas&quot;);
        let ctx = canvas.getContext(&quot;2d&quot;);
        let img = new Image();
        img.crossOrigin = &#39;anonymous&#39;;
        img.src = &quot;https:&#47;&#47;static001.geekbang.org&#47;resource&#47;image&#47;0f&#47;ac&#47;0f6f4cc6d564df9986e0108cb8a427ac.jpg&quot;;
        img.onload = function () {
            console.log(canvas.clientWidth);
            console.log(canvas.clientWidth &#47; img.width * img.height);
            ctx.drawImage(img, 0, 0, canvas.clientWidth, canvas.clientWidth &#47; img.width * img.height);
        }
        function changeColor() {
            let imgData = ctx.getImageData(0, 0, canvas.clientWidth, canvas.clientWidth &#47; img.width * img.height);
            let data = imgData.data;
            for (let i = 0; i &lt; data.length; i = i + 4) {
                if (data[i + 1] - data[i] &gt; 40 || data[i] + data[i + 1] + data[i + 2] &lt; 110) {
                    let temp = data[i]
                    data[i] = data[i + 1];
                    data[i + 1] = temp;
                }
            }
            ctx.putImageData(imgData, 0, 0);
        }

    &lt;&#47;script&gt;
&lt;&#47;body&gt;

&lt;&#47;html&gt;</p>2020-12-18</li><br/><li><span>无双</span> 👍（0） 💬（0）<p>请问老师，我后台用的是Tomcat服务器，前端用ajax请求静态资源时会间隔会报412，也就是一次成功进入后台，一次报412，这该怎么解决呢？</p>2019-04-29</li><br/><li><span>Mupernb</span> 👍（0） 💬（0）<p>for(var i=0;i&lt;imgData.data.length;i++){
                [imgData.data[4*i+0],imgData.data[4*i+1]]=[imgData.data[4*i+1],imgData.data[4*i+0]]
            }</p>2019-04-28</li><br/>
</ul>