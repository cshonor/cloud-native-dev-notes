# 第9章：Actions 与安全 (Actions and Security)

> **后端学习提示**：本章**必学**。重点掌握 Secrets 管理、最小权限 `permissions`、脚本注入防护、`pull_request` vs `pull_request_target` 区别。

## 9.1 通过配置实现安全 (Security by Configuration)

* **核心主旨**：虽然 GitHub Actions 提供了强大的自动化能力，但也引入了安全风险，通过合理的配置（Configuration）可以直接在存储库和环境层面施加防护，防止恶意滥用和意外破坏。
* **核心知识点与关键定义**：
  * **Actions 权限 (Actions permissions)**：可在存储库「设置 (Settings)」中控制允许运行哪些操作。选项包括：允许所有、完全禁用、仅允许当前组织的本地操作，或**仅允许指定的操作和可重用工作流 (Allow specified actions and reusable workflows)**。
  * **已验证创建者 (Verified creators)**：指通过了 GitHub 业务开发团队验证的 Action 作者，其发布的 Action 旁边会带有特殊的复选框徽章。
  * **外部协作者 (Outside Collaborator)**：针对 Fork 存储库发起拉取请求 (Pull Request) 的用户。可配置需要管理员**批准 (Require approval)** 后，才能在其 PR 上运行工作流，防止外部恶意代码直接在工作流计算环境中执行。
  * **CODEOWNERS 文件**：通过在存储库根目录或 `.github` 目录下定义该文件，可以强制要求特定团队或人员对特定文件（如安全配置、工作流文件）的修改进行审查。
  * **受保护的分支与标签 (Protected Branches and Tags)**：设置规则来禁止破坏性操作（如强制推送 force push、删除），并要求合并前必须通过状态检查 (Status checks) 和 PR 审查。
  * **存储库规则集 (Repository Rulesets)**：将多个保护规则逻辑打包，通过 `fnmatch` 语法跨多个分支或标签批量应用，支持设定可绕过规则的用户白名单。
* **逻辑脉络与前后因果**：
  * **配置的纵深防御逻辑**：限制可用的外部 Actions（防供应链污染）→ 限制谁能触发执行（防外部恶意触发）→ 限制内置 Token 权限（防越权访问）→ 保护核心分支与标签（防代码篡改）。
* **易错细节**：
  * **规则重叠陷阱 (Rule Layering)**：如果多个规则集应用于同一个标签或分支，规则会被**聚合 (aggregated)**，当配置存在冲突时，系统强制采用**最严格 (most restrictive)** 的规则。

## 9.2 通过设计实现安全 (Security by Design)

* **核心主旨**：不仅要配置安全，工作流的代码设计本身必须具备防御性，特别是在处理敏感数据（机密、令牌）和外部不可信输入时，需遵循最小权限和隔离原则。
* **核心知识点与关键概念**：
  * **个人访问令牌 (PAT, Personal Access Token)**：用户级别的广域令牌。**安全规范**：仅在生成时可见，必须立即存入 GitHub Secrets 中，绝不能明文写在代码里。
  * **内置 `GITHUB_TOKEN`**：GitHub 自动注入的生命周期最多为 **24 小时** 的临时令牌。**防止死循环机制**：系统默认禁止通过该 Token 触发的操作去启动新的工作流运行（例外情况：`workflow_dispatch` 和 `repository_dispatch` 事件仍可触发）。
  * **不可信输入 (Untrusted Input)**：从触发事件上下文中获取的任何外部数据（如 PR 标题、提交信息）。
  * **脚本注入 (Script Injection)**：攻击者在文本字段中植入恶意 Shell 命令，若工作流在 `run` 步骤中直接展开这些变量，系统会将其作为可执行命令运行。
* **公式要点与解决方案**：
  * **危险设计（脚本注入漏洞）**：`run: echo ${{ github.event.head_commit.message }}`。如果提交信息包含 `; rm -rf /`，该代码将实际执行注入命令。
  * **安全设计（环境变量中转）**：必须先将不可信输入绑定到步骤级别的环境变量中，然后再在 Shell 中引用，避免直接的宏替换展开：

```yaml
# ❌ 危险：直接展开不可信输入
# run: echo ${{ github.event.head_commit.message }}

# ✅ 安全：通过 env 中转
env:
  COMMIT_MSG: ${{ github.event.head_commit.message }}
run: echo "$COMMIT_MSG"
```

* **易错细节与机密陷阱**：
  * **机密值并非绝对安全**：虽然 GitHub 会在日志中将 Secrets 自动脱敏并替换为 `***`，但如果在机密数据中植入 Shell 脚本代码并被直接执行，**代码仍然会在运行器上物理执行**，即使日志不显示其具体内容。
* **案例数据与依赖安全**：
  * 在引用第三方 Action 时，直接使用 `@main` 等分支名风险极高；推荐使用具体的 **提交哈希 (Commit SHA)** 锁定绝对版本，以防止第三方 Action 作者在其标签或分支下隐秘注入恶意代码。

```yaml
permissions:
  contents: read
  packages: write

# 锁定 Action 版本（生产推荐 SHA）
- uses: actions/checkout@b4ffde65f46336ab88eb53be4084771dbfa32975 # v4.1.1
```

## 9.3 通过监控实现安全 (Security by Monitoring)

* **核心主旨**：持续审查引入的更改、自动化扫描已知漏洞，并在处理拉取请求时隔离恶意代码的执行权限，构建安全闭环。
* **关键定义与工具生态**：
  * **代码扫描 (Code Scanning)**：通过官方提供的入门工作流快速接入扫描，如 **CodeQL**（静态安全分析）和 **Dependabot**（自动依赖项扫描并推送修复 PR）。
  * **OSSF Scorecard**：评估存储库安全状况的开源工具，通过 GitHub Action 自动扫描并为安全实践（如分支保护、依赖锁定）打分（1-10 分）。
* **核心知识点与拉取请求漏洞剖析 (Pull Request Vulnerabilities)**：
  * **`pull_request` 事件**：
    * 运行在拉取请求的**合并提交 (Merge commit)** 上。
    * 默认具有**极低权限**的只读 Token，且**无法访问存储库机密 (Secrets)**。
  * **`pull_request_target` 事件**：
    * 运行在目标存储库（通常是 base 分支，如 `main`）的上下文中。
    * 具有**读写权限**的 Token，并能**直接访问存储库机密**。
* **逻辑脉络与致命陷阱**：
  * **漏洞复现链条**：开发者为了让 PR 能够读取机密去执行测试，将触发器改为了 `pull_request_target`。但如果工作流中包含了 `uses: actions/checkout@v4` 并显式指定 `ref: ${{ github.event.pull_request.head.sha }}`（拉取攻击者提交的 PR 代码），这会导致**完全不可信的代码被拉取到一个拥有完整写权限和机密访问权的高特权环境中**执行。
  * **攻击后果**：攻击者只需在提交中修改构建脚本，加入外发 HTTP 请求、删除文件或读取环境变量的逻辑。当高特权的 `pull_request_target` 触发并运行该构建脚本时，机密将被窃取或暴露。
* **实用要点（安全隔离方案）**：
  * **拆分工作流模式 (Workflow Splitting)**：使用两个独立的工作流来安全处理不受信的 PR：
    1. **不受信环境 (Workflow 1)**：通过普通 `pull_request` 触发，不含任何特权和机密，进行基础的编译/测试，然后将结果和日志上传为**制品 (Artifact)**。
    2. **特权环境 (Workflow 2)**：通过 **`workflow_run`** 事件触发（当 Workflow 1 成功完成时）。它运行在受信任的 base 分支上下文中，下载前一个工作流生成的制品，然后利用其拥有的高权限机密去执行最终操作（如部署、发布或评论 Issue）。

```
PR 代码（不可信）
    ↓ pull_request（无 Secrets，只读）
Workflow 1: 测试 → 上传 Artifact
    ↓ workflow_run（可信 base 分支）
Workflow 2: 下载 Artifact → 使用 Secrets 部署
```

## 9.4 结论 (Conclusion)

* **重点结论**：GitHub Actions 的灵活性伴随着等量的风险敞口。建立安全的自动化环境不仅仅是勾选复选框，更需要在工作流的**配置权限**、**代码编写方式（防注入与机密滥用）**以及**受限的 PR 隔离监控**这三个维度同步发力。
* **知识点关联**：通过本章了解了如何使代码免受蓄意攻击或配置错误的影响，这种强大的「审计与故障排查」意识将自然引出下一章（第 10 章）的主题：如何使用日志记录、监控和内置调试工具深入洞察工作流在运行时的底层状态。

## 本章速记（后端必记）

| 主题 | 要点 |
|------|------|
| Secrets | 存仓库 Settings，用 `${{ secrets.XXX }}`，禁止硬编码 |
| `permissions` | 最小权限，显式声明后未写的 scope 变 `none` |
| 脚本注入 | 不可信输入走 `env` 中转，不要直接 `${{ }}` 拼进 `run` |
| `pull_request` | 无 Secrets，安全跑 PR 测试 |
| `pull_request_target` | 有 Secrets，**绝不能 checkout PR 代码** |
| Action 版本 | 生产用 Tag 或 SHA，不用 `@main` |
