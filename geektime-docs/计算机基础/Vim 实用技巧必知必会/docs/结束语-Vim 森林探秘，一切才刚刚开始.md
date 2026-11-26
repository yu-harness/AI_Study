你好，我是吴咏炜。

我们的课程到这里就结束了，而你的学习旅程，到这儿只能算是一个小小的休息站。

## 学习的度

对于一个持续发展了 30 年的编辑器，我们显然不可能在一门短小精悍的课程里完整地覆盖它的所有功能。不过，我从来就没打算介绍 Vim 的一切。如果把 Vim 比作一片大森林，我只是一个导游，为你制定了一条旅游路线，带你绕过沼泽地和陷阱，攀上了几座峰顶，让你能够领略到若干美景。如果想在林中长久地居住下去，熟稔各条秘径，你仍然要靠自己去探索。

Vim 的作者 Bram 这么告诫人们不要走到两个极端上去 \[Moolenaar 2007]：

> 你需要马上把文本准备好。所以没有时间读文档或学习新命令。——**你会一直使用原始的命令。**
> 
> 你想学编辑器提供的所有功能，并在任何时候都能使用最高效的命令。——**你会浪费很多时间学习很多你永远不会用到的东西。**

前者的问题很明显，如果你不学习，那你只能使用初级的功能，所以效率一定很低。后者的问题可能不那么明显了：实际上，除了多花时间之外，你很难培养出良好的习惯，形成“肌肉记忆”。而这，恰恰是高效工作的关键之一——不需要想，就知道怎么做，从而可以把头脑和精力投入到更重要的问题上。

在这个课程里，我也只是告诉你基本的原则和技巧，并培养你基本的编辑习惯。回头，在遇到实际问题时，你会需要使用搜索引擎、讨论组等工具来找到问题的答案。

## 学习、积累和分享

我学习 Vim，原本是处于 Linux 下开发的需要，而后慢慢成为一种习惯。回过头来看，Vim 就和 Unix 一样，老而弥坚，经久不衰，不管时代怎样变化，它们却一直没有过时。而同时代我用过的其他 Windows 上的编辑器，如 EditPlus 和 UltraEdit，现在虽然都还在，但是应该已经很少有人提起了吧……

经过几年的学习和使用，我居然也就可以给别人分享我的经验了。我先是在 IBM developerWorks 上发了一系列的三篇 Vim 文章，后面又在 SHLUG（Shanghai Linux User Group）的活动中分享了我的 Vim 使用经验。事后，我在网上看到别人觉得我这个分享做得最好，也是非常的欣慰。

时间快进到今年的年初，我做完了我在极客时间的第一门课程《现代 C++ 实战 30 讲》。当编辑问我还有什么其他可分享的课程时，我立刻想到了 Vim。于是，就有了这个课程。我很喜欢知识分享的过程，因为准备的过程同时也是自我梳理和刷新的过程，毕竟要给别人讲，就不能像自己用的时候那样不求甚解了。让我没预料到的是，在课程中我还向某些积极的同学学了一两手（为了不让你们太骄傲，我就不点名了😉）。知识分享真是一种非常好的活动，于人于己都非常有利。建议大家在工作中也可以多多考虑😇。它唯一的缺点，就是会让自己变得非常忙碌、周末没有休息时间而已😂。

## 高效编辑的诀窍

现在回到 Vim。我们来考虑一下这个“元”问题：**怎么样可以进行高效的编辑？**

事实上，Bram 早就回答过这个问题了。这跟一般的效率改进计划没有本质的区别。我们要做的是：

1. 发现低效的根源
2. 找出更快的方法
3. 形成新的习惯

Vim 的功能也是围绕着这样的模式开发出来的。

比如，我们要找出当前文件中某个符号的使用，在任何编辑器里，都会提供一个搜索的功能。但每次都使用搜索，实际上也是有点麻烦的。Vim 里的 `*` 搜索键和搜索加亮，这两个你目前应当已经习以为常的功能，就是为了解决这种低效而诞生的。而对你，现在更快的方法，就是在配置中启用搜索加亮（目前我们的基本配置里已经启用），并使用 `*` 来搜索光标下的单词。

又比如，我们有一个非常长的函数名，打起来又费力又容易出错。这时候，我们需要找出更快的方法，那就是自动完成。Vim 内置的改进方法是 `<C-N>` 和 `<C-P>` 命令。而我们学到现在的就该知道，YCM 还提供了更现代的模糊完成引擎。用好内置命令，或安装合适的插件，就是我们需要形成的新习惯。

说到这儿，你也看到了，不仅我们的课程不是高效编辑的终点，而且就连 Vim 也不是。Vim 一直在发展，但有人嫌 Vim 发展得不够激进，另外搞了 Neovim。我们这个课程完全没有讨论 Neovim，主要是不想在一个已经很复杂的课题上再增加复杂性（同时也是因为 Neovim 虽然看起来势头不错，但远没到可以尘埃落定、一定会在将来替代 Vim 的程度，再加上两者并不完全兼容……反过来，Neovim 倒是刺激 Vim 更快地添加新功能了）。

抛开 Neovim 不谈，我们还有插件：正是这些辛勤的插件作者，才使得 Vim 真正更为强大，成为一个特别高效的编辑器。就像上面讨论的，有了 YCM，我们找到了一个比 Vim 内置功能更加简单、直观、高效的方法。我们也应该去用好这样的新工具，提升自己的工作效率。

**要提高自己的编辑效率，需要时时刻刻注意自己有哪儿效率特别低，出现了不必要的重复，然后找到更好的办法来改进，并确保自己形成新的习惯。**

这个新的习惯是什么呢？可以是掌握了 Vim 里的一个之前不熟悉的功能，可以是用上了一个新的插件，也可以是……为 Vim 社区贡献一个新的插件！

这也恰恰是我在开篇词里提到的“懒惰”。所谓懒惰，就是我们要不让自己做低效的重复工作。而要不做低效的重复工作，我们就需要开动自己的脑子，监测自己的工作方式，找出问题点，予以改进，并坚持下去。懒惰的手段就是高效；反过来说也可以，高效的目的就是懒惰。

![](https://static001.geekbang.org/resource/image/9a/6d/9acfda8886d48783a2ce44992cf9c06d.jpg?wh=1920%2A1239)

期待你在 Vim 森林里找出自己的“传送门”，能够慵懒地一抬腿，就飞速到达任何自己想去的地方。

我们后会有期！

《Vim 实用技巧必知必会》课程结束了，这里有一份[毕业问卷](https://jinshuju.net/f/vUVK4d)，题目不多，希望你能花两分钟填一下。十分期待能听到你说一说，你对这个课程的想法和建议。  
[![](https://static001.geekbang.org/resource/image/71/24/71b5fb4e0b3db4623c0686b6a0715e24.jpg?wh=1142%2A801)](https://jinshuju.net/f/vUVK4d)

## 参考资料

作为写作的基本规矩，我最后列一下我参考过的资料（插件和之前文中直接给出的链接则不再重复）。希望它们也能帮到你，让你在下面的旅途中再上一层楼：

Allen, Leo. 2016. [“Why Vim is so much better than Atom”](https://blog.makersacademy.com/why-vim-is-so-much-better-than-atom-4e8253e6f605).

Arthur, Barry. 2014. [“Learning the tool of Vim”](http://of-vim-and-vigor.blogspot.com/2014/08/learning-tool-of-vim.html).

Bringhurst, Robert. 2012. *The Elements of Typographic Style*, 4th ed. Hartley &amp; Marks Publishers.

Irwin, Conrad. 2013. [“Bracketed paste mode”](https://cirw.in/blog/bracketed-paste).

Kochkov, Anton. 2019. [“Terminal Colors”](https://gist.github.com/XVilka/8346728).

Leonard, Andrew. 2000. [“BSD Unix: Power to the people, from the code”](https://www.salon.com/test/2000/05/16/chapter_2_part_one/).

Moolenaar, Bram. 2000. [“The continuing history of Vim”](https://moolenaar.net/vimstory.pdf).

Moolenaar, Bram. 2002. [“Vim, an open-source text editor”](http://www.free-soft.org/FSM/english/issue01/vim.html).

Moolenaar, Bram. 2007. [“7 habits for effective text editing 2.0”](https://moolenaar.net/habits_2007.pdf). [YouTube video](https://www.youtube.com/watch?v=p6K4iIMlouI).

Moolenaar, Bram. 2018. [“Vim: Recent developments”](https://www.moolenaar.net/Vim_Krakow_2018.pdf).

Neil, Drew. 2015. *Practical Vim*, 2nd ed. O’Reilly. 中文版：杨源、车文隆译《Vim 实用技巧》，人民邮电出版社，2014（第一版），2016（第二版）。

Neil, Drew. 2018. *Modern Vim: Craft your development Environment with Vim 8 and Neovim*. Pragmatic Bookshelf. 中文版：死月译《精通 Vim：用 Vim 8 和 Neovim 实现高效开发》，电子工业出版社，2020。

Ornbo, George. 2019. [“Vim: you don’t need NERDtree or (maybe) netrw”](https://shapeshed.com/vim-netrw/).

Osipov, Ruslan. 2018. *Mastering Vim*. Packt. 中文版：王文涛译《Vim 8 文本处理实战》，人民邮电出版社，2020。

Robbins, Arnold, Elbert Hannah, and Linda Lamb. 2008. *Learning the vi and Vim Editors*, 7th ed. O’Reilly.

Salus, Peter H. 1994. *A Quarter Century of UNIX*. Addison-Wesley.

Schneider, Peter A. 2018. [Answer to “How do I disable the weird characters from ‘bracketed paste mode’ on the Mac OS X default terminal?”](https://stackoverflow.com/a/50654284/816999).

Stack Overflow. 2015. [“2015 developer survey”, section “Technology &gt; Text editor”](https://insights.stackoverflow.com/survey/2015#tech-editor).

Stack Overflow. 2019. [“Developer survey results 2019”, section “Technology &gt; Development environments and tools”](https://insights.stackoverflow.com/survey/2019#development-environments-and-tools).

Target, Sinclair. 2018. [“Where Vim came from”](https://twobithistory.org/2018/08/05/where-vim-came-from.html).

Vance, Ashlee. 2003. [“Bill Joy’s greatest gift to man – the vi editor”](https://www.theregister.co.uk/2003/09/11/bill_joys_greatest_gift).

[Vim Online](https://www.vim.org/).

Wikipedia. [“Berkeley Software Distribution”](https://en.wikipedia.org/wiki/Berkeley_Software_Distribution).

Wikipedia. [“Bill Joy”](https://en.wikipedia.org/wiki/Bill_Joy).

Wikipedia. [“ex (text editor)”](https://en.wikipedia.org/wiki/Ex_%28text_editor%29).

Wikipedia. [“Version 6 Unix”](https://en.wikipedia.org/wiki/Version_6_Unix).

Wikipedia. [“vi”](https://en.wikipedia.org/wiki/Vi).

Wikipedia. [“Vim”](https://en.wikipedia.org/wiki/Vim_%28text_editor%29).

Wikipedia. [“Visual editor”](https://en.wikipedia.org/wiki/Visual_editor).
<div><strong>精选留言（10）</strong></div><ul>
<li><span>我来也</span> 👍（6） 💬（2）<p>老师辛苦了！

本专栏令我收获颇丰！
还有很多地方有待我去实践。

老师这个 参考资料 够长的。
看了这里，才发现《精通 Vim：用 Vim 8 和 Neovim 实现高效开发》今年3月都已经出版了。
虽然英文版的看过了，但还是想支持一下正版。</p>2020-09-11</li><br/><li><span>顾才朋</span> 👍（3） 💬（1）<p>我在2011年的时候，从《程序员的修炼之道》这本书中知道了 vi 编辑器之后，花了不少时间折腾。虽然从未把 vi 真正搞成自己的 IDE，但实实在在的，一直在 IDE 中（主要是 idea）使用 vim 模拟器。

我买这门课的目的是想了解一下，真正把 vim 当 IDE 的人是怎样做的。

学完以后，还是让我感到一点惊讶，现在 vim 的生态发展比之前花时间折腾的时候已经好了太多。要想直接把 vim 配置到替代 idea 大概不太可能，但是做到能够代替 sublimetext 或者 vscode 的程度，可行性还是非常高的。对于我来讲，严肃的编程还是得靠 idea，但时常会用 sublimetext （vim 模拟器）去完成一些简单的任务。看起来这些简单的任务，未来完全可以用 vim 更加高效的完成。

非常感谢作者的分享，让我对 vim 进行配置和使用，有了更系统性的认识。</p>2020-09-21</li><br/><li><span>Sochooligan</span> 👍（2） 💬（2）<p>感谢老师的深厚经验和精彩分享！断续在看，很有必要再精读几遍。虽然现在用的是emacs、spacemacs用的是emacs的按键，但编辑器（IDE）面对的问题都是类似的，很多解决问题的方法都是通用的。关于编辑器我有一点体会是：你最终会在Vim和Emacs之间不再纠结（也许还有sublime，atom，vs code等），选择一个自己的最爱，把使用时所有遇到的问题，都在这个编辑器里配好、改进，并一直用下去，用到最好。选你所爱，爱你所选！</p>2020-09-11</li><br/><li><span>YouCompleteMe</span> 👍（1） 💬（1）<p>虽然之前看过《Vim实用技巧》&#47;《Vim8文本实战处理》，但是这个专栏才真正打通了我使用Vim的任督二脉。以前自己的vimrc参考了Github上一些Vim插件作者的配置，很多配置只是人云亦云，现在有了一份自己的精简的vimrc，对其中的每一项配置都了然于胸。对于发现不高效的地方，还可以自己写VimL改进效率。感谢老师的辛苦付出，收获颇丰，期待老师的下一门课程。
待老师的下一门课程。</p>2020-09-11</li><br/><li><span>doge</span> 👍（1） 💬（1）<p>老师的课程让我受益良多，虽然一直用vim，也一直沿用github上高手们共享的配置，但还没真正仔细的研究过相关功能实现的方式以及脚本的写法，看了老师的教学和评论高手的分享，对vim的理解更深入了些，对高效编辑的一些思考也多了一些。按照老师的脚本也算是自我定制出了比较满意的一个vim版本。评论的朋友说的好，选好一个编辑器，然后一直用下去，好东西还是需要多多打磨的。最后再次感谢老师系统性的分享。</p>2020-09-11</li><br/><li><span>瀚海星尘</span> 👍（0） 💬（1）<p>花了几个月，一点一点的挤出时间，一节一节的慢慢练。上课前已经强迫自己用了一段时间的 vim，但是经常应为效率开发问题，被逼回到 vscode。几个月下来，vscode 已经拜拜了！收益匪浅哈，谢谢吴老师！������</p>2020-10-25</li><br/><li><span>pyhhou</span> 👍（0） 💬（1）<p>到这里真是有些不舍，感觉自己每一讲都能学到很多新知识，了解自己之前不曾了解的东西（可能是自己对 VIM 的了解不够������）。回看这个专栏，自己的收获真的不小，比如掌握了 vim 脚本的基本配置方法，了解了一些高效便捷的指令组合，也跟着老师知道了很多很便捷的插件，另外自己还尝试阅读了一些 VIM 源码。让我收获最大的还是专栏通过各种常见的例子，很清楚地展示一些指令和插件的应用场景，知道了一个指令或插件为什么会比一般的编辑方法更高效，再加上老师每次的耐心解答，像我这种 VIM 新人都感受到了 VIM 的强大。除了高效编辑，感觉 VIM 给我们带来了很多额外的好处，比如增加了操作命令行的熟练度，最重要的还是 VIM 让人变得更加 “懒惰”，时刻想着如何改进脚本让自己能够更方便地去写程序，给自己留足了想象和创作的空间。看来自己的 VIM 之路才刚开始

感谢老师的辛勤付出，也感谢老师每一讲的提问都耐心解答</p>2020-09-13</li><br/><li><span>newcode</span> 👍（0） 💬（1）<p>时间过得真快，“一切才刚刚开始”。</p>2020-09-11</li><br/><li><span>qinsi</span> 👍（0） 💬（1）<p>个人觉得Vim作为IDE而言功能还是薄弱了些，毕竟原本定位就只是编辑器。而很多传统的使用场景如运维连上远程服务器改配置，或是在服务器上进行简单的远程开发和调试等，也随着自动化运维以及WebIDE技术的发展逐渐减少。但Vim的高效编辑键位作为一种遗产保留了下来，在很多主流IDE中都可以通过插件方式支持。既然离不开现有的IDE，仅仅通过熟练掌握Vim的键位也可以显著提高效率。但很多操作是键位表上没有的，这门课起到了很好的补充。感谢老师。

</p>2020-09-11</li><br/><li><span>及時行樂</span> 👍（0） 💬（0）<p>毕业工作已经3年了，从始至终都在深耕vim，从事驱动开发，只接触C代码，我的开发场景vim完全替代ide，如今接触到其他语言，vim在很多方面确实没有必比ide高效，或者学习成本过高。通过老师的课程，也算是对自己学习vim过程中的一个总结。
vim就像一未开锋的剑，日夜的打磨渐渐成为一把与自己无比契合的宝剑</p>2024-02-22</li><br/>
</ul>