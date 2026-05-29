# 第十七章：部署真实的应用程序 (Chapter 17: Deploying Real-World Applications)

## 引入与核心主旨 (Introduction)

* **核心主旨**：
  * 前置章节介绍了 Kubernetes 集群中各种独立的 API 对象（如 Pods, ReplicaSets, Deployments, StatefulSets 等），本章旨在展示如何将这些组件拼装组合，用于部署和管理完整的、真实的分布式应用程序。
* **四大真实案例矩阵**：
  * **Jupyter**：基于 Web 的开源科学计算笔记本。
  * **Parse**：面向移动应用的开源 API 服务器。
  * **Ghost**：博客与内容管理平台。
  * **Redis**：轻量级、高性能的键值对（Key/Value）存储。

| 应用 | 核心 K8s 模式 | 状态依赖 |
|------|--------------|----------|
| Jupyter | Deployment + port-forward | 无（可扩展 PV） |
| Parse | Deployment + env + Service | MongoDB StatefulSet |
| Ghost | ConfigMap + Deployment → 横向扩容 | SQLite → MySQL |
| Redis | StatefulSet + Headless + 多容器 Pod | 内存 + 主从复制 |

> 💡 **后续拓展空间**：可在此补充如何利用 Helm Charts 这样的包管理工具将这些复杂的多组件应用打包为一键安装的模板，进一步简化真实应用的部署流程。

---

## Jupyter (科学计算笔记本)

* **核心定义与场景**：
  * **Jupyter Project** 供全球学生和科学家用于数据探索与可视化，由于其部署简单且使用场景有趣，是入门 Kubernetes 部署的绝佳首选。
* **部署逻辑与操作脉络**：
  1. **隔离部署环境**：首先通过 `kubectl create namespace jupyter` 创建专用的命名空间。
  2. **创建单副本部署 (Deployment)**：编写 `jupyter.yaml`，指定镜像为 `jupyter/scipy-notebook`，并在 `jupyter` 命名空间下启动 1 个副本的 Deployment。
  3. **状态追踪**：由于该容器镜像非常庞大（约 2GB），启动需要几分钟时间，可通过 `watch kubectl get pods` 持续监控拉取和启动进度。
* **访问与调试要点**：
  * **获取动态 Token**：Jupyter 启动时会生成一个动态的初始登录 Token。必须通过 `kubectl logs` 命令查看对应 Pod 的启动日志来提取该 Token。
  * **端口转发映射**：使用 `kubectl port-forward <pod-name> 8888:8888` 将集群内 Pod 的端口安全映射到本地，从而通过 `http://localhost:8888/?token=<token>` 在浏览器中访问仪表板。

```bash
kubectl create namespace jupyter
kubectl apply -f jupyter.yaml -n jupyter
watch kubectl get pods -n jupyter
kubectl logs -n jupyter <pod-name> | grep token
kubectl port-forward -n jupyter <pod-name> 8888:8888
```

> 💡 **后续拓展空间**：可拓展如何结合 Kubernetes 的 PersistentVolume (PV) 为 Jupyter 提供持久化的 Notebook 文件存储，防止 Pod 重启导致代码丢失。

---

## Parse (移动应用 API 服务器)

* **核心定义与背景**：
  * **Parse server** 是一个为移动应用提供易用存储的云 API（曾被 Facebook 收购后开源）。
* **前置依赖与架构设计**：
  * **有状态后端支撑**：Parse 的运行强依赖于一个健康的 MongoDB 集群。部署前必须已经通过 StatefulSet 建立了一个三副本的 Mongo 集群（节点如 `mongo-0.mongo`、`mongo-1.mongo` 等）。
* **部署脉络与配置细节**：
  1. **自定义镜像构建 (Build & Push)**：克隆 Parse 源码仓库，使用内置的 Dockerfile 通过 `docker build` 构建镜像，并推送到公开的 Docker Hub。
  2. **环境变量注入**：在 Deployment 声明中，Parse 核心通过三个**环境变量（Environment Variables）**进行配置：
     * `PARSE_SERVER_APPLICATION_ID`：应用的授权标识。
     * `PARSE_SERVER_MASTER_KEY`：超级管理员密钥。
     * `PARSE_SERVER_DATABASE_URI`：**核心关联配置**，其值必须指向预先搭建好的 MongoDB 集群的完整连接字符串（例如 `mongodb://mongo-0.mongo:27017,.../?replicaSet=rs0`）。
* **服务暴露与测试**：
  * 通过创建 `Service` 对象将容器的 1337 端口暴露出来，供前端移动应用调用。

```yaml
env:
  - name: PARSE_SERVER_APPLICATION_ID
    value: myAppId
  - name: PARSE_SERVER_MASTER_KEY
    valueFrom:
      secretKeyRef:
        name: parse-secrets
        key: master-key
  - name: PARSE_SERVER_DATABASE_URI
    value: mongodb://mongo-0.mongo:27017,mongo-1.mongo:27017/?replicaSet=rs0
```

> 💡 **后续拓展空间**：可以进一步结合 Kubernetes Secrets 来存放 `PARSE_SERVER_MASTER_KEY` 等敏感环境变量，替代直接在 Deployment YAML 中硬编码明文密码的做法。

---

## Ghost (博客平台)

* **核心定义与场景**：
  * **Ghost** 是一款使用 JavaScript 编写的流行博客引擎，支持文件型 SQLite 数据库或 MySQL 数据库作为底层存储。
* **架构演进与配置逻辑**：
  * **阶段一：单点测试配置 (SQLite)**
    * **配置外置 (ConfigMap)**：将 `ghost-config.js` 配置文件通过 `kubectl create cm --from-file` 转化为 Kubernetes 的 ConfigMap。
    * **挂载陷阱与巧妙解法**：Kubernetes 的 ConfigMap 挂载机制默认会**覆盖整个目录**，但 Ghost 期望在目录中还能看到其他原生文件。解决方案是在 Pod 的 `command` 中注入一个启动脚本（如 `cp /ghost-config/ghost-config.js /var/lib/ghost/config.js`），将配置文件从挂载点复制到应用期望的最终路径，再启动 Node.js 进程。
    * **暴露访问**：通过 `kubectl proxy` 建立安全隧道访问服务。
  * **阶段二：生产级可扩展架构 (Ghost + MySQL)**
    * **状态剥离**：将数据库连接配置从 SQLite 更改为外部的 `mysql` 服务。
    * **横向扩容 (Scale out)**：因为应用的**状态已被成功解耦（Decoupled）**到数据库中，Ghost 应用本身变为了无状态服务。此时可以直接将 Deployment 的 `replicas` 从 1 修改为 3，轻松实现水平扩展。

```yaml
# ConfigMap 挂载陷阱的启动脚本解法
command:
  - /bin/sh
  - -c
  - |
    cp /ghost-config/ghost-config.js /var/lib/ghost/config.js
    node current/index.js
```

> 💡 **后续拓展空间**：探讨在具有多个 Ghost Web 副本时，如何配置 Ingress 规则和 TLS 证书来实现生产级别的域名路由与 HTTPS 加密访问。

---

## Redis (键值存储集群)

* **核心定义与架构级价值**：
  * **Redis** 是一款高性能的内存键值存储系统。
  * **Pod 抽象的最佳实践**：部署一个高可用的 Redis 是展示 Kubernetes **Pod 内部多容器共生抽象（Pod abstraction）**价值的绝佳范例。一个可靠的 Redis 节点实际上需要两个程序协同工作：`redis-server`（负责读写数据）和 `redis-sentinel`（负责健康检查与主从故障转移）。这两个程序被**完美同置（Colocated）**在同一个 Pod 中运行。
* **配置文件聚合 (ConfigMaps)**：
  * Redis 部署极度依赖配置。需要为 Master (`master.conf`)、Slave (`slave.conf`)、Sentinel (`sentinel.conf`) 以及启动引导脚本 (`init.sh`, `sentinel.sh`) 创建多个配置文件。
  * 所有的这些文件被打包进一个单一的、巨大的 `redis-config` ConfigMap 中。
* **部署与网络拓扑策略**：
  * **无头服务 (Headless Service)**：为 Redis 创建一个 `clusterIP: None` 的服务，这使得系统为每个副本分配可解析的独立 DNS 名称（如 `redis-0.redis`），用于集群内部的主从寻址。
  * **有状态副本集 (StatefulSet)**：使用 StatefulSet 进行部署，以获得有序创建和严格的索引后缀（`redis-0`, `redis-1`）。
* **读写分离逻辑验证 (Testing)**：
  * 使用 `kubectl exec` 登入 `redis-2` (只读副本) 尝试写入数据会收到错误 `READONLY You can't write against a read only slave`。
  * 登入 `redis-0` (主节点) 写入数据成功，随后在 `redis-2` 上可成功读取该数据，证明主从数据复制链路已连通。

```bash
# 验证主从复制
kubectl exec -it redis-0 -- redis-cli SET key hello
kubectl exec -it redis-2 -- redis-cli GET key
kubectl exec -it redis-2 -- redis-cli SET key fail   # READONLY 错误
```

> 💡 **后续拓展空间**：可以进一步讨论当 Redis Master (`redis-0`) 发生物理宕机时，`redis-sentinel` 是如何自动选举新的 Master，以及 StatefulSet 控制器是如何在其他节点上重新拉起 `redis-0` 的自愈全过程。

---

## 总结 (Summary)

* **核心结论提炼**：
  * 本章通过将各种 Kubernetes 概念融会贯通，演示了多类型应用的部署模式。
  * 利用**基于服务的命名与发现（Service-based naming and discovery）**可以部署 Web 前端（Ghost）和 API 后端（Parse）。
  * 利用 **Pod 的多容器抽象（Pod abstraction）**可以轻松部署由多个共生组件构成的高可用系统（Redis 集群）。
  * 掌握这些模式化的部署套路，是在现实生产环境中利用 Kubernetes 管理复杂分布式应用的基础。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| Jupyter | Namespace + Deployment；logs 取 token + port-forward |
| Parse | 依赖 Mongo StatefulSet；env 注入 DB URI |
| Ghost SQLite | ConfigMap 挂载会盖目录 → 启动脚本 cp 配置 |
| Ghost 生产 | 状态外置 MySQL → replicas 横向扩容 |
| Redis | 同 Pod 内 redis-server + sentinel |
| Redis 拓扑 | Headless Service + StatefulSet 固定 DNS |
| 完整链路 | 镜像 → Deployment/StatefulSet → Service → Config/Secret |
