你好，我是蒋宏伟。这节课我们来做一次集中答疑。

我在后台留言里见到的最多的问题就是搭建环境卡住了，走不下去。为了方便新同学学习 React Native，更快地搭建好环境，今天我会从头到尾带你搭建一套新环境，帮助你快速上手。

先说结论：**没有畅通无阻的网络，搭建 React Native 环境是较为困难的，但并非不可能。**

在这节课中，我使用的是 MacBook Pro 2016 款，系统版本是 macOS Monterey。我参考的是 React Native 0.71 版的[官方文档](https://reactnative.dev/docs/next/environment-setup)，搭建的 iOS 环境。在按照官方文档搭建的过程中，我也遇到了较多的网络问题，但所有问题都通过镜像的方式解决了。

下面我就具体展示下我的搭建步骤，供你参考。如果遇到更多问题，欢迎给我留言。

## Homebrew

第一步是安装 Homebrew。Homebrew 是 Mac OS 的一个软件包管理器。

React Native 官方文档中，给了我们一个 Homebrew 的安装地址，从该地址可以进入 Homebrew 官方文档。

![图片](https://static001.geekbang.org/resource/image/fc/e1/fc55c1964cdf1848514b5cea04cdcde1.png?wh=1010x113)

该文档中会有如下命令，但执行命令后的结果会报错。

```plain
$ /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

报错内容如下：

![图片](https://static001.geekbang.org/resource/image/d2/b6/d23b379780c6d9b13c6a5ff38d198eb6.png?wh=1011x311)

报错的内容是 `unable to access github`，也就是**访问不到 GitHub 地址**。在后面还有非常多的类似网络报错。在这里，我就不再一一列举了。解决方案都是类似的，要么保持自己的网络畅通，要么使用相关的镜像源。

在知乎上有位大牛提供了 [Homebrew 镜像源及工具](https://zhuanlan.zhihu.com/p/111014448)，你可以通过如下命令一键安装。

```plain
$ /bin/zsh -c "$(curl -fsSL https://gitee.com/cunkai/HomebrewCN/raw/master/Homebrew.sh)"
```

![图片](https://static001.geekbang.org/resource/image/6a/01/6a254cd5cdc047f6c061032fec70bc01.png?wh=1019x661)

安装完成后，重启当前 Terminal，brew 就安装成功了。你可以运行如下命令，检查它是否安装成功。

```plain
$ brew --version
Homebrew 3.6.15
```

## Node 和 NPM

第二步是安装 Node 和 NPM。

Node 是 React Native 应用程序中，JavaScript 相关服务的运行环境，比如构建服务就是通过 Node 环境提供的。安装的 Node，会自带 NPM 包管理器，它将帮助我们管理相关依赖。

我们可以通过 Homebrew 来安装 Node。

```plain
$ brew install node
```

安装完成后，你可以通过如下命令检查 Node 和 NPM 是否安装成功。

```plain
$ node --version
$ npm --version
```

![图片](https://static001.geekbang.org/resource/image/40/54/408fedc765d5bf25a6bc02a4f0561154.png?wh=1152x221)

安装完 NPM 后，为保证后续网络的畅通，你需要将 NPM 的 registry 设置为淘宝源。切换命令如下：

```plain
npx nrm use taobao
```

## Watchman

第三步，是安装一个名为 Watchman 的工具。它是由 Facebook 开发的一个工具，只要你的文件有一些变化，它就会自动重新运行你的项目。

我们使用 Homebrew 来安装 watchman。

```plain
$ brew install watchman
```

安装完成后，通过如下命令检查是否安装成功。

```plain
$ watchman --version
```

![图片](https://static001.geekbang.org/resource/image/b4/33/b4d7931144c840357d6300c1e951f833.png?wh=1003x658)

## Ruby

第四步，要安装的是 Ruby。

Ruby 是一种常用编程语言。在 React Native iOS 应用的依赖管理中会使用到它。Mac 电脑上默认集成了 Ruby，但却和 React Native 所依赖的 Ruby 版本有些不一致。因此，**你需要通过 rbenv 对 Ruby 进行版本管理，就像使用 NVM 工具用于管理 Node 的版本一样。**

首先，你可以运行如下命令查看当前的 Ruby 版本。

```plain
$ ruby --version
```

![图片](https://static001.geekbang.org/resource/image/74/59/7471b043a8d299e9f38ca7808f99a659.png?wh=1375x97)

系统自带的 Ruby 是 2.6.10 版本，而 React Native 0.71 所依赖的 Ruby 版本是 [2.7.6](https://github.com/facebook/react-native/blob/main/template/_ruby-version)。因此，我们需要使用 [rbenv](https://github.com/rbenv/rbenv) 将 Ruby 版本切换到 2.7.6。

接着，你可以使用 Homebrew 安装 rbenv，安装命令如下：

```plain
$ brew install rbenv ruby-build 
```

安装完成后，运行 `init` 命令。运行完成后，它会提示你需要在 .zshrc 文件中执行 `rbenv init` 命令，因此你需要根据提示，使用 `echo` 将 `init` 命令添加到 Terminal 启动前。以保障 Terminal 启动时，rbenv 会生效。相关命令如下：

```plain
$ rbenv init

# 每人的提示信息不一定相同，根据提示信息进行相关操作
$ echo 'eval "$(rbenv init - zsh)"' >> ~/.zshrc
```

![图片](https://static001.geekbang.org/resource/image/25/0f/257578f9197b797d10dab413ba8b960f.png?wh=821x217)

命令执行完成后，重启 Terminal，安装并切换到 React Native 所依赖的 Ruby 版本。

```plain
$ rbenv install 2.7.6
$ rbenv global 2.7.6
```

切换完成 Ruby 版本后，再次重启 Terminal，再次运行 `ruby --version` 命令，确定 Ruby 版本是否切换成功。

![图片](https://static001.geekbang.org/resource/image/0b/cf/0b28e419f7b1e53b07d0f122f8bffccf.png?wh=1182x86)

### Gem 和 Bundler

第五步，是切换 Ruby 包管理工具的镜像源。

Ruby 有两种常用包管理工具，**Gem 和 Bundler**。这两种包管理工具都会用到，因此需要将这两种包管理工具的镜像源都切换到国内。

切换 Gem 镜像源的方法是通过 `gem sources` 命令进行切换，命令如下：

```plain
$ gem sources --add https://gems.ruby-china.com/ --remove https://rubygems.org/
$ gem sources -l
https://gems.ruby-china.com
```

这里我们使用 [Ruby China](https://gems.ruby-china.com/) 提供的镜像源进行安装。

切换 Bundler 镜像源的方法是通过设置 config 进行切换，命令如下：

```plain
$ bundle config mirror.https://rubygems.org https://gems.ruby-china.com
```

具体来说，它会在 Bundler 的全局配置中添加一个 `mirror.https://rubygems.org` 的参数，将其值设置为 `https://gems.ruby-china.com`，表示在下载和安装包时使用 [Ruby China](https://gems.ruby-china.com/) 的镜像源地址。

## Xcode

第六步，是安装和配置 Xcode。

安装 Xcode 有两种方法：

- 从 Mac App Store 中进行安装
- 从[开发者中心](https://developer.apple.com/download/all/)进行下载和安装

如果你的网络较好，你可以使用 Mac App Store 进行安装。打开 App Store，搜索 Xcode 进行下载。下载完成后，App Store 会自动帮你安装 Xcode。

![图片](https://static001.geekbang.org/resource/image/6c/81/6c4yy031435e96036e85201063e31f81.png?wh=1023x716)

但如果你的网络不好，从 Mac App Store 下载完成后，就会一直显示“正在等待…”。这是因为从 Xcode 的安装还依赖网络校验，网络校验不通过就会一直显示“正在等待…”。当出现这种情况时，你可以长按图标删除 Xcode，然后到开发者下载中心进行下载和安装。

![图片](https://static001.geekbang.org/resource/image/71/98/716fa2f861e309f78fdf5010d1795e98.png?wh=682x377)

第二种方法就是从[开发者中心](https://developer.apple.com/download/all/?q=xcode)进行下载。

从开发者中心进行下载需要一个 Apple ID，你需要自己申请一个，免费的就行。申请完成后，填写账号密码，登录开发者中心。

![图片](https://static001.geekbang.org/resource/image/39/40/39952391ccdb69b5db9b749fea102b40.png?wh=899x583)

在开发者中心搜索 Xcode，并找到你电脑操作系统版本所支持的 Xcode。因为我那台 16 年电脑的系统版本是 12.6.3，所以我下载的是 Xcode 14.0.1。

![图片](https://static001.geekbang.org/resource/image/9f/7a/9f12b040069c64914b6c2fdd6267b87a.png?wh=1018x289)

下载完成后，双击安装，点击 Agree，输入密码开始安装。

![图片](https://static001.geekbang.org/resource/image/6a/c4/6acd31934f0e4682caf0547dd04dabc4.png?wh=1007x488)

安装时，勾选默认的选项进行安装即可。

![图片](https://static001.geekbang.org/resource/image/19/db/19dba4b5c6afb61b55b75c37db826edb.png?wh=954x1011)

默认项安装完成后，找到左上角的 Xcode 标识，点击 Preferences。

![图片](https://static001.geekbang.org/resource/image/d5/b2/d5e73b6d6e7dc2ee67a0337d4d07a0b2.png?wh=1045x1029)

找到 Locations 标签中的 Command Line Tools 一栏，选择对应的 Xcode。选择完成后，会出现类似 `/Applications/Xcode.app` 之类的地址，你可以点进去，确定 Xcode 的目录地址是否正确。

![图片](https://static001.geekbang.org/resource/image/6e/34/6ea0dfb0e6a1be9debebbac5d273ec34.png?wh=1014x534)

确定完成后，就完成了 Xcode 的安装和配置。

### CocoaPods

第七步，是安装 CocoaPods。

在前面我们提到过，Ruby 有两种常用包管理工具，Gem 和 Bundler。CocoaPods 是另一种包管理工具，它虽然是用 Ruby 编写的，但不是 Ruby 的包管理工具，而是 iOS 的包管理工具。

这里我们借助 Gem 来安装 CocoaPods。

```plain
$ sudo gem install cocoapods
```

安装完成后，运行如下命令确定 CocoaPods 是否已经安装成功。

```plain
$ pod --version
1.11.3
```

## 新建项目

第七步，是新建一个 React Native 项目。

这里我们借助 React Native 内置的命令行工具，来创建一个名为 “AwesomeProject” 的新项目。

```plain
npx react-native init AwesomeProject
```

但是，在 “Installing CocoaPods dependencies” 这一步会出现错误，错误截图如下所示：

![图片](https://static001.geekbang.org/resource/image/f0/39/f06807d34abe2b69331c6d2ff2e18c39.png?wh=979x852)

这是由于没有切换 CocoaPods 的镜像源导致的。解决方案是，切换到[清华大学开源软件镜像站](https://mirrors.tuna.tsinghua.edu.cn/)的镜像，切换方式如下：

```plain
$ cd ~/.cocoapods/repos 
$ pod repo remove master
$ git clone https://mirrors.tuna.tsinghua.edu.cn/git/CocoaPods/Specs.git master
```

执行完上述命令后，进入 `AwesomeProject/ios` 目录，找到 Podfile 文件，在文件第一行添加：

```plain
source 'https://mirrors.tuna.tsinghua.edu.cn/git/CocoaPods/Specs.git'
```

这时，再在 `AwesomeProject/ios` 目录下，运行 CocoaPods 安装命令即可。

```plain
$ bundle exec pod install
```

但是，此时仍可能会遇到报错，报错内容如下：

![图片](https://static001.geekbang.org/resource/image/eb/52/ebe130179e04e224d921092ec5d2f552.png?wh=992x644)

报错的内容是，无法访问地址 `https://github.com/lblasa/double-conversion.git`。

这是因为，即便配置了镜像，但镜像提供的地址仍然是 GitHub 地址。执行 `pod install` 时，没有访问到 GitHub 地址。那么该怎么办呢？

**解决方案是，我们可以把所有的 GitHub 地址替换成 Gitee 地址，主要有以下四步**（该方案由群友柯察提供）：

> 1. 将 GitHub 仓库导入到 Gitee
> 2. 将 GitHub 地址的相关配置，手动替换为 Gitee 地址
> 3. 重新 pod install
> 4. 如遇报错，继续重复上述步骤

下面我们逐个步骤看一下。

第一步，将 GitHub 仓库导入到 Gitee。

首先，登录 [Gitee](https://gitee.com/)。从右上角的 “+” 号中找到“从 GitHub/GitLab 导入仓库”的功能。填写对应的 GitHub 地址，然后点击导入。

![图片](https://static001.geekbang.org/resource/image/5e/71/5e83449d09ce6dc01a05871703ee7171.png?wh=1016x519)

接着，进入该仓库后，找到 “克隆/下载” 按钮，复制其 HTTPS 地址，示例如下：

```plain
https://gitee.com/jhwleo/double-conversion.git
```

然后，为了方便克隆该仓库地址，你还需要将其从私有仓库设置为开源仓库。你需要先点击进入管理标签页，填写介绍，选择开源，并勾选公开须知，然后点击保存。设置方法见下图：

![图片](https://static001.geekbang.org/resource/image/b6/cf/b60863fc512bd5735893ca5544e452cf.png?wh=1016x303)

第二步，将 GitHub 地址的相关配置，手动替换为 Gitee 地址，详细操作如下。

首先，使用 [VSCode](https://code.visualstudio.com/) 编辑器，打开目录 `~/.cocoapods/repos/master`。

![图片](https://static001.geekbang.org/resource/image/f8/f6/f8a2c580db544750ed07324e745040f6.png?wh=1018x521)

然后，点击 Search 一栏，将 GitHub 地址替换成 Gitee 地址。

```plain
Github地址：github.com/lblasa/double-conversion.git

Gitee地址：gitee.com/jhwleo/double-conversion.git
```

![图片](https://static001.geekbang.org/resource/image/f9/00/f984a2857a5272f2b5590f1dc9cc8700.png?wh=1014x228)

第三步，重新 pod install。

由于下载地址已经改成了 Gitee，再次运行 `pod install` 时，就不会遇到 double-conversion 库无法访问的报错了。

![图片](https://static001.geekbang.org/resource/image/c1/39/c1212eec55cc8cfb7cd453f4063ea039.png?wh=995x653)

你可以看到，上图中的 Flipper-DoubleConversion(double-conversion) 库，在第二次安装的时候，已经安装成功。但是，我们又遇到了其他库的网络错误。

因此，**第四步是不断重复前三步的**，我们现在要做的就是将所有下载不了的 GitHub 地址都逐一替换成 Gitee 地址，完成 pod install 的步骤。

当然，由于在上述方案中，你需要一个个手动地进行更改和重试。所以建议有条件的同学，还是通过保持网络畅通的方式进行下载更为方便。

## 启动项目

最后一步是启动 React Native 项目。

在上一步中，我们通过 `npx react-native init` 命令创建了一个名为 “AwesomeProject” 的新项目。现在，我们进入该项目目录，运行如下命令来启动 iOS 项目。

```plain
npx react-native run-ios
```

命令运行后，会自动启动模拟器并加载项目。你可以看到如下界面：

![图片](https://static001.geekbang.org/resource/image/77/fe/7751377b91b3ae5982d74c70f4e051fe.png?wh=1020x718)

至此，我们已经成功搭建了 React Native 的开发环境，并成功运行了一个 React Native 项目。

## 总结

搭建开发环境是很多新同学的痛点，这一步劝退了很多想学习 React Native 的新同学。

在这节课中，我给你介绍了一种不借助网络工具搭建 React Native 环境的方法。它主要包括八个步骤，涉及了 Homebrew、Node、Watchman、Ruby、Gem、Bundler、Xcode、CocoaPods 的安装或镜像配置方案，以及如何新建项目和启动项目。

希望能对你有所帮助。

## 思考题

你在搭建 React Native 环境的过程中，遇到过哪些问题，能把你的解决方案和大家分享分享吗？

期待你的输出，如果觉得有所收获，也欢迎你把今天的内容分享给更多的朋友！
<div><strong>精选留言（11）</strong></div><ul>
<li><span>JawQ_</span> 👍（0） 💬（0）<p>请问有群吗？刚买了这个课程，就是希望有个共同学习rn的群可以交流一下</p>2024-08-21</li><br/><li><span>不矫情不做作那是我</span> 👍（0） 💬（0）<p>Installing OpenSSL-Universal (1.1.1100)

[!] Error installing OpenSSL-Universal
[!] &#47;usr&#47;bin&#47;curl -f -L -o &#47;var&#47;folders&#47;dy&#47;y_3zjx6j0rdbcbzgm625f6yc0000gn&#47;T&#47;d20240119-11554-l0dvbm&#47;file.zip https:&#47;&#47;github.com&#47;krzyzanowskim&#47;OpenSSL&#47;archive&#47;1.1.1100.zip --create-dirs --netrc-optional --retry 2 -A &#39;CocoaPods&#47;1.14.3 cocoapods-downloader&#47;2.1&#39;

  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
  0     0    0     0    0     0      0      0 --:--:--  0:01:15 --:--:--     0
curl: (28) Failed to connect to github.com port 443 after 75016 ms: Couldn&#39;t connect to server
Warning: Problem : timeout. Will retry in 1 seconds. 2 retries left.
  0     0    0     0    0     0      0      0 --:--:--  0:01:15 --:--:--     0
curl: (28) Failed to connect to github.com port 443 after 75023 ms: Couldn&#39;t connect to server
Warning: Problem : timeout. Will retry in 2 seconds. 1 retries left.
  0     0    0     0    0     0      0      0 --:--:--  0:01:15 --:--:--     0
curl: (28) Failed to connect to github.com port 443 after 75019 ms: Couldn&#39;t connect to server
我这个报错怎么解决啊 哪位大佬知道 实在没办法了</p>2024-01-19</li><br/><li><span>花永落</span> 👍（0） 💬（0）<p>bundle exec pod install;
报错] Invalid `Podfile` file: exit.

 #  from &#47;Users&#47;luojx&#47;crossEndPro&#47;AwesomeProject&#47;ios&#47;Podfile:35
有遇到该问题的吗?</p>2023-11-19</li><br/><li><span>Geek_f82ad7</span> 👍（0） 💬（0）<p>Mac OS X 10.11后安装cocoapods应该用下面的命令吧？
sudo gem install -n &#47;usr&#47;local&#47;bin cocoapods</p>2023-10-23</li><br/><li><span>钙中钙</span> 👍（0） 💬（0）<p>rbenv install 2.7.6的时候， 一直停在

Downloading ruby-2.7.6.tar.bz2...
-&gt; https:&#47;&#47;cache.ruby-lang.org&#47;pub&#47;ruby&#47;2.7&#47;ruby-2.7.6.tar.bz2

请问这个要如何解决啊</p>2023-08-22</li><br/><li><span>北鸟南游</span> 👍（0） 💬（0）<p>error Failed to build iOS project. We ran &quot;xcodebuild&quot; command but it exited with error code 65. 提示这个报错，有知道怎么解决吗？</p>2023-05-18</li><br/><li><span>Simplelicity</span> 👍（0） 💬（0）<p>Xcode14.3 里面运行不了，提示一堆错误</p>2023-04-28</li><br/><li><span>孤独的二向箔</span> 👍（0） 💬（0）<p>好顶赞！</p>2023-03-31</li><br/><li><span>墨色</span> 👍（0） 💬（2）<p>老师，能来一个Android的环境搭建吗
</p>2023-03-22</li><br/><li><span>Euterpe</span> 👍（0） 💬（1）<p>老师，可以讲解下旧的版本如何升级到最新版本么？我尝试了下，各种问题。</p>2023-03-16</li><br/><li><span>杨永安</span> 👍（0） 💬（1）<p>我半年前折腾不了了之，最近又跑了一次，居然成功了。</p>2023-03-08</li><br/>
</ul>