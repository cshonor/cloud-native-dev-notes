# 第十三章：ConfigMaps 与 Secrets (Chapter 13: ConfigMaps and Secrets)

## ConfigMaps

* **引入背景与核心痛点**：
  * 容器镜像应具备高度的**可复用性（Reusable）**。理想状态下，开发、预发、生产环境应运行完全相同的底层镜像。如果每个环境都需要重新打包镜像，不仅增加风险，也违背了不可变基础设施的原则。
* **核心定义与主旨**：
  * **ConfigMap** 是用于为工作负载提供配置信息的 Kubernetes API 对象。
  * 它可以被视为一个**小型的挂载文件系统**，或者一组可以在定义容器环境或命令行时使用的**变量集合**。
  * **逻辑脉络**：ConfigMap 是在 Pod 真正运行之前与其动态结合的。这意味着只需在运行时替换关联的 ConfigMap，同一个容器镜像就能在不同应用程序或环境中无缝复用。
* **创建配置 (Creating ConfigMaps)**：
  * 支持命令式创建：`kubectl create configmap <name> --from-file=<filepath> --from-literal=<key>=<value>`。其中 `--from-file` 导入整个文件，`--from-literal` 导入特定的键值对。
* **三大核心使用模式 (Using a ConfigMap)**：
  1. **文件系统挂载（Filesystem）**：
     * 将 ConfigMap 作为一个数据卷（Volume）挂载到 Pod 内部。ConfigMap 中的每一个键（Key）都会在这个目录下生成一个对应的同名文件，文件的内容就是该键对应的值（Value）。
  2. **环境变量注入（Environment variable）**：
     * 在 Pod 清单的 `env` 段落中，使用 `valueFrom.configMapKeyRef` 结构，将 ConfigMap 中特定键的值动态注入为容器的环境变量。
  3. **命令行参数（Command-line argument）**：
     * Kubernetes 支持基于注入的环境变量构建动态启动命令。在清单的 `command` 字段中，使用特殊的 `$(<ENV_VAR_NAME>)` 语法进行字符串插值替换。

```bash
kubectl create configmap app-config \
  --from-file=nginx.conf \
  --from-literal=log_level=info
```

```yaml
# 模式 1：文件挂载
volumes:
  - name: config
    configMap:
      name: app-config
volumeMounts:
  - name: config
    mountPath: /etc/config

# 模式 2：环境变量
env:
  - name: LOG_LEVEL
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: log_level

# 模式 3：命令行插值
env:
  - name: LOG_LEVEL
    valueFrom:
      configMapKeyRef:
        name: app-config
        key: log_level
command: ["/app/server", "--log-level=$(LOG_LEVEL)"]
```

> 💡 **后续拓展空间**：可在此处延伸补充如何使用 `subPath` 挂载机制，使得 ConfigMap 中的特定键值能够以单个文件的形式覆盖到容器现有的目录中，而不至于遮蔽该目录下的其他原生文件。

---

## Secrets

* **核心定义与场景**：
  * 虽然 ConfigMap 适合大多数常规配置，但面对**高敏感数据（Extra-sensitive data）**（如数据库密码、安全令牌、私钥或 TLS 证书），必须使用 **Secrets** 对象。
  * Secrets 防止敏感数据被硬编码打包进容器镜像中，从而保障镜像可以在不受信任的环境间安全分发。
* **底层安全机制与易错细节**：
  * **默认存储陷阱**：默认情况下，Kubernetes Secrets 以**明文（Plain text）**形式存储在集群底层的 `etcd` 数据库中。任何拥有集群管理员权限的用户都可以读取它们。
  * **加固建议**：现代 Kubernetes 支持集成云服务商的密钥管理系统（KMS）或自定义密钥对 Secrets 进行**静态加密（Encryption at rest）**。
* **创建与消费 (Creating and Consuming)**：
  * 通过命令 `kubectl create secret generic <name> --from-file=<key>=<filepath>` 生成。
  * **内存盘挂载（tmpfs）**：当以数据卷（Secrets volume）形式挂载到 Pod 时，kubelet 会将其直接挂载到 **`tmpfs`（RAM 磁盘）**中。**核心结论：Secrets 数据绝不会被写入工作节点的物理硬盘**，以防止由于硬盘废弃或窃取造成的数据泄露。
* **私有镜像仓库凭证 (Private Docker Registries)**：
  * **痛点**：若 Pod 引用了需要身份验证的私有镜像仓库，kubelet 将因无权限拉取镜像而失败。
  * **解决方案**：创建一种特殊类型的 Secret —— **Image Pull Secrets** (`kubectl create secret docker-registry ...`)，并在 Pod 规范的 `spec.imagePullSecrets` 数组中引用它，kubelet 会自动提取该凭证去拉取私有镜像。

```bash
kubectl create secret generic db-creds \
  --from-literal=username=admin \
  --from-literal=password=s3cr3t

kubectl create secret docker-registry regcred \
  --docker-server=registry.example.com \
  --docker-username=user \
  --docker-password=pass
```

```yaml
# Secret 挂载
volumes:
  - name: secrets
    secret:
      secretName: db-creds
volumeMounts:
  - name: secrets
    mountPath: /etc/secrets
    readOnly: true

# 私有镜像拉取
spec:
  imagePullSecrets:
    - name: regcred
```

> 💡 **后续拓展空间**：可拓展介绍 Kubernetes 社区外部凭证管理方案，例如结合 HashiCorp Vault 的生态集成，或者云平台原生的 CSI 密钥驱动（Secrets Store CSI Driver），彻底避免在 etcd 中长期存储敏感信息。

---

## 命名约束 (Naming Constraints)

* **数据键名规范（Key Names）**：
  * ConfigMap 和 Secret 中的键名必须符合有效的环境变量命名规范。
  * **正则表达式限制**：只能包含字母、数字、破折号（`-`）、下划线（`_`）和点（`.`）。点不能连续重复出现，点、破折号、下划线互相之间不能相邻。
  * **实用要点**：命名时应考虑挂载为文件后的可读性。例如，将 TLS 密钥命名为 `key.pem` 远比 `tls-key` 显得更符合 Linux 文件系统惯例。
* **数据格式与体积限制 (Data Formats and Limits)**：
  * **ConfigMap**：数据值被视为**简单的 UTF-8 纯文本**。
  * **Secret**：为了安全存储二进制数据（如非 ASCII 的加密证书），其数据值在底层全部采用 **Base64 编码（Base64 encoding）**进行序列化存放。
  * **硬性体积红线**：ConfigMap 或 Secret 对象的**最大体积被严格限制为 1 MB**。它们被设计为存放零散配置，不适合当成大型文件存储系统使用。

```yaml
# Secret YAML：data 需 Base64；stringData 可写明文（仅写入时）
apiVersion: v1
kind: Secret
metadata:
  name: tls-cert
type: kubernetes.io/tls
stringData:
  tls.crt: |
    -----BEGIN CERTIFICATE-----
    ...
  tls.key: |
    -----BEGIN PRIVATE KEY-----
    ...
```

> 💡 **后续拓展空间**：进一步解释在 YAML 清单中编写 Secret 时，`data` 字段必须预先 Base64 编码，而 `stringData` 字段（仅写入时有效）允许用户直接写明文的机制差异。

---

## 管理 ConfigMaps 与 Secrets (Managing ConfigMaps and Secrets)

* **列表与探查 (Listing)**：
  * 使用 `kubectl get configmaps` 或 `kubectl get secrets` 查看。使用 `kubectl describe` 可以展示键名列表和各自的数据体积大小，但不会直接暴露 Secret 数据内容。
  * 若想强行提取数据原文，需通过 `-o yaml` 导出原始表现形式，并自行针对 Secret 执行 Base64 解码。
* **三种更新手段 (Updating)**：
  1. **从文件更新 (Update from file)**：
     * 修改原始 YAML 清单后，使用 `kubectl replace -f` 或 `kubectl apply -f` 推送覆盖。
     * **极高危防坑警告**：**绝对不要将包含明文/Base64敏感数据的 Secret YAML 文件提交到代码版本控制库（Source control / Git）中！**这极易导致安全事故。
  2. **重建并覆盖更新 (Recreate and update)**：
     * 如果不希望手动处理烦琐的 Base64 编解码，可以使用 Unix 管道流重塑更新流：
     * `kubectl create secret generic <name> --from-file=<file> --dry-run -o yaml | kubectl replace -f -`。这巧妙地利用 `--dry-run` 在本地生成内存配置结构，并直接推送给 API Server 覆盖当前版本。
  3. **交互式编辑 (Edit current version)**：
     * 执行 `kubectl edit configmap <name>` 唤出文本编辑器实时保存变更。
* **热更新机制 (Live Updates)**：
  * **核心机制**：一旦 ConfigMap 或 Secret 通过 API Server 被更新，kubelet 会在数秒钟后将更新后的文件内容**自动静默推送到所有挂载了该卷的运行中容器内部**。
  * **系统局限性**：Kubernetes 目前**没有内置机制主动向应用程序发送配置变更信号（如 SIGHUP）**。这要求应用程序本身具备热加载能力（如定期轮询或监听 Inotify 文件系统事件），否则即使底层文件已更新，程序可能依然需要重启才能读取新配置。

```bash
kubectl get configmaps
kubectl describe secret db-creds
kubectl edit configmap app-config

# 安全更新 Secret（不提交 Git）
kubectl create secret generic db-creds \
  --from-literal=password=newpass \
  --dry-run=client -o yaml | kubectl apply -f -
```

> 💡 **后续拓展空间**：推荐配合开源工具（如 `Reloader` 或 `Kustomize` 的 SecretGenerator哈希重载机制）来实现：当 ConfigMap 发生变更时，自动触发关联 Deployment 的滚动重启（RollingUpdate）。

---

## 总结 (Summary)

* **核心主旨提炼**：
  * ConfigMaps 和 Secrets 提供了应用程序的**动态配置（Dynamic configuration）**能力。
  * 它们彻底切断了「配置数据」与「应用程序代码」的硬编码绑定。依靠这套机制，企业不仅能打通同一镜像从 Dev 到 Staging 再到 Prod 环境的安全流转，还能实现单个镜像在多个不同微服务团队中的泛化复用。分离配置与代码，是让应用实现极高可用性和复用性的架构基石。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| ConfigMap | 非敏感配置；挂载 / env / 命令行三种消费方式 |
| Secret | 敏感数据；默认 etcd 明文，建议 KMS 加密 |
| Secret 挂载 | tmpfs 内存盘，不写节点硬盘 |
| imagePullSecrets | 私有镜像仓库拉取凭证 |
| 体积限制 | ConfigMap/Secret 最大 1 MB |
| Secret 编码 | `data` 需 Base64；`stringData` 可写明文 |
| 热更新 | kubelet 自动推送文件；应用需自行 reload |
| 安全禁忌 | Secret YAML 勿提交 Git |
