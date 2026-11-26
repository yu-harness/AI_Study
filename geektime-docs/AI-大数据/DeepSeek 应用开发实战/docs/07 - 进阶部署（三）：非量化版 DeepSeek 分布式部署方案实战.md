你好，我是邢云阳。

在上节课中，我们学习了 DeepSeek 官方在做私有化部署时，推荐的一个工具，也就是 vLLM。通过学习 vLLM，想必你对分布式部署是怎么回事儿，已经有了初步感知。

今天，我们将学习另一个组件——Ray。随后，我们将在一台配备双GPU（A100）的Kubernetes集群上，演示如何分布式部署DeepSeek-R1-Distill-Llama-70B模型。

## 什么是Ray

Ray 是一个开源的分布式计算框架，旨在简化大规模机器学习和分布式应用程序的开发。它提供了高效的并行处理能力，支持数据预处理、分布式训练、超参数调优、模型服务和强化学习等任务。Ray 的核心概念包括任务（Tasks）、参与者（Actors）和对象（Objects），使得开发者能够轻松地在分布式环境中编写和执行并行代码。

如下图所示，便是程序通过 Ray 的处理之后，在三个节点上分布式运行的一个简单示意图。Ray 会将程序拆分成多片，分布到多个节点去运行。

![](https://static001.geekbang.org/resource/image/53/50/53b90c2cyy4a05727e4c0b881c73b450.jpg?wh=1600x839)

在之前的 Kubernetes 入门课中，我们讲过 K8s 作为云原生基础设施标准所具备的优势，比如弹性伸缩、资源调度等等。

因此，由字节跳动技术团队牵头，联合 AnyScale、蚂蚁金服、微软等公司在 Ray 的基础上又开发了适配 Kubernetes 版本的 KubeRay。它采用了经典的 Operator 设计，提供了 RayCluster、RayJob 和 RayService 等自定义资源定义（CRD），使得在 Kubernetes 集群上部署和管理 Ray 集群变得更加简便。通过 KubeRay，用户可以高效地管理 Ray 集群的生命周期，实现弹性伸缩、资源调度和作业管理等功能。

Ray-Operator 是 KubeRay 项目中的核心组件，负责在 Kubernetes 集群中创建和管理 Ray 集群。它通过监听 RayCluster、RayJob 和 RayService 等 CRD 的变化，自动化地处理 Ray 集群的部署、扩缩容和故障恢复等任务。Ray-Operator 使得用户能够以声明式的方式管理 Ray 集群，简化了集群的运维工作。

下图是在 Kubernetes上通过 Ray-operator 创建 Ray 集群的示意图。用户通过向 Ray-operator 提交 CR 的方式，来创建 Ray-Cluster。Ray-Cluster 包括一个 Head 和多个 Worker，会分别分布在不同的 GPU 节点上。以图中所示为例，含有两个 GPU 节点，则会有一个 Head 和一个 Worker 分别在这两个节点上以 pod 形式创建。

![](https://static001.geekbang.org/resource/image/09/1e/09a6047330cc49ba68ceb5yy5e878e1e.jpg?wh=3429x2569)

OK，理论部分就讲到这，你只要知道什么是 Ray，以及 Ray-Cluster 的架构即可，我们把重点放在部署和使用上。

## 部署过程

### 环境与模型准备

首先是准备 GPU 机器。上节课讲过，分布式推理有两种方案，一种是一个节点上有多张卡的情况，这种情况是通过使用 NVLink 技术，在卡之间建立高速通道，实现卡卡高速互联。第二种是多节点单（多）卡的情况，这种情况依赖节点间的高速网络。

这节课我们来测试多节点的情况，因此我在联通云上开通了一台 GPU 版本的 K8s，包含三个非 GPU 的 master 节点，以及两个 GPU 节点，每个节点上有一张 A100 卡。

![图片](https://static001.geekbang.org/resource/image/16/d4/1693293866808ff351095a1804e96bd4.png?wh=1920x540)

这台 K8s 会通过 NVIDIA 的 GPU-operator 部署好 NVIDIA 相关的驱动等，CUDA 版本选择 12.2。

机器准备好后，接下来就是模型文件的准备。对于不能科学上网的同学，模型文件可以在魔搭社区下载，链接：[https://www.modelscope.cn/models/deepseek-ai/DeepSeek-R1-Distill-Llama-70B/files](https://www.modelscope.cn/models/deepseek-ai/DeepSeek-R1-Distill-Llama-70B/files)。由于文件非常大，整个 repo 大概有 131G 左右，因此推荐你将模型下载到对象存储或者云硬盘，再通过 PV、PVC 的方式挂载。我采用的是对象存储的方式，PV、PVC 的 YAML 如下：

```python
apiVersion: v1                                                                                                                                                           
kind: PersistentVolume                                                                                                                                                   
metadata:                                                                                                                                                                
  name: deepseek                                                                                                                                                    
spec:                                                                                                                                                                    
  accessModes:                                                                                                                                                           
  - ReadWriteMany                                                                                                                                                        
  capacity:                                                                                                                                                              
    storage: 200Gi                                                                                                                                                       
  csi:                                                                                                                                                                   
    driver: ossplugin.csi.cucloud.com                                                                                                                                    
    volumeAttributes:                                                                                                                                                    
      bucket: deepseek                                                                                                                                               
      url: http://obs-sh-internal.cucloud.cn                                                                                                                             
    volumeHandle: deepseek                                                                                                                                           
  persistentVolumeReclaimPolicy: Retain                                                                                                                                  
  volumeMode: Filesystem                                                                                                                                                 
---                                                                                                                                                                                                                                                                              
apiVersion: v1                                                                                                                                                           
kind: PersistentVolumeClaim                                                                                                                                              
metadata:                                                                                                                                                                
  name: deepseek                                                                                                                                                    
  namespace: kuberay-operator                                                                                                                                              
spec:                                                                                                                                                                    
  accessModes:                                                                                                                                                           
  - ReadWriteMany                                                                                                                                                        
  resources:                                                                                                                                                             
    requests:                                                                                                                                                            
      storage: 200Gi                                                                                                                                                     
  volumeMode: Filesystem                                                                                                                                                 
  volumeName: deepseek
```

在 ModelScope 上下载模型有多种方式，推荐使用 ModelScope Python SDK 的方式进行下载。执行以下命令即可下载。

```plain
pip install modelscope

modelscope download --model deepseek-ai/DeepSeek-R1-Distill-Llama-70B --cache_dir /mnt/deepseek
```

我们可以使通过–cache\_dir 指定模型文件存放目录。例如在我的命令中的 /mnt/deepseek，意思是把模型下载到 /mnt/deepseek 目录。下载完成后，上传到对象存储即可。

为了节省一遍上传的时间，我们也可以在 K8s 上创建一个带有 python 环境的 pod，然后将上文中的对象存储 PVC 挂载到 pod 中，这样就可以直接在 pod 内访问到对象存储桶，也就可以直接将模型下载到对象存储桶内了。

当然，我还有种更简便的做法。可以先把 Ray 集群拉起来，Ray 集群内就带了 python 环境，然后把对象存储 PVC 挂载到 Ray 集群的 Head 中即可。因此，你也可以和我一样，先学习后面的 Ray 部署，然后再下载模型。

### Ray 集群部署

接下来看一下 Ray 的部署。我们知道通过 kuberay-operator，可以方便的部署 Ray 集群。kuberay-operator 可以使用官方提供的 Helm Chart 包进行安装。命令如下：

```plain
helm repo add kuberay https://ray-project.github.io/kuberay-helm/helm repo update
helm repo update
helm install kuberay-operator -n kuberay-operator kuberay/kuberay-operator
```

之后看一下 kuberay-operator 的 pod 运行状况：

```plain
kubectl get po -n kuberay-operator

NAME                                          READY   STATUS    RESTARTS   AGE                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 
kuberay-operator-5c5cb548db-2q2br             1/1     Running   0          23h
```

确认它处于 Running 状态就可以了。

然后我们来创建 Ray-Cluster，向 kuberay-operator 提交 CR即可。官方将 CR 封装成了 Helm Chart 包，可以通过如下命令部署。

```plain
helm install raycluster kuberay/ray-cluster -n kuberay-operator
```

但由于 CUDA 版本原因，我们需要找一个合适版本的 Ray 集群，因此我是将 Helm 包 fetch 下来，将 CR yaml 提取出来，手动进行了更改。YAML 如下：

```plain
apiVersion: ray.io/v1                                                                                                                                                                                                                                                                                                                                  
kind: RayCluster                                                                                                                                                                                                                                                                                                                                       
metadata:                                                                                                                                                                                                                                                                                                                                              
  annotations:                                                                                                                                                                                                                                                                                                                                         
    meta.helm.sh/release-name: raycluster                                                                                                                                                                                                                                                                                                              
    meta.helm.sh/release-namespace: kuberay-operator                                                                                                                                                                                                                                                                                                   
  generation: 3                                                                                                                                                                                                                                                                                                                                        
  labels:                                                                                                                                                                                                                                                                                                                                              
    app.kubernetes.io/instance: raycluster                                                                                                                                                                                                                                                                                                             
    app.kubernetes.io/managed-by: Helm                                                                                                                                                                                                                                                                                                                 
    helm.sh/chart: ray-cluster-1.2.2                                                                                                                                                                                                                                                                                                                   
  name: raycluster-kuberay                                                                                                                                                                                                                                                                                                                             
  namespace: kuberay-operator                                                                                                                                                                                                                                                                                                                          
spec:                                                                                                                                                                                                                                                                                                                                                  
  headGroupSpec:                                                                                                                                                                                                                                                                                                                                       
    rayStartParams:                                                                                                                                                                                                                                                                                                                                    
      dashboard-host: 0.0.0.0                                                                                                                                                                                                                                                                                                                          
    serviceType: ClusterIP                                                                                                                                                                                                                                                                                                                             
    template:                                                                                                                                                                                                                                                                                                                                          
      metadata:                                                                                                                                                                                                                                                                                                                                        
        annotations: {}                                                                                                                                                                                                                                                                                                                                
        labels:                                                                                                                                                                                                                                                                                                                                        
          app.kubernetes.io/instance: raycluster                                                                                                                                                                                                                                                                                                       
          app.kubernetes.io/managed-by: Helm                                                                                                                                                                                                                                                                                                           
          helm.sh/chart: ray-cluster-1.2.2                                                                                                                                                                                                                                                                                                             
      spec:                                                                                                                                                                                                                                                                                                                                            
        affinity: {}                                                                                                                                                                                                                                                                                                                                   
        containers:                                                                                                                                                                                                                                                                                                                                    
        - image: docker.1ms.run/rayproject/ray-ml:2.11.0.a464b6-py310-gpu                                                                                                                                                                                                                                                                              
          imagePullPolicy: IfNotPresent                                                                                                                                                                                                                                                                                                                
          name: ray-head                                                                                                                                                                                                                                                                                                                               
          resources:                                                                                                                                                                                                                                                                                                                                   
            limits:                                                                                                                                                                                                                                                                                                                                    
              cpu: "4"                                                                                                                                                                                                                                                                                                                                 
              memory: 16G                                                                                                                                                                                                                                                                                                                              
            requests:                                                                                                                                                                                                                                                                                                                                  
              cpu: "1"                                                                                                                                                                                                                                                                                                                                 
              memory: 2G                                                                                                                                                                                                                                                                                                                               
          securityContext: {}                                                                                                                                                                                                                                                                                                                          
          volumeMounts:                                                                                                                                                                                                                                                                                                                                
          - mountPath: /tmp/ray                                                                                                                                                                                                                                                                                                                        
            name: log-volume                                                                                                                                                                                                                                                                                                                           
          - mountPath: /mnt/deepseek                                                                                                                                                                                                                                                                                                                   
            name: deepseek-r1                                                                                                                                                                                                                                                                                                                          
        imagePullSecrets: []                                                                                                                                                                                                                                                                                                                           
        nodeSelector: {}                                                                                                                                                                                                                                                                                                                               
        tolerations: []                                                                                                                                                                                                                                                                                                                                
        volumes:                                                                                                                                                                                                                                                                                                                                       
        - emptyDir: {}                                                                                                                                                                                                                                                                                                                                 
          name: log-volume                                                                                                                                                                                                                                                                                                                             
        - name: deepseek-r1                                                                                                                                                                                                                                                                                                                            
          persistentVolumeClaim:                                                                                                                                                                                                                                                                                                                       
            claimName: deepseek                                                                                                                                                                                                                                                                                                                        
  workerGroupSpecs:                                                                                                                                                                                                                                                                                                                                    
  - groupName: workergroup                                                                                                                                                                                                                                                                                                                             
    maxReplicas: 3                                                                                                                                                                                                                                                                                                                                     
    minReplicas: 1                                                                                                                                                                                                                                                                                                                                     
    numOfHosts: 1                                                                                                                                                                                                                                                                                                                                      
    rayStartParams:                                                                                                                                                                                                                                                                                                                                    
      num-gpus: "1"                                                                                                                                                                                                                                                                                                                                    
    replicas: 1                                                                                                                                                                                                                                                                                                                                        
    template:                                                                                                                                                                                                                                                                                                                                          
      metadata:                                                                                                                                                                                                                                                                                                                                        
        annotations: {}                                                                                                                                                                                                                                                                                                                                
        labels:                                                                                                                                                                                                                                                                                                                                        
          app.kubernetes.io/instance: raycluster                                                                                                                                                                                                                                                                                                       
          app.kubernetes.io/managed-by: Helm                                                                                                                                                                                                                                                                                                           
          helm.sh/chart: ray-cluster-1.2.2                                                                                                                                                                                                                                                                                                             
      spec:                                                                                                                                                                                                                                                                                                                                            
        affinity: {}                                                                                                                                                                                                                                                                                                                                   
        containers:                                                                                                                                                                                                                                                                                                                                    
        - image: docker.1ms.run/rayproject/ray-ml:2.11.0.a464b6-py310-gpu                                                                                                                                                                                                                                                                              
          imagePullPolicy: IfNotPresent                                                                                                                                                                                                                                                                                                                
          name: ray-worker                                                                                                                                                                                                                                                                                                                             
          resources:                                                                                                                                                                                                                                                                                                                                   
            limits:                                                                                                                                                                                                                                                                                                                                    
              cpu: "14"                                                                                                                                                                                                                                                                                                                                
              memory: 60G                                                                                                                                                                                                                                                                                                                              
            requests:                                                                                                                                                                                                                                                                                                                                  
              cpu: "1"                                                                                                                                                                                                                                                                                                                                 
              memory: 1G                                                                                                                                                                                                                                                                                                                               
          securityContext: {}                                                                                                                                                                                                                                                                                                                          
          volumeMounts:                                                                                                                                                                                                                                                                                                                                
          - mountPath: /tmp/ray                                                                                                                                                                                                                                                                                                                        
            name: log-volume                                                                                                                                                                                                                                                                                                                           
          - mountPath: /mnt/deepseek                                                                                                                                                                                                                                                                                                                   
            name: deepseek-r1                                                                                                                                                                                                                                                                                                                          
        imagePullSecrets: []                                                                                                                                                                                                                                                                                                                           
        nodeSelector: {}                                                                                                                                                                                                                                                                                                                               
        tolerations: []                                                                                                                                                                                                                                                                                                                                
        volumes:                                                                                                                                                                                                                                                                                                                                       
        - emptyDir: {}                                                                                                                                                                                                                                                                                                                                 
          name: log-volume                                                                                                                                                                                                                                                                                                                             
        - name: deepseek-r1                                                                                                                                                                                                                                                                                                                            
          persistentVolumeClaim:                                                                                                                                                                                                                                                                                                                       
            claimName: deepseek
```

首先是镜像，使用 rayproject/ray-ml:2.11.0.a464b6-py310-gpu，也就是 2.11.0 版本的 Ray 集群。之后是 Head 节点和 Worker 节点的配置。Head 节点很简单，就是将对象存储 PVC 挂载上即可。Worker 节点除了挂载 PVC 之后，还需要配置两个参数，即：

```plain
numOfHosts: 1                                                                                                                                                                                                                                                                                                                                      
rayStartParams:                                                                                                                                                                                                                                                                                                                                    
  num-gpus: "1"  
```

numOfHosts 代表在一个节点上部署 worker，num-gpus 代表每个节点上有一张卡。这里是个坑，很多网上的教程在只有两个 GPU 节点的情况下会把 numOfHosts 设置成 2，这是没有理解 Ray 集群的组成。实际上，Head 本身会占用一个节点，因此 **Worker 创建一个即可**。

配好参数后，直接 kubectl apply 拉起：

```plain
kubectl get po -n kuberay-operator -owide

NAME                                          READY   STATUS    RESTARTS   AGE    IP             NODE           NOMINATED NODE   READINESS GATES                                                                                                                                                                                                                                                                                                                                                                                                                                    
raycluster-kuberay-head-zphgs                 1/1     Running   0          171m   10.43.0.35     192.168.0.34                                                                                                                                                                                                                              
raycluster-kuberay-workergroup-worker-kbsvr   1/1     Running   0          171m   10.43.140.28   192.168.0.68              
```

状态如上所示，就说明成功了。你可以直接拿我的 YAML，针对你的集群环境做相应的修改。

此时可以进入 raycluster-kuberay-head-zphgs 内，查看 ray 集群的状态。

```plain
(base) ray@raycluster-kuberay-head-zphgs:~$ ray status                                                                                                                                                                                                                                                                                                 
2025-02-13 00:54:12,571 - INFO - Note: NumExpr detected 16 cores but "NUMEXPR_MAX_THREADS" not set, so enforcing safe limit of 8.                                                                                                                                                                                                                      
2025-02-13 00:54:12,571 - INFO - NumExpr defaulting to 8 threads.                                                                                                                                                                                                                                                                                      
======== Autoscaler status: 2025-02-13 00:54:12.737576 ========                                                                                                                                                                                                                                                                                        
Node status                                                                                                                                                                                                                                                                                                                                            
---------------------------------------------------------------                                                                                                                                                                                                                                                                                        
Active:                                                                                                                                                                                                                                                                                                                                                
 1 node_a0dcf7b6cdb9c28191d6db6a44ba774ed04fb0bbda704a498112674f                                                                                                                                                                                                                                                                                       
 1 node_3804fd0732e483a2240e9f608d15362f415411fca7c69b58232a1174                                                                                                                                                                                                                                                                                       
Pending:                                                                                                                                                                                                                                                                                                                                               
 (no pending nodes)                                                                                                                                                                                                                                                                                                                                    
Recent failures:                                                                                                                                                                                                                                                                                                                                       
 (no failures)                                                                                                                                                                                                                                                                                                                                         
                                                                                                                                                                                                                                                                                                                                                       
Resources                                                                                                                                                                                                                                                                                                                                              
---------------------------------------------------------------                                                                                                                                                                                                                                                                                        
Usage:                                                                                                                                                                                                                                                                                                                                                 
 0.0/18.0 CPU                                                                                                                                                                                                                                                                                                                                          
 0.0/2.0 GPU                                                                                                                                                                                                                                                                                                                                           
 0B/70.78GiB memory                                                                                                                                                                                                                                                                                                                                    
 0B/20.90GiB object_store_memory                                                                                                                                                                                                                                                                                                                       
                                                                                                                                                                                                                                                                                                                                                       
Demands:                                                                                                                                                                                                                                                                                                                                               
 (no resource demands)
```

可以看到有两个 Active 的节点，和两个没有使用的 GPU。Ray 集群自带了一个可视化 UI，可以直观地查看 CPU，内存，GPU 等的使用量以及任务执行情况等，因此可以通过 loadBalancer 或者 NodePort 将 UI 的端口暴露出去，即可在集群外部访问。我们在浏览器输入 [http://xxxx:8265](http://xxxx:8265) 进入 Web UI查看。

![图片](https://static001.geekbang.org/resource/image/55/75/55381bebcbde46c5895a53a2a80e6775.png?wh=1920x492)

这样 Ray 集群部分，我们就部署完了。

PS：别忘了这时就可以下载模型文件了。

### 在 Ray 中 部署 Vllm

在 Ray 容器中，默认提供了一个 Conda 环境，有很多基础包，但需要将 pynvml 包卸载掉，因为这会与另一个包 nvidia-ml-py 冲突，命令：

```plain
pip uninstall pynvml
```

之后就可以安装 vllm 了，为了适配 Ray 集群，我选择的版本是 0.6.1.post2，安装命令为：

```plain
pip install vllm==0.6.1.post2
```

安装完成后，便可以使用 vllm 拉起大模型。就像上节课讲得那样，此处可以使用 python 代码的方式，也可以直接使用 vllm serve 命令，它会拉起大模型，同时提供一个 OpenAI 兼容的服务器。命令：

```plain
vllm serve /mnt/deepseek/deepseek-ai/DeepSeek-R1-Distill-Llama-70B \
--port 8000 \
--trust-remote-code \
--served-model-name deepseek-r1 \
--gpu-memory-utilization 0.95 \
--tensor-parallel-size 2 \
--max-model-len 8096
```

等待一段时间后，会有如下显示：

![图片](https://static001.geekbang.org/resource/image/df/00/df9be8dcc098194bb440654a3616a500.png?wh=1920x685)

此时就说明，模型加载成功，server 也启动了。

这时我们再看一下 Ray 集群情况：

![图片](https://static001.geekbang.org/resource/image/57/23/579bb55923904f018d011bfa57b0a823.png?wh=1920x536)

可以看到模型在两个 GPU 卡上各占了一半的显存，这也就意味着分布式部署成功了。

我们可以用 curl 测试一下，命令如下：

```plain
curl http://<公网IP>:8000/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
    "model": "deepseek-r1",
    "messages": [
        {"role": "user", "content": "帮我写一个client-go代码，可以列出pod列表"}
    ]
}'
```

![图片](https://static001.geekbang.org/resource/image/41/ab/4152bd888d0fc619246463a80f4ea4ab.png?wh=1877x821)

## 使用对话前端连接模型

在 [Ollama 那节课](https://time.geekbang.org/column/article/857432)，我们讲过 LobeChat。通过 docker 一键拉起 LobeChat 后，点击设置，语言模型，在 OpenAI 模型中输入上文命令中的 Server 地址，点击获取模型列表，即可获取到可用模型。

![图片](https://static001.geekbang.org/resource/image/13/7f/13aca85b22449bcb35ae3524111f0b7f.png?wh=968x695)

然后便可以开始对话了。

![图片](https://static001.geekbang.org/resource/image/8d/bc/8db259617800be28c4ea1aa81efdc6bc.png?wh=1898x902)

至此，我们就用分布式的方式成功部署了Deepseek-R1:70B 模型，。如果你机会去部署 671B 模型，可以使用这节课的套路来操作，两者之间在部署手法上一模一样，没有任何区别。

## 总结

今天通过分布式部署非量化版 DeepSeek-R1 模型的实战，我们不仅深入了解了 Ray 这一强大的分布式计算框架，还掌握了如何在 Kubernetes 集群上高效部署和管理大规模机器学习模型。

首先我们要理解Ray 在分布式计算中的核心作用，它通过任务、参与者和对象等概念，简化了并行代码的编写和执行。特别是在 Kubernetes 上通过 KubeRay 部署 Ray 集群，使得集群的弹性伸缩、资源调度和作业管理变得更加便捷。这不仅提高了资源利用率，还为大规模模型的推理提供了坚实的基础。

随后通过实际的部署过程，我们体会到了分布式部署的复杂性。从 GPU 机器的准备、模型文件的下载与存储，到 Ray 集群的配置与启动，每一步都需要细致地规划和调试。特别是在多节点、多 GPU 的场景下，如何合理分配资源、避免瓶颈，成为了成功部署的关键。

最后，通过 vLLM 的集成和模型的成功加载，我们验证了分布式部署的可行性。

总的来说，如果只是对着文档一步步执行命令行，那整个过程并不复杂。但在这个过程中，我们需要多多思考，理解每一步为什么要这么做，意义是什么，这样才能在后续版本更新，部署手法发生变化时，能够读懂官方文档，做到举一反三。

## 思考题

如果一个 Kubernetes 集群，包含 3 个 master 节点，2 个 CPU worker 节点以及 3 个 GPU worker 节点，应如何设置 numOfHosts 和 num-gpus？

欢迎你在留言区展示你的思考结果，我们一起探讨。如果你觉得这节课的内容对你有帮助的话，也欢迎你分享给其他朋友，我们下节课再见！
<div><strong>精选留言（15）</strong></div><ul>
<li><span>蓝雨</span> 👍（4） 💬（1）<p>vllm和ray是怎么协同的呢？在ray容器中启动，就被ray识别为分布式计算任务？不是很明白</p>2025-03-15</li><br/><li><span>somunslotus</span> 👍（1） 💬（1）<p>我看你这个是启动ray集群后，手动进入ray head容器用vllm启动模型，可否基于ray的镜像把vllm安装进去，做一个新的镜像，然后headGroup的container启动命令设置为vllm拉起模型的命令，这样就可以用一个apply命令启动ray集群同时启动deepseek服务</p>2025-04-23</li><br/><li><span>卖猪肉的大叔</span> 👍（1） 💬（1）<p>老师，问一下分布式集群里同一个节点的GPU卡可以是不同型号的么，不同节点可以是不同的服务器类型么？</p>2025-04-02</li><br/><li><span>小浣熊干脆面</span> 👍（1） 💬（2）<p>老师我这里有两个疑问。
1. 您在案例中的分布式部署只用到了张量并行tp，tp对带宽要求高。请问一般需要多大的内网带宽可以满足tp的要求并不影响推理性能
2. 什么情况下可以使用pp呢（管道并行）。还是说两者可以同时使用，因为我在阿里云文档的案例上看到tp才适合多节点。pp适合每台节点多卡的情况。也有可能是我理解错了</p>2025-03-24</li><br/><li><span>SONG</span> 👍（1） 💬（1）<p>在 Ray 容器中，默认提供了一个 Conda 环境，有很多基础包，但需要将 pynvml 包卸载掉，因为这会与另一个包 nvidia-ml-py 冲突。这个Ray容器指的是那个容器</p>2025-03-18</li><br/><li><span>蓝雨</span> 👍（1） 💬（1）<p>我看vllm官方也提供了multiple node solution，不用ray，减少依赖，是不是会更清爽点。https:&#47;&#47;docs.vllm.ai&#47;en&#47;latest&#47;serving&#47;distributed_serving.html</p>2025-03-15</li><br/><li><span>grok</span> 👍（1） 💬（2）<p>老师，你对SGLang什么看法？这门课为什么不采用SGLang？（不吹不黑不引战）

我发现sglang的社区很火；并且很多评测显示用其部署后比vLLM快。您怎么看？

企业环境使用SGLang有坑吗？</p>2025-03-15</li><br/><li><span>麦耀锋</span> 👍（1） 💬（1）<p>老师，您提供的raycluster的yaml里面，只看到将设置workerGroup的 `rayStartParams: num-gpus: &quot;1&quot;`， 我的理解，在headerGroup的配置里面也应当设置上吧，否则header怎么能用上gpu资源呢？另外，为何对cpu&#47;memory的limit配置，header配置4&#47;16G，而worker配置14&#47;60G呢？我的理解中，header既包含worker process，也包含管理的process，所以，理论上header所需求的资源不应该比worker少？</p>2025-03-14</li><br/><li><span>娄尚</span> 👍（1） 💬（1）<p>能具体讲讲基于deepseek搭建本地的知识库、或者基于推理功能在项目中的实际的应用
</p>2025-03-14</li><br/><li><span>hello its me</span> 👍（0） 💬（1）<p>vllm server 已经设置了固定的--tensor-parallel-size 2，假设有足够的多个gpu节点，maxReplicas: 3, minReplicas: 1 有实际作用吗？
</p>2025-05-23</li><br/><li><span>Geek_83c8ee</span> 👍（0） 💬（2）<p>老师，在安装完vllm 0.6.1.post2之后会报依赖冲突的问题，这个会对大模型运行有影响不？</p>2025-05-22</li><br/><li><span>Lily</span> 👍（0） 💬（1）<p>老师好，我有一个问题。
在用vllm serve拉起大模型时，设置参数--tensor-parallel-size 2 。这里为什么不是 --pipeline-parallel-size 2 --tensor-parallel-size 1，这里不是有2台机器，每台机器一张GPU卡吗？</p>2025-05-09</li><br/><li><span>east super</span> 👍（0） 💬（1）<p>老师，您平时一般用MAC还是windows做开发</p>2025-04-28</li><br/><li><span>一路前行</span> 👍（0） 💬（1）<p>联通云上开通了一台 GPU 版本的 K8s，包含三个非 GPU 的 master 节点，以及两个 GPU 节点，每个节点上有一张 A100 卡。 这是几个节点啊，没看明白。 一台gpu版本的k8s，包含3个非gpu的master????</p>2025-04-21</li><br/><li><span>0mfg</span> 👍（0） 💬（2）<p>老师请教一个问题老师好请教一下没看明白的地方，vllm serve只在一台服务器上启动就可以吗？最后lobechat设置的api地址是两台服务器哪台的地址呢</p>2025-03-20</li><br/>
</ul>