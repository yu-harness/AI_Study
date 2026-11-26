你好，我是Chrono。

距离《Kubernetes入门实战课》完结已经有一段时间了，不知道你是否还在持续地学习、实践这个云原生时代的操作系统呢？我想答案应该是肯定的吧。

这次我带来了一个关于Kubernetes的最新消息，长期以来被关注的“下一代” Ingress 对象：Gateway API，在经过了近4年的讨论、测试和验证之后，终于在2023年的11月正式发布，可以用于生产环境，也就是我们常说的GA（generally available）。

那么，什么是Gateway API呢？它与Ingress有什么样的联系和区别呢？我们应该怎样在Kubernetes里部署和使用它呢？

今天我就来深入探讨这个话题，来看看Kubernetes的最新进展。

## 什么是 Gateway API

我们在[第21讲](https://time.geekbang.org/column/article/538760)对Ingress做过详细的介绍，相信你已经对它很熟悉了，它管理集群的进出口流量，提供完善的负载均衡和反向代理功能，**是部署Kubernetes应用必不可缺的组件**。

但是，Ingress的缺点也很明显，它自身的能力较弱，只能编写有限的路由规则，不能完全满足各种实际需求，所以Ingress Controller的实现者（如NGINX Ingress Controller、Kong Ingress Controller等）不得不使用大量的annotation和CRD来定制、扩展功能。

这种实现混乱的局面被戏称为 “annotations wild west”，对Kubernetes用户非常不友好，同一个功能在不同的Ingress Controller之间用法差异极大，迁移的成本非常高，没有统一的标准导致Ingress使用起来相当麻烦。

有鉴于此，Kubernetes社区就打算参考Ingress，重新设计一组对象来解决这些问题。于是在2019年末圣地亚哥的KubeCon上，许多不同背景的人们发起了一个新的项目，也就是Gateway API，**目标是全面替代和超越Ingress，更好地管理Kubernetes里各方向的流量**。

![](https://static001.geekbang.org/resource/image/cd/c0/cd8bd1ee97087c357760239yyc02a2c0.png?wh=900x250 "图片来源：https://kubernetes.io/blog/2023/10/31/gateway-api-ga/gateway-api-logo.png")

在随后的几年，陆续有一些公司加入了Gateway API项目，因为有Ingress的“前车之鉴”，Gateway API一开始就具备了良好的架构，避免了Ingress所踩过的“坑”，所以它的进展还是比较顺利的。

下图来自Kubernetes的官方统计数据，显示了在这个过程中各个公司的**贡献程度**。

![](https://static001.geekbang.org/resource/image/20/c7/20e0aeaab81b9a4a5ab0451fa52206c7.png?wh=2802x1448)

在2023年11月发布的1.0版本里包括3个已经成熟稳定的对象，Gateway Class、Gateway和HTTPRoute（相关的[博客](https://kubernetes.io/blog/2023/10/31/gateway-api-ga/)在这里）。

在Gateway API项目的[主页](https://gateway-api.sigs.k8s.io/)上，对这3个重要的对象有简单的介绍。

![](https://static001.geekbang.org/resource/image/bc/26/bcfb81598c01a23f28745b9b00a19d26.png?wh=2414x1418 "图片来源：https://gateway-api.sigs.k8s.io/images/api-model.png")

由于Gateway API是Ingress的后继者，所以我们可以对比Ingress来理解它们的概念和作用。

最上层的Gateway Class类似于Ingress Class，由各个云厂商提供；中间的Gateway类似于Ingress Controller，由集群管理员管理；下面的HTTPRoute类似于Ingress，由开发人员管理，定义路由规则，规定流量将如何被Gateway分发到集群里的Service和Pod。

可以看到，Gateway API的结构非常清晰明了，很容易理解。

在Gateway API正式发布时（11月1日），大部分厂商还没有提供完整支持，基本都是预览版或测试版，但也有两家公司几乎同步实现了GA，这就是GKE（Google Kubernetes Engine）和Kong，所以下面我就以Kong为例，来介绍Gateway API的用法。

## 安装 Gateway API

首先要说的是，Gateway API只支持较新的Kubernetes，不能运行在Kubernetes 1.23上，为了体验Gateway API，我们最好使用最新版本的Kubernetes。

这里我选用了minikube 1.32.0，Kubernetes是1.28.3，你可以参考[第9讲](https://time.geekbang.org/column/article/529780)的内容来安装，或者直接用下面的命令。

```plain
# Intel x86_64
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64

# Apple arm64
curl -Lo minikube https://storage.googleapis.com/minikube/releases/latest/minikube-linux-arm64

sudo install minikube /usr/local/bin/

minikube start --kubernetes-version=v1.28.3
kubectl version
```

![图片](https://static001.geekbang.org/resource/image/fd/d3/fd97a8d12705951a840ceff5421214d3.png?wh=1620x1438)

有了合适的Kubernetes环境，下面就来部署Gateway API。

要注意的是Gateway API比较特殊，并不是集成在Kubernetes内部，而是在外部以相对独立的方式开发实现的，所以需要用YAML文件的形式来部署进Kubernetes。

你可以在[Gateway API项目网站](https://gateway-api.sigs.k8s.io/guides/)里找到安装命令，很简单，用 `kubectl apply` 就能够搞定。

```plain
wget https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml
kubectl apply -f standard-install.yaml
```

![图片](https://static001.geekbang.org/resource/image/24/e0/2449fd1d96136aaae9d7b5b6d7996be0.png?wh=1920x232)

安装完成后，可以用 `kubectl api-resources` 命令来查看新的Gateway API对象。

```plain
kubectl api-resources | grep gateway
```

![图片](https://static001.geekbang.org/resource/image/ec/yc/ec938c5b47edfff23a38f1e17126dyyc.png?wh=1920x197)

这就证明Gateway API已经成功安装到了当前的Kubernetes集群里，而且你还应该注意到Gateway Class的缩写是 “gc”，Gateway的缩写是 “gtw”。

现在用YAML创建实验用的Gateway Class和Gateway对象，但目前它们还不能使用 `kubectl create` 生成样板，只能手动编写。

```plain
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: kong-gc
  annotations:
    konghq.com/gatewayclass-unmanaged: 'true'

spec:
  controllerName: konghq.com/kic-gateway-controller

---

apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: kong-gtw
spec:
  gatewayClassName: kong-gc
  listeners:
  - name: proxy
    port: 80
    protocol: HTTP
```

这个YAML定义了一个叫 kong-gc 的Gateway Class对象，指定使用的Controller是 konghq.com/kic-gateway-controller。然后Gateway对象的名字是 kong-gtw，它关联了 kong-gc，在80端口上处理HTTP协议。

`kubectl apply` 后再用 `kubectl get` 命令，会看到它们已经创建成功。

![图片](https://static001.geekbang.org/resource/image/6b/55/6b54ecccbf830d9482e0f99e993bc855.png?wh=1586x360)

## 安装 Kong Ingress Controller

刚才部署好了Kubernetes环境和Gateway API，现在就可以安装Kong Gateway，它的实现仍然是以Ingress Controller的形式，也就是Kong Ingress Controller，在之前的[加餐](https://time.geekbang.org/column/article/612952)中我也对它做过详细的介绍。

不过那个时候使用的Kong Ingress Controller还是2.7.0，而现在它已经升级到了3.0.0，里里外外都发生了很多变化，完全是一个新的应用。

Kong Ingress Controller 2.x 可以使用YAML文件直接安装，但3.0.0已经废弃了这种方式，只能够使用Helm或Operator来安装，这里我选用的是Helm。

你也许不太熟悉Helm，我来简单介绍一下。它类似于Linux里的yum、apt，对复杂的云原生应用非常有用，可以把众多的YAML文件组合成安装包的形式，再轻松地把应用部署进Kubernetes集群。但由于它不是我们今天的重点，所以就不多说了。

Helm的安装很简单，它提供了一个[官方脚本](https://helm.sh/docs/intro/install/)，直接执行即可。

```plain
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

![图片](https://static001.geekbang.org/resource/image/2d/86/2d1cc05530497261db10e30bdca79486.png?wh=1920x155)

然后我们需要添加远端仓库（Helm charts），用法和yum、apt也很类似。

```plain
helm repo add kong https://charts.konghq.com
helm repo update
```

之后可以查看远端仓库里可用的安装包。

```plain
helm repo list
helm search repo kong
```

![图片](https://static001.geekbang.org/resource/image/72/1a/721064f98d17534d58d5b05b298a771a.png?wh=1920x325)

这里显示的 kong/ingress 就是Kong Ingress Controller。

使用命令 `helm install` 指定名字和安装包，再加上一些定制参数就可以安装Kong Ingress Controller。

```plain
helm install \
    kong kong/ingress \
    -n kong \
    --create-namespace \
    --set gateway.env.router_flavor=expressions
```

这里我多加了一个 “–set” 选项，启用Kong Ingress Controller的表达式路由，能够更好地支持Gateway API。

Kong Ingress Controller默认安装在kong名字空间，用 `kubectl get` 就可以看到它的Pod、Service等对象。

![图片](https://static001.geekbang.org/resource/image/50/7c/501c7cef1dyy43c351e7424c29609d7c.png?wh=1920x403)

要注意的是kong-gateway-proxy这个Service，它的类型是LoadBalancer，也就是对外的服务接口，在实验环境里使用的端口是 31198，后续我们要使用这个端口来测试。

使用 `curl` 访问这个服务可以验证Kong Ingress Controller是否正常工作。

```plain
curl -i $(minikube ip):31198
```

![图片](https://static001.geekbang.org/resource/image/71/47/7104ccb33e4e936d20e80b544e4a5d47.png?wh=1270x726)

`curl` 命令的输出是404，这是因为我们还没有配置HTTPRoute资源，没有路由规则，所以Gateway无法处理流量。

这时再检查Gateway Class和Gateway对象，会看到 ACCEPTED 和 PROGRAMMED 字段都已经变成了 True，这就表示Gateway对象已经正确关联了Kong Ingress Controller。

![图片](https://static001.geekbang.org/resource/image/5c/0f/5c63c241286b27690591afbab3dfa30f.png?wh=1590x366)

## 准备后端服务

为了验证Gateway API的流量管理效果，我们还要创建测试用的后端服务，具体做法可以参考[第20讲](https://time.geekbang.org/column/article/536829)和[第21讲](https://time.geekbang.org/column/article/538760)，部署NGINX来输出简单的字符串。

下面的这个YAML是一个样板文件，你可以使用查找替换的方式生成多个不同名字的服务。

```plain
apiVersion: v1
kind: ConfigMap
metadata:
  name: ngx-conf

data:
  default.conf: |
    server {
      listen 80;
      location / {
        default_type text/plain;
        return 200
          'ngx\nsrv : $server_addr:$server_port\nhost: $hostname\nuri : $request_method $host $request_uri\n';
      }
    }

---

apiVersion: apps/v1
kind: Deployment
metadata:
  name: ngx-dep
  labels:
    app: ngx-dep

spec:
  replicas: 1
  selector:
    matchLabels:
      app: ngx-dep

  template:
    metadata:
      labels:
        app: ngx-dep
    spec:
      volumes:
      - name: ngx-conf-vol
        configMap:
          name: ngx-conf

      containers:
      - image: nginx:alpine
        name: nginx
        ports:
        - containerPort: 80

        volumeMounts:
        - mountPath: /etc/nginx/conf.d
          name: ngx-conf-vol

---

apiVersion: v1
kind: Service
metadata:
  name: ngx-svc

spec:
  selector:
    app: ngx-dep

  ports:
  - port: 80
    protocol: TCP
    targetPort: 80
```

比如使用 `sed` 命令，就可以快速得到 “red-svc”“green-svc”“bule-svc”“black-svc” 等4个Service。

```plain
sed 's/ngx/red/g'   backend.yml | kubectl apply -f -
sed 's/ngx/green/g' backend.yml | kubectl apply -f -
sed 's/ngx/blue/g'  backend.yml | kubectl apply -f -
sed 's/ngx/black/g' backend.yml | kubectl apply -f -
```

![图片](https://static001.geekbang.org/resource/image/ae/1d/ae54615a90c3e32b9cee98bdc61abe1d.png?wh=1054x426)

## 使用 Gateway API

完成以上的准备工作，下面就要开始实际使用Gateway API了。

让我们先从最简单的路由开始，只使用域名规则，创建一个HTTPRoute对象。

```plain
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: ngx-host-route
spec:
  parentRefs:
  - name: kong-gtw
  hostnames:
  - "gtw.test"
  rules:
  - backendRefs:
    - name: red-svc
      port: 80
```

HTTPRoute对象和Ingress很相似，但要简洁一些，具体的内部字段含义和用法可以参考文档或者使用 `kubectl explain`，我就不浪费时间细解释了。

这里使用 `parentRefs` 指定了路由使用的Gateway对象，用 `hostnames` 指定一个或多个域名，用 `backendRefs` 指定后端Service。合起来看，就是要求Gateway把域名 gtw.test 的流量都转发到 red-svc。

`kubectl apply` 创建这个路由对象后，可以用 `curl` 向 kong-gateway-proxy 发送请求来验证。

```plain
curl -i $(minikube ip):31198 -H 'host: gtw.test'
```

![图片](https://static001.geekbang.org/resource/image/a6/74/a6866b7fafff761be9b3bc2a0386ae74.png?wh=1474x904)

从截图里可以看到，因为我们指定了域名 gtw.test，匹配了路由规则，所以Gateway就把请求转发给了red-svc。

然后我们再来编写两个路由规则，分别使用路径匹配和头字段匹配，转发到green-svc和blue-svc。

```plain
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: ngx-path-route
spec:
  parentRefs:
  - name: kong-gtw
  hostnames:
  - "gtw.ops"

  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /hello
    backendRefs:
    - name: green-svc
      port: 80

---

apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: ngx-header-route
spec:
  parentRefs:
  - name: kong-gtw
  hostnames:
  - "gtw.dev"

  rules:
  - matches:
    - headers:
      - type: Exact
        name: area
        value: north
    backendRefs:
    - name: blue-svc
      port: 80
```

和第一个路由相比，它们多了 `matches` 字段，可以在里面详细指定或组合各种匹配条件，支持精确匹配、前缀匹配、正则匹配等等。

使用 `curl` 测试的效果如图：

```plain
curl -i $(minikube ip):31198/hello -H 'host: gtw.ops'
curl -i $(minikube ip):31198 -H 'host: gtw.dev' -H 'area: north'
```

![图片](https://static001.geekbang.org/resource/image/16/6a/161bc93c0a8cc931ac61916f9c34d56a.png?wh=1602x900)

![图片](https://static001.geekbang.org/resource/image/67/9e/678326c131b61a15be63669586b8209e.png?wh=1886x898)

Gateway API不仅支持路由转发，它还能够轻松实现流量拆分，比如常见的金丝雀部署和蓝绿部署，只需要调整 `backendRefs` 字段即可。

这个YAML定义了两个HTTPRoute。

```plain
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: ngx-canary-route
spec:
  parentRefs:
  - name: kong-gtw
  hostnames:
  - "canary.test"

  rules:

  - backendRefs:
    - name: blue-svc
      port: 80

  - matches:
    - headers:
      - name: traffic
        value: canary
    - path:
        type: Exact
        value: /login
    backendRefs:
    - name: green-svc
      port: 80

---

apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: ngx-blue-green-route
spec:
  parentRefs:
  - name: kong-gtw
  hostnames:
  - "blue-green.test"
  rules:

  - backendRefs:

    - name: blue-svc
      port: 80
      weight: 70

    - name: green-svc
      port: 80
      weight: 30
```

`ngx-canary-route` 里有两条规则，默认的后端服务是blue-svc，另一个加了匹配条件，只有访问特定的地址、使用特定的头字段才会转到后端服务green-svc。

`ngx-blue-green-route` 里也是两个后端服务，blue-svc和green-svc，但使用 weight 字段指定了不同的权重，这样在部署的时候就可以随意调节流量比例。

最后我们再来看一下Gateway API的filter特性，它可以对应到Kong Gateway的插件机制，实现对流量的附加处理，比如速率限制、改写数据、身份验证等等，不过目前标准的filter还不多，所以有的时候还是要依赖CRD资源定义Plugin。

下面的YAML添加了响应头和限速，其实这两个功能已经在之前讲Kong Ingress Controller的加餐里介绍过了，但现在改成了Gateway API，你可以对比看一下两者的区别。

```plain
apiVersion: configuration.konghq.com/v1
kind: KongPlugin
metadata:
  name: kong-rate-limiting-plugin

plugin: rate-limiting
config:
  minute: 2

---

apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: ngx-filter-route

  annotations:
    konghq.com/plugins: |
        kong-rate-limiting-plugin

spec:
  parentRefs:
  - name: kong-gtw
  hostnames:
  - "filter.test"

  rules:

  - backendRefs:
    - name: black-svc
      port: 80

    filters:
    - type: ResponseHeaderModifier
      responseHeaderModifier:
        add:
        - name: A-New-Header
          value: k8s-gtw-api
```

同样的，发送 `curl` 请求，就可以看到新增加的响应头和限速信息。

![图片](https://static001.geekbang.org/resource/image/91/07/9113b394a6284757faed5a98ecde8407.png?wh=1522x1144)

## 小结

好了，今天我介绍了Kubernetes的最新成果：Gateway API，它是Ingress的继任者，功能更强大、用法更灵活，也是Kubernetes社区今后的重点发展方向，值得我们投入精力去研究。

**简单小结一下今天的内容要点：**

1. Gateway API已经正式生产可用，目前包括3个成熟的对象，分别是Gateway Class、Gateway和HTTPRoute。
2. Gateway API只能运行在较新版本的Kubernetes上，而且不内置在Kubernetes里，需要使用YAML额外安装。
3. 大多数厂商都在某种程度上支持Gateway API，但只有少数达到了GA程度，这里使用的是Kong Ingress Controller。
4. 使用Gateway API可以任意配置各种路由规则，如域名、路径、头字段、查询参数、流量权重等，功能非常丰富。
5. Gateway API还支持filter功能，可以对流量做各种处理，但功能不如路由那么多。

另外再提醒一下，你可以在专栏的[GitHub 项目](https://github.com/chronolaw/k8s_study)里找到这节课的全部代码，还有更多的示例。

期待你的学习分享，我们留言区见！

![](https://static001.geekbang.org/resource/image/60/99/60d040daa2268f53df1d1c62386daf99.jpg?wh=1920x2635)
<div><strong>精选留言（5）</strong></div><ul>
<li><span>Geek_07ead6</span> 👍（1） 💬（1）<p>老师，不是说Gateway Class、Gateway 和 HTTPRoute是代替原来的ingress、ingressclass、ingressController这三个东西的吗？为啥上面又多了kong ingress controller的部署，kong ingress controller不只是原来ingressController的一个实现吗。没看懂新的里面GateWay和kong ingress controller的关系是啥，老师能加张图说一下Gateway Class、Gateway、HTTPRoute、kong ingress controller这四者的关系吗？</p>2024-04-11</li><br/><li><span>Geek_768d90</span> 👍（1） 💬（1）<p>感谢老师的坚持与付出！我认为学习K8S本身也要遵循CI&#47;CD：不断学习新知识，集成进自己的大脑；不断地在现网中实践，提供更加优化的交付方案。
我坚信这门课在极客时间一定会是一门精品课！</p>2023-12-02</li><br/><li><span>sgcls</span> 👍（0） 💬（1）<p>Gateway API 与 Ingress 类似的功能模块映射：
Gateway --- Ingress Controller # 流量控制器
Gateway Class --- Ingress Class # 流量控制器类别
HTTPRoute --- Ingress # 路由规则集

这里 HTTPRoute 与 Ingress 的 Yaml 不同点：
HTTPRoute 指定了 Controller（parentRefs.0.name -&gt; Gateway 对象），而
Ingress 指定的是 Controller Class （spec.ingressClassName -&gt; Ingress Class 对象）


为什么这里会不一致呢？有种割裂感。
是不是因为 Ingress Class 后面才引入的，所以在 Ingress 里明确设置 ingressClassName 指向 Ingress Class 以支持新特性呢..</p>2024-09-06</li><br/><li><span>六月</span> 👍（0） 💬（1）<p>看完本章马上去试了一下😂发现我的集群是1.23.17版本的。。。</p>2024-02-06</li><br/><li><span>Geek_479239</span> 👍（0） 💬（1）<p>居然读到了最新的文章，新公司在用k8s开发，正好学习实战下</p>2023-12-01</li><br/>
</ul>