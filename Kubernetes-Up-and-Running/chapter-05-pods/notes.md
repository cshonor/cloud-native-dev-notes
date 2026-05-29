# 第五章：Pods (Chapter 5: Pods)

## Kubernetes中的Pods (Pods in Kubernetes)

* **核心定义**：
  * **Pod**是Kubernetes中最小的可部署和管理的基本计算单元，代表在同一执行环境中运行的一个或多个应用容器及卷的集合。
  * 同一个Pod中的所有容器永远会被调度并运行在同一台机器（Node）上。
* **资源与网络隔离逻辑**：
  * Pod内的每个容器运行在自己的**cgroup**中，但它们共享一组Linux命名空间（Namespaces）。
  * **网络与通信**：Pod内的应用共享相同的IP地址和端口空间（网络命名空间），拥有相同的主机名（UTS命名空间），并可以通过System V IPC或POSIX消息队列进行原生的进程间通信（IPC命名空间）。
  * **边界与隔离**：不同Pod中的应用彼此完全隔离，拥有不同的IP地址和主机名，如同运行在不同的独立服务器上。
* **易错细节**：
  * 容器（Container）并非Kubernetes的最小调度单元，**Pod才是真正的原子调度单位**。

> 💡 **后续拓展空间**：可在此补充Linux cgroup与namespace的底层技术原理，以及跨Pod通信的CNI网络插件实现机制。

---

## Pods的设计思维 (Thinking with Pods)

* **核心主旨**：如何决定哪些容器应该放入同一个Pod？
* **逻辑脉络与判断准则**：
  * 判断的核心问题是：「**如果这些容器分别落在不同的机器上，它们还能否正常工作？**」。
  * 如果答案是「不能」（例如两个容器必须通过本地文件系统高频交互），则它们应该被分在同一个Pod中。
  * 如果答案是「能」，则它们应该被部署在多个不同的Pod中。
* **案例分析：WordPress与MySQL**：
  * **反模式（Anti-pattern）**：将WordPress容器和MySQL数据库容器放在同一个Pod中是典型的架构反模式。
  * **因果关系**：WordPress和数据库之间通过网络通信，并非强共生关系。此外，两者的**扩缩容策略完全不同**：WordPress是无状态的，可以通过增加Pod数量来横向扩容（Scale out）；而MySQL是状态强相关的，通常需要增加单实例的资源分配（Scale up）。如果将它们强行绑定在同一个Pod中，将迫使两者采用相同的扩缩容策略，导致资源浪费或架构僵化。

> 💡 **后续拓展空间**：可在此补充Pod中常见的「边车模式」（Sidecar Pattern）案例，如日志收集Sidecar或Service Mesh代理（如Envoy）。

---

## Pod清单 (The Pod Manifest)

* **关键定义**：
  * **Pod清单（Manifest）**是Kubernetes API对象的文本文件表示，采用**声明式配置（Declarative Configuration）**理念。
* **声明式与命令式的逻辑对比**：
  * **命令式（Imperative）**：用户记录一系列变更动作（如 `apt-get install`）来改变系统状态，难以维护和回滚。
  * **声明式（Declarative）**：用户写下期望的系统目标状态，Kubernetes系统负责采取行动使实际状态与期望状态一致。这便于代码审查、版本控制，并构成了Kubernetes自愈（Self-healing）行为的基础。
* **调度与因果脉络**：
  * API服务器接收到Pod清单后，将其持久化存储到etcd中。
  * **调度器（Scheduler）**利用API寻找未被调度的Pod，根据清单中的资源需求和约束，将Pod分配到健康的节点（Node）上。
  * 出于可靠性考虑，调度器会尽量将同一应用的多个Pod副本分散调度到不同的物理机器上，避免单点故障。
  * **核心结论**：Pod一旦被调度到某个节点，就不会发生移动；如果需要迁移，必须显式销毁并重新调度。
* **清单结构与代码要点**：
  * 清单通常使用**YAML**编写，便于人类阅读和添加注释。
  * 核心字段包括：`metadata`（包含名称和标签）、`spec`（描述卷）、以及需要运行的 `containers` 列表。

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-pod
  labels:
    app: my-app
spec:
  containers:
    - name: app
      image: nginx:alpine
```

> 💡 **后续拓展空间**：可在此补充Pod清单中 `NodeSelector`、`Taints/Tolerations` 以及亲和性/反亲和性（Affinity）的高级调度策略配置。

---

## 运行Pods (Running Pods)

* **操作命令与生命周期**：
  * **创建**：使用 `kubectl apply -f <file.yaml>` 提交清单。
  * **状态查看**：使用 `kubectl get pods` 列出当前运行的Pod，初始状态为 `Pending`（已提交但尚未调度），成功后转为 `Running`。
  * **详情排查**：使用 `kubectl describe pods <pod-name>` 可查看Pod分配的节点、IP、标签、容器状态及底层事件（Events）。
* **Pod销毁与优雅终止（Graceful Shutdown）**：
  * 删除命令：`kubectl delete pods/<name>` 或 `kubectl delete -f <file.yaml>`。
  * **逻辑脉络**：Pod被删除时并不会被立即杀死，而是进入 `Terminating` 状态。所有Pod默认拥有**30秒的终止宽限期（Termination Grace Period）**。
  * **实用要点**：宽限期对于服务的可靠性至关重要，它确保Pod停止接收新请求，并允许其在被强行终止前处理完仍在进行中的活跃请求。
* **易错细节**：
  * 删除Pod将同步删除其关联的容器内的所有数据。如果需要跨Pod实例持久化数据，必须使用**持久卷（PersistentVolumes）**。

> 💡 **后续拓展空间**：可补充Pod生命周期的完整状态机（Pending → Running → Succeeded/Failed/Unknown）及 `preStop` 钩子函数的使用。

---

## 访问你的Pod (Accessing Your Pod)

* **实用调试工具矩阵**：
  1. **端口转发（Port Forwarding）**：
     * 命令：`kubectl port-forward <pod-name> <local-port>:<remote-port>`。
     * 原理：在本地机器与工作节点上的Pod之间，通过Kubernetes Master建立一条安全的网络隧道，无需将服务暴露至公网即可进行访问测试。
  2. **日志查看（Logs）**：
     * 命令：`kubectl logs <pod-name>`。添加 `-f` 参数可实现日志持续追踪流（stream）。
     * 添加 `--previous` 标志可以获取已崩溃/重启的上一实例的日志，对排查启动失败的容器极其有用。
  3. **容器内执行命令（Exec）**：
     * 命令：`kubectl exec -it <pod-name> -- bash`，可进入容器内部获取交互式Shell环境进行深度排查。
  4. **文件拷贝（Copy）**：
     * 命令：`kubectl cp <pod-name>:<remote-path> <local-path>`。
* **操作禁忌与防错**：
  * **核心警告**：向容器内直接拷贝文件并修改（热修复）被视为**架构反模式（Anti-pattern）**。容器应当被视为**不可变基础设施（Immutable）**，虽然热修复能暂时止血，但如果没有同步更新镜像并重新部署，这些变更将在下一次常规滚动更新中被彻底覆盖丢失。

> 💡 **后续拓展空间**：可引入日志聚合系统（如EFK/ELK技术栈或Fluentd架构）的最佳实践，替代单Pod级别的日志调试方法。

---

## 健康检查 (Health Checks)

* **核心机制与痛点**：
  * 默认的进程级健康检查仅确认主进程是否在运行，但对于发生**死锁（Deadlock）**的进程束手无策，此时进程仍在运行但已无法处理请求。
* **两种探针机制（Probes）**：
  1. **存活探针（Liveness Probe）**：
     * **定义**：判断应用是否正常运行。运行应用特定的逻辑验证（如加载网页）。
     * **结论**：未通过Liveness检查的容器将被**强制重启（Restarted）**。
  2. **就绪探针（Readiness Probe）**：
     * **定义**：判断容器是否已准备好处理用户请求（特别是启动时期的初始化阶段）。
     * **结论**：未通过Readiness检查的容器将被**从服务负载均衡器中移除（Removed from service load balancers）**，直到其恢复健康。
* **探针类型与参数公式**：
  * **类型**：支持 `httpGet`（HTTP状态码≥200且<400为成功）、`tcpSocket`（成功建立TCP连接为成功）以及 `exec`（执行脚本，返回值为0为成功）。
  * **关键参数**：`initialDelaySeconds`（容器启动后延迟执行的时间）、`timeoutSeconds`（超时判定限制）、`periodSeconds`（检查执行的频率）、`failureThreshold`（判定失败的最大连续失败次数）。
* **重启策略（RestartPolicy）**：
  * 选项包括：`Always`（默认）、`OnFailure` 或 `Never`。

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
readinessProbe:
  httpGet:
    path: /ready
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 3
```

> 💡 **后续拓展空间**：深入探讨如何结合 Readiness Probe 和 Liveness Probe 应对高并发场景下的「雪崩效应」，以及Kubernetes 1.16+ 引入的 `Startup Probe`。

---

## 资源管理 (Resource Management)

* **核心目标与逻辑**：
  * 容器编排的关键经济价值在于提升计算节点的**利用率（Utilization）**。利用率 = 正在使用的资源 / 购买的资源总数。
  * Kubernetes允许精确定义资源需求，使得调度器能够计算出最优的容器装箱（Resource packing）方案，从而将节点利用率推高至50%以上。
* **资源请求与限制的区别**：
  1. **资源请求（Resource Requests）**：
     * **定义**：运行应用所需的**最低资源量**。
     * **机制**：调度器依据Requests寻找合适的节点。节点上所有Pod的Requests总和绝不会超过该节点的实际容量。因此，Pod被**保证（Guaranteed）**获得所请求的资源。
  2. **资源限制（Resource Limits）**：
     * **定义**：应用可以消耗的**最大资源上限**。
     * **机制**：通过内核特性进行限制，当系统空闲时Pod可以使用超出Requests但低于Limits的资源，但这部分属于「尽力而为（Best-effort）」保障。
* **CPU与内存的底层逻辑差异**：
  * **CPU**：使用Linux内核的 `cpu-shares` 功能实现。属于可压缩资源，如果触及Limits，只会被限流（Throttled），容器继续运行。
  * **内存**：属于不可压缩资源。由于操作系统无法直接从进程中剥离已分配的内存，当系统内存耗尽或容器超过其内存Limits时，kubelet将**强行终止（Terminated / OOMKilled）**该容器。随后容器将被重启。

```yaml
resources:
  requests:
    cpu: 500m
    memory: 128Mi
  limits:
    cpu: 1000m
    memory: 256Mi
```

> 💡 **后续拓展空间**：可补充 `LimitRange` 和 `ResourceQuota` 这两个命名空间级别的资源管控组件的使用场景。

---

## 使用卷持久化数据 (Persisting Data with Volumes)

* **引入背景**：
  * 当Pod被删除或容器重启时，容器文件系统内的所有数据都会丢失。对于有状态应用，必须通过挂载卷来解决数据持久化问题。
* **配置规范**：
  * 需要在Pod清单中添加两个关键段落：`spec.volumes`（定义Pod级别可用的卷）和在具体容器下的 `volumeMounts`（定义卷挂载至容器内部的具体路径）。
* **四大核心应用模式（Patterns）**：
  1. **通信/同步（Communication/synchronization）**：
     * 使用 `emptyDir` 卷，其生命周期与Pod绑定。同一个Pod中的多个容器可通过该共享目录通信（如：Git拉取容器和Web服务容器共享目录）。
  2. **缓存（Cache）**：
     * 同样使用 `emptyDir`，将重建成本较高的数据作为缓存写入其中，确保容器因健康检查失败重启时，缓存依然存在。
  3. **持久化数据（Persistent data）**：
     * 使用网络存储协议（如NFS, iSCSI）或云提供商的云盘（AWS EBS, Azure Disk, GCE Persistent Disk）。数据完全独立于Pod的生命周期，即使Pod在集群中的另一台机器上重启，云端卷也会自动挂载至新机器，确保数据不丢失。
  4. **挂载主机文件系统（Mounting the host filesystem）**：
     * 使用 `hostPath` 卷，将底层工作节点（Node）的指定绝对路径暴露给容器（如访问底层的 `/dev` 文件系统）。

> 💡 **后续拓展空间**：结合后文的 PersistentVolume (PV)、PersistentVolumeClaim (PVC) 及 StorageClass，延伸出动态卷配置（Dynamic Volume Provisioning）的高阶知识点。

---

## 综合应用 (Putting It All Together)

* **架构全景结论**：
  * 一个真正具备生产可用性的有状态Pod，是多种原子能力的结合体：**持久卷（Persistent Volumes）**保障数据不丢 + **存活/就绪探针（Health Probes）**保障服务可用性 + **资源请求与限制（Resource Restrictions）**保障调度安全与性能边界。
* **案例范式**：
  * `kuard-pod-full.yaml` 将上述知识点融合，展示了NFS网络挂载、HTTP双探针、500m CPU与128Mi内存请求、及严苛的容错时间阈值。

> 💡 **后续拓展空间**：进一步过渡到ReplicaSet和Deployment组件，解释当管理成百上千个此类Pod时，如何利用上层控制器实现自动化的故障转移与版本滚动升级。

---

## 总结 (Summary)

* **核心论点归纳**：
  * Pod是Kubernetes集群中工作的原子单位，本质是存在**共生关系（Symbiotically）**的容器的组合。
  * 用户不应直接通过HTTP调用API Server，而应提交Pod清单。调度器（Scheduler）接管寻找适配机器的工作，由目标机器上的守护进程（Kubelet）负责启动容器并执行配置好的健康检查。
  * **限制与下一步演进**：裸Pod在分配到节点后，如果该物理节点宕机，**Pod不会被自动重新调度**。且手动管理多个同质Pod极度繁琐。因此，在实际生产中必须引入上层的控制器资源——**ReplicaSets（副本集）**，来实现实例的自动修复和多副本管理。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| Pod | 最小调度单元，同 Pod 容器共享网络/IPC/UTS 命名空间 |
| 设计准则 | 分开部署后仍能工作的容器，不应放同一 Pod |
| Manifest | 声明式 YAML，`metadata` + `spec` + `containers` |
| Liveness | 失败 → 重启容器 |
| Readiness | 失败 → 从 Service 摘除，不重启 |
| Requests | 调度保证的最低资源 |
| Limits | 可消耗上限；内存超限 OOMKilled |
| emptyDir | Pod 级临时/共享存储 |
| 裸 Pod 局限 | 节点宕机不自动迁移，需 ReplicaSet/Deployment |
