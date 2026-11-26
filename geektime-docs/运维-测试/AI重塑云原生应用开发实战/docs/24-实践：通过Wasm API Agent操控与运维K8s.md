你好，我是邢云阳。

上一节课，我们留了一个小尾巴，也就是在 Agent 插件中，如何实现 JSON Mode 输出呢？本节课，我们先来解决掉这个小尾巴。

## JSON Mode

在[第 21 讲](https://time.geekbang.org/column/article/842102)中，我带你开发JSON Mode小插件时，详细讲解了JSON Mode的工作原理。其核心是通过prompt指示大模型按照指定的JSON Schema格式化输出结果。由于本插件的JSON Schema支持自定义，因此我对之前的JSON Mode prompt进行了调整，修改后的形式如下：

```go
Given the Json Schema: %s, please help me convert the following content to a pure json: %s
Do not respond other content except the pure json!!!!
```

- 第一个%s用于填充用户自定义的JSON Schema内容；
- 第二个%s用于填充需要格式化的原始数据。

在完成核心逻辑后，代码的实现就变得顺理成章了。具体流程如下：

1. 在获取到“Final Answer”时，首先判断是否开启了JSON输出设置。
2. 如果开启了JSON格式化功能，就先将结果按照指定的JSON Schema进行格式化；
3. 如果未开启，就直接返回结果，继续后续的Body替换操作。

JSON 格式化的核心代码如下：

```go
func jsonFormat(llmClient wrapper.HttpClient, llmInfo LLMInfo, jsonSchema map[string]interface{}, assistantMessage Message, actionInput string, headers [][2]string, streamMode bool, rawResponse Response, log wrapper.Log) string {
    prompt := fmt.Sprintf(prompttpl.Json_Resp_Template, jsonSchema, actionInput)

    messages := []dashscope.Message{{Role: "user", Content: prompt}}

    completion := dashscope.Completion{
        Model:    llmInfo.Model,
        Messages: messages,
    }

    completionSerialized, _ := json.Marshal(completion)
    var content string
    err := llmClient.Post(
        llmInfo.Path,
        headers,
        completionSerialized,
        func(statusCode int, responseHeaders http.Header, responseBody []byte) {
            //得到gpt的返回结果
.                       ...
        }, uint32(llmInfo.MaxExecutionTime))
    if err != nil {
        log.Debugf("[onHttpRequestBody] completion err: %s", err.Error())
        proxywasm.ResumeHttpRequest()
    }
    return content
}
```

在代码实现中，我们首先拼接好了包含JSON Schema和待格式化数据的prompt模板，随后通过HTTP请求调用大模型，成功获取了JSON格式化后的结果。至此，上节课遗留的“小尾巴”问题就圆满解决了。

此外，我想补充一点关于编译命令的注意事项。之前我们使用的编译命令是：

```go
tinygo build -o main.wasm -scheduler=none -target=wasi -gc=custom -tags='custommalloc nottinygc_finalizer' ./main.go
```

这条命令仅适用于插件根目录下只有一个main.go文件的情况。如果根目录下还存在其他Go文件（例如config.go），那么该命令会报错。为了解决这个问题，我们需要将./main.go替换为.，表示编译当前目录下的所有Go文件。完整的命令如下：

```yaml
tinygo build -o agent.wasm -scheduler=none -target=wasi -gc=custom
 -tags='custommalloc nottinygc_finalizer' .
```

## 测试

### 部署 ginTools 服务

接下来，我们将使用前面章节中介绍的ginTools工具来测试本插件的效果。首先，简单回顾一下ginTools的功能：它是一个基于gin框架和client-go库开发的服务器，主要用于与Kubernetes集群进行交互。ginTools提供了以下几个核心路由：

```plain
GET /:resource 获取指定资源列表
DELETE /:resource 删除指定资源
POST /:resource 创建指定资源
GET /pods/logs 获取指定pod的日志
GET /pods/events 获取指定pod的事件
```

为了将ginTools工具以Pod形式部署到Higress所在的Kubernetes集群中，我们需要解决一个关键问题：ginTools如何在容器内操作容器外部的K8s资源？

在之前讲解client-go时，我曾简要提到过一种方法，即使用 **InCluster 模式**。这种模式允许运行在K8s集群中的Pod通过集群内部的认证机制访问外部的K8s资源。下面，我们来详细说明具体操作步骤。

首先，我们需要创建一个K8s服务账户（ServiceAccount，简称sa），作为ginTools访问K8s资源的凭证。该服务账户的权限决定了ginTools能够操作哪些K8s资源。

为了给服务账户赋予权限，通常使用Role/RoleBinding或ClusterRole/ClusterRoleBinding：

- Role/RoleBinding：作用域限定在某个命名空间内。
- ClusterRole/ClusterRoleBinding：作用域覆盖整个集群。

由于ginTools可能需要操作集群级别的资源，我们选择使用ClusterRole/ClusterRoleBinding来为服务账户赋权。以下是具体的YAML配置：

```yaml
apiVersion: v1                                                                                                                                                           
kind: ServiceAccount                                                                                                                                                     
metadata:                                                                                                                                                                
  labels:                                                                                                                                                                
    app: example                                                                                                                                                         
  name: sa-example                                                                                                                                                       
  namespace: default                                                                                                                                                     
---                                                                                                                                                                      
apiVersion: rbac.authorization.k8s.io/v1                                                                                                                                 
kind: ClusterRoleBinding                                                                                                                                                 
metadata:                                                                                                                                                                
  labels:                                                                                                                                                                
    app: example                                                                                                                                                         
  name: sa-example                                                                                                                                                       
roleRef:                                                                                                                                                                 
  apiGroup: rbac.authorization.k8s.io                                                                                                                                    
  kind: ClusterRole                                                                                                                                                      
  name: sa-example                                                                                                                                                       
subjects:                                                                                                                                                                
  - kind: ServiceAccount                                                                                                                                                 
    name: sa-example                                                                                                                                                     
    namespace: default                                                                                                                                                   
---                                                                                                                                                                      
apiVersion: rbac.authorization.k8s.io/v1                                                                                                                                 
kind: ClusterRole                                                                                                                                                        
metadata:                                                                                                                                                                
  labels:                                                                                                                                                                
    app: example                                                                                                                                                         
  name: sa-example                                                                                                                                                       
rules:                                                                                                                                                                   
  - apiGroups:                                                                                                                                                           
      - ""                                                                                                                                                               
    resources:                                                                                                                                                           
      - pods                                                                                                                                                             
      - pods/log                                                                                                                                                         
      - services                                                                                                                                                         
      - events                                                                                                                                                           
    verbs:                                                                                                                                                               
      - get                                                                                                                                                              
      - list                                                                                                                                                             
      - delete 
      - create                                                                                                                                                                                                                                                                                                                     
  - apiGroups:                                                                                                                                                           
      - ""                                                                                                                                                               
    resources:                                                                                                                                                           
      - namespaces                                                                                                                                                       
    verbs:                                                                                                                                                               
      - get                                                                                                                                                              
      - list
```

在本测试中，我们仅对Pod、Service以及Pod的日志（logs）和事件（events）进行操作测试，其他资源暂不涉及。因此，在ClusterRole的resources字段中，我们只配置了 YAML 文件中 resources 所对应的几种类型。同时，我们为这些资源设置了增（create）、删（delete）、查（get）以及列表（list）四种操作权限。

接下来是 ginTools 的部署 YAML：

```yaml
---                                                                                                                                                                      
apiVersion: apps/v1                                                                                                                                                      
kind: Deployment                                                                                                                                                         
metadata:                                                                                                                                                                
  name: gintools                                                                                                                                                         
  namespace: default  # Deployment 所 在 的 命 名 空 间                                                                                                                         
spec:                                                                                                                                                                    
  replicas: 1                                                                                                                                                            
  selector:                                                                                                                                                              
    matchLabels:                                                                                                                                                         
      app: gintools                                                                                                                                                      
  template:                                                                                                                                                              
    metadata:                                                                                                                                                            
      labels:                                                                                                                                                            
        app: gintools                                                                                                                                                    
    spec:                                                                                                                                                                
      serviceAccountName: sa-example  # 使 用 指 定 的  ServiceAccount                                                                                                        
      containers:                                                                                                                                                        
      - name: gintools                                                                                                                                                   
        image: registry.cn-hangzhou.aliyuncs.com/aitools/gintools:v1.1                                                                                                   
        ports:                                                                                                                                                           
        - containerPort: 8080                                                                                                                                            
---                                                                                                                                                                      
apiVersion: v1                                                                                                                                                           
kind: Service                                                                                                                                                            
metadata:                                                                                                                                                                
  name: gintools-service                                                                                                                                                 
  namespace: default  # Service 所 在 的 命 名 空 间                                                                                                                            
spec:                                                                                                                                                                    
  type: ClusterIP                                                                                                                                                        
  ports:                                                                                                                                                                 
  - port: 38880                                                                                                                                                          
    targetPort: 8080                                                                                                                                                     
  selector:                                                                                                                                                              
    app: gintools
```

整个 YAML 很简单，唯一需要注意的就是 serviceAccountName 字段，这里要填刚刚创建的 sa 的名称。部署完成后，可以在 Higress 控制台的服务列表页面查看到该服务。

![图片](https://static001.geekbang.org/resource/image/3c/d7/3c6c4b7721e08b01bfa483a4a26565d7.png?wh=1456x338)

### 暴露 ginTools 服务

目前，我们已经接近在插件中访问ginTools服务的目标，但还差最后一步。由于Kubernetes（K8s）集群中的服务数量可能非常多，如果所有服务都能被插件访问，会导致以下问题：

1. xds推送时的计算开销增加：大量服务信息需要被计算和推送，影响性能。
2. 内存开销增加：过多的指标和服务信息会占用大量内存。

为了解决这些问题，Higress在设计上默认只允许插件访问与路由关联的服务。如果需要放开这一限制，有以下两种方式：

**方式一：修改Helm安装参数**

在安装Higress时，可以通过修改Helm的global.onlyPushRouteCluster参数为false，从而允许插件访问所有K8s服务。具体命令如下：

```plain
helm install higress ./higress-chart \
  --set global.onlyPushRouteCluster=false
```

这种方式虽然简单，但可能会带来额外的计算和内存开销，因此需要根据实际需求谨慎使用。

**方式二：使用 DNS 域名暴露服务**

我们可以通过 DNS 域名的方式将K8s服务暴露出来。该方式还是通过在 Higress 控制台的服务来源页面配置。如下图所示，服务端口需要填写服务的 service 暴露出的 pod，域名列表填写服务地址，这些信息在上文中的服务列表中都可以查到。

![图片](https://static001.geekbang.org/resource/image/5c/bd/5ca67b4d1070aed6c57f1e1801318dbd.png?wh=981x814)

由于ginTools在部署时采用的是ClusterIP方式的服务暴露，这种方式只能在Kubernetes集群内部访问。为了在外部（例如浏览器）测试配置的DNS域名方式是否生效，我们需要为ginTools添加一个路由规则，将其暴露到外部网络。

![图片](https://static001.geekbang.org/resource/image/65/f0/650cf2fb5b1565ee64b88394d79e7bf0.png?wh=980x536)

![图片](https://static001.geekbang.org/resource/image/d9/24/d9659ef50b3f0a7055ace1b2b6883c24.png?wh=945x158)

配置完成后，在浏览器输入 URL：

```yaml
http://<你的网关IP>/pods/logs?podname=<你的ginTools pod名称>
```

得到下图效果，说明服务是可用的。

![图片](https://static001.geekbang.org/resource/image/b1/df/b1b71e21174493d343382c4ffa4515df.png?wh=1910x422)

我们用肉眼看一下日志的最后一行，提示 watch pod 失败，这是由于上文在配置 sa 权限时，我们故意没有配置 watch 权限导致的。接下来就用该服务作为 Agent 的工具，让 agent 来分析一下这个日志。

### 配置与测试 Agent

Agent 的配置主要包含 API 和 LLM 两个部分，我先写一个示例，然后再讲解参数的含义：

```yaml
apis:
- api: |-
    openapi: 3.1.0
    info:
      title: k8s资源管理系统
      description: 操作 k8s 资源
      version: v1.0.0
    servers:
      - url: http://gintools-service.default.svc.cluster.local:38880
    paths:
      /pods/logs:
        get:
          description: 根据pod名称和命名空间获取pod的日志
          operationId: get_pod_log
          parameters:
            - name: ns
              in: query
              description: 命名空间名称
              required: true
              schema:
                type: string
            - name: podname
              in: query
              description: pod名称
              required: true
              schema:
                type: string
          deprecated: false
      /{resource}:
        get:
          description: 根据k8s资源名称和指定命名空间获取资源列表
          operationId: get_resource_list
          parameters:
            - name: ns
              in: query
              description: 命名空间名称
              required: true
              schema:
                type: string
            - name: resource
              in: path
              description: k8s资源名称
              required: true
              schema:
                type: string
          deprecated: false
    components:
      schemas: {}
  apiProvider:
    domain: "gintools-service.default.svc.cluster.local"
    serviceName: "gin.dns"
    servicePort: 38880
llm:
  apiKey: "sk-85axxxxxxxxxxxxxxxx"
  domain: "api.deepseek.com"
  maxIterations: 10
  model: "deepseek-chat"
  path: "/v1/chat/completions"
  serviceName: "deepseek.dns"
  servicePort: 443
promptTemplate:
  language: "CH"
```

在 apis 部分，配置外部工具。此处可以配置多个服务商的工具，例如可以同时配置高德地图 + 心知天气的 API Tools。在这里我们就先配置本地的 ginTools 工具。在OpenAPI 文档中，url 即为服务的 service 地址。在 apiProvider 部分，由于是本地服务，没有 APIKey，因此没有如下关于 apiKey 的配置：

```yaml
apiKey: 
  in: query
  name: key
  value: xxxxxxxxxxxxxxx
```

llm 部分就是 Agent 从第二轮对话开始所使用的大模型的服务商信息，按自己的实际情况填写即可，但是建议使用推理能力强的模型，否则可能幻觉会比较严重。

配置完成后，我们用 apifox 软件做一下测试：

![图片](https://static001.geekbang.org/resource/image/9c/e7/9cf6ce78e3e74fc0e257bb2cb32c1ae7.png?wh=1489x573)

我让 Agent 帮我分析一下 gintools pod 的日志。得到的返回为：

![图片](https://static001.geekbang.org/resource/image/64/bf/6456bb296ba5c647c116a1b873472abf.png?wh=1489x610)

可以看到 deepseek 模型给出了正确的分析和排查方向。接下来，我们补充给 sa 补充上 watch 权限后，再来测一个列出资源列表的用例。

补充完 watch 权限的 YAML如下：

```yaml
---                                                                                                                                                                      
apiVersion: rbac.authorization.k8s.io/v1                                                                                                                                 
kind: ClusterRole                                                                                                                                                        
metadata:                                                                                                                                                                
  labels:                                                                                                                                                                
    app: example                                                                                                                                                         
  name: sa-example                                                                                                                                                       
rules:                                                                                                                                                                   
  - apiGroups:                                                                                                                                                           
      - ""                                                                                                                                                               
    resources:                                                                                                                                                           
      - pods                                                                                                                                                             
      - pods/log                                                                                                                                                         
      - services                                                                                                                                                         
      - events                                                                                                                                                           
    verbs:                                                                                                                                                               
      - get                                                                                                                                                              
      - list                                                                                                                                                             
      - delete 
      - create  
      - watch                                                                                                                                                                                                                                                                                                                   
  - apiGroups:                                                                                                                                                           
      - ""                                                                                                                                                               
    resources:                                                                                                                                                           
      - namespaces                                                                                                                                                       
    verbs:                                                                                                                                                               
      - get                                                                                                                                                              
      - list
```

需要重新执行以下 kubectl apply。配置完成后，我们来进行测试：

![图片](https://static001.geekbang.org/resource/image/d5/be/d5e4548d39d75ff78f7eff934ba716be.png?wh=1492x572)

结果如下：

![图片](https://static001.geekbang.org/resource/image/01/2c/015450461af591ff2132861fb1916b2c.png?wh=1494x515)

得到了预期的结果。

最后，我们测一下 JSON Mode 的效果，首先不自定义 JSON Schema。在 agent 配置中新增如下配置：

```yaml
apis:
 ...
llm:
 ...
jsonResp:
  enable: true
```

开始测试：

![图片](https://static001.geekbang.org/resource/image/e7/d4/e77f3a7e2d47d59f6ff65c7b6a4a0ed4.png?wh=1490x587)

测试结果：

![图片](https://static001.geekbang.org/resource/image/18/5a/1846e7c319d6e0c73cc46844cfdeaf5a.png?wh=1497x414)

看起来是得到了一坨 JSON，我们让大模型给我们格式化一下，看得更清楚一点：

![图片](https://static001.geekbang.org/resource/image/59/dd/59cc4e4349e1e6607943b2e540c3e4dd.png?wh=1229x294)

![图片](https://static001.geekbang.org/resource/image/67/8c/675e416b78a0ab598ac63f0c56479f8c.png?wh=1114x581)

可以看到，效果非常惊艳，大模型是建立在读懂了 ginTools 返回的内容的基础上，才自动设计了 Schema，并做了 JSON 格式化。自定义 JSON Schema 的方式就留给你当作课后思考题自行测试吧。

## 总结

在本节课中，我们首先回顾并解答了上节课的思考题，探讨了JSON Mode代码在AI Agent插件中的实现方法。接着，我们以第二章和第三章中使用的ginTools工具为例，详细介绍了将Kubernetes服务暴露给插件的两种方式。经过比较，我们最终选择了DNS方式，将ginTools服务配置为Agent Tool，并进行了实际测试。测试结果令人满意，完全符合我们的预期目标。

通过本节课的学习，相信你对AI微服务的特点有了更加直观和清晰的理解。让我们再次总结一下这些特点：

1. **网关具备AI Agent能力**：能够自主调用后端API，实现智能化服务。
2. **前端访问方式的革新**：不再需要直接调用各种API，而是通过自然语言的形式进行交互。
3. **后端输出的自然语言化**：通过JSON Mode规范格式，使输出更加结构化和易于理解。

你可以通过测试更好地理解这几个特点。

## 思考题

在课上，我们测试了让大模型自动 JSON 格式化的效果，感兴趣的话你可以测试一下自定义 JSON Schema 又是什么效果。

欢迎你在留言区分享你的测试效果，我们一起来讨论。如果你觉得这节课的内容对你有帮助的话，也欢迎你分享给其他朋友，我们下节课再见！