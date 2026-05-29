# 第4章：使用工作流 (Working with Workflows)

## 4.1 在存储库中创建第一个工作流 (Creating the First Workflow in a Repository)

* **核心主旨**：介绍如何在一个没有任何工作流的空存储库或现有项目中，通过 GitHub Web 界面从零开始或利用模板引导创建第一个自动化工作流。
* **核心知识点与关键定义**：
  * **入口与智能推荐**：点击存储库顶部的 **Actions 选项卡**，进入工作流引导页。GitHub 会自动扫描代码库语言（如 Go、Java），并在「建议 (Suggested)」区域推荐最匹配的入门工作流模板。
  * **四种创建途径**：
    1. 从零开始设置工作流 (set up a workflow yourself)。
    2. 使用 GitHub 建议的**入门工作流模板 (Starter Workflows)**。
    3. 从持续集成 (CI) 列表中选择其他模板。
    4. 选择其他类别（如部署 Deployment、安全 Security）的模板。
  * **模板语法结构解析（以基础 CI 为例）**：
    * `name`：工作流的名称。
    * `on`：定义触发条件（如对 `main` 分支的 `push` 或 `pull_request`）。
    * `workflow_dispatch`：允许从 Actions 界面**手动触发**运行。
    * `jobs` 与 `runs-on`：定义作业及所需的运行器（如 `ubuntu-latest`）。
    * `steps`：通过 `uses` 调用预定义操作，或通过 `run` 执行 Shell 脚本。
* **逻辑脉络与段落分层**：
  * **场景预设**：从一个没有任何 Actions 的简单项目出发。
  * **创建流程**：进入 Actions 页面 → 评估推荐模板 → 预览与配置模板 → 解析生成的 YAML 骨架代码。
* **易错细节**：
  * **手动触发的前提条件**：如果工作流包含 `workflow_dispatch` 触发器，该工作流文件**必须存在于默认分支（通常为 `main`）**上，界面才会显示「Run workflow」按钮。
* **拓展建议**：
  * 企业项目可自定义组织级别的入门工作流模板（结合第 12 章，后端可跳过）。

```yaml
# 基础 CI 骨架
name: CI
on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: go test ./...
```

## 4.2 提交初始工作流 (Committing the Initial Workflow)

* **核心主旨**：讲解在 Web 编辑器中保存工作流并将其提交到代码库的流程，以及如何利用 GitHub 原生 UI 监控执行状态、排查日志和管理历史运行记录。
* **核心知识点与关键定义**：
  * **提交流程 (Committing)**：像普通文件一样，通过「Commit changes」按钮将 YAML 文件提交到当前分支或创建新分支（引发 Pull Request）。
  * **界面导航与状态下钻**：
    * **宏观视图**：Actions 左侧边栏列出所有工作流，点击特定工作流可过滤右侧的运行历史。
    * **手动执行**：对于配置了 `workflow_dispatch` 的工作流，点击「Run workflow」可手动选择分支进行触发。
    * **运行详情 (Run Details)**：点击某次运行记录进入作业层级，再次点击作业名可查看每一步的详细控制台输出（包括环境准备、执行命令和耗时）。
  * **状态徽章 (Status Badge)**：提供工作流「通过/失败」的视觉指示，可通过界面生成 Markdown 代码并嵌入项目的 `README.md` 中，点击徽章可直接跳转至运行列表。
  * **重新运行 (Re-running)**：在运行记录页面的右上角，支持**重新运行所有作业 (Re-run all jobs)** 或**仅重新运行失败的作业 (Re-run failed jobs)**。
* **逻辑脉络与段落分层**：
  * **提交流程**：Web 编辑器操作 → 填写提交信息 → 选择目标分支 → 触发初次运行。
  * **查看与管理**：探索 Actions 仪表板 → 按分支/事件过滤 → 深入单次运行日志。
  * **PR 集成测试**：演示通过新分支发起 Pull Request，在合并前通过状态检查 (Checks) 验证工作流的过程。
* **易错细节与格式硬性规则**：
  * **文件路径强限制**：工作流文件**必须**保存在代码库的 `.github/workflows/` 目录下，修改此路径将导致 GitHub Actions 无法识别该文件。
  * **快捷编辑技巧**：在查看工作流文件源码时，可以通过按下键盘上的 `.` 键，直接在浏览器中唤起基于 VS Code 的集成编辑器。
* **拓展建议**：
  * 重新运行时可勾选 **Enable debug logging** 获取更详细底层日志（详见第 10 章）。

```markdown
<!-- README 状态徽章示例 -->
![CI](https://github.com/<owner>/<repo>/actions/workflows/ci.yml/badge.svg)
```

## 4.3 使用 VS Code GitHub Actions 扩展 (Using the VS Code GitHub Actions Extension)

* **核心主旨**：脱离浏览器，通过本地集成开发环境 (IDE) 中的官方插件实现工作流代码的高效编写、语法检查与运行监控。
* **核心知识点与功能拆解**：
  * **官方支持**：GitHub 官方提供的 VS Code 扩展（全面的工作流管理平台）。
  * **三大核心功能模块**：
    1. **运行监控**：可视化展示当前分支和存储库下的所有工作流及其历史运行记录。点击相应图标可在浏览器打开或直接在本地查看运行日志。
    2. **日志导航 (Explorer Outline)**：在本地查看日志时，提供结构化大纲 (Outline)，支持快速跳转至特定步骤的执行日志。
    3. **高级代码辅助**：
       * **上下文提示**：鼠标悬停在关键字上即可获得属性说明与文档帮助。
       * **语法验证 (Linting)**：实时检测 YAML 语法错误、缩进错误及无效键值。
       * **自动补全**：基于 Actions schema 提供可用参数和上下文变量的代码补全建议。
* **逻辑脉络与实用要点**：
  * **配置链路**：在 VS Code 插件市场搜索 `GitHub Actions` → 安装 → 授权 GitHub 账号读取权限 → 拉取代码并自动解析 `.github/workflows`。
  * **效率提升**：相较于 Web 盲写，插件通过「悬停查看 Action 源码」、「实时错误标注」极大地降低了配置复杂工作流时的试错成本。
* **拓展方向**：
  * 利用 IDE 自动补全快速引入经过组织认证的私有 Action，防止手写拼写错误。

## 4.4 结论 (Conclusion)

* **重点结论**：
  * GitHub 提供的 Web 界面打造了一个一站式的闭环体验，允许开发者**无需离开浏览器即可创建、编辑、执行和查阅工作流**。
  * **入门工作流模板**是降低学习曲线的利器，系统通过分析现有代码智能匹配配置，避免了从零手写 YAML 的繁琐。
* **前后因果关系**：
  * 本章解决了「如何将代码转化为可执行的自动化管道」这一实操问题。在掌握了工作流的编写与提交流程后，逻辑将自然过渡至下一章（第 5 章）：深入探讨这些代码实际执行的物理或虚拟计算环境——**运行器 (Runners)**。

## 本章速记

| 要点 | 说明 |
|------|------|
| 工作流路径 | 必须在 `.github/workflows/*.yml` |
| 创建入口 | 仓库 Actions 选项卡 → 模板或从零开始 |
| 手动触发 | 需 `workflow_dispatch` 且在默认分支 |
| 监控下钻 | Workflow run → Job → Step 日志 |
| 本地开发 | VS Code GitHub Actions 扩展（补全 + Lint） |
