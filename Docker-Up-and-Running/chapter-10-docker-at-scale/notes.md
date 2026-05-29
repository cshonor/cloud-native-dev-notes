# 第10章 大规模使用 Docker (Docker at Scale)

> **版次说明**：中译/第一版常称「第9章 大规模使用 Docker」，第二版目录为 **Ch 10**。  
> **后端学习提示**：本书策略为 **跳过实操**——Swarm / Centurion / ECS 属历史或云厂商方案；后端主线是 **镜像 + Registry + Kubernetes**。本章建立「单机 → 集群 → 托管编排」脉络即可，细节见《K8s Up & Running》。

## 章节核心主旨与背景

* **核心主旨与实用要点**
  * 阐明了从单机环境向大规模集群、云平台演进的核心优势：Docker 对底层硬件和操作系统做了完美的抽象处理，使其不再受特定宿主机或环境的限制。
  * *逻辑脉络*：使用 Docker 分发的无状态应用不仅便于在数据中心内横向扩展，还能轻易跨越多个公有云平台（如 AWS、Google Cloud、Azure 等），实现「一次编写，到处运行」的终极目标。
* **后端拓展：混合云 / 多云**
  * **抽象一致**：同一镜像在自建机房、AWS、GCP 行为相同，迁移成本主要在编排与网络存储配置，而非改代码。
  * **容灾**：多区域 Registry 镜像复制 + K8s 多集群 / 多 AZ Deployment，故障时切换流量（DNS / 全局 LB）。
  * **成本**：无状态服务可配合 HPA 按负载扩缩；有状态仍依赖托管 DB（RDS 等），容器只跑应用层。

```
同一镜像 → Registry → 自建 K8s / EKS / GKE / AKS
         （换的是编排与 IaC，不是应用包）
```

## Docker Swarm

* **核心主旨与实用要点**
  * 介绍了 Docker 官方发布的原生集群管理工具 Swarm，它通过提供与单机 Docker 完全一致的 API 接口，将多个独立宿主机整合为一个统一的资源池。
* **核心知识点与逻辑拆解**
  * **架构定位**：Swarm 的形式既是集群的中央管理枢纽，又是运行在各个宿主机中的代理。它不负责实现复杂的应用监控或自愈，仅专注于基础的**集群资源管理功能**。
  * **部署与通信逻辑（三步工作流）**：
    1. **创建集群**：执行 `docker run --rm swarm create`，会向 Docker Hub 的发现服务请求并返回一个唯一的集群哈希值（Token）。
    2. **节点加入**：在每个计算节点上运行 `swarm join` 命令（如 `docker run -d swarm join --addr=<节点IP>:2375 token://<哈希值>`），将节点的 Docker 守护进程注册到集群中。
    3. **启动管理器**：在管理节点上执行 `swarm manage`，监听特定端口（如 9999 或 2375），收集代理节点信息并对外提供统一控制端点。
  * **易错细节与警告**：
    * *环境配置切换*：启动 Swarm 管理器后，必须将本机的环境变量 `DOCKER_HOST` 修改为管理器监听的 IP 和端口。如果不做切换，执行的 `docker ps` 等命令依然只作用于单机，无法查看集群全局的容器状态。
    * *依赖盲区*：Swarm 的 `create` 命令默认强依赖于公网的 `discovery.hub.docker.com`。在生产内网环境中，必须替换为本地高可用的键值存储系统（如 **etcd** 或 **Consul**）以防止单点故障。
* **后端拓展：Swarm Mode 演进**
  * **早期 Swarm**：独立 `swarm` 镜像 + 外部 discovery（Hub / etcd），本书描述的是这一代。
  * **Swarm Mode（Docker 1.12+）**：`docker swarm init` / `join`，内置 Raft 状态存储，无需外部 discovery；`docker service` 声明服务。仍比 K8s 功能薄，新项目不选。
  * **对照 K8s**：`DOCKER_HOST` 切到 Swarm manager ≈ `kubectl` 连 apiserver；生产用 kubeconfig。

```bash
# 早期 Swarm（书中，历史参考）
docker run --rm swarm create
# → token://<hash>

docker run -d swarm join --addr=<NODE_IP>:2375 token://<hash>
docker run -d -p 2375:2375 swarm manage token://<hash>

export DOCKER_HOST=tcp://<MANAGER_IP>:2375
docker ps   # 此时才是集群视图
```

```bash
# 现代 Swarm Mode（了解即可）
docker swarm init
docker swarm join --token <token> <manager>:2377
docker service create --replicas 3 -p 80:80 nginx
```

| 时代 | 发现机制 | 现状 |
|------|----------|------|
| 早期 Swarm | Docker Hub / etcd | 已过时 |
| Swarm Mode | 内置 Raft | 小集群可用，生态弱 |
| Kubernetes | etcd + 丰富 API | **后端默认** |

## Centurion

* **核心主旨与实用要点**
  * 介绍了由 New Relic 开发的批量部署工具 Centurion，它不同于把网络看作一台大电脑的分布式调度器，而是专注于通过简单的配置，将应用可靠地**滚动部署**到已知的一组宿主机上。
* **核心知识点与执行机制**
  * **技术栈与安装**：Centurion 是基于 Ruby 语言编写的，需通过 `gem install centurion` 安装。其核心依赖于 `Rakefile` 形式的配置文件来定义部署逻辑。
  * **配置参数（案例要点）**：
    * 在配置文件中，需明确指定环境变量（`env_vars`）、端口映射（`host_port` 和 `container_port`）以及目标宿主机列表（如 `host 'docker1'`, `host 'docker2'`）。
  * **部署动作拆解（因果逻辑）**：
    * 执行 `centurion -p <项目> -e <环境> -a rolling_deploy` 后，工具会严格遵循以下迭代步骤：
      1. 并发从注册处拉取（Pulling）最新映像到所有目标节点。
      2. 在第一台宿主机上停止（Stopping）旧容器。
      3. 创建（Creating）并启动（Starting）新容器。
      4. 验证新容器健康状态（等待端口启动）。
      5. 清理（Removing）旧容器，接着对下一台宿主机重复此过程。
    * *因果结论*：这种极其稳健的**滚动更新（Rolling Update）**机制，确保了部署过程中集群始终有健康节点提供服务，且如果某台部署失败，可以立即停止，不会造成全局宕机。
* **后端拓展：K8s Deployment 滚动更新**
  * Centurion 的「逐台换容器」≈ K8s `Deployment` 的 `RollingUpdate` 策略。
  * `maxUnavailable`：更新时最多多少 Pod 不可用（类似一次只停一台）。
  * `maxSurge`：最多多出多少新 Pod（可先起新再删旧，实现零停机）。

```yaml
# K8s Deployment 滚动更新（Centurion 的现代替代）
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
      maxSurge: 1
```

```
Centurion:  host1 换完 → host2 换完 → ...
K8s:        按 ReplicaSet 逐步替换 Pod，由控制器保证期望副本数
```

## Amazon EC2 Container Service (ECS)

* **核心主旨与实用要点**
  * 详解了如何在主流公有云 AWS 上利用其托管的 ECS 服务构建企业级容器集群，重点解析了 ECS 特有的权限管控与任务定义模型。
* **关键定义与组件拆解**
  * **IAM 角色（安全基石）**：在启动任何 ECS 实例前，必须配置 AWS 的身份和访问管理（IAM），赋予实例 `ecs:CreateCluster`、`ecs:RegisterContainerInstance` 等 API 访问权限，否则代理节点将无权加入集群。
  * **ECS 集群（Cluster）**：逻辑上的资源池。通过 AWS CLI 命令 `aws ecs create-cluster --cluster-name testing` 创建。
  * **容器实例（Container Instance）**：运行着特殊 `ecs-agent` 容器的普通 EC2 虚拟机。*关键细节*：代理容器启动时，必须通过环境变量 `ECS_CLUSTER=testing` 将其强行绑定到指定的集群，否则会默认加入名为 `default` 的集群中。
  * **任务定义（Task Definition）**：
    * 类似 `docker-compose.yml` 的作用，是一段 **JSON 格式的代码**，用于声明式地描述应用运行所需的所有属性。
    * 包含参数：`image`（映像地址）、`memory`（内存限制）、`cpu`（算力限制）、`portMappings`（端口映射）以及 `environment`（注入的环境变量）。
* **部署流程与状态校验逻辑**
  * *流程*：定义 JSON -> 注册任务（`register-task-definition`） -> 运行任务（`run-task --cluster testing --task-definition <名称>`）。
  * *状态校验（易错细节）*：执行 `run-task` 命令后，返回的 JSON 状态 `lastStatus` 往往是 **PENDING（等待中）**，这代表调度器刚接收到请求。必须随后使用 `describe-tasks` 命令轮询，直到状态转变为 **RUNNING（运行中）**，才代表容器真正在 EC2 节点上成功启动并提供服务。
* **后端拓展：ECS vs Fargate vs EKS**
  * **ECS on EC2**（本书）：自管 EC2 + `ecs-agent`，你要管节点补丁与容量。
  * **Fargate**：无 EC2 感知，按 Task 付费；Task Definition 仍用，但不注册 Container Instance。
  * **EKS**：AWS 托管的 **Kubernetes**；后端若已学 K8s，云上优先 EKS 而非 ECS Task JSON。

```bash
aws ecs create-cluster --cluster-name testing
aws ecs register-task-definition --cli-input-json file://task-def.json
aws ecs run-task --cluster testing --task-definition myapp:1
aws ecs describe-tasks --cluster testing --tasks <task-arn>
# 轮询直到 lastStatus == RUNNING
```

```json
// task-def.json 片段（声明式，类似 Compose）
{
  "family": "myapp",
  "containerDefinitions": [{
    "name": "web",
    "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/myapp:1.0",
    "memory": 512,
    "cpu": 256,
    "portMappings": [{ "containerPort": 8080, "hostPort": 8080 }],
    "environment": [{ "name": "ENV", "value": "prod" }]
  }]
}
```

| AWS 方案 | 你管什么 | 后端选型 |
|----------|----------|----------|
| ECS + EC2 | EC2 + agent + Task JSON | 遗留 / 简单任务 |
| Fargate | 只管 Task Definition | 无 K8s 时的 Serverless 容器 |
| EKS | K8s YAML / Helm | **与 K8s 技能栈一致** |

## 小结

* **核心主旨与重点结论**
  * 总结指出，无论是使用偏向命令式的滚动更新工具（Centurion），还是使用高度托管的声明式公有云服务（ECS），Docker 均发挥了其不可替代的作用。
  * 由于 Docker 对底层的 Linux 系统做了大量抽象处理，企业可以根据业务规模的变化，在自建数据中心和各种云平台之间极其顺畅地迁移应用，而不必重新打包或修改代码架构。
* **后端拓展：技术演进脉络**
  * **单机**：`docker run` / Compose（开发）
  * **多机命令式**：Centurion 滚动部署（已知主机列表）
  * **多机调度**：Swarm / Mesos（把集群当一台机）
  * **声明式平台**：**Kubernetes**（期望状态 + 控制器调和）+ 云托管控制面（EKS/GKE/AKS）
  * **CI/CD**：构建镜像 → Registry → GitOps / `kubectl apply` / Helm，取代手工 `rolling_deploy`

```
Docker 镜像（不变）
    ↓
Compose（本地）→ Centurion/Swarm（历史）→ K8s + 云托管（现状）
```

## 本章速记

| 概念 | 一句话 |
|------|--------|
| 规模化价值 | 镜像抽象硬件/OS，便于横向扩展与多云迁移 |
| 早期 Swarm | token 发现 → join → manage；**必须设 `DOCKER_HOST`** |
| Swarm 内网 | 不用 Hub discovery，用 etcd/Consul |
| Swarm Mode | `docker swarm init`，内置 Raft（与书中早期版不同） |
| Centurion | Ruby + Rakefile，**逐台滚动部署** |
| K8s 对照 | Deployment 的 `maxSurge` / `maxUnavailable` |
| ECS 组件 | Cluster / Container Instance / Task Definition |
| `run-task` | 先看 PENDING，**describe-tasks 等到 RUNNING** |
| Fargate | 免管 EC2 的 ECS Task |
| 后端结论 | **跳过深挖本章工具，用 K8s + 托管集群** |
