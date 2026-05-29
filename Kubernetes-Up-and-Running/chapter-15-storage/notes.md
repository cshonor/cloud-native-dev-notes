# 第十五章：集成存储解决方案与Kubernetes (Chapter 15: Integrating Storage Solutions and Kubernetes)

## 导入外部服务 (Importing External Services)

* **引入背景与痛点**：
  * 许多真实的分布式系统并非在真空中构建，往往需要与传统虚拟机上运行的现有数据库（具有**数据重力 Data Gravity**）进行集成，完全迁移至容器内可能并不现实。
* **核心逻辑与价值**：
  * 尽管外部服务不运行在Kubernetes内部，但在Kubernetes中**表示（Represent）**这些服务具有巨大的架构价值。
  * **高保真度一致性（High fidelity）**：通过内置的命名和发现机制，应用容器可以将外部数据库视为集群内的原生服务。这使得在测试环境（使用集群内瞬态数据库）和生产环境（使用外部遗留数据库）之间保持完全相同的配置成为可能，仅需在不同命名空间（Namespace）下指向不同的目标即可。

### 没有选择器的服务 (Services Without Selectors)

* **核心机制与操作规范**：
  * 常规服务通过标签选择器（Label Selector）寻找后端的Pod，而外部服务没有标签选择器。
  * **基于DNS名称的外部服务（ExternalName）**：
    * 如果外部数据库有完整的DNS域名（如云提供商的RDS服务 `database.company.com`），可以创建一个**无选择器（Without Selectors）**且 `type: ExternalName` 的Service对象。
    * **底层路由逻辑**：Kubernetes DNS服务将不会为其分配虚拟IP和A记录，而是生成一个**CNAME记录**。当集群内应用解析该服务名时，会被DNS协议无缝重定向（Alias）至外部的真实数据库域名。
  * **基于IP地址的外部服务**：
    * 如果外部服务仅有IP地址，则创建一个无选择器且**不指定** `ExternalName` 类型的常规Service对象。
    * 系统会为其分配虚拟IP，但因为没有选择器，不会自动生成对应的服务端点（Endpoints）。
    * **手动关联机制**：用户必须**手动创建一个同名的 `Endpoints` 对象**，并在其中硬编码外部服务的真实IP地址和端口。流量将由Kubernetes负载均衡器转发至该手动指定的外部IP。

```yaml
# ExternalName：DNS CNAME 指向外部域名
apiVersion: v1
kind: Service
metadata:
  name: legacy-db
spec:
  type: ExternalName
  externalName: database.company.com
```

```yaml
# 基于 IP：Service + 手动 Endpoints
apiVersion: v1
kind: Service
metadata:
  name: external-mysql
spec:
  ports:
    - port: 3306
---
apiVersion: v1
kind: Endpoints
metadata:
  name: external-mysql
subsets:
  - addresses:
      - ip: 10.0.1.50
    ports:
      - port: 3306
```

### 外部服务的局限性：健康检查 (Limitations of External Services: Health Checking)

* **易错细节与风险**：
  * 对于这种导入的外部服务，**Kubernetes不提供任何健康检查（Health Checking）机制**。
  * 用户（或外部自动化脚本）必须自行承担责任，确保手动配置在Endpoints中的IP地址是准确、高可用且处于健康状态的。

> 💡 **后续拓展空间**：可以进一步探讨如何结合外部的监控探针引擎（如Prometheus Blackbox Exporter）结合K8s Operator来动态更新外部服务的Endpoints健康状态。

---

## 运行可靠的单例 (Running Reliable Singletons)

* **核心主旨**：
  * 对于无法使用云提供商托管数据库，且不需要极高可用性（允许节点宕机时的短暂中断）的小型业务，在Kubernetes内运行一个单Pod的数据库（可靠单例）是一种极其合理的权衡。
  * 这摒弃了在K8s中实现数据库复杂多副本同步的麻烦，其可靠性等同于在单一物理机/虚拟机上运行传统数据库。

### 运行MySQL单例 (Running a MySQL Singleton)

* **架构三要素与因果逻辑**：
  * **1. 持久卷（PersistentVolume, PV）**：将数据生命周期与容器/Pod的生命周期强行剥离。即使容器崩溃或漂移至其他机器，只要底层云盘（如NFS、AWS EBS）挂载跟随转移，数据就绝对不会丢失。
  * **2. 持久卷声明（PersistentVolumeClaim, PVC）**：通过PVC来间接认领PV，保持Pod配置与底层云平台存储实现的解耦（Cloud-agnostic）。
  * **3. 副本集（ReplicaSet）**：这是**最关键的防错设计**。裸Pod一旦所在的物理节点宕机，将会随之永久消失且不会被重新调度。通过创建一个 `replicas: 1` 的 ReplicaSet（或 Deployment），能确保在该单点故障发生时，Kubernetes会自动在另一个健康节点上重建该MySQL实例，并重新挂载PVC。
  * 最后，创建一个Service将该单例暴露给集群内的其他应用。

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mysql-pvc
spec:
  accessModes: [ReadWriteOnce]
  resources:
    requests:
      storage: 10Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mysql
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mysql
  template:
    metadata:
      labels:
        app: mysql
    spec:
      containers:
        - name: mysql
          image: mysql:8
          volumeMounts:
            - name: data
              mountPath: /var/lib/mysql
      volumes:
        - name: data
          persistentVolumeClaim:
            claimName: mysql-pvc
```

### 动态卷配置 (Dynamic Volume Provisioning)

* **配置机制**：
  * 集群管理员可以创建 `StorageClass` 对象（如指定底层使用Azure Disk或AWS EBS）。
  * 在PVC中，通过指定 `storage-class` 注解或字段，告知Kubernetes动态配置器（Dynamic Provisioner）。系统会自动调用云API创建真实的物理磁盘，并与该PVC绑定，省去了手动预先创建PV的繁琐步骤。
* **高危易错细节（回收策略陷阱）**：
  * 动态配置的持久卷的生命周期由PVC的回收策略（Reclamation policy）决定。默认情况下，**卷的存活期与创建它的Pod/PVC绑定**。
  * **灾难场景**：如果在缩容（Scale-down）或清理操作时意外删除了该PVC，底层的云盘及其数据也可能会被同步自动销毁（取决于StorageClass的 `reclaimPolicy`）。操作状态有状态应用时必须极度谨慎。

```yaml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: fast-ssd
provisioner: kubernetes.io/aws-ebs
reclaimPolicy: Retain   # Retain 防误删；Delete 会随 PVC 销毁
```

> 💡 **后续拓展空间**：在此可以补充介绍Kubernetes中Volume Snapshot（卷快照）和Clone机制，以及在故障演练时如何安全地对动态卷进行备份。

---

## 使用StatefulSets进行Kubernetes原生存储 (Kubernetes-Native Storage with StatefulSets)

* **引入背景**：
  * Kubernetes早期（如ReplicaSet）极度强调副本的同质性（Homogeneity）与无状态性。对于像MongoDB这样需要明确主从身份、集群选主和精确网络身份的应用，这是巨大的阻碍。StatefulSet专门为此类有状态服务而生。

### StatefulSets的属性 (Properties of StatefulSets)

* **核心特性矩阵**：
  1. **持久化且唯一的网络标识**：每个副本不再分配随机后缀，而是获得基于严格索引的固定主机名（如 `database-0`, `database-1`）。
  2. **有序创建（Ordered Creation）**：按照索引从低到高（0 → N）依次创建。**阻塞逻辑**：只有前一个索引的Pod变为健康可用（Healthy and available）后，才会启动下一个Pod的创建。
  3. **有序销毁/缩容**：按从高到低的严格相反顺序（N → 0）逐个终止。这有效防止了分布式数据库在缩容时发生数据脑裂或同步异常。
* **设计价值**：固定的索引和可预测的启动顺序，使得后面的副本可以稳定地将 `database-0` 作为发现节点和初始集群主节点（Quorum）进行连接引用。

### 使用StatefulSets手动复制MongoDB (Manually Replicated MongoDB with StatefulSets)

* **核心机制与Headless Service**：
  * 要让StatefulSet中的固定主机名在网络上可解析，必须配合**无头服务（Headless Service）**使用。配置时需将 `clusterIP` 明确设置为 `None`。
  * **DNS机制解析**：创建无头服务后，K8s内部DNS会直接为每个Pod副本生成专门的A记录（如 `mongo-0.mongo.default.svc.cluster.local`）。这打破了传统服务必须经过统一虚拟IP负载均衡的限制，允许点对点直接通信。

```yaml
apiVersion: v1
kind: Service
metadata:
  name: mongo
spec:
  clusterIP: None          # Headless Service
  selector:
    app: mongo
  ports:
    - port: 27017
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: mongo
spec:
  serviceName: mongo
  replicas: 3
  selector:
    matchLabels:
      app: mongo
  template:
    metadata:
      labels:
        app: mongo
    spec:
      containers:
        - name: mongo
          image: mongo:6
```

```
mongo-0.mongo.default.svc.cluster.local  →  Pod mongo-0 的 IP
mongo-1.mongo.default.svc.cluster.local  →  Pod mongo-1 的 IP
```

### 自动化MongoDB集群创建 (Automating MongoDB Cluster Creation)

* **自动化初始化逻辑**：
  * 利用ConfigMap注入一个初始化脚本（`init.sh`）到包含Mongo的主容器旁边的额外容器中。
  * 脚本内含角色探测逻辑：如果是 `mongo-0` 节点，则执行 `rs.initiate` 启动主节点；如果是其他节点，则等待 `mongo-0` 启动后执行 `rs.add` 将自己加入集群。
* **易错细节（Pod级别的重启策略约束）**：
  * Pod规范中的 `RestartPolicy` 作用于该Pod内的**所有**容器。
  * 为了防止主要数据库进程退出，通常被设置为 `Always`。这也意味着**初始化容器在完成集群构建后，不能直接退出（Exit 0）**。如果它退出了，kubelet会认为该容器宕机并不断重启它，导致整个Pod被判定为不健康。必须在初始化脚本末尾加入 `while true; do sleep 3600; done` 使其永远挂起休眠。

### 持久卷和StatefulSets (Persistent Volumes and StatefulSets)

* **动态存储挂载痛点与解法**：
  * 由于StatefulSet会生成多个独立的副本，不能像单例那样在Pod模板里硬编码挂载单一的 `PersistentVolumeClaim`（否则所有数据库节点会写入同一块云盘导致损坏）。
  * **卷声明模板（volumeClaimTemplates）**：必须在StatefulSet配置的末尾使用该数组结构。它的工作原理类似Pod模板：每当StatefulSet控制器创建一个新Pod（如 `mongo-0`），它也会根据此模板同步动态生成一个独立对应的PVC（及对应的持久卷）并将其独占绑定。
  * **前提要求**：这要求集群必须已开启且配置好了可靠的**动态卷配置（Dynamic Provisioning）**机制，或者管理员提前手工创建了足够数量的PV池供绑定，否则Pod将因无法获得独立存储而一直处于 `Pending` 状态。

```yaml
spec:
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: [ReadWriteOnce]
        resources:
          requests:
            storage: 10Gi
```

### 最后一件事：就绪探针 (One Final Thing: Readiness Probes)

* **保障健康更新的关键**：
  * 必须为数据库容器配置真实的Liveness和Readiness Probes（例如执行 `mongo --eval db.serverStatus()`）。
  * 缺乏探针将导致StatefulSet在滚动更新或有序扩展时发生「盲飞（Running blind）」，无法准确判定上一个节点是否已真正在应用层面上准备好同步。

> 💡 **后续拓展空间**：在生产环境中，纯基于StatefulSet的部署仍需要大量运维脚本。这里可以自然过渡到下一章关于CustomResourceDefinition (CRD) 和 Operator 模式，解释为何目前业界倾向于使用专门的 DB-Operator 来替代复杂的启动/维护脚本。

---

## 总结 (Summary)

* **核心结论提炼**：
  * 通过将**StatefulSets**（处理稳定网络拓扑和启停顺序）、**持久卷声明（PVC/PV）**（保障数据状态留存）以及**存活/就绪探针**（掌控可用性边界）相结合，开发者能够直接在Kubernetes之上运行出具备高度扩展性、生产级强度的云原生有状态应用集群。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| ExternalName | Service DNS → CNAME 指向外部域名 |
| 外部 IP | 无 selector 的 Service + 手动 Endpoints |
| 外部服务局限 | K8s 不做健康检查，需自行保障 |
| 可靠单例 | PV + PVC + replicas:1 Deployment |
| StorageClass | 动态创建云盘；注意 reclaimPolicy |
| StatefulSet | 固定主机名、有序创建/销毁 |
| Headless Service | `clusterIP: None`，每 Pod 独立 DNS A 记录 |
| volumeClaimTemplates | 每副本独立 PVC，不可共享单 PVC |
| 初始化容器陷阱 | RestartPolicy=Always 时 init 不能 exit |
| 生产建议 | 复杂 DB 优先 Operator，非手写脚本 |
