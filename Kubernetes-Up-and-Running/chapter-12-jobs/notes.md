# 第十二章：Jobs (Chapter 12: Jobs)

## The Job Object (Job 对象)

* **核心定义与主旨**：
  * **Job** 对象主要负责创建和管理执行短期、一次性任务（如数据库迁移或批处理作业）的 Pod。
  * 与普通的长期运行 Pod（无论退出代码如何都会不断重启）不同，Job 创建的 Pod 会一直运行，直到**成功终止（Successful termination，即退出状态码为 0）**为止。
* **核心机制与逻辑**：
  * Job 对象通过其规范（Spec）中的 Pod 模板来创建 Pod，并协调多个 Pod 的并行运行。
  * 如果 Pod 在成功终止前发生失败（例如应用程序错误、运行时异常或节点故障），**Job 控制器（Job Controller）**将基于模板创建一个新的 Pod 来替换它，直到任务最终成功完成。
* **易错细节**：
  * 由于分布式系统的特性及调度机制的资源限制，在某些特定的故障场景下，Job 偶尔可能会为同一个任务创建出**重复的 Pod（Duplicate Pods）**。

> 💡 **后续拓展空间**：可在此补充 Job 控制器的底层源码实现逻辑，以及它是如何通过追踪 Pod 的状态阶段（Phase）来判定任务是否彻底完成或失败的。

---

## Job Patterns (Job 模式)

* **核心主旨**：
  * Job 被设计用于管理批量型的工作负载，其中工作项（Work items）由一个或多个 Pod 处理。
* **关键参数与控制公式**：
  * Job 模式主要由两个核心属性定义和控制：
    1. **`completions`（完成次数）**：定义任务需要成功终止的 Pod 总数。
    2. **`parallelism`（并行度）**：定义允许同时并发运行的 Pod 数量。
* **三大主流执行模式矩阵**：
  1. **单次执行（One Shot）**：`completions=1`, `parallelism=1`。适用于数据库迁移等场景，单个 Pod 运行一次直到成功。
  2. **并行固定次数（Parallel fixed completions）**：`completions=1+`, `parallelism=1+`。适用于多个 Pod 并行处理一组已知工作量的数据，直到达到固定的成功次数。
  3. **工作队列（Work queue: parallel jobs）**：`completions=1`（或不设置）, `parallelism=2+`。多个 Pod 作为消费者从一个集中的工作队列中处理任务，直到队列清空。

| 模式 | completions | parallelism | 场景 |
|------|-------------|-------------|------|
| One Shot | 1 | 1 | 数据库迁移 |
| 并行固定 | N | M | 已知总量批处理 |
| 工作队列 | 不设/1 | 2+ | 消费者池直到队列空 |

> 💡 **后续拓展空间**：可以进一步介绍 Kubernetes 1.21+ 引入的 Indexed Job（索引作业）模式，探讨它如何为并行任务的每一个 Pod 分配静态的并发索引（Completion Index）。

---

## One Shot (单次执行任务)

* **核心机制与执行逻辑**：
  * 提供了一种运行单个 Pod 直至其成功终止的机制。
  * Job 的提交方式既可以通过 YAML 配置文件声明（`kind: Job`），也可以通过命令行指令 `kubectl run -i <job-name> --restart=OnFailure` 快速创建。
* **重启策略对比与防坑指南（RestartPolicy）**：
  * Job 规范中的 `restartPolicy` 绝不能设置为 `Always`。
  * **策略一：`OnFailure`（推荐）**：当 Pod 内部进程非正常退出时，kubelet 会在**原节点、原 Pod 内就地重启容器**（受本地 CrashLoopBackOff 退避机制控制），不会产生新的 Pod 对象。
  * **策略二：`Never`（易错陷阱）**：如果设置为 `Never`，当容器失败时，kubelet 不会重启它，而是直接将该 Pod 标记为错误（Error）。随后，Job 控制器会察觉到失败，并**创建一个全新的替换 Pod**。如果不加以小心限制，这将在集群中产生大量的失败 Pod 「垃圾（Junk）」占用资源。
* **状态洞察与排障**：
  * 历史版本中，使用 `kubectl get jobs` 时，默认会隐藏已完成的 Job，除非添加 `-a`（全量显示）标志（注：新版 K8s 行为可能有所变化，但需留意已完成 Job 的可视性）。
  * 如果任务陷入死锁且无法取得任何进展，可以结合**存活探针（Liveness Probes）**使用。当探针判定 Pod 死亡时，Job 会自动重启/替换该 Pod 以打破僵局。

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate
spec:
  backoffLimit: 4
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: migrate
          image: myapp/migrate:v1
```

```bash
kubectl apply -f db-migrate-job.yaml
kubectl get jobs
kubectl logs job/db-migrate
```

> 💡 **后续拓展空间**：补充 Job 资源规范中的 `backoffLimit`（最大重试次数阈值）和 `activeDeadlineSeconds`（任务整体超时时间）的高阶容错控制参数。

---

## Parallelism (并行处理)

* **引入背景**：
  * 对于耗时较长的任务（如生成大量密钥或批量图片转码），启动多个工作进程可以显著加快执行速度。
* **逻辑脉络与参数配置**：
  * 通过组合使用 `completions`（期望完成总数）和 `parallelism`（最大并发数）实现。
  * **案例推演**：如果目标是生成 100 个密钥，设定总任务需跑 10 次（`completions: 10`），但为防止瞬间耗尽集群资源，限制同时最多只能有 5 个 Pod 并行（`parallelism: 5`）。
  * Job 控制器最初会启动 5 个 Pod，随着部分 Pod 成功退出，控制器会不断启动新的 Pod 以填补并发空缺，直至累计成功退出次数达到 10 次。

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: keygen
spec:
  completions: 10
  parallelism: 5
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: worker
          image: myapp/keygen:v1
```

> 💡 **后续拓展空间**：结合集群自动扩缩容（Cluster Autoscaler），探讨大规模并行计算 Job 如何瞬间拉起大量底层计算节点并在任务结束后自动释放。

---

## Work Queues (工作队列)

* **核心场景与系统架构**：
  * 在工作队列场景中，通常存在一个中心化的队列服务（Work Queue Service）。生产者（Producer）将大量工作项放入队列，而 Worker Job 会启动多个消费者 Pod（Consumer）并行地从队列中拉取并处理任务，直到队列被彻底清空。
* **执行步骤与逻辑脉络**：
  1. **启动中心队列**：通常使用 ReplicaSet（确保高可用）及 Service 部署一个内存型队列服务（如 `kuard` 的 MemQ 模式）。
  2. **填充任务数据**：生产者通过 API 接口（如 HTTP POST）向队列注入工作项。
  3. **创建消费者 Job（核心要点）**：
     * 在 Job 配置中，设置 `parallelism: 5`（同时开启 5 个消费者并发处理）。
     * **关键配置技巧**：**不设置（Unset） `completions` 参数**。这将使 Job 进入**工作池模式（Worker Pool Mode）**。
* **终止判定的触发机制**：
  * 在工作池模式下，只要任何一个 Pod 以 0（成功）状态码退出，Job 控制器就会认为「任务已接近尾声」，从而开始收尾工作，**并且绝对不会再启动任何新的 Pod**。
  * 这意味着消费者程序的逻辑应当是：不断拉取并处理任务，一旦发现队列为空，则干净地退出。当所有工作完成，所有的 Pod 平滑退出，整个 Job 被标记为完成。

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: queue-worker
spec:
  parallelism: 5
  # 不设置 completions → 工作池模式
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: consumer
          image: myapp/consumer:v1
```

> 💡 **后续拓展空间**：探讨更成熟的外部队列架构（如 RabbitMQ、Kafka）以及如何结合 KEDA（Kubernetes Event-driven Autoscaling）实现基于队列深度的 Job 动态并发度伸缩。

---

## CronJobs (定时任务)

* **核心定义**：
  * 有时需要在特定的时间间隔或指定周期内执行任务，Kubernetes 提供了 **CronJob** 对象来实现此需求。
* **机制与格式规范**：
  * CronJob 的本质是一个调度器，它负责在特定的时间点触发并创建一个新的 Job 对象。
  * 时间规则通过 `spec.schedule` 字段定义，采用**标准的 Cron 格式字符串**（如 `"0 */5 * * *"` 表示每 5 个小时执行一次）。
  * 实际要执行的任务内容则嵌套封装在其内部的 `jobTemplate.spec.template` 层级下。

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: backup
spec:
  schedule: "0 2 * * *"   # 每天凌晨 2 点
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: backup
              image: myapp/backup:v1
```

```bash
kubectl apply -f backup-cronjob.yaml
kubectl get cronjobs
kubectl get jobs   # 查看 CronJob 触发的 Job
```

> 💡 **后续拓展空间**：详细拆解 CronJob 的并发控制策略（`concurrencyPolicy`：Allow, Forbid, Replace），以及在错失调度窗口（`startingDeadlineSeconds`）时的应对机制。

---

## Summary (总结)

* **核心论点归纳**：
  * 在同一个集群中，Kubernetes 不仅能够完美运行如 Web 应用这样的长驻型工作负载，也能高效处理如批处理任务这样的短生命周期工作负载。
  * Job 抽象提供了极大的灵活性，能够模拟从简单的一次性任务，到并行任务，再到基于工作队列直至任务耗尽的复杂批处理模式。
* **架构价值与演进**：
  * Job 是一个相对底层的原语（Low-level primitive），它可以被直接用于简单的工作负载。
  * 得益于 Kubernetes 自底向上的可扩展性设计，Job 完全可以被更高层级的编排系统（如 Workflow 或 DAG 引擎，如 Argo/Tekton）作为原子执行单元来进行调用，从而接管更复杂的业务任务。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| Job | 短生命周期任务，Pod 成功退出（code 0）即完成 |
| completions | 需要成功完成的 Pod 总数 |
| parallelism | 同时并发的 Pod 上限 |
| restartPolicy | Job 中只能用 `OnFailure` 或 `Never`，禁 `Always` |
| OnFailure vs Never | 前者容器内重启；后者失败则新建 Pod |
| 工作池模式 | 不设 completions；任一 Pod 成功退出即停止新建 |
| CronJob | 按 Cron 表达式定时创建 Job |
| backoffLimit | 最大重试次数 |
| 上层编排 | Argo/Tekton 等以 Job 为原子单元 |
