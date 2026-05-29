# 第3章 安装Docker (Installing Docker)

> **后端学习提示**：本章**必学**。会装客户端/守护进程、能跑通 `docker run` 验证；现代环境优先用 **Docker Desktop**（Mac/Windows）或发行版包管理器（Linux），书中 Boot2Docker 仅作历史背景了解。

## 重要的术语

* **核心主旨与实用要点**
  * 在进入具体的安装步骤前，界定 Docker 生态中最核心的五个基础概念，为后续理解 C/S 架构和运行机制奠定基础。
* **关键定义与知识点拆解**
  * **Docker 客户端（Client）**：在日常的 Docker 式工作流程中，用户主要通过执行 `docker` 命令来控制客户端，并由它与远程的 Docker 服务器进行通信。
  * **Docker 服务器（Server / Daemon）**：以守护进程（daemon）模式运行的 `docker` 命令。它负责将底层的 Linux 系统转化为 Docker 服务器，接受客户端请求，从而在宿主机中部署、启动或删除容器。
  * **Docker 映像（Image）**：由一个或多个文件系统层及配置元数据组成的只读模板，包含了运行 Docker 化应用所需的所有文件。一个 Docker 容器可以通过映像复制到多个宿主机中。
  * **Docker 容器（Container）**：使用 Docker 映像实例化后的 Linux 容器。特定状态的容器只能存在一次，但可以使用同一个映像轻易地创建多个同样的容器。
  * **基元宿主机（Atomic Host）**：经过细致调整的**小型操作系统映像**（例如 CoreOS 和 Project Atomic），专门用于存储容器，支持原子的操作系统升级操作。
* **逻辑脉络与关联**
  * *逻辑关联*：用户通过**客户端**发出指令 → **服务器（守护进程）**接收指令 → 服务器提取**映像** → 根据映像在**基元宿主机**或普通 Linux 内核上创建并运行**容器**。
* **预留拓展补充空间**
  * > *[此处可补充：Docker 架构中「注册处（Registry）」的概念定义，以及它与 Image 和 Container 之间的生命周期流转图]*

```
Client → Daemon → Image → Container
              ↑
         Registry（拉取镜像）
```

## 安装 Docker 客户端

* **核心主旨与实用要点**
  * 详解在不同操作系统（Linux, Mac OS X, Windows）下获取和安装 Docker 客户端可执行文件的标准途径。
* **详细知识点拆解与环境配置**
  * **系统兼容性要求**：Docker 客户端原生支持 **64 位**的 Linux 和 Mac OS X（因为底层都是 UNIX）。目前**不支持 32 位**系统。
  * **Linux 系统安装**：
    * 强烈建议在最新版本的 Linux 发行版中运行（内核要求使用 3.8 或以上版本）。
    * *Debian/Ubuntu*：使用 `apt` 包管理工具，例如执行 `sudo apt-get install docker.io`，并通过 `source /etc/bash_completion.d/docker.io` 开启命令补全。
    * *Red Hat/Fedora/CentOS*：使用 `rpm` 及其前端工具 `yum`，例如执行 `sudo yum -y install docker-io`。
      * *易错细节/警告*：在 Fedora 旧版中，系统包里已有一个名为 `docker` 的包（属于 WindowMaker 桌面），所以 Docker 包被重命名为 `docker-io`。此外，若遇到 "Cannot start container" 错误，需执行 `sudo yum upgrade selinux-policy` 并重启系统。
  * **Mac OS X 系统安装**：
    * 可通过官方提供的 Boot2Docker GUI 安装程序（包含 VirtualBox）进行一键安装。
    * 或通过包管理器 **Homebrew** 安装：`brew install docker` 和 `brew install boot2docker`（需先安装 `caskroom/cask/brew-cask` 扩展和 VirtualBox）。
      * *安全警告*：随意运行网上的不明脚本（如 `curl -L | sh` 形式）存在被恶意篡改的巨大安全隐患，建议先阅读脚本内容或使用官方包管理器。
  * **Windows 系统安装**：
    * 主要依赖下载最新版的 Boot2Docker 安装程序进行配置，安装过程会自动提供 VirtualBox 和 Docker 客户端。
* **现代安装方式（后端推荐）**：

```bash
# Linux（Ubuntu/Debian 示例）
sudo apt-get update
sudo apt-get install docker.io

# Mac（Homebrew）
brew install --cask docker   # Docker Desktop

# 验证客户端
docker version
```

* **预留拓展补充空间**
  * > *[此处可补充：目前最新的 Docker Desktop for Mac/Windows 的安装要求与架构（如基于 WSL2 或 Hyper-V），替代早期 Boot2Docker 的演进过程]*

## 安装 Docker 服务器

* **核心主旨与实用要点**
  * 阐述如何启动 Docker 的核心后台进程（守护进程），以及在非 Linux 平台下如何借助虚拟机工具搭建合规的服务端环境。
* **详细配置拆解与启动逻辑**
  * **命令与端口绑定（核心机制）**：
    * Docker 服务器集成在与客户端相同的二进制文件中。通过 `sudo docker -d` 命令以守护进程模式启动。
    * *网络配置*：可以使用 `-H` 参数指定绑定的套接字。例如 `-H unix:///var/run/docker.sock` (绑定本地 UNIX 套接字) 以及 `-H tcp://0.0.0.0:2375` (绑定所有本地 IP 的未加密端口 2375)。
  * **Linux 系统初始化守护进程配置**：
    * *systemd*（如 Fedora）：执行 `sudo systemctl enable docker` 设置开机启动，`sudo systemctl start docker` 立即启动。
    * *upstart*（如 Ubuntu 旧版）：脚本配置通常已自动化完成，无需手动干预。
    * *init.d*（如 Red Hat 6）：使用 `chkconfig docker on` 开启自启，`service docker start` 启动服务。
  * **在 Linux 之外的系统中使用虚拟机搭建服务器（重点分类）**：
    * 由于 Docker 服务端必须依赖 Linux 内核，Mac 和 Windows 用户必须使用底层虚拟机环境。可选方案包括：
    * **Boot2Docker**：执行 `boot2docker init` 下载 ISO 并初始化，然后执行 `boot2docker up` 启动虚拟机，最后按提示导出 `$DOCKER_HOST`、`$DOCKER_TLS_VERIFY` 等环境变量，以便本地客户端连接虚拟机内的服务端。
    * **Docker Machine**：官方推出的更强健工具。通过 `docker-machine create --driver virtualbox local` 创建虚拟机，使用 `eval "$(docker-machine env local)"` 快速配置本地 Shell 的环境变量。可使用 `docker-machine ssh local` 直接登录节点。
    * **Vagrant**：适合需要更灵活定制开发环境的用户，可配合 CoreOS 或 Ubuntu 盒子（Box）使用 `Vagrantfile` 及 `cloud-init` 脚本自动化拉起预置好 Docker 环境的虚拟机。
* **易错细节与排障**
  * *环境变量遗漏*：在 Mac/Windows 上使用命令行客户端时，如果不设置 `DOCKER_HOST`，客户端默认寻找本地的 UNIX sock，将导致无法连接服务器错误。
* **Linux 现代启动命令**：

```bash
sudo systemctl enable docker
sudo systemctl start docker
sudo systemctl status docker

# 将当前用户加入 docker 组（免 sudo）
sudo usermod -aG docker $USER
```

* **预留拓展补充空间**
  * > *[此处可补充：在企业级生产环境中，如何配置 `daemon.json` 文件以持久化管理守护进程参数（如配置国内镜像加速器 Registry-mirrors、日志轮转策略等）]*

## 测试安装的 Docker

* **核心主旨与实用要点**
  * 通过运行一个最基础的测试容器，验证从客户端、网络到服务端虚拟化隔离层的全链路是否正常可用。
* **测试指令与参数要点**
  * **通用验证命令**：`docker run --rm -ti ubuntu:latest /bin/bash`。
  * **参数解析**：
    * `--rm`：指示 Docker 在该容器退出运行后，立即自动清理/删除该容器文件系统，避免测试垃圾残留。
    * `-ti`：为容器分配一个伪终端（TTY）并保持标准输入（STDIN）打开，使得用户可以进入交互式 bash shell 操作。
    * `ubuntu:latest`：指定测试的基础映像。也可以根据宿主系统替换为 `fedora:latest` 或 `centos:latest`。
  * *易错细节*：在部分 Linux 系统中直接执行上述命令可能会遇到权限拒绝，需要加上 `sudo`，或者将当前用户加入到宿主机的 `docker` 用户组中。
* **预留拓展补充空间**
  * > *[此处可补充：`docker run hello-world` 的底层执行步骤拆解，从本地 Cache 查找缺失、到向 Docker Hub 发起 Pull，最后创建 Container 执行的完整流转图]*

```bash
# 快速冒烟测试
docker run hello-world

# 交互式验证
docker run --rm -ti ubuntu:latest /bin/bash
```

## 小结

* **核心主旨与结论**
  * 确认基础设施搭建完毕，总结了如何确保 Docker 客户端与服务器的正确通信连接，为进入后续深度的容器操作扫清障碍。
* **关键关联与注意事项**
  * *核心要点*：后续所有进阶学习的前提，是必须确保环境变量配置正确（或传入了 `-H` 标志），只有这样客户端才能随时准确无误地定位并连接到守护进程。
* **预留拓展补充空间**
  * > *[此处可补充：常见环境连通性排错指南 (Troubleshooting)，例如遇到 "Cannot connect to the Docker daemon" 时的系统化排查命令清单]*

## 本章速记

| 概念 | 一句话 |
|------|--------|
| Client | `docker` 命令，向 Daemon 发请求 |
| Daemon | 后台守护进程，真正创建/管理容器 |
| Image | 只读模板；Container 是其实例 |
| Linux 安装 | `apt install docker.io` 或 Docker Desktop |
| 启动 Daemon | `systemctl enable/start docker` |
| Mac/Win | 需 Linux VM（现用 Docker Desktop / WSL2） |
| DOCKER_HOST | 未设置则客户端找不到远程 Daemon |
| 验证 | `docker run hello-world` 或 `--rm -ti ubuntu bash` |
| 权限 | 加 `docker` 用户组或 `sudo` |
