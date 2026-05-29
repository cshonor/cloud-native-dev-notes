# Docker Up & Running

《Docker 即学即用》学习笔记。

> **版本说明**：你手上的版本为 **12 章结构**（非第二版 14 章通用目录）。**全书无独立 Docker Compose 章节**——书中仅零星提及，无系统教学；Compose 见下方「课外补漏」。  
> **技术栈侧重**：PostgreSQL / pgvector / TimescaleDB + 容器化。  
> **后端定位**：会打包、能配合 K8s/CI/CD，不做专职运维。

---

## 核心结论（先看这个）

| 问题 | 答案 |
|------|------|
| 为什么找不到 Compose？ | **本书根本没有 Compose 专章**，不要继续在书里找 |
| 第 7 / 8 / 9 章是什么？ | **生产部署** → **调试容器** → **大规模编排（Swarm/ECS）** |
| Compose 怎么学？ | **脱离本书**，学 [Docker 官方 Compose 文档](https://docs.docker.com/compose/) + `supplement/compose-v2.md` |
| 集群编排要不要深学？ | 现阶段 **浅读/跳过** Ch 9；单机 PG + 少量容器为主 |

---

## 章节对照表（你的 12 章 ↔ 仓库文件夹）

| 你的章节 | 原书目录 | 仓库文件夹 | 优先级 | 说明 |
|----------|----------|------------|--------|------|
| 01 | 引言 | `chapter-01-introduction` | ✅ **必学** | Docker 是什么、解决什么问题 |
| 02 | Docker 概览 | `chapter-02-docker-landscape` | ✅ **必学** | 生态、架构、工作流程 |
| 03 | 安装 Docker | `chapter-03-installing-docker` | ✅ **必学** | 安装与验证 |
| 04 | 使用 Docker 映像 | `chapter-04-docker-images` | ✅ **必学** ⭐ | Dockerfile、build、push |
| 05 | 使用 Docker 容器 | `chapter-05-containers` | ✅ **必学** | 生命周期、卷、基础网络 |
| 06 | 探索 Docker 的其他功能 | `chapter-06-exploring-docker` | ✅ **必学** | inspect、exec、logs、stats |
| 07 | **在生产环境中使用容器** | `chapter-09-path-to-production` | ✅ **精读** | 部署规范、上线测试；PG 容器上线重点 |
| 08 | **调试容器** | `chapter-07-debugging` | ✅ **精读** | ps/inspect/网络/文件系统；排障 PG 刚需 |
| 09 | **大规模使用 Docker** | `chapter-10-docker-at-scale` | 🔄 **浅读/跳过** | Swarm、Centurion、ECS；了解即可 |
| 10 | 高级话题 | `chapter-11-advanced-topics` | 🔄 **选读** | 网络、安全精读；存储驱动/cgroup 按需 |
| 11 | 自己设计…线上平台 | `chapter-13-platform-design` | 🔄 **通读** | 十二要素、响应式宣言；架构思维 |
| 12 | 总结 | `chapter-14-conclusion` | 🔄 **浏览** | 全书回顾、最佳实践闭环 |
| — | *(12章版无；第三版 Ch3+8.4/8.5)* | `chapter-08-docker-compose` | ✅ **必学** ⭐⭐⭐ | Compose V2；见 `notes.md` + `supplement/` |

> 文件夹编号按第二版英文目录命名，与书中章号不完全一致；上表为权威对照。

---

## 分章学习建议（PostgreSQL 向）

### 第 1～6 章（基础核心，必吃透）

镜像、容器生命周期、`exec` 进入容器、`logs` 日志、启停与清理——后续操作 PG 容器高频使用。

### 第 7 章 生产环境（精读）

容器部署与上线测试 → 适配 PostgreSQL、pgvector、TimescaleDB 打包容器上线。

### 第 8 章 调试（精读）

`docker ps` / `inspect` / 网络 / 镜像历史 / 文件系统 → 排查 PG 启动失败、连接异常、挂载问题。

### 第 9 章 大规模（浅读/跳过）

Swarm、云容器服务 → 单机/少量容器阶段用不到，仅建立概念。

### 第 10～12 章（收尾）

- **Ch 10**：网络、安全小节值得精读；内核/cgroup 想会用可略读
- **Ch 11**：十二要素、响应式宣言，快速通读
- **Ch 12**：总结浏览，知识闭环

---

## 课外补漏（书中缺失，必学）

| 文件 | 内容 |
|------|------|
| [`chapter-08-docker-compose/notes.md`](chapter-08-docker-compose/notes.md) | 第三版 Compose 完整笔记（配置、健康检查、命令、.env） |
| [`supplement/compose-v2.md`](supplement/compose-v2.md) | 速查：命令对照、pgvector 一键模板 |
| [`supplement/dockerfile-tips.md`](supplement/dockerfile-tips.md) | 多阶段构建、`.dockerignore` |

---

## 整体学习顺序（执行版）

1. **收尾本书**：10 → 11 → 12，Ch 10 抓**网络、安全**
2. **脱离本书**：系统学 **Docker Compose V2**（`supplement/compose-v2.md` + 官方文档）
3. **Compose 实操**：单 PG → PG + TimescaleDB → 多服务联动
4. **主线回归**：PostgreSQL + 时序/向量插件

---

## 学习进度

| 章节文件夹 | 书中章 | 状态 |
|------------|--------|------|
| chapter-01-introduction | 01 | ✅ 已完成 |
| chapter-02-docker-landscape | 02 | ✅ 已完成 |
| chapter-03-installing-docker | 03 | ✅ 已完成 |
| chapter-04-docker-images | 04 | ✅ 已完成 |
| chapter-05-containers | 05 | ✅ 已完成 |
| chapter-06-exploring-docker | 06 | ✅ 已完成 |
| chapter-09-path-to-production | **07** | ✅ 已完成（精读） |
| chapter-07-debugging | **08** | ✅ 已完成（精读） |
| chapter-10-docker-at-scale | **09** | ✅ 已完成（浅读） |
| chapter-11-advanced-topics | **10** | ✅ 已完成（选读） |
| chapter-13-platform-design | **11** | ⬜ 未开始 |
| chapter-14-conclusion | **12** | ⬜ 未开始 |
| chapter-08-docker-compose | *(第三版课外)* | ✅ 已完成（必学） |

> 状态：⬜ 未开始 / 🔄 进行中 / ✅ 已完成 / ⏭️ 跳过

---

## 学完你能做什么

- 给任意后端项目写 Dockerfile 并构建镜像
- 用 **Compose V2** 本地一键拉起 PG + pgvector / 多服务开发环境
- 排查容器日志、网络、挂载问题
- 推镜像到仓库，无缝衔接 K8s / GitHub Actions
