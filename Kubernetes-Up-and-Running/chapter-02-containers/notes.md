# 第二章：创建与运行容器 (Chapter 2: Creating and Running Containers)

## 容器镜像 (Container Images)

* **核心定义**：
  * **容器镜像（Container Image）**是一个二进制包，封装了在操作系统容器内运行程序所需的所有文件。
  * 最流行的格式是**Docker镜像格式**，该格式已被开放容器倡议（OCI）标准化，Kubernetes通过Docker及其他运行时支持兼容的镜像。
* **层级架构与Overlay文件系统逻辑**：
  * 容器镜像并非单一文件，而是由一系列**文件系统层（Filesystem Layers）**构建而成。
  * 每一层在上一层的基础上添加、删除或修改文件，这是一种**Overlay文件系统**的典型实现（如aufs, overlay2等）。
  * **逻辑脉络**：例如，层A为基础操作系统（如Debian），层B在A基础上添加Ruby，层C在A基础上添加Golang。B和C共享底层A的文件，这种指针引用式的层级结构大幅提升了存储与传输效率。
* **容器分类**：
  * **系统容器（System containers）**：试图模仿虚拟机，运行完整的启动过程（包括ssh、cron、syslog等），目前被视为不良实践。
  * **应用容器（Application containers）**：通常**每个容器只运行一个单一程序**，为构建可扩展应用提供了完美的粒度，这也是Kubernetes中Pod设计的核心哲学。

> 💡 **后续拓展空间**：可在此补充OCI（Open Container Initiative）规范的具体结构，以及Overlay2文件系统在Linux内核级别的挂载原理与性能表现。

---

## 使用Docker构建应用镜像 (Building Application Images with Docker)

* **Dockerfile配置脉络**：
  * **Dockerfile**是用于自动化创建容器镜像的配方文件。
  * 构建一个典型的Node.js应用，核心指令包括：`FROM`（指定基础镜像），`WORKDIR`（设置工作目录），`COPY`（拷贝文件，利用`.dockerignore`排除无关文件），`RUN`（执行安装命令），以及`CMD`（指定容器启动时的默认命令）。
* **镜像体积优化与缓存逻辑**：
  * **易错细节（层级陷阱）**：在某一层中添加了一个大文件，并在后续层中将其删除。该文件在最终镜像中虽然不可访问，但**实际上仍然存在于底层镜像中**。在推送或拉取镜像时，该隐藏文件依然会占用网络带宽。
  * **缓存命中逻辑**：每一层都是前一层的增量。如果更改了某一层，其**之后的所有层**都必须重新构建和拉取。
  * **实用要点（最佳实践）**：在Dockerfile中，应当**将最不可能更改的层放在前面，最可能更改的层放在后面**。例如，先拷贝包管理文件（`package.json`）并安装依赖，最后再拷贝频繁变动的应用程序源代码，以此最大化缓存利用率。
* **镜像安全硬性规则**：
  * **核心警告**：**绝不能将密码或密钥硬编码到镜像的任何层中**。由于层级叠加特性，即使在最终层删除了密码文件，攻击者依然可以通过提取特定底层历史记录来获取敏感信息。

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
CMD ["node", "server.js"]
```

> 💡 **后续拓展空间**：可深入讨论无发行版（Distroless）镜像的使用场景，以及容器镜像漏洞扫描工具（如Trivy或Clair）的CI/CD集成方案。

---

## 多阶段镜像构建 (Multistage Image Builds)

* **引入背景与痛点**：
  * 将代码编译过程放在镜像构建阶段是最简单的方法，但这会导致最终镜像中残留大量不必要的编译工具（如Go编译器、React工具链以及源代码），导致镜像体积庞大，严重拖慢部署速度。
* **核心机制与逻辑**：
  * **多阶段构建（Multistage builds）**允许在一个Dockerfile中生成多个镜像阶段（Stage）。
  * **实施逻辑**：第一阶段（命名为`build`）包含完整的编译环境并执行构建脚本；第二阶段（部署阶段）从一个极简的基础镜像（如Alpine）开始，使用`COPY --from=build`指令**仅将编译好的二进制文件**拷贝过来。
* **案例数据对比**：
  * 对于包含React前端和Go后端的`kuard`应用，采用传统单阶段构建的镜像大小超过 **500 MB**。采用多阶段构建后，最终镜像大小缩减至约 **20 MB**。

```dockerfile
# 构建阶段
FROM golang:1.22 AS build
WORKDIR /src
COPY . .
RUN go build -o /app/server .

# 运行阶段
FROM alpine:3.19
COPY --from=build /app/server /server
CMD ["/server"]
```

> 💡 **后续拓展空间**：可补充C/C++或Java等其他编译型语言的多阶段构建模板，以及如何利用跨阶段构建来隔离不同团队的构建环境。

---

## 在远程注册表中存储镜像 (Storing Images in a Remote Registry)

* **核心主旨**：
  * 将镜像存储在**远程注册表（Remote Registry）**中是实现Kubernetes集群内跨节点共享镜像的前提标准做法，坚决抵制手动导入导出的反模式。
* **公有与私有注册表**：
  * **公有注册表**：允许无验证的自由下载（如Docker Hub），适合分发开源软件。
  * **私有注册表**：需要身份验证（`docker login`），适用于存放企业的闭源核心业务代码。
* **操作命令要点**：
  * 使用冒号（`:`）为镜像添加版本标签，并前置目标注册表地址：`docker tag <image> <registry>/<name>:<tag>`。
  * 推送至远端：`docker push <registry>/<name>:<tag>`。

> 💡 **后续拓展空间**：可在此引入Harbor等企业级私有镜像仓库的搭建原理，以及Kubernetes中`imagePullSecrets`的对象管理机制。

---

## Docker容器运行时 (The Docker Container Runtime)

* **底层架构逻辑**：
  * Kubernetes提供应用部署的API，但依赖底层的**容器运行时（Container Runtime）**通过原生OS API（如Linux的cgroups和namespaces）来实际启动容器。
  * Kubernetes与运行时的接口通过**CRI（Container Runtime Interface）**标准定义，支持`containerd-cri`、`cri-o`等多种实现。
* **本地运行与网络隔离**：
  * 使用`docker run -d --name <name> -p <local-port>:<container-port> <image>`来后台运行容器。
  * **关键原因**：必须使用`-p`进行端口转发，因为每个容器都分配了独立的内部IP地址，直接在容器内监听`localhost`无法将流量暴露给宿主机。
* **资源限制机制 (Limiting Resource Usage)**：
  * 利用Linux内核的cgroup技术，可以强制约束容器的资源使用，保证硬件的多租户公平共享。
  * **内存限制**：通过`--memory`和`--memory-swap`参数设置。如果程序消耗的内存超过分配限制，容器进程将被操作系统直接**终止（Terminated / OOM）**。
  * **CPU限制**：通过`--cpu-shares`限制。CPU属于可压缩资源，超出限制通常面临限流而非终止。

> 💡 **后续拓展空间**：可拓展介绍CRI-O与Docker在Kubernetes生态中的演进历史，以及cgroup v1与v2版本在资源控制上的细微差异。

---

## 清理工作 (Cleanup)

* **易错细节与垃圾回收**：
  * **标签覆盖陷阱**：使用完全相同的名称构建新镜像时，仅仅是将Tag转移到了新镜像上，**旧镜像的底层文件并不会被删除**，它会作为游离镜像（Dangling image）永久保留在系统中占用空间。
* **清理命令与自动化**：
  * 手动删除特定镜像：`docker rmi <tag-name>` 或 `docker rmi <image-id>`。
  * **批量清理**：使用`docker system prune`可一次性删除所有已停止的容器、未打标签的镜像以及构建缓存。
  * **最佳实践**：在CI/CD节点或开发机上，建议将清理工具（如`docker-gc`）配置为**Cron定时任务**（每日或每小时运行），以实现镜像垃圾的自动化回收。

> 💡 **后续拓展空间**：探讨在Kubernetes工作节点上，`kubelet`内置的镜像垃圾回收机制（Image Garbage Collection）的触发阈值配置（HighThresholdPercent/LowThresholdPercent）。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| 容器镜像 | OCI 标准化的分层二进制包 |
| Overlay 层 | 共享底层，增删改叠加；删文件不删层内数据 |
| 应用容器 | 一容器一进程，K8s Pod 的设计基础 |
| Dockerfile 缓存 | 变动少的层放前面，变动多的放后面 |
| 多阶段构建 | `COPY --from=build` 只带二进制，大幅瘦身 |
| Registry | 集群跨节点共享镜像的标准方式 |
| CRI | K8s 与 containerd/cri-o 等运行时的标准接口 |
| 资源限制 | 内存超限 OOM；CPU 超限限流 |
| 镜像清理 | 重打 tag 不删旧层；`docker system prune` |
