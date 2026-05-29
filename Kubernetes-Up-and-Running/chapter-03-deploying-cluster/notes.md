# 第三章：部署Kubernetes集群 (Chapter 3: Deploying a Kubernetes Cluster)

## 在公有云提供商上安装Kubernetes (Installing Kubernetes on a Public Cloud Provider)

* **核心主旨与逻辑**：
  * 对于初学者或无需自行维护底层硬件的团队，高度推荐使用公有云提供的**托管Kubernetes服务（Kubernetes-as-a-Service）**。将管理控制平面的复杂性交给云厂商，不仅能快速启动，且通常管理节点服务是免费的。
* **三大主流云厂商的部署方案与命令**：
  1. **Google Kubernetes Engine (GKE)**：
     * 需要GCP账号并开启计费，依赖 `gcloud` 命令行工具。
     * 核心执行逻辑：设置可用区 `gcloud config set compute/zone us-west1-a` → 创建集群 `gcloud container clusters create kuar-cluster` → 获取凭证 `gcloud auth application-default login`。
  2. **Azure Kubernetes Service (AKS)**：
     * 推荐使用Azure门户内置的 **Azure Cloud Shell**（已预装 `az` 工具）。
     * 核心执行逻辑：创建资源组 `az group create` → 创建集群 `az aks create` → 获取凭证 `az aks get-credentials`。
  3. **Amazon Web Services (EKS)**：
     * 使用开源的命令行工具 **`eksctl`**。
     * 核心执行逻辑：`eksctl create cluster --name kuar-cluster`，该工具会自动处理基础配置并将上下文注入本地客户端。

> 💡 **后续拓展空间**：可在此处延伸对比GKE、AKS、EKS在底层网络模型（CNI）、节点自动伸缩（Cluster Autoscaler）机制及IAM权限集成方案上的技术实现差异。

---

## 使用minikube在本地安装Kubernetes (Installing Kubernetes Locally Using minikube)

* **核心定义与适用场景**：
  * **minikube** 是一个在本地笔记本/台式机上通过虚拟机（VM）运行**单节点集群（Single-node cluster）**的工具。
  * **适用场景**：本地开发、学习和实验。对于不想支付公有云资源费用的开发者是理想选择。
* **局限性与易错细节**：
  * **并非高可用**：由于仅在单节点的VM中运行，它无法提供分布式Kubernetes集群的可靠性（无故障转移能力）。
  * **云功能受限**：某些依赖云提供商原生集成的功能（如云盘持久化卷、LoadBalancer类型服务）在minikube中不可用或仅能以受限方式工作。
* **前置要求与操作生命周期**：
  * 依赖底层**Hypervisor（虚拟机管理器）**：Linux/macOS常用 `virtualbox`，Windows默认使用 `Hyper-V`。
  * 生命周期命令：`minikube start`（创建VM并配置kubectl）、`minikube stop`（停止VM）、`minikube delete`（彻底销毁集群）。

```bash
minikube start
kubectl get nodes
minikube stop
minikube delete
```

> 💡 **后续拓展空间**：可补充说明Docker Desktop内置的Kubernetes单机版实现机制，以及minikube与其他本地化工具（如MicroK8s、k3s）在资源开销上的对比。

---

## 在Docker中运行Kubernetes (Running Kubernetes in Docker)

* **核心机制与项目背景**：
  * 使用**Docker容器**来模拟多个Kubernetes节点，而不是使用庞大的虚拟机。
  * 代表性开源项目为 **`kind` (Kubernetes IN Docker)**。它极大地优化了启动速度，主要被Kubernetes的核心开发者用于快速测试集群。
* **操作流与命令要点**：
  * 创建集群：`kind create cluster --wait 5m`。
  * 导出配置并验证：`export KUBECONFIG="$(kind get kubeconfig-path)"`，然后执行 `kubectl cluster-info`。
  * 销毁集群：`kind delete cluster`。

```bash
kind create cluster --wait 5m
kubectl cluster-info
kind delete cluster
```

> 💡 **后续拓展空间**：深入探讨`kind`如何利用Docker-in-Docker (DinD) 技术模拟复杂的多节点网络拓扑，以及在CI/CD流水线中集成`kind`进行端到端(E2E)测试的最佳实践。

---

## 在树莓派上运行Kubernetes (Running Kubernetes on Raspberry Pi)

* **核心主旨**：
  * 为需要体验物理硬件拔插（如断电、断网）以验证Kubernetes自愈特性的用户，提供一种超低成本的**裸机（Bare metal）集群**方案。
  * 具体构建步骤与所需的软硬件配置清单被归纳在附录A中，主要依赖 **`kubeadm`** 工具进行集群的初始化和节点加入。

> 💡 **后续拓展空间**：可在此补充ARM架构下容器镜像（如multi-arch images）的构建原理，以及边缘计算场景中Kubernetes（如KubeEdge）的应用架构。

---

## Kubernetes客户端 (The Kubernetes Client)

* **核心定义**：
  * **`kubectl`** 是官方的命令行工具，负责向Kubernetes API发起交互请求，用于部署、管理各种对象（如Pods, ReplicaSets, Services），并可检查集群的整体健康状况。
* **检查集群状态 (Checking Cluster Status)**：
  * **版本兼容性逻辑**：`kubectl version` 会同时显示客户端工具版本和API服务器版本。工具的向后/向前兼容性要求两者之间的差异**保持在两个次要版本（Minor versions）以内**。
  * **组件健康检查**：通过 `kubectl get componentstatuses` 可验证核心控制平面组件是否健康，包括 **`scheduler`**（调度器）、**`controller-manager`**（控制器管理器）和 **`etcd-0`**（存储集群API对象状态的分布式键值库）。
* **列出工作节点及调度隔离逻辑 (Listing Kubernetes Worker Nodes)**：
  * 命令：`kubectl get nodes`，可查看所有节点的状态和运行时间。
  * **主节点与工作节点的隔离**：Kubernetes节点分为主节点（Master nodes，运行控制平面容器）和工作节点（Worker nodes，运行用户容器）。**调度器默认不会将用户的Pod调度到主节点上**，以确保用户负载不会破坏集群控制平面的整体运行。
  * **深度排查与资源边界**：通过 `kubectl describe nodes <node-name>` 可以查看节点的底层OS细节、分配的标签、底层压力状态（如 `DiskPressure`, `MemoryPressure`），以及每个Pod分配的**资源请求（Requests）与限制（Limits）**情况。

```bash
kubectl version
kubectl get componentstatuses   # 旧版集群；新版可用 get --raw 等替代
kubectl get nodes
kubectl describe node <node-name>
```

> 💡 **后续拓展空间**：可在此处引入`kubectl`的底层身份认证机制（kubeconfig配置文件解析）、Context上下文切换，以及API Server的RESTful API交互原理。

---

## 集群组件 (Cluster Components)

* **核心主旨与架构特性**：
  * Kubernetes的一个有趣设计是**「自托管」（Self-hosting）**：组成Kubernetes集群的许多核心组件，实际上是作为应用被部署在Kubernetes自身的集群内部。它们默认运行在 **`kube-system` 命名空间** 中。
* **关键组件拆解**：
  1. **Kubernetes Proxy (`kube-proxy`)**：
     * **作用**：负责将网络流量路由到Kubernetes集群内的负载均衡服务。
     * **调度要求**：必须在集群的**每一个节点**上运行，因此在许多集群中，它是通过 **`DaemonSet`** 对象来部署的。
  2. **Kubernetes DNS**：
     * **作用**：为集群中定义的服务提供内部域名命名和发现机制。
     * **演进与部署**：作为一个支持多副本的部署（Deployment）运行（如 `core-dns` 取代了旧版的 `kube-dns`），系统为其提供一个集群虚拟IP（如 `10.96.0.10`），并将该IP注入到每个容器的 `/etc/resolv.conf` 文件中以接管解析。
  3. **Kubernetes UI (Dashboard)**：
     * **作用**：提供图形化界面浏览集群资源。通常作为单一副本的Deployment部署以实现高可用和自动升级。
     * **访问安全**：不可直接暴露，应通过 `kubectl proxy` 建立安全的本地网络代理通道（如访问 `http://localhost:8001/...`）进行安全内网访问。

```bash
kubectl get pods -n kube-system
kubectl proxy   # 另开终端访问 Dashboard
```

> 💡 **后续拓展空间**：进一步解析`kube-proxy`的几种工作模式（iptables vs. IPVS）的性能差异，以及CoreDNS的内部插件链（Plugins）和存根域（Stub Domains）的配置机制。

---

## 总结 (Summary)

* **核心脉络归纳**：
  * 拥有一个实际运行的Kubernetes集群是后续一切操作的前置条件。无论是托管云方案、本地虚拟机还是Docker内模拟方案，其核心目标是提供一个API控制平面。
  * 通过掌握 `kubectl` 工具探索集群基础设施（Nodes、System Components），能够为后续全面掌握Kubernetes的高级API对象部署打下坚实的物理认知基础。

> 💡 **后续拓展空间**：作为本书实践操作的起点，直接引出下一章对 `kubectl` 更进阶命令（如应用声明式清单、执行命令及排障）的全方位教学。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| KaaS | GKE / AKS / EKS，托管控制平面，上手最快 |
| minikube | 本地 VM 单节点，学习用，非 HA |
| kind | Docker 内模拟多节点，启动快，适合 CI |
| kubeadm | 裸机/树莓派自建集群的标准工具 |
| kubectl | 官方 CLI，版本与 API Server 差 ≤2 个 minor |
| Master 隔离 | 默认不把用户 Pod 调度到主节点 |
| kube-system | 控制平面组件自托管在此命名空间 |
| kube-proxy | 每节点 Service 流量路由，常由 DaemonSet 部署 |
| CoreDNS | 集群内服务发现，IP 写入容器 resolv.conf |
