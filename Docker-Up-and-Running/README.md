# Docker Up & Running

《Docker 即学即用》**第三版**（14 章）学习笔记。

> **技术栈侧重**：PostgreSQL / pgvector / TimescaleDB + 容器化。  
> **后端定位**：会打包、能配合 K8s/CI/CD，不做专职运维。  
> **策略**：Ch 1～8 **必学**（含 Compose）；Ch 9 **精读**；Ch 10 **浅读**；Ch 11～14 按需/跳过。

---

## 笔记结构（一书一小节一文件）

每章目录：

```
chapter-08-docker-compose/
  README.md          ← 章索引（链到各小节）
  notes.md           ← 跳转说明
  sections/
    8.1-配置docker-compose.md
    8.2-启动服务.md
    ...
```

- **第三版有几个小节，就有几个 `.md` 文件**（如 8.5.1 / 8.5.2 / 8.5.3 各一篇）。
- 你粘贴某小节原文 → 只改对应 `sections/X.Y-*.md`，不整章重写。
- 书中尚无内容的小节标 **待补充**，发原文后可逐节填满。

---

| 章 | 标题 | 仓库文件夹 | 优先级 |
|----|------|------------|--------|
| 01 | 引言 | `chapter-01-introduction` | ✅ 必学 |
| 02 | Docker 概览 | `chapter-02-docker-landscape` | ✅ 必学 |
| 03 | 安装 Docker | `chapter-03-installing-docker` | ✅ 必学 |
| 04 | 使用 Docker 映像 | `chapter-04-docker-images` | ✅ 必学 ⭐ |
| 05 | 使用 Docker 容器 | `chapter-05-containers` | ✅ 必学 |
| 06 | 探索 Docker 的其他功能 | `chapter-06-exploring-docker` | ✅ 必学 |
| 07 | **调试容器** | `chapter-07-debugging` | ✅ 精读 |
| 08 | **探索 Docker Compose** | `chapter-08-docker-compose` | ✅ 必学 ⭐⭐⭐ |
| 09 | **在生产环境中部署容器** | `chapter-09-path-to-production` | ✅ 精读 |
| 10 | **容器弹性伸缩** | `chapter-10-docker-at-scale` | 🔄 浅读 |
| 11 | 高级话题 | `chapter-11-advanced-topics` | 🔄 选读 |
| 12 | 丰富的选择 | `chapter-12-expanding-landscape` | ⏭️ 跳过 |
| 13 | 容器平台设计 | `chapter-13-platform-design` | 🔄 通读 |
| 14 | 总结 | `chapter-14-conclusion` | 🔄 浏览 |

> 文件夹名沿用英文 slug；**书中章号 = 上表「章」列**（第三版已与文件夹 07～14 对齐）。

### 曾混淆的章号（以第三版为准）

| 内容 | 第三版正确章号 | 曾误记为 |
|------|----------------|----------|
| Docker Compose | **第 8 章** | 12 章版无专章 / 误为 Ch 3 |
| 生产部署 | **第 9 章** | 12 章版第 7 章 |
| 弹性伸缩（Swarm/K8s/ECS） | **第 10 章** | 12 章版第 9 章 |
| 高级话题（cgroup/安全） | **第 11 章** | 12 章版第 10 章 |
| 十二要素 / 响应式宣言 | **第 13 章** | 12 章版第 11 章 |

---

## 各章小节索引（第三版）

<details>
<summary>点击展开完整小节</summary>

**Ch 01 引言** — 1.1 希望 · 1.2 不是什么 · 1.3 术语 · 1.4 小结  
**Ch 02 概览** — 2.1 简化流程 · 2.2 广泛支持 · 2.3 架构 · 2.4 合理利用 · 2.5 工作流程 · 2.6 小结  
**Ch 03 安装** — 3.1 客户端 · 3.2 服务器 · 3.3 测试 · 3.4 探索服务器 · 3.5 小结  
**Ch 04 映像** — 4.1 Dockerfile · 4.2 构建 · 4.3 运行 · 4.4 定制基础 · 4.5 存储 · 4.6 优化 · 4.7 诊断构建 · 4.8 多架构 · 4.9 小结  
**Ch 05 容器** — 5.1～5.8 生命周期 · 5.9 Windows · 5.10 小结  
**Ch 06 探索** — 6.1～6.9 版本/info/pull/inspect/exec/logs/监控 · 6.10 Prometheus · 6.11～6.12  
**Ch 07 调试** — 7.1 进程 · 7.2 审查进程 · 7.3 管控 · 7.4 网络 · 7.5 映像历史 · 7.6 容器 · 7.7 文件系统 · 7.8 小结  
**Ch 08 Compose** — 8.1 配置 · 8.2 启动 · 8.3 Rocket.Chat · 8.4 命令 · 8.5 配置管理 · 8.6 小结  
**Ch 09 生产** — 9.1 部署 · 9.2 Docker 角色 · 9.3 DevOps 流水线 · 9.4 小结  
**Ch 10 伸缩** — 10.1 Swarm · 10.2 Kubernetes · 10.3 ECS/Fargate · 10.4 小结  
**Ch 11 高级** — 11.1 容器详解 · 11.2 安全 · 11.3 配置 · 11.4 存储 · 11.5 nsenter · 11.6 结构 · 11.7 替换运行时 · 11.8 小结  
**Ch 12 选择** — 12.1 nerdctl/podman/buildah · 12.2 Rancher/Podman Desktop · 12.3 小结  
**Ch 13 平台设计** — 13.1 十二要素 · 13.2 响应式宣言 · 13.3 小结  
**Ch 14 总结** — 14.1～14.7

</details>

---

## 分章学习建议（PostgreSQL 向）

| 章节 | 建议 |
|------|------|
| 1～6 | 必吃透：镜像、容器、`exec`、`logs`、卷 |
| **7 调试** | 精读：排障 PG 启动失败、挂载、网络 |
| **8 Compose** | **必学**：PG + pgvector 本地多服务编排 |
| **9 生产** | 精读：部署规范、CI/CD、上线验证 |
| **10 伸缩** | 浅读：Swarm/K8s/ECS 概念；实操见《K8s Up & Running》 |
| 11 高级 | 选读：安全、网络；cgroup/存储按需 |
| 12 | 跳过：podman/nerdctl 了解即可 |
| 13～14 | 通读/浏览：架构思维与全书回顾 |

---

## 补充材料

| 文件 | 内容 |
|------|------|
| [`chapter-08-docker-compose/`](chapter-08-docker-compose/) | 第 8 章，按 8.1～8.6（含 8.5.x）分文件 |
| [`supplement/compose-v2.md`](supplement/compose-v2.md) | 命令速查、pgvector 模板 |
| [`supplement/dockerfile-tips.md`](supplement/dockerfile-tips.md) | 多阶段构建、`.dockerignore` |

---

## 学习进度

| 章 | 文件夹 | 状态 |
|----|--------|------|
| 01 | chapter-01-introduction | ✅ 已完成 |
| 02 | chapter-02-docker-landscape | ✅ 已完成 |
| 03 | chapter-03-installing-docker | ✅ 已完成 |
| 04 | chapter-04-docker-images | ✅ 已完成 |
| 05 | chapter-05-containers | ✅ 已完成 |
| 06 | chapter-06-exploring-docker | ✅ 已完成 |
| 07 | chapter-07-debugging | ✅ 已完成（精读） |
| 08 | chapter-08-docker-compose | ✅ 已完成（必学） |
| 09 | chapter-09-path-to-production | 🔄 待按第三版 9.1～9.4 增补 |
| 10 | chapter-10-docker-at-scale | 🔄 待按第三版 10.2 K8s 增补 |
| 11 | chapter-11-advanced-topics | ✅ 已完成（选读） |
| 12 | chapter-12-expanding-landscape | ⏭️ 跳过 |
| 13 | chapter-13-platform-design | ⬜ 未开始 |
| 14 | chapter-14-conclusion | ⬜ 未开始 |

> 状态：⬜ 未开始 / 🔄 进行中 / ✅ 已完成 / ⏭️ 跳过  
> Ch 9、10 笔记基于旧版结构，与第三版小节部分重合；发原文后可逐节对齐。

---

## 学完你能做什么

- 给任意后端项目写 Dockerfile 并构建镜像
- 用 **Compose V2** 本地一键拉起 PG + pgvector / 多服务开发环境
- 排查容器日志、网络、挂载问题
- 推镜像到仓库，无缝衔接 K8s / GitHub Actions
