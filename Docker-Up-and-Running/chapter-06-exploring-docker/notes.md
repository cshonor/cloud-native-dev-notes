# 第6章 探索Docker的其他功能 (Exploring Docker)

> **后端学习提示**：本章**必学**。`docker version`/`info`、`inspect`、`exec`、`logs`、`stats` 是日常排障核心；与 K8s 的 `kubectl describe`/`logs`/`exec`/`top` 一一对应。

## 打印 Docker 的版本号

* **核心主旨与实用要点**
  * 本节介绍了排查客户端与服务端连接故障的最简单切入点：获取和核对系统各组件的版本信息。
* **核心知识点与诊断逻辑**
  * **执行指令**：`docker version`。
  * **输出内容拆解**：该命令不仅会显示客户端（Client）的版本号，还会尝试连接服务端并拉取服务端（Server）的版本号、API 版本、Go 语言编译版本以及底层操作系统架构（OS/Arch）。
  * **排障因果逻辑**：如果在执行该命令时只看到客户端信息，而服务端部分报错退出，**这通常明确意味着客户端无法通过当前环境变量（如 DOCKER_HOST）或本地套接字正确连接到远程/本地的 Docker 守护进程**。在排查复杂故障前，应首先用此命令验证环境可用性。
* **预留拓展补充空间**
  * > *[此处可补充：不同 Docker 版本（如 API 1.xx 与 1.yy）之间可能存在的客户端与服务端兼容性矩阵表格]*

```bash
docker version
```

## 服务器信息

* **核心主旨与实用要点**
  * 阐述了如何审查 Docker 守护进程级别的全局硬件与底层引擎配置信息，用于环境审计。
* **指令参数与关键结论**
  * **执行指令**：`docker info`。
  * **核心状态数据**：命令输出当前环境中的容器总数（Containers）、映像总数（Images）、存储驱动类型（Storage Driver，如 aufs / devicemapper）、执行驱动（Execution Driver）、内核版本（Kernel Version）以及分配给 Docker 守护进程的 CPU 和内存总量。
  * **跨环境对比**：在使用不同方式或在不同云平台（如 Ubuntu vs CentOS）上安装 Docker 时，此命令能够清晰展示底层使用的系统目录和驱动差异。
* **预留拓展补充空间**
  * > *[此处可补充：在生产环境中，Storage Driver（存储驱动）选择 overlay2 或 devicemapper 对底层性能的影响深度分析]*

```bash
docker info
```

## 下载映像的更新

* **核心主旨与实用要点**
  * 说明了 Docker 映像的本地缓存机制，以及如何手动拉取远程注册处的最新版本。
* **执行机制与易错细节**
  * **执行指令**：`docker pull <映像名>:<标签>`。
  * **本地缓存盲区（易错细节）**：Docker 在本地已有对应映像时，**不会自动联网检查或下载该映像的新版本**。即使上游发布了重要的安全补丁，必须显式地定期执行 `docker pull` 才能获取最新的分层。
  * **`latest` 标签逻辑**：执行拉取时，`latest` 标签始终指向注册处中当前最新分发版本的引用。
* **预留拓展补充空间**
  * > *[此处可补充：CI/CD 自动化流水线中，如何利用 Watchtower 或其他机制实现映像的自动检查与更新]*

```bash
docker pull nginx:latest
```

## 审查容器

* **核心主旨与实用要点**
  * 讲解了如何通过深度检视工具提取容器运行时的内部配置结构和底层硬件挂载细节。
* **数据结构与逻辑脉络**
  * **执行指令**：`docker inspect <容器ID或名称>`。
  * **输出格式**：返回一个高度详细的 **JSON 格式数组**，包含配置指令（Config）、挂载路径（Mounts/Volumes）、网络设置（NetworkSettings）及环境变量（Env）等。
  * **完整 ID 与简短 ID**：平时通过 `docker ps` 看到的只是简短截断的 ID。`docker inspect` 的输出中的 `Id` 字段，提供的是由 64 个十六进制字符组成的**完整 SHA 标识符**，这在直接查找底层文件系统路径时至关重要。
* **预留拓展补充空间**
  * > *[此处可补充：如何使用 `--format` (Go 模板) 标志高效过滤 JSON 输出，例如快速提取特定容器的 IP 地址：`docker inspect --format '{{ .NetworkSettings.IPAddress }}' <ID>`]*

```bash
docker inspect myapp
docker inspect --format '{{.NetworkSettings.IPAddress}}' myapp
docker inspect --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{"\n"}}{{end}}' myapp
```

## 进入运行中的容器

* **核心主旨与实用要点**
  * 探讨了在不中断业务服务的前提下，注入新的 Shell 进程以调试和诊断容器的最佳实践。
* **技术沿革与核心工具（段落分层）**
  * **原生首选方案（Docker 1.3+）**：使用 `docker exec -i -t <容器ID> /bin/bash`。这是目前官方推荐的规范操作，它利用守护进程直接在已有的命名空间中启动一个全新的交互式终端（TTY），进行动态检视而不影响主进程。
  * **备用方案（nsenter）**：在旧版或原生机制不可用时，利用 Linux 原生的命名空间进入工具 `nsenter`。操作逻辑为：首先通过 `docker inspect` 获取容器主进程的 PID，然后执行 `nsenter --target $PID --mount --uts --ipc --net --pid` 挂载对应的隔离视图。为了简化，社区曾提供过 `docker-enter` 包装脚本。
* **易错细节与警告**
  * **安全与架构警告**：绝对不建议在容器中强行打包运行 SSH 守护进程（SSH Server）来进行登录。这违背了单一进程的轻量级容器设计哲学，增加了无谓的安全攻击面。
* **预留拓展补充空间**
  * > *[此处可补充：`docker exec` 与 `docker attach` 的本质区别，解释为何 `attach` 容易导致误杀主进程（PID 1）引发容器意外停止]*

```bash
docker exec -it myapp /bin/bash
# exec：新进程；attach：连到 PID 1，Ctrl+C 可能杀容器
```

## 在 shell 中探索

* **核心主旨与实用要点**
  * 描述进入容器内部 Shell 后的视角隔离特性，以及容器内生命周期的临时性表现。
* **逻辑脉络与重点结论**
  * **进程隔离验证**：在容器内执行 `ps -ef`，通常只会看到屈指可数的几个进程（如 PID 为 1 的主应用，及当前执行的 Shell 进程）。这直观证明了命名空间在隐藏宿主机全量系统进程上的隔离效果。
  * **修改的瞬态性**：用户可以在 Shell 中执行包管理器（如 `apt-get install`）安装调试工具。但**因果关系**在于：这些改动仅写入在当前容器可读写的顶层（Top Layer）中，并不会反向修改只读的基础映像。容器一旦销毁，这些手动修改的调试环境将彻底丢失。
* **预留拓展补充空间**
  * > *[此处可补充：如何在调试完毕后，利用 `docker commit` 将当前容器的修改态临时保存为新映像用于问题溯源]*

## 返回结果

* **核心主旨与实用要点**
  * 阐明 Docker 容器与宿主机之间关于标准输入/输出流（STDIN/STDOUT）及进程退出状态码的桥接机制。
* **核心知识点拆解**
  * **退出码传递**：在容器内执行的任务（例如 `docker run ... /bin/false`），其生成的退出状态码（如 1）会被 Docker 守护进程捕获，并**原样返回给外部宿主机的终端**。
  * **管道重定向（Pipes）**：
    * 支持将宿主机的数据通过标准输入传递给容器处理。
    * 支持将容器的标准输出通过管道传回宿主机交由外部工具处理（例如：`docker run ... cat /etc/passwd | wc -l`）。
  * **易错细节**：在编写管道操作时，需分清是由宿主机 Shell 解析还是由容器内 Shell 解析，这取决于是否使用了正确的引号包裹命令行。
* **预留拓展补充空间**
  * > *[此处可补充：在后台运行（-d）场景下，如何处理 STDIN 以保持进程不退出（-i 的作用机理）]*

```bash
docker run --rm alpine cat /etc/os-release | grep PRETTY
echo "hello" | docker run -i --rm alpine cat
```

## Docker 的日志

* **核心主旨与实用要点**
  * 讲解容器标准输出到宿主机日志文件的流转机制，以及日志管理的潜在系统风险与解决方案。
* **日志流获取与底层机制**
  * **查询指令**：`docker logs <容器ID>`（可配合 `-f` 持续跟踪尾部日志）。
  * **JSON 存储机制**：Docker 默认拦截容器的 STDOUT 和 STDERR，并将其格式化为带有时间戳的 JSON 对象，存储在宿主机特定的文件路径中（如 `/var/lib/docker/containers/<ID>/<ID>-json.log`）。
* **易错细节与严重警告**
  * **磁盘耗尽风险**：**Docker 的默认 JSON 日志引擎不会自动执行日志轮转（Log Rotation）**。如果容器产生大量日志，将直接耗尽宿主机磁盘空间。
  * **应对方案**：1. 配置外部工具（如 `logrotate` 结合 `copytruncate`）；2. 启动容器时指定专门的日志驱动（Log Driver），例如使用 `--log-driver=syslog` 或设置为 `none` 禁用日志，转而利用应用内部日志或第三方收集器（如 Logspout）。
* **预留拓展补充空间**
  * > *[此处可补充：现代 Docker 支持的进阶 Log Drivers 配置体系，如 Fluentd, JSON-file 的 max-size 和 max-file 参数配置]*

```bash
docker logs myapp
docker logs -f --tail 100 myapp
docker logs --since 10m myapp
```

```json
// daemon.json 日志轮转
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

## 监控 Docker

* **核心主旨与实用要点**
  * 介绍保障生产环境稳定运行所需的容器层级实时状态、资源统计及生命周期事件监控手段。
* **三大监控支柱拆解**
  * **动态统计信息（Stats）**：
    * **执行指令**：`docker stats <容器ID>`。
    * **作用**：在终端实时刷新显示容器的 CPU 利用率、内存消耗与限制量、以及网络 I/O 字节数。
    * **API 层面**：系统在后台实际调用了 Docker Remote API 的 `/stats` 端点，流式输出详细的硬件消耗 JSON 数据块。
  * **事件总线（Events）**：
    * **执行指令**：`docker events`。
    * **机制**：守护进程会持续将所有容器的生命周期状态变更（如 start, stop, die, destroy）推送到事件流。可以结合 `--since` 或 `--until` 按照时间范围回溯审查历史故障事件。
  * **图形化监控工具（cAdvisor）**：
    * **重点推荐**：面对纯文本或原始 API 调用的局限性，推荐部署 Google 开源的容器监控利器 **cAdvisor**。
    * **部署方式**：它本身即可作为 Docker 容器运行，需挂载宿主机的只读核心目录（如 `/rootfs`, `/var/run`, `/sys`, `/var/lib/docker`）以读取底层隔离视图。
    * **效果**：通过暴露的 Web 界面直观输出每个容器历史到当前的 CPU、内存和网络波动图表。
* **预留拓展补充空间**
  * > *[此处可补充：企业级云原生监控体系演进，cAdvisor 数据如何被 Prometheus 抓取并展示在 Grafana 大盘中的集成方案]*

```bash
docker stats
docker events --since 1h
```

| Docker 命令 | K8s 对应 |
|-------------|----------|
| docker logs | kubectl logs |
| docker exec | kubectl exec |
| docker inspect | kubectl describe |
| docker stats | kubectl top pods |

## 小结

* **核心主旨与实用要点**
  * 复习了从环境检查到日志审查、再到实时监控的一整套进阶工具链，强调这些指令在实际问题排查中的不可或缺性。
* **补充工具清单**
  * 在本章末尾简述了其他文件系统相关的常用命令：
    * `docker cp`：在容器内部与宿主机系统之间安全地进行文件和目录的复制迁移。
    * `docker export`：提取整个容器系统的扁平化打包归档（tar 文件）。
    * `docker save / import`：用于打包/导入整个 Docker 映像（含层级历史）。
* **预留拓展补充空间**
  * > *[此处可补充：`docker export` (针对容器文件系统) 与 `docker save` (针对完整分层映像) 的技术差异与使用场景选型]*

```bash
docker cp myapp:/app/logs ./logs
docker save myapp:1.0 -o myapp.tar    # 完整镜像层
docker export myapp -o myapp-fs.tar   # 扁平容器 FS
```

## 本章速记

| 概念 | 一句话 |
|------|--------|
| docker version | 客户端 + 服务端；连不上先查这个 |
| docker info | 守护进程级：驱动、容器/镜像数 |
| docker pull | 本地有镜像不会自动更新 |
| docker inspect | JSON 详情；`--format` 提取字段 |
| docker exec | 进容器调试；首选，不用 SSH |
| 容器内改动 | 只写顶层，销毁即丢 |
| docker logs | 默认 JSON 文件；注意磁盘爆满 |
| docker stats | 实时 CPU/内存/网络 |
| docker events | 容器生命周期事件流 |
| docker cp | 容器 ↔ 宿主机拷文件 |
