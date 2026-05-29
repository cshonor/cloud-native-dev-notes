# 第2章：Actions 是如何工作的？(How Does Actions Work?)

## 2.1 概览 (An Overview)

* **核心主旨**：深入解析 GitHub Actions 的组成部分及各组件之间如何协同工作，建立对自动化系统流转的宏观认知。
* **核心知识点与关键定义**：
  * **Actions (大写 A，GitHub Actions)**：指代用于响应事件并执行自动化工作流的**整个系统或执行环境 (entire system)**。
  * **actions (小写 a)**：指代实现单个具体操作的**代码单元及相关底层组件 (units of code)**。
* **逻辑脉络与执行因果流**：
  * **触发流**：系统检测到匹配的**事件 (Event)** 发生 → 触发存储库中预先定义的**工作流 (Workflow)** → 工作流在被指定的**运行器 (Runner)** 上调度并分配**作业 (Jobs)** → 作业按顺序拆解为执行的**步骤 (Steps)** → 最终由步骤去调用预定义的**操作 (actions)** 或直接执行 OS Shell 命令。
* **拓展建议**：
  * 可延伸探讨多作业并发调度，以及 Runner 与 GitHub API 的通信机制（后端了解即可）。

```
Event → Workflow → Runner → Job(s) → Step(s) → action / shell
         ↑ 大写 Actions（系统）          ↑ 小写 actions（代码单元）
```

## 2.2 触发工作流 (Triggering Workflows)

* **核心主旨**：定义自动化流程的启动条件及事件的捕获与过滤机制。
* **核心知识点与语法要点**：
  * **事件 (Event)**：GitHub 存储库中发生的操作（如发起 Pull Request 或 Push 代码），是最常见的工作流触发来源。
  * **`on` 关键字**：用于 YAML 工作流语法中，声明工作流将要匹配并启动执行的**触发器类型及条件判定**。
* **易错细节与避坑指南**：
  * **默认分支隐性限制**：一小部分不常见的事件，**仅当工作流文件（YAML 文件）存在于存储库的默认分支（通常为 `main`）时，才会实际触发工作流的运行**。
  * **因果排查误区**：如果用户在一个非默认分支中开发此类特定触发器的工作流，并尝试触发对应事件，系统将不会有任何响应。在跨分支测试工作流逻辑且尚未合并到默认分支前，极易因不了解此规则而导致排查陷入僵局。
* **拓展补充**（第 8 章高级触发）：

```yaml
on:
  push:
    branches: [main]
    paths: ['src/**']
  pull_request:
  schedule:
    - cron: '0 8 * * 1'    # 每周一 08:00 UTC
  workflow_dispatch:       # 手动触发
```

## 2.3 组件 (Components)

* **核心主旨**：拆解构成 GitHub Actions 自动化管道的四大核心基础构件，明确其层级与语法结构。
* **核心层级与语法拆解**：
  * **步骤 (Steps)**：
    * **定义**：作业中执行的最小单元，直接与系统交互。
    * **语法规范**：在 YAML 列表中使用 `-` 标识步骤的开始。通过 `uses` 子句调用预定义的 action（例如 `actions/checkout@v4`）。通过 `with` 子句传递 action 所需的输入参数。通过 `run` 子句执行特定的 Shell 命令。可通过 `name` 字段为步骤设置高可读性的名称。
  * **运行器 (Runners)**：
    * **定义**：已经配置了与 GitHub Actions 系统交互协议的服务器（虚拟机、物理机）或容器。作业中的所有步骤均在其提供的操作系统环境中执行。
  * **作业 (Jobs)**：
    * **定义**：由按顺序排列的步骤序列组合而成。
    * **语法规范**：必须包含 `runs-on` 子句以明确声明运行当前作业所需的计算环境（如 `ubuntu-latest`），并包含具体的 `steps` 执行列表。
  * **工作流 (Workflow)**：
    * **定义**：类似于传统 CI 中的自动化管道。顶层定义事件触发规则，底层封装响应时所需执行的一系列作业。
* **拓展：多作业依赖与数据传递**：
  * 使用 `needs` 声明作业依赖顺序；跨作业数据通过 `outputs` + `needs.<job_id>.outputs` 传递（详见第 7 章）。

```yaml
name: CI Example
on: [push]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      - name: Run tests
        run: go test ./...

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - run: echo "deploy after build succeeds"
```

## 2.4 工作流执行 (Workflow Execution)

* **核心主旨**：利用 GitHub 原生提供的可视化界面追踪、监控及审查自动化工作流的实际运行状态。
* **实用要点与操作链路**：
  * **界面入口**：代码推送到存储库后，点击顶部导航栏的 **Actions 选项卡**，即可进入工作流执行的图形化监控平台。
  * **状态下钻逻辑**：
    1. 首先展示历史工作流运行（Workflow runs）的宏观列表。
    2. 点击特定的运行记录，可下钻查看该工作流中包含的各个**作业 (Jobs)** 的状态（显示成功或失败的标识）、执行时长等概要信息。
    3. 进一步点击特定作业，界面将展开显示该作业内每一个独立**步骤 (Steps)** 的实时控制台输出与执行日志。
* **拓展方向**（结合第 10 章）：
  * 通过 Actions 界面可下载构建制品、查看报错堆栈、**重新运行失败的作业 (Re-run jobs)**。

## 2.5 结论 (Conclusion)

* **重点结论**：
  * **术语的双重性辨析**：**Actions** 一词在语境中具有双重含义，既可以指代实现特定功能的代码块（action），也可以指代定义和执行这些操作的整个宏观自动化运行环境。
* **逻辑脉络关联**：
  * 本章通过明确工作流的结构组件与界面追踪逻辑，构建了自动化流程的骨架。这为下一章（Chapter 3）将视角从宏观转向微观，深入剖析单一 action 的内部构造（如 `action.yml` 元数据定义）奠定了基础。

## 本章速记

| 层级 | YAML 关键字 | 作用 |
|------|-------------|------|
| Workflow | `on`, `jobs` | 定义触发规则与作业集合 |
| Job | `runs-on`, `steps`, `needs` | 在 Runner 上执行步骤序列 |
| Step | `uses` / `run`, `with`, `name` | 调用 Action 或执行命令 |
| Action | `uses: org/repo@version` | 可复用的功能模块 |
