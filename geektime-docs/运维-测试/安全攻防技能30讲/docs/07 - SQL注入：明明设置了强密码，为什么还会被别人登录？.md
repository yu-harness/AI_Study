你好，我是何为舟。

在上一讲中，我们介绍了XSS攻击。今天，我们来介绍另外一种常见的Web攻击：SQL注入。

在讲正文之前，让我们先来看一个案例。某天，当你在查看应用的管理后台时，发现有很多异常的操作。接着，你很快反应过来了，这应该是黑客成功登录了管理员账户。于是，你立刻找到管理员，责问他是不是设置了弱密码。管理员很无辜地表示，自己的密码非常复杂，不可能泄露，但是为了安全起见，他还是立即修改了当前的密码。奇怪的是，第二天，黑客还是能够继续登录管理员账号。问题来了，黑客究竟是怎么做到的呢？你觉得这里面的问题究竟出在哪里呢？你可以先自己思考一下，然后跟着我开始今天的学习！

## SQL注入攻击是如何产生的？

在上一讲中，我们讲了，XSS是黑客通过篡改HTML代码，来插入并执行恶意脚本的一种攻击。其实，SQL注入和XSS攻击很类似，都是黑客通过篡改代码逻辑发起的攻击。那么，不同的点是什么？SQL注入到底是什么呢？

通常来说，我们会将应用的用户信息存储在数据库中。每次用户登录时，都会执行一个相应的SQL语句。这时，黑客会通过构造一些恶意的输入参数，在应用拼接SQL语句的时候，去篡改正常的SQL语意，从而执行黑客所控制的SQL查询功能。这个过程，就相当于黑客“注入”了一段SQL代码到应用中。这就是我们常说的**SQL注入**。

这么说可能还是有点理论，不够具体。接下来，我就以几个简单而又经典的示例，来给你介绍两种主要的SQL注入方式。

### 1.修改WHERE语句

我们先来看一个例子。现在有一个简单的登录页面，需要用户输入Username和Password这两个变量来完成登录。具体的Web后台代码如下所示：

```
uName = getRequestString("username");
uPass = getRequestString("password");

sql = 'SELECT * FROM Users WHERE Username ="' + uName + '" AND Password ="' + uPass + '"'
```

当用户提交一个表单（假设Username为admin，Password为123456）时，Web将执行下面这行代码：

```
SELECT * FROM Users WHERE Username ="admin" AND Password ="123456"
```

用户名密码如果正确的话，这句SQL就能够返回对应的用户信息；如果错误的话，不会返回任何信息。因此，只要返回的行数≥1，就说明验证通过，用户可以成功登录。

所以，当用户正常地输入自己的用户名和密码时，自然就可以成功登录应用。那黑客想要在不知道密码的情况下登录应用，他又会输入什么呢？他会输入 **`" or ""="`** 。这时，应用的数据库就会执行下面这行代码：

```
SELECT * FROM Users WHERE Username ="" AND Password ="" or ""=""
```

我们可以看到，WHERE语句后面的判断是通过or进行拼接的，其中""=""的结果是true。那么，当有一个or是true的时候，最终结果就一定是true了。因此，这个WHERE语句是恒为真的，所以，数据库将返回全部的数据。

这样一来，我们就能解答文章开头的问题了，也就是说，黑客只需要在登录页面中输入 **`" or ""="`** ，就可以在不知道密码的情况下，成功登录后台了。而这，也就是所谓的“万能密码”。而这个“万能密码”，其实就是通过修改WHERE语句，改变数据库的返回结果，实现无密码登录。

### 2.执行任意语句

除此之外，大部分的数据库都支持多语句执行。因此，黑客除了修改原本的WHERE语句之外，也可以在原语句的后面，插入额外的SQL语句，来实现任意的增删改查操作。在实际工作中，MySQL是最常用的数据库，我们就以它为例，来介绍一下，任意语句是如何执行的。

在MySQL中，实现任意语句执行最简单的方法，就是利用分号将原本的SQL语句进行分割。这样，我们就可以一次执行多个语句了。比如，下面这个语句在执行的时候会先插入一个行，然后再返回Users表中全部的数据。

```
INSERT INTO Users (Username, Password) VALUES("test","000000"); SELECT * FROM Users;
```

接下来，我们来看一个具体的例子。在用户完成登录后，应用通常会通过userId来获取对应的用户信息。其Web后台的代码如下所示：

```
uid = getRequestString("userId");
sql = "SELECT * FROM Users WHERE UserId = " + uid;
```

在这种情况下，黑客只要在传入的userId参数中加入一个分号，就可以执行任意的SQL语句了。比如，黑客想“删库跑路”的话，就令userId为 **`1;DROP TABLE Users`** ，那么，后台实际执行的SQL就会变成下面这行代码，而数据库中所有的用户信息就都会被删除。

```
SELECT * FROM Users WHERE UserId = 1；DROP TABLE Users
```

SQL注入的“姿势”还有很多（比如：[没有回显的盲注](https://www.freebuf.com/articles/web/175049.html)、[基于INSERT语句的注入](https://www.jianshu.com/p/1f82582452df?utm_campaign)等等），它们的原理都是一样的，都是通过更改SQL的语义来执行黑客设定的SQL语句。如果你有兴趣，可以通过我前面给出的链接去进一步了解。

## 通过SQL注入攻击，黑客能做什么？

通过上面对SQL注入的简单介绍，我们已经知道，SQL注入会令Web后台执行非常规的SQL语句，从而导致各种各样的问题。那么通过SQL注入攻击，黑客究竟能够干些什么呢？下面我们就一一来看。

### 1.绕过验证

在上面的内容中，我们已经介绍过， **`" or ""="`** 作为万能密码，可以让黑客在不知道密码的情况下，通过登录认证。因此，SQL注入最直接的利用方式，就是绕过验证，也就相当于身份认证被破解了。

### 2.任意篡改数据

除了绕过验证，我们在任意语句执行的部分中讲到，SQL注入漏洞导致黑客可以执行任意的SQL语句。因此，通过插入DML类的SQL语句（INSERT、UPDATE、DELETE、TRUNCATE、DROP等），黑客就可以对表数据甚至表结构进行更改，这样数据的完整性就会受到损害。比如上面例子中，黑客通过插入DROP TABLE Users，删除数据库中全部的用户。

### 3.窃取数据

在XSS漏洞中，黑客可以通过窃取Cookie和“钓鱼”获得用户的隐私数据。那么，在SQL注入中，黑客会怎么来获取这些隐私数据呢？

在各类安全事件中，我们经常听到“拖库”这个词。所谓“拖库”，就是指黑客通过类似SQL注入的手段，获取到数据库中的全部数据（如用户名、密码、手机号等隐私数据）。最简单的，黑客利用UNION关键词，将SQL语句拼接成下面这行代码之后，就可以直接获取全部的用户信息了。

```
SELECT * FROM Users WHERE UserId = 1 UNION SELECT * FROM Users
```

### 4.消耗资源

通过[第1讲](https://time.geekbang.org/column/article/176567)对CIA三元组的学习，我们知道，除了获取数据之外，影响服务可用性也是黑客的目标之一。

SQL注入破坏可用性十分简单，可以通过完全消耗服务器的资源来实现。比如，在Web后台中，黑客可以利用WHILE打造死循环操作，或者定义存储过程，触发一个无限迭代等等。在这些情况下，数据库服务器因为CPU被迅速打满，持续100%，而无法及时响应其他请求。

总结来说，通过SQL注入攻击，黑客可以绕过验证登录后台，非法篡改数据库中的数据；还能执行任意的SQL语句，盗取用户的隐私数据影响公司业务等等。所以，我认为，SQL注入相当于让黑客直接和服务端的数据库进行了交互。正如我们一直所说的，应用的本质是数据，黑客控制了数据库，也就相当于控制了整个应用。

## 如何进行SQL注入防护 ？

在认识到SQL注入的危害之后，我们知道，一个简单的SQL查询逻辑，能够带来巨大的安全隐患。因此，我们应该做到在开发过程中就避免出现SQL注入漏洞。那具体应该怎么做呢？接下来，我会为你介绍3种常见的防护方法，它们分别是：使用PreparedStatement、使用存储过程和验证输入。接下来，我们一一来看。

### 1.使用PreparedStatement

通过**合理地**使用PreparedStatement，我们就能够避免99.99%的SQL注入问题。你肯定很好奇，我为什么会这么说。接下来，让我们一起看一下它的实现过程。

当数据库在处理一个SQL命令的时候，大致可以分为两个步骤：

- 将SQL语句解析成数据库可使用的指令集。我们在使用EXPLAIN关键字分析SQL语句，就是干的这个事情；
- 将变量代入指令集，开始实际执行。之所以在批量处理SQL的时候能够提升性能，就是因为这样做避免了重复解析SQL的过程。

那么PreparedStatement为什么能够避免SQL注入的问题呢？

这是因为，SQL注入是在解析的过程中生效的，用户的输入会影响SQL解析的结果。因此，我们可以通过使用PreparedStatement，将SQL语句的解析和实际执行过程分开，只在执行的过程中代入用户的操作。这样一来，无论黑客提交的参数怎么变化，数据库都不会去执行额外的逻辑，也就避免了SQL注入的发生。

在Java中，我们可以通过执行下面的代码将解析和执行分开：

```
String sql = "SELECT * FROM Users WHERE UserId = ?";
PreparedStatement statement = connection.prepareStatement(sql);
statement.setInt(1, userId); 
ResultSet results = statement.executeQuery();

```

为了实现相似的效果，在PHP中，我们可以使用PDO（PHP Data Objects）；在C#中，我们可以使用OleDbCommand等等。

这里有一点需要你注意，前面我们说了，通过合理地使用PreparedStatement就能解决99.99%的SQL注入问题，那到底怎么做才算“合理地”使用呢？

PreparedStatement为SQL语句的解析和执行提供了不同的“方法”，你需要分开来调用。但是，如果你在使用PreparedStatement的时候，还是通过字符串拼接来构造SQL语句，那仍然是将解析和执行放在了一块，也就不会产生相应的防护效果了。我这里给你展示了一个错误案例，你可以和上面的代码进行对比。

```
String sql = "SELECT * FROM Users WHERE UserId = " + userId;
PreparedStatement statement = connection.prepareStatement(sql);
ResultSet results = statement.executeQuery();
```

### 2.使用存储过程

接下来，我们说一说，如何使用[存储过程](https://baike.baidu.com/item/%E5%AD%98%E5%82%A8%E8%BF%87%E7%A8%8B/1240317?fr=aladdin)来防止SQL注入。实际上，它的原理和使用PreparedStatement类似，都是通过将SQL语句的解析和执行过程分开，来实现防护。区别在于，存储过程防注入是将解析SQL的过程，由数据库驱动转移到了数据库本身。

还是上述的例子，使用存储过程，我们可以这样来实现：

```
delimiter $$　　#将语句的结束符号从分号;临时改为两个$$(可以是自定义)
CREATE PROCEDURE select_user(IN p_id INTEGER)
BEGIN
　 SELECT * FROM Users WHERE UserId = p_id;
END$$ 
delimiter;　　#将语句的结束符号恢复为分号

call select_user(1);
```

### 3.验证输入

在上一节课中，我们讲过，**防护的核心原则是，一切用户输入皆不可信**。因此，SQL注入的防护手段和XSS其实也是相通的，主要的不同在于：

- SQL注入的攻击发生在输入的时候，因此，我们只能在输入的时候去进行防护和验证；
- 大部分数据库不提供针对SQL的编码，因为那会改变原有的语意，所以SQL注入没有编码的保护方案。

因此，对所有输入进行验证或者过滤操作，能够很大程度上避免SQL注入的出现。比如，在通过userId获取Users相关信息的示例中，我们可以确认userId必然是一个整数。因此，我们只需要对userId参数，进行一个整型转化（比如，Java中的Integer.parseInt，PHP的intval），就可以实现防护了。

当然，部分场景下，用户输入的参数会比较复杂。我们以用户发出的评论为例，其内容完全由用户定义，应用无法预判它的格式。这种情况下，应用只能通过对部分关键字符进行过滤，来避免SQL注入的发生。比如，在MySQL中，需要注意的关键词有" % ’ \\ \_。

这里我简单地总结一下，在实际使用这些防护方法时的注意点。对于验证输入来说，尤其是在复杂场景下的验证输入措施，其防护效果是最弱的。因此，避免SQL注入的防护方法，首要选择仍然是PreparedStatement或者存储过程。

## 总结

好了，这一节内容差不多了，下面我来带你总结回顾一下，你要掌握的重点内容。

SQL注入就是黑客通过相关漏洞，篡改SQL语句的攻击。通过SQL注入，黑客既可以影响正常的SQL执行结果，从而绕过验证，也可以执行额外的SQL语句，对数据的机密性、完整性和可用性都产生影响。

为了避免SQL注入的出现，我们需要正确地使用PreparedStatement方法或者存储过程，尽量避免在SQL语句中出现字符串拼接的操作。除此之外，SQL注入的防护也可以和XSS一样，对用户的输入进行验证、检测并过滤SQL中的关键词，从而避免原有语句被篡改。

今天的内容比较多，为了方便你记忆，我总结了一个知识脑图，你可以通过它来对今天的重点内容进行复习巩固。  
![](https://static001.geekbang.org/resource/image/1b/36/1b898391a3a04a764d0442d8481c4236.jpg?wh=1142%2A802)

## 思考题

好了，今天的内容差不多了，我们来看一道思考题。

假设有下面这样一个语句：

```
SELECT Username FROM Users WHERE UserId = 1
```

你现在已经知道，WHERE语句中存在了SQL注入的点。那么，我们怎么才能获取到除了Username之外的其他字段呢？这里我给你一个小提示，你可以先了解一下“[盲注](https://www.freebuf.com/articles/web/175049.html)”这个概念，之后再来思考这个问题。

欢迎留言和我分享你的思考和疑惑，也欢迎你把文章分享给你的朋友。我们下一讲再见！
<div><strong>精选留言（15）</strong></div><ul>
<li><span>豆豆</span> 👍（48） 💬（1）<p>之前只是知道些简单的 SQL 注入方式以及防范措施，今天文末的盲注确实涨了知识，关于思考题自己做了如下的练习。

首先盲注应该也是通过 web 端的输入来实现黑客的入侵目的的，那么黑客就可以通过观察页面的反应来动态修改自己的注入参数。比如一些提交输入框，当我们提交了参数之后页面反应正常那么就说明我们的猜测是正确的，否则继续猜。

我们都知道 MySQL 内部有一个 information_schema 的库，里面都是数据裤的元信息，那么我们就可以利用这个库进行猜测，通过观察页面的反应来验证自己的猜测是否正确。

第一步我们要知道数据的名字，那么就先猜测其长度。以下我们会用到 DATABASE(), LENGTH(), SUBSTRING(), ASCII() 四个内置函数。

1. 确定数据库长度

SELECT name FROM user WHERE id = 1 AND (SELECT LENGTH(DATABASE()) = 4);

得到数据库长度之后猜测数据库名字的每个字母。

2. 确定数据库名字 通过 ASCII 码方式

SELECT name FROM user WHERE id = 1 AND (SELECT ASCII(SUBSTRING(DATABASE(), 1, 1)) &lt; 128); 

根据 ASCII 码猜测是可以使用二分法来猜测。假设的到的结果是 test。

得到数据库名字之后，猜测 user 表有多少个列。

3. 获取该表有多少列

SELECT name FROM user WHERE id = 1 AND ((SELECT COUNT(*) FROM information_schema.COLUMNS WHERE table_name = &#39;user&#39; AND TABLE_SCHEMA = &#39;test&#39;) = 3);

获取到列的多少列之后，就可以获取到每一列的长度了。

4. 获取列长
SELECT name FROM user WHERE id = 1  AND ((SELECT LENGTH(column_name) FROM information_schema.COLUMNS WHERE table_name = &#39;user&#39; AND TABLE_SCHEMA = &#39;test&#39; LIMIT 0, 1) = 2);


最后，获取每一列的具体值。

5. 获取列名，同样是使用 ASCII 码方式
SELECT name FROM user WHERE id = 1  AND ((SELECT ASCII(SUBSTRING(column_name, 1, 1)) FROM information_schema.COLUMNS WHERE table_name = &#39;user&#39; AND TABLE_SCHEMA = &#39;test&#39; LIMIT 0, 1) &lt; 120)

为了故事的顺利发展这里我假设我们已知表名 user，但是我们可以根据同样的逻辑从 information_schema.TABLES 表中获取 test 库的所有表信息。

最后，我感觉这个方式有点傻啊，因为它依赖一些很特定的条件，比如后端没有做 SQL 注入的防护，而且还必须结合前端页面的反应。</p>2019-12-23</li><br/><li><span>小晏子</span> 👍（8） 💬（1）<p>研究了下盲注的文章，长见识了，以前只是大概知道sql注入，知道最简单的方式，盲注这种方法还是第一次接触，针对这个思考题，可以按如下方式获取其他字段，思路如下，可以写脚本实现，还有前提是能够进行盲注，
1. 先判断字段的第一个字符是否在a-z中，如下所示，

select Username from Users where UserId = 1 and 1 = (select 1 from information_schema.columns WHERE table_name=&#39;Users’ and COLUMN_NAME REGEXP &#39;^[a-z]&#39;)
如果结果显示Username那就说明字段的第一个字符在a到z中，

2. 使用二分查找法在a到z之间查找第一个字符，如下语句，

select Username from Users where UserId = 1 and 1 = (select 1 from information_schema.columns WHERE table_name=&#39;Users’ and COLUMN_NAME REGEXP &#39;^a[a-z]&#39;)

如果能显示Username，那么就说明a是第一个字符，再依次去查第二个字符，反之，换一个字符再试。

3. 以此类推，可以找到所有的字段名。

顺便说下，字段名中可能包含其他字符，如 _ 等，可以在正则表达式中同样去匹配。

</p>2019-12-23</li><br/><li><span>小老鼠</span> 👍（2） 💬（2）<p>现在SQL注入不常见了吧，现在的开发框架都可避免SQL注入了吧。比如基于python的Django。</p>2019-12-31</li><br/><li><span>sober</span> 👍（2） 💬（1）<p>希望老师能抽出一节讲讲登录实战，想真正了解一下整个登录如何应用加密，谢谢老师了</p>2019-12-24</li><br/><li><span>Gamer777</span> 👍（0） 💬（1）<p>通过使用 PreparedStatement，将 SQL 语句的解析和实际执行过程分开，只在执行的过程中代入用户的操作。分开执行还是无法防御SQL注入吗，不然为什么底层还是会对一些特殊符号进行转义操作？</p>2020-07-18</li><br/><li><span>HE明伟</span> 👍（0） 💬（1）<p>老师，现在的spring boot这些框架都能预防sql注入了吧</p>2020-07-09</li><br/><li><span>felix</span> 👍（0） 💬（1）<p>如果是string,还是解决不了第一个password或的情况?</p>2020-01-13</li><br/><li><span>律飛</span> 👍（0） 💬（1）<p>作为编程小白而言，学习难度有点大哦🙄。多看了好几篇盲注的文章，仍然是晕头转向的。豆豆已经提供了很好的答案。不过我还是来说说我的理解，不足之处请老师批评指正。

盲注其实就是结合SQL最基本的两种注入方式，不断去猜测并验证数据库可能的信息，最终获得答案的过程。这需要注入者简单的基础和丰富的经验，以及长时间频繁地跟数据库交互。

对于这种攻击，开发者采用PreparedStatment,存储过程，验证输入等方法就可以防范攻击。

请教老师：对于输入内容验证是不是还可以通过长度进行控制？对于盲注是不是可以通过单位时间内某个id跟数据库连接次数进行限制和预警？如果想动手试验，如何避免触碰红线？</p>2020-01-02</li><br/><li><span>小老鼠</span> 👍（0） 💬（1）<p>可介绍下sqlmap吗？</p>2019-12-31</li><br/><li><span>Zhen</span> 👍（0） 💬（1）<p>了解了一下盲注，比较有意思，根据你SQL注入的攻击语句返回TRUE或者FALSE，可被用来一点点猜测获取数据库schema。 比如：如果 http:&#47;&#47;newspaper.com&#47;items.php?id=2 and 1=2   返回FALSE；http:&#47;&#47;newspaper.com&#47;items.php?id=2 and 1=1 返回正确，就说明后面输入的语句被服务器执行了   而且存在一个数字型的注入；那我们现在就可以开始盲注，判断它目前使用的数据库、版本、一点点猜测数据库内容。

另外有个很初级的问题想请教一下，SQL注入是不是所有SQL数据库固有的问题？为什么数据库本身不能自我完善做到输入参数的过滤和保护，而是要Java应用程序来通过PreparedStatement来做？</p>2019-12-23</li><br/><li><span>Cy23</span> 👍（0） 💬（2）<p>注册的时候看input的name都有什么，基本上就了解个大概有什么字段，然后尝试猜常用的字段，
或者查询显示的语句里注入查询表中所有字段名，然后替换字段名到显示输出的地方查看，
突然想起原来有个资源下载的网站，原来是免费的，后来收费了，有天无意将页面上下载所需要的分值改为负数，结果下载--为正给我加分了，然后尝试修改分值大小，结果我给自己充满了，我把这个漏洞告诉给站长，站长为了表示感谢奖励我1000分，然后我发现，我那999999999变成了1000。</p>2019-12-23</li><br/><li><span>rocedu</span> 👍（0） 💬（1）<p>要是有个课题程配套虚拟机就更好了</p>2019-12-23</li><br/><li><span>ban</span> 👍（0） 💬（1）<p>现在应该很多大部分开发都使用 PreparedStatement 了吧</p>2019-12-23</li><br/><li><span>亚林</span> 👍（1） 💬（0）<p>OWASP的 Enterprise Security API Java库好像可以搞定这些问题</p>2021-06-22</li><br/><li><span>陈启航</span> 👍（0） 💬（0）<p>使用ORM操作数据库是不是也可以避免很大一部分sql注入呢?</p>2021-02-21</li><br/>
</ul>