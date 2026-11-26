你好，我是张磊。今天我和你分享的主题是：深入理解StatefulSet之存储状态。

在上一篇文章中，我和你分享了StatefulSet如何保证应用实例的拓扑状态，在Pod删除和再创建的过程中保持稳定。

而在今天这篇文章中，我将继续为你解读StatefulSet对存储状态的管理机制。这个机制，主要使用的是一个叫作Persistent Volume Claim的功能。

在前面介绍Pod的时候，我曾提到过，要在一个Pod里声明Volume，只要在Pod里加上spec.volumes字段即可。然后，你就可以在这个字段里定义一个具体类型的Volume了，比如：hostPath。

可是，你有没有想过这样一个场景：**如果你并不知道有哪些Volume类型可以用，要怎么办呢**？

更具体地说，作为一个应用开发者，我可能对持久化存储项目（比如Ceph、GlusterFS等）一窍不通，也不知道公司的Kubernetes集群里到底是怎么搭建出来的，我也自然不会编写它们对应的Volume定义文件。

所谓“术业有专攻”，这些关于Volume的管理和远程持久化存储的知识，不仅超越了开发者的知识储备，还会有暴露公司基础设施秘密的风险。

比如，下面这个例子，就是一个声明了Ceph RBD类型Volume的Pod：

```
apiVersion: v1
kind: Pod
metadata:
  name: rbd
spec:
  containers:
    - image: kubernetes/pause
      name: rbd-rw
      volumeMounts:
      - name: rbdpd
        mountPath: /mnt/rbd
  volumes:
    - name: rbdpd
      rbd:
        monitors:
        - '10.16.154.78:6789'
        - '10.16.154.82:6789'
        - '10.16.154.83:6789'
        pool: kube
        image: foo
        fsType: ext4
        readOnly: true
        user: admin
        keyring: /etc/ceph/keyring
        imageformat: "2"
        imagefeatures: "layering"
```

其一，如果不懂得Ceph RBD的使用方法，那么这个Pod里Volumes字段，你十有八九也完全看不懂。其二，这个Ceph RBD对应的存储服务器的地址、用户名、授权文件的位置，也都被轻易地暴露给了全公司的所有开发人员，这是一个典型的信息被“过度暴露”的例子。

这也是为什么，在后来的演化中，**Kubernetes项目引入了一组叫作Persistent Volume Claim（PVC）和Persistent Volume（PV）的API对象，大大降低了用户声明和使用持久化Volume的门槛。**

举个例子，有了PVC之后，一个开发人员想要使用一个Volume，只需要简单的两步即可。

**第一步：定义一个PVC，声明想要的Volume的属性：**

```
kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: pv-claim
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

可以看到，在这个PVC对象里，不需要任何关于Volume细节的字段，只有描述性的属性和定义。比如，storage: 1Gi，表示我想要的Volume大小至少是1 GiB；accessModes: ReadWriteOnce，表示这个Volume的挂载方式是可读写，并且只能被挂载在一个节点上而非被多个节点共享。

> 备注：关于哪种类型的Volume支持哪种类型的AccessMode，你可以查看Kubernetes项目官方文档中的[详细列表](https://kubernetes.io/docs/concepts/storage/persistent-volumes/#access-modes)。

**第二步：在应用的Pod中，声明使用这个PVC：**

```
apiVersion: v1
kind: Pod
metadata:
  name: pv-pod
spec:
  containers:
    - name: pv-container
      image: nginx
      ports:
        - containerPort: 80
          name: "http-server"
      volumeMounts:
        - mountPath: "/usr/share/nginx/html"
          name: pv-storage
  volumes:
    - name: pv-storage
      persistentVolumeClaim:
        claimName: pv-claim
```

可以看到，在这个Pod的Volumes定义中，我们只需要声明它的类型是persistentVolumeClaim，然后指定PVC的名字，而完全不必关心Volume本身的定义。

这时候，只要我们创建这个PVC对象，Kubernetes就会自动为它绑定一个符合条件的Volume。可是，这些符合条件的Volume又是从哪里来的呢？

答案是，它们来自于由运维人员维护的PV（Persistent Volume）对象。接下来，我们一起看一个常见的PV对象的YAML文件：

```
kind: PersistentVolume
apiVersion: v1
metadata:
  name: pv-volume
  labels:
    type: local
spec:
  capacity:
    storage: 10Gi
  accessModes:
    - ReadWriteOnce
  rbd:
    monitors:
    # 使用 kubectl get pods -n rook-ceph 查看 rook-ceph-mon- 开头的 POD IP 即可得下面的列表
    - '10.16.154.78:6789'
    - '10.16.154.82:6789'
    - '10.16.154.83:6789'
    pool: kube
    image: foo
    fsType: ext4
    readOnly: true
    user: admin
    keyring: /etc/ceph/keyring
```

可以看到，这个PV对象的spec.rbd字段，正是我们前面介绍过的Ceph RBD Volume的详细定义。而且，它还声明了这个PV的容量是10 GiB。这样，Kubernetes就会为我们刚刚创建的PVC对象绑定这个PV。

所以，Kubernetes中PVC和PV的设计，**实际上类似于“接口”和“实现”的思想**。开发者只要知道并会使用“接口”，即：PVC；而运维人员则负责给“接口”绑定具体的实现，即：PV。

这种解耦，就避免了因为向开发者暴露过多的存储系统细节而带来的隐患。此外，这种职责的分离，往往也意味着出现事故时可以更容易定位问题和明确责任，从而避免“扯皮”现象的出现。

而PVC、PV的设计，也使得StatefulSet对存储状态的管理成为了可能。我们还是以上一篇文章中用到的StatefulSet为例（你也可以借此再回顾一下[《深入理解StatefulSet（一）：拓扑状态》](https://time.geekbang.org/column/article/41017)中的相关内容）：

```
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: web
spec:
  serviceName: "nginx"
  replicas: 2
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx:1.9.1
        ports:
        - containerPort: 80
          name: web
        volumeMounts:
        - name: www
          mountPath: /usr/share/nginx/html
  volumeClaimTemplates:
  - metadata:
      name: www
    spec:
      accessModes:
      - ReadWriteOnce
      resources:
        requests:
          storage: 1Gi
```

这次，我们为这个StatefulSet额外添加了一个volumeClaimTemplates字段。从名字就可以看出来，它跟Deployment里Pod模板（PodTemplate）的作用类似。也就是说，凡是被这个StatefulSet管理的Pod，都会声明一个对应的PVC；而这个PVC的定义，就来自于volumeClaimTemplates这个模板字段。更重要的是，这个PVC的名字，会被分配一个与这个Pod完全一致的编号。

这个自动创建的PVC，与PV绑定成功后，就会进入Bound状态，这就意味着这个Pod可以挂载并使用这个PV了。

如果你还是不太理解PVC的话，可以先记住这样一个结论：**PVC其实就是一种特殊的Volume**。只不过一个PVC具体是什么类型的Volume，要在跟某个PV绑定之后才知道。关于PV、PVC更详细的知识，我会在容器存储部分做进一步解读。

当然，PVC与PV的绑定得以实现的前提是，运维人员已经在系统里创建好了符合条件的PV（比如，我们在前面用到的pv-volume）；或者，你的Kubernetes集群运行在公有云上，这样Kubernetes就会通过Dynamic Provisioning的方式，自动为你创建与PVC匹配的PV。

所以，我们在使用kubectl create创建了StatefulSet之后，就会看到Kubernetes集群里出现了两个PVC：

```
$ kubectl create -f statefulset.yaml
$ kubectl get pvc -l app=nginx
NAME        STATUS    VOLUME                                     CAPACITY   ACCESSMODES   AGE
www-web-0   Bound     pvc-15c268c7-b507-11e6-932f-42010a800002   1Gi        RWO           48s
www-web-1   Bound     pvc-15c79307-b507-11e6-932f-42010a800002   1Gi        RWO           48s
```

可以看到，这些PVC，都以“&lt;PVC名字&gt;-&lt;StatefulSet名字&gt;-&lt;编号&gt;”的方式命名，并且处于Bound状态。

我们前面已经讲到过，这个StatefulSet创建出来的所有Pod，都会声明使用编号的PVC。比如，在名叫web-0的Pod的volumes字段，它会声明使用名叫www-web-0的PVC，从而挂载到这个PVC所绑定的PV。

所以，我们就可以使用如下所示的指令，在Pod的Volume目录里写入一个文件，来验证一下上述Volume的分配情况：

```
$ for i in 0 1; do kubectl exec web-$i -- sh -c 'echo hello $(hostname) > /usr/share/nginx/html/index.html'; done
```

如上所示，通过kubectl exec指令，我们在每个Pod的Volume目录里，写入了一个index.html文件。这个文件的内容，正是Pod的hostname。比如，我们在web-0的index.html里写入的内容就是"hello web-0"。

此时，如果你在这个Pod容器里访问`“http://localhost”`，你实际访问到的就是Pod里Nginx服务器进程，而它会为你返回/usr/share/nginx/html/index.html里的内容。这个操作的执行方法如下所示：

```
$ for i in 0 1; do kubectl exec -it web-$i -- curl localhost; done
hello web-0
hello web-1
```

现在，关键来了。

如果你使用kubectl delete命令删除这两个Pod，这些Volume里的文件会不会丢失呢？

```
$ kubectl delete pod -l app=nginx
pod "web-0" deleted
pod "web-1" deleted
```

可以看到，正如我们前面介绍过的，在被删除之后，这两个Pod会被按照编号的顺序被重新创建出来。而这时候，如果你在新创建的容器里通过访问`“http://localhost”`的方式去访问web-0里的Nginx服务：

```
# 在被重新创建出来的Pod容器里访问http://localhost
$ kubectl exec -it web-0 -- curl localhost
hello web-0
```

就会发现，这个请求依然会返回：hello web-0。也就是说，原先与名叫web-0的Pod绑定的PV，在这个Pod被重新创建之后，依然同新的名叫web-0的Pod绑定在了一起。对于Pod web-1来说，也是完全一样的情况。

**这是怎么做到的呢？**

其实，我和你分析一下StatefulSet控制器恢复这个Pod的过程，你就可以很容易理解了。

首先，当你把一个Pod，比如web-0，删除之后，这个Pod对应的PVC和PV，并不会被删除，而这个Volume里已经写入的数据，也依然会保存在远程存储服务里（比如，我们在这个例子里用到的Ceph服务器）。

此时，StatefulSet控制器发现，一个名叫web-0的Pod消失了。所以，控制器就会重新创建一个新的、名字还是叫作web-0的Pod来，“纠正”这个不一致的情况。

需要注意的是，在这个新的Pod对象的定义里，它声明使用的PVC的名字，还是叫作：www-web-0。这个PVC的定义，还是来自于PVC模板（volumeClaimTemplates），这是StatefulSet创建Pod的标准流程。

所以，在这个新的web-0 Pod被创建出来之后，Kubernetes为它查找名叫www-web-0的PVC时，就会直接找到旧Pod遗留下来的同名的PVC，进而找到跟这个PVC绑定在一起的PV。

这样，新的Pod就可以挂载到旧Pod对应的那个Volume，并且获取到保存在Volume里的数据。

**通过这种方式，Kubernetes的StatefulSet就实现了对应用存储状态的管理。**

看到这里，你是不是已经大致理解了StatefulSet的工作原理呢？现在，我再为你详细梳理一下吧。

**首先，StatefulSet的控制器直接管理的是Pod**。这是因为，StatefulSet里的不同Pod实例，不再像ReplicaSet中那样都是完全一样的，而是有了细微区别的。比如，每个Pod的hostname、名字等都是不同的、携带了编号的。而StatefulSet区分这些实例的方式，就是通过在Pod的名字里加上事先约定好的编号。

**其次，Kubernetes通过Headless Service，为这些有编号的Pod，在DNS服务器中生成带有同样编号的DNS记录**。只要StatefulSet能够保证这些Pod名字里的编号不变，那么Service里类似于web-0.nginx.default.svc.cluster.local这样的DNS记录也就不会变，而这条记录解析出来的Pod的IP地址，则会随着后端Pod的删除和再创建而自动更新。这当然是Service机制本身的能力，不需要StatefulSet操心。

**最后，StatefulSet还为每一个Pod分配并创建一个同样编号的PVC**。这样，Kubernetes就可以通过Persistent Volume机制为这个PVC绑定上对应的PV，从而保证了每一个Pod都拥有一个独立的Volume。

在这种情况下，即使Pod被删除，它所对应的PVC和PV依然会保留下来。所以当这个Pod被重新创建出来之后，Kubernetes会为它找到同样编号的PVC，挂载这个PVC对应的Volume，从而获取到以前保存在Volume里的数据。

这么一看，原本非常复杂的StatefulSet，是不是也很容易理解了呢？

## 总结

在今天这篇文章中，我为你详细介绍了StatefulSet处理存储状态的方法。然后，以此为基础，我为你梳理了StatefulSet控制器的工作原理。

从这些讲述中，我们不难看出StatefulSet的设计思想：StatefulSet其实就是一种特殊的Deployment，而其独特之处在于，它的每个Pod都被编号了。而且，这个编号会体现在Pod的名字和hostname等标识信息上，这不仅代表了Pod的创建顺序，也是Pod的重要网络标识（即：在整个集群里唯一的、可被访问的身份）。

有了这个编号后，StatefulSet就使用Kubernetes里的两个标准功能：Headless Service和PV/PVC，实现了对Pod的拓扑状态和存储状态的维护。

实际上，在下一篇文章的“有状态应用”实践环节，以及后续的讲解中，你就会逐渐意识到，StatefulSet可以说是Kubernetes中作业编排的“集大成者”。

因为，几乎每一种Kubernetes的编排功能，都可以在编写StatefulSet的YAML文件时被用到。

## 思考题

在实际场景中，有一些分布式应用的集群是这么工作的：当一个新节点加入到集群时，或者老节点被迁移后重建时，这个节点可以从主节点或者其他从节点那里同步到自己所需要的数据。

在这种情况下，你认为是否还有必要将这个节点Pod与它的PV进行一对一绑定呢？（提示：这个问题的答案根据不同的项目是不同的。关键在于，重建后的节点进行数据恢复和同步的时候，是不是一定需要原先它写在本地磁盘里的数据）

感谢你的收听，欢迎你给我留言，也欢迎分享给更多的朋友一起阅读。
<div><strong>精选留言（15）</strong></div><ul>
<li><span>虎虎❤️</span> 👍（80） 💬（6）<p>老师，由于无法追问，恳请能够回复详细一些。提前谢过了。
pvc的使用方式当中，对于由运维人员去创建pv，我始终有些疑问。
首先，一个pv对应一个pvc。如果实际绑定的pvc小于pv声明的存储大小，会造成存储的浪费吗？
其次，运维人员事先要创建多少个，以及多大容量的pv呢？因为并不清楚开发人员将来可能用多少1g的,10g的或者100g的pvc。创建的数量或大小不合适，会导致pv不够用。开发还是会来找运维的。
最后，如果回收方式是retain，那么pvc删除后，原来的pv并不会删除，如果开发人员想重新使用同一块存储，需要重建pv。这带来了很多运维工作。
所以，手动创建pv的最佳实践是怎样的呢？当然，如果用storage class去动态创建pv可以解决这件事，但是有时我们希望针对namespace创建属于自己的pv来限制存储的使用quota，而不得不用手动创建pv的模式。
</p>2018-10-05</li><br/><li><span>不知所措</span> 👍（26） 💬（3）<p>老师你好，statefulset 如果 不同的pod ，需要不同的配置，
比如说 zk集群，每个集群的myid 都是不同的，比如mysql集群每个主机的serverid 也是不同的，这种的怎么处理呢？</p>2018-12-11</li><br/><li><span>silver</span> 👍（18） 💬（4）<p>所以大体是Pod与PVC绑定，PVC与PV绑定，所以完成了Pod与PV的绑定?</p>2018-10-10</li><br/><li><span>Terry Hu</span> 👍（15） 💬（5）<p>由于没有ceph server ，pv用hostPath方式，在master上创建了index.html，pv pvc都创建好了，bound上了，登陆容器后在&#47;usr&#47;share&#47;nginx&#47;html目录下死活找不到index.html，搞了一个小时。突然猛醒原来hostPath指的是worker节点的path......哎，蠢啊</p>2018-11-28</li><br/><li><span>Alery</span> 👍（15） 💬（1）<p>前辈，我有个疑问，我通过deployment创建一个pods，在podTemplate中我声明volume使用persistentVolumeClaim并指定我事先创建pvc name， 这个时候我删除pod， 同样当pod删除的时候并不影响我事先创建的这个pvc，我是不是可以认为deployment这种资源也是能保存存储状态的呢？</p>2018-10-16</li><br/><li><span>Joe Black</span> 👍（14） 💬（1）<p>对于有些应用，比如关系数据库，它保存数据文件的位置必须严格符合POSIX接口，远程文件系统例如NFS对于类似锁定这样的操作支持的不好，即使是sqlite官方文档也不推荐用NFS。这种情况下，数据库应用好像只能用本地硬盘或者iSCSI的存储盘，这不就等同必须把重启的StatefulSet的Pod每次调度到同一个机器上才行吗？因为那个机器硬盘上的文件不会自动传输到其它机器上。是不是可以这么理解？</p>2018-10-14</li><br/><li><span>kitsdk</span> 👍（12） 💬（3）<p>pv对象不会绑定namespace吗？
命令 kubectl -n myns  delete pv --all --include-uninitialized 
执行完了，所有的pv也进入删除状态，当然因为有其他的pv绑定，没有立即删除。</p>2019-04-16</li><br/><li><span>北卡</span> 👍（12） 💬（1）<p>asdf100的问题应该是：一个集群中可能有很多个pv, pvc是如何找到他对应的pv的?

试着回答一下：
1、 指定了storageClassName的pv, 只有指定了同样storageClassName的pvc才能绑定到它上面。
2、对于没有指定storageClassName的pv,默认classname为&quot;&quot;, 同样只有没有指定classname的pvc才能绑定到它上面。
3、pvc可以用matchLabels和matchExpressions来指定标签完成更详细的匹配需求。
4、匹配成功应该还需要一些基本的存储条件吧，比如pvc申请的存储空间肯定不能大于指定的pv.

关于第四点没有验证过，用aws的efs可以动态扩展空间的，好像没有这些限制。请张老师详细解答一下。</p>2018-10-06</li><br/><li><span>LQ</span> 👍（7） 💬（3）<p>在一个 Pod 里面有两个容器， 容器 a 里自己实现一个 fuse filesystem，将远程的文件（比如 hdfs 上的数据）mount 到该容器里，另外一个容器 b 通过什么方式能读取到容器 a 里 mount 的数据呢，通过 PV 吗？有啥解决方案没？</p>2018-10-17</li><br/><li><span>silver</span> 👍（5） 💬（1）<p>如果一个stateful set的pod挂了，PV所在的机子被分配给了其他pod。那当stateful pod重新schedule的时候会不会出现PV所在机器资源不足导致无法schedule的情况？k8s是否针对这种问题有优化?</p>2018-10-10</li><br/><li><span>yuliz</span> 👍（4） 💬（1）<p>storage: 1Gi，表示我想要的 Volume 大小至少是 1 GB；这里是笔误么？1Gi不等于1GB,如果这里是1G应该更符合语景</p>2018-10-10</li><br/><li><span>艾利特-G</span> 👍（3） 💬（2）<p>老师您好，请问下只用Statefulset情况下，能做到指定编号的副本创建pvc，其他副本不创建pvc吗？还是说由Statefulset管理的副本必须有pvc呢？</p>2020-03-06</li><br/><li><span>我来也</span> 👍（3） 💬（3）<p>表示 nginx:1.9.1 里并没有 curl 命令.
通过 for i in 0 1; do kubectl exec -it web-$i -- curl localhost; done 无法获取到期待的结果.
通过
不知道其他小伙伴尝试过没有.
当然最终通过其他方式 比如之前的:
kubectl run -i --tty --image busybox:1.28.4 dns-test --restart=Never --rm &#47;bin&#47;sh
使用 wget 也是可以验证.
</p>2018-10-13</li><br/><li><span>Geek_dn82ci</span> 👍（2） 💬（1）<p>请问pvc声明的存储容量是多个pod副本share还是每一个独立的存储容量？</p>2018-11-11</li><br/><li><span>宋晓明</span> 👍（1） 💬（1）<p>我怎么感觉PV与PVC的关系就像LVM(逻辑卷管理)中的PV和VG的关系如出一辙呢？  也就是说PVC是在PV那么大的地盘里划出一小部分(PVC)供用户读写的，不知道理解的对不对？</p>2018-11-08</li><br/>
</ul>