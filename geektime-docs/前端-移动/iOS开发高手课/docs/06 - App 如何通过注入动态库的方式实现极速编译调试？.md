你好，我是戴铭。

在上一篇文章中，我和你分享了链接器的基础知识。今天我们再继续聊聊，动态库链接器的实际应用，也就是编译调试的提速问题。

iOS 原生代码的编译调试，都是通过一遍又一遍地编译重启 App 来进行的。所以，项目代码量越大，编译时间就越长。虽然我们可以通过将部分代码先编译成二进制集成到工程里，来避免每次都全量编译来加快编译速度，但即使这样，每次编译都还是需要重启 App，需要再走一遍调试流程。

对于开发者来说，提高编译调试的速度就是提高生产效率。试想一下，如果上线前一天突然发现了一个严重的bug，每次编译调试都要耗费几十分钟，结果这一天的黄金时间，一晃就过去了。到最后，可能就是上线时间被延误。这个责任可不轻啊。

那么问题来了，原生代码怎样才能够实现动态极速调试，以此来大幅提高编译调试速度呢？在回答这个问题之前，我们先看看有哪些工具是这么玩儿的。了解了它们的玩法，我们也就自然清楚这个问题的答案了。

## Swift Playground

说到iOS代码动态极速调试的工具，你首先能想到的估计就是 Playground。它是 Xcode 里集成的一个能够快速、实时调试程序的工具，可以实现所见即所得的效果，如下图所示：

![](https://static001.geekbang.org/resource/image/46/01/46007bcd100b7b23edccd46b760e5b01.png?wh=2224%2A1668)

图1 Playground工具实时调试示例

可以看到，任何的代码修改都能够实时地在右侧反馈出来。

## Flutter Hot Reload

Flutter 是 Google 开发的一个跨平台开发框架，调试也是快速实时的。官方的效果动画如下：

![](https://static001.geekbang.org/resource/image/6d/1d/6d8b83e4e063dbccf279adfe2b66dd1d.gif?wh=878%2A522)

图2 Flutter使用示例

可以看到，在 Flutter 编辑器中修改文字 clicked 为 tapped 后点击 reload，模拟器中的文字立刻就改变了，程序没有重启。同样地，修改按钮图标也会立刻生效。

接下来，我们先看看 Flutter 是怎么实现实时编译的。

Flutter 会在点击 reload 时去查看自上次编译以后改动过的代码，重新编译涉及到的代码库，还包括主库，以及主库的相关联库。所有这些重新编译过的库都会转换成内核文件发到 Dart VM 里，Dart VM 会重新加载新的内核文件，加载后会让 Flutter framework 触发所有的Widgets 和 Render Objects 进行重建、重布局、重绘。

Flutter 为了能够支持跨平台开发，使用了自研的 Dart 语言配合在 App 内集成 Dart VM 的方式运行 Flutter 程序。目前 Flutter 还没有达到 Cocoa 框架那样的普及程度，所以如果你不是使用 Flutter 来开发 iOS 程序的话，想要达到极速调试应该要怎么做呢？

# Injection for Xcode

所幸的是，John Holdsworth 开发了一个叫作 Injection 的工具可以动态地将 Swift 或 Objective-C 的代码在已运行的程序中执行，以加快调试速度，同时保证程序不用重启。John Holdsworth 也提供了动画演示效果，如下：

![](https://static001.geekbang.org/resource/image/a2/13/a239763b1a5c7226e5ee8d7481285a13.gif?wh=1592%2A938)

图3 Injection使用示例

作者已经开源了这个工具，地址是[https://github.com/johnno1962/InjectionIII](https://github.com/johnno1962/InjectionIII) 。使用方式就是 clone 下代码，构建 InjectionPluginLite/InjectionPlugin.xcodeproj ；删除方式是，在终端里运行下面这行代码：

```
rm -rf ~/Library/Application\ Support/Developer/Shared/Xcode/Plug-ins/InjectionPlugin.xcplugin
```

构建完成后，我们就可以编译项目。这时添加一个新的方法：

```
- (void)injected
{
    NSLog(@"I've been injected: %@", self);
}
```

然后在这个方法中添加一个断点，按下 ctrl + = ，接下来你会发现程序运行时会停到断点处，这样你的代码就成功地被运行中的 App 执行了。那么，**Injection 是怎么做到的呢？**

Injection 会监听源代码文件的变化，如果文件被改动了，Injection Server 就会执行 rebuildClass 重新进行编译、打包成动态库，也就是 .dylib 文件。编译、打包成动态库后使用 writeSting 方法通过 Socket 通知运行的 App。writeString 的代码如下：

```
- (BOOL)writeString:(NSString *)string {
    const char *utf8 = string.UTF8String;
    uint32_t length = (uint32_t)strlen(utf8);
    if (write(clientSocket, &length, sizeof length) != sizeof length ||
        write(clientSocket, utf8, length) != length)
        return FALSE;
    return TRUE;
}
```

Server 会在后台发送和监听 Socket 消息，实现逻辑在 `InjectionServer.mm` 的 runInBackground 方法里。Client 也会开启一个后台去发送和监听 Socket 消息，实现逻辑在 `InjectionClient.mm`里的 runInBackground 方法里。

Client 接收到消息后会调用 inject(tmpfile: String) 方法，运行时进行类的动态替换。inject(tmpfile: String) 方法的具体实现代码，你可以点击[这个链接](https://github.com/johnno1962/InjectionIII/blob/master/InjectionBundle/SwiftInjection.swift)查看。

inject(tmpfile: String) 方法的代码大部分都是做新类动态替换旧类。inject(tmpfile: String) 的入参 tmpfile 是动态库的文件路径，那么这个动态库是如何加载到可执行文件里的呢？具体的实现在inject(tmpfile: String) 方法开始里，如下：

```
let newClasses = try SwiftEval.instance.loadAndInject(tmpfile: tmpfile)
```

你先看下 SwiftEval.instance.loadAndInject(tmpfile: tmpfile) 这个方法的代码实现：

```
@objc func loadAndInject(tmpfile: String, oldClass: AnyClass? = nil) throws -> [AnyClass] {

    print("???? Loading .dylib - Ignore any duplicate class warning...")
    // load patched .dylib into process with new version of class
    guard let dl = dlopen("\(tmpfile).dylib", RTLD_NOW) else {
        throw evalError("dlopen() error: \(String(cString: dlerror()))")
    }
    print("???? Loaded .dylib - Ignore any duplicate class warning...")

    if oldClass != nil {
        // find patched version of class using symbol for existing

        var info = Dl_info()
        guard dladdr(unsafeBitCast(oldClass, to: UnsafeRawPointer.self), &info) != 0 else {
            throw evalError("Could not locate class symbol")
        }

        debug(String(cString: info.dli_sname))
        guard let newSymbol = dlsym(dl, info.dli_sname) else {
            throw evalError("Could not locate newly loaded class symbol")
        }

        return [unsafeBitCast(newSymbol, to: AnyClass.self)]
    }
    else {
        // grep out symbols for classes being injected from object file

        try injectGenerics(tmpfile: tmpfile, handle: dl)

        guard shell(command: """
            \(xcodeDev)/Toolchains/XcodeDefault.xctoolchain/usr/bin/nm \(tmpfile).o | grep -E ' S _OBJC_CLASS_\\$_| _(_T0|\\$S).*CN$' | awk '{print $3}' >\(tmpfile).classes
            """) else {
            throw evalError("Could not list class symbols")
        }
        guard var symbols = (try? String(contentsOfFile: "\(tmpfile).classes"))?.components(separatedBy: "\n") else {
            throw evalError("Could not load class symbol list")
        }
        symbols.removeLast()

        return Set(symbols.flatMap { dlsym(dl, String($0.dropFirst())) }).map { unsafeBitCast($0, to: AnyClass.self) }
```

在这段代码中，你是不是看到你所熟悉的动态库加载函数 dlopen 了呢？

```
guard let dl = dlopen("\(tmpfile).dylib", RTLD_NOW) else {
    throw evalError("dlopen() error: \(String(cString: dlerror()))")
}
```

如上代码所示，dlopen 会把 tmpfile 动态库文件载入运行的 App 里，返回指针 dl。接下来，dlsym 会得到 tmpfile 动态库的符号地址，然后就可以处理类的替换工作了。dlsym 调用对应代码如下：

```
guard let newSymbol = dlsym(dl, info.dli_sname) else {
    throw evalError("Could not locate newly loaded class symbol")
}
```

当类的方法都被替换后，我们就可以开始重新绘制界面了。整个过程无需重新编译和重启 App，至此使用动态库方式极速调试的目的就达成了。

我把Injection的工作原理用一张图表示了出来，如下所示：

![](https://static001.geekbang.org/resource/image/4f/c9/4f49ea2047d2dd2d5c4646b0ba55b8c9.png?wh=1920%2A1080)

图4 Injection的工作原理示意图

## 小结

今天这篇文章，我和你详细分享了动态库链接器的一个非常实用的应用场景：如何使用动态库加载方式进行极速调试。由此我们可以看出，类似链接器这样的底层知识是非常重要的。

当然了，这只是一个场景，还有更多的场景等待着我们去发掘。比如把 Injection 技术扩展开想，每当你修改了另一个人负责的代码就给那个人发条消息，同时将修改的代码编译、打包成动态库直接让对方看到修改的情况，这样不仅是提高了自己的效率，还提高了整个团队的沟通效率。怎么样？是不是有种想立刻尝试的感觉，心动不如行动，动手写起来吧。

所以，打好了底层知识的基础以后，我们才可以利用它们去提高开发效率，为用户提供更稳定、性能更好的 App 。

今天这篇文章最后，我留给你的一个小作业是，思考一下底层知识还有哪些运用场景，并在评论区分享出来吧。

感谢你的收听，欢迎你在评论区给我留言分享你的观点，也欢迎把它分享给更多的朋友一起阅读。

![](https://static001.geekbang.org/resource/image/6c/89/6c844d233e74aec08417be65e4ef1d89.jpg?wh=1110%2A549)
<div><strong>精选留言（15）</strong></div><ul>
<li><span>bubble</span> 👍（2） 💬（2）<p>想问下老师 为什么只有模拟器可以 而真机不可以呢？</p>2019-03-25</li><br/><li><span>mqhong</span> 👍（2） 💬（1）<p>讲的有点深了 有没有推介的gnustep源码必读的类实现 和阅读的方法😂</p>2019-03-23</li><br/><li><span>Damon</span> 👍（1） 💬（1）<p>报错了，建议看看留言或者直接看github仓库中的issue看是否有你遇到的问题；看了留言我的问题完美解决</p>2019-04-30</li><br/><li><span>刘儒勇</span> 👍（0） 💬（1）<p>历尽千辛万苦，终于可以用了✌️</p>2019-05-31</li><br/><li><span>Ant</span> 👍（0） 💬（1）<p>这样审核能通过吗？ 是不是调试的时候用，提交App Store时候移除呢</p>2019-04-10</li><br/><li><span>郑昊鸣</span> 👍（0） 💬（1）<p>感谢老师，对于已经模块化的项目，在pod的example project中开发，InjectionIII就不好用了。InjectionIII要求项目都在一个目录下，当项目加载本地pod进行开发的时候，本地pod和项目project不在同一目录下，InjectionIII该如何使用呢，谢谢~</p>2019-03-28</li><br/><li><span>痞子胡</span> 👍（0） 💬（1）<p>接入到项目中，启动后直接crash，报bad access。找了一天还没找到原因，求解。</p>2019-03-27</li><br/><li><span>徐秀滨</span> 👍（0） 💬（1）<p>接我上个问题，已经解决了。
使用通知接收就可以。
[[NSNotificationCenter defaultCenter] addObserver:self selector:@selector(test) name:@&quot;INJECTION_BUNDLE_NOTIFICATION&quot; object:nil];</p>2019-03-26</li><br/><li><span>drunkenMouse</span> 👍（31） 💬（1）<p>Clone一下代码弄得有点懵，不知道怎么克隆。然后我用了另一种方式使用了injection

1.在App Store下载InjectionIII, 打开。
2.选择项目的根目录
3.项目的Appdelegate加入：
#if DEBUG
 &#47;&#47; iOS
    [[NSBundle bundleWithPath:@&quot;&#47;Applications&#47;InjectionIII.app&#47;Contents&#47;Resources&#47;iOSInjection.bundle&quot;] load];
#endif

XCode10 是这个
#if DEBUG
 &#47;&#47; iOS
    [[NSBundle bundleWithPath:@&quot;&#47;Applications&#47;InjectionIII.app&#47;Contents&#47;Resources&#47;iOSInjection10.bundle&quot;] load];
#endif

而后启动，修改，保存，就会卡到断点位置了。</p>2019-03-23</li><br/><li><span>Daniel</span> 👍（21） 💬（0）<p>ios10之后由于沙盒的限制 应用无法加载自身bundle之外的动态库 这个工具只能在模拟器上使用</p>2019-04-10</li><br/><li><span>景天儿</span> 👍（17） 💬（2）<p>蛮好用的，但是有几个需要注意的地方：
1. 进行swizzling的类不要动态修改，否则二次交换，会引起死循环。
2. 不支持方法的删除：删除后，方法调用仍然有效，不抛异常。
3. 不支持新增类：新增类引入后使用无效。但类的重命名是有效的。
4. 属性新增、删除、修改：反射上体现不出来。
其中后三个的原因，不知道戴铭老师有没有什么见解。
在我的角度来看，应该不是InjectionIII的问题，可能与苹果动态库调用有关。</p>2019-05-28</li><br/><li><span>mαnajay</span> 👍（13） 💬（0）<p>InjectionIII 上面有个 issue 是解决 pod 组件引入修改源码无法进行注入的问题  https:&#47;&#47;github.com&#47;johnno1962&#47;InjectionIII&#47;issues&#47;34,  https:&#47;&#47;github.com&#47;johnno1962&#47;InjectionIII&#47;issues&#47;53 , 使用组件后接入还是有点麻烦</p>2019-03-23</li><br/><li><span>Geek_48dbbf</span> 👍（7） 💬（0）<p>真机上如何实现注入动态库实时调试？</p>2019-04-18</li><br/><li><span>Love mi</span> 👍（7） 💬（1）<p>1.在App Store下载InjectionIII, 打开。
2.选择项目的根目录
3.项目的Appdelegate加入：
    [[NSBundle bundleWithPath:@&quot;&#47;Applications&#47;InjectionIII.app&#47;Contents&#47;Resources&#47;iOSInjection.bundle&quot;] load];
运行报
Error loading &#47;Applications&#47;InjectionIII.app&#47;Contents&#47;Resources&#47;iOSInjection.bundle&#47;iOSInjection:  dlopen(&#47;Applications&#47;InjectionIII.app&#47;Contents&#47;Resources&#47;iOSInjection.bundle&#47;iOSInjection, 265): Symbol not found: _$s19ArrayLiteralElements013ExpressibleByaB0PTl
  Referenced from: &#47;Applications&#47;InjectionIII.app&#47;Contents&#47;Resources&#47;iOSInjection.bundle&#47;iOSInjection
  Expected in: &#47;Applications&#47;Xcode.app&#47;Contents&#47;Developer&#47;Toolchains&#47;XcodeDefault.xctoolchain&#47;usr&#47;lib&#47;swift&#47;iphonesimulator&#47;libswiftCore.dylib
 in &#47;Applications&#47;InjectionIII.app&#47;Contents&#47;Resources&#47;iOSInjection.bundle&#47;iOSInjection</p>2019-03-28</li><br/><li><span>亡命之徒</span> 👍（6） 💬（0）<p>项目使用了cocopods、这个插件用不了呀，保存的时候报错😭，新建的demo使用就没问题,麻烦老师解答下</p>2019-03-29</li><br/>
</ul>