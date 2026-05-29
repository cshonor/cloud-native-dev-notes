# 第11章 高级话题 (Advanced Topics)

> **版次说明**：中译/第一版常称「第10章 高级话题」，第二版目录为 **Ch 11**。  
> **后端学习提示**：本章 **跳过深挖**——存储驱动、cgroup/namespace 细节属运维/内核向。后端需记住：**overlay2、非 root、不用 `--privileged`、Docker API 不裸奔**；集群级安全见 K8s PSA / SecComp / NetworkPolicy。

## 可更换的后端

* **核心主旨与实用要点**
  * 本节深入探讨了 Docker 底层架构的灵活性。Docker 作为一个静态编译的 Go 语言二进制文件，其架构设计中包含了多个可配置的「后端」（Backends），允许用户根据宿主机系统的特性（如 Linux 发行版差异）自由更换**执行驱动（Execution Driver）**和**存储后端（Storage Driver）**。
* **核心知识点与底层机制**
  * **执行驱动（Execution Driver）**：
    * *技术沿革*：在 Docker 0.9 版本之前，默认且唯一支持的底层容器引擎是 **LXC (Linux Containers)**。
    * *架构演进*：由于 LXC 依赖特定的系统配置且经常发生破坏性更新，Docker 开发了原生的 **libcontainer** 库（即 `native` 驱动）并将其作为默认选项。
    * *易错细节*：使用 `native` 驱动时，通过 `docker run --lxc-conf` 传递的 LXC 专属配置将会失效。如果业务强依赖 LXC 的特定配置，必须在启动守护进程时通过 `docker -d -e lxc` 强制降级切换回 LXC 驱动。
  * **存储后端（Storage Backends）**：
    * 用于实现 Docker 镜像分层和**写时复制（CoW）**机制的核心驱动。
    * **AUFS**：Docker 最早支持的后端，联合文件系统，性能极高。*缺点*：未被纳入 Linux 官方主线内核，通常只有 Ubuntu 默认支持。
    * **Device Mapper**：主要为弥补 Red Hat 系系统不支持 AUFS 而开发。基于块级别（Block-level）的 LVM 和精简置备（Thin Provisioning）技术。
    * **btrfs**：原生的写时复制文件系统。性能优秀，但要求底层的磁盘必须格式化为 btrfs 格式。
    * **vfs**：最简单但**最慢**的后端。它不支持真正的写时复制，而是每次都执行完整的目录拷贝。通常仅用于测试或无其他驱动可用的保底情况。
    * **OverlayFS**：被视为未来的标准。它并入了 Linux 3.18 主线内核，在速度和内存利用率上优于 AUFS，是现代 Docker 环境的推荐选择。
* **后端拓展：overlay2 与 inode 耗尽**
  * 现代 Docker / containerd 默认 **overlay2**，AUFS / devicemapper 已淘汰。`docker info` 查看 `Storage Driver`。
  * **inode 耗尽**：大量小文件层叠时，`df -i` 满但 `df -h` 有余；症状是 pull/build 失败。处理：清理 dangling 镜像/层、`docker system prune`、增大文件系统 inode，或拆镜像减少层数。

```bash
docker info | grep -i "storage driver"
docker system df
docker system prune -a   # 慎用：删未用镜像
```

| 存储驱动 | 现状 |
|----------|------|
| overlay2 | ✅ 默认推荐 |
| aufs / devicemapper | 历史，勿新项目 |
| vfs | 仅测试/兜底 |

## 容器详解

* **核心主旨与实用要点**
  * 剥开「容器」这个抽象概念的外衣，从 Linux 内核层面详细拆解构成容器隔离性的两大核心基石：**控制组（cgroups）**与**命名空间（Namespaces）**。
* **控制组（cgroups）深度剖析**
  * *功能定义*：cgroups 用于设定进程及其子进程对硬件资源（CPU、内存、磁盘 I/O）的**使用限额**。
  * *底层交互机制*：Docker 在启动容器时，会在宿主机的 `/sys/fs/cgroup/` 虚拟文件系统下为该容器创建专属的层级目录。
  * *动态调试（操作技巧）*：管理员可以直接进入 `/sys/fs/cgroup/cpu/docker/<完整容器ID>/` 目录，通过修改 `cpu.shares` 文件的数值，实现对运行中容器 CPU 权重的**热更新（无需重启容器）**。
* **六大命名空间（Namespaces）拆解**
  * **挂载命名空间（Mount）**：实现文件系统的隔离，类似于强化版的 `chroot`。容器内的进程只能看到属于自己的根目录 `/`。
  * **UTS 命名空间**：隔离主机名和域名（Hostname/Domain name），使容器能拥有独立于宿主机的标识。
  * **IPC 命名空间**：隔离进程间通信（如 System V 消息队列和共享内存），防止容器内进程干涉宿主机或其他容器的通信。
  * **PID 命名空间（核心逻辑）**：隔离进程号池。*因果关系*：因为具有独立的 PID 树，所以容器内部的主应用会自认为是 `PID 1`（系统的 init 进程），而在宿主机上查看时，它只是一个普通的随机 PID（如 `PID 46049`）。
  * **网络命名空间（Network）**：隔离网络设备、IP 地址和端口。每个容器拥有完全独立的虚拟网卡。
  * **用户命名空间（User）**：允许实现宿主机与容器之间的 **UID/GID 映射**。例如，容器内的 `root` 用户（UID 0）可以被映射为宿主机上的一个无特权普通用户，极大提升安全性。
* **后端拓展：unshare 与 K8s 资源**
  * `unshare` 可手动创建 namespace 沙盒，帮助理解隔离原理（实验用）。
  * 后端日常用 **`docker run --cpus` / `--memory`** 或 K8s `resources.requests/limits`，不必手改 cgroup 文件。

```bash
# 查看容器 cgroup 路径（cgroup v1 示例，路径因版本而异）
docker inspect --format '{{.Id}}' myapp
# ls /sys/fs/cgroup/cpu/docker/<id>/cpu.shares

docker run --cpus=1.5 --memory=512m myapp
```

```bash
# 手动体验 namespace（理解用）
sudo unshare --fork --mount --uts --ipc --pid --net --user /bin/bash
```

| Namespace | 隔离什么 | 后端关联 |
|-----------|----------|----------|
| Mount | 文件系统视图 | 镜像层 + Volume |
| PID | 进程号 | 容器内 PID 1 |
| Network | 网卡/IP/端口 | `-p` / K8s Service |
| User | UID/GID | `runAsNonRoot` |
| cgroups | CPU/内存/IO | limits / HPA 之外的基础配额 |

## 安全性

* **核心主旨与实用要点**
  * 直面 Docker 容器的系统安全挑战，强调容器不同于虚拟机的「有限隔离」特性，并提供应对权限越界和守护进程暴露的防范指南。
* **核心安全风险与防范（重点结论）**
  * **内核共享的本质脆弱性**：虚拟机通过 Hypervisor 实现硬件级隔离，而所有容器共享宿主机的操作系统内核。一旦 Linux 内核存在越权漏洞，所有容器都将面临被击穿的风险。
  * **UID 0 (Root) 陷阱（严重警告）**：
    * 默认情况下，容器内的进程以 `root` 用户运行。
    * *因果推导*：如果用户未配置用户命名空间映射，且容器内的进程被攻破，攻击者实际上就掌握了对宿主机具有极大破坏潜力的 `root` 进程。书中的案例表明，即使在容器内执行 `rmmod floppy`（卸载内核模块），如果权限控制不当，也会直接影响宿主机内核。
  * **特权模式与能力（Capabilities）管控**：
    * *危险操作*：使用 `--privileged=true` 启动容器会赋予其近乎所有的内核访问权限，这是极其危险的。
    * *最佳实践*：应坚持「最小权限原则」，使用 Linux Capabilities 机制进行细粒度授权。例如，若只需修改网络配置，应使用 `--cap-add=NET_ADMIN` 而非直接开启完全特权模式。
  * **强制访问控制（MAC - SELinux/AppArmor）**：
    * Docker 深度集成了操作系统的安全策略。Red Hat 系使用 **SELinux**，Ubuntu 系使用 **AppArmor**。这些系统能够在内核级别锁定即使是 `root` 用户也无法访问的敏感路径（如 `/proc` 和 `/sys`），是防御容器逃逸的关键防线。
  * **守护进程的网络安全**：
    * Docker 守护进程（Daemon）必须以 `root` 权限运行。如果将其监听端口（如 `2375`）无保护地暴露在公网上，任何连接者都能轻易获取宿主机的最高权限。
    * *解决方案*：必须开启并配置 **TLS 双向证书认证（Mutual TLS）**，确保只有持有有效客户端证书的请求才能向守护进程下达命令。
* **后端拓展：K8s 集群级安全**
  * **Pod Security Admission (PSA)**：`restricted` / `baseline` 禁止特权容器、hostNetwork 等。
  * **SecComp**：限制可用 syscall；默认 profile 已较严，可自定义。
  * **Dockerfile**：`USER nonroot`；不在镜像里塞 secrets。

```bash
# 最小权限示例
docker run --read-only --cap-drop=ALL myapp
docker run --cap-add=NET_BIND_SERVICE myapp   # 仅绑定低端口等

# 危险：勿在生产使用
docker run --privileged myapp
```

```yaml
# K8s Pod 安全基线片段
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
```

| 风险 | 防范 |
|------|------|
| 容器内 root | `USER` 非 root / `runAsNonRoot` |
| `--privileged` | 禁止；用 `--cap-add` 按需 |
| 2375 裸 API | TLS + 防火墙；生产用 K8s API |
| 内核漏洞 | 及时打补丁；多租户考虑 VM 隔离 |

## 网络

* **核心主旨与实用要点**
  * 解析 Docker 默认网桥模式的网络拓扑结构，以及如何通过牺牲网络隔离来换取极致网络性能的特殊模式。
* **网络拓扑与流量转发逻辑**
  * **标准桥接模型（网桥模式）**：
    * *内部链路*：容器内的 `eth0` 网卡通过一对虚拟以太网线缆（**veth pair**）连接到宿主机的 `docker0` 虚拟网桥上（处于 `172.16.x.x` 子网）。
    * *外部暴露（因果机制）*：当通过 `-p` 暴露端口时，Docker 会启动一个用户态的 **`docker-proxy`** 进程，并在系统的 `iptables` 中注入 NAT 规则。外部入站流量首先命中宿主机网卡 -> 转发给 `docker-proxy` -> 穿越 `docker0` 网桥 -> 最终抵达容器内部。
  * **Host 网络模式（易错细节与性能权衡）**：
    * *指令*：启动时加入 `--net=host` 参数。
    * *现象与本质*：容器将完全丧失网络命名空间的隔离，直接共享宿主机的网络栈。容器内执行 `ifconfig` 或查看 `/etc/hosts`，看到的将是宿主机的真实网卡和配置。
    * *应用场景*：这种模式绕过了 `veth` 对和 NAT 转换的所有开销，对于极其渴求网络吞吐量和极低延迟的应用（如高频交易服务）是最佳选择。但代价是**端口冲突风险**（容器占用的端口即宿主机的端口）以及**安全隔离的丧失**。
* **后端拓展：CNM 与跨主机网络**
  * **CNM**：Docker 网络模型——Network / Endpoint / Sandbox；`docker network create` 自定义 bridge。
  * **跨主机**：单机 bridge 仅限一机；集群用 **Overlay**（Swarm overlay）、**Flannel**（VXLAN）、**Calico**（BGP/IP 路由）。K8s 默认 CNI 插件（Calico/Cilium/Flannel）承担同类职责。
  * 后端默认：**bridge + Compose 服务名 DNS**（本地）；**K8s Service + Ingress**（生产）。

```bash
docker network ls
docker network inspect bridge
docker run -d --name web -p 8080:80 nginx          # bridge + NAT
docker run -d --net=host nginx                      # 共享宿主机网络栈
```

```
bridge 模式:
  外界:host:8080 → iptables/docker-proxy → docker0 → veth → 容器 eth0

host 模式:
  容器直接监听宿主机 :80（无隔离，端口冲突）
```

| 模式 | 隔离 | 典型场景 |
|------|------|----------|
| bridge（默认） | ✅ | 通用开发/部署 |
| host | ❌ | 极致性能、DaemonSet 类 |
| overlay（多机） | ✅ 跨节点 | Swarm/K8s CNI |

## 本章速记

| 概念 | 一句话 |
|------|--------|
| 执行驱动 | LXC → libcontainer（native）；今由 runc/containerd |
| 存储驱动 | **overlay2** 主流；AUFS/devicemapper 历史 |
| inode 耗尽 | 小文件过多；prune 镜像 / 扩 inode |
| cgroups | CPU/内存限额；`--cpus` `--memory` |
| Namespaces | Mount/PID/Net/UTS/IPC/User 六维隔离 |
| 容器 ≠ VM | 共享内核，内核漏洞影响全机 |
| root 陷阱 | Dockerfile `USER` + 不用默认 root |
| `--privileged` | 近 root 权限，**生产禁用** |
| Capabilities | `--cap-drop=ALL` 再按需 `cap-add` |
| 2375 API | 必须 TLS；勿公网暴露 |
| bridge | veth + docker0 + NAT/docker-proxy |
| `--net=host` | 无网络隔离，高性能高风险 |
| 跨主机 | K8s CNI（Calico/Flannel 等） |
