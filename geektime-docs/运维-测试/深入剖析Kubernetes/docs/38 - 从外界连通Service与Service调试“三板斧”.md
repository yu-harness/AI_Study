你好，我是张磊。今天我和你分享的主题是：从外界连通Service与Service调试“三板斧”。

在上一篇文章中，我为你介绍了Service机制的工作原理。通过这些讲解，你应该能够明白这样一个事实：Service的访问信息在Kubernetes集群之外，其实是无效的。

这其实也容易理解：所谓Service的访问入口，其实就是每台宿主机上由kube-proxy生成的iptables规则，以及kube-dns生成的DNS记录。而一旦离开了这个集群，这些信息对用户来说，也就自然没有作用了。

所以，在使用Kubernetes的Service时，一个必须要面对和解决的问题就是：**如何从外部（Kubernetes集群之外），访问到Kubernetes里创建的Service？**

这里最常用的一种方式就是：NodePort。我来为你举个例子。

```
apiVersion: v1
kind: Service
metadata:
  name: my-nginx
  labels:
    run: my-nginx
spec:
  type: NodePort
  ports:
  - nodePort: 8080
    targetPort: 80
    protocol: TCP
    name: http
  - nodePort: 443
    protocol: TCP
    name: https
  selector:
    run: my-nginx
```

在这个Service的定义里，我们声明它的类型是，type=NodePort。然后，我在ports字段里声明了Service的8080端口代理Pod的80端口，Service的443端口代理Pod的443端口。

当然，如果你不显式地声明nodePort字段，Kubernetes就会为你分配随机的可用端口来设置代理。这个端口的范围默认是30000-32767，你可以通过kube-apiserver的–service-node-port-range参数来修改它。

那么这时候，要访问这个Service，你只需要访问：

```
<任何一台宿主机的IP地址>:8080
```

就可以访问到某一个被代理的Pod的80端口了。

而在理解了我在上一篇文章中讲解的Service的工作原理之后，NodePort模式也就非常容易理解了。显然，kube-proxy要做的，就是在每台宿主机上生成这样一条iptables规则：

```
-A KUBE-NODEPORTS -p tcp -m comment --comment "default/my-nginx: nodePort" -m tcp --dport 8080 -j KUBE-SVC-67RL4FN6JRUPOJYM
```

而我在上一篇文章中已经讲到，KUBE-SVC-67RL4FN6JRUPOJYM其实就是一组随机模式的iptables规则。所以接下来的流程，就跟ClusterIP模式完全一样了。

需要注意的是，在NodePort方式下，Kubernetes会在IP包离开宿主机发往目的Pod时，对这个IP包做一次SNAT操作，如下所示：

```
-A KUBE-POSTROUTING -m comment --comment "kubernetes service traffic requiring SNAT" -m mark --mark 0x4000/0x4000 -j MASQUERADE
```

可以看到，这条规则设置在POSTROUTING检查点，也就是说，它给即将离开这台主机的IP包，进行了一次SNAT操作，将这个IP包的源地址替换成了这台宿主机上的CNI网桥地址，或者宿主机本身的IP地址（如果CNI网桥不存在的话）。

当然，这个SNAT操作只需要对Service转发出来的IP包进行（否则普通的IP包就被影响了）。而iptables做这个判断的依据，就是查看该IP包是否有一个“0x4000”的“标志”。你应该还记得，这个标志正是在IP包被执行DNAT操作之前被打上去的。

可是，**为什么一定要对流出的包做SNAT操作呢？**

这里的原理其实很简单，如下所示：

```
           client
             \ ^
              \ \
               v \
   node 1 <--- node 2
    | ^   SNAT
    | |   --->
    v |
 endpoint
```

当一个外部的client通过node 2的地址访问一个Service的时候，node 2上的负载均衡规则，就可能把这个IP包转发给一个在node 1上的Pod。这里没有任何问题。

而当node 1上的这个Pod处理完请求之后，它就会按照这个IP包的源地址发出回复。

可是，如果没有做SNAT操作的话，这时候，被转发来的IP包的源地址就是client的IP地址。**所以此时，Pod就会直接将回复发给client。**对于client来说，它的请求明明发给了node 2，收到的回复却来自node 1，这个client很可能会报错。

所以，在上图中，当IP包离开node 2之后，它的源IP地址就会被SNAT改成node 2的CNI网桥地址或者node 2自己的地址。这样，Pod在处理完成之后就会先回复给node 2（而不是client），然后再由node 2发送给client。

当然，这也就意味着这个Pod只知道该IP包来自于node 2，而不是外部的client。对于Pod需要明确知道所有请求来源的场景来说，这是不可以的。

所以这时候，你就可以将Service的spec.externalTrafficPolicy字段设置为local，这就保证了所有Pod通过Service收到请求之后，一定可以看到真正的、外部client的源地址。

而这个机制的实现原理也非常简单：**这时候，一台宿主机上的iptables规则，会设置为只将IP包转发给运行在这台宿主机上的Pod**。所以这时候，Pod就可以直接使用源地址将回复包发出，不需要事先进行SNAT了。这个流程，如下所示：

```
       client
       ^ /   \
      / /     \
     / v       X
   node 1     node 2
    ^ |
    | |
    | v
 endpoint
```

当然，这也就意味着如果在一台宿主机上，没有任何一个被代理的Pod存在，比如上图中的node 2，那么你使用node 2的IP地址访问这个Service，就是无效的。此时，你的请求会直接被DROP掉。

从外部访问Service的第二种方式，适用于公有云上的Kubernetes服务。这时候，你可以指定一个LoadBalancer类型的Service，如下所示：

```
---
kind: Service
apiVersion: v1
metadata:
  name: example-service
spec:
  ports:
  - port: 8765
    targetPort: 9376
  selector:
    app: example
  type: LoadBalancer
```

在公有云提供的Kubernetes服务里，都使用了一个叫作CloudProvider的转接层，来跟公有云本身的 API进行对接。所以，在上述LoadBalancer类型的Service被提交后，Kubernetes就会调用CloudProvider在公有云上为你创建一个负载均衡服务，并且把被代理的Pod的IP地址配置给负载均衡服务做后端。

而第三种方式，是Kubernetes在1.7之后支持的一个新特性，叫作ExternalName。举个例子：

```
kind: Service
apiVersion: v1
metadata:
  name: my-service
spec:
  type: ExternalName
  externalName: my.database.example.com
```

在上述Service的YAML文件中，我指定了一个externalName=my.database.example.com的字段。而且你应该会注意到，这个YAML文件里不需要指定selector。

这时候，当你通过Service的DNS名字访问它的时候，比如访问：my-service.default.svc.cluster.local。那么，Kubernetes为你返回的就是`my.database.example.com`。所以说，ExternalName类型的Service，其实是在kube-dns里为你添加了一条CNAME记录。这时，访问my-service.default.svc.cluster.local就和访问my.database.example.com这个域名是一个效果了。

此外，Kubernetes的Service还允许你为Service分配公有IP地址，比如下面这个例子：

```
kind: Service
apiVersion: v1
metadata:
  name: my-service
spec:
  selector:
    app: MyApp
  ports:
  - name: http
    protocol: TCP
    port: 80
    targetPort: 9376
  externalIPs:
  - 80.11.12.10
```

在上述Service中，我为它指定的externalIPs=80.11.12.10，那么此时，你就可以通过访问80.11.12.10:80访问到被代理的Pod了。不过，在这里Kubernetes要求externalIPs必须是至少能够路由到一个Kubernetes的节点。你可以想一想这是为什么。

实际上，在理解了Kubernetes Service机制的工作原理之后，很多与Service相关的问题，其实都可以通过分析Service在宿主机上对应的iptables规则（或者IPVS配置）得到解决。

比如，当你的Service没办法通过DNS访问到的时候。你就需要区分到底是Service本身的配置问题，还是集群的DNS出了问题。一个行之有效的方法，就是检查Kubernetes自己的Master节点的Service DNS是否正常：

```
# 在一个Pod里执行
$ nslookup kubernetes.default
Server:    10.0.0.10
Address 1: 10.0.0.10 kube-dns.kube-system.svc.cluster.local

Name:      kubernetes.default
Address 1: 10.0.0.1 kubernetes.default.svc.cluster.local
```

如果上面访问kubernetes.default返回的值都有问题，那你就需要检查kube-dns的运行状态和日志了。否则的话，你应该去检查自己的 Service 定义是不是有问题。

而如果你的Service没办法通过ClusterIP访问到的时候，你首先应该检查的是这个Service是否有Endpoints：

```
$ kubectl get endpoints hostnames
NAME        ENDPOINTS
hostnames   10.244.0.5:9376,10.244.0.6:9376,10.244.0.7:9376
```

需要注意的是，如果你的Pod的readniessProbe没通过，它也不会出现在Endpoints列表里。

而如果Endpoints正常，那么你就需要确认kube-proxy是否在正确运行。在我们通过kubeadm部署的集群里，你应该看到kube-proxy输出的日志如下所示：

```
I1027 22:14:53.995134    5063 server.go:200] Running in resource-only container "/kube-proxy"
I1027 22:14:53.998163    5063 server.go:247] Using iptables Proxier.
I1027 22:14:53.999055    5063 server.go:255] Tearing down userspace rules. Errors here are acceptable.
I1027 22:14:54.038140    5063 proxier.go:352] Setting endpoints for "kube-system/kube-dns:dns-tcp" to [10.244.1.3:53]
I1027 22:14:54.038164    5063 proxier.go:352] Setting endpoints for "kube-system/kube-dns:dns" to [10.244.1.3:53]
I1027 22:14:54.038209    5063 proxier.go:352] Setting endpoints for "default/kubernetes:https" to [10.240.0.2:443]
I1027 22:14:54.038238    5063 proxier.go:429] Not syncing iptables until Services and Endpoints have been received from master
I1027 22:14:54.040048    5063 proxier.go:294] Adding new service "default/kubernetes:https" at 10.0.0.1:443/TCP
I1027 22:14:54.040154    5063 proxier.go:294] Adding new service "kube-system/kube-dns:dns" at 10.0.0.10:53/UDP
I1027 22:14:54.040223    5063 proxier.go:294] Adding new service "kube-system/kube-dns:dns-tcp" at 10.0.0.10:53/TCP
```

如果kube-proxy一切正常，你就应该仔细查看宿主机上的iptables了。而**一个iptables模式的Service对应的规则，我在上一篇以及这一篇文章里已经全部介绍到了，它们包括：**

1. KUBE-SERVICES或者KUBE-NODEPORTS规则对应的Service的入口链，这个规则应该与VIP和Service端口一一对应；
2. KUBE-SEP-(hash)规则对应的DNAT链，这些规则应该与Endpoints一一对应；
3. KUBE-SVC-(hash)规则对应的负载均衡链，这些规则的数目应该与 Endpoints 数目一致；
4. 如果是NodePort模式的话，还有POSTROUTING处的SNAT链。

通过查看这些链的数量、转发目的地址、端口、过滤条件等信息，你就能很容易发现一些异常的蛛丝马迹。

当然，**还有一种典型问题，就是Pod没办法通过Service访问到自己**。这往往就是因为kubelet的hairpin-mode没有被正确设置。关于Hairpin的原理我在前面已经介绍过，这里就不再赘述了。你只需要确保将kubelet的hairpin-mode设置为hairpin-veth或者promiscuous-bridge即可。

> 这里，你可以再回顾下第34篇文章[《Kubernetes网络模型与CNI网络插件》](https://time.geekbang.org/column/article/67351)中的相关内容。

其中，在hairpin-veth模式下，你应该能看到CNI 网桥对应的各个VETH设备，都将Hairpin模式设置为了1，如下所示：

```
$ for d in /sys/devices/virtual/net/cni0/brif/veth*/hairpin_mode; do echo "$d = $(cat $d)"; done
/sys/devices/virtual/net/cni0/brif/veth4bfbfe74/hairpin_mode = 1
/sys/devices/virtual/net/cni0/brif/vethfc2a18c5/hairpin_mode = 1
```

而如果是promiscuous-bridge模式的话，你应该看到CNI网桥的混杂模式（PROMISC）被开启，如下所示：

```
$ ifconfig cni0 |grep PROMISC
UP BROADCAST RUNNING PROMISC MULTICAST  MTU:1460  Metric:1
```

## 总结

在本篇文章中，我为你详细讲解了从外部访问Service的三种方式（NodePort、LoadBalancer 和 External Name）和具体的工作原理。然后，我还为你讲述了当Service出现故障的时候，如何根据它的工作原理，按照一定的思路去定位问题的可行之道。

通过上述讲解不难看出，所谓Service，其实就是Kubernetes为Pod分配的、固定的、基于iptables（或者IPVS）的访问入口。而这些访问入口代理的Pod信息，则来自于Etcd，由kube-proxy通过控制循环来维护。

并且，你可以看到，Kubernetes里面的Service和DNS机制，也都不具备强多租户能力。比如，在多租户情况下，每个租户应该拥有一套独立的Service规则（Service只应该看到和代理同一个租户下的Pod）。再比如DNS，在多租户情况下，每个租户应该拥有自己的kube-dns（kube-dns只应该为同一个租户下的Service和Pod创建DNS Entry）。

当然，在Kubernetes中，kube-proxy和kube-dns其实也是普通的插件而已。你完全可以根据自己的需求，实现符合自己预期的Service。

## 思考题

为什么Kubernetes要求externalIPs必须是至少能够路由到一个Kubernetes的节点？

感谢你的收听，欢迎你给我留言，也欢迎分享给更多的朋友一起阅读。
<div><strong>精选留言（15）</strong></div><ul>
<li><span>王天明</span> 👍（28） 💬（6）<p>终于算是清楚了，在nodePort模式下，关于端口的有三个参数，port, nodePort, targetPort。
如果如下定义，（请张老师指出是否有理解偏差）
spec:
  type: NodePort
  ports:
    - name: http
      port: 8080
      nodePort: 30080
      targetPort: 80
      protocol: TCP

则svc信息如下，（注意下面无targetPort信息，只是ClustorPort与NodePort，注意后者为Nodeport）
ingress-nginx   ingress-nginx                 NodePort    10.105.192.34    &lt;none&gt;        8080:30080&#47;TCP,8443:30443&#47;TCP   28m

则可访问的组合为
1. clusterIP + port: 10.105.192.34:8080
2. 内网IP&#47;公网ip + nodePort: 172.31.14.16:30080。（172.31.14.16我的aws局域网ip.）

30080为nodePort也可以在iptables-save中映证。
还有，就是port参数是必要指定的，nodePort即使是显式指定，也必须是在指定范围内。

（在三板斧中也问过张老师如何使用nodePort打通外网的问题，一并谢谢了）
</p>2018-11-24</li><br/><li><span>Flying</span> 👍（3） 💬（2）<p>老师，你好，使用NodePort类型的Service，会创建 -A KUBE-NODEPORTS 类的 iptables规则及 SNAT规则，如果kube-proxy使用的是 ipvs模式，也同样会创建这两个规则吗</p>2019-04-13</li><br/><li><span>王天明</span> 👍（1） 💬（3）<p>张老师，我在使用NodePort暴露外网访问一直不成功，无论是公网IP还是局域网IP但不成功，只能使用ClusterIP+NodePort访问。查看events也都正常，只几节课里使用NodePort都有类似的问题。是我理解哪里存在偏差吗？</p>2018-11-23</li><br/><li><span>我来也</span> 👍（107） 💬（9）<p>课后思考题:
为什么 Kubernetes 要求 externalIPs 必须是至少能够路由到一个 Kubernetes 的节点？

因为k8s只是在集群中的每个节点上创建了一个 externalIPs 与kube-ipvs0网卡的绑定关系.
若流量都无法路由到任意的一个k8s节点,那自然无法将流量转给具体的service.

--------------------------------
最近在这个externalIPs上面踩了一个坑.
在阿里云上提交了工单.第二天,应该是换了第3个售后工程师,才解决的.
给你们分享一下,哈哈!

事情是这样的:
我的k8s集群中有3个节点,假设分别是:
A: 192.168.1.1
B: 192.168.1.2
C: 192.168.1.3

症状是:
我在节点B&#47;C上,ssh 192.168.1.1, 最终都是登录到了本机,并未成功登录节点A.
但是节点A登录节点B&#47;C, 节点B和节点C互相登录都正常.
只有节点B和节点C上,登录节点A不成功.

就是因为我的某一个service服务就配置了 externalIPs, 配置的IP就是 192.168.1.1(A)
--------------------------------
那个售后工程师发现在节点B和C上有这么一条记录
$ ip addr
inet 192.168.1.1&#47;32 brd 192.168.1.1 scope global kube-ipvs0

那么在节点B和节点C上,访问192.168.1.1的流量,全都转到了kube-ipvs0.
最终这个流量都转到本机了,并未真的发送到远端真实的IP:192.168.1.1

我立马就意识到,我的service绑定了节点的IP.可能是这个导致的.
后来把externalIPs移除掉节点的IP后,该规则就不见了,节点B和节点C也可以正常访问节点A了.

--------------------------------
这个 externalIPs 其实可以填多个,且不要求本机就有对应的IP.
比如你可以填集群中根本就不存在的IP 172.17.0.1,
那么在k8s所有节点上,你都可以通过netstat -ant | grep 172.17.0.1 查看到,有监听该IP的端口.

</p>2020-04-11</li><br/><li><span>mazhen</span> 👍（30） 💬（8）<p>对ExternalName的作用没太理解。
访问my-service.default.svc.cluster.local被替换为my.database.example.com，这和我从外部访问到 Kubernetes 里的服务有什么关系？
感觉这更像是从Kubernetes内访问外部资源的方法。</p>2018-11-19</li><br/><li><span>虎虎❤️</span> 👍（8） 💬（1）<p>思考题 pod的external ip 应该是通过iptables进行配置。可能是一个虚拟ip，在网络中没有对应的设备。所以，必须有路由规则支持。否则客户端可能没办法找到该ip的路径，得到目的网络不可达的回复。</p>2018-11-21</li><br/><li><span>坤</span> 👍（5） 💬（0）<p>nodePort下必须要指定Service的port,我用的v1.14，可能检查的更严格了。</p>2019-11-06</li><br/><li><span>Geek_5baa01</span> 👍（4） 💬（0）<p>我一直再想 LoadBalancer 的问题，如果他是负载到 k8s node 上，那么我应该选择那些 node 做它的负载端点呢？这里被负载的 node 需要额外承担更多的网络流程，这对这些 node 带宽容量评估是个问题，另外还需要考虑 HA 问题，肯定要选择多个 node 作为负载端点，要怎么选择呢？</p>2021-07-02</li><br/><li><span>LEON</span> 👍（4） 💬（1）<p>在我们通过 kubeadm 部署的集群里，你应该看到 kube-proxy 输出的日志如下所示：—输出日志的命令是什么？</p>2018-11-19</li><br/><li><span>我来也</span> 👍（3） 💬（0）<p>关于源IP的问题，简易看看这篇官方文档：

文档 教程 Services 使用 Source IP
https:&#47;&#47;kubernetes.io&#47;zh&#47;docs&#47;tutorials&#47;services&#47;source-ip&#47;</p>2020-10-11</li><br/><li><span>Len</span> 👍（3） 💬（1）<p>因为 kubernetes 维护着 externalIPs IP + PORT 到具体服务的 endpoints 路由规则。</p>2018-11-21</li><br/><li><span>勤劳的小胖子-libo</span> 👍（2） 💬（0）<p>写了一个简单的nodeport,可以访问上一节的hostname deployment.
apiVersion: v1
kind: Service
metadata:
  name: hostnames
  labels:
    app: hostnames
spec:
  type: NodePort
  selector:
    app: hostnames
  ports:
  - nodePort: 30225
    port: 80
    targetPort: 9376
    protocol: TCP
    name: http


通过curl &lt;任意Node&gt;:30225可以访问。
vagrant@kubeadm1:~&#47;37ServiceDns$ curl 192.168.0.24:30225
hostnames-84985c9fdd-sgwpp

另外感觉我这边的输出关于kube-proxy:
vagrant@kubeadm1:~&#47;37ServiceDns$ kubectl logs -n kube-system kube-proxy-pscvh
W1122 10:13:18.794590       1 server_others.go:295] Flag proxy-mode=&quot;&quot; unknown, assuming iptables proxy
I1122 10:13:18.817014       1 server_others.go:148] Using iptables Proxier.
I1122 10:13:18.817394       1 server_others.go:178] Tearing down inactive rules.
E1122 10:13:18.874465       1 proxier.go:532] Error removing iptables rules in ipvs proxier: error deleting chain &quot;KUBE-MARK-MASQ&quot;: exit status 1: iptables: Too many links.
I1122 10:13:18.894045       1 server.go:447] Version: v1.12.2

后面信息都是正常的。不知道上面这些信息可以ignore吗？</p>2018-11-22</li><br/><li><span>LEON</span> 👍（2） 💬（1）<p>而如果你的 Service 没办法通过 ClusterIP 访问到的时候，你首先应该检查的是这个 Service 是否有 Endpoints：———请问老师service ip与cluster ip有什么区别？为什么这块不直接是service ip?</p>2018-11-19</li><br/><li><span>yuling朱</span> 👍（1） 💬（0）<p>&quot;在 NodePort 方式下，Kubernetes 会在 IP 包离开宿主机发往目的 Pod 时，对这个 IP 包做一次 SNAT 操作&quot;,有个疑问，这里表述是不是有点不准确，在ClusterIP下就不会做SNAT了吗？
只要转发到其他节点就会做SNAT。</p>2022-09-14</li><br/><li><span>陈斯佳</span> 👍（1） 💬（0）<p>第三十八课:从外界连通你好Service与Service调试“三板斧”
Service的类型分为ClusterIP,NodePort, ExternalIP,ExternalName.

当Service没办法通过DNS访问到的时候，可以先检查Master节点的Service DNS是否可以访问到:
# 在一个Pod里执行
$ nslookup kubernetes.default

如果有问题，就去看kube-dns日志，否则，就要看Service本身定义是否有问题


如果Service没办法通过ClusterIP访问，应该先检查这个Service是否有Endpoint:
$ kubectl get endpoints hostnames

如果Endpoint正确，就要检查kube-proxy是否正确运行，如果正常，就要检查一下iptables

如果Pod没办法访问到自己，就要看看是不是kubelet 的 hairpin-mode 没有被正确设置。你只需要确保将 kubelet 的 hairpin-mode 设置为 hairpin-veth 或者 promiscuous-bridge 即可。

所谓的Service,其实就是k8s为Pod分配的、固定的、基于iptables的访问入口。
</p>2021-10-30</li><br/>
</ul>