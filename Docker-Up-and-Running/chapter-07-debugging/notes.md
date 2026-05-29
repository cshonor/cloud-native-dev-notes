# 第7章 调试容器 (Debugging Containers)

> **版次说明**：中译/第一版常称「第8章 调试容器」，第二版目录为 **Ch 07**。  
> **后端学习提示**：本章 **选学**——遇到问题时再翻。日常优先用 `docker logs` / `exec` / `inspect`（Ch 06）；`strace`/`gdb`/宿主机 `kill` 多在运维侧或疑难故障时使用。K8s 对应 `kubectl top`、Ephemeral Debug Container。

## 列出进程

* **核心主旨与实用要点**
  * 本节介绍了在不直接进入容器内部的情况下，如何从宿主机视角透视和审查容器内正在运行的进程树，以及跨命名空间管理进程时必须注意的用户权限（UID）映射陷阱。
* **核心知识点与逻辑拆解**
  * **基础审查命令**：执行 `docker top <容器ID>`。该命令通过调用 Docker Remote API，列出容器内运行的进程列表，输出格式类似 Linux 系统的 `ps` 命令（包含 UID、PID、PPID、C、STIME、TTY、TIME、CMD）。
  * **UID 映射陷阱（易错细节与警告）**：
    * *现象*：容器内的进程在宿主机执行 `ps` 审查时，显示的用户名可能极其怪异（例如在 CentOS 宿主机上，容器内原本属于 `lp` 的进程，宿主机上可能显示为 `halt` 用户）。
    * *因果关系*：因为容器内的 `UID` 是隔离的，但宿主机在执行 `ps` 解析用户名时，会**直接根据宿主机本地的 `/etc/passwd` 文件进行反向查找**。当容器内分配的 `UID=7` 对应 `lp`，而宿主机 `UID=7` 对应 `halt` 时，就会产生视觉欺骗。
    * *安全建议*：为了避免与宿主机系统用户（如 `nagios` 或 `postgres`）混淆甚至引发潜在的安全越权漏洞，强烈建议在启动容器时**使用一个明确且非零的自定义 UID（例如 `-u 5000`）**。
  * **进程树重构（逻辑脉络）**：
    * 宿主机的 `ps` 无法直观区分进程归属哪个容器，所有的进程都是平铺的。
    * *解决方案*：使用 `pstree` 和 `pidof` 组合命令。执行 `$ pstree -p \`pidof docker\``，可以将视图严格限制在 Docker 进程树下，清晰展示 `docker` 守护进程如何派生出 `docker-proxy`，以及具体的业务进程（如 `redis-server`、`mongod`）。
* **后端拓展：User Namespace**
  * 启用 User Namespace 后，容器内 `root`（UID 0）可映射为宿主机上的非特权 UID，降低容器逃逸后危害。生产镜像仍建议 `USER` 非 root + `runAsNonRoot`（K8s）。

```bash
docker top myapp
docker run -u 5000:5000 myapp          # 固定 UID，避免与宿主机用户撞号
pstree -p $(pidof docker)
```

| 命令 | 作用 |
|------|------|
| `docker top` | 容器内进程列表（不进入容器） |
| 宿主机 `ps` | UID 用户名可能误导，看数字 UID |
| `pstree -p $(pidof docker)` | 只看 Docker 子进程树 |

## 检查进程

* **核心主旨与实用要点**
  * 阐明容器本质上是标准的 UNIX 进程。因此，运维人员完全可以直接使用宿主机上成熟的底层调试工具对容器内运行的业务进行深度剖析。
* **关键调试工具与操作要点**
  * **系统调用追踪（strace）**：
    * *操作*：在宿主机上通过 `strace -p <PID>` 挂载到容器的实际 PID 上。
    * *结论*：由于容器共享宿主机内核，`strace` 能像监控本地原生应用一样，完美截获并输出容器进程产生的所有系统调用（如 `select`, `fcntl`, `accept4`）。
  * **打开文件审查（lsof）**：
    * *操作*：执行 `lsof -p <PID>` 审查进程调用的文件句柄。
    * *易错细节*：输出的路径（如 `/usr/local/rbenv/...`）是**相对于容器后端文件系统**的路径，而不是基于宿主机根文件系统的路径。不能直接在宿主机根目录下使用 `cd` 寻找这些文件。
  * **高级调试（gdb）**：
    * 只要使用具有相应权限的用户（通常是 `root`），甚至可以直接利用 GNU 调试器（gdb）和其他核心检查工具挂载到容器进程进行内存级调试。
* **后端拓展：K8s Ephemeral Container**
  * 精简镜像（distroless/alpine）常无 `strace`/`curl`。K8s 可注入临时调试容器共享 PID/网络命名空间，无需改生产镜像。对应：`kubectl debug -it pod/myapp --image=busybox --target=myapp`。

```bash
# 先拿容器在宿主机上的 PID（docker top 或 inspect）
PID=$(docker inspect --format '{{.State.Pid}}' myapp)
sudo strace -p $PID -f -e trace=network
sudo lsof -p $PID
```

```bash
# K8s 临时调试容器（现代替代：不在生产镜像里装调试工具）
kubectl debug -it myapp-xxx --image=nicolaka/netshoot --target=myapp
```

## 管理进程

* **核心主旨与实用要点**
  * 说明在不使用 Docker CLI 的情况下，如何通过原生 Linux 信号机制（Signals）直接从宿主机层面控制容器内进程的生命周期。
* **核心知识点与操作机制**
  * **直接信号传递（因果推导）**：
    * *传统认知*：通常我们使用 `docker kill` 命令强行终止容器。
    * *底层真相*：`docker kill` 本质上是对进程发送了 `SIGKILL` 信号。因为容器就是底层 UNIX 进程，所以我们完全可以在宿主机上直接执行标准的 `kill` 命令。
  * **优雅控制案例**：
    * 如果想让容器内的 `nginx` 重新加载日志文件而不终止运行，可以在宿主机上执行 `kill -SIGUSR1 <PID>`。这种机制在编写外部自动化运维脚本时极其高效。
* **后端拓展：PID 1 与 init**
  * 容器内 **PID 1** 负责收尸（僵尸进程）。若应用不处理 `SIGTERM` 或不回收子进程，会出现僵尸堆积或停不掉。多阶段镜像常在 `ENTRYPOINT` 用 **tini** / **dumb-init** 包装：`ENTRYPOINT ["/sbin/tini", "--"]`。

```bash
PID=$(docker inspect --format '{{.State.Pid}}' nginx-container)
kill -SIGUSR1 $PID          # nginx 重载配置/日志
docker kill myapp           # 等价于向 PID 1 发 SIGKILL
docker stop myapp           # 先发 SIGTERM，超时再 SIGKILL（优雅退出）
```

| 信号 / 命令 | 效果 |
|-------------|------|
| `docker stop` | SIGTERM → 等待 → SIGKILL |
| `docker kill` | 直接 SIGKILL |
| `kill -SIGUSR1 <PID>` | 如 nginx 重载，不杀进程 |

## 检查网络

* **核心主旨与实用要点**
  * 解析 Docker 容器端口映射在宿主机网络栈上的具体实现形式，帮助排查网络连通性故障。
* **核心指令与架构逻辑**
  * **网络状态查询（netstat）**：
    * 在宿主机执行 `netstat -anp | grep <端口号>`。
    * *重要结论*：输出结果显示，绑定在宿主机公网或本地 IP 上的监听服务（LISTEN），其所属进程**并不是容器内部的业务进程（如 nginx）**，而是 **`docker-proxy`**。
    * *逻辑脉络*：Docker 会在容器与外界建立隔离时，为每一个使用映射端口的容器生成一个 `docker-proxy` 进程。所有外部的入站请求首先命中宿主机的 `docker-proxy`，再由它通过 NAT（网络地址转换）或者底层桥接网络转发给隔离环境内的实际容器接口。
  * **底层抓包分析**：
    * 既然容器网络基于标准的网络设备，管理员可以毫无障碍地在宿主机物理接口或虚拟网桥（`docker0`）上使用 **`tcpdump`** 等工具进行网络层面的抓包与故障分析。
* **后端拓展：iptables 与 userland-proxy**
  * 现代 Docker 默认用 **iptables DNAT** 转发，`-p` 映射时 `docker-proxy` 可能不出现（取决于 `userland-proxy` 配置）。排障可查：`iptables -t nat -L DOCKER`。K8s 侧用 Service / `kubectl port-forward` / `tcpdump` on node。

```bash
ss -tlnp | grep 8080
# 或
netstat -anp | grep 8080

sudo tcpdump -i docker0 port 8080 -nn
sudo iptables -t nat -L DOCKER -n
```

```
外部请求 → 宿主机:8080 → docker-proxy（或 iptables）→ 容器 IP:容器端口
```

## 查看映像的历史

* **核心主旨与实用要点**
  * 介绍如何对现有 Docker 映像进行逆向工程分析，找出引发异常的某一层级文件或指令。
* **命令拆解与因果应用**
  * **执行指令**：`docker history <映像名称>`。
  * **输出数据（案例数据）**：命令会按时间倒序输出构建该映像的完整层级列表，包含每一层的 **Image ID**、**创建时间（CREATED）**、**执行命令（CREATED BY，如 CMD, ADD, ENV）** 以及该层的**体积大小（SIZE）**。
  * *应用场景推导*：如果容器因为依赖库版本陈旧而报错，且没有原始的 `Dockerfile`，运维人员可以通过 `docker history` 梳理出每一层的来源，精准定位是哪一步 `ADD` 或 `RUN apt-get` 引入了过期的包文件。
* **后端拓展：dive**
  * [`dive`](https://github.com/wagoodman/dive) 可逐层浏览镜像文件系统、标出「浪费层」，比纯文本 `history` 更直观。CI 中可配合镜像体积门禁。

```bash
docker history myapp:1.0 --no-trunc
dive myapp:1.0
```

## 检查容器

* **核心主旨与实用要点**
  * 揭示 Docker 守护进程在宿主机磁盘上持久化存储容器状态信息的底层目录结构。这是在 Docker 服务端进程卡死或容器无法启动时的「终极保底调试手段」。
* **目录结构与核心文件解析**
  * **存储路径**：所有的容器专属数据均存放在宿主机的 **/var/lib/docker/containers/<完整ID>** 目录下。
  * **完整 ID 获取（易错细节）**：`docker ps` 显示的仅仅是简短的截断 ID。要访问对应的存储目录，必须先通过 `docker inspect <容器名>` 获取包含 64 个十六进制字符的完整 `Id` 字段。
  * **关键文件拆解**：
    * **`config.json`**：存放容器的详细配置数据（JSON 格式）。
    * **`hostconfig.json`**：存放特定于宿主机的资源分配及挂载信息。
    * **`hostname` / `hosts` / `resolv.conf`**：挂载到容器内部提供网络域名解析的实体文件。
    * **`<ID>-json.log`**：容器内程序的标准输出和标准错误日志，当 `docker logs` 命令不可用时，可直接读取该文件进行抢救性审查。
* **后端拓展：Daemon 崩溃时**
  * `dockerd` 无响应时：可读 `config.json` 还原 `Env`、`Cmd`、`Image`；日志直接 `tail` `*-json.log`。恢复后应用 `docker start` 或按配置重建容器。**勿手改 JSON 除非明确后果**。

```bash
CID=$(docker inspect --format '{{.Id}}' myapp)
sudo ls /var/lib/docker/containers/$CID/
sudo cat /var/lib/docker/containers/$CID/$CID-json.log | tail
sudo jq .Config.Env /var/lib/docker/containers/$CID/config.v2.json  # 路径因版本而异，常用 inspect 代替
```

## 检查文件系统

* **核心主旨与实用要点**
  * 利用 Docker 联合文件系统（UnionFS）的写时复制（CoW）特性，快速审计容器在运行时对文件系统造成的增量修改。
* **功能命令与状态标识**
  * **执行指令**：`docker diff <容器ID>`。
  * **输出标识符定义**：该命令会将当前容器的顶层可写层与底层只读基础镜像进行逐文件比对，输出三种状态：
    * **`C` (Changed)**：文件或目录的内容/权限被修改。
    * **`A` (Added)**：新增的文件或目录。
    * **`D` (Deleted)**：从基础镜像中被删除的文件。
  * **应用逻辑与价值**：
    * *审计与排障*：能清晰看出应用（如 Redis）在运行过程中向哪些意外路径（如 `/var/run/crond.pid` 或 `/var/lib/redis/dump.rdb`）写入了数据。
    * *架构优化指导*：如果发现大量数据写入了容器顶层，这违背了无状态原则。开发者可以据此精准识别出哪些目录需要在后续部署时通过挂载外部 Volume 进行持久化。
* **后端拓展：安全审计**
  * 入侵排查：`docker diff` 看异常 `A` 文件；`docker commit` 可固化现场（**仅取证，勿把被污染镜像推生产**）。

```bash
docker diff myapp
# 示例输出：
# C /etc/nginx/nginx.conf
# A /var/lib/redis/dump.rdb
```

| 标记 | 含义 |
|------|------|
| C | 修改 |
| A | 新增 |
| D | 删除（相对基础镜像） |

## 接下来

* **核心主旨**
  * 章节过渡总结，标志着对单机 Docker 环境（部署、测试、调试）的学习告一段落。
* **脉络关联（第二版）**
  * 已掌握单体容器深度排错；下一步 **Ch 08 Docker Compose**（必学）——本地一键拉起 app + DB + Redis。集群与弹性伸缩见 Ch 10（本书跳过，交给《K8s Up & Running》）。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| `docker top` | 宿主机视角看容器内进程 |
| UID 陷阱 | 宿主机 `ps` 用户名不可信，用 `-u` 固定 UID |
| `strace` / `lsof` | 挂宿主机 PID；路径是容器内视角 |
| K8s 调试 | Ephemeral Container / `kubectl debug` |
| `kill` 信号 | 容器即进程；`SIGUSR1` 可 reload nginx |
| PID 1 | 用 tini/dumb-init 处理僵尸与信号 |
| 端口映射 | LISTEN 常是 `docker-proxy` 或 iptables NAT |
| `docker history` | 逆向 Dockerfile 层；配合 dive |
| `/var/lib/docker/containers/` | 保底读 config、json.log |
| `docker diff` | C/A/D 审计可写层；指导 Volume 挂载 |
