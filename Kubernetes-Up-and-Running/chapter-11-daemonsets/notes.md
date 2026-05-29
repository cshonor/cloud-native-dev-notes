# 第十一章：DaemonSets (Chapter 11: DaemonSets)

## DaemonSets 核心定义与场景 (Introduction to DaemonSets)

* **核心定义**：
  * **DaemonSet** 是 Kubernetes 中的一种 API 对象，用于确保在集群的所有节点（或特定的子集节点）上都运行一个 Pod 的副本。
  * 其本质目标是在每个目标节点上部署一个守护进程（Daemon）。
* **适用场景与逻辑对比**：
  * **适用场景**：常用于部署系统级守护进程，例如**日志收集器（log collectors）**（如 fluentd）和**监控代理（monitoring agents）**。
  * **与 ReplicaSet 的核心区别**：ReplicaSet 适用于应用与节点完全解耦的场景，可以在同一节点上运行多个副本；而 DaemonSet 严格要求在每个（或特定）节点上仅运行单个应用程序副本。
  * **错误防范**：如果你的目标是让每个节点只运行一个 Pod，不应通过复杂的调度限制（如反亲和性）来强行控制 ReplicaSet，而应该**直接使用 DaemonSet**。
* **云原生基础设施的一致性价值**：
  * 在动态不可变基础设施（如云环境的自动缩放集群）中，节点的增加或升级往往伴随虚拟机的重建。DaemonSet 可以确保无论底层节点如何动态变化，特定的企业级软件（如合规要求的安全代理）都会被自动安装并运行在每一台新机器上。

> 💡 **后续拓展空间**：可在此引入 Kubernetes 中的静态 Pod（Static Pods）概念，并对比 DaemonSet 与 kubelet 直接管理的静态 Pod 在使用场景、控制平面可见性及更新机制上的本质差异。

---

## DaemonSet 调度器 (DaemonSet Scheduler)

* **调度机制与底层逻辑**：
  * 默认情况下，DaemonSet 会在集群的**每一个节点**上创建一个 Pod 副本。
  * **绕过传统调度器**：DaemonSet 在创建 Pod 时，会直接在 Pod 的规范（`spec`）中指定 `nodeName` 字段。这意味着由 DaemonSet 创建的 Pod **会被 Kubernetes 默认调度器（Scheduler）忽略**，直接被绑定到目标节点。
* **协调循环（Reconciliation Loop）**：
  * 如同其他控制器，DaemonSet 也是由一个协调循环管理的。
  * 它持续比对**期望状态**（Pod 存在于所有目标节点）与**观察状态**（特定节点上是否已有该 Pod）。如果发现某个节点（如新加入集群的节点）缺失该 Pod，控制器会立即响应该状态差并创建 Pod。
* **架构解耦的优势**：
  * DaemonSet 并没有将 Pod 作为其子资源进行强封装，Pod 依然是独立的顶级对象。
  * 这意味着所有用于操作和排查普通 Pod 的工具（如 `kubectl logs <pod-name>`）对 DaemonSet 创建的 Pod **完全适用**，实现了架构上的高度解耦与工具复用。

```
新节点加入 → DaemonSet 协调循环检测 → 在该节点创建 Pod（nodeName 直绑）
```

> 💡 **后续拓展空间**：可以进一步探讨 Kubernetes 版本演进中，DaemonSet 调度机制从 DaemonSet Controller 独立调度转向由 Default Scheduler 统一调度（通过 NodeAffinity 替代 NodeName）的底层架构重构原因。

---

## 创建 DaemonSets (Creating DaemonSets)

* **规范要求**：
  * DaemonSet 在指定的 Kubernetes 命名空间内必须具备**唯一的名称**。
  * 它必须包含一个**Pod 模板规范（Pod template spec）**，用作按需生成 Pod 的图纸。
* **操作命令与生命周期跟踪**：
  * **提交声明**：使用 `kubectl apply -f fluentd.yaml` 将 DaemonSet 提交至 API 服务器。
  * **状态检查**：通过 `kubectl describe daemonset fluentd` 可以查看所需调度的节点数、当前已调度的节点数、以及错调（Misscheduled）的节点数。
  * **拓扑验证**：使用 `kubectl get pods -o wide` 可以清晰地观察到每个生成的 Pod 都精确地分布在集群的不同节点上。
  * **自动化扩容验证**：当新的节点被加入集群时，无需任何人工干预，DaemonSet 控制器会自动在该新节点上部署一个新的 Pod 副本。

```yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluentd
spec:
  selector:
    matchLabels:
      app: fluentd
  template:
    metadata:
      labels:
        app: fluentd
    spec:
      containers:
        - name: fluentd
          image: fluent/fluentd:v1.16
```

```bash
kubectl apply -f fluentd.yaml
kubectl describe daemonset fluentd
kubectl get pods -o wide -l app=fluentd
```

> 💡 **后续拓展空间**：补充 DaemonSet 中 `Tolerations` (容忍度) 的默认行为，解释为何 DaemonSet 的 Pod 能够默认调度到被设置了 `NoSchedule` 污点（Taints）的主节点（Master Node）上。

---

## 将 DaemonSets 限制在特定节点 (Limiting DaemonSets to Specific Nodes)

* **核心场景**：
  * 有些工作负载只应该运行在集群的**子集节点**上。例如：需要运行在暴露于边缘网络的节点上的入侵检测软件，或必须调度到配备了 GPU、高性能 SSD 的节点上的特殊任务。
* **操作流与逻辑链路**：
  1. **为节点添加标签 (Adding Labels to Nodes)**：
     * 使用 `kubectl label nodes <node-name> ssd=true` 命令为目标物理机打上特定标签。
     * 可以通过 `kubectl get nodes --selector ssd=true` 验证标签是否成功应用。
  2. **配置节点选择器 (Node Selectors)**：
     * 在 DaemonSet 的 Pod 模板规范中，定义 `nodeSelector` 字段（如 `ssd: "true"`）。
* **动态控制与易错细节**：
  * **核心结论**：DaemonSet 与标签系统的联动是**动态且严格**的。如果你从某个节点上**移除**了被 DaemonSet 节点选择器所要求的标签，DaemonSet 控制器会立即从该节点上**销毁/驱逐**对应的 Pod。

```bash
kubectl label nodes node-1 ssd=true
kubectl get nodes --selector ssd=true
```

```yaml
spec:
  template:
    spec:
      nodeSelector:
        ssd: "true"
```

> 💡 **后续拓展空间**：引入比 `nodeSelector` 更具表现力的 `nodeAffinity`（节点亲和性）机制，演示如何使用 `In`、`NotIn` 等操作符进行更复杂的 DaemonSet 节点匹配逻辑。

---

## 更新 DaemonSet (Updating a DaemonSet)

* **演进痛点与引入背景**：
  * 在 Kubernetes 1.6 版本之前，更新 DaemonSet 管理的 Pod 是一场灾难：用户必须更新 DaemonSet 配置，然后**手动逐个删除**现有的 Pod，以触发使用新配置的重建。
* **DaemonSet 的滚动更新 (Rolling Update of a DaemonSet)**：
  * **触发机制**：从 1.6 版本开始，通过将 `spec.updateStrategy.type` 设置为 **`RollingUpdate`**，任何对 `spec.template`（如镜像版本）的更改都将自动触发滚动升级。
  * **参数配置与控制公式**：
    1. **`spec.minReadySeconds`**：指定新 Pod 在被系统判定为「健康且滚动可继续」前，必须保持就绪状态的最短时间。建议配置为 **30~60秒**，以防范短时崩溃。
    2. **`spec.updateStrategy.rollingUpdate.maxUnavailable`**：控制滚动更新期间**最大可同时不可用的 Pod 数量**。
  * **策略权衡（爆炸半径控制）**：
    * 设置为 `1` 是最安全的保守策略，但更新总耗时较长（节点数 × `minReadySeconds`）。
    * 增大该值能显著提升部署速度，但一旦配置有误，会扩大故障的**爆炸半径（Blast radius）**。建议默认从 `1` 开始，仅在速度成为明显瓶颈时逐步上调。
  * **状态监控**：使用 `kubectl rollout status daemonSets <name>` 实时追踪更新进度。

```yaml
spec:
  minReadySeconds: 30
  updateStrategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
```

```bash
kubectl apply -f fluentd.yaml
kubectl rollout status daemonset/fluentd
```

> 💡 **后续拓展空间**：结合 `ControllerRevision` 对象，讨论如何在 DaemonSet 滚动更新失败时执行安全的回滚操作（Rollback）。

---

## 删除 DaemonSet (Deleting a DaemonSet)

* **操作命令与级联逻辑**：
  * 通过 `kubectl delete -f <file.yaml>` 或直接指定名称 `kubectl delete ds <name>` 均可删除资源。
  * **默认行为**：这会触发**级联删除（Cascading deletion）**，DaemonSet 及其管理的所有 Pod 都会被立刻销毁。
* **孤儿模式（Orphaning / 保留 Pod）**：
  * **实用要点**：若仅想移除控制层面的 DaemonSet 对象，而不影响当前正在节点上运行的 Daemon 进程，需追加 **`--cascade=false`** 参数。

```bash
kubectl delete daemonset fluentd
kubectl delete daemonset fluentd --cascade=orphan
```

> 💡 **后续拓展空间**：探讨在生产环境中级联删除引发的服务瞬断风险，以及如何平滑地将 DaemonSet 管理的 Pod 迁移为其他资源控制器管理的方法。

---

## 总结 (Summary)

* **核心价值提炼**：
  * DaemonSet 为在 Kubernetes 集群的所有节点（或基于标签过滤的子集节点）上运行进程提供了易用且原生的抽象。
  * 自带独立的控制器与调度逻辑，专注于保障**基础设施级服务**（如监控、日志、网络插件等）的绝对覆盖率。
* **架构高阶意义**：
  * 不同于关注横向并发算力的传统 Web 业务，DaemonSet 赋予了 Kubernetes 集群**自管理、自装备**的能力。
  * 特别是在自动缩放（Autoscaled）的云原生集群中，节点的增减无需人为干预，DaemonSet 能确保任何新弹出的节点在接管业务流量前，自动配置好必需的底层代理软件。

> 💡 **后续拓展空间**：承接后续章节（如存储或安全），讨论 DaemonSet 挂载高权限 `hostPath` 和配置 `privileged: true` 时的安全风险防范（如 Pod Security Policies / Pod Security Admission）。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| DaemonSet | 每节点（或子集）一个 Pod 副本 |
| vs ReplicaSet | RS 横向扩缩；DS 按节点铺守护进程 |
| 调度 | 默认直绑 `nodeName`，绕过 Scheduler |
| 典型场景 | 日志收集、监控代理、网络插件 |
| nodeSelector | 限制 DS 只跑带特定标签的节点 |
| 标签移除 | 节点标签被删 → Pod 立即被驱逐 |
| RollingUpdate | 改 template 自动滚动；`maxUnavailable` 控速度 |
| minReadySeconds | 新 Pod Ready 后等待 N 秒再继续 |
| 删除 | 默认级联删 Pod；`--cascade=orphan` 保留 |
