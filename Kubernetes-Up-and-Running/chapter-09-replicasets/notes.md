# 第九章：ReplicaSets (Chapter 9: ReplicaSets)

## ReplicaSets 核心定义与场景 (Introduction to ReplicaSets)

* **引入背景与痛点**：
  * 裸 Pod 本质上是一次性的单例（Singletons）。在真实的生产环境中，通常需要同时运行一个容器的多个副本，其核心动机包括：**冗余容灾（Redundancy）**、**横向扩展（Scale）**以及**分片并行计算（Sharding）**。
  * 手动创建和管理多个极其相似的 Pod 清单既繁琐又容易出错。
* **核心定义**：
  * **ReplicaSet** 充当集群级别的 Pod 管理器，是一个将其管理的 Pod 集合视为单一实体进行定义的 API 对象。
  * 它确保在任何给定时间，集群中都运行着**正确类型**且**正确数量**的 Pod 副本。
  * **逻辑比喻**：ReplicaSet 就像是将「**饼干模具（Cookie cutter，即 Pod 模板）**」和「**期望的饼干数量（Desired number of replicas）**」结合在一起的抽象引擎。

> 💡 **后续拓展空间**：可在此补充 ReplicaSet 与 Kubernetes 早期版本中 ReplicationController (RC) 的演进历史，以及标签选择器支持表达能力上的底层差异。

---

## 协调循环 (Reconciliation Loops)

* **核心机制与逻辑脉络**：
  * **协调循环（Reconciliation Loops）**是 Kubernetes 系统设计与实现的最底层基石。
  * **期望状态（Desired state） vs 观察状态（Observed/Current state）**：期望状态是用户在清单中声明的目标（例如：要求运行 3 个 kuard Pod）；观察状态是系统当前实际的运行情况（例如：由于节点宕机，当前只有 2 个在运行）。
  * 协调循环是一个**持续运行（Constantly running）**的后台引擎，不断对比期望状态与观察状态。一旦发现偏差，它立即采取行动（如创建新 Pod 或销毁多余 Pod），努力使实际状态收敛于期望状态。
* **设计优势**：
  * 这是一个天生以目标为导向的**自愈（Self-healing）**系统。ReplicaSet 只需要通过一个极简的循环逻辑，就能同时应对用户的扩缩容操作、物理节点的宕机崩溃、以及网络分区等复杂的分布式故障。

```
期望状态 (YAML)  ←→  协调循环  ←→  观察状态 (实际 Pod 数)
     replicas: 3         持续对比          当前: 2 → 创建 1 个
```

> 💡 **后续拓展空间**：可深入解析 Kubernetes 控制平面中 Controller Manager 的底层架构，包括 Informer 机制、工作队列（WorkQueue）以及 Level-triggered（基于状态）与 Edge-triggered（基于事件）设计的本质区别。

---

## 关联 Pod 与 ReplicaSet (Relating Pods and ReplicaSets)

* **核心架构理念：解耦（Decoupling）**：
  * ReplicaSet **并不真正「拥有（Own）」**它们所创建的 Pod。相反，ReplicaSet 与 Pod 之间是极其松散的解耦关系。
  * **机制**：ReplicaSet 完全依赖**标签查询（Label queries / Selectors）**来识别并纳管它应该管理的 Pod 集合。
* **解耦带来的两大高级操作模式**：
  1. **接管现有容器 (Adopting Existing Containers)**：
     * **场景**：最初为了测试手动（命令式）部署了一个单例 Pod 且正在提供服务。现在希望将其升级为受控的高可用集群。
     * **逻辑**：由于松耦合，只需创建一个标签选择器匹配该运行中 Pod 的 ReplicaSet，ReplicaSet 就会自动「收编（Adopt）」这个现有 Pod，并根据需要扩容出新的副本，全程**零停机时间（No downtime）**。
  2. **隔离故障容器 (Quarantining Containers)**：
     * **场景痛点**：应用发生异常（如死锁、内存泄漏），但进程依然存活骗过了健康检查。如果直接杀死 Pod 重启，现场数据和内存快照将全部丢失，使得开发人员只能对着残缺的日志盲目排障。
     * **解决方案**：通过 `kubectl label` 命令手动**修改该故障 Pod 的标签**。这会使该 Pod 瞬间脱离 ReplicaSet 和 Service 的纳管边界（不再接收线上流量）。ReplicaSet 发现副本数减一，会立即创建一个新的健康 Pod 补齐算力。而那个故障的 Pod 则被完美隔离，开发人员可以从容地进入其中（通过 `exec` 或 `port-forward`）进行深度的交互式调试。

```bash
# 隔离故障 Pod：改掉标签使其脱离 ReplicaSet 选择器
kubectl label pod faulty-pod app=kuard-debug --overwrite
```

> 💡 **后续拓展空间**：可在此补充 Kubernetes Owner References（属主引用）机制，解释在垃圾回收（Garbage Collection）时标签与属主引用是如何协同工作的。

---

## ReplicaSet 的设计思维 (Designing with ReplicaSets)

* **核心主旨**：
  * ReplicaSet 被设计用来代表架构中一个单一的、可横向扩展的**微服务（Microservice）**。
  * 由 ReplicaSet 生成的所有 Pod 必须是**完全同质（Homogeneous）且可互换的（Interchangeable）**。
* **适用边界**：
  * 它主要适用于**无状态（Stateless）或近乎无状态**的服务。
  * **缩容逻辑**：当执行缩容时，系统会**任意/随机选择（Arbitrary）**一个 Pod 进行销毁。因此，应用架构必须保证销毁其中任何一个节点都不会对整体业务逻辑造成破坏。

> 💡 **后续拓展空间**：对比 StatefulSet 的有序缩容与持久化状态保留机制，进一步明确 ReplicaSet 在无状态服务中的专职定位。

---

## ReplicaSet 规范 (ReplicaSet Spec)

* **清单结构与代码要点**：
  * 必须包含全局唯一的 `metadata.name`。
  * `spec.replicas`：声明期望同时运行的副本数量。
  * `spec.template`：定义当副本数不足时，用于生成新 Pod 的**Pod 模板（Pod Template）**。
* **核心元素拆解**：
  1. **Pod 模板 (Pod Templates)**：
     * 相当于「饼干模具」。ReplicaSet 控制器利用此模板自动向 API Server 提交生成实际 Pod 对象的请求。
  2. **标签与选择器 (Labels & Selector)**：
     * **核心机制**：ReplicaSet 依据 `spec.selector.matchLabels` 过滤并追踪集群内的 Pod 数量。
     * **硬性规则与易错细节**：在 ReplicaSet 的定义中，**选择器（Selector）中声明的标签必须是 Pod 模板（Template）中声明的标签的真子集（Proper subset）或完全一致**。如果模板生成的 Pod 缺失了选择器所需的标签，控制器将无法识别自己创建的 Pod，进而导致陷入疯狂无限创建新 Pod 的灾难级死循环。

```yaml
apiVersion: apps/v1
kind: ReplicaSet
metadata:
  name: kuard-rs
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kuard
      version: "2"
  template:
    metadata:
      labels:
        app: kuard
        version: "2"
    spec:
      containers:
        - name: kuard
          image: gcr.io/kuar-demo/kuard-amd64:2
          ports:
            - containerPort: 8080
```

> 💡 **后续拓展空间**：可在此引入 ReplicaSet 规范中 `minReadySeconds` 属性的用法，解释其在防止因短时崩溃导致的集群级抖动中的作用。

---

## 创建 ReplicaSet (Creating a ReplicaSet)

* **操作命令**：
  * 将定义好的 YAML 文件通过 `kubectl apply -f <file.yaml>` 提交至 Kubernetes API。
* **执行逻辑**：
  * 提交后，控制器被唤醒。检测到当前匹配选择器的 Pod 数量为 0，而期望数量为 N。随后依据模板自动创建 N 个 Pod 实例。

```bash
kubectl apply -f kuard-rs.yaml
kubectl get rs,pods
```

> 💡 **后续拓展空间**：可补充通过 API 调用直接构建和提交 ReplicaSet 对象的客户端代码（如 Go-client 或 Python 库）示例。

---

## 审查 ReplicaSet (Inspecting a ReplicaSet)

* **状态概览**：使用 `kubectl describe rs <name>` 可查看标签选择器、镜像信息以及所有管理的 Pod 在生命周期中的细分状态（Running / Waiting / Succeeded / Failed）。
* **双向追溯排查技巧**：
  1. **通过 Pod 查找其 ReplicaSet (Finding a ReplicaSet from a Pod)**：
     * 通过命令 `kubectl get pods <pod-name> -o yaml`，寻找 `metadata.annotations` 中的 **`kubernetes.io/created-by`** 字段。此注解记录了创建它的 ReplicaSet 身份。（*注：此行为依赖于系统自动生成，且可被用户移除，属「尽力而为」的标识*）
  2. **查找 ReplicaSet 管理的所有 Pod (Finding a Set of Pods for a ReplicaSet)**：
     * 提取 ReplicaSet 描述信息中的 Label Selector。
     * 执行相同的过滤查询：`kubectl get pods -l <selector-string>`（如 `-l app=kuard,version=2`）。这也是控制器底层计算副本数时执行的确切查询动作。

```bash
kubectl describe rs kuard-rs
kubectl get pods -l app=kuard,version=2
```

> 💡 **后续拓展空间**：探讨在具有数万个 Pod 的大型集群中，API Server 如何通过内部索引优化 Label Selector 的查询性能。

---

## 扩缩容 ReplicaSets (Scaling ReplicaSets)

* **底层逻辑**：扩缩容的本质仅仅是修改 Kubernetes 系统中 ReplicaSet 对象上 `spec.replicas` 键对应的值，剩余工作全权交由协调循环（Reconciliation loop）处理。
* **三种扩缩容模式与防坑指南**：
  1. **使用 kubectl scale 进行命令式扩缩容 (Imperative Scaling)**：
     * 命令：`kubectl scale replicasets <name> --replicas=<num>`。
     * **高危易错细节（配置漂移灾难）**：在紧急应对突发流量（如缩扩容至 10 个副本）后，如果操作员**忘记将这一更改同步更新到版本控制库（Git）的 YAML 文件中**。几天后，另一位工程师利用源代码中旧的 YAML（此时 replicas 为 5）执行了新版本发布。这将导致系统在更新的同时瞬间损失 50% 的算力，引发极为严重的生产级雪崩故障。
  2. **使用 kubectl apply 进行声明式扩缩容 (Declarative Scaling)**：
     * **最佳实践**：直接修改源代码库中的 YAML 配置文件，经过代码审查（Code Review）后，再执行 `kubectl apply -f` 提交。这保证了**文件系统始终是集群状态的唯一事实来源（Source of Truth）**。
  3. **自动扩缩容 (Autoscaling a ReplicaSet)**：
     * Kubernetes 支持通过 **Horizontal Pod Autoscaling (HPA)** 基于指标（如 CPU、内存消耗或自定义应用指标）进行动态横向伸缩。
     * **前置依赖**：集群中必须运行 `metrics-server` 以采集并暴露监控指标。
     * **操作示例**（基于CPU）：`kubectl autoscale rs <name> --min=2 --max=5 --cpu-percent=80`。
     * **操作禁忌（Anti-pattern）**：**绝对不要将 HPA（自动扩缩）与手动修改副本数（命令式或声明式）混合使用！**。由于系统是解耦的，二者之间没有强制互斥锁定，同时使用会导致人机互相覆盖指令，产生极其不可预知的剧烈集群波动。

```bash
# 命令式（紧急用，记得同步 Git）
kubectl scale rs kuard-rs --replicas=10

# 声明式（推荐）
kubectl apply -f kuard-rs.yaml

# HPA
kubectl autoscale rs kuard-rs --min=2 --max=5 --cpu-percent=80
```

> 💡 **后续拓展空间**：引入 Kubernetes 演进中 Custom Metrics API 的应用，以及基于外部事件源（如 KEDA 组件，通过 Kafka 队列深度自动扩缩容）的高级 HPA 架构。

---

## 删除 ReplicaSets (Deleting ReplicaSets)

* **常规删除**：
  * 执行 `kubectl delete rs <name>`。默认行为是**级联删除（Cascading deletion）**，即不仅销毁 ReplicaSet 对象自身，还将同步强制终止其纳管的所有底层 Pod。
* **孤儿删除（Orphaning）**：
  * **实用要点**：如果因为某些架构重组需要销毁控制器，但绝不能影响当前正在处理线上流量的容器进程，可以追加 **`--cascade=false`** 参数。
  * 执行后，ReplicaSet 被删除，但所有相关的 Pod 将作为「孤儿（Orphans）」继续在集群中平稳运行。

```bash
kubectl delete rs kuard-rs
kubectl delete rs kuard-rs --cascade=orphan
```

> 💡 **后续拓展空间**：结合前文的「隔离容器」概念，探讨如何在不停止服务的情况下，将由 ReplicaSet 管理的孤儿 Pod 平滑地过度、移交给更高级的 Deployment 控制器纳管。

---

## 总结 (Summary)

* **核心结论**：
  * 将裸 Pod 升级组合为 ReplicaSet，是构建具备**自动故障转移（Automatic failover）**能力和健壮扩展性的现代化应用的基础。
  * **最佳实践原则**：生产环境中的任何容器应用，**即使明确只需要单例（1 个副本）运行，也应当毫不犹豫地使用 ReplicaSet 而非直接创建裸 Pod**，以保障由于底层物理节点失效时应用能被自动迁移重建。
* **向后延伸**：虽然 ReplicaSet 完美解决了横向扩缩容和自愈容灾问题，但它不具备优雅滚动更新不同镜像版本的能力。处理业务代码的版本迭代与平滑发布，必须引入建立在 ReplicaSet 之上的更高维抽象——**Deployment（部署对象）**。

> 💡 **后续拓展空间**：直接衔接下一章，从 ReplicaSet 平滑过渡到 Deployment，解析 Deployment 是如何通过操控多个底层的 ReplicaSet 来实现不停机的蓝绿发布与滚动更新。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| ReplicaSet | 保证正确类型、正确数量的 Pod 副本 |
| 协调循环 | 持续对比期望状态 vs 观察状态并纠偏 |
| 与 Pod 关系 | 松耦合，靠 label selector 纳管 |
| 隔离故障 Pod | 改标签脱离 selector，RS 补新 Pod |
| 适用场景 | 无状态、同质、可互换的 Pod |
| selector ⊆ template labels | 违反则无限创建 Pod |
| scale vs apply | 紧急 scale 后必须同步 Git，防配置漂移 |
| HPA | 勿与手动改 replicas 混用 |
| 孤儿删除 | `--cascade=orphan` 保留 Pod |
| 下一步 | 版本滚动更新 → Deployment |
