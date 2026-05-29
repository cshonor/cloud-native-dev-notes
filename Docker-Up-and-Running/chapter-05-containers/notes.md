# 第5章 使用 Docker 容器 (Working with Docker Containers)

> **后端学习提示**：本章**必学**。重点掌握 `docker run`、`-p` 端口映射、`-v` 数据卷、`--restart`、资源限制（浅看）；与 K8s Pod 的端口、Volume、探针概念直接对应。

## 容器是什么？

* **核心主旨与实用要点**
  * 辨析容器与传统虚拟机的底层技术差异，明确容器作为「轻量级自成一体执行环境」的本质，并梳理容器技术的历史演变脉络。
* **核心知识点与关键定义**
  * **传统虚拟机（VMware/Xen）机制**：使用监控程序（hypervisor），在不同的内存空间里运行各自独立的客户机内核，模拟完整硬件交互。
  * **容器机制（重点结论）**：所有容器**共用宿主机的同一个内核**，它们之间的隔离完全在这个内核中实现（通过 cgroups 和 namespace）。
  * **libcontainer 定义**：容器是自成一体的执行环境，所有容器共用宿主机内核，且系统中的容器之间是相互隔离的（但不强制要求隔离所有方面）。
  * **容器的历史演变（逻辑脉络）**：
    * *1979年*：UNIX 引入 `chroot` 系统调用（最早的隔离形式）。
    * *2000年*：FreeBSD 发布 `jail` 命令，增强了网络和底层系统的限制。
    * *2004年*：Sun 发布 Solaris Zones（早期商业实现）。
    * *2008年*：Linux 内核 2.6.24 推出 **LXC (Linux Containers)**。
    * *2013年*：Docker 诞生，将繁琐的 LXC 操作标准化、简单化；随后 Google 开源 lmctfy，CoreOS 发布 Rocket，容器技术百花齐放。
* **前后因果与逻辑关联**
  * *因果推导*：因为容器共用同一个内核且少了硬件模拟层，所以运行在容器里的进程只需要极少的额外内核交互，导致其性能开销极低，启动速度极快。
* **预留拓展补充空间**
  * > *[此处可补充：OCI (Open Container Initiative) 容器运行时标准的建立背景，以及 runC 与 libcontainer 的关系演进]*

```
VM：应用 → 客户机 OS → Hypervisor → 宿主机
容器：应用 → 容器运行时 → 共享宿主机内核
```

## 创建容器

* **核心主旨与实用要点**
  * 详解 `docker run` 和 `docker create` 命令中众多高级标志（flag）的用法，涵盖网络、存储、名称、资源配额及权限限制等核心配置。
* **详细知识点拆解与参数解析**
  * **基本配置（名称与标注）**：
    * `--name`：为容器指定唯一、有意义的名称（替代默认的随机形容词+名人名）。**易错细节**：宿主机内容器名必须唯一，重复创建同名容器会报错。
    * `-l` / `--label`：为容器添加键值对形式的元数据标签（如 `deployer=Ahmed`），可通过 `docker ps -f label=...` 过滤查询。
  * **网络与环境配置（主机名、DNS、MAC）**：
    * **主机名**：默认情况下，Docker 使用容器的 ID 作为主机名，并将宿主机的 `/etc/hostname` 等文件通过**绑定挂载（bind mount）**连接到容器内。可通过 `-h` 或 `--hostname` 显式更改。
    * **DNS**：可通过 `--dns` 和 `--dns-search` 覆盖默认挂载的 `/etc/resolv.conf` 配置，指定自定义的域名解析服务器。
    * **MAC 地址**：部分底层网络环境需要授权特定 MAC 才能通信，可通过 `--mac-address` 显式指定。
  * **存储卷（Volumes）**：
    * 使用 `-v` 标志（如 `-v /mnt/data:/data`）将宿主机的目录直接挂载进容器。
    * **安全强化（重点结论）**：结合 `--read-only=true` 参数，可将容器的根文件系统设为**只读**，仅允许数据写入挂载的 Volume 中，大幅提升安全性。
  * **资源配额（Resource Quotas - cgroups）**：
    * **CPU 份额**：使用 `-c` 或 `--cpu-shares` 分配相对的 CPU 权重（默认 1024 份）。**逻辑重点**：这是一种**弹性限制**，只有当多个容器竞争 CPU 时，权重才起作用。若需绝对绑定核心，需使用 `--cpuset-cpus`（如 `0,1,2`）。
    * **内存（Memory）**：使用 `-m` 指定最大 RAM 占用（如 `-m 512m`）。通过 `--memory-swap` 限制内存+交换区总大小（设为 `-1` 时完全禁用 swap）。
    * **易错细节/警告**：如果容器内存超出配额，会触发 Linux 内核的 **OOM (Out of Memory)** 机制将其杀死。此外，宿主机内核必须支持 swap 限制，否则 `--memory-swap` 无效。
  * **用户权限（ulimit）**：
    * 通过 `--ulimit` 覆盖操作系统的软/硬限制（如限制最大打开文件数 `--ulimit nofile=50:150`），防止异常容器耗尽宿主机全局资源。可以在守护进程级别通过 `--default-ulimit` 设定全局默认值。
* **预留拓展补充空间**
  * > *[此处可补充：Docker 存储卷的进阶用法（如命名卷 Named Volumes 与挂载绑定 Bind Mounts 的详细差异及使用场景分析）]*

```bash
docker run -d \
  --name myapp \
  -p 8080:8080 \
  -v app-data:/data \
  --read-only \
  -m 512m \
  --cpus 1.0 \
  --restart unless-stopped \
  myapp:1.0
```

| 挂载类型 | 语法 | 场景 |
|----------|------|------|
| Bind mount | `-v /host/path:/container/path` | 开发时挂载代码 |
| Named volume | `-v vol-name:/data` | 生产持久化数据 |

## 启动容器

* **核心主旨与实用要点**
  * 介绍如何分离「创建」与「启动」步骤，通过 `docker start` 激活处于停止状态的容器实例。
* **逻辑脉络与执行机制**
  * **命令逻辑**：`docker run` 本质上是 `docker create` 加上 `docker start` 的组合。在某些复杂部署场景下（如仅预分配资源），可先执行 `docker create` 获得容器 ID，后续再通过 `docker start <ID>` 正式启动。
* **预留拓展补充空间**
  * > *[此处可补充：结合 `docker create` 的场景案例，例如在 Kubernetes 早期对接 Docker 运行时（Dockershim）时是如何分步创建 Infra 容器和业务容器的]*

```bash
docker create --name myapp -p 8080:8080 myapp:1.0
docker start myapp
```

## 自动重启容器

* **核心主旨与实用要点**
  * 利用 Docker 内置的重启策略保证服务的高可用性，防止因瞬态错误导致应用长时间宕机。
* **参数要点与机制拆解**
  * **--restart 策略**：
    * `no`（默认）：容器退出后不再重启。
    * `always`：无论退出码是什么，只要容器退出就会自动重启。
    * `on-failure:<次数>`：仅当容器以非零状态（异常）退出时尝试重启，并可限制最大重启次数（如 `on-failure:3`）。
  * **易错细节**：配置了 `always` 或 `on-failure` 的容器，在系统重新启动或 Docker 守护进程重启后，依然会自动拉起。
* **预留拓展补充空间**
  * > *[此处可补充：Docker 的重启退避策略（Exponential Backoff Delay），解释 Docker 是如何避免崩溃循环（CrashLoop）导致宿主机 CPU 飙升的]*

```bash
docker run -d --restart unless-stopped myapp:1.0
# unless-stopped：除非手动 stop，否则总是重启（现代常用）
```

## 停止容器

* **核心主旨与实用要点**
  * 掌握优雅关闭容器中运行进程的标准方法，避免直接截断导致的数据损坏。
* **核心指令与信号传递机制**
  * **命令**：`docker stop <ID或名称>`
  * **执行逻辑（重点结论）**：执行 `stop` 命令时，Docker 会向容器内的主进程（PID 1）发送 **SIGTERM** 信号。进程有一段宽限期（默认 10 秒）用于保存状态、关闭连接。如果超时进程仍未退出，Docker 会强制发送 **SIGKILL** 信号终止进程。
  * *比喻逻辑*：`docker stop` 相当于按下电脑的 ACPI 关机键（触发系统软关机），而强杀相当于直接拔掉电源。
* **预留拓展补充空间**
  * > *[此处可补充：如何在 Dockerfile 中利用 `STOPSIGNAL` 指令自定义优雅停止信号，例如 Nginx 更适合接收 SIGQUIT 信号]*

```bash
docker stop myapp
docker stop -t 30 myapp   # 自定义宽限期 30 秒
```

## 清除容器

* **核心主旨与实用要点**
  * 应对容器无法正常停止的异常情况，或者需要发送特定系统信号控制容器内程序的场景。
* **核心指令与信号控制**
  * **命令**：`docker kill <ID>`
  * **执行机制**：默认情况下，`docker kill` 直接向主进程发送不可阻挡的 **SIGKILL** 信号，强制立刻清除进程。
  * **发送自定义信号**：可通过 `--signal` 标志发送任意指定的 UNIX 信号（例如 `docker kill --signal=USR1 <ID>`），这在需要触发程序特定行为（如重载配置文件、打印堆栈信息）时非常有用。
* **预留拓展补充空间**
  * > *[此处可补充：不同编程语言（如 Java, Node.js, Go）在容器内捕获和处理 UNIX 信号（Signal Handling）的最佳实践及常见陷阱]*

## 暂停和恢复容器

* **核心主旨与实用要点**
  * 介绍基于 Linux cgroup freezer 机制的容器状态冻结功能，用于特殊调试或资源临时调配。
* **工作机制与因果关系**
  * **命令**：`docker pause <ID>` 与 `docker unpause <ID>`
  * **核心原理（逻辑拆解）**：与 `stop` 或 `kill` 不同，`pause` 不向容器发送任何 UNIX 信号。它直接利用底层的 cgroup 冻结程序（freezer）将整个进程组挂起。
  * *结果*：容器内的程序对暂停过程**完全无感知**，时间会在恢复时从断点继续计算。适用于快速备份状态或临时释放 CPU 资源。
* **预留拓展补充空间**
  * > *[此处可补充：CRIU (Checkpoint/Restore In Userspace) 技术与容器热迁移（Live Migration）的关联，说明容器内存状态持久化的前沿探索]*

## 清理容器和映像

* **核心主旨与实用要点**
  * 梳理日常维护 Docker 环境的批量清理技巧，防止磁盘空间和挂载点耗尽。
* **指令组合与过滤技巧**
  * **清理停止的容器**：通过组合命令 `docker rm $(docker ps -a -q)` 可删除所有非运行状态的容器。若需更精确，可结合 `--filter`（如 `docker rm $(docker ps -a -q --filter 'exited!=0')` 仅删除异常退出的容器）。
  * **清理映像**：使用 `docker rmi <映像名/ID>` 删除映像。
    * **易错细节/警告**：如果存在基于该映像的容器（即使处于停止状态），Docker 会返回 `Conflict, cannot delete` 错误。必须先删除容器，才能删除底层映像。
  * **清理悬挂映像（Dangling Images）**：执行 `docker rmi $(docker images -q -f "dangling=true")` 可批量清理构建过程中产生的无标签且无依赖的废弃映像层。
* **预留拓展补充空间**
  * > *[此处可补充：Docker 1.13 之后引入的现代清理命令 `docker system prune` 及其高级参数，对比旧版脚本式清理的优势]*

```bash
docker system prune -a        # 清理停止容器、无用网络、悬空镜像
docker system prune --volumes # 含未使用 volume
```

## 接下来

* **核心主旨**
  * 章节过渡总结，提示读者已经掌握了 Docker 的核心实体操作。
* **脉络关联**
  * 从映像的构建到容器的完整生命周期管理（启动、配置、监控、销毁）已经跑通，下一章将进入 `docker exec`、日志审查等深入探索容器内部的高级功能。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| 容器 vs VM | 共享宿主机内核；cgroup + namespace 隔离 |
| docker run | create + start；`-d` 后台，`-p` 端口 |
| -v | 挂载卷；`--read-only` 根 FS 只读更安全 |
| cpu-shares | 相对权重；竞争时才生效 |
| -m / --memory-swap | 内存上限；超限 OOMKilled |
| --restart | always / on-failure / unless-stopped |
| docker stop | SIGTERM → 宽限期 → SIGKILL |
| docker kill | 默认 SIGKILL；`--signal` 自定义 |
| docker pause | cgroup freezer 冻结，不发信号 |
| 清理顺序 | 先删容器，再删镜像 |
