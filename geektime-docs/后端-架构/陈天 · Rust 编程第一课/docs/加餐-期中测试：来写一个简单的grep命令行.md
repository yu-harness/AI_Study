你好，我是陈天。

现在 Rust 基础篇已经学完了，相信你已经有足够的信心去应对一些简单的开发任务。今天我们就来个期中测试，实际考察一下你对 Rust 语言的理解以及对所学知识的应用情况。

我们要做的小工具是 rgrep，它是一个类似 grep 的工具。如果你是一个 \*nix 用户，那大概率使用过 grep 或者 ag 这样的文本查找工具。

grep 命令用于查找文件里符合条件的字符串。如果发现某个文件的内容符合所指定的字符串，grep 命令会把含有字符串的那一行显示出；若不指定任何文件名称，或是所给予的文件名为 **-**，grep 命令会从标准输入设备读取数据。

我们的 rgrep 要稍微简单一些，它可以支持以下三种使用场景：

首先是最简单的，给定一个字符串以及一个文件，打印出文件中所有包含该字符串的行：

```plain
$ rgrep Hello a.txt
55: Hello world. This is an exmaple text
```

然后放宽限制，允许用户提供一个正则表达式，来查找文件中所有包含该字符串的行：

```plain
$ rgrep Hel[^\\s]+ a.txt
55: Hello world. This is an exmaple text
89: Help me! I need assistant!
```

如果这个也可以实现，那进一步放宽限制，允许用户提供一个正则表达式，来查找满足文件通配符的所有文件（你可以使用 [globset](https://docs.rs/globset/0.4.8/globset/) 或者 [glob](https://docs.rs/glob/0.3.0/glob/) 来处理通配符），比如：

```plain
$ rgrep Hel[^\\s]+ a*.txt
a.txt 
    55:1 Hello world. This is an exmaple text
    89:1 Help me! I need assistant!
    5:6  Use `Help` to get help.
abc.txt:
    100:1 Hello Tyr!
```

其中，冒号前面的数字是行号，后面的数字是字符在这一行的位置。

给你一点小提示。

- 对于命令行的部分，你可以使用 [clap3](https://docs.rs/clap/3.0.0-beta.4/clap/index.html) 或者 [structopt](https://docs.rs/structopt/0.3.23/structopt/)，也可以就用 env.args()。
- 对于正则表达式的支持，可以使用 [regex](https://github.com/rust-lang/regex)。
- 至于文件的读取，可以使用 [std::fs](https://doc.rust-lang.org/std/fs/index.html) 或者 [tokio::fs](https://docs.rs/tokio/1.12.0/tokio/fs/index.html)。你可以顺序对所有满足通配符的文件进行处理，也可以用 [rayon](https://docs.rs/rayon/1.5.1/rayon/) 或者 [tokio](https://docs.rs/tokio/1.12.0/tokio/) 来并行处理。
- 对于输出的结果，最好能把匹配的文字用不同颜色展示。

![](https://static001.geekbang.org/resource/image/95/1f/95d87be96953d3655daf9c3yy8b6bf1f.png?wh=2356x1318 "例如这样的输出")

如果你有余力，可以看看 grep 的文档，尝试实现更多的功能。

祝你好运！

加油，我们下节课作业讲解见。
<div><strong>精选留言（11）</strong></div><ul>
<li><span>Quincy</span> 👍（3） 💬（1）<p>
1. 最简单的
```rust
use std::error::Error;

use clap::{AppSettings, Clap};
use colored::Colorize;
use tokio::fs;

#[derive(Clap)]
#[clap(version = &quot;1.0&quot;, author = &quot;Custer&lt;custer@email.cn&gt;&quot;)]
#[clap(setting = AppSettings::ColoredHelp)]
struct Opts {
    find: String,
    path: String,
}

#[tokio::main]
async fn main() -&gt; Result&lt;(), Box&lt;dyn Error&gt;&gt; {
    &#47;&#47; 1. 解析参数
    let opts: Opts = Opts::parse();
    let find = opts.find;
    let path = opts.path;
    let length = find.len();

    &#47;&#47; 2. 读取文件
    let contents = fs::read_to_string(path).await?;

    &#47;&#47; 3. 匹配字符串
    for (row, line) in contents.lines().enumerate() {
        if let Some(col) = line.find(&amp;find) {
            println!(
                &quot;{}:{} {}{}{}&quot;,
                row + 1,
                col + 1,
                &amp;line[..col],
                &amp;line[col..col + length].red().bold(),
                &amp;line[col + length..]
            );
        }
    }
    Ok(())
}
```
2. 允许用户提供一个正则表达式，来查找文件中所有包含该字符串的行
```rust
    &#47;&#47; 3. 匹配字符串
    for (row, line) in contents.lines().enumerate() {
        if let Some(re) = Regex::new(find.as_str()).unwrap().find(line) {
            let start = re.start();
            let end = re.end();
            println!(
                &quot;{}:{} {}{}{}&quot;,
                row + 1,
                start + 1,
                &amp;line[..start],
                &amp;line[start..end].red().bold(),
                &amp;line[end..]
            );
        }
    }
```
3. 允许用户提供一个正则表达式，来查找满足文件通配符的所有文件(好像并不需要使用globset 或者 glob 就可以处理通配符？）

```rust
...
struct Opts {
    find: String,
    #[clap(multiple_values = true)]
    paths: Vec&lt;String&gt;,
}

#[tokio::main]
async fn main() -&gt; Result&lt;(), Box&lt;dyn Error&gt;&gt; {
    &#47;&#47; 1. 解析参数
    let opts: Opts = Opts::parse();
    let find = opts.find.as_str();
    let paths = opts.paths;

    &#47;&#47; 2. 循环读取匹配到的文件
    for path in paths {
        println!(&quot;{:?}&quot;, path);
        let contents = fs::read_to_string(path).await?;

        &#47;&#47; 3. 匹配字符串
        ...
    }
    Ok(())
}
```</p>2021-10-15</li><br/><li><span>余泽锋</span> 👍（2） 💬（1）<p>时间比较紧，先写个初始版本：

extern crate clap;

use std::path::Path;
use std::ffi::OsStr;
use std::error::Error;

use clap::{Arg, App};
use regex::Regex;
use tokio::fs::{File, read_dir};
use tokio::io::AsyncReadExt;



#[tokio::main]
async fn main() -&gt; Result&lt;(), Box&lt;dyn Error&gt;&gt; {

    let matches = App::new(&quot;rgrep&quot;)
                        .version(&quot;1.0&quot;)
                        .about(&quot;Does awesome things&quot;)
                        .arg(Arg::with_name(&quot;key_word&quot;)
                                .index(1))
                        .arg(Arg::with_name(&quot;file&quot;)
                                .multiple(true)
                                .index(2))
                        .get_matches();
    println!(&quot;{:?}&quot;, matches);
    let key_word = matches.value_of(&quot;key_word&quot;).unwrap();
    println!(&quot;{}&quot;, key_word);
    let file_path = matches.values_of_lossy(&quot;file&quot;).unwrap();
    println!(&quot;{:?}&quot;, file_path);

    let re_key_word = format!(r&quot;{}&quot;, &amp;key_word);
    println!(&quot;re_key_word: {}&quot;, &amp;re_key_word);
    let re = Regex::new(&amp;re_key_word).unwrap();

    for file_path in file_path {
        
        let mut file = File::open(&amp;file_path).await?;
        &#47;&#47; let mut contents = vec![];
        let result = tokio::fs::read_to_string(&amp;file_path).await?;

        if let Some(caps) = re.captures(&amp;result) {
            println!(&quot;file_path: {:?}&quot;, &amp;file_path);
            println!(&quot;file: {:?}&quot;, &amp;file);
            println!(&quot;caps: {:?}&quot;, &amp;caps);
            println!(&quot;result: {:?}&quot;, &amp;result);
        }
    }

    Ok(())
}
</p>2021-10-17</li><br/><li><span>夏洛克Moriaty</span> 👍（2） 💬（1）<p>磕磕盼盼搞了一天终于实现了这一讲的需求，期中测试算是通过了。自己动手实现的过程中收获了非常多的东西。代码结构前前后后改了许多次，还达不到开发过程中接口不变只是实现变的能力。我把代码仓库链接贴在下面算是献丑了，说实话有点不好意思拿出来哈哈。

https:&#47;&#47;github.com&#47;LgnMs&#47;rgrep</p>2021-10-14</li><br/><li><span>D. D</span> 👍（1） 💬（1）<p>试着写了一下，实现得比较匆忙。
为了练习之前学过的内容，试了各种写法，应该会有很多不合理的地方。
而且没有做并行化，希望以后有时间可以加上，并把代码重构得更好。
https:&#47;&#47;github.com&#47;imag1ne&#47;grepr</p>2021-10-15</li><br/><li><span>记事本</span> 👍（1） 💬（1）<p> let filename = std::env::args().nth(2).unwrap();
    let query = std::env::args().nth(1).unwrap();
    let case_sensitive = std::env::var(&quot;is_sens&quot;).is_err();

    let contents = std::fs::read_to_string(filename).unwrap();

    if case_sensitive {
        let mut i = 1;
        for v in contents.lines(){
            if v.contains(&amp;query){
                println!(&quot;{}:{}&quot;,i,v);
            }
            i+=1;
        }
    }else {
        let c =contents.lines().filter(|item|item.contains(&amp;query)).collect::&lt;Vec&lt;_&gt;&gt;();
        for i in 1..=c.len(){
            println!(&quot;{}:{}&quot;,i,c[i]);
        }
    }
</p>2021-10-13</li><br/><li><span>目标</span> 👍（0） 💬（0）<p>pub fn search_in(k: &amp;str, file_path: &amp;str) -&gt; Result&lt;Vec&lt;Match&gt;, Error&gt; {
    let mut result = Vec::new();
    let file = std::fs::File::open(file_path)?;
    let reader = std::io::BufReader::new(file);
    for (no, line) in reader.lines().enumerate() {
        let line = line?;
        &#47;&#47; consider k as a regular expression
        let r = Regex::new(k)?;

        if let Some(mat) = r.find(&amp;line) {
            let start = mat.start();
            let colored_line =
                r.replace_all(&amp;line, |caps: &amp;Captures| format!(&quot;{}&quot;, &amp;caps[0].blue()));
            result.push(Match {
                line: colored_line.to_string(),
                line_number: no + 1,
                start,
            });
        }
    }
    Ok(result)
}</p>2024-04-08</li><br/><li><span>支离益</span> 👍（0） 💬（0）<p>我碰到一个问题，loop中的print！:
loop {
        print!(&quot;&gt; &quot;);

        let mut line = String::new();
        io::stdin().read_line(&amp;mut line)
            .expect(&quot;Failed to read line&quot;);

        println!(&quot;{}&quot;, line);
    }

为什么实际执行中，&gt;不会第一时间显示，会显示在回车之后回显的第一个字符，输入行是空白，回显的时候是&gt;+刚刚输入的字符

用println！就能正常第一行显示&gt;，然后输入，回显</p>2023-10-29</li><br/><li><span>鞠文桦</span> 👍（0） 💬（0）<p>
error: The following required arguments were not provided:
    &lt;PATTERN&gt;
    &lt;GLOB&gt;

USAGE:
    rgrep.exe &lt;PATTERN&gt; &lt;GLOB&gt;

For more information try --help
error: process didn&#39;t exit successfully: `E:\geektime-Rust-master\geektime-rust-master\target\debug\rgrep.exe` (exit code: 2)

Process finished with exit code 2
求助。。。不知道为什么总输出这个</p>2022-06-09</li><br/><li><span>鞠文桦</span> 👍（0） 💬（0）<p>error: The following required arguments were not provided:
    &lt;PATTERN&gt;
    &lt;GLOB&gt;

USAGE:
    rgrep.exe &lt;PATTERN&gt; &lt;GLOB&gt;

For more information try --help
error: process didn&#39;t exit successfully: `E:\geektime-Rust-master\geektime-rust-master\target\debug\rgrep.exe` (exit code: 2)求助</p>2022-06-08</li><br/><li><span>gt</span> 👍（0） 💬（0）<p>交个作业：https:&#47;&#47;github.com&#47;ForInfinity&#47;rgrep
把整个程序分成了fs、pattern、formatter三个部分，分别负责文件读写、匹配和高亮及输出console。先分别敲定了trait，然后实现。以后可以扩展使用不同的fs来源、更多的匹配模式、不同的formatter。
不过在编写泛型的时候遇到了个问题：
首先存在一个trait MatchOutput:
```
pub trait MatchOutput&lt;T&gt;
    where T: Display
```
当我想实现另一个trait Printer时：
``
pub struct Printer&lt;M: Display, T: MatchOutput&lt;M&gt;&gt;
{
    pub formatter: T,
}
```
rust会编译不通过，提示存在未使用的泛型M：
```
error[E0392]: parameter `M` is never used
```
对此不太理解，也不知道是不是因为这不是最佳实践。
现在临时的解决方案是添加一个私有的变量_m:M，并在写new方法的时候将其初始化为None：
```
pub struct Printer&lt;M: Display, T: MatchOutput&lt;M&gt;&gt;
{
    &#47;&#47; To pass the compiler
    &#47;&#47; Otherwise: error[E0392]: parameter `M` is never used
    _m: Option&lt;M&gt;,
    pub formatter: T,
}
```
蹲个老师的解答。</p>2022-03-19</li><br/><li><span>Geek_994f3b</span> 👍（0） 💬（0）<p>也写了个：https:&#47;&#47;github.com&#47;startdusk&#47;rgrep，欢迎老师指正</p>2022-03-08</li><br/>
</ul>