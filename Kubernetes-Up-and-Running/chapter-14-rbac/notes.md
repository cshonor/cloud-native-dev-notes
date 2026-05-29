# 第十四章：Kubernetes的基于角色的访问控制 (Chapter 14: Role-Based Access Control for Kubernetes)

## 基于角色的访问控制 (Role-Based Access Control)

* **核心定义与主旨**：
  * **RBAC (Role-Based Access Control)** 是一种限制对Kubernetes API的访问和操作的机制，确保只有合适的用户才能访问集群中的API。
  * **多租户安全警告（防坑指南）**：RBAC虽然能限制API访问，但如果用户能在集群内运行任意代码，他们实际上就能获得整个集群的root权限。因此，仅靠RBAC不足以防范恶意多租户，必须结合**虚拟机隔离容器（Hypervisor isolated container）**或容器沙箱技术。
* **请求处理的逻辑脉络**：
  1. **身份认证 (Authentication)**：识别发出请求的调用者身份。Kubernetes没有内置的身份存储，而是深度集成了可插拔的认证提供商（如HTTP Basic、x509客户端证书、静态令牌、Azure AD/AWS IAM等云提供商、以及Webhooks）。
  2. **授权 (Authorization)**：结合用户的**身份 (Identity)**、**资源 (Resource)**（即HTTP路径）以及**动词/操作 (Verb)**，决定该请求是否被允许。如果未授权，则返回HTTP 403错误。

```
请求 → Authentication（你是谁）→ Authorization（你能做什么）→ API 处理
```

* **Kubernetes中的身份 (Identity)**：
  * **服务账户 (Service accounts)**：由Kubernetes自身创建和管理，通常与集群内运行的组件关联。
  * **用户账户 (User accounts)**：与实际用户或集群外的自动化系统（如CI/CD服务）关联。未认证的请求也会被关联到特殊的 `system:unauthenticated` 组。
* **角色与角色绑定 (Roles and Role Bindings)**：
  * **角色 (Role)**：一组抽象的能力集合（例如：创建Pods和Services的能力）。
  * **角色绑定 (RoleBinding)**：将一个角色分配给一个或多个身份（用户或组）。
  * **层级划分机制**：
    1. **命名空间级别**：`Role` 和 `RoleBinding`。它们仅在声明它们的特定命名空间内有效，不能用于非命名空间资源（如CRD）。
    2. **集群级别**：`ClusterRole` 和 `ClusterRoleBinding`。作用域覆盖整个集群或用于限制集群级别的资源。
* **RBAC操作动词矩阵 (Verbs)**：
  * 角色能力通过资源和**动词 (Verb)**来定义，动词大致映射到HTTP方法：
    * `create` (POST)、`delete` (DELETE)、`get` (GET)、`list` (GET)、`patch` (PATCH)、`update` (PUT)、`watch` (GET)、`proxy` (GET)。
* **内置角色与自动协调陷阱 (Built-in Roles & Auto-reconciliation)**：
  * **四大通用最终用户角色**：`cluster-admin`（集群完全访问）、`admin`（命名空间完全访问）、`edit`（命名空间内修改权限）、`view`（命名空间只读权限）。
  * **易错细节（自动更新覆盖）**：API服务器启动时会自动安装/覆盖内置的ClusterRoles。如果你修改了内置角色，重启后修改将丢失。**解决方案**：在内置角色上添加注解 `rbac.authorization.kubernetes.io/autoupdate: "false"` 以阻止系统覆盖。
  * **极高危安全配置**：默认情况下，系统允许 `system:unauthenticated` 组访问API服务器的发现端点。如果集群暴露在公网，这会导致严重的安全漏洞。**必须在API服务器上设置 `--anonymous-auth=false` 标志**以关闭匿名访问。

```yaml
# 命名空间级 Role + RoleBinding
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: dev
  name: pod-reader
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  namespace: dev
  name: read-pods
subjects:
  - kind: User
    name: jane
    apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

> 💡 **后续拓展空间**：可在此补充Kubernetes中Webhook模式的认证与授权流程细节，以及如何集成OpenID Connect (OIDC) 实现企业级单点登录 (SSO)。

---

## 管理RBAC的技术 (Techniques for Managing RBAC)

* **核心主旨**：由于RBAC配置不当可能导致严重的安全问题，使用专门的工具和版本控制技术来管理RBAC是生产环境的最佳实践。
* **授权测试工具 (can-i)**：
  * **机制与命令**：使用 `kubectl auth can-i <verb> <resource>` 命令，可以在配置集群或排查用户权限时，快速验证特定用户是否具备执行某项操作的权限。
  * **子资源验证**：通过附加 `--subresource` 标志，可以测试日志查看或端口转发等深层权限（如：`kubectl auth can-i get pods --subresource=logs`）。
* **源码控制与声明式管理 (Managing RBAC in Source Control)**：
  * **逻辑脉络**：由于RBAC策略需要强审计、问责和回滚能力，必须将其YAML/JSON文件存入版本控制系统（如Git）。
  * **专用协调命令**：有别于普通的 `apply`，Kubernetes提供了专门的授权协调命令 `kubectl auth reconcile -f <rbac-config.yaml>`，用于将文本定义的角色和绑定安全地与集群当前状态进行协调同步。结合 `--dry-run` 可以在实际应用前预览变更。

```bash
kubectl auth can-i create deployments --namespace=dev
kubectl auth can-i get pods --subresource=logs
kubectl auth can-i '*' '*' --as=jane

kubectl auth reconcile -f rbac.yaml
kubectl auth reconcile -f rbac.yaml --dry-run=client
```

> 💡 **后续拓展空间**：可在此引入GitOps理念，探讨如何使用ArgoCD或Flux自动同步Git仓库中的RBAC策略，并防止用户通过kubectl直接在集群上进行手动提权。

---

## 高级主题 (Advanced Topics)

* **聚合ClusterRoles (Aggregating ClusterRoles)**：
  * **核心机制**：在管理大规模角色时，直接复制权限容易出错。Kubernetes支持通过**聚合规则 (aggregationRule)**将多个基础角色组合成一个全新的高级角色。
  * **底层逻辑**：聚合是通过**标签选择器 (label selectors)**实现的。在ClusterRole的 `clusterRoleSelectors` 字段中定义选择器，所有匹配该标签的ClusterRoles的权限会自动且动态地合并到当前角色的 `rules` 数组中。子角色的任何更新都会自动传递给聚合角色。
  * **最佳实践**：创建大量细粒度的基础角色，然后通过标签（例如：`rbac.authorization.k8s.io/aggregate-to-edit: "true"`）将它们聚合成如 `edit` 或 `admin` 这样的高级内置角色。
* **使用组进行绑定 (Using Groups for Bindings)**：
  * **核心理念**：在大型组织中，应始终将RoleBinding绑定到**组 (Group)**，而不是具体的**个人 (Individual)**。
  * **优势脉络分析**：
    1. **人员伸缩与一致性**：权限按团队划分（如前端运维团队）。人员入职/离职只需在身份提供商端加入/移出组，而无需在K8s集群内修改数十个RoleBinding，确保了权限配置的绝对一致性。
    2. **JIT即时访问 (Just-in-Time Access)**：许多身份系统支持基于事件（如深夜报警）临时将用户加入高权限组。这确保了生产环境不会存在常驻的个人高权限，有效控制被盗账号的危害。
  * **语法要点**：在RoleBinding的 `subjects` 列表中，将 `kind` 设置为 `Group`，由外部的身份认证提供商向K8s传递组信息。

```yaml
# 绑定到组而非个人
subjects:
  - kind: Group
    name: dev-team
    apiGroup: rbac.authorization.k8s.io
```

> 💡 **后续拓展空间**：可深入解析如何利用K8s的 `Impersonation` (用户伪装) API 来测试和验证Group的权限边界，以及RBAC中的通配符(`*`)滥用可能导致的权限逃逸漏洞。

---

## 总结 (Summary)

* **核心论点归纳**：
  * 随着团队扩张和产品的核心化，集群不能再保持「人人拥有同等访问权限」的模式。
  * **最小权限原则**：在一个设计良好的集群中，应当将访问权限严格限制为仅满足有效管理应用所需的最小人员集合和最小能力集合。
  * **实施建议**：与测试基础设施的建设一样，RBAC的最佳实践是**尽早建立**，从一开始就打下正确的基础，远比在后期强行改造成本要低得多。

> 💡 **后续拓展空间**：可衔接后续的安全加固章节，探讨RBAC如何与网络策略 (Network Policies) 和准入控制器 (Admission Controllers) 共同构成Kubernetes集群的纵深防御 (Defense in Depth) 体系。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| RBAC | 认证 + 授权，限制 API 访问 |
| Role / RoleBinding | 命名空间级权限与绑定 |
| ClusterRole / ClusterRoleBinding | 集群级权限与绑定 |
| Verbs | create/get/list/delete/patch/update/watch/proxy |
| 内置角色 | cluster-admin / admin / edit / view |
| can-i | 快速测试当前用户是否有某权限 |
| auth reconcile | RBAC 专用协调命令，优于普通 apply |
| 绑定组 | 权限绑 Group 不绑个人，便于入职离职 |
| 多租户局限 | RBAC 不够，需容器沙箱/虚拟机隔离 |
| 匿名访问 | 公网集群须 `--anonymous-auth=false` |
