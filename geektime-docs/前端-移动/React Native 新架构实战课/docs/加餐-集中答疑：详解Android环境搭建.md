你好，我是蒋宏伟。

今天这节课，我会为你解答如何搭建 Android 环境。

在写这节课之前，我自己重装系统重新搭建了一次环境。我使用的电脑是 Macbook Pro 2016 版，系统版本是 12.6.3，供你参考。

总体上说，搭建 Android 环境比搭建 iOS 环境遇到的网络问题更少，因此我更建议新手直接搭建 Android 环境。并在每搭建一步之后做一次检查，比如相关包的版本检查，这可能会让你少走弯路。

下面我来分享一下，我搭建 Android React Native 开发环境的详细步骤，你也可以跟着一起动起手来。

## Homebrew

第一步是安装 Homebrew，后续很多程序的安装都会借助 Homebrew 进行。

Homebrew 是 macOS 的一个软件包管理器。直接使用 [Homebrew 官方文档](https://brew.sh/)进行安装，我这边出现了网络报错。报错的内容是 `unable to access github`，也就是访问不到 GitHub 地址。解决方案要么是保持自己的网络畅通，要么使用相关的镜像源。

知乎上有大牛提供了 Homebrew [镜像源及工具](https://zhuanlan.zhihu.com/p/111014448)，你可以通过如下命令一键安装。

```bash
$ /bin/zsh -c "$(curl -fsSL <https://gitee.com/cunkai/HomebrewCN/raw/master/Homebrew.sh>)"
```

![图片](https://static001.geekbang.org/resource/image/e6/dc/e67948373afe7be627ce7814yy7ae5dc.png?wh=1920x1259)

安装完成后，重启当前 Terminal，brew 就安装成功了。你可以运行如下命令，检查它是否安装成功。

```plain
$ brew --version
Homebrew 3.6.15
```

## Node 和 NPM

第二步是安装 Node 和 NPM，搭建 JavaScript 环境。

Node 是 React Native 应用程序中，JavaScript 相关服务的运行环境，比如构建服务就是通过 Node 环境提供的。安装 Node 时，会自动安装 NPM 包管理器，它将帮助我们管理相关依赖。

我们可以通过 Homebrew 进行 Node 的安装。

```bash
$ brew install node
```

安装完成后，你可以通过如下命令检查 Node 和 NPM 是否安装成功。

```bash
$ node --version
v19.7.0
$ npm --version
9.5.0
```

![图片](https://static001.geekbang.org/resource/image/22/37/22c3ac2eeaff6a51fd0b08c1fa935c37.png?wh=1920x386)

为保证后续网络的畅通，你最好将 NPM 的 registry 设置为淘宝源。切换命令如下：

```bash
$ npx nrm use taobao
```

## Watchman

第三步，是安装一个名为 Watchman 的工具。它是由 Facebook 开发的一个工具，只要你的文件有一些变化，它就会自动重新运行你的项目。

我们使用 Homebrew 来安装 Watchman。

```plain
$ brew install watchman
```

安装完成后，通过如下命令检查是否安装成功。

```plain
$ watchman --version
2023.02.20.00
```

![图片](https://static001.geekbang.org/resource/image/d8/aa/d841d889eae880be5faabc685a979aaa.png?wh=1920x1256)

## 安装 JDK

第四步是安装 Java Development Kit（JDK），搭建 Java 开发环境。

众所周知，Android 依赖 Java 开发环境，这里我们搭建 Java 环境使用的工具是 Zulu。Zulu 是一款 Java 运行环境，它是基于 OpenJDK（一个 Java 编程语言的开源实现的源代码）构建的。Zulu 提供了 Intel 和 M1 Mac 的 JDK，这使得 JDK 的安装更为方便。

由于 Zulu 是一个图形界面程序，需要手动安装，为了方便这里我们借助 Cask 一键安装。你需要先借助 Homebrew 安装 Cask 再安装 Zulu。命令如下：

```bash
$ brew tap homebrew/cask-versions
$ brew install --cask zulu11
```

![图片](https://static001.geekbang.org/resource/image/50/77/50dd88byy16ed17f35d9a2e7751a7377.png?wh=1920x1156)

当你安装成功后，你可以运行 `java --version` 检查 Java 运行时环境（JRE）的版本，或运行 `javac --version` 检查 Java 开发工具包（JDK）中 Java 编译器（javac）的版本。

```bash
$ java --version
java 16.0.2 2021-07-20 
$ javac --version
javac 16.0.2  
```

## 安装 Android Studio

第五步是安装 Android Studio，它是搭建 Android 开发环境的前提条件。

Android Studio 是 Android 开发的官方集成开发环境（IDE）。你需要安装 Android Studio 才能在本机构建 React Native 应用程序，并运行在真机或模拟器上。

你可以从 [Android Studio 官方网站](https://developer.android.com/studio)下载和安装 Android Studio。在 Android Studio 安装向导中，选择默认选项并设置相关镜像安装默认依赖即可。

![图片](https://static001.geekbang.org/resource/image/b2/b5/b28d50c33b97b8bf5a719794dyyc0eb5.png?wh=1920x1205)

```bash
腾讯： https://mirrors.cloud.tencent.com/AndroidSDK/

阿里： https://mirrors.aliyun.com/android.googlesource.com/
```

这一步的完整流程比较长，细节比较多，因此我录了一个小视频，供你参考：

## 安装 **Android SDK**

第六步是安装 Android SDK。

在上一步中，我们已经把 Android Studio 和默认依赖安装好了，除了默认依赖，你还需要安装：

- `Android SDK Platform 33`
- `Intel x86 Atom_64 System Image` 或 `Google APIs Intel x86 Atom System Image`(Inter CPU) 或 `Google APIs ARM 64 v8a System Image` (Apple CPU)
- `Android SDK Build-Tools` 33.0.0 版本

安装的第一部分的是 `Android SDK Platform`。它是指针对 Android 特定版本的 Android 平台组件，包括库、工具和框架等。

安装的第二部分的是 `System Image`。它是针对特定处理器架构的 Android 系统镜像，该镜像主要用于在模拟器上模拟具有特定 CPU 和 Google API 的 Android 设备。带有 Intel 字样的适配的是 Intel CPU，带有 ARM 字样的适配的是苹果 CPU，此外带有 Google 字样表示集成了 Google 的 API。

一般情况下，Intel CPU 选择 `Google APIs Intel x86 Atom System Image`，苹果 CPU 选择 `Google APIs ARM 64 v8a System Image`。

安装的第三部分是 `Android SDK Build-Tools`，你可以在 Android Studio 的左上角找到 Preference，并打开它。然后搜索 Android SDK，找到其中的 `SDK Platforms` 和 `SDK Tools` 配置页，然后按下图所示勾选，最后点击 `Apply` 完成相关项的安装。

![图片](https://static001.geekbang.org/resource/image/87/c2/879b19e4c2053ece3f416a02564afdc2.png?wh=1920x1411)

![图片](https://static001.geekbang.org/resource/image/41/27/411c92d3909937fbfdfefc9476946927.png?wh=1920x1397)

同样，这一步我也录制了视频。

## 配置 **Android 环境变量**

第七步是配置 Android 环境变量。

由于后续操作会依赖于一些命令行，因此你还需要将 Android 环境变量暴露到全局，以便使用。

Zsh（Z shell）和 Bash（Bourne Again SHell）是两种不同的命令工具，你可以运行如下命令检查你用的是哪种工具。

```bash
$ echo $SHELL
/bin/zsh
```

如果你用的是 Zsh，那么你需要修改 `~/.zprofile` 或 `~/.zshrc` 文件。如果你用的是 Bash，那么你需要修改 `~/.bash_profile` 或 `~/.bashrc` 文件。你可以使用自带的 `vi` 编辑器进行编辑，命令如下：

```bash
$ vi ~/.zshrc
# 或 vi ~/.bashrc
```

接着，按 `i` 键进入插入模式，再使用箭头键将光标移动到插入文本的位置，然后将下列内容复制粘贴到文本中。

```bash
export ANDROID_HOME=$HOME/Library/Android/sdk
export PATH=$PATH:$ANDROID_HOME/emulator
export PATH=$PATH:$ANDROID_HOME/platform-tools
```

完成插入后，按 `Esc` 键退出插入模式，输入 `:wq` 以保存更改并退出 `vi` 编辑器。

再接着，为了让更改生效，你可以重启终端（Shell）或者运行 `source ~/.zshrc` 使配置生效。

最后，运行如下命令检查 Android 环境变量是否设置成功。

```bash
$ echo $ANDROID_HOME
/Users/jianghongwei/Library/Android/sdk
$ echo $PATH
/Users/local/bin...
```

这一步依然可以参考视频。

## 安装 Android 模拟器

第八步是安装 Android 模拟器。安装 Android 模拟器是搭建 Android 环境中的最后一步。当然你可以使用真机进行调试，但是模拟器大多数情况下更加方便，因此我选择安装了 Android 模拟器。

如果你还在 `Welcome to Android Studio` 页面，那么你可以在 `More Actions` 下拉框中选择 `Virtual Device Manager`。其他情况，你可以在顶部菜单栏中点击 `Tools` &gt; `Virtual Device Manager`。

![图片](https://static001.geekbang.org/resource/image/a4/f9/a418d9789bca1a09b8fe26fefe46eff9.png?wh=1920x1709)

在 `Device Manager` 界面中，点击 `Create Virtual Device` 按钮创建虚拟设备。

![图片](https://static001.geekbang.org/resource/image/86/68/86dc18b83d13edc264f1991c1a884468.png?wh=1920x1558)

在 `Virtual Device Configuration` 页面选择虚拟硬件，你可以选择任意一个设备，比如 Pixel XL，然后点击Next。

![图片](https://static001.geekbang.org/resource/image/66/12/66e0da248cbe35252ce5985909b65b12.png?wh=1920x1302)

接着，你会进入到 `Virtual Device Configuration` 页面的 `System Image` 系统镜像选择步骤，选择模拟器的 Android 版本，然后点击下载按钮进行下载。

![图片](https://static001.geekbang.org/resource/image/0c/87/0cd0245881e69d4d3c5b9b6c2389a687.png?wh=1920x1319)

现在，你已成功创建了一个新的 Android 模拟器。回到 `Device Manager` 页面后，你将看到新创建的模拟器设备。点击 `Actions` 中的播放图标 ▶️ 启动模拟器。接着会自动打开一个模拟器，并加载所选的 Android 系统镜像。

![图片](https://static001.geekbang.org/resource/image/04/9c/04ff8f12a9yy8a12115dcc4bdf95219c.png?wh=1920x1419)

当你看到 Android 操作系统界面时，你的模拟器就安装完成了。此时，Android 环境已经搭建完成。接下来，我们将创建和启动 React Native 项目。

![图片](https://static001.geekbang.org/resource/image/3d/7b/3d844a5d4a3e2224442c8bfa9814607b.png?wh=1920x1186)

参考视频如下：

## 创建 React Native 项目

第九步是创建 React Native 项目。

你可以使用 React Native CLI 来创建一个新的 React Native 项目，命令如下：

```bash
$ npx react-native@latest init AwesomeProject
```

运行上述命令后，会依次下载 JavaScript/Java/Objective-C 的相关依赖和项目模板，如果没有配置 NPM、Maven 或 CocoaPods 的相关镜像，很有可能会遇到运行失败的问题。在运行失败后，你需要确定一下是上述 3 个部分依赖中的哪部分依赖没有下载成功。

React Native iOS 环境中的 CocoaPods 报错，我已经在 [iOS 环境搭建](https://time.geekbang.org/column/article/635210)中解答过了，NPM 镜像在前面步骤中也已经切换到淘宝源，这部分重点介绍 Android Maven 镜像源的替换。

例如，你可能会遇到如下图所示的 iOS Environment 安装失败的报错，但由于你要安装的是 React Native Android，因此你可以选择忽略 iOS 的报错。

![图片](https://static001.geekbang.org/resource/image/64/57/64abc00b51460b668a9eb1407c75c657.png?wh=1920x1237)

再仔细观察图中内容，你可以看到 `Donwloading template` 、`Copying template` 、`Processing template` 三个模板相关的步骤已经处理完成，报错的是 `Installing Bundler` 这一步。

这意味着，创建 React Native 项目已经完成，只是安装 Android 依赖失败了，所以你只需要切换 Maven 镜像源，再安装和启动 React Native 项目即可。

你需要打开 `./android/build.gradle` 文件，将 Maven 源切换为阿里或华为的镜像源，操作方法如下：

```java
阿里：https://maven.aliyun.com/repository/public/
华为：https://repo.huaweicloud.com/repository/maven/
```

![图片](https://static001.geekbang.org/resource/image/21/77/219b77d5ccaa995b014029da0d953b77.png?wh=1920x1106)

切换好源之后，你需要 `cd android` 目录，然后运行 `gradlew build` 命令，Android 依赖安装是使用 `gradlew` 进行管理的。

```bash
$ cd android
$ ./gradlew build --refresh-dependencies
```

![图片](https://static001.geekbang.org/resource/image/3b/13/3bef42bc9f712f980152c73a7c4db713.png?wh=1920x1101)

参考视频如下：

## 启动 React Native 项目

最后一步就是启动 React Native 项目。

在上一步，我们已经完成了 React Native 项目的创建和 Maven 源的切换，所有准备工作都已经完成。这一步，我们需要完成：

1. 在本地启动 React Native 构建服务；
2. 在模拟器中安装 React Native Android App。

在项目的根目录中，运行如下命令，它会帮你在本地启动一个 React Native 构建服务。

```bash
# 如果在 Android 目录，需要 cd ../ 到根目录
$ npx react-native start
```

运行完成后，会出现如下的 `Welcome to Metro` 的欢迎界面，`Metro` 就是 React Native 的构建服务。同时，底部会显示 `r` `d` `i` `a` 四个选项，其中 `a` 选项是 `run on Android`，也就是说当你按下 `a` 按钮，它会帮你在模拟器上安装 React Native Android 应用。

![图片](https://static001.geekbang.org/resource/image/eb/9e/eb53c40bd6d2cbf87e87404dc5f5719e.png?wh=1920x1251)

按下 `a` 按钮后，稍等一会，当你看到 Welcome to React Native 页面时，你的 React Native Android 应用就安装完成了。

![图片](https://static001.geekbang.org/resource/image/b3/1f/b3ca414c22bc7b37611e22b2fdc5ec1f.png?wh=1920x1294)

参考视频如下：

至此，恭喜你，React Native Android 环境已经搭建成功了。

## **总结**

搭建开发环境是很多新手的痛点。React Native 项目依赖项繁多，首先是依赖 Android 环境，其次是依赖 Node.js 环境。Android 环境又依赖 Java 环境，还需要安装 Android Studio、Android SDK 和虚拟机。同时，Node.js 和 Java 的环境搭建也都依赖 Homebrew，环环相扣。

## 思考题

你在搭建 React Native 环境过程中，遇到过哪些问题？能把你的解决方案和大家分享分享吗？

期待你的输出，如果觉得有所收获，也欢迎你把今天的内容分享给更多的朋友！
<div><strong>精选留言（15）</strong></div><ul>
<li><span>大大小小</span> 👍（9） 💬（0）<p>jdk推荐用sdkman，类似node的nvm，方便管理多个java版本。</p>2023-03-30</li><br/><li><span>五十米深蓝，</span> 👍（1） 💬（0）<p>大哥 没有对应平台的编译打包过程讲解吗？！！！！！！！！！！！</p>2023-07-24</li><br/><li><span>handy</span> 👍（0） 💬（0）<p>使用$ npx react-native@latest init AwesomeProject这个命令
创建项目的时候 ，提示The `init` command is deprecated.怎么解决呢</p>2025-01-02</li><br/><li><span>Geek1560</span> 👍（0） 💬（0）<p>新版本 Android studio 采用腾讯源没动静 😂</p>2024-11-11</li><br/><li><span>黑马有点白986</span> 👍（0） 💬（0）<p>现在有哪些公司用rn</p>2024-11-08</li><br/><li><span>在男神经路上越走越远</span> 👍（0） 💬（0）<p>Android Studio启动AVD卡在Starting Up，怎么处理？

avd.ini.encoding=UTF-8
path=&#47;Users&#47;Mao&#47;.android&#47;avd&#47;Pixel_XL_API_33.avd
path.rel=avd&#47;Pixel_XL_API_33.avd
target=android-33
</p>2024-06-18</li><br/><li><span>羊了个羊</span> 👍（0） 💬（0）<p>现在24年了，可以学吗</p>2024-06-12</li><br/><li><span>羊了个羊</span> 👍（0） 💬（0）<p>没有windows的吗？</p>2024-06-12</li><br/><li><span>Geek_a73298</span> 👍（0） 💬（0）<p>额windows的没有嘛？？？</p>2024-04-24</li><br/><li><span>黄科泽</span> 👍（0） 💬（0）<p>这个错误有 遇到过吗？要怎么解决
Execution failed for task &#39;:app:buildCMakeDebug[arm64-v8a]&#39;.
&gt; com.android.ide.common.process.ProcessException: ninja: Entering directory `D:\RN_Project\study4\react-native-classroom-main\android\app\.cxx\Debug\3d212c3w\arm64-v8a&#39;
  [0&#47;2] Re-checking globbed directories...

  C++ build system [build] failed while executing:
      @echo off
      &quot;C:\\Users\\PC\\AppData\\Local\\Android\\Sdk\\cmake\\3.22.1\\bin\\ninja.exe&quot; ^
        -C ^
        &quot;D:\\RN_Project\\study4\\react-native-classroom-main\\android\\app\\.cxx\\Debug\\3d212c3w\\arm64-v8a&quot; ^
        appmodules ^
        react_codegen_RNCViewPager ^
        react_codegen_RTNCalculatorSpec ^
        react_codegen_RTNCenteredTextSpecs ^
        react_codegen_RTNCustomViewSpecs ^
        react_codegen_reactnativemmkv ^
        react_codegen_rngesturehandler_codegen ^
        react_codegen_rnscreens ^
        react_codegen_safeareacontext
    from D:\RN_Project\study4\react-native-classroom-main\android\app
  ninja: error: Stat(C:&#47;Users&#47;PC&#47;.gradle&#47;caches&#47;transforms-3&#47;b65107381eb04de4935992b7f9f75be6&#47;transformed&#47;jetified-react-android-0.72.0-debug&#47;prefab&#47;modules&#47;rrc_legacyviewmanagerinterop&#47;include&#47;react&#47;renderer&#47;components&#47;legacyviewmanagerinterop&#47;UnstableLegacyViewManagerInteropComponentDescriptor.h): Filename longer than 260 characters</p>2024-03-24</li><br/><li><span>Print JQK°</span> 👍（0） 💬（0）<p>在使用tcp与服务端连接时，应用切到后台后与服务端的网络连接就断开了，如何才能实现网络保持连接</p>2023-12-07</li><br/><li><span>mike</span> 👍（0） 💬（0）<p>讲打包发布了吗？</p>2023-11-24</li><br/><li><span>请务必优秀</span> 👍（0） 💬（0）<p>为啥我连Homebrew都安装失败</p>2023-11-06</li><br/><li><span>侗家人ᯤ⁶ᴳ</span> 👍（0） 💬（0）<p>花了59块买了7天有效期，真是牛逼了！</p>2023-10-12</li><br/><li><span>五十米深蓝，</span> 👍（0） 💬（1）<p>老师 有windows环境的搭建教程吗</p>2023-07-06</li><br/>
</ul>