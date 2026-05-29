# 第8章：管理工作流执行 (Managing Workflow Execution)

> **后端学习提示**：本章为**选学**，用到再查。日常开发优先掌握 `paths`/`branches` 过滤、`workflow_dispatch`、Job 依赖；矩阵构建和并发控制按需学习。

## 8.1 从更改中进行高级触发 (Advanced Triggering from Changes)

* **核心主旨**：GitHub Actions 的工作流在本质上是**声明式 (declarative)** 而非命令式的，但在基础事件触发之外，系统提供了丰富的过滤器与活动类型，以便精确控制工作流的执行时机与边界。
* **核心知识点与关键定义**：
  * **基于活动类型的触发 (Triggering Based on Activity Types)**：允许用户指定对象上发生何种类型的操作时才触发工作流。例如，针对 `issues` 事件，可以通过 `types: [opened, edited, closed]` 明确仅在问题新建、编辑或关闭时运行。
  * **使用过滤器细化触发 (Using Filters to Refine Triggers)**：支持基于路径 (`paths`, `paths-ignore`)、分支 (`branches`, `branches-ignore`) 和标签 (`tags`, `tags-ignore`) 进行模式匹配过滤。
* **逻辑脉络与执行因果流**：
  * **过滤评估逻辑**：分支和标签的过滤模式会严格针对 Git 结构中的 `refs/heads` 进行匹配求值。
* **易错细节与格式硬性规则**：
  * **互斥规则**：不能对同一个事件同时使用包含 (inclusive) 和排除 (exclusive) 关键字。例如，**绝对不能**在同一个 `push` 触发器中同时声明 `branches` 和 `branches-ignore`。
  * **路径过滤的盲区**：针对标签 (Tags) 的推送操作，系统**不会**评估路径过滤器 (Path filters)。

```yaml
on:
  push:
    branches: [main, develop]
    paths:
      - 'src/**'
      - 'go.mod'
  pull_request:
    paths-ignore:
      - 'docs/**'
  issues:
    types: [opened, closed]
```

## 8.2 无更改触发工作流 (Triggering Workflows Without a Change)

* **核心主旨**：在代码或仓库未发生直接变更的情况下，通过外部系统调用或人工干预来启动自动化流程。
* **关键定义与核心机制**：
  * **`repository_dispatch`**：主要用于响应 GitHub 外部发生的特定活动，允许通过外部 CI/CD 进程等发起请求，从而在目标仓库中一次性调用一个或多个工作流。
  * **`workflow_dispatch`**：专门用于触发单个特定工作流的机制。配置此触发器后，允许通过 GitHub Actions 可视化选项卡、GitHub CLI 工具或 REST API **手动触发**执行。
* **易错细节与触发前提**：
  * 若要使 `workflow_dispatch` 的「运行工作流 (Run workflow)」按钮在 GitHub 界面上可见，该工作流文件**必须存在于默认分支 (通常为 `main`) 中**。

```yaml
on:
  workflow_dispatch:
    inputs:
      environment:
        description: 'Deploy target'
        required: true
        default: 'staging'
        type: choice
        options: [staging, production]
```

## 8.3 处理并发 (Dealing with Concurrency)

* **核心主旨**：对同一工作流或作业的多次重复触发进行并行控制，避免资源争抢和重复部署。
* **逻辑脉络与调度机制**：
  * 在作业或工作流级别添加 **`concurrency`** 子句并指定一个并发组名称（如 `concurrency: release-build`）。
  * **因果调度规则**：当带有该并发组声明的新实例被触发时，如果当前已有同一组的实例在运行或挂起：
    1. 新实例将被标记为**挂起 (pending)**。
    2. 如果之前已经存在一个处于挂起状态的同一组实例，该旧的挂起实例将被立即**取消 (cancelled)**。
* **重点结论与依赖隔离**：
  * 当一个作业因并发规则被取消时，任何依赖于该作业的下游作业都不会运行；但同一工作流中**未依赖该被取消作业的其他独立作业仍可继续运行**。

```yaml
concurrency:
  group: deploy-${{ github.ref }}
  cancel-in-progress: true   # 新部署取消旧部署
```

## 8.4 使用矩阵运行工作流 (Running a Workflow with a Matrix)

* **核心主旨**：通过声明多维度的数据集合，自动化地横向生成和调度多个同构作业，极大简化跨环境（如跨浏览器、多操作系统版本）的重复构建配置。
* **关键定义与层级结构**：
  * 在工作流中通过 **`strategy: matrix:`** 声明矩阵策略。
  * **一维矩阵 (One-Dimensional Matrices)**：例如定义一个 `product` 数组，包含 `prod1` 和 `prod2`，系统将动态生成 2 个独立的作业。
  * **多维矩阵 (Multi-dimensional Matrices)**：如果同时定义 `product`（2 个值）和 `level`（3 个值），系统将计算笛卡尔积，自动派生出 6 个并行的组合运行作业。
* **异常控制与逻辑脉络**：
  * **处理失败情况 (Continue on Error)**：默认行为下（`fail-fast: true`），如果矩阵生成的任何一个作业失败，所有剩余的待处理或运行中的矩阵作业将被取消。
  * 通过设置 **`continue-on-error: true`**（或将 `fail-fast` 设为 `false`），可以强制允许矩阵处理忽略单个作业的失败，继续遍历执行剩余的组合。
* **拓展方向**：
  * 第 12、13 章将深入探讨 `include` 添加特定组合，或 `exclude` 排除不需要的矩阵变量交集。

```yaml
strategy:
  fail-fast: false
  matrix:
    go-version: ['1.21', '1.22']
    os: [ubuntu-latest, windows-latest]
```

## 8.5 工作流函数 (Workflow Functions)

* **核心主旨**：在声明式工作流中引入内置的动态计算、字符串处理和状态判断能力，用于变量检查和执行路径分支。
* **公式要点与常用内置函数**：
  * **数据检查与格式化**：
    * `contains(search, item)`：判断字符串或数组是否包含某项。
    * `startsWith()` / `endsWith()`：判断前缀或后缀。
    * `format()` / `join()`：字符串格式化与拼接。
  * **数据转换与摘要**：
    * `fromJSON(value)`：将字符串转换为 JSON 对象或布尔值、整数等数据类型。
    * `toJSON(value)`：将变量或上下文对象转换为格式化的 JSON 字符串输出。**实用要点**：调试时可将 `github` 或 `steps` 上下文完整转储到日志。
    * **`hashFiles(path)`**：返回指定路径匹配文件的哈希摘要。通常用作缓存键 (Cache key)。
  * **条件与状态函数 (Conditionals and Status Functions)**：
    * 通过 `if` 关键字结合状态函数控制执行流（例如 `runner.os != 'Windows'` 或 `github.ref == 'refs/heads/test'`）。
    * 内置状态控制核心：
      * **`success()`**：前置步骤均成功时执行（默认隐式行为）。
      * **`always()`**：无论前置状态如何始终执行（易造成非预期执行，需谨慎使用）。
      * **`cancelled()`** / **`failure()`**：仅在被取消或发生错误时介入执行。
* **易错细节与边界限制**：
  * **超时控制 (`timeout-minutes`)**：工作流作业的默认最大运行时间设定为 **360 分钟**。
  * **凭证生命周期短板**：注入环境的 **`GITHUB_TOKEN`** 具有绝对的生命周期上限，最大过期时间为 **24 小时**。如果自定义的超时时间过长，Token 的过期可能会成为导致作业突然中断的隐性决定因素。

```yaml
- name: Debug context
  run: echo '${{ toJSON(github) }}'

- name: Cache key
  uses: actions/cache@v4
  with:
    path: ~/.cache/go-build
    key: ${{ runner.os }}-go-${{ hashFiles('**/go.sum') }}
```

## 8.6 结论 (Conclusion)

* **重点结论**：本章从矩阵生成、外部调度分发到精准的状态和并发控制，提供了掌控工作流执行流的核心进阶工具。这标志着基础构建模块部分的结束，为后续应对复杂环境中的安全性分析和底层故障监控奠定了技术实现的基础。

## 本章速记

| 主题 | 后端常用场景 |
|------|-------------|
| `paths` / `branches` 过滤 | 仅后端代码变更时跑 CI |
| `workflow_dispatch` | 手动触发部署 |
| `concurrency` | 防止重复部署互相覆盖 |
| `matrix` | 多 Go/Java 版本测试 |
| `hashFiles` | 缓存依赖键 |
| `if: failure()` | 失败时发通知 |
