# 第12章：高级工作流 (Advanced Workflows)

> **后端学习提示**：本章**跳过**。入门工作流、可重用工作流、必选工作流属**组织/企业级**治理，个人项目和小团队无需深究；了解 `workflow_call` 概念即可。

## 12.1 创建您自己的入门工作流 (Creating Your Own Starter Workflows)

* **核心主旨**：为组织内部创建自定义的「入门工作流模板」，以标准化新项目的自动化构建流程，降低团队成员上手 GitHub Actions 的门槛。
* **核心知识点与关键文件规范**：
  * **存放位置**：自定义的入门工作流必须存放在组织级别名为 `.github` 的特殊存储库中，且路径必须为 `workflow-templates` 目录。
  * **必需的配套文件**：
    1. **工作流 YAML 文件**：包含实际自动化逻辑的代码文件（如 `rndrepos-info.yml`）。
    2. **SVG 图标文件**：用于在 GitHub Web 界面的入门工作流列表中显示的矢量图形文件（如 `check-square.svg`）。
    3. **JSON 元数据文件**：文件名必须与 YAML 文件名匹配（如 `rndrepos-info.properties.json`）。该文件为系统提供元数据，使工作流能够作为官方模板在界面中正确渲染和推荐。
* **公式要点与语法规范**：
  * **动态分支占位符**：在模板中定义触发分支时，不应硬编码为 `main`，而应使用 **`$default-branch`** 占位符。当用户将此模板应用到具体存储库时，GitHub 会自动将其替换为该库的实际默认分支名。
* **易错细节**：
  * 如果将入门工作流设计得过于复杂，反而会失去「入门模板」的意义。对于高度复杂的逻辑，最佳实践是将其抽象为**自定义操作 (Custom Actions)** 或**可重用工作流 (Reusable Workflows)**，然后在简单的入门工作流中去调用它们。

```
.github 组织仓库/
└── workflow-templates/
    ├── ci-go.yml
    ├── ci-go.properties.json
    └── ci-go.svg
```

## 12.2 可重用工作流 (Reusable Workflows)

* **核心主旨**：通过声明特殊的调用触发器，允许一个工作流被其他工作流直接引用，从而实现自动化代码的跨项目复用与共享，避免代码重复。
* **关键定义与核心机制**：
  * **触发器声明**：通过在工作流配置中添加 **`workflow_call`** 事件，将其标记为可被外部工作流调用的「可重用工作流」。被调用的工作流将直接继承调用方 (Caller workflow) 的事件负载 (Event payload) 上下文。
  * **概念辨析**：

| 触发器 | 用途 |
|--------|------|
| `workflow_call` | 工作流间复用 |
| `workflow_dispatch` | 手动界面触发 |
| `workflow_run` | 一个工作流完成后触发另一个 |

* **逻辑脉络与数据传递（输入、机密与输出）**：
  * **接收输入与机密 (Inputs and Secrets)**：在 `workflow_call` 触发器下，使用 `inputs` 声明需接收的参数，使用 `secrets` 声明必须传入的加密凭证。调用方在 `uses` 时通过 `with` 和 `secrets` 子句传值。支持 `secrets: inherit` 将调用方所有机密透传。
  * **返回输出 (Outputs)**：步骤值写入 **`$GITHUB_OUTPUT`**，映射为作业 `outputs`，再在 `workflow_call` 的 `outputs` 块中暴露给调用方。
* **易错细节与硬性限制 (Limitations)**：
  1. 一个调用方工作流最多只能调用 **20 个**可重用工作流（含嵌套）。
  2. 调用方在 `env` 上下文中定义的环境变量**不会**自动传递给可重用工作流。
  3. **私有库隔离限制**：无法调用另一个独立私有存储库中的可重用工作流。只有同在**同一个私有存储库内**的工作流才能互相调用。
* **重点结论（与复合操作的对比）**：
  * 相比于复合操作 (Composite Actions) 只能运行在单作业且无法直接使用 `secrets`，**可重用工作流支持多作业并行、可以直接传递和使用机密数据，并拥有更强大的日志和 `runs-on` 控制能力**。

```yaml
# 被调用的可重用工作流 (.github/workflows/reusable-ci.yml)
on:
  workflow_call:
    inputs:
      go-version:
        required: true
        type: string
    secrets:
      TOKEN:
        required: true

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: ${{ inputs.go-version }}
      - run: go test ./...

# 调用方
jobs:
  call-ci:
    uses: ./.github/workflows/reusable-ci.yml
    with:
      go-version: '1.22'
    secrets: inherit
```

## 12.3 必选工作流 (Required Workflows)

* **核心主旨**：允许组织管理员强制规定某些工作流必须在特定（或所有）存储库中运行，并作为拉取请求 (Pull Request) 合并的强制性安全/合规检查闸门。
* **逻辑脉络与配置执行**：
  * **作用域设置**：在组织的 Settings → Actions → General 中配置，可选择将其应用于「所有存储库 (All repositories)」或「选定的存储库 (Selected repositories)」。
  * **因果触发逻辑**：一旦配置生效，目标库中发起的任何拉取请求，系统都会自动并排执行此必选工作流。只有当必选工作流的检查状态变为 `Success` 时，系统才允许代码合并操作。
* **易错细节与系统限制 (Constraints)**：
  * 工作流文件必须是有效的 YAML 语法。
  * 触发器必须包含有效的 PR 事件（**`pull_request` 或 `pull_request_target`**）。
  * **致命限制**：**必选工作流内部绝不允许使用代码扫描操作 (Code-scanning actions，如 CodeQL)**。代码扫描必须通过单独的仓库安全策略页面进行配置，违规调用会导致配置失败并报错。
* **拓展建议**：
  * 企业级实战中可结合必选工作流实现跨全组织的强制合规审查（例如强制检测项目中是否包含合规的 `CONTRIBUTING.md` 或许可证声明）。

## 12.4 结论 (Conclusion)

* **重点结论**：
  * 本章通过三种进阶模式大幅提升了自动化架构的可维护性与管控力：
    1. **入门工作流 (Starter workflows)**：标准化组织内的新工作流结构和上手流程。
    2. **可重用工作流 (Reusable workflows)**：提供一种共享模型，让多个用户和存储库能够安全地复用现成的自动化代码。
    3. **必选工作流 (Required workflows)**：作为组织合规的强制抓手，直接拦截不合规的拉取请求。
* **前后知识点关联**：
  * 掌握了组织级工作流的复用与管控后，逻辑将自然过渡至下一章（第 13 章），进一步探讨在这些工作流内部，如何通过矩阵策略 (Matrix)、容器化 (Containers) 以及直接调用 GitHub CLI 来编排极其复杂的底层执行流。

## 本章速记

| 模式 | 层级 | 后端需要？ |
|------|------|-----------|
| Starter Workflows | 组织 `.github` 仓库 | ❌ |
| Reusable Workflows (`workflow_call`) | 仓库内复用 | 🔄 了解概念 |
| Required Workflows | 组织强制 PR 检查 | ❌ |
