# 第四章：常用的 kubectl 命令 (Chapter 4: Common kubectl Commands)

## 命名空间 (Namespaces)

* **核心定义与主旨**：
  * **命名空间（Namespaces）**是 Kubernetes 中用于组织集群内对象的机制，逻辑上类似于文件系统中的文件夹。
* **操作命令与逻辑脉络**：
  * 默认情况下，`kubectl` 命令行工具仅与 `default` 命名空间交互。
  * **指定命名空间**：通过在命令后添加 `--namespace=<name>` 标志，可以访问特定命名空间中的对象。
  * **全局查询**：若需跨所有命名空间进行交互（例如列出集群中的所有 Pods），需使用 `--all-namespaces` 标志。

```bash
kubectl get pods
kubectl get pods -n kube-system
kubectl get pods --all-namespaces
```

> 💡 **后续拓展空间**：可在此补充如何通过 `ResourceQuota` 和 `LimitRange` 在命名空间级别进行资源配额限制和默认资源分配的高级用例。

---

## 上下文 (Contexts)

* **核心定义与主旨**：
  * **上下文（Contexts）**用于持久化地更改 `kubectl` 的默认命名空间、集群连接信息和身份验证配置。相关配置通常存储在 `$HOME/.kube/config` 文件中。
* **操作命令与执行逻辑**：
  * **设置上下文**：使用 `kubectl config set-context <context-name> --namespace=<namespace-name>` 创建或修改上下文环境。
  * **应用上下文**：创建后不会立即生效，必须通过 `kubectl config use-context <context-name>` 显式切换并启用新配置。
* **实用要点**：
  * 通过组合使用 `--users` 或 `--clusters` 标志，上下文配置可以极其方便地在多个物理集群或不同认证用户之间进行快速切换。

```bash
kubectl config set-context dev --namespace=dev --cluster=minikube --user=minikube
kubectl config use-context dev
kubectl config get-contexts
```

> 💡 **后续拓展空间**：可进一步探讨 `kubeconfig` 文件的多文件合并机制（利用 `KUBECONFIG` 环境变量）以及相关的安全管理最佳实践。

---

## 查看 Kubernetes API 对象 (Viewing Kubernetes API Objects)

* **核心概念与底层逻辑**：
  * Kubernetes 中的所有内容均表示为 **RESTful 资源（API 对象）**。每个对象均挂载在唯一的 HTTP 路径下（例如，`default` 命名空间中的 Pod `my-pod` 其路径为 `/api/v1/namespaces/default/pods/my-pod`）。
  * `kubectl` 命令本质上是向这些 URL 发起 HTTP 请求以访问对应对象。
* **基础与高阶查询命令**：
  * **基础列表**：`kubectl get <resource-name>` 列出当前命名空间下该资源的所有实例。
  * **特定对象查询**：`kubectl get <resource-name> <obj-name>` 获取单一指定对象的摘要信息。
* **格式化与数据提取要点**：
  * **人类可读性（默认）**：默认打印精简表格。添加 `-o wide` 标志可输出包含更多详细信息的加长表格。
  * **原始数据格式**：使用 `-o json` 或 `-o yaml` 标志可查看对象的完整定义。
  * **管道流处理**：添加 `--no-headers` 标志可移除输出的表头，极度适合与 Unix 管道命令（如 `awk`）结合使用。
  * **精准字段提取**：利用 **JSONPath** 查询语言可精确抓取指定字段。例如：`kubectl get pods my-pod -o jsonpath --template={.status.podIP}` 可直接提取 Pod 的 IP 地址。
* **深度排查工具**：
  * 使用 `kubectl describe <resource-name> <obj-name>` 可生成该对象的丰富多行摘要，并关联展示底层的相关事件（Events），是核心的排障命令。

```bash
kubectl get pods -o wide
kubectl get pod my-pod -o yaml
kubectl get pod my-pod -o jsonpath='{.status.podIP}'
kubectl describe pod my-pod
kubectl api-resources
```

> 💡 **后续拓展空间**：可深入介绍 Kubernetes API 组（API Groups）的层级架构（如 `apps/v1` 等）以及如何使用 `kubectl api-resources` 探索可用端点。

---

## 创建、更新和销毁 Kubernetes 对象 (Creating, Updating, and Destroying Kubernetes Objects)

* **核心理念**：
  * Kubernetes API 对象通过 JSON 或 YAML 文件表示，可使用这些文件在服务器上创建、更新或删除对象。
* **操作命令与执行机制**：
  * **声明式应用（Apply）**：`kubectl apply -f obj.yaml` 是核心命令。它会自动从文件中识别资源类型并进行创建或更新。
  * **幂等性逻辑**：`apply` 命令仅对「与集群当前状态不同」的变更进行修改。若集群状态已满足文件要求，则安全退出，这使得它非常适合在持续协调循环（Reconcile loop）中使用。
  * **防坑细节与测试**：添加 `--dry-run` 标志可在不向服务器发送实际写请求的情况下，向终端打印预计会发生的变更结果。
  * **交互式编辑**：`kubectl edit <resource-name> <obj-name>` 可直接下载对象当前状态，使用本地编辑器修改后保存，即刻自动覆盖回集群。
* **状态记录溯源**：
  * `apply` 命令会在对象的注解（Annotation）中记录历史配置。可通过 `edit-last-applied`、`set-last-applied` 和 `view-last-applied` 命令对其进行查看和回溯。
* **销毁对象的硬性警告**：
  * 删除命令：`kubectl delete -f obj.yaml` 或 `kubectl delete <resource-name> <obj-name>`。
  * **易错细节（极度危险）**：执行删除命令时，**`kubectl` 绝对不会弹出二次确认提示，一旦回车，对象将立刻被彻底删除！**。

```bash
kubectl apply -f deployment.yaml
kubectl apply -f deployment.yaml --dry-run=client
kubectl edit deployment my-app
kubectl delete -f deployment.yaml
```

> 💡 **后续拓展空间**：可补充介绍 Kubernetes 服务端应用（Server-side Apply）相较于客户端 `kubectl apply` 的架构级差异及冲突解决逻辑。

---

## 标记和注解对象 (Labeling and Annotating Objects)

* **核心概念**：
  * **标签（Labels）**和**注解（Annotations）**是挂载在对象上的键值对数据元组。
* **命令规范与易错细节**：
  * **添加/修改**：使用 `kubectl label pods bar color=red`。默认情况下，不允许直接覆盖已存在的标签，必须显式附加 `--overwrite` 标志。
  * **删除逻辑**：若要删除标签，其语法为键名后紧跟一个减号（`-`），例如 `kubectl label pods bar color-`。
  * 注解操作：`kubectl annotate` 命令的语法与行为逻辑与 `label` 完全一致。

```bash
kubectl label pod bar color=red
kubectl label pod bar color=blue --overwrite
kubectl label pod bar color-
kubectl annotate pod bar description="test pod"
```

> 💡 **后续拓展空间**：深入分析标签选择器（Label Selectors）在底层 Controller 匹配（如 ReplicaSet 纳管 Pod）时的集合与等式判定机制。

---

## 调试命令 (Debugging Commands)

* **核心调试矩阵**：
  1. **日志流（Logs）**：
     * `kubectl logs <pod-name>` 获取输出日志。
     * 多容器场景下，必须用 `-c` 标志指定具体的容器名称。
     * 追加 `-f` (`follow`) 可实现日志的持续无中断实时追踪。
     * **高优排障技巧**：对于频繁崩溃导致刚启动即销毁的容器，必须使用 `--previous` 标志调取上一已死容器实例的「遗言」日志。
  2. **远程执行（Exec）**：
     * `kubectl exec -it <pod-name> -- bash` 可直接进入运行中容器的内部，开启一个交互式 Shell 会话进行内核级排障。
  3. **依附控制台（Attach）**：
     * 若容器内缺少 `bash` 环境，可使用 `kubectl attach -it <pod-name>` 直接连接到正在运行的主进程（前提是该进程已配置标准输入/输出接入）。
  4. **双向文件拷贝（Copy）**：
     * `kubectl cp <pod-name>:</remote/path> </local/path>` 实现在远程容器与本地机器间的双向文件（或目录）拷贝。
  5. **端口转发隧道（Port-forwarding）**：
     * `kubectl port-forward <pod-name> 8080:80` 可安全穿透到内网，将本地 8080 端口请求转发到远端容器 80 端口。
     * **易错细节**：虽可以将该命令作用于 Service (`services/<name>`)，但这会导致请求**只被锁定转发到该服务后端的单一 Pod 上**，负载均衡机制在此时将完全失效。
  6. **资源利用率查看（Top）**：
     * `kubectl top nodes` / `kubectl top pods` 可展示绝对单位（如核心数）及百分比形式的 CPU 与内存消耗情况（支持 `--all-namespaces`）。

```bash
kubectl logs my-pod -f
kubectl logs my-pod --previous
kubectl exec -it my-pod -- bash
kubectl port-forward pod/my-pod 8080:80
kubectl top pods
```

> 💡 **后续拓展空间**：可补充介绍 Kubernetes v1.18+ 引入的临时容器调试功能（`kubectl debug`，Ephemeral Containers），专门针对极简镜像（Distroless）的终极排障方案。

---

## 命令自动补全 (Command Autocompletion)

* **实现机制**：
  * `kubectl` 原生支持与 shell 集成以提供命令和资源的按 Tab 键自动补全功能。
* **配置规范**：
  * 前置依赖：需要通过系统包管理器预先安装好 `bash-completion` 环境（如 `brew`, `yum`, `apt-get`）。
  * 临时激活：执行 `source <(kubectl completion bash)`。
  * **持久化操作**：追加配置到终端启动文件 `echo "source <(kubectl completion bash)" >> ${HOME}/.bashrc`（同样支持 `zsh` 环境）。

> 💡 **后续拓展空间**：可以进一步推荐 Kubernetes 社区广泛使用的 CLI 增强别名（如 `alias k=kubectl`）的完整补全绑定配置。

---

## 查看集群的其他替代方式 (Alternative Ways of Viewing Your Cluster)

* **生态拓展**：
  * 除 `kubectl` 之外，许多代码编辑器提供了深度集成的 Kubernetes 插件（如：**Visual Studio Code**, **IntelliJ**, **Eclipse**）。
  * 开源社区还提供了移动应用程序，支持通过手机监控管理集群。

> 💡 **后续拓展空间**：推荐现代云原生生态中备受推崇的终端可视化管理神器（如 `k9s` 或 `Lens`）。

---

## 总结 (Summary)

* **核心结论**：
  * `kubectl` 是管理 Kubernetes 集群和应用程序功能的强大入口。
* **实用要点**：
  * 面对遗忘的指令，始终依赖其内置的强大帮助系统：执行 `kubectl help` 获取大盘指引，或执行 `kubectl help <command-name>` 获取单指令的细节语法和代码示例。

> 💡 **后续拓展空间**：引出后续章节关于声明式资源部署（Deployments）的实践编排，将零散命令组织成自动化运维管线。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| Namespace | 逻辑隔离；`-n` 指定，`--all-namespaces` 全局 |
| Context | kubeconfig 中集群+用户+默认 ns 的组合 |
| get / describe | get 列表摘要；describe 详情 + Events |
| apply | 声明式幂等创建/更新；`--dry-run` 预演 |
| delete | 无二次确认，回车即删 |
| label / annotate | 键值元数据；覆盖需 `--overwrite`，删除用 `key-` |
| logs --previous | 崩溃容器的上一轮日志 |
| port-forward | 本地隧道；对 Service 会绕过负载均衡 |
| completion | `source <(kubectl completion bash)` |
