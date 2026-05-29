# 第3章：Action 的内部结构 (What's in an action?)

## 3.1 Action 的结构 (The Structure of an action)

* **核心主旨**：Action 的底层实现形式具有高度弹性，既可以是非常简单的单行脚本，也可以是包含测试用例、复杂业务逻辑和自身自动化流水线的完整代码库。
* **核心知识点与关键定义**：
  * 每一个 Action 的背后都对应一个标准的 **GitHub 存储库 (Repository)**。
  * 以高度复杂的官方 `checkout` action 为例，其源代码库不仅包含执行核心逻辑的代码（如 `src` 目录下的 TypeScript 文件），还包含许可证、测试目录以及相关配置文件。
* **逻辑脉络与因果关联**：
  * **相互依赖的嵌套逻辑**：工作流 (Workflows) 在步骤中调用 Action 来执行具体任务；而 Action 的开发者同样会为其 Action 代码库配置专属的工作流（存放在 `.github/workflows` 中），用于在代码推送或拉取请求时进行自身的 **CI/CD 自动化验证与测试**。这揭示了 GitHub Actions 系统内组件高度解耦且自我闭环的设计哲学。
* **拓展建议**：
  * 结合第 11 章可了解从零初始化自定义 Action 存储库的目录规范（后端学习可跳过自定义 Action 开发）。

```
Workflow 调用 Action
       ↓
Action 仓库（含 action.yml + 源码 + 自身 CI workflow）
```

## 3.2 与 Action 交互 (Interfacing with actions)

* **核心主旨**：通过专属的元数据文件定义 Action 的对外交互契约，明确工作流调用该 Action 时所需传递的数据格式与期望返回的结果。
* **关键定义与核心配置拆解**：
  * **`action.yml` (或 `action.yaml`)**：这是一个特殊的 YAML 元数据文件，是标识一个存储库为可用 Action 的核心标志。
  * **文件四大核心区块**：
    1. **基本信息 (Basic info)**：定义 `name`（名称）、`author`（作者）和 `description`（描述）。
    2. **`inputs`（输入参数）**：定义 Action 接收的外部数据。可配置参数的描述、默认值 (`default`) 以及是否为必填项 (`required: true/false`)。
    3. **`outputs`（输出结果）**：定义 Action 执行完毕后将返回给工作流的数据点。
    4. **`runs`（执行配置）**：定义 Action 采用何种底层技术实现（如 Node.js、Docker 容器或复合脚本）及其执行入口。
  * **可选配置区块**：**`branding`**（品牌化），允许为 Action 指定在 Marketplace 中显示的图标 (`icon`) 和颜色 (`color`)。
* **逻辑脉络与实用要点**：
  * `action.yml` 文件本质上是工作流与 Action 代码之间的**硬性契约**。当 `inputs` 中声明某参数为必填时，工作流中调用该 Action 的 `with` 子句必须提供对应键值对。
  * 用户通常可以通过查看 Action 仓库根目录下的 `README.md` 文件直观地获取这些接口规范的展示版本。

```yaml
# action.yml 结构示例
name: 'My Action'
description: 'Do something useful'
inputs:
  token:
    description: 'API token'
    required: true
outputs:
  result:
    description: 'Operation result'
runs:
  using: 'node20'
  main: 'dist/index.js'
```

```yaml
# 工作流中调用
- uses: my-org/my-action@v1
  with:
    token: ${{ secrets.API_TOKEN }}
```

## 3.3 使用 Action (Using actions)

* **核心主旨**：规范化声明 Action 的拉取路径及版本控制策略，确保工作流执行的稳定性与可复现性。
* **公式要点与语法规范**：
  * **调用语法**：使用 **`uses: <相对路径>@<版本标识>`**。
  * **路径解析逻辑**：例如 `uses: actions/checkout@v4` 中，`actions/checkout` 实际上是指向 `github.com/actions/checkout` 存储库的相对路径。
* **核心知识点与版本控制策略**：
  * **`@` 符号后的版本引用机制**：系统支持任何有效的 Git 引用类型作为版本锁定锚点。
    1. **标签 (Tag)**：最推荐的生产级用法（如 `@v4`、`@v4.2.0`），兼顾稳定性与明确的语义化版本控制。
    2. **分支名 (Branch)**：例如 `@main`。**易错细节**：这会始终拉取分支最新代码，极易因 Action 引入破坏性更新而导致工作流突然崩溃，**不推荐在生产环境使用**。
    3. **提交哈希 (Commit SHA)**：提供绝对的不可变性和最高安全级别，但失去了自动获取补丁更新的便利性。

| 引用方式 | 稳定性 | 适用场景 |
|----------|--------|----------|
| `@v4` / `@v4.2.0` | 高 | 生产环境（推荐） |
| `@main` | 低 | 仅开发调试 |
| `@abc1234...` (SHA) | 最高 | 安全敏感场景 |

## 3.4 公开 Action 与操作市场 (Public actions and the Marketplace)

* **核心主旨**：Actions Marketplace 是 GitHub 生态内发现、分享和集成开源自动化模块的中央枢纽，旨在最大化避免重复造轮子。
* **实用要点与导航逻辑**：
  * **独立入口**：用户可通过 [github.com/marketplace?type=actions](https://github.com/marketplace?type=actions) 直接浏览全局操作市场。
  * **编辑器内联集成**：在代码仓库的 Web 端编辑工作流时，右侧会自动唤出 Marketplace 侧边栏，支持直接搜索关键字并根据当前仓库代码类型推荐相关 Action。
  * **官方第一方操作**：GitHub 官方提供的基础且权威的 Action（如 checkout、cache）统一托管在 **`github.com/actions`** 组织下。
* **逻辑脉络与界面展示差异**：
  * 如果直接访问仓库 URL（如 `github.com/actions/checkout`），看到的是标准的源码树结构。
  * 如果通过 Marketplace 链接访问，GitHub 会渲染一个专门的**用户友好页面**，不仅包含美化后的 `README.md`，还在页面顶部提供 **「使用最新版本」 (Use latest version)** 下拉按钮，一键生成可直接复制到工作流中的 YAML 调用代码片段。

## 3.5 结论 (Conclusion)

* **重点结论**：
  * Action 的本质由两部分构成：实际执行的**代码集**，以及规定环境、输入和输出契约的特殊元数据文件 **`action.yml`**。
  * 合理利用 GitHub Actions Marketplace 和编辑器内置的搜索功能，是快速组装高效工作流的关键。
* **知识点关联**：
  * 理解了单个 Action 是如何被结构化定义和版本引用的，为后续（第 4 章）在 GitHub Web 界面中实际编写和提交串联多个 Action 的工作流（Workflow）铺平了道路。

## 本章速记

| 概念 | 要点 |
|------|------|
| `action.yml` | Action 的元数据契约：inputs / outputs / runs |
| `uses: org/repo@version` | 调用语法，生产用 Tag 或 SHA |
| Marketplace | 发现和复用公开 Action，避免重复造轮子 |
| 官方 Actions | 托管在 `github.com/actions` 组织下 |
