# 第十六章：扩展 Kubernetes (Chapter 16: Extending Kubernetes)

## 扩展 Kubernetes 的含义 (What It Means to Extend Kubernetes)

* **核心定义**：
  * 扩展 Kubernetes 意味着向集群添加新功能，或者限制及调整用户与集群交互的方式。
* **逻辑脉络与权限边界**：
  * **高权限警示**：扩展集群是一项**极高权限（Very high-privilege）**的操作，通常需要**集群管理员（Cluster Administrator）**级别的权限。
  * **安全风险**：扩展组件（如准入控制器）可以拦截和查看集群中创建的所有对象，如果将此权限赋予任意用户或随意运行第三方代码，极易成为窃取集群机密（Secrets）或运行恶意代码的攻击向量。
* **易错细节**：
  * 扩展会使集群偏离原生的 Kubernetes 标准状态。在管理多个集群时，必须构建自动化工具来保证各集群间扩展组件的安装和体验的一致性。

> 💡 **后续拓展空间**：可在此补充 Kubernetes 架构演进中脱离树内（Out-of-tree）开发的趋势，以及 Cloud Controller Manager（CCM）如何帮助云厂商独立扩展核心功能。

---

## 扩展点 (Points of Extensibility)

* **核心主旨**：
  * Kubernetes 提供了多种扩展接口（如 CNI/CSI/CRI），但对于集群终端用户而言，最核心的 API 服务器扩展主要通过添加**自定义资源定义（CustomResourceDefinitions, CRD）**和**准入控制器（Admission Controllers）**来实现。
* **API 请求处理脉络**：
  * **请求流转层级**：身份认证与授权 (Authentication/Authorization) → **准入控制 (Admission Control, 包含验证与变更)** → API 服务器 (API Server) → 持久化存储 (Storage / etcd)。

```
请求 → AuthN/AuthZ → Mutating Webhook → Validating Webhook → API Server → etcd
```

* **自定义资源定义 (CustomResourceDefinition, CRD)**：
  * **机制**：CRD 本质上是一种「元资源（Meta-resource）」，用于向 API 服务器注册全新的 API 对象（例如定义一个代表负载测试的 `LoadTest` 资源）。注册后的新资源享有与原生资源相同的能力：支持命名空间隔离、受 RBAC 控制、可被 `kubectl` 工具直接访问。
  * **命名硬性规则**：CRD 的名称必须遵循 `<resource-plural>.<api-group>` 的严格格式。这是为了保证集群内资源定义的**全局唯一性**，防止两个不同的 CRD 产生命名冲突。
* **自定义控制器 (Custom Resource Controller) 与监听机制**：
  * **逻辑因果**：仅仅定义并提交 CRD 只会产生一个基础的 CRUD（增删改查）API 存取层，并不能产生实际的业务动作。要让资源真正生效，必须配备在后台持续运行的代码——**控制器（Controller）**，以实现状态协调。
  * **性能优化要点（轮询 vs 监听）**：简单的控制器使用死循环进行**轮询（Polling）**，这会带来严重的延迟和无效的 API 服务器负载。**高效/最佳实践**是使用 API 的 **`watch` 机制**获取实时更新流，强烈推荐直接使用 client-go 库中的 **Informer 模式**来安全地处理事件流。
* **准入控制器 (Admission Controllers) 的验证与默认值填充**：
  * **痛点**：简单的 OpenAPI 规范无法验证复杂的业务逻辑（如校验 URL 协议头是否合法、保证参数为正数等），且 CRD 原生缺乏自动填充默认值的能力。
  * **执行逻辑**：通过向集群注册**动态准入控制器（Dynamic admission controller）**来拦截请求。API 服务器会通过 HTTP 回调外部的 Webhook（甚至可以是云平台上的 Serverless 函数如 AWS Lambda）。
  * **两大分支**：
    1. **验证型（ValidatingWebhookConfiguration）**：仅用于校验并选择放行或拒绝请求（如拒绝负数的负载请求配置）。
    2. **变更型（MutatingWebhookConfiguration）**：用于在落盘前修改请求对象（如自动注入 Sidecar 或补充缺失的必填参数），实现原理是返回一个 `JSONPatch` 指令体。
  * **安全防坑约束**：被 API 服务器调用的 Webhook **必须且只能通过 HTTPS 通信**。这意味着开发者必须使用集群的证书颁发机构（CA）生成证书签名请求（CSR），并为准入控制器正确配置 TLS 证书。

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: loadtests.example.com
spec:
  group: example.com
  names:
    kind: LoadTest
    plural: loadtests
  scope: Namespaced
  versions:
    - name: v1
      served: true
      storage: true
      schema:
        openAPIV3Schema:
          type: object
          properties:
            spec:
              type: object
              properties:
                target:
                  type: string
                requests:
                  type: integer
                  minimum: 1
```

> 💡 **后续拓展空间**：深入探讨 Mutating 准入控制器的执行顺序优先级，以及它在 Service Mesh（如 Istio 自动注入 envoy 代理）中的核心底层原理。

---

## 自定义资源的模式 (Patterns for Custom Resources)

* **核心主旨**：根据业务抽象的深度，自定义资源 API 扩展主要分为三种渐进式的经典架构模式。
* **三大架构模式矩阵**：
  1. **纯数据模式 (Just Data)**：
     * **定义与机制**：仅将 API 服务器作为存放配置信息的存取中心（例如存储金丝雀发布的流量路由比例配置）。通常只需要一个 Webhook 确保数据格式合规，无需后台运行复杂的控制器。
     * **操作禁忌（防坑点）**：**绝不能将 Kubernetes API 服务器当作应用程序的通用键值数据库（Key/Value store）来存储业务数据**。API 扩展仅应被用于存储控制或配置数据。
  2. **编译器/抽象模式 (Compilers / Abstractions)**：
     * **定义与机制**：将高级的抽象对象「编译（Compiled）」转化为多个低级 Kubernetes 原生对象的组合（例如将一个用户层面的 `LoadTest` 对象编译为底层的若干个 Pods 和 Services）。
     * **逻辑脉络**：需要控制器在后台监听并负责生成和销毁底层对象。但**控制器不负责**这些低级对象的在线健康维护，健康检查和自愈被下放给低级对象（如 Pod 的重启策略）自身负责。
  3. **Operator 模式 (Operators)**：
     * **定义与价值**：最复杂但也最强大的终极扩展模式。在编译模式的基础上，Operator 还能对应用提供**在线的主动管理（Online, proactive management）**。
     * **核心行为**：Operator 扮演了「自动驾驶（Self-driving）」的人工智能运维角色，它会持续监控特定应用（如复杂数据库集群）的运行状态，执行诸如抓取快照备份、处理脑裂故障、检测到新版本后执行自动升级等闭环修复动作。
* **最佳实践起步 (Getting Started)**：
  * 从零手写 API 扩展不仅极度繁琐且极易引入并发漏洞。官方社区提供的 **`Kubebuilder`** 项目库封装了大量核心代码，是构建可靠 Kubernetes API 扩展的推荐脚手架。

| 模式 | 控制器职责 | 典型场景 |
|------|-----------|----------|
| Just Data | 无/仅 Webhook 校验 | 金丝雀比例配置 |
| Compiler | 生成/销毁底层 K8s 对象 | LoadTest → Pod+Service |
| Operator | 生成对象 + 主动运维闭环 | 数据库备份/升级/故障修复 |

> 💡 **后续拓展空间**：可在此补充 Operator Framework 或 CoreOS 提出的 Operator 成熟度模型（Capability Model），并以 Prometheus Operator 为例展示复杂应用的声明式纳管。

---

## 总结 (Summary)

* **核心论点归纳**：
  * Kubernetes 的一项伟大「超能力（Superpower）」在于其庞大的生态系统，而推动这一生态系统繁荣的最核心动力，正是 Kubernetes API 强大的**可扩展性（Extensibility）**。
  * 无论是通过自行设计 CRD 来个性化定制企业内部集群，还是引入外部现成的实用程序和 Operator 模式插件，掌握 API 扩展机制都是突破 Kubernetes 基础能力边界、快速构建和运维可靠现代分布式应用的绝对关键。

> 💡 **后续拓展空间**：可以引出 Helm 等包管理工具如何将复杂的 CRD 及配套的控制器进行一键打包分发，降低集群扩展组件的安装门槛。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| 扩展 K8s | 加功能或限制交互；需集群管理员权限 |
| CRD | 注册新 API 资源；名格式 `<plural>.<group>` |
| Controller | CRD 只存数据；控制器做协调循环 |
| Informer | 用 watch 替代轮询，client-go 最佳实践 |
| Mutating Webhook | 落盘前修改对象（注入 Sidecar 等） |
| Validating Webhook | 校验后放行或拒绝 |
| Webhook 安全 | 必须 HTTPS + 正确 TLS 证书 |
| Just Data | 仅存配置，勿当 KV 数据库 |
| Compiler 模式 | 高级 CR → 编译为 Pod/Service 等 |
| Operator | Compiler + 主动运维（备份/升级/修复） |
| Kubebuilder | 官方推荐 CRD/Controller 脚手架 |
