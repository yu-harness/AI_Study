你可能或多或少听别人说过，“HTTPS的连接很慢”。那么“慢”的原因是什么呢？

通过前两讲的学习，你可以看到，HTTPS连接大致上可以划分为两个部分，第一个是建立连接时的**非对称加密握手**，第二个是握手后的**对称加密报文传输**。

由于目前流行的AES、ChaCha20性能都很好，还有硬件优化，报文传输的性能损耗可以说是非常地小，小到几乎可以忽略不计了。所以，通常所说的“HTTPS连接慢”指的就是刚开始建立连接的那段时间。

在TCP建连之后，正式数据传输之前，HTTPS比HTTP增加了一个TLS握手的步骤，这个步骤最长可以花费两个消息往返，也就是2-RTT。而且在握手消息的网络耗时之外，还会有其他的一些“隐形”消耗，比如：

- 产生用于密钥交换的临时公私钥对（ECDHE）；
- 验证证书时访问CA获取CRL或者OCSP；
- 非对称加密解密处理“Pre-Master”。

在最差的情况下，也就是不做任何的优化措施，HTTPS建立连接可能会比HTTP慢上几百毫秒甚至几秒，这其中既有网络耗时，也有计算耗时，就会让人产生“打开一个HTTPS网站好慢啊”的感觉。

不过刚才说的情况早就是“过去时”了，现在已经有了很多行之有效的HTTPS优化手段，运用得好可以把连接的额外耗时降低到几十毫秒甚至是“零”。

我画了一张图，把TLS握手过程中影响性能的部分都标记了出来，对照着它就可以“有的放矢”地来优化HTTPS。

![](https://static001.geekbang.org/resource/image/c4/ed/c41da1f1b1bdf4dc92c46330542c5ded.png?wh=2017%2A1754)

## 硬件优化

在计算机世界里的“优化”可以分成“硬件优化”和“软件优化”两种方式，先来看看有哪些硬件的手段。

硬件优化，说白了就是“花钱”。但花钱也是有门道的，要“有钱用在刀刃上”，不能大把的银子撒出去“只听见响”。

HTTPS连接是计算密集型，而不是I/O密集型。所以，如果你花大价钱去买网卡、带宽、SSD存储就是“南辕北辙”了，起不到优化的效果。

那该用什么样的硬件来做优化呢？

首先，你可以选择**更快的CPU**，最好还内建AES优化，这样即可以加速握手，也可以加速传输。

其次，你可以选择“**SSL加速卡**”，加解密时调用它的API，让专门的硬件来做非对称加解密，分担CPU的计算压力。

不过“SSL加速卡”也有一些缺点，比如升级慢、支持算法有限，不能灵活定制解决方案等。

所以，就出现了第三种硬件加速方式：“**SSL加速服务器**”，用专门的服务器集群来彻底“卸载”TLS握手时的加密解密计算，性能自然要比单纯的“加速卡”要强大的多。

## 软件优化

不过硬件优化方式中除了CPU，其他的通常可不是靠简单花钱就能买到的，还要有一些开发适配工作，有一定的实施难度。比如，“加速服务器”中关键的一点是通信必须是“异步”的，不能阻塞应用服务器，否则加速就没有意义了。

所以，软件优化的方式相对来说更可行一些，性价比高，能够“少花钱，多办事”。

软件方面的优化还可以再分成两部分：一个是**软件升级**，一个是**协议优化**。

软件升级实施起来比较简单，就是把现在正在使用的软件尽量升级到最新版本，比如把Linux内核由2.x升级到4.x，把Nginx由1.6升级到1.16，把OpenSSL由1.0.1升级到1.1.0/1.1.1。

由于这些软件在更新版本的时候都会做性能优化、修复错误，只要运维能够主动配合，这种软件优化是最容易做的，也是最容易达成优化效果的。

但对于很多大中型公司来说，硬件升级或软件升级都是个棘手的问题，有成千上万台各种型号的机器遍布各个机房，逐一升级不仅需要大量人手，而且有较高的风险，可能会影响正常的线上服务。

所以，在软硬件升级都不可行的情况下，我们最常用的优化方式就是在现有的环境下挖掘协议自身的潜力。

## 协议优化

从刚才的TLS握手图中你可以看到影响性能的一些环节，协议优化就要从这些方面着手，先来看看核心的密钥交换过程。

如果有可能，应当尽量采用TLS1.3，它大幅度简化了握手的过程，完全握手只要1-RTT，而且更加安全。

如果暂时不能升级到1.3，只能用1.2，那么握手时使用的密钥交换协议应当尽量选用椭圆曲线的ECDHE算法。它不仅运算速度快，安全性高，还支持“False Start”，能够把握手的消息往返由2-RTT减少到1-RTT，达到与TLS1.3类似的效果。

另外，椭圆曲线也要选择高性能的曲线，最好是x25519，次优选择是P-256。对称加密算法方面，也可以选用“AES\_128\_GCM”，它能比“AES\_256\_GCM”略快一点点。

在Nginx里可以用“ssl\_ciphers”“ssl\_ecdh\_curve”等指令配置服务器使用的密码套件和椭圆曲线，把优先使用的放在前面，例如：

```
ssl_ciphers   TLS13-AES-256-GCM-SHA384:TLS13-CHACHA20-POLY1305-SHA256:EECDH+CHACHA20；
ssl_ecdh_curve              X25519:P-256;
```

## 证书优化

除了密钥交换，握手过程中的证书验证也是一个比较耗时的操作，服务器需要把自己的证书链全发给客户端，然后客户端接收后再逐一验证。

这里就有两个优化点，一个是**证书传输**，一个是**证书验证**。

服务器的证书可以选择椭圆曲线（ECDSA）证书而不是RSA证书，因为224位的ECC相当于2048位的RSA，所以椭圆曲线证书的“个头”要比RSA小很多，即能够节约带宽也能减少客户端的运算量，可谓“一举两得”。

客户端的证书验证其实是个很复杂的操作，除了要公钥解密验证多个证书签名外，因为证书还有可能会被撤销失效，客户端有时还会再去访问CA，下载CRL或者OCSP数据，这又会产生DNS查询、建立连接、收发数据等一系列网络通信，增加好几个RTT。

CRL（Certificate revocation list，证书吊销列表）由CA定期发布，里面是所有被撤销信任的证书序号，查询这个列表就可以知道证书是否有效。

但CRL因为是“定期”发布，就有“时间窗口”的安全隐患，而且随着吊销证书的增多，列表会越来越大，一个CRL经常会上MB。想象一下，每次需要预先下载几M的“无用数据”才能连接网站，实用性实在是太低了。

所以，现在CRL基本上不用了，取而代之的是OCSP（在线证书状态协议，Online Certificate Status Protocol），向CA发送查询请求，让CA返回证书的有效状态。

但OCSP也要多出一次网络请求的消耗，而且还依赖于CA服务器，如果CA服务器很忙，那响应延迟也是等不起的。

于是又出来了一个“补丁”，叫“OCSP Stapling”（OCSP装订），它可以让服务器预先访问CA获取OCSP响应，然后在握手时随着证书一起发给客户端，免去了客户端连接CA服务器查询的时间。

## 会话复用

到这里，我们已经讨论了四种HTTPS优化手段（硬件优化、软件优化、协议优化、证书优化），那么，还有没有其他更好的方式呢？

我们再回想一下HTTPS建立连接的过程：先是TCP三次握手，然后是TLS一次握手。这后一次握手的重点是算出主密钥“Master Secret”，而主密钥每次连接都要重新计算，未免有点太浪费了，如果能够把“辛辛苦苦”算出来的主密钥缓存一下“重用”，不就可以免去了握手和计算的成本了吗？

这种做法就叫“**会话复用**”（TLS session resumption），和HTTP Cache一样，也是提高HTTPS性能的“大杀器”，被浏览器和服务器广泛应用。

会话复用分两种，第一种叫“**Session ID**”，就是客户端和服务器首次连接后各自保存一个会话的ID号，内存里存储主密钥和其他相关的信息。当客户端再次连接时发一个ID过来，服务器就在内存里找，找到就直接用主密钥恢复会话状态，跳过证书验证和密钥交换，只用一个消息往返就可以建立安全通信。

实验环境的端口441实现了“Session ID”的会话复用，你可以访问URI  
“[https://www.chrono.com:441/28-1](https://www.chrono.com:441/28-1)”，刷新几次，用Wireshark抓包看看实际的效果。

```
Handshake Protocol: Client Hello
    Version: TLS 1.2 (0x0303)
    Session ID: 13564734eeec0a658830cd…
    Cipher Suites Length: 34


Handshake Protocol: Server Hello
    Version: TLS 1.2 (0x0303)
    Session ID: 13564734eeec0a658830cd…
    Cipher Suite: TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384 (0xc030)
```

通过抓包可以看到，服务器在“ServerHello”消息后直接发送了“Change Cipher Spec”和“Finished”消息，复用会话完成了握手。

![](https://static001.geekbang.org/resource/image/12/ac/125fe443a147ed38a97a4492045d98ac.png?wh=2004%2A2892)

## 会话票证

“Session ID”是最早出现的会话复用技术，也是应用最广的，但它也有缺点，服务器必须保存每一个客户端的会话数据，对于拥有百万、千万级别用户的网站来说存储量就成了大问题，加重了服务器的负担。

于是，又出现了第二种“**Session Ticket**”方案。

它有点类似HTTP的Cookie，存储的责任由服务器转移到了客户端，服务器加密会话信息，用“New Session Ticket”消息发给客户端，让客户端保存。

重连的时候，客户端使用扩展“**session\_ticket**”发送“Ticket”而不是“Session ID”，服务器解密后验证有效期，就可以恢复会话，开始加密通信。

这个过程也可以在实验环境里测试，端口号是442，URI是“[https://www.chrono.com:442/28-1](https://www.chrono.com:442/28-1)”。

不过“Session Ticket”方案需要使用一个固定的密钥文件（ticket\_key）来加密Ticket，为了防止密钥被破解，保证“前向安全”，密钥文件需要定期轮换，比如设置为一小时或者一天。

## 预共享密钥

“False Start”“Session ID”“Session Ticket”等方式只能实现1-RTT，而TLS1.3更进一步实现了“**0-RTT**”，原理和“Session Ticket”差不多，但在发送Ticket的同时会带上应用数据（Early Data），免去了1.2里的服务器确认步骤，这种方式叫“**Pre-shared Key**”，简称为“PSK”。

![](https://static001.geekbang.org/resource/image/11/ab/119cfd261db49550411a12b1f6d826ab.png?wh=2001%2A1446)

但“PSK”也不是完美的，它为了追求效率而牺牲了一点安全性，容易受到“重放攻击”（Replay attack）的威胁。黑客可以截获“PSK”的数据，像复读机那样反复向服务器发送。

解决的办法是只允许安全的GET/HEAD方法（参见[第10讲](https://time.geekbang.org/column/article/101518)），在消息里加入时间戳、“nonce”验证，或者“一次性票证”限制重放。

## 小结

1. 可以有多种硬件和软件手段减少网络耗时和计算耗时，让HTTPS变得和HTTP一样快，最可行的是软件优化；
2. 应当尽量使用ECDHE椭圆曲线密码套件，节约带宽和计算量，还能实现“False Start”；
3. 服务器端应当开启“OCSP Stapling”功能，避免客户端访问CA去验证证书；
4. 会话复用的效果类似Cache，前提是客户端必须之前成功建立连接，后面就可以用“Session ID”“Session Ticket”等凭据跳过密钥交换、证书验证等步骤，直接开始加密通信。

## 课下作业

1. 你能比较一下“Session ID”“Session Ticket”“PSK”这三种会话复用手段的异同吗？
2. 你觉得哪些优化手段是你在实际工作中能用到的？应该怎样去用？

欢迎你把自己的学习体会写在留言区，与我和其他同学一起讨论。如果你觉得有所收获，也欢迎把文章分享给你的朋友。

![unpreview](https://static001.geekbang.org/resource/image/a2/ab/a251606fb0637c6db45b7fd6660af5ab.png?wh=1769%2A3265)
<div><strong>精选留言（15）</strong></div><ul>
<li><span>-W.LI-</span> 👍（17） 💬（2）<p>Session ID:会话复用压力在服务端
Session Ticket:压力在客户端，客户端不安全所以要频繁换密钥文件
PSK:验证阶段把数据也带上，少一次请求
前两个都是缓存复用的思想，重用之前计算好的结果，达到降低CPU的目的。第三个就是少一次链接减少网络开销。
感觉都可以把开销大的东西缓存起来复用，缓存真个好东西，空间局部命中和时间局部命中定理太牛逼了。不过最关键的还是找性能瓶颈，精确定位性能瓶颈比较重要，然后针对瓶颈优化，空间换时间或者时间换空间。这个时候算法的价值就体现出来了。可惜这些我都不会╯﹏╰</p>2019-07-31</li><br/><li><span>俊伟</span> 👍（10） 💬（1）<p>session id 把会话信息存在服务端
session ticket 把会话信息存在客户端
psk 在session ticket 的基础上，使用early data顺便再发送一下服务端的数据</p>2020-01-17</li><br/><li><span>前端西瓜哥</span> 👍（7） 💬（1）<p>1. 你能比较一下“Session ID”“Session Ticket”“PSK”这三种会话复用手段的异同吗？

答：
（1）Session ID 类似网站开发中用来验证用户的 cookie，服务器会保存 Session ID对应的主密钥，需要用到服务器的存储空间。
（2）Session Ticket 貌似有点类似网站开发中的 JWT（JSON Web Token），JWT的做法是服务器将必要的信息（主密钥和过期时间）加上密钥进行 HMAC 加密，然后将生成的密文和原文相连得到 JWT 字符串，交给客户端。当客户端发送 JWT 给服务端后，服务器会取出其中的原文和自己的密钥进行 HMAC 运算，如果得到的结果和 JWT 中的密文一样，就说明是服务端颁发的 JWT，服务器就会认为 JWT 存储 的主密钥和有效时间是有效的。另外，JWT 中不应该存放用户的敏感信息，明文部分任何人可见（不知道 Session Ticket 的实现是不是也是这样？）
（3）PSK 不是很懂，貌似是在 tcp 握手的时候，就直接给出了 Ticket（可是这样 Ticket 好像没有加密呢）。

总的来说，Session ID 需要服务器来存储会话；而 Session Ticket 则不需要服务器使用存储空间，但要保护好密钥。另外为了做到“前向安全”，需要经常更换密钥。PSK相比 Session Tick，直接在第一次握手时，就将 ticket 发送过去了，减少了握手次数。</p>2019-08-01</li><br/><li><span>Wr</span> 👍（3） 💬（1）<p>1、相同点：都是会话复用技术
区别：
Seesion ID：会话数据缓存在服务端，如果服务器客户量大，对服务器会造成很大压力
Seeion Ticket：会话数据缓存在客户端
PAK：在Seesion Ticket的基础上，应用数据和Session Ticket一起发送给服务器，省去了中间服务器与客户端的确认步骤

2、暂无</p>2020-01-14</li><br/><li><span>饭粒</span> 👍（2） 💬（2）<p>1.抓包看了下 442 ，复用会话时 Client Hello session_ticket 确实有数据，Sessioin Id 好像也还会复用。
Transport Layer Security
    TLSv1.2 Record Layer: Handshake Protocol: Client Hello
        Content Type: Handshake (22)
        Version: TLS 1.0 (0x0301)
        Length: 512
        Handshake Protocol: Client Hello
            ...
            Random: 9474888cafdce89fd32eac247a8b464f842efbac706d8930…
            Session ID Length: 32
            Session ID: a4a0caef10dee7a6f44aa522a35f6c799101d5eced01eb32…   # Session ID
            ...
            Extension: session_ticket (len=192)     # session_ticket
                Type: session_ticket (35)
                Length: 192
                Data (192 bytes)
            ...

Transport Layer Security
    TLSv1.2 Record Layer: Handshake Protocol: Server Hello
        Content Type: Handshake (22)
        Version: TLS 1.2 (0x0303)
        Length: 100
        Handshake Protocol: Server Hello
            ...
            Random: e82519e9e8bfcbd40e1da7a202bd50ff993d5ef0cbc33378…
            Session ID Length: 32
            Session ID: a4a0caef10dee7a6f44aa522a35f6c799101d5eced01eb32…   # Session ID
            Cipher Suite: TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384 (0xc030)
            ...
    TLSv1.2 Record Layer: Change Cipher Spec Protocol: Change Cipher Spec
    TLSv1.2 Record Layer: Handshake Protocol: Finished   

2.有个疑问：会话复用技术，保存会话数据的一端使用对端传过来的 Sessin Id 查询到之前的 master secret，但它如何安全的把这个 master secret 传递给对端（对端应该只有 Sessin Id 吧）？

3.抓包过程用 Chrome 发请求，前三次 Client Hello, Server Hello 握手过程都因为 Alert (Level: Fatal, Description: Certificate Unknown) 失败了，第四次才成功。 而使用 FireFox 发请则不会出现。这是因为 Chrome 内置的证书更少吗？</p>2020-05-05</li><br/><li><span>lesserror</span> 👍（2） 💬（1）<p>老师，以下问题麻烦请回答一下：
1.客户端有时还会再去访问 CA，下载 CRL 或者 OCSP 数据，这又会产生 DNS 查询、建立连接、收发数据等一系列网络通信，增加好几个 RTT。这个CRL 或者 OCSP是对应到某个网址上面的嘛？客户端根据网址访问？

2.它可以让服务器预先访问 CA 获取 OCSP 响应，然后在握手时随着证书一起发给客户端，免去了客户端连接 CA 服务器查询的时间。这里不是客户端自己去验证的会不会有问题？服务器自己代做了。</p>2019-12-21</li><br/><li><span>ifelse</span> 👍（1） 💬（1）<p>good good study，day day up.</p>2023-01-31</li><br/><li><span>路漫漫</span> 👍（1） 💬（1）<p>老师，文章里说，这后一次握手的重点是算出主密钥“Master Secret”，而主密钥每次连接都要重新计算，未免有点太浪费了。难道每次连接的主密钥是一样的？不是每次连接的ecdhe的公钥私钥都是不同的吗？怎么还可以缓存呢？</p>2021-11-23</li><br/><li><span>钱</span> 👍（1） 💬（1）<p>1：你能比较一下“Session ID”“Session Ticket”“PSK”这三种会话复用手段的异同吗？
1-1：回话复用
核心是缓存主密钥，为啥要缓存？因为计算出主密钥比较费劲，如果能重复利用，重复计算的活就免了，这是在拿空间换时间。
1-2：Session ID
可以认为是缓存主密钥的key，在客户端和服务器都有存储，通过传递这个key来获取和重用主密钥。
缺点是太费服务器的村村资源，因为每一个客户端的回话数据都需要保存，如果客户端有百万甚至千万基本，那存储空间使用的就有些多啦！
1-3：Session ticket
这个方案可以解决服务器存储空间压力山大的问题，核心是把信息放在客户端存储，当然是加密后的信息，服务器侧需要解码后再使用。
1-44：PSK
和Session ticket类似，为了效率加大了一些安全风险，ticket中带上了应用数据的信息，这样能省去服务器的确认步骤。为了加强安全性，使用上做了一些限制。
有此可见，没有完美的解决方案，具体想要什么需要自己权衡对待。想要实现多快好省，那要么是一句口号，要么必须付出其他的代价。

2：你觉得哪些优化手段是你在实际工作中能用到的？应该怎样去用？
软件优化这个估计最常用，也能用到，一些安全漏洞或性能优化常这么玩。</p>2020-04-04</li><br/><li><span>书生依旧</span> 👍（1） 💬（1）<p>PSK 在发送 Ticket 的同时会带上应用数据，免去了 1.2 里面的服务器确认步骤。
这句话有点不太理解，请问老师：
1. 看图上 pre_shared_key 是在 Hello 中发送的，Session Ticket 也是在 Hello 中发送的吗？
2. 带上应用数据是什么数据?
3. 1.2 里面的服务器验证指的是哪个步骤？</p>2019-10-16</li><br/><li><span>Snooker</span> 👍（0） 💬（1）<p>关于证书优化“OCSP Stapling”（OCSP 装订），有个小点，赘述一下：针对服务器返回的OCSP 响应，客户端是会进行相关验证的，大概是验证 ocsp响应数据是否被篡改、响应数据内的一些状态码等</p>2024-05-08</li><br/><li><span>Mingyan</span> 👍（0） 💬（2）<p>老师请问一下，ssl connections什么条件下才会复用的？我遇到从一台机子循环发送A然后B两个请求，A和B是不同域名下的资源。第一个请求是A第二个请求是B第三个请求再发A并不会复用ssl connections而是新开。</p>2023-06-26</li><br/><li><span>Geek_11246e</span> 👍（0） 💬（1）<p>请问异步通信可以讲下吗</p>2023-02-28</li><br/><li><span>泥鳅儿</span> 👍（0） 💬（2）<p>老师，如果安装的ssl证书过期了，之后进行的http数据传输还是加密的吗</p>2022-10-09</li><br/><li><span>cake</span> 👍（0） 💬（1）<p>老师请问下    非对称加密解密处理“Pre-Master” 这计划的意思就是生成 “Pre-Master” 的意思么</p>2021-11-27</li><br/>
</ul>