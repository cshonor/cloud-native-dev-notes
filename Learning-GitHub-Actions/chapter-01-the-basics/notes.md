# 第1章：基础知识 (The Basics)

## 1.1 什么是 GitHub Actions？ (What Is GitHub Actions?)

* **核心主旨**：GitHub Actions 是一个直接内置且由 GitHub 托管与管理的**自动化平台 (Automation Platform)** 与**执行框架 (Framework)**，旨在帮助开发者直接在代码仓库环境中实现软件交付生命周期（如 CI/CD）的自动化。
* **核心知识点与关键定义**：
  * **自动化平台 (Automation Platform)**：允许用户定义在特定事件发生时（如代码推送 Push、拉取请求 Pull Request 或审查更新），系统应自动执行的响应流程。例如：当代码被推送到分支时，自动抓取最新代码并尝试构建；若失败则更新 issue。
  * **执行框架 (Framework)**：一套由核心组件构成的系统，可以组合起来执行从简单的验证到复杂的流水线任务。所有的自动化逻辑都作为代码（as code）直接存储在 GitHub 的代码仓库中。
* **逻辑脉络与执行因果流**：
  * **触发因果**：代码仓库发生匹配的**事件 (Event)** → 触发代码仓库中定义的**工作流 (Workflow)** → 工作流在指定的**运行器 (Runner)** 上调度并执行**作业 (Jobs)** → 作业按顺序分解为执行的具体**步骤 (Steps)** → 步骤实际调用预定义的**操作 (Actions)** 或是直接运行 OS Shell 命令。
* **拓展建议**：
  * 对比 GitHub Actions 内置执行模型与传统外部 CI/CD 服务器（如 Jenkins、Travis CI）的架构差异：Actions 与代码仓库同域，无需额外维护 CI 服务器；外部 CI 通常更灵活但集成与运维成本更高。

```
Event → Workflow → Job(s) → Step(s) → Action / Shell
```

## 1.2 GitHub Actions 的用例有哪些？ (What Are the Use Cases for GitHub Actions?)

* **核心主旨**：虽然最常见的场景是持续集成与交付 (CI/CD)，但 Actions 实际上可用于自动化几乎任何开发流程。用户可以通过使用**入门工作流 (Starter Workflows)** 和 **操作市场 (Actions Marketplace)** 来快速引导和构建功能。
* **关键定义（核心概念辨析）**：
  * **工作流 (Workflows)**：控制 GitHub Actions 中自动化活动执行流程与顺序的**脚本或管道 (scripts or pipelines)**。
  * **操作 (Actions)**：在工作流步骤中被调用的**独立功能单元或模块**，用于执行具体的针对性任务（例如：检出代码）。
* **实用要点与核心资源提取**：
  * **入门工作流 (Starter Workflows)**：创建新工作流时，GitHub 提供的开箱即用模板，分类包括：持续集成 (CI)、部署 (Deployment)、安全 (Security)、自动化 (Automation) 以及 GitHub Pages 配置等。
  * **操作市场 (Actions Marketplace)**：一个提供海量现有且**免费**操作的组件库（类似于应用程序的插件库）。涵盖的分类如 IDE 交互、本地化任务、移动端开发以及与 JIRA 等项目管理工具的集成等。使用市场操作可免去从头编码的精力。
* **逻辑脉络与触发场景**：
  * 除了响应 GitHub 内部事件外，工作流还可以被外部环境事件触发、基于时间表（Schedule）定时运行，或者通过 GitHub 界面**手动启动**。

```yaml
# 常见触发方式示例
on:
  push:
    branches: [main]
  pull_request:
  schedule:
    - cron: '0 2 * * 1'
  workflow_dispatch:
```

## 1.3 涉及哪些成本？ (What Costs Are Involved?)

* **核心主旨**：GitHub Actions 采用基础免费与按量计费结合的模式。公共仓库完全免费，私有仓库提供一定免费额度（存储空间与运行器分钟数），超额后严格按照系统类型收取阶梯费用。
* **核心概念与易错细节**：
  * **制品 (Artifacts)** 与 **包 (Packages)** 的严格区别：
    * **制品 (Artifacts)** 是工作流执行期间生成或上传的对象，仅用于作业流转，**不收取额外的数据传输（流量）费用**。
    * **GitHub Packages** 用于对外提供标准的包或容器下载服务，**会单独计收数据传输费用**。
* **案例数据与公式要点（成本计算逻辑）**：
  * **存储成本**：超额后的存储（制品及 Packages）通常计费为 **$0.25/GB**。
  * **运行时间成本公式**：`实际消耗分钟数 × 操作系统乘数`。
  * **操作系统阶梯费率（关键数据）**：
    * **Linux**：计费乘数 **1**，基础费率 **$0.008/分钟**。
    * **Windows**：计费乘数 **2**，基础费率 **$0.016/分钟**。
    * **macOS**：计费乘数 **10**，基础费率 **$0.08/分钟**。
* **拓展建议**：
  * 针对分钟消耗过快的痛点，可延伸引入第 5 章的内容，探讨企业如何通过搭建「自托管运行器 (Self-hosted runners)」来规避官方运行器的分钟计费机制。（后端学习可跳过自托管部分。）

## 1.4 什么时候迁移到 GitHub Actions 是有意义的？ (When Does Moving to GitHub Actions Make Sense?)

* **核心主旨**：决定是否实施迁移取决于团队对 GitHub 原生生态的依赖程度、复用公共组件的能力，以及重构现有自动化脚本的成本。
* **逻辑脉络与评估标准**：
  * **对 GitHub 的投入考量 (Investment in GitHub)**：如果源代码和开发生命周期已经高度托管在 GitHub，直接使用集成的 Actions 可以避免引入第三方自动化工具造成的系统割裂。
  * **利用公共操作的潜力 (Use of Public Actions)**：能否直接从操作市场中找到满足业务需求的开源 Actions。大量复用现成操作可以成倍降低迁移的定制化投入。
  * **自定义与重构成本 (Creating Your Own Actions)**：若团队拥有大量在其他平台上编写的私有脚本，需评估将它们转化为自定义操作（Custom Actions）语法或直接在 Actions Shell 中调用的改造成本。
* **易错细节**：
  * 迁移过程中必须重新规划和考量**制品管理 (Artifact Management)** 机制，以及重新审视其安全提示与加密配置。

## 1.5 结论 (Conclusion)

* **重点结论**：GitHub Actions 提供了一个全面的框架，允许开发者无需借助任何外部应用即可直接实现 GitHub 内托管内容的全面自动化。
* **核心主旨与知识点关联**：
  * 自动化的实施程度具有极高弹性：既可以极其简单，也可以异常复杂。
  * 不断增长的用户社区提供的现成工作流和操作，极大降低了学习和定制设置的门槛。本章通过明确核心定义和计费模型，为下一章（深入解构 GitHub Actions 工作流组件与底层运行逻辑）奠定了基础。

## 本章速记

| 概念 | 一句话 |
|------|--------|
| Workflow | 自动化管道，存在 `.github/workflows/` |
| Action | 可复用的步骤模块 |
| Runner | 实际执行作业的机器环境 |
| Artifact | 作业间传文件，不收流量费 |
| Packages | 对外发包，收流量费 |
