# 第六章：标签与注解 (Chapter 6: Labels and Annotations)

## 标签 (Labels)

* **核心定义与主旨**：
  * **标签（Labels）**是附加在Kubernetes对象（如Pods和ReplicaSets）上的键值对（Key/Value pairs）。
  * 标签提供对象的身份元数据，是进行分组、查看和操作的基础。
* **设计逻辑与脉络**：
  * **反单例模式**：生产环境中应避免单例（Singleton），应用程序成熟后通常由多实例集合构成，标签的设计正是为了处理**对象集合（Sets of objects）**而非单一实例。
  * **打破僵化层级**：系统强制的层级结构往往无法适应复杂场景，且分组方式会随时间变化（例如某服务从专用于一应用变为多应用共享）。标签的灵活性使其能够适应各种组织方式。
* **语法规范与格式限制**：
  * **键（Key）**：分为可选的前缀（Prefix）和名称（Name），以斜杠（`/`）分隔。
    * 前缀必须是有效的DNS子域，最长253个字符。
    * 名称是必填项，最长63个字符，必须以字母或数字开头和结尾，内部允许使用破折号（`-`）、下划线（`_`）和点（`.`）。
  * **值（Value）**：最大长度为63个字符的字符串，字符规则与名称相同。
  * **规范应用**：当使用域名作为前缀时，通常表示与该特定实体对齐（如云提供商专有特性）。

> 💡 **后续拓展空间**：可在此补充Kubernetes官方推荐的标准标签（Recommended Labels，如 `app.kubernetes.io/name` 等）及其在Helm等包管理工具中的标准化应用。

---

## 应用标签 (Applying Labels)

* **操作与逻辑脉络**：
  * 在创建资源时，可通过命令直接注入多维度的标签属性。
  * **案例数据**：创建一个名为 `alpaca-prod` 的Deployment，通过 `--labels="ver=1,app=alpaca,env=prod"` 赋予其版本、应用名和环境三个维度的标签。
* **多维拓扑结构**：
  * 不同应用（如 `alpaca`, `bandicoot`）和不同环境（如 `prod`, `test`, `staging`）通过标签交叉，可以在逻辑上形成类似韦恩图（Venn diagram）的集合交集结构。

```bash
kubectl create deployment alpaca-prod --image=nginx --labels="ver=1,app=alpaca,env=prod"
```

```yaml
metadata:
  labels:
    app: alpaca
    env: prod
    ver: "1"
```

> 💡 **后续拓展空间**：可在此补充如何在YAML清单（Manifest）的 `metadata.labels` 字段中声明式地应用这些标签。

---

## 修改标签 (Modifying Labels)

* **核心操作命令**：
  * 使用 `kubectl label` 命令可为已存在的对象添加或更新标签（如 `kubectl label deployments alpaca-test "canary=true"`）。
  * **查看标签列**：在 `kubectl get` 命令中附加 `-L <label-name>` 参数，可将特定标签作为独立的数据列展示。
  * **删除标签**：在标签键名后加上减号（`-`）即可移除该标签（如 `kubectl label deployments alpaca-test "canary-"`）。
* **易错细节（防坑指南）**：
  * **标签生效范围陷阱**：使用 `kubectl label` 修改Deployment的标签时，**仅会改变Deployment自身的标签**，并不会影响该Deployment已生成的ReplicaSets和Pods。若要改变底层Pod的标签，必须修改Deployment内嵌的Pod模板（Template）。

```bash
kubectl label deployments alpaca-test canary=true
kubectl get deployments -L app,env,canary
kubectl label deployments alpaca-test canary-
```

> 💡 **后续拓展空间**：可在此引入 `kubectl label` 的 `--overwrite` 参数行为，解释如何强制覆盖已有同名标签。

---

## 标签选择器 (Label Selectors)

* **核心定义**：
  * **标签选择器（Label Selectors）**是一种简单的布尔查询语言，用于基于标签集合过滤Kubernetes对象。
  * 它不仅被终端用户（通过 `kubectl`）使用，也是Kubernetes内部组件（如ReplicaSet关联Pod）的核心机制。
* **关键机制与内置标签**：
  * **`pod-template-hash`**：Deployment会自动为其生成的Pod应用该标签，以便精确追踪哪些Pod是由哪个特定版本的模板生成的，这是实现滚动更新（Rolling Updates）的核心基础。
* **查询语法与逻辑运算符矩阵**：
  1. **精确匹配**：`--selector="ver=2"`。
  2. **逻辑与（AND）**：使用逗号分隔，如 `--selector="app=bandicoot,ver=2"`，需同时满足两个条件。
  3. **集合匹配（IN）**：如 `--selector="app in (alpaca,bandicoot)"`。
  4. **存在性匹配**：仅提供键名，如 `--selector="canary"` 表示匹配所有带有 `canary` 键（无论值是什么）的对象。
  5. **反向选择**：`!=`（不等于），`notin`（不在集合内），或 `!<key>`（键不存在）。
  6. **复合逻辑**：支持正向和反向条件混合，如 `-l 'ver=2,!canary'`。

```bash
kubectl get pods -l app=bandicoot,ver=2
kubectl get pods -l 'app in (alpaca,bandicoot)'
kubectl get pods -l 'ver=2,!canary'
```

> 💡 **后续拓展空间**：可以进一步分析标签选择器在大规模集群中查询时的性能影响，以及API Server底层的etcd索引机制。

---

## API对象中的标签选择器 (Label Selectors in API Objects)

* **核心逻辑与演进脉络**：
  * 在YAML等配置文件中，K8s对象引用其他对象时必须使用结构化的标签选择器。出于历史兼容性原因，K8s支持两种选择器格式。
* **两种格式拆解**：
  1. **新型（Set-based / 集合型）**：
     * 更强大的表达式格式，包含 `matchLabels`（简单的键值匹配）和 `matchExpressions`。
     * `matchExpressions` 包含键（key）、操作符（operator，如 `In`, `NotIn`, `Exists`, `DoesNotExist`）和值列表（values）。
     * **逻辑脉络**：不同条件间默认隐式执行逻辑与（AND）。若要表达不等式（`!=`），只能通过 `NotIn` 操作符配合单值列表来实现。
  2. **旧型（Equality-based / 等值型）**：
     * 主要被ReplicationControllers和Services等早期资源使用。
     * 仅支持简单的键值对精确匹配（`=` 操作符）。

```yaml
selector:
  matchLabels:
    app: bandicoot
  matchExpressions:
    - key: env
      operator: In
      values: [prod, staging]
    - key: canary
      operator: DoesNotExist
```

> 💡 **后续拓展空间**：深入探讨这两种选择器在跨不同API版本（如 `apps/v1` vs 旧版）时的字段约束要求。

---

## Kubernetes架构中的标签 (Labels in the Kubernetes Architecture)

* **核心主旨**：
  * Kubernetes是一个**刻意解耦（Purposefully decoupled）**的系统，不存在硬编码的层级结构。标签和选择器正是将这些独立组件粘合在一起的「胶水」。
* **架构关联案例**：
  * **ReplicaSets** 通过选择器查找并纳管对应的Pods。
  * **Service** 负载均衡器通过选择器识别后端应该将流量路由给哪些Pods。
  * **Node Selector** 通过标签决定Pod应该调度到哪些物理节点上。
  * **NetworkPolicy** 结合标签来界定Pod间的网络通信白名单/黑名单。

> 💡 **后续拓展空间**：结合Service Mesh（如Istio）场景，阐述标签在流量治理和遥测（Telemetry）中扮演的路由标识角色。

---

## 注解 (Annotations)

* **核心定义与区别**：
  * **注解（Annotations）**与标签存储机制类似（同为键值对），但**专门用于存放非标识性（Nonidentifying）数据**，主要供外部工具和库读取使用。
  * **使用准则**：如果不确定应该用标签还是注解，请先使用注解。当发现需要用它来进行选择器过滤时，再将其提升（Promote）为标签。
* **核心使用场景**：
  * 记录对象最近更新的「原因（reason）」。
  * 向定制化调度器传递特殊的调度策略。
  * 附加构建、发布版本或镜像哈希等不适合作为标签的元数据。
  * 协助Deployment对象追踪并控制ReplicaSets的滚动更新（Rollouts）状态与回滚信息。
  * 为UI界面提供增强数据（如编码后的图标信息）。
  * 对K8s的Alpha级新功能进行原型设计（不创建核心API字段，而是将参数编入注解中）。
* **操作禁忌**：
  * **切勿将Kubernetes API服务器当作通用数据库**。注解仅适合存储与特定资源强相关的极少量数据。

> 💡 **后续拓展空间**：补充Kubernetes版本迭代中，如何通过Annotation作为新特性（如Ingress Controllers的高级配置）的载体。

---

## 定义注解 (Defining Annotations)

* **键值规范与局限性**：
  * **键（Key）**：格式与标签键一致。但因其常用于跨工具通信，**命名空间前缀（Namespace prefix）极其重要**（例如 `deployment.kubernetes.io/revision` 或 `kubernetes.io/change-cause`）。
  * **值（Value）**：完全自由格式的字符串。
* **易错细节**：
  * 由于Value是无格式约束的自由文本（甚至经常存入JSON字符串），**Kubernetes服务器不对注解内容进行任何数据校验（No validation）**。如果数据格式错误，这会导致排障变得极其困难。
* **声明式位置**：在YAML清单中，统一配置在所有K8s对象通用的 `metadata.annotations` 层级下。

```yaml
metadata:
  annotations:
    kubernetes.io/change-cause: "Deploy v2.1.0 from CI pipeline #4821"
    deployment.kubernetes.io/revision: "3"
```

> 💡 **后续拓展空间**：扩展讲解K8s 1.13+ 中增加的注解最大体积限制（通常为256KB），避免将大段文本塞入元数据。

---

## 清理工作 (Cleanup)

* **实用命令**：
  * 执行 `kubectl delete deployments --all` 可一键清理当前命名空间下的所有Deployments。
  * 也可以结合 `--selector` 参数（如 `--selector="app=alpaca"`）进行精准的安全清理。

```bash
kubectl delete deployments --all
kubectl delete deployments -l app=alpaca
```

> 💡 **后续拓展空间**：补充Kubernetes中对象垃圾回收（Garbage Collection）的 Owner References 底层级联删除（Cascading deletion）机制。

---

## 总结 (Summary)

* **核心主旨提炼**：
  * **标签（Labels）**解决了「你是谁」和「你属于哪个组」的问题，为Pods等对象提供了运行时的动态逻辑分组及API选择器基石。
  * **注解（Annotations）**解决了「附加信息存储」的问题，为自动化工具、客户端库和第三方调度器提供了对象级别的键值存储空间。
* **架构价值**：这两者共同构成了理解和利用Kubernetes解耦机制的核心，是构建任何自动化部署流水线和高阶调度策略的起点。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| Label | 标识性键值对，用于分组与选择器过滤 |
| Annotation | 非标识性元数据，供工具读取，不参与选择 |
| 改 Deployment 标签 | 只改 Deployment 自身，不改已有 Pod |
| pod-template-hash | Deployment 追踪模板版本，支撑滚动更新 |
| 选择器语法 | `=`, `in`, `!=`, `notin`, `!key`；逗号 = AND |
| matchExpressions | 集合型选择器：`In` / `NotIn` / `Exists` / `DoesNotExist` |
| 架构胶水 | ReplicaSet、Service、NodeSelector、NetworkPolicy 都靠标签 |
| 不确定用哪个 | 先用 Annotation，需要过滤再提升为 Label |
