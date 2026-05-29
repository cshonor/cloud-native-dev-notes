# Cloud Native Dev Notes

云原生学习笔记仓库：Docker、Kubernetes、Nginx、GitHub Actions 的系统化学习记录与可运行示例。

## 书单

| 书名 | 目录 | 说明 |
|------|------|------|
| 《Docker 即学即用》第二版 | `docs/docker-up-running/` | 容器基础、镜像、网络、编排入门 |
| 《Kubernetes Up & Running》 | `docs/k8s-up-running/` | K8s 核心概念与生产实践 |
| 《Nginx 经典实例（NGINX Cookbook）》 | `docs/nginx-cookbook/` | 反向代理、负载均衡、性能调优 |
| Learning GitHub Actions | `docs/github-actions/` | CI/CD 工作流与自动化 |

## 学习路线

```
Docker 基础 → Docker Compose → Kubernetes 入门 → K8s 进阶
     ↓              ↓                ↓
  Nginx 配置    GitHub Actions    full-pipeline 端到端串联
```

1. **阶段一：容器化** — 阅读 Docker 笔记，动手 `code/docker/` 示例
2. **阶段二：编排** — K8s 笔记 + `code/kubernetes/` 清单部署
3. **阶段三：网关** — Nginx 笔记 + `code/nginx/` 配置实践
4. **阶段四：自动化** — Actions 笔记 + `code/github-actions/` 工作流
5. **阶段五：串联** — `code/full-pipeline/` 端到端 CI/CD 案例

## 目录结构

```
cloud-native-dev-notes/
├── docs/           # 按书本分章的 Markdown 笔记
├── code/           # 可运行代码、配置、YAML
├── cheatsheet/     # 命令与配置速查表
├── supplement/     # Docker 第二版缺失特性补充
└── troubleshoot/   # 踩坑与排错记录
```

## 环境准备

### 必备工具

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)（含 Compose V2）
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- 本地 K8s：`minikube` / `kind` / Docker Desktop Kubernetes 任选其一
- [Nginx](https://nginx.org/en/download.html)（或通过 Docker 运行）
- [Git](https://git-scm.com/) + GitHub 账号

### 推荐版本

| 工具 | 最低版本 |
|------|----------|
| Docker Engine | 24.x+ |
| Docker Compose | V2 |
| kubectl | 1.28+ |
| Kubernetes | 1.28+ |

### 快速验证

```bash
docker --version
docker compose version
kubectl version --client
nginx -v   # 可选
```

## 使用说明

- 笔记统一放在 `docs/<书名>/chapter-XX/`，每章一个或多个 `.md` 文件
- 可运行示例放在 `code/` 对应子目录，与笔记章节对应
- 日常查阅用 `cheatsheet/`，遇到问题先查 `troubleshoot/`
- Docker 新版特性（BuildKit、buildx 等）见 `supplement/`
