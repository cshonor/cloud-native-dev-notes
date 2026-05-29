# 第9章 通往生产环境的容器之路 (The Path to Production Containers)

> **版次说明**：中译/第一版常称「第7章 在生产环境中使用容器」，第二版目录为 **Ch 09**。  
> **后端学习提示**：本章 **浅看** 即可——理解「构建→测试→推送→部署」闭环、退出码判定、Compose 仅限单机测试；编排与调度交给 K8s / CI/CD，不必深挖 Centurion、Fleet 等历史工具。

## 部署

* **核心主旨与实用要点**
  * 阐述了 Docker 容器化模式如何彻底改变应用上线部署流程。如同现实中的「集装箱」统一定义了货运标准，Docker 规范了软件交付的标准格式，使得部署工作从零散繁琐的脚本堆砌，变为对目标服务器「交付完全不用关心容器里是什么的标准化构建产物」。
* **核心知识点与操作脉络**
  * **标准部署三步曲**：
    1. 在开发设备中构建并测试 Docker 映像。
    2. 构建正式用于测试和部署的映像。
    3. 把 Docker 映像部署到服务器。
  * **部署工具的两大硬性条件**：
    * **必须能重复执行**：保证每次部署动作具备幂等性和一致性。
    * **动态配置管理**：必须能为具体环境提供灵活的配置下发，且确保每次配置应用相同。
* **部署工具类别划分（重点结论）**：
  * **类别一：编排工具（Orchestration Tools）**
    * *定位*：代替传统的 Capistrano、Fabric 和 Shell 脚本。主要在多个 Docker 守护进程之间采用**异步方式**协调应用的配置和部署。
    * *优势*：对底层基础设施要求不高，开箱即用。
    * *代表工具*：New Relic 开发的 **Centurion**、Spotify 开发的 **Helios**、以及 Ansible for Docker。
  * **类别二：分布式调度程序（Distributed Schedulers）**
    * *定位*：把整个网络看作「一台大型电脑」。用户只需制定运行策略（如运行什么、运行多少个），调度程序自行决定分配到哪个健康的节点上运行。
    * *代表工具*：
      * **Fleet (CoreOS)**：结合 systemd 作为分布式初始化系统，需配合 etcd 使用。
      * **Kubernetes (Google)**：功能极强，提供丰富的 API，支持通过 Flannel 等搭建网络隔离，需依赖 etcd。
      * **Mesos (Apache)**：专为超大规模集群设计，作为底层资源池框架，通常结合 Marathon 或 Aurora 等调度器使用。
      * **Docker Swarm**：Docker 官方原生集群工具，将多个宿主机做成统一资源池。
* **后端拓展：为何 K8s 成为事实标准**
  * **声明式 vs 命令式**：Capistrano/Ansible 式工具是「执行一组步骤」；K8s 是「描述期望状态（Deployment YAML）」，控制器持续调和——更适合弹性扩缩、故障自愈。
  * **生态与 API**：统一的工作负载抽象（Pod/Deployment/Service）、Ingress、ConfigMap/Secret、HPA；云厂商与 GitOps（Argo CD）均围绕 K8s API。
  * **Swarm / Mesos 退场**：Swarm 与 Docker 引擎耦合深但功能薄；Mesos 通用资源层过重，Marathon 维护停滞。后端交付主线：**镜像 + Registry + K8s + CI/CD**。

```
开发机 docker build → CI 测试（同镜像）→ docker push Registry
                                              ↓
                         K8s pull 镜像 + ConfigMap/Secret 注入环境
```

| 工具类型 | 代表 | 后端现状 |
|----------|------|----------|
| Shell/编排脚本 | Capistrano, Ansible | 被 CI/CD + GitOps 取代 |
| 单机编排 | Docker Compose | **仅本地/单机集成测试** |
| 分布式调度 | **Kubernetes** | **生产标配** |
| 历史参考 | Swarm, Mesos, Fleet | 了解即可，新项目不选 |

## 测试容器

* **核心主旨与实用要点**
  * 强调「测试 Docker 化的应用不仅是测试代码本身，更是测试运行该代码的完整容器环境」。由于 Docker 保证了测试环境与生产环境底层依赖的绝对一致，能有效消除因底层库差异导致的「在我的电脑上能跑」的问题。
* **测试流程逻辑与详细步骤（前后因果）**
  * *流程触发*：代码提交触发构建流程，在本地完成 `docker build` 拿到最新映像。
  * *环境配置与执行（关键命令）*：使用提交的哈希值作为标签（Tag）定位映像，通过 `docker run` 注入测试专属的环境变量，并覆盖默认启动命令执行测试脚本。
    * *示例*：`docker run -e ENVIRONMENT=testing -e API_KEY=12345 -i -t awesome_app:version1 /opt/awesome_app/test.sh`。
  * *状态判定（易错细节）*：测试是否通过，**绝对不能仅凭肉眼看日志**。必须严格依赖 `docker run` 命令执行后的**系统退出码（Exit Code）**。如果脚本或测试框架返回 `0`，则代表成功；任何非 `0` 值均代表失败。
  * *交付流转*：只有测试成功后，才会执行 `docker tag` 打上正式标签（如 `latest`），并通过 `docker push` 推送至注册处供生产环境拉取。
* **重点结论与安全警告**
  * 这种把构建与测试严格绑定的流程，无法保证「修补底层操作系统漏洞」的速度。若需更新基础映像（如修补 OpenSSL 漏洞），整个流程必须重新走一遍，不能依赖在线热更新。

```bash
# 1. 用 commit SHA 打标签，便于追溯
docker build -t myapp:${GIT_SHA} .
# 2. 在容器内跑测试；退出码传给 Shell
docker run --rm \
  -e ENVIRONMENT=testing \
  -e DATABASE_URL=postgres://test@db:5432/test \
  myapp:${GIT_SHA} \
  /opt/myapp/run-tests.sh
echo $?   # 0 = 通过，非 0 = CI 应失败

# 3. 测试通过后再打发布标签并推送
docker tag myapp:${GIT_SHA} registry.example.com/myapp:1.2.3
docker push registry.example.com/myapp:1.2.3
```

```yaml
# .gitlab-ci.yml 片段：捕获 Docker 退出码
test:
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker run --rm $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA npm test
  # run 非 0 退出时 job 自动失败，无需额外判断
```

| 步骤 | 要点 |
|------|------|
| Tag | 用 `GIT_SHA` 或版本号，**生产不用 `latest` 做唯一标识** |
| `docker run` 测 | 覆盖 CMD 跑测试脚本 |
| 判定 | **看退出码**，不是看日志 |
| 基础镜像漏洞 | 重建基础镜像 → 全量重跑流水线 |

## 外部依赖

* **核心主旨与实用要点**
  * 探讨在容器自动化测试中，如何处理应用所依赖的外部服务（如数据库、缓存系统等）。
* **解决方案与逻辑脉络**
  * *测试环境方案*：为了防止测试环境对外部系统的干扰，推荐使用 **Docker Compose**（前身为 Fig）等工具。通过 Docker 的**链接机制（Links）**把测试容器和临时的数据库容器动态连接起来。
  * *局限性与警告（易错细节）*：
    * Docker 的原生链接机制**只能在一台物理宿主机上使用**。
    * *因果推导*：因为 Compose 依赖该链接机制，所以 **Docker Compose 只适合在开发和单机测试环境中使用，绝对不适合用于真实的分布式生产环境**。
  * *引出问题*：由于容器是一次性的且随时可能销毁，如果发生依赖故障或应用崩溃，传统的排错方式将难以适用，这就需要掌握更为深入的容器调试技巧（为 **Ch 07 Debugging** 做铺垫）。
* **后端拓展：Links 已被自定义网络取代**
  * 现代做法：Compose 里定义 `networks`，服务名即 DNS 主机名（如 `http://postgres:5432`），无需 `--link`。
  * 生产多机：用 K8s Service / Helm chart 拉起 DB sidecar 或指向托管 RDS，不用 Compose。

```yaml
# compose 示例：服务名 DNS 解析（现代写法，非 --link）
services:
  app:
    build: .
    environment:
      DATABASE_URL: postgres://user:pass@db:5432/app
    depends_on:
      - db
  db:
    image: postgres:16
    environment:
      POSTGRES_PASSWORD: pass
```

```bash
# 历史写法（书中 Links，已废弃，仅作对照）
docker run --link mydb:db -e DB_HOST=db myapp
```

| 场景 | 工具 | 说明 |
|------|------|------|
| 本地开发 + 单机集成测试 | Docker Compose | ✅ 标配 |
| 分布式生产 | Kubernetes | ✅ Service / Ingress |
| `--link` | 单机 legacy | ❌ 已废弃，用自定义 bridge 网络 |

## 本章速记

| 概念 | 一句话 |
|------|--------|
| 部署三步 | 构建测试 → 正式镜像 → 推到服务器/集群 |
| 部署工具要求 | 幂等可重复 + 环境配置一致 |
| 编排工具 | 多机异步部署，替代 Capistrano/Fabric |
| 分布式调度 | 声明策略，调度器选节点；**K8s 为现状标准** |
| 容器测试 | 测的是「代码 + 完整运行环境」 |
| 测试判定 | **`docker run` 退出码 0 才算过** |
| 漏洞修复 | 更新基础镜像 → 整条流水线重跑 |
| Compose + Links | **仅单机**；生产用 K8s，不用 Compose 扛分布式 |
| 现代网络 | 自定义网络 / Compose service 名 DNS，取代 `--link` |
