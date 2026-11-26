你好，我是张磊。今天我和你分享的主题是：Custom Metrics，让Auto Scaling不再“食之无味”。

在上一篇文章中，我为你详细讲述了 Kubernetes 里的核心监控体系的架构。不难看到，Prometheus 项目在其中占据了最为核心的位置。

实际上，借助上述监控体系，Kubernetes 就可以为你提供一种非常有用的能力，那就是 Custom Metrics，自定义监控指标。

在过去的很多 PaaS 项目中，其实都有一种叫作 Auto Scaling，即自动水平扩展的功能。只不过，这个功能往往只能依据某种指定的资源类型执行水平扩展，比如 CPU 或者 Memory 的使用值。

而在真实的场景中，用户需要进行Auto Scaling 的依据往往是自定义的监控指标。比如，某个应用的等待队列的长度，或者某种应用相关资源的使用情况。这些复杂多变的需求，在传统 PaaS项目和其他容器编排项目里，几乎是不可能轻松支持的。

而凭借强大的 API 扩展机制，Custom Metrics已经成为了 Kubernetes 的一项标准能力。并且，Kubernetes 的自动扩展器组件 Horizontal Pod Autoscaler （HPA）， 也可以直接使用Custom Metrics来执行用户指定的扩展策略，这里的整个过程都是非常灵活和可定制的。

不难想到，Kubernetes 里的 Custom Metrics 机制，也是借助Aggregator APIServer 扩展机制来实现的。这里的具体原理是，当你把 Custom Metrics APIServer 启动之后，Kubernetes 里就会出现一个叫作`custom.metrics.k8s.io`的 API。而当你访问这个 URL 时，Aggregator就会把你的请求转发给Custom Metrics APIServer 。

而Custom Metrics APIServer 的实现，其实就是一个 Prometheus 项目的 Adaptor。

比如，现在我们要实现一个根据指定 Pod 收到的 HTTP 请求数量来进行 Auto Scaling 的 Custom Metrics，这个 Metrics 就可以通过访问如下所示的自定义监控 URL 获取到：

```
https://<apiserver_ip>/apis/custom-metrics.metrics.k8s.io/v1beta1/namespaces/default/pods/sample-metrics-app/http_requests 
```

这里的工作原理是，当你访问这个 URL 的时候，Custom Metrics APIServer就会去 Prometheus 里查询名叫sample-metrics-app这个Pod 的http\_requests指标的值，然后按照固定的格式返回给访问者。

当然，http\_requests指标的值，就需要由 Prometheus 按照我在上一篇文章中讲到的核心监控体系，从目标 Pod 上采集。

这里具体的做法有很多种，最普遍的做法，就是让 Pod 里的应用本身暴露出一个/metrics API，然后在这个 API 里返回自己收到的HTTP的请求的数量。所以说，接下来 HPA 只需要定时访问前面提到的自定义监控 URL，然后根据这些值计算是否要执行 Scaling 即可。

接下来，我通过一个具体的实例，来为你讲解一下 Custom Metrics 具体的使用方式。这个实例的 GitHub 库[在这里](https://github.com/resouer/kubeadm-workshop)，你可以点击链接查看。在这个例子中，我依然会假设你的集群是 kubeadm 部署出来的，所以 Aggregator 功能已经默认开启了。

> 备注：我们这里使用的实例，fork 自 Lucas 在上高中时做的一系列Kubernetes 指南。

**首先**，我们当然是先部署 Prometheus 项目。这一步，我当然会使用 Prometheus Operator来完成，如下所示：

```
$ kubectl apply -f demos/monitoring/prometheus-operator.yaml
clusterrole "prometheus-operator" created
serviceaccount "prometheus-operator" created
clusterrolebinding "prometheus-operator" created
deployment "prometheus-operator" created

$ kubectl apply -f demos/monitoring/sample-prometheus-instance.yaml
clusterrole "prometheus" created
serviceaccount "prometheus" created
clusterrolebinding "prometheus" created
prometheus "sample-metrics-prom" created
service "sample-metrics-prom" created
```

**第二步**，我们需要把 Custom Metrics APIServer 部署起来，如下所示：

```
$ kubectl apply -f demos/monitoring/custom-metrics.yaml
namespace "custom-metrics" created
serviceaccount "custom-metrics-apiserver" created
clusterrolebinding "custom-metrics:system:auth-delegator" created
rolebinding "custom-metrics-auth-reader" created
clusterrole "custom-metrics-read" created
clusterrolebinding "custom-metrics-read" created
deployment "custom-metrics-apiserver" created
service "api" created
apiservice "v1beta1.custom-metrics.metrics.k8s.io" created
clusterrole "custom-metrics-server-resources" created
clusterrolebinding "hpa-controller-custom-metrics" created
```

**第三步**，我们需要为 Custom Metrics APIServer 创建对应的 ClusterRoleBinding，以便能够使用curl来直接访问 Custom Metrics 的 API：

```
$ kubectl create clusterrolebinding allowall-cm --clusterrole custom-metrics-server-resources --user system:anonymous
clusterrolebinding "allowall-cm" created
```

**第四步**，我们就可以把待监控的应用和 HPA 部署起来了，如下所示：

```
$ kubectl apply -f demos/monitoring/sample-metrics-app.yaml
deployment "sample-metrics-app" created
service "sample-metrics-app" created
servicemonitor "sample-metrics-app" created
horizontalpodautoscaler "sample-metrics-app-hpa" created
ingress "sample-metrics-app" created
```

这里，我们需要关注一下 HPA 的配置，如下所示：

```
kind: HorizontalPodAutoscaler
apiVersion: autoscaling/v2beta1
metadata:
  name: sample-metrics-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: sample-metrics-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Object
    object:
      target:
        kind: Service
        name: sample-metrics-app
      metricName: http_requests
      targetValue: 100
```

可以看到，**HPA 的配置，就是你设置 Auto Scaling 规则的地方。**

比如，scaleTargetRef字段，就指定了被监控的对象是名叫sample-metrics-app的 Deployment，也就是我们上面部署的被监控应用。并且，它最小的实例数目是2，最大是10。

在metrics字段，我们指定了这个 HPA 进行 Scale 的依据，是名叫http\_requests的 Metrics。而获取这个 Metrics 的途径，则是访问名叫sample-metrics-app的 Service。

有了这些字段里的定义， HPA 就可以向如下所示的 URL 发起请求来获取 Custom Metrics 的值了：

```
https://<apiserver_ip>/apis/custom-metrics.metrics.k8s.io/v1beta1/namespaces/default/services/sample-metrics-app/http_requests
```

需要注意的是，上述这个 URL 对应的被监控对象，是我们的应用对应的 Service。这跟本文一开始举例用到的 Pod 对应的 Custom Metrics URL 是不一样的。当然，**对于一个多实例应用来说，通过 Service 来采集 Pod 的 Custom Metrics 其实才是合理的做法。**

这时候，我们可以通过一个名叫hey的测试工具来为我们的应用增加一些访问压力，具体做法如下所示：

```
$ # Install hey
$ docker run -it -v /usr/local/bin:/go/bin golang:1.8 go get github.com/rakyll/hey

$ export APP_ENDPOINT=$(kubectl get svc sample-metrics-app -o template --template {{.spec.clusterIP}}); echo ${APP_ENDPOINT}
$ hey -n 50000 -c 1000 http://${APP_ENDPOINT}
```

与此同时，如果你去访问应用 Service 的 Custom Metircs URL，就会看到这个 URL 已经可以为你返回应用收到的 HTTP 请求数量了，如下所示：

```
$ curl -sSLk https://<apiserver_ip>/apis/custom-metrics.metrics.k8s.io/v1beta1/namespaces/default/services/sample-metrics-app/http_requests
{
  "kind": "MetricValueList",
  "apiVersion": "custom-metrics.metrics.k8s.io/v1beta1",
  "metadata": {
    "selfLink": "/apis/custom-metrics.metrics.k8s.io/v1beta1/namespaces/default/services/sample-metrics-app/http_requests"
  },
  "items": [
    {
      "describedObject": {
        "kind": "Service",
        "name": "sample-metrics-app",
        "apiVersion": "/__internal"
      },
      "metricName": "http_requests",
      "timestamp": "2018-11-30T20:56:34Z",
      "value": "501484m"
    }
  ]
}
```

**这里需要注意的是，Custom Metrics API 为你返回的 Value 的格式。**

在为被监控应用编写/metrics API 的返回值时，我们其实比较容易计算的，是该 Pod 收到的 HTTP request 的总数。所以，我们这个[应用的代码](https://github.com/resouer/kubeadm-workshop/blob/master/images/autoscaling/server.js)其实是如下所示的样子：

```
  if (request.url == "/metrics") {
    response.end("# HELP http_requests_total The amount of requests served by the server in total\n# TYPE http_requests_total counter\nhttp_requests_total " + totalrequests + "\n");
    return;
  }
```

可以看到，我们的应用在/metrics 对应的 HTTP response 里返回的，其实是http\_requests\_total的值。这，也就是 Prometheus 收集到的值。

而 Custom Metrics APIServer 在收到对http\_requests指标的访问请求之后，它会从Prometheus 里查询http\_requests\_total的值，然后把它折算成一个以时间为单位的请求率，最后把这个结果作为http\_requests指标对应的值返回回去。

所以说，我们在对前面的 Custom Metircs URL 进行访问时，会看到值是501484m，这里的格式，其实就是milli-requests，相当于是在过去两分钟内，每秒有501个请求。这样，应用的开发者就无需关心如何计算每秒的请求个数了。而这样的“请求率”的格式，是可以直接被 HPA 拿来使用的。

这时候，如果你同时查看 Pod 的个数的话，就会看到 HPA 开始增加 Pod 的数目了。

不过，在这里你可能会有一个疑问，Prometheus 项目，又是如何知道采集哪些 Pod 的 /metrics API 作为监控指标的来源呢。

实际上，如果仔细观察一下我们前面创建应用的输出，你会看到有一个类型是ServiceMonitor的对象也被创建了出来。它的 YAML 文件如下所示：

```
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: sample-metrics-app
  labels:
    service-monitor: sample-metrics-app
spec:
  selector:
    matchLabels:
      app: sample-metrics-app
  endpoints:
  - port: web
```

这个ServiceMonitor对象，正是 Prometheus Operator 项目用来指定被监控 Pod 的一个配置文件。可以看到，我其实是通过Label Selector 为Prometheus 来指定被监控应用的。

# 总结

在本篇文章中，我为你详细讲解了 Kubernetes 里对自定义监控指标，即 Custom Metrics 的设计与实现机制。这套机制的可扩展性非常强，也终于使得Auto Scaling 在 Kubernetes 里面不再是一个“食之无味”的鸡肋功能了。

另外可以看到，Kubernetes 的 Aggregator APIServer，是一个非常行之有效的 API 扩展机制。而且，Kubernetes 社区已经为你提供了一套叫作 [KubeBuilder](https://github.com/kubernetes-sigs/kubebuilder) 的工具库，帮助你生成一个 API Server 的完整代码框架，你只需要在里面添加自定义 API，以及对应的业务逻辑即可。

# 思考题

在你的业务场景中，你希望使用什么样的指标作为 Custom Metrics ，以便对 Pod 进行 Auto Scaling 呢？怎么获取到这个指标呢？

感谢你的收听，欢迎你给我留言，也欢迎分享给更多的朋友一起阅读。

![](https://static001.geekbang.org/resource/image/96/25/96ef8576a26f5e6266c422c0d6519725.jpg?wh=1110%2A659)
<div><strong>精选留言（15）</strong></div><ul>
<li><span>虎虎❤️</span> 👍（20） 💬（0）<p>HPA 通过 HorizontalPodAutoscaler 配置要访问的 Custom Metrics, 来决定如何scale。
Custom Metric APIServer 的实现其实是一个Prometheus 的Adaptor，会去Prometheus中读取某个Pod&#47;Servicce的具体指标值。比如，http request的请求率。
Prometheus 通过 ServiceMonitor object 配置需要监控的pod和endpoints，来确定监控哪些pod的metrics。
应用需要实现&#47;metrics， 来响应Prometheus的数据采集请求。

留给自己的思考，Pod 的 metrics endpoint 如何对应到http_requests 这个指标的？
</p>2018-12-16</li><br/><li><span>单朋荣</span> 👍（13） 💬（1）<p>张老师，伸缩是不是写的简单了点，毕竟伸缩也是核心功能之一。主要想了解下，hpa伸缩的判定算法的替换方法，vpa预测算法的常见类型及优缺点，ca在大规模场景下实现的原理，ar的应用场景等；还有就是自定义伸缩（prometheus)时间戳优化原理、方法，及最后微服务下伸缩的结合方法等。可不可以从伸缩的数据分类、获取手段、处理算法、伸缩流程、调度算法、故障处理反馈机制等方面，再列几章讲一下，谢谢张老师！！</p>2020-05-25</li><br/><li><span>William</span> 👍（7） 💬（2）<p>请问能否实现跨node的水平扩展?</p>2018-12-24</li><br/><li><span>DJH</span> 👍（7） 💬（2）<p>请教一个问题：对于多POD的应用（如多副本的deployment），假设配置了根据CPU使用率进行自动水平伸缩（HPA），那么HPA执行水平伸缩的依据是各个POD中CPU使用率平均值还是最高值？另外HPA探测到多少次CPU高于设置值才会开始伸缩？CPU使用率探测的频率又是多久一次呢？</p>2018-12-14</li><br/><li><span>剑走偏锋</span> 👍（3） 💬（0）<p>就为了做自定义业务指标的监控，我们也做了水晶桥(Crystal Bridge)项目开源在github上了。思路是自采通过annotations公开的promethus指标，然后推往prometheus GW，最后再由上层prometheus来采集。

今天这种让HPA通过自定义指标来完成扩容&#47;缩容操作的技术设计的确很棒，学习了，感谢。</p>2019-01-04</li><br/><li><span>Mars</span> 👍（1） 💬（0）<p>请教下老师 为什么knative要自己弄一个autoscaler。既然k8s已经有了autoscaler了，感觉没啥必要再造一个轮子。</p>2020-06-10</li><br/><li><span>manatee</span> 👍（1） 💬（4）<p>请问下老师，扩容好理解就是加容器，那缩容的话如何实现呢，怎么保证在删除容器的时候容器上的请求不受影响呢</p>2019-12-18</li><br/><li><span>stan</span> 👍（1） 💬（1）<p>请张老师帮忙解惑，对于多实例应用，采集 service暴露的指标才是正确的做法，这句怎么理解？采集每个pod对应的指标不好吗，service后面对应的api无法确认来自哪个pod吧？数据可能忽大忽小，如果采集到一个刚刚hpa的pod指标，数据可能更小，这样应该没有采集每个pod，然后平均值来的更精确吧？类似对于cpu 的hpa，就是采集的每个pod的指标然后做平均值</p>2018-12-20</li><br/><li><span>源子陌</span> 👍（0） 💬（2）<p>“所以说，我们在对前面的 Custom Metircs URL 进行访问时，会看到值是 501484m，这里的格式，其实就是 milli-requests，相当于是在过去两分钟内，每秒有 501 个请求。”——这个 501484m 是怎么折算成 501 QPS的，老师能再解释下嘛？</p>2022-05-24</li><br/><li><span>陈斯佳</span> 👍（0） 💬（0）<p>第四十七课:Custom Metrics: 让Auto Scaling不再“食之无味”

很多 PaaS 项目中的Auto Scaling，即自动水平扩展的功能，只能依据某种指定的资源类型执行水平扩展，比如 CPU 或者 Memory 的使用值。凭借强大的 API 扩展机制，Custom Metrics 已经成为了 Kubernetes 的一项标准能力。并且，Kubernetes 的自动扩展器组件 Horizontal Pod Autoscaler （HPA）， 也可以直接使用 Custom Metrics 来执行用户指定的扩展策略，这里的整个过程都是非常灵活和可定制的。Kubernetes 里的 Custom Metrics 机制，也是借助 Aggregator APIServer 扩展机制来实现的。这里的具体原理是，当你把 Custom Metrics APIServer 启动之后，Kubernetes 里就会出现一个叫作custom.metrics.k8s.io的 API。而当你访问这个 URL 时，Aggregator 就会把你的请求转发给 Custom Metrics APIServer 。而 Custom Metrics APIServer 的实现，其实就是一个 Prometheus 项目的 Adaptor。</p>2021-11-08</li><br/><li><span>罗峰</span> 👍（0） 💬（0）<p>Hpa里面配置了对哪些deploy等进行水平伸缩、伸缩的范围，对应的指标的阈值。
指标是普罗主动拉取的，需要个servicemonitor告诉普罗哪个指标拉取哪个pod。
这样指标有了，需扩展的k8资源确定了，ha功能也就可以了。</p>2021-06-01</li><br/><li><span>饮水</span> 👍（0） 💬（0）<p>你好，老师，KubeBuilder还能用来做api么，那这个api和operator有啥区别？</p>2021-04-23</li><br/><li><span>小白</span> 👍（0） 💬（1）<p>HPA 定义时并没看到是访问custom.metrics.k8s.io接口的，Aggregator 怎么知道应该调用custom metrics API server?</p>2020-08-06</li><br/><li><span>单朋荣</span> 👍（0） 💬（0）<p>Warning  FailedGetObjectMetric         1m (x13 over 7m)  horizontal-pod-autoscaler  unable to get metric http_requests: Service on default sample-metrics-app&#47;unable to fetch metrics from custom metrics API: the server could not find the metric http_requests for services
  Warning  FailedComputeMetricsReplicas  1m (x13 over 7m)  horizontal-pod-autoscaler  failed to get object metric value: unable to get metric http_requests: Service on default sample-metrics-app&#47;unable to fetch metrics from custom metrics API: the server could not find the metric http_requests for services
遇到一个问题，求解决思路。。
</p>2019-10-22</li><br/><li><span>yzw</span> 👍（0） 💬（0）<p>老师，对于没有证书的kubernetes集群，修改prometheus的什么参数可以保证访问采用的是不安全方式呢？我的kubernetes集群是v1.11.2，prometheus是kube-prometheus:v0.1.0，谢谢解答</p>2019-08-06</li><br/>
</ul>