# Learning GitHub Actions

《Learning GitHub Actions》（Brent Laster，ISBN 9781098131067）学习笔记。

> **后端定位**：代码检查、单测、镜像构建推送、K8s 自动部署；能搭完整 CI/CD 流水线。  
> **不做**：私有 Runner 集群、组织级权限体系、企业 CI 平台运维。

---

## 学习模块对照表（按后端场景）

### 🔴 必学 — 全部要实操落地

| 你的学习目标 | 对应原书章节 | 核心内容 |
|--------------|-------------|----------|
| Workflow/Job/Step/Action 概念 | **Ch 01** The Basics | 触发事件、`.github/workflows/` |
| 工作流执行机制 | **Ch 02** How Does Actions Work | 触发器、组件、执行流程 |
| 使用公开 Action | **Ch 03** What's in an action | Marketplace、`uses:` 引用 |
| 编写 Workflow YAML ⭐ | **Ch 04** Working with Workflows | 第一个 workflow、提交触发 |
| 环境变量 & Secrets ⭐⭐ | **Ch 06** Workflow Environments | `env`、`secrets`、权限 |
| 密钥安全管理 | **Ch 09** Actions and Security | Secrets 最佳实践、Token |
| 流水线调试 | **Ch 10** Monitoring & Debugging | 日志、重跑、定位失败步骤 |

> **Ch 05 Runners**：了解 GitHub-hosted runner 即可；自建 Runner **跳过**。

### 🟡 选学 — 复杂流程再用

| 学习目标 | 对应原书章节 |
|----------|-------------|
| Job 依赖、并行编排 | Ch 08 Workflow Execution |
| Matrix 多版本构建 | Ch 08 Workflow Execution |
| 依赖缓存加速 | Ch 07 Managing Data（cache） |
| 制品归档 / Release | Ch 07 Managing Data（artifacts） |
| Workflow 中用 Docker 容器 | Ch 13 Advanced Techniques |
| 可复用 Workflow | Ch 12 Advanced Workflows |

### ⚫ 跳过 — 平台运维向

| 内容 | 对应原书章节 |
|------|-------------|
| 自建 Runner 集群、自动扩缩 | Ch 05 Runners（自托管部分） |
| 自定义 Action 开发发布 | Ch 11 Custom Actions |
| 企业级可复用 Workflow 模板 | Ch 12 Advanced Workflows |
| 从 Jenkins/GitLab 迁移 | Ch 14 Migrating |

---

## 章节对照表（原书 14 章）

| 章 | 原书目录 | 优先级 |
|----|----------|--------|
| 01 | The Basics | ✅ **必学** |
| 02 | How Does Actions Work? | ✅ **必学** |
| 03 | What's in an action? | ✅ **必学** |
| 04 | Working with Workflows | ✅ **必学** ⭐⭐ |
| 05 | Runners | 🔄 浅看（hosted）；自托管 ❌ 跳过 |
| 06 | Managing Your Workflow Environments | ✅ **必学** ⭐⭐ |
| 07 | Managing Data Within Workflows | 🔄 选学（cache/artifacts） |
| 08 | Managing Workflow Execution | 🔄 选学（matrix/并发） |
| 09 | Actions and Security | ✅ **必学** ⭐ |
| 10 | Monitoring, Logging, and Debugging | ✅ **必学** |
| 11 | Creating Custom actions | ❌ 跳过 |
| 12 | Advanced Workflows | ❌ 跳过 |
| 13 | Advanced Workflow Techniques | 🔄 选学（容器步骤） |
| 14 | Migrating to GitHub Actions | ❌ 跳过 |

---

## 后端极简学习路线

```
Ch 01～04（概念+写 YAML）→ Ch 06+09（Secrets）→ Ch 10（调试）
→ supplement 实操：测试 → 构建镜像 → 推送 → kubectl 部署 K8s
```

| 顺序 | 任务 | 产出 |
|------|------|------|
| 1 | 读 Ch 01～04 | 能写触发 push 的基础 workflow |
| 2 | 读 Ch 06、09 | 配置仓库 Secrets，不写死密码 |
| 3 | 实操 `ci-test.yaml` | push 自动跑单测 |
| 4 | 实操 `docker-build-push.yaml` | 自动构建并推送镜像 |
| 5 | 实操 `k8s-deploy.yaml` | 完整链路：代码 → 镜像 → K8s |
| 6 | 读 Ch 10 | 流水线失败能看日志定位 |

---

## 必做实操清单

- [ ] 编写 workflow：`push` → 安装依赖 → 运行单元测试
- [ ] 增加步骤：构建 Docker 镜像 → 推送到镜像仓库
- [ ] 配置 `KUBE_CONFIG` Secret，执行 `kubectl apply` 更新 Deployment
- [ ] 故意让某步失败，练习从 Actions 日志定位问题

---

## Workflow 模板（`supplement/`）

| 文件 | 用途 |
|------|------|
| `ci-test.yaml` | 代码拉取 + 单测 |
| `docker-build-push.yaml` | 构建镜像 + 推送 GHCR |
| `k8s-deploy.yaml` | 完整 CI/CD：测试 → 镜像 → K8s 部署 |

### 需要配置的 Secrets

| Secret | 用途 |
|--------|------|
| `KUBE_CONFIG` | Base64 编码的 kubeconfig（K8s 部署） |
| `GITHUB_TOKEN` | 默认提供，推送 GHCR 时可用 |

---

## 学完后端能力自检

- [ ] 搭建从代码提交到 K8s 部署的全自动流水线
- [ ] 提交代码自动跑测试、打包镜像、更新服务
- [ ] 合理管理 Secrets，无硬编码凭据
- [ ] 能调试流水线报错，读懂失败步骤日志

---

## 学习进度

| 章节文件夹 | 状态 |
|------------|------|
| chapter-01-the-basics | 🔄 进行中 |
| chapter-02-how-actions-work | 🔄 进行中 |
| chapter-03-whats-in-an-action | 🔄 进行中 |
| chapter-04-working-with-workflows | 🔄 进行中 |
| chapter-05-runners | 🔄 进行中（托管 Runner 必看，自托管跳过） |
| chapter-06-workflow-environments | 🔄 进行中 |
| chapter-07-managing-data | 🔄 进行中 |
| chapter-08-workflow-execution | 🔄 进行中（选学） |
| chapter-09-security | 🔄 进行中 |
| chapter-10-monitoring-debugging | ⬜ 未开始 |
| chapter-11-custom-actions | ⏭️ 跳过 |
| chapter-12-advanced-workflows | ⏭️ 跳过 |
| chapter-13-advanced-techniques | ⬜ 未开始 |
| chapter-14-migrating | ⏭️ 跳过 |

> 状态：⬜ 未开始 / 🔄 进行中 / ✅ 已完成 / ⏭️ 跳过
