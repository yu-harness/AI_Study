你好，我是雪飞。

上节课我介绍了 Service，它主要负责集群的服务发现和负载均衡。对于来自集群外部的访问，可以使用 NodePort 或者 LoadBalance 类型的 Service，K8s 会自动绑定集群节点的端口号，通过 “&lt;节点 IP&gt;:&lt;节点端口&gt;” 来访问 Service，从而最终访问到 Service 代理的应用 Pod。但是在微服务架构中，由于集群中通常运行着多个需要暴露到外部访问的应用，如果每个应用都通过这种 Service 绑定节点端口的方式访问，可能会导致节点端口管理变得复杂且存在安全隐患。

此外，Service 是通过 IP 地址和端口来提供网络访问，这是一种四层的负载均衡，我们在实际开发项目中，更多时候是通过 URL 地址来访问应用，这需要七层的负载均衡，例如我们常用的 Nginx Web 服务就可以使用域名来代理到不同的网络应用。

> 负载均衡可以分为四层和七层，分别对应 OSI 模型的传输层和应用层。  
> 四层负载均衡工作在传输层，负责处理 TCP/UDP 协议。根据源 IP、源端口号以及目的IP和目的端口号来转发流量到应用服务器。而七层负载均衡工作在应用层，可以根据 HTTP、HTTPS、DNS 等应用层协议来进行负载均衡，还可以基于 URL、浏览器类型、语言等内容来制定负载均衡策略。

所以为了解决 Service 处理集群外部访问请求的局限性，K8s 提供了 Ingress 资源对象。Ingress 是一种七层的负载均衡，可以实现高级路由策略，从而更高效地管理集群外部流量。

## 认识 Ingress

Ingress 通过定义一系列的路由规则，允许你将集群外部的 HTTP/HTTPS 请求分配到集群内不同的 Service 上。所以 Ingress 的机制相当于是在 Service 上又加了一层规则，它获取到用户访问的域名和路径，然后根据规则把访问请求转发到了对应的 Service 上，然后再由 Service 把流量转发到具体的应用 Pod。

![图片](https://static001.geekbang.org/resource/image/67/e0/671d322bc3547f0a0f6d0b1523b6bce0.jpg?wh=1177x721)

Ingress 由三个核心组件组成，Ingress、Ingress Controller 和 Ingress Class。

Ingress 是一组路由规则（Rules）。每个规则定义了如何处理进入集群的访问请求，包含主机域名（Host）和路径列表（Path）。路径列表定义了基于 URL 路径的请求分发规则，每个路径都关联一个后端服务（Backend），后端服务就是实际处理请求的 Service，包含了 Service 的名称（ServiceName）和端口（ServicePort）。Ingress 本身并不直接处理流量，它的功能需要依赖于 Ingress Controller。

Ingress Controller 是负责实现 Ingress 规则的组件，它负责监听 Ingress 的变化，并确保路由规则被正确应用。K8s 官方并没有实现自己的 Ingress Controller，而是定义了 Ingress Controller 的实现标准，很多第三方公司都基于标准实现了自己的 Ingress Controller，目前我们最常用的就是大名鼎鼎的 Nginx Ingress Controller，你也可以使用其他公司实现的 [Ingress Controller](https://kubernetes.io/zh-cn/docs/concepts/services-networking/ingress-controllers/)。

Ingress Class 是夹在 Ingress 和 Ingress Controller 中间的一个层级，解除了 Ingress 和 Ingress Controller 的强绑定关系。在 Ingress 中指定要使用的 Ingress Class，而在 Ingress Class 中可以指定要使用的 Ingress Controller 以及设置一些额外的配置。

总之，Ingress 类似法律条文，而 Ingress Controller 则是法官。当集群外部请求到达 Ingress Controller 时，Ingress Controller 会根据 Ingress 规则中定义的主机域名和路径将请求发送到对应的 Service。

## 安装 Ingress Controller

由于 K8s 集群中没有默认安装 Ingress Controller。我们需要先在集群中部署 Ingress Controller，这里我选择常用的 Nginx Ingress Controller。（参考[官方文档](https://kubernetes.github.io/ingress-nginx/deploy/#quick-start)）

Nginx Ingress Controller 组件也是部署在 K8s 集群中，我们可以直接用官网提供的 YAML 文件部署。但是国内无法直接下载镜像，所以我们需要先下载 YAML 文件，找到对应镜像位置，然后替换成国内阿里云的镜像库。

```bash
# 通过 wget 命令下载 Nginx Ingress Controller 部署文件
[root@k8s-master ~]# wget https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.10.1/deploy/static/provider/cloud/deploy.yaml
...
HTTP request sent, awaiting response... 200 OK
Length: 16136 (16K) [text/plain]
Saving to: ‘deploy.yaml’
100%[============================================================================================>] 16,136      15.6KB/s   in 1.0s   
2024-06-23 19:11:45 (15.6 KB/s) - ‘deploy.yaml’ saved [16136/16136]
```

通过 vi 编辑器编辑 YAML 文件（deploy.yaml），把 registry.k8s.io 的镜像替换成如下阿里云镜像库的镜像：

- registry.cn-hangzhou.aliyuncs.com/google\_containers/nginx-ingress-controller:v1.10.1
- registry.cn-hangzhou.aliyuncs.com/google\_containers/kube-webhook-certgen:v1.4.1

```bash
[root@k8s-master ~]# vi deploy.yaml 
...
446      # image: registry.k8s.io/ingress-nginx/controller:v1.10.1@sha256:e24f39d3eed6bcc239a56f20098878845f62baa34b9f2be2fd2c38ce9fb0f29e
447      image:registry.cn-hangzhou.aliyuncs.com/google_containers/nginx-ingress-controller:v1.10.1
...
548      # image: registry.k8s.io/ingress-nginx/kube-webhook-certgen:v1.4.1@sha256:36d05b4077fb8e3d13663702fa337f124675ba8667cbd949c03a8e8ea6fa4366
549      image: registry.cn-hangzhou.aliyuncs.com/google_containers/kube-webhook-certgen:v1.4.1
...
602      # image: registry.k8s.io/ingress-nginx/kube-webhook-certgen:v1.4.1@sha256:36d05b4077fb8e3d13663702fa337f124675ba8667cbd949c03a8e8ea6fa4366
603      image: registry.cn-hangzhou.aliyuncs.com/google_containers/kube-webhook-certgen:v1.4.1
...
```

保存后，使用 “kubectl apply” 命令部署，等 Nginx Ingress Controller 部署完成，查看 Ingress Controller 的 Deployment 和 Service，注意需要加上 ingress-nginx 命名空间，最后再查看一下 Ingress Class。

```bash
[root@k8s-master ~]# kubectl apply -f deploy.yaml
[root@k8s-master ~]# kubectl get deployment,svc -n ingress-nginx
NAME                                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/ingress-nginx-controller   1/1     1            1           11m

NAME                                         TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)                      AGE
service/ingress-nginx-controller             LoadBalancer   10.106.241.178   <pending>     80:31445/TCP,443:30181/TCP   11m
service/ingress-nginx-controller-admission   ClusterIP      10.100.108.214   <none>        443/TCP                      11m
[root@k8s-master ~]# kubectl get ingressclass  # 查看 Ingress Class
NAME    CONTROLLER             PARAMETERS   AGE
nginx   k8s.io/ingress-nginx   <none>       11m
```

可以看到 Nginx Ingress Controller 是通过 Deployment 来部署的，同时也创建了一个 Service 和一个 Ingress Class，这个 Ingress Class 指向 Nginx（Nginx Ingress Controller 部署的控制器名称）。下面我们就可以在创建 Ingress 规则时使用这个 Ingress Class。

## 创建 Ingress 规则

使用 Ingress 规则的前提是已经部署好了应用的 Deployment 和其中的 Pod ，同时也对 Pod 创建了 Service 网络访问代理。我们上节课已经搭建好了相关环境，所以下面的例子是创建一个 Ingress 规则，将集群外部访问 myapp.address.com 域名以及访问路径为 “/” 的请求都转发到之前创建好的名称为 my-service 的 Service 中，然后再经过 my-service 转发到具体的应用 Pod 中去处理。

准备好了 Ingress Controller 和 Ingress Class，就可以开始创建 Ingress 规则了。使用 kubectl 命令或 YAML 文件创建 Ingress 规则。

**使用 kubectl 命令**

使用 “kubectl create ingress” 命令创建一条名称为 “my-ingress” 的规则。

```bash
[root@k8s-master ~]# kubectl create ingress my-ingress --class=nginx --rule="myapp.address.com/*=my-service:80"
ingress.networking.k8s.io/my-ingress created
```

- **–class**：指定了要使用的 Ingress Class 为 nginx。
- **–rule**：指定了具体的路由规则，“myapp.address.com” 是主机域名，/* 是匹配路径，my-service 是该规则转发到后端的 Service 名称，80 是 Service 的端口号。

通过命令可以快速生成一条简单的 Ingress 规则，但是在实际项目中，Ingress 规则通常比较复杂，因此我们通常使用 YAML 文件来配置 Ingress 规则。

Ingress 的 YAML 文件（my-ingress.yaml）如下：

```yaml
# my-ingress.yaml 
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-ingress
  namespace: default
spec:
  ingressClassName: nginx
  rules:
  - host: myapp.address.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-service
            port:
              number: 80
```

- **host：**指定主机域名，可以是精确匹配（例如 “myapp.address.com”）或者使用通配符来匹配（例如 “\*.address.com”）。
- **path：**指定访问请求的路径。
- **pathType：**路径匹配方式。有三种类型：ImplementationSpecific（取决于 IngressClass）、Exact（精确匹配 URL 路径，区分大小写）和 Prefix（前缀匹配，区分大小写）。通常我们使用 Prefix 类型。
- **backend：**转发到的后端 Service，也就是部署好的应用的代理 Service。

使用 “kubectl apply” 命令部署 Ingress，部署成功后可以查看 Ingress 信息。

```yaml
[root@k8s-master ~]# kubectl apply -f my-ingress.yaml
[root@k8s-master ~]# kubectl get ingress
NAME         CLASS   HOSTS               ADDRESS   PORTS   AGE
my-ingress   nginx   myapp.address.com             80      7m43s
```

现在路由转发规则也创建好了，我们思考一下如何通过域名和路径访问应用。

## 访问 Ingress Controller

你已经知道在 Ingress 机制中，集群外部的访问请求是由 Ingress Controller 按照规则转发到不同 Service的，所以要访问应用 Pod，就需要访问到 Ingress Controller。而 Ingress Controller 是由部署到 K8s 的 Deployment（包含处理流量转发的 Pod）和 Service 组成的。因此，我们实际上要访问这个 Service，从而访问到 Deployment 中的处理流量转发的 Pod。

![图片](https://static001.geekbang.org/resource/image/a4/af/a4688551d4446a07459048306c5cf6af.jpg?wh=472x489)

根据以上原理，我们通过 “kubectl get svc” 命令查看 Ingress Controller 的 Service。

**注意：**命名空间为 “ingress-nginx”。

```bash
[root@k8s-master ~]# kubectl get svc ingress-nginx-controller -n ingress-nginx
NAME                       TYPE           CLUSTER-IP      EXTERNAL-IP   PORT(S)                      AGE
ingress-nginx-controller   LoadBalancer   10.106.241.178  <pending>     80:31445/TCP,443:30181/TCP   2d1h
```

从结果中我们看到名称为 ingress-nginx-controller 的 Service，它的类型是 LoadBalancer。

如果集群可以使用外部的第三方负载均衡器，那么这个 Service 可以分配到一个外部 IP（EXTERNAL-IP），我们就可以**把域名解析到这个 IP，然后直接通过“&lt;域名&gt;&lt;路径&gt;”方式访问 Service，从而访问到最终的应用 Pod**。

如果没有外部 IP（EXTERNAL-IP），我们也可以通过 NodePort 的方式访问 Service。 LoadBalancer 类型的 Service 也会自动分配一个 NodePort 端口，我们可以通过这个节点端口来访问 Service。但是，这里访问 Service 不能使用 “&lt;节点 IP&gt;:&lt;节点端口&gt;” 的方式，因为 Ingress 需要根据访问请求的域名和路径来转发流量，所以我们**需要把域名解析到任意节点的 IP，然后使用“&lt;域名&gt;:&lt;节点端口&gt;&lt;路径&gt;”的方式访问 Service，从而访问到最终的应用 Pod**。这种 NodePort 访问方式虽然简单，但是缺点就是访问时还需要输入节点端口号。

![图片](https://static001.geekbang.org/resource/image/96/6d/9678e175f030c24cae59b2035e94b76d.jpg?wh=520x538)

最后，如果你无法配置互联网上的域名解析，只是想在本地机器上测试规则，我们可以在自己的本地机器上配置一条域名解析。对于 Mac 系统用户，可以打开终端，编辑 “/etc/hosts” 文件，在文件末尾添加 “IP 域名”的映射规则。这样，在本地机器的浏览器中输入域名访问时，系统会优先按照 “/etc/hosts” 文件中的配置来解析 IP，从而将请求转发到集群中的相应节点上。其他系统的配置方法可以参考网上相关文档。

```yaml
[steve@bogon ~]# vi /etc/hosts  # 在文件中插入域名解析规则条目
...
49.xxx.xxx.187  myapp.address.com
# 使用你的集群中任意节点的公网 IP，以及你在 Ingress 中配置的 Host 域名
```

然后你在本地机器的浏览器中输入域名和端口号，尝试一下，终于出现了我们部署在 Deployment 中的应用 Nginx，也就意味着 Ingress 路由规则生效了。

![图片](https://static001.geekbang.org/resource/image/26/16/2665ab54407a698c9c2d4db50cbcd416.jpg?wh=1399x547)

## 配置 HTTPS

现在，一套完整的 Web 应用已经部署成功了，这套部署方案中包含了 Deployment、Service 和 Ingress，最终通过 URL 访问到了我们的应用，是不是很有成就感？先别着急，我们还有一个重要的问题，那就是 HTTPS 请求。在当前的网络环境下，大部分网络访问请求都使用 HTTPS 协议，因此我们需要在 Ingress 中配置一下 HTTPS 协议。

> HTTPS 是一种安全可靠的网络通信协议，它通过 SSL/TLS 证书实现数据加密和服务提供方身份验证。证书由权威的证书颁发机构（CA）签发。当浏览器通过 HTTPS 访问服务提供方时，它会检查服务方的证书，确保证书有效。一旦验证通过，浏览器和服务方就会使用证书中的密钥建立加密连接，从而安全地传输数据。

Ingress 支持处理集群外部的 HTTPS 请求。你可以为Ingress 配置一个 Secret 来提供 SSL/TLS 的证书和私钥。用户通过 HTTPS 请求时，Ingress 会返回证书，浏览器验证通过后，就可以使用证书加密请求数据。请求到达 Ingress Controller 后，会被解密并转发到后端的 Service。

下面我就带你来动手配置 HTTPS。

### 第一步：生成证书文件

首先，我们需要获取证书文件，该文件可以由权威机构颁发，或者使用 OpenSSL 自签名证书。如果购买使用权威机构颁发的证书，可以在它们网站里下载服务器类型是 “Nginx” 的证书文件。如果想自签名证书，可以安装 OpenSSL 工具，使用该工具生成证书。

这里我简单介绍如何在 Linux 系统上生成自签名证书文件。你可以把我用的域名 “myapp.address.com” 替换成你的域名。

在管理节点上执行以下命令来生成一个自签名证书。

```bash
# 1、安装 OpenSSL 工具
yum install -y openssl openssl-devel

# 2、生成一个私钥文件
openssl genpkey -algorithm RSA -out myapp.address.com.key

# 3、成证书签名请求（CSR）
openssl req -new -key myapp.address.com.key -out mycsr.csr
# 你将被提示输入国家、地区、组织名称、组织单位、通用名称（通常是你的域名或服务器名称）等信息
# Country Name (2 letter code) [XX]: 国家简称，中国是 CN
# State or Province Name (full name) []: 省份拼音
# Locality Name (eg, city) [Default City]: 城市拼音
# Organization Name (eg, company) [Default Company Ltd]: 公司英文名
# Organizational Unit Name (eg, section) []: 部门英文名
# Common Name (eg, your name or your server's hostname) []: 域名
# Email Address []: 邮箱
# extra 额外信息不用填写

# 4、使用私钥和 CSR 生成自签名证书
openssl x509 -req -days 365 -in mycsr.csr -signkey myapp.address.com.key -out certificate.crt
# 这个命令会生成一个名为 certificate.crt 的自签名证书，有效期为 365 天

# 5、验证证书的内容
openssl x509 -text -noout -in certificate.crt

# 6、实际部署时，需要将私钥和证书合并到一个文件中
cat myapp.address.com.key certificate.crt > myapp.address.com.pem
```

最终生成的文件分别是 “myapp.address.com.key” 和 “myapp.address.com.pem”。

### 第二步：部署证书 Secret

将私钥和证书文件通过 Secret 部署。之前介绍 Secret 的时候说过它的三种类型：docker-registry、generic 和 tls。这次我们将使用 tls 类型。

通过 “kubectl create” 命令创建 tls 类型的 Secret，使用证书和私钥文件的路径作为参数。

```bash
kubectl create secret tls myapp-address-com-secret --cert=./myapp.address.com.pem --key=./myapp.address.com.key
```

- **–cert：**证书文件，一般后缀名为 “.pem” 或 “.crt”，此参数需要填写证书文件的路径（绝对路径或相对路径）。
- **–key：**私钥文件，一般后缀名为 “.key”，此参数需要填写私钥文件的路径（绝对路径或相对路径）。

执行命令后，会在 K8s 集群里创建一个证书 Secret。

### 第三步：在 Ingress 的 YAML 文件中增加 tls 配置

在上面的 Ingress 规则的 YAML 文件（my-ingress.yaml）中加入 tls 属性。

```yaml
# my-ingress.yaml
...
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - myapp.address.com
    secretName: myapp-address-com-secret
...
```

重新保存 YAML 文件，部署成功后，我们再来查看一下 Ingress Controller 的 Service。

```bash
[root@k8s-master ~]# kubectl apply -f my-ingress.yaml
ingress.networking.k8s.io/my-ingress configured
[root@k8s-master ~]# kubectl get svc ingress-nginx-controller -n ingress-nginx
NAME                       TYPE           CLUSTER-IP       EXTERNAL-IP   PORT(S)                      AGE
ingress-nginx-controller   LoadBalancer   10.106.241.178   <pending>     80:31445/TCP,443:30181/TCP   2d2h
```

这时，我们要注意，**HTTPS 协议访问请求默认是 443 端口，也就是要访问 Ingress Controller 中的 Service 的 443 端口，这个端口被映射到了节点的 30181 端口（443:30181/TCP），**此时就可以通过本地机器的浏览器访问 [https://myapp.address.com:30181/](https://myapp.address.com:30181/) URL 地址。我们就可以看到返回的 Nginx 欢迎页面了（因为我们使用了自签名证书，其实并不安全，所以浏览器通常都会有个安全提示，在提示页面中的高级按钮中点击继续就可以看到欢迎网页了）。

![图片](https://static001.geekbang.org/resource/image/98/b5/98a9c3a5b2ca04046df75d333a6412b5.jpg?wh=1916x678)

## **小结**

今天，我介绍了 Ingress 资源对象在 K8s 集群中的作用和使用方法。

Ingress 通过定义一系列的路由规则，允许你将集群外部的 HTTP/HTTPS 请求转发到集群内不同的 Service 上。它获取到用户访问的域名和路径，然后根据规则把访问请求转发到了对应的 Service 上，然后再由 Service 把流量转发到具体的应用 Pod。Ingress 路由机制的主要组成包括 Ingress、Ingress Controller 和 Ingress Class。Ingress 定义了访问路由转发规则，Ingress Controller 负责根据这些规则将外部访问请求转发到后端的 Service，而 Ingress Class 则用于解耦 Ingress 和 Ingress Controller。

K8s 官方并没有实现自己的 Ingress Controller，所以我带你一步步安装了最常用的 Nginx Ingress Controller，安装之后，会自动在 K8s 集群中部署 Ingress Controller 的 Deployment 和 Service，同时生成一个对应的 Ingress Class。

之后，你可以通过 kubectl 命令或者 YAML 文件创建 Ingress 规则。每个规则定义了如何处理进入集群的访问请求，包含主机名（Host）和路径列表（Path），每个路径又关联一个后端服务（Backend），后端服务就是实际处理访问请求的 Service。

部署好 Ingress 规则，就可以通过 Ingress Controller 的 Service 来访问。这是一个 LoadBalance 类型的 Service，如果集群支持 LoadBalance 类型，你可以把域名解析到外部 IP（EXTERNAL-IP），然后通过“&lt;域名&gt;&lt;路径&gt;”访问。如果不支持 LoadBalance 类型，你可以通过 NodePort 的方式来访问，把域名解析到任意节点 IP，然后通过“&lt;域名&gt;:&lt;节点端口&gt;&lt;路径&gt;”访问。

最后，介绍了如何在 Ingress 上配置 HTTPS 访问，包括生成证书文件、部署证书 Secret 以及在 Ingress 的 YAML 文件中增加 tls 属性等步骤。

## 思考题

这就是今天的全部内容，Ingress 是 K8s 中又一个非常重要的网络资源对象，在 CKA 中也会考到相关的知识点，我给你留一道思考题。

配置 HTTPS 时，需要使用 443 端口，那么在 Ingress 规则对应的 Service 中是否需要配置 443 端口，同时在 Deployment 的应用 Pod 中，容器 Nginx 是否也需要暴露 443 端口？

我希望你能实际动手实验一下，相信经过动手实践，会让你对知识的理解更加深刻。
<div><strong>精选留言（4）</strong></div><ul>
<li><span>Michael闫· ᴥ ·</span> 👍（0） 💬（2）<p>老师，安装ingress的时候有一个报错，如下：
error: failed to create ingress: Internal error occurred: failed calling webhook &quot;validate.nginx.ingress.kubernetes.io&quot;: failed to call webhook: Post &quot;https:&#47;&#47;ingress-nginx-controller-admission.ingress-nginx.svc:443&#47;networking&#47;v1&#47;ingresses?timeout=10s&quot;: context deadline exceeded
</p>2024-07-28</li><br/><li><span>Michael闫· ᴥ ·</span> 👍（0） 💬（2）<p>求教一下老师：
我用service的NodePort方式，公网+ip 可以正常登录nginx，但是在ingress这部分用域名+端口就不成功，想咨询下您这里的域名+端口里面的端口指的是哪个端口啊，我下面给您复制下我的代码：
[root@k8s-master ~]# kubectl get deployment,svc -n ingress-nginx
NAME                                       READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps&#47;ingress-nginx-controller   1&#47;1     1            1           41m

NAME                                         TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)                      AGE
service&#47;ingress-nginx-controller             LoadBalancer   10.103.29.35   &lt;pending&gt;     80:30257&#47;TCP,443:32431&#47;TCP   41m
service&#47;ingress-nginx-controller-admission   ClusterIP      10.106.98.61   &lt;none&gt;        443&#47;TCP 

[root@k8s-master ~]# kubectl get svc
NAME         TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
kubernetes   ClusterIP   10.96.0.1     &lt;none&gt;        443&#47;TCP        67m
my-service   NodePort    10.108.8.79   &lt;none&gt;        80:30001&#47;TCP   35m

运行service：http:&#47;&#47;120.27.143.120:30001&#47;   成功
运行ingress：http:&#47;&#47;myapp.address.com:32431&#47;   失败</p>2024-07-27</li><br/><li><span>Y</span> 👍（0） 💬（1）<p>用命令可以正常访问Nginx，用my-ingress.yaml文件不行(访问308，404)。my-ingress.yaml里面不知道哪个地方有问题。</p>2024-07-23</li><br/><li><span>抱紧我的小鲤鱼</span> 👍（0） 💬（1）<p>ingress controller 的service 需要暴露 443，用来处理https请求
deployment 的pod 层面并不需要暴露 443，加解密其实在ingress 层处理，pod只需要叫监听内部配置的端口，然后将service 的流量转发到这个端口</p>2024-07-19</li><br/>
</ul>