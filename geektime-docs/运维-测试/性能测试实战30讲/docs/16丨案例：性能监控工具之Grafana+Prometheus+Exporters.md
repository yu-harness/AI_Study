在本模块中，我将把几个常用的监控部分给梳理一下。前面我们提到过，在性能监控图谱中，有操作系统、应用服务器、中间件、队列、缓存、数据库、网络、前端、负载均衡、Web服务器、存储、代码等很多需要监控的点。

显然这些监控点不能在一个专栏中全部覆盖并一一细化，我只能找最常用的几个，做些逻辑思路的说明，同时也把具体的实现描述出来。如果你遇到了其他的组件，也需要一一实现这些监控。

在本篇中，主要想说明白下图的这个监控逻辑。

![](https://static001.geekbang.org/resource/image/e0/39/e0aa269a7f528f393b859cc8ed69ac39.jpg?wh=1894%2A1022)

这应该是现在最流行的一套监控逻辑了吧。

我今天把常见的使用Grafana、Prometheus、InfluxDB、Exporters的数据展示方式说一下，如果你刚进入性能测试领域，也能有一个感性的认识。

有测试工具，有监控工具，才能做后续的性能分析和瓶颈定位，所以有必要把这些工具的逻辑跟你摆一摆。

所有做性能的人都应该知道一点，不管数据以什么样的形式展示，最要紧的还是看数据的来源和含义，以便做出正确的判断。

我先说明一下JMeter和node\_exporter到Grafana的数据展示逻辑。至于其他的Exporter，我就不再解释这个逻辑了，只说监控分析的部分。

## JMeter+InfluxDB+Grafana的数据展示逻辑

一般情况下，我们用JMeter做压力测试时，都是使用JMeter的控制台来查看结果。如下图所示：

![](https://static001.geekbang.org/resource/image/60/75/60469fd6df4eff032fe0ce161963f675.png?wh=1189%2A397)

或者装个插件来看结果：

![](https://static001.geekbang.org/resource/image/bd/32/bdcaa07b1ce26ffe504a7fde931b1d32.png?wh=1202%2A512)

或者用JMeter来生成HTML：

![](https://static001.geekbang.org/resource/image/98/f2/98d050b5df8554a7109e3e532e0781f2.png?wh=1001%2A555)

这样看都没有问题，我们在前面也强调过，对于压力工具来说，我们最多只关心三条曲线的数据：TPS（T由测试目标定义）、响应时间、错误率。这里的错误率还只是辅助排查问题的曲线，没有问题时，只看TPS和响应时间即可。

不过采取以上三种方式有几个方面的问题。

1. 整理结果时比较浪费时间。
2. 在GUI用插件看曲线，做高并发时并不现实。
3. 在场景运行时间比较长的时候，采用生成HTML的方式，会出现消耗内存过大的情况，而实际上，在生成的结果图中，有很多生成的图我们并不是那么关注。
4. 生成的结果保存之后再查看比较麻烦，还要一个个去找。

那么如何解决这几个问题呢？

用JMeter的Backend Listener帮我们实时发送数据到InfluxDB或Graphite可以解决这样的问题。Graphite Backend Listener的支持是在JMeter 2.13版本，InfluxdDB Backend Listener的支持是在JMeter 3.3的版本，它们都是用异步的方式把数据发送出来，以便查看。

其实有这个JMeter发送给InfluxDB的数据之后，我们不需要看上面的那些HTML数据，也可以直观地看到系统性能的性能趋势。并且这样保存下来的数据，在测试结束后想再次查看也比较方便比对。

JMeter+InfluxDB+Grafana的结构如下：

![](https://static001.geekbang.org/resource/image/60/d6/60e7006b3baf95393080b302ccab9fd6.jpg?wh=1814%2A842)

在这个结构中，JMeter发送压力到服务器的同时，统计下TPS、响应时间、线程数、错误率等信息。默认每30秒在控制台输出一次结果（在jmeter.properties中有一个参数#summariser.interval=30可以控制）。配置了Backend Listener之后，将统计出的结果异步发送到InfluxDB中。最后在Grafana中配置InfluxDB数据源和JMeter显示模板。

然后就可以实时查看JMeter的测试结果了，这里看到的数据和控制台的数据是一样。

但如果这么简单就说完了，这篇文章也就没价值了。下面我们来说一下，数据的传输和展示逻辑。

### JMeter中Backend Listener的配置

下面我们就InfluxDB的Backend Listener做个说明。它的配置比较简单，在脚本中加上即可。

![](https://static001.geekbang.org/resource/image/b1/38/b1da92bbdf07f81f80c17a863a1ae238.png?wh=1358%2A345)

我们先配置好influxdb Url、application等信息，application这个配置可以看成是场景名。

那么JMeter如何将数据发给InfluxDB呢？请看源码中的关键代码，如下所示：

```
    private void addMetrics(String transaction, SamplerMetric metric) {
        // FOR ALL STATUS
        addMetric(transaction, metric.getTotal(), metric.getSentBytes(), metric.getReceivedBytes(), TAG_ALL, metric.getAllMean(), metric.getAllMinTime(),
                metric.getAllMaxTime(), allPercentiles.values(), metric::getAllPercentile);
        // FOR OK STATUS
        addMetric(transaction, metric.getSuccesses(), null, null, TAG_OK, metric.getOkMean(), metric.getOkMinTime(),
                metric.getOkMaxTime(), okPercentiles.values(), metric::getOkPercentile);
        // FOR KO STATUS
        addMetric(transaction, metric.getFailures(), null, null, TAG_KO, metric.getKoMean(), metric.getKoMinTime(),
                metric.getKoMaxTime(), koPercentiles.values(), metric::getKoPercentile);
​
​
        metric.getErrors().forEach((error, count) -> addErrorMetric(transaction, error.getResponseCode(),
                    error.getResponseMessage(), count));
    }

```

从这段代码可以看出，站在全局统计的视角来看，这里把JMeter运行的统计结果，比如事务的Total请求、发送接收字节、平均值、最大值、最小值等，都加到metric中，同时也会把成功和失败的事务信息添加到metric中去。

在源码中，还有更多的添加metric的步骤，你有兴趣的话，也可以看一下JMeter源码中的`InfluxdbBackendListenerClient.java`。

保存了metric之后，再使用InfluxdbMetricsSender发送到Influxdb中去。发送关键代码如下：

```
   @Override
    public void writeAndSendMetrics() {
 ........
        if (!copyMetrics.isEmpty()) {
            try {
                if(httpRequest == null) {
                    httpRequest = createRequest(url);
                }
                StringBuilder sb = new StringBuilder(copyMetrics.size()*35);
                for (MetricTuple metric : copyMetrics) {
                    // Add TimeStamp in nanosecond from epoch ( default in InfluxDB )
                    sb.append(metric.measurement)
                        .append(metric.tag)
                        .append(" ") //$NON-NLS-1$
                        .append(metric.field)
                        .append(" ")
                        .append(metric.timestamp+"000000") 
                        .append("\n"); //$NON-NLS-1$
                }


                StringEntity entity = new StringEntity(sb.toString(), StandardCharsets.UTF_8);
                
                httpRequest.setEntity(entity);
                lastRequest = httpClient.execute(httpRequest, new FutureCallback<HttpResponse>() {
                    @Override
                    public void completed(final HttpResponse response) {
                        int code = response.getStatusLine().getStatusCode();
                        /*
                         * HTTP response summary 2xx: If your write request received
                         * HTTP 204 No Content, it was a success! 4xx: InfluxDB
                         * could not understand the request. 5xx: The system is
                         * overloaded or significantly impaired.
                         */
                        if (MetricUtils.isSuccessCode(code)) {
                            if(log.isDebugEnabled()) {
                                log.debug("Success, number of metrics written: {}", copyMetrics.size());
                            } 
                        } else {
                            log.error("Error writing metrics to influxDB Url: {}, responseCode: {}, responseBody: {}", url, code, getBody(response));
                        }
                    }
                    @Override
                    public void failed(final Exception ex) {
                        log.error("failed to send data to influxDB server : {}", ex.getMessage());
                    }
                    @Override
                    public void cancelled() {
                        log.warn("Request to influxDB server was cancelled");
                    }
                });               
 ........
            }
        }
    }
```

通过writeAndSendMetrics，就将所有保存的metrics都发给了InfluxDB。

### InfluxDB中的存储结构

然后我们再来看下InfluxDB中如何存储：

```
> show databases
name: databases
name
----
_internal
jmeter
> use jmeter
Using database jmeter
>
> show MEASUREMENTS
name: measurements
name
----
events
jmeter
> select * from events where application='7ddemo'
name: events
time                application text                title
----                ----------- ----                -----
1575255462806000000 7ddemo      Test Cycle1 started ApacheJMeter
1575256463820000000 7ddemo      Test Cycle1 ended   ApacheJMeter
..............
n> select * from jmeter where application='7ddemo' limit 10
name: jmeter
time                application avg                count countError endedT hit max maxAT meanAT min minAT pct90.0            pct95.0           pct99.0 rb responseCode responseMessage sb startedT statut transaction
----                ----------- ---                ----- ---------- ------ --- --- ----- ------ --- ----- -------            -------           ------- -- ------------ --------------- -- -------- ------ -----------
1575255462821000000 7ddemo                                          0              0     0          0                                                                                     0               internal
1575255467818000000 7ddemo      232.82352941176472 17    0                 17  849              122       384.9999999999996  849               849     0                               0           all    all
1575255467824000000 7ddemo      232.82352941176472 17                          849              122       384.9999999999996  849               849     0                               0           all    0_openIndexPage
1575255467826000000 7ddemo      232.82352941176472 17                          849              122       384.9999999999996  849               849                                                 ok     0_openIndexPage
1575255467829000000 7ddemo                                          0              1     1          1                                                                                     1               internal
1575255472811000000 7ddemo      205.4418604651163  26    0                 26  849              122       252.6              271.4             849     0                               0           all    all
1575255472812000000 7ddemo                                          0              1     1          1                                                                                     1               internal
1575255472812000000 7ddemo      205.4418604651163  26                          849              122       252.6              271.4             849                                                 ok     0_openIndexPage
1575255472812000000 7ddemo      205.4418604651163  26                          849              122       252.6              271.4             849     0                               0           all    0_openIndexPage
1575255477811000000 7ddemo      198.2142857142857  27    0                 27  849              117       263.79999999999995 292.3500000000001 849     0                               0           all    all

```

这段代码也就是说，在InfluxDB中，创建了两个MEASUREMENTS，分别是events和jmeter。这两个各自存了数据，我们在界面中配置的testtile和eventTags放在了events这个MEASUREMENTS中。在模板中这两个值暂时都是不用的。

在jmeter这个MEASUREMENTS中，我们可以看到application和事务的统计信息，这些值和控制台一致。

在Grafana中显示的时候，就是从这个表中取出的数据，根据时序做的曲线。

### Grafana中的配置

有了JMeter发送到InfluxDB中的数据，下面就来配置一下Grafana中的展示。首先，要配置一个InfluxDB数据源。如下所示：

![](https://static001.geekbang.org/resource/image/88/c8/880584ed313336eac49fe7fe6f82a3c8.png?wh=875%2A926)

在这里配置好URL、Database、User、Password之后，直接点击保存即可。

然后添加一个JMeter dashboard，我们常用的dashboard是Grafana官方ID为5496的模板。导入进来后，选择好对应的数据源。

![](https://static001.geekbang.org/resource/image/f7/82/f7291868468ec639efda5b24b2555182.png?wh=880%2A438)

然后就看到界面了。

![](https://static001.geekbang.org/resource/image/97/f3/97095aac53edf2d164e25de3db3221f3.png?wh=1845%2A777)

这时还没有数据，我们稍后做个示例，看下JMeter中的数据怎么和这个界面的数据对应起来。

我们先看下图中两个重要的数据查询语句吧。

TPS曲线：

```
SELECT last("count") / $send_interval FROM "$measurement_name" WHERE ("transaction" =~ /^$transaction$/ AND "statut" = 'ok') AND $timeFilter GROUP BY time($__interval)
```

上面这个就是Total TPS了，在这里称为throughput。关于这个概念，我在第一篇中就已经有了说明，这里再次提醒，概念的使用在团队中要有统一的认识，不要受行业内一些传统信息的误导。

这里取的数据来自MEASUREMENTS中成功状态的所有事务。

响应时间曲线：

```
SELECT mean("pct95.0") FROM "$measurement_name" WHERE ("application" =~ /^$application$/) AND $timeFilter GROUP BY "transaction", time($__interval) fill(null)
```

这里是用95 pct内的响应时间画出来的曲线。

整体展示出来的效果如下：

![](https://static001.geekbang.org/resource/image/ff/3d/ffac987c827b103fef240916f7cb233d.png?wh=1843%2A777)

### 数据比对

首先，我们在JMeter中配置一个简单的场景。10个线程，每个线程迭代10次，以及两个HTTP请求。

![](https://static001.geekbang.org/resource/image/55/dc/5546c4449baf0e59d477095a93d717dc.png?wh=719%2A282)

也就是说，这时会产生10x10x2=200次请求。我们用JMeter跑起来看一下。

![](https://static001.geekbang.org/resource/image/92/b9/92d1144a5e8d9ebb7fec246777431bb9.png?wh=1004%2A71)

看到了吧，这个请求数和我们预想的一样。下面我们看一下Grafana中展示出来的结果。

![](https://static001.geekbang.org/resource/image/ff/55/ffb38e433239eeb4712887f7d9723155.png?wh=1848%2A833)

还有针对每个事务的统计情况。

![](https://static001.geekbang.org/resource/image/3b/47/3b921720759c06ea39673ec5c84a8047.png?wh=1851%2A780)

至此，JMeter到Grafana的展示过程就完成了。以后我们就不用再保存JMeter的执行结果了，也不用等着JMeter输出HTML了。

## node\_exporter+Prometheus+Grafana的数据展示逻辑

对性能测试来说，在常用的Grafana+Prometheus+Exporter的逻辑中，第一步要看的就是操作系统资源了。所以在这一篇中，我们将以node\_exporter为例来说明一下操作系统抽取数据的逻辑，以便知道监控数据的来源，至于数据的含义，我们将在后续的文章中继续描述。

首先，我们还是要画一个图。

![](https://static001.geekbang.org/resource/image/39/6b/39a970eea119124245e2318779ec7c6b.jpg?wh=744%2A1246)

现在node\_exporter可以支持很多个操作系统了。官方列表如下：

![](https://static001.geekbang.org/resource/image/76/e9/76c6d768b427dd0e3003f9c78a57b3e9.png?wh=1154%2A751)

当然不是说只支持这些，你也可以扩展自己的Exporter。

### 配置node\_exporter

node\_exporter目录如下：

```
[root@7dgroup2 node_exporter-0.18.1.linux-amd64]# ll
total 16524
-rw-r--r-- 1 3434 3434    11357 Jun  5 00:50 LICENSE
-rwxr-xr-x 1 3434 3434 16878582 Jun  5 00:41 node_exporter
-rw-r--r-- 1 3434 3434      463 Jun  5 00:50 NOTICE
```

启动：

```
[root@7dgroup2 node_exporter-0.18.1.linux-amd64]#./node_exporter --web.listen-address=:9200 &
```

是不是很简洁？如果想看更多的功能 ，可以查看下它的帮助。

### 配置Prometheus

先下载Prometheus：

```
[root@7dgroup2 data]# wget -c https://github.com/prometheus/prometheus/releases/download/v2.14.0/prometheus-2.14.0.linux-amd64.tar.gz
..........
100%[=============================================================================================>] 58,625,125   465KB/s   in 6m 4s


2019-11-29 15:40:16 (157 KB/s) - ‘prometheus-2.14.0.linux-amd64.tar.gz’ saved [58625125/58625125]


[root@7dgroup2 data]

```

解压之后，我们可以看到目录结构如下：

```
[root@7dgroup2 prometheus-2.11.1.linux-amd64]# ll
total 120288
drwxr-xr-x. 2 3434 3434     4096 Jul 10 23:26 console_libraries
drwxr-xr-x. 2 3434 3434     4096 Jul 10 23:26 consoles
drwxr-xr-x. 3 root root     4096 Nov 30 12:55 data
-rw-r--r--. 1 3434 3434    11357 Jul 10 23:26 LICENSE
-rw-r--r--. 1 root root       35 Aug  7 23:19 node.yml
-rw-r--r--. 1 3434 3434     2770 Jul 10 23:26 NOTICE
-rwxr-xr-x. 1 3434 3434 76328852 Jul 10 21:53 prometheus
-rw-r--r--  1 3434 3434     1864 Sep 21 09:36 prometheus.yml
-rwxr-xr-x. 1 3434 3434 46672881 Jul 10 21:54 promtool
[root@7dgroup2 prometheus-2.11.1.linux-amd64]#
```

在`prometheus.yml`中添加如下配置，以取数据：

```
  - job_name: 's1'
    static_configs:
    - targets: ['172.17.211.143:9200']
```

启动：

```
[root@7dgroup2 data]# ./prometheus --config.file=prometheus.yml &

```

这样就行了吗？当然不是。根据上面的流程图，我们还需要配置Grafana。

### 配置Grafana

首先配置一个数据源，非常简单。如下所示：

![](https://static001.geekbang.org/resource/image/7f/04/7fdde673c4aabe7d2b0293384237dc04.png?wh=492%2A680)

再配置一个node\_exporter的模板，比如我这里选择了官方模板（ID：11074），展示如下：

![](https://static001.geekbang.org/resource/image/33/00/33c880ff5ba645285f6e6dfbd32aed00.png?wh=1861%2A992)

### 数据逻辑说明

说明完上面的过程之后，对我们做性能测试和分析的人来说，最重要的，就是要知道数据的来源和含义了。

拿上面图中的CPU使用率来说吧（因为CPU使用率是非常重要的一个计数器，所以我们今天先拿它来开刀）。

我们先点一下title上的edit，看一下它的query语句。

```
avg(irate(node_cpu_seconds_total{instance=~"$node",mode="system"}[30m])) by (instance)
avg(irate(node_cpu_seconds_total{instance=~"$node",mode="user"}[30m])) by (instance)
avg(irate(node_cpu_seconds_total{instance=~"$node",mode="iowait"}[30m])) by (instance)
1 - avg(irate(node_cpu_seconds_total{instance=~"$node",mode="idle"}[30m])) by (instance)
```

这些都是从Prometheus中取出来的数据，查询语句读了Prometheus中`node_cpu_seconds_total`的不同的模块数据。

下面我们来看一下，`node_exporter`暴露出来的计数器。

![](https://static001.geekbang.org/resource/image/a6/b0/a6a96e9ead348d8d206c8f10e1890db0.png?wh=682%2A412)

这些值和top一样，都来自于`/proc/`目录。下面这张图是top数据，我们可以比对一下。

![](https://static001.geekbang.org/resource/image/2d/50/2d62f76de8535a92caa3c0e140cba250.png?wh=673%2A393)

到此，我们就了解到了操作系统中监控数据的取值逻辑了，也就是从操作系统本身的计数器中取出值来，然后传给Prometheus，再由Grafana中的query语句查出相应的数据，最后由Grafana展示在界面上。

## 总结

为什么要解释数据的逻辑呢？

因为最近在工作中遇到一些情况，有人觉得有了Prometheus+Grafana+Exportor这样的组合工具之后，基本上都不再用手工执行什么命令了。但我们要了解的是，对于监控平台来说，它取的所有的数据必然是被监控者可以提供的数据，像node\_exporter这样小巧的监控收集器，它可以获取的监控数据，并不是整个系统全部的性能数据，只是取到了常见的计数器而已。

这些计数器不管是用命令查看，还是用这样炫酷的工具查看，它的值本身都不会变。所以不管是在监控平台上看到的数据，还是在命令行中看到的数据，我们最重要的是要知道含义以及这些值的变化对性能测试和分析的下一步骤的影响。

后面我们将着重来解释这些细节。

## 问题

最后我个问题吧，你可以自己去验证下。JMeter是如何把数据推送到Grafana中呢？另外，同样是监控操作系统的计数器，监控平台中的数据和监控命令中的数据有什么区别？

欢迎你在评论区写下你的思考，也欢迎把这篇文章分享给你的朋友或者同事，一起交流一下。
<div><strong>精选留言（15）</strong></div><ul>
<li><span>小昭</span> 👍（7） 💬（2）<p>今日思考题：
问题1：JMeter 是如何把数据推送到 Grafana 中的？
共分为两个大步骤：
1、JMeter 将数据发给 InfluxDB：
（1）在JMeter 中配置 Backend Listener ；
（2）使用InfluxdbBackendListenerClient将JMeter运行的统计结果添加到metric中，并保存metric；
（3）使用InfluxdbMetricsSender将metric发送到Influxdb；
2、Grafana从 InfluxDB获取数据：
（1）在Grafana 中配置InfluxDB 数据源
（2）添加 JMeter dashboard，导入模板，选择对应的数据源即可看到界面


问题2：同样是监控操作系统的计数器，监控平台中的数据和监控命令中的数据有什么区别？
就数据的值来说，没有区别；
就数据量来说，监控平台的数据通常比监控命令中查到的数据会少一些。


今日感悟：
高老师的专栏，音频总会比文章多讲一些，知道这一点之后，我就调整了学习方式，我先听音频，再细读文章（以前我的习惯是先看文章，再听音频）。这节内容，不适用了，不知道是因为我太弱，还是老师语速变快了，边听边看文章，听的真是一脸懵。
大概听了3遍之后，这节课在我眼里变成了高不可攀的形象。甚至让我有一种，这个专栏我可能就卡在这里学不动了的感觉。然后抵触心理就出来了，有点不想学。
但是吧，不能轻言放弃，于是我不听音频了，开始细细读文章。边读边整理笔记，梳理思路。
神奇般的，我觉得我又能懂了，虽然不是说完全能把这个监控平台搭起来，但是我觉得我体会到了老师这节课想强调的东西。
最后，作为一个小白，这节课我对自己的要求就是：达到一个感性的认识。

其实归根结底还是自己手头没有实际的性能项目来练习，边学边练其实才是最好的。

最最后：文中“通过 writeAndSendMetrics，就将所有保存的 metrix 都发给了 InfluxDB。” 老师单词是不是拼错啦，应该是metric吧（或者是metrics?）</p>2020-03-30</li><br/><li><span>bettynie</span> 👍（7） 💬（1）<p>老师，按照你讲的原理，其实我们需要搭建 jmeter+influxdb+grafana 和 prometheus+exports+grafana 2套系统来分别监控我们需要的性能指标，是么？
 jmeter+influxdb+grafana用来监控jmeter中的线程数，响应时间和吞吐量，prometheus+exports+grafana 用来监控系统资源或者数据库以及其他资源, 对么？
并且prometheus+exports+grafana 只能监控linux和uinx系统，无法监控windows,并且只能监控mysql数据库，感觉好像就是为监控docker之内的容器而生的~</p>2020-02-29</li><br/><li><span>SeaYang</span> 👍（6） 💬（1）<p>老师您好，backend listener本身没有问题，可能我描述的不够清楚，我再描述一次我的问题：
1、背景
我们基于jmeter做了个压测平台，在平台的前端页面上编写接口、场景等，点击压测，后端会调度多台压力机，每台压力机会将接口、场景数据使用jmeter的api生成jmx文件，然后调用jmeter的命令行启动压测。生成jmx文件的过程中会创建一个backend listener元件，每台压力机backend listener元件的application字段设置为了同一个值，这样子我们可以通过这个application值调用InfluxDB的http接口，获得所有压力机的tps总和

2、遇到的问题
1）实验过程
使用控制目标TPS的方式，TPS目标是2000，启动20台压力机，每台压力机的目标TPS为2000 &#47; 20 = 100，注意，单台压力机就能达到2000TPS。
2）现象
通过观察前端页面的tps曲线，会发现TPS经常达不到2000，经常是1800， 1900左右，看上去像是有一两台压力机没有将数据抛到InfluxDB中，查看InfluxDB，会发现每秒确实只有18条、19条的数据。
3）分析
查看每台压力机的jmeter输出日志，有summary输出，说明每台压力机都正常调起了jmeter并正常压测了，查看InfluxDB的连接也没有问题。
后来同时启动30台压力机，也是看上去像是有一两台压力机没有抛数据一样，但jmeter日志都没问题，这就很奇怪了，如果是InfluxDB不支持20台压力机同时抛数据，那么30台压力机同时抛数据就应该最多每秒只有十几条数据啊。难道是因为每台压力机的application值都一样，有一定概率发生数据覆盖？

3、解决办法
将每台压力机的backend listener的application字段设置为不同的值，但是有一个相同的前缀，通过这个前缀值去查询总的TPS数据，经过几十次的测试，都是正常的，没有再出现问题了。但是之前是不是发生了数据覆盖也不确定，但暂时也不管了。</p>2020-11-12</li><br/><li><span>障碍物</span> 👍（5） 💬（1）<p>Prometheus有插件能监控sqlserver或者oracle等其他数据库么</p>2020-02-11</li><br/><li><span>dao</span> 👍（3） 💬（2）<p>如果有人和我一样安装的是 influxdb 2.0，那么需要在 JMeter Backend Listener 设置 influxdbUrl 和 influxdbToken。比如我的设置
influxdbUrl：http:&#47;&#47;192.168.1.196:9999&#47;api&#47;v2&#47;write?bucket=test&amp;org=dao
influxdbToken：好长的一串 base64 编码的 token</p>2021-05-04</li><br/><li><span>蔚来懿</span> 👍（3） 💬（1）<p>老师，有一个疑问，我的情况是这样的，我们公司环境有很多（测试环境，开发环境，预发布环境，开发环境），很多个项目，每个项目结构复杂，机器有很多，如果按照这样的部署的话，需要安装很多软件，还有防火墙的问题，请问是否有轻量级的监控方式，比如说，直接在服务器上装工具（类似nmon，但是直观），</p>2021-01-13</li><br/><li><span>涓涓</span> 👍（3） 💬（1）<p>高老师，好。
你看这样配置行不行:
1. 要监控的每台服务器都配置一个node_exporter
2.  然后再找台服务器安装prometheus，在prometheus.yml中添加每个node_exporter的配置
3. 最后在grafana中配置prometheus，查看采集的各台服务器数据。</p>2021-01-08</li><br/><li><span>SeaYang</span> 👍（3） 💬（1）<p>1、JMeter 是如何把数据推送到 Grafana 中呢？
JMeter实际上是将数据推送到Influxdb中，Influxdb本身对外提供了HTTP接口，Grafana通过HTTP接口轮询性能指标，若自己去画前端页面图表的话，也可以不用Grafana，直接调用Influxdb的HTTP接口

2、另外，同样是监控操作系统的计数器，监控平台中的数据和监控命令中的数据有什么区别？
没有区别，只是命令可能能看到更多的值

有时候压测过程中，压力机本身的资源情况也是需要关注的，通过Prometheus + node_exporter + Grafana可以很方便的查看压力机集群的资源情况，比传统一台台登录方便很多，顺便熟悉监控的部署</p>2020-11-11</li><br/><li><span>杜艳</span> 👍（3） 💬（16）<p>感觉老师讲的都是偏理论，知道数据的来龙去脉了，但是使用过程怎么搭建这个整体的监控平台步骤能不能详细介绍，让我们可以用在项目中呢？</p>2020-02-09</li><br/><li><span>Cheese</span> 👍（2） 💬（1）<p>老师，如果用nodeexporter监控容器要怎么监控，因为容器IP是变化的，是通过端口来监控吗</p>2021-11-21</li><br/><li><span>不将就</span> 👍（2） 💬（1）<p>问题1:：Jmeter直接面向的是influxdb,Granfana通过官方插件取指定的influxdb中抓取数据做展示
问题2：监控平台的数据本质上还是通过操作系统命令获取的，而且有抓取周期，通过网络传过来，实时性不如直接在操作系统获取，但是好处也是明显的，就是图形化展示和历史监控数据的便捷查询</p>2020-11-05</li><br/><li><span>aoe</span> 👍（2） 💬（3）<p>上来安装了 InfluxDB 2.0 ，结果悲剧了，找了一天没找到怎么创建 database，后来看官方文档，感觉是理念变了，全部通过 API 完成。请选择 InfluxDB v1.8 ，避免 2.0 的尴尬。</p>2020-10-28</li><br/><li><span>Geek_a55bf0</span> 👍（2） 💬（1）<p>高老师，我的jmeter传到influxdb的数据没有事务名，请问您知道原因吗？如果没有碰到过麻烦提供下您的软件版本，我按您的版本安装试试</p>2020-06-16</li><br/><li><span>Joie</span> 👍（2） 💬（1）<p>我在项目中用到了jmeter+influxDB+grafana，拉长时间段来看TPS和响应时间 还有分事务来看不同趋势 效果很明显。不过有时候不知道为什么在趋势显示时中间会有断开曲线的情况，在jmeter自身的log中是没有出现的</p>2020-04-16</li><br/><li><span>郑频雅</span> 👍（1） 💬（1）<p>请问老师，除了这套工具，nmon为什么没有介绍，这个工具不是必不可少的？</p>2021-07-09</li><br/>
</ul>