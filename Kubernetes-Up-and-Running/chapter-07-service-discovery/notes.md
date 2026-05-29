# 第七章：服务发现 (Chapter 7: Service Discovery)

## 什么是服务发现？ (What Is Service Discovery?)

* **核心定义**：
  * **服务发现（Service Discovery）**是一类用于解决「如何找到哪些进程正在哪些地址上监听哪些服务」问题的工具和机制。
  * 一个优秀的服务发现系统需要能够快速、可靠、低延迟地解析这些信息，并且能够存储更丰富的服务定义（例如关联多个端口）。
* **逻辑脉络与传统痛点**：
  * **动态性带来的挑战**：Kubernetes是一个高度动态的系统，会自动将Pod调度到节点上、确保其运行，甚至基于负载进行水平自动扩缩容。传统的网络基础设施并非为这种高度动态的环境而设计。
  * **DNS的局限性**：域名系统（DNS）是互联网上传统的服务发现系统，其设计初衷是相对稳定的名称解析和广泛高效的缓存。然而在Kubernetes的动态世界中，许多系统（例如默认状态下的Java）会直接查询DNS而不重新解析，导致客户端**缓存了过期的映射**，从而向错误的IP发送请求。此外，标准DNS难以处理单个域名下超过20-30个A记录的情况，且客户端通常只取第一个IP，无法替代真正的负载均衡机制。

> 💡 **后续拓展空间**：可在此处延伸讨论Kubernetes中CoreDNS的架构实现，以及它是如何通过短TTL机制和集成Kubernetes API来缓解传统DNS缓存带来的一致性问题。

---

## 服务对象 (The Service Object)

* **核心定义**：
  * 真正的Kubernetes服务发现始于**服务对象（Service Object）**。本质上，Service对象是一种创建**命名标签选择器（Named label selector）**的途径。
* **操作命令与机制**：
  * 通过 `kubectl expose deployment <name>` 命令可以快速从Deployment创建一个Service。
  * 该命令会自动从Deployment定义中提取标签选择器以及相关端口配置。
  * **集群IP（Cluster IP）**：系统会为Service分配一种新型的虚拟IP，称为Cluster IP。系统会自动将流量负载均衡到被该服务选择器识别出的所有Pod上。

```bash
kubectl expose deployment alpaca-prod --port=80 --target-port=8080
kubectl get svc
```

### 服务 DNS (Service DNS)

* **核心机制与逻辑**：
  * 由于Cluster IP是虚拟且稳定的，因此为其分配一个DNS地址是非常合理的。这彻底消除了客户端缓存DNS结果带来的过期问题。
  * Kubernetes提供了一个运行在集群内的DNS服务（本身作为Kubernetes系统组件部署），专门为Cluster IP提供DNS名称。
* **DNS命名规范与层级拆解**：
  * 完整的DNS名称示例为 `alpaca-prod.default.svc.cluster.local.`。
  * `alpaca-prod`：当前查询的**服务名称**。
  * `default`：该服务所在的**命名空间（Namespace）**。
  * `svc`：标识这是一个**服务（Service）**类型的资源，为未来Kubernetes通过DNS暴露其他类型的资源预留了空间。
  * `cluster.local.`：集群的**基础域名（Base domain）**。管理员可对其进行修改，以便在多集群环境中实现唯一的DNS命名。
* **实用要点**：
  * 在同一命名空间内，可直接使用短名称（如 `alpaca-prod`）访问；跨命名空间可通过 `<service-name>.<namespace>` 访问。

```
alpaca-prod.default.svc.cluster.local
    │         │      │        │
  服务名   命名空间  类型   集群基础域
```

### 就绪检查 (Readiness Checks)

* **引入背景与逻辑**：
  * 应用启动时通常需要时间进行初始化（从零点几秒到几分钟不等）。在此期间，应用并未准备好处理请求。Service对象的一大关键特性是能够通过**就绪检查（Readiness Checks）**来跟踪哪些Pod已准备就绪。
* **配置要点与关键参数**：
  * 就绪探针附加在Pod模板的容器定义下。
  * 关键参数包括：`path` 和 `port`（检查端点）、`periodSeconds`（检查频率，如每2秒一次）、`failureThreshold`（连续失败几次后判定为未就绪，默认通常为3次）、`successThreshold`（成功几次后判定为就绪，通常为1次）。
* **因果关系与核心结论**：
  * **核心结论**：**只有处于就绪（Ready）状态的Pod才会接收到流量**。
  * **优雅关闭（Graceful Shutdown）**：就绪检查也是一种允许过载或「生病」的服务器向系统发出「停止接收新流量」信号的方式。服务器可以在准备退出前主动让就绪检查失败，等待现有连接处理完毕后再干净地退出。

```yaml
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  periodSeconds: 2
  failureThreshold: 3
  successThreshold: 1
```

> 💡 **后续拓展空间**：深入探讨Readiness Probes与Liveness Probes的联动策略，以及在数据库连接池耗尽等极端边界情况下的探针设计模式。

---

## 展望集群之外 (Looking Beyond the Cluster)

* **引入背景**：
  * 通常Pod的IP只能在集群内部访问。但在实际应用中，最终必须允许外部流量进入。
* **NodePort机制**：
  * **定义**：**NodePort** 是将服务暴露到集群外部的最具可移植性的方式。
  * **机制逻辑**：除了分配Cluster IP外，系统还会挑选一个物理端口（用户也可手动指定），随后**集群中的每一个节点（Node）**都会将对该端口的流量转发至对应的服务。
  * **优势**：只要能访问集群中任何一个节点，就能访问该服务。客户端无需知道该服务的Pod具体运行在哪个节点上。该特性常与硬件或软件负载均衡器结合使用以作进一步暴露。
  * 配置方式：修改Service的 `spec.type` 为 `NodePort`。

```yaml
spec:
  type: NodePort
  ports:
    - port: 80
      targetPort: 8080
      nodePort: 30080
```

### 云集成 (Cloud Integration)

* **核心机制 (LoadBalancer)**：
  * 如果底层云提供商支持，可将 `spec.type` 修改为 `LoadBalancer`。
  * 该类型在NodePort的基础上，进一步指示云平台自动创建并配置一个新的云端原生负载均衡器，并将流量引导至集群内的节点。
* **易错细节**：
  * 刚创建或修改为 `LoadBalancer` 后，`EXTERNAL-IP` 列最初会显示为 `<pending>`，由于云端资源的调配需要时间，获取公共地址通常需要等待几分钟。
  * 不同云厂商的返回格式可能不同（例如GCP和Azure返回IP地址，而AWS返回DNS主机名）。

```yaml
spec:
  type: LoadBalancer
```

| 类型 | 访问范围 | 典型场景 |
|------|----------|----------|
| ClusterIP | 仅集群内 | 微服务互访（默认） |
| NodePort | 节点 IP + 端口 | 开发测试、无云 LB |
| LoadBalancer | 公网/云 LB | 生产对外暴露 |

> 💡 **后续拓展空间**：可以进一步讨论 `externalTrafficPolicy: Local` 对NodePort和LoadBalancer流量路径中源IP保留及网络跳数优化的影响。

---

## 高级细节 (Advanced Details)

* Kubernetes被设计为一个可扩展的系统，理解Service底层的实现细节有助于排障和构建更高级的集成系统。

### 端点 (Endpoints)

* **核心概念与逻辑**：
  * 在某些场景下，系统或应用需要直接与服务通信，而不经过Cluster IP。这是通过**端点（Endpoints）对象**实现的。
  * 对于每一个Service对象，Kubernetes会自动创建一个与之同名的「伙伴」Endpoints对象，其中包含了该服务所有可用Pod的IP地址清单。
* **高阶用法**：
  * 高级应用可以通过直接调用Kubernetes API来查找和调用端点。
  * 利用Kubernetes API的「监听（Watch）」机制（如 `kubectl get endpoints <name> --watch`），客户端可以在服务端点关联的IP地址发生变化的瞬间立即做出反应。

```bash
kubectl get endpoints alpaca-prod
kubectl get endpoints alpaca-prod --watch
```

### 手动服务发现 (Manual Service Discovery)

* **底层机制揭秘**：
  * Kubernetes服务建立在对Pod的标签选择器之上。因此，即使不使用Service对象，也完全可以通过调用API进行手动的服务发现。
* **操作与痛点**：
  * 通过 `kubectl get pods -o wide --selector=app=alpaca,env=prod` 命令可以直接过滤出对应的Pod及IP。
  * **痛点**：在复杂的系统中，手动保持和同步正确的标签集合极其困难，这就是为什么需要抽象出Service对象的原因。

### kube-proxy与集群IP (kube-proxy and Cluster IPs)

* **工作原理脉络**：
  * Cluster IP是一种稳定的虚拟IP，通过负载均衡将流量分发至服务下的所有端点。这一魔法是由运行在每个节点上的 **`kube-proxy` 组件** 实现的。
  * `kube-proxy` 持续监听API Server中的服务变化。当有新服务创建或端点发生变化（因Pod销毁/新建或就绪状态改变）时，它会**在当前宿主机的内核中重写一组iptables规则**，将发往Cluster IP的包的目标地址改写为对应的服务端点IP。
* **配置约束**：
  * 集群IP地址范围通过 `kube-apiserver` 的 `--service-cluster-ip-range` 参数配置。
  * **易错细节**：服务IP地址段**绝不能**与任何Docker网桥或Kubernetes节点分配的IP子网重叠。

### 集群IP环境变量 (Cluster IP Environment Variables)

* **遗留机制**：
  * 除了首选的DNS方式，Kubernetes还在Pod启动时向其注入一组包含集群IP的环境变量（如 `ALPACA_PROD_SERVICE_HOST` 和 `ALPACA_PROD_SERVICE_PORT`）。
* **操作禁忌与防错**：
  * **反模式**：这种基于环境变量的注入机制要求资源创建具有**严格的时间顺序限制**——即Service对象必须在其关联的Pod被创建**之前**就已存在，否则Pod中无法注入该环境变量。
  * 这会给复杂应用的部署引入巨大的复杂性。**强烈建议优先使用DNS进行服务发现**。

> 💡 **后续拓展空间**：可补充介绍 Kubernetes 引入的 EndpointSlice API 是如何解决传统 Endpoints API 在单个服务管理成千上万个Pod时带来的 etcd 性能瓶颈问题的。

---

## 与其他环境连接 (Connecting with Other Environments)

* **核心主旨与业务场景**：
  * 现实世界中的应用通常需要将部署在Kubernetes中的云原生应用与部署在传统环境（如虚拟机）或本地（On-premise）机房的遗留基础设施集成。
* **两大集成方案逻辑**：
  1. **无选择器的服务（Services Without Selectors）**：
     * 应对外部服务（如遗留数据库）的最佳实践。通过创建一个没有标签选择器的Service，并在同名Endpoints或通过 `type: ExternalName` 指定外部服务的DNS/固定IP。
     * **效果**：集群内的Pod可以像访问原生Kubernetes Service一样使用内部DNS，但网络流量实际上被重定向到了集群外部资源。
  2. **将外部资源接入集群**：
     * 如果云平台支持，可以通过创建「内部」负载均衡器（位于VPC内），将固定IP暴露给外部资源，再通过DNS解析。
     * 在纯本地环境中，甚至可以在外部机器上直接运行完整的 `kube-proxy` 并将其配置为使用集群内部的DNS，但这极度复杂且仅限于特定内网环境。

```yaml
# ExternalName：将 Service DNS 映射到外部域名
apiVersion: v1
kind: Service
metadata:
  name: legacy-db
spec:
  type: ExternalName
  externalName: db.example.com
```

> 💡 **后续拓展空间**：探讨Service Mesh（如Istio的ServiceEntry资源）或Consul架构在多集群和异构跨云环境中的流量路由和安全管控最佳实践。

---

## 清理工作 (Cleanup)

* **操作命令**：
  * 可以使用标签选择器批量删除本章创建的所有服务和部署：`kubectl delete services,deployments -l app`。

```bash
kubectl delete services,deployments -l app
```

---

## 总结 (Summary)

* **核心论点归纳**：
  * Kubernetes作为高度动态的系统，颠覆了传统的命名和服务连接方式。**服务对象（Service Object）**提供了一种强大且灵活的方式，无论是将服务暴露在集群内部还是集群外部。
  * 掌握Kubernetes中动态服务发现的机制是释放其全部潜力的关键。一旦应用能够动态查找服务并适应动态部署，开发者即可摆脱对基础设施（物理机及网络拓扑）的静态依赖，将精力聚焦于业务逻辑。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| Service | 命名标签选择器 + 稳定 Cluster IP + 负载均衡 |
| DNS | `<svc>.<ns>.svc.cluster.local`；同 ns 可用短名 |
| Readiness | 未就绪 Pod 不接收 Service 流量 |
| ClusterIP | 集群内访问（默认） |
| NodePort | 每节点固定端口，最具可移植性 |
| LoadBalancer | 云厂商自动创建外部 LB |
| Endpoints | Service 的 Pod IP 清单，可 Watch |
| kube-proxy | 每节点 iptables/IPVS 实现 Cluster IP 转发 |
| 环境变量发现 | 反模式；Service 须先于 Pod 创建 |
| ExternalName | 集群 DNS 指向外部服务 |
