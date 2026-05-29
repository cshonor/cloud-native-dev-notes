# 第十章：Deployments (Chapter 10: Deployments)

## 引入与核心场景 (Introduction)

* **核心痛点与引入背景**：
  * Pods、ReplicaSets 和 Services 只能用于构建和管理应用程序的**单一版本（Single instance/version）**。
  * 它们缺乏管理软件新版本发布（Rollout）的能力，一旦镜像固定，便难以实现平滑的版本更迭。
* **Deployment 的核心定义**：
  * **Deployment（部署对象）** 是为了管理软件新版本发布而存在的，它代表了一个超越单一特定版本的部署应用。
  * 它提供了一种规范且谨慎的**发布（Rollout）**机制：能够在升级各个 Pod 之间等待用户配置的时间，利用健康检查确保新版本运行正常，并在错误过多时自动停止发布。
* **架构优势**：
  * Deployment 控制器运行在 Kubernetes 集群内部，这意味着发布过程可以**无人值守（Unattended）**地安全进行，甚至在网络连接不佳的情况下也能可靠执行。

```
Deployment → ReplicaSet → Pod
     ↑           ↑
  管理发布    管理副本数
```

> 💡 **后续拓展空间**：可在此补充 Deployment 之前 Kubernetes 早期版本中 `kubectl rolling-update` 命令式更新的局限性，从而凸显声明式 Deployment 控制器的架构演进价值。

---

## 你的第一个 Deployment (Your First Deployment)

* **声明式清单结构**：
  * Deployment 同样使用 YAML 进行声明，关键字段包括定义期望副本数的 `replicas`，以及包含 Pod 标签和镜像的 `template`。
  * 创建命令：`kubectl create -f kuard-deployment.yaml`。

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kuard
spec:
  replicas: 3
  selector:
    matchLabels:
      app: kuard
  template:
    metadata:
      labels:
        app: kuard
    spec:
      containers:
        - name: kuard
          image: gcr.io/kuar-demo/kuard-amd64:1
          ports:
            - containerPort: 8080
```

> 💡 **后续拓展空间**：可在此处扩展说明在 CI/CD 流水线中如何通过自动化模板渲染（如 Helm 或 Kustomize）来动态生成初始的 Deployment YAML 清单。

---

## Deployment 内部机制 (Deployment Internals)

* **核心层级与控制逻辑**：
  * 正如 ReplicaSets 管理 Pods 一样，**Deployments 管理 ReplicaSets**。
  * 这种管理关系同样是通过**标签选择器（Label selector）**来确立的。
* **级联扩缩容现象**：
  * 当使用 `kubectl scale` 改变 Deployment 的副本数时，其底层控制的 ReplicaSet 的副本数也会被同步缩放。
* **易错细节（控制循环冲突）**：
  * **高危操作**：如果绕过 Deployment，直接去修改底层 ReplicaSet 的副本数（例如从 2 缩减为 1），Kubernetes 的自愈协调循环会立刻介入。由于 Deployment 的期望状态仍为 2，控制器会立刻将 ReplicaSet 的副本数改回 2，从而覆盖人工修改。
  * **结论**：绝不能直接干预由 Deployment 管理的 ReplicaSet。如需直接管理，必须先删除上层的 Deployment（并使用 `--cascade=false` 保留底层资源）。

> 💡 **后续拓展空间**：深入探讨 Deployment Controller 的底层源码实现，特别是它是如何通过 OwnerReferences 机制追踪并接管底层 ReplicaSet 的。

---

## 创建 Deployments (Creating Deployments)

* **操作规范与命令要点**：
  * 强烈建议使用声明式（Declarative）方法管理配置文件。
  * **防坑细节**：如果首次使用 `create` 命令，建议配合 `--save-config` 参数（如 `kubectl replace -f ... --save-config`），这会在对象的 Annotation 中记录最后一次应用的配置，以便后续 `kubectl apply` 能进行更智能的 3-way 合并。
* **清单核心代码段（`strategy` 对象）**：
  * 除了 Pod 模板，Deployment 规范中还包含一个 `strategy`（策略）对象。
  * 该对象决定了软件新版本发布的具体方式，支持两种核心策略：**`Recreate`（重新创建）** 和 **`RollingUpdate`（滚动更新）**。

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
```

> 💡 **后续拓展空间**：可在此补充 Server-Side Apply（服务端应用）对 `--save-config` 客户端机制的替代方案及其在冲突解决上的优势。

---

## 管理 Deployments (Managing Deployments)

* **状态洞察工具**：
  * `kubectl describe deployments <name>` 提供了极为丰富的运维信息。
  * **关键字段**：`OldReplicaSets` 和 `NewReplicaSet`。如果正在进行发布，这两个字段都会有值；如果发布完成，旧的 ReplicaSet 会显示为 `<none>`。
* **Rollout 专属命令集**：
  * `kubectl rollout history`：查看 Deployment 的历史发布记录。
  * `kubectl rollout status`：查看当前正在进行的发布的实时进度与状态。

```bash
kubectl describe deployment kuard
kubectl rollout history deployment/kuard
kubectl rollout status deployment/kuard
```

> 💡 **后续拓展空间**：引入 Kubernetes 仪表板（Dashboard）或终端 UI（如 k9s）中对 Deployment 及其关联 ReplicaSet 拓扑结构的可视化监控方法。

---

## 更新 Deployments (Updating Deployments)

* **扩缩容（Scaling）**：
  * **最佳实践**：直接修改 YAML 文件中的 `spec.replicas`，然后执行 `kubectl apply -f` 进行声明式更新。
* **更新容器镜像（Updating a Container Image）**：
  * 通过修改 YAML 中的 `image` 字段来触发新版本发布。
  * **易错细节**：建议在 Pod 模板的 `metadata.annotations` 中添加 `kubernetes.io/change-cause` 以记录变更原因（如 "Update to green kuard"）。必须注意：此注解应加在 **Template** 级别而非 Deployment 级别；且在单纯的扩缩容操作时**不要修改此注解**，否则会被系统视为模板变更从而意外触发一次全新的 Rollout。
* **中断与恢复（Pause and Resume）**：
  * 如果在发布中途发现系统行为异常需要调查，可使用 `kubectl rollout pause` **暂停**发布。
  * 确认安全后，使用 `kubectl rollout resume` **恢复**发布进度。
* **发布历史与回滚（Rollout History & Undo）**：
  * 每次修改 Pod 模板都会生成一个新的单调递增的 **修订号（Revision）**。
  * `kubectl rollout undo` 命令用于**回滚**到上一个版本。其本质上只是执行一次**反向的发布（Rollout in reverse）**，所有的发布策略（如滚动更新）在回滚时同样适用。
  * **底层逻辑**：回滚时，Deployment 直接复用历史的 ReplicaSet 模板，并为其分配最新的修订号（例如从 v3 回滚到 v1，实际上是将 v1 的模板重新应用并标记为 v4）。
  * **清理机制**：通过 `revisionHistoryLimit` 参数限制保留的历史修订版本数量（如 14），防止长期运行的 Deployment 对象体积无限膨胀。

```yaml
template:
  metadata:
    annotations:
      kubernetes.io/change-cause: "Update to green kuard"
```

```bash
kubectl apply -f kuard-deployment.yaml
kubectl rollout pause deployment/kuard
kubectl rollout resume deployment/kuard
kubectl rollout undo deployment/kuard
kubectl rollout undo deployment/kuard --to-revision=2
```

> 💡 **后续拓展空间**：结合 GitOps 理念（如 ArgoCD/Flux），探讨如何在不依赖人工执行 `kubectl rollout undo` 的情况下，仅通过代码仓库的 Revert 提交来实现生产环境的自动化安全回滚。

---

## Deployment 部署策略 (Deployment Strategies)

### 1. Recreate 策略 (Recreate Strategy)

* **机制**：将由其管理的 ReplicaSet 更新为新镜像，并**立刻终止（terminates）**所有旧 Pod。当旧 Pod 归零后，再全量创建新 Pod。
* **优缺点**：极其简单快速，但**必定会导致服务停机（Downtime）**。仅适用于不面向用户且允许短暂不可用的测试环境。

```yaml
spec:
  strategy:
    type: Recreate
```

### 2. RollingUpdate 策略 (RollingUpdate Strategy)

* **机制**：对于用户面服务，通常首选滚动更新策略。它每次只更新一小部分 Pod，逐步推进，实现**零停机时间（without any downtime）**。
* **强制解耦约束（前后向兼容性）**：
  * 由于新老版本会在更新期间**同时处理流量**，这意味着客户端可能在极短时间内交替访问到 v1 和 v2 版本的服务端 API。
  * **核心架构要求**：必须保证 API 的前后向兼容性。这一策略从根本上倒逼开发者采用**解耦（Decoupled）**架构，剥离强绑定的胖客户端。
* **核心配置参数公式**：
  * **`maxUnavailable`（最大不可用数）**：设定发布期间允许处于不可用状态的 Pod 的最大数量（可为绝对值或百分比）。该值直接决定了可用容量的底线，值越大，更新速度越快，但容量风险越高。
  * **`maxSurge`（最大激增数）**：设定在期望副本数之上，允许额外创建的 Pod 的最大数量。它允许通过消耗额外的集群资源来保障 100% 的基线容量。
  * **蓝绿部署等效公式**：将 `maxUnavailable` 设为 `0` 且 `maxSurge` 设为 `100%`，即可在 Kubernetes 中实现等效的**蓝绿部署（Blue/Green deployment）**。

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 100%    # 蓝绿等效
```

### 3. 放缓发布以确保服务健康 (Slowing Rollouts to Ensure Service Health)

* **核心痛点**：仅依靠就绪探针（Readiness Probe）变为 Ready 状态并不足以证明新版本完全健康。例如，某些内存泄漏或仅影响 1% 流量的隐蔽 Bug 需要运行几分钟后才会暴露。
* **关键参数与机制**：
  * **强制前提**：必须为容器配置**就绪探针（Readiness health checks）**，否则 Deployment 控制器相当于「盲飞（running blind）」。
  * **`minReadySeconds`（最短就绪时间）**：设定一个等待期（如 60 秒），控制器在看到新 Pod 变为健康后，必须**强制等待该时长**，若在此期间未崩溃，才继续更新下一个 Pod。
  * **`progressDeadlineSeconds`（进度截止时间）**：设定防死锁超时时间（默认通常为 10 分钟）。如果某个阶段（例如新版本一启动就发生死锁导致永远无法 Ready）卡住的时间超过此阈值，发布将被标记为**失败（Failed）**并彻底停止推进。

```yaml
spec:
  minReadySeconds: 60
  progressDeadlineSeconds: 600
```

> 💡 **后续拓展空间**：深入探讨如何结合 Service Mesh（如 Istio）将 Deployment 的 RollingUpdate 细化为更高级的流量灰度发布（Canary Release）机制。

---

## 删除与监控 Deployment (Deleting and Monitoring a Deployment)

* **级联删除逻辑**：
  * 执行 `kubectl delete deployments kuard` 时，默认行为是**级联删除**——不仅删除 Deployment，还会连根拔起其管理的所有 ReplicaSets 及其底层的全部 Pods。保留底层资源的参数为 `--cascade=false`。
* **监控失败状态**：
  * 当发布因超时（达到 `progressDeadlineSeconds`）而停滞时，Deployment 的 `status.conditions` 数组中会出现一个 `Type` 为 **`Progressing`** 且 `Status` 为 **`False`** 的 Condition。
  * **实用要点**：生产环境中应通过监控系统（如 Prometheus）捕获此类状态，以便触发告警、工单介入或自动化回滚流。

```bash
kubectl delete deployment kuard
kubectl delete deployment kuard --cascade=orphan
```

> 💡 **后续拓展空间**：扩展介绍 Kubernetes 自定义指标体系和 Operator 如何自动化处理 `Progressing=False` 状态的修复逻辑。

---

## 总结 (Summary)

* **核心主旨提炼**：
  * Kubernetes 的最终目标不仅是让应用运行一次，而是管理该软件**长期、有节奏的版本更新（Regularly scheduled rollout）**。
  * Deployment 对象通过抽象化的 ReplicaSet 操控、完备的策略配置（RollingUpdate / Recreate）、内置的健康熔断机制，成为了云原生时代保障服务平滑升级与高可用发布的最核心、最基础的构建块。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| Deployment | 管理版本发布；控制 ReplicaSet |
| 层级 | Deployment → ReplicaSet → Pod |
| 勿改底层 RS | Deployment 协调循环会覆盖人工修改 |
| RollingUpdate | 逐步替换，零停机；需 API 前后兼容 |
| Recreate | 先杀后建，有停机，仅测试用 |
| maxUnavailable | 发布期允许不可用的 Pod 上限 |
| maxSurge | 期望副本之上的额外 Pod 上限 |
| minReadySeconds | Ready 后等待 N 秒再更新下一个 |
| progressDeadlineSeconds | 发布卡住超时 → Failed |
| change-cause | 加在 template 注解；扩缩容勿改 |
| rollout undo | 反向发布，复用历史 RS 模板 |
| 蓝绿等效 | maxUnavailable=0, maxSurge=100% |
