# 第4章 使用 Docker 映像 (Working with Docker Images)

> **后端学习提示**：本章**必学** ⭐。Dockerfile 指令、`docker build`/缓存、推送到 Registry 是后端日常核心技能；与 K8s Deployment 镜像字段、CI/CD 流水线直接衔接。

## 剖析 Dockerfile 文件

* **核心主旨与实用要点**
  * 本节深度剖析了用于自动化构建 Docker 映像的 `Dockerfile` 脚本文件，解析了基础指令的语法、作用及最佳实践。
* **核心指令拆解与易错细节**
  * **FROM**：指定构建的基础映像（例如 `FROM node:0.10`），后续所有指令都将基于该映像的文件系统。
  * **MAINTAINER**：定义作者联系信息，该信息最终会出现在映像元数据的 Author 字段中。
  * **LABEL**：自 Docker 1.6 引入，使用键值对（如 `LABEL "rating"="Five Stars"`）为映像添加自定义元数据标签，可通过 `docker inspect` 命令查看。
  * **USER**：指定容器运行时使用的系统用户。
    * *安全警告*：默认情况下容器以 **root** 用户身份运行。由于容器与底层系统共享内核，这存在潜在的安全隐患，建议尽可能修改为非特权用户。
  * **ENV**：设置容器内部的 shell 环境变量。
    * *逻辑脉络*：合理使用 `ENV` 有助于遵守 **DRY（Don't Repeat Yourself，不要重复自己）** 原则，使得路径或配置在后续脚本中可复用，减少输入错误。
  * **RUN**：在容器内执行系统命令，并将结果提交为新的映像层。
    * *易错细节/警告*：**切勿单独执行 `apt-get -y update`**。因为 Docker 的缓存机制会导致该层的包索引长期不更新，建议将其与安装命令合并（如 `RUN apt-get -y update && apt-get -y install supervisor`），以确保每次构建时获取最新的依赖包。
  * **ADD**：将宿主机的文件或目录复制到映像中，并具备自动解压归档文件的能力。
  * **WORKDIR**：更改容器内部的工作目录，类似于 `cd` 命令，后续的 `RUN` 等指令都会在这个新目录中执行。
  * **CMD**：指定启动容器时默认执行的进程或命令（例如 `CMD ["supervisord", "-n"]`）。
* **预留拓展补充空间**
  * > *[此处可补充：`ADD` 与 `COPY` 指令的核心区别，以及官方推荐在无需自动解压场景下优先使用 `COPY` 的最佳实践]*

```dockerfile
FROM node:20-alpine
LABEL maintainer="team@example.com"
ENV APP_HOME=/app
WORKDIR $APP_HOME
COPY package*.json ./
RUN npm ci --only=production
COPY . .
USER node
CMD ["node", "server.js"]
```

| 指令 | 作用 |
|------|------|
| FROM | 基础镜像 |
| COPY | 复制文件（优先于 ADD） |
| RUN | 构建时执行，产生新层 |
| ENV | 环境变量 |
| USER | 运行用户（建议非 root） |
| CMD | 容器启动默认命令 |

## 构建映像

* **核心主旨与实用要点**
  * 讲解如何通过 `docker build` 命令将 `Dockerfile` 及其上下文转化为可用的 Docker 映像，并探讨了缓存机制的影响。
* **核心知识点与运行逻辑**
  * **构建命令**：通常只需在包含 `Dockerfile` 的目录执行 `docker build -t <标签名> .` 即可完成构建。该过程会逐行执行指令，每成功执行一步都会生成一个新的临时映像层。
  * **.dockerignore 文件**：
    * *作用*：用于指定在构建时不想上传到 Docker 守护进程的文件和目录（例如 `.git` 目录）。
    * *因果关系*：因为构建时 Docker 会打包发送整个当前目录，使用该文件排除无用的大型文件，可以**极大节省传输时间和网络带宽**。
  * **缓存机制（Cache）**：
    * *逻辑脉络*：Docker 为了提升构建速度，会默认复用之前构建过的相同层（终端输出 `---> Using cache`）。
    * *易错细节*：有时缓存会导致未能拉取到最新的代码或安全补丁。如果想彻底禁用缓存进行干净构建，必须在命令中添加 `--no-cache` 选项。
* **预留拓展补充空间**
  * > *[此处可补充：多阶段构建（Multi-stage builds）的应用场景，如何通过多阶段构建大幅减小最终输出映像的体积]*

```bash
docker build -t myapp:1.0 .
docker build --no-cache -t myapp:1.0 .
```

```
# .dockerignore 示例
.git
node_modules
*.md
```

## 运行映像

* **核心主旨与实用要点**
  * 展示了在成功构建映像后，如何将其作为后台服务运行，并正确映射网络端口以提供外部访问。
* **操作指令与排障细节**
  * **端口绑定与后台运行**：使用 `docker run -d -p 8080:8080 <映像名>`。`-d` 使容器在后台运行，`-p` 将宿主机的 8080 端口映射到容器的 8080 端口。
  * **确认运行状态**：通过 `docker ps` 命令可查看当前正在运行的容器列表及其映射端口。
  * **获取宿主机 IP**：
    * *易错细节*：对于使用 Boot2Docker 或 Docker Machine 的非 Linux 用户，在浏览器中访问 `localhost:8080` 会失败，因为容器实际运行在虚拟机中。
    * *解决方案*：必须通过打印 `$DOCKER_HOST` 环境变量，或执行 `boot2docker ip` / `docker-machine ip <设备名>` 来获取真实的宿主机 IP 地址。
* **预留拓展补充空间**
  * > *[此处可补充：`docker logs -f <容器ID>` 命令的使用，以便在容器后台运行时实时追踪应用的输出日志]*

```bash
docker run -d -p 8080:8080 --name myapp myapp:1.0
docker ps
docker logs -f myapp
```

## 定制基础映像

* **核心主旨与实用要点**
  * 探讨了在特定场景下，摒弃通用操作系统的基础映像，从零开始（或使用极简环境）构建专属基础映像的优势。
* **核心结论与应用场景**
  * *常规情况*：大多数人倾向于使用精简的 Linux 发行版（如 Ubuntu、Fedora 或 CentOS）作为 `FROM` 的起点。
  * *定制优势（因果逻辑）*：对于静态编译的语言（如 C 或 Go），应用本身不需要依赖完整的 Ubuntu 发行版及其众多不必要的文件。直接定制基础映像或放入空映像中，可以**最大限度地减少映像的体积**，同时**降低潜在的攻击面**。
* **预留拓展补充空间**
  * > *[此处可补充：`FROM scratch` 指令的用法，以及基于 Alpine Linux 构建极小体积映像的实战对比]*

```dockerfile
# 多阶段构建示例（Go）
FROM golang:1.22 AS build
WORKDIR /src
COPY . .
RUN CGO_ENABLED=0 go build -o /app

FROM alpine:3.19
COPY --from=build /app /app
CMD ["/app"]
```

## 存储映像

* **核心主旨与实用要点**
  * 系统介绍了 Docker 映像的分发与存储机制，涵盖公开注册处、私有托管方案以及本地镜像缓存的配置。
* **详细知识点拆解**
  * **公开注册处**：
    * **Docker Hub**：官方提供的最大公开注册处，类似 GitHub，支持公开分享映像。
    * **Quay.io**：由 CoreOS 收购的注册处服务，提供类似 SaaS 的私有映像托管服务。
  * **私有注册处**：
    * 由于直接部署时拉取公网映像会受到网络延迟的严重影响，甚至因公网故障导致无法部署。很多公司选择使用开源的 `docker-registry` 部署内部专用的私有注册处。
  * **身份认证（.dockercfg）**：
    * 通过 `docker login` 登录注册处后，Docker 会在用户的主目录生成一个隐藏文件 `.dockercfg`。
    * *易错细节*：该文件以 **JSON 格式明文存储**登录凭据，因此其访问权限必须严格限制为 `0600`，以防止其他用户窃取凭证。退出登录（`docker logout`）会直接删除该凭证文件。
  * **配置本地守护进程镜像（Registry Mirror）**：
    * *逻辑脉络*：为了加速大批量节点的拉取速度，可以通过配置 Docker 守护进程参数 `--registry-mirror`，指向局域网内搭建的缓存注册处实例。
    * *性能数据*：在本地镜像服务缓存后，拉取同一个 CentOS 映像的时间可从 1 分 25 秒骤降至仅仅 **2 秒钟**。
  * **分发映像的其他方式**：
    * 除了标准的 Registry 协议，还可以使用 `docker save` 和 `docker load` 命令将映像导出为 tar 归档文件，并通过 Amazon S3（借助 `dogestry`）或 BT 种子（`torrent-docker`）进行离线/P2P分发。
* **预留拓展补充空间**
  * > *[此处可补充：现代企业级私有镜像仓库 Harbor 的核心优势（如 RBAC 权限控制、镜像漏洞扫描组件集成），以及 Docker 1.7 之后新的凭证存储机制（凭据助手 credential helpers）]*

```bash
docker tag myapp:1.0 registry.example.com/myapp:1.0
docker login registry.example.com
docker push registry.example.com/myapp:1.0

docker save myapp:1.0 -o myapp.tar
docker load -i myapp.tar
```

## 本章速记

| 概念 | 一句话 |
|------|--------|
| Dockerfile | 自动化构建镜像的配方 |
| RUN 合并 update | `update && install` 一行，防缓存过期 |
| COPY vs ADD | 无解压需求优先 COPY |
| .dockerignore | 减小 build context，加速构建 |
| 缓存 | 层不变则复用；`--no-cache` 干净构建 |
| docker build -t | 构建并打标签 |
| docker run -d -p | 后台运行 + 端口映射 |
| Registry | Hub 公开；企业用私有 Registry/Harbor |
| docker push/pull | 标准镜像分发方式 |
