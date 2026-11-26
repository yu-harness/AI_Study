这一讲是“破冰篇”的最后一讲，我会先简单地回顾一下之前的内容，然后在Windows系统上实际操作，用几个应用软件搭建出一个“最小化”的HTTP实验环境，方便后续的“基础篇”“进阶篇”“安全篇”的学习。

## “破冰篇”回顾

HTTP协议诞生于30年前，设计之初的目的是用来传输纯文本数据。但由于形式灵活，搭配URI、HTML等技术能够把互联网上的资源都联系起来，构成一个复杂的超文本系统，让人们自由地获取信息，所以得到了迅猛发展。

HTTP有多个版本，目前应用的最广泛的是HTTP/1.1，它几乎可以说是整个互联网的基石。但HTTP/1.1的性能难以满足如今的高流量网站，于是又出现了HTTP/2和HTTP/3。不过这两个新版本的协议还没有完全推广开。在可预见的将来，HTTP/1.1还会继续存在下去。

HTTP翻译成中文是“超文本传输协议”，是一个应用层的协议，通常基于TCP/IP，能够在网络的任意两点之间传输文字、图片、音频、视频等数据。

HTTP协议中的两个端点称为**请求方**和**应答方**。请求方通常就是Web浏览器，也叫user agent，应答方是Web服务器，存储着网络上的大部分静态或动态的资源。

在浏览器和服务器之间还有一些“中间人”的角色，如CDN、网关、代理等，它们也同样遵守HTTP协议，可以帮助用户更快速、更安全地获取资源。

HTTP协议不是一个孤立的协议，需要下层很多其他协议的配合。最基本的是TCP/IP，实现寻址、路由和可靠的数据传输，还有DNS协议实现对互联网上主机的定位查找。

对HTTP更准确的称呼是“**HTTP over TCP/IP**”，而另一个“**HTTP over SSL/TLS**”就是增加了安全功能的HTTPS。

## 软件介绍

常言道“实践出真知”，又有俗语“光说不练是假把式”。要研究HTTP协议，最好有一个实际可操作、可验证的环境，通过实际的数据、现象来学习，肯定要比单纯的“动嘴皮子”效果要好的多。

现成的环境当然有，只要能用浏览器上网，就会有HTTP协议，就可以进行实验。但现实的网络环境又太复杂了，有很多无关的干扰因素，这些“噪音”会“淹没”真正有用的信息。

所以，我给你的建议是：搭建一个“**最小化**”的环境，在这个环境里仅有HTTP协议的两个端点：请求方和应答方，去除一切多余的环节，从而可以抓住重点，快速掌握HTTP的本质。

![](https://static001.geekbang.org/resource/image/85/0b/85cadf90dc96cf413afaf8668689ef0b.png?wh=3000%2A1681)

简单说一下这个“最小化”环境用到的应用软件：

- Wireshark
- Chrome/Firefox
- Telnet
- OpenResty

**Wireshark**是著名的网络抓包工具，能够截获在TCP/IP协议栈中传输的所有流量，并按协议类型、地址、端口等任意过滤，功能非常强大，是学习网络协议的必备工具。

它就像是网络世界里的一台“高速摄像机”，把只在一瞬间发生的网络传输过程如实地“拍摄”下来，事后再“慢速回放”，让我们能够静下心来仔细地分析那一瞬到底发生了什么。

**Chrome**是Google开发的浏览器，是目前的主流浏览器之一。它不仅上网方便，也是一个很好的调试器，对HTTP/1.1、HTTPS、HTTP/2、QUIC等的协议都支持得非常好，用F12打开“开发者工具”还可以非常详细地观测HTTP传输全过程的各种数据。

如果你更习惯使用**Firefox**，那也没问题，其实它和Chrome功能上都差不太多，选择自己喜欢的就好。

与Wireshark不同，Chrome和Firefox属于“事后诸葛亮”，不能观测HTTP传输的过程，只能看到结果。

**Telnet**是一个经典的虚拟终端，基于TCP协议远程登录主机，我们可以使用它来模拟浏览器的行为，连接服务器后手动发送HTTP请求，把浏览器的干扰也彻底排除，能够从最原始的层面去研究HTTP协议。

**OpenResty**你可能比较陌生，它是基于Nginx的一个“强化包”，里面除了Nginx还有一大堆有用的功能模块，不仅支持HTTP/HTTPS，还特别集成了脚本语言Lua简化Nginx二次开发，方便快速地搭建动态网关，更能够当成应用容器来编写业务逻辑。

选择OpenResty而不直接用Nginx的原因是它相当于Nginx的“超集”，功能更丰富，安装部署更方便。我也会用Lua编写一些服务端脚本，实现简单的Web服务器响应逻辑，方便实验。

## 安装过程

这个“最小化”环境的安装过程也比较简单，大约只需要你半个小时不到的时间就能搭建完成。

我在GitHub上为本专栏开了一个项目：[http\_study](https://github.com/chronolaw/http_study.git)，可以直接用“git clone”下载，或者去Release页面，下载打好的[压缩包](https://github.com/chronolaw/http_study/releases)。

我使用的操作环境是Windows 10，如果你用的是Mac或者Linux，可以用VirtualBox等虚拟机软件安装一个Windows虚拟机，再在里面操作（或者可以到“答疑篇”的[Linux/Mac实验环境搭建](https://time.geekbang.org/column/article/146833)中查看搭建方法）。

首先你要获取**最新**的http\_study项目源码，假设clone或解压的目录是“D:\\http\_study”，操作完成后大概是下图这个样子。

![](https://static001.geekbang.org/resource/image/86/ee/862511b8ef87f78218631d832927bcee.png?wh=2000%2A1121)

Chrome和WireShark的安装比较简单，一路按“下一步”就可以了。版本方面使用最新的就好，我的版本可能不是最新的，Chrome是73，WireShark是3.0.0。

Windows 10自带Telnet，不需要安装，但默认是不启用的，需要你稍微设置一下。

打开Windows的设置窗口，搜索“Telnet”，就会找到“启用或关闭Windows功能”，在这个窗口里找到“Telnet客户端”，打上对钩就可以了，可以参考截图。

![](https://static001.geekbang.org/resource/image/1a/47/1af035861c4fd33cb42005eaa1f5f247.png?wh=2000%2A1121)

接下来我们要安装OpenResty，去它的[官网](http://openresty.org)，点击左边栏的“Download”，进入下载页面，下载适合你系统的版本（这里我下载的是64位的1.15.8.1，包的名字是“openresty-1.15.8.1-win64.zip”）。

![](https://static001.geekbang.org/resource/image/ee/0a/ee7016fecd79919de550677af32f740a.png?wh=2000%2A760)

然后要注意，你必须把OpenResty的压缩包解压到刚才的“D:\\http\_study”目录里，并改名为“openresty”。

![](https://static001.geekbang.org/resource/image/5a/b5/5acb89c96041f91bbc747b7e909fd4b5.png?wh=2000%2A1121)

安装工作马上就要完成了，为了能够让浏览器能够使用DNS域名访问我们的实验环境，还要改一下本机的hosts文件，位置在“C:\\WINDOWS\\system32\\drivers\\etc”，在里面添加三行本机IP地址到测试域名的映射，你也可以参考GitHub项目里的hosts文件，这就相当于在一台物理实机上“托管”了三个虚拟主机。

```
127.0.0.1       www.chrono.com
127.0.0.1       www.metroid.net
127.0.0.1       origin.io
```

注意修改hosts文件需要管理员权限，直接用记事本编辑是不行的，可以切换管理员身份，或者改用其他高级编辑器，比如Notepad++，而且改之前最好做个备份。

到这里，我们的安装工作就完成了！之后你就可以用Wireshark、Chrome、Telnet在这个环境里随意“折腾”，弄坏了也不要紧，只要把目录删除，再来一遍操作就能复原。

## 测试验证

实验环境搭建完了，但还需要把它运行起来，做一个简单的测试验证，看是否运转正常。

首先我们要启动Web服务器，也就是OpenResty。

在http\_study的“www”目录下有四个批处理文件，分别是：

![](https://static001.geekbang.org/resource/image/e5/da/e5d35bb94c46bfaaf8ce5c143b2bb2da.png?wh=2000%2A1121)

- start：启动OpenResty服务器；
- stop：停止OpenResty服务器；
- reload：重启OpenResty服务器；
- list：列出已经启动的OpenResty服务器进程。

使用鼠标双击“start”批处理文件，就会启动OpenResty服务器在后台运行，这个过程可能会有Windows防火墙的警告，选择“允许”即可。

运行后，鼠标双击“list”可以查看OpenResty是否已经正常启动，应该会有两个nginx.exe的后台进程，大概是下图的样子。

![](https://static001.geekbang.org/resource/image/db/1d/dba34b8a38e98bef92289315db29ee1d.png?wh=2000%2A661)

有了Web服务器后，接下来我们要运行Wireshark，开始抓包。

因为我们的实验环境运行在本机的127.0.0.1上，也就是loopback“环回”地址。所以，在Wireshark里要选择“Npcap loopback Adapter”，过滤器选择“HTTP TCP port(80)”，即只抓取HTTP相关的数据包。鼠标双击开始界面里的“Npcap loopback Adapter”即可开始抓取本机上的网络数据。

![](https://static001.geekbang.org/resource/image/12/c4/128d8a5ed9cdd666dbfa4e17fd39afc4.png?wh=2000%2A728)

然后我们打开Chrome，在地址栏输入“`http://localhost`”，访问刚才启动的OpenResty服务器，就会看到一个简单的欢迎界面，如下图所示。

![](https://static001.geekbang.org/resource/image/d7/88/d7f12d4d480d7100cd9804d2b16b8a88.png?wh=2000%2A672)

这时再回头去看Wireshark，应该会显示已经抓到了一些数据，就可以用鼠标点击工具栏里的“停止捕获”按钮告诉Wireshark“到此为止”，不再继续抓包。

![](https://static001.geekbang.org/resource/image/f7/79/f7d05a3939d81742f18d2da7a1883179.png?wh=2000%2A587)

至于这些数据是什么，表示什么含义，我会在下一讲再详细介绍。

如果你能够在自己的电脑上走到这一步，就说明“最小化”的实验环境已经搭建成功了，不要忘了实验结束后运行批处理“stop”停止OpenResty服务器。

## 小结

这次我们学习了如何在自己的电脑上搭建HTTP实验环境，在这里简单小结一下今天的内容。

1. 现实的网络环境太复杂，有很多干扰因素，搭建“最小化”的环境可以快速抓住重点，掌握HTTP的本质；
2. 我们选择Wireshark作为抓包工具，捕获在TCP/IP协议栈中传输的所有流量；
3. 我们选择Chrome或Firefox浏览器作为HTTP协议中的user agent；
4. 我们选择OpenResty作为Web服务器，它是一个Nginx的“强化包”，功能非常丰富；
5. Telnet是一个命令行工具，可用来登录主机模拟浏览器操作；
6. 在GitHub上可以下载到本专栏的专用项目源码，只要把OpenResty解压到里面即可完成实验环境的搭建。

## 课下作业

1.按照今天所学的，在你自己的电脑上搭建出这个HTTP实验环境并测试验证。

2.由于篇幅所限，我无法详细介绍Wireshark，你有时间可以再上网搜索Wireshark相关的资料，了解更多的用法。

欢迎你把自己的学习体会写在留言区，与我和其他同学一起讨论。如果你觉得有所收获，也欢迎把文章分享给你的朋友。

![unpreview](https://static001.geekbang.org/resource/image/03/dd/03727c2a64cbc628ec18cf39a6a526dd.png?wh=1769%2A3004)

![unpreview](https://static001.geekbang.org/resource/image/56/63/56d766fc04654a31536f554b8bde7b63.jpg?wh=1110%2A659)
<div><strong>精选留言（15）</strong></div><ul>
<li><span>cylim</span> 👍（157） 💬（12）<p>在Mac上，

拷贝项目（需要Git）
1. git clone https:&#47;&#47;github.com&#47;chronolaw&#47;http_study

安装OpenResty （推荐使用Homebrew）
1. brew tap openresty&#47;brew
2. brew install openresty 

运行项目
1. cd http_study&#47;www&#47;
2. openresty -p `pwd` -c conf&#47;nginx.conf

停止项目
1. openresty -s quit -p `pwd` -c conf&#47;nginx.conf</p>2019-06-12</li><br/><li><span>前端西瓜哥</span> 👍（29） 💬（6）<p>对 cylim 的 mac 上运行 openresty 的教程进行补充：
按照 cylim 的做法，我遇到了访问 localhost 时，网页报 403 错误的情况，原因是没有 html&#47;index.html 文件的访问权限。我研究并找到了解决方案：
先 ls -la html，查看文件的权限，得到 user 和 group，我这里是 fstar 和 staff。

然后在 conf&#47;nginx.conf 文件的顶部添加

user fstar staff;

然后再启动 openresty 就可以正常访问了。</p>2019-06-28</li><br/><li><span>古夜</span> 👍（23） 💬（7）<p>我打赌很多人抓不到包，找不到本地回环地址，不知道最新版的wireshark是否修复了这个问题，如果出现以上问题，记得卸载重装wireshark，不要勾选它自带的ncap应该是这个名字，然后自己去单独下一个这个软件</p>2019-06-12</li><br/><li><span>geek桃</span> 👍（17） 💬（5）<p>送给后来的同学：
如果你按照步骤操作之后出现：start启动完成后，cmd窗口一闪而过，点击list启动时显示“没有运行的任务匹配制定标准”，请按任意键继续，当随便输入数据时，cmd窗口又没了；去查找www&#47;logs&#47;error.log，如果日志报错为“10013: An attempt was made to access a socket in a way forbidden by its access permissions”，说明你的80端口被占用了，按照下面步骤操作。
1.按键盘win+r 打开运行界面，输入cmd，确定，打开管理员界面
2.输入 netstat -aon | findstr :80 （有一条0.0.0.0的数据，记住这条数据最后的数字；我的是5884）
3.输入  tasklist|findstr &quot;5884&quot; （根据上一步查到的数字，找到5884端口对应的服务名称，我的是snv）
4.在控制台关闭服务
5.重新启动start.bat，成功！
</p>2021-03-03</li><br/><li><span>名曰蓝兮</span> 👍（17） 💬（1）<p>centos上的安装步骤，有错误请指出
wireshark：
1. yum install wireshark
    yum install wireshark-gnome
2. 如果不是root用户，启动后没有权限，做如下操作
    2.1 添加当前用户到wireshark组，我的用户叫&#39;zp&#39;：
          usermod -a -G wireshark zp
    2.2 然后给dumpcap读网卡的权限：
          setcap cap_net_raw,cap_net_admin+eip &#47;usr&#47;sbin&#47;dumpcap
完成后重启机器。

telnet：
yum install telnet

OpenResty:
官网有说明，按照说明一步步来
1. 添加OpenResty仓库：
    sudo yum install yum-utils
    sudo yum-config-manager --add-repo https:&#47;&#47;openresty.org&#47;package&#47;centos&#47;openresty.repo
2. 安装OpenResty:
    sudo yum install openresty
    sudo yum install openresty-resty
3. 在～目录下创建conf和logs文件夹：
    mkdir ~&#47;work
    cd ~&#47;work
    mkdir logs&#47; conf&#47;
4. 在conf文件夹下创建nginx.conf文件，内容如下：
worker_processes  1;
error_log logs&#47;error.log;
events {
    worker_connections 1024;
}
http {
    server {
        listen 8080;
        location &#47; {
            default_type text&#47;html;
            content_by_lua_block {
                ngx.say(&quot;&lt;p&gt;hello, world&lt;&#47;p&gt;&quot;)
            }
        }
    }
}
5. 添加OpenResty环境变量，注意冒号，别丢了:
    PATH=&#47;usr&#47;local&#47;openresty&#47;nginx&#47;sbin:$PATH
    export PATH
6. 在&#39;~&#47;work&#39;目录下启动OpenResty:
    nginx -p `pwd`&#47; -c conf&#47;nginx.conf
7. 验证安装：
    curl http:&#47;&#47;localhost:8080
    输出：
    &lt;p&gt;hello, world&lt;&#47;p&gt;</p>2019-06-19</li><br/><li><span>珈蓝白塔</span> 👍（16） 💬（5）<p>Mac 开发环境的搭建参考《答疑篇41》，项目中已经有前辈写好的 shell 脚本，终端里直接运行就可以，不需要自己输入 openresty 命令啦；服务器启动以后访问 localhost 环境遇到了 403 问题，显示不出来 HTML，可参照留言区中提出的，在 conf&#47;nginx.conf 文件的顶部添加 user xxxx staff; 来解决，这个 xxxx 是自己的 mac 账户名；Wireshark(v3.2.3) 中选择环回地址时，选择 lockback：lo0 就可以啦，过滤器是和文中一样的，已成功搭建环境（2020年4月13日）</p>2020-04-13</li><br/><li><span>YUANWOW</span> 👍（12） 💬（4）<p>我一开始nginx一直起不来
后面看了error.log
发现本机443端口被占用了
netstat -ano | findstr &quot;443&quot;
看到一个 0.0.0.0:443  最后一列是进程的PID
查找到是vmware-hostd这个进程
后面谷歌搜索了下 
vmware的虚拟机共享会默认占用443端口
所以安装了vmware的把虚拟机共享关闭就好了  </p>2019-07-02</li><br/><li><span>geraltlaush</span> 👍（11） 💬（1）<p>破冰篇最后一篇，是马上开展破冰行动，抓捕林耀东了吗</p>2019-06-12</li><br/><li><span>pyhhou</span> 👍（11） 💬（2）<p>想请问下在 MacOs 或者是 Linux 上怎么搭建？（不是太想弄 Windows 虚拟机）</p>2019-06-12</li><br/><li><span>郁方林</span> 👍（10） 💬（2）<p>start启动完成后，cmd窗口一闪而过，当我点击list启动时显示“没有运行的任务匹配制定标准”，请按任意键继续，当我随便输入数据时，cmd窗口又没了</p>2019-06-12</li><br/><li><span>Geek_d4dee7</span> 👍（7） 💬（1）<p>老师 最近我维护的一个网站打开速度非常慢  服务器CPU 负载0.5到0.8之间 有十多台web 服务器  redis  db  负载都正常 只是nginx 的链接数在出问题的时间点有上升  我目前不知道从哪下手排查这个问题 是用php symfony 开发的  能否给点思路 万分感谢</p>2019-06-12</li><br/><li><span>兔嘟嘟</span> 👍（6） 💬（2）<p>windows上装的最新的3.4.7版，没有npcap，但是有一个Adapter for loopback traffic，用起来效果一样，就是抓到的Source是::1，猜测是这台电脑比较新，用上了IPv6的localhost</p>2021-07-16</li><br/><li><span>Amark</span> 👍（6） 💬（1）<p>老师，上面过程怎么没有用到telnet</p>2019-06-12</li><br/><li><span>geraltlaush</span> 👍（5） 💬（1）<p>老师可以把环境打包成容器，我们进容器直接嗨，隔离更彻底</p>2019-06-12</li><br/><li><span>Cris</span> 👍（4） 💬（1）<p>在浏览器和服务器之间还存在“中间人”，这些中间人也都遵循http协议，我想问下，这些中间人是不是都工作在应用层？</p>2019-07-11</li><br/>
</ul>