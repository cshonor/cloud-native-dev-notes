# Docker Up & Running

《Docker 即学即用》**第二版**（ISBN 9781492036722）学习笔记。

> **后端定位**：会打包、能配合 K8s/CI/CD，不做专职运维。  
> **策略**：正文 **第 1～8 章吃透**，第 9 章浅看，**第 10～14 章直接跳过**。

---

## 章节对照表（第二版原书 14 章）

| 章 | 原书目录 | 优先级 | 说明 |
|----|----------|--------|------|
| 01 | Introduction | ✅ **必学** | Docker 是什么、解决什么问题 |
| 02 | The Docker Landscape | ✅ **必学** | 镜像/容器/仓库生态，建立全局观 |
| 03 | Installing Docker | ✅ **必学** | 本地安装与验证 |
| 04 | Working with Docker Images | ✅ **必学** ⭐ | 镜像分层、拉取/推送、**Dockerfile 编写与 build** |
| 05 | Working with Docker Containers | ✅ **必学** | run/exec/logs、端口映射、**数据卷、基础网络**；CPU/内存限制小节浅看 |
| 06 | Exploring Docker | ✅ **必学** | inspect、stats、logs 等日常排查命令 |
| 07 | Debugging Containers | 🔄 **选学** | 容器排错思路，遇到问题时再翻 |
| 08 | Exploring Docker Compose | ✅ **必学** ⭐⭐⭐ | 本地编排后端 + DB + Redis，开发环境标配 |
| 09 | The Path to Production Containers | 🔄 **浅看** | 生产部署思路、registry 概念；不必实操 |
| 10 | Docker at Scale | ❌ **跳过** | Swarm / ECS / K8s 预览，交给《K8s Up & Running》 |
| 11 | Advanced Topics | ❌ **跳过** | 内核、cgroup、存储驱动、深度安全 |
| 12 | The Expanding Landscape | ❌ **跳过** | 生态扩展，与后端交付无关 |
| 13 | Container Platform Design | ❌ **跳过** | 平台架构设计，运维向 |
| 14 | Conclusion | ❌ **跳过** | 收尾，不用读 |

---

## 与你总结的对应关系

| 你的学习清单 | 对应章节 |
|--------------|----------|
| 容器原理、生态 | Ch 01～02 |
| 安装、基础命令 | Ch 03、05、06 |
| 镜像管理 | Ch 04 |
| Dockerfile | Ch 04 ⭐ |
| Docker Compose | Ch 08 ⭐⭐⭐ |
| 数据卷、持久化 | Ch 05 |
| 基础网络 | Ch 05 |
| 资源限制、健康检查 | Ch 05（浅看） |
| Swarm / 集群编排 | Ch 10（跳过） |
| 内核 / 存储驱动 / 安全加固 | Ch 11～13（跳过） |

---

## 第二版缺失内容补充（约 1 小时）

书本未覆盖、但后端必会的 2 点，见 `supplement/`：

| 文件 | 内容 |
|------|------|
| `supplement/compose-v2.md` | `docker-compose` → `docker compose` |
| `supplement/dockerfile-tips.md` | 多阶段构建、`.dockerignore` |

---

## 学习进度

| 章节文件夹 | 状态 |
|------------|------|
| chapter-01-introduction | 🔄 进行中 |
| chapter-02-docker-landscape | 🔄 进行中 |
| chapter-03-installing-docker | ⬜ 未开始 |
| chapter-04-docker-images | ⬜ 未开始 |
| chapter-05-containers | ⬜ 未开始 |
| chapter-06-exploring-docker | ⬜ 未开始 |
| chapter-07-debugging | ⬜ 未开始 |
| chapter-08-docker-compose | ⬜ 未开始 |
| chapter-09-path-to-production | ⬜ 未开始 |
| chapter-10-docker-at-scale | ⏭️ 跳过 |
| chapter-11-advanced-topics | ⏭️ 跳过 |
| chapter-12-expanding-landscape | ⏭️ 跳过 |
| chapter-13-platform-design | ⏭️ 跳过 |
| chapter-14-conclusion | ⏭️ 跳过 |

> 状态：⬜ 未开始 / 🔄 进行中 / ✅ 已完成 / ⏭️ 跳过

---

## 学完你能做什么

- 给任意后端项目写 Dockerfile 并构建镜像
- 用 Compose 本地一键拉起完整开发环境
- 推镜像到仓库，无缝衔接 K8s / GitHub Actions
