# Kubernetes Up & Running

《Kubernetes Up & Running》**第三版**（ISBN 9781098110192）学习笔记。

> **后端定位**：能把自己的服务安全、稳定、可发布地跑在 K8s 上；会写 YAML、会排简单故障、懂发布和伸缩。  
> **不做**：集群升级、etcd、网络插件维护、存储集群、节点故障处理。

---

## 章节对照表（原书 18 章）

| 章 | 原书目录 | 优先级 | 后端要学到什么程度 |
|----|----------|--------|-------------------|
| 01 | Introduction | ✅ **快速读** | K8s 解决什么问题：自动化部署、自愈、弹性、服务发现 |
| 02 | Creating and Running Containers | ✅ **必看** | Dockerfile、镜像仓库（复习 Docker）；cgroup/namespace 了解即可 |
| 03 | Deploying a Kubernetes Cluster | ✅ **重点** | minikube / kind 本地集群；略过云上 HA master 部署 |
| 04 | Common kubectl Commands | ✅ **全章吃透** ⭐ | get/describe/logs/exec/apply/delete、namespace、context、标签选择器 |
| 05 | Pods | ✅ **必学** ⭐ | Pod 结构、多容器、生命周期、**liveness/readiness 探针**、requests/limits |
| 06 | Labels and Annotations | ✅ **必学** | label、selector、annotation，服务筛选和发布全靠它 |
| 07 | Service Discovery | ✅ **必学** ⭐ | ClusterIP / NodePort / LoadBalancer、DNS（`svc.ns.svc.cluster.local`） |
| 08 | HTTP Load Balancing with Ingress | 🔄 **选学** | 域名路由、路径规则、SSL；配合 Nginx 书深入 |
| 09 | ReplicaSets | 🔄 **理解** | 副本数、自愈原理；日常用 Deployment 即可 |
| 10 | Deployments | ✅ **精读+实操** ⭐⭐⭐ | 滚动更新、回滚、扩缩容；**90% 后端服务靠它** |
| 11 | DaemonSets | 🔄 **了解** | 每节点跑一个 Pod（日志/监控 agent），知道用途即可 |
| 12 | Jobs | ✅ **必学** | 一次性任务、**CronJob 定时任务**（批处理很常见） |
| 13 | ConfigMaps and Secrets | ✅ **重中之重** ⭐⭐ | 配置与镜像解耦、敏感信息注入、挂载与环境变量 |
| 14 | Role-Based Access Control | 🔄 **浅看** | 懂 RBAC 概念，知道怎么申请权限即可 |
| 15 | Integrating Storage Solutions | ✅ **够用** | Volume、emptyDir、PVC/PV；会挂存储，不管 StorageClass 运维 |
| 16 | Extending Kubernetes | ❌ **跳过** | CRD、Operator 扩展，非后端必修 |
| 17 | Deploying Real-World Applications | ✅ **跟着做一遍** ⭐⭐⭐ | 完整链路：镜像 → Deployment → Service → Ingress → Config/Secret → 存储 |
| 18 | Organizing Your Application | 🔄 **选学** | 多环境、命名空间组织，按需阅读 |

---

## 后端极简学习路线（推荐顺序）

```
Docker 过关后 → 按下面顺序学，不必严格按书页码线性读
```

| 顺序 | 章节 | 核心产出 |
|------|------|----------|
| 1 | Ch 01～02 | 理解 K8s 价值，确认会打包镜像 |
| 2 | Ch 03 | 本地 minikube/kind 可玩 |
| 3 | Ch 04 | kubectl 熟练，不查手册能操作 |
| 4 | Ch 05 | 会配探针和资源限制 |
| 5 | Ch 06 | 会打 label、写 selector |
| 6 | Ch 07 | 服务互访、DNS 能讲清楚 |
| 7 | Ch 13 | ConfigMap + Secret 会写会挂 |
| 8 | Ch 10 | Deployment 发布/回滚/扩缩容 |
| 9 | Ch 12 | Job / CronJob 跑批任务 |
| 10 | Ch 15 | PVC 给有状态服务挂盘 |
| 11 | Ch 08 | Ingress 域名暴露（选学） |
| 12 | Ch 17 | **完整应用部署实操** |

> Ch 09 ReplicaSet、Ch 11 DaemonSet、Ch 14 RBAC 穿插在阅读 Deployment 时顺带理解即可。

---

## 每章实操清单

| 章 | 动手任务 |
|----|----------|
| 03 | `minikube start` 或 `kind create cluster`，`kubectl get nodes` 成功 |
| 04 | 创建 namespace；`kubectl get/describe/logs/exec` 练熟 |
| 05 | 写一个带 liveness + readiness 探针的 Pod YAML 并 apply |
| 06 | 给 Deployment 打 `app`/`env` label，用 `-l` 筛选资源 |
| 07 | 部署 Service，在集群内 `curl my-svc` 或 DNS 解析验证 |
| 08 | 安装 Ingress Controller，配一条域名/路径规则 |
| 10 | 滚动更新镜像 tag → `kubectl rollout status` → `rollout undo` 回滚 |
| 12 | 跑一个 Job 完成退出；写一个 CronJob 定时任务 |
| 13 | ConfigMap 注入环境变量；Secret 挂载文件或 env |
| 15 | 创建 PVC 并挂载到 Pod/Deployment |
| 17 | 按书例部署完整应用（前后端+数据库），走通全流程 |

---

## YAML 模板（`supplement/`）

| 文件 | 用途 |
|------|------|
| `deployment.yaml` | Deployment + 探针 + 资源限制 + 引用 Config/Secret |
| `service.yaml` | ClusterIP / NodePort 示例 |
| `configmap-secret.yaml` | ConfigMap + Secret |
| `ingress.yaml` | Ingress 域名路由 |
| `job-cronjob.yaml` | Job + CronJob |
| `pvc.yaml` | PersistentVolumeClaim + 挂载注释 |

---

## 学完后端 K8s 能力自检

- [ ] 独立写 Deployment + Service + ConfigMap/Secret YAML，把服务跑起来
- [ ] 会配健康检查、资源配额、滚动发布、回滚
- [ ] 用 kubectl 看状态、查日志、进容器、debug 启动/网络问题
- [ ] 懂服务发现、集群内 DNS、Ingress 域名暴露
- [ ] 会用 PVC 给有状态服务挂存储
- [ ] **不做**集群升级、etcd 维护、网络/存储插件运维

---

## 学习进度

| 章节文件夹 | 状态 |
|------------|------|
| chapter-01-introduction | ✅ 已完成 |
| chapter-02-containers | ✅ 已完成 |
| chapter-03-deploying-cluster | ✅ 已完成 |
| chapter-04-kubectl | ⬜ 未开始 |
| chapter-05-pods | ✅ 已完成 |
| chapter-06-labels-annotations | ⬜ 未开始 |
| chapter-07-service-discovery | ⬜ 未开始 |
| chapter-08-ingress | ⬜ 未开始 |
| chapter-09-replicasets | ⬜ 未开始 |
| chapter-10-deployments | ⬜ 未开始 |
| chapter-11-daemonsets | ⬜ 未开始 |
| chapter-12-jobs | ⬜ 未开始 |
| chapter-13-configmaps-secrets | ⬜ 未开始 |
| chapter-14-rbac | ⬜ 未开始 |
| chapter-15-storage | ⬜ 未开始 |
| chapter-16-extending-k8s | ⏭️ 跳过 |
| chapter-17-real-world-apps | ⬜ 未开始 |
| chapter-18-organizing-app | ⬜ 未开始 |

> 状态：⬜ 未开始 / 🔄 进行中 / ✅ 已完成 / ⏭️ 跳过
